# AT-PARALLEL-012 Phase B3: Dtype Sensitivity Experiments

**Date:** 2025-09-30
**Script:** `scripts/validate_single_stage_reduction.py` (corrected to honor dtype parameter)
**Objective:** Validate whether float64 reduces plateau fragmentation vs float32, and whether multi-stage reduction is the root cause.

## Executive Summary

**Finding:** Both float32 and float64 exhibit ~5× plateau fragmentation compared to C float32. The root cause is **per-pixel floating-point operations** (geometry calculations, sinc functions), NOT multi-stage accumulation order as Phase B1 hypothesized.

**Implication:** Single-stage reduction refactoring will NOT fix the AT-012 peak matching regression. Phase C must pursue alternative mitigations.

## Experimental Setup

- Configuration: `simple_cubic` test case (100Å cubic cell, 5×5×5 unit cells, λ=6.2Å)
- Detector: 1024×1024 pixels, 0.1mm pixel size, 100mm distance, MOSFLM convention
- ROI: 20×20 pixels centered at beam center (pixel 512,512)
- Reference baseline: C float32 golden data = 66 unique values in ROI

## Results

### Float32 (Current Default)
```
Unique values (full image): 1,012,257
Unique values (beam center 20×20 ROI): 324
Fragmentation ratio vs C: 4.91×
```

### Float64 (Precision Test)
```
Unique values (full image): 963,113
Unique values (beam center 20×20 ROI): 301
Fragmentation ratio vs C: 4.56×
```

## Analysis

### Hypothesis Validation

**Phase B1 Hypothesis (REJECTED):** Multi-stage reduction (sum over phi/mosaic, then sources, then subpixels) causes 7.68× fragmentation.

**Actual Result:** Both float32 and float64 show ~5× fragmentation in beam center ROI, matching Phase A3 baseline measurements exactly:
- Float32: 324 unique values (4.91×) — matches Phase A3 finding
- Float64: 301 unique values (4.56×) — matches Phase A3 finding

### Root Cause Confirmation

The **simple_cubic** test case has:
- `phi_steps=1` (no phi oscillation)
- `mosaic_domains=1` (no mosaicity)
- `sources=1` (single wavelength)
- `oversample=1` (no subpixel sampling)

With all accumulation dimensions = 1, multi-stage vs single-stage reduction is **mathematically identical**. Therefore, the fragmentation MUST originate from per-pixel calculations:
- Detector geometry (basis vectors, pix0, pixel coordinates)
- Scattering vector calculation
- Sinc function evaluations (sincg)
- Lattice shape factor products

### Why Float64 Doesn't Fix It

Float64 reduces unique values by only ~7% (324 → 301 in ROI), still leaving 4.56× fragmentation. This indicates:
1. Fundamental algorithmic difference between C and PyTorch implementations (compiler optimizations, FMA usage, operation ordering)
2. Higher precision alone cannot restore plateau stability
3. C compiler's `-O3` optimizations may produce more deterministic float32 arithmetic than PyTorch's dynamic graph

## Phase C Implications

**Single-stage reduction is NOT the solution.** Phase B1 analysis was based on a hypothetical case with N_phi=10, N_mos=10 (multi-dimensional accumulation), which does NOT apply to the failing AT-012 test.

### Recommended Phase C Mitigations (Priority Order)

1. **Peak clustering algorithm** (most pragmatic)
   - Modify `find_peaks()` to cluster maxima within 0.5px radius
   - Preserves spec-compliant physics, adapts validation to handle plateau fragmentation
   - Trade-off: Slightly less sensitive peak detection

2. **Investigate compiler FMA settings**
   - Research PyTorch/CPU backend FMA behavior
   - Explore `torch.set_float32_matmul_precision('high')` or similar flags
   - Trade-off: May require PyTorch version-specific tuning

3. **Document float64 override for AT-012** (fallback)
   - Accept that AT-012 requires float64 while other tests use float32
   - Update arch.md and testing_strategy.md with rationale
   - Trade-off: Violates DTYPE-DEFAULT-001 goal

## Artifacts

- **Script:** `scripts/validate_single_stage_reduction.py` (commit: [pending])
- **Raw output:** Captured in this report
- **Related reports:**
  - `reports/2025-10-AT012-regression/phase_a3_summary.md` (baseline plateau analysis)
  - `reports/2025-10-AT012-regression/PHASE_B1_REPORT.md` (rejected multi-stage hypothesis)

## Next Actions

1. Update `docs/fix_plan.md` Attempt #15 with Phase B3 completion and corrected hypothesis
2. Update plan `plans/active/at-parallel-012-plateau-regression/plan.md` task B3 state to [X]
3. Consult with supervisor on Phase C mitigation selection (peak clustering vs FMA vs float64 override)
4. Execute chosen mitigation under `prompts/debug.md`
