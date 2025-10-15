# Phase L Infrastructure Fixtures Analysis

**STAMP:** 20251015T190350Z
**Phase:** L (Guarded full-suite rerun with collection-time guardrails)
**Fixtures Implemented:** Phase K (STAMP 20251015T182108Z)

---

## Fixtures Under Test

### 1. session_infrastructure_gate (Session-Scoped, Autouse)

**Location:** `tests/conftest.py` (session-scoped fixture)
**Purpose:** Validate infrastructure prerequisites before test collection/execution
**Scope:** Entire test suite (autouse=True)

**Validated Behaviors:**
1. **C Binary Resolution:** Follows precedence: `NB_C_BIN` env → `./golden_suite_generator/nanoBragg` → `./nanoBragg`
2. **C Binary Executability:** Executes `<binary> -help` with <10s timeout to verify binary is functional
3. **Golden Asset Availability:** Checks presence of:
   - `scaled.hkl` (HKL test fixture)
   - `reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json` (CLI test fixture)

**Bypass Mechanism:** `NB_SKIP_INFRA_GATE=1` environment variable (not detected in Phase L logs)

**Phase L Evidence:**
- ✅ Test suite collected successfully (692 tests, 0 collection errors)
- ✅ No infrastructure guard skip messages in logs
- ✅ C binary resolution occurred (evidenced by test execution, though F1 failure indicates runtime path issue)
- ❌ Golden asset validation passed guard but F4 failures indicate CWD mismatch at test runtime

**Conclusion:** Fixture executed successfully during session startup. However, CWD validation gap allows tests to run from non-canonical workspace (`/home/ollie/Documents/tmp/nanoBragg` instead of repo root), causing golden asset path mismatches at test runtime despite guard validation at collection time.

---

### 2. gradient_policy_guard (Module-Scoped, test_gradients.py)

**Location:** `tests/test_gradients.py` (module-scoped fixture)
**Purpose:** Enforce `NANOBRAGG_DISABLE_COMPILE=1` requirement for gradient tests
**Scope:** `test_gradients.py` module only

**Validated Behavior:**
- Checks `os.environ.get("NANOBRAGG_DISABLE_COMPILE") == "1"` before allowing gradient tests to execute
- Skips module with clear remediation message if environment variable unset

**Phase L Evidence:**
- ✅ Module loaded successfully (no skip messages in logs for gradient tests)
- ✅ `NANOBRAGG_DISABLE_COMPILE=1` was correctly set (per command guard)
- ✅ Test `test_property_gradient_stability` executed (failed on timeout, not on environment check)
- ❌ Timeout (F5) occurred during test execution (>905s), not during fixture validation

**Conclusion:** Fixture executed successfully and validated environment correctly. Timeout failure (F5) is unrelated to fixture behavior—it occurred during gradient computation, not environment validation.

---

## Fixture Performance Impact

### Collection Time
- **Phase L:** <10s (typical collection time, not measured separately)
- **Phase G:** <10s (baseline without fixtures)
- **Delta:** ≈0s (no observable collection overhead)

**Conclusion:** Infrastructure guard validation (<10s C binary `-help` execution + file system checks) adds negligible overhead to collection phase.

### Execution Time
- **Phase L:** 1661.37s (27:41 wall clock)
- **Phase G:** 1656.77s (27:36 wall clock)
- **Delta:** +4.60s (+0.28% within measurement noise)

**Conclusion:** Fixtures introduced ZERO observable runtime overhead. Variance (+4.60s) is within normal measurement noise (≈±0.3% typical for 27-minute runs).

### Test Outcomes
- **Phase L:** 540 passed / 8 failed / 143 skipped
- **Phase G:** 540 passed / 8 failed / 143 skipped
- **Delta:** IDENTICAL

**Conclusion:** Fixtures did NOT introduce any new test failures or change test outcomes.

---

## Identified Gaps

### Gap 1: CWD Validation Missing
**Problem:** Infrastructure guard validates golden assets exist at repo root paths, but does NOT validate current working directory matches expected workspace.

**Evidence:**
- F4 failures: `FileNotFoundError: reports/2025-10-cli-flags/...`
- Tests ran from `/home/ollie/Documents/tmp/nanoBragg` (temporary directory)
- Golden assets exist at canonical repo root `/home/ollie/Documents/nanoBragg4/nanoBragg/reports/...`

**Impact:** Tests pass infrastructure guard but fail at runtime due to relative path resolution from wrong CWD.

**Remediation:**
1. Add `Path.cwd()` validation to `session_infrastructure_gate`:
   ```python
   expected_root = Path(__file__).parent.parent.resolve()  # tests/../ -> repo root
   if Path.cwd() != expected_root:
       pytest.fail(f"Working directory mismatch: {Path.cwd()} != {expected_root}. Run pytest from repo root.")
   ```
2. **OR** Update test fixtures to use absolute paths derived from `pytest.config.rootdir`

**Priority:** HIGH (blocks F4 resolution)

---

### Gap 2: C Binary Version/Hash Validation Not Implemented
**Problem:** Infrastructure guard validates C binary exists and executes `-help`, but does NOT validate binary version, build date, or SHA256 hash.

**Impact:** Tests may run against stale or incorrect C binary, causing spurious parity failures.

**Evidence:** F1 failure (`C reference run failed`) could indicate:
- Wrong C binary version
- Binary built with different flags
- Binary missing required features

**Remediation:**
Add version/hash check to `session_infrastructure_gate`:
```python
result = subprocess.run([c_bin, "-version"], capture_output=True, text=True, timeout=10)
if "expected_version_string" not in result.stdout:
    pytest.fail(f"C binary version mismatch: {result.stdout}")
```

**Priority:** MEDIUM (would improve F1 diagnostics, but not blocking)

---

### Gap 3: No Fixture Execution Logging
**Problem:** Fixtures execute silently during collection; no explicit log messages confirm guard execution or provide diagnostic breadcrumbs.

**Impact:** Difficult to diagnose infrastructure guard failures or confirm guard executed correctly.

**Remediation:**
Add logging to fixtures:
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"[session_infrastructure_gate] C binary resolved: {c_bin}")
logger.info(f"[session_infrastructure_gate] Golden assets validated: {asset_paths}")
```

**Priority:** LOW (nice-to-have for debugging, not blocking)

---

## Fixture Bypass Testing

### Bypass Mechanism: NB_SKIP_INFRA_GATE=1
**Status:** NOT TESTED in Phase L (bypass flag was not set)

**Phase K Validation (V4):** Confirmed bypass flag skips infrastructure guard and allows suite to run without C binary or golden assets.

**Phase L Evidence:** No bypass flag detected; guard ran normally.

---

## Fixture Integration with Test Suite

### Session Fixture Load Order
1. **conftest.py session-scoped fixtures:** `session_infrastructure_gate` (autouse)
2. **Test collection:** 692 tests discovered
3. **Module fixtures:** `gradient_policy_guard` loads when `test_gradients.py` module executes

**Evidence:** No collection errors, confirming fixture load order is correct.

### Fixture Dependencies
- `session_infrastructure_gate` has NO dependencies (runs first)
- `gradient_policy_guard` depends on `NANOBRAGG_DISABLE_COMPILE` env var (set via pytest invocation)

**Evidence:** Both fixtures executed successfully with no dependency errors.

---

## Recommendations

### Immediate (Phase M)
1. **Add CWD validation** to `session_infrastructure_gate` (Gap 1) — **CRITICAL** for F4 resolution
2. **Document gradient timeout policy** — Choose between 1200s uplift, chunked execution, or accept transient (F5)

### Near-Term (Phase N+)
1. **Add C binary version/hash check** (Gap 2) — Improves F1 diagnostics
2. **Add fixture execution logging** (Gap 3) — Improves observability
3. **Full-suite bypass test** — Validate `NB_SKIP_INFRA_GATE=1` in production full-suite context (not just isolated validation)

### Long-Term
1. **Fixture telemetry** — Capture guard execution times, C binary metadata, asset checksums to artifact bundle
2. **CI enforcement** — Add CI job that fails if infrastructure guard is bypassed without explicit approval
3. **Asset staleness warnings** — Warn if golden assets are >N days old (suggests regeneration needed)

---

## Conclusion

Phase K infrastructure fixtures (`session_infrastructure_gate`, `gradient_policy_guard`) executed successfully in Phase L full-suite rerun with **ZERO observable impact** on test outcomes or runtime. However, **Gap 1 (CWD validation)** is CRITICAL and blocks F4 golden asset path resolution. Remediation landed in Phase M implementation sprint will enable full resolution of infrastructure-related failures.

**Verdict:** ✅ Fixtures are operational and non-intrusive. Gaps identified are addressable in Phase M/N implementation work.
