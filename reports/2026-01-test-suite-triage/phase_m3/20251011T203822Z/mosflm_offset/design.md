# DETECTOR-CONFIG-001: MOSFLM Beam Center Offset Remediation Design (Option A)

**STAMP:** 20251011T203822Z
**Phase:** M3 Phase B (Behavior Contract & Blueprint Refresh)
**Plan Reference:** `plans/active/detector-config.md`
**Decision:** **Option A RATIFIED** — Track beam center source explicitly via config flag

---

## Executive Summary

This design document specifies the **Option A** remediation for C8 cluster failures (MOSFLM beam center offset misapplication). The implementation will add a `beam_center_source` attribute to `DetectorConfig` to distinguish between auto-calculated (defaults) and explicit user-provided beam centers, ensuring the MOSFLM convention +0.5 pixel offset is applied **only** to auto-calculated values per spec-a-core.md §72 and arch.md §ADR-03.

**Classification:** Implementation bug (specification violation)
**Priority:** P2.1 (High — spec compliance for user-provided coordinates)
**Estimated Effort:** 2-3 hours (implementation + test expansion + targeted validation)

---

## 1. Normative Requirements

### 1.1 Specification References

**spec-a-core.md §§68-73** (MOSFLM Convention — Geometry & Conventions):
```
- MOSFLM:
    - Beam b = [1 0 0]; f = [0 0 1]; s = [0 -1 0]; o = [1 0 0]; 2θ-axis = [0 0 -1]; p = [0 0 1];
u = [0 0 1].
    - Default Xbeam = (detsize_s + pixel)/2, Ybeam = (detsize_f + pixel)/2.
    - Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel. Pivot = BEAM.
```

**Key Insight:** The +0.5 pixel offset is part of the **mapping formula** from `Xbeam/Ybeam` (mm) to `Fbeam/Sbeam` (meters), applied when beam centers are **derived from detector size defaults**. The spec does not mandate this offset for **explicit user-provided coordinates**.

**arch.md §ADR-03** (Beam-center Mapping (MOSFLM) and +0.5 pixel Offsets):
```
- MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs.
```

**Interpretation:** The ADR clarifies that CUSTOM convention does not apply implicit offsets. By extension, explicit user inputs in **any** convention should not receive implicit adjustments beyond what the user explicitly requested.

### 1.2 Current Bug

**Observed Behavior:**
The `Detector` class applies the +0.5 pixel offset to **all** MOSFLM beam center coordinates, regardless of whether they are auto-calculated defaults or explicit user inputs.

**Failing Test:**
`tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation`

**Expected:** User provides `beam_center_s=512.5` → detector uses exactly 512.5 pixels
**Actual:** Detector computes 513.0 pixels (512.5 + 0.5 offset)

**Impact:** Users cannot specify exact beam center positions when using MOSFLM convention, causing geometry mismatches with external tools and breaking parity with explicitly provided coordinates.

---

## 2. Option A Design: Explicit Source Tracking

### 2.1 Approach

Add a `beam_center_source` attribute to `DetectorConfig` (enum or string literal) to distinguish:
- `"auto"`: Beam center derived from detector size defaults → apply MOSFLM +0.5 pixel offset
- `"explicit"`: Beam center explicitly provided by user → no implicit offset

This approach provides **semantic clarity** and **auditability** for the entire CLI → config → detector pipeline.

### 2.2 Core Changes

#### 2.2.1 Configuration Layer (`src/nanobrag_torch/config.py`)

```python
from enum import Enum
from dataclasses import dataclass
from typing import Literal

# Option 1: Enum (more type-safe)
class BeamCenterSource(Enum):
    AUTO = "auto"
    EXPLICIT = "explicit"

# Option 2: Literal (more lightweight)
BeamCenterSourceType = Literal["auto", "explicit"]

@dataclass
class DetectorConfig:
    # Existing fields...
    beam_center_s_mm: float
    beam_center_f_mm: float
    pixel_size_mm: float
    detector_convention: DetectorConvention

    # NEW FIELD:
    beam_center_source: BeamCenterSourceType = "auto"  # Default to auto-calculated

    # ... other fields
```

**Rationale for Default:** Setting `beam_center_source="auto"` by default preserves backward compatibility for code paths that construct `DetectorConfig` without specifying this field (e.g., tests, internal utilities). The CLI layer will override to `"explicit"` when appropriate.

#### 2.2.2 CLI Parsing Layer (`src/nanobrag_torch/__main__.py`)

**Detection Logic:** Set `beam_center_source="explicit"` if **any** of the following flags are provided:

```python
# Beam center flags that indicate explicit user input:
EXPLICIT_BEAM_CENTER_FLAGS = [
    'Xbeam',          # -Xbeam
    'Ybeam',          # -Ybeam
    'beam_center_s',  # --beam-center-s (API-style flag, if supported)
    'beam_center_f',  # --beam-center-f (API-style flag, if supported)
    'beam_center_x',  # --beam-center-x (alternative naming)
    'beam_center_y',  # --beam-center-y (alternative naming)
    'Xclose',         # -Xclose (forces SAMPLE pivot, not MOSFLM relevant but explicit)
    'Yclose',         # -Yclose (forces SAMPLE pivot, not MOSFLM relevant but explicit)
]

# In argparse handling:
def determine_beam_center_source(args) -> str:
    """Determine if beam center is explicit or auto-calculated."""
    for flag in EXPLICIT_BEAM_CENTER_FLAGS:
        if hasattr(args, flag) and getattr(args, flag) is not None:
            return "explicit"
    return "auto"

# Apply to config construction:
detector_config = DetectorConfig(
    beam_center_s_mm=beam_center_s,
    beam_center_f_mm=beam_center_f,
    beam_center_source=determine_beam_center_source(args),
    # ... other fields
)
```

**Edge Case Handling:**

1. **Header Ingestion (`-img`/`-mask`):**
   - If beam center values are read from SMV headers, treat them as **explicit** (user provided the image file intending to use those coordinates).
   - Set `beam_center_source="explicit"` after header parsing.

2. **API Direct Construction:**
   - If users construct `DetectorConfig` directly in Python code with `beam_center_s_mm` and `beam_center_f_mm` arguments, they must also set `beam_center_source="explicit"` explicitly, or the default `"auto"` will apply.
   - **Documentation Requirement:** Add a note to `DetectorConfig` docstring explaining this requirement.

#### 2.2.3 Detector Model Layer (`src/nanobrag_torch/models/detector.py`)

**Conditional Offset Application:** Modify the `beam_center_s_pixels` and `beam_center_f_pixels` properties to check both convention **and** source:

```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """
    Compute beam center slow-axis position in pixels.

    For MOSFLM convention with auto-calculated beam centers, applies the
    normative +0.5 pixel offset per spec-a-core.md §72. Explicit user-provided
    beam centers are used as-is without adjustment.

    Returns:
        Beam center slow coordinate in pixels (tensor, preserves dtype/device).
    """
    base_pixels = self.config.beam_center_s_mm / self.config.pixel_size_mm

    # Apply MOSFLM +0.5 pixel offset ONLY for auto-calculated defaults
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == "auto"):
        # Preserve tensor operations for differentiability
        offset = torch.tensor(0.5, dtype=base_pixels.dtype, device=base_pixels.device)
        return base_pixels + offset

    return base_pixels

@property
def beam_center_f_pixels(self) -> torch.Tensor:
    """
    Compute beam center fast-axis position in pixels.

    For MOSFLM convention with auto-calculated beam centers, applies the
    normative +0.5 pixel offset per spec-a-core.md §72. Explicit user-provided
    beam centers are used as-is without adjustment.

    Returns:
        Beam center fast coordinate in pixels (tensor, preserves dtype/device).
    """
    base_pixels = self.config.beam_center_f_mm / self.config.pixel_size_mm

    # Apply MOSFLM +0.5 pixel offset ONLY for auto-calculated defaults
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == "auto"):
        # Preserve tensor operations for differentiability
        offset = torch.tensor(0.5, dtype=base_pixels.dtype, device=base_pixels.device)
        return base_pixels + offset

    return base_pixels
```

**Device/Dtype Neutrality:** The offset is created as a tensor with matching dtype/device to preserve:
- PyTorch gradient flow (differentiability requirement per arch.md §15)
- Device/dtype neutrality (per CLAUDE.md Core Implementation Rules §16)

**Alternative (Cleaner):** Extract offset application to a helper method:

```python
def _apply_mosflm_offset_if_needed(self, value_pixels: torch.Tensor) -> torch.Tensor:
    """Apply MOSFLM +0.5 pixel offset for auto-calculated beam centers only."""
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == "auto"):
        offset = torch.tensor(0.5, dtype=value_pixels.dtype, device=value_pixels.device)
        return value_pixels + offset
    return value_pixels

@property
def beam_center_s_pixels(self) -> torch.Tensor:
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm
    return self._apply_mosflm_offset_if_needed(base)

@property
def beam_center_f_pixels(self) -> torch.Tensor:
    base = self.config.beam_center_f_mm / self.config.pixel_size_mm
    return self._apply_mosflm_offset_if_needed(base)
```

---

## 3. Test Impact Matrix

### 3.1 Failing Test (Primary Target)

**Test:** `tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation`

**Current Status:** FAILING (applies unwanted +0.5 offset to explicit beam center)

**Expected Outcome After Fix:** PASSING (explicit beam center preserved exactly)

**Validation Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation
```

### 3.2 New Test Coverage Required

**Test File:** `tests/test_at_parallel_003.py` (extend existing module) or new `tests/test_beam_center_source.py`

**Test Cases:**

1. **test_mosflm_auto_calculated_applies_offset**
   - **Setup:** MOSFLM convention, `beam_center_source="auto"`, use detector size defaults for beam center
   - **Expectation:** Beam center in pixels = (mm / pixel_size_mm) + 0.5
   - **Rationale:** Validates +0.5 offset **is** applied for auto-calculated defaults

2. **test_mosflm_explicit_no_offset**
   - **Setup:** MOSFLM convention, `beam_center_source="explicit"`, user-provided beam center
   - **Expectation:** Beam center in pixels = (mm / pixel_size_mm) exactly (no +0.5 offset)
   - **Rationale:** Validates +0.5 offset is **not** applied for explicit coordinates

3. **test_xds_no_offset_regardless_of_source**
   - **Setup:** XDS convention, test both `beam_center_source="auto"` and `"explicit"`
   - **Expectation:** Beam center in pixels = (mm / pixel_size_mm) exactly for both cases (no offset)
   - **Rationale:** Validates non-MOSFLM conventions never apply the offset

4. **test_explicit_matches_default_value**
   - **Setup:** User provides explicit beam center that coincidentally equals the MOSFLM default formula
   - **Expectation:** No offset applied (explicit source wins over value heuristic)
   - **Rationale:** Edge case validation — ensures source flag overrides value-based heuristics

5. **test_header_ingestion_sets_explicit**
   - **Setup:** Ingest beam center from `-img` or `-mask` header
   - **Expectation:** `beam_center_source` is set to `"explicit"` automatically
   - **Rationale:** Validates CLI header ingestion logic

### 3.3 Existing Test Updates Required

**File:** `tests/test_detector_config.py`

**Changes:**
- Update `DetectorConfig` instantiations to include `beam_center_source` parameter where relevant
- Add assertions checking `beam_center_source` value after config construction
- Ensure tests for MOSFLM convention distinguish between auto and explicit cases

**Estimated Test File Changes:** 3-5 test functions requiring minor updates

---

## 4. Documentation Impact

### 4.1 Architecture Documentation

**File:** `docs/architecture/detector.md`

**Section:** §8.2 (Beam Center Mapping) and §9 (Pivot Modes)

**Required Updates:**
- Add description of `beam_center_source` attribute
- Clarify when +0.5 pixel offset is applied (auto-calculated only)
- Add example showing explicit vs auto-calculated behavior
- Cross-reference spec-a-core.md §72 and arch.md §ADR-03

### 4.2 Configuration Mapping Documentation

**File:** `docs/development/c_to_pytorch_config_map.md`

**Section:** Detector Parameters table, MOSFLM convention row

**Required Updates:**
- Add column or note explaining `beam_center_source` detection logic
- Document the 8 explicit beam center CLI flags
- Clarify header ingestion behavior (sets `"explicit"`)
- Add examples of CLI → config mapping for both auto and explicit cases

### 4.3 Findings Documentation

**File:** `docs/findings.md`

**Entry:** API-002 (pix0 overrides beam center)

**Required Updates:**
- Add cross-reference to CONVENTION-001 and DETECTOR-CONFIG-001
- Note interaction: if `pix0_vector` is provided, it overrides beam center **and** forces `beam_center_source="explicit"`
- Document precedence: `pix0_vector` > explicit beam center > auto-calculated defaults

---

## 5. Risk Assessment

### 5.1 Interacting Findings

**API-002:** `pix0_vector` parameter overrides beam center calculation
**Interaction:** If user provides both `pix0_vector` **and** explicit beam center, which takes precedence?
**Mitigation:** Document clear precedence order and add validation/warning when both are provided.

**CONVENTION-001:** CUSTOM convention disables implicit offsets
**Interaction:** CUSTOM behavior aligns with explicit beam center behavior (no implicit offsets)
**Mitigation:** Ensure CUSTOM convention tests also verify `beam_center_source` interaction.

### 5.2 Device/Dtype Neutrality

**Risk:** Creating offset tensor with hardcoded dtype could break device/dtype neutrality.

**Mitigation:**
- Always create offset tensor with `dtype=value.dtype, device=value.device`
- Add smoke tests for CPU/CUDA execution (per CLAUDE.md Core Implementation Rules §16)
- Run targeted validation on both devices before marking complete

**Validation Commands:**
```bash
# CPU
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_003.py

# GPU (if available)
env KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_003.py
```

### 5.3 Differentiability

**Risk:** Introducing non-differentiable logic (e.g., string comparisons) could break gradient flow.

**Mitigation:**
- The conditional logic `if beam_center_source == "auto"` is evaluated once during property access; the mathematical operations remain fully differentiable
- Offset tensor creation uses `torch.tensor()` which is differentiable
- Verification: Existing gradient tests (`tests/test_gradients.py`) should pass without modification
- Add explicit gradient check for beam center parameters if not already covered

### 5.4 Header Ingestion Edge Cases

**Risk:** Header ingestion from `-img`/`-mask` might not correctly set `beam_center_source="explicit"`.

**Mitigation:**
- Add explicit test for header ingestion path (test case #5 above)
- Document header ingestion logic in CLI code comments
- Validate with actual SMV header file in test suite

### 5.5 Backward Compatibility

**Risk:** Existing code constructing `DetectorConfig` without `beam_center_source` could break.

**Mitigation:**
- Default value `beam_center_source="auto"` ensures backward compatibility
- All direct `DetectorConfig` construction in codebase should be audited for correctness
- If explicit beam centers were intended, update call sites to include `beam_center_source="explicit"`

**Audit Strategy:** Search codebase for `DetectorConfig(` and review each instantiation.

---

## 6. Implementation Sequence

### 6.1 Phase C Tasks (per `plans/active/detector-config.md`)

**C1. Update configuration layer**
- Add `beam_center_source` field to `DetectorConfig` dataclass
- Add `BeamCenterSource` enum (or use Literal type)
- Set default value to `"auto"`

**C2. Adjust CLI parsing**
- Implement `determine_beam_center_source()` helper
- Update argparse handling to set `beam_center_source="explicit"` when beam center flags present
- Add header ingestion logic to set `"explicit"` for `-img`/`-mask` beam centers

**C3. Apply conditional offset in Detector**
- Modify `beam_center_s_pixels` property to check convention **and** source
- Modify `beam_center_f_pixels` property similarly
- Optionally extract helper method `_apply_mosflm_offset_if_needed()`
- Ensure tensor operations preserve dtype/device

**C4. Expand regression coverage**
- Add 5 new test cases to `tests/test_at_parallel_003.py` or new module
- Update existing tests in `tests/test_detector_config.py` to include `beam_center_source`
- Add CPU/GPU smoke tests if not already present

**C5. Targeted validation bundle**
- Run failing test: `pytest -v tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation`
- Run full detector config tests: `pytest -v tests/test_detector_config.py`
- Capture logs and metrics under `reports/2026-01-test-suite-triage/phase_m3/<STAMP>/mosflm_fix/`

**C6. Documentation sync**
- Update `docs/architecture/detector.md` §§8.2/9
- Update `docs/development/c_to_pytorch_config_map.md` Detector Parameters table
- Add cross-references to findings (API-002, CONVENTION-001)

**C7. Ledger & tracker update**
- Refresh `docs/fix_plan.md` `[DETECTOR-CONFIG-001]` entry with attempt log
- Update `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md` to mark C8 resolved

---

## 7. Exit Criteria

### 7.1 Implementation Complete

- [ ] `DetectorConfig` has `beam_center_source` field with default `"auto"`
- [ ] CLI parsing sets `beam_center_source="explicit"` when any of 8 beam center flags present
- [ ] Header ingestion sets `beam_center_source="explicit"` for `-img`/`-mask` beam centers
- [ ] `Detector.beam_center_s_pixels` applies +0.5 offset **only** for MOSFLM + auto
- [ ] `Detector.beam_center_f_pixels` applies +0.5 offset **only** for MOSFLM + auto
- [ ] Offset tensor creation preserves dtype/device neutrality

### 7.2 Test Coverage Complete

- [ ] `test_at_parallel_003.py::test_detector_offset_preservation` PASSES
- [ ] 5 new test cases added and passing:
  - [ ] `test_mosflm_auto_calculated_applies_offset`
  - [ ] `test_mosflm_explicit_no_offset`
  - [ ] `test_xds_no_offset_regardless_of_source`
  - [ ] `test_explicit_matches_default_value`
  - [ ] `test_header_ingestion_sets_explicit`
- [ ] Updated tests in `test_detector_config.py` passing
- [ ] CPU smoke test passing
- [ ] GPU smoke test passing (if CUDA available)

### 7.3 Validation Complete

- [ ] C-code parity validated for MOSFLM explicit beam center case (correlation ≥0.999)
- [ ] Gradient tests passing (verify `tests/test_gradients.py` unaffected)
- [ ] No regressions in Phase M0 chunked suite (46 failures → 45 or fewer)

### 7.4 Documentation Complete

- [ ] `docs/architecture/detector.md` updated with `beam_center_source` description
- [ ] `docs/development/c_to_pytorch_config_map.md` updated with detection logic
- [ ] `docs/findings.md` cross-references added (API-002 interaction)
- [ ] `docs/fix_plan.md` Attempts History updated with metrics/artifacts
- [ ] `remediation_tracker.md` C8 marked resolved with artifact paths

---

## 8. Artifact Expectations

### 8.1 Implementation Artifacts

- **Config changes:** `src/nanobrag_torch/config.py` (add `beam_center_source` field)
- **CLI changes:** `src/nanobrag_torch/__main__.py` (add detection logic)
- **Detector changes:** `src/nanobrag_torch/models/detector.py` (conditional offset logic)

### 8.2 Test Artifacts

- **New tests:** `tests/test_at_parallel_003.py` or `tests/test_beam_center_source.py` (5 new test cases)
- **Updated tests:** `tests/test_detector_config.py` (3-5 test function updates)
- **Test logs:** `reports/2026-01-test-suite-triage/phase_m3/<STAMP>/mosflm_fix/pytest.log`
- **Metrics:** `reports/2026-01-test-suite-triage/phase_m3/<STAMP>/mosflm_fix/summary.md`

### 8.3 Validation Artifacts

- **CPU validation:** pytest log showing test pass on CPU
- **GPU validation:** pytest log showing test pass on CUDA (if available)
- **Parity check:** C vs PyTorch correlation metrics for MOSFLM explicit beam center case
- **Gradient validation:** confirmation that existing gradient tests remain passing

### 8.4 Documentation Artifacts

- **detector.md updates:** Diff showing added `beam_center_source` description
- **c_to_pytorch_config_map.md updates:** Diff showing updated Detector Parameters table
- **fix_plan.md updates:** New Attempts History entry with metrics/next actions
- **remediation_tracker.md updates:** C8 status change to resolved

---

## 9. Spec/Arch Alignments

### 9.1 Normative Spec Citations

- **spec-a-core.md §72:** "Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel."
  - Interpretation: Formula applies to the default beam center mapping for MOSFLM convention
  - Does NOT mandate offset for explicit user inputs

- **spec-a-core.md §71:** "Default Xbeam = (detsize_s + pixel)/2, Ybeam = (detsize_f + pixel)/2."
  - Defines when beam centers are **auto-calculated** (when user does not provide explicit values)

### 9.2 Architecture Decision Alignment

- **arch.md §ADR-03:** "MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs."
  - Option A aligns by distinguishing explicit vs auto-calculated sources
  - CUSTOM convention behavior (no implicit offsets) matches explicit beam center behavior

- **arch.md §15 (Differentiability Guidelines):** All tensor operations must preserve gradient flow
  - Option A implementation uses `torch.tensor()` for offset creation (differentiable)
  - Conditional logic evaluated at property access (does not break computation graph)

- **CLAUDE.md Core Implementation Rules §16 (Device/Dtype Neutrality):**
  - Offset tensor created with matching dtype/device to preserve neutrality
  - Implementation tested on both CPU and CUDA

### 9.3 MOSFLM Convention Semantics

The MOSFLM convention uses a "shifted origin" coordinate system where pixel indices refer to the **leading edge/corner** of pixels rather than centers. The +0.5 pixel offset compensates for this convention when computing beam center coordinates.

**Key Insight:** This offset is a **coordinate system convention**, not a universal geometric transformation. When users provide explicit beam centers, they are already accounting for the coordinate system they intend to use. Applying an additional +0.5 offset would **double-shift** the coordinates, causing incorrect geometry.

---

## 10. Alternative Options Rejected

### 10.1 Option B: Value-Based Heuristic

**Approach:** Compare beam center values against computed defaults; if they match, apply offset.

**Rejection Rationale:**
1. **Fragility:** User could coincidentally provide a value matching the default formula → heuristic fails
2. **Unclear semantics:** Hard to reason about behavior without explicit flag
3. **Coupling:** Ties beam center logic to detector size logic (violates separation of concerns)
4. **Auditability:** Cannot trace decision path from CLI → config → detector without inspecting values

**Conclusion:** Option B trades implementation simplicity for semantic clarity and robustness. Option A is superior for maintainability and user-facing clarity.

### 10.2 Implicit Detection via CLI Flag Presence

**Approach:** Do not add config field; detect explicit beam centers in `Detector.__init__()` by checking if config values differ from computed defaults.

**Rejection Rationale:**
1. **Violation of dataclass immutability:** Detector should not modify config or infer missing information
2. **Non-reproducibility:** Same config object produces different results depending on construction context
3. **Testing complexity:** Cannot construct minimal test cases without also constructing full CLI parsing context

**Conclusion:** Detection logic belongs in CLI layer (where user intent is clear), not in model layer (where only config is available).

---

## 11. Glossary

**Auto-calculated beam center:** Beam center derived from detector size defaults using convention-specific formulas (e.g., MOSFLM: `Xbeam = (detsize_s + pixel)/2`).

**Explicit beam center:** Beam center explicitly provided by user via CLI flags (`-Xbeam`, `-Ybeam`, etc.), API parameters, or header ingestion (`-img`/`-mask`).

**MOSFLM +0.5 pixel offset:** Convention-specific adjustment to beam center pixel coordinates: `Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel`. Applied to compensate for MOSFLM's "leading-edge" pixel indexing convention.

**beam_center_source:** New `DetectorConfig` attribute (string literal: `"auto"` or `"explicit"`) distinguishing the origin of beam center values.

**Convention:** Detector coordinate system standard (MOSFLM, XDS, DIALS, ADXV, DENZO, CUSTOM) defining basis vectors, pivot modes, and beam center mapping formulas.

---

## 12. References

### 12.1 Primary Documents

- **Specification:** `specs/spec-a-core.md` §§68-73 (Geometry & Conventions → MOSFLM)
- **Architecture:** `arch.md` §ADR-03 (Beam-center Mapping and +0.5 pixel Offsets)
- **Plan:** `plans/active/detector-config.md` (Phase B tasks B1-B4, Phase C tasks C1-C7)
- **Evidence:** `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md`

### 12.2 Supporting Documents

- **Testing Strategy:** `docs/development/testing_strategy.md` (Tier 1 translation correctness)
- **Config Mapping:** `docs/development/c_to_pytorch_config_map.md` (MOSFLM convention implicit rules)
- **Detector Architecture:** `docs/architecture/detector.md` (§§8.2 & 9)
- **Findings:** `docs/findings.md` (API-002, CONVENTION-001)

### 12.3 Test Files

- **Primary Failing Test:** `tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation`
- **Detector Config Tests:** `tests/test_detector_config.py`
- **Gradient Tests:** `tests/test_gradients.py` (verification of differentiability preservation)

---

## 13. Approval & Next Steps

### 13.1 Phase B Completion

- [x] **B1:** Option A vs Option B comparison documented
- [x] **B2:** Config/CLI propagation logic specified with code examples
- [x] **B3:** Test impact matrix completed (5 new tests, 3-5 existing test updates)
- [x] **B4:** Risk assessment documented (API-002/CONVENTION-001 interactions, device/dtype/differentiability neutrality)

**Phase B Status:** ✅ **COMPLETE** — Design ratified, ready for Phase C implementation

### 13.2 Phase C Readiness Checklist

- [ ] Supervisor approval obtained for Phase C implementation
- [ ] `input.md` updated with Phase C "Do Now" directive
- [ ] Engineer (ralph) assigned to Phase C tasks C1-C7
- [ ] Target STAMP for Phase C artifacts determined

### 13.3 Expected Timeline

- **Phase C Implementation:** 2-3 hours (code + tests)
- **Phase C Validation:** 30-60 minutes (targeted tests + CPU/GPU smoke)
- **Phase C Documentation:** 30-60 minutes (3 doc files + fix_plan/tracker updates)
- **Total Estimated Effort:** 3-5 hours end-to-end

---

**Design Document Status:** ✅ **RATIFIED**
**Next Action:** Await supervisor approval for Phase C implementation handoff
**Blocking:** None — all Phase B prerequisites satisfied
**Ready for Implementation:** YES
