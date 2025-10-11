"""
DETECTOR-CONFIG-001: Beam Center Source Tracking Tests

Tests for the beam_center_source attribute that distinguishes auto-calculated
beam centers from explicit user-provided values, ensuring the MOSFLM +0.5 pixel
offset is applied only to auto-calculated defaults per spec-a-core.md §72.
"""

import pytest
import torch
from src.nanobrag_torch.config import DetectorConfig, DetectorConvention
from src.nanobrag_torch.models.detector import Detector


class TestBeamCenterSource:
    """Test beam_center_source tracking and conditional MOSFLM offset application."""

    def test_mosflm_auto_calculated_applies_offset(self):
        """Test that MOSFLM convention applies +0.5 pixel offset for auto-calculated defaults.

        Per spec-a-core.md §72 and arch.md §ADR-03, the MOSFLM +0.5 pixel offset
        is part of the default beam center mapping formula and should be applied
        when beam centers are derived from detector size defaults.
        """
        # Setup: MOSFLM convention with auto-calculated beam centers
        config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=256,
            fpixels=256,
            beam_center_s=12.8,  # 256 * 0.1 / 2 = 12.8mm (detector center)
            beam_center_f=12.8,
            beam_center_source="auto",  # Explicitly mark as auto-calculated
        )

        detector = Detector(config)

        # Expected: beam_center in pixels = (12.8 / 0.1) + 0.5 = 128.5 pixels
        expected_pixels = 128.5

        assert abs(detector.beam_center_s.item() - expected_pixels) < 0.01, \
            f"MOSFLM auto beam_center_s should be 128.5, got {detector.beam_center_s.item()}"
        assert abs(detector.beam_center_f.item() - expected_pixels) < 0.01, \
            f"MOSFLM auto beam_center_f should be 128.5, got {detector.beam_center_f.item()}"

    def test_mosflm_explicit_no_offset(self):
        """Test that MOSFLM convention does NOT apply +0.5 pixel offset for explicit beam centers.

        Per DETECTOR-CONFIG-001 design, explicit user-provided beam centers should be
        used as-is without implicit adjustments. The +0.5 pixel offset is only for
        auto-calculated defaults.
        """
        # Setup: MOSFLM convention with explicit beam centers
        config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=256,
            fpixels=256,
            beam_center_s=12.8,  # User explicitly provides 12.8mm
            beam_center_f=12.8,
            beam_center_source="explicit",  # User-provided value
        )

        detector = Detector(config)

        # Expected: beam_center in pixels = 12.8 / 0.1 = 128.0 pixels (no offset)
        expected_pixels = 128.0

        assert abs(detector.beam_center_s.item() - expected_pixels) < 0.01, \
            f"MOSFLM explicit beam_center_s should be 128.0, got {detector.beam_center_s.item()}"
        assert abs(detector.beam_center_f.item() - expected_pixels) < 0.01, \
            f"MOSFLM explicit beam_center_f should be 128.0, got {detector.beam_center_f.item()}"

    def test_xds_no_offset_regardless_of_source(self):
        """Test that XDS convention never applies +0.5 pixel offset, regardless of source.

        The +0.5 pixel offset is specific to MOSFLM convention. XDS and other conventions
        should use beam centers as-is for both auto-calculated and explicit values.
        """
        # Test both auto and explicit sources with XDS convention
        for source in ["auto", "explicit"]:
            config = DetectorConfig(
                detector_convention=DetectorConvention.XDS,
                distance_mm=100.0,
                pixel_size_mm=0.1,
                spixels=256,
                fpixels=256,
                beam_center_s=12.8,
                beam_center_f=12.8,
                beam_center_source=source,
            )

            detector = Detector(config)

            # Expected: beam_center in pixels = 12.8 / 0.1 = 128.0 pixels (no offset)
            expected_pixels = 128.0

            assert abs(detector.beam_center_s.item() - expected_pixels) < 0.01, \
                f"XDS beam_center_s should be 128.0 for source={source}, got {detector.beam_center_s.item()}"
            assert abs(detector.beam_center_f.item() - expected_pixels) < 0.01, \
                f"XDS beam_center_f should be 128.0 for source={source}, got {detector.beam_center_f.item()}"

    def test_explicit_matches_default_value(self):
        """Test that explicit beam center takes precedence even when value matches default.

        Edge case: User provides explicit beam center that coincidentally equals the
        MOSFLM default formula. The system should NOT apply the +0.5 offset because
        the source flag indicates explicit input.
        """
        # Calculate what would be the MOSFLM default for this detector
        detector_size = 256
        pixel_size = 0.1
        # MOSFLM default formula: (detsize + pixel) / 2
        mosflm_default = (detector_size * pixel_size + pixel_size) / 2  # 12.85mm

        # User provides this exact value explicitly
        config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            distance_mm=100.0,
            pixel_size_mm=pixel_size,
            spixels=detector_size,
            fpixels=detector_size,
            beam_center_s=mosflm_default,
            beam_center_f=mosflm_default,
            beam_center_source="explicit",  # Source flag overrides value heuristic
        )

        detector = Detector(config)

        # Expected: Use explicit value as-is, no offset
        # 12.85 / 0.1 = 128.5 pixels (no additional offset)
        expected_pixels = mosflm_default / pixel_size

        assert abs(detector.beam_center_s.item() - expected_pixels) < 0.01, \
            f"Explicit beam_center_s should match provided value {expected_pixels}, got {detector.beam_center_s.item()}"
        assert abs(detector.beam_center_f.item() - expected_pixels) < 0.01, \
            f"Explicit beam_center_f should match provided value {expected_pixels}, got {detector.beam_center_f.item()}"

        # Verify this is different from what auto-calculated would give
        config_auto = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            distance_mm=100.0,
            pixel_size_mm=pixel_size,
            spixels=detector_size,
            fpixels=detector_size,
            beam_center_s=mosflm_default,
            beam_center_f=mosflm_default,
            beam_center_source="auto",  # Auto applies additional offset
        )

        detector_auto = Detector(config_auto)

        # Auto should add +0.5 offset: 128.5 + 0.5 = 129.0 pixels
        expected_auto_pixels = expected_pixels + 0.5

        assert abs(detector_auto.beam_center_s.item() - expected_auto_pixels) < 0.01, \
            f"Auto beam_center_s should be {expected_auto_pixels}, got {detector_auto.beam_center_s.item()}"

        # Verify explicit != auto (proves source flag matters)
        assert abs(detector.beam_center_s.item() - detector_auto.beam_center_s.item()) > 0.4, \
            "Explicit and auto beam centers should differ by ~0.5 pixels"

    def test_default_beam_center_source_is_auto(self):
        """Test that beam_center_source defaults to 'auto' for backward compatibility.

        When beam_center_source is not specified, it should default to "auto" to
        preserve existing behavior for code that doesn't set this field explicitly.
        """
        # Create config without specifying beam_center_source
        config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=256,
            fpixels=256,
            beam_center_s=12.8,
            beam_center_f=12.8,
            # beam_center_source not specified - should default to "auto"
        )

        # Verify default value
        assert config.beam_center_source == "auto", \
            f"beam_center_source should default to 'auto', got {config.beam_center_source}"

        detector = Detector(config)

        # With default "auto", MOSFLM should apply +0.5 offset
        expected_pixels = 128.5  # (12.8 / 0.1) + 0.5

        assert abs(detector.beam_center_s.item() - expected_pixels) < 0.01, \
            f"Default auto beam_center_s should be 128.5, got {detector.beam_center_s.item()}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
