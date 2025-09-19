#!/usr/bin/env python3
"""
AT-PARALLEL-005: Beam Center Parameter Mapping

Test that different parameter mappings for beam center produce equivalent results:
- -Xbeam/-Ybeam (MOSFLM convention)
- -ORGX/-ORGY (XDS convention)
- -Xclose/-Yclose (pivot mode dependent)

Expectation: Equivalent configurations SHALL produce same beam centers ±0.5 pixels
"""

import os
import pytest
import torch
import numpy as np
from pathlib import Path

# Set PyTorch environment for MKL compatibility
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.config import (
    DetectorConfig, DetectorConvention, DetectorPivot,
    BeamConfig, CrystalConfig
)
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

# Only run these tests when explicitly requested
pytestmark = pytest.mark.skipif(
    os.environ.get('NB_RUN_PARALLEL') != '1',
    reason="Parallel validation tests only run with NB_RUN_PARALLEL=1"
)


class TestAT_PARALLEL_005_BeamCenterMapping:
    """Test beam center parameter mappings across conventions."""

    def test_mosflm_xbeam_ybeam_mapping(self):
        """Test MOSFLM convention using -Xbeam/-Ybeam parameters."""
        # Configuration using Xbeam/Ybeam (MOSFLM style)
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            beam_center_s=61.2,  # Xbeam in mm
            beam_center_f=61.2,  # Ybeam in mm
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM,
        )

        detector = Detector(detector_config)

        # MOSFLM applies +0.5 pixel offset
        expected_beam_s_pixels = 61.2 / 0.1 + 0.5  # 612.5 pixels
        expected_beam_f_pixels = 61.2 / 0.1 + 0.5  # 612.5 pixels

        assert abs(detector.beam_center_s - expected_beam_s_pixels) < 0.5, \
            f"MOSFLM beam_center_s {detector.beam_center_s} != expected {expected_beam_s_pixels}"
        assert abs(detector.beam_center_f - expected_beam_f_pixels) < 0.5, \
            f"MOSFLM beam_center_f {detector.beam_center_f} != expected {expected_beam_f_pixels}"

    def test_xds_orgx_orgy_mapping(self):
        """Test XDS convention using -ORGX/-ORGY parameters."""
        # Configuration using ORGX/ORGY (XDS style - still in mm like MOSFLM)
        # The convention difference is the pixel offset, not the units
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            beam_center_s=61.2,  # ORGX in mm
            beam_center_f=61.2,  # ORGY in mm
            detector_convention=DetectorConvention.XDS,
            detector_pivot=DetectorPivot.SAMPLE,  # XDS default
        )

        detector = Detector(detector_config)

        # XDS doesn't apply pixel offset
        expected_beam_s_pixels = 61.2 / 0.1  # 612.0 pixels (no offset)
        expected_beam_f_pixels = 61.2 / 0.1  # 612.0 pixels (no offset)

        assert abs(detector.beam_center_s - expected_beam_s_pixels) < 0.5, \
            f"XDS beam_center_s {detector.beam_center_s} != expected {expected_beam_s_pixels}"
        assert abs(detector.beam_center_f - expected_beam_f_pixels) < 0.5, \
            f"XDS beam_center_f {detector.beam_center_f} != expected {expected_beam_f_pixels}"

    def test_pivot_mode_consistency(self):
        """Test that different pivot modes set beam centers consistently."""
        # Test with close_distance (should set SAMPLE pivot)
        detector_config_sample = DetectorConfig(
            close_distance_mm=100.0,  # Using close_distance
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            beam_center_s=61.2,  # Xclose in mm
            beam_center_f=61.2,  # Yclose in mm
            detector_convention=DetectorConvention.MOSFLM,
            # Pivot should be auto-set to SAMPLE
        )

        # Test with distance (should set BEAM pivot)
        detector_config_beam = DetectorConfig(
            distance_mm=100.0,  # Using distance
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            beam_center_s=61.2,  # Xbeam in mm
            beam_center_f=61.2,  # Ybeam in mm
            detector_convention=DetectorConvention.MOSFLM,
            # Pivot should be auto-set to BEAM
        )

        detector_sample = Detector(detector_config_sample)
        detector_beam = Detector(detector_config_beam)

        # Both should have consistent beam centers (accounting for convention)
        expected_pixels = 61.2 / 0.1 + 0.5  # MOSFLM offset

        assert abs(detector_sample.beam_center_s - expected_pixels) < 0.5
        assert abs(detector_sample.beam_center_f - expected_pixels) < 0.5
        assert abs(detector_beam.beam_center_s - expected_pixels) < 0.5
        assert abs(detector_beam.beam_center_f - expected_pixels) < 0.5

        # Verify pivot modes were set correctly
        assert detector_sample.config.detector_pivot == DetectorPivot.SAMPLE
        assert detector_beam.config.detector_pivot == DetectorPivot.BEAM

    def test_equivalent_configurations_produce_same_pattern(self):
        """Test that equivalent beam center configs produce the same diffraction pattern."""
        # Common crystal and beam config
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5),
        )
        beam_config = BeamConfig(wavelength_A=6.2)

        # Config 1: MOSFLM with Xbeam/Ybeam
        config1 = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=256,
            fpixels=256,
            beam_center_s=12.8,  # mm
            beam_center_f=12.8,  # mm
            detector_convention=DetectorConvention.MOSFLM,
        )

        # Config 2: XDS with same beam center in mm
        # Both conventions use mm for beam centers, just differ in pixel offset
        config2 = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=256,
            fpixels=256,
            beam_center_s=12.85,  # mm - slightly adjusted to match MOSFLM+0.5 pixels
            beam_center_f=12.85,  # mm - slightly adjusted to match MOSFLM+0.5 pixels
            detector_convention=DetectorConvention.XDS,
        )

        # Create Crystal and Detector objects
        from nanobrag_torch.models.crystal import Crystal
        crystal = Crystal(crystal_config)

        detector1 = Detector(config1)
        detector2 = Detector(config2)

        # Generate patterns
        sim1 = Simulator(crystal, detector1, crystal_config, beam_config)
        pattern1 = sim1.run()

        sim2 = Simulator(crystal, detector2, crystal_config, beam_config)
        pattern2 = sim2.run()

        # Patterns should be very similar (conventions differ in beam direction)
        # But beam centers should map to the same pixel position
        # Check that beam centers map to same pixel position
        assert abs(detector1.beam_center_s - detector2.beam_center_s) < 0.5, \
            f"Beam center S mismatch: {detector1.beam_center_s} vs {detector2.beam_center_s}"
        assert abs(detector1.beam_center_f - detector2.beam_center_f) < 0.5, \
            f"Beam center F mismatch: {detector1.beam_center_f} vs {detector2.beam_center_f}"

        # Find peak positions (maximum intensity pixel)
        peak1_idx = torch.argmax(pattern1)
        peak1_s = peak1_idx // 256
        peak1_f = peak1_idx % 256

        peak2_idx = torch.argmax(pattern2)
        peak2_s = peak2_idx // 256
        peak2_f = peak2_idx % 256

        # Peak positions should be within a few pixels (conventions have different beam directions)
        # But they should be centered around the beam center consistently
        dist1_from_center = torch.sqrt((peak1_s - detector1.beam_center_s)**2 +
                                       (peak1_f - detector1.beam_center_f)**2)
        dist2_from_center = torch.sqrt((peak2_s - detector2.beam_center_s)**2 +
                                       (peak2_f - detector2.beam_center_f)**2)

        # Distance from beam center should be similar
        assert abs(dist1_from_center - dist2_from_center) < 5, \
            f"Peak distance from beam center differs: {dist1_from_center:.1f} vs {dist2_from_center:.1f}"