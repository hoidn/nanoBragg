"""
Test configuration and fixtures for nanoBragg PyTorch tests.

This file contains pytest configuration, fixtures, and environment setup
that is shared across all test modules.
"""

import os
import sys
from pathlib import Path
import pytest
import subprocess

# Set environment variable to prevent MKL library conflicts with PyTorch
# This must be set before importing torch in any test module
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Add src to path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ============================================================================
# Phase K Task K1: Session Infrastructure Gate
# ============================================================================

def _resolve_c_binary():
    """
    Resolve C binary path using documented precedence order.

    Returns:
        Path object if resolved, None otherwise
    """
    nb_c_bin = os.environ.get('NB_C_BIN')
    if nb_c_bin:
        path = Path(nb_c_bin)
        if path.exists():
            return path
        else:
            # NB_C_BIN set but invalid - this is a user error, fail explicitly
            return None

    # Fallback 1: instrumented binary (recommended)
    fallback1 = Path('./golden_suite_generator/nanoBragg')
    if fallback1.exists():
        return fallback1

    # Fallback 2: frozen reference binary
    fallback2 = Path('./nanoBragg')
    if fallback2.exists():
        return fallback2

    return None


def _check_c_binary_executable(binary_path):
    """
    Verify C binary can execute -help command.

    Args:
        binary_path: Path object pointing to C binary

    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    if not os.access(binary_path, os.X_OK):
        return False, f"Binary not executable (missing execute permission): {binary_path}"

    try:
        result = subprocess.run(
            [str(binary_path), '-help'],
            capture_output=True,
            timeout=10,
            text=True
        )
        # nanoBragg exits with non-zero but produces help text on stdout
        if 'usage: nanobragg' in result.stdout.lower():
            return True, None
        else:
            return False, f"Binary failed to produce help text (stdout: {result.stdout[:200]}, stderr: {result.stderr[:200]})"
    except subprocess.TimeoutExpired:
        return False, f"Binary -help command timed out (>10s): {binary_path}"
    except Exception as e:
        return False, f"Binary execution failed: {binary_path} ({type(e).__name__}: {e})"


def _check_golden_assets():
    """
    Verify golden asset files exist and are readable.

    Returns:
        list: Empty if all checks pass, otherwise list of error messages
    """
    errors = []

    # Asset 1: scaled.hkl
    hkl_path = Path('scaled.hkl')
    if not hkl_path.exists():
        errors.append(
            "Golden asset not found: scaled.hkl\n"
            "  Generate via: python scripts/validation/create_scaled_hkl.py\n"
            "  See: docs/fix_plan.md Attempt #6 for provenance"
        )
    elif hkl_path.stat().st_size < 1_000_000:  # Expect ~1.35 MB
        errors.append(
            f"Golden asset corrupted (size {hkl_path.stat().st_size} bytes, expected ~1.35 MB): scaled.hkl"
        )

    # Asset 2: pix0_expected.json
    pix0_path = Path('reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json')
    if not pix0_path.exists():
        errors.append(
            "Golden asset not found: reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json\n"
            "  Regenerate via: plans/active/cli-noise-pix0/plan.md Phase H reproduction steps"
        )
    elif pix0_path.stat().st_size < 100:  # Expect ~438 bytes
        errors.append(
            f"Golden asset corrupted (size {pix0_path.stat().st_size} bytes, expected ~438 bytes): {pix0_path}"
        )

    return errors


@pytest.fixture(scope="session", autouse=True)
def session_infrastructure_gate():
    """
    Validate infrastructure prerequisites at pytest session start.

    See: reports/2026-01-test-suite-refresh/phase_j/20251015T180301Z/analysis/session_fixture_design.md
    """
    # Allow bypass for debugging (not recommended for CI)
    if os.environ.get('NB_SKIP_INFRA_GATE') == '1':
        import warnings
        warnings.warn(
            "Infrastructure gate bypassed (NB_SKIP_INFRA_GATE=1). "
            "This should only be used for debugging.",
            UserWarning
        )
        return

    errors = []

    # Check 1: C binary resolution
    c_binary_path = _resolve_c_binary()
    if c_binary_path is None:
        nb_c_bin = os.environ.get('NB_C_BIN')
        if nb_c_bin:
            errors.append(
                f"NB_C_BIN set but invalid: {nb_c_bin}\n"
                "  Verify path exists and is executable"
            )
        else:
            errors.append(
                "C binary not found. Expected one of:\n"
                "  1. NB_C_BIN environment variable pointing to binary\n"
                "  2. ./golden_suite_generator/nanoBragg (instrumented binary)\n"
                "  3. ./nanoBragg (frozen reference)\n"
                "  Rebuild with: make -C golden_suite_generator"
            )

    # Check 2: C binary executability
    if c_binary_path is not None:
        success, error_msg = _check_c_binary_executable(c_binary_path)
        if not success:
            errors.append(error_msg)

    # Check 3: Golden assets
    asset_errors = _check_golden_assets()
    errors.extend(asset_errors)

    # Fail fast if any checks failed
    if errors:
        pytest.fail(
            "\n" + "=" * 80 + "\n" +
            "Infrastructure Gate Check FAILED\n" +
            "=" * 80 + "\n" +
            "\n".join(f"  - {err}" for err in errors) + "\n\n" +
            "For details, see:\n"
            "  - reports/2026-01-test-suite-refresh/phase_h/20251015T171757Z/\n"
            "  - docs/development/testing_strategy.md S1.5\n"
            "  - plans/active/test-suite-triage-phase-h.md\n"
            "=" * 80
        )