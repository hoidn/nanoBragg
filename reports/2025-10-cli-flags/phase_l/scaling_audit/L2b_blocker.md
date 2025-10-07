# Phase L2b Evidence Gathering — Blocker

**Date:** 2025-10-17
**Engineer:** Ralph (Loop i=62, evidence-only mode)
**Plan Reference:** `plans/active/cli-noise-pix0/plan.md` Phase L2b
**Task:** Generate PyTorch scaling trace mirroring C trace instrumentation

---

## Blocker Summary

**Phase L2b cannot be completed as specified because the PyTorch `Simulator` class does not expose intermediate scaling chain values needed for trace comparison.**

The C implementation provides explicit trace output for:
- `I_before_scaling` — Raw accumulated intensity before normalization
- `r_e_sqr` — Thomson cross section
- `fluence_photons_per_m2` — Total X-ray fluence
- `steps` — Normalization divisor
- `oversample_thick/polar/omega` — Last-value flags
- `capture_fraction` — Detector absorption
- `polar` — Kahn polarization factor
- `omega_pixel` — Solid angle

These values are computed internally in `Simulator.run()` but not returned or logged, making it impossible to perform the requested trace comparison without modifying production code (which is forbidden in evidence-only mode per `input.md` rules).

---

## Evidence Attempted

### Attempted Approach #1: Custom Trace Harness
**File:** `reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py`

**Status:** Blocked by API limitations

**Issues encountered:**
1. `CrystalConfig` requires cell parameters even when using MOSFLM matrix (resolved by calling `reciprocal_to_real_cell`)
2. `read_mosflm_matrix` signature change requires wavelength argument (resolved)
3. Parameter name mismatches (`fdet_vector` → `custom_fdet_vector`, `exposure_s` → `exposure`, `beam_size_mm` → `beamsize_mm`)
4. `read_hkl_file` returns `(tensor, metadata_dict)` not individual unpacked values (resolved)
5. **FINAL BLOCKER:** `Simulator.__init__` expects `Detector`/`Crystal` objects but harness only constructed configs; attempting to construct objects hit circular dependencies and incomplete API surface for accessing internal scaling values

**Root cause:** The Simulator's `run()` method returns only final intensities, not intermediate scaling factors.

### Attempted Approach #2: CLI Wrapper Script
**File:** `reports/2025-10-cli-flags/phase_l/scaling_audit/run_pytorch_trace.sh`

**Status:** Insufficient - CLI doesn't output scaling chain

**Outcome:** The nanoBragg CLI entry point (`__main__.py`) only outputs final statistics (max_I, mean, RMS) without intermediate scaling factors, matching the C code's behavior when trace pixels are NOT specified.

---

## Resolution Options

### Option A: Add Trace Instrumentation (Code Change Required)
Modify `src/nanobrag_torch/simulator.py` to:
1. Add optional `trace_pixel` parameter to `Simulator.__init__`
2. Emit `TRACE_PY:` lines matching C format when trace pixel is hit
3. Expose `I_before_scaling`, `fluence`, `steps`, etc. via logging

**Pros:** Provides exact parity with C trace workflow
**Cons:** Requires production code changes (violates evidence-only constraint)

### Option B: Return Scaling Metadata from Simulator.run()
Change `Simulator.run()` signature to return `(intensities, metadata_dict)` where metadata includes:
- `r_e_sqr`, `fluence`, `steps`, `omega_grid`, `polar_grid`, etc.

**Pros:** Clean API for downstream analysis
**Cons:** Breaking API change; violates evidence-only constraint

### Option C: Defer to Implementation Loop
**Recommended:** Mark Phase L2b as blocked in `docs/fix_plan.md` and defer trace harness work to a Ralph implementation loop where code changes are allowed.

**Next Actions:**
1. Update `docs/fix_plan.md` Attempt history for CLI-FLAGS-003 with L2b blocker
2. Document exact API changes needed in a new plan entry (e.g., `[SIMULATOR-TRACE-001]`)
3. Supervisor to reassign L2b to implementation mode or defer until Phase L3 requires it

---

## Artifacts

### Created Files (Evidence of Attempt)
- `trace_harness.py` — Incomplete harness (stopped at Simulator init)
- `run_pytorch_trace.sh` — CLI wrapper (insufficient for scaling chain)
- `trace_py_env.json` — Environment snapshot (auto-generated during harness attempts)
- `notes.md` — Workflow log
- `L2b_blocker.md` — This document

### NOT Created (Blocked)
- `trace_py_scaling.log` — Would contain TRACE_PY lines (requires code changes)
- `config_snapshot.json` — Would document harness params (incomplete harness)

---

## Technical Details for Future Implementation

When Phase L2b is resumed in implementation mode, the following changes are needed in `src/nanobrag_torch/simulator.py`:

1. **Add trace pixel support to `__init__`:**
   ```python
   def __init__(self, ..., trace_pixel: Optional[Tuple[int, int]] = None):
       self.trace_pixel = trace_pixel  # (slow, fast) or None
   ```

2. **Emit trace lines in `_compute_physics_for_position` or `run`:**
   ```python
   if self.trace_pixel == (slow, fast):
       print(f"TRACE_PY: I_before_scaling {I_accumulated:.15g}")
       print(f"TRACE_PY: r_e_sqr {self.r_e_sqr:.15g}")
       print(f"TRACE_PY: fluence_photons_per_m2 {self.fluence:.15g}")
       # ... (see instrumentation_notes.md for full list)
   ```

3. **Update CLI to accept `-trace_pixel` flag:**
   ```python
   parser.add_argument('--trace_pixel', type=int, nargs=2, metavar=('SLOW', 'FAST'))
   ```

4. **Thread trace_pixel through configs:**
   ```python
   simulator = Simulator(..., trace_pixel=args.trace_pixel)
   ```

**Estimated effort:** 1-2 Ralph loops (implementation + regression coverage)

---

## References

- C trace instrumentation: `golden_suite_generator/nanoBragg.c:3367-3382`
- C scaling formula: `nanoBragg.c:3358` (`test = r_e_sqr*fluence*I/steps`)
- PyTorch scaling implementation: `src/nanobrag_torch/simulator.py` (~lines 930-1085, exact location TBD based on current code structure)
- Plan: `plans/active/cli-noise-pix0/plan.md` Phase L2b (exit criteria unmet)
- Fix Plan: `docs/fix_plan.md` [CLI-FLAGS-003] (to be updated with this blocker)

---

**Status:** Phase L2b BLOCKED pending code changes; evidence-only loop cannot proceed further.
