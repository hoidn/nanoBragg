# Contributing: Differentiability & Performance Checklist (Physics Helpers)

Use this checklist when changing hot helpers such as `sincg`, `sinc3`, polarization, or geometry kernels.

1) Problem reproduction
- [ ] Link to failing gradcheck / NaN incidence / numerical error or perf motivation

2) Minimal fix
- [ ] Implement the smallest change that resolves the reproduced issue
- [ ] Avoid speculative branches; keep vectorized, mask-based logic

3) Gradient validation
- [ ] `torch.autograd.gradcheck` passes in float64
- [ ] Float32 gradcheck or targeted tests pass (if relevant to production path)

4) Performance validation
- [ ] Microbenchmark (≥1e6 evals) attached for old vs new helper
- [ ] No regression (±5% tolerance) or regression is justified with data

5) Tolerances and dtype
- [ ] Tolerance rationale includes dtype assumptions (float64 vs float32)

6) Documentation
- [ ] Rationale documented succinctly in code comments (what changed and why)
- [ ] Reference to Architecture Addendum §1.2 and Lessons §4
