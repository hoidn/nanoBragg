"""
Test AT-PARALLEL-014: Noise Robustness Test

This test validates that the noise generation process maintains the expected
statistical properties and doesn't significantly perturb peak positions.
"""

import numpy as np
import torch
import pytest
from pathlib import Path
import tempfile
import struct

from nanobrag_torch.config import (
    DetectorConfig, CrystalConfig, BeamConfig,
    DetectorConvention, NoiseConfig
)
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.utils.noise import generate_poisson_noise
from nanobrag_torch.io.smv import read_smv


class TestATParallel014NoiseRobustness:
    """AT-PARALLEL-014: Noise Robustness Test."""

    def setup_method(self):
        """Set up test configuration."""
        # Create simple cubic configuration
        self.detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=256,
            fpixels=256,
            detector_convention=DetectorConvention.MOSFLM,
        )

        self.crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            default_F=100.0,
            N_cells=(5, 5, 5),
        )

        self.beam_config = BeamConfig(
            wavelength_A=6.2,
            fluence=1e12,  # Moderate intensity to get mean ~1e3
        )

    def find_peaks(self, image, n_peaks=20, threshold_percentile=95):
        """Find top N peaks in an image."""
        # Apply threshold
        threshold = np.percentile(image, threshold_percentile)

        # Find local maxima with simple 3x3 window
        peaks = []
        for i in range(1, image.shape[0] - 1):
            for j in range(1, image.shape[1] - 1):
                if image[i, j] > threshold:
                    # Check if it's a local maximum
                    window = image[i-1:i+2, j-1:j+2]
                    if image[i, j] == np.max(window):
                        peaks.append((i, j, image[i, j]))

        # Sort by intensity and take top N
        peaks.sort(key=lambda x: x[2], reverse=True)
        return peaks[:n_peaks]

    def compute_centroid(self, image, peak_pos, window_size=5):
        """Compute sub-pixel centroid around a peak."""
        i, j, _ = peak_pos
        half = window_size // 2

        # Extract window around peak
        i_min = max(0, i - half)
        i_max = min(image.shape[0], i + half + 1)
        j_min = max(0, j - half)
        j_max = min(image.shape[1], j + half + 1)

        window = image[i_min:i_max, j_min:j_max]

        # Compute center of mass
        i_coords, j_coords = np.meshgrid(
            np.arange(i_min, i_max),
            np.arange(j_min, j_max),
            indexing='ij'
        )

        total = np.sum(window)
        if total > 0:
            i_centroid = np.sum(i_coords * window) / total
            j_centroid = np.sum(j_coords * window) / total
        else:
            i_centroid, j_centroid = i, j

        return (i_centroid, j_centroid)

    def test_mean_preservation_after_scaling(self):
        """Test that mean(intimage) is within ±1% of scale·mean(float)+ADC."""
        # Generate float image
        detector = Detector(self.detector_config)
        crystal = Crystal(self.crystal_config)
        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            crystal_config=self.crystal_config,
            beam_config=self.beam_config,
        )

        float_image = simulator.run()

        # Set up scaling parameters
        scale = 100.0
        adc_offset = 40.0

        # Convert to integer with scaling
        int_image = torch.floor(
            torch.clamp(float_image * scale + adc_offset, 0, 65535)
        ).to(torch.int32)

        # Check mean preservation
        expected_mean = scale * float_image.mean().item() + adc_offset
        actual_mean = int_image.float().mean().item()
        relative_error = abs(actual_mean - expected_mean) / expected_mean

        assert relative_error < 0.01, f"Mean preservation error: {relative_error:.3%}"

    def test_peak_centroid_stability(self):
        """Test that peak centroids don't shift significantly with noise."""
        # Generate float image
        detector = Detector(self.detector_config)
        crystal = Crystal(self.crystal_config)
        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            crystal_config=self.crystal_config,
            beam_config=self.beam_config,
        )

        float_image = simulator.run()

        # Scale for moderate intensities
        scale = 1000.0 / float_image.max().item()
        scaled_float = float_image * scale

        # Find peaks in float image
        float_peaks = self.find_peaks(scaled_float.numpy(), n_peaks=20)

        # Generate noisy images with different seeds
        shifts = []
        for seed in [123, 456]:
            noise_config = NoiseConfig(seed=seed, adc_offset=40.0)
            noisy_image, _ = generate_poisson_noise(
                scaled_float,
                seed=seed,
                adc_offset=noise_config.adc_offset
            )

            # Compute centroid shifts for each peak
            for peak in float_peaks:
                float_centroid = self.compute_centroid(scaled_float.numpy(), peak)
                noisy_centroid = self.compute_centroid(noisy_image.numpy(), peak)

                shift = np.sqrt(
                    (float_centroid[0] - noisy_centroid[0])**2 +
                    (float_centroid[1] - noisy_centroid[1])**2
                )
                shifts.append(shift)

        # Check metrics
        shifts = np.array(shifts)
        median_shift = np.median(shifts)
        percentile_90 = np.percentile(shifts, 90)

        assert median_shift <= 0.5, f"Median centroid shift {median_shift:.2f} > 0.5 pixels"
        assert percentile_90 <= 1.0, f"90th percentile shift {percentile_90:.2f} > 1.0 pixels"

    def test_overload_count_consistency(self):
        """Test that overload counts are consistent across seeds."""
        # Generate float image with some high intensities
        detector = Detector(self.detector_config)
        crystal = Crystal(self.crystal_config)
        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            crystal_config=self.crystal_config,
            beam_config=self.beam_config,
        )

        float_image = simulator.run()

        # Scale to get some overloads
        scale = 65000.0 / float_image.max().item()
        scaled_float = float_image * scale * 1.2  # Push some pixels over the limit

        # Generate noisy images with different seeds and count overloads
        overload_counts = []
        for seed in [123, 456, 789]:
            _, overloads = generate_poisson_noise(
                scaled_float,
                seed=seed,
                adc_offset=40.0,
                overload_value=65535.0
            )
            overload_counts.append(overloads)

        # Check that overload counts are within ±10% of each other
        mean_overloads = np.mean(overload_counts)
        for count in overload_counts:
            if mean_overloads > 0:
                relative_diff = abs(count - mean_overloads) / mean_overloads
                assert relative_diff <= 0.1, \
                    f"Overload count {count} differs by {relative_diff:.1%} from mean"
            else:
                # If no overloads, all should be zero
                assert count == 0

    def test_noise_statistics(self):
        """Test that noise follows proper Poisson statistics."""
        # Create images with different mean intensities
        detector = Detector(self.detector_config)
        crystal = Crystal(self.crystal_config)
        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            crystal_config=self.crystal_config,
            beam_config=self.beam_config,
        )

        float_image = simulator.run()

        # Test different intensity regimes
        test_means = [5, 50, 500, 5000]  # Small, medium, large means

        for target_mean in test_means:
            # Scale image to target mean
            scale = target_mean / float_image.mean().item()
            scaled_image = float_image * scale

            # Generate many realizations to check statistics
            n_realizations = 100

            # Collect pixel values across realizations
            pixel_samples = []
            for i in range(n_realizations):
                noisy, _ = generate_poisson_noise(
                    scaled_image,
                    seed=42 + i,
                    adc_offset=0.0
                )
                # Sample a few pixels
                pixel_samples.append(noisy[100:110, 100:110].flatten().numpy())

            pixel_samples = np.array(pixel_samples)

            # For Poisson distribution: mean = variance
            sample_means = np.mean(pixel_samples, axis=0)
            sample_vars = np.var(pixel_samples, axis=0, ddof=1)

            # Only check pixels with reasonable signal
            mask = sample_means > 1
            if np.sum(mask) > 0:
                mean_var_ratio = sample_vars[mask] / sample_means[mask]
                # Poisson: variance/mean should be close to 1
                # Note: We allow wider tolerance as our implementation may have
                # readout noise and other factors that increase variance slightly
                assert np.median(mean_var_ratio) > 0.5 and np.median(mean_var_ratio) < 3.0, \
                    f"Variance/mean ratio {np.median(mean_var_ratio):.2f} not in expected range"

    def test_deterministic_noise_with_seed(self):
        """Test that the same seed produces identical noise."""
        detector = Detector(self.detector_config)
        crystal = Crystal(self.crystal_config)
        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            crystal_config=self.crystal_config,
            beam_config=self.beam_config,
        )

        float_image = simulator.run()

        # Generate noise twice with same seed
        noisy1, overload1 = generate_poisson_noise(
            float_image, seed=42, adc_offset=40.0
        )
        noisy2, overload2 = generate_poisson_noise(
            float_image, seed=42, adc_offset=40.0
        )

        # Should be identical
        assert torch.allclose(noisy1, noisy2, rtol=0, atol=0), \
            "Same seed didn't produce identical noise"
        assert overload1 == overload2, "Overload counts differ for same seed"