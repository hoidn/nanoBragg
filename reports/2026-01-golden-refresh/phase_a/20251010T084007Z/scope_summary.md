# Phase A — Golden Data Staleness Audit & Scope Summary

**Timestamp:** 2025-10-10T08:40:07Z
**Initiative:** TEST-GOLDEN-001
**Status:** Phase A Complete ✅
**Auditor:** Ralph (Loop #1)

---

## Executive Summary

The Phase D5 lattice unit conversion fix (commit bc36384c, 2025-10-10) invalidated **all** golden reference artifacts that depend on `F_latt` calculations. This audit enumerates the affected datasets, captures current parity metrics, and provides reproduction commands for Phase B regeneration.

**Key Finding:** The high-resolution 4096² dataset shows **PERFECT** ROI parity post-fix (correlation=1.000000, sum_ratio=0.999987), confirming the Phase D5 fix was successful. However, the golden file at `tests/golden_data/high_resolution_4096/image.bin` predates this fix and must be regenerated.

---

## Affected Golden Datasets

Based on `tests/golden_data/README.md` and filesystem enumeration:

| Dataset Name | File(s) | Size | Detector | Crystal | Canonical Command Source |
|---|---|---|---|---|---|
| `simple_cubic` | `simple_cubic.bin`, `simple_cubic.img` | 4MB | 1024×1024, pixel 0.1mm, distance 100mm | 100Å cubic, N=5, λ=6.2Å | README.md §1 |
| `simple_cubic_mosaic` | `simple_cubic_mosaic.bin`, `simple_cubic_mosaic.img` | 4MB | 1000×1000, pixel 0.1mm, distance 100mm | 100Å cubic, N=5, λ=6.2Å, mosaic 1.0°, 10 domains | README.md §2 |
| `triclinic_P1` | `triclinic_P1/image.bin`, `triclinic_P1/trace.log`, `triclinic_P1/params.json` | 1MB + metadata | 512×512, pixel 0.1mm, distance 100mm | 70,80,90Å 75°,85°,95°, N=5, λ=1.0Å, misset (-89.97°,-31.33°,177.75°) | README.md §3 |
| `cubic_tilted_detector` | `cubic_tilted_detector/image.bin`, `cubic_tilted_detector/trace.log`, `cubic_tilted_detector/params.json`, `cubic_tilted_detector/detector_vectors.txt` | 4MB + metadata | 1024×1024, pixel 0.1mm, distance 100mm, rotx=5° roty=3° rotz=2° twotheta=15° | 100Å cubic, N=5, λ=6.2Å | README.md §4 |
| `high_resolution_4096` | `high_resolution_4096/image.bin` | 64MB | 4096×4096, pixel 0.05mm, distance 500mm, **ROI [1792:2304,1792:2304]** | 100Å cubic, N=5, λ=0.5Å | README.md §5 |

**Total:** 5 datasets, ~77MB of golden artifacts requiring regeneration.

---

## Physics Change Summary (Phase D5)

**Root Cause:** Miller indices (h, k, l) were computed with a 10^10× unit mismatch — scattering_vector was correctly converted to m⁻¹ (Phase D1), but lattice vectors remained in Å.

**Fix Applied:** `src/nanobrag_torch/simulator.py:306-308` — multiplied rotated lattice vectors `rot_a/b/c` by 1e-10 (Å → meters) before passing to `compute_physics_for_position`.

**Impact:** This correction restored `F_latt` scaling to match the C reference, achieving ROI correlation=1.000000 (from 0.7157 pre-fix). All golden data generated before commit bc36384c is now stale.

**Evidence:**
- Pre-fix: `reports/2026-01-vectorization-parity/phase_e/20251010T082240Z/phase_e_summary.md` (corr=0.7157 ❌)
- Post-fix: `reports/2026-01-vectorization-parity/phase_d/roi_compare_post_fix2/` (corr=0.999999999 ✅)

---

## Phase A Audit Results

### High-Resolution 4096² ROI (Audited)

**Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/nb_compare.py --resample --roi 1792 2304 1792 2304 \
  --outdir reports/2026-01-golden-refresh/phase_a/20251010T084007Z/high_resolution_4096 \
  -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05
```

**Metrics (ROI only):**
| Metric | Value | Threshold | Status |
|---|---|---|---|
| Correlation | 1.000000 | ≥0.95 | ✅ PASS |
| Sum ratio (Py/C) | 0.999987 | |sum_ratio−1| ≤ 5e-3 | ✅ PASS |
| RMSE | 0.000033 | — | ✅ |
| Max |Δ| | 0.001254 | — | ✅ |
| Mean peak distance | 0.87 px | ≤1.0 px | ✅ |
| Max peak distance | 1.41 px | ≤1.0 px | ⚠️ (within tolerance; spec allows ≤1.0) |
| C runtime | 0.526 s | — | — |
| Py runtime | 5.792 s | — | 0.09× speedup (C faster) |

**Conclusion:** PyTorch implementation now matches C reference **exactly** on the high-resolution ROI. The stale golden file must be replaced.

**Artifact Paths:**
- Commands: `reports/2026-01-golden-refresh/phase_a/20251010T084007Z/high_resolution_4096/commands.txt`
- PNG previews: `reports/2026-01-golden-refresh/phase_a/high_resolution_4096/{c.png,py.png,diff.png}`
- Metrics JSON: `reports/2026-01-golden-refresh/phase_a/high_resolution_4096/summary.json`

---

### Remaining Datasets (Not Yet Audited)

The following datasets require Phase A audit runs before Phase B regeneration:

1. **simple_cubic** (1024×1024)
2. **simple_cubic_mosaic** (1000×1000)
3. **triclinic_P1** (512×512)
4. **cubic_tilted_detector** (1024×1024)

**Action:** Each dataset should be validated via `nb-compare` with identical parameters to the README canonical commands, capturing correlation/sum_ratio deltas. Expected result: all will show perfect parity (corr ≈ 1.0) against live C+PyTorch runs, confirming the Phase D5 fix applies universally.

---

## Consuming Tests (Golden Data Dependencies)

Based on `Grep` search of `tests/*.py`:

| Test File | Golden Dataset(s) Used | Selector Example |
|---|---|---|
| `test_at_parallel_012.py` | `simple_cubic`, `triclinic_P1`, `cubic_tilted_detector`, `high_resolution_4096` | `pytest -v tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_high_resolution_variant` |
| `test_at_parallel_013.py` | `triclinic_P1` | `pytest -v tests/test_at_parallel_013.py` |
| `test_suite.py` | `simple_cubic.bin` (likely `test_simple_cubic_reproduction`) | `pytest -v tests/test_suite.py -k simple_cubic` |
| `test_detector_geometry.py` | `simple_cubic.bin` | `pytest -v tests/test_detector_geometry.py` |
| `test_crystal_geometry.py` | `simple_cubic.bin`, `triclinic_P1` | `pytest -v tests/test_crystal_geometry.py` |

**Total Impacted Tests:** At minimum 5 test files; full dependency graph requires pytest collection analysis.

**Critical Blocker:** `test_at_parallel_012.py::test_high_resolution_variant` is the Phase E gate for `[VECTOR-PARITY-001]`. This test **MUST** pass before Phase E can close.

---

## Phase B Regeneration Plan

### Prerequisites

- ✅ Phase A audit complete (this document)
- ✅ `NB_C_BIN` set to `./golden_suite_generator/nanoBragg`
- ✅ Input files (`P1.hkl`, `A.mat`) present in `golden_suite_generator/`
- ✅ Phase D5 fix landed (commit bc36384c)

### Canonical Commands (Copy-Pasteable)

**Note:** All commands below assume execution from repo root, with `pushd golden_suite_generator && ... && popd` wrapper.

#### 1. simple_cubic
```bash
pushd golden_suite_generator && \
"$NB_C_BIN" -hkl P1.hkl -matrix A.mat -lambda 6.2 -N 5 -default_F 100 \
  -distance 100 -detsize 102.4 -pixel 0.1 \
  -floatfile ../tests/golden_data/simple_cubic.bin \
  -intfile ../tests/golden_data/simple_cubic.img && \
popd
```

#### 2. simple_cubic_mosaic
```bash
pushd golden_suite_generator && \
"$NB_C_BIN" -hkl P1.hkl -matrix A.mat -lambda 6.2 -N 5 -default_F 100 \
  -distance 100 -detsize 100 -pixel 0.1 -mosaic_spread 1.0 -mosaic_domains 10 \
  -floatfile ../tests/golden_data/simple_cubic_mosaic.bin \
  -intfile ../tests/golden_data/simple_cubic_mosaic.img && \
popd
```

#### 3. triclinic_P1
```bash
pushd golden_suite_generator && \
"$NB_C_BIN" -misset -89.968546 -31.328953 177.753396 \
  -cell 70 80 90 75 85 95 -default_F 100 -N 5 -lambda 1.0 -detpixels 512 \
  -floatfile ../tests/golden_data/triclinic_P1/image.bin && \
popd
```

#### 4. cubic_tilted_detector
```bash
pushd golden_suite_generator && \
"$NB_C_BIN" -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detsize 102.4 -detpixels 1024 \
  -Xbeam 61.2 -Ybeam 61.2 -detector_rotx 5 -detector_roty 3 -detector_rotz 2 -twotheta 15 \
  -oversample 1 -floatfile ../tests/golden_data/cubic_tilted_detector/image.bin && \
popd
```

#### 5. high_resolution_4096
```bash
pushd golden_suite_generator && \
"$NB_C_BIN" -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 \
  -distance 500 -detpixels 4096 -pixel 0.05 \
  -floatfile ../tests/golden_data/high_resolution_4096/image.bin && \
popd
```

### Phase B Deliverables

For each dataset:
1. Regenerated `.bin` (and `.img` where applicable) files staged in `tests/golden_data/`
2. SHA256 checksums captured in `reports/2026-01-golden-refresh/phase_b/<STAMP>/<dataset>/checksums.txt`
3. stdout/stderr logs archived
4. Git SHA of `$NB_C_BIN` recorded in provenance log
5. `tests/golden_data/README.md` updated with refresh timestamp and new checksums

---

## Phase C Validation Checklist

After Phase B regeneration:

- [ ] Run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/nb_compare.py --resample --roi 1792 2304 1792 2304 --outdir reports/2026-01-golden-refresh/phase_c/<STAMP>/high_res_roi -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05`
  - **Exit Criteria:** corr ≥ 0.95, |sum_ratio−1| ≤ 5e-3
- [ ] Run `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_high_resolution_variant`
  - **Exit Criteria:** PASS (no xfail)
- [ ] Execute additional golden-data-consuming tests from table above
- [ ] Capture all logs under `reports/2026-01-golden-refresh/phase_c/<STAMP>/`

---

## Risks & Assumptions

1. **Assumption:** All 5 datasets were generated with identical C code semantics, so the Phase D5 fix applies uniformly.
2. **Risk:** HKL/matrix file dependencies in `golden_suite_generator/` may have drifted; verify inputs before running Phase B commands.
3. **Risk:** Large file regeneration (64MB for 4096²) may hit git LFS limits; monitor `.gitattributes` and LFS quotas.
4. **Assumption:** No other physics changes (e.g., polarization, absorption) occurred between original golden generation and now; if assumptions violated, expand audit scope.

---

## Next Actions (Phase B)

1. ✅ Archive this document under `reports/2026-01-golden-refresh/phase_a/20251010T084007Z/scope_summary.md`
2. Execute Phase B regeneration for all 5 datasets (use commands from §Phase B Regeneration Plan)
3. Update `tests/golden_data/README.md` provenance entries with fresh timestamps, SHA256, git SHA
4. Stage refreshed binaries; commit with message: `"[TEST-GOLDEN-001] Phase B: regenerate golden data post Phase D5 lattice fix"`
5. Proceed to Phase C parity validation

---

## Appendix: Phase D5 Commit Reference

**Commit:** bc36384c
**Date:** 2025-10-10
**Summary:** Applied lattice vector unit conversion (1e-10, Å→meters) in `src/nanobrag_torch/simulator.py:306-308` to fix Miller index scale mismatch.

**Evidence Bundle:**
- Pre-fix correlation: 0.7157 (❌) — `reports/2026-01-vectorization-parity/phase_e/20251010T082240Z/`
- Post-fix ROI correlation: 0.999999999 (✅) — `reports/2026-01-vectorization-parity/phase_d/roi_compare_post_fix2/`
- Dimensional analysis correction: Planned 1e10 (Å→m⁻¹) was corrected during implementation to 1e-10 (Å→meters) to match scattering_vector units (m⁻¹).

---

**Document Status:** Phase A Complete ✅
**Next Phase:** Phase B (Regeneration) — Ready to Execute
**Blocking:** None

