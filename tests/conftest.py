"""
Test configuration and fixtures for nanoBragg PyTorch tests.

This file contains pytest configuration, fixtures, and environment setup
that is shared across all test modules.
"""

import os
import subprocess
import sys
from pathlib import Path
import pytest

# Set environment variable to prevent MKL library conflicts with PyTorch
# This must be set before importing torch in any test module
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Add src to path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def pytest_configure(config):
    """
    Auto-compile test dependencies if needed.
    
    This runs once at the start of the test session to ensure all required
    binaries are available.
    """
    # Check if we should skip compilation (e.g., in CI environments without gcc)
    if os.environ.get("SKIP_TEST_COMPILATION") == "1":
        return
    
    # Define required binaries and how to build them
    required_binaries = [
        {
            "path": Path("golden_suite_generator/nanoBragg_trace"),
            "build_cmd": ["make", "-C", "golden_suite_generator", "nanoBragg_trace"],
            "description": "C reference binary for trace validation"
        },
        {
            "path": Path("nanoBragg_config"),
            "build_cmd": ["make", "-C", "golden_suite_generator", "nanoBragg_config"],
            "description": "C binary for configuration consistency tests"
        },
    ]
    
    # Check and build each required binary
    for binary_info in required_binaries:
        binary_path = binary_info["path"]
        
        if not binary_path.exists():
            print(f"\n🔨 Building {binary_info['description']}...")
            print(f"   Binary: {binary_path}")
            
            try:
                result = subprocess.run(
                    binary_info["build_cmd"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and binary_path.exists():
                    print(f"   ✅ Successfully built {binary_path.name}")
                else:
                    # Compilation failed - provide helpful message
                    print(f"   ⚠️  Failed to build {binary_path.name}")
                    if result.stderr:
                        print(f"   Error: {result.stderr[:500]}")  # First 500 chars of error
                    print(f"\n   To manually build, run: {' '.join(binary_info['build_cmd'])}")
                    print(f"   Or set SKIP_TEST_COMPILATION=1 to skip compilation attempts")
                    
                    # Don't exit - let tests handle missing binaries with skipif
                    
            except subprocess.TimeoutExpired:
                print(f"   ⚠️  Build timed out for {binary_path.name}")
                print(f"   To manually build, run: {' '.join(binary_info['build_cmd'])}")
                
            except FileNotFoundError as e:
                # make or gcc not found
                print(f"   ⚠️  Build tools not found: {e}")
                print(f"   Please ensure 'make' and 'gcc' are installed")
                print(f"   Or set SKIP_TEST_COMPILATION=1 to skip compilation")
                
            except Exception as e:
                print(f"   ⚠️  Unexpected error building {binary_path.name}: {e}")
    
    print()  # Empty line for cleaner output


# Import torch after setting environment variable
import torch


@pytest.fixture(scope="session")
def device():
    """
    Fixture that provides the appropriate torch device for testing.
    
    By default uses CPU for reproducibility and golden data comparison.
    Set environment variable NANOBRAGG_TEST_DEVICE=cuda to test on GPU.
    
    Usage:
        def test_something(device):
            tensor = torch.tensor([1.0], device=device)
    """
    device_str = os.environ.get("NANOBRAGG_TEST_DEVICE", "cpu")
    
    if device_str == "cuda":
        if not torch.cuda.is_available():
            pytest.skip("CUDA requested but not available")
        print(f"\n🎮 Running tests on GPU: {torch.cuda.get_device_name(0)}")
    
    return torch.device(device_str)


@pytest.fixture(scope="session") 
def dtype():
    """
    Fixture that provides the default dtype for testing.
    
    Uses float64 for maximum precision in comparisons with C code.
    """
    return torch.float64


def pytest_collection_modifyitems(config, items):
    """
    Automatically mark tests that require specific binaries.
    
    This allows us to skip tests gracefully when binaries are missing,
    rather than having them fail.
    """
    # Check which binaries are available
    nanoBragg_trace_available = Path("golden_suite_generator/nanoBragg_trace").exists()
    nanoBragg_config_available = Path("./nanoBragg_config").exists()
    
    for item in items:
        # Skip configuration tests if nanoBragg_config is missing
        if "test_configuration_consistency" in str(item.fspath):
            if not nanoBragg_config_available:
                skip_marker = pytest.mark.skip(reason="nanoBragg_config binary not available")
                item.add_marker(skip_marker)