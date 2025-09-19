"""
Test AT-GEO-004: Two-theta axis defaults by convention

Per spec-a.md:
- MOSFLM → axis=[0,0,-1]
- XDS → [1,0,0]
- DIALS → [0,1,0]

The applied rotation axis SHALL match the convention default unless overridden.
The reported TWOTHETA value SHALL equal the user-specified value (deg).
"""

import os
import torch
import numpy as np
import pytest

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from src.nanobrag_torch.config import DetectorConfig, DetectorConvention
from src.nanobrag_torch.models.detector import Detector


def test_twotheta_axis_defaults():
    """Test that twotheta axis defaults correctly based on convention."""

    # Test MOSFLM convention
    config_mosflm = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        detector_twotheta_deg=10.0  # Small two-theta
    )
    expected_axis_mosflm = torch.tensor([0.0, 0.0, -1.0])
    torch.testing.assert_close(config_mosflm.twotheta_axis, expected_axis_mosflm)

    # Test XDS convention
    config_xds = DetectorConfig(
        detector_convention=DetectorConvention.XDS,
        detector_twotheta_deg=10.0
    )
    expected_axis_xds = torch.tensor([1.0, 0.0, 0.0])
    torch.testing.assert_close(config_xds.twotheta_axis, expected_axis_xds)

    # Test DIALS convention
    config_dials = DetectorConfig(
        detector_convention=DetectorConvention.DIALS,
        detector_twotheta_deg=10.0
    )
    expected_axis_dials = torch.tensor([0.0, 1.0, 0.0])
    torch.testing.assert_close(config_dials.twotheta_axis, expected_axis_dials)


def test_twotheta_axis_override():
    """Test that explicit twotheta_axis overrides convention defaults."""

    custom_axis = torch.tensor([0.5, 0.5, 0.707107])  # Custom unit vector

    # Override MOSFLM default
    config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        detector_twotheta_deg=10.0,
        twotheta_axis=custom_axis
    )
    torch.testing.assert_close(config.twotheta_axis, custom_axis)


def test_twotheta_rotation_applied():
    """Test that twotheta rotation is actually applied to detector basis vectors."""

    # Test with XDS convention and its default [1,0,0] axis
    config = DetectorConfig(
        detector_convention=DetectorConvention.XDS,
        detector_twotheta_deg=20.0,  # Noticeable rotation
        distance_mm=100.0,
        pixel_size_mm=0.1,
        beam_center_s=51.2,
        beam_center_f=51.2
    )

    detector = Detector(config)

    # The twotheta rotation should affect the detector basis vectors
    # For XDS with twotheta axis [1,0,0], rotation should be around X axis
    # Original XDS basis: fdet=[1,0,0], sdet=[0,1,0], odet=[0,0,1]
    # After 20° rotation around X-axis:
    # - fdet should remain [1,0,0] (rotation axis)
    # - sdet and odet should be rotated

    fdet_vec = detector.fdet_vec
    sdet_vec = detector.sdet_vec
    odet_vec = detector.odet_vec

    # fdet should remain close to [1,0,0] since it's along the rotation axis
    expected_fdet = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
    torch.testing.assert_close(fdet_vec, expected_fdet, atol=1e-6, rtol=1e-6)

    # sdet and odet should be rotated by 20 degrees around X axis
    angle_rad = np.radians(20.0)
    cos_angle = np.cos(angle_rad)
    sin_angle = np.sin(angle_rad)

    # Expected sdet after rotation: [0, cos(20°), sin(20°)]
    expected_sdet = torch.tensor([0.0, cos_angle, sin_angle], dtype=torch.float64)
    torch.testing.assert_close(sdet_vec, expected_sdet, atol=1e-6, rtol=1e-6)

    # Expected odet after rotation: [0, -sin(20°), cos(20°)]
    expected_odet = torch.tensor([0.0, -sin_angle, cos_angle], dtype=torch.float64)
    torch.testing.assert_close(odet_vec, expected_odet, atol=1e-6, rtol=1e-6)


def test_twotheta_value_preserved():
    """Test that the TWOTHETA value equals the user-specified value."""

    test_twotheta_deg = 15.5

    for convention in [DetectorConvention.MOSFLM, DetectorConvention.XDS, DetectorConvention.DIALS]:
        config = DetectorConfig(
            detector_convention=convention,
            detector_twotheta_deg=test_twotheta_deg
        )

        # The config should preserve the exact twotheta value
        assert config.detector_twotheta_deg == test_twotheta_deg

        # Create detector and verify the value is used
        detector = Detector(config)
        # The detector internally converts to radians but the config value should remain in degrees
        assert config.detector_twotheta_deg == test_twotheta_deg


def test_mosflm_twotheta_rotation():
    """Test MOSFLM convention twotheta rotation around [0,0,-1]."""

    config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        detector_twotheta_deg=30.0,
        distance_mm=100.0,
        pixel_size_mm=0.1
    )

    detector = Detector(config)

    # For MOSFLM with twotheta axis [0,0,-1], rotation should be around negative Z axis
    # Original MOSFLM basis: fdet=[0,0,1], sdet=[0,-1,0], odet=[1,0,0]
    # After 30° rotation around -Z axis, vectors in XY plane rotate

    angle_rad = np.radians(30.0)
    cos_angle = np.cos(angle_rad)
    sin_angle = np.sin(angle_rad)

    fdet_vec = detector.fdet_vec
    sdet_vec = detector.sdet_vec
    odet_vec = detector.odet_vec

    # fdet=[0,0,1] is along Z, perpendicular to rotation axis, stays [0,0,1]
    expected_fdet = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    torch.testing.assert_close(fdet_vec, expected_fdet, atol=1e-6, rtol=1e-6)

    # sdet=[0,-1,0] rotates around -Z: becomes [-sin(30°), -cos(30°), 0]
    # Rotation around -Z by angle θ: [x',y'] = [x*cos(θ) + y*sin(θ), -x*sin(θ) + y*cos(θ)]
    # For [0,-1,0]: x'=0*cos(30°)+(-1)*sin(30°)=-0.5, y'=-0*sin(30°)+(-1)*cos(30°)=-0.866
    expected_sdet = torch.tensor([-sin_angle, -cos_angle, 0.0], dtype=torch.float64)
    torch.testing.assert_close(sdet_vec, expected_sdet, atol=1e-6, rtol=1e-6)

    # odet=[1,0,0] rotates around -Z: becomes [cos(30°), -sin(30°), 0]
    # For [1,0,0]: x'=1*cos(30°)+0*sin(30°)=0.866, y'=-1*sin(30°)+0*cos(30°)=-0.5
    expected_odet = torch.tensor([cos_angle, -sin_angle, 0.0], dtype=torch.float64)
    torch.testing.assert_close(odet_vec, expected_odet, atol=1e-6, rtol=1e-6)


def test_dials_twotheta_rotation():
    """Test DIALS convention twotheta rotation around [0,1,0]."""

    config = DetectorConfig(
        detector_convention=DetectorConvention.DIALS,
        detector_twotheta_deg=25.0,
        distance_mm=100.0,
        pixel_size_mm=0.1
    )

    # For DIALS, need to check what initial basis vectors are
    # Based on spec, DIALS has: beam [0,0,1], f=[1,0,0], s=[0,1,0], o=[0,0,1]
    # However, the Detector class needs to implement DIALS basis vectors properly
    # For now, test that the axis is set correctly

    expected_axis = torch.tensor([0.0, 1.0, 0.0])
    torch.testing.assert_close(config.twotheta_axis, expected_axis)

    # The rotation itself will be tested once DIALS basis vectors are implemented in Detector


if __name__ == "__main__":
    test_twotheta_axis_defaults()
    test_twotheta_axis_override()
    test_twotheta_rotation_applied()
    test_twotheta_value_preserved()
    test_mosflm_twotheta_rotation()
    test_dials_twotheta_rotation()
    print("All AT-GEO-004 tests passed!")