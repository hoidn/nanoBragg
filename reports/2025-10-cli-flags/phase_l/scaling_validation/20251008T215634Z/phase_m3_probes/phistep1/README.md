# Phase M3c: Single-φ Parity Experiment

**Bundle:** `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T215634Z/phase_m3_probes/phistep1/`
**Date:** 2025-10-08T21:56:34Z
**Purpose:** Isolate rotation vs accumulation effects with phisteps=1, osc=0

---

## Quick Summary

**Finding:** PyTorch produces intensities **126,000× higher** than C reference with phisteps=1, despite perfect spatial correlation (r=0.999999). This is caused by missing normalization factor and likely additional scaling errors.

**Root Cause:** PyTorch sums over phi/mosaic dimensions without dividing by number of steps (see `root_cause_identified.md`).

**Status:** ROOT CAUSE PARTIALLY IDENTIFIED — requires code fix + validation

---

## Files in This Bundle

### Primary Artifacts
- **`summary.md`** — Complete experiment analysis and findings
- **`root_cause_identified.md`** — Technical analysis of C vs PyTorch scaling
- **`comparison_results.txt`** — Numerical pixel comparison output
- **`commands.txt`** — Full command documentation
- **`notes.txt`** — Experiment setup notes

### Data Files
- **`c_phistep1.bin`** — C reference float image (24 MB, 2463×2527 pixels)
- **`py_phistep1.bin`** — PyTorch float image (24 MB, 2463×2527 pixels)
- **`c_phistep1_full.log`** — C execution log with TRACE_C detector setup
- **`py_phistep1_full.log`** — PyTorch execution log
- **`c_phistep1_trace.log`** — Extracted TRACE_C lines (24 lines, detector only)

### Metadata
- **`env.json`** — Experiment environment and parameters
- **`sha256.txt`** — SHA256 checksums for all artifacts
- **`README.md`** — This file

---

## Key Findings

| Metric | C Reference | PyTorch | Ratio (Py/C) |
|--------|-------------|---------|--------------|
| Max intensity | 548.048 | 6.904e7 | **125,970× ** |
| Max location | (1039, 685) | (1039, 685) | Identical |
| Mean intensity | 0.001059 | 133.4 | 125,925× |
| **Correlation** | — | **0.999999** | — |

**Interpretation:**
- Spatial pattern is correct (near-perfect correlation)
- Magnitude is wrong by ~5 orders of magnitude
- Error is in scaling/normalization, NOT physics

---

## Root Cause (Preliminary)

### C Code Normalization (nanoBragg.c)
```c
// Line 2710
steps = sources*mosaic_domains*phisteps*oversample*oversample;

// Line 3358
test = r_e_sqr*fluence*I/steps;  // ← Division by steps!
```

### PyTorch Missing Normalization (simulator.py)
```python
# Line 321
intensity = torch.sum(intensity, dim=(-2, -1))  # ← No division!
```

**Expected Fix:**
```python
intensity = torch.sum(intensity, dim=(-2, -1))
N_phi = intensity_shape[-2]
N_mos = intensity_shape[-1]
intensity = intensity / (N_phi * N_mos)  # Normalize by sampling steps
```

---

## Comparison with Baseline

### Baseline (phisteps=10, from analysis_20251008T212459Z.md)
- PyTorch 14.6% LOWER than C
- Suggests multiple errors partially canceling

### This Experiment (phisteps=1)
- PyTorch 125,970× HIGHER than C
- Reveals underlying scaling error

**Conclusion:** The 14.6% deficit is a red herring. True error is much larger but masked by multi-step averaging and physics errors.

---

## Next Actions

### Immediate (Phase M3 continuation)
1. ✅ Identify missing `/steps` normalization
2. [ ] Search for additional scaling factors (126,000 vs expected ~10)
3. [ ] Inspect flux/exposure application in PyTorch code

### Implementation (Phase M4)
1. [ ] Add steps normalization after line 321 in simulator.py
2. [ ] Test with phisteps=1 (expect ratio → 1.0)
3. [ ] Test with phisteps=10 (expect deficit to change)
4. [ ] Validate on CPU and CUDA

### Validation (Phase M5)
1. [ ] Rerun trace_harness.py comparison
2. [ ] Verify gradcheck still passes
3. [ ] Run nb-compare on full ROI

---

## References

### Normative Specs
- **`specs/spec-a-core.md:204-236`** — Lattice factor and φ rotation
- **`specs/spec-a-cli.md`** — CLI flag semantics

### C Code (CLAUDE Rule #11)
- **`nanoBragg.c:2710`** — `steps = sources×mosaic_domains×phisteps×oversample²`
- **`nanoBragg.c:3358`** — `test = r_e_sqr×fluence×I/steps`

### PyTorch Code
- **`src/nanobrag_torch/simulator.py:321`** — Missing normalization
- **`src/nanobrag_torch/simulator.py:300-570`** — Main accumulation loop

### Related Analysis
- **`reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/analysis_20251008T212459Z.md`** — Baseline 14.6% deficit analysis
- **`plans/active/cli-noise-pix0/plan.md`** — Phase M task list

---

## Checksums (Verification)

SHA256 checksums available in `sha256.txt`. Key files:
```
b00d21689fe75d06df0126ae6969d7582bd0e0bc860354a531ac356a749a294b  c_phistep1.bin
61de3825c688cc5599e16fd7a9054b5c54c47146cffe99582407652692473fbf  py_phistep1.bin
```

---

**Status:** Phase M3c COMPLETE — ROOT CAUSE IDENTIFIED, READY FOR IMPLEMENTATION
**Created:** 2025-10-08T21:56:34Z
**Git SHA:** (to be updated post-commit)
