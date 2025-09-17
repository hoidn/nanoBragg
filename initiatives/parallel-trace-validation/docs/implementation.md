<!-- ACTIVE IMPLEMENTATION PLAN -->
<!-- DO NOT MISTAKE THIS FOR A TEMPLATE. THIS IS THE OFFICIAL SOURCE OF TRUTH FOR THE PROJECT'S PHASED PLAN. -->

# Phased Implementation Plan

**Project**: Deterministic Debugging of Tilted Detector Geometry via Parallel Tracing (v2)  
**Core Technologies**: PyTorch, Python, C, Bash

## 📄 DOCUMENT HIERARCHY

This document orchestrates the implementation of the objective defined in the main R&D plan.

- `initiatives/parallel-trace-validation/docs/rd-plan.md` (The high-level R&D Plan, v2)
- `initiatives/parallel-trace-validation/docs/implementation.md` (This file - The Phased Implementation Plan)
- `initiatives/parallel-trace-validation/docs/phase1.md` (Checklist for Phase 1: Instrumentation & Trace Generation)
- `initiatives/parallel-trace-validation/docs/phase2.md` (Checklist for Phase 2: Analysis, Fix & Verification)

## 🎯 PHASE-BASED IMPLEMENTATION

**Overall Goal**: To achieve a high-precision (atol=1e-8) match for the pix0_vector in the tilted BEAM pivot configuration by performing a rigorous, step-by-step numerical comparison between the PyTorch and C-code implementations, and thereby fix the end-to-end correlation failure.

## 📋 IMPLEMENTATION PHASES

### Phase 1: Instrumentation & Trace Generation

**Goal**: To instrument both C and Python codebases to produce detailed, comparable trace logs of the detector geometry calculation, and to create the tools for deterministic comparison.

**Deliverable**: A set of new/modified scripts and C code that can generate parallel trace logs, along with a comparator script to analyze them.

**Implementation Checklist**:  
The detailed, step-by-step implementation for this phase is tracked in: `[ ] phase1.md`

**Key Tasks Summary**:

1. **Determinism Guardrails**:
   - Update the C compilation flags in `golden_suite_generator/Makefile` to include `-fno-fast-math -ffp-contract=off`.
   - Update `scripts/c_reference_runner.py` to run the C executable with the `LC_NUMERIC=C` environment variable.

2. **C-Code Instrumentation**:
   - Add high-precision printf statements to `golden_suite_generator/nanoBragg.c` for every intermediate variable in the detector geometry pipeline, following the `TRACE_C:key=value` schema.
   - Log rotation matrices (Rx, Ry, Rz, R_total), basis vectors at each stage, convention mapping, and final pix0_vector calculation.

3. **Python Trace Script**:
   - Create `scripts/debug_beam_pivot_trace.py` to replicate the C-code's mathematical steps and produce an identically formatted `TRACE_PY:` log.
   - Force CPU + float64 execution with disabled gradients for maximum determinism.

4. **Comparator Tool**:
   - Create `scripts/compare_traces.py` to parse the two log files and report the first numerical discrepancy that exceeds a tolerance of 1e-12.
   - Handle different data types (scalars, vectors, matrices) with appropriate tolerance checking.

**Success Test (Acceptance Gate)**:
- Running the instrumented C code produces a well-formatted `c_trace.log`.
- Running `scripts/debug_beam_pivot_trace.py` produces a well-formatted `py_trace.log`.
- Running `scripts/compare_traces.py c_trace.log py_trace.log` executes successfully and reports the first mismatch.

**Duration**: 1-2 days

### Phase 2: Analysis, Fix & Verification

**Goal**: To use the parallel trace infrastructure to identify the root cause of the numerical discrepancy, implement a targeted fix, and validate the solution with a full suite of tests.

**Deliverable**: A corrected Detector class that passes all geometry tests with high precision and restores the end-to-end simulation correlation.

**Implementation Checklist**:  
The detailed, step-by-step implementation for this phase is tracked in: `[ ] phase2.md`

**Key Tasks Summary**:

1. **Analysis**:
   - Run the trace generation and comparison tools to identify the exact line of divergence.
   - Analyze the divergence point to understand the root cause (rotation order, convention mapping, numerical precision, etc.).

2. **Implementation**:
   - Apply a minimal, targeted fix to the single identified line of code in `src/nanobrag_torch/models/detector.py`.
   - Ensure the fix maintains differentiability and follows all project conventions.

3. **Verification**:
   - Rerun the trace comparison to confirm the logs now match within tolerance.
   - Update the ground-truth value in `tests/test_detector_geometry.py` with the newly verified pix0_vector from the C trace.
   - Run the `test_pix0_vector_matches_c_reference_in_beam_pivot` test and ensure it passes with atol=1e-8.
   - Run the end-to-end `scripts/verify_detector_geometry.py` script and confirm the tilted correlation is now > 0.999.

4. **Cleanup**:
   - Remove the instrumentation from nanoBragg.c and archive the debug scripts.
   - Document the fix in the commit message with reference to the trace analysis.
   - Commit the final, validated fix.

**Success Test (Acceptance Gate)**:
- All tests in `tests/test_detector_geometry.py` pass with high precision (atol=1e-8).
- The end-to-end correlation for the tilted detector test case exceeds 0.999.
- The bug is understood, fixed, and documented in the commit message.

**Duration**: 1 day

## 📝 PHASE TRACKING

- [ ] **Phase 1**: Instrumentation & Trace Generation
- [ ] **Phase 2**: Analysis, Fix & Verification

**Current Phase**: Phase 1: Instrumentation & Trace Generation

**Next Milestone**: A working parallel trace system that can identify the first point of numerical divergence between the C and Python implementations.

## 🔧 TECHNICAL SPECIFICATIONS

### Trace Schema Format
```
TRACE_X:key=value(s)
```

### Critical Trace Points
1. `detector_convention=MOSFLM`
2. `angles_rad=rotx:X roty:Y rotz:Z twotheta:W`
3. `beam_center_m=X:A Y:B pixel_mm:C`
4. `initial_fdet=X Y Z`, `initial_sdet=X Y Z`, `initial_odet=X Y Z`
5. `Rx=[matrix]`, `Ry=[matrix]`, `Rz=[matrix]`, `R_total=[matrix]`
6. `fdet_after_rotx=X Y Z`, etc. for each rotation stage
7. `convention_mapping=Fbeam←Ybeam_mm(+0.5px),Sbeam←Xbeam_mm(+0.5px),beam_vec=[1 0 0]`
8. `pix0_vector=X Y Z`

### Test Case Parameters (cubic_tilted_detector)
- **Pixel size**: 0.1 mm
- **Distance**: 100.0 mm  
- **Beam center**: Xbeam=51.2mm, Ybeam=51.2mm
- **Rotations**: rotx=1°, roty=5°, rotz=0°, twotheta=3°
- **Convention**: MOSFLM

### Success Metrics
- **Trace convergence**: All trace values match within 1e-12 tolerance
- **Geometry parity**: pix0_vector matches within 1e-8 tolerance
- **E2E correlation**: >0.999 for tilted detector configurations