# Phase K3f Evidence: Base Lattice & Scattering Trace Comparison

**Date:** 2025-10-06  
**Phase:** CLI-FLAGS-003 Phase K3f (Evidence Only)  
**Objective:** Diagnose the Δk≈6 Miller index mismatch by capturing base lattice vectors before φ rotation

## Executive Summary

Phase K3f successfully captured matched C/PyTorch traces for base lattice vectors and identified the **first divergence**: reciprocal vectors (`a_star`, `b_star`, `c_star`) differ by a factor of **~40.51×**.

### Key Findings

1. **Reciprocal Vector Scaling Error (First Divergence)**
   - PyTorch reciprocal vectors are 40.51× larger than C
   - All three vectors (a*, b*, c*) show identical scaling factor
   - This strongly suggests a λ-scaling problem in MOSFLM matrix loading

2. **Real Vector Cascade**
   - Real-space vectors (a, b, c) are ~405,149× larger in PyTorch
   - This cascades from the reciprocal vector error via the cross-product calculation

3. **Volume Inversion**
   - C: V_cell = 24,682 m³ (should be Å³, likely a unit display issue)
   - PyTorch: V_cell = 1.64×10⁻⁹ m³
   - The reciprocal volume error compounds

### Root Cause Hypothesis

The **40.51× factor** matches `λ² × constant`, suggesting:
- MOSFLM matrix files contain λ-scaled vectors (already multiplied by 1/λ)
- PyTorch `read_mosflm_matrix()` or `Crystal.compute_cell_tensors()` may be applying λ-scaling again
- Need to verify: does `read_mosflm_matrix(wavelength_A)` expect raw or pre-scaled vectors?

## Artifacts

| File | Description |
|------|-------------|
| `c_stdout.txt` | Full C trace output (291 lines) |
| `trace_py.log` | PyTorch trace output (37 lines) |
| `summary.md` | Automated comparison report |
| `compare_traces.py` | Comparison script (K3f3) |
| `trace_harness.py` | PyTorch trace generator (K3f2) |
| `run_c_trace.sh` | C trace capture script (K3f1) |
| `metadata.json` | Environment and configuration snapshot |

## Evidence Quality

- ✅ C trace: 291 lines, includes all base vectors + φ=0 scattering
- ✅ PyTorch trace: 37 lines, matching structure
- ✅ Comparison: Automated script with 5e-4 tolerance
- ✅ Reproducibility: Scripts capture exact commands and environment

## Next Actions (Phase K3f4)

Per plan task K3f4, document the root cause and remediation path:

1. **Investigate MOSFLM Matrix Handling**
   - Check `src/nanobrag_torch/io/mosflm.py:read_mosflm_matrix()`
   - Verify whether the function expects raw or λ-scaled input
   - Compare with C code (`nanoBragg.c:3135-3148`)

2. **Review Crystal Tensor Computation**
   - Check `src/nanobrag_torch/models/crystal.py:compute_cell_tensors()`
   - Look for MOSFLM branch that might be double-scaling
   - Validate against Core Rule #12 (misset rotation pipeline)

3. **Test Hypothesis**
   - Try removing λ-scaling from `read_mosflm_matrix()` output
   - Or adjust `compute_cell_tensors()` to skip scaling when MOSFLM vectors provided

## References

- Plan: `plans/active/cli-noise-pix0/plan.md` Phase K3f
- Input: `input.md` Do Now section (2025-10-06)
- Fix Plan: `docs/fix_plan.md` [CLI-FLAGS-003]
- C instrumentation: `golden_suite_generator/nanoBragg.c:2120-2310`
