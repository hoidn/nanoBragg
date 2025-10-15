# Cluster CLUSTER-GRAD-001 — Gradient Stability Timeout

## Summary
- Tests: `tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability`
- Classification: Critical performance regression (timeout)
- Failure mode: Test exceeded the 905 s timeout guard (Phase R tolerance). Phase B captured termination at ~905 s with no output, implying degraded performance in gradient accumulation path.
- Evidence: `reports/2026-01-test-suite-refresh/phase_b/20251015T113531Z/pytest.log` (TimeoutExpired near lines 3010-3095).

## Reproduction Command
```bash
timeout 1200 env \
  CUDA_VISIBLE_DEVICES=-1 \
  KMP_DUPLICATE_LIB_OK=TRUE \
  NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -vv tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability
```
- Increase timeout if analysis requires; capture `/usr/bin/time -v` output for resource profiling.

## Downstream Plan Alignment
- Primary owner: `[PERF-PYTORCH-004]` — kernel fusion / performance uplift initiative.
- Secondary linkage: `[VECTOR-PARITY-001]` (ensure vectorization changes tracked for gradient impact).
- Supporting docs: `docs/development/testing_strategy.md §1.4` (runtime guardrails), `docs/architecture/pytorch_design.md` (vectorized gradient path details).

## Recommended Next Actions
1. Run reproduction command with extended timeout and attach `--durations=0` to collect per-test runtime breakdown; store logs under this cluster directory.
2. Capture PyTorch autograd profiler trace for gradient accumulation loops (especially tricubic path) to pinpoint bottlenecks.
3. Compare with historical timings in `reports/2026-01-test-suite-triage/phase_p/` to quantify regression magnitude.
4. Update `[PERF-PYTORCH-004]` with findings and propose targeted investigation (e.g., check for accidental dtype promotion or device sync forced by instrumentation).

## Exit Criteria
- Profiler/diagnostic artifacts saved under this cluster directory with reproduction command documented.
- Updated `docs/fix_plan.md` entry for `[PERF-PYTORCH-004]` referencing this evidence and enumerating next remediation experiments.
- Input.md for implementation loop directs execution of prioritized next step (e.g., run profiler, test hypothesis).
