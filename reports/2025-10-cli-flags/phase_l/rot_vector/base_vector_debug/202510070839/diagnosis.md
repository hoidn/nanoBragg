# CLI-FLAGS-003 Phase L3k.3b Diagnosis
## Timestamp: 2025-10-07 08:41 UTC
## Tag: 202510070839

## Objective
Regenerate per-φ C and PyTorch traces with TRACE_C_PHI instrumentation active to diagnose φ rotation parity issues.

## C Trace Generation
**Command:**
```bash
./golden_suite_generator/nanoBragg -mat A.mat -floatfile img.bin -hkl scaled.hkl \
  -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 \
  -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 \
  -distance 231.274660 -lambda 0.976800 -pixel 0.172 \
  -detpixels_x 2463 -detpixels_y 2527 \
  -odet_vector -0.000088 0.004914 -0.999988 \
  -sdet_vector -0.005998 -0.999970 -0.004913 \
  -fdet_vector 0.999982 -0.005998 -0.000118 \
  -pix0_vector_mm -216.336293 215.205512 -230.200866 \
  -beam_vector 0.00051387949 0.0 -0.99999986 \
  -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 \
  -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 \
  -trace_pixel 685 1039
```

**TRACE_C_PHI Availability:** ✅ **PRESENT**
- 10 TRACE_C_PHI lines captured (phi_tic 0-9)
- C binary was instrumented with -trace_pixel flag
- Instrumentation location: `golden_suite_generator/nanoBragg.c:3156-3160`

## PyTorch Trace Generation
**Command:**
```bash
PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python \
  reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py \
  --config supervisor --pixel 685 1039 \
  --out trace_py_rot_vector_202510070839.log \
  --device cpu --dtype float64
```

**TRACE_PY_PHI Availability:** ✅ **PRESENT**
- 10 TRACE_PY_PHI lines captured (phi_tic 0-9)
- Output: `trace_py_rot_vector_202510070839_per_phi.json`

## Key Findings: k_frac Deltas

### φ_tic=0 (DIVERGENCE POINT)
- **C k_frac:** -0.607255839576692
- **PyTorch k_frac:** -0.589139352775903
- **Δk:** 1.811649e-02 (❌ DIVERGENCE)

### φ_tic=1-9 (ACCEPTABLE DELTAS)
- **Max Δk:** 2.845147e-05
- **Status:** ✅ All within tolerance

### Observation
The **first φ step (φ=0°)** shows significant divergence (Δk ≈ 0.018), but subsequent φ steps (φ>0°) show excellent agreement (Δk < 3e-5).

## Root Cause Hypotheses

### H1: φ=0 Initialization Issue
C implementation may handle φ=0 differently than φ>0. At φ=0°, C shows **identical k_frac values** at φ_tic=0 and φ_tic=9:
- φ_tic=0: k=-0.607255839576692
- φ_tic=9: k=-0.607255839576692

PyTorch shows **different values**:
- φ_tic=0: k=-0.589139352775903
- φ_tic=9: k=-0.607227388110849

**Implication:** PyTorch's φ=0 rotation may not match the C "no rotation" path.

### H2: Spindle Axis Application
The supervisor command specifies `-spindle_axis -1 0 0` (rotation about -X axis). PyTorch may:
1. Apply the rotation differently at φ=0
2. Use a different rotation convention (Rodrigues vs axis-angle)
3. Have sign convention mismatch on spindle axis

### H3: Base Lattice Vector Parity
Before φ rotation is applied, base lattice vectors (a, b, c) may already differ between C and PyTorch, causing the k_frac mismatch at φ=0.

## Next Actions (from input.md Do Now)

1. ✅ **Phase L3k.3b COMPLETE** - Generated per-φ traces with TRACE_C_PHI data present
2. ⏭️ **Phase L3k.3d** - Resolve nb-compare ROI anomaly before VG-3/VG-4
3. ⏭️ **Phase L3k.3e** - Update `mosflm_matrix_correction.md` with findings
4. ⏭️ **Phase L3k.4** - Log attempt in fix_plan.md with metrics

## Artifact Summary
- C trace: `c_trace_phi_202510070839.log` (10 TRACE_C_PHI lines)
- PyTorch trace: `trace_py_rot_vector_202510070839_per_phi.json` (10 entries)
- Comparison: `comparison_summary.md` (table + root cause)
- This diagnosis: `diagnosis.md`

## Metrics
- **TRACE_C_PHI lines:** 10 ✅
- **TRACE_PY_PHI lines:** 10 ✅
- **First divergence:** φ_tic=0, Δk=1.811649e-02
- **Subsequent deltas:** Δk < 3e-5 (9/10 steps within tolerance)
- **k_frac span (PyTorch):** 1.8088e-02 (from comparison output)
