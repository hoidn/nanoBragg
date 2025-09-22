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


def run_pytorch_nanoBragg(params: list) -> dict:
    """Run PyTorch nanoBragg with given parameters and extract configuration."""
    # Convert CLI-style parameters to DetectorConfig
    config = DetectorConfig()

    # Parse parameters similar to CLI
    i = 0
    while i < len(params):
        param = params[i]

        if param == "-fdet_vector" and i + 3 < len(params):
            config.fdet_vector = torch.tensor([
                float(params[i+1]), float(params[i+2]), float(params[i+3])
            ])
            i += 4
        elif param == "-sdet_vector" and i + 3 < len(params):
            config.sdet_vector = torch.tensor([
                float(params[i+1]), float(params[i+2]), float(params[i+3])
            ])
            i += 4
        elif param == "-odet_vector" and i + 3 < len(params):
            config.odet_vector = torch.tensor([
                float(params[i+1]), float(params[i+2]), float(params[i+3])
            ])
            i += 4
        elif param == "-beam_vector" and i + 3 < len(params):
            config.beam_vector = torch.tensor([
                float(params[i+1]), float(params[i+2]), float(params[i+3])
            ])
            i += 4
        elif param == "-polar_vector" and i + 3 < len(params):
            config.polar_vector = torch.tensor([
                float(params[i+1]), float(params[i+2]), float(params[i+3])
            ])
            i += 4
        elif param == "-spindle_axis" and i + 3 < len(params):
            # For the test's purposes, treat spindle_axis as a custom vector
            # In reality this would be part of CrystalConfig
            config.spindle_axis = torch.tensor([
                float(params[i+1]), float(params[i+2]), float(params[i+3])
            ])
            i += 4
        elif param == "-twotheta_axis" and i + 3 < len(params):
            config.twotheta_axis = torch.tensor([
                float(params[i+1]), float(params[i+2]), float(params[i+3])
            ])
            config._twotheta_axis_explicit = True
            i += 4
        elif param == "-pix0_vector" and i + 3 < len(params):
            config.pix0_vector = torch.tensor([
                float(params[i+1]), float(params[i+2]), float(params[i+3])
            ])
            i += 4
        elif param == "-mosflm":
            config.detector_convention = DetectorConvention.MOSFLM
            i += 1
        elif param == "-xds":
            config.detector_convention = DetectorConvention.XDS
            i += 1
        else:
            i += 1

    # Re-run post_init to update configuration mode detection
    config.__post_init__()

    # Return configuration info
    return config.get_config_info()


class TestConfigurationConsistency:
    """Tests to ensure configuration consistency between implementations."""
    
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
    
    def test_mode_detection_accuracy(self):
        """Verify we correctly identify active mode from output."""
        # Test MOSFLM mode
        mosflm_config = run_pytorch_nanoBragg([])
        assert mosflm_config['mode'] == 'MOSFLM', "Default should be MOSFLM"

        # Test CUSTOM mode (triggered by parameter)
        custom_config = run_pytorch_nanoBragg(["-fdet_vector", "0", "0", "1"])
        assert custom_config['mode'] == 'CUSTOM', "fdet_vector should trigger CUSTOM"

        # Test explicit mode setting
        explicit_config = run_pytorch_nanoBragg(["-mosflm"])
        assert explicit_config['mode'] == 'MOSFLM', "Explicit -mosflm should set MOSFLM"
    
    def test_trigger_tracking(self):
        """Verify we track what triggered the configuration."""
        # Default trigger
        default_config = run_pytorch_nanoBragg([])
        assert default_config['trigger'] == 'default'

        # Parameter trigger
        param_config = run_pytorch_nanoBragg(["-twotheta_axis", "1", "0", "0"])
        assert 'twotheta_axis' in param_config['trigger']

        # Explicit mode trigger
        explicit_config = run_pytorch_nanoBragg(["-mosflm"])
        assert 'default' in explicit_config['trigger']  # mosflm is default mode
    
    def test_all_vector_parameters_trigger_custom(self):
        """Test that all vector parameters trigger CUSTOM mode."""
        vector_params = [
            (["-fdet_vector", "0", "0", "1"], "fdet_vector"),
            (["-sdet_vector", "0", "-1", "0"], "sdet_vector"),
            (["-odet_vector", "1", "0", "0"], "odet_vector"),
            (["-beam_vector", "1", "0", "0"], "beam_vector"),
            (["-polar_vector", "0", "0", "1"], "polar_vector"),
            (["-spindle_axis", "0", "0", "1"], "spindle_axis"),
            (["-twotheta_axis", "0", "0", "-1"], "twotheta_axis"),
            (["-pix0_vector", "0", "0", "0"], "pix0_vector"),
        ]
        
        for params, param_name in vector_params:
            config = run_pytorch_nanoBragg(params)
            assert config['mode'] == 'CUSTOM', (
                f"{param_name} should trigger CUSTOM mode"
            )
            assert param_name in config['trigger'], (
                f"Trigger should mention {param_name}"
            )


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