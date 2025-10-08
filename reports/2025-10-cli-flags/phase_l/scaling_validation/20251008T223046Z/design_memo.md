# Phase M4a — Normalization Contract Summary (20251008T223046Z)

## References Reviewed
- `specs/spec-a-core.md` §§4.2–4.3 (inner-loop accumulation + final scaling contract).
- `docs/development/c_to_pytorch_config_map.md` (scaling/fluence notes under SimulatorConfig).
- `golden_suite_generator/nanoBragg.c` lines 3332–3368 (post-loop normalization & final scaling).
- `src/nanobrag_torch/simulator.py` lines 942–1135 (current PyTorch normalization pipeline).

## C Implementation — Authoritative Contract
```c
/* end of detector thickness loop */

/* convert pixel intensity into photon units */
test = r_e_sqr*fluence*I/steps;

/* do the corrections now, if they haven't been applied already */
if(! oversample_thick) test *= capture_fraction;
if(! oversample_polar) test *= polar;
if(! oversample_omega) test *= omega_pixel;
floatimage[imgidx] += test;
```
- `I` is the running accumulator over sources × mosaic × φ × subpixels (no division inside loops).
- `steps = n_sources * n_mosaic * phisteps * oversample^2`.
- Only **one** division by `steps` occurs, just before multiplying by `r_e^2 * fluence`.
- Last-value semantics for capture_fraction/polar/omega mirror the spec (apply only if the corresponding oversample flag was disabled during the loops).

## Spec Alignment
- `specs/spec-a-core.md:233-258` mirrors the C snippet: accumulate `I_term`, then compute `S = r_e^2 * fluence * I / steps` and optionally multiply by last-value factors.
- `specs/spec-a-core.md:224-231` clarifies that oversample_thick/polar/omega multiply the running sum **inside** the loop when enabled; otherwise the final `S` uses the last computed value.
- No spec clause authorizes a second division by `steps` after the accumulator is normalized.

## Current PyTorch Behaviour (Divergence)
- `src/nanobrag_torch/simulator.py:971-1050` divides the accumulated tensor by `steps` **immediately** after each `_compute_physics_for_position` call (`normalized_intensity = intensity / steps`).
- Later, when forming `physical_intensity` (`lines 1118-1135`), the code divides by `steps` again:
  ```python
  physical_intensity = (
      normalized_intensity
      / steps
      * self.r_e_sqr
      * self.fluence
  )
  ```
- Result: total scale is `I / steps^2 * r_e^2 * fluence`, i.e., a second, unintentional reduction by the step count.
- Trace evidence (`reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/metrics.json`) shows PyTorch intensity is ~14.6% low relative to C, consistent with extra division (steps=10 for φ, additional factors from oversample_subpixels).

## Required Change (Phase M4b Preview)
1. Keep early `intensity / steps` only if the accumulator is never re-used without final scaling (ensures averages stay bounded for oversample paths). Otherwise, move the `/ steps` so it happens exactly once alongside `r_e^2 * fluence`.
2. Update `TRACE_PY` logging so `I_before_scaling` prints the pre-division accumulator (matching `TRACE_C: I_before_scaling`).
3. Ensure last-value semantics for capture_fraction/polar/omega remain intact after the division is repositioned.
4. Maintain vectorized tensor math (no Python loops, no `.item()` except within trace print guards), and keep device/dtype neutrality.

## Verification Checklist (for M4c/M4d)
- `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py`
- `KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --bundle reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline`
- Capture new bundle under `reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223046Z/` with `summary.md`, `commands.txt`, `env.json`, and diff of `trace_py` vs `trace_c`.
- Update `lattice_hypotheses.md` to mark Hypothesis H4 (missing normalization) as resolved once parity is achieved.

## Open Questions
- Confirm whether early `/ steps` is still desirable once final scaling is corrected; if redundant, remove it to minimize rounding error.
- Assess interaction with detector absorption: verify `capture_fraction` tensors are computed before normalization so division reordering does not alter values.
