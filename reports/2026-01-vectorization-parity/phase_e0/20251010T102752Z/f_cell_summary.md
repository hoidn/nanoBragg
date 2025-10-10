# Phase E5 PyTorch Tap 4 F_cell Summary

**Timestamp (UTC):** 2025-10-10T10:28:27Z
**Artifact Bundle:** `reports/2026-01-vectorization-parity/phase_e0/20251010T102752Z/`
**Initiative:** `[VECTOR-PARITY-001]` Phase E5 PyTorch Tap 4 capture
**Mode:** Evidence-only (Parity)

## Executive Summary

Captured F_cell lookup statistics for edge pixel (0,0) and centre pixel (2048,2048) with oversample=2 (4 subpixels per pixel). Both pixels exhibit **zero out-of-bounds HKL lookups** and **100% default_F usage** (mean F_cell=100.0 for all 4 subpixel lookups). This confirms that for the baseline test configuration (λ=0.5Å, cell=100×100×100Å, default_F=100), PyTorch is correctly applying the default structure factor when no HKL file is provided, regardless of pixel position.

**Key Finding:** Edge and centre pixels show identical default_F behavior (total_lookups=4, out_of_bounds=0, zero_f=0, mean=100.0). The difference lies in Miller index ranges:
- **Edge (0,0):** h∈[-8,-8], k∈[39,39], l∈[-39,-39] (far from reciprocal origin)
- **Centre (2048,2048):** h∈[0,0], k∈[0,0], l∈[0,0] (at reciprocal origin, direct beam transmission region)

**Implication for Parity Regression:** Since out_of_bounds_count=0 for both edge and centre, Tap 4 **does NOT explain** the corr=0.721 full-frame divergence. The edge/background correlation collapse observed in Phase E1 cannot be attributed to differential default_F usage between edge and centre pixels.

## Methodology

### Configuration
- **Detector:** 4096×4096 pixels, pixel=0.05mm, distance=500mm
- **Beam:** λ=0.5Å, MOSFLM convention
- **Crystal:** cell=100×100×100Å, 90°×90°×90°, N=5×5×5, default_F=100
- **Sampling:** oversample=2 (4 subpixels: [-0.5, +0.5] offset grid per axis)
- **Device/Dtype:** CPU, torch.float64 (deterministic trace mode)

### Execution
```bash
# Edge pixel (0,0)
KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py \
  --pixel 0 0 --tag edge --oversample 2 --taps f_cell --json \
  --out-dir reports/2026-01-vectorization-parity/phase_e0/20251010T102752Z/py_taps

# Centre pixel (2048,2048)
KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py \
  --pixel 2048 2048 --tag centre --oversample 2 --taps f_cell --json \
  --out-dir reports/2026-01-vectorization-parity/phase_e0/20251010T102752Z/py_taps
```

**Trace Script Version:** Enhanced per Attempt #25 (`docs/fix_plan.md:48`) with `--oversample`, `--taps`, and `--json` support.

## Results

### Edge Pixel (0, 0)

**Source JSON:** `py_taps/pixel_0_0_f_cell_stats.json`

| Metric | Value |
|--------|-------|
| Total HKL lookups | 4 |
| Out-of-bounds count | 0 |
| Zero F count | 0 |
| Mean F_cell | 100.000000 |
| HKL bounds (h) | [-8, -8] |
| HKL bounds (k) | [39, 39] |
| HKL bounds (l) | [-39, -39] |

**Interpretation:** All 4 subpixels queried the same rounded Miller indices h=-8, k=39, l=-39. This reflection is far from the reciprocal origin (|G|≈√(8²+39²+39²)≈56.23 Å⁻¹) and lies in the high-angle diffraction region. Since no HKL file was provided, F_cell defaults to 100.0 for all lookups.

**Final Intensity:** 3.018e-04 (dim pixel, high scattering angle with weak lattice factor F_latt=1.88)

### Centre Pixel (2048, 2048)

**Source JSON:** `py_taps/pixel_2048_2048_f_cell_stats.json`

| Metric | Value |
|--------|-------|
| Total HKL lookups | 4 |
| Out-of-bounds count | 0 |
| Zero F count | 0 |
| Mean F_cell | 100.000000 |
| HKL bounds (h) | [0, 0] |
| HKL bounds (k) | [0, 0] |
| HKL bounds (l) | [0, 0] |

**Interpretation:** All 4 subpixels queried h=0, k=0, l=0 (reciprocal origin, direct beam transmission). This is the (000) reflection with maximum lattice factor F_latt=124.02 (near the ideal N³=125 for a 5³ cell). F_cell again defaults to 100.0 for all lookups.

**Final Intensity:** 1.538 (bright pixel, direct beam region with strong lattice factor)

### Edge vs Centre Comparison

| Metric | Edge (0,0) | Centre (2048,2048) | Delta |
|--------|------------|---------------------|-------|
| Total lookups | 4 | 4 | 0 |
| Out-of-bounds | 0 | 0 | 0 |
| Zero F count | 0 | 0 | 0 |
| Mean F_cell | 100.0 | 100.0 | 0.0 |
| HKL span (h) | 0 (single value -8) | 0 (single value 0) | — |
| HKL span (k) | 0 (single value 39) | 0 (single value 0) | — |
| HKL span (l) | 0 (single value -39) | 0 (single value 0) | — |
| Final I | 3.018e-04 | 1.538 | 5096× ratio |

**Key Observation:** Despite the 5096× intensity difference, **both pixels use default_F identically** (100% default, 0% out-of-bounds). The intensity variation arises purely from **lattice factor differences** (F_latt=1.88 for edge vs 124.02 for centre) and **solid angle geometry** (ω=8.86e-09 sr for edge vs 1.00e-08 sr for centre).

## Analysis & Implications

### Hypothesis Validation

**Hypothesis (from `plans/active/vectorization-parity-regression.md:80-82`):** Edge/background pixels may have higher out-of-bounds HKL lookups, triggering more default_F usage and causing systematic bias relative to centre pixels with in-bounds lookups.

**Verdict:** ❌ **REFUTED**

**Evidence:** Both edge and centre show out_of_bounds_count=0 with 100% default_F usage. There is **no differential default_F behavior** between edge and centre pixels for this test case.

### Physical Interpretation

For the baseline configuration (no HKL file, default_F=100):
1. **All pixels** use default_F regardless of scattering angle or Miller index magnitude.
2. The edge pixel's dim intensity (3e-04) results from weak lattice interference at high angles (h=-8,k=39,l=-39), **not** from missing structure factors.
3. The centre pixel's bright intensity (1.54) reflects strong forward scattering at the (000) reflection, again using the **same default_F=100**.

### Ruling Out F_cell as Parity Culprit

Since out-of-bounds lookups are uniformly zero across edge and centre:
- F_cell bias **cannot explain** the corr=0.721 full-frame regression (Phase E1, Attempt #21).
- The correlation collapse must originate from a factor that varies systematically with pixel position **other than** structure factor lookup logic.

**Remaining Suspects (per `omega_comparison.md`):**
1. **Tap 5 (Pre-normalization intensity):** Check whether `I_before_scaling` shows edge/centre anomalies independent of F_cell.
2. **Tap 6 (Water background):** Verify uniform vs position-dependent background contributions (F_bg²·r_e²·fluence·...).
3. **ROI masking/boundary effects:** Confirm full-frame pixel iteration order matches C-code (slow-major) and edges are not silently skipped.

## Artifacts

**Bundle Root:** `reports/2026-01-vectorization-parity/phase_e0/20251010T102752Z/`

### PyTorch Taps (`py_taps/`)
- `pixel_0_0_f_cell_stats.json` — Tap 4 metrics for edge pixel
- `pixel_0_0_metadata.json` — Configuration snapshot (oversample, device, dtype)
- `pixel_0_0.log` — Full TRACE_PY log (72 tap points)
- `pixel_2048_2048_f_cell_stats.json` — Tap 4 metrics for centre pixel
- `pixel_2048_2048_metadata.json` — Configuration snapshot
- `pixel_2048_2048.log` — Full TRACE_PY log
- `commands.txt` — Exact CLI invocations for reproducibility

### Environment (`env/`)
- `trace_env.txt` — Complete environment variables at runtime
- `torch_env.json` — PyTorch version, CUDA availability, Python version

## Next Actions (per `input.md:35`)

Per supervisor guidance, **proceed to Phase E6 C Tap 4 instrumentation** once PyTorch metrics are archived (complete as of this summary).

**Phase E6 Deliverables:**
1. Instrument `golden_suite_generator/nanoBragg.c` to emit Tap 4 metrics for pixels (0,0) and (2048,2048) with oversample=2.
2. Capture C tap logs to `reports/2026-01-vectorization-parity/phase_e0/20251010T102752Z/c_taps/`.
3. Author `c_taps/f_cell_comparison.md` comparing C vs PyTorch Tap 4 results.
4. Update `[VECTOR-PARITY-001]` Attempts History with Phase E6 outcomes.

**Alternative Path (if Tap 4 C parity confirms PyTorch behavior):** Skip C instrumentation and proceed directly to Tap 5 (pre-norm intensity) or Tap 6 (water background) for PyTorch-only exploratory diagnostics.

## Reproducibility

**Command Prefix (all):** `KMP_DUPLICATE_LIB_OK=TRUE`

**STAMP Reuse:** All commands used `STAMP=20251010T102752Z` to collocate artifacts.

**Git Context:** (Add git SHA + branch once committed)

## Audit Trail

- **Input.md Do Now (lines 7-8):** Executed both edge and centre commands with matching STAMP.
- **Tap Points Schema (`tap_points.md`):** Matched Tap 4 schema (total_lookups, HKL bounds, default_F hits).
- **Pitfalls Avoided (input.md:21-27):**
  - ✅ Same STAMP for both pixels
  - ✅ Tensors on requested device (CPU, no spurious `.cpu()` calls)
  - ✅ Artifacts untracked (`reports/` not in git staging)
  - ✅ TRACE output ordering preserved (legacy 72-line format + tap summary)
  - ✅ JSON files confirmed before summary draft
  - ✅ Protected Assets untouched (no edits to `docs/index.md`, golden data)

**Elapsed Time:** ~45 seconds (edge + centre execution)

---

**Prepared by:** ralph (evidence-only loop)
**Review Status:** Awaiting supervisor sign-off for Phase E6 or alternate path selection
**Canonical Reference:** `plans/active/vectorization-parity-regression.md:80-82` (Phase E5 checklist)
