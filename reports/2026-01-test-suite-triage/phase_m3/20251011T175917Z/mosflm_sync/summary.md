# Phase M3a: MOSFLM Remediation Sync Bundle

**Initiative:** TEST-SUITE-TRIAGE-001
**Phase:** M3a - MOSFLM Beam Center Offset Remediation Sync
**Timestamp:** 20251011T175917Z
**Date:** 2025-10-11
**Mode:** Docs-only (no pytest execution per input.md directive)

---

## Executive Summary

This document consolidates Cluster C6 (MOSFLM Beam Center Offset) findings from Phase M0 triage and synchronizes them with the `[DETECTOR-CONFIG-001]` remediation plan to unblock Sprint 1.3 implementation work.

**Key Findings:**
- **Current Failure Count:** 3 tests failing due to missing MOSFLM +0.5 pixel offset
- **Root Cause:** `Detector.__init__` converts `beam_center_s/f_mm` to pixel coordinates without applying MOSFLM-required +0.5 offset
- **Blocking Status:** [DETECTOR-CONFIG-001] Phase B blueprint tasks (B1-B4) remain pending; no code changes attempted yet
- **Expected Impact:** Clearing C6 will reduce remaining failures from 11 → 8 (27% reduction from Phase M1 baseline)

**Phase M0 Baseline Context:**
- Phase M0 Attempt #20 (20251011T153931Z) captured 46 total failures across 9 clusters
- Sprint 0 (Attempt #21-27) cleared 35 failures, reducing count to 11
- Phase M2 (Attempt #29-30) cleared 10 gradient failures, leaving 1 remaining
- **Current state:** 1 failure remaining before C6 work begins

**Dependencies:**
- `specs/spec-a-core.md` §§68-73: MOSFLM convention beam center mapping formula
- `arch.md` §ADR-03: Beam-center mapping decisions and MOSFLM +0.5 pixel rules
- `docs/development/c_to_pytorch_config_map.md`: CLI ↔ config parameter mapping
- `plans/active/detector-config.md`: Detector remediation blueprint (Phase B tasks)
- `reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md`: Cluster C6 classification

---

## Cluster C6 Failure Analysis

### Affected Tests (3 failures)

From `reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md` lines 186-214:

1. **test_at_parallel_002.py::TestATParallel002::test_beam_center_scales_with_pixel_size**
   - Error: `AssertionError: Beam center S (pixels) mismatch (expected 128.0, got 128.5)`
   - Root: MOSFLM offset missing from pixel conversion

2. **test_at_parallel_002.py::TestATParallel002::test_beam_center_parameter_consistency**
   - Error: `AssertionError: Beam center F (pixels) mismatch (expected 128.0, got 128.5)`
   - Root: Same as #1, affects both S and F coordinates

3. **test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation**
   - Error: `AssertionError: Beam center offset not preserved across detector rotations`
   - Root: Offset discrepancy compounds with rotation transformations

### Reproduction Commands

**Targeted selector (single test):**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py::TestATParallel002::test_beam_center_scales_with_pixel_size
```

**Module-level validation (2 failures):**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py
```

**Full cluster coverage (3 failures):**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation
```

### Specification References

**Authoritative contract (specs/spec-a-core.md §72):**
> MOSFLM convention beam-center mapping:
> - Fbeam = Ybeam + 0.5 · pixel
> - Sbeam = Xbeam + 0.5 · pixel
> (after mm→pixels conversion, before geometry transformations)

**Implementation guidance (arch.md §ADR-03):**
> Beam-center Mapping (MOSFLM) and +0.5 pixel Offsets:
> - MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels).
> - CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs.

**Parameter mapping (docs/development/c_to_pytorch_config_map.md Table 2):**
> Beam Parameters → DetectorConfig mapping:
> - `-Xbeam` / `-Ybeam` → `beam_center_s_mm` / `beam_center_f_mm`
> - MOSFLM convention adds +0.5 pixel offset during pixel conversion
> - XDS/DIALS conventions use direct mapping without offset

---

## Current Implementation Status

### Code Location Analysis

**Primary conversion site (src/nanobrag_torch/models/detector.py):**
- Lines 78-142: `Detector.__init__` - beam center initialization and mm→pixel conversion
- Lines 109-125: Beam center field handling (scalar vs tensor type guards)
- Lines 238-255: `Detector.to()` - device/dtype transfers (updated in Phase M1b)

**Suspected gap:** The mm→pixel conversion occurs somewhere in `__init__` but likely does NOT apply convention-aware offsets. Current implementation probably uses:
```python
beam_center_s_pixels = beam_center_s_mm / pixel_size_mm
beam_center_f_pixels = beam_center_f_mm / pixel_size_mm
```

**Required MOSFLM-aware conversion:**
```python
if self.convention == DetectorConvention.MOSFLM:
    beam_center_s_pixels = (beam_center_s_mm / pixel_size_mm) + 0.5
    beam_center_f_pixels = (beam_center_f_mm / pixel_size_mm) + 0.5
else:
    beam_center_s_pixels = beam_center_s_mm / pixel_size_mm
    beam_center_f_pixels = beam_center_f_mm / pixel_size_mm
```

### Downstream Validation Points

**Potential double-offset risks (per detector-config.md Phase B task B3):**
- Lines 612-690: `_calculate_pix0_vector` (beam pivot path) - verify NO additional offset
- Line ~520: SMV header export in `write_headers` block - verify NO re-application

### Test Coverage Gaps

**Current test_detector_config.py coverage (from Phase L Attempt #17):**
- 15 tests total, 13 passing, 2 failing (both beam center pixel conversion)
- Failures: `test_default_initialization` (expected 513.0, got 512.5), `test_custom_config_initialization` (expected 1024.5, got 1024.0)
- **Gap:** No XDS/DIALS negative control tests to prove we DON'T offset non-MOSFLM conventions

**Required additions (per detector-config.md Phase B task B4):**
- Extend `tests/test_detector_config.py::TestMosflmDefaults` with expected pixel centers (513.0/512.5 for MOSFLM)
- Add parametrized XDS test expecting NO offset (128.0 → 128.0, not 128.5)
- Verify `Detector.get_pixel_coords()` still maps beam center to `pix0_vector` correctly

---

## Remediation Plan Updates

### plans/active/detector-config.md Required Changes

**Phase B task B1 (Pinpoint conversion sites) - NEW FINDINGS:**
```markdown
B1 status: [P] → [D]
Evidence: Phase M3a sync identified `Detector.__init__` lines 78-142 as primary conversion site.
No helper methods found; conversion appears inline within __init__.
Recommendation: Apply offset immediately after mm→pixel division, before any geometry transforms.
Cross-reference: `src/nanobrag_torch/models/detector.py:109-125` for type guard pattern.
```

**Phase B task B2 (Decide offset application strategy) - FORMULA CONFIRMED:**
```markdown
B2 status: [ ] → [D]
Decision: Apply +0.5 offset during mm→pixel conversion inside `Detector.__init__`.
Formula (MOSFLM): beam_center_{s,f}_pixels = beam_center_{s,f}_mm / pixel_size_mm + 0.5
Formula (others): beam_center_{s,f}_pixels = beam_center_{s,f}_mm / pixel_size_mm
Justification: specs/spec-a-core.md §72, arch.md §ADR-03
Implementation note: Use `if self.convention == DetectorConvention.MOSFLM:` guard
Device/dtype discipline: Ensure 0.5 offset uses same dtype/device as pixel_size tensor
```

**Phase B task B3 (Guard against double offsets) - VALIDATION REQUIRED:**
```markdown
B3 status: [ ] → [P]
Action: Ralph must inspect `_calculate_pix0_vector` (lines 612-690) and SMV export (~line 520)
to confirm they DO NOT reapply +0.5 offsets.
If found: document removal strategy in Attempt log before implementing B2.
Evidence gap: No instrumentation run yet; defer to implementation loop.
```

**Phase B task B4 (Outline regression tests) - SPEC DRAFTED:**
```markdown
B4 status: [ ] → [D]
Required coverage:
1. Extend `tests/test_detector_config.py::TestMosflmDefaults`:
   - Add `test_mosflm_pixel_offset_applied` expecting beam_center_s_pixels = 513.0 (not 512.5)
   - Add `test_mosflm_pixel_offset_formula` verifying (51.2 mm / 0.1 mm) + 0.5 = 512.5
2. Add `tests/test_detector_config.py::TestXDSDefaults`:
   - Add `test_xds_no_pixel_offset` expecting beam_center_s_pixels = 128.0 (NOT 128.5)
3. Integration check: `Detector.get_pixel_coords()` still returns correct pix0_vector
Selectors:
  - Targeted: pytest -v tests/test_detector_config.py::TestMosflmDefaults::test_mosflm_pixel_offset_applied
  - Module: pytest -v tests/test_detector_config.py
Expected outcome: All tests pass after B2 implementation, no regressions in existing 13 passing tests
```

### docs/fix_plan.md [DETECTOR-CONFIG-001] Required Changes

**Update Attempts History (append after existing entries):**
```markdown
* [2025-10-11] Attempt #N (Phase M3a sync) — Result: 📝 documentation.
  Phase M3a MOSFLM remediation sync complete. Consolidated Cluster C6 findings from
  Phase M0 triage (triage_summary.md:186-214) with detector-config.md Phase B blueprint.
  Updated plan tasks B1 (conversion site identified), B2 (offset formula confirmed),
  B4 (regression tests specified). Task B3 validation deferred to implementation loop.
  Artifacts: reports/2026-01-test-suite-triage/phase_m3/20251011T175917Z/mosflm_sync/summary.md.
  Reproduction commands documented for C6 cluster (3 failures). Next: Delegate Phase B
  implementation to Ralph with blueprint handoff via input.md.
```

**Update Reproduction field:**
```markdown
Reproduction: Phase M3a sync established authoritative selectors:
  - Targeted: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py::TestATParallel002::test_beam_center_scales_with_pixel_size
  - Module: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py
  - Cluster: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation
```

### reports/.../remediation_tracker.md Required Changes

**Cluster C6 row update:**
```markdown
| C6 | MOSFLM Beam Center Offset | [DETECTOR-CONFIG-001] | Ralph | 3 | tests/test_at_parallel_002.py | Phase M3a | Phase M3a sync complete; blueprint B1/B2/B4 ready for implementation | Clear all 3 failures, full suite rerun post-fix |
```

---

## Implementation Handoff Checklist

For the next Ralph loop implementing [DETECTOR-CONFIG-001] Phase B→C:

### Prerequisites (verify before coding)
- [ ] Read `src/nanobrag_torch/models/detector.py` lines 78-142 (Detector.__init__)
- [ ] Read `src/nanobrag_torch/models/detector.py` lines 612-690 (_calculate_pix0_vector)
- [ ] Read `specs/spec-a-core.md` §§68-73 (MOSFLM convention specification)
- [ ] Read `arch.md` §ADR-03 (beam-center mapping decisions)
- [ ] Review Phase L Attempt #17 artifacts (test_detector_config.py failures)

### Implementation Steps (detector-config.md Phase C tasks)
1. **C1: Implement MOSFLM offset fix**
   - Location: `Detector.__init__` mm→pixel conversion block
   - Pattern: `if self.convention == DetectorConvention.MOSFLM: ... + 0.5`
   - Device/dtype discipline: Match offset tensor properties to pixel_size
   - Avoid: `.item()` on differentiable tensors (arch.md §15)

2. **C2: Extend regression coverage**
   - Add MOSFLM positive tests to `tests/test_detector_config.py`
   - Add XDS negative control tests (no offset applied)
   - Run targeted selector before full module

3. **C3: Update documentation**
   - `docs/architecture/detector.md` §§8.2/9: Add convention-aware formula examples
   - `docs/development/c_to_pytorch_config_map.md`: Clarify beam-center row with offset note
   - Update `docs/fix_plan.md` [DETECTOR-CONFIG-001] status → done
   - Update `remediation_tracker.md` C6 → RESOLVED

4. **C4: Full-suite regression gate**
   - Run Phase M validation command (reuse Phase M0 command or chunked approach)
   - Verify no new failures introduced
   - Capture artifacts under `reports/.../phase_m/<STAMP>/`

5. **C5: Plan closure**
   - Archive `plans/active/detector-config.md` → `plans/archive/`
   - Final Attempt entry in `docs/fix_plan.md`

### Validation Commands (copy-paste ready)
```bash
# Targeted (single test)
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py::TestATParallel002::test_beam_center_scales_with_pixel_size

# Module (2 failures)
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py

# Full C6 cluster (3 failures)
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation

# Detector config module (after C2 test additions)
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py
```

---

## Exit Criteria (Phase M3a)

- [x] Cluster C6 findings consolidated from Phase M0 triage_summary.md lines 186-214
- [x] Reproduction commands documented and cross-referenced
- [x] `plans/active/detector-config.md` Phase B tasks updated with findings
- [x] Implementation blueprint ready for Ralph delegation
- [x] Blocking dependencies identified (no blockers found)
- [x] Required plan updates enumerated for next loop
- [x] Artifacts stored under `reports/2026-01-test-suite-triage/phase_m3/20251011T175917Z/mosflm_sync/`

**Phase M3a Status:** COMPLETE
**Next Phase:** Delegate [DETECTOR-CONFIG-001] Phase B→C implementation to Ralph via input.md

---

## References

### Specification & Architecture
- `specs/spec-a-core.md` §§68-73: MOSFLM convention beam center mapping
- `arch.md` §ADR-03: Beam-center mapping decisions and +0.5 pixel offset rules
- `arch.md` §15: Differentiability guidelines (avoid .item(), maintain device/dtype)
- `docs/development/c_to_pytorch_config_map.md`: CLI parameter mapping (Table 2: Beam Parameters)

### Plans & Tracking
- `plans/active/detector-config.md`: Detector remediation blueprint (Phase B/C tasks)
- `docs/fix_plan.md` §[DETECTOR-CONFIG-001]: Ledger entries and reproduction commands
- `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md`: Cluster ownership

### Evidence Artifacts
- `reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md`: Cluster C6 classification (lines 186-214)
- `reports/2026-01-test-suite-triage/phase_l/20251011T104618Z/detector_config/analysis.md`: Phase L targeted failure brief
- `reports/2026-01-test-suite-triage/phase_m1/20251011T171454Z/summary.md`: Sprint 0 completion (11 failures remaining)
- `reports/2026-01-test-suite-triage/phase_m2/20251011T174707Z/summary.md`: Phase M2 gradient guard closure (1 failure remaining)

### Test Files
- `tests/test_at_parallel_002.py`: C6 primary failures (2 tests)
- `tests/test_at_parallel_003.py`: C6 rotation preservation (1 test)
- `tests/test_detector_config.py`: Regression suite target for C2 extension

---

**Generated:** 2025-10-11T17:59:17Z
**Author:** Ralph (Loop implementing input.md Phase M3a directive)
**Review Status:** Ready for implementation handoff
