# Placeholder / Steps Parity Design Memo

**Date**: 2025-10-09
**Phase**: SOURCE-WEIGHT-001 Phase E
**Status**: Evidence Collection (No Implementation Yet)

## Goals

- Match nanoBragg.c source counting even with sourcefile inputs
- Preserve vectorization + differentiability guardrails (arch.md §15, docs/architecture/pytorch_design.md §1.1)
- Diagnose 47-120× intensity inflation beyond the known 2× steps mismatch

## Problem Statement

Current parity failures:
- TC-D1: correlation=0.049 (threshold ≥0.999), sum_ratio=46.85 (|ratio-1| ≤1e-3)
- TC-D3: correlation=0.053, sum_ratio=120.06

Known divergences:
1. **Steps mismatch**: PyTorch counts 2 sources, C counts 4 (2 actual + 2 zero-weight divergence placeholders)
   - Expected contribution: 2× intensity difference
2. **Residual ~24-60× inflation**: After accounting for steps, significant gap remains

## C-Code References

### Source Ingestion (nanoBragg.c lines 2570-2720)

Key behaviors:
- Lines 2570-2576: Read sourcefile, ignore weight and wavelength columns
- Lines 2604-2610: Create zero-weight divergence placeholders when hdivsteps/vdivsteps=0
- Lines 2700-2720: Calculate steps = sources_total × mosaic_domains × phi_steps × oversample²
- All sources (including zero-weight) count toward steps denominator

### Steps Calculation

C-code always counts:
- Actual sources from sourcefile (with their specified weights)
- Zero-weight divergence placeholders (position (0,0,0), weight=0, lambda=0)
- Auto-generated divergence/dispersion sources

## PyTorch Current Behavior

Location: `src/nanobrag_torch/simulator.py` lines 847-874

Current logic:
```python
steps = n_sources × mosaic_domains × phi_steps × oversample²
```

Where `n_sources = len(self._source_directions)`

**Problem**: PyTorch `_source_directions` contains only actual sources from sourcefile, NOT zero-weight placeholders.

## Hypotheses for Residual Divergence

Based on Attempt #22/#23 evidence:

1. **Per-source polarization** (CONFIRMED 2× factor):
   - PyTorch: polar=0.9997 (≈1.0)
   - C: polar=0.5
   - Contributes additional 2× (total 4× with steps)

2. **Structure factor sampling**:
   - Different interpolation or default_F application per source?
   - Need to check F_cell, F_latt for source index 2 vs aggregate

3. **Intensity accumulation**:
   - PyTorch I_before_scaling=154450368
   - C I_before_scaling=104370.1042
   - Ratio ~1481× matches residual error after steps/polar

## Required Evidence (This Loop)

### Trace Variables to Capture

For source index 2 (first non-placeholder source in C):

- F_cell (structure factor)
- F_latt (lattice factor)
- I_before_scaling (pre-normalization intensity)
- polar (polarization factor)
- cos2theta (scattering angle)
- steps (normalization denominator)

### C Instrumentation Location

Around nanoBragg.c lines 2900-3200 (main pixel loop):
```c
if(source==2 && fpixel==trace_fpixel && spixel==trace_spixel){
  fprintf(stderr, "TRACE_C_SOURCE2: F_cell=%.15g\n", F_cell);
  fprintf(stderr, "TRACE_C_SOURCE2: F_latt=%.15g\n", F_latt);
  fprintf(stderr, "TRACE_C_SOURCE2: I_before_scaling=%.15g\n", I_before_scaling);
  fprintf(stderr, "TRACE_C_SOURCE2: polar=%.15g\n", polar);
  fprintf(stderr, "TRACE_C_SOURCE2: cos2theta=%.15g\n", cos2theta);
}
```

### PyTorch Trace Location

In `_compute_physics_for_position` when processing first source (index 0 in PyTorch = source 2 in C):
- Log same variables per source before final reduction
- Match format/precision with C trace

## Implementation Strategy (Deferred)

**DO NOT IMPLEMENT YET** - Evidence collection only this loop.

Proposed fixes (for future loop):
1. **Zero-weight placeholder injection**: Modify source initialization to add placeholders when hdivsteps/vdivsteps=0
2. **Steps reconciliation**: Count all sources including zero-weight
3. **Per-source polarization**: Apply polar before reduction, not after
4. **Preserve vectorization**: Use masked operations for zero-weight sources instead of Python loops

## Acceptance Criteria

- Trace bundle complete with py_trace_source2.txt, c_trace_source2.txt, diff.txt
- trace_notes.md documents first divergence and hypotheses
- No simulator code changes this loop
- Design reviewed before implementation

## References

- `golden_suite_generator/nanoBragg.c:2570-2720` — source ingestion
- `src/nanobrag_torch/simulator.py:847-874` — current steps calculation
- `docs/architecture/pytorch_design.md` §1.1 — vectorization rules
- `arch.md` §15 — differentiability guardrails
- `reports/2025-11-source-weights/phase_e/20251009T192746Z/trace/trace_notes.md` — baseline trace
