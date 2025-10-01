"""
AT-PARALLEL-012: Reference Pattern Correlation
Tests correlation between PyTorch and canonical C golden reference data.

Acceptance Test Requirements (from spec-a-parallel.md):
- Setup: Use canonical C commands from tests/golden_data/README.md to generate fixtures:
  - simple_cubic (1024×1024)
  - triclinic_P1 (512×512, explicit misset)
  - cubic_tilted_detector (rotations + 2θ)
- Pass criteria:
  - simple_cubic: correlation ≥ 0.9995 and top N=50 peaks ≤ 0.5 px
  - triclinic_P1: correlation ≥ 0.9995 and top N=50 peaks ≤ 0.5 px
  - tilted: correlation ≥ 0.9995 and top N=50 peaks ≤ 1.0 px
- High-resolution variant: λ=0.5Å, 4096×4096 detector, 0.05mm pixels, 500mm distance
  - Pass: No NaNs/Infs; correlation ≥ 0.95 on 512×512 ROI; top N=50 peaks ≤ 1.0 px
"""

import os
import struct
import numpy as np
import torch
import pytest
from pathlib import Path
from scipy.optimize import linear_sum_assignment
from scipy.ndimage import maximum_filter
from scipy.stats import pearsonr
from typing import Tuple, List

from nanobrag_torch.config import (
    DetectorConfig,
    DetectorConvention,
    DetectorPivot,
    CrystalConfig,
    BeamConfig,
)
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator


def load_golden_float_image(filename: str, shape: Tuple[int, int]) -> np.ndarray:
    """Load a binary float image from golden data."""
    with open(filename, 'rb') as f:
        data = f.read()
        n_floats = len(data) // 4
        assert n_floats == shape[0] * shape[1], f"Expected {shape[0]*shape[1]} floats, got {n_floats}"
        floats = struct.unpack(f'{n_floats}f', data)
        return np.array(floats).reshape(shape)


def find_peaks(
    image: np.ndarray,
    n_peaks: int = 50,
    percentile: float = 99.0,
    min_distance: int = 3
) -> List[Tuple[int, int]]:
    """Find top N peaks in an image."""
    # Apply percentile threshold
    threshold = np.percentile(image, percentile)

    # Find local maxima
    local_max = maximum_filter(image, size=min_distance)
    mask = (image == local_max) & (image > threshold)

    # Extract peak coordinates and intensities
    peak_coords = np.column_stack(np.where(mask))
    peak_intensities = image[mask]

    # Sort by intensity (descending)
    sorted_idx = np.argsort(peak_intensities)[::-1]

    # Return top N peaks
    top_peaks = peak_coords[sorted_idx[:n_peaks]]
    return [(int(p[0]), int(p[1])) for p in top_peaks]


def match_peaks_hungarian(
    peaks1: List[Tuple[int, int]],
    peaks2: List[Tuple[int, int]],
    max_distance: float
) -> Tuple[int, float]:
    """
    Match peaks between two lists using Hungarian algorithm.

    Returns:
        Tuple of (number of matches, mean distance of matches)
    """
    if not peaks1 or not peaks2:
        return 0, float('inf')

    # Build cost matrix
    n1, n2 = len(peaks1), len(peaks2)
    cost_matrix = np.zeros((n1, n2))

    for i, p1 in enumerate(peaks1):
        for j, p2 in enumerate(peaks2):
            dist = np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
            cost_matrix[i, j] = dist

    # Solve assignment
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    # Count matches within threshold
    matches = []
    distances = []
    for i, j in zip(row_ind, col_ind):
        dist = cost_matrix[i, j]
        if dist <= max_distance:
            matches.append((i, j))
            distances.append(dist)

    mean_dist = np.mean(distances) if distances else float('inf')
    return len(matches), mean_dist


class TestATParallel012ReferencePatternCorrelation:
    """Test reference pattern correlation against golden C data."""

    def test_simple_cubic_correlation(self):
        """Test simple cubic pattern correlation (≥0.9995 correlation, ≤0.5px peaks)."""
        # Load golden data (now correctly 1024x1024 as documented)
        golden_file = Path(__file__).parent / "golden_data" / "simple_cubic.bin"
        golden_image = load_golden_float_image(str(golden_file), (1024, 1024))

        # Setup PyTorch configuration to match golden data generation
        # Generated with: -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -default_F 100 -distance 100 -detpixels 1024 -pixel 0.1
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5),
            default_F=100.0
        )

        detector_config = DetectorConfig(
            spixels=1024,
            fpixels=1024,
            pixel_size_mm=0.1,
            distance_mm=100.0,
            detector_convention=DetectorConvention.MOSFLM,  # C code default (no explicit convention flag)
            detector_pivot=DetectorPivot.BEAM
        )

        beam_config = BeamConfig(
            wavelength_A=6.2
            # Use default fluence to match C code default
        )

        # Run PyTorch simulation
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        pytorch_image = simulator.run().cpu().numpy()

        # Calculate correlation
        corr, _ = pearsonr(golden_image.flatten(), pytorch_image.flatten())

        # Find peaks
        # Note: Cast PyTorch image to float32 to match golden data precision for peak detection.
        # The golden C output is saved as float32, creating intensity plateaus. PyTorch's float64
        # precision breaks these ties with numerical noise, causing maximum_filter to find fewer
        # local maxima (45 vs 52). Correlation remains 1.0, confirming physics correctness.
        golden_peaks = find_peaks(golden_image, n_peaks=50, percentile=99.5)
        pytorch_peaks = find_peaks(pytorch_image.astype(np.float32), n_peaks=50, percentile=99.5)

        # Match peaks
        n_matches, mean_dist = match_peaks_hungarian(golden_peaks, pytorch_peaks, max_distance=0.5)

        # Assertions per spec
        assert corr >= 0.9995, f"Correlation {corr:.4f} < 0.9995 requirement"
        assert n_matches >= len(golden_peaks) * 0.95, (
            f"Only {n_matches}/{len(golden_peaks)} peaks matched (need ≥95%)"
        )
        assert mean_dist <= 0.5, f"Mean peak distance {mean_dist:.2f} > 0.5 pixel requirement"

    def test_triclinic_P1_correlation(self):
        """Test triclinic P1 pattern correlation (≥0.9995 correlation, ≤0.5px peaks)."""
        # Load golden data (512x512)
        golden_file = Path(__file__).parent / "golden_data" / "triclinic_P1" / "image.bin"
        golden_image = load_golden_float_image(str(golden_file), (512, 512))

        # Setup PyTorch configuration to match canonical command
        # From README: -misset -89.968546 -31.328953 177.753396 -cell 70 80 90 75 85 95
        # -default_F 100 -N 5 -lambda 1.0 -detpixels 512
        crystal_config = CrystalConfig(
            cell_a=70.0, cell_b=80.0, cell_c=90.0,
            cell_alpha=75.0, cell_beta=85.0, cell_gamma=95.0,
            N_cells=(5, 5, 5),
            misset_deg=(-89.968546, -31.328953, 177.753396),
            default_F=100.0
        )

        detector_config = DetectorConfig(
            spixels=512,
            fpixels=512,
            pixel_size_mm=0.1,
            distance_mm=100.0,
            detector_convention=DetectorConvention.MOSFLM,  # C code default (no explicit convention flag)
            detector_pivot=DetectorPivot.BEAM
        )

        beam_config = BeamConfig(
            wavelength_A=1.0
            # Use default fluence to match C code default
        )

        # Run PyTorch simulation
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        pytorch_image = simulator.run().cpu().numpy()

        # Calculate correlation
        corr, _ = pearsonr(golden_image.flatten(), pytorch_image.flatten())

        # Find peaks
        # Note: Cast to float32 to match golden data precision (see simple_cubic test for rationale)
        golden_peaks = find_peaks(golden_image, n_peaks=50, percentile=99.0)
        pytorch_peaks = find_peaks(pytorch_image.astype(np.float32), n_peaks=50, percentile=99.0)

        # Match peaks
        n_matches, mean_dist = match_peaks_hungarian(golden_peaks, pytorch_peaks, max_distance=0.5)

        # Assertions per spec
        assert corr >= 0.9995, f"Correlation {corr:.4f} < 0.9995 requirement"
        assert n_matches >= len(golden_peaks) * 0.95, (
            f"Only {n_matches}/{len(golden_peaks)} peaks matched (need ≥95%)"
        )
        assert mean_dist <= 0.5, f"Mean peak distance {mean_dist:.2f} > 0.5 pixel requirement"

    def test_cubic_tilted_detector_correlation(self):
        """Test tilted detector pattern correlation (≥0.9995 correlation, ≤1.0px peaks)."""
        # Load golden data (1024x1024)
        golden_file = Path(__file__).parent / "golden_data" / "cubic_tilted_detector" / "image.bin"
        golden_image = load_golden_float_image(str(golden_file), (1024, 1024))

        # Setup PyTorch configuration to match canonical command
        # From README: -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100
        # -distance 100 -detsize 102.4 -detpixels 1024 -Xbeam 61.2 -Ybeam 61.2
        # -detector_rotx 5 -detector_roty 3 -detector_rotz 2 -twotheta 15
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5),
            default_F=100.0
        )

        # Note: -Xbeam/-Ybeam are in mm, and MOSFLM convention applies
        detector_config = DetectorConfig(
            spixels=1024,
            fpixels=1024,
            pixel_size_mm=0.1,
            distance_mm=100.0,
            beam_center_s=61.2,  # Xbeam in MOSFLM -> slow axis
            beam_center_f=61.2,  # Ybeam in MOSFLM -> fast axis
            detector_rotx_deg=5.0,
            detector_roty_deg=3.0,
            detector_rotz_deg=2.0,
            detector_twotheta_deg=15.0,
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM  # -Xbeam/-Ybeam force BEAM pivot
        )

        beam_config = BeamConfig(
            wavelength_A=6.2
            # Use default fluence to match C code default
        )

        # Run PyTorch simulation
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        pytorch_image = simulator.run().cpu().numpy()

        # Calculate correlation
        corr, _ = pearsonr(golden_image.flatten(), pytorch_image.flatten())

        # Find peaks (use lower percentile for tilted detector)
        # Note: Cast to float32 to match golden data precision (see simple_cubic test for rationale)
        golden_peaks = find_peaks(golden_image, n_peaks=50, percentile=98.0)
        pytorch_peaks = find_peaks(pytorch_image.astype(np.float32), n_peaks=50, percentile=98.0)

        # Match peaks (relaxed to 1.0 pixel for tilted case)
        n_matches, mean_dist = match_peaks_hungarian(golden_peaks, pytorch_peaks, max_distance=1.0)

        # Assertions per spec (relaxed to 1.0 pixel for tilted detector)
        assert corr >= 0.9995, f"Correlation {corr:.4f} < 0.9995 requirement"
        assert n_matches >= len(golden_peaks) * 0.95, (
            f"Only {n_matches}/{len(golden_peaks)} peaks matched (need ≥95%)"
        )
        assert mean_dist <= 1.0, f"Mean peak distance {mean_dist:.2f} > 1.0 pixel requirement"

    @pytest.mark.skip(reason="High-resolution variant requires large memory and golden data generation")
    def test_high_resolution_variant(self):
        """
        Test high-resolution variant with 4096×4096 detector.

        This test requires:
        - λ=0.5Å
        - 4096×4096 detector, 0.05mm pixels, 500mm distance
        - Compare on 512×512 ROI centered on beam
        - Pass: No NaNs/Infs, correlation ≥ 0.95 on ROI, top 50 peaks ≤ 1.0 px
        """
        # This test would need golden data to be generated first
        # and requires significant memory (4096×4096×4 bytes = 64MB per image)
        pass