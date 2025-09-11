#!/usr/bin/env python3
"""
Critical tests for configuration consistency between C and PyTorch implementations.

These tests would have prevented 3-6 months of debugging by catching configuration
mismatches early.
"""

import os
import sys
import subprocess
import tempfile
import re
import pytest
from pathlib import Path

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.nanobrag_torch.config import DetectorConfig, DetectorConvention
from src.nanobrag_torch.models.detector import Detector
import torch


def extract_config_from_output(output: str) -> dict:
    """Extract configuration information from C or PyTorch output."""
    config = {}
    
    # Extract CONFIG_MODE
    mode_match = re.search(r'CONFIG_MODE:\s*(\w+)', output)
    if mode_match:
        config['mode'] = mode_match.group(1)
    
    # Extract CONFIG_TRIGGER
    trigger_match = re.search(r'CONFIG_TRIGGER:\s*(.+)', output)
    if trigger_match:
        config['trigger'] = trigger_match.group(1).strip()
    
    # Extract CONFIG_HASH
    hash_match = re.search(r'CONFIG_HASH:\s*(\w+)', output)
    if hash_match:
        config['hash'] = hash_match.group(1)
    
    return config


def run_c_nanoBragg(params: list) -> dict:
    """Run C nanoBragg with given parameters and extract configuration."""
    # Use the compiled version with config echo
    nanoBragg_path = "./nanoBragg_config"
    
    # Basic command
    cmd = [nanoBragg_path]
    cmd.extend(["-lambda", "6.2"])
    cmd.extend(["-N", "1"])
    cmd.extend(["-cell", "100", "100", "100", "90", "90", "90"])
    cmd.extend(["-default_F", "100"])
    cmd.extend(["-distance", "100"])
    cmd.extend(["-detpixels", "1024"])
    
    # Add custom parameters
    cmd.extend(params)
    
    # Output file
    with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as tmp:
        cmd.extend(["-floatfile", tmp.name])
        temp_file = tmp.name
    
    try:
        # Run command and capture output
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout + result.stderr
        
        # Extract configuration
        config = extract_config_from_output(output)
        return config
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)


class TestConfigurationConsistency:
    """Tests to ensure configuration consistency between implementations.
    
    Note: These tests require a specially modified nanoBragg that outputs
    CONFIG_MODE, CONFIG_TRIGGER, and CONFIG_HASH information. The standard
    nanoBragg binary doesn't provide this output.
    """
    
    @pytest.mark.skip(reason="Requires special nanoBragg build with CONFIG output - not yet implemented")
    def test_mode_detection_accuracy(self):
        """Verify we correctly identify active mode from output."""
        # Test MOSFLM mode
        mosflm_config = run_c_nanoBragg([])
        assert mosflm_config['mode'] == 'MOSFLM', "Default should be MOSFLM"
        
        # Test XDS mode
        xds_config = run_c_nanoBragg(["-convention", "XDS"])
        assert xds_config['mode'] == 'XDS', "Should switch to XDS"
        
        # Test CUSTOM mode trigger from rotation
        custom_config = run_c_nanoBragg(["-detector_rotx", "45"])
        assert custom_config['mode'] == 'CUSTOM', "Rotation should trigger CUSTOM"
    
    @pytest.mark.skip(reason="Requires special nanoBragg build with CONFIG output - not yet implemented")
    def test_trigger_tracking(self):
        """Test that we correctly identify what triggered custom mode."""
        # Test detector rotation trigger
        rotx_config = run_c_nanoBragg(["-detector_rotx", "30"])
        assert rotx_config['mode'] == 'CUSTOM'
        assert 'detector_rotx' in rotx_config.get('trigger', ''), \
            f"Should identify rotx as trigger, got: {rotx_config.get('trigger')}"
        
        # Test beam center trigger
        beam_config = run_c_nanoBragg(["-Xbeam", "100"])
        assert beam_config['mode'] == 'CUSTOM'
        assert 'Xbeam' in beam_config.get('trigger', ''), \
            f"Should identify Xbeam as trigger, got: {beam_config.get('trigger')}"
    
    @pytest.mark.skip(reason="Requires special nanoBragg build with CONFIG output - not yet implemented")
    def test_all_vector_parameters_trigger_custom(self):
        """Verify all basis vector overrides trigger CUSTOM mode."""
        vector_params = [
            "-detector_fsx", "-detector_fsy", "-detector_fsz",
            "-detector_ssx", "-detector_ssy", "-detector_ssz",
            "-twotheta_axis"
        ]
        
        for param in vector_params:
            config = run_c_nanoBragg([param, "0.5"])
            assert config['mode'] == 'CUSTOM', \
                f"Parameter {param} should trigger CUSTOM mode"
            assert param.replace('-', '') in config.get('trigger', ''), \
                f"Should identify {param} as trigger"
    
    @pytest.mark.xfail(reason="C nanoBragg has known bug: passing default twotheta_axis switches to CUSTOM mode")
    def test_explicit_defaults_equal_implicit(self):
        """
        CRITICAL TEST: Explicit defaults must behave like implicit defaults.
        
        This is the test that would have caught the nanoBragg issue where
        passing -twotheta_axis 0 0 -1 (the MOSFLM default) switched the
        convention to CUSTOM.
        
        This test is marked as xfail because the C code currently has a bug
        where passing the default axis value switches to CUSTOM mode.
        """
        # Test 1: C implementation - implicit defaults
        c_implicit = run_c_nanoBragg([])
        
        # Test 2: C implementation - explicit MOSFLM defaults
        c_explicit = run_c_nanoBragg(["-twotheta_axis", "0", "0", "-1"])
        
        # CRITICAL ASSERTION: Mode must not change when passing default values
        # This will fail until the C code bug is fixed
        assert c_implicit['mode'] == c_explicit['mode'], (
            f"CRITICAL FAILURE: Explicit defaults changed mode from "
            f"{c_implicit['mode']} to {c_explicit['mode']}. "
            f"This is the exact bug that caused 3-6 months of debugging!"
        )
    
    @pytest.mark.skip(reason="TODO: Configuration echo feature not yet implemented")
    def test_configuration_echo_present(self):
        """Verify both implementations output configuration information."""
        # Test C implementation
        c_config = run_c_nanoBragg([])
        assert 'mode' in c_config, "C implementation must output CONFIG_MODE"
        assert 'trigger' in c_config, "C implementation must output CONFIG_TRIGGER"
        assert 'hash' in c_config, "C implementation must output CONFIG_HASH"
        
        # Test PyTorch implementation
        from io import StringIO
        import sys
        
        # Capture PyTorch output
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        
        try:
            config = DetectorConfig()
            detector = Detector(config)
            output = mystdout.getvalue()
        finally:
            sys.stdout = old_stdout
        
        py_config = extract_config_from_output(output)
        assert 'mode' in py_config, "PyTorch must output CONFIG_MODE"
        assert 'trigger' in py_config, "PyTorch must output CONFIG_TRIGGER"
        assert 'hash' in py_config, "PyTorch must output CONFIG_HASH"


if __name__ == "__main__":
    # Run the critical test
    test = TestConfigurationConsistency()
    
    print("Running critical test: explicit defaults equal implicit...")
    try:
        test.test_explicit_defaults_equal_implicit()
        print("✓ PASS: Explicit defaults behave like implicit defaults")
    except AssertionError as e:
        print(f"✗ FAIL: {e}")
        print("\nThis is expected! The C code currently has this bug.")
        print("The Configuration Consistency Initiative will fix this.")
    
    print("\nRunning other tests...")
    test.test_configuration_echo_present()
    print("✓ Configuration echo present in both implementations")
    
    test.test_mode_detection_accuracy()
    print("✓ Mode detection accurate")
    
    test.test_trigger_tracking()
    print("✓ Trigger tracking working")
    
    test.test_all_vector_parameters_trigger_custom()
    print("✓ All vector parameters trigger CUSTOM mode")
    
    print("\nAll tests complete!")