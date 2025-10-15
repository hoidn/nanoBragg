# Phase A — Baseline Failure Capture

**Initiative:** [GRADIENT-FLOW-001] Gradient flow regression
**Phase:** A (Baseline Evidence)
**STAMP:** 20251015T052020Z
**Date:** 2025-10-15
**Runtime:** Evidence-only loop (no production code changes)

## Objective

Reproduce the gradient failure from chunk 03 (C19 cluster) with fresh artifacts and quantify current gradient magnitudes to establish baseline for Phase B instrumentation.

## Command Executed

```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -vv tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation \
  --maxfail=1 --durations=25 --tb=short \
  --junitxml reports/2026-01-gradient-flow/phase_a/$STAMP/pytest.xml \
  | tee reports/2026-01-gradient-flow/phase_a/$STAMP/pytest.log
```

## Results

**Test Outcome:** ❌ FAILED
**Runtime:** 2.47s (1.58s call + 0.89s overhead)
**Exit Code:** 1 (stored in `exit_code.txt`)
**Assertion Message:** `AssertionError: At least one gradient should be non-zero`

### Gradient Magnitudes

All cell parameter gradients are **exactly zero**:

```json
{
  "loss": 0.0,
  "gradients": {
    "cell_a": 0.0,
    "cell_b": 0.0,
    "cell_c": 0.0,
    "cell_alpha": 0.0,
    "cell_beta": 0.0,
    "cell_gamma": 0.0
  }
}
```

**Critical Finding:** Loss itself is zero (`loss = image.sum() = 0.0`), which explains why all gradients vanish. The simulation is producing a completely blank (zero-intensity) image.

## Context

### Historical Evidence

Per `reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/chunks/chunk_03/summary.md`:
- C19 cluster: 1 failure (`test_gradient_flow_simulation`)
- Chunk 03 Part 3b runtime: 845.68s
- Status: Sole remaining functional failure after C2 gradcheck resolution

### Environment Guardrails

Environment variables per `arch.md` §15 and `testing_strategy.md` §4.1:
- `CUDA_VISIBLE_DEVICES=-1` → CPU-only execution (determinism)
- `KMP_DUPLICATE_LIB_OK=TRUE` → Avoid MKL conflicts
- `NANOBRAGG_DISABLE_COMPILE=1` → Prevent torch.compile donated buffers

Verified environment:
- Python 3.13.5
- PyTorch 2.7.1+cu126
- CUDA 12.6 available (forced CPU)
- dtype=float64 (for precision)

## Analysis

### Two-Level Problem

1. **Primary Issue:** Simulation produces zero intensity
   - Test configuration: cubic cell (100Å), N=5, mosaic=0, default_F not explicitly set
   - Possible causes: missing structure factors, culling, or configuration error

2. **Secondary Issue:** Zero gradients (consequence of zero loss)
   - Even if loss were non-zero, gradient flow path from config tensors → image must be verified
   - Per `plans/active/gradient-flow-regression.md` Phase B, callchain analysis will map the full path

### Hypothesis Ranking

Based on zero-intensity finding:

1. **H1 (most likely):** Missing structure factors — test doesn't provide `-hkl` or `-default_F`, triggering empty HKL grid (all F=0)
2. **H2:** Config caching — CrystalConfig parameters passed as `.item()` scalars instead of tensors, severing graph
3. **H3:** Intermediate detachment — Reciprocal vectors or rotated vectors use `.detach()`/`.clone()` without preserving `requires_grad`

## Artifacts

All evidence stored under `reports/2026-01-gradient-flow/phase_a/20251015T052020Z/`:

- `pytest.log` — Full pytest output with assertion details
- `pytest.xml` — JUnit XML for ledger automation
- `exit_code.txt` — Exit status (1 = failure)
- `gradients.json` — Gradient snapshot showing all zeros
- `summary.md` — This document

## Exit Criteria Status

- [x] A1: Targeted pytest run reproduced failure with exit code 1
- [x] A2: Gradient magnitudes recorded (all ≤1e-10, in fact exactly 0.0)
- [x] A3: Summary document captures command, runtime, assertion, and links to chunk_03 summary

## Next Actions

Per `plans/active/gradient-flow-regression.md` Phase B:

1. **Immediate:** Investigate zero-intensity root cause
   - Check test fixture for missing `-default_F` or `-hkl` (H1)
   - Review `CrystalConfig` construction in test for `.item()` usage (H2)

2. **Phase B Prep:** Once intensity issue resolved, proceed with callchain tracing
   - Use `prompts/callchain.md` workflow
   - Focus on `Crystal.build_state → Simulator.run` data flow
   - Register autograd hooks on reciprocal vectors, rotated real vectors, structure factors

3. **Ledger Sync:**
   - Update `docs/fix_plan.md` [GRADIENT-FLOW-001] Attempts History with Phase A findings
   - Mark A1/A2/A3 tasks complete in plan
   - Queue Phase B1 task for next loop

## References

- Test source: `tests/test_gradients.py:360-444`
- Plan: `plans/active/gradient-flow-regression.md`
- Chunk 03 baseline: `reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/chunks/chunk_03/summary.md`
- Architecture guardrails: `arch.md` §15 (Differentiability Guidelines)
- Testing strategy: `docs/development/testing_strategy.md` §4.1 (Gradient Test Requirements)
