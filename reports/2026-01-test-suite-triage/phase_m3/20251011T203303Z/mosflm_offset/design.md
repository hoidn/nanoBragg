# DETECTOR-CONFIG-001: Option A Remediation Design

**STAMP:** 20251011T203303Z
**Phase:** M3 Phase B (Behavior Contract & Blueprint Refresh)
**Status:** Design Complete — Ready for Phase C Implementation
**Design Rationale:** Explicit beam center source tracking (Option A) chosen over heuristic-based detection (Option B)

---

## Executive Summary

This design document specifies **Option A** remediation for the MOSFLM beam center +0.5 pixel offset misapplication bug (C8 cluster). The current implementation incorrectly applies the MOSFLM +0.5 pixel offset to ALL beam center coordinates, including explicit user-provided values. Per spec-a-core.md §72 and arch.md §ADR-03, the offset should ONLY be applied to auto-calculated beam centers.

**Chosen Approach:** Add `beam_center_source: Literal["auto", "explicit"]` attribute to `DetectorConfig` to explicitly track whether beam center values originated from user input or were auto-calculated from detector geometry. This provides clear semantic distinction, maintainability, and auditability.

**Rejection of Option B:** Heuristic-based detection (comparing beam center values against computed defaults) is fragile, couples unrelated logic, and creates ambiguity when users coincidentally provide default-matching values.

---

## 1. Configuration Layer Changes

### 1.1 DetectorConfig Dataclass (`src/nanobrag_torch/config.py`)

**Add new field:**

```python
from typing import Literal

@dataclass
class DetectorConfig:
    # Existing fields...
    beam_center_s_mm: float
    beam_center_f_mm: float

    # NEW FIELD
    beam_center_source: Literal["auto", "explicit"] = "auto"

    # ... other fields
```

**Rationale:**
- `Literal` type provides type safety and restricts values to valid options
- Default `"auto"` maintains backward compatibility for programmatic instantiations
- Explicit semantic distinction makes config behavior self-documenting

**Device/Dtype Neutrality:** This field is a string literal and does not interact with tensor operations; no device/dtype concerns.

**Differentiability:** This field is non-differentiable metadata; does not affect gradient flow through numeric parameters.

---

## 2. CLI Parsing Logic (`src/nanobrag_torch/__main__.py`)

### 2.1 Detection of Explicit Beam Center Inputs

**Add detection logic after parsing arguments:**

```python
def main():
    args = parser.parse_args()

    # ... existing config setup ...

    # Determine beam_center_source based on CLI flags
    beam_center_source = "auto"  # Default

    # Eight explicit beam center flags (any one triggers "explicit" mode)
    explicit_flags = [
        args.beam_center_s is not None,      # --beam_center_s
        args.beam_center_f is not None,      # --beam_center_f
        args.Xbeam is not None,              # -Xbeam (MOSFLM/DENZO)
        args.Ybeam is not None,              # -Ybeam (MOSFLM/DENZO)
        args.Xclose is not None,             # -Xclose (XDS SAMPLE pivot)
        args.Yclose is not None,             # -Yclose (XDS SAMPLE pivot)
        args.ORGX is not None,               # -ORGX (XDS pixels)
        args.ORGY is not None,               # -ORGY (XDS pixels)
    ]

    if any(explicit_flags):
        beam_center_source = "explicit"

    # Pass to DetectorConfig
    detector_config = DetectorConfig(
        beam_center_s_mm=computed_s,
        beam_center_f_mm=computed_f,
        beam_center_source=beam_center_source,  # NEW
        # ... other fields
    )
```

**Rationale:**
- Captures all eight CLI beam center specification methods
- Clear boolean logic makes intent explicit
- Single source of truth for explicit vs auto determination

**Edge Cases Handled:**
- Multiple explicit flags provided → all trigger "explicit" (any-of logic)
- Convention-specific defaults (MOSFLM vs XDS vs DIALS) → handled by "auto" when no explicit flags present
- Header ingestion (see §2.2 below)

---

### 2.2 Header Ingestion Handling (`-img` / `-mask`)

**Update header ingestion to set source appropriately:**

```python
def ingest_header(header_dict, current_config):
    """Extract beam center from SMV header and mark as explicit."""

    if "BEAM_CENTER_X" in header_dict or "BEAM_CENTER_Y" in header_dict:
        # User provided an image with explicit beam center metadata
        current_config.beam_center_source = "explicit"

    # Similarly for MOSFLM_CENTER_X/Y, DIALS_ORIGIN, XDS_ORGX/Y
    convention_keys = [
        "MOSFLM_CENTER_X", "MOSFLM_CENTER_Y",
        "DIALS_ORIGIN",
        "XDS_ORGX", "XDS_ORGY",
    ]

    if any(key in header_dict for key in convention_keys):
        current_config.beam_center_source = "explicit"

    return current_config
```

**Rationale:**
- Headers with beam center metadata represent explicit user geometry
- Preserves parity with C-code header precedence rules (last file read wins)
- Prevents auto-calculated offsets from corrupting header-derived geometry

---

## 3. Detector Model Logic (`src/nanobrag_torch/models/detector.py`)

### 3.1 Conditional Offset in Beam Center Properties

**Modify beam center pixel conversion properties:**

```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """
    Convert beam center slow coordinate from mm to pixels.

    MOSFLM Convention Offset:
    Per spec-a-core.md §72, MOSFLM adds +0.5 pixel offset to AUTO-CALCULATED
    beam centers only. Explicit user-provided centers must not be adjusted.
    """
    base_pixels = self.config.beam_center_s_mm / self.config.pixel_size_mm

    # Apply +0.5 offset ONLY for MOSFLM convention with auto-calculated centers
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == "auto"):
        return base_pixels + 0.5

    return base_pixels

@property
def beam_center_f_pixels(self) -> torch.Tensor:
    """
    Convert beam center fast coordinate from mm to pixels.

    MOSFLM Convention Offset:
    Per spec-a-core.md §72, MOSFLM adds +0.5 pixel offset to AUTO-CALCULATED
    beam centers only. Explicit user-provided centers must not be adjusted.
    """
    base_pixels = self.config.beam_center_f_mm / self.config.pixel_size_mm

    # Apply +0.5 offset ONLY for MOSFLM convention with auto-calculated centers
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == "auto"):
        return base_pixels + 0.5

    return base_pixels
```

**Rationale:**
- Properties maintain @property pattern for gradient flow compatibility
- Clear guard conditions make logic auditable
- Docstrings cite spec for future maintainers
- Consistent tensor return types preserve device/dtype neutrality

**Device/Dtype Neutrality:**
- `self.config.beam_center_s_mm` and `pixel_size_mm` already respect caller's device/dtype
- Scalar addition (`+ 0.5`) broadcasts correctly to tensor dtype
- No explicit `.to()` calls or device transfers

**Differentiability:**
- Properties recompute from base config tensors on each access (no caching of derived values)
- Conditional logic does not break gradient flow (torch supports control flow in autograd)
- `beam_center_source` is non-differentiable metadata (string literal) but does not participate in numeric computation graph

---

### 3.2 Validation and Debugging Support

**Add validation in `_is_default_config()` if present:**

```python
def _is_default_config(self) -> bool:
    """
    Check if detector is using default configuration.

    Note: This method does NOT determine beam_center_source; that is set
    explicitly by CLI parsing. This method is for diagnostic purposes only.
    """
    # Existing checks...

    # Log for debugging (not a decision point)
    if self.config.beam_center_source == "explicit":
        # User provided explicit beam center; offset logic already handled
        pass

    return ...
```

**Rationale:**
- Decouples validation from offset application (separation of concerns)
- Prevents future maintainers from introducing Option B heuristics
- Logging aids post-implementation debugging

---

## 4. Test Impact Matrix

### 4.1 Existing Tests Requiring Updates

| Test File | Test Name | Change Required | Rationale |
|-----------|-----------|-----------------|-----------|
| `tests/test_detector_config.py` | `test_default_initialization` | **FIX EXPECTED** | Currently expects 513.0 pixels (with offset); should now expect 512.5 pixels (auto mode, offset applied correctly) |
| `tests/test_detector_config.py` | `test_custom_config_initialization` | **FIX EXPECTED** | Currently expects 1024.5 pixels; should now expect 1024.0 pixels (auto mode, offset applied correctly) |
| `tests/test_at_parallel_003.py` | `test_detector_offset_preservation` | **WILL PASS** | Currently FAILS; will pass after fix (explicit beam center preserved at 512.5 pixels without offset) |
| `tests/test_at_parallel_002.py` | Pixel size independence tests | **VERIFY PASS** | Should remain passing; may need `beam_center_source` parameter added to DetectorConfig instantiations |
| `tests/test_beam_center_offset.py` | All MOSFLM tests | **UPDATE FIXTURES** | Add `beam_center_source="auto"` to auto-calculated test cases; `"explicit"` to user-provided cases |

---

### 4.2 New Test Cases Required

**File:** `tests/test_at_parallel_003.py` (expand existing)

1. **`test_mosflm_auto_beam_center_applies_offset`**
   - **Setup:** MOSFLM convention, no explicit beam center flags, detector size 1024×1024, pixel 0.1mm
   - **Expectation:** `beam_center_s_pixels == 512.5` (512.0 + 0.5 offset)
   - **Purpose:** Verify +0.5 offset IS applied for auto-calculated centers

2. **`test_mosflm_explicit_beam_center_no_offset`**
   - **Setup:** MOSFLM convention, `beam_center_s=512.5` mm (explicit), pixel 0.1mm
   - **Expectation:** `beam_center_s_pixels == 512.5` (no additional offset)
   - **Purpose:** Verify +0.5 offset is NOT applied for explicit centers

3. **`test_non_mosflm_no_offset_regardless_of_source`**
   - **Setup:** XDS convention, both auto and explicit beam centers
   - **Expectation:** No +0.5 offset for either case
   - **Purpose:** Verify offset is MOSFLM-specific

4. **`test_header_ingestion_marks_explicit`**
   - **Setup:** Load `-img` with `BEAM_CENTER_X/Y` in header
   - **Expectation:** `beam_center_source == "explicit"`, no offset applied
   - **Purpose:** Verify header ingestion correctly marks source

5. **`test_explicit_matches_default_still_no_offset`**
   - **Setup:** MOSFLM convention, user explicitly provides beam center that happens to match default formula
   - **Expectation:** No offset applied (explicit source overrides heuristic)
   - **Purpose:** Demonstrates why Option B (heuristic) would fail

---

## 5. Documentation Impact

### 5.1 Files Requiring Updates

| Document | Section | Change Description |
|----------|---------|-------------------|
| `docs/architecture/detector.md` | §8.2 Beam Center Mapping | Add subsection "Auto vs Explicit Beam Centers"; document `beam_center_source` field and offset logic |
| `docs/architecture/detector.md` | §9 Detector Configuration | Add `beam_center_source` to configuration table with description |
| `docs/development/c_to_pytorch_config_map.md` | Detector Parameters table | Add row for `beam_center_source` mapping; note 8 CLI flags that trigger "explicit" |
| `docs/findings.md` | API-002 (pix0 overrides) | Add cross-reference note: "See DETECTOR-CONFIG-001 for beam_center_source interaction" |
| `docs/findings.md` | CONVENTION-001 (CUSTOM) | Add note: "CUSTOM convention uses `beam_center_source='auto'` by default (no +0.5 offset per ADR-03)" |

---

### 5.2 Quick Reference Table Addition

**Add to `docs/architecture/detector.md` §8.2:**

> #### Auto vs Explicit Beam Centers
>
> | Scenario | `beam_center_source` | MOSFLM +0.5 Offset? | Examples |
> |----------|---------------------|---------------------|----------|
> | User provides `-Xbeam 51.2` | `"explicit"` | ❌ No | CLI flags, header ingestion |
> | Defaults from detector size | `"auto"` | ✅ Yes | `(detsize_s+pixel)/2` formula |
> | XDS convention (any source) | N/A | ❌ No | XDS never uses +0.5 offset |

---

## 6. Risk Assessment

### 6.1 API-002 Interaction (pix0 overrides beam center)

**Finding:** `pix0_vector` can override beam center calculations in certain code paths.

**Risk:** If `pix0_vector` is provided alongside explicit beam center flags, which takes precedence?

**Mitigation:**
- Document precedence: `pix0_vector` (if provided) → explicit beam center → auto-calculated
- Add validation warning if both `pix0_vector` and explicit beam center are provided
- Test case: `test_pix0_overrides_explicit_beam_center`

---

### 6.2 CONVENTION-001 Interaction (CUSTOM convention)

**Finding:** CUSTOM convention behavior is underspecified in the spec for beam center offsets.

**Risk:** Ambiguity in whether CUSTOM should apply MOSFLM-like offsets.

**Mitigation:**
- Per ADR-03, CUSTOM convention uses `beam_center_source="auto"` but does NOT apply +0.5 offset
- Update ADR-03 if clarification needed
- Test case: `test_custom_convention_no_offset`

---

### 6.3 Header Ingestion Precedence (last file wins)

**Finding:** When both `-img` and `-mask` are provided, last file wins for shared keys.

**Risk:** Conflicting `beam_center_source` values if headers disagree.

**Mitigation:**
- Header ingestion always sets `beam_center_source="explicit"` (conservative)
- If no beam center keys in headers, preserve existing `beam_center_source` from CLI
- Test case: `test_header_precedence_with_explicit_flag`

---

### 6.4 Backward Compatibility

**Risk:** Existing code that instantiates `DetectorConfig` without `beam_center_source` may break.

**Mitigation:**
- Default value `"auto"` maintains current behavior for programmatic use
- CLI parsing explicitly sets the field (no ambiguity for command-line users)
- All unit tests updated to explicitly pass `beam_center_source`

**Validation:** Run full test suite after fix; expect 0 new failures, 3-5 fixes (C8 cluster + detector_config tests).

---

### 6.5 PyTorch Device/Dtype/Differentiability Neutrality

**Assessment:**
- ✅ `beam_center_source` is a string literal (non-tensor metadata); no device/dtype concerns
- ✅ Properties recompute from config tensors; gradient flow preserved
- ✅ Conditional logic (`if convention == MOSFLM`) does not break autograd
- ✅ Scalar addition (`+ 0.5`) broadcasts to tensor dtype correctly
- ✅ No `.item()`, `.detach()`, or explicit device transfers introduced

**Verification:** Run `tests/test_gradients.py` gradient checks; expect all passing.

---

## 7. Acceptance Criteria

### 7.1 Implementation Complete

- [ ] `DetectorConfig` includes `beam_center_source` field (default `"auto"`)
- [ ] CLI parsing detects all 8 explicit beam center flags
- [ ] Header ingestion marks beam centers as `"explicit"` when metadata present
- [ ] `Detector.beam_center_s_pixels` and `beam_center_f_pixels` apply +0.5 offset conditionally
- [ ] Docstrings cite spec-a-core.md §72 and arch.md §ADR-03

---

### 7.2 Test Coverage

- [ ] `test_at_parallel_003.py::test_detector_offset_preservation` PASSES (was FAILING)
- [ ] 5 new test cases added (auto offset, explicit no-offset, non-MOSFLM, header, edge case)
- [ ] Existing tests in `test_detector_config.py` updated with correct expectations
- [ ] Existing tests in `test_at_parallel_002.py` remain passing (pixel size independence preserved)
- [ ] No regressions in full test suite (Phase M rerun ≤ 31 failures baseline)

---

### 7.3 C-Code Parity

- [ ] C-code reference run with MOSFLM + explicit beam center (e.g., `-Xbeam 51.2 -Ybeam 51.2`)
- [ ] PyTorch run with equivalent config (`beam_center_source="explicit"`)
- [ ] Correlation ≥0.9999 for final images
- [ ] Beam center pixel values match exactly (no +0.5 difference)

**Parity Command:**
```bash
# C reference
./golden_suite_generator/nanoBragg -cell 100 100 100 90 90 90 -default_F 100 \
  -lambda 1.0 -distance 100 -detpixels 256 -Xbeam 12.8 -Ybeam 12.8 \
  -floatfile /tmp/c_output.bin

# PyTorch
nanoBragg -cell 100 100 100 90 90 90 -default_F 100 \
  -lambda 1.0 -distance 100 -detpixels 256 -Xbeam 12.8 -Ybeam 12.8 \
  -floatfile /tmp/py_output.bin

# Comparison
python scripts/compare_float_images.py /tmp/c_output.bin /tmp/py_output.bin 256 256
```

---

### 7.4 Documentation Synced

- [ ] `docs/architecture/detector.md` §8.2 and §9 updated
- [ ] `docs/development/c_to_pytorch_config_map.md` includes `beam_center_source` row
- [ ] `docs/findings.md` cross-references added to API-002 and CONVENTION-001
- [ ] Quick reference table added to detector.md

---

## 8. Implementation Sequence (Phase C Tasks)

**Phase C Tasks per `plans/active/detector-config.md`:**

| Task | Files | Lines/LOC | Priority | Est. Time |
|------|-------|-----------|----------|-----------|
| C1: Update configuration layer | `config.py` | +3 | P1 | 15 min |
| C2: Adjust CLI parsing | `__main__.py` | +15 | P1 | 30 min |
| C3: Apply conditional offset in Detector | `detector.py` | +8 (2 properties) | P1 | 30 min |
| C4: Expand regression coverage | `test_at_parallel_003.py`, `test_detector_config.py` | +100 | P1 | 60 min |
| C5: Targeted validation bundle | Run pytest selectors | N/A | P1 | 15 min |
| C6: Documentation sync | `detector.md`, `c_to_pytorch_config_map.md`, `findings.md` | +30 | P2 | 30 min |
| C7: Ledger & tracker update | `fix_plan.md`, `remediation_tracker.md` | +20 | P2 | 15 min |

**Total Estimated Time:** 2 hours 45 minutes (core implementation: 1h 15m; testing: 1h; docs: 30m)

---

## 9. Next Actions (Phase C Handoff)

1. **Supervisor approval:** input.md should confirm design ratified and authorize Phase C
2. **Implementation:** Ralph executes tasks C1-C3 (code changes)
3. **Targeted validation:** Run selectors from C5 before full suite rerun
4. **Documentation:** Update docs per C6 after code changes proven
5. **Full suite rerun:** Phase D chunked rerun to capture net delta vs baseline

---

## 10. References

### 10.1 Normative Spec Statements

**spec-a-core.md §72 (MOSFLM Convention):**
> "MOSFLM applies a +0.5 pixel offset to beam center calculations when deriving from detector geometry defaults. Explicit user-provided beam centers must not be adjusted."

**arch.md §ADR-03 (Beam-center Mapping):**
> "MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs."

---

### 10.2 Evidence Artifacts

- **Phase L Analysis:** `reports/2026-01-test-suite-triage/phase_l/20251011T104618Z/detector_config/analysis.md`
- **Phase M3 Summary:** `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md`
- **Plan Reference:** `plans/active/detector-config.md`
- **Fix Plan Entry:** `docs/fix_plan.md` §[DETECTOR-CONFIG-001]

---

### 10.3 Related Findings

- **API-002:** `pix0_vector` overrides beam center (docs/findings.md)
- **CONVENTION-001:** CUSTOM convention behavior underspecified (docs/findings.md)

---

## 11. Decision Rationale: Why Option A Over Option B

### 11.1 Option B Weaknesses

**Heuristic Fragility:**
- What if user explicitly provides a value that happens to match the default formula?
  - Example: `-Xbeam 51.2` on 1024×1024 detector with 0.1mm pixels → matches default
  - Option B would incorrectly apply offset; Option A correctly preserves explicit value

**Coupling:**
- Ties beam center logic to detector size calculations
- Makes offset behavior dependent on multiple config fields (beam center + detsize + pixel size)
- Harder to reason about and debug

**Future Maintenance:**
- What if default formulas change (e.g., ADXV vs MOSFLM)?
- Heuristic would need updates across multiple conventions

---

### 11.2 Option A Strengths

**Explicit Semantics:**
- Single field (`beam_center_source`) clearly documents intent
- No ambiguity for users or maintainers

**Separation of Concerns:**
- CLI parsing sets source flag (input layer)
- Detector properties apply offset conditionally (computation layer)
- Configuration carries metadata (data layer)

**Testability:**
- Easy to write deterministic tests (control `beam_center_source` directly)
- No edge cases from coincidental value matches

**Future-Proof:**
- Adding new conventions only requires spec-ing their offset behavior
- No heuristic updates across codebase

---

## 12. Summary

**Design Status:** Complete and ready for implementation.

**Key Decision:** Option A (`beam_center_source` explicit tracking) chosen for clarity, maintainability, and correctness.

**Implementation Scope:** 3 files (config, CLI, detector), ~26 lines of code, 5 new tests, 3 doc files.

**Expected Outcome:** C8 cluster resolved (1 failure → 0), C↔PyTorch parity restored for MOSFLM explicit beam centers, no regressions.

**Next Phase:** Phase C implementation per tasks C1-C7 in `plans/active/detector-config.md`.

---

**Design Approved:** [ ] Supervisor
**Phase C Authorized:** [ ] input.md Do Now
**Implementation Owner:** ralph
**Target Completion:** 2026-01-22 (Phase C + D rerun)
