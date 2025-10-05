# Lessons in Differentiability: Minimal Fix, Measured Impact

## Lesson 4: Avoid Unproven Safeguards (sincg case)

What happened:
- We added multiple special cases (zero and near-integer) and extra guards to `sincg` to “ensure” differentiability.
- Later analysis showed the zero case can be merged into the near-integer mask, and the denominator guard is mostly redundant at the documented tolerance. The extra branching slowed the hot path without improving gradients.

Key lesson:
- Reproduce → Fix minimally → Measure. Only harden math where a concrete failure exists or you can show a measurable improvement.

Checklist (use at PR time for helpers):
- [ ] Issue reproduced (link to failing gradcheck/NaN trace or numerical error)
- [ ] Minimal change implemented (no speculative branches)
- [ ] Gradcheck passes (float64 required; float32 if relevant)
- [ ] Microbenchmark (≥1e6 evals) shows no regression, or regression justified with data
- [ ] Vectorization preserved (no data-dependent Python loops)
- [ ] Tolerance rationale states dtype assumptions (f64 vs f32)

Do/Don’t: Analytic Limits (sincg)
- Do
  - Apply a single near-integer mask (covers n=0) and parity sign; keep vectorized.
  - Use at most one epsilon guard as cheap insurance against tiny denominators.
  - Back any extra branches with gradcheck + microbench numbers.
- Don’t
  - Add separate zero branches or nested wheres without a measured need.
  - Duplicate masks or recompute trig unnecessarily in the hot path.
  - Assume float64 tolerances when production runs in float32.
