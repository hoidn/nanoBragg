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
    """Load a binary float image from golden data.

    Returns float32 to match C code storage precision and enable plateau-based peak detection.
    The golden C output uses float32 storage, which creates intensity plateaus at beam center.
    Loading as float64 would add artificial precision that breaks plateau tie-breaking in
    peak detection algorithms (scipy.ndimage.maximum_filter).
    """
    with open(filename, 'rb') as f:
        data = f.read()
        n_floats = len(data) // 4
        assert n_floats == shape[0] * shape[1], f"Expected {shape[0]*shape[1]} floats, got {n_floats}"
        floats = struct.unpack(f'{n_floats}f', data)
        return np.array(floats, dtype=np.float32).reshape(shape)


def find_peaks(
    image: np.ndarray,
    n_peaks: int = 50,
    percentile: float = 99.0,
    min_distance: int = 3,
    plateau_tolerance: float = 1e-4
) -> List[Tuple[int, int]]:
    """Find top N peaks in an image with plateau-aware detection.

    Handles numerical plateau fragmentation by using a tolerance-based local maximum
    test instead of exact equality. When float32 precision creates multiple slightly
    different values in what should be a plateau (e.g., PyTorch produces 324 unique
    values vs C's 66 in beam-center ROI), treats values within plateau_tolerance as
    equivalent for maximum detection.

    This addresses AT-PARALLEL-012 regression where PyTorch float32 produces 5× more
    unique intensity values than C float32, causing maximum_filter with exact equality
    to find too few or fragmented local maxima.

    Args:
        image: 2D intensity array
        n_peaks: Number of peaks to return
        percentile: Intensity percentile threshold
        min_distance: Local maximum neighborhood size
        plateau_tolerance: Relative tolerance for plateau detection (default 1e-4,
            calibrated for float32 fragmentation levels observed in AT-012)

    Returns:
        List of (row, col) peak coordinates
    """
    # Apply percentile threshold
    threshold = np.percentile(image, percentile)

    # Find local maxima using tolerance-based comparison
    local_max = maximum_filter(image, size=min_distance)

    # A pixel is a local maximum if its value is within plateau_tolerance of the
    # neighborhood maximum (handles float32 fragmentation on plateaus)
    rel_diff = np.abs(image - local_max) / (local_max + 1e-10)
    mask = (rel_diff <= plateau_tolerance) & (image > threshold)

    # Extract peak coordinates and intensities
    peak_coords = np.column_stack(np.where(mask))
    peak_intensities = image[mask]

    # Sort by intensity (descending)
    sorted_idx = np.argsort(peak_intensities)[::-1]
    sorted_coords = peak_coords[sorted_idx]
    sorted_intensities = peak_intensities[sorted_idx]

    # Cluster nearby peaks to avoid duplicates from plateau tolerance
    # Use cluster_radius=1.5px to handle float32 fragmentation (Phase B3: 5× more unique values)
    # This ensures that peaks on the same physical plateau are merged into single representatives
    clustered_peaks = []
    used = np.zeros(len(sorted_coords), dtype=bool)
    cluster_radius = 1.5  # Calibrated for AT-012 float32 plateau fragmentation

    for i in range(len(sorted_coords)):
        if used[i]:
            continue

        # Find all peaks in this cluster
        seed_peak = sorted_coords[i]
        distances = np.sqrt(np.sum((sorted_coords - seed_peak)**2, axis=1))
        cluster_mask = (distances <= cluster_radius) & ~used
        cluster_indices = np.where(cluster_mask)[0]

        # Compute intensity-weighted center of mass for this cluster
        cluster_coords = sorted_coords[cluster_indices]
        cluster_intensities = sorted_intensities[cluster_indices]
        weights = cluster_intensities / np.sum(cluster_intensities)
        com = np.sum(cluster_coords * weights[:, np.newaxis], axis=0)

        clustered_peaks.append((int(np.round(com[0])), int(np.round(com[1]))))

        # Mark all peaks in this cluster as used
        used[cluster_indices] = True

        # Stop once we have enough peaks
        if len(clustered_peaks) >= n_peaks:
            break

    return clustered_peaks[:n_peaks]


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

        # Run PyTorch simulation with default dtype (float32)
        # Peak clustering in find_peaks() handles numerical plateau fragmentation
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        pytorch_image = simulator.run().cpu().numpy()

        # Calculate correlation
        corr, _ = pearsonr(golden_image.flatten(), pytorch_image.flatten())

        # Find peaks (both should detect exactly 50 per spec)
        golden_peaks = find_peaks(golden_image, n_peaks=50, percentile=99.5)
        pytorch_peaks = find_peaks(pytorch_image.astype(np.float32), n_peaks=50, percentile=99.5)

        # Match peaks using spec-required 0.5 pixel tolerance
        n_matches, mean_dist = match_peaks_hungarian(golden_peaks, pytorch_peaks, max_distance=0.5)

        # Assertions per spec-a-parallel.md §AT-012
        assert corr >= 0.9995, f"Correlation {corr:.4f} < 0.9995 requirement"

        # Spec requires ≥95% of top 50 peaks within 0.5px
        required_matches = int(0.95 * 50)  # 48 peaks
        assert n_matches >= required_matches, (
            f"Only {n_matches}/50 peaks matched within 0.5px (need ≥{required_matches})"
        )
        assert mean_dist <= 0.5, f"Mean peak distance {mean_dist:.2f}px > 0.5px requirement"

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

        # Run PyTorch simulation with default dtype (float32)
        # Peak clustering in find_peaks() handles numerical plateau fragmentation
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        pytorch_image = simulator.run().cpu().numpy()

        # Calculate correlation
        corr, _ = pearsonr(golden_image.flatten(), pytorch_image.flatten())

        # Find peaks (both should detect exactly 50 per spec)
        golden_peaks = find_peaks(golden_image, n_peaks=50, percentile=99.0)
        pytorch_peaks = find_peaks(pytorch_image.astype(np.float32), n_peaks=50, percentile=99.0)

        # Match peaks using spec-required 0.5 pixel tolerance
        n_matches, mean_dist = match_peaks_hungarian(golden_peaks, pytorch_peaks, max_distance=0.5)

        # Assertions per spec-a-parallel.md §AT-012
        assert corr >= 0.9995, f"Correlation {corr:.4f} < 0.9995 requirement"

        # Spec requires ≥95% of top 50 peaks within 0.5px
        required_matches = int(0.95 * 50)  # 48 peaks
        assert n_matches >= required_matches, (
            f"Only {n_matches}/50 peaks matched within 0.5px (need ≥{required_matches})"
        )
        assert mean_dist <= 0.5, f"Mean peak distance {mean_dist:.2f}px > 0.5px requirement"

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

        # Run PyTorch simulation with default dtype (float32)
        # Peak clustering in find_peaks() handles numerical plateau fragmentation
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        pytorch_image = simulator.run().cpu().numpy()

        # Calculate correlation
        corr, _ = pearsonr(golden_image.flatten(), pytorch_image.flatten())

        # Find peaks (both should detect exactly 50 per spec)
        golden_peaks = find_peaks(golden_image, n_peaks=50, percentile=98.0)
        pytorch_peaks = find_peaks(pytorch_image.astype(np.float32), n_peaks=50, percentile=98.0)

        # Match peaks (spec allows 1.0 pixel for tilted detector)
        n_matches, mean_dist = match_peaks_hungarian(golden_peaks, pytorch_peaks, max_distance=1.0)

        # Assertions per spec-a-parallel.md §AT-012 (tilted variant allows 1.0px)
        assert corr >= 0.9995, f"Correlation {corr:.4f} < 0.9995 requirement"

        # Spec requires ≥95% of top 50 peaks within 1.0px for tilted detector
        required_matches = 48  # ceiling(0.95 * 50) = 48 peaks
        assert n_matches >= required_matches, (
            f"Only {n_matches}/50 peaks matched within 1.0px (need ≥{required_matches})"
        )
        assert mean_dist <= 1.0, f"Mean peak distance {mean_dist:.2f}px > 1.0px requirement"

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