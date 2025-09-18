"""
Test suite for AT-NOISE-001: Noise image generation and seeds

Acceptance Test Specification:
- Setup: Write -noisefile; set -seed; choose pixels with means <12, between 12 and 1e6, and >1e6.
- Expectation: For <12, use exact Poisson; for large means up to 1e6, use rejection sampling;
  for >1e6, use Gaussian approximation N(mean, variance=mean). Output reproducibility SHALL
  follow -seed; additive ADC and clipping SHALL be applied; overload count SHALL be reported.
"""

import pytest
import torch
import numpy as np
from src.nanobrag_torch.utils.noise import generate_poisson_noise
from src.nanobrag_torch.config import NoiseConfig


class TestATNoise001:
    """Test suite for AT-NOISE-001: Poisson noise generation with three regimes."""

    def test_small_mean_exact_poisson(self):
        """Test exact Poisson for means < 12."""
        # Create test data with small means
        mean = torch.tensor([1.0, 3.0, 5.0, 8.0, 10.0, 11.9])

        # Generate noise with fixed seed for reproducibility
        noisy, overload_count = generate_poisson_noise(
            mean,
            seed=42,
            adc_offset=0.0,  # Disable ADC for this test
            readout_noise=0.0,  # Disable readout noise
            overload_value=65535.0
        )

        # For small means, output should be discrete counts
        assert torch.all(noisy >= 0)
        assert noisy.dtype == torch.int32

        # Statistical test: mean should approximate input over many samples
        n_samples = 10000
        samples = torch.zeros(n_samples, len(mean))
        for i in range(n_samples):
            samples[i], _ = generate_poisson_noise(
                mean,
                seed=42 + i,
                adc_offset=0.0,
                readout_noise=0.0,
                overload_value=65535.0
            )

        # Check mean is close to input (within statistical error)
        sample_mean = samples.float().mean(dim=0)
        relative_error = torch.abs(sample_mean - mean) / mean
        assert torch.all(relative_error < 0.1), f"Mean error: {relative_error}"

        # Check variance approximates mean (Poisson property)
        sample_var = samples.float().var(dim=0)
        var_relative_error = torch.abs(sample_var - mean) / mean
        assert torch.all(var_relative_error < 0.2), f"Variance error: {var_relative_error}"

    def test_medium_mean_rejection_sampling(self):
        """Test rejection sampling for 12 <= mean <= 1e6."""
        # Create test data with medium means
        mean = torch.tensor([12.0, 50.0, 100.0, 1000.0, 10000.0, 100000.0, 999999.0])

        # Generate noise with fixed seed
        noisy, overload_count = generate_poisson_noise(
            mean,
            seed=123,
            adc_offset=0.0,
            readout_noise=0.0,
            overload_value=1e7  # High limit to avoid clipping
        )

        # Output should be integer counts
        assert torch.all(noisy >= 0)
        assert noisy.dtype == torch.int32

        # For larger means, check statistical properties with fewer samples
        n_samples = 1000
        samples = torch.zeros(n_samples, len(mean))
        for i in range(n_samples):
            samples[i], _ = generate_poisson_noise(
                mean,
                seed=123 + i,
                adc_offset=0.0,
                readout_noise=0.0,
                overload_value=1e7
            )

        # Check mean approximates input (looser tolerance for larger values)
        sample_mean = samples.float().mean(dim=0)
        relative_error = torch.abs(sample_mean - mean) / mean
        assert torch.all(relative_error < 0.05), f"Mean error: {relative_error}"

        # Variance should still approximate mean
        sample_var = samples.float().var(dim=0)
        var_relative_error = torch.abs(sample_var - mean) / mean
        assert torch.all(var_relative_error < 0.1), f"Variance error: {var_relative_error}"

    def test_large_mean_gaussian_approximation(self):
        """Test Gaussian approximation for mean > 1e6."""
        # Create test data with very large means
        mean = torch.tensor([1e6 + 1, 1e7, 1e8, 1e9])

        # Generate noise
        noisy, overload_count = generate_poisson_noise(
            mean,
            seed=456,
            adc_offset=0.0,
            readout_noise=0.0,
            overload_value=1e10  # Very high to avoid clipping
        )

        # For very large means, Poisson approaches Gaussian
        assert torch.all(noisy >= 0)
        assert noisy.dtype == torch.int32

        # Generate multiple samples to test Gaussian properties
        n_samples = 100
        samples = torch.zeros(n_samples, len(mean))
        for i in range(n_samples):
            samples[i], _ = generate_poisson_noise(
                mean,
                seed=456 + i,
                adc_offset=0.0,
                readout_noise=0.0,
                overload_value=1e10
            )

        # For Gaussian approximation, mean should be very close
        sample_mean = samples.float().mean(dim=0)
        relative_error = torch.abs(sample_mean - mean) / mean
        assert torch.all(relative_error < 0.01), f"Mean error: {relative_error}"

        # Standard deviation should be sqrt(mean)
        sample_std = samples.float().std(dim=0)
        expected_std = torch.sqrt(mean)
        std_relative_error = torch.abs(sample_std - expected_std) / expected_std
        assert torch.all(std_relative_error < 0.1), f"Std error: {std_relative_error}"

    def test_seed_reproducibility(self):
        """Test that same seed gives identical results."""
        mean = torch.tensor([5.0, 50.0, 500.0, 5000.0, 5e6])

        # Generate with seed 789
        noisy1, overload1 = generate_poisson_noise(mean, seed=789)
        noisy2, overload2 = generate_poisson_noise(mean, seed=789)

        # Should be identical
        assert torch.allclose(noisy1, noisy2)
        assert overload1 == overload2

        # Different seed should give different results
        noisy3, overload3 = generate_poisson_noise(mean, seed=790)
        assert not torch.allclose(noisy1, noisy3)

    def test_adc_and_clipping(self):
        """Test ADC offset addition and overload clipping."""
        mean = torch.tensor([100.0, 1000.0, 60000.0, 70000.0])

        # Generate with ADC offset and low overload value
        noisy, overload_count = generate_poisson_noise(
            mean,
            seed=321,
            adc_offset=40.0,
            readout_noise=3.0,
            overload_value=65535.0
        )

        # All values should have ADC offset added (minimum is ADC offset)
        # With readout noise, some values might be slightly below ADC offset
        # but should be clipped at 0
        assert torch.all(noisy >= 0)

        # Maximum should be clipped at overload value
        assert torch.all(noisy <= 65535)

        # Should have some overloads for high mean values
        assert overload_count > 0, "Should have overloads for high intensity pixels"

        # Test that values near overload are actually clipped
        high_mean = torch.tensor([65000.0, 66000.0, 70000.0])
        noisy_high, overload_high = generate_poisson_noise(
            high_mean,
            seed=654,
            adc_offset=40.0,
            readout_noise=0.0,  # No readout noise for clearer test
            overload_value=65535.0
        )

        # All should be at or below overload value
        assert torch.all(noisy_high <= 65535)
        assert overload_high > 0, "High intensity pixels should cause overloads"

    def test_all_regimes_in_single_image(self):
        """Test that all three regimes work correctly in a single image."""
        # Create an image with pixels in all three regimes
        mean = torch.tensor([
            0.5, 1.0, 5.0, 11.0,  # Small (exact Poisson)
            12.0, 100.0, 10000.0, 500000.0,  # Medium (rejection)
            1.1e6, 5e6, 1e7, 1e8  # Large (Gaussian)
        ])

        # Generate noise
        noisy, overload_count = generate_poisson_noise(
            mean,
            seed=999,
            adc_offset=40.0,
            readout_noise=3.0,
            overload_value=1e9  # High to avoid clipping affecting statistics
        )

        # All values should be valid
        assert torch.all(noisy >= 0)
        assert noisy.dtype == torch.int32

        # The noisy values should have reasonable relationship to input
        # (accounting for ADC offset)
        noisy_float = noisy.float() - 40.0  # Remove ADC offset

        # For very small means, noise can dominate
        # For larger means, should be within reasonable factor
        large_mean_mask = mean > 10
        if large_mean_mask.any():
            ratio = noisy_float[large_mean_mask] / mean[large_mean_mask]
            # Should be within order of magnitude
            assert torch.all(ratio > 0.1)
            assert torch.all(ratio < 10.0)

    def test_noise_config_integration(self):
        """Test integration with NoiseConfig dataclass."""
        config = NoiseConfig(
            seed=12345,
            adc_offset=40.0,
            readout_noise=3.0,
            overload_value=65535.0,
            generate_noise_image=True,
            intfile_scale=1.0
        )

        # Generate test data
        mean = torch.tensor([100.0, 1000.0, 10000.0]) * config.intfile_scale

        # Generate noise using config parameters
        noisy, overload_count = generate_poisson_noise(
            mean,
            seed=config.seed,
            adc_offset=config.adc_offset,
            readout_noise=config.readout_noise,
            overload_value=config.overload_value
        )

        # Basic sanity checks
        assert torch.all(noisy >= 0)
        assert torch.all(noisy <= config.overload_value)
        assert noisy.dtype == torch.int32

        # Test with different scale factor
        config.intfile_scale = 10.0
        mean_scaled = torch.tensor([100.0, 1000.0, 10000.0]) * config.intfile_scale

        noisy_scaled, _ = generate_poisson_noise(
            mean_scaled,
            seed=config.seed,
            adc_offset=config.adc_offset,
            readout_noise=config.readout_noise,
            overload_value=config.overload_value
        )

        # Scaled version should have higher values on average
        assert noisy_scaled.float().mean() > noisy.float().mean()