# Phase 1 — Diagnosis & Root Cause Analysis (Self-Contained Checklist)

**Overall Goal**: Identify the exact source of the 0.040 correlation failure in tilted detector configurations through systematic parameter verification, trace comparison, and convention analysis.

**Prerequisites**: C-code already instrumented with TRACING macros; parallel trace infrastructure available.

**Update each task's State as you go**: `[ ]` → `[P]` (In Progress) → `[D]` (Done)

---

## Section 1: Environment Setup & Build Verification

### 1.A Verify trace-enabled C build — State: [ ]

**Why**: Ensure C executable has trace output enabled for parallel debugging.  
**How**: Check compilation flags and rebuild if necessary.

```bash
cd golden_suite_generator
grep "TRACING" Makefile  # Should show -DTRACING=1

# If not present, rebuild with tracing:
make clean
make nanoBragg CFLAGS="-O2 -lm -fno-fast-math -ffp-contract=off -DTRACING=1 -fopenmp"

# Verify trace output works:
./nanoBragg -lambda 6.2 -N 1 -default_F 100 2>&1 | grep "TRACE_C:"
# Should see output like: TRACE_C:detector_convention=MOSFLM
```

### 1.B Set deterministic environment — State: [ ]

**Why**: Ensure reproducible numeric output across runs.  
**How**: Configure environment variables for both C and Python.

```bash
# Add to your shell session or script:
export LC_NUMERIC=C                # Consistent decimal formatting
export KMP_DUPLICATE_LIB_OK=TRUE   # Prevent PyTorch MKL conflicts
export PYTHONPATH=$PWD/src:$PYTHONPATH
```

---

## Section 2: Parameter Verification (Priority 1.1)

### 2.A Generate parameter parity report — State: [ ]

**Why**: Confirm C code receives correct parameters, especially twotheta_axis.  
**How**: Run verification script with debug output.

```bash
# Run with explicit debug output
cd /Users/ollie/Documents/nanoBragg
python scripts/verify_detector_geometry.py > results/parameter_verification/parity_report.txt 2>&1

# Check for parameter mismatches
grep "CONFIGURATION PARITY TABLE" results/parameter_verification/parity_report.txt -A 20
```

### 2.B Add C-code parameter debug output — State: [ ]

**Why**: Verify twotheta_axis is fully received (all 3 components).  
**How**: Add temporary debug printf to nanoBragg.c after parameter parsing.

```c
// In nanoBragg.c, after argument parsing (around line 200):
#ifdef TRACING
printf("DEBUG: twotheta_axis = [%f, %f, %f]\n", 
       twotheta_axis[1], twotheta_axis[2], twotheta_axis[3]);
printf("DEBUG: detector_pivot = %s\n", 
       detector_pivot == SAMPLE ? "SAMPLE" : "BEAM");
#endif
```

Recompile and test:
```bash
cd golden_suite_generator
make nanoBragg
./nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 1024 -Xbeam 61.2 -Ybeam 61.2 \
  -detector_rotx 5 -detector_roty 3 -detector_rotz 2 \
  -twotheta 20 -twotheta_axis 0 0 -1 -pivot SAMPLE \
  2>&1 | grep "DEBUG:" > ../results/parameter_verification/c_params_debug.txt
```

### 2.C Document parameter findings — State: [ ]

**Why**: Record any parameter passing issues for the fix phase.  
**How**: Update findings document with discovered issues.

```bash
# Document in findings.md:
echo "## Parameter Verification Results" >> docs/findings.md
echo "C receives twotheta_axis: $(grep twotheta_axis results/parameter_verification/c_params_debug.txt)" >> docs/findings.md
echo "Pivot mode: $(grep detector_pivot results/parameter_verification/c_params_debug.txt)" >> docs/findings.md
```

---

## Section 3: Single Pixel Trace Comparison (Priority 1.2)

### 3.A Generate C trace for pixel (377, 644) — State: [ ]

**Why**: This pixel shows ~208 pixel displacement in tilted configuration.  
**How**: Run C code with tilted parameters and capture trace output.

```bash
cd golden_suite_generator

# Generate trace for specific pixel
./nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 1024 -Xbeam 61.2 -Ybeam 61.2 \
  -detector_rotx 5 -detector_roty 3 -detector_rotz 2 \
  -twotheta 20 -pivot SAMPLE \
  2>&1 | grep "TRACE_C:" > ../initiatives/detector-correlation-fix/traces/c_pixel_377_644.trace

# Count trace lines
wc -l ../initiatives/detector-correlation-fix/traces/c_pixel_377_644.trace
```

### 3.B Generate Python trace for same pixel — State: [ ]

**Why**: Create parallel trace from PyTorch implementation.  
**How**: Use or create debug script matching C trace points.

```python
# Create/update scripts/debug_tilted_trace.py:
#!/usr/bin/env python3
import os
import sys
import torch
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.detector import Detector

# Match C parameters exactly
config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    detector_pivot=DetectorPivot.SAMPLE,
    distance_mm=100.0,
    beam_center_s=61.2,  # Maps to Xbeam
    beam_center_f=61.2,  # Maps to Ybeam  
    pixel_size_mm=0.1,
    detector_rotx_deg=5.0,
    detector_roty_deg=3.0,
    detector_rotz_deg=2.0,
    detector_twotheta_deg=20.0,
)

detector = Detector(config)

# Trace key values
print(f"TRACE_PY:detector_convention=MOSFLM")
print(f"TRACE_PY:pivot_mode={config.detector_pivot.name}")
print(f"TRACE_PY:beam_center_s={config.beam_center_s:.15g}")
print(f"TRACE_PY:beam_center_f={config.beam_center_f:.15g}")

# Get pixel (377, 644) coordinates
pixel_coords = detector.get_pixel_coords(torch.tensor([[377.0, 644.0]]))
print(f"TRACE_PY:pixel_377_644={pixel_coords[0,0]:.15g} {pixel_coords[0,1]:.15g} {pixel_coords[0,2]:.15g}")

# Trace pix0_vector
pix0 = detector.pix0_vector
print(f"TRACE_PY:pix0_vector={pix0[0]:.15g} {pix0[1]:.15g} {pix0[2]:.15g}")
```

Run and capture:
```bash
python scripts/debug_tilted_trace.py > initiatives/detector-correlation-fix/traces/py_pixel_377_644.trace 2>&1
```

### 3.C Compare traces to find divergence — State: [ ]

**Why**: Identify exact calculation step where values diverge.  
**How**: Use trace comparison tool or manual diff.

```bash
cd initiatives/detector-correlation-fix

# Use existing comparison tool if available
python ../../archive/parallel_trace_debugger/compare_traces.py \
  traces/c_pixel_377_644.trace \
  traces/py_pixel_377_644.trace \
  > results/trace_comparison/divergence_report.txt

# Or manual comparison
diff -u traces/c_pixel_377_644.trace traces/py_pixel_377_644.trace | head -50
```

---

## Section 4: Rotation Convention Analysis (Priority 2)

### 4.A Test rotation matrix construction — State: [ ]

**Why**: Verify PyTorch and C use same Euler angle convention.  
**How**: Run rotation matrix comparison script.

```bash
cd initiatives/detector-correlation-fix
python scripts/test_rotation_matrices.py

# Check conclusion
grep "CONCLUSION" results/rotation_analysis/rotation_matrix_comparison.txt -A 2
```

### 4.B Verify twotheta rotation implementation — State: [ ]

**Why**: Confirm twotheta rotation axis and application method match.  
**How**: Run twotheta rotation test.

```bash
python scripts/test_twotheta_rotation.py

# Check orthogonality preservation
grep "Orthogonality check" results/rotation_analysis/twotheta_rotation_test.txt
```

### 4.C Validate basis vector conventions — State: [ ]

**Why**: Ensure initial basis vectors and coordinate system match.  
**How**: Run basis vector verification.

```bash
python scripts/verify_basis_vectors.py

# Check summary
grep "SUMMARY" results/rotation_analysis/basis_vector_verification.txt -A 5
```

---

## Section 5: Progressive Rotation Testing (Priority 4.1)

### 5.A Create progressive rotation test script — State: [ ]

**Why**: Isolate which rotation component causes correlation failure.  
**How**: Test incrementally adding rotations.

```python
# Create scripts/progressive_rotation_test.py:
#!/usr/bin/env python3
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

test_cases = [
    {"name": "baseline", "rotx": 0, "roty": 0, "rotz": 0, "twotheta": 0},
    {"name": "rotx_only", "rotx": 5, "roty": 0, "rotz": 0, "twotheta": 0},
    {"name": "roty_only", "rotx": 0, "roty": 3, "rotz": 0, "twotheta": 0},
    {"name": "rotz_only", "rotx": 0, "roty": 0, "rotz": 2, "twotheta": 0},
    {"name": "xyz_no_twotheta", "rotx": 5, "roty": 3, "rotz": 2, "twotheta": 0},
    {"name": "twotheta_only", "rotx": 0, "roty": 0, "rotz": 0, "twotheta": 20},
    {"name": "full_tilted", "rotx": 5, "roty": 3, "rotz": 2, "twotheta": 20},
]

for test in test_cases:
    # Run verification for each configuration
    # Save correlation values
    pass
```

### 5.B Execute progressive tests — State: [ ]

**Why**: Identify at which rotation step correlation degrades.  
**How**: Run test script and collect results.

```bash
python scripts/progressive_rotation_test.py > results/rotation_analysis/progressive_test_results.txt
```

---

## Phase 1 Acceptance Gate

Before proceeding to Phase 2, ensure:

✅ Parameter verification complete - any C parameter issues documented  
✅ Trace divergence point identified - exact variable and line number recorded  
✅ Rotation convention analysis complete - any differences documented  
✅ Progressive rotation tests show which component causes failure  
✅ All findings documented in `docs/findings.md` with specific technical details  

## Quick Command Reference

```bash
# Environment setup
export LC_NUMERIC=C KMP_DUPLICATE_LIB_OK=TRUE

# Generate traces
cd golden_suite_generator
./nanoBragg [params] 2>&1 | grep "TRACE_C:" > ../traces/c_trace.log
python ../scripts/debug_tilted_trace.py > ../traces/py_trace.log

# Compare traces
python archive/parallel_trace_debugger/compare_traces.py traces/c_trace.log traces/py_trace.log

# Run test scripts
python scripts/test_rotation_matrices.py
python scripts/test_twotheta_rotation.py
python scripts/verify_basis_vectors.py
```

---

**Next Phase**: Once root cause is identified, proceed to `phase2-checklist.md` for fix implementation.