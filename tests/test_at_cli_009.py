"""
Test AT-CLI-009: Error handling and usage

Setup: Invoke nanoBragg without -hkl and without an Fdump.bin and with -default_F=0.

Expectation: Program prints usage/help indicating required inputs and exits with
a non-zero status.
"""
import os
import tempfile
import subprocess
import pytest
from pathlib import Path

# Set environment variable for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


class TestATCLI009ErrorHandling:
    """Test cases for AT-CLI-009: Error handling and usage"""

    def setup_method(self):
        """Create a temporary directory for test outputs"""
        self.test_dir = tempfile.mkdtemp(prefix='test_at_cli_009_')
        # Change to test directory to ensure no Fdump.bin exists
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up and restore directory"""
        os.chdir(self.original_dir)
        import shutil
        if hasattr(self, 'test_dir') and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_missing_hkl_and_fdump_with_default_f_zero(self):
        """Test error when no HKL file, no Fdump.bin, and default_F=0"""
        args = [
            'python', '-m', 'nanobrag_torch',
            '-cell', '100', '100', '100', '90', '90', '90',
            '-default_F', '0',  # Explicitly set to 0
            '-lambda', '1.5',
            '-distance', '100'
        ]

        result = subprocess.run(args, capture_output=True, text=True)

        # Should exit with non-zero status
        assert result.returncode != 0, f"Should exit with error, but returned {result.returncode}"

        # Should print error message about missing inputs
        output = result.stdout + result.stderr
        assert 'Error' in output or 'error' in output, \
            f"Should print error message, got: {output}"

        # Should mention the need for HKL, Fdump, or default_F
        assert any(x in output for x in ['hkl', 'HKL', 'Fdump', 'default_F']), \
            f"Error message should mention HKL/Fdump/default_F, got: {output}"

        # Should include usage information
        assert 'Usage' in output or 'usage' in output, \
            f"Should print usage information, got: {output}"

    def test_missing_hkl_but_has_default_f(self):
        """Test that simulation runs when HKL is missing but default_F > 0"""
        output_file = Path(self.test_dir) / 'output.bin'
        args = [
            'python', '-m', 'nanobrag_torch',
            '-cell', '100', '100', '100', '90', '90', '90',
            '-default_F', '10',  # Non-zero default_F
            '-lambda', '1.5',
            '-distance', '100',
            '-detsize', '20',
            '-detpixels', '32',
            '-N', '1',
            '-floatfile', str(output_file),
            '-nopgm'
        ]

        result = subprocess.run(args, capture_output=True, text=True)

        # Should succeed
        assert result.returncode == 0, \
            f"Should succeed with default_F > 0, got error: {result.stderr}"

        # Output file should be created
        assert output_file.exists(), "Output file should be created"

    def test_missing_cell_parameters(self):
        """Test error when neither -mat nor -cell is provided"""
        # Create a dummy HKL file
        hkl_file = Path(self.test_dir) / 'test.hkl'
        with open(hkl_file, 'w') as f:
            f.write("0 0 1 100.0\n")

        args = [
            'python', '-m', 'nanobrag_torch',
            '-hkl', str(hkl_file),
            # No -cell or -mat provided
            '-lambda', '1.5',
            '-distance', '100'
        ]

        result = subprocess.run(args, capture_output=True, text=True)

        # Should exit with error
        assert result.returncode != 0, f"Should exit with error, but returned {result.returncode}"

        # Should mention missing cell or mat
        output = result.stdout + result.stderr
        assert any(x in output for x in ['cell', 'mat', 'Error', 'error']), \
            f"Should mention missing cell/mat parameters, got: {output}"

    def test_fdump_fallback(self):
        """Test that Fdump.bin is used when present and no HKL file specified"""
        # Create a simple Fdump.bin file
        import struct
        import numpy as np
        fdump_file = Path(self.test_dir) / 'Fdump.bin'
        with open(fdump_file, 'wb') as f:
            # Write ASCII header: h_min h_max k_min k_max l_min l_max
            header = "-2 2 -2 2 -2 2"
            f.write(header.encode('ascii'))
            f.write(b'\x0c')  # Form feed separator
            # Write binary grid data (5x5x5 = 125 values)
            data = np.full(125, 100.0, dtype=np.float64)
            data.tofile(f)

        output_file = Path(self.test_dir) / 'output.bin'
        args = [
            'python', '-m', 'nanobrag_torch',
            # No -hkl specified, should use Fdump.bin
            '-cell', '100', '100', '100', '90', '90', '90',
            '-lambda', '1.5',
            '-distance', '100',
            '-detsize', '20',
            '-detpixels', '32',
            '-N', '1',
            '-floatfile', str(output_file),
            '-nopgm'
        ]

        result = subprocess.run(args, capture_output=True, text=True)

        # Should succeed using Fdump.bin
        assert result.returncode == 0, \
            f"Should succeed with Fdump.bin, got error: {result.stderr}"

        # Output file should be created
        assert output_file.exists(), "Output file should be created"

    def test_help_message(self):
        """Test that -h prints help and exits with status 0"""
        args = ['python', '-m', 'nanobrag_torch', '-h']

        result = subprocess.run(args, capture_output=True, text=True)

        # Should exit with status 0
        assert result.returncode == 0, f"Help should exit with 0, got {result.returncode}"

        # Should print usage information
        assert 'usage' in result.stdout.lower(), \
            f"Help should include usage, got: {result.stdout}"

        # Should include various options
        assert all(x in result.stdout for x in ['-hkl', '-cell', '-lambda', '-distance']), \
            f"Help should list main options"

    def test_unsupported_flag_dispstep(self):
        """Test that unsupported flag -dispstep is rejected with clear error"""
        args = [
            'python', '-m', 'nanobrag_torch',
            '-cell', '100', '100', '100', '90', '90', '90',
            '-default_F', '100',
            '-lambda', '1.5',
            '-distance', '100',
            '-dispstep', '3',  # Unsupported flag per spec
            '-detpixels', '32',
            '-floatfile', 'output.bin'
        ]

        result = subprocess.run(args, capture_output=True, text=True)

        # Should exit with non-zero status
        assert result.returncode != 0, f"Should reject unsupported flag, but returned {result.returncode}"

        # Should print error about unrecognized argument
        output = result.stdout + result.stderr
        assert 'dispstep' in output or 'unrecognized' in output, \
            f"Should mention unsupported flag -dispstep, got: {output}"

        # Should include usage information
        assert 'usage' in output.lower(), \
            f"Should print usage information on error, got: {output}"

    def test_unsupported_flag_hdiv(self):
        """Test that unsupported flag -hdiv is rejected with clear error"""
        args = [
            'python', '-m', 'nanobrag_torch',
            '-cell', '100', '100', '100', '90', '90', '90',
            '-default_F', '100',
            '-lambda', '1.5',
            '-distance', '100',
            '-hdiv', '0.28',  # Unsupported flag per spec (should be -hdivrange)
            '-detpixels', '32',
            '-floatfile', 'output.bin'
        ]

        result = subprocess.run(args, capture_output=True, text=True)

        # Should exit with non-zero status
        assert result.returncode != 0, f"Should reject unsupported flag, but returned {result.returncode}"

        # Should print error about unrecognized argument
        output = result.stdout + result.stderr
        assert 'hdiv' in output or 'unrecognized' in output, \
            f"Should mention unsupported flag -hdiv, got: {output}"

    def test_unsupported_flag_vdiv(self):
        """Test that unsupported flag -vdiv is rejected with clear error"""
        args = [
            'python', '-m', 'nanobrag_torch',
            '-cell', '100', '100', '100', '90', '90', '90',
            '-default_F', '100',
            '-lambda', '1.5',
            '-distance', '100',
            '-vdiv', '0.28',  # Unsupported flag per spec (should be -vdivrange)
            '-detpixels', '32',
            '-floatfile', 'output.bin'
        ]

        result = subprocess.run(args, capture_output=True, text=True)

        # Should exit with non-zero status
        assert result.returncode != 0, f"Should reject unsupported flag, but returned {result.returncode}"

        # Should print error about unrecognized argument
        output = result.stdout + result.stderr
        assert 'vdiv' in output or 'unrecognized' in output, \
            f"Should mention unsupported flag -vdiv, got: {output}"