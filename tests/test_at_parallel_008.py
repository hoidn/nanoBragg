#!/usr/bin/env python3
"""AT-PARALLEL-008: Multi-Peak Pattern Registration

Tests that multiple peaks in complex patterns are correctly positioned and matched
between C and PyTorch implementations using Hungarian algorithm for optimal matching.
"""

import os
import sys
import torch
import numpy as np
import pytest
from scipy import ndimage, stats
from scipy.optimize import linear_sum_assignment
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from pathlib import Path
import tempfile
import subprocess

# Test configuration
REQUIRE_PARALLEL = os.environ.get("NB_RUN_PARALLEL") == "1"

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nanobrag_torch.config import (
    CrystalConfig, DetectorConfig, BeamConfig,
    DetectorConvention, DetectorPivot, CrystalShape
)
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.simulator import Simulator


@dataclass
class Peak:
    """Represents a detected peak in the diffraction pattern."""
    slow: float
    fast: float
    intensity: float

    def distance_to(self, other: 'Peak') -> float:
        """Calculate Euclidean distance to another peak."""
        return np.sqrt((self.slow - other.slow)**2 + (self.fast - other.fast)**2)


def get_c_binary() -> Optional[Path]:
    """Get path to C binary, checking in order of precedence."""
    if "NB_C_BIN" in os.environ:
        return Path(os.environ["NB_C_BIN"])

    paths = [
        Path("./golden_suite_generator/nanoBragg"),
        Path("./nanoBragg")
    ]

    for p in paths:
        if p.exists():
            return p.resolve()

    return None


def find_local_maxima(image: np.ndarray, percentile: float = 99.0,
                      min_distance: int = 3) -> List[Peak]:
    """Find local maxima in the image above a percentile threshold.

    Args:
        image: 2D intensity array
        percentile: Threshold percentile for peak detection
        min_distance: Minimum pixel distance between peaks

    Returns:
        List of Peak objects sorted by intensity (highest first)
    """
    # Calculate threshold
    threshold = np.percentile(image, percentile)

    # Create binary mask of high-intensity regions
    mask = image > threshold

    # Find local maxima using scipy
    local_max_mask = ndimage.maximum_filter(image, size=min_distance) == image

    # Combine masks: must be above threshold AND a local maximum
    peaks_mask = mask & local_max_mask

    # Get peak coordinates
    peak_coords = np.where(peaks_mask)

    # Create Peak objects
    peaks = []
    for slow, fast in zip(peak_coords[0], peak_coords[1]):
        intensity = image[slow, fast]
        peaks.append(Peak(slow=float(slow), fast=float(fast), intensity=float(intensity)))

    # Sort by intensity (highest first)
    peaks.sort(key=lambda p: p.intensity, reverse=True)

    return peaks


def hungarian_match_peaks(peaks1: List[Peak], peaks2: List[Peak],
                         max_distance: float = 1.0) -> Tuple[List[Tuple[int, int]], float]:
    """Match peaks between two lists using Hungarian algorithm.

    Args:
        peaks1: First list of peaks
        peaks2: Second list of peaks
        max_distance: Maximum allowed distance for a valid match

    Returns:
        Tuple of (matched pairs as indices, fraction matched)
    """
    if not peaks1 or not peaks2:
        return [], 0.0

    # Build cost matrix (distance between all peak pairs)
    n1, n2 = len(peaks1), len(peaks2)
    cost_matrix = np.full((n1, n2), max_distance * 2)  # Initialize with large cost

    for i, p1 in enumerate(peaks1):
        for j, p2 in enumerate(peaks2):
            dist = p1.distance_to(p2)
            if dist <= max_distance:
                cost_matrix[i, j] = dist

    # Solve assignment problem
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    # Filter out matches that exceed max_distance
    matched_pairs = []
    for i, j in zip(row_ind, col_ind):
        if cost_matrix[i, j] <= max_distance:
            matched_pairs.append((i, j))

    # Calculate match fraction
    match_fraction = len(matched_pairs) / min(n1, n2)

    return matched_pairs, match_fraction


def run_c_simulation(params: Dict, output_file: str) -> bool:
    """Run C nanoBragg simulation with given parameters."""
    c_binary = get_c_binary()
    if not c_binary:
        return False

    # Build command
    cmd = [str(c_binary)]

    # Add parameters
    for key, value in params.items():
        if isinstance(value, bool):
            if value:
                cmd.append(f"-{key}")
        elif isinstance(value, (list, tuple)):
            cmd.append(f"-{key}")
            for v in value:
                cmd.append(str(v))
        else:
            cmd.append(f"-{key}")
            cmd.append(str(value))

    # Add output file
    cmd.extend(["-floatfile", output_file])

    # Run command
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"C simulation failed: {e.stderr}")
        return False


def load_float_image(filepath: str, shape: Tuple[int, int]) -> np.ndarray:
    """Load a binary float image."""
    data = np.fromfile(filepath, dtype=np.float32)
    return data.reshape(shape)


class TestAT_PARALLEL_008:
    """Multi-Peak Pattern Registration tests."""

    @pytest.mark.skipif(not REQUIRE_PARALLEL, reason="Requires NB_RUN_PARALLEL=1")
    def test_triclinic_multi_peak_pattern(self):
        """Test multi-peak pattern registration for triclinic crystal.

        Spec requirement:
        - Setup: Triclinic 70,80,90,75,85,95 cell; -default_F 100; N=5;
                 detector 512×512, -pixel 0.1, -distance 100; MOSFLM
        - Procedure: Find local maxima; take top N=100 peaks above 99th percentile
        - Pass: ≥95% matched within ≤1.0 pixel; RMS error <10%; correlation ≥0.98
        """
        # Configuration parameters
        cell_params = (70.0, 80.0, 90.0, 75.0, 85.0, 95.0)
        detector_size = 512
        pixel_size = 0.1
        distance = 100.0

        # Setup PyTorch simulation
        crystal_config = CrystalConfig(
            cell_a=cell_params[0],
            cell_b=cell_params[1],
            cell_c=cell_params[2],
            cell_alpha=cell_params[3],
            cell_beta=cell_params[4],
            cell_gamma=cell_params[5],
            N_cells=(5, 5, 5),
            default_F=100.0,
            shape=CrystalShape.SQUARE,
            phi_start_deg=0.0,
            osc_range_deg=0.0,
            phi_steps=1,
            mosaic_spread_deg=0.0,
            mosaic_domains=1
        )

        detector_config = DetectorConfig(
            distance_mm=distance,
            pixel_size_mm=pixel_size,
            spixels=detector_size,
            fpixels=detector_size,
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM,
            oversample=1
        )

        beam_config = BeamConfig(
            wavelength_A=1.0,
            polarization_factor=0.0,
            fluence=1e15
        )

        # Run PyTorch simulation
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal.config, beam_config)
        py_image = simulator.run()
        py_image_np = py_image.cpu().numpy()

        # Run C simulation
        with tempfile.TemporaryDirectory() as tmpdir:
            c_output = os.path.join(tmpdir, "c_output.bin")

            c_params = {
                "cell": cell_params,
                "default_F": 100,
                "N": 5,
                "lambda": 1.0,
                "detpixels": detector_size,
                "pixel": pixel_size,
                "distance": distance,
                "mosflm": True,
                "phi": 0,
                "osc": 0,
                "mosaic": 0,
                "oversample": 1
            }

            if not run_c_simulation(c_params, c_output):
                pytest.skip("C simulation failed")

            c_image_np = load_float_image(c_output, (detector_size, detector_size))

        # Find peaks in both images
        py_peaks = find_local_maxima(py_image_np, percentile=99.0, min_distance=3)
        c_peaks = find_local_maxima(c_image_np, percentile=99.0, min_distance=3)

        # Take top 100 peaks from each
        py_peaks_top = py_peaks[:100] if len(py_peaks) >= 100 else py_peaks
        c_peaks_top = c_peaks[:100] if len(c_peaks) >= 100 else c_peaks

        # Match peaks using Hungarian algorithm
        matched_pairs, match_fraction = hungarian_match_peaks(
            py_peaks_top, c_peaks_top, max_distance=1.0
        )

        # Calculate statistics on matched peaks
        if matched_pairs:
            # Calculate intensity ratios for matched peaks
            intensity_ratios = []
            for i, j in matched_pairs:
                py_intensity = py_peaks_top[i].intensity
                c_intensity = c_peaks_top[j].intensity
                if c_intensity > 0:
                    ratio = py_intensity / c_intensity
                    intensity_ratios.append(ratio)

            # RMS error of intensity ratios
            if intensity_ratios:
                mean_ratio = np.mean(intensity_ratios)
                rms_error = np.sqrt(np.mean([(r - mean_ratio)**2 for r in intensity_ratios]))
                relative_rms_error = rms_error / mean_ratio if mean_ratio > 0 else 0
            else:
                relative_rms_error = 0
        else:
            relative_rms_error = 1.0  # No matches means 100% error

        # Calculate image correlation
        correlation = np.corrcoef(py_image_np.flatten(), c_image_np.flatten())[0, 1]

        # Print diagnostics
        print(f"\nMulti-Peak Pattern Registration Results:")
        print(f"  PyTorch peaks found: {len(py_peaks)} (top 100: {len(py_peaks_top)})")
        print(f"  C peaks found: {len(c_peaks)} (top 100: {len(c_peaks_top)})")
        print(f"  Matched peaks: {len(matched_pairs)}/{min(len(py_peaks_top), len(c_peaks_top))}")
        print(f"  Match fraction: {match_fraction:.1%}")
        print(f"  RMS error of intensity ratios: {relative_rms_error:.1%}")
        print(f"  Image correlation: {correlation:.4f}")

        # Assertions based on spec requirements
        assert match_fraction >= 0.95, \
            f"Peak match fraction {match_fraction:.1%} below 95% requirement"

        assert relative_rms_error < 0.10, \
            f"RMS error of intensity ratios {relative_rms_error:.1%} exceeds 10% tolerance"

        assert correlation >= 0.98, \
            f"Image correlation {correlation:.4f} below 0.98 requirement"

    @pytest.mark.skipif(not REQUIRE_PARALLEL, reason="Requires NB_RUN_PARALLEL=1")
    def test_peak_intensity_ordering(self):
        """Test that peak intensities are correctly ordered in both implementations."""
        # Simpler test with cubic crystal for clearer peaks
        detector_size = 256

        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5),
            default_F=100.0,
            shape=CrystalShape.SQUARE
        )

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=detector_size,
            fpixels=detector_size,
            detector_convention=DetectorConvention.MOSFLM,
            oversample=1
        )

        beam_config = BeamConfig(wavelength_A=1.5, fluence=1e15)

        # Run PyTorch simulation
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal.config, beam_config)
        py_image = simulator.run()

        # Find top 20 peaks
        py_peaks = find_local_maxima(py_image.cpu().numpy(), percentile=95.0)[:20]

        # Check that peaks are sorted by intensity
        intensities = [p.intensity for p in py_peaks]
        assert intensities == sorted(intensities, reverse=True), \
            "Peaks should be sorted by intensity (highest first)"

        # Check reasonable intensity range
        assert all(i > 0 for i in intensities), "All peak intensities should be positive"
        assert max(intensities) / min(intensities) < 1000, \
            "Intensity range seems unreasonable (too large dynamic range)"

    @pytest.mark.skipif(not REQUIRE_PARALLEL, reason="Requires NB_RUN_PARALLEL=1")
    def test_non_max_suppression(self):
        """Test that non-maximum suppression correctly identifies distinct peaks."""
        # Create a simple test pattern
        detector_size = 128

        crystal_config = CrystalConfig(
            cell_a=50.0, cell_b=50.0, cell_c=50.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(3, 3, 3),
            default_F=100.0,
            shape=CrystalShape.SQUARE
        )

        detector_config = DetectorConfig(
            distance_mm=50.0,
            pixel_size_mm=0.1,
            spixels=detector_size,
            fpixels=detector_size,
            detector_convention=DetectorConvention.MOSFLM,
            oversample=1
        )

        beam_config = BeamConfig(wavelength_A=1.0, fluence=1e15)

        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal.config, beam_config)
        image = simulator.run().cpu().numpy()

        # Find peaks with different min_distance values
        peaks_close = find_local_maxima(image, percentile=90.0, min_distance=1)
        peaks_medium = find_local_maxima(image, percentile=90.0, min_distance=3)
        peaks_far = find_local_maxima(image, percentile=90.0, min_distance=7)

        # More peaks should be found with smaller min_distance
        assert len(peaks_close) >= len(peaks_medium), \
            "Smaller min_distance should find more or equal peaks"
        assert len(peaks_medium) >= len(peaks_far), \
            "Smaller min_distance should find more or equal peaks"

        # Check that peaks are well-separated
        for peaks, min_dist in [(peaks_medium, 3), (peaks_far, 7)]:
            for i, p1 in enumerate(peaks):
                for p2 in peaks[i+1:]:
                    dist = p1.distance_to(p2)
                    assert dist >= min_dist - 0.5, \
                        f"Peaks too close: {dist:.1f} < {min_dist}"


if __name__ == "__main__":
    # Allow running directly for debugging
    test = TestAT_PARALLEL_008()

    # Check if we should run parallel tests
    if REQUIRE_PARALLEL:
        print("Running multi-peak pattern registration tests...")
        test.test_triclinic_multi_peak_pattern()
        test.test_peak_intensity_ordering()
        test.test_non_max_suppression()
        print("All tests passed!")
    else:
        print("Set NB_RUN_PARALLEL=1 to run parallel validation tests")