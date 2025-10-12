# DETECTOR-CONFIG-001 Phase B Design — Option A (COMPLETED & ARCHIVED)

**STAMP:** 20251012T015202Z
**Status:** ⚠️ REDUNDANT REQUEST — Work Already Complete
**Loop:** Ralph Attempt #64 (21st consecutive redundant loop)

---

## Executive Summary

**This design document was created per input.md Do Now directive, but [DETECTOR-CONFIG-001] Phase B/C/D work was already completed and archived on 2025-10-11.**

- **Status:** `done (archived)` per `docs/fix_plan.md:232`
- **Plan archived:** `plans/archive/detector-config_20251011_resolved.md`
- **C8 cluster:** ✅ RESOLVED (test `test_at_parallel_003::test_detector_offset_preservation` PASSES)
- **Prior design documents:** 20+ comprehensive designs created in Attempts #42-63
- **Most authoritative:** STAMP 20251011T214422Z (583 lines, 11 sections)

---

## Problem Statement

Per spec-a-core.md §72 and arch.md §ADR-03, the MOSFLM +0.5 pixel offset applies **only to auto-calculated beam center defaults**, not explicit user-provided values. The C code bug applied the offset unconditionally.

**Buggy behavior (fixed in Phase C):**
```python
# WRONG: Offset applied to ALL beam centers
beam_center_s_pixels = beam_center_s / pixel_size + 0.5  # MOSFLM
```

**Correct behavior (implemented):**
```python
# RIGHT: Offset only for auto-calculated defaults
if convention == MOSFLM and beam_center_source == "auto":
    offset = 0.5
else:
    offset = 0.0
beam_center_s_pixels = beam_center_s / pixel_size + offset
```

---

## Design Solution: Option A (Explicit Source Tracking)

### Configuration Layer
Added `BeamCenterSource` enum to `DetectorConfig`:
```python
from typing import Literal
BeamCenterSource = Literal["auto", "explicit"]

@dataclass
class DetectorConfig:
    beam_center_source: BeamCenterSource = "auto"  # default preserves backward compat
```

### CLI Detection Layer (`__main__.py`)
Created `determine_beam_center_source()` helper detecting 8 explicit flags:
- `-beam_center_s` / `-beam_center_f`
- `-Xbeam` / `-Ybeam`
- `-Xclose` / `-Yclose`
- `-ORGX` / `-ORGY`
- Header ingestion from `-img` / `-mask` (if beam center keys present)

### Detector Properties Layer (`detector.py`)
Modified `beam_center_*_pixels` properties to apply conditional offset:
```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    offset = torch.tensor(
        0.5 if (self.config.detector_convention == DetectorConvention.MOSFLM and
                self.config.beam_center_source == "auto") else 0.0,
        dtype=self.dtype, device=self.device
    )
    return self.config.beam_center_s / self.config.pixel_size_mm + offset
```

---

## Implementation Status

### Phase C (Implementation): ✅ COMPLETE
**STAMP:** 20251011T213351Z
**Tasks:** C1-C7 all executed
**Files modified:** `config.py`, `__main__.py`, `detector.py`, `test_beam_center_source.py` (5 new tests), `test_at_parallel_003.py`, `test_detector_config.py`

### Phase D (Validation): ✅ COMPLETE
**STAMP:** 20251011T223549Z
**Results:** 554 passed / 13 failed / 119 skipped (80.8% pass rate)
**C8 Status:** ✅ RESOLVED (`test_detector_offset_preservation` PASSES)
**Regressions:** 0 new failures

---

## Test Coverage

### New Tests (5 total in `test_beam_center_source.py`)
1. **MOSFLM auto**: Verifies +0.5 offset applied to default beam center
2. **MOSFLM explicit**: Verifies NO offset for explicit `-Xbeam`/`-Ybeam`
3. **Non-MOSFLM**: Verifies NO offset for XDS/ADXV conventions
4. **CLI detection**: Validates `determine_beam_center_source()` logic
5. **Edge cases**: Header ingestion, pix0 override interactions

### Existing Test Updates
- `test_at_parallel_003.py::test_detector_offset_preservation`: Updated to specify `beam_center_source="explicit"` for parity commands
- `test_detector_config.py`: Updated default beam center expectations to match corrected formula `(detsize + pixel)/2`

---

## Documentation Updates

1. **`docs/architecture/detector.md` §8.2/§9**: Added beam center source tracking semantics, CLI detection table, API usage warnings
2. **`docs/development/c_to_pytorch_config_map.md`**: Updated MOSFLM convention row with explicit source tracking requirements, added new section with CLI examples
3. **`docs/findings.md` DETECTOR-CONFIG-001**: Cross-referenced API-002 breaking change and CONVENTION-001 interaction

---

## Normative References

- **Spec:** `specs/spec-a-core.md:72` (MOSFLM beam center mapping formula)
- **Architecture:** `arch.md` §ADR-03 (offset policy)
- **Evidence:** `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md`
- **Prior designs:** `reports/2026-01-test-suite-triage/phase_m3/20251011T214422Z/mosflm_offset/design.md` (most comprehensive)

---

## Recommendation

**Input.md appears stale.** [DETECTOR-CONFIG-001] is complete. Supervisor should:

1. Acknowledge Phase B/C/D completion
2. Update input.md to redirect to active priority: **[TEST-SUITE-TRIAGE-001]** (Critical, in_progress, 13 failures remaining)
   - C2: Gradient infrastructure (10 tests, requires `NANOBRAGG_DISABLE_COMPILE=1`)
   - C15: Mixed units zero intensity (1 test, physics/unit bug, needs callchain)
   - C16: Detector orthogonality tolerance (1 test, extreme rotation precision)
3. Stop requesting Phase B design drafting (21 consecutive redundant loops)

---

## Artifacts

- **This document:** `reports/2026-01-test-suite-triage/phase_m3/20251012T015202Z/mosflm_offset/design.md`
- **Prior authoritative design:** `20251011T214422Z/mosflm_offset/design.md` (583 lines)
- **Implementation summary:** `20251011T193829Z/mosflm_offset/summary.md` (C8 evidence bundle)
- **Full-suite validation:** `20251011T223549Z/summary.md` (Phase D results)
- **Archived plan:** `plans/archive/detector-config_20251011_resolved.md`

---

**Conclusion:** No further action required on [DETECTOR-CONFIG-001]. Item is done (archived) with exit criteria satisfied. Redirect to [TEST-SUITE-TRIAGE-001] for next priority work.
