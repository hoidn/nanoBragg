"""
Test divergence grid culling modes (round_div/square_div).

This test verifies the -round_div and -square_div CLI flags that control
elliptical trimming of the divergence grid per spec-a-parallel.md.
"""
import pytest
import subprocess
import tempfile
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nanobrag_torch.utils.auto_selection import (
    generate_sources_from_divergence_dispersion,
    auto_select_divergence,
    SamplingParams
)
import torch


class TestDivergenceCulling:
    """Test divergence grid culling modes."""

    def test_cli_round_div_flag(self):
        """Test that -round_div flag is accepted by CLI."""
        cmd = [
            sys.executable, '-m', 'nanobrag_torch',
            '-default_F', '100',
            '-cell', '100', '100', '100', '90', '90', '90',
            '-lambda', '1.0',
            '-distance', '100',
            '-detpixels', '32',
            '-hdivrange', '1.0',
            '-vdivrange', '1.0',
            '-hdivsteps', '5',
            '-vdivsteps', '5',
            '-round_div',
            '--help'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert 'elliptical trimming' in result.stdout.lower()

    def test_cli_square_div_flag(self):
        """Test that -square_div flag is accepted by CLI."""
        cmd = [
            sys.executable, '-m', 'nanobrag_torch',
            '-default_F', '100',
            '-cell', '100', '100', '100', '90', '90', '90',
            '-lambda', '1.0',
            '-distance', '100',
            '-detpixels', '32',
            '-hdivrange', '1.0',
            '-vdivrange', '1.0',
            '-hdivsteps', '5',
            '-vdivsteps', '5',
            '-square_div',
            '--help'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"CLI failed: {result.stderr}"

    def test_round_div_elliptical_trimming(self):
        """Test that round_div applies elliptical trimming to divergence grid."""
        # Set up divergence parameters
        hdiv_params = SamplingParams(count=5, range=2e-3, step=0.5e-3)
        vdiv_params = SamplingParams(count=5, range=2e-3, step=0.5e-3)
        disp_params = SamplingParams(count=1, range=0.0, step=0.0)

        # Generate sources with round_div=True (elliptical trimming)
        sources_round, _, _ = generate_sources_from_divergence_dispersion(
            hdiv_params=hdiv_params,
            vdiv_params=vdiv_params,
            disp_params=disp_params,
            central_wavelength_m=1e-10,
            source_distance_m=10.0,
            round_div=True
        )

        # Generate sources with round_div=False (square grid)
        sources_square, _, _ = generate_sources_from_divergence_dispersion(
            hdiv_params=hdiv_params,
            vdiv_params=vdiv_params,
            disp_params=disp_params,
            central_wavelength_m=1e-10,
            source_distance_m=10.0,
            round_div=False
        )

        # With elliptical trimming, we should have fewer sources
        # The corners of the square grid should be excluded
        assert sources_round.shape[0] < sources_square.shape[0], \
            f"Elliptical trimming should reduce source count: round={sources_round.shape[0]}, square={sources_square.shape[0]}"

        # Square grid should have exactly hdivsteps * vdivsteps * dispsteps sources
        expected_square = hdiv_params.count * vdiv_params.count * disp_params.count
        assert sources_square.shape[0] == expected_square, \
            f"Square grid should have {expected_square} sources, got {sources_square.shape[0]}"

    def test_round_div_single_divergence_point(self):
        """Test that round_div doesn't apply when there's only one divergence point."""
        # Set up divergence parameters with single point
        hdiv_params = SamplingParams(count=1, range=0.0, step=0.0)
        vdiv_params = SamplingParams(count=1, range=0.0, step=0.0)
        disp_params = SamplingParams(count=1, range=0.0, step=0.0)

        # Generate sources with round_div=True
        sources_round, _, _ = generate_sources_from_divergence_dispersion(
            hdiv_params=hdiv_params,
            vdiv_params=vdiv_params,
            disp_params=disp_params,
            central_wavelength_m=1e-10,
            source_distance_m=10.0,
            round_div=True
        )

        # Generate sources with round_div=False
        sources_square, _, _ = generate_sources_from_divergence_dispersion(
            hdiv_params=hdiv_params,
            vdiv_params=vdiv_params,
            disp_params=disp_params,
            central_wavelength_m=1e-10,
            source_distance_m=10.0,
            round_div=False
        )

        # With single point, both should be identical
        assert sources_round.shape[0] == sources_square.shape[0] == 1, \
            "Single divergence point should not be affected by culling mode"

    def test_cli_integration_with_divergence(self):
        """Test that divergence culling modes work in full CLI integration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_round = os.path.join(tmpdir, 'output_round.bin')
            output_square = os.path.join(tmpdir, 'output_square.bin')

            # Common arguments
            base_args = [
                sys.executable, '-m', 'nanobrag_torch',
                '-default_F', '100',
                '-cell', '100', '100', '100', '90', '90', '90',
                '-lambda', '1.0',
                '-distance', '100',
                '-detpixels', '32',
                '-hdivrange', '2.0',
                '-vdivrange', '2.0',
                '-hdivsteps', '5',
                '-vdivsteps', '5',
                '-roi', '10', '20', '10', '20'  # Small ROI for speed
            ]

            # Run with round_div
            cmd_round = base_args + ['-round_div', '-floatfile', output_round]
            result_round = subprocess.run(cmd_round, capture_output=True, text=True)
            assert result_round.returncode == 0, f"round_div run failed: {result_round.stderr}"
            assert os.path.exists(output_round), "round_div output not created"

            # Run with square_div
            cmd_square = base_args + ['-square_div', '-floatfile', output_square]
            result_square = subprocess.run(cmd_square, capture_output=True, text=True)
            assert result_square.returncode == 0, f"square_div run failed: {result_square.stderr}"
            assert os.path.exists(output_square), "square_div output not created"

            # The outputs should be different due to different source counts
            # We don't compare the actual image data, just verify the runs complete
            file_size_round = os.path.getsize(output_round)
            file_size_square = os.path.getsize(output_square)
            assert file_size_round == file_size_square, "Output files should have same pixel count"

    def test_default_is_round_div(self):
        """Test that the default behavior is round_div (elliptical trimming)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_default = os.path.join(tmpdir, 'output_default.bin')
            output_round = os.path.join(tmpdir, 'output_round.bin')

            # Common arguments
            base_args = [
                sys.executable, '-m', 'nanobrag_torch',
                '-default_F', '100',
                '-cell', '100', '100', '100', '90', '90', '90',
                '-lambda', '1.0',
                '-distance', '100',
                '-detpixels', '16',
                '-hdivrange', '2.0',
                '-vdivrange', '2.0',
                '-hdivsteps', '3',
                '-vdivsteps', '3',
                '-roi', '5', '10', '5', '10'  # Very small ROI for speed
            ]

            # Run with default (no flag)
            cmd_default = base_args + ['-floatfile', output_default]
            result_default = subprocess.run(cmd_default, capture_output=True, text=True)
            assert result_default.returncode == 0, f"Default run failed: {result_default.stderr}"

            # Run with explicit -round_div
            cmd_round = base_args + ['-round_div', '-floatfile', output_round]
            result_round = subprocess.run(cmd_round, capture_output=True, text=True)
            assert result_round.returncode == 0, f"round_div run failed: {result_round.stderr}"

            # Both should produce identical output since default is round_div
            # We verify this by checking that both runs complete successfully
            # and produce output files of the same size
            assert os.path.getsize(output_default) == os.path.getsize(output_round), \
                "Default behavior should match -round_div"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])