"""
Tests for divergence culling modes (-round_div and -square_div CLI flags).

These tests verify that:
1. -round_div (default) applies elliptical trimming to the divergence grid
2. -square_div disables elliptical trimming (uses full square grid)
3. The number of sources differs between round and square modes
4. The trimming is applied correctly based on normalized radius
"""

import numpy as np
import torch
import pytest
from typing import Tuple, List

from nanobrag_torch.utils.auto_selection import (
    SamplingParams,
    generate_sources_from_divergence_dispersion,
)


class TestDivergenceCullingModes:
    """Test suite for divergence culling modes as specified in spec-a-parallel.md."""

    def test_round_div_applies_elliptical_trimming(self):
        """
        Test that round_div=True applies elliptical trimming to divergence grid.
        Points outside the unit circle (normalized radius > 1) should be excluded.
        """
        # Create divergence parameters for a 5x5 grid
        hdiv_params = SamplingParams(
            count=5,
            range=2.0,  # 2 radians total range
            step=0.5,   # 0.5 radian steps
        )
        vdiv_params = SamplingParams(
            count=5,
            range=2.0,
            step=0.5,
        )
        # No dispersion for simplicity
        disp_params = SamplingParams(count=1, range=0.0, step=0.0)

        # Generate sources with round_div=True
        directions, weights, wavelengths = generate_sources_from_divergence_dispersion(
            hdiv_params=hdiv_params,
            vdiv_params=vdiv_params,
            disp_params=disp_params,
            central_wavelength_m=1e-10,  # 1 Angstrom
            round_div=True,  # Apply elliptical trimming
        )

        # With a 5x5 grid, the corner points should be excluded
        # The full grid would have 25 points, but with elliptical trimming
        # the 4 corners are excluded (they have normalized radius > 1)
        assert len(directions) < 25, "Elliptical trimming should exclude some points"

        # Specifically, for a 5x5 grid centered at origin with range 2.0:
        # The elliptical trimming is more aggressive than a simple corner exclusion
        # The actual implementation trims to 13 points for this configuration
        assert len(directions) == 13, f"Expected 13 points after trimming, got {len(directions)}"

    def test_square_div_uses_full_grid(self):
        """
        Test that round_div=False (square_div) uses the full square grid
        without any elliptical trimming.
        """
        # Same parameters as above
        hdiv_params = SamplingParams(
            count=5,
            range=2.0,
            step=0.5,
        )
        vdiv_params = SamplingParams(
            count=5,
            range=2.0,
            step=0.5,
        )
        disp_params = SamplingParams(count=1, range=0.0, step=0.0)

        # Generate sources with round_div=False (square_div)
        directions, weights, wavelengths = generate_sources_from_divergence_dispersion(
            hdiv_params=hdiv_params,
            vdiv_params=vdiv_params,
            disp_params=disp_params,
            central_wavelength_m=1e-10,
            round_div=False,  # No elliptical trimming
        )

        # Should have all 25 points (5x5 grid)
        assert len(directions) == 25, f"Square grid should have all 25 points, got {len(directions)}"

    def test_round_vs_square_source_count_difference(self):
        """
        Test that round_div produces fewer sources than square_div
        for the same divergence parameters.
        """
        # Use a larger grid to see more pronounced difference
        hdiv_params = SamplingParams(count=7, range=2.0, step=2.0/6)
        vdiv_params = SamplingParams(count=7, range=2.0, step=2.0/6)
        disp_params = SamplingParams(count=1, range=0.0, step=0.0)

        # Generate with round_div
        directions_round, _, _ = generate_sources_from_divergence_dispersion(
            hdiv_params=hdiv_params,
            vdiv_params=vdiv_params,
            disp_params=disp_params,
            central_wavelength_m=1e-10,
            round_div=True,
        )

        # Generate with square_div
        directions_square, _, _ = generate_sources_from_divergence_dispersion(
            hdiv_params=hdiv_params,
            vdiv_params=vdiv_params,
            disp_params=disp_params,
            central_wavelength_m=1e-10,
            round_div=False,
        )

        # Round should have fewer sources
        assert len(directions_round) < len(directions_square), \
            "Round divergence should produce fewer sources than square"

        # For 7x7 grid, square should have 49 points
        assert len(directions_square) == 49, f"7x7 grid should have 49 points, got {len(directions_square)}"

        # Round should exclude corner points
        print(f"Round: {len(directions_round)} sources, Square: {len(directions_square)} sources")
        assert len(directions_round) > 0, "Round divergence should still have some sources"

    def test_single_divergence_point_unaffected(self):
        """
        Test that when there's only a single divergence point (count=1),
        the round_div flag has no effect.
        """
        # Single point in divergence
        hdiv_params = SamplingParams(count=1, range=0.0, step=0.0)
        vdiv_params = SamplingParams(count=1, range=0.0, step=0.0)
        disp_params = SamplingParams(count=1, range=0.0, step=0.0)

        # Generate with both modes
        dirs_round, _, _ = generate_sources_from_divergence_dispersion(
            hdiv_params, vdiv_params, disp_params,
            central_wavelength_m=1e-10,
            round_div=True,
        )

        dirs_square, _, _ = generate_sources_from_divergence_dispersion(
            hdiv_params, vdiv_params, disp_params,
            central_wavelength_m=1e-10,
            round_div=False,
        )

        # Both should have exactly 1 source
        assert len(dirs_round) == 1, "Single divergence point with round_div should give 1 source"
        assert len(dirs_square) == 1, "Single divergence point with square_div should give 1 source"

    def test_elliptical_trimming_threshold(self):
        """
        Test that elliptical trimming correctly applies the normalized
        radius threshold of 1.0 as specified.
        """
        # Create a grid where we can predict which points will be trimmed
        # Use 3x3 for simplicity
        hdiv_params = SamplingParams(
            count=3,
            range=2.0,  # -1, 0, +1 radians
            step=1.0,
        )
        vdiv_params = SamplingParams(
            count=3,
            range=2.0,  # -1, 0, +1 radians
            step=1.0,
        )
        disp_params = SamplingParams(count=1, range=0.0, step=0.0)

        directions, _, _ = generate_sources_from_divergence_dispersion(
            hdiv_params=hdiv_params,
            vdiv_params=vdiv_params,
            disp_params=disp_params,
            central_wavelength_m=1e-10,
            round_div=True,
        )

        # For a 3x3 grid with range 2.0:
        # Points: (-1,-1), (-1,0), (-1,1), (0,-1), (0,0), (0,1), (1,-1), (1,0), (1,1)
        # Normalized by range/2 = 1.0:
        # Corners have normalized coords (±1, ±1) with radius sqrt(2) > 1 - excluded
        # Others have radius ≤ 1 - included
        # So we should have 5 points: center + 4 edge midpoints
        assert len(directions) == 5, f"3x3 grid with elliptical trimming should have 5 points, got {len(directions)}"

    def test_combined_divergence_and_dispersion(self):
        """
        Test that culling modes work correctly when combined with
        wavelength dispersion (multiple wavelengths per divergence point).
        """
        # Small divergence grid
        hdiv_params = SamplingParams(count=3, range=2.0, step=1.0)
        vdiv_params = SamplingParams(count=3, range=2.0, step=1.0)
        # Add wavelength dispersion
        disp_params = SamplingParams(count=3, range=0.1, step=0.05)  # 10% dispersion, 3 wavelengths

        # With round_div
        dirs_round, weights_round, waves_round = generate_sources_from_divergence_dispersion(
            hdiv_params, vdiv_params, disp_params,
            central_wavelength_m=1e-10,
            round_div=True,
        )

        # With square_div
        dirs_square, weights_square, waves_square = generate_sources_from_divergence_dispersion(
            hdiv_params, vdiv_params, disp_params,
            central_wavelength_m=1e-10,
            round_div=False,
        )

        # Each divergence point should have 3 wavelengths
        # Round: 5 divergence points * 3 wavelengths = 15 sources
        # Square: 9 divergence points * 3 wavelengths = 27 sources
        assert len(dirs_round) == 15, f"Round with dispersion should have 15 sources, got {len(dirs_round)}"
        assert len(dirs_square) == 27, f"Square with dispersion should have 27 sources, got {len(dirs_square)}"

        # Check wavelengths are properly distributed
        unique_waves = np.unique(waves_round.numpy())
        assert len(unique_waves) == 3, f"Should have 3 unique wavelengths, got {len(unique_waves)}"

        # Check wavelength range (10% dispersion around 1e-10)
        expected_min = 1e-10 * 0.95  # (1 - 0.1/2)
        expected_max = 1e-10 * 1.05  # (1 + 0.1/2)
        assert np.isclose(unique_waves.min(), expected_min), \
            f"Min wavelength {unique_waves.min():.3e} != expected {expected_min:.3e}"
        assert np.isclose(unique_waves.max(), expected_max), \
            f"Max wavelength {unique_waves.max():.3e} != expected {expected_max:.3e}"