"""
Test for AT-GEO-006: Point-pixel solid angle.

Per spec:
- With -point_pixel, Ω SHALL equal 1/R^2
- Without it, Ω SHALL equal (pixel_size^2/R^2)·(close_distance/R)
"""

import torch
import pytest
from src.nanobrag_torch.config import DetectorConfig
from src.nanobrag_torch.models.detector import Detector
import math


class TestATGEO006PointPixelSolidAngle:
    """Test suite for AT-GEO-006: Point-pixel solid angle."""

    def test_point_pixel_solid_angle(self):
        """
        Test that with point_pixel=True, solid angle equals 1/R^2.
        """
        # Setup: Create a detector with point_pixel enabled
        config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=10,
            fpixels=10,
            point_pixel=True  # Enable point-pixel mode
        )
        detector = Detector(config)

        # Get pixel coordinates and solid angles
        pixel_coords = detector.get_pixel_coords()
        solid_angles = detector.get_solid_angle(pixel_coords)

        # Calculate expected solid angles: 1/R^2
        R = torch.norm(pixel_coords, dim=-1)
        expected_omega = 1.0 / (R * R)

        # Assert they match
        torch.testing.assert_close(solid_angles, expected_omega, rtol=1e-6, atol=1e-10)

    def test_default_solid_angle_with_obliquity(self):
        """
        Test that without point_pixel, solid angle equals (pixel_size^2/R^2)·(close_distance/R).
        """
        # Setup: Create a detector without point_pixel (default)
        config = DetectorConfig(
            distance_mm=100.0,
            close_distance_mm=95.0,  # Set close_distance for obliquity factor
            pixel_size_mm=0.1,
            spixels=10,
            fpixels=10,
            point_pixel=False  # Default mode with obliquity
        )
        detector = Detector(config)

        # Get pixel coordinates and solid angles
        pixel_coords = detector.get_pixel_coords()
        solid_angles = detector.get_solid_angle(pixel_coords)

        # Calculate expected solid angles: (pixel_size^2/R^2) · (close_distance/R)
        R = torch.norm(pixel_coords, dim=-1)
        pixel_size_m = detector.pixel_size  # Already in meters
        close_distance_m = detector.close_distance  # Already in meters
        expected_omega = (pixel_size_m * pixel_size_m) / (R * R) * (close_distance_m / R)

        # Assert they match
        torch.testing.assert_close(solid_angles, expected_omega, rtol=1e-6, atol=1e-10)

    def test_off_center_pixel_comparison(self):
        """
        Test an off-center pixel to verify the difference between point_pixel and obliquity modes.
        """
        # Common configuration
        distance_mm = 100.0
        pixel_size_mm = 0.1
        close_distance_mm = 98.0

        # Create two detectors: one with point_pixel, one without
        config_point = DetectorConfig(
            distance_mm=distance_mm,
            close_distance_mm=close_distance_mm,
            pixel_size_mm=pixel_size_mm,
            spixels=100,
            fpixels=100,
            point_pixel=True
        )

        config_default = DetectorConfig(
            distance_mm=distance_mm,
            close_distance_mm=close_distance_mm,
            pixel_size_mm=pixel_size_mm,
            spixels=100,
            fpixels=100,
            point_pixel=False
        )

        detector_point = Detector(config_point)
        detector_default = Detector(config_default)

        # Get solid angles for both
        omega_point = detector_point.get_solid_angle()
        omega_default = detector_default.get_solid_angle()

        # Pick an off-center pixel
        s_idx, f_idx = 75, 75

        # Get the position vector for this pixel
        pixel_coords = detector_point.get_pixel_coords()
        pixel_pos = pixel_coords[s_idx, f_idx, :]
        R = torch.norm(pixel_pos)

        # Verify point_pixel mode: Ω = 1/R^2
        expected_point = 1.0 / (R * R)
        assert torch.allclose(omega_point[s_idx, f_idx], expected_point, rtol=1e-6)

        # Verify default mode: Ω = (pixel_size^2/R^2) · (close_distance/R)
        pixel_size_m = detector_default.pixel_size
        close_distance_m = detector_default.close_distance
        expected_default = (pixel_size_m * pixel_size_m) / (R * R) * (close_distance_m / R)
        assert torch.allclose(omega_default[s_idx, f_idx], expected_default, rtol=1e-6)

        # The default mode should have a smaller solid angle due to the pixel size and obliquity
        assert omega_default[s_idx, f_idx] < omega_point[s_idx, f_idx]

    def test_gradient_flow(self):
        """
        Test that solid angle calculation maintains gradient flow for differentiable parameters.
        """
        # Create a detector with differentiable distance
        distance = torch.tensor(100.0, requires_grad=True)

        config = DetectorConfig(
            distance_mm=distance,
            pixel_size_mm=0.1,
            spixels=5,
            fpixels=5,
            point_pixel=True
        )
        detector = Detector(config)

        # Calculate solid angle and sum (to get a scalar for backward)
        omega = detector.get_solid_angle()
        loss = omega.sum()

        # Check that gradients flow
        loss.backward()
        assert distance.grad is not None
        assert not torch.isnan(distance.grad)
        assert torch.abs(distance.grad) > 0  # Should have non-zero gradient

    def test_corner_pixel_values(self):
        """
        Test specific solid angle values for corner pixels to ensure correctness.
        """
        # Setup with known geometry
        config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=1.0,  # 1mm pixels for easier calculation
            spixels=100,
            fpixels=100,
            beam_center_f=50.0,  # Center of detector
            beam_center_s=50.0,
            point_pixel=True
        )
        detector = Detector(config)

        # Get solid angles
        omega = detector.get_solid_angle()

        # Check center pixel (closest to beam)
        center_s, center_f = 50, 50
        pixel_coords = detector.get_pixel_coords()
        center_pos = pixel_coords[center_s, center_f, :]
        R_center = torch.norm(center_pos)

        # For a centered detector, the center pixel should be approximately at distance
        # (with small corrections for pixel center offset)
        expected_omega_center = 1.0 / (R_center * R_center)
        assert torch.allclose(omega[center_s, center_f], expected_omega_center, rtol=1e-5)

        # Check corner pixel (furthest from beam typically)
        corner_s, corner_f = 99, 99
        corner_pos = pixel_coords[corner_s, corner_f, :]
        R_corner = torch.norm(corner_pos)
        expected_omega_corner = 1.0 / (R_corner * R_corner)
        assert torch.allclose(omega[corner_s, corner_f], expected_omega_corner, rtol=1e-5)

        # Corner should have smaller solid angle (larger R)
        assert omega[corner_s, corner_f] < omega[center_s, center_f]