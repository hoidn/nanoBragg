# Session Infrastructure Fixture (Phase J — Task J1)

## Purpose & Scope

**Objective:** Implement a pytest session-scoped fixture that validates infrastructure prerequisites at collection time, before any test execution begins. This fixture will eliminate transient infrastructure failures observed in Phase B/E/G reruns by failing fast with actionable error messages when prerequisites are missing.

**Scope:**
- C binary resolution and executability verification
- Golden asset availability checks
- Environment diagnostic reporting
- Clear remediation guidance in failure messages

**Out of Scope:**
- Runtime physics validation (covered by existing test suite)
- Performance benchmarking (covered by separate profiling workflows)
- Golden asset content validation (hashes checked separately, not during every session)

## Preconditions

**Required Files:**
- `tests/conftest.py` — pytest configuration file where fixture will be added
- `./golden_suite_generator/nanoBragg` OR `./nanoBragg` OR `$NB_C_BIN` — C reference binary
- `scaled.hkl` — HKL golden asset (1.3 MB, generated October 6, 2025)
- `reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json` — pix0 reference data

**Required Environment:**
- Repository root as working directory
- Editable install active (`pip install -e .`)
- Python >=3.11, pytest available

**Optional Environment Variables:**
- `NB_C_BIN` — explicit path to C binary (takes precedence over fallback paths)
- `NB_SKIP_INFRA_GATE` — set to `1` to bypass fixture for debugging (not recommended for CI)

## Implementation Design

### Fixture Signature

```python
@pytest.fixture(scope="session", autouse=True)
def session_infrastructure_gate():
    """
    Validate infrastructure prerequisites at pytest session start.

    This fixture runs once per test session (autouse=True) and checks:
    1. C binary resolution (NB_C_BIN env var or fallback paths)
    2. C binary executability (can run -help command)
    3. Golden asset availability (scaled.hkl, pix0_expected.json)

    Fails fast with actionable error messages if prerequisites are missing.

    References:
    - docs/development/testing_strategy.md S1.5 (Do Now expectations)
    - docs/development/c_to_pytorch_config_map.md (NB_C_BIN precedence)
    - plans/active/test-suite-triage-phase-h.md (Phase H infrastructure gate)
    - reports/2026-01-test-suite-refresh/phase_h/20251015T171757Z/analysis/infrastructure_gate.md

    Environment Variables:
    - NB_C_BIN: Explicit path to C binary (optional, takes precedence)
    - NB_SKIP_INFRA_GATE: Set to '1' to bypass checks (debugging only)
    """
```

### Resolution Logic (C Binary)

**Precedence Order:** (per `docs/development/c_to_pytorch_config_map.md`)
1. `$NB_C_BIN` environment variable (if set and non-empty)
2. `./golden_suite_generator/nanoBragg` (instrumented binary, recommended)
3. `./nanoBragg` (frozen reference binary)
4. **FAIL** with clear error message

**Implementation:**
```python
def _resolve_c_binary():
    """
    Resolve C binary path using documented precedence order.

    Returns:
        Path object if resolved, None otherwise
    """
    import os
    from pathlib import Path

    nb_c_bin = os.environ.get('NB_C_BIN')
    if nb_c_bin:
        path = Path(nb_c_bin)
        if path.exists():
            return path
        else:
            # NB_C_BIN set but invalid - this is a user error, fail explicitly
            return None  # Will trigger error with specific message

    # Fallback 1: instrumented binary (recommended)
    fallback1 = Path('./golden_suite_generator/nanoBragg')
    if fallback1.exists():
        return fallback1

    # Fallback 2: frozen reference binary
    fallback2 = Path('./nanoBragg')
    if fallback2.exists():
        return fallback2

    return None
```

### Executability Check

**Test Method:** Run `./nanoBragg -help` and verify:
- Command completes within 10s timeout
- stderr contains `usage: nanoBragg` (C binary writes help to stderr)
- No subprocess exceptions

**Implementation:**
```python
def _check_c_binary_executable(binary_path):
    """
    Verify C binary can execute -help command.

    Args:
        binary_path: Path object pointing to C binary

    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    import subprocess
    import os

    if not os.access(binary_path, os.X_OK):
        return False, f"Binary not executable (missing execute permission): {binary_path}"

    try:
        result = subprocess.run(
            [str(binary_path), '-help'],
            capture_output=True,
            timeout=10,
            text=True
        )
        # nanoBragg exits with non-zero but produces help text on stderr
        if 'usage: nanoBragg' in result.stderr.lower():
            return True, None
        else:
            return False, f"Binary failed to produce help text (stderr: {result.stderr[:200]})"
    except subprocess.TimeoutExpired:
        return False, f"Binary -help command timed out (>10s): {binary_path}"
    except Exception as e:
        return False, f"Binary execution failed: {binary_path} ({type(e).__name__}: {e})"
```

### Golden Asset Verification

**Assets to Check:**
1. `scaled.hkl` — 1.35 MB HKL file (generated CLI-FLAGS-003 Phase H, October 6, 2025)
2. `reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json` — 438 bytes JSON (pix0 reference)

**Check Method:**
- Use `Path.exists()` for presence check
- Optionally check `Path.stat().st_size` against expected sizes to detect corruption
- Do NOT validate hashes every session (too slow); hash checks are one-time verification

**Implementation:**
```python
def _check_golden_assets():
    """
    Verify golden asset files exist and are readable.

    Returns:
        list: Empty if all checks pass, otherwise list of error messages
    """
    from pathlib import Path

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
```

### Complete Fixture Implementation

```python
@pytest.fixture(scope="session", autouse=True)
def session_infrastructure_gate():
    """
    Validate infrastructure prerequisites at pytest session start.

    See: reports/2026-01-test-suite-refresh/phase_j/20251015T180301Z/analysis/session_fixture_design.md
    """
    import os

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
```

## Failure Messaging & Remediation Steps

### Failure Scenario 1: C Binary Not Found

**Error Message:**
```
Infrastructure Gate Check FAILED
  - C binary not found. Expected one of:
    1. NB_C_BIN environment variable pointing to binary
    2. ./golden_suite_generator/nanoBragg (instrumented binary)
    3. ./nanoBragg (frozen reference)
    Rebuild with: make -C golden_suite_generator
```

**Remediation:**
```bash
# Option A: Rebuild instrumented binary (recommended)
make -C golden_suite_generator

# Option B: Use frozen reference
export NB_C_BIN=./nanoBragg

# Option C: Point to custom build
export NB_C_BIN=/path/to/custom/nanoBragg
```

### Failure Scenario 2: C Binary Not Executable

**Error Message:**
```
Infrastructure Gate Check FAILED
  - Binary not executable (missing execute permission): ./golden_suite_generator/nanoBragg
```

**Remediation:**
```bash
chmod +x ./golden_suite_generator/nanoBragg
```

### Failure Scenario 3: Golden Assets Missing

**Error Message:**
```
Infrastructure Gate Check FAILED
  - Golden asset not found: scaled.hkl
    Generate via: python scripts/validation/create_scaled_hkl.py
    See: docs/fix_plan.md Attempt #6 for provenance
```

**Remediation:**
```bash
# Regenerate HKL asset
python scripts/validation/create_scaled_hkl.py

# Or restore from backup (if available)
git restore scaled.hkl
```

### Failure Scenario 4: NB_C_BIN Invalid Path

**Error Message:**
```
Infrastructure Gate Check FAILED
  - NB_C_BIN set but invalid: /nonexistent/path/nanoBragg
    Verify path exists and is executable
```

**Remediation:**
```bash
# Check current value
echo $NB_C_BIN

# Fix to valid path
export NB_C_BIN=./golden_suite_generator/nanoBragg

# Or unset to use fallback
unset NB_C_BIN
```

## Integration Points

**File:** `tests/conftest.py`

**Location:** Add fixture at top of file, after imports, before existing fixtures

**Dependencies:**
- `pytest` (already imported in conftest.py)
- `pathlib.Path` (standard library)
- `subprocess` (standard library)
- `os` (standard library)

**Interaction with Existing Fixtures:**
- `session_infrastructure_gate` runs first (session scope, autouse=True)
- Other fixtures can assume infrastructure is valid after this runs
- No circular dependencies expected

## Testing the Fixture

**Validation Strategy:** (per Phase J Task J3)

1. **Positive Test:** Verify fixture passes with valid infrastructure
   ```bash
   pytest --collect-only -q
   # Expected: collection succeeds, no errors
   ```

2. **Negative Test 1:** Missing C binary
   ```bash
   # Temporarily rename binary
   mv ./golden_suite_generator/nanoBragg ./golden_suite_generator/nanoBragg.backup
   pytest --collect-only -q
   # Expected: pytest.fail() with "C binary not found" message
   # Restore: mv ./golden_suite_generator/nanoBragg.backup ./golden_suite_generator/nanoBragg
   ```

3. **Negative Test 2:** Missing golden asset
   ```bash
   # Temporarily rename asset
   mv scaled.hkl scaled.hkl.backup
   pytest --collect-only -q
   # Expected: pytest.fail() with "Golden asset not found: scaled.hkl" message
   # Restore: mv scaled.hkl.backup scaled.hkl
   ```

4. **Bypass Test:** Verify NB_SKIP_INFRA_GATE bypass
   ```bash
   # Temporarily rename binary
   mv ./golden_suite_generator/nanoBragg ./golden_suite_generator/nanoBragg.backup
   NB_SKIP_INFRA_GATE=1 pytest --collect-only -q
   # Expected: UserWarning about bypass, collection proceeds
   # Restore: mv ./golden_suite_generator/nanoBragg.backup ./golden_suite_generator/nanoBragg
   ```

**Artifact Capture:**
- Run each validation command
- Save pytest output to `reports/2026-01-test-suite-refresh/phase_j/20251015T180301Z/validation/fixture_test_*.log`
- Record exit codes and error messages

## Open Questions

1. **Binary Version Tracking:** Should we capture and log the C binary SHA256 hash at session start for traceability? (Would add ~0.1s overhead but improve debugging for binary update issues)

2. **Asset Staleness Warnings:** Should we warn if golden assets are >30 days old? (Could indicate stale test environment)

3. **CI Environment Detection:** Should fixture behavior differ in CI vs. local? (e.g., stricter checks in CI, allow bypass locally)

4. **Performance Impact:** Session-scoped fixture runs once, but subprocess call to test binary adds ~0.5s overhead. Is this acceptable? (Alternative: skip -help check, only verify file exists)

5. **Partial Failure Handling:** Should fixture continue checking all prerequisites even if first check fails, or fail fast on first error? (Current design: collect all errors before failing)

## References

- **Authoritative Spec:** `docs/development/testing_strategy.md` S1.5 (Do Now + validation scripts)
- **C Binary Precedence:** `docs/development/c_to_pytorch_config_map.md` (NB_C_BIN resolution order)
- **Asset Provenance:** `plans/active/cli-noise-pix0/plan.md` (scaled.hkl generation commands)
- **Phase H Findings:** `reports/2026-01-test-suite-refresh/phase_h/20251015T171757Z/analysis/infrastructure_gate.md`
- **Plan Context:** `plans/active/test-suite-triage-phase-h.md` (Phase J Task J1)
