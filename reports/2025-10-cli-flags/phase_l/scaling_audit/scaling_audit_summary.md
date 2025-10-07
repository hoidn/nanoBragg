# Phase L2b Scaling Audit Summary

**Date:** 2025-10-17
**Engineer:** Ralph (Loop i=64, evidence-only mode)
**Plan Reference:** `plans/active/cli-noise-pix0/plan.md` Phase L2b
**Task:** Compare C vs PyTorch scaling chain for pixel (685, 1039)

---

## Executive Summary

✅ **Phase L2b COMPLETE:** PyTorch scaling trace successfully captured via CLI `-trace_pixel` flag.

**Key Finding:** Three major scaling factor divergences identified:
1. **Steps:** PyTorch=160 vs C=10 (16× factor from auto-oversample 4²)
2. **Fluence:** PyTorch=1.26e+29 vs C=1e+24 (~100,000× error)
3. **Polarization:** PyTorch=1.0 vs C=0.9146 (9.3% error)

**First Divergence:** Fluence calculation (5 orders of magnitude)

---

## Comparison Table

| Factor | C Value | PyTorch Value | Δ (%) | Match? |
|--------|---------|---------------|-------|--------|
| `steps` | 10 | 160 | 1500% | ✗ |
| `r_e_sqr` (m²) | 7.94079248e-30 | 7.94079273e-30 | 0.0003% | ✓ |
| `fluence` (ph/m²) | 1.0e+24 | 1.26e+29 | ~100,000× | ✗ |
| `omega_pixel` (sr) | 4.20413e-07 | 4.18050e-07 | 0.56% | ✓ |
| `polar` | 0.91463969 | 1.0 | 9.3% | ✗ |
| `capture_fraction` | 1.0 | 1.0 | 0% | ✓ |
| `oversample_thick` | 0 | 0 | 0% | ✓ |
| `oversample_polar` | 0 | 0 | 0% | ✓ |
| `oversample_omega` | 0 | 0 | 0% | ✓ |

---

## Detailed Findings

### 1. Steps Normalization (16× factor)

**C Implementation:**
```
steps = 10  (sources=1 × mosaic=1 × phisteps=10 × oversample=1²)
```

**PyTorch Implementation:**
```
steps = 160  (sources=1 × mosaic=1 × phisteps=10 × oversample=4²)
auto-selected 4-fold oversampling
```

**Root Cause:** PyTorch CLI auto-selects 4× oversample when none specified; C defaults to 1×.

**Implication:** PyTorch intensities are 16× dimmer due to excessive normalization.

---

### 2. Fluence Calculation (~100,000× error)

**C Implementation:**
```c
fluence = 1e24  // explicitly set via command line or default
```

**PyTorch Implementation:**
```python
# BeamConfig calculates fluence from flux/exposure/beamsize
fluence = flux * exposure / (beamsize^2)
        = 1e18 * 1.0 / (1.0mm² → m²)
        = 1e18 / 1e-6
        = 1e24 expected, but got 1.26e+29
```

**Root Cause:** Likely beam_size unit conversion error (mm vs meters) or area calculation.

**Calculation Check:**
```
Expected: flux × exposure / (π × (beamsize/2)²)
        = 1e18 × 1.0 / (π × (0.0005)²)
        = 1e18 / 7.85e-7
        = 1.27e+24 ✓ (if using radius)
        
Observed: 1.26e+29 = 1e5× higher
        → suggests beamsize was treated as 1e-5 meters instead of 1mm
```

---

### 3. Polarization Factor (9.3% error)

**C Implementation:**
```c
polar = 0.91463969894451  // Kahn formula with cos²(2θ) term
```

**PyTorch Implementation:**
```python
polar = 1.0  // appears to be nopolar behavior despite K=0 in config
```

**Root Cause:** PyTorch may not be applying polarization when `polarization_factor=0.0`.

**Expected Behavior:** Even with K=0, the Kahn formula should still compute the geometric term:
```
polar = 0.5 * (1 + cos²(2θ) - K×cos(2ψ)×sin²(2θ))
      = 0.5 * (1 + cos²(2θ))  when K=0
```

For `cos(2θ) = -0.130070`:
```
polar = 0.5 * (1 + (-0.130070)²)
      = 0.5 * (1 + 0.01692)
      = 0.50846  ≠ 1.0 ✗
```

**Issue:** PyTorch is bypassing polarization calculation entirely.

---

## Artifacts

- C trace: `c_trace_scaling.log` (12,852 bytes, 172 lines)
- PyTorch trace: `trace_py_scaling.log` (40 lines, TRACE_PY only)
- Full PyTorch output: `trace_py_cli_full.log` (64 lines with context)
- Environment: `trace_py_env.json`
- Config: `config_snapshot_final.json`
- Notes: `notes.md` (updated with execution summary)
- pytest collection: `pytest_collect_final.log` (4 tests collected)

---

## Next Actions (Phase L2c)

1. Build `compare_scaling_traces.py` script to automate line-by-line diff
2. Extract C trace values programmatically for comparison
3. Generate `compare_scaling_traces.json` with parsed deltas
4. Update `docs/fix_plan.md` CLI-FLAGS-003 Attempt history with:
   - First Divergence: Fluence (~100,000× error)
   - Metrics: steps=160 vs 10, fluence=1.26e+29 vs 1e+24, polar=1.0 vs 0.9146
   - Artifacts: All files under `reports/2025-10-cli-flags/phase_l/scaling_audit/`
   - Hypotheses: beam_size unit error, auto-oversample divergence, polarization bypass
   - Next Actions: Phase L3 normalization fixes

---

## Exit Criteria Status

✅ Phase L2b exit criteria MET:
- [x] C and PyTorch traces captured under `reports/2025-10-cli-flags/phase_l/scaling_audit/`
- [x] Comparison summary identifies first mismatched term (fluence, ~100,000× delta)
- [x] docs/fix_plan.md Attempt log ready for update (see artifacts section above)

**Ready to proceed to Phase L2c (comparison script) and Phase L3 (fixes).**

