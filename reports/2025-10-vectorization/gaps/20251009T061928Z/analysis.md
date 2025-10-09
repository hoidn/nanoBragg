# Vectorization Gap Recon (generate_sources)

## Summary
- Initiative: PERF-PYTORCH-004 (vectorization/perf backlog) — identify non-vectorized surfaces beyond tricubic/absorption (aligns with long-term Goal 2).
- Scope: `src/nanobrag_torch/utils/auto_selection.py::generate_sources_from_divergence_dispersion`.

## Key Findings
- Function builds divergence/dispersion grids using triple nested Python loops (hdiv × vdiv × dispersion) and repeated Rodrigues rotations per source. No batching/vectorization is applied.
- Complexity grows with product of sampling counts (e.g., 25×25 divergence × 9 dispersion = 3,969 sources). This loop sits on CLI path before every simulation run.
- Timings (see `generate_sources_timing.txt`):
  - 3,969-source configuration (counts=25/25/9) takes ~0.126 s per call on CPU.
  - Repeated calls are similar cost (~0.124 s average). Large divergence grids (e.g., 51×51×21) would scale super-linearly due to Python overhead and `torch.linalg.cross` per source.
- The generated direction/weight/wavelength tensors are already vector-friendly (stacked at end), suggesting we can pre-vectorize angles and use batched trig/rotation formulas instead of Python loops.

## Candidate Remediation Outline
1. Build divergence mesh via `torch.linspace` (respecting elliptical trimming using tensor masks).
2. Construct wavelength grid as tensor using broadcasting.
3. Use batched Rodrigues rotation (`rotate_axis`) with precomputed axes to transform base beam vector for all (h_angle, v_angle) pairs in one go.
4. Apply dispersion by broadcasting wavelengths and reuse weights as ones. Avoid append/stack patterns.
5. Ensure dtype/device neutrality by deriving `dtype` from inputs and running on caller’s device.

## Next Steps
- Confirm invocation sites (CLI path in `__main__.py` and tests) and evaluate maximum sampling counts seen in practice (check fix_plan/perf benchmarks).
- Sketch vectorized prototype and benchmark vs current loops under PERF-PYTORCH-004 Phase C or new sub-phase (document in plan).
- Update fix_plan `[PERF-PYTORCH-004]` Next Actions once prototype timing shows ≥10× speedup for large grids.
