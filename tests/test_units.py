"""
Test unit conversion utilities.
"""

import pytest
import torch

from src.nanobrag_torch.utils.units import (
    mm_to_angstroms,
    meters_to_angstroms,
    degrees_to_radians,
    angstroms_to_mm,
    angstroms_to_meters,
    radians_to_degrees,
)


class TestUnitConversions:
    """Test unit conversion functions."""

    def test_mm_to_angstroms_scalar(self):
        """Test mm to Angstrom conversion with scalar."""
        assert mm_to_angstroms(1.0) == 10000000.0
        assert mm_to_angstroms(0.1) == 1000000.0

    def test_mm_to_angstroms_tensor(self):
        """Test mm to Angstrom conversion with tensor."""
        input_tensor = torch.tensor([1.0, 0.1, 10.0])
        expected = torch.tensor([10000000.0, 1000000.0, 100000000.0])
        result = mm_to_angstroms(input_tensor)
        torch.testing.assert_close(result, expected)

    def test_mm_to_angstroms_gradient(self):
        """Test gradient preservation in mm to Angstrom conversion."""
        input_tensor = torch.tensor([1.0], requires_grad=True)
        result = mm_to_angstroms(input_tensor)
        assert result.requires_grad

        # Compute gradient
        result.backward()
        assert input_tensor.grad is not None
        torch.testing.assert_close(input_tensor.grad, torch.tensor([10000000.0]))

    def test_meters_to_angstroms_scalar(self):
        """Test meters to Angstrom conversion with scalar."""
        assert meters_to_angstroms(1.0) == 1e10
        assert meters_to_angstroms(0.001) == 1e7

    def test_meters_to_angstroms_tensor(self):
        """Test meters to Angstrom conversion with tensor."""
        input_tensor = torch.tensor([1.0, 0.001, 1e-10])
        expected = torch.tensor([1e10, 1e7, 1.0])
        result = meters_to_angstroms(input_tensor)
        torch.testing.assert_close(result, expected)

    def test_degrees_to_radians_scalar(self):
        """Test degrees to radians conversion with scalar."""
        import math

        assert (
            abs(degrees_to_radians(180.0) - math.pi) < 1e-7
        )  # Reduced precision for float32
        assert abs(degrees_to_radians(90.0) - math.pi / 2) < 1e-7
        assert abs(degrees_to_radians(0.0)) < 1e-10

    def test_degrees_to_radians_tensor(self):
        """Test degrees to radians conversion with tensor."""
        import math

        input_tensor = torch.tensor([180.0, 90.0, 0.0, 45.0])
        expected = torch.tensor([math.pi, math.pi / 2, 0.0, math.pi / 4])
        result = degrees_to_radians(input_tensor)
        torch.testing.assert_close(result, expected)

    def test_degrees_to_radians_gradient(self):
        """Test gradient preservation in degrees to radians conversion."""
        input_tensor = torch.tensor([180.0], requires_grad=True)
        result = degrees_to_radians(input_tensor)
        assert result.requires_grad

        # Compute gradient
        result.backward()
        assert input_tensor.grad is not None
        # Gradient should be pi/180
        expected_grad = torch.tensor([torch.pi / 180.0])
        torch.testing.assert_close(input_tensor.grad, expected_grad)

    def test_inverse_conversions(self):
        """Test that inverse conversions work correctly."""
        # mm <-> angstroms
        assert abs(angstroms_to_mm(mm_to_angstroms(1.0)) - 1.0) < 1e-10

        # meters <-> angstroms
        assert abs(angstroms_to_meters(meters_to_angstroms(1.0)) - 1.0) < 1e-10

        # degrees <-> radians
        assert abs(radians_to_degrees(degrees_to_radians(180.0)) - 180.0) < 1e-10

    def test_batch_tensor_conversions(self):
        """Test conversions with batch tensors."""
        batch_mm = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
        result = mm_to_angstroms(batch_mm)
        expected = torch.tensor([[10000000.0, 20000000.0], [30000000.0, 40000000.0]])
        torch.testing.assert_close(result, expected)
