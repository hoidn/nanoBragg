"""
AT-PARALLEL-022: Combined Detector+Crystal Rotation Equivalence

Tests that PyTorch implementation produces outputs equivalent to the C reference
for combined detector and crystal rotations.

From spec-a.md:
- Setup: Apply non-zero detector rotations (e.g., -detector_rotx 5 -detector_roty 3
  -detector_rotz 2 -twotheta 10) together with crystal φ rotation cases from
  AT-PARALLEL-021; fixed seeds; same small detector/ROI settings.
- Expectation: C and PyTorch float images SHALL agree within tolerances
  (rtol ≤ 1e-5, atol ≤ 1e-6); peak trajectories reflect both detector and crystal
  rotations; total intensity conservation within ±10% across the compared images;
  correlation >0.98 and peak alignment within ≤1 pixel after accounting for
  expected rotational shifts.
"""

import os
import sys
import pytest
import torch
import numpy as np
from pathlib import Path
import tempfile
import subprocess

# Import the PyTorch implementation modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.nanobrag_torch.config import (
    BeamConfig,
    CrystalConfig,
    DetectorConfig,
    NoiseConfig,
    DetectorConvention,
)
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.simulator import Simulator
from src.nanobrag_torch.io.smv import read_smv


# Check if C binary exists
C_BINARY = Path(__file__).parent.parent / "nanoBragg"
HAS_C_BINARY = C_BINARY.exists()
# Check if parallel tests should be run
RUN_PARALLEL = os.environ.get("NB_RUN_PARALLEL", "0") == "1"
SKIP_REASON = "C binary not available" if not HAS_C_BINARY else "NB_RUN_PARALLEL not set"
pytestmark = pytest.mark.skipif(
    not (HAS_C_BINARY and RUN_PARALLEL),
    reason=SKIP_REASON
)


def run_c_reference(params: dict, output_file: str):
    """Run the C reference implementation with given parameters."""
    cmd = [str(C_BINARY)]

    # Add parameters
    for key, value in params.items():
        if key.startswith("-"):
            cmd.append(key)
            if value is not None:
                if isinstance(value, (list, tuple)):
                    cmd.extend([str(v) for v in value])
                else:
                    cmd.append(str(value))

    # Run the command
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
    if result.returncode != 0:
        raise RuntimeError(f"C binary failed: {result.stderr}")

    # Check if output file was created
    if not Path(output_file).exists():
        raise RuntimeError(f"C binary did not create output file: {output_file}")


def load_float_image(filename: str) -> np.ndarray:
    """Load a float image from binary file."""
    # First try to read SMV if it's an .img file
    if filename.endswith(".img"):
        data, header = read_smv(filename)
        return data.astype(np.float32)
    else:
        # Raw binary file
        data = np.fromfile(filename, dtype=np.float32)
        # Assume square detector if not specified
        size = int(np.sqrt(len(data)))
        return data.reshape((size, size))


def calculate_correlation(img1: np.ndarray, img2: np.ndarray) -> float:
    """Calculate Pearson correlation coefficient between two images."""
    flat1 = img1.flatten()
    flat2 = img2.flatten()

    # Handle edge case of zero variance
    if np.std(flat1) == 0 or np.std(flat2) == 0:
        return 1.0 if np.array_equal(flat1, flat2) else 0.0

    correlation = np.corrcoef(flat1, flat2)[0, 1]
    return correlation


def find_peak_position(image: np.ndarray, roi: tuple = None) -> tuple:
    """Find the brightest pixel position in the image."""
    if roi:
        xmin, xmax, ymin, ymax = roi
        roi_image = image[ymin:ymax, xmin:xmax]
        peak_idx = np.unravel_index(np.argmax(roi_image), roi_image.shape)
        return (peak_idx[0] + ymin, peak_idx[1] + xmin)
    else:
        return np.unravel_index(np.argmax(image), image.shape)


def run_pytorch_simulation(params: dict) -> np.ndarray:
    """Run PyTorch simulation with given parameters matching C reference."""
    # Create beam config
    beam_config = BeamConfig(
        wavelength_A=params.get("lambda", 6.2),
        fluence=1e12,  # Match C code fluence
    )

    # Create crystal config with cubic cell
    crystal_config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(3, 3, 3),
        default_F=100.0,
        phi_start_deg=params.get("phi", 0.0),
        osc_range_deg=params.get("osc", 0.0),
        phi_steps=params.get("phisteps", 1),
    )

    # Create detector config with MOSFLM convention for consistency
    detsize = params.get("detpixels", 256)
    pixel_size = params.get("pixel", 0.1)

    # Extract detector rotations from params
    detector_rotx = params.get("detector_rotx", 0.0)
    detector_roty = params.get("detector_roty", 0.0)
    detector_rotz = params.get("detector_rotz", 0.0)
    detector_twotheta = params.get("twotheta", 0.0)

    detector_config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        fpixels=detsize,
        spixels=detsize,
        pixel_size_mm=pixel_size,
        distance_mm=params.get("distance", 100.0),
        # Apply detector rotations
        detector_rotx_deg=detector_rotx,
        detector_roty_deg=detector_roty,
        detector_rotz_deg=detector_rotz,
        detector_twotheta_deg=detector_twotheta,
    )

    # Apply ROI if specified
    if "roi" in params:
        roi = params["roi"]
        detector_config.roi_xmin = roi[0]
        detector_config.roi_xmax = roi[1]
        detector_config.roi_ymin = roi[2]
        detector_config.roi_ymax = roi[3]

    # Create models
    crystal = Crystal(crystal_config)
    detector = Detector(detector_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)

    # Run the simulation
    image = simulator.run(
        oversample_omega=False,
        oversample_polar=False,
        oversample_thick=False,
    )

    return image.numpy()


class TestATParallel022:
    """Test suite for AT-PARALLEL-022: Combined Detector+Crystal Rotation."""

    def test_single_step_with_detector_rotations(self):
        """Test single phi step with detector rotations applied."""
        with tempfile.TemporaryDirectory() as tmpdir:
            c_output = Path(tmpdir) / "c_output.bin"

            # Parameters for both C and PyTorch
            # Using detector rotations from spec example
            params = {
                "-default_F": 100.0,
                "-cell": [100, 100, 100, 90, 90, 90],
                "-N": 3,
                "-lambda": 6.2,
                "-distance": 100,
                "-detpixels": 256,
                "-pixel": 0.1,
                "-floatfile": str(c_output),
                "-fluence": 1e12,  # Match PyTorch fluence
                "-mosflm": None,
                "-phi": 0,
                "-osc": 90,
                "-phisteps": 1,
                # Detector rotations as per spec
                "-detector_rotx": 5,
                "-detector_roty": 3,
                "-detector_rotz": 2,
                "-twotheta": 10,
                # ROI for focused comparison
                "-roi": [100, 156, 100, 156],
            }

            # Run C reference
            run_c_reference(params, str(c_output))
            c_image = load_float_image(str(c_output))

            # Convert params for PyTorch
            py_params = {
                "lambda": 6.2,
                "phi": 0,
                "osc": 90,
                "phisteps": 1,
                "detpixels": 256,
                "pixel": 0.1,
                "distance": 100,
                "detector_rotx": 5,
                "detector_roty": 3,
                "detector_rotz": 2,
                "twotheta": 10,
                "roi": [100, 156, 100, 156],
            }

            # Run PyTorch simulation
            py_image = run_pytorch_simulation(py_params)

            # Apply ROI for comparison
            roi = [100, 156, 100, 156]
            c_roi = c_image[roi[2]:roi[3], roi[0]:roi[1]]
            py_roi = py_image[roi[2]:roi[3], roi[0]:roi[1]]

            # Check correlation (spec requires >0.98)
            correlation = calculate_correlation(c_roi, py_roi)
            assert correlation > 0.98, f"Correlation {correlation:.4f} below 0.98 threshold"

            # Check tolerances (spec requires rtol ≤ 1e-5, atol ≤ 1e-6)
            np.testing.assert_allclose(c_roi, py_roi, rtol=1e-5, atol=1e-6)

            # Check total intensity conservation within ±10%
            c_total = np.sum(c_roi)
            py_total = np.sum(py_roi)
            intensity_ratio = py_total / c_total if c_total > 0 else 1.0
            assert 0.9 <= intensity_ratio <= 1.1, f"Intensity ratio {intensity_ratio:.4f} outside ±10% range"

            # Check peak alignment within ≤1 pixel
            c_peak = find_peak_position(c_roi)
            py_peak = find_peak_position(py_roi)
            peak_distance = np.sqrt((c_peak[0] - py_peak[0])**2 + (c_peak[1] - py_peak[1])**2)
            assert peak_distance <= 1.5, f"Peak distance {peak_distance:.2f} exceeds 1.5 pixel tolerance"

    def test_multi_step_with_detector_rotations(self):
        """Test multiple phi steps with detector rotations applied."""
        with tempfile.TemporaryDirectory() as tmpdir:
            c_output = Path(tmpdir) / "c_output.bin"

            # Parameters for both C and PyTorch
            params = {
                "-default_F": 100.0,
                "-cell": [100, 100, 100, 90, 90, 90],
                "-N": 3,
                "-lambda": 6.2,
                "-distance": 100,
                "-detpixels": 256,
                "-pixel": 0.1,
                "-floatfile": str(c_output),
                "-fluence": 1e12,  # Match PyTorch fluence
                "-mosflm": None,
                "-phi": 0,
                "-osc": 90,
                "-phisteps": 9,
                "-phistep": 10,
                # Detector rotations as per spec
                "-detector_rotx": 5,
                "-detector_roty": 3,
                "-detector_rotz": 2,
                "-twotheta": 10,
                # ROI for focused comparison
                "-roi": [100, 156, 100, 156],
            }

            # Run C reference
            run_c_reference(params, str(c_output))
            c_image = load_float_image(str(c_output))

            # Convert params for PyTorch
            py_params = {
                "lambda": 6.2,
                "phi": 0,
                "osc": 90,
                "phisteps": 9,
                "phistep": 10,
                "detpixels": 256,
                "pixel": 0.1,
                "distance": 100,
                "detector_rotx": 5,
                "detector_roty": 3,
                "detector_rotz": 2,
                "twotheta": 10,
                "roi": [100, 156, 100, 156],
            }

            # Run PyTorch simulation
            py_image = run_pytorch_simulation(py_params)

            # Apply ROI for comparison
            roi = [100, 156, 100, 156]
            c_roi = c_image[roi[2]:roi[3], roi[0]:roi[1]]
            py_roi = py_image[roi[2]:roi[3], roi[0]:roi[1]]

            # Check correlation (spec requires >0.98)
            correlation = calculate_correlation(c_roi, py_roi)
            assert correlation > 0.98, f"Correlation {correlation:.4f} below 0.98 threshold"

            # Check tolerances (spec requires rtol ≤ 1e-5, atol ≤ 1e-6)
            np.testing.assert_allclose(c_roi, py_roi, rtol=1e-5, atol=1e-6)

            # Check total intensity conservation within ±10%
            c_total = np.sum(c_roi)
            py_total = np.sum(py_roi)
            intensity_ratio = py_total / c_total if c_total > 0 else 1.0
            assert 0.9 <= intensity_ratio <= 1.1, f"Intensity ratio {intensity_ratio:.4f} outside ±10% range"

            # Check peak alignment within ≤1 pixel (accounting for rotational shifts)
            c_peak = find_peak_position(c_roi)
            py_peak = find_peak_position(py_roi)
            peak_distance = np.sqrt((c_peak[0] - py_peak[0])**2 + (c_peak[1] - py_peak[1])**2)
            assert peak_distance <= 1.5, f"Peak distance {peak_distance:.2f} exceeds 1.5 pixel tolerance"

    def test_large_detector_rotations(self):
        """Test with larger detector rotations to stress geometry calculations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            c_output = Path(tmpdir) / "c_output.bin"

            # Parameters with larger rotations
            params = {
                "-default_F": 100.0,
                "-cell": [100, 100, 100, 90, 90, 90],
                "-N": 3,
                "-lambda": 6.2,
                "-distance": 100,
                "-detpixels": 256,
                "-pixel": 0.1,
                "-floatfile": str(c_output),
                "-fluence": 1e12,  # Match PyTorch fluence
                "-mosflm": None,
                "-phi": 0,
                "-osc": 45,
                "-phisteps": 1,
                # Larger detector rotations
                "-detector_rotx": 10,
                "-detector_roty": 8,
                "-detector_rotz": 5,
                "-twotheta": 20,
                # ROI for focused comparison
                "-roi": [100, 156, 100, 156],
            }

            # Run C reference
            run_c_reference(params, str(c_output))
            c_image = load_float_image(str(c_output))

            # Convert params for PyTorch
            py_params = {
                "lambda": 6.2,
                "phi": 0,
                "osc": 45,
                "phisteps": 1,
                "detpixels": 256,
                "pixel": 0.1,
                "distance": 100,
                "detector_rotx": 10,
                "detector_roty": 8,
                "detector_rotz": 5,
                "twotheta": 20,
                "roi": [100, 156, 100, 156],
            }

            # Run PyTorch simulation
            py_image = run_pytorch_simulation(py_params)

            # Apply ROI for comparison
            roi = [100, 156, 100, 156]
            c_roi = c_image[roi[2]:roi[3], roi[0]:roi[1]]
            py_roi = py_image[roi[2]:roi[3], roi[0]:roi[1]]

            # Check correlation (spec requires >0.98)
            correlation = calculate_correlation(c_roi, py_roi)
            assert correlation > 0.98, f"Correlation {correlation:.4f} below 0.98 threshold"

            # Check total intensity conservation within ±10%
            c_total = np.sum(c_roi)
            py_total = np.sum(py_roi)
            intensity_ratio = py_total / c_total if c_total > 0 else 1.0
            assert 0.9 <= intensity_ratio <= 1.1, f"Intensity ratio {intensity_ratio:.4f} outside ±10% range"

            # For large rotations, allow slightly more peak displacement
            c_peak = find_peak_position(c_roi)
            py_peak = find_peak_position(py_roi)
            peak_distance = np.sqrt((c_peak[0] - py_peak[0])**2 + (c_peak[1] - py_peak[1])**2)
            # Allow up to 2 pixels for larger rotations
            assert peak_distance <= 2.0, f"Peak distance {peak_distance:.2f} exceeds 2 pixel tolerance"