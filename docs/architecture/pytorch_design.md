# nanoBragg PyTorch Architecture Design (Addendum)

## 1.2 Differentiability vs Performance

Principle: Differentiability is required; over-hardening is not. Prefer the minimal change that passes gradcheck and preserves vectorization.

- Minimal Differentiability Contract
  - Return analytic limits at removable singularities only when the raw op produces NaN/Inf or unacceptable relative error in tests.
  - Keep the nominal fast path branch-free (or mask-based) and fully vectorized.
  - Avoid speculative guards and extra branches unless backed by (a) a reproduced gradient failure or (b) a measured numerical/perf improvement.

- Branching Budget (Hot Helpers)
  - Per-element branching inside hot helpers (e.g., `sincg`, `sinc3`, polarization) must be justified with numbers (gradcheck evidence or microbenchmark delta).

- Mask vs Guard
  - Masks gate analytic limits; a single epsilon guard may backstop tiny denominators. If the mask tolerance renders guards redundant, prefer the mask alone.

- Precision Guidance
  - Default dev dtype: float64; default prod dtype: float32. Tolerances must state dtype assumptions and be tested in both where relevant.

- Acceptance Criteria for Helper Changes
  - Show a before/after gradcheck result (float64 required, float32 if relevant).
  - Include a microbenchmark (≥1e6 evaluations) comparing old/new helper.
  - Confirm vectorization preserved (no data-dependent Python control flow).

