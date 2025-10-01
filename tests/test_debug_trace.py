"""
Tests for CLI debug trace features: -printout, -printout_pixel, -trace_pixel.

These features provide verbose debugging output for simulation inspection.
"""

import pytest
import subprocess
import tempfile
import os
import numpy as np
from pathlib import Path


class TestDebugTraceFeatures:
    """Test the debug trace CLI features."""

    @pytest.fixture
    def minimal_args(self):
        """Minimal valid arguments for running the simulator."""
        return [
            '-cell', '100', '100', '100', '90', '90', '90',
            '-default_F', '100',
            '-lambda', '1.0',
            '-distance', '100',
            '-detpixels', '64',
            '-pixel', '0.1'
        ]

    def test_printout_flag(self, minimal_args):
        """Test that -printout produces verbose debug output."""
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
            output_file = f.name

        try:
            # Run with -printout flag
            cmd = ['python', '-m', 'nanobrag_torch'] + minimal_args + [
                '-floatfile', output_file,
                '-printout'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env={**os.environ, 'KMP_DUPLICATE_LIB_OK': 'TRUE'}
            )

            # Check that the command succeeded
            assert result.returncode == 0, f"Command failed: {result.stderr}"

            # Check for debug output markers
            output = result.stdout
            assert "Debug output enabled" in output or "Debug Output" in output
            assert "Image shape" in output or "Max intensity" in output
            assert "Brightest pixel" in output or "Mean intensity" in output

        finally:
            # Clean up
            if os.path.exists(output_file):
                os.unlink(output_file)
            if Path("Fdump.bin").exists():
                os.unlink("Fdump.bin")

    def test_printout_pixel_flag(self, minimal_args):
        """Test that -printout_pixel limits output to specific pixel."""
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
            output_file = f.name

        try:
            # Run with -printout_pixel flag for pixel (10, 20) [fast, slow]
            cmd = ['python', '-m', 'nanobrag_torch'] + minimal_args + [
                '-floatfile', output_file,
                '-printout_pixel', '10', '20'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env={**os.environ, 'KMP_DUPLICATE_LIB_OK': 'TRUE'}
            )

            # Check that the command succeeded
            assert result.returncode == 0, f"Command failed: {result.stderr}"

            # Check for pixel-specific output
            output = result.stdout
            assert "Limiting output to pixel" in output or "Pixel (10, 20)" in output
            
            # Should mention the specific pixel coordinates
            assert "10" in output and "20" in output

        finally:
            # Clean up
            if os.path.exists(output_file):
                os.unlink(output_file)
            if Path("Fdump.bin").exists():
                os.unlink("Fdump.bin")

    def test_trace_pixel_flag(self, minimal_args):
        """Test that -trace_pixel produces detailed trace for specific pixel."""
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
            output_file = f.name

        try:
            # Run with -trace_pixel flag for pixel (32, 32) [slow, fast]
            cmd = ['python', '-m', 'nanobrag_torch'] + minimal_args + [
                '-floatfile', output_file,
                '-trace_pixel', '32', '32'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env={**os.environ, 'KMP_DUPLICATE_LIB_OK': 'TRUE'}
            )

            # Check that the command succeeded
            assert result.returncode == 0, f"Command failed: {result.stderr}"

            # Check for trace output markers
            output = result.stdout
            assert "Tracing pixel" in output or "TRACE:" in output
            
            # Should have detailed trace information
            if "TRACE:" in output:
                assert "Final intensity" in output or "intensity =" in output
                assert "Position" in output or "Airpath" in output

        finally:
            # Clean up
            if os.path.exists(output_file):
                os.unlink(output_file)
            if Path("Fdump.bin").exists():
                os.unlink("Fdump.bin")

    def test_combined_debug_flags(self, minimal_args):
        """Test that multiple debug flags can be used together."""
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
            output_file = f.name

        try:
            # Run with both -printout and -trace_pixel
            cmd = ['python', '-m', 'nanobrag_torch'] + minimal_args + [
                '-floatfile', output_file,
                '-printout',
                '-trace_pixel', '30', '30'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env={**os.environ, 'KMP_DUPLICATE_LIB_OK': 'TRUE'}
            )

            # Check that the command succeeded
            assert result.returncode == 0, f"Command failed: {result.stderr}"

            # Check for both types of output
            output = result.stdout
            
            # Should have general debug output
            assert "Debug" in output or "Image shape" in output or "Max intensity" in output
            
            # Should also have trace output
            assert "Tracing pixel" in output or "TRACE:" in output

        finally:
            # Clean up
            if os.path.exists(output_file):
                os.unlink(output_file)
            if Path("Fdump.bin").exists():
                os.unlink("Fdump.bin")

    def test_out_of_bounds_pixel(self, minimal_args):
        """Test that out-of-bounds pixel indices are handled gracefully."""
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
            output_file = f.name

        try:
            # Run with out-of-bounds pixel (detector is 64x64)
            cmd = ['python', '-m', 'nanobrag_torch'] + minimal_args + [
                '-floatfile', output_file,
                '-trace_pixel', '100', '100'  # Out of bounds
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env={**os.environ, 'KMP_DUPLICATE_LIB_OK': 'TRUE'}
            )

            # Should still succeed (gracefully handle out of bounds)
            assert result.returncode == 0, f"Command failed: {result.stderr}"

            # Should not crash, but might not have trace output for invalid pixel
            output = result.stdout
            # The simulation should still run and produce statistics
            assert "Statistics" in output

        finally:
            # Clean up
            if os.path.exists(output_file):
                os.unlink(output_file)
            if Path("Fdump.bin").exists():
                os.unlink("Fdump.bin")
