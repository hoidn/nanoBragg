# Review Request: Phase 1 - Instrumentation & Trace Generation

**Initiative:** Parallel Trace Validation
**Generated:** 2025-08-13 19:21:58

## Instructions for Reviewer
1.  Analyze the planning documents and the code changes (`git diff`) below.
2.  Create a new file named `review_phase_1.md` in this same directory (`initiatives/parallel-trace-validation/docs/`).
3.  In your review file, you **MUST** provide a clear verdict on a single line: `VERDICT: ACCEPT` or `VERDICT: REJECT`.
4.  If rejecting, you **MUST** provide a list of specific, actionable fixes under a "Required Fixes" heading.

---
## 1. Planning Documents

### R&D Plan (`rd-plan.md`)
```markdown
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

This systematic approach ensures we identify and fix the geometry mismatch with mathematical precision rather than trial-and-error debugging.```

### Implementation Plan (`implementation.md`)
```markdown
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
- **E2E correlation**: >0.999 for tilted detector configurations```

### Phase Checklist (`phase1.md`)
```markdown
# Phase 1 — Instrumentation & Trace Generation (Self-Contained Checklist)

**Overall Goal**: instrument both C and Python to emit comparable, deterministic geometry traces and provide a comparator that halts on the first numeric mismatch.

**Update each task's State as you go**: `[ ]` → `[P]` → `[D]`.

## Section 1: Deterministic Build & Runtime

### 1.A Update C compiler flags — State: [ ]

**Why**: strict IEEE-754; avoid fused ops; enable trace toggling.  
**How**: add to `golden_suite_generator/Makefile`:

```makefile
# golden_suite_generator/Makefile
CFLAGS += -O2 -fno-fast-math -ffp-contract=off -DTRACING=1
```

### 1.B Update C runner environment — State: [ ]

**Why**: force `.` decimal regardless of locale.  
**How**: create/modify `scripts/c_reference_runner.py`:

```python
# scripts/c_reference_runner.py
import os, subprocess, sys

def run(cmd):
    env = {"LC_NUMERIC": "C", **os.environ}
    subprocess.run(cmd, env=env, check=True)

if __name__ == "__main__":
    # Replace with the actual C binary and args used by your golden script
    run(["./golden_suite_generator/nanobragg_c_tilted_beam"])
```

## Section 2: C-Code Instrumentation

### 2.A Add trace helper functions — State: [ ]

**Why**: consistent, single-line, high-precision trace records.  
**How**: at the top of `golden_suite_generator/nanoBragg.c`:

```c
#include <stdio.h>
#include <math.h>
#include <locale.h>

static void trace_vec(const char* tag, double x, double y, double z) {
    printf("TRACE_C:%s=%.15g %.15g %.15g\n", tag, x, y, z);
}
static void trace_mat3(const char* tag, const double M[3][3]) {
    printf("TRACE_C:%s=[%.15g %.15g %.15g; %.15g %.15g %.15g; %.15g %.15g %.15g]\n",
           tag, M[0][0],M[0][1],M[0][2], M[1][0],M[1][1],M[1][2], M[2][0],M[2][1],M[2][2]);
}
static void trace_scalar(const char* tag, double v) {
    printf("TRACE_C:%s=%.15g\n", tag, v);
}
```

### 2.B Instrument the detector geometry (BEAM pivot) — State: [ ]

**Why**: ground-truth, step-by-step parity against Python.  
**How**: inside the BEAM pivot code path (right after all angles and basis vectors are known, and before computing pix0_vector), add:

```c
#ifdef TRACING
setlocale(LC_NUMERIC, "C");

/* Replace these with your actual variables. This block assumes:
   - angles already converted to radians: detector_rotx, detector_roty, detector_rotz, detector_twotheta
   - MOSFLM initial basis before rotations: fdet_vector[3], sdet_vector[3], odet_vector[3]
   - beam center inputs in mm: Xbeam_mm, Ybeam_mm; pixel_size in meters or mm (see below)
   - distance in meters: distance
   - beam_vector = [1,0,0] (MOSFLM)
   - 0-based arrays. If 1-based in your code, adjust indices.
*/

/* 1) Headers */
printf("TRACE_C:detector_convention=MOSFLM\n");
printf("TRACE_C:angles_rad=rotx:%.15g roty:%.15g rotz:%.15g twotheta:%.15g\n",
       detector_rotx, detector_roty, detector_rotz, detector_twotheta);

/* beam_center_m logs X,Y in meters and pixel_mm for doc */
double pixel_mm = /* your pixel size in millimeters */ 0.1; /* set to your value */
printf("TRACE_C:beam_center_m=X:%.15g Y:%.15g pixel_mm:%.15g\n",
       Xbeam_mm/1000.0, Ybeam_mm/1000.0, pixel_mm);

/* 2) Initial basis */
trace_vec("initial_fdet", fdet_vector[0], fdet_vector[1], fdet_vector[2]);
trace_vec("initial_sdet", sdet_vector[0], sdet_vector[1], sdet_vector[2]);
trace_vec("initial_odet", odet_vector[0], odet_vector[1], odet_vector[2]);

/* 3) Explicit Rx,Ry,Rz and R_total = Rz @ Ry @ Rx */
double cx=cos(detector_rotx), sx=sin(detector_rotx);
double cy=cos(detector_roty), sy=sin(detector_roty);
double cz=cos(detector_rotz), sz=sin(detector_rotz);

double Rx[3][3]={{1,0,0},{0,cx,-sx},{0,sx,cx}};
double Ry[3][3]={{cy,0,sy},{0,1,0},{-sy,0,cy}};
double Rz[3][3]={{cz,-sz,0},{sz,cz,0},{0,0,1}};

/* R_total = Rz * Ry * Rx */
double Tmp[3][3], R_total[3][3];
/* Tmp = Rz * Ry */
for(int i=0;i<3;i++) for(int j=0;j<3;j++){ Tmp[i][j]=0; for(int k=0;k<3;k++) Tmp[i][j]+=Rz[i][k]*Ry[k][j]; }
/* R_total = Tmp * Rx */
for(int i=0;i<3;i++) for(int j=0;j<3;j++){ R_total[i][j]=0; for(int k=0;k<3;k++) R_total[i][j]+=Tmp[i][k]*Rx[k][j]; }

trace_mat3("Rx", Rx);
trace_mat3("Ry", Ry);
trace_mat3("Rz", Rz);
trace_mat3("R_total", R_total);

/* 4) Stage-wise rotated fdet */
double f_rx[3], f_ry[3], f_rz[3];
/* f_rx = Rx * fdet */
for(int i=0;i<3;i++){ f_rx[i]=Rx[i][0]*fdet_vector[0] + Rx[i][1]*fdet_vector[1] + Rx[i][2]*fdet_vector[2]; }
trace_vec("fdet_after_rotx", f_rx[0], f_rx[1], f_rx[2]);
/* f_ry = Ry * f_rx */
for(int i=0;i<3;i++){ f_ry[i]=Ry[i][0]*f_rx[0] + Ry[i][1]*f_rx[1] + Ry[i][2]*f_rx[2]; }
trace_vec("fdet_after_roty", f_ry[0], f_ry[1], f_ry[2]);
/* f_rz = Rz * f_ry */
for(int i=0;i<3;i++){ f_rz[i]=Rz[i][0]*f_ry[0] + Rz[i][1]*f_ry[1] + Rz[i][2]*f_ry[2]; }
trace_vec("fdet_after_rotz", f_rz[0], f_rz[1], f_rz[2]);

/* Similarly rotate sdet and odet (to apply twotheta next) */
double s_rx[3], s_ry[3], s_rz[3], o_rx[3], o_ry[3], o_rz[3];
for(int i=0;i<3;i++){ s_rx[i]=Rx[i][0]*sdet_vector[0] + Rx[i][1]*sdet_vector[1] + Rx[i][2]*sdet_vector[2]; }
for(int i=0;i<3;i++){ s_ry[i]=Ry[i][0]*s_rx[0] + Ry[i][1]*s_rx[1] + Ry[i][2]*s_rx[2]; }
for(int i=0;i<3;i++){ s_rz[i]=Rz[i][0]*s_ry[0] + Rz[i][1]*s_ry[1] + Rz[i][2]*s_ry[2]; }
for(int i=0;i<3;i++){ o_rx[i]=Rx[i][0]*odet_vector[0] + Rx[i][1]*odet_vector[1] + Rx[i][2]*odet_vector[2]; }
for(int i=0;i<3;i++){ o_ry[i]=Ry[i][0]*o_rx[0] + Ry[i][1]*o_rx[1] + Ry[i][2]*o_rx[2]; }
for(int i=0;i<3;i++){ o_rz[i]=Rz[i][0]*o_ry[0] + Rz[i][1]*o_ry[1] + Rz[i][2]*o_ry[2]; }

/* 5) Two-theta around axis [0,0,-1] (MOSFLM) using Rodrigues */
double axis[3]={0.0,0.0,-1.0};
trace_vec("twotheta_axis", axis[0], axis[1], axis[2]);

/* helper: rotate v by angle a around unit axis k */
auto rotate_axis = [](const double v[3], const double k[3], double a, double out[3]){
    double c=cos(a), s=sin(a);
    double cross[3]={ k[1]*v[2]-k[2]*v[1], k[2]*v[0]-k[0]*v[2], k[0]*v[1]-k[1]*v[0] };
    double dot = k[0]*v[0]+k[1]*v[1]+k[2]*v[2];
    for(int i=0;i<3;i++) out[i] = v[i]*c + cross[i]*s + k[i]*dot*(1.0-c);
};

/* apply twotheta */
double f_tt[3], s_tt[3], o_tt[3];
rotate_axis(f_rz, axis, detector_twotheta, f_tt);
rotate_axis(s_rz, axis, detector_twotheta, s_tt);
rotate_axis(o_rz, axis, detector_twotheta, o_tt);

trace_vec("fdet_after_twotheta", f_tt[0], f_tt[1], f_tt[2]);
trace_vec("sdet_after_twotheta", s_tt[0], s_tt[1], s_tt[2]);
trace_vec("odet_after_twotheta", o_tt[0], o_tt[1], o_tt[2]);

/* 6) Beam-center mapping & scalars (MOSFLM): Fbeam←Ybeam_mm(+0.5 px), Sbeam←Xbeam_mm(+0.5 px) */
printf("TRACE_C:convention_mapping=Fbeam←Ybeam_mm(+0.5px),Sbeam←Xbeam_mm(+0.5px),beam_vec=[1 0 0]\n");
double Fbeam = (Ybeam_mm + 0.5*pixel_mm) / 1000.0;  /* meters */
double Sbeam = (Xbeam_mm + 0.5*pixel_mm) / 1000.0;  /* meters */
trace_scalar("Fbeam_m", Fbeam);
trace_scalar("Sbeam_m", Sbeam);
trace_scalar("distance_m", distance);

/* 7) Terms and pix0 */
double term_fast[3]={ -Fbeam*f_tt[0], -Fbeam*f_tt[1], -Fbeam*f_tt[2] };
double term_slow[3]={ -Sbeam*s_tt[0], -Sbeam*s_tt[1], -Sbeam*s_tt[2] };
double term_beam[3]={ distance*1.0, 0.0, 0.0 }; /* beam_vec=[1,0,0] */
trace_vec("term_fast", term_fast[0], term_fast[1], term_fast[2]);
trace_vec("term_slow", term_slow[0], term_slow[1], term_slow[2]);
trace_vec("term_beam", term_beam[0], term_beam[1], term_beam[2]);

double pix0_vector[3]={ term_fast[0]+term_slow[0]+term_beam[0],
                         term_fast[1]+term_slow[1]+term_beam[1],
                         term_fast[2]+term_slow[2]+term_beam[2] };
trace_vec("pix0_vector", pix0_vector[0], pix0_vector[1], pix0_vector[2]);
#endif /* TRACING */
```

⚠️ **Adjust variable names** (`Xbeam_mm`, `Ybeam_mm`, `pixel_mm`, `distance`, `fdet_vector`, etc.) to match your C. Keep the keys and order exactly as shown.

### 2.C Recompile C — State: [ ]
```bash
make -C golden_suite_generator clean all
```

## Section 3: Python Trace & Comparator

### 3.A Create Python trace script — State: [ ]

**File**: `scripts/debug_beam_pivot_trace.py`

```python
#!/usr/bin/env python3
import os, math, argparse
import numpy as np

os.environ["CUDA_VISIBLE_DEVICES"] = ""
np.set_printoptions(precision=17, floatmode="maxprec_equal", suppress=False)

def deg2rad(x): return x * math.pi / 180.0
def R_x(ax):
    c, s = math.cos(ax), math.sin(ax)
    return np.array([[1.0,0.0,0.0],[0.0,c,-s],[0.0,s,c]], dtype=np.float64)
def R_y(ay):
    c, s = math.cos(ay), math.sin(ay)
    return np.array([[c,0.0,s],[0.0,1.0,0.0],[-s,0.0,c]], dtype=np.float64)
def R_z(az):
    c, s = math.cos(az), math.sin(az)
    return np.array([[c,-s,0.0],[s,c,0.0],[0.0,0.0,1.0]], dtype=np.float64)
def rotate_axis(v, axis, phi):
    axis = axis / np.linalg.norm(axis)
    c, s = math.cos(phi), math.sin(phi)
    cross = np.cross(axis, v)
    dot   = np.dot(axis, v)
    return v*c + cross*s + axis*dot*(1.0 - c)

def p_vec(tag, v): print(f"TRACE_PY:{tag}={v[0]:.15g} {v[1]:.15g} {v[2]:.15g}")
def p_mat(tag, M):
    a,b,c = M
    print(f"TRACE_PY:{tag}=[{a[0]:.15g} {a[1]:.15g} {a[2]:.15g}; "
          f"{b[0]:.15g} {b[1]:.15g} {b[2]:.15g}; "
          f"{c[0]:.15g} {c[1]:.15g} {c[2]:.15g}]")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pixel-mm", type=float, default=0.1)
    ap.add_argument("--distance-mm", type=float, default=100.0)
    ap.add_argument("--xbeam-mm", type=float, default=51.2)
    ap.add_argument("--ybeam-mm", type=float, default=51.2)
    ap.add_argument("--rotx-deg", type=float, default=1.0)
    ap.add_argument("--roty-deg", type=float, default=5.0)
    ap.add_argument("--rotz-deg", type=float, default=0.0)
    ap.add_argument("--twotheta-deg", type=float, default=3.0)
    args = ap.parse_args()

    rotx = deg2rad(args.rotx_deg)
    roty = deg2rad(args.roty_deg)
    rotz = deg2rad(args.rotz_deg)
    tth  = deg2rad(args.twotheta_deg)

    print("TRACE_PY:detector_convention=MOSFLM")
    print(f"TRACE_PY:angles_rad=rotx:{rotx:.15g} roty:{roty:.15g} rotz:{rotz:.15g} twotheta:{tth:.15g}")
    print(f"TRACE_PY:beam_center_m=X:{args.xbeam_mm/1000.0:.15g} Y:{args.ybeam_mm/1000.0:.15g} pixel_mm:{args.pixel_mm:.15g}")

    fdet = np.array([0.0,  0.0, 1.0])
    sdet = np.array([0.0, -1.0, 0.0])
    odet = np.array([1.0,  0.0, 0.0])
    p_vec("initial_fdet", fdet); p_vec("initial_sdet", sdet); p_vec("initial_odet", odet)

    Rx, Ry, Rz = R_x(rotx), R_y(roty), R_z(rotz)
    R = Rz @ Ry @ Rx
    p_mat("Rx", Rx); p_mat("Ry", Ry); p_mat("Rz", Rz); p_mat("R_total", R)

    f_rx = Rx @ fdet; p_vec("fdet_after_rotx", f_rx)
    f_ry = Ry @ f_rx; p_vec("fdet_after_roty", f_ry)
    f_rz = Rz @ f_ry; p_vec("fdet_after_rotz", f_rz)

    s_rz = Rz @ (Ry @ (Rx @ sdet))
    o_rz = Rz @ (Ry @ (Rx @ odet))

    tth_axis = np.array([0.0, 0.0, -1.0])
    p_vec("twotheta_axis", tth_axis)

    f_tt = rotate_axis(f_rz, tth_axis, tth); p_vec("fdet_after_twotheta", f_tt)
    s_tt = rotate_axis(s_rz, tth_axis, tth); p_vec("sdet_after_twotheta", s_tt)
    o_tt = rotate_axis(o_rz, tth_axis, tth); p_vec("odet_after_twotheta", o_tt)

    print("TRACE_PY:convention_mapping=Fbeam←Ybeam_mm(+0.5px),Sbeam←Xbeam_mm(+0.5px),beam_vec=[1 0 0]")
    Fbeam_m = (args.ybeam_mm + 0.5*args.pixel_mm) / 1000.0
    Sbeam_m = (args.xbeam_mm + 0.5*args.pixel_mm) / 1000.0
    dist_m  =  args.distance_mm / 1000.0
    print(f"TRACE_PY:Fbeam_m={Fbeam_m:.15g}")
    print(f"TRACE_PY:Sbeam_m={Sbeam_m:.15g}")
    print(f"TRACE_PY:distance_m={dist_m:.15g}")

    term_fast = -Fbeam_m * f_tt; p_vec("term_fast", term_fast)
    term_slow = -Sbeam_m * s_tt; p_vec("term_slow", term_slow)
    term_beam =  dist_m  * np.array([1.0, 0.0, 0.0]); p_vec("term_beam", term_beam)

    pix0 = term_fast + term_slow + term_beam
    p_vec("pix0_vector", pix0)

if __name__ == "__main__":
    main()
```

### 3.B Create comparator — State: [ ]

**File**: `scripts/compare_traces.py`

```python
#!/usr/bin/env python3
import sys, math, re

TOL = 1e-12

def parse_line(line):
    try:
        _, rest = line.strip().split(":", 1)
        key, val = rest.split("=", 1)
        return key, val.strip()
    except ValueError:
        return None, None

def parse_vals(s):
    if s.startswith("[") and s.endswith("]"):
        rows = [r.strip() for r in s[1:-1].split(";")]
        return [list(map(float, r.split())) for r in rows]
    if ":" in s and " " in s and re.search(r":[-+0-9.]", s):
        out = {}
        for tok in s.split():
            k, v = tok.split(":")
            out[k] = float(v)
        return out
    parts = s.split()
    if len(parts) == 1:
        try: return float(parts[0])
        except: return s
    return list(map(float, parts))

def close(a, b, tol=TOL):
    if type(a) != type(b): return False
    if isinstance(a, float): return math.isfinite(a) and math.isfinite(b) and abs(a-b) <= tol
    if isinstance(a, list):
        if len(a) != len(b): return False
        if isinstance(a[0], list):
            return all(close(r1, r2, tol) for r1, r2 in zip(a,b))
        return all(abs(x-y) <= tol for x,y in zip(a,b))
    if isinstance(a, dict):
        return a.keys()==b.keys() and all(abs(a[k]-b[k]) <= tol for k in a)
    return a == b

def main(c_log, p_log):
    c_lines = [l for l in open(c_log) if l.startswith("TRACE_C:")]
    p_lines = [l for l in open(p_log) if l.startswith("TRACE_PY:")]
    if len(c_lines) != len(p_lines):
        print(f"Line count differs: C={len(c_lines)} PY={len(p_lines)}"); sys.exit(1)
    for i, (lc, lp) in enumerate(zip(c_lines, p_lines), 1):
        kc, vc = parse_line(lc); kp, vp = parse_line(lp)
        if kc != kp:
            print(f"Key mismatch at line {i}: C:{kc} vs PY:{kp}"); sys.exit(1)
        pc, pp = parse_vals(vc), parse_vals(vp)
        if not close(pc, pp):
            print(f"Value mismatch at key '{kc}' (line {i}):")
            print(f"  C : {vc}")
            print(f"  PY: {vp}")
            sys.exit(1)
    print("OK: traces match within tolerance.")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
```

## Section 4: Verification of Infrastructure

### 4.A Generate C trace log — State: [ ]

**How**:

```bash
# build instrumented C
make -C golden_suite_generator clean all

# run the exact golden command (from your regenerate_golden.sh)
python scripts/c_reference_runner.py > tests/golden_data/cubic_tilted_detector/c_trace.log
```

### 4.B Generate Python trace log — State: [ ]

**How**: (match the exact parameters from the C run)

```bash
python scripts/debug_beam_pivot_trace.py \
  --pixel-mm 0.1 \
  --distance-mm 100.0 \
  --xbeam-mm 51.2 \
  --ybeam-mm 51.2 \
  --rotx-deg 1.0 \
  --roty-deg 5.0 \
  --rotz-deg 0.0 \
  --twotheta-deg 3.0 \
  > tests/golden_data/cubic_tilted_detector/py_trace.log
```

### 4.C Run the comparator — State: [ ]
```bash
python scripts/compare_traces.py \
  tests/golden_data/cubic_tilted_detector/c_trace.log \
  tests/golden_data/cubic_tilted_detector/py_trace.log
```

**Expected**: prints the first mismatched key/value and exits non-zero (or "OK" if identical within 1e-12).

## Section 5: Finalization

### 5.A Format & lint — State: [ ]
```bash
black scripts/*.py
ruff scripts/*.py --fix
```

### 5.B Commit Phase 1 — State: [ ]

**Message**:
```
feat(debug): Phase 1 - Implement parallel trace infrastructure for detector geometry

Phase 1 Acceptance Gate
```

## Phase 1 Acceptance Gate

✅ `compare_traces.py` runs and either prints OK or the first numerical divergence for the tilted case.

✅ All new/modified files are committed.```

---
## 2. Code Changes for This Phase

**Baseline Commit:** HEAD

```diff
```
