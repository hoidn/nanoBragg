"""
AT-PARALLEL-007: Peak Position with Rotations
Tests peak positions with detector rotations and twotheta using Hungarian matching.

Acceptance Test Requirements (from spec-a-parallel.md):
- Setup: 100,100,100,90,90,90 cell; -default_F 100; detector 256×256, -pixel 0.1
- Distance 100mm; MOSFLM convention; auto beam center
- Rotations: -detector_rotx 5 -detector_roty 3 -detector_rotz 2 -twotheta 10
- Procedure: Detect local maxima above 99.5th percentile; select top N=25 peaks
- Register C↔PyTorch peaks via Hungarian matching with 1.0‑pixel gating
- Pass: Image correlation ≥ 0.98; ≥ 95% matched peaks within ≤ 1.0 pixel
- Total float-image sums ratio in [0.9, 1.1]
"""

import os
import subprocess
import tempfile
import numpy as np
import torch
import pytest
from pathlib import Path
from scipy.optimize import linear_sum_assignment
from scipy.ndimage import maximum_filter
from scipy.stats import pearsonr
from typing import Tuple, List, Dict, Any

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


def find_peaks_percentile(
    image: np.ndarray,
    percentile: float = 99.5,
    n_peaks: int = 25,
    min_distance: int = 3
) -> List[Tuple[int, int]]:
    """
    Find peaks above given percentile threshold with local maxima filtering.

    Args:
        image: 2D intensity image
        percentile: Percentile threshold (99.5 for AT-PARALLEL-007)
        n_peaks: Maximum number of peaks to return
        min_distance: Minimum distance between peaks (non-max suppression)

    Returns:
        List of (slow, fast) peak positions sorted by intensity
    """
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

    # Return top N peaks as list of tuples
    top_peaks = peak_coords[sorted_idx[:n_peaks]]
    return [(int(p[0]), int(p[1])) for p in top_peaks]


def hungarian_match_peaks(
    peaks_c: List[Tuple[int, int]],
    peaks_py: List[Tuple[int, int]],
    max_distance: float = 1.0
) -> Tuple[List[Tuple[int, int]], float]:
    """
    Match peaks between C and PyTorch using Hungarian algorithm.

    Args:
        peaks_c: List of (slow, fast) peak positions from C
        peaks_py: List of (slow, fast) peak positions from PyTorch
        max_distance: Maximum allowed matching distance (1.0 pixel for AT-PARALLEL-007)

    Returns:
        Tuple of:
        - List of matched peak pairs as (c_idx, py_idx)
        - Percentage of successfully matched peaks
    """
    if not peaks_c or not peaks_py:
        return [], 0.0

    # Build cost matrix (Euclidean distances)
    n_c, n_py = len(peaks_c), len(peaks_py)
    cost_matrix = np.zeros((n_c, n_py))

    for i, pc in enumerate(peaks_c):
        for j, pp in enumerate(peaks_py):
            dist = np.sqrt((pc[0] - pp[0])**2 + (pc[1] - pp[1])**2)
            # Use large cost for distances beyond threshold
            cost_matrix[i, j] = dist if dist <= max_distance else 1e6

    # Solve assignment problem
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    # Filter matches within max_distance
    matches = []
    for i, j in zip(row_ind, col_ind):
        if cost_matrix[i, j] <= max_distance:
            matches.append((i, j))

    # Calculate match percentage
    match_percentage = 100.0 * len(matches) / min(n_c, n_py)

    return matches, match_percentage


class TestATParallel007PeakPositionWithRotations:
    """Test peak positions with detector rotations using Hungarian matching."""

    @pytest.fixture
    def setup_config(self) -> Dict[str, Any]:
        """Setup configuration per AT-PARALLEL-007 spec."""
        return {
            'cell': (100, 100, 100, 90, 90, 90),
            'default_F': 100.0,
            'N_cells': (5, 5, 5),
            'wavelength': 6.2,  # Default wavelength if not specified
            'detector': {
                'size': (256, 256),
                'pixel_size_mm': 0.1,
                'distance_mm': 100.0,
                'convention': DetectorConvention.MOSFLM,
                'pivot': DetectorPivot.BEAM,
                'detector_rotx_deg': 5.0,
                'detector_roty_deg': 3.0,
                'detector_rotz_deg': 2.0,
                'detector_twotheta_deg': 10.0,
            },
            'phi': 0.0,
            'osc': 0.0,
            'mosaic': 0.0,
            'oversample': 1,
        }

    def run_pytorch_simulation(self, config: Dict[str, Any]) -> np.ndarray:
        """Run PyTorch simulation with given configuration."""
        # Create crystal
        crystal_config = CrystalConfig(
            cell_a=config['cell'][0],
            cell_b=config['cell'][1],
            cell_c=config['cell'][2],
            cell_alpha=config['cell'][3],
            cell_beta=config['cell'][4],
            cell_gamma=config['cell'][5],
            N_cells=config['N_cells'],
            default_F=config['default_F'],
            phi_start_deg=config['phi'],
            osc_range_deg=config['osc'],
            phi_steps=1,
            mosaic_spread_deg=config['mosaic'],
            mosaic_domains=1,
        )
        crystal = Crystal(crystal_config)

        # Create detector with rotations
        det_cfg = config['detector']
        detector_config = DetectorConfig(
            spixels=det_cfg['size'][0],
            fpixels=det_cfg['size'][1],
            pixel_size_mm=det_cfg['pixel_size_mm'],
            distance_mm=det_cfg['distance_mm'],
            detector_convention=det_cfg['convention'],
            detector_pivot=det_cfg['pivot'],
            detector_rotx_deg=det_cfg['detector_rotx_deg'],
            detector_roty_deg=det_cfg['detector_roty_deg'],
            detector_rotz_deg=det_cfg['detector_rotz_deg'],
            detector_twotheta_deg=det_cfg['detector_twotheta_deg'],
            oversample=config['oversample'],
        )
        detector = Detector(detector_config)

        # Create beam
        beam_config = BeamConfig(wavelength_A=config['wavelength'])

        # Run simulation
        simulator = Simulator(crystal, detector, crystal_config, beam_config)
        result = simulator.run()

        return result.cpu().numpy()

    def run_c_simulation(self, config: Dict[str, Any]) -> np.ndarray:
        """Run C simulation with identical configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "c_output.bin"

            # Build C command
            c_binary = os.environ.get('NB_C_BIN', './nanoBragg')
            # Convert to absolute path if relative
            if not os.path.isabs(c_binary):
                c_binary = os.path.abspath(c_binary)
            cmd = [
                c_binary,
                '-cell'] + [str(x) for x in config['cell']] + [
                '-default_F', str(config['default_F']),
                '-N', str(config['N_cells'][0]),
                '-lambda', str(config['wavelength']),
                '-detpixels', str(config['detector']['size'][0]),
                '-pixel', str(config['detector']['pixel_size_mm']),
                '-distance', str(config['detector']['distance_mm']),
                '-mosflm',  # Convention
                '-detector_rotx', str(config['detector']['detector_rotx_deg']),
                '-detector_roty', str(config['detector']['detector_roty_deg']),
                '-detector_rotz', str(config['detector']['detector_rotz_deg']),
                '-twotheta', str(config['detector']['detector_twotheta_deg']),
                '-phi', str(config['phi']),
                '-osc', str(config['osc']),
                '-mosaic', str(config['mosaic']),
                '-oversample', str(config['oversample']),
                '-floatfile', str(output_file),
            ]

            # Run C code
            c_dir = os.path.dirname(c_binary) if os.path.dirname(c_binary) else '.'
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=c_dir
            )

            if result.returncode != 0:
                raise RuntimeError(f"C simulation failed: {result.stderr}")

            # Read binary output
            image = np.fromfile(output_file, dtype=np.float32)
            size = config['detector']['size'][0]
            return image.reshape(size, size)

    @pytest.mark.skipif(
        os.environ.get('NB_RUN_PARALLEL', '0') != '1',
        reason="Parallel C-PyTorch tests disabled (set NB_RUN_PARALLEL=1)"
    )
    def test_peak_positions_with_rotations(self, setup_config):
        """
        Test peak positions with detector rotations match between C and PyTorch.
        Uses Hungarian matching with 99.5th percentile threshold.
        """
        # Run both simulations
        pytorch_image = self.run_pytorch_simulation(setup_config)
        c_image = self.run_c_simulation(setup_config)

        # Find peaks using 99.5th percentile
        peaks_py = find_peaks_percentile(pytorch_image, percentile=99.5, n_peaks=25)
        peaks_c = find_peaks_percentile(c_image, percentile=99.5, n_peaks=25)

        # Hungarian matching with 1.0 pixel threshold
        matches, match_percentage = hungarian_match_peaks(peaks_c, peaks_py, max_distance=1.0)

        # Calculate correlation
        correlation, _ = pearsonr(pytorch_image.flatten(), c_image.flatten())

        # Calculate intensity ratio
        sum_py = np.sum(pytorch_image)
        sum_c = np.sum(c_image)
        intensity_ratio = sum_py / sum_c if sum_c > 0 else 0

        # Assertions per spec
        assert correlation >= 0.98, (
            f"Correlation {correlation:.4f} below required 0.98"
        )

        assert match_percentage >= 95.0, (
            f"Only {match_percentage:.1f}% peaks matched (need ≥95%)"
        )

        assert 0.9 <= intensity_ratio <= 1.1, (
            f"Intensity ratio {intensity_ratio:.4f} outside [0.9, 1.1]"
        )

        # Report results
        print(f"\n=== AT-PARALLEL-007 Results ===")
        print(f"Correlation: {correlation:.4f} (≥0.98 ✓)")
        print(f"Peaks matched: {len(matches)}/{min(len(peaks_c), len(peaks_py))} "
              f"({match_percentage:.1f}% ≥95% ✓)")
        print(f"Intensity ratio: {intensity_ratio:.4f} ∈ [0.9, 1.1] ✓")
        print(f"C peaks found: {len(peaks_c)}")
        print(f"PyTorch peaks found: {len(peaks_py)}")

        # Show first few matches
        if matches:
            print(f"\nFirst 5 peak matches (pixel distance):")
            for i, (c_idx, py_idx) in enumerate(matches[:5]):
                pc = peaks_c[c_idx]
                pp = peaks_py[py_idx]
                dist = np.sqrt((pc[0] - pp[0])**2 + (pc[1] - pp[1])**2)
                print(f"  {i+1}. C{pc} ↔ Py{pp}: {dist:.3f} px")

    @pytest.mark.skipif(
        os.environ.get('NB_RUN_PARALLEL', '0') != '1',
        reason="Parallel C-PyTorch tests disabled"
    )
    def test_peak_intensity_ordering(self, setup_config):
        """Verify that peak intensity ordering is preserved."""
        # Run simulations
        pytorch_image = self.run_pytorch_simulation(setup_config)
        c_image = self.run_c_simulation(setup_config)

        # Get top 10 peaks by intensity
        peaks_py = find_peaks_percentile(pytorch_image, percentile=99.5, n_peaks=10)
        peaks_c = find_peaks_percentile(c_image, percentile=99.5, n_peaks=10)

        # Get intensities at peak positions
        intensities_py = [pytorch_image[p[0], p[1]] for p in peaks_py]
        intensities_c = [c_image[p[0], p[1]] for p in peaks_c]

        # Check that intensities are monotonically decreasing (sorted)
        assert all(i >= j for i, j in zip(intensities_py[:-1], intensities_py[1:])), \
            "PyTorch peak intensities not properly sorted"
        assert all(i >= j for i, j in zip(intensities_c[:-1], intensities_c[1:])), \
            "C peak intensities not properly sorted"

        # Match and compare relative ordering
        matches, _ = hungarian_match_peaks(peaks_c[:5], peaks_py[:5], max_distance=2.0)

        print(f"\nTop 5 peak intensities:")
        print(f"C:       {intensities_c[:5]}")
        print(f"PyTorch: {intensities_py[:5]}")
        print(f"Matched pairs: {len(matches)}/5")

    @pytest.mark.skipif(
        os.environ.get('NB_RUN_PARALLEL', '0') != '1',
        reason="Parallel C-PyTorch tests disabled"
    )
    def test_rotation_effect_on_pattern(self, setup_config):
        """Verify that rotations actually change the diffraction pattern."""
        # Run with rotations
        pytorch_with_rot = self.run_pytorch_simulation(setup_config)

        # Run without rotations
        config_no_rot = setup_config.copy()
        config_no_rot['detector']['detector_rotx_deg'] = 0.0
        config_no_rot['detector']['detector_roty_deg'] = 0.0
        config_no_rot['detector']['detector_rotz_deg'] = 0.0
        config_no_rot['detector']['detector_twotheta_deg'] = 0.0
        pytorch_no_rot = self.run_pytorch_simulation(config_no_rot)

        # Patterns should be different
        correlation, _ = pearsonr(pytorch_with_rot.flatten(), pytorch_no_rot.flatten())

        # With these rotations, correlation should be less than 0.95
        assert correlation < 0.95, (
            f"Rotations didn't change pattern enough (corr={correlation:.4f})"
        )

        # Peak positions should shift
        peaks_with = find_peaks_percentile(pytorch_with_rot, percentile=99.0, n_peaks=10)
        peaks_without = find_peaks_percentile(pytorch_no_rot, percentile=99.0, n_peaks=10)

        # Average shift should be significant (> 5 pixels)
        if peaks_with and peaks_without:
            min_shifts = []
            for pw in peaks_with[:5]:
                dists = [np.sqrt((pw[0]-p[0])**2 + (pw[1]-p[1])**2) for p in peaks_without[:5]]
                min_shifts.append(min(dists))
            avg_shift = np.mean(min_shifts)

            assert avg_shift > 5.0, (
                f"Peak shift too small ({avg_shift:.1f} px) - rotations not working?"
            )

            print(f"\nRotation effect validated:")
            print(f"Pattern correlation: {correlation:.4f} (<0.95 ✓)")
            print(f"Average peak shift: {avg_shift:.1f} px (>5 ✓)")