# CLI-FLAGS-003 Phase L3k.3c.4 Evidence Capture

**Date:** 2025-10-08T01:33:45Z  
**Commit:** 61fd718  
**Plan:** `plans/active/cli-phi-parity-shim/plan.md` Phase C4

## Overview

Executed dual-mode parity trace comparison per `input.md` Do Now directive. Generated fresh PyTorch traces for both `spec` and `c-parity` modes and compared against the reference C trace.

## Execution Summary

### Spec Mode
- **Final intensity:** 2.38140349778394e-07
- **φ=0 divergence:** Δk = 1.811649e-02 (EXPECTED per specs/spec-a-core.md:211-214)
- **φ=1..9 parity:** max Δk = 2.845147e-05 (OK)
- **Status:** ✅ Spec-compliant behavior confirmed

### C-Parity Mode
- **Final intensity:** 2.79075741428655e-07
- **φ=0 parity:** Δk = 2.845147e-05 (reproduces C-PARITY-001)
- **φ=1..9 parity:** max Δk = 2.845147e-05 (consistent)
- **Status:** ⚠️ Reproduces C bug, but exceeds VG-1 target

## VG-1 Gate Analysis

**Target:** Δk ≤ 1e-6

**Actual:** Δk = 2.845147e-05

**Ratio:** 28.45× over target

**Conclusion:** While c-parity mode successfully emulates the C-PARITY-001 bug (φ=0 carryover), it still has a ~2.8e-5 residual drift that prevents meeting the stricter VG-1 tolerance. This appears to be a systematic numerical difference rather than a logic bug.

## Test Results

### test_phi_carryover_mode.py::TestPhiCarryoverBehavior
- **Result:** 12/12 PASSED (2.56s)
- **Coverage:** Both modes, CPU+CUDA, float32+float64
- **Devices tested:** cpu, cuda
- **Status:** ✅ All parametrized tests passing

### test_cli_scaling_phi0.py::TestPhiZeroParity
- **Result:** 2/2 PASSED (2.13s)
- **Coverage:** φ=0 spec baseline validation
- **Status:** ✅ Spec compliance verified

## Artifacts

All artifacts stored in: `reports/2025-10-cli-flags/phase_l/parity_shim/20251008T013345Z/`

### Trace Files
- `trace_py_spec.log` - Spec mode PyTorch trace
- `trace_py_c_parity.log` - C-parity mode PyTorch trace
- `c_trace_phi.log` - Reference C trace (copied from 20251008T005247Z)
- `trace_py_spec_per_phi.json` - Spec mode per-φ data
- `trace_py_c_parity_per_phi.json` - C-parity mode per-φ data

### Comparison Results
- `per_phi_summary_spec.txt` - Spec vs C comparison
- `per_phi_summary_c_parity.txt` - C-parity vs C comparison
- `delta_metrics.json` - Quantitative metrics

### Test Logs
- `pytest_phi_carryover.log` - Carryover mode tests (12 passed)
- `pytest_phi0.log` - φ=0 spec baseline tests (2 passed)

### Verification
- `sha256.txt` - Cryptographic hashes of all artifacts

## Observations

1. **Spec mode behavior correct:** The φ=0 divergence (Δk=1.811649e-02) confirms the default implementation follows the normative spec (fresh rotation each step).

2. **C-parity mode functional:** Successfully reproduces the C-PARITY-001 bug behavior documented in `docs/bugs/verified_c_bugs.md:166-204`.

3. **Residual drift persistent:** The 2.845e-05 plateau across all c-parity φ steps suggests a systematic numerical difference (likely precision or rounding) rather than a φ-dependent bug.

4. **Tests pass but VG-1 fails:** The pytest suite validates mode behavior and device/dtype neutrality, but the stricter VG-1 gate (≤1e-6) remains unmet.

## Hypotheses for 2.8e-5 Drift

1. **Float32 vs Float64 mismatch:** C may use different precision paths
2. **Reciprocal vector recalculation:** The cross-product → V_actual path may accumulate error
3. **Rotation matrix precision:** `rotate_axis` or `rotate_umat` numerical differences
4. **C trace staleness:** The copied C trace may not reflect current binary behavior (TRACE_C_PHI may be missing)

## Next Actions

Per `input.md` and `plans/active/cli-phi-parity-shim/plan.md`:

1. **Restore TRACE_C_PHI instrumentation** in `golden_suite_generator/nanoBragg.c` and regenerate a fresh C trace to rule out staleness.

2. **Investigate numerical precision:** Profile the reciprocal recomputation and rotation paths to identify where the 2.8e-5 error originates.

3. **Phase C4 completion blocked:** Cannot mark C4 as [D]one until either:
   - VG-1 tolerance relaxed to 5e-5 (supervisor decision), OR
   - Implementation refined to eliminate the 2.8e-5 drift

4. **Phase C5 documentation** can proceed with current evidence while C4 parity work continues.

## References

- Plan: `plans/active/cli-phi-parity-shim/plan.md`
- Spec: `specs/spec-a-core.md:204-240`
- C Bug: `docs/bugs/verified_c_bugs.md:166-204`
- Fix Plan: `docs/fix_plan.md` CLI-FLAGS-003 Attempt #122
