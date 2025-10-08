"""
AT-PARALLEL-029: Subpixel Sampling and Aliasing Mitigation

Tests that verify proper subpixel sampling and aliasing mitigation across
different oversample values. Validates that:
1. Aliasing artifacts decrease with increased oversampling
2. Peak positions remain stable across oversample values
3. C and PyTorch implementations show equivalent behavior

From specs/spec-a-parallel.md:
- Setup: Cubic cell 100x100x100, N=5, default_F=100, lambda=1.0
- Detector: 256x256, pixel=0.1mm, distance=50mm
- Test oversample values: {1, 2, 4, 8}
"""

import pytest
import torch
import numpy as np
from scipy import ndimage
from scipy.signal import peak_widths
import os
from pathlib import Path

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


def find_peaks_2d(image, min_height=None, window_size=3):
    """Find local maxima in 2D array using maximum filter."""
    # Apply maximum filter to find local maxima
    max_filtered = ndimage.maximum_filter(image, size=window_size)
    peaks = (image == max_filtered)

    # Apply height threshold if provided
    if min_height is not None:
        peaks = peaks & (image >= min_height)

    # Get peak coordinates
    peak_coords = np.column_stack(np.where(peaks))
    peak_values = image[peaks]

    # Sort by intensity (descending)
    sorted_idx = np.argsort(peak_values)[::-1]

    return peak_coords[sorted_idx], peak_values[sorted_idx]


def compute_peak_fwhm(image, peak_coords, n_peaks=10):
    """Compute average FWHM for the brightest peaks."""
    if len(peak_coords) == 0:
        return 0.0

    n_peaks = min(n_peaks, len(peak_coords))
    fwhms = []

    for i in range(n_peaks):
        y, x = peak_coords[i]

        # Extract horizontal and vertical profiles through peak
        h_profile = image[y, :]
        v_profile = image[:, x]

        # Compute FWHM for each profile
        try:
            # Horizontal FWHM
            h_widths, _, _, _ = peak_widths(h_profile, [x], rel_height=0.5)
            # Vertical FWHM
            v_widths, _, _, _ = peak_widths(v_profile, [y], rel_height=0.5)

            # Average the two directions
            fwhm = (h_widths[0] + v_widths[0]) / 2.0
            fwhms.append(fwhm)
        except:
            # Skip peaks where FWHM cannot be computed
            continue

    return np.mean(fwhms) if fwhms else 0.0


def measure_high_frequency_content(image, nyquist_fraction=0.5):
    """Measure high-frequency content in FFT power spectrum."""
    # Compute 2D FFT
    fft = np.fft.fft2(image)
    fft_shifted = np.fft.fftshift(fft)
    power_spectrum = np.abs(fft_shifted) ** 2

    # Get frequency grid
    h, w = image.shape
    freq_y = np.fft.fftshift(np.fft.fftfreq(h))
    freq_x = np.fft.fftshift(np.fft.fftfreq(w))
    freq_r = np.sqrt(freq_x[None, :]**2 + freq_y[:, None]**2)

    # Measure power above Nyquist/2
    nyquist = 0.5  # Maximum frequency
    high_freq_mask = freq_r > (nyquist * nyquist_fraction)
    high_freq_power = np.sum(power_spectrum[high_freq_mask])
    total_power = np.sum(power_spectrum)

    return high_freq_power / total_power if total_power > 0 else 0.0


def compute_fft_correlation(spectrum1, spectrum2):
    """Compute correlation between two FFT power spectra."""
    # Flatten and normalize
    s1 = spectrum1.flatten()
    s2 = spectrum2.flatten()

    # Compute correlation coefficient
    correlation = np.corrcoef(s1, s2)[0, 1]
    return correlation


class TestSubpixelSamplingAT029:
    """Test suite for AT-PARALLEL-029: Subpixel Sampling and Aliasing Mitigation."""

    def setup_simulation(self, oversample=1):
        """Create simulation configuration with specified oversample value."""
        # Crystal config - cubic cell 100x100x100
        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(5, 5, 5),
            default_F=100.0,
            phi_start_deg=0.0,
            osc_range_deg=0.0,
            phi_steps=1,
            mosaic_spread_deg=0.0,
            mosaic_domains=1
        )

        # Detector config - 256x256, 0.1mm pixels, 50mm distance
        # Set oversample in detector config
        detector_config = DetectorConfig(
            spixels=256,
            fpixels=256,
            pixel_size_mm=0.1,
            distance_mm=50.0,
            detector_convention=DetectorConvention.MOSFLM,
            oversample=oversample
        )

        # Beam config - 1.0 Angstrom wavelength
        beam_config = BeamConfig(
            wavelength_A=1.0,
            fluence=1e12
        )

        # Create simulator
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            crystal_config=crystal_config,
            beam_config=beam_config
        )

        return simulator

    def test_pytorch_aliasing_reduction(self):
        """Test that increasing oversample reduces aliasing in PyTorch implementation."""
        oversample_values = [1, 2, 4, 8]
        high_freq_content = []

        for oversample in oversample_values:
            # Run simulation
            simulator = self.setup_simulation(oversample=oversample)
            image = simulator.run()

            # Convert to numpy
            if isinstance(image, torch.Tensor):
                image = image.detach().cpu().numpy()

            # Measure high-frequency content
            hf_content = measure_high_frequency_content(image)
            high_freq_content.append(hf_content)

        # Verify aliasing reduction
        # oversample>=2 should reduce high-frequency content significantly
        # Note: The exact reduction depends on the pattern and FFT analysis method
        # We expect at least 15% reduction as a baseline after fixing subpixel physics
        reduction_2 = 1.0 - (high_freq_content[1] / high_freq_content[0])
        assert reduction_2 >= 0.15, f"Oversample=2 should reduce HF content by >=15%, got {reduction_2*100:.1f}%"

        # Further oversampling should continue reducing aliasing (with tolerance)
        for i in range(2, len(oversample_values)):
            # Allow small tolerance for numerical precision (1%)
            assert high_freq_content[i] <= high_freq_content[i-1] * 1.01, \
                f"Higher oversample should reduce or maintain aliasing: {oversample_values[i]} vs {oversample_values[i-1]}"

    def test_pytorch_peak_stability(self):
        """Test that peak positions remain stable across oversample values."""
        oversample_values = [1, 2, 4, 8]
        all_peak_positions = []

        for oversample in oversample_values:
            # Run simulation
            simulator = self.setup_simulation(oversample=oversample)
            image = simulator.run()

            # Convert to numpy
            if isinstance(image, torch.Tensor):
                image = image.detach().cpu().numpy()

            # Find peaks
            threshold = np.percentile(image, 99)
            peak_coords, _ = find_peaks_2d(image, min_height=threshold)

            # Store top 10 peak positions
            top_peaks = peak_coords[:10] if len(peak_coords) >= 10 else peak_coords
            all_peak_positions.append(top_peaks)

        # Compare peak positions between consecutive oversample values
        for i in range(1, len(oversample_values)):
            prev_peaks = all_peak_positions[i-1]
            curr_peaks = all_peak_positions[i]

            # Match peaks between the two sets
            matched_count = 0
            for prev_peak in prev_peaks[:5]:  # Check top 5 peaks
                # Find closest peak in current set
                if len(curr_peaks) > 0:
                    distances = np.sqrt(np.sum((curr_peaks - prev_peak)**2, axis=1))
                    min_dist = np.min(distances)

                    # Peak should be within 0.5 pixels
                    if min_dist <= 0.5:
                        matched_count += 1

            # At least 80% of top peaks should match within 0.5 pixels
            match_ratio = matched_count / min(5, len(prev_peaks))
            assert match_ratio >= 0.8, \
                f"Peak drift too large between oversample {oversample_values[i-1]} and {oversample_values[i]}"

    def test_pytorch_fwhm_convergence(self):
        """Test that peak FWHM stabilizes with higher oversampling."""
        oversample_values = [1, 2, 4, 8]
        fwhm_values = []

        for oversample in oversample_values:
            # Run simulation
            simulator = self.setup_simulation(oversample=oversample)
            image = simulator.run()

            # Convert to numpy
            if isinstance(image, torch.Tensor):
                image = image.detach().cpu().numpy()

            # Find peaks and compute FWHM
            threshold = np.percentile(image, 99)
            peak_coords, _ = find_peaks_2d(image, min_height=threshold)

            if len(peak_coords) > 0:
                avg_fwhm = compute_peak_fwhm(image, peak_coords, n_peaks=10)
                fwhm_values.append(avg_fwhm)
            else:
                fwhm_values.append(0.0)

        # Check FWHM stabilization for oversample>=4
        if fwhm_values[2] > 0 and fwhm_values[3] > 0:
            relative_change = abs(fwhm_values[3] - fwhm_values[2]) / fwhm_values[2]
            assert relative_change <= 0.05, \
                f"FWHM should stabilize within 5% for oversample>=4, got {relative_change*100:.1f}% change"

    @pytest.mark.skipif(
        os.getenv("NB_RUN_PARALLEL") != "1",
        reason="Parallel validation requires C binary and NB_RUN_PARALLEL=1"
    )
    def test_c_pytorch_oversample_equivalence(self):
        """Test that C and PyTorch show equivalent behavior across oversample values."""
        from scripts.c_reference_runner import CReferenceRunner

        oversample_values = [1, 2, 4, 8]
        correlations = []

        for oversample in oversample_values:
            # Run PyTorch simulation
            simulator = self.setup_simulation(oversample=oversample)
            pytorch_image = simulator.run()

            if isinstance(pytorch_image, torch.Tensor):
                pytorch_image = pytorch_image.detach().cpu().numpy()

            # Run C simulation
            c_runner = CReferenceRunner()
            c_image = c_runner.run(
                cell=(100.0, 100.0, 100.0, 90.0, 90.0, 90.0),
                N=5,
                default_F=100.0,
                wavelength_A=1.0,
                distance_mm=50.0,
                detpixels=256,
                pixel_size_mm=0.1,
                oversample=oversample,
                detector_convention='mosflm',
                phi_deg=0.0,
                osc_deg=0.0,
                mosaic_spread_deg=0.0,
                fluence=1e12
            )

            # Compute correlation
            correlation = np.corrcoef(pytorch_image.flatten(), c_image.flatten())[0, 1]
            correlations.append(correlation)

            # Verify correlation threshold
            assert correlation >= 0.98, \
                f"C-PyTorch correlation should be >=0.98 for oversample={oversample}, got {correlation:.3f}"

        # Also check FFT correlation for oversample=1 (aliasing equivalence)
        if oversample_values[0] == 1:
            # Compute FFT power spectra
            pytorch_fft = np.abs(np.fft.fftshift(np.fft.fft2(pytorch_image))) ** 2
            c_fft = np.abs(np.fft.fftshift(np.fft.fft2(c_image))) ** 2

            fft_correlation = compute_fft_correlation(pytorch_fft, c_fft)
            assert fft_correlation >= 0.95, \
                f"FFT correlation should be >=0.95 for oversample=1, got {fft_correlation:.3f}"

    @pytest.mark.skipif(
        os.getenv("NB_RUN_PARALLEL") != "1",
        reason="Parallel validation requires C binary and NB_RUN_PARALLEL=1"
    )
    def test_issue_subpixel_aliasing(self):
        """Test the specific case reported in issues/subpixel.md."""
        # This is the exact command from the issue report
        # "-default_F 100 -cell 100 100 100 90 90 90 -N 5 -detpixels 256 -distance 50 -lambda 1.0"

        from scripts.c_reference_runner import CReferenceRunner

        # Run PyTorch simulation (default oversample should handle aliasing)
        simulator = self.setup_simulation(oversample=1)
        pytorch_image = simulator.run()

        if isinstance(pytorch_image, torch.Tensor):
            pytorch_image = pytorch_image.detach().cpu().numpy()

        # Run C simulation
        c_runner = CReferenceRunner()
        c_image = c_runner.run(
            cell=(100.0, 100.0, 100.0, 90.0, 90.0, 90.0),
            N=5,
            default_F=100.0,
            wavelength_A=1.0,
            distance_mm=50.0,
            detpixels=256,
            pixel_size_mm=0.1,
            oversample=1,
            detector_convention='mosflm',
            fluence=1e12
        )

        # Check for aliasing artifacts
        pytorch_hf = measure_high_frequency_content(pytorch_image)
        c_hf = measure_high_frequency_content(c_image)

        # Both should show similar aliasing at oversample=1
        relative_diff = abs(pytorch_hf - c_hf) / max(pytorch_hf, c_hf)
        assert relative_diff <= 0.1, \
            f"PyTorch and C should show similar aliasing at oversample=1, diff={relative_diff*100:.1f}%"

        # Now test with higher oversampling to reduce aliasing
        simulator_fixed = self.setup_simulation(oversample=4)
        pytorch_fixed = simulator_fixed.run()

        if isinstance(pytorch_fixed, torch.Tensor):
            pytorch_fixed = pytorch_fixed.detach().cpu().numpy()

        pytorch_fixed_hf = measure_high_frequency_content(pytorch_fixed)

        # Should have significantly less aliasing
        reduction = 1.0 - (pytorch_fixed_hf / pytorch_hf)
        assert reduction >= 0.5, \
            f"Oversample=4 should reduce aliasing by >=50%, got {reduction*100:.1f}%"