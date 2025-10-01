"""
Test detector basis vector calculations.
"""

import pytest
import torch
import numpy as np

from src.nanobrag_torch.config import DetectorConfig, DetectorConvention
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.utils.geometry import angles_to_rotation_matrix, rotate_axis


class TestDetectorBasisVectors:
    """Test calculation of detector basis vectors with rotations."""

    def test_default_mosflm_convention(self):
        """Test MOSFLM convention basis vectors without rotation."""
        config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            detector_rotx_deg=0.0,
            detector_roty_deg=0.0,
            detector_rotz_deg=0.0,
            detector_twotheta_deg=0.0,
        )
        detector = Detector(config, dtype=torch.float64)

        # Check basis vectors match expected MOSFLM convention
        torch.testing.assert_close(
            detector.fdet_vec, torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
        )
        torch.testing.assert_close(
            detector.sdet_vec, torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64)
        )
        torch.testing.assert_close(
            detector.odet_vec, torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
        )

    def test_default_xds_convention(self):
        """Test XDS convention basis vectors without rotation."""
        config = DetectorConfig(
            detector_convention=DetectorConvention.XDS,
            detector_rotx_deg=0.0,
            detector_roty_deg=0.0,
            detector_rotz_deg=0.0,
            detector_twotheta_deg=0.0,
        )
        detector = Detector(config, dtype=torch.float64)

        # Check basis vectors match expected XDS convention
        torch.testing.assert_close(
            detector.fdet_vec, torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
        )
        torch.testing.assert_close(
            detector.sdet_vec, torch.tensor([0.0, 1.0, 0.0], dtype=torch.float64)
        )
        torch.testing.assert_close(
            detector.odet_vec, torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
        )

    def test_single_axis_rotations(self):
        """Test basis vectors with single-axis rotations."""
        # Test X-axis rotation (90 degrees)
        config = DetectorConfig(
            detector_rotx_deg=90.0,
            detector_roty_deg=0.0,
            detector_rotz_deg=0.0,
            detector_twotheta_deg=0.0,
        )
        detector = Detector(config, dtype=torch.float64)

        # After 90 degree rotation around X:
        # - fdet (0,0,1) -> (0,-1,0)
        # - sdet (0,-1,0) -> (0,0,-1)
        # - odet (1,0,0) stays at (1,0,0)
        torch.testing.assert_close(
            detector.fdet_vec,
            torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64),
            rtol=1e-7,
            atol=1e-7,
        )
        torch.testing.assert_close(
            detector.sdet_vec,
            torch.tensor([0.0, 0.0, -1.0], dtype=torch.float64),
            rtol=1e-7,
            atol=1e-7,
        )
        torch.testing.assert_close(
            detector.odet_vec,
            torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64),
            rtol=1e-7,
            atol=1e-7,
        )

        # Test Y-axis rotation (90 degrees)
        config = DetectorConfig(
            detector_rotx_deg=0.0,
            detector_roty_deg=90.0,
            detector_rotz_deg=0.0,
            detector_twotheta_deg=0.0,
        )
        detector = Detector(config, dtype=torch.float64)

        # After 90 degree rotation around Y:
        # - fdet (0,0,1) -> (1,0,0)
        # - sdet (0,-1,0) stays at (0,-1,0)
        # - odet (1,0,0) -> (0,0,-1)
        torch.testing.assert_close(
            detector.fdet_vec,
            torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64),
            rtol=1e-7,
            atol=1e-7,
        )
        torch.testing.assert_close(
            detector.sdet_vec,
            torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64),
            rtol=1e-7,
            atol=1e-7,
        )
        torch.testing.assert_close(
            detector.odet_vec,
            torch.tensor([0.0, 0.0, -1.0], dtype=torch.float64),
            rtol=1e-7,
            atol=1e-7,
        )

    def test_combined_rotations(self):
        """Test basis vectors with combined rotations."""
        # Test combined X and Y rotations
        config = DetectorConfig(
            detector_rotx_deg=30.0,
            detector_roty_deg=45.0,
            detector_rotz_deg=0.0,
            detector_twotheta_deg=0.0,
        )
        detector = Detector(config, dtype=torch.float64)

        # Manually calculate expected result
        rotx_rad = np.radians(30.0)
        roty_rad = np.radians(45.0)

        # Build rotation matrices (matching C-code order: X then Y then Z)
        Rx = np.array(
            [
                [1, 0, 0],
                [0, np.cos(rotx_rad), -np.sin(rotx_rad)],
                [0, np.sin(rotx_rad), np.cos(rotx_rad)],
            ]
        )
        Ry = np.array(
            [
                [np.cos(roty_rad), 0, np.sin(roty_rad)],
                [0, 1, 0],
                [-np.sin(roty_rad), 0, np.cos(roty_rad)],
            ]
        )
        R = Ry @ Rx

        # Apply to initial vectors
        fdet_expected = R @ np.array([0, 0, 1])
        sdet_expected = R @ np.array([0, -1, 0])
        odet_expected = R @ np.array([1, 0, 0])

        torch.testing.assert_close(
            detector.fdet_vec,
            torch.tensor(fdet_expected, dtype=torch.float64),
            rtol=1e-7,
            atol=1e-7,
        )
        torch.testing.assert_close(
            detector.sdet_vec,
            torch.tensor(sdet_expected, dtype=torch.float64),
            rtol=1e-7,
            atol=1e-7,
        )
        torch.testing.assert_close(
            detector.odet_vec,
            torch.tensor(odet_expected, dtype=torch.float64),
            rtol=1e-7,
            atol=1e-7,
        )

    def test_twotheta_rotation(self):
        """Test two-theta rotation around arbitrary axis."""
        # Test two-theta rotation around Y axis
        config = DetectorConfig(
            detector_rotx_deg=0.0,
            detector_roty_deg=0.0,
            detector_rotz_deg=0.0,
            detector_twotheta_deg=30.0,
            twotheta_axis=torch.tensor([0.0, 1.0, 0.0]),
        )
        detector = Detector(config, dtype=torch.float64)

        # Calculate expected vectors after 30 degree rotation around Y
        angle_rad = np.radians(30.0)
        cos_angle = np.cos(angle_rad)
        sin_angle = np.sin(angle_rad)

        # For rotation around Y-axis:
        # fdet (0,0,1) -> (sin(30), 0, cos(30))
        # sdet (0,-1,0) stays at (0,-1,0)
        # odet (1,0,0) -> (cos(30), 0, -sin(30))
        fdet_expected = torch.tensor([sin_angle, 0.0, cos_angle], dtype=torch.float64)
        sdet_expected = torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64)
        odet_expected = torch.tensor([cos_angle, 0.0, -sin_angle], dtype=torch.float64)

        torch.testing.assert_close(
            detector.fdet_vec, fdet_expected, rtol=1e-7, atol=1e-7
        )
        torch.testing.assert_close(
            detector.sdet_vec, sdet_expected, rtol=1e-7, atol=1e-7
        )
        torch.testing.assert_close(
            detector.odet_vec, odet_expected, rtol=1e-7, atol=1e-7
        )

    def test_all_rotations_combined(self):
        """Test all rotations applied together."""
        config = DetectorConfig(
            detector_rotx_deg=10.0,
            detector_roty_deg=20.0,
            detector_rotz_deg=30.0,
            detector_twotheta_deg=15.0,
            twotheta_axis=torch.tensor([0.0, 1.0, 0.0]),
        )
        detector = Detector(config, dtype=torch.float64)

        # Verify that basis vectors are orthonormal
        # Check orthogonality
        assert abs(torch.dot(detector.fdet_vec, detector.sdet_vec).item()) < 1e-9
        assert abs(torch.dot(detector.fdet_vec, detector.odet_vec).item()) < 1e-9
        assert abs(torch.dot(detector.sdet_vec, detector.odet_vec).item()) < 1e-9

        # Check unit length
        assert abs(torch.norm(detector.fdet_vec).item() - 1.0) < 1e-9
        assert abs(torch.norm(detector.sdet_vec).item() - 1.0) < 1e-9
        assert abs(torch.norm(detector.odet_vec).item() - 1.0) < 1e-9

    def test_tensor_rotation_parameters(self):
        """Test that tensor parameters work correctly."""
        # Use float64 to match detector's default dtype
        rotx = torch.tensor(15.0, dtype=torch.float64, requires_grad=True)
        roty = torch.tensor(25.0, dtype=torch.float64, requires_grad=True)
        rotz = torch.tensor(35.0, dtype=torch.float64, requires_grad=True)
        twotheta = torch.tensor(45.0, dtype=torch.float64, requires_grad=True)

        config = DetectorConfig(
            detector_rotx_deg=rotx,
            detector_roty_deg=roty,
            detector_rotz_deg=rotz,
            detector_twotheta_deg=twotheta,
        )
        detector = Detector(config, dtype=torch.float64)

        # Verify tensors preserve gradients
        assert detector.fdet_vec.requires_grad
        assert detector.sdet_vec.requires_grad
        assert detector.odet_vec.requires_grad

        # Verify orthonormality
        assert abs(torch.dot(detector.fdet_vec, detector.sdet_vec).item()) < 1e-9
        assert abs(torch.norm(detector.fdet_vec).item() - 1.0) < 1e-9
