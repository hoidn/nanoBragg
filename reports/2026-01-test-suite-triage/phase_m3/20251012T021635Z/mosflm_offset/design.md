# MOSFLM Beam Center Offset Remediation Design (Option A)

**STAMP:** 20251012T021635Z
**Phase:** M3 Documentation
**Status:** Design Specification for Implementation

---

## Executive Summary

This document specifies the Option A design for fixing the MOSFLM beam center offset misapplication bug (C8 cluster). The bug causes the detector to incorrectly apply the MOSFLM convention +0.5 pixel offset to ALL beam center coordinates, including explicit user-provided values, violating spec-a-core.md §72 and arch.md §ADR-03.

**Core Design Principle:** Add explicit provenance tracking to DetectorConfig via a `beam_center_source` attribute that distinguishes between auto-calculated convention defaults (`"auto"`) and explicit user inputs (`"explicit"`). The detector layer then conditionally applies the MOSFLM +0.5 offset ONLY when `convention=MOSFLM AND source=AUTO`.

---

## Normative References

### Specification Requirements

**specs/spec-a-core.md §72 (MOSFLM Convention):**
```
- MOSFLM:
    - Beam b = [1 0 0]; f = [0 0 1]; s = [0 -1 0]; o = [1 0 0]; 2θ-axis = [0 0 -1]; p = [0 0 1];
u = [0 0 1].
    - Default Xbeam = (detsize_s + pixel)/2, Ybeam = (detsize_f + pixel)/2.
    - Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel. Pivot = BEAM.
```

**Key Interpretation:** The +0.5 pixel offset is part of the MOSFLM beam center **default calculation formula**, not a mandatory transformation applied to all beam center values. When users provide explicit beam centers, those values must be preserved exactly.

### Architecture ADR

**arch.md §ADR-03 (Beam-center Mapping (MOSFLM) and +0.5 pixel Offsets):**
```
- MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels).
  CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets
  unless provided by user inputs.
```

**Clarification:** This ADR documents the MOSFLM formula but does not explicitly state when to apply it. The design interprets this as "apply during default calculation, not to explicit inputs."

---

## Problem Statement

### Current Incorrect Behavior

**Location:** `src/nanobrag_torch/models/detector.py` (beam center properties, lines ~78-142)

**Pseudocode:**
```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm
    if self.config.detector_convention == DetectorConvention.MOSFLM:
        return base + 0.5  # ALWAYS applied, regardless of source
    return base
```

**Failure Mode:** When a user provides explicit `--beam_center_s 512.5`, the detector receives `512.5` (in mm), converts to pixels (`512.5`), then applies the offset to get `513.0` pixels — a 0.5 pixel error.

### Test Failure

**Failing Test:** `tests/test_at_parallel_003.py::test_detector_offset_preservation`

**Test Logic:**
```python
# User provides explicit beam center
config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    beam_center_s_mm=51.25,  # 512.5 pixels at 0.1mm pixel size
    beam_center_f_mm=51.25,
    pixel_size_mm=0.1,
)

detector = Detector(config)

# Expectation: Explicit values preserved exactly
assert detector.beam_center_s_pixels == 512.5  # FAILS: gets 513.0
```

---

## Option A Design: Explicit Provenance Tracking

### Design Rationale

**Why Option A over Option B (heuristic checking)?**

1. **Semantic Clarity:** Provenance is a first-class concept in the config
2. **Robustness:** No fragile edge cases (e.g., user coincidentally provides default value)
3. **Auditability:** Easy to trace through CLI → config → detector pipeline
4. **Maintainability:** Future developers can reason about the system without guessing

**Trade-off:** Requires touching 3 files (config, CLI, detector) and updating all test DetectorConfig instantiations.

### Component Breakdown

#### 1. Configuration Layer (`src/nanobrag_torch/config.py`)

**Addition:** `BeamCenterSource` enum to encode provenance semantics.

```python
from enum import Enum

class BeamCenterSource(Enum):
    """Provenance tracking for beam center coordinates.

    AUTO: Beam center derived from convention-specific default formulas.
          MOSFLM convention applies +0.5 pixel offset during computation.

    EXPLICIT: Beam center provided directly by user via CLI flags or API.
              No convention-dependent offsets applied; values preserved exactly.
    """
    AUTO = "auto"
    EXPLICIT = "explicit"


@dataclass
class DetectorConfig:
    """Detector geometry configuration.

    ... existing docstring ...

    beam_center_source: BeamCenterSource
        Provenance of beam_center_s_mm and beam_center_f_mm values.
        Determines whether MOSFLM +0.5 pixel offset is applied.
        Defaults to AUTO for backward compatibility.
    """
    # ... existing fields ...

    beam_center_source: BeamCenterSource = BeamCenterSource.AUTO
```

**Backward Compatibility:** Default value `AUTO` preserves existing behavior for tests/code that don't set the flag explicitly.

#### 2. CLI Detection Logic (`src/nanobrag_torch/__main__.py`)

**Addition:** `determine_beam_center_source()` helper function to detect explicit beam center flags.

```python
def determine_beam_center_source(args: argparse.Namespace) -> BeamCenterSource:
    """Detect whether beam center coordinates are explicit or auto-calculated.

    Args:
        args: Parsed CLI arguments

    Returns:
        BeamCenterSource.EXPLICIT if any explicit beam center flag is provided,
        BeamCenterSource.AUTO otherwise.

    Explicit flags:
        --beam_center_s, --beam_center_f (direct slow/fast coordinates)
        -Xbeam, -Ybeam (MOSFLM/DENZO style, mm)
        -Xclose, -Yclose (SAMPLE pivot, mm)
        -ORGX, -ORGY (XDS style, pixels)
        --img, --mask (header ingestion; treated as explicit if headers contain beam center)
    """
    explicit_flags = [
        args.beam_center_s is not None,
        args.beam_center_f is not None,
        args.Xbeam is not None,
        args.Ybeam is not None,
        args.Xclose is not None,
        args.Yclose is not None,
        args.ORGX is not None,
        args.ORGY is not None,
        # Note: --img/--mask detection requires header parsing;
        # conservatively treat as explicit if provided
        args.img is not None,
        args.mask is not None,
    ]

    if any(explicit_flags):
        return BeamCenterSource.EXPLICIT
    return BeamCenterSource.AUTO
```

**Usage in main():**
```python
def main():
    args = parse_args()

    # ... existing config construction ...

    detector_config = DetectorConfig(
        # ... existing parameters ...
        beam_center_source=determine_beam_center_source(args),
    )
```

**Header Ingestion Note:** When `--img` or `--mask` is provided, headers may contain `BEAM_CENTER_X`/`BEAM_CENTER_Y` keys. The current implementation conservatively treats header-sourced values as explicit. Future refinement: parse headers first, then check if beam center keys exist before setting `EXPLICIT`.

#### 3. Detector Properties (`src/nanobrag_torch/models/detector.py`)

**Modification:** Add two-condition guard to beam center pixel conversion.

```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """Beam center slow-axis coordinate in pixel units.

    Conversion: mm → pixels via division by pixel_size_mm.

    MOSFLM Offset Handling (ADR-03):
        If convention=MOSFLM AND source=AUTO:
            Apply +0.5 pixel offset (convention default calculation)
        Otherwise:
            Preserve exact pixel value (explicit user input or non-MOSFLM convention)

    Returns:
        Beam center in pixels (float tensor)
    """
    base_pixels = self.config.beam_center_s_mm / self.config.pixel_size_mm

    # Apply MOSFLM offset ONLY to auto-calculated defaults
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == BeamCenterSource.AUTO):
        return base_pixels + 0.5

    return base_pixels


@property
def beam_center_f_pixels(self) -> torch.Tensor:
    """Beam center fast-axis coordinate in pixel units.

    (Same logic as beam_center_s_pixels, applied to fast axis)
    """
    base_pixels = self.config.beam_center_f_mm / self.config.pixel_size_mm

    # Apply MOSFLM offset ONLY to auto-calculated defaults
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == BeamCenterSource.AUTO):
        return base_pixels + 0.5

    return base_pixels
```

**Critical Implementation Note:** Both conditions (`convention == MOSFLM` AND `source == AUTO`) must be true for offset application. This ensures:
- MOSFLM with explicit values → no offset
- Non-MOSFLM conventions → no offset (regardless of source)
- MOSFLM with auto defaults → offset applied (existing behavior preserved)

---

## Implementation Tasks (Phase B)

### B1. Config Layer Changes

**File:** `src/nanobrag_torch/config.py`

**Tasks:**
1. Add `BeamCenterSource` enum with `AUTO` and `EXPLICIT` values
2. Add comprehensive docstring explaining provenance semantics
3. Add `beam_center_source: BeamCenterSource = BeamCenterSource.AUTO` field to `DetectorConfig`
4. Update `DetectorConfig` docstring to document the new field and its effect on MOSFLM offset behavior

**Validation:**
- Import succeeds: `from nanobrag_torch.config import BeamCenterSource, DetectorConfig`
- Default value works: `DetectorConfig(...) → beam_center_source == BeamCenterSource.AUTO`
- Explicit value works: `DetectorConfig(..., beam_center_source=BeamCenterSource.EXPLICIT)`

### B2. CLI Detection Logic

**File:** `src/nanobrag_torch/__main__.py`

**Tasks:**
1. Implement `determine_beam_center_source(args)` helper function
2. Document all 8 explicit beam center flags (see CLI Detection Logic section above)
3. Integrate helper into `main()` config construction
4. Add unit tests for detection logic (see B4 below)

**Edge Cases:**
- Multiple explicit flags provided → still returns `EXPLICIT` (any explicit flag triggers)
- `--img`/`--mask` without beam center headers → conservatively treats as `EXPLICIT` (safe choice)
- No flags provided → returns `AUTO` (default convention behavior)

### B3. Detector Property Guards

**File:** `src/nanobrag_torch/models/detector.py`

**Tasks:**
1. Modify `beam_center_s_pixels` property: add two-condition guard
2. Modify `beam_center_f_pixels` property: add two-condition guard
3. Update docstrings to document offset behavior explicitly
4. Verify no other code paths access beam center raw values (audit uses of `self.config.beam_center_*_mm`)

**Validation:**
- MOSFLM + AUTO → offset applied (existing test cases)
- MOSFLM + EXPLICIT → no offset (new test case)
- XDS/DIALS/CUSTOM + any source → no offset (existing test cases)

### B4. Test Coverage Expansion

**New Test File:** `tests/test_beam_center_source.py`

**Test Cases:**

```python
class TestBeamCenterSource:
    """Validate beam center provenance tracking and offset application."""

    def test_mosflm_auto_applies_offset(self):
        """MOSFLM with auto-calculated defaults applies +0.5 pixel offset."""
        config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            beam_center_s_mm=12.8,  # 128 pixels at 0.1mm
            beam_center_f_mm=12.8,
            pixel_size_mm=0.1,
            beam_center_source=BeamCenterSource.AUTO,
        )
        detector = Detector(config)

        # Expectation: offset applied
        assert detector.beam_center_s_pixels == 128.5
        assert detector.beam_center_f_pixels == 128.5

    def test_mosflm_explicit_no_offset(self):
        """MOSFLM with explicit user values preserves coordinates exactly."""
        config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            beam_center_s_mm=51.25,  # 512.5 pixels at 0.1mm
            beam_center_f_mm=51.25,
            pixel_size_mm=0.1,
            beam_center_source=BeamCenterSource.EXPLICIT,
        )
        detector = Detector(config)

        # Expectation: NO offset applied
        assert detector.beam_center_s_pixels == 512.5
        assert detector.beam_center_f_pixels == 512.5

    def test_xds_no_offset_regardless_of_source(self):
        """Non-MOSFLM conventions never apply offset."""
        for source in [BeamCenterSource.AUTO, BeamCenterSource.EXPLICIT]:
            config = DetectorConfig(
                detector_convention=DetectorConvention.XDS,
                beam_center_s_mm=12.8,
                beam_center_f_mm=12.8,
                pixel_size_mm=0.1,
                beam_center_source=source,
            )
            detector = Detector(config)

            # Expectation: no offset for XDS
            assert detector.beam_center_s_pixels == 128.0
            assert detector.beam_center_f_pixels == 128.0

    def test_cli_detection_explicit_flags(self):
        """CLI detection correctly identifies explicit beam center flags."""
        args = argparse.Namespace(
            beam_center_s=512.5, beam_center_f=512.5,
            Xbeam=None, Ybeam=None, Xclose=None, Yclose=None,
            ORGX=None, ORGY=None, img=None, mask=None,
        )
        assert determine_beam_center_source(args) == BeamCenterSource.EXPLICIT

    def test_cli_detection_auto_defaults(self):
        """CLI detection returns AUTO when no explicit flags provided."""
        args = argparse.Namespace(
            beam_center_s=None, beam_center_f=None,
            Xbeam=None, Ybeam=None, Xclose=None, Yclose=None,
            ORGX=None, ORGY=None, img=None, mask=None,
        )
        assert determine_beam_center_source(args) == BeamCenterSource.AUTO
```

**Existing Test Update:** Modify `tests/test_at_parallel_003.py::test_detector_offset_preservation` to set `beam_center_source=BeamCenterSource.EXPLICIT` explicitly.

---

## API Impact Analysis

### API-002: Direct DetectorConfig Instantiation

**Risk:** Users constructing `DetectorConfig` directly in Python code (not via CLI) may not set `beam_center_source` explicitly, leading to unintended AUTO behavior.

**Mitigation Strategies:**

1. **Default to AUTO for backward compatibility:** Existing code that doesn't set the flag will continue to work with default convention behavior.

2. **Documentation Warning:** Add prominent note to `DetectorConfig` docstring:

```python
@dataclass
class DetectorConfig:
    """...

    WARNING: When constructing DetectorConfig directly (not via CLI), you MUST
    explicitly set beam_center_source=BeamCenterSource.EXPLICIT if providing
    explicit beam center coordinates. Otherwise, the default AUTO will apply
    MOSFLM +0.5 pixel offset unintentionally for MOSFLM convention.

    Example (CORRECT):
        config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            beam_center_s_mm=51.25,
            beam_center_source=BeamCenterSource.EXPLICIT,  # Required!
        )

    Example (INCORRECT - will apply unwanted offset):
        config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            beam_center_s_mm=51.25,
            # beam_center_source defaults to AUTO → applies +0.5 offset
        )
    """
```

3. **Test Coverage:** Add test demonstrating the incorrect behavior when `beam_center_source` is omitted (with explicit `pytest.xfail` marker and comment explaining the API trap).

---

## Convention Interaction Analysis (CONVENTION-001)

### MOSFLM Behavior Matrix

| Source      | Convention | Beam Center (pixels) | Offset Applied? | Rationale                    |
|-------------|------------|----------------------|-----------------|------------------------------|
| AUTO        | MOSFLM     | 128.0 → 128.5        | ✅ YES          | Convention default formula   |
| EXPLICIT    | MOSFLM     | 512.5 → 512.5        | ❌ NO           | User-provided, preserve exact|
| AUTO        | XDS        | 128.0 → 128.0        | ❌ NO           | XDS has no offset            |
| EXPLICIT    | XDS        | 512.5 → 512.5        | ❌ NO           | XDS has no offset            |

### CUSTOM Convention Edge Case

**Scenario:** User provides explicit beam center with `detector_convention=CUSTOM`.

**Behavior:** No offset applied (CUSTOM convention has no implicit offsets per ADR-03).

**Validation:** Covered by `test_xds_no_offset_regardless_of_source` (generalizes to CUSTOM/DIALS/DENZO).

### pix0 Override Interaction

**Scenario:** User provides explicit `pix0_vector` override (API-002 related).

**Current Design:** `pix0_vector` overrides are handled separately in `_compute_pix0_vector()` and bypass beam center calculations entirely.

**Impact:** No conflict. `beam_center_source` only affects beam center → pix0 calculation path, not explicit pix0 overrides.

---

## Testing Strategy

### Unit Tests (New: `tests/test_beam_center_source.py`)

**Coverage:**
1. MOSFLM + AUTO → offset applied ✅
2. MOSFLM + EXPLICIT → no offset ✅
3. Non-MOSFLM + any source → no offset ✅
4. CLI detection with explicit flags → EXPLICIT ✅
5. CLI detection with no flags → AUTO ✅

**Runtime:** ~0.5s (lightweight config/detector instantiation, no full simulation)

### Integration Test (Existing: `tests/test_at_parallel_003.py`)

**Update Required:** Modify `test_detector_offset_preservation` to set `beam_center_source=EXPLICIT`:

```python
def test_detector_offset_preservation(self):
    """AT-PARALLEL-003: Explicit beam centers preserved without convention offsets."""
    config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        beam_center_s_mm=51.25,
        beam_center_f_mm=51.25,
        pixel_size_mm=0.1,
        beam_center_source=BeamCenterSource.EXPLICIT,  # NEW
    )
    detector = Detector(config)

    # This test previously FAILED; now PASSES with explicit source
    assert detector.beam_center_s_pixels == 512.5
    assert detector.beam_center_f_pixels == 512.5
```

**Expected Outcome:** Test transitions from FAILED → PASSED after implementation.

### Parity Validation (C-PyTorch Equivalence)

**Test Cases:**

1. **MOSFLM with defaults (AUTO):**
   - C command: `./nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 -distance 100 -detpixels 256`
   - PyTorch: `DetectorConfig(..., beam_center_source=AUTO)`
   - Expectation: Both apply +0.5 offset, correlation ≥0.999

2. **MOSFLM with explicit beam center (EXPLICIT):**
   - C command: `./nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 -distance 100 -detpixels 256 -Xbeam 12.8 -Ybeam 12.8`
   - PyTorch: `DetectorConfig(..., beam_center_s_mm=12.8, beam_center_f_mm=12.8, beam_center_source=EXPLICIT)`
   - Expectation: Both preserve exact values, correlation ≥0.999

3. **XDS convention:**
   - C command: `./nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 -distance 100 -detpixels 256 -convention XDS`
   - PyTorch: `DetectorConfig(..., detector_convention=XDS, beam_center_source=AUTO or EXPLICIT)`
   - Expectation: No offset for either, correlation ≥0.999

**Parity Harness:** Add cases to `tests/test_parity_matrix.py` or `tests/parity_cases.yaml` covering the matrix above.

---

## Documentation Updates

### 1. Detector Architecture (`docs/architecture/detector.md`)

**Section to Update:** §Beam Center Mapping

**Addition:**
```markdown
### Beam Center Provenance Tracking (Phase M3, Option A)

The detector distinguishes between auto-calculated convention defaults and explicit
user-provided beam center coordinates via the `beam_center_source` attribute.

**Beam Center Source Values:**
- `AUTO`: Beam center derived from convention-specific default formulas. MOSFLM
  convention applies +0.5 pixel offset during computation.
- `EXPLICIT`: Beam center provided directly by user via CLI flags (--beam_center_s,
  -Xbeam, etc.) or API. No convention-dependent offsets applied.

**MOSFLM Offset Behavior:**
```python
if convention == MOSFLM and source == AUTO:
    beam_center_pixels = (beam_center_mm / pixel_size_mm) + 0.5
else:
    beam_center_pixels = beam_center_mm / pixel_size_mm
```

**CLI Detection:** The following flags indicate EXPLICIT beam center input:
- `--beam_center_s`, `--beam_center_f`
- `-Xbeam`, `-Ybeam` (MOSFLM/DENZO style)
- `-Xclose`, `-Yclose` (SAMPLE pivot style)
- `-ORGX`, `-ORGY` (XDS style)
- `--img`, `--mask` (header ingestion, treated as explicit)

**See:** `docs/development/c_to_pytorch_config_map.md` §DETECTOR-CONFIG-001 for
complete mapping and implicit rules.
```

### 2. C-to-PyTorch Config Map (`docs/development/c_to_pytorch_config_map.md`)

**Section to Add:** §Beam Center Source Detection (DETECTOR-CONFIG-001)

**Content:** (Inline existing section from c_to_pytorch_config_map.md lines 70-133, already present in the map)

**Status:** Already documented in current map; no changes needed.

### 3. Findings Document (`docs/findings.md`)

**Section to Update:** §Detector Geometry

**Addition:**
```markdown
### MOSFLM Beam Center Offset (C8 Cluster, Phase M3)

**Issue:** Detector incorrectly applied MOSFLM +0.5 pixel offset to ALL beam center
coordinates, including explicit user inputs.

**Root Cause:** `beam_center_s_pixels` / `beam_center_f_pixels` properties lacked
provenance tracking; couldn't distinguish auto-calculated defaults from explicit inputs.

**Resolution (Option A):** Added `beam_center_source` enum to DetectorConfig with
AUTO/EXPLICIT values. CLI detection logic sets source based on presence of explicit
flags. Detector properties apply offset ONLY when `convention=MOSFLM AND source=AUTO`.

**Test:** `tests/test_at_parallel_003.py::test_detector_offset_preservation` now PASSES.

**References:**
- Phase M3 Summary: `reports/.../phase_m3/20251011T193829Z/mosflm_offset/summary.md`
- Design Document: `reports/.../phase_m3/20251012T021635Z/mosflm_offset/design.md`
- Spec: `specs/spec-a-core.md` §72
- Architecture: `arch.md` §ADR-03
```

---

## Rollout Plan (Phase C Implementation)

### C1. Config Layer (Priority 1)

**File:** `src/nanobrag_torch/config.py`
**Tasks:** Add `BeamCenterSource` enum, add `beam_center_source` field to `DetectorConfig`
**Validation:** Import succeeds, default value works

### C2. CLI Detection (Priority 1)

**File:** `src/nanobrag_torch/__main__.py`
**Tasks:** Implement `determine_beam_center_source()`, integrate into `main()`
**Validation:** Unit tests for detection logic

### C3. Detector Properties (Priority 1)

**File:** `src/nanobrag_torch/models/detector.py`
**Tasks:** Add two-condition guards to `beam_center_s_pixels` and `beam_center_f_pixels`
**Validation:** Targeted pytest run on new test_beam_center_source.py

### C4. Test Coverage (Priority 2)

**File:** `tests/test_beam_center_source.py`
**Tasks:** Implement 5 new test cases (see B4 above)
**Validation:** All 5 tests PASS, runtime <1s

### C5. Integration Test Update (Priority 2)

**File:** `tests/test_at_parallel_003.py`
**Tasks:** Add `beam_center_source=EXPLICIT` to `test_detector_offset_preservation`
**Validation:** Test transitions from FAILED → PASSED

### C6. Documentation Sync (Priority 3)

**Files:** `docs/architecture/detector.md`, `docs/findings.md`
**Tasks:** Add sections documented above
**Validation:** Docs build succeeds, no broken links

### C7. Plan Update (Priority 3)

**File:** `docs/fix_plan.md`
**Tasks:** Mark C8 cluster RESOLVED, append Phase M3 completion note
**Validation:** Manual review of plan consistency

---

## Exit Criteria

- [ ] `BeamCenterSource` enum exists in `config.py` with AUTO/EXPLICIT values
- [ ] `DetectorConfig.beam_center_source` field exists with default value AUTO
- [ ] `determine_beam_center_source()` implemented in `__main__.py` with 8 flag detection
- [ ] `beam_center_s_pixels` and `beam_center_f_pixels` have two-condition guards
- [ ] `tests/test_beam_center_source.py` created with 5 test cases, all PASSING
- [ ] `test_at_parallel_003.py::test_detector_offset_preservation` PASSES
- [ ] Full test suite: no new regressions introduced (C8 failure → resolved)
- [ ] C-PyTorch parity validated for MOSFLM AUTO/EXPLICIT cases (correlation ≥0.999)
- [ ] Documentation updated: detector.md, findings.md
- [ ] Plan ledger updated: C8 marked RESOLVED with artifact links

---

## Risk Register

| Risk ID | Description | Likelihood | Impact | Mitigation |
|---------|-------------|------------|--------|------------|
| R1 | API users forget to set `beam_center_source=EXPLICIT` | Medium | Medium | Prominent docs warning, test demonstrating trap |
| R2 | Header ingestion from `--img`/`--mask` doesn't parse beam center keys | Low | Low | Conservative default (treat as explicit); future refinement |
| R3 | Test suite has other tests assuming AUTO behavior | Medium | Low | Full-suite rerun; update failing tests case-by-case |
| R4 | pix0 override interactions not fully tested | Low | Low | Existing pix0 tests cover override path separately |

---

## Validation Artifacts Expected

### Phase C (Implementation)

- **C1-C3 Code Changes:** Git commits for config.py, __main__.py, detector.py
- **C4 Test File:** `tests/test_beam_center_source.py` with 5 passing tests
- **C5 Test Update:** Modified `test_at_parallel_003.py` showing FAILED → PASSED transition
- **C6 Documentation:** Updated detector.md and findings.md
- **C7 Plan Update:** `docs/fix_plan.md` with C8 cluster RESOLVED

### Phase D (Validation)

- **Full-Suite Run:** `pytest -v tests/` output showing no new regressions
- **Parity Metrics:** C vs PyTorch correlation ≥0.999 for MOSFLM AUTO/EXPLICIT cases
- **Artifacts:** Correlation plots, metrics.json, test logs under `reports/.../phase_d/<STAMP>/`

---

## References

- **C8 Cluster Summary:** `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md`
- **Spec:** `specs/spec-a-core.md` §72 (MOSFLM Convention)
- **Architecture:** `arch.md` §ADR-03 (Beam-center Mapping)
- **Config Map:** `docs/development/c_to_pytorch_config_map.md` §DETECTOR-CONFIG-001
- **Detector Architecture:** `docs/architecture/detector.md` §Beam Center Mapping
- **Testing Strategy:** `docs/development/testing_strategy.md` §2 (Configuration Parity)
- **Debugging Checklist:** `docs/debugging/detector_geometry_checklist.md` §Beam Center

---

**Design Status:** ✅ COMPLETE (Ready for Phase C Implementation)

**Approval:** This design document ratifies Option A as the implementation approach for resolving C8 cluster. Implementation proceeds per tasks C1-C7.

**Estimated Effort:** 2-3 hours (implementation + test expansion + targeted validation)

**Next Phase:** Phase C (Implementation) - Execute tasks C1-C7 sequentially, validate with targeted tests, then proceed to Phase D full-suite validation.
