#!/usr/bin/env python3
"""
Regression test for automatic pivot mode selection in C reference commands.

This test ensures that the fix for automatic pivot mode selection is working
correctly - when twotheta != 0, the C command should automatically include
'-pivot sample' regardless of the Python detector configuration.

Background:
- The C code nanoBragg.c automatically sets detector_pivot = SAMPLE when 
  -twotheta is specified (see nanoBragg.c line ~784)
- Our Python code needs to replicate this behavior when generating C commands
- Without this fix, correlation between Python and C drops to ~0.04 instead of >0.999

Test: https://github.com/project/nanoBragg/issues/pivot-mode-fix
"""

import pytest
from nanobrag_torch.config import BeamConfig, CrystalConfig, DetectorConfig, DetectorConvention, DetectorPivot
from scripts.c_reference_utils import build_nanobragg_command


class TestPivotModeSelection:
    """Test automatic pivot mode selection in C reference commands."""

    def test_twotheta_zero_uses_config_pivot(self):
        """When twotheta=0, should use the configured pivot mode."""
        # Test with BEAM pivot
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            beam_center_s=51.2,
            beam_center_f=51.2,
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM,
            detector_twotheta_deg=0.0,  # No twotheta
        )
        
        crystal_config = CrystalConfig()
        beam_config = BeamConfig()
        
        cmd = build_nanobragg_command(detector_config, crystal_config, beam_config)
        cmd_str = " ".join(cmd)
        
        # Should use the configured BEAM pivot
        assert "-pivot beam" in cmd_str
        assert "-pivot sample" not in cmd_str
        
        # Test with SAMPLE pivot
        detector_config.detector_pivot = DetectorPivot.SAMPLE
        cmd = build_nanobragg_command(detector_config, crystal_config, beam_config)
        cmd_str = " ".join(cmd)
        
        # Should use the configured SAMPLE pivot
        assert "-pivot sample" in cmd_str
        assert "-pivot beam" not in cmd_str

    def test_twotheta_nonzero_forces_sample_pivot(self):
        """When twotheta != 0, should always use SAMPLE pivot regardless of config."""
        crystal_config = CrystalConfig()
        beam_config = BeamConfig()
        
        # Test with BEAM configured but twotheta != 0
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            beam_center_s=51.2,
            beam_center_f=51.2,
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM,  # Configured as BEAM
            detector_twotheta_deg=15.0,  # But twotheta != 0
        )
        
        cmd = build_nanobragg_command(detector_config, crystal_config, beam_config)
        cmd_str = " ".join(cmd)
        
        # Should force SAMPLE pivot despite BEAM configuration
        assert "-pivot sample" in cmd_str
        assert "-pivot beam" not in cmd_str
        assert "-twotheta 15.0" in cmd_str
        
        # Test with SAMPLE configured and twotheta != 0 
        detector_config.detector_pivot = DetectorPivot.SAMPLE
        cmd = build_nanobragg_command(detector_config, crystal_config, beam_config)
        cmd_str = " ".join(cmd)
        
        # Should still use SAMPLE pivot
        assert "-pivot sample" in cmd_str
        assert "-pivot beam" not in cmd_str

    def test_small_twotheta_values(self):
        """Test edge cases with very small twotheta values."""
        crystal_config = CrystalConfig()
        beam_config = BeamConfig()
        
        # Test with tiny but non-zero twotheta (above 1e-6 threshold)
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            beam_center_s=51.2,
            beam_center_f=51.2,
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM,
            detector_twotheta_deg=2e-6,  # Very small but > 1e-6 threshold
        )
        
        cmd = build_nanobragg_command(detector_config, crystal_config, beam_config)
        cmd_str = " ".join(cmd)
        
        # Should still force SAMPLE pivot
        assert "-pivot sample" in cmd_str
        assert "-pivot beam" not in cmd_str
        
        # Test with value below threshold
        detector_config.detector_twotheta_deg = 1e-8  # Below 1e-6 threshold
        
        cmd = build_nanobragg_command(detector_config, crystal_config, beam_config)
        cmd_str = " ".join(cmd)
        
        # Should use configured pivot (BEAM)
        assert "-pivot beam" in cmd_str
        assert "-pivot sample" not in cmd_str
        assert "-twotheta" not in cmd_str  # Should not add twotheta parameter

    def test_negative_twotheta_forces_sample_pivot(self):
        """Test that negative twotheta values also force SAMPLE pivot."""
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            beam_center_s=51.2,
            beam_center_f=51.2,
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM,
            detector_twotheta_deg=-10.0,  # Negative twotheta
        )
        
        crystal_config = CrystalConfig()
        beam_config = BeamConfig()
        
        cmd = build_nanobragg_command(detector_config, crystal_config, beam_config)
        cmd_str = " ".join(cmd)
        
        # Should force SAMPLE pivot
        assert "-pivot sample" in cmd_str
        assert "-pivot beam" not in cmd_str
        assert "-twotheta -10.0" in cmd_str

    def test_pivot_fix_integration(self):
        """Integration test matching the original issue configuration."""
        # This replicates the exact configuration that was failing
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            beam_center_s=51.2,
            beam_center_f=51.2,
            detector_convention=DetectorConvention.MOSFLM,
            detector_rotx_deg=5.0,
            detector_roty_deg=3.0,
            detector_rotz_deg=2.0,
            detector_twotheta_deg=20.0,  # This should force SAMPLE pivot
            detector_pivot=DetectorPivot.SAMPLE,  # Even if explicitly set
        )
        
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5),
        )
        
        beam_config = BeamConfig(wavelength_A=6.2)
        
        cmd = build_nanobragg_command(detector_config, crystal_config, beam_config)
        cmd_str = " ".join(cmd)
        
        # Verify all expected parameters are present
        assert "-twotheta 20.0" in cmd_str
        assert "-detector_rotx 5.0" in cmd_str
        assert "-detector_roty 3.0" in cmd_str
        assert "-detector_rotz 2.0" in cmd_str
        assert "-pivot sample" in cmd_str
        assert "-pivot beam" not in cmd_str
        
        # Verify twotheta axis is NOT included for default MOSFLM
        # According to C-code logic, passing default MOSFLM axis triggers CUSTOM convention
        assert "-twotheta_axis" not in cmd_str


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])