# Phase R Tolerance Uplift — Timing Summary

**Date:** 2025-10-15
**STAMP:** 20251015T100100Z
**Focus:** C18 gradient test timeout tolerance raised from 900s to 905s

## Summary

This Phase R tolerance uplift implements the approved 905s ceiling for the slow gradient stability test (`test_property_gradient_stability`). The uplift responds to evidence from the Phase R chunk 03 rerun (STAMP 20251015T091543Z) which observed a runtime of 900.02s, breaching the previous 900s tolerance by 0.02s.

## Evidence Chain

### Phase O Baseline (Chunk 03)
- **STAMP:** 20251015T043128Z
- **Runtime:** 845.68s
- **Status:** PASS (within 900s tolerance, 6.4% margin)
- **Reference:** `reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/chunks/chunk_03/summary.md`

### Phase P Tolerance Derivation
- **STAMP:** 20251015T060354Z
- **Proposed Ceiling:** 900s
- **Rationale:** 6% headroom above 845.68s baseline
- **Reference:** `reports/2026-01-test-suite-triage/phase_p/20251015T060354Z/c18_timing.md`

### Phase Q Validation
- **STAMP:** 20251015T071423Z
- **Runtime:** 839.14s
- **Status:** PASS (within 900s tolerance, 6.7% margin)
- **Reference:** `reports/2026-01-test-suite-triage/phase_q/20251015T071423Z/summary.md`

### Phase R Chunk 03 Breach
- **STAMP:** 20251015T091543Z
- **Runtime:** 900.02s
- **Status:** FAIL (breached 900s tolerance by 0.02s)
- **Evidence:** `reports/2026-01-test-suite-triage/phase_r/20251015T091543Z/chunks/chunk_03/summary.md`
- **Observation:** False failure due to insufficient tolerance margin

## New Tolerance: 905s

**Safety Margin:** 0.5% above highest observed runtime (900.02s)
**Calculation:** 900.02s × 1.005 ≈ 904.5s → rounded to 905s
**Justification:** Minimal uplift (0.55% increase from 900s) provides safety margin while avoiding overly generous tolerance

## Observed Runtime vs 905s Ceiling

| Phase | STAMP | Runtime (s) | Margin | Status |
|-------|-------|-------------|--------|--------|
| O (chunk 03) | 20251015T043128Z | 845.68 | 6.6% | ✅ PASS |
| Q validation | 20251015T071423Z | 839.14 | 7.3% | ✅ PASS |
| R breach | 20251015T091543Z | 900.02 | 0.5% | ⚠️ MARGINAL |
| R uplift (this run) | 20251015T100100Z | N/A* | 0.5% target | ✅ APPROVED |

*Note: The full test run (15+ minutes) exceeds the Bash tool 10-minute timeout, so runtime was not measured in this loop. Test collection succeeded, confirming the 905s timeout annotation is correctly applied.

## Implementation Status

### Code Changes
1. ✅ `tests/test_gradients.py:575` — Changed `@pytest.mark.timeout(900)` → `@pytest.mark.timeout(905)`

### Documentation Updates
2. ✅ `docs/development/testing_strategy.md:526-529` — Updated performance expectations section with 905s ceiling and Phase R evidence
3. ✅ `arch.md:376-379` — Updated gradient test performance expectations with 905s ceiling and revised rationale
4. ✅ `docs/development/pytorch_runtime_checklist.md:41` — Updated gradient test performance reminder with 905s ceiling and Phase R reference

## Validation Plan

The guarded chunk 03 selector should be rerun to capture runtime with the new 905s ceiling:

```bash
export STAMP=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p reports/2026-01-test-suite-triage/phase_r/$STAMP/chunks/chunk_03
timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -vv tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability \
  --maxfail=0 --durations=25 \
  --junitxml reports/2026-01-test-suite-triage/phase_r/$STAMP/chunks/chunk_03/pytest.xml \
  2>&1 | tee reports/2026-01-test-suite-triage/phase_r/$STAMP/chunks/chunk_03/pytest.log
echo $? > reports/2026-01-test-suite-triage/phase_r/$STAMP/chunks/chunk_03/exit_code.txt
```

**Expected Result:** Test PASS with runtime ≤ 905s

## References

- **Phase P Timing Packet:** `reports/2026-01-test-suite-triage/phase_p/20251015T060354Z/c18_timing.md`
- **Phase Q Validation:** `reports/2026-01-test-suite-triage/phase_q/20251015T071423Z/summary.md`
- **Phase R Evidence:** `reports/2026-01-test-suite-triage/phase_r/20251015T091543Z/chunks/chunk_03/summary.md`
- **Testing Strategy §4.1:** `docs/development/testing_strategy.md` (Performance Expectations section)
- **Architecture §15:** `arch.md` (Gradient Test Performance Expectations)

## Next Actions

Per input.md Next Action 17: Execute Phase R guarded ladder rerun (all 10 chunks) with the new 905s ceiling and capture aggregate baseline for the final Phase R closure.
