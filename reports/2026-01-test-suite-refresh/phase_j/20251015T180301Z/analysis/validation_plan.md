# Validation Strategy (Phase J — Task J3)

## Purpose & Scope

**Objective:** Define the validation methodology for Phase J fixture implementations (J1: session_infrastructure_gate, J2: gradient_policy_guard) before implementation begins. This plan ensures fixtures can be tested in isolation and integration without requiring full suite runs.

**Scope:**
- Targeted pytest selectors for fixture validation
- Expected artifact outputs (logs, exit codes, metrics)
- Pass/fail criteria for each validation scenario
- Reproducible commands for regression testing

**Out of Scope:**
- Full test suite execution (deferred to Phase K)
- Physics correctness validation (covered by existing tests)
- Performance benchmarking (fixtures have minimal overhead)

## Targeted Selectors

### Validation Approach

Fixtures will be validated using **synthetic failure scenarios** and **collection-time checks**. This approach avoids dependency on test content while proving guard behavior.

### V1: Infrastructure Gate - Positive Case

**Objective:** Verify fixture passes with valid infrastructure

**Command:**
```bash
pytest --collect-only -q 2>&1 | tee validation/v1_infra_gate_pass.log
```

**Environment Prerequisites:**
- C binary exists at `./golden_suite_generator/nanoBragg` OR `./nanoBragg` OR `$NB_C_BIN`
- Golden assets exist: `scaled.hkl`, `reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json`
- Working directory is repository root
- Editable install active

**Expected Output:**
```
tests/test_at_*.py::test_*
tests/test_gradients.py::test_*
...
==================== XXX tests collected ====================
```

**Pass Criteria:**
- ✅ Exit code 0
- ✅ No "Infrastructure gate check failed" message
- ✅ Collection completes normally
- ✅ No pytest warnings about fixtures

**Artifacts:**
- `validation/v1_infra_gate_pass.log` — pytest output
- Exit code recorded in `validation/v1_exit_code.txt`

### V2: Infrastructure Gate - Missing C Binary

**Objective:** Verify fixture fails with clear message when C binary is missing

**Setup:**
```bash
# Temporarily rename all C binaries
mv ./golden_suite_generator/nanoBragg ./golden_suite_generator/nanoBragg.hidden 2>/dev/null || true
mv ./nanoBragg ./nanoBragg.hidden 2>/dev/null || true
```

**Command:**
```bash
pytest --collect-only -q 2>&1 | tee validation/v2_infra_gate_missing_binary.log
EXIT_CODE=$?
echo $EXIT_CODE > validation/v2_exit_code.txt
```

**Cleanup:**
```bash
mv ./golden_suite_generator/nanoBragg.hidden ./golden_suite_generator/nanoBragg 2>/dev/null || true
mv ./nanoBragg.hidden ./nanoBragg 2>/dev/null || true
```

**Expected Output:**
```
================================================================================
Infrastructure Gate Check FAILED
================================================================================
  - C binary not found. Expected one of:
    1. NB_C_BIN environment variable pointing to binary
    2. ./golden_suite_generator/nanoBragg (instrumented binary)
    3. ./nanoBragg (frozen reference)
    Rebuild with: make -C golden_suite_generator
...
```

**Pass Criteria:**
- ✅ Exit code non-zero (pytest collection failure)
- ✅ Error message contains "C binary not found"
- ✅ Remediation guidance present ("Rebuild with:")
- ✅ No tests collected (failure during session setup)

**Artifacts:**
- `validation/v2_infra_gate_missing_binary.log`
- `validation/v2_exit_code.txt`

### V3: Infrastructure Gate - Missing Golden Asset

**Objective:** Verify fixture fails when golden assets are missing

**Setup:**
```bash
# Temporarily rename HKL asset
mv scaled.hkl scaled.hkl.hidden
```

**Command:**
```bash
pytest --collect-only -q 2>&1 | tee validation/v3_infra_gate_missing_asset.log
EXIT_CODE=$?
echo $EXIT_CODE > validation/v3_exit_code.txt
```

**Cleanup:**
```bash
mv scaled.hkl.hidden scaled.hkl
```

**Expected Output:**
```
================================================================================
Infrastructure Gate Check FAILED
================================================================================
  - Golden asset not found: scaled.hkl
    Generate via: python scripts/validation/create_scaled_hkl.py
    See: docs/fix_plan.md Attempt #6 for provenance
...
```

**Pass Criteria:**
- ✅ Exit code non-zero
- ✅ Error message contains "Golden asset not found: scaled.hkl"
- ✅ Generation command provided
- ✅ No tests collected

**Artifacts:**
- `validation/v3_infra_gate_missing_asset.log`
- `validation/v3_exit_code.txt`

### V4: Infrastructure Gate - Bypass Mechanism

**Objective:** Verify NB_SKIP_INFRA_GATE bypass works

**Setup:**
```bash
# Temporarily rename C binary to simulate missing infrastructure
mv ./golden_suite_generator/nanoBragg ./golden_suite_generator/nanoBragg.hidden 2>/dev/null || true
```

**Command:**
```bash
NB_SKIP_INFRA_GATE=1 pytest --collect-only -q 2>&1 | tee validation/v4_infra_gate_bypass.log
EXIT_CODE=$?
echo $EXIT_CODE > validation/v4_exit_code.txt
```

**Cleanup:**
```bash
mv ./golden_suite_generator/nanoBragg.hidden ./golden_suite_generator/nanoBragg 2>/dev/null || true
```

**Expected Output:**
```
tests/test_*.py::test_*
...
==================== XXX tests collected ====================
```

**Also Expected:** UserWarning about bypass:
```
UserWarning: Infrastructure gate bypassed (NB_SKIP_INFRA_GATE=1). This should only be used for debugging.
```

**Pass Criteria:**
- ✅ Exit code 0 (collection succeeds despite missing binary)
- ✅ Warning present in output
- ✅ Tests collected normally

**Artifacts:**
- `validation/v4_infra_gate_bypass.log`
- `validation/v4_exit_code.txt`

### V5: Gradient Guard - Positive Case

**Objective:** Verify gradient tests collect when environment is set

**Command:**
```bash
env NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py --collect-only -q 2>&1 | \
  tee validation/v5_gradient_guard_pass.log
EXIT_CODE=$?
echo $EXIT_CODE > validation/v5_exit_code.txt
```

**Expected Output:**
```
tests/test_gradients.py::TestCellParameterGradients::test_cell_a_gradient
tests/test_gradients.py::TestCellParameterGradients::test_cell_gamma_gradient
...
==================== 15 tests collected ====================
```

**Pass Criteria:**
- ✅ Exit code 0
- ✅ All gradient tests collected (no skips)
- ✅ No skip messages

**Artifacts:**
- `validation/v5_gradient_guard_pass.log`
- `validation/v5_exit_code.txt`
- Test count: extract with `grep -oP '\d+ tests collected'`

### V6: Gradient Guard - Missing Environment

**Objective:** Verify gradient tests skip when NANOBRAGG_DISABLE_COMPILE not set

**Command:**
```bash
pytest -v tests/test_gradients.py --collect-only -q 2>&1 | \
  tee validation/v6_gradient_guard_skip.log
EXIT_CODE=$?
echo $EXIT_CODE > validation/v6_exit_code.txt
```

**Expected Output:**
```
tests/test_gradients.py::TestCellParameterGradients::test_cell_a_gradient SKIPPED
tests/test_gradients.py::TestCellParameterGradients::test_cell_gamma_gradient SKIPPED
...
==================== 15 skipped in 0.05s ====================

SKIPPED [15] tests/test_gradients.py:XX: Gradient tests require NANOBRAGG_DISABLE_COMPILE=1 environment variable.

Run with: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py
```

**Pass Criteria:**
- ✅ Exit code 0 (skip is not failure)
- ✅ All gradient tests skipped
- ✅ Skip message present with reproduction command
- ✅ Skip message references `NANOBRAGG_DISABLE_COMPILE=1`

**Artifacts:**
- `validation/v6_gradient_guard_skip.log`
- `validation/v6_exit_code.txt`
- Skip count: extract with `grep -oP '\d+ skipped'`

### V7: Gradient Guard - Wrong Value

**Objective:** Verify guard rejects non-"1" values

**Command:**
```bash
env NANOBRAGG_DISABLE_COMPILE=0 pytest -v tests/test_gradients.py --collect-only -q 2>&1 | \
  tee validation/v7_gradient_guard_wrong_value.log
EXIT_CODE=$?
echo $EXIT_CODE > validation/v7_exit_code.txt
```

**Expected Output:**
```
==================== 15 skipped in 0.05s ====================

SKIPPED [15] tests/test_gradients.py:XX: Gradient tests require NANOBRAGG_DISABLE_COMPILE=1 environment variable.
```

**Pass Criteria:**
- ✅ Exit code 0 (skip, not error)
- ✅ All gradient tests skipped
- ✅ Skip message identical to V6 case

**Artifacts:**
- `validation/v7_gradient_guard_wrong_value.log`
- `validation/v7_exit_code.txt`

### V8: Integration - Both Fixtures Active

**Objective:** Verify fixtures work together without conflicts

**Command:**
```bash
env NANOBRAGG_DISABLE_COMPILE=1 pytest --collect-only -q 2>&1 | \
  tee validation/v8_integration_both_fixtures.log
EXIT_CODE=$?
echo $EXIT_CODE > validation/v8_exit_code.txt
```

**Expected Output:**
```
tests/test_at_*.py::test_*
tests/test_gradients.py::test_*
...
==================== XXX tests collected ====================
```

**Pass Criteria:**
- ✅ Exit code 0
- ✅ Infrastructure gate passes (no failure message)
- ✅ Gradient guard passes (no skips in test_gradients.py)
- ✅ All non-gradient tests collected
- ✅ Total test count matches expected suite size (~180 tests)

**Artifacts:**
- `validation/v8_integration_both_fixtures.log`
- `validation/v8_exit_code.txt`
- Test count recorded

### V9: Gradient Guard - Execution Validation

**Objective:** Verify fixtures don't break actual gradient test execution

**Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  timeout 120 pytest -v tests/test_gradients.py -k "gradcheck" --tb=short 2>&1 | \
  tee validation/v9_gradient_execution.log
EXIT_CODE=$?
echo $EXIT_CODE > validation/v9_exit_code.txt
```

**Expected Output:**
```
tests/test_gradients.py::test_cell_a_gradient PASSED
tests/test_gradients.py::test_detector_distance_gradient PASSED
...
==================== 10 passed in 45-60s ====================
```

**Pass Criteria:**
- ✅ Exit code 0
- ✅ All gradcheck tests pass (10/10)
- ✅ No donated buffer errors
- ✅ Runtime <120s (sanity check, not full slow_gradient suite)

**Artifacts:**
- `validation/v9_gradient_execution.log`
- `validation/v9_exit_code.txt`
- Runtime: extract with `grep -oP 'passed in \K[\d.]+s'`

## Exit Criteria

### Phase J Validation Complete When:

1. ✅ **All V1-V9 validation commands executed successfully**
   - Exit codes match expected (0 for pass/skip, non-zero for intended failures)
   - Output messages match expected patterns
   - Artifacts captured in `reports/2026-01-test-suite-refresh/phase_j/20251015T180301Z/validation/`

2. ✅ **Synthetic failure scenarios validated**
   - V2: Missing C binary triggers clear error
   - V3: Missing golden asset triggers clear error
   - V4: Bypass mechanism works
   - V6: Missing env var triggers skip with remediation

3. ✅ **Positive cases validated**
   - V1: Infrastructure gate passes with valid setup
   - V5: Gradient guard passes with correct environment
   - V8: Integration works (both fixtures active)
   - V9: Gradient tests execute successfully

4. ✅ **Documentation artifacts complete**
   - All `validation/v*_*.log` files present
   - All `validation/v*_exit_code.txt` files present
   - `validation/summary.md` created with pass/fail matrix (see template below)

5. ✅ **Plan updates complete**
   - `plans/active/test-suite-triage-phase-h.md` Phase J tasks marked [D] (Done)
   - `docs/fix_plan.md` Attempt #18 logged with STAMP and artifact paths
   - Next Actions updated (Phase K: full suite rerun scheduled)

## Artifact Expectations

### Directory Structure

```
reports/2026-01-test-suite-refresh/phase_j/20251015T180301Z/
├── analysis/
│   ├── session_fixture_design.md     (Task J1 deliverable)
│   ├── gradient_policy_guard.md      (Task J2 deliverable)
│   └── validation_plan.md            (Task J3 deliverable - this file)
├── notes/
│   ├── env_snapshot.txt              (printenv output)
│   └── open_questions.md             (blockers/design questions)
├── validation/                        (created during validation execution)
│   ├── v1_infra_gate_pass.log
│   ├── v1_exit_code.txt
│   ├── v2_infra_gate_missing_binary.log
│   ├── v2_exit_code.txt
│   ├── ... (v3-v9 artifacts)
│   └── summary.md                     (validation results matrix)
└── STAMP.txt                          (timestamp reference)
```

### Summary Template

File: `validation/summary.md`

```markdown
# Phase J Validation Summary

**STAMP:** 20251015T180301Z
**Date:** 2025-10-15
**Executor:** [Name/Role]
**Duration:** [Total validation time]

## Results Matrix

| Test | Objective | Exit Code | Status | Notes |
|------|-----------|-----------|--------|-------|
| V1 | Infrastructure gate pass | 0 | ✅ PASS | XXX tests collected |
| V2 | Missing C binary | ≠0 | ✅ PASS | Clear error message |
| V3 | Missing golden asset | ≠0 | ✅ PASS | Remediation guidance present |
| V4 | Bypass mechanism | 0 | ✅ PASS | UserWarning observed |
| V5 | Gradient guard pass | 0 | ✅ PASS | 15 tests collected |
| V6 | Missing NANOBRAGG_DISABLE_COMPILE | 0 | ✅ PASS | 15 skipped, clear message |
| V7 | Wrong NANOBRAGG_DISABLE_COMPILE value | 0 | ✅ PASS | 15 skipped |
| V8 | Integration (both fixtures) | 0 | ✅ PASS | XXX tests collected |
| V9 | Gradient execution | 0 | ✅ PASS | 10/10 gradcheck passed |

## Overall Status

**✅ PHASE J VALIDATION COMPLETE**

All validation scenarios passed. Fixtures are ready for implementation.

## Artifacts

- Logs: `validation/v*_*.log` (9 files)
- Exit codes: `validation/v*_exit_code.txt` (9 files)
- Design docs: `analysis/*.md` (3 files)

## Next Steps

1. **Phase K Preparation:** Merge fixture implementations to feature branch
2. **Full Suite Rerun:** Schedule Phase K (full pytest rerun with fixtures active)
3. **Documentation Updates:**
   - Update `docs/development/testing_strategy.md` §1.5 with fixture references
   - Add fixture usage examples to `CLAUDE.md` testing section
4. **CI Integration:** Add infrastructure gate to CI pipeline pytest jobs

## References

- Plan: `plans/active/test-suite-triage-phase-h.md` Phase J tasks
- Design: `reports/2026-01-test-suite-refresh/phase_j/20251015T180301Z/analysis/`
- Fix Plan: `docs/fix_plan.md` [TEST-SUITE-TRIAGE-002] Attempt #18
```

### Metrics to Extract

From validation logs, extract and record:

1. **Test Counts:**
   ```bash
   grep -oP '\d+ tests collected' validation/v1_infra_gate_pass.log
   grep -oP '\d+ skipped' validation/v6_gradient_guard_skip.log
   ```

2. **Runtime (V9 only):**
   ```bash
   grep -oP 'passed in \K[\d.]+s' validation/v9_gradient_execution.log
   ```

3. **Exit Codes:**
   ```bash
   for i in {1..9}; do
     echo "V$i: $(cat validation/v${i}_exit_code.txt)"
   done
   ```

4. **Error Message Presence:**
   ```bash
   grep -q "Infrastructure Gate Check FAILED" validation/v2_infra_gate_missing_binary.log && echo "V2: Error message ✅"
   grep -q "Golden asset not found" validation/v3_infra_gate_missing_asset.log && echo "V3: Asset message ✅"
   grep -q "NANOBRAGG_DISABLE_COMPILE=1" validation/v6_gradient_guard_skip.log && echo "V6: Skip message ✅"
   ```

## Execution Workflow

### Phase J Implementation Loop (Post-Design)

Once fixture designs (J1/J2) are approved:

1. **Implement fixtures** in `tests/conftest.py` and `tests/test_gradients.py`
2. **Execute validation sequence** (V1-V9 commands)
3. **Capture artifacts** to `validation/` directory
4. **Generate summary.md** using template above
5. **Commit fixtures + validation artifacts** together
6. **Update plan files** (Phase J tasks → [D], fix_plan Attempt #18)

### Validation Execution Script (Optional)

**File:** `scripts/validation/run_phase_j_validation.sh`

```bash
#!/bin/bash
# Phase J Fixture Validation Runner
# Usage: ./scripts/validation/run_phase_j_validation.sh

set -e

STAMP="20251015T180301Z"
VALIDATION_DIR="reports/2026-01-test-suite-refresh/phase_j/$STAMP/validation"
mkdir -p "$VALIDATION_DIR"

echo "Starting Phase J validation sequence..."

# V1: Infrastructure gate pass
pytest --collect-only -q 2>&1 | tee "$VALIDATION_DIR/v1_infra_gate_pass.log"
echo $? > "$VALIDATION_DIR/v1_exit_code.txt"

# V2: Missing C binary (setup, run, cleanup)
# ... (implement synthetic scenarios)

# ... (continue for V3-V9)

echo "Validation complete. Check $VALIDATION_DIR for artifacts."
```

**Note:** Validation script is optional; manual execution is sufficient for Phase J evidence-only loop.

## Known Limitations

1. **Binary Staleness:** Validation does not check if C binary is outdated relative to source. Future enhancement: add SHA256 tracking.

2. **Asset Content Validation:** Validation only checks file existence/size, not correctness. Hash validation is one-time (Phase H), not per-validation-run.

3. **Device Availability:** V9 gradient execution uses CPU only (`CUDA_VISIBLE_DEVICES=-1`). GPU gradient execution validation deferred to Phase K full suite.

4. **Timeout Coverage:** V9 uses 120s timeout for fast feedback. Full `test_property_gradient_stability` (905s) not executed during Phase J validation.

5. **Concurrency:** Validation runs sequentially. Parallel execution not needed for evidence-only phase.

## Open Questions

1. **Validation Frequency:** Should fixture validation be added to CI as a pre-test gate? (Adds ~1 minute overhead but prevents fixture regressions)

2. **Artifact Retention:** How long should validation logs be retained? (Proposal: archive after Phase K completion)

3. **Fixture Evolution:** When fixture logic changes, should validation be re-run? (Yes, validation is cheap and should be part of fixture update workflow)

4. **Phase K Trigger Condition:** Should Phase K (full suite rerun) wait for stakeholder sign-off on Phase J deliverables? (Recommended: yes, to avoid premature implementation)

## References

- **Plan Context:** `plans/active/test-suite-triage-phase-h.md` (Phase J Task J3)
- **Fixture Designs:**
  - `reports/2026-01-test-suite-refresh/phase_j/20251015T180301Z/analysis/session_fixture_design.md` (J1)
  - `reports/2026-01-test-suite-refresh/phase_j/20251015T180301Z/analysis/gradient_policy_guard.md` (J2)
- **Testing Strategy:** `docs/development/testing_strategy.md` §1.5 (Do Now expectations)
- **Phase H Baseline:** `reports/2026-01-test-suite-refresh/phase_h/20251015T171757Z/analysis/infrastructure_gate.md`
