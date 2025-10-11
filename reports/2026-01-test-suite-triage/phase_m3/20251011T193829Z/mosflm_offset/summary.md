# C8 Cluster: MOSFLM Beam Center Offset Misapplication

**STAMP:** 20251011T193829Z
**Phase:** M3 (post-Phase M2 validation)
**Cluster ID:** C8
**Category:** MOSFLM Beam Center Offset
**Status:** → Phase M3 (implementation bug, needs fix)

---

## Executive Summary

**Classification:** Implementation Bug (specification violation)

The Detector class incorrectly applies the MOSFLM convention +0.5 pixel offset to ALL beam center coordinates, including explicit user-provided values. Per spec-a-core.md §72 and arch.md §ADR-03, the +0.5 pixel offset should ONLY be applied to auto-calculated beam centers when using MOSFLM convention, NOT to explicit user inputs.

**Impact:** When users provide explicit beam center coordinates (e.g., `--beam_center_s 512.5 --beam_center_f 512.5`), the detector applies an additional unintended +0.5 pixel shift, resulting in incorrect geometry.

**Priority:** P2.1 (High — spec violation affecting user-provided coordinates)

---

## Failure Summary

**Total Failures:** 1

### Affected Test

**Test:** `test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation`

**Purpose:** Validates that explicit beam center coordinates are preserved exactly when provided by user (no implicit convention-based adjustments).

**Failure Mode:** Test provides `beam_center_s=512.5`, expects detector to use exactly 512.5 pixels, but receives 513.0 pixels (512.5 + 0.5 offset).

---

## Reproduction Commands

### Minimal Targeted Reproduction
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation
```

**Expected:** FAILED (beam center shifted by +0.5 pixels)

### Module-Level Validation
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_003.py
```

**Expected:** 1 failure in offset preservation test; other tests in module may pass.

### Cluster-Wide Validation
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_003.py tests/test_detector_config.py tests/test_beam_center_offset.py
```

**Expected:** Comprehensive validation across all MOSFLM beam center handling.

---

## Technical Details

### Root Cause Analysis

**Location:** `src/nanobrag_torch/models/detector.py`

**Suspect Code Paths:**
1. **Beam center property** (lines ~78-142): Converts mm → pixels and applies convention offsets
2. **Convention setup** (lines ~612-690): Initializes MOSFLM-specific parameters including offsets
3. **pix0 calculation** (lines ~520): Uses beam center properties to compute detector origin

**Current Behavior (INCORRECT):**
```python
# Simplified pseudocode
if convention == MOSFLM:
    beam_center_pixels = (beam_center_mm / pixel_size_mm) + 0.5  # ALWAYS applied
```

**Correct Behavior:**
```python
# Should distinguish explicit vs auto-calculated
if convention == MOSFLM and beam_center_source == "auto":
    beam_center_pixels = (beam_center_mm / pixel_size_mm) + 0.5
else:
    beam_center_pixels = beam_center_mm / pixel_size_mm  # No offset for explicit
```

### Spec Reference

**spec-a-core.md §72 (MOSFLM Convention):**
> "MOSFLM applies a +0.5 pixel offset to beam center calculations when deriving from detector geometry defaults. Explicit user-provided beam centers must not be adjusted."

**arch.md §ADR-03 (Beam-center Mapping):**
> "MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs."

**Key Insight:** The offset is a convention-specific DEFAULT behavior, not a mandatory transformation for all coordinates.

---

## Implementation Fix Strategy

### Option A: Track Beam Center Source (RECOMMENDED)

**Approach:** Add `beam_center_source` attribute to DetectorConfig to distinguish explicit vs auto-calculated values.

**Changes Required:**
1. **config.py (DetectorConfig):**
   ```python
   @dataclass
   class DetectorConfig:
       beam_center_s_mm: float
       beam_center_f_mm: float
       beam_center_source: str = "auto"  # or "explicit"
       # ... other fields
   ```

2. **__main__.py (CLI parsing):**
   ```python
   if args.beam_center_s is not None:
       config.beam_center_source = "explicit"
   elif args.Xbeam is not None or args.Ybeam is not None:
       config.beam_center_source = "explicit"
   else:
       config.beam_center_source = "auto"
   ```

3. **detector.py (beam center property):**
   ```python
   @property
   def beam_center_s_pixels(self) -> torch.Tensor:
       base = self.config.beam_center_s_mm / self.config.pixel_size_mm
       if self.config.detector_convention == DetectorConvention.MOSFLM and \
          self.config.beam_center_source == "auto":
           return base + 0.5
       return base
   ```

**Benefits:**
- Explicit semantic distinction in config
- Easy to audit CLI → config → detector pipeline
- Minimal code changes (3 files)

**Risks:**
- Requires updating all DetectorConfig instantiations (tests, examples)
- Must ensure "explicit" flag propagates correctly through all code paths

### Option B: Check for Default Values

**Approach:** Compare beam center values against computed defaults; if they match defaults, apply offset.

**Changes Required:**
```python
def _is_auto_calculated(self) -> bool:
    default_s = (self.config.detsize_s_mm - self.config.pixel_size_mm) / 2
    default_f = (self.config.detsize_f_mm + self.config.pixel_size_mm) / 2
    return (abs(self.config.beam_center_s_mm - default_s) < 1e-6 and
            abs(self.config.beam_center_f_mm - default_f) < 1e-6)

@property
def beam_center_s_pixels(self) -> torch.Tensor:
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm
    if self.config.detector_convention == DetectorConvention.MOSFLM and \
       self._is_auto_calculated():
        return base + 0.5
    return base
```

**Benefits:**
- No config changes required
- Backwards compatible

**Risks:**
- Fragile heuristic (what if user coincidentally provides default value?)
- Harder to reason about behavior
- Couples beam center logic to detector size logic

**Recommendation:** Option A (explicit source tracking) is more maintainable and semantically clear.

---

## Test Coverage

### Existing Test (Failing)
- `test_at_parallel_003.py::test_detector_offset_preservation` — Explicit beam center preservation

### Additional Tests Needed (Post-Fix)
1. **MOSFLM auto-calculated beam center test** — Verify +0.5 offset IS applied when using defaults
2. **MOSFLM explicit beam center test** — Verify +0.5 offset is NOT applied when user provides coordinates
3. **Non-MOSFLM convention test** — Verify no offset applied regardless of source (XDS, DIALS, CUSTOM, etc.)
4. **Edge case: User provides default-matching value** — Verify explicit source overrides heuristic

### Parity Validation
Compare C-code and PyTorch outputs for:
- **Case 1:** MOSFLM with defaults (should match, both apply +0.5)
- **Case 2:** MOSFLM with explicit beam center (currently fails parity; will match after fix)
- **Case 3:** XDS with any beam center (should match, no offset)

---

## Exit Criteria

- [ ] Detector class distinguishes explicit vs auto-calculated beam centers
- [ ] MOSFLM +0.5 pixel offset ONLY applied to auto-calculated beam centers
- [ ] `test_at_parallel_003.py::test_detector_offset_preservation` PASSES
- [ ] Additional test coverage added for auto vs explicit cases
- [ ] C-code parity validated for all MOSFLM beam center scenarios
- [ ] Documentation updated in detector.md and c_to_pytorch_config_map.md

---

## Code Locations

**Primary:**
- `src/nanobrag_torch/config.py` (DetectorConfig dataclass)
- `src/nanobrag_torch/models/detector.py` (beam center properties, lines ~78-142)
- `src/nanobrag_torch/__main__.py` (CLI parsing, beam center flag handling)

**Secondary:**
- `tests/test_at_parallel_003.py` (failing test + coverage expansion)
- `tests/test_detector_config.py` (may need updates for new config attribute)
- `tests/test_beam_center_offset.py` (comprehensive MOSFLM offset validation)

**Documentation:**
- `docs/architecture/detector.md` (§Beam Center Mapping)
- `docs/development/c_to_pytorch_config_map.md` (MOSFLM convention row)
- `specs/spec-a-core.md` (reference only, no changes)

---

## Spec/Arch References

- **spec-a-core.md §72:** MOSFLM beam center mapping formula
- **arch.md §ADR-03:** Beam-center Mapping (MOSFLM) and +0.5 pixel Offsets
- **arch.md §7:** Geometry Model & Conventions (lines 223-227, MOSFLM row)
- **docs/development/c_to_pytorch_config_map.md:** MOSFLM convention implicit rules (row 8)

---

## Related Fix Plan Items

- **[DETECTOR-CONFIG-001]:** In progress; Phase C depends on this C8 resolution
- **Phase M3a:** Handoff summary at `reports/2026-01-test-suite-triage/phase_m3/20251011T175917Z/mosflm_sync/summary.md` (per plan lines 236)

---

## Artifacts Expected

- **Implementation PR:** Code changes across config.py, detector.py, __main__.py
- **Test Coverage:** Expanded tests in test_at_parallel_003.py, test_beam_center_offset.py
- **Passing Validation:** `pytest -v tests/test_at_parallel_003.py` → 100% pass
- **Parity Check:** C vs PyTorch correlation ≥0.999 for MOSFLM explicit beam center case
- **Documentation Updates:** detector.md, c_to_pytorch_config_map.md refreshed

---

**Status:** → Phase M3 (ready for implementation handoff). Blueprint complete; awaiting [DETECTOR-CONFIG-001] Phase C execution.

**Phase M3 Classification:** Implementation bug requiring code fix (NOT tolerance adjustment or deprecation). Estimated effort: 2-3 hours (implementation + test expansion + parity validation).
