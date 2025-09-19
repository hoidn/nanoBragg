"""Test MOSFLM matrix file loading functionality."""

import pytest
import numpy as np
import tempfile
from pathlib import Path

from src.nanobrag_torch.io.mosflm import read_mosflm_matrix, reciprocal_to_real_cell


class TestMOSFLMMatrixLoading:
    """Test loading and parsing of MOSFLM-style orientation matrices."""

    def test_read_identity_matrix(self):
        """Test reading an identity matrix."""
        # Create identity matrix file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mat', delete=False) as f:
            f.write("1.0 0.0 0.0\n")
            f.write("0.0 1.0 0.0\n")
            f.write("0.0 0.0 1.0\n")
            matrix_file = f.name

        try:
            # Read with wavelength 1.0 Å
            a_star, b_star, c_star = read_mosflm_matrix(matrix_file, wavelength_A=1.0)

            # Check that we get unit vectors
            np.testing.assert_array_almost_equal(a_star, [1.0, 0.0, 0.0])
            np.testing.assert_array_almost_equal(b_star, [0.0, 1.0, 0.0])
            np.testing.assert_array_almost_equal(c_star, [0.0, 0.0, 1.0])

            # Convert to real cell
            cell_params = reciprocal_to_real_cell(a_star, b_star, c_star)
            a, b, c, alpha, beta, gamma = cell_params

            # Should give a 1 Å cubic cell
            assert abs(a - 1.0) < 1e-10
            assert abs(b - 1.0) < 1e-10
            assert abs(c - 1.0) < 1e-10
            assert abs(alpha - 90.0) < 1e-10
            assert abs(beta - 90.0) < 1e-10
            assert abs(gamma - 90.0) < 1e-10
        finally:
            Path(matrix_file).unlink()

    def test_read_cubic_matrix(self):
        """Test reading a matrix for a 100 Å cubic cell."""
        # Create matrix for 100 Å cubic cell
        # Reciprocal vectors are 2π/100 = 0.0628... but MOSFLM uses 1/d = 0.01
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mat', delete=False) as f:
            f.write("0.01 0.0 0.0\n")
            f.write("0.0 0.01 0.0\n")
            f.write("0.0 0.0 0.01\n")
            matrix_file = f.name

        try:
            # Read with wavelength 1.0 Å
            a_star, b_star, c_star = read_mosflm_matrix(matrix_file, wavelength_A=1.0)

            # Check reciprocal vectors
            np.testing.assert_array_almost_equal(a_star, [0.01, 0.0, 0.0])
            np.testing.assert_array_almost_equal(b_star, [0.0, 0.01, 0.0])
            np.testing.assert_array_almost_equal(c_star, [0.0, 0.0, 0.01])

            # Convert to real cell
            cell_params = reciprocal_to_real_cell(a_star, b_star, c_star)
            a, b, c, alpha, beta, gamma = cell_params

            # Should give a 100 Å cubic cell
            assert abs(a - 100.0) < 1e-6
            assert abs(b - 100.0) < 1e-6
            assert abs(c - 100.0) < 1e-6
            assert abs(alpha - 90.0) < 1e-6
            assert abs(beta - 90.0) < 1e-6
            assert abs(gamma - 90.0) < 1e-6
        finally:
            Path(matrix_file).unlink()

    def test_wavelength_scaling(self):
        """Test that wavelength scaling works correctly."""
        # Create a matrix
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mat', delete=False) as f:
            # Values that would give a 50 Å cell with λ=2.0 Å
            f.write("0.04 0.0 0.0\n")
            f.write("0.0 0.04 0.0\n")
            f.write("0.0 0.0 0.04\n")
            matrix_file = f.name

        try:
            # Read with wavelength 2.0 Å
            a_star, b_star, c_star = read_mosflm_matrix(matrix_file, wavelength_A=2.0)

            # Scaling factor should be 1/2.0 = 0.5
            np.testing.assert_array_almost_equal(a_star, [0.02, 0.0, 0.0])
            np.testing.assert_array_almost_equal(b_star, [0.0, 0.02, 0.0])
            np.testing.assert_array_almost_equal(c_star, [0.0, 0.0, 0.02])

            # Convert to real cell
            cell_params = reciprocal_to_real_cell(a_star, b_star, c_star)
            a, b, c, _, _, _ = cell_params

            # Should give a 50 Å cubic cell
            assert abs(a - 50.0) < 1e-6
            assert abs(b - 50.0) < 1e-6
            assert abs(c - 50.0) < 1e-6
        finally:
            Path(matrix_file).unlink()

    def test_triclinic_matrix(self):
        """Test reading a matrix for a triclinic cell."""
        # Create a non-orthogonal matrix
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mat', delete=False) as f:
            f.write("0.01 0.002 0.0\n")
            f.write("0.0 0.015 0.003\n")
            f.write("0.001 0.0 0.012\n")
            matrix_file = f.name

        try:
            # Read with wavelength 1.0 Å
            a_star, b_star, c_star = read_mosflm_matrix(matrix_file, wavelength_A=1.0)

            # Check that vectors are not orthogonal
            dot_ab = np.dot(a_star, b_star)
            dot_ac = np.dot(a_star, c_star)
            dot_bc = np.dot(b_star, c_star)

            assert abs(dot_ab) > 1e-10  # Not orthogonal
            assert abs(dot_ac) > 1e-10  # Not orthogonal
            assert abs(dot_bc) > 1e-10  # Not orthogonal

            # Convert to real cell
            cell_params = reciprocal_to_real_cell(a_star, b_star, c_star)
            a, b, c, alpha, beta, gamma = cell_params

            # Should give a triclinic cell (non-90 degree angles)
            assert a > 0 and b > 0 and c > 0
            assert abs(alpha - 90.0) > 0.1  # Not cubic
            assert abs(beta - 90.0) > 0.1   # Not cubic
            assert abs(gamma - 90.0) > 0.1  # Not cubic
        finally:
            Path(matrix_file).unlink()

    def test_missing_file(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            read_mosflm_matrix("nonexistent_file.mat", wavelength_A=1.0)

    def test_invalid_format(self):
        """Test error handling for invalid format."""
        # Create file with wrong number of values
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mat', delete=False) as f:
            f.write("1.0 0.0\n")  # Only 2 values
            matrix_file = f.name

        try:
            with pytest.raises(ValueError, match="must contain exactly 9"):
                read_mosflm_matrix(matrix_file, wavelength_A=1.0)
        finally:
            Path(matrix_file).unlink()

    def test_comments_and_whitespace(self):
        """Test that comments and extra whitespace are handled."""
        # Create matrix with comments and varied whitespace
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mat', delete=False) as f:
            f.write("# This is a comment\n")
            f.write("  0.01   0.0    0.0  \n")
            f.write("\n")  # Empty line
            f.write("0.0   0.01  0.0\n")
            f.write("# Another comment\n")
            f.write("   0.0  0.0   0.01   \n")
            matrix_file = f.name

        try:
            # Should still read correctly
            a_star, b_star, c_star = read_mosflm_matrix(matrix_file, wavelength_A=1.0)

            np.testing.assert_array_almost_equal(a_star, [0.01, 0.0, 0.0])
            np.testing.assert_array_almost_equal(b_star, [0.0, 0.01, 0.0])
            np.testing.assert_array_almost_equal(c_star, [0.0, 0.0, 0.01])
        finally:
            Path(matrix_file).unlink()