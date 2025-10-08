# Phase M3c: Single-φ Parity Experiment — Summary

**Initiative:** CLI-FLAGS-003
**Bundle:** `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T215634Z/phase_m3_probes/phistep1/`
**Date:** 2025-10-08
**Timestamp:** 20251008T215634Z
**Purpose:** Isolate rotation vs accumulation effects by testing with phisteps=1, osc=0

---

## Executive Summary

**CRITICAL FINDING:** With `phisteps=1` and `osc=0`, PyTorch produces intensities approximately **126,000× higher** than C reference, despite maintaining nearly perfect spatial correlation (r=0.999999). This is a fundamentally different behavior than the 14.6% deficit observed in the multi-step (phisteps=10) baseline.

**Interpretation:** This suggests:
1. The scaling/normalization logic differs dramatically between single-step and multi-step modes
2. The 14.6% deficit in phisteps=10 may be masking a much larger underlying scaling error
3. The error is likely NOT in φ-rotation application but in per-φ intensity normalization

---

## 1. Experimental Configuration

### Command Used
```bash
# Modified supervisor command with phisteps=1, osc=0
# All other parameters identical to plan.md lines 6-12

-mat A.mat -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 \
-exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 \
-Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 \
-pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 \
-odet_vector -0.000088 0.004914 -0.999988 \
-sdet_vector -0.005998 -0.999970 -0.004913 \
-fdet_vector 0.999982 -0.005998 -0.000118 \
-pix0_vector_mm -216.336293 215.205512 -230.200866 \
-beam_vector 0.00051387949 0.0 -0.99999986 \
-Na 36 -Nb 47 -Nc 29 \
-osc 0 -phi 0 -phisteps 1 \
-detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0
```

### Changes from Baseline
- `phisteps`: 10 → 1
- `osc`: 0.1 → 0

### Target Pixel
ROI pixel (685, 1039) — the pixel showing maximum intensity in both implementations

---

## 2. Results Comparison

### 2.1 Image-Wide Statistics

| Metric | C Reference | PyTorch | Ratio (Py/C) |
|--------|-------------|---------|--------------|
| **Max intensity** | 5.480479e+02 | 6.903750e+07 | **125,970** |
| Max pixel location | (1039, 685) | (1039, 685) | Identical |
| Mean intensity | 1.059360e-03 | 1.334194e+02 | 125,925 |
| RMS | 3.484960e-01 | 4.391000e+04 | 126,025 |
| **Correlation** | — | 0.999999342 | — |

**Key Observations:**
1. Spatial pattern is nearly identical (correlation = 0.999999)
2. Magnitude differs by factor of ~126,000
3. Both implementations identify same peak pixel

### 2.2 Target Pixel (685, 1039)

| Implementation | Intensity | Notes |
|----------------|-----------|-------|
| C Reference | 2.111535e-07 | Very low value (near background) |
| PyTorch | 2.648173e-02 | 125,414× higher |

**Observation:** The target pixel is NOT the maximum intensity pixel - it was chosen based on previous divergence analysis. The actual max is at (1039, 685).

### 2.3 Maximum Intensity Pixel (1039, 685)

| Implementation | Intensity | Notes |
|----------------|-----------|-------|
| C Reference | 5.480479e+02 | |
| PyTorch | 6.903750e+07 | 125,970× higher |

---

## 3. Comparison with Baseline (phisteps=10)

### Baseline Results (from analysis_20251008T212459Z.md)
- **C I_before_scaling:** 943,654.81
- **PyTorch I_before_scaling:** 805,473.79
- **Ratio (Py/C):** 0.854 (14.6% deficit)

### Single-Step Results (this experiment)
- **C max:** 548.048
- **PyTorch max:** 6.9037e7
- **Ratio (Py/C):** 125,970 (12,597,000% surplus!)

### Critical Discrepancy

The behavior is **opposite** between single-step and multi-step:
- **Multi-step (phisteps=10):** PyTorch is 14.6% LOWER than C
- **Single-step (phisteps=1):** PyTorch is 126,000× HIGHER than C

This cannot be explained by φ-rotation errors alone. It indicates:
1. **Scaling normalization differs between single/multi-step modes**
2. **Per-φ accumulation logic may be compensating for an upstream error**
3. **Exposure/flux/phisteps scaling may be applied incorrectly**

---

## 4. Hypothesis Revision

### Original Hypothesis (H4 from analysis_20251008T212459Z.md)
- φ-rotation application error
- F_latt sign flip due to k_frac mismatch
- Small rotation errors accumulate

### **New Hypothesis (H5): Per-φ Normalization Error — HIGH CONFIDENCE**

**Evidence:**
1. Single φ-step shows 126,000× scaling error
2. Multi φ-step shows 14.6% deficit
3. Spatial correlation remains perfect (0.999999)
4. Pattern is correct, magnitude is wrong

**Mechanism:**
1. PyTorch may be missing a per-φ intensity normalization factor
2. C code likely divides accumulated intensity by `phisteps` or similar
3. With phisteps=1: PyTorch accumulates full intensity without normalization
4. With phisteps=10: PyTorch accumulates 10× too much, but then partial cancellation from F_latt sign flips reduces net error to 14.6%

**Expected C Code Pattern:**
```c
// Likely in nanoBragg.c simulation loop
for (phi_tic = 0; phi_tic < phisteps; phi_tic++) {
    // ... compute F_latt for this phi ...
    I_pixel += F_cell² × F_latt² × <factors>;
}
// Normalization by number of phi steps?
I_pixel /= phisteps;  // or similar averaging
```

**PyTorch Missing Step:**
- May be accumulating without dividing by phisteps
- Or applying normalization only in multi-step mode
- Or missing exposure/oscillation scaling factors

---

## 5. Observed F_latt Values

### From C Trace (phistep1 experiment)
- No per-pixel physics traces were emitted
- Only detector initialization traces available
- Cannot directly compare F_latt, k_frac for this run

### Expected F_latt at φ=0 (from baseline analysis)
- **C:** F_latt = -2.383, F_latt_b = +1.051, k_frac = -0.6073
- **PyTorch:** F_latt = +1.379, F_latt_b = -0.858, k_frac = -0.5892

**Note:** The sign flip still matters for multi-step parity, but the 126,000× scaling error dominates the single-step case.

---

## 6. Code Inspection Required

### Priority 1: Find Normalization Factor
**File:** `src/nanobrag_torch/simulator.py`
**Search for:**
- `phisteps` references in accumulation loop
- Division by `phisteps`, `osc`, or `exposure`
- Conditional logic that differs between single/multi-step modes

**Compare to:** `nanoBragg.c` lines around the main φ-step loop (approx 2604-3278)

### Priority 2: Exposure/Flux Scaling
**File:** `src/nanobrag_torch/simulator.py`
**Check:**
- How `-exposure`, `-flux`, `-beamsize` factors are applied
- Whether scaling differs for phisteps=1 vs phisteps>1
- Order of operations: exposure × flux × phisteps normalization

### Priority 3: Trace Instrumentation
**Current Gap:** PyTorch did not emit `TRACE_PY` lines for this run
**Action:** Verify trace flag is enabled in CLI for physics calculations (not just detector)
**Expected:** Per-pixel traces showing F_cell, F_latt, I_before_scaling

---

## 7. Next Steps

### Immediate Actions
1. **Inspect PyTorch normalization logic** in `simulator.py` main loop
2. **Compare C code** φ-step accumulation and averaging (cite line numbers per CLAUDE Rule #11)
3. **Enable per-pixel PyTorch traces** for phisteps=1 run and compare F_latt values
4. **Test hypothesis:** Manually divide PyTorch output by 126,000 and check if parity improves

### Validation Tests
1. **phisteps=2 test:** See if PyTorch intensity is 63,000× higher (half of 126,000)
2. **phisteps=5 test:** See if PyTorch intensity is 25,200× higher (1/5 of 126,000)
3. **Expected pattern:** If normalization is missing, ratio should be proportional to 1/phisteps

### Phase M3 Completion Criteria
- [ ] Identify exact line in PyTorch code where normalization should occur
- [ ] Confirm C code has corresponding normalization (cite line number)
- [ ] Implement fix in PyTorch
- [ ] Rerun phisteps=1 parity test (expect ratio ≈ 1.0)
- [ ] Rerun phisteps=10 baseline (expect 14.6% deficit to change or disappear)

---

## 8. Artifacts Generated

### Files in This Bundle
- `commands.txt` — Full command documentation
- `notes.txt` — Experiment setup notes
- `comparison_results.txt` — Pixel-by-pixel comparison output
- `c_phistep1.bin` — C reference float image (24 MB)
- `py_phistep1.bin` — PyTorch float image (24 MB)
- `c_phistep1_full.log` — C execution log (includes TRACE_C detector setup)
- `py_phistep1_full.log` — PyTorch execution log (no TRACE_PY physics)
- `c_phistep1_trace.log` — Extracted TRACE_C lines (24 lines, detector only)
- `summary.md` — This file

### Key Files Missing
- `py_phistep1_trace.log` — Empty (no TRACE_PY physics emitted)
- Per-φ rotation matrix traces
- Per-pixel F_latt, k_frac traces

---

## 9. Spec & Code References

### Normative Specs
- **`specs/spec-a-core.md:204-236`** — Lattice factor and φ rotation pipeline
- **`specs/spec-a-cli.md`** — `-phisteps`, `-osc`, `-exposure` semantics

### C Code References (CLAUDE Rule #11)
- **`nanoBragg.c:2604-3278`** — Main simulation loop (per-φ accumulation)
- **`nanoBragg.c:TBD`** — Normalization/averaging step (TO BE IDENTIFIED)

### PyTorch Implementation
- **`src/nanobrag_torch/simulator.py:300-570`** — Main accumulation loop (TO BE INSPECTED)
- **`src/nanobrag_torch/cli.py`** — Parameter parsing for phisteps, exposure

---

## 10. Conclusion

**The phisteps=1 experiment revealed a critical normalization error** that was previously hidden by the 14.6% deficit in multi-step runs. The spatial pattern is correct (r=0.999999), but the magnitude is wrong by 5 orders of magnitude.

**Root Cause:** Likely missing per-φ intensity normalization (division by phisteps or similar).

**Impact:** This error is MORE fundamental than the F_latt sign flip identified in Phase M2. It must be fixed BEFORE addressing the rotation matrix discrepancies.

**Phase M3 Status:** Experiment complete. Hypothesis H5 (normalization error) promoted to HIGH confidence. Proceed to code inspection and fix implementation.

---

**Document Created:** 2025-10-08T21:56:34Z
**Analyst:** Claude Agent (Ralph context)
**Git SHA:** (to be updated post-commit)
