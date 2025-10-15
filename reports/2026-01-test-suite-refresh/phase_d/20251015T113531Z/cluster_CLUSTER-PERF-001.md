# Cluster CLUSTER-PERF-001 — Memory Bandwidth Regression

## Summary
- Tests: `tests/test_at_perf_003.py::TestATPERF003MemoryBandwidth::test_memory_bandwidth_utilization`
- Classification: Performance regression (runtime metric below threshold)
- Failure mode: Assertion expects ≥0.5 GB/s aggregate bandwidth at 2048²; Phase B log records 0.176 GB/s, triggering `AssertionError`.
- Evidence: `reports/2026-01-test-suite-refresh/phase_b/20251015T113531Z/pytest.log` (`bandwidth_gb_s=0.176` around lines 2470-2488).

## Reproduction Command
```bash
KMP_DUPLICATE_LIB_OK=TRUE \
NANOBRAGG_DISABLE_COMPILE=1 \
pytest -v tests/test_at_perf_003.py::TestATPERF003MemoryBandwidth::test_memory_bandwidth_utilization
```
- Optional profiling: prepend `/usr/bin/time -v` or set `NB_PROFILER_OUT=reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-PERF-001/profile.json` for custom profiler harness once implemented.

## Downstream Plan Alignment
- Primary owner: `[PERF-PYTORCH-004]` — Fuse physics kernels & tackle bandwidth regressions.
- Supporting docs: `docs/development/testing_strategy.md §1.4` (device/dtype discipline) and `docs/architecture/pytorch_design.md §Vectorization` for expected throughput.
- Findings touchpoints: none formal yet; log perf delta if regression persists to justify new finding.

## Recommended Next Actions
1. Capture fresh timing using the command above plus `/usr/bin/time -v` to quantify CPU usage and context switches.
2. If slowdown reproducible, collect PyTorch autograd profiler trace (`torch.profiler`) focusing on `_accumulate_pixel_contrib` hotspots; store under cluster directory.
3. Compare results against historical baseline in `reports/2026-01-vectorization-parity/` to determine whether regression aligns with recent vectorization work.
4. Update `[PERF-PYTORCH-004]` plan with evidence + next debug step (e.g., experiment with tensor fusion or memory format adjustments).

## Exit Criteria
- Profiling artifact committed under this cluster directory with reproduction command and runtime metrics.
- Next Action appended to `[PERF-PYTORCH-004]` (docs/fix_plan.md) referencing the captured evidence.
- Decision recorded on whether tolerance should be revised (if regression not actionable) or implementation fix pursued.
