"""
Test for AT-SRC-001 CLI integration with sourcefile option.

This test ensures that the sourcefile CLI option properly loads source files
and integrates them into the simulation.
"""

import os
import sys
import subprocess
import tempfile
import struct
import pytest
import numpy as np

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAT_SRC_001_CLI:
    """Test suite for sourcefile CLI integration."""

    def test_sourcefile_loading_via_cli(self):
        """Test that sourcefile can be loaded and used via CLI."""

        # Create a temporary source file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("# Test source file with multiple sources\n")
            f.write("# X    Y    Z    weight  wavelength\n")
            f.write("0.0   0.0   10.0   1.0     6.2e-10\n")
            f.write("0.1   0.0   10.0   1.5     6.2e-10\n")  # Different weight
            f.write("-0.1  0.0   10.0   0.5     6.3e-10\n")  # Different wavelength
            sourcefile_path = f.name

        # Create a temporary output file
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
            output_path = f.name

        try:
            # Run the CLI with sourcefile option
            cmd = [
                sys.executable, '-m', 'nanobrag_torch',
                '-default_F', '100',
                '-cell', '100', '100', '100', '90', '90', '90',
                '-lambda', '6.2',
                '-detpixels', '32',
                '-distance', '100',
                '-sourcefile', sourcefile_path,
                '-floatfile', output_path
            ]

            # Set environment variable
            env = os.environ.copy()
            env['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

            result = subprocess.run(cmd, capture_output=True, text=True, env=env)

            # Check that the command succeeded
            assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"

            # Check that sources were loaded (should see message in stdout)
            assert "Loaded 3 sources from" in result.stdout, \
                f"Source loading message not found in output: {result.stdout}"

            # Check that output file was created
            assert os.path.exists(output_path), "Output file was not created"

            # Read and check the output file has data
            with open(output_path, 'rb') as f:
                data = f.read()
                assert len(data) == 32 * 32 * 4, "Output file has wrong size"

                # Convert to float array
                floats = struct.unpack('f' * (32 * 32), data)
                floats_array = np.array(floats).reshape(32, 32)

                # Check that we have non-zero intensity
                assert floats_array.max() > 0, "No intensity in output image"

        finally:
            # Clean up temporary files
            if os.path.exists(sourcefile_path):
                os.remove(sourcefile_path)
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_sourcefile_with_missing_columns(self):
        """Test that sourcefile with missing columns uses defaults."""

        # Create a source file with only X,Y,Z (no weight or wavelength)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("# Minimal source file\n")
            f.write("0.0   0.0   10.0\n")
            f.write("0.1   0.0   10.0\n")
            sourcefile_path = f.name

        # Create a temporary output file
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
            output_path = f.name

        try:
            # Run the CLI
            cmd = [
                sys.executable, '-m', 'nanobrag_torch',
                '-default_F', '100',
                '-cell', '100', '100', '100', '90', '90', '90',
                '-lambda', '6.2',
                '-detpixels', '16',  # Smaller for speed
                '-distance', '100',
                '-sourcefile', sourcefile_path,
                '-floatfile', output_path
            ]

            env = os.environ.copy()
            env['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

            result = subprocess.run(cmd, capture_output=True, text=True, env=env)

            # Check that command succeeded
            assert result.returncode == 0, f"Command failed: {result.stderr}"

            # Check that sources were loaded
            assert "Loaded 2 sources from" in result.stdout, \
                "Source loading message not found"

            # Check output exists and has data
            assert os.path.exists(output_path)
            with open(output_path, 'rb') as f:
                data = f.read()
                assert len(data) == 16 * 16 * 4

        finally:
            if os.path.exists(sourcefile_path):
                os.remove(sourcefile_path)
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_sourcefile_takes_precedence_over_divergence(self):
        """Test that sourcefile takes precedence over divergence parameters."""

        # Create a source file with 2 sources
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("0.0   0.0   10.0\n")
            f.write("0.1   0.0   10.0\n")
            sourcefile_path = f.name

        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
            output_path = f.name

        try:
            # Run with both sourcefile and divergence parameters
            cmd = [
                sys.executable, '-m', 'nanobrag_torch',
                '-default_F', '100',
                '-cell', '100', '100', '100', '90', '90', '90',
                '-lambda', '6.2',
                '-detpixels', '16',
                '-distance', '100',
                '-sourcefile', sourcefile_path,
                '-hdivrange', '0.1',  # These should be ignored
                '-vdivrange', '0.1',  # when sourcefile is present
                '-hdivsteps', '5',
                '-vdivsteps', '5',
                '-floatfile', output_path
            ]

            env = os.environ.copy()
            env['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

            result = subprocess.run(cmd, capture_output=True, text=True, env=env)

            assert result.returncode == 0, f"Command failed: {result.stderr}"

            # Should load from file, not generate from divergence
            assert "Loaded 2 sources from" in result.stdout, \
                "Should load from sourcefile"
            assert "Generated" not in result.stdout, \
                "Should not generate from divergence when sourcefile is present"

        finally:
            if os.path.exists(sourcefile_path):
                os.remove(sourcefile_path)
            if os.path.exists(output_path):
                os.remove(output_path)