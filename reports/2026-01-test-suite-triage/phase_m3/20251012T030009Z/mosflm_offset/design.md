# MOSFLM Beam Center Offset Remediation Design (Option A)

**STAMP:** 20251012T030009Z
**Phase:** M3 Design Documentation
**Initiative:** DETECTOR-CONFIG-001
**Status:** Design Complete (Implementation Reference)

---

## Executive Summary

This document specifies the **Option A** remediation strategy for MOSFLM beam center offset handling, resolving the C8 cluster failure where the Detector class incorrectly applies +0.5 pixel offsets to ALL beam center coordinates, including explicit user-provided values.

**Core Decision:** Track beam center provenance via explicit `beam_center_source` attribute in `DetectorConfig` to distinguish auto-calculated defaults (where MOSFLM offset applies) from explicit user inputs (where offset must NOT be applied).

**Normative Basis:**
- **spec-a-core.md §72:** "Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel" (MOSFLM convention)
- **arch.md §ADR-03:** "MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs."

**Key Insight:** The +0.5 pixel offset is a **convention-specific default behavior**, not a mandatory transformation for all coordinates. Explicit user inputs must be preserved exactly.

---

## Phase B: Design Tasks

### B1. Decision Ratification

**Option A: Explicit Source Tracking (SELECTED)**

**Approach:** Add `beam_center_source` enum attribute to `DetectorConfig` with values `AUTO` (convention defaults) and `EXPLICIT` (user-provided).

**Why Option A:**
1. **Semantic Clarity:** Explicit intent encoded in config, not inferred from value comparison
2. **Auditability:** Single source of truth for offset application logic
3. **Maintainability:** No fragile heuristics comparing against computed defaults
4. **Testability:** Clear boundary between auto vs explicit cases

**Rejected Alternative (Option B: Value Comparison Heuristic):**
- Fragile: User could coincidentally provide default-matching value
- Couples beam center logic to detector size defaults
- Harder to reason about in edge cases (e.g., partial overrides)

### B2. CLI Detection Mapping

**Explicit Beam Center Flags (8 total):**

| CLI Flag | Convention Affinity | Pivot Implication | Source Assignment |
|----------|---------------------|-------------------|-------------------|
| `--beam_center_s` | Generic | None | EXPLICIT |
| `--beam_center_f` | Generic | None | EXPLICIT |
| `-Xbeam` | MOSFLM/DENZO | BEAM | EXPLICIT |
| `-Ybeam` | MOSFLM/DENZO | BEAM | EXPLICIT |
| `-Xclose` | XDS/DIALS | SAMPLE | EXPLICIT |
| `-Yclose` | XDS/DIALS | SAMPLE | EXPLICIT |
| `-ORGX` | XDS | SAMPLE | EXPLICIT |
| `-ORGY` | XDS | SAMPLE | EXPLICIT |

**Detection Logic (Pseudocode):**
```python
# In __main__.py CLI parsing
if any([args.beam_center_s is not None,
        args.beam_center_f is not None,
        args.Xbeam is not None,
        args.Ybeam is not None,
        args.Xclose is not None,
        args.Yclose is not None,
        args.ORGX is not None,
        args.ORGY is not None]):
    config.beam_center_source = BeamCenterSource.EXPLICIT
else:
    config.beam_center_source = BeamCenterSource.AUTO
```

**Edge Case Handling:**
- **Partial Overrides:** If user provides only `-Xbeam` (not `-Ybeam`), mark as EXPLICIT (user is actively configuring beam center, even if incomplete)
- **Header Ingestion:** Beam centers read from `-img`/`-mask` headers are treated as EXPLICIT (user has encoded them in the image file)
- **Matrix Files:** MOSFLM `-mat` files do NOT imply beam center source (they specify crystal orientation only)

### B3. Implementation Touch Points

**Configuration Layer (`src/nanobrag_torch/config.py`):**

```python
from enum import Enum
from dataclasses import dataclass

class BeamCenterSource(Enum):
    """Provenance of beam center coordinates."""
    AUTO = "auto"        # Convention-specific defaults → apply MOSFLM offset
    EXPLICIT = "explicit"  # User-provided values → no offset

@dataclass
class DetectorConfig:
    # ... existing fields ...
    beam_center_s_mm: float
    beam_center_f_mm: float
    beam_center_source: BeamCenterSource = BeamCenterSource.AUTO
    # ... other fields ...
```

**CLI Parsing (`src/nanobrag_torch/__main__.py`):**

Add detection logic after all beam center flags are parsed:
```python
# After resolving all beam center flags
explicit_flags = [
    args.beam_center_s, args.beam_center_f,
    args.Xbeam, args.Ybeam,
    args.Xclose, args.Yclose,
    args.ORGX, args.ORGY
]
if any(flag is not None for flag in explicit_flags):
    config.beam_center_source = BeamCenterSource.EXPLICIT
else:
    config.beam_center_source = BeamCenterSource.AUTO
```

**Detector Properties (`src/nanobrag_torch/models/detector.py`):**

Modify beam center pixel conversion properties:
```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """Beam center in slow-axis pixels.

    Applies MOSFLM +0.5 pixel offset ONLY to auto-calculated defaults.
    Explicit user inputs are preserved exactly.
    """
    base_pixels = self.config.beam_center_s_mm / self.config.pixel_size_mm

    # Two-condition guard: MOSFLM convention AND auto-calculated source
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == BeamCenterSource.AUTO):
        return base_pixels + 0.5

    return base_pixels

@property
def beam_center_f_pixels(self) -> torch.Tensor:
    """Beam center in fast-axis pixels.

    Applies MOSFLM +0.5 pixel offset ONLY to auto-calculated defaults.
    Explicit user inputs are preserved exactly.
    """
    base_pixels = self.config.beam_center_f_mm / self.config.pixel_size_mm

    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == BeamCenterSource.AUTO):
        return base_pixels + 0.5

    return base_pixels
```

**Key Design Constraint:** Properties must remain differentiable (no `.item()` calls, preserve tensor graph).

### B4. Test Coverage Strategy

**New Test Module (`tests/test_beam_center_source.py`):**

1. **test_mosflm_auto_applies_offset:**
   - Setup: MOSFLM convention, no explicit beam center flags (AUTO source)
   - Expectation: `beam_center_s_pixels` returns `(s_mm / pixel_mm) + 0.5`

2. **test_mosflm_explicit_no_offset:**
   - Setup: MOSFLM convention, `--beam_center_s 512.5` (EXPLICIT source)
   - Expectation: `beam_center_s_pixels` returns exactly `512.5 / pixel_mm` (no +0.5)

3. **test_non_mosflm_no_offset:**
   - Setup: XDS/DIALS/CUSTOM conventions, any beam center source
   - Expectation: No offset applied for any convention except MOSFLM

4. **test_cli_detection_explicit:**
   - Setup: Provide each of 8 explicit flags individually
   - Expectation: `beam_center_source == BeamCenterSource.EXPLICIT` for all

5. **test_edge_case_explicit_matches_default:**
   - Setup: User provides beam center value that coincidentally equals convention default
   - Expectation: EXPLICIT source wins (no offset), demonstrating provenance tracking over value comparison

**Existing Test Updates:**
- `tests/test_at_parallel_003.py::test_detector_offset_preservation` — Should PASS after fix
- `tests/test_detector_config.py` — Update instantiations to include `beam_center_source` field

**Parity Validation:**
```bash
# Case 1: MOSFLM AUTO (both C and PyTorch apply +0.5)
./golden_suite_generator/nanoBragg -convention MOSFLM -default_F 100 -cell 100 100 100 90 90 90 ...
nanoBragg --convention MOSFLM --default_F 100 --cell 100 100 100 90 90 90 ...

# Case 2: MOSFLM EXPLICIT (C preserves, PyTorch should match after fix)
./golden_suite_generator/nanoBragg -convention MOSFLM -Xbeam 51.2 -Ybeam 51.2 ...
nanoBragg --convention MOSFLM --Xbeam 51.2 --Ybeam 51.2 ...

# Case 3: XDS (no offset for any source)
./golden_suite_generator/nanoBragg -convention XDS -default_F 100 ...
nanoBragg --convention XDS --default_F 100 ...
```

Expected: Correlation ≥0.999, |sum_ratio - 1| ≤5e-3 for all cases.

---

## Interaction Analysis

### API-002: `pix0` Override Interaction

**Concern:** Users can override `pix0_vector` directly via `--pix0`. How does this interact with `beam_center_source`?

**Resolution:**
- `pix0` override is an **orthogonal mechanism** for advanced users to bypass all convention logic
- When `pix0` is explicitly provided, beam center calculations are skipped entirely (detector origin is user-specified)
- `beam_center_source` only affects beam center → pix0 calculation when using convention-based geometry
- **No conflict:** If both `--pix0` and explicit beam center are provided, `pix0` wins (as per existing precedence rules)

**Test Coverage:**
```python
def test_pix0_override_bypasses_beam_center():
    """Verify pix0 override takes precedence over all beam center logic."""
    config = DetectorConfig(
        beam_center_s_mm=51.2,
        beam_center_source=BeamCenterSource.EXPLICIT,
        pix0_vector=[0.1, 0.05, -0.05],  # Explicit override
        detector_convention=DetectorConvention.MOSFLM,
        # ... other fields
    )
    detector = Detector(config)
    assert torch.allclose(detector.pix0, torch.tensor([0.1, 0.05, -0.05]))
    # Beam center properties are never evaluated when pix0 is explicit
```

### CONVENTION-001: CUSTOM Convention Behavior

**Concern:** CUSTOM convention has no normative offset rules. How should it behave?

**Spec Statement (spec-a-core.md §83):**
> "CUSTOM: Uses provided vectors; default Xbeam,Ybeam = Xclose,Yclose; Fbeam = Xbeam; Sbeam = Ybeam."

**Interpretation:**
- CUSTOM has NO implicit offset behavior (confirmed by arch.md ADR-03: "CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs")
- `beam_center_source` tracking still applies (to support future extensions)
- CUSTOM with AUTO source: no offset (default behavior)
- CUSTOM with EXPLICIT source: no offset (user values preserved)

**Implementation:**
```python
# In detector.py properties
if (self.config.detector_convention == DetectorConvention.MOSFLM and
    self.config.beam_center_source == BeamCenterSource.AUTO):
    return base_pixels + 0.5
# All other conventions (XDS, DIALS, ADXV, DENZO, CUSTOM): no offset
return base_pixels
```

**Test Coverage:**
```python
def test_custom_convention_no_offset():
    """CUSTOM convention never applies offsets, regardless of source."""
    for source in [BeamCenterSource.AUTO, BeamCenterSource.EXPLICIT]:
        config = DetectorConfig(
            beam_center_s_mm=51.2,
            beam_center_source=source,
            detector_convention=DetectorConvention.CUSTOM,
            # ... other fields
        )
        detector = Detector(config)
        expected = 51.2 / detector.config.pixel_size_mm
        assert torch.isclose(detector.beam_center_s_pixels, torch.tensor(expected))
```

---

## Normative Requirements Compliance

### spec-a-core.md §72 (MOSFLM Convention)

> "MOSFLM: Beam b = [1 0 0]; f = [0 0 1]; s = [0 -1 0]; o = [1 0 0]; 2θ-axis = [0 0 -1]; p = [0 0 1]; u = [0 0 1].
> Default Xbeam = (detsize_s + pixel)/2, Ybeam = (detsize_f + pixel)/2.
> **Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel.** Pivot = BEAM."

**Interpretation:**
- The formula "Fbeam = Ybeam + 0.5·pixel" describes the mapping for **convention defaults**
- When users provide explicit Xbeam/Ybeam values, those are treated as Fbeam/Sbeam directly (no additional offset)
- The offset is part of the "MOSFLM convention defaults" behavior, not the coordinate system itself

**Evidence from C Code:**
The C reference implementation applies the offset only when computing default beam centers from detector geometry, not when user provides explicit coordinates. (See `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md` §Root Cause Analysis)

### arch.md §ADR-03 (Beam-center Mapping)

> "MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs."

**Implementation Alignment:**
- Option A directly implements ADR-03's distinction between implicit (AUTO) and explicit offsets
- The `beam_center_source` attribute is the concrete realization of "unless provided by user inputs"
- CUSTOM convention behavior follows ADR-03's decision (no implicit offsets)

### AT-GEO-001 (Acceptance Test)

> "Setup: detector_convention=MOSFLM; pixel_size=0.1 mm; distance=100.0 mm; beam_center_X=beam_center_Y=51.2 mm; pivot=BEAM; no rotations; twotheta=0.
> Expectation: Using f=[0,0,1], s=[0,-1,0], o=[1,0,0], Fbeam=Sbeam=(51.2+0.05) mm. The detector origin SHALL be pix0_vector = [0.1, 0.05125, -0.05125] meters (±1e-9 m tolerance)."

**Conflict Resolution:**
- AT-GEO-001 as written assumes +0.5 offset is ALWAYS applied
- Per spec §72 and ADR-03, offset should only apply to AUTO defaults
- **Design Decision:** AT-GEO-001 test case describes an AUTO scenario (no explicit flags provided in setup)
- When user provides `--beam_center_X 51.2 --beam_center_Y 51.2` explicitly, offset should NOT be applied
- Test interpretation: "beam_center_X=beam_center_Y=51.2 mm" describes the **config values**, not CLI flags
- For AUTO source (convention defaults), the test expectation is correct

---

## Phase Boundaries and Dependencies

### Phase A: Analysis (COMPLETE)
- ✅ Root cause identified (C8 cluster triage)
- ✅ Spec/arch references documented
- ✅ Options A and B evaluated

### Phase B: Design (THIS DOCUMENT)
- ✅ B1: Option A ratified with justification
- ✅ B2: CLI detection logic specified (8 explicit flags)
- ✅ B3: Implementation touch points mapped (3 files)
- ✅ B4: Test coverage strategy defined (5 new tests + 2 updates)

### Phase C: Implementation (PENDING)
Tasks:
- C1: Add `BeamCenterSource` enum to `config.py`
- C2: Implement CLI detection in `__main__.py`
- C3: Update detector properties in `detector.py`
- C4: Create `tests/test_beam_center_source.py` with 5 test cases
- C5: Run targeted validation: `pytest -v tests/test_beam_center_source.py tests/test_at_parallel_003.py`
- C6: Update documentation (detector.md, c_to_pytorch_config_map.md, findings.md)
- C7: Update fix_plan.md ledger

**Exit Criteria:**
- [ ] 16/16 targeted tests PASS (5 new + existing detector tests)
- [ ] `test_at_parallel_003.py::test_detector_offset_preservation` PASSES
- [ ] No new failures introduced in detector geometry test suite

### Phase D: Validation (PENDING)
Tasks:
- D1: Full test suite rerun (`pytest -v tests/`)
- D2: C-PyTorch parity validation (3 cases: MOSFLM AUTO, MOSFLM EXPLICIT, XDS)
- D3: Documentation sync check

**Exit Criteria:**
- [ ] Test suite pass rate ≥ baseline (no regressions)
- [ ] C-PyTorch correlation ≥0.999 for all parity cases
- [ ] Documentation updated and consistent across detector.md, arch.md, c_to_pytorch_config_map.md

---

## Risk Assessment

### Implementation Risks

**R1: Backward Compatibility**
- **Risk:** Existing code/tests assume AUTO behavior everywhere
- **Mitigation:** Default to `AUTO` (preserves existing behavior for code not using explicit flags)
- **Verification:** Run full test suite before/after; flag any XPASS transitions

**R2: Device/Dtype Neutrality**
- **Risk:** Enum comparisons or tensor operations break device/dtype neutrality
- **Mitigation:**
  - Enum comparisons are Python-level (device-agnostic)
  - All tensor arithmetic remains unchanged (properties return tensors with same device/dtype as inputs)
- **Verification:** Run CPU and CUDA smoke tests (when available)

**R3: Differentiability Preservation**
- **Risk:** Adding control flow to properties breaks gradient flow
- **Mitigation:**
  - Properties remain pure functions of config tensors
  - Conditional (if) based on enum (not tensor value) → doesn't break autograd graph
  - No `.item()` or `.detach()` introduced
- **Verification:** Gradient tests in `test_gradients.py` must remain passing

**R4: Test Suite Impact**
- **Risk:** Many tests instantiate DetectorConfig without new field
- **Mitigation:** Provide default value `AUTO` in dataclass definition
- **Verification:** Run `pytest --collect-only` to ensure no collection errors

### Integration Risks

**R5: Header Ingestion Ambiguity**
- **Risk:** Beam centers from `-img`/`-mask` headers could be convention defaults or explicit user values
- **Mitigation:** Treat all header-ingested beam centers as EXPLICIT (conservative choice: preserve user data)
- **Verification:** Add test for header ingestion setting EXPLICIT source

**R6: CLI Precedence Conflicts**
- **Risk:** User provides conflicting flags (e.g., `--beam_center_s` AND `-Xbeam`)
- **Mitigation:** Existing precedence rules apply (last-wins or priority order); source is EXPLICIT for any explicit flag
- **Verification:** Test multiple explicit flags together (e.g., `--Xbeam 51.2 --beam_center_s 512`)

---

## Acceptance Criteria (Phase B Complete)

- [x] Option A selected and justified against Option B
- [x] CLI detection logic specified for all 8 explicit beam center flags
- [x] Implementation touch points mapped (config.py, __main__.py, detector.py)
- [x] Test coverage strategy defined (5 new tests, 2 updates, parity validation)
- [x] Interaction analysis complete (API-002 pix0, CONVENTION-001 CUSTOM)
- [x] Normative compliance verified (spec-a-core.md §72, arch.md ADR-03, AT-GEO-001)
- [x] Phase boundaries defined (A complete, B complete, C/D pending)
- [x] Risk assessment documented (6 risks, all with mitigations)

---

## Artifacts and References

**Design Artifacts:**
- This document: `reports/2026-01-test-suite-triage/phase_m3/20251012T030009Z/mosflm_offset/design.md`
- Previous analysis: `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md`

**Normative References:**
- `specs/spec-a-core.md` §68-86 (Geometry & Conventions)
- `arch.md` §79-80 (ADR-03: Beam-center Mapping)
- `docs/architecture/detector.md` (Detector component specification)
- `docs/development/c_to_pytorch_config_map.md` (C↔PyTorch configuration parity)

**Implementation References:**
- `src/nanobrag_torch/config.py` (DetectorConfig dataclass)
- `src/nanobrag_torch/models/detector.py` (beam_center_s_pixels, beam_center_f_pixels properties)
- `src/nanobrag_torch/__main__.py` (CLI parsing and precedence)

**Test References:**
- `tests/test_at_parallel_003.py` (C8 cluster failing test)
- `tests/test_detector_config.py` (Detector configuration validation)
- `tests/test_beam_center_offset.py` (Comprehensive MOSFLM offset tests - to be created)

---

## Next Steps (Phase C Implementation)

1. **Enum Definition (30 min):**
   - Add `BeamCenterSource` enum to `config.py`
   - Update `DetectorConfig` dataclass with `beam_center_source` field (default AUTO)

2. **CLI Detection (45 min):**
   - Add detection logic after beam center flag parsing in `__main__.py`
   - Test with manual CLI invocations to verify correct source assignment

3. **Property Updates (30 min):**
   - Modify `beam_center_s_pixels` and `beam_center_f_pixels` in `detector.py`
   - Add docstrings explaining offset logic

4. **Test Creation (60 min):**
   - Create `tests/test_beam_center_source.py` with 5 test cases
   - Update existing tests for new config field

5. **Targeted Validation (15 min):**
   - Run `pytest -v tests/test_beam_center_source.py tests/test_at_parallel_003.py`
   - Verify 100% pass rate

6. **Documentation Sync (30 min):**
   - Update `docs/architecture/detector.md` (Beam Center Mapping section)
   - Update `docs/development/c_to_pytorch_config_map.md` (MOSFLM row with AUTO/EXPLICIT note)
   - Add entry to `docs/findings.md`

7. **Ledger Update (15 min):**
   - Append to `docs/fix_plan.md` Attempts History for C8 cluster
   - Mark C8 as RESOLVED with Phase C artifacts

**Estimated Total Effort:** 3.5 hours

---

**Status:** Phase B Design Complete ✅
**Next Phase:** C (Implementation) — Pending approval and execution
