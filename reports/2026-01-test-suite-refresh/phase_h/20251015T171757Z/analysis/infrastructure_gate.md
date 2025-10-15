# Phase H Infrastructure Gate Notes

- NB_C_BIN resolved: <unset>
- Primary binary used: ./golden_suite_generator/nanoBragg
- Golden asset hashes recorded in checks/golden_assets.txt
- Next steps: outline pytest collection-time fixture assertions per plans/active/test-suite-triage-phase-h.md

## Infrastructure Findings

### C Binary Resolution
- **Status:** ✅ PASSED
- **Resolved Path:** `./golden_suite_generator/nanoBragg`
- **Executable:** Yes (0775 permissions)
- **Size:** 139552 bytes
- **SHA256:** `eec0f143648d3826017e3635b9b4adb1b1e3cbd9d0a1994bf594d6cd23049eb3`
- **Help Command:** Successfully executed in <10s timeout
- **Fallback Precedence:** Used fallback_golden (`./golden_suite_generator/nanoBragg`) since NB_C_BIN environment variable is unset

### Golden Asset Verification
- **Status:** ✅ PASSED
- **Assets Checked:**
  1. `scaled.hkl`
     - Size: 1350993 bytes
     - SHA256: `65b668b3fa5c4de14c9049d9262945453d982ff193b572358846f38b173855ba`
     - Modified: Oct 6 23:39
  2. `reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json`
     - Size: 438 bytes
     - SHA256: `0fee99285f8fb7331db5b7b2d7b5bece3313e0aef80df45482d8ec742f6892cd`
     - Modified: Oct 6 12:44

- **Provenance:** Assets generated during CLI-FLAGS-003 Phase H/L work (October 6, 2025) per `docs/fix_plan.md` Attempt #6 notes

## Proposed pytest Collection-Time Fixture Strategy

### Fixture 1: `session_infrastructure_gate` (session-scoped)

**Purpose:** Validate infrastructure prerequisites at test collection time before any test execution begins

**Implementation Location:** `tests/conftest.py` (add new fixture)

**Validation Logic:**
```python
@pytest.fixture(scope="session", autouse=True)
def session_infrastructure_gate():
    """
    Validate infrastructure prerequisites at pytest session start.

    Checks:
    1. C binary resolution (NB_C_BIN precedence: env -> golden_suite_generator -> root)
    2. C binary executability (can run -help command)
    3. Golden asset availability (scaled.hkl, pix0_expected.json)

    Fails fast with actionable error messages if prerequisites are missing.

    References:
    - docs/development/testing_strategy.md §1.5 (Do Now expectations)
    - docs/development/c_to_pytorch_config_map.md (NB_C_BIN precedence)
    - plans/active/cli-noise-pix0/plan.md (asset provenance)
    """
    import os
    import subprocess
    from pathlib import Path

    errors = []

    # Check 1: C binary resolution
    nb_c_bin = os.environ.get('NB_C_BIN')
    if nb_c_bin:
        c_binary_path = Path(nb_c_bin)
    elif Path('./golden_suite_generator/nanoBragg').exists():
        c_binary_path = Path('./golden_suite_generator/nanoBragg')
    elif Path('./nanoBragg').exists():
        c_binary_path = Path('./nanoBragg')
    else:
        errors.append(
            "C binary not found. Expected NB_C_BIN env var or "
            "./golden_suite_generator/nanoBragg or ./nanoBragg"
        )
        c_binary_path = None

    # Check 2: C binary executability
    if c_binary_path and c_binary_path.exists():
        if not os.access(c_binary_path, os.X_OK):
            errors.append(f"C binary not executable: {c_binary_path}")
        else:
            try:
                result = subprocess.run(
                    [str(c_binary_path), '-help'],
                    capture_output=True,
                    timeout=10,
                    text=True
                )
                # nanoBragg -help exits with error code but produces help text
                if 'usage: nanoBragg' not in result.stderr:
                    errors.append(f"C binary failed to produce help text: {c_binary_path}")
            except subprocess.TimeoutExpired:
                errors.append(f"C binary -help command timed out: {c_binary_path}")
            except Exception as e:
                errors.append(f"C binary execution failed: {c_binary_path} ({e})")

    # Check 3: Golden assets
    golden_assets = [
        'scaled.hkl',
        'reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json'
    ]
    for asset in golden_assets:
        asset_path = Path(asset)
        if not asset_path.exists():
            errors.append(f"Golden asset not found: {asset}")

    if errors:
        pytest.fail(
            "Infrastructure gate check failed:\n" +
            "\n".join(f"  - {err}" for err in errors) +
            "\n\nSee reports/2026-01-test-suite-refresh/phase_h/20251015T171757Z/ for details"
        )
```

**Expected Behavior:**
- **Pass:** All checks succeed, test suite proceeds normally
- **Fail:** Session aborts with clear error message before any test execution
- **Benefit:** Eliminates transient infrastructure failures seen in Phase B/E/G reruns

### Fixture 2: `gradient_policy_guard` (module-scoped, test_gradients.py only)

**Purpose:** Enforce NANOBRAGG_DISABLE_COMPILE=1 for gradient tests

**Implementation Location:** `tests/test_gradients.py` (add as class fixture or module fixture)

**Validation Logic:**
```python
@pytest.fixture(scope="module", autouse=True)
def gradient_policy_guard():
    """
    Enforce NANOBRAGG_DISABLE_COMPILE=1 environment variable for gradient tests.

    Gradient tests require compile guard to prevent torch.compile donated buffer
    interference with torch.autograd.gradcheck.

    References:
    - docs/development/testing_strategy.md §4.1 (gradient test requirements)
    - arch.md §15 (gradient test performance expectations)
    """
    import os
    if os.environ.get('NANOBRAGG_DISABLE_COMPILE') != '1':
        pytest.skip(
            "Gradient tests require NANOBRAGG_DISABLE_COMPILE=1 environment variable. "
            "Run with: env NANOBRAGG_DISABLE_COMPILE=1 pytest tests/test_gradients.py"
        )
```

**Expected Behavior:**
- **Pass:** NANOBRAGG_DISABLE_COMPILE=1 is set, gradient tests execute
- **Skip:** Environment variable not set, skip all gradient tests with clear message
- **Benefit:** Prevents C2 cluster donated-buffer errors from recurring

## Unanswered Questions

1. **C binary version tracking:** Should we record the C binary version/commit hash in fixture output to detect silent binary updates between test runs?

2. **Golden asset staleness:** Should fixtures check modification timestamps to warn if assets are stale (e.g., >30 days old)?

3. **NB_C_BIN precedence documentation:** Should we emit a warning when falling back to default paths instead of using an explicit NB_C_BIN environment variable?

4. **Fixture failure handling:** Should infrastructure gate failures be logged to a separate file for CI/CD diagnostics, or is pytest's built-in failure reporting sufficient?

5. **Phase J validation:** How should we test the fixtures themselves? Create a synthetic test environment with missing binaries/assets to verify failure messages?

## References

- C-to-PyTorch Config Map: `docs/development/c_to_pytorch_config_map.md` (NB_C_BIN precedence rules)
- Testing Strategy: `docs/development/testing_strategy.md` §§1.5, 2.5 (Do Now expectations, parity commands)
- CLI Noise Pix0 Plan: `plans/active/cli-noise-pix0/plan.md` (golden asset provenance)
- Phase G Summary: `reports/2026-01-test-suite-refresh/phase_g/20251015T163131Z/analysis/summary.md` (infrastructure gap analysis)
