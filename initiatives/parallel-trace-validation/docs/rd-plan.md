# Parallel Trace Validation Initiative

## Executive Summary

This initiative implements a systematic parallel trace validation strategy to identify and fix the detector geometry mismatch causing correlation failures in tilted detector configurations. The approach leverages deterministic, step-by-step logging from both C and Python implementations to isolate the exact divergence point.

## Problem Statement

Current detector geometry calculations show correlation mismatches between C reference and PyTorch implementation:
- **Simple cubic (no tilt)**: Perfect correlation (>0.999)
- **Tilted detector cases**: Poor correlation (<0.9), indicating systematic geometry calculation errors

## Solution Approach: Deterministic Parallel Tracing

### Core Strategy
Use identical, deterministic trace logging from both C and Python to create line-by-line comparable execution logs. Compare these logs with tolerance-based validation to identify the exact point where calculations diverge.

### Key Technical Improvements

#### 1. Determinism Guardrails
- **Python**: Force CPU + float64, disable gradients, fix RNG
- **C**: Compile with strict IEEE doubles (`-fno-fast-math -ffp-contract=off`)
- **Environment**: Set `LC_NUMERIC=C` to avoid locale issues

#### 2. Standardized Trace Schema
```
TRACE_X:key=value(s)
```
- One key per line, identical ordering in C and Python
- All angles in radians, positions in meters
- Explicit logging of rotation matrices and stage-by-stage transformations

#### 3. Critical Data Points to Trace
- **Convention mapping**: MOSFLM Fbeam←Ybeam, Sbeam←Xbeam with +0.5px adjustment
- **Initial basis vectors**: fdet, sdet, odet before any rotations
- **Rotation matrices**: Individual Rx, Ry, Rz and composite R_total = Rz@Ry@Rx
- **Stage-by-stage vectors**: After each rotation (rotx, roty, rotz, twotheta)
- **Final pix0 calculation**: All terms and final vector

## Implementation Plan

### Phase 1: Infrastructure Setup
1. **C Code Instrumentation**
   - Add trace helper functions to nanoBragg.c
   - Insert comprehensive logging in detector geometry section
   - Compile with strict IEEE compliance flags

2. **Python Tracer Script**
   - Create `scripts/debug_beam_pivot_trace.py`
   - Mirror C math exactly (no Detector class calls)
   - Match trace output format and ordering

3. **Trace Comparator**
   - Build `scripts/compare_traces.py` with tolerance checking
   - Stop at first divergence point with detailed delta reporting

### Phase 2: Validation & Debugging
4. **Generate Test Traces**
   - Run both C and Python tracers on cubic_tilted_detector case
   - Compare traces to identify divergence point

5. **Fix Geometry Bug**
   - Analyze divergence point to understand root cause
   - Implement fix in PyTorch detector geometry

6. **Verification**
   - Re-run traces to confirm convergence
   - Validate E2E correlation >0.999

### Phase 3: Test Integration
7. **Unit Tests**
   - Add `test_pix0_vector_matches_c_reference_in_beam_pivot`
   - Strict tolerance checking (1e-8)

8. **CI Integration**
   - Ensure geometry tests gate any detector changes

## Deliverables

### Scripts
- `initiatives/parallel-trace-validation/scripts/debug_beam_pivot_trace.py`
- `initiatives/parallel-trace-validation/scripts/compare_traces.py`
- `initiatives/parallel-trace-validation/scripts/instrument_c_code.patch`

### Traces
- `initiatives/parallel-trace-validation/traces/c_cubic_tilted.log`
- `initiatives/parallel-trace-validation/traces/py_cubic_tilted.log`
- `initiatives/parallel-trace-validation/traces/divergence_analysis.md`

### Tests
- `initiatives/parallel-trace-validation/tests/test_geometry_parity.py`
- Integration into main test suite

### Documentation
- This R&D plan
- Divergence analysis report
- Geometry fix implementation notes

## Success Criteria

1. **Trace Convergence**: C and Python traces match within 1e-12 tolerance
2. **Geometry Parity**: pix0_vector calculations identical between implementations
3. **Correlation Recovery**: E2E correlation >0.999 for all detector configurations
4. **Robust Testing**: Geometry parity tests prevent regression

## Timeline

- **Week 1**: Infrastructure setup (C instrumentation, Python tracer, comparator)
- **Week 2**: Trace generation, divergence analysis, geometry fix
- **Week 3**: Verification, test integration, documentation

## Technical Notes

### MOSFLM Convention Mapping
```
Fbeam = (Ybeam_mm + 0.5 * pixel_mm) / 1000.0  # meters
Sbeam = (Xbeam_mm + 0.5 * pixel_mm) / 1000.0  # meters
beam_vector = [1, 0, 0]  # X-axis
twotheta_axis = [0, 0, -1]  # -Z axis
```

### Rotation Order (Extrinsic XYZ)
```
R_total = Rz @ Ry @ Rx
```

### Critical Trace Points
- Initial basis vectors (MOSFLM convention)
- Each rotation matrix (Rx, Ry, Rz)
- Vectors after each rotation stage
- Convention mapping values
- Final pix0_vector calculation

This systematic approach ensures we identify and fix the geometry mismatch with mathematical precision rather than trial-and-error debugging.