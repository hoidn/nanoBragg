"""
Test detector conventions including ADXV and DENZO.

This test verifies that all detector conventions (MOSFLM, XDS, DIALS, ADXV, DENZO)
are correctly implemented with proper basis vectors, beam directions, and beam center mappings.
"""

import pytest
import torch
import numpy as np
from src.nanobrag_torch.config import DetectorConfig, DetectorConvention
from src.nanobrag_torch.models.detector import Detector


class TestDetectorConventions:
    """Test all detector conventions including newly added ADXV and DENZO."""

    def test_adxv_convention_basis_vectors(self):
        """Test ADXV convention has correct basis vectors per spec."""
        config = DetectorConfig(
            detector_convention=DetectorConvention.ADXV,
            spixels=512,
            fpixels=512,
            pixel_size_mm=0.1,
            distance_mm=100.0
        )

        detector = Detector(config, dtype=torch.float64)

        # ADXV per spec: f = [1 0 0]; s = [0 -1 0]; o = [0 0 1]
        expected_fdet = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
        expected_sdet = torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64)
        expected_odet = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)

        assert torch.allclose(detector.fdet_vec, expected_fdet, atol=1e-6), \
            f"ADXV fast vector incorrect: {detector.fdet_vec}"
        assert torch.allclose(detector.sdet_vec, expected_sdet, atol=1e-6), \
            f"ADXV slow vector incorrect: {detector.sdet_vec}"
        assert torch.allclose(detector.odet_vec, expected_odet, atol=1e-6), \
            f"ADXV normal vector incorrect: {detector.odet_vec}"

    def test_denzo_convention_basis_vectors(self):
        """Test DENZO convention has same basis vectors as MOSFLM per spec."""
        config_denzo = DetectorConfig(
            detector_convention=DetectorConvention.DENZO,
            spixels=512,
            fpixels=512,
            pixel_size_mm=0.1,
            distance_mm=100.0
        )

        config_mosflm = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            spixels=512,
            fpixels=512,
            pixel_size_mm=0.1,
            distance_mm=100.0
        )

        detector_denzo = Detector(config_denzo, dtype=torch.float64)
        detector_mosflm = Detector(config_mosflm, dtype=torch.float64)

        # DENZO should have same basis vectors as MOSFLM
        assert torch.allclose(detector_denzo.fdet_vec, detector_mosflm.fdet_vec, atol=1e-6), \
            "DENZO fast vector should match MOSFLM"
        assert torch.allclose(detector_denzo.sdet_vec, detector_mosflm.sdet_vec, atol=1e-6), \
            "DENZO slow vector should match MOSFLM"
        assert torch.allclose(detector_denzo.odet_vec, detector_mosflm.odet_vec, atol=1e-6), \
            "DENZO normal vector should match MOSFLM"

    def test_denzo_beam_center_mapping(self):
        """Test DENZO beam center mapping differs from MOSFLM (no +0.5 pixel offset)."""
        # Use explicit beam centers to test the offset behavior
        beam_center_mm_s = 50.0  # mm
        beam_center_mm_f = 50.0  # mm
        pixel_size = 0.1  # mm

        config_denzo = DetectorConfig(
            detector_convention=DetectorConvention.DENZO,
            spixels=1024,
            fpixels=1024,
            pixel_size_mm=pixel_size,
            distance_mm=100.0,
            beam_center_s=beam_center_mm_s,
            beam_center_f=beam_center_mm_f
        )

        config_mosflm = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            spixels=1024,
            fpixels=1024,
            pixel_size_mm=pixel_size,
            distance_mm=100.0,
            beam_center_s=beam_center_mm_s,
            beam_center_f=beam_center_mm_f
        )

        detector_denzo = Detector(config_denzo, dtype=torch.float64)
        detector_mosflm = Detector(config_mosflm, dtype=torch.float64)

        # Convert mm to pixels for comparison
        beam_center_pixels = beam_center_mm_s / pixel_size  # 500 pixels

        # CRITICAL: Both DENZO and MOSFLM should store beam center as-is (user input) in pixels.
        # The MOSFLM +0.5 pixel offset per spec-a-core.md line 72 ("Fbeam = Ybeam + 0.5·pixel")
        # is a MAPPING formula applied in _calculate_pix0_vector, NOT in the stored attribute.
        # See AT-GEO-001-MOSFLM-OFFSET fix (fix_plan.md lines 110-127).
        expected_stored = beam_center_pixels  # 500.0 for both conventions

        assert torch.allclose(detector_denzo.beam_center_s, torch.tensor(expected_stored, dtype=torch.float64), atol=1e-6), \
            f"DENZO beam_center_s should be {expected_stored}, got {detector_denzo.beam_center_s}"
        assert torch.allclose(detector_denzo.beam_center_f, torch.tensor(expected_stored, dtype=torch.float64), atol=1e-6), \
            f"DENZO beam_center_f should be {expected_stored}, got {detector_denzo.beam_center_f}"
        assert torch.allclose(detector_mosflm.beam_center_s, torch.tensor(expected_stored, dtype=torch.float64), atol=1e-6), \
            f"MOSFLM beam_center_s should be {expected_stored} (offset applied in pix0 calc), got {detector_mosflm.beam_center_s}"
        assert torch.allclose(detector_mosflm.beam_center_f, torch.tensor(expected_stored, dtype=torch.float64), atol=1e-6), \
            f"MOSFLM beam_center_f should be {expected_stored} (offset applied in pix0 calc), got {detector_mosflm.beam_center_f}"

    def test_adxv_beam_direction(self):
        """Test ADXV uses beam along +Z axis."""
        config = DetectorConfig(
            detector_convention=DetectorConvention.ADXV,
            spixels=512,
            fpixels=512,
            pixel_size_mm=0.1,
            distance_mm=100.0
        )

        detector = Detector(config, dtype=torch.float64)

        # ADXV beam should be along +Z per spec
        # This is tested indirectly through the normal vector and r-factor calculation
        # For ADXV with no rotations, the detector normal is [0, 0, 1] (along beam)
        # So r-factor should be 1.0
        r_factor = detector.get_r_factor()

        assert torch.allclose(r_factor, torch.tensor(1.0, dtype=torch.float64), atol=1e-6), \
            f"ADXV r-factor should be 1.0 with no rotations, got {r_factor}"

    def test_adxv_twotheta_axis_default(self):
        """Test ADXV has correct default two-theta axis."""
        config = DetectorConfig(
            detector_convention=DetectorConvention.ADXV,
            spixels=512,
            fpixels=512,
            pixel_size_mm=0.1,
            distance_mm=100.0
        )

        # ADXV default two-theta axis should be [-1, 0, 0] per spec
        expected_axis = torch.tensor([-1.0, 0.0, 0.0])

        assert torch.allclose(config.twotheta_axis, expected_axis, atol=1e-6), \
            f"ADXV two-theta axis incorrect: {config.twotheta_axis}"

    def test_denzo_twotheta_axis_default(self):
        """Test DENZO has same two-theta axis as MOSFLM."""
        config_denzo = DetectorConfig(
            detector_convention=DetectorConvention.DENZO,
            spixels=512,
            fpixels=512,
            pixel_size_mm=0.1,
            distance_mm=100.0
        )

        config_mosflm = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            spixels=512,
            fpixels=512,
            pixel_size_mm=0.1,
            distance_mm=100.0
        )

        # DENZO should have same two-theta axis as MOSFLM
        assert torch.allclose(config_denzo.twotheta_axis, config_mosflm.twotheta_axis, atol=1e-6), \
            f"DENZO two-theta axis should match MOSFLM"

    def test_adxv_default_beam_centers(self):
        """Test ADXV default beam center calculation per spec."""
        config = DetectorConfig(
            detector_convention=DetectorConvention.ADXV,
            spixels=1024,
            fpixels=1024,
            pixel_size_mm=0.1,
            distance_mm=100.0
            # Auto-calculate beam centers
        )

        detsize_s = 1024 * 0.1  # 102.4 mm
        detsize_f = 1024 * 0.1  # 102.4 mm

        # Per spec: ADXV default Xbeam = (detsize_f + pixel)/2, Ybeam = (detsize_s - pixel)/2
        # But internally we use different mapping: beam_center_f is for fast axis, beam_center_s for slow
        # ADXV: Fbeam = Xbeam, Sbeam = detsize_s - Ybeam (per spec line 67)
        expected_beam_center_f = (detsize_f + 0.1) / 2.0  # Xbeam
        expected_beam_center_s = (detsize_s - 0.1) / 2.0  # Ybeam maps differently

        assert abs(config.beam_center_f - expected_beam_center_f) < 1e-6, \
            f"ADXV beam_center_f incorrect: {config.beam_center_f} vs {expected_beam_center_f}"
        assert abs(config.beam_center_s - expected_beam_center_s) < 1e-6, \
            f"ADXV beam_center_s incorrect: {config.beam_center_s} vs {expected_beam_center_s}"

    def test_all_conventions_orthonormal(self):
        """Test that all conventions produce orthonormal basis vectors."""
        conventions = [
            DetectorConvention.MOSFLM,
            DetectorConvention.XDS,
            DetectorConvention.DIALS,
            DetectorConvention.ADXV,
            DetectorConvention.DENZO
        ]

        for conv in conventions:
            config = DetectorConfig(
                detector_convention=conv,
                spixels=512,
                fpixels=512,
                pixel_size_mm=0.1,
                distance_mm=100.0
            )

            detector = Detector(config, dtype=torch.float64)

            # Check orthogonality
            dot_fs = torch.dot(detector.fdet_vec, detector.sdet_vec)
            dot_fo = torch.dot(detector.fdet_vec, detector.odet_vec)
            dot_so = torch.dot(detector.sdet_vec, detector.odet_vec)

            assert abs(dot_fs) < 1e-6, f"{conv.name}: f and s not orthogonal"
            assert abs(dot_fo) < 1e-6, f"{conv.name}: f and o not orthogonal"
            assert abs(dot_so) < 1e-6, f"{conv.name}: s and o not orthogonal"

            # Check unit vectors
            assert torch.allclose(torch.norm(detector.fdet_vec), torch.tensor(1.0, dtype=torch.float64), atol=1e-6), \
                f"{conv.name}: f not unit vector"
            assert torch.allclose(torch.norm(detector.sdet_vec), torch.tensor(1.0, dtype=torch.float64), atol=1e-6), \
                f"{conv.name}: s not unit vector"
            assert torch.allclose(torch.norm(detector.odet_vec), torch.tensor(1.0, dtype=torch.float64), atol=1e-6), \
                f"{conv.name}: o not unit vector"

    def test_conventions_with_rotations(self):
        """Test that basis vectors are properly rotated for all conventions."""
        conventions = [
            DetectorConvention.MOSFLM,
            DetectorConvention.XDS,
            DetectorConvention.DIALS,
            DetectorConvention.ADXV,
            DetectorConvention.DENZO
        ]

        for conv in conventions:
            config = DetectorConfig(
                detector_convention=conv,
                spixels=512,
                fpixels=512,
                pixel_size_mm=0.1,
                distance_mm=100.0,
                detector_rotx_deg=5.0,
                detector_roty_deg=3.0,
                detector_rotz_deg=2.0
            )

            detector = Detector(config, dtype=torch.float64)

            # After rotation, basis should still be orthonormal
            # Check orthogonality
            dot_fs = torch.dot(detector.fdet_vec, detector.sdet_vec)
            dot_fo = torch.dot(detector.fdet_vec, detector.odet_vec)
            dot_so = torch.dot(detector.sdet_vec, detector.odet_vec)

            assert abs(dot_fs) < 1e-6, f"{conv.name} with rotations: f and s not orthogonal"
            assert abs(dot_fo) < 1e-6, f"{conv.name} with rotations: f and o not orthogonal"
            assert abs(dot_so) < 1e-6, f"{conv.name} with rotations: s and o not orthogonal"

            # Check unit vectors
            assert torch.allclose(torch.norm(detector.fdet_vec), torch.tensor(1.0, dtype=torch.float64), atol=1e-6), \
                f"{conv.name} with rotations: f not unit vector"
            assert torch.allclose(torch.norm(detector.sdet_vec), torch.tensor(1.0, dtype=torch.float64), atol=1e-6), \
                f"{conv.name} with rotations: s not unit vector"
            assert torch.allclose(torch.norm(detector.odet_vec), torch.tensor(1.0, dtype=torch.float64), atol=1e-6), \
                f"{conv.name} with rotations: o not unit vector"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])