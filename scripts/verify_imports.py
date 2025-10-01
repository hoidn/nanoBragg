#!/usr/bin/env python3
"""
Import Verification Script for nanoBragg PyTorch Implementation

This script verifies that all critical import patterns work correctly.
Run this to troubleshoot import issues.
"""

import os
import sys
from typing import List, Tuple

# Set required environment variable for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


def test_imports() -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Test all critical import patterns.

    Returns:
        Tuple of (successful_imports, failed_imports_with_errors)
    """
    # Import patterns to test
    test_cases = [
        # Basic package import
        "import nanobrag_torch",

        # Package-level imports (after pip install -e .)
        "from nanobrag_torch.models.detector import Detector",
        "from nanobrag_torch.models.crystal import Crystal",
        "from nanobrag_torch.simulator import Simulator",
        "from nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig",
        "from nanobrag_torch.config import DetectorConvention, DetectorPivot",

        # Utility imports (using actual function names)
        "from nanobrag_torch.utils.geometry import angles_to_rotation_matrix",
        "from nanobrag_torch.utils.physics import polarization_factor",
        "from nanobrag_torch.utils.noise import generate_poisson_noise",

        # I/O imports (using actual function names)
        "from nanobrag_torch.io.hkl import read_hkl_file",
        "from nanobrag_torch.io.smv import read_smv",

        # Development imports (using src/ path)
        "from src.nanobrag_torch.models.detector import Detector",
        "from src.nanobrag_torch.config import DetectorConfig",
    ]

    successful = []
    failed = []

    for test_import in test_cases:
        try:
            exec(test_import)
            successful.append(test_import)
        except ImportError as e:
            failed.append((test_import, str(e)))
        except Exception as e:
            failed.append((test_import, f"Unexpected error: {e}"))

    return successful, failed


def test_problematic_imports() -> List[Tuple[str, str]]:
    """
    Test import patterns that should fail (to verify they fail correctly).

    Returns:
        List of (import_statement, error_message) for imports that unexpectedly succeeded
    """
    # These should all fail
    problematic_imports = [
        "from nanoBragg.detector import Detector",
        "from nanoBragg.components.detector import Detector",
        "from nanoBragg.models.detector import Detector",
        "import nanoBragg",
    ]

    unexpected_successes = []

    for import_stmt in problematic_imports:
        try:
            exec(import_stmt)
            unexpected_successes.append((import_stmt, "Import unexpectedly succeeded!"))
        except ImportError:
            # This is expected - the import should fail
            pass
        except Exception as e:
            unexpected_successes.append((import_stmt, f"Unexpected error type: {e}"))

    return unexpected_successes


def test_basic_functionality():
    """Test that basic functionality works after imports."""
    try:
        from nanobrag_torch.config import DetectorConfig
        from nanobrag_torch.models.detector import Detector

        # Create a simple detector to verify functionality
        config = DetectorConfig()
        detector = Detector(config)

        print("✓ Basic functionality test passed")
        return True

    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False


def main():
    """Main verification function."""
    print("=" * 60)
    print("nanoBragg PyTorch Import Verification")
    print("=" * 60)

    print("\n1. Testing valid import patterns...")
    successful, failed = test_imports()

    if successful:
        print(f"\n✅ Successfully imported {len(successful)} pattern(s):")
        for import_stmt in successful:
            print(f"   ✓ {import_stmt}")

    if failed:
        print(f"\n❌ Failed to import {len(failed)} pattern(s):")
        for import_stmt, error in failed:
            print(f"   ✗ {import_stmt}")
            print(f"     Error: {error}")

    print("\n2. Testing problematic import patterns (should fail)...")
    unexpected = test_problematic_imports()

    if not unexpected:
        print("✅ All problematic imports correctly failed")
    else:
        print(f"⚠️  {len(unexpected)} import(s) unexpectedly succeeded:")
        for import_stmt, message in unexpected:
            print(f"   ⚠️  {import_stmt}: {message}")

    print("\n3. Testing basic functionality...")
    functionality_ok = test_basic_functionality()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total_valid = len(successful) + len(failed)
    success_rate = (len(successful) / total_valid) * 100 if total_valid > 0 else 0

    # Separate src/ import failures (these are expected in some contexts)
    src_failures = [f for f in failed if "src.nanobrag_torch" in f[0]]
    critical_failures = [f for f in failed if "src.nanobrag_torch" not in f[0]]

    print(f"Valid imports:      {len(successful)}/{total_valid} ({success_rate:.1f}%)")
    print(f"Problematic checks: {'PASS' if not unexpected else 'FAIL'}")
    print(f"Functionality test: {'PASS' if functionality_ok else 'FAIL'}")

    if src_failures:
        print(f"Note: {len(src_failures)} src/ import(s) failed (may be expected)")

    # Overall assessment
    if len(critical_failures) == 0 and len(unexpected) == 0 and functionality_ok:
        print("\n🎉 ALL TESTS PASSED - Your import setup is working correctly!")
        if src_failures:
            print("Note: src/ imports failed, but this is normal unless you're running from the repo root with sys.path modifications")
        return 0
    elif len(successful) > 0 and functionality_ok and len(critical_failures) == 0:
        print("\n✅ SUCCESS - All critical imports working correctly!")
        if src_failures:
            print("Note: src/ imports are not working, but package imports are fine")
        return 0
    elif len(successful) > 0 and functionality_ok:
        print("\n⚠️  PARTIAL SUCCESS - Some imports work, but there may be setup issues")
        if critical_failures:
            print("\nTROUBLESHOOTING:")
            print("- Try installing the package: pip install -e .")
            print("- Make sure you're in the nanoBragg repository directory")
        return 1
    else:
        print("\n❌ MAJOR ISSUES - Most imports are failing")
        print("\nTROUBLESHOOTING:")
        print("1. Make sure you're in the nanoBragg repository directory")
        print("2. Try installing the package: pip install -e .")
        print("3. Check that src/nanobrag_torch/ directory exists")
        print("4. Verify Python can find the package: python -c 'import sys; print(sys.path)'")
        return 2


if __name__ == "__main__":
    sys.exit(main())