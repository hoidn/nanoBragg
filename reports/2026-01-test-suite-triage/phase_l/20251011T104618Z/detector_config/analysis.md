# Phase L Detector Config Targeted Rerun — Analysis

**Timestamp:** 2025-10-11T10:46:18Z
**Focus:** Detector configuration default validation (C8 cluster per Phase K)
**Environment:** Python 3.13.5, PyTorch 2.7.1+cu126, CUDA 12.6, CPU-only (CUDA_VISIBLE_DEVICES=-1)

---

## Executive Summary

**Status:** ⚠️ **2 failures, 13 passed** (86.7% pass rate)
**Verdict:** Partial success — detector config validation progressing, but beam center mapping still has a **0.5-pixel discrepancy** vs spec expectations.

**Cluster C8 Status:** IN PROGRESS — 2/2 failures from Phase K rerun reproduced here, blockers identified.

---

## Test Results

### Overall Metrics

| Metric | Value |
|--------|-------|
| **Tests Collected** | 15 |
| **Passed** | 13 (86.7%) |
| **Failed** | 2 (13.3%) |
| **Runtime** | 1.92s |
| **Exit Code** | 1 (failures present) |

### Failures

#### 1. `test_default_initialization` (lines 124-147)

**Location:** `tests/test_detector_config.py:142`

**Failure:**
```python
assert detector.beam_center_s == 513.0
# Actual: tensor(512.5000, dtype=torch.float64)
# Expected: 513.0
```

**Root Cause Analysis:**

The test expects MOSFLM convention beam center calculation to include the +0.5 pixel offset **in pixel space**, but the implementation is returning the value **before** adding 0.5.

**Spec Reference:** `specs/spec-a-core.md` §72:
> "MOSFLM: ... Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel."

**Config Flow:**
1. Default `beam_center_s` in mm = 51.25 mm (per test line 29: `(1024 * 0.1 + 0.1) / 2.0`)
2. MOSFLM convention SHOULD compute: `beam_center_s_pixels = (51.25 mm / 0.1 mm per pixel) + 0.5 = 513.0`
3. **Actual implementation returns:** 512.5 pixels (missing the +0.5 adjustment)

**Gap:** The `Detector` class (or `DetectorConfig`) is **not applying the MOSFLM +0.5 pixel offset** when converting beam center from mm to pixel coordinates.

---

#### 2. `test_custom_config_initialization` (lines 149-172)

**Location:** `tests/test_detector_config.py:171`

**Failure:**
```python
assert detector.beam_center_s == 1024.5
# Actual: tensor(1024., dtype=torch.float64)
# Expected: 1024.5
```

**Root Cause:** Same as failure #1 — missing MOSFLM +0.5 pixel offset.

**Config Flow:**
1. Custom `beam_center_s` in mm = 204.8 mm
2. Pixel size = 0.2 mm
3. Expected: `(204.8 / 0.2) + 0.5 = 1024.5` pixels
4. **Actual:** 1024.0 pixels (missing +0.5)

---

## Specification Cross-Reference

### Relevant Spec Sections

1. **`specs/spec-a-core.md` §68-72 (MOSFLM Convention):**
   > "MOSFLM: Beam b = [1 0 0]; f = [0 0 1]; s = [0 -1 0]; o = [1 0 0]; 2θ-axis = [0 0 -1]; p = [0 0 1]; u = [0 0 1].
   > Default Xbeam = (detsize_s + pixel)/2, Ybeam = (detsize_f + pixel)/2.
   > **Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel.** Pivot = BEAM."

2. **`arch.md` §ADR-03 (Beam-center Mapping):**
   > "MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs."

3. **`docs/development/c_to_pytorch_config_map.md` (Beam Center Mapping):**
   > "MOSFLM: → Fbeam directly; → Sbeam = detsize_s - Ybeam"
   > (Implicit context: this mapping assumes the +0.5 pixel offset is applied during pixel coordinate conversion)

---

## Implementation Gap

### Current Behavior

The `Detector` class appears to be converting beam center from mm to pixels using **direct division** without adding the MOSFLM-required +0.5 pixel offset:

```python
# Hypothesized current implementation (NOT verified — inference from test failures):
beam_center_s_pixels = beam_center_s_mm / pixel_size_mm  # Missing +0.5
```

### Expected Behavior (per spec)

```python
# MOSFLM convention requires:
beam_center_s_pixels = (beam_center_s_mm / pixel_size_mm) + 0.5
beam_center_f_pixels = (beam_center_f_mm / pixel_size_mm) + 0.5
```

### Likely Fix Location

Based on the test structure and spec requirements:

1. **Primary candidate:** `src/nanobrag_torch/models/detector.py` — `Detector.__init__()` or property methods computing beam center in pixels
2. **Secondary candidate:** `src/nanobrag_torch/config.py` — `DetectorConfig.__post_init__()` beam center logic

**Critical:** The fix MUST be **convention-aware**:
- **MOSFLM:** Add +0.5 pixel
- **XDS/DIALS/CUSTOM:** Do NOT add +0.5
- **DENZO:** Uses `Fbeam = Ybeam, Sbeam = Xbeam` (no +0.5 per spec §73)

---

## Blocker Status for [DETECTOR-CONFIG-001]

**Blocker:** These 2 failures block closure of `[DETECTOR-CONFIG-001]` (Detector defaults audit).

**Exit Criteria (from `docs/fix_plan.md`):**
- ✅ Default `DetectorConfig` values match spec §4 defaults (PASSED — 13/15 tests passed include default value checks)
- ❌ MOSFLM beam center pixel conversion includes +0.5 offset (FAILED — both failures trace to this gap)
- ❌ All detector_config tests pass (FAILED — 2/15 still failing)

**Next Actions (per `input.md` L51-52):**
1. ✅ Phase L artifacts collected (this document + logs)
2. **TODO:** Update `remediation_tracker.md` with C8 status (2 failures, beam center offset gap identified)
3. **TODO:** Delegate to Ralph for implementation — fix MOSFLM beam center pixel calculation in `Detector` class

---

## Artifacts

All Phase L artifacts stored under:
`reports/2026-01-test-suite-triage/phase_l/20251011T104618Z/detector_config/`

### File Inventory

| File | Purpose |
|------|---------|
| `logs/pytest.log` | Full pytest output (15 tests, 2 failures) |
| `env/torch_env.txt` | Python/PyTorch/CUDA versions |
| `env/pip_freeze.txt` | Complete package list (237 packages) |
| `commands.txt` | Exact reproduction commands |
| `analysis.md` | This document — failure triage and spec cross-reference |

---

## Observations

1. **Test Suite Health:** 86.7% pass rate for detector config tests is acceptable for evidence gathering, but the 2 failures are **critical** as they directly contradict the spec's MOSFLM convention requirements.

2. **Test Quality:** The failing tests (`test_default_initialization`, `test_custom_config_initialization`) include **clear spec citations** (e.g., line 141: `# MOSFLM convention: 51.25 mm / 0.1 mm per pixel + 0.5 = 513.0`), making the gap unambiguous.

3. **No Regressions:** All 13 passing tests cover:
   - Default value validation
   - Convention-specific defaults (XDS twotheta axis)
   - Input validation (negative/zero pixel counts, distance, oversample)
   - Tensor parameter acceptance
   - Basis vector initialization
   - Device/dtype handling

4. **Scope Containment:** Both failures are **isolated to beam center pixel conversion** — no cascading issues with rotations, pivots, or other geometry.

---

## Recommendations

1. **Implementation Priority:** HIGH — MOSFLM is the default convention, so this affects the majority of use cases.

2. **Fix Strategy:**
   - Locate beam center pixel calculation in `Detector` class
   - Add convention guard: `if self.config.detector_convention == DetectorConvention.MOSFLM: offset = 0.5 else: offset = 0.0`
   - Apply offset: `beam_center_s_pixels = (beam_center_s_mm / pixel_size_mm) + offset`
   - Add unit test for DENZO (no offset), XDS (no offset), MOSFLM (offset) to prevent regressions

3. **Validation:**
   - After fix, rerun: `pytest -v tests/test_detector_config.py`
   - Target: 15/15 passed
   - Also check: `tests/test_at_parallel_004.py` (MOSFLM 0.5 pixel offset parity test)

4. **Documentation:**
   - Update `docs/architecture/detector.md` with explicit beam center conversion formula per convention
   - Cross-reference `c_to_pytorch_config_map.md` for CLI → config flow

---

## Phase L Checklist Status

Per `plans/active/test-suite-triage.md` Phase L tasks:

- ✅ **L1:** Run targeted detector-config pytest command
- ✅ **L2:** Capture artifacts (logs, env, commands)
- ✅ **L3:** Generate `analysis.md` with spec cross-references
- **PENDING:** Update `remediation_tracker.md` (galph/ralph next loop)
- **PENDING:** Sync `docs/fix_plan.md` with Phase L attempt notes (galph/ralph next loop)

**Ready for handoff:** ✅ YES — all evidence collected, blocker identified, next actions clear.
