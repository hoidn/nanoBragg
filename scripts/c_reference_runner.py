#!/usr/bin/env python3
"""
C Reference Runner for parallel verification.

This module provides a wrapper for executing nanoBragg.c with parameter validation
and result parsing, enabling parallel verification of PyTorch implementations.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from c_reference_utils import (
    build_nanobragg_command,
    generate_identity_matrix,
    get_default_executable_path,
    validate_executable_exists,
)
from nanobrag_torch.config import BeamConfig, CrystalConfig, DetectorConfig
from smv_parser import parse_smv_image, validate_smv_file


class CReferenceRunner:
    """Wrapper for executing nanoBragg.c with parameter validation."""

    def __init__(
        self, executable_path: Optional[str] = None, work_dir: Optional[str] = None
    ):
        """Initialize with path to compiled nanoBragg executable.

        Args:
            executable_path: Path to nanoBragg executable (default: auto-detect)
            work_dir: Working directory for temporary files (default: temp dir)
        """
        if executable_path is None:
            executable_path = get_default_executable_path()

        self.executable_path = Path(executable_path)
        self.work_dir = Path(work_dir) if work_dir else Path(".")
        self._is_available = None

    def is_available(self) -> bool:
        """Check if the C reference implementation is available.

        Returns:
            True if nanoBragg executable exists and is runnable
        """
        if self._is_available is None:
            self._is_available = validate_executable_exists(str(self.executable_path))
        return self._is_available

    def run_simulation(
        self,
        detector_config: DetectorConfig,
        crystal_config: CrystalConfig,
        beam_config: BeamConfig,
        label: str = "",
        cleanup: bool = True,
    ) -> Optional[np.ndarray]:
        """Execute C simulation and return image data.

        Args:
            detector_config: DetectorConfig instance
            crystal_config: CrystalConfig instance
            beam_config: BeamConfig instance
            label: Descriptive label for logging
            cleanup: Whether to clean up temporary files

        Returns:
            np.ndarray: Image data from intimage.img, or None if execution failed
        """
        if not self.is_available():
            print(f"❌ nanoBragg executable not available: {self.executable_path}")
            return None

        print(f"🔬 Running C reference simulation: {label}")

        # Create temporary directory for this simulation
        with tempfile.TemporaryDirectory(
            prefix="c_ref_", dir=self.work_dir
        ) as temp_dir:
            temp_path = Path(temp_dir)

            try:
                # Generate identity matrix in temp directory
                matrix_file = temp_path / "identity.mat"
                generate_identity_matrix(str(matrix_file))

                # Build command
                cmd = build_nanobragg_command(
                    detector_config,
                    crystal_config,
                    beam_config,
                    matrix_file=str(matrix_file),
                    executable_path=str(self.executable_path),
                )

                # Enhanced logging for debugging
                print(f"\n📋 COMMAND DEBUG INFO:")
                print(f"   Label: {label}")
                print(f"   Detector config details:")
                print(f"      - beam_center_s: {detector_config.beam_center_s}")
                print(f"      - beam_center_f: {detector_config.beam_center_f}")
                print(f"      - distance_mm: {detector_config.distance_mm}")
                print(f"      - pixel_size_mm: {detector_config.pixel_size_mm}")
                print(f"      - spixels: {detector_config.spixels}")
                print(f"      - fpixels: {detector_config.fpixels}")
                print(f"      - detector_rotx_deg: {detector_config.detector_rotx_deg}")
                print(f"      - detector_roty_deg: {detector_config.detector_roty_deg}")
                print(f"      - detector_rotz_deg: {detector_config.detector_rotz_deg}")
                print(f"      - detector_twotheta_deg: {detector_config.detector_twotheta_deg}")
                print(f"      - detector_pivot: {detector_config.detector_pivot}")
                print(f"      - twotheta_axis: {detector_config.twotheta_axis}")
                print(f"   Raw command list: {cmd}")
                print(f"   Command via subprocess.list2cmdline: {subprocess.list2cmdline(cmd)}")
                print(f"   Formatted command: {' '.join(cmd)}")
                
                # Check beam values in command
                beam_idx = None
                if "-beam" in cmd:
                    beam_idx = cmd.index("-beam")
                    if beam_idx + 2 < len(cmd):
                        print(f"   Beam values in command: -beam {cmd[beam_idx+1]} {cmd[beam_idx+2]}")
                        # Verify beam values match config
                        cmd_beam_s = float(cmd[beam_idx+1])
                        cmd_beam_f = float(cmd[beam_idx+2])
                        if abs(cmd_beam_s - detector_config.beam_center_s) > 1e-6 or abs(cmd_beam_f - detector_config.beam_center_f) > 1e-6:
                            print(f"   ⚠️  WARNING: Beam values mismatch!")
                            print(f"      Config: ({detector_config.beam_center_s}, {detector_config.beam_center_f})")
                            print(f"      Command: ({cmd_beam_s}, {cmd_beam_f})")
                else:
                    print(f"   ⚠️  WARNING: No -beam argument found in command!")
                    
                # Check detector rotation values
                if "-detector_twotheta" in cmd:
                    tt_idx = cmd.index("-detector_twotheta")
                    print(f"   Two-theta in command: {cmd[tt_idx+1]} degrees")
                if "-detector_rotx" in cmd:
                    rotx_idx = cmd.index("-detector_rotx")
                    print(f"   Detector rotx in command: {cmd[rotx_idx+1]} degrees")
                if "-detector_roty" in cmd:
                    roty_idx = cmd.index("-detector_roty")
                    print(f"   Detector roty in command: {cmd[roty_idx+1]} degrees")
                if "-detector_rotz" in cmd:
                    rotz_idx = cmd.index("-detector_rotz")
                    print(f"   Detector rotz in command: {cmd[rotz_idx+1]} degrees")
                    
                print(f"{'='*60}\n")
                
                # Print parity table if verify_detector_geometry module is available
                try:
                    from verify_detector_geometry import print_parity_report
                    print_parity_report(detector_config, cmd, label)
                except ImportError:
                    pass

                # Execute command - nanoBragg needs to be run from project root
                # Convert relative executable path to absolute
                if not self.executable_path.is_absolute():
                    abs_executable = (Path.cwd() / self.executable_path).resolve()
                    cmd[0] = str(abs_executable)

                # Set LC_NUMERIC=C for deterministic number formatting
                env = os.environ.copy()
                env["LC_NUMERIC"] = "C"
                
                result = subprocess.run(
                    cmd,
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=60,  # 60 second timeout
                    env=env,
                )

                if result.returncode != 0:
                    print(
                        f"❌ nanoBragg execution failed (return code: {result.returncode})"
                    )
                    print(f"STDOUT: {result.stdout}")
                    print(f"STDERR: {result.stderr}")
                    return None

                # Parse output image
                image_file = temp_path / "intimage.img"
                if not image_file.exists():
                    print(f"❌ Output image not found: {image_file}")
                    print(f"STDOUT: {result.stdout}")
                    return None

                if not validate_smv_file(str(image_file)):
                    print(f"❌ Invalid SMV file: {image_file}")
                    return None

                # Parse the image
                image_data, header = parse_smv_image(str(image_file))

                print(f"✅ C reference simulation completed")
                print(f"   Image shape: {image_data.shape}")
                print(
                    f"   Value range: {image_data.min():.2e} to {image_data.max():.2e}"
                )

                return image_data.astype(np.float64)  # Convert to float for comparison

            except subprocess.TimeoutExpired:
                print(f"❌ nanoBragg execution timed out (>60s)")
                return None
            except Exception as e:
                print(f"❌ Error in C reference execution: {e}")
                return None

    def run_both_configurations(
        self,
        baseline_config: Tuple[DetectorConfig, CrystalConfig, BeamConfig],
        tilted_config: Tuple[DetectorConfig, CrystalConfig, BeamConfig],
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Run both baseline and tilted configurations.

        Args:
            baseline_config: Tuple of (detector, crystal, beam) configs for baseline
            tilted_config: Tuple of (detector, crystal, beam) configs for tilted

        Returns:
            Tuple of (baseline_image, tilted_image) or (None, None) if failed
        """
        baseline_detector, baseline_crystal, baseline_beam = baseline_config
        tilted_detector, tilted_crystal, tilted_beam = tilted_config

        print(f"\n{'='*60}")
        print("C REFERENCE PARALLEL VERIFICATION")
        print(f"{'='*60}")

        # Run baseline
        baseline_image = self.run_simulation(
            baseline_detector,
            baseline_crystal,
            baseline_beam,
            label="Baseline (simple_cubic)",
        )

        if baseline_image is None:
            print("❌ Baseline C simulation failed")
            return None, None

        # Run tilted
        tilted_image = self.run_simulation(
            tilted_detector,
            tilted_crystal,
            tilted_beam,
            label="Tilted (15° two-theta + rotations)",
        )

        if tilted_image is None:
            print("❌ Tilted C simulation failed")
            return baseline_image, None

        return baseline_image, tilted_image

    def get_executable_info(self) -> dict:
        """Get information about the nanoBragg executable.

        Returns:
            Dictionary with executable information
        """
        info = {
            "path": str(self.executable_path),
            "exists": self.executable_path.exists(),
            "executable": False,
            "size": None,
            "available": self.is_available(),
        }

        if info["exists"]:
            info["executable"] = os.access(self.executable_path, os.X_OK)
            info["size"] = self.executable_path.stat().st_size

        return info


def compute_agreement_metrics(
    pytorch_results: Tuple[np.ndarray, np.ndarray],
    c_results: Tuple[np.ndarray, np.ndarray],
) -> dict:
    """Compute quantitative agreement metrics between PyTorch and C results.

    Args:
        pytorch_results: Tuple of (baseline_image, tilted_image) from PyTorch
        c_results: Tuple of (baseline_image, tilted_image) from C reference

    Returns:
        Dictionary with agreement metrics
    """
    pytorch_baseline, pytorch_tilted = pytorch_results
    c_baseline, c_tilted = c_results

    metrics = {}

    # Baseline comparison
    if pytorch_baseline is not None and c_baseline is not None:
        # Ensure same shape
        if pytorch_baseline.shape == c_baseline.shape:
            # Correlation coefficient
            baseline_corr = np.corrcoef(pytorch_baseline.ravel(), c_baseline.ravel())[
                0, 1
            ]

            # RMS difference
            baseline_rms = np.sqrt(np.mean((pytorch_baseline - c_baseline) ** 2))
            baseline_rms_relative = baseline_rms / np.mean(np.abs(c_baseline))

            metrics["baseline"] = {
                "correlation": baseline_corr,
                "rms_absolute": baseline_rms,
                "rms_relative": baseline_rms_relative,
                "max_difference": np.max(np.abs(pytorch_baseline - c_baseline)),
            }
        else:
            metrics["baseline"] = {"error": "Shape mismatch"}

    # Tilted comparison
    if pytorch_tilted is not None and c_tilted is not None:
        if pytorch_tilted.shape == c_tilted.shape:
            tilted_corr = np.corrcoef(pytorch_tilted.ravel(), c_tilted.ravel())[0, 1]
            tilted_rms = np.sqrt(np.mean((pytorch_tilted - c_tilted) ** 2))
            tilted_rms_relative = tilted_rms / np.mean(np.abs(c_tilted))

            metrics["tilted"] = {
                "correlation": tilted_corr,
                "rms_absolute": tilted_rms,
                "rms_relative": tilted_rms_relative,
                "max_difference": np.max(np.abs(pytorch_tilted - c_tilted)),
            }
        else:
            metrics["tilted"] = {"error": "Shape mismatch"}

    # Overall metrics
    if "baseline" in metrics and "tilted" in metrics:
        if "correlation" in metrics["baseline"] and "correlation" in metrics["tilted"]:
            metrics["overall"] = {
                "min_correlation": min(
                    metrics["baseline"]["correlation"], metrics["tilted"]["correlation"]
                ),
                "all_correlations_good": (
                    metrics["baseline"]["correlation"] > 0.999
                    and metrics["tilted"]["correlation"] > 0.999
                ),
            }

    return metrics


if __name__ == "__main__":
    # Example usage and testing
    print("C Reference Runner - Test")
    print("=" * 30)

    runner = CReferenceRunner()

    # Check availability
    info = runner.get_executable_info()
    print(f"Executable info: {info}")

    if runner.is_available():
        print("✅ C reference is available")

        # Test with minimal configuration
        from nanobrag_torch.config import DetectorConvention, DetectorPivot

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=10,  # Small for testing
            fpixels=10,
            beam_center_s=5.0,
            beam_center_f=5.0,
            detector_convention=DetectorConvention.MOSFLM,
        )

        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(2, 2, 2),  # Small for testing
        )

        beam_config = BeamConfig(
            wavelength_A=6.2,
            N_source_points=1,
            source_distance_mm=10000.0,
            source_size_mm=0.0,
        )

        # Run test simulation
        result = runner.run_simulation(
            detector_config, crystal_config, beam_config, "Test simulation"
        )

        if result is not None:
            print(f"✅ Test simulation successful: {result.shape}")
        else:
            print("❌ Test simulation failed")
    else:
        print("⚠️  C reference not available, skipping test")
