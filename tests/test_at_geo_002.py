"""
Test for AT-GEO-002: Pivot defaults and overrides

From spec-a.md Acceptance Test:
- Setup A: Provide -distance only (no -close_distance), MOSFLM.
- Expectation: pivot SHALL be BEAM.
- Setup B: Provide -close_distance only.
- Expectation: pivot SHALL be SAMPLE.
- Setup C: Provide -pivot sample when -distance is also set.
- Expectation: pivot SHALL be SAMPLE (explicit override wins).
"""

import torch
import pytest
from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot


def test_at_geo_002_setup_a_distance_only():
    """Test AT-GEO-002 Setup A: -distance only → pivot SHALL be BEAM."""

    # Setup A: Only -distance provided, MOSFLM convention
    config = DetectorConfig.from_cli_args(
        distance_mm=150.0,  # Only -distance provided
        close_distance_mm=None,  # No -close_distance
        pivot=None,  # No explicit pivot override
        detector_convention=DetectorConvention.MOSFLM,
        pixel_size_mm=0.1,
        beam_center_f=51.2,
        beam_center_s=51.2
    )

    # Expectation: pivot SHALL be BEAM
    assert config.detector_pivot == DetectorPivot.BEAM, \
        f"Setup A failed: Expected BEAM pivot, got {config.detector_pivot}"

    # Verify distance is set correctly
    assert config.distance_mm == 150.0, \
        f"Setup A: Distance should be 150.0, got {config.distance_mm}"

    print("✅ AT-GEO-002 Setup A PASSED: -distance only → BEAM pivot")


def test_at_geo_002_setup_b_close_distance_only():
    """Test AT-GEO-002 Setup B: -close_distance only → pivot SHALL be SAMPLE."""

    # Setup B: Only -close_distance provided
    config = DetectorConfig.from_cli_args(
        distance_mm=None,  # No -distance
        close_distance_mm=200.0,  # Only -close_distance provided
        pivot=None,  # No explicit pivot override
        detector_convention=DetectorConvention.MOSFLM,
        pixel_size_mm=0.1,
        beam_center_f=51.2,
        beam_center_s=51.2
    )

    # Expectation: pivot SHALL be SAMPLE
    assert config.detector_pivot == DetectorPivot.SAMPLE, \
        f"Setup B failed: Expected SAMPLE pivot, got {config.detector_pivot}"

    # Verify close_distance is used as the actual distance
    assert config.distance_mm == 200.0, \
        f"Setup B: Distance should use close_distance value (200.0), got {config.distance_mm}"

    assert config.close_distance_mm == 200.0, \
        f"Setup B: close_distance_mm should be preserved as 200.0, got {config.close_distance_mm}"

    print("✅ AT-GEO-002 Setup B PASSED: -close_distance only → SAMPLE pivot")


def test_at_geo_002_setup_c_explicit_override():
    """Test AT-GEO-002 Setup C: Explicit -pivot override wins."""

    # Setup C: Both -distance and explicit -pivot sample provided
    config = DetectorConfig.from_cli_args(
        distance_mm=150.0,  # -distance is provided
        close_distance_mm=None,  # No -close_distance
        pivot="sample",  # Explicit pivot override to SAMPLE
        detector_convention=DetectorConvention.MOSFLM,
        pixel_size_mm=0.1,
        beam_center_f=51.2,
        beam_center_s=51.2
    )

    # Expectation: pivot SHALL be SAMPLE (explicit override wins)
    assert config.detector_pivot == DetectorPivot.SAMPLE, \
        f"Setup C failed: Expected SAMPLE pivot (override), got {config.detector_pivot}"

    # Verify distance is set correctly
    assert config.distance_mm == 150.0, \
        f"Setup C: Distance should be 150.0, got {config.distance_mm}"

    print("✅ AT-GEO-002 Setup C PASSED: Explicit -pivot override wins")


def test_at_geo_002_setup_c_beam_override():
    """Test AT-GEO-002 Setup C variant: Explicit -pivot beam with -close_distance."""

    # Setup C variant: -close_distance with explicit -pivot beam override
    config = DetectorConfig.from_cli_args(
        distance_mm=None,  # No -distance
        close_distance_mm=200.0,  # -close_distance provided
        pivot="beam",  # Explicit pivot override to BEAM
        detector_convention=DetectorConvention.MOSFLM,
        pixel_size_mm=0.1,
        beam_center_f=51.2,
        beam_center_s=51.2
    )

    # Expectation: pivot SHALL be BEAM (explicit override wins over close_distance)
    assert config.detector_pivot == DetectorPivot.BEAM, \
        f"Setup C variant failed: Expected BEAM pivot (override), got {config.detector_pivot}"

    # Verify close_distance is used as actual distance
    assert config.distance_mm == 200.0, \
        f"Setup C variant: Distance should use close_distance value (200.0), got {config.distance_mm}"

    print("✅ AT-GEO-002 Setup C variant PASSED: Explicit -pivot beam overrides close_distance default")


def test_at_geo_002_direct_instantiation():
    """Test AT-GEO-002 with direct DetectorConfig instantiation (backward compatibility)."""

    # Test direct instantiation with close_distance_mm
    config = DetectorConfig(
        distance_mm=100.0,  # Default value
        close_distance_mm=200.0,  # Provided close_distance
        detector_pivot=None,  # Let __post_init__ decide
        detector_convention=DetectorConvention.MOSFLM
    )

    # Should detect close_distance and set SAMPLE pivot
    assert config.detector_pivot == DetectorPivot.SAMPLE, \
        f"Direct instantiation with close_distance: Expected SAMPLE pivot, got {config.detector_pivot}"

    # Test direct instantiation with explicit pivot
    config2 = DetectorConfig(
        distance_mm=150.0,
        detector_pivot=DetectorPivot.BEAM,  # Explicit pivot
        detector_convention=DetectorConvention.MOSFLM
    )

    # Should keep explicit pivot
    assert config2.detector_pivot == DetectorPivot.BEAM, \
        f"Direct instantiation with explicit pivot: Expected BEAM pivot, got {config2.detector_pivot}"

    print("✅ AT-GEO-002 Direct instantiation tests PASSED")


def run_all_tests():
    """Run all AT-GEO-002 tests."""
    test_at_geo_002_setup_a_distance_only()
    test_at_geo_002_setup_b_close_distance_only()
    test_at_geo_002_setup_c_explicit_override()
    test_at_geo_002_setup_c_beam_override()
    test_at_geo_002_direct_instantiation()
    print("\n🎉 ALL AT-GEO-002 TESTS PASSED!")


if __name__ == "__main__":
    run_all_tests()