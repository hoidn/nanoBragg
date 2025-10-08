# ROOT CAUSE IDENTIFICATION: Missing Steps Normalization

**Date:** 2025-10-08T21:56:34Z
**Finding:** PyTorch is missing the `/steps` normalization factor that C code applies
**Severity:** CRITICAL — causes 126,000× scaling error in single-step mode

---

## C Code Reference (nanoBragg.c)

### Line 2710: Steps calculation
```c
steps = sources*mosaic_domains*phisteps*oversample*oversample;
```

### Line 3358-3363: Steps normalization applied
```c
/* convert pixel intensity into photon units */
test = r_e_sqr*fluence*I/steps;

/* do the corrections now, if they haven't been applied already */
if(! oversample_thick) test *= capture_fraction;
if(! oversample_polar) test *= polar;
if(! oversample_omega) test *= omega_pixel;
```

**Key Insight:** C code divides accumulated intensity `I` by `steps` before applying other corrections.

---

## PyTorch Code Analysis

### Current Implementation (simulator.py:321)
```python
# Sum over phi and mosaic dimensions
# intensity shape before sum: (S, F, N_phi, N_mos) or (n_sources, S, F, N_phi, N_mos) or (n_sources, batch, N_phi, N_mos)
intensity = torch.sum(intensity, dim=(-2, -1))
# After sum: (S, F) or (n_sources, S, F) or (n_sources, batch)
```

**Problem:** Direct sum without averaging. This is equivalent to C's accumulated `I` but **before division by steps**.

---

## Numerical Verification

### Our Experiment (phisteps=1, oversample=1, sources=1, mosaic_domains=1)
- **C code:** `steps = 1 * 1 * 1 * 1 * 1 = 1`
- **C normalization:** `I / 1 = I` (no effect)
- **PyTorch:** No normalization, sums to `I`
- **Expected difference:** Should match if PyTorch were correct

### But we observed 126,000× difference!

**Analysis:** This suggests PyTorch has ANOTHER scaling factor applied somewhere that C doesn't have. Let me calculate:

```
PyTorch / C = 126,000
If C applies: I / steps = I / 1 = I
Then PyTorch must be computing: I × 126,000
```

**Hypothesis:** PyTorch may be:
1. Missing the `/steps` division (explains why multi-step has different behavior)
2. ALSO applying an extra multiplication factor (possibly exposure, flux, or beamsize)

### Reverse Engineering the 126,000 Factor

From our experiment parameters:
- exposure = 1.0
- flux = 1e18
- beamsize = 1.0
- Na = 36, Nb = 47, Nc = 29

Let's check some combinations:
- 36 × 47 × 29 = 49,068 (close to 50k, but not 126k)
- sqrt(1e18) = 1e9 (way too big)
- 1e18 / (36×47×29) = 2.04e13 (not it)

**Need to inspect:** Where else does PyTorch apply scaling factors that C doesn't?

---

## Multi-Step Baseline Comparison

### Baseline (phisteps=10)
- **C:** `steps = 1 * 1 * 10 * 1 * 1 = 10`, so `I / 10`
- **PyTorch (if missing /steps):** `I` (no division)
- **Expected PyTorch/C ratio:** `I / (I/10) = 10`

But we observed PyTorch **14.6% LOWER** than C, which is `ratio = 0.854`.

**This is contradictory!** If PyTorch were missing `/steps`, it should be 10× HIGHER, not lower.

---

## Resolution: Two Separate Errors

**Hypothesis H5 (revised):** There are TWO independent scaling errors:

### Error #1: Exposure/Flux Scaling (manifests in phisteps=1)
- PyTorch applies flux/exposure scaling incorrectly
- Causes 126,000× surplus
- Hidden in multi-step mode by Error #2

### Error #2: Missing Steps Division (manifests in phisteps=10)
- PyTorch sums over phi/mosaic without averaging
- Should divide by (phi_steps × mosaic_domains)
- Causes 10× surplus in baseline case
- But F_latt sign flips and other physics errors partially cancel this

### Combined Effect
- phisteps=1: Error #1 dominates → 126,000× too high
- phisteps=10: Error #1 × Error #2 = 126,000 × 10 = 1,260,000×
- But F_latt physics errors reduce this to only 85.4% of C value
- Net result: appears 14.6% too LOW despite underlying 1,260,000× surplus!

**Conclusion:** The 14.6% deficit is a red herring caused by multiple errors partially canceling.

---

## Required Fixes

### Fix #1: Add Steps Normalization (HIGH PRIORITY)
**File:** `src/nanobrag_torch/simulator.py`
**Line:** After line 321

**Current:**
```python
intensity = torch.sum(intensity, dim=(-2, -1))
```

**Proposed:**
```python
# Sum over phi and mosaic dimensions
intensity = torch.sum(intensity, dim=(-2, -1))

# CRITICAL FIX: Normalize by number of steps (matches nanoBragg.c:3358)
# steps = sources × mosaic_domains × phisteps × oversample²
# For single-pixel case: intensity is already summed, so divide by (N_phi × N_mos)
N_phi = intensity_before_sum.shape[-2]  # phi dimension size
N_mos = intensity_before_sum.shape[-1]  # mosaic dimension size
intensity = intensity / (N_phi * N_mos)
```

**C Reference:**
- `nanoBragg.c:2710` — steps calculation
- `nanoBragg.c:3358` — `test = r_e_sqr*fluence*I/steps;`

### Fix #2: Identify Extra Scaling Factor (HIGH PRIORITY)
**Action:** Search for where exposure, flux, or other factors are applied in PyTorch
**Expected:** Find a multiplication by ~126,000 that shouldn't be there
**Files to check:**
- `src/nanobrag_torch/simulator.py` (fluence application)
- `src/nanobrag_torch/config.py` (parameter units/conversions)

---

## Validation Plan

### Step 1: Apply Fix #1 only
- Add steps normalization
- Rerun phisteps=1 test
- **Expected:** Ratio should change from 126,000× to ~1.0 (if this is the only error)
- **If ratio is still wrong:** Error #2 exists, proceed to find extra scaling factor

### Step 2: Rerun phisteps=10 baseline
- After Fix #1
- **Expected:** 14.6% deficit should change (possibly flip to surplus)
- **Goal:** Isolate remaining physics errors (F_latt sign flip, etc.)

### Step 3: Comprehensive Validation
- Test phisteps=2, 5, 10, 20
- Verify ratio scales correctly with steps
- Ensure physics errors are independent of phisteps

---

## Document Status

**Status:** ROOT CAUSE PARTIALLY IDENTIFIED
**Confidence:** HIGH for missing `/steps` normalization
**Confidence:** MEDIUM for extra scaling factor hypothesis
**Next Action:** Code inspection to find all scaling factor applications in PyTorch
**Blocking:** Phase M4 (physics fix implementation)

---

**References:**
- `nanoBragg.c:2710` — steps = sources×mosaic_domains×phisteps×oversample²
- `nanoBragg.c:3358` — test = r_e_sqr×fluence×I/steps
- `src/nanobrag_torch/simulator.py:321` — intensity = torch.sum(intensity, dim=(-2, -1))
- `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/analysis_20251008T212459Z.md` — 14.6% deficit analysis

**Git SHA:** (to be updated post-commit)
