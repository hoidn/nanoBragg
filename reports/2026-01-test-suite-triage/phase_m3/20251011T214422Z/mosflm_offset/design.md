# MOSFLM Beam Center Offset Remediation Design (Option A)

**Initiative:** DETECTOR-CONFIG-001 — Detector defaults audit  
**Cluster:** C8 (MOSFLM Beam Center Offset)  
**STAMP:** 20251011T214422Z  
**Phase:** M3 Design Document  
**Status:** Option A — Beam Center Source Tracking (RECOMMENDED)

---

## Executive Summary

This design document specifies the **Option A remediation** for C8 cluster failures (MOSFLM beam center offset misapplication). The implementation tracks beam center **provenance** via a `beam_center_source` flag to distinguish auto-calculated defaults (which require the MOSFLM +0.5 pixel offset per spec) from explicit user-provided values (which must NOT be adjusted).

**Normative References:**
- **specs/spec-a-core.md §72:** "Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel. Pivot = BEAM."
- **arch.md §ADR-03:** "MOSFLM applies +0.5 pixel offset to beam center calculations when deriving from detector geometry defaults. Explicit user-provided beam centers must not be adjusted."

**Key Insight:** The +0.5 pixel offset is a **convention-specific default behavior**, NOT a mandatory transformation for all coordinates. User-provided coordinates must pass through unchanged.

---

## 1. Configuration Layer Changes

### 1.1 Add BeamCenterSource Enum

**Location:** `src/nanobrag_torch/config.py`

**Implementation:**

```python
from enum import Enum

class BeamCenterSource(Enum):
    """Tracks provenance of beam center values for convention-specific offset application."""
    AUTO = "auto"      # Beam center auto-calculated from detector geometry defaults
    EXPLICIT = "explicit"  # Beam center explicitly provided by user (CLI, API, or header)
```

**Rationale:** Type-safe enum prevents string typos and provides clear semantic distinction.

### 1.2 Extend DetectorConfig

**Location:** `src/nanobrag_torch/config.py` (DetectorConfig dataclass)

**Changes:**

```python
@dataclass
class DetectorConfig:
    # ... existing fields ...
    
    # NEW FIELD (add after beam_center_f_mm):
    beam_center_source: BeamCenterSource = BeamCenterSource.AUTO
    """Provenance of beam center coordinates.
    
    AUTO: Beam centers derived from detector geometry defaults.
          MOSFLM convention applies +0.5 pixel offset per spec-a-core.md §72.
          
    EXPLICIT: Beam centers explicitly provided by user via CLI flags, API call,
              or header ingestion. NO convention-specific adjustments applied.
    
    This distinction is critical for spec compliance: MOSFLM offset applies ONLY
    to auto-calculated defaults, not user-provided coordinates.
    """
```

**Backward Compatibility:** Default value `AUTO` preserves existing behavior for code that doesn't explicitly set the field.

---

## 2. CLI Parsing Layer Changes

### 2.1 Detect Explicit Beam Center Flags

**Location:** `src/nanobrag_torch/__main__.py` (argument parsing section)

**Detection Logic:** The following CLI flags indicate **explicit** beam center input:

| Flag | Description | Category |
|------|-------------|----------|
| `--beam_center_s <val>` | Direct API-style slow-axis coordinate | Direct |
| `--beam_center_f <val>` | Direct API-style fast-axis coordinate | Direct |
| `-Xbeam <val>` | MOSFLM/DENZO X coordinate (maps to slow) | MOSFLM |
| `-Ybeam <val>` | MOSFLM/DENZO Y coordinate (maps to fast) | MOSFLM |
| `-Xclose <val>` | XDS X close distance (SAMPLE pivot) | XDS |
| `-Yclose <val>` | XDS Y close distance (SAMPLE pivot) | XDS |
| `-ORGX <val>` | XDS origin X in pixels | XDS |
| `-ORGY <val>` | XDS origin Y in pixels | XDS |

**Implementation:**

```python
def determine_beam_center_source(args) -> BeamCenterSource:
    """Determine if beam center was explicitly provided or should use defaults.
    
    Returns BeamCenterSource.EXPLICIT if any explicit beam center flag is present,
    otherwise BeamCenterSource.AUTO for convention-dependent defaults.
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
    ]
    
    if any(explicit_flags):
        return BeamCenterSource.EXPLICIT
    else:
        return BeamCenterSource.AUTO

# In main config construction:
detector_config = DetectorConfig(
    # ... existing parameters ...
    beam_center_source=determine_beam_center_source(args),
)
```

**Edge Case:** If **both** explicit and default values are mixed (unlikely but possible), explicit flag presence takes precedence and sets `EXPLICIT`.

### 2.2 Header Ingestion Handling

**Location:** `src/nanobrag_torch/__main__.py` (header parsing section)

**Special Case:** Header ingestion via `-img` or `-mask` files:

```python
def parse_smv_header(header_dict: dict, is_mask: bool) -> dict:
    """Parse SMV header and extract beam center if present."""
    config_updates = {}
    
    # ... existing header parsing ...
    
    # Track if header provided beam center
    if 'BEAM_CENTER_X' in header_dict or 'BEAM_CENTER_Y' in header_dict:
        config_updates['beam_center_source'] = BeamCenterSource.EXPLICIT
    
    return config_updates

# Apply header updates after CLI parsing:
if args.img or args.mask:
    header_updates = parse_smv_header(header_content, is_mask=bool(args.mask))
    if 'beam_center_source' in header_updates:
        detector_config.beam_center_source = header_updates['beam_center_source']
```

**Rationale:** Headers containing beam center coordinates are treated as explicit user input, not defaults.

---

## 3. Detector Layer Changes

### 3.1 Conditional Offset Application

**Location:** `src/nanobrag_torch/models/detector.py` (beam center pixel conversion properties)

**Current Implementation (INCORRECT):**

```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """Convert beam center slow coordinate from mm to pixels."""
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm
    
    # PROBLEM: Always applies offset for MOSFLM
    if self.config.detector_convention == DetectorConvention.MOSFLM:
        return base + 0.5
    return base
```

**Corrected Implementation:**

```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """Convert beam center slow coordinate from mm to pixels.
    
    Applies MOSFLM +0.5 pixel offset ONLY when:
    1. Convention is MOSFLM, AND
    2. Beam center source is AUTO (convention defaults)
    
    Explicit user-provided beam centers pass through unchanged per spec-a-core.md §72.
    """
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm
    
    # Apply MOSFLM offset ONLY to auto-calculated defaults
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == BeamCenterSource.AUTO):
        return base + 0.5
    
    return base

@property
def beam_center_f_pixels(self) -> torch.Tensor:
    """Convert beam center fast coordinate from mm to pixels.
    
    Applies MOSFLM +0.5 pixel offset ONLY when:
    1. Convention is MOSFLM, AND
    2. Beam center source is AUTO (convention defaults)
    
    Explicit user-provided beam centers pass through unchanged per spec-a-core.md §72.
    """
    base = self.config.beam_center_f_mm / self.config.pixel_size_mm
    
    # Apply MOSFLM offset ONLY to auto-calculated defaults
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == BeamCenterSource.AUTO):
        return base + 0.5
    
    return base
```

**Key Change:** Two-condition guard ensures offset applies ONLY when both:
1. Convention is MOSFLM (spec requirement)
2. Source is AUTO (distinction this fix introduces)

---

## 4. Test Impact Matrix

### 4.1 Existing Tests Requiring Updates

| Test File | Change Required | Rationale |
|-----------|-----------------|-----------|
| `tests/test_detector_config.py` | Update assertions expecting +0.5 offset | Tests currently validate incorrect behavior; must distinguish auto vs explicit cases |
| `tests/test_at_parallel_003.py` | Should PASS after fix | Currently fails due to unwanted offset on explicit coordinates |
| `tests/test_beam_center_offset.py` | Add if missing; expand coverage | Need comprehensive MOSFLM offset validation |

### 4.2 New Test Cases Required

**Test File:** `tests/test_beam_center_source.py` (NEW)

**Coverage:**

1. **MOSFLM Auto-Calculated Test**
   ```python
   def test_mosflm_auto_beam_center():
       """Verify MOSFLM +0.5 offset IS applied to auto-calculated defaults."""
       config = DetectorConfig(
           detector_convention=DetectorConvention.MOSFLM,
           beam_center_s_mm=12.8,  # 128 pixels at 0.1mm/pixel
           beam_center_f_mm=12.8,
           beam_center_source=BeamCenterSource.AUTO,  # Explicit AUTO
           pixel_size_mm=0.1,
       )
       detector = Detector(config)
       # Expect 128.0 + 0.5 = 128.5 pixels
       assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(128.5))
       assert torch.allclose(detector.beam_center_f_pixels, torch.tensor(128.5))
   ```

2. **MOSFLM Explicit Beam Center Test**
   ```python
   def test_mosflm_explicit_beam_center():
       """Verify MOSFLM +0.5 offset is NOT applied to explicit user coordinates."""
       config = DetectorConfig(
           detector_convention=DetectorConvention.MOSFLM,
           beam_center_s_mm=12.8,  # 128 pixels at 0.1mm/pixel
           beam_center_f_mm=12.8,
           beam_center_source=BeamCenterSource.EXPLICIT,  # User-provided
           pixel_size_mm=0.1,
       )
       detector = Detector(config)
       # Expect exact 128.0 pixels (no offset)
       assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(128.0))
       assert torch.allclose(detector.beam_center_f_pixels, torch.tensor(128.0))
   ```

3. **Non-MOSFLM Convention Test**
   ```python
   def test_non_mosflm_no_offset():
       """Verify no offset applied for XDS/DIALS regardless of source."""
       for convention in [DetectorConvention.XDS, DetectorConvention.DIALS, DetectorConvention.CUSTOM]:
           for source in [BeamCenterSource.AUTO, BeamCenterSource.EXPLICIT]:
               config = DetectorConfig(
                   detector_convention=convention,
                   beam_center_s_mm=12.8,
                   beam_center_f_mm=12.8,
                   beam_center_source=source,
                   pixel_size_mm=0.1,
               )
               detector = Detector(config)
               # Expect exact 128.0 pixels (no MOSFLM offset for other conventions)
               assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(128.0))
               assert torch.allclose(detector.beam_center_f_pixels, torch.tensor(128.0))
   ```

4. **CLI Detection Test**
   ```python
   def test_cli_explicit_detection():
       """Verify CLI parsing correctly detects explicit beam center flags."""
       # Simulate argparse namespace
       args_explicit = argparse.Namespace(Xbeam=51.2, Ybeam=51.2, ...)
       assert determine_beam_center_source(args_explicit) == BeamCenterSource.EXPLICIT
       
       args_auto = argparse.Namespace(Xbeam=None, Ybeam=None, ...)
       assert determine_beam_center_source(args_auto) == BeamCenterSource.AUTO
   ```

5. **Edge Case: Default-Matching Value**
   ```python
   def test_explicit_overrides_default_match():
       """Verify explicit flag overrides heuristic even if value matches default."""
       # User provides value that happens to equal the default
       config = DetectorConfig(
           detector_convention=DetectorConvention.MOSFLM,
           beam_center_s_mm=51.25,  # Matches default for 1024x1024 detector
           beam_center_f_mm=51.25,
           beam_center_source=BeamCenterSource.EXPLICIT,  # But explicitly provided
           pixel_size_mm=0.1,
           spixels=1024,
           fpixels=1024,
       )
       detector = Detector(config)
       # Explicit source prevents offset even though value matches default
       assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(512.5))  # NOT 513.0
   ```

---

## 5. Documentation Impact

### 5.1 Files Requiring Updates

| Document | Section | Change Required |
|----------|---------|-----------------|
| `docs/architecture/detector.md` | §8.2 Beam Center Mapping | Add `beam_center_source` semantics; clarify MOSFLM offset applies ONLY to AUTO defaults |
| `docs/development/c_to_pytorch_config_map.md` | MOSFLM convention row (line ~57) | Document beam_center_source detection; list 8 explicit flags |
| `docs/findings.md` | API-002 interaction | Note pix0_vector override now interacts with beam_center_source |

### 5.2 Example Documentation Update

**detector.md §Beam Center Mapping (NEW TEXT):**

```markdown
### Beam Center Source Tracking

The `beam_center_source` field in `DetectorConfig` distinguishes between:

- **AUTO (default):** Beam centers derived from detector geometry defaults.
  For MOSFLM convention, applies the required +0.5 pixel offset per spec-a-core.md §72.
  
- **EXPLICIT:** Beam centers explicitly provided by user via:
  - CLI flags: `-Xbeam`, `-Ybeam`, `--beam_center_s`, etc.
  - API: `DetectorConfig(beam_center_s_mm=..., beam_center_source=BeamCenterSource.EXPLICIT)`
  - Header ingestion: `-img` or `-mask` files containing `BEAM_CENTER_X/Y` keys
  
  NO convention-specific adjustments applied to explicit coordinates.

**Critical:** When constructing `DetectorConfig` directly in Python (not via CLI), users MUST
explicitly set `beam_center_source=BeamCenterSource.EXPLICIT` when providing beam centers.
Otherwise, the default `AUTO` will apply MOSFLM offset unintentionally.
```

---

## 6. Risk Assessment

### 6.1 API-002 Interaction (pix0_vector Override)

**Finding:** `docs/findings.md` documents that `-pix0_vector_mm` CLI flag allows direct detector origin override, bypassing beam center calculations.

**Risk:** If user provides both explicit beam center AND pix0_vector override, which takes precedence?

**Mitigation:**
1. Document precedence order: `pix0_vector_mm` > beam center (existing behavior)
2. Add validation warning if both are provided:
   ```python
   if args.pix0_vector_mm and args.beam_center_source == BeamCenterSource.EXPLICIT:
       logger.warning("Both pix0_vector and explicit beam center provided; "
                     "pix0_vector takes precedence per API-002")
   ```

### 6.2 CONVENTION-001 Interaction (CUSTOM Convention)

**Finding:** `docs/findings.md` notes that CUSTOM convention disables implicit offsets.

**Risk:** For CUSTOM convention, `beam_center_source` logic should short-circuit.

**Mitigation:** CUSTOM already uses `Fbeam = Xbeam` mapping (no offset). The two-condition guard in §3.1 naturally handles this: CUSTOM ≠ MOSFLM, so offset never applies. No additional code needed.

**Verification Test:**
```python
def test_custom_convention_no_offset():
    """Verify CUSTOM convention never applies MOSFLM offset."""
    config = DetectorConfig(
        detector_convention=DetectorConvention.CUSTOM,
        beam_center_s_mm=12.8,
        beam_center_source=BeamCenterSource.AUTO,  # Even with AUTO
        pixel_size_mm=0.1,
    )
    detector = Detector(config)
    assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(128.0))  # No offset
```

### 6.3 Header Ingestion Edge Cases

**Risk:** Mixed header ingestion scenarios (e.g., `-img` provides beam center, `-mask` does not).

**Mitigation:** "Last file read wins" precedence (existing behavior, spec-a-core.md §AT-PRE-001). If last file contains beam center keys, set `EXPLICIT`; otherwise preserve current source.

**Implementation Note:**
```python
# Process -img first
if args.img:
    img_updates = parse_smv_header(img_header, is_mask=False)
    config.update(img_updates)

# Then -mask (may override)
if args.mask:
    mask_updates = parse_smv_header(mask_header, is_mask=True)
    config.update(mask_updates)  # Last wins per spec
```

### 6.4 PyTorch Device/Dtype/Differentiability Neutrality

**Risk:** New code must preserve device/dtype agnosticism and gradient flow.

**Analysis:**
- `beam_center_source` is an **Enum**, not a tensor → no device/dtype concerns
- Beam center properties already return tensors → no new tensor allocation
- Conditional logic (`if` statements) does not break gradients
- No `.item()`, `.detach()`, or `torch.linspace` introduced

**Verification:** Existing gradient tests (`tests/test_gradients.py`) already cover beam center parameters. No new gradient breaks introduced.

### 6.5 Backward Compatibility

**Risk:** Existing code constructing `DetectorConfig` without `beam_center_source` field.

**Mitigation:** Default value `BeamCenterSource.AUTO` preserves existing behavior:
- Old code: `DetectorConfig(beam_center_s_mm=12.8, ...)`
- Behavior: Same as before (AUTO defaults, MOSFLM offset applies)

**Breaking Change:** None. Only **semantic** change: users can now opt out of MOSFLM offset by setting `EXPLICIT`.

---

## 7. Acceptance Criteria

### 7.1 Code Changes

- [ ] `BeamCenterSource` enum added to `config.py`
- [ ] `DetectorConfig.beam_center_source` field added with default `AUTO`
- [ ] `determine_beam_center_source()` helper function in `__main__.py`
- [ ] Beam center properties in `detector.py` use two-condition offset guard
- [ ] Header ingestion logic updates `beam_center_source` when applicable

### 7.2 Test Coverage

- [ ] 5 new test cases in `tests/test_beam_center_source.py` PASS
- [ ] `test_at_parallel_003.py::test_detector_offset_preservation` PASSES
- [ ] Existing detector config tests updated for new field
- [ ] CLI detection test validates 8 explicit flags
- [ ] Edge case: explicit-matches-default test PASSES

### 7.3 C-PyTorch Parity

- [ ] **Case 1 (MOSFLM AUTO):** C and PyTorch both apply +0.5 offset, correlation ≥0.999
- [ ] **Case 2 (MOSFLM EXPLICIT):** PyTorch no longer applies offset, now matches C behavior for explicit coordinates, correlation ≥0.999
- [ ] **Case 3 (XDS/DIALS/CUSTOM):** No offset for any source, correlation ≥0.999

### 7.4 Documentation

- [ ] `docs/architecture/detector.md` updated with `beam_center_source` semantics
- [ ] `docs/development/c_to_pytorch_config_map.md` lists 8 explicit flags
- [ ] API-002 interaction documented in findings.md
- [ ] Direct API usage warning added to c_to_pytorch_config_map.md

### 7.5 Regression Safety

- [ ] Targeted validation bundle (detector config tests) green
- [ ] No new warnings/errors in full Phase M chunked suite
- [ ] C8 cluster resolved (1 failure → 0 failures)

---

## 8. Implementation Sequence (Phase C Tasks)

Based on `plans/active/detector-config.md` Phase C:

### C1. Update Configuration Layer
- Add `BeamCenterSource` enum
- Extend `DetectorConfig` with `beam_center_source` field
- **Validation:** `pytest -v tests/test_detector_config.py`

### C2. Adjust CLI Parsing
- Implement `determine_beam_center_source()` helper
- Detect 8 explicit beam center flags
- Update header ingestion logic
- **Validation:** CLI integration tests

### C3. Apply Conditional Offset in Detector
- Modify `beam_center_s_pixels` property with two-condition guard
- Modify `beam_center_f_pixels` property with two-condition guard
- **Validation:** `pytest -v tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation`

### C4. Expand Regression Coverage
- Create `tests/test_beam_center_source.py` with 5 test cases
- Update existing detector config tests
- Add non-MOSFLM negative controls
- **Validation:** `pytest -v tests/test_beam_center_source.py`

### C5. Targeted Validation Bundle
- Run: `pytest -v tests/test_detector_config.py tests/test_at_parallel_002.py tests/test_at_parallel_003.py`
- Capture logs + metrics at `reports/.../phase_m3/<STAMP>/mosflm_fix/`
- **Success:** 16/16 tests pass, no regressions

### C6. Documentation Sync
- Update `docs/architecture/detector.md`
- Update `docs/development/c_to_pytorch_config_map.md`
- Document API-002 interaction
- **Validation:** Manual review

### C7. Ledger & Tracker Update
- Update `docs/fix_plan.md` [DETECTOR-CONFIG-001] Attempts History
- Mark C8 cluster RESOLVED in remediation_tracker.md
- **Validation:** Git commit

---

## 9. Alternative Considered: Option B (Heuristic)

**Approach:** Compare beam center values against computed defaults; if they match, apply offset.

**Rejected Reasons:**
1. **Fragile:** What if user coincidentally provides default value explicitly?
2. **Coupling:** Ties beam center logic to detector size calculations
3. **Non-semantic:** Heuristic doesn't capture **intent** (explicit vs auto)
4. **Maintenance:** Harder to debug when heuristic fails

**Option A Advantages:**
- **Semantic clarity:** `source` field explicitly tracks intent
- **Robustness:** No false positives from value matching
- **Auditability:** Easy to trace CLI → config → detector pipeline
- **Spec alignment:** Directly implements spec-a-core.md §72 distinction

---

## 10. References

### Normative
- `specs/spec-a-core.md` §72 (MOSFLM convention)
- `arch.md` §ADR-03 (Beam-center Mapping)
- `plans/active/detector-config.md` (this initiative's plan)

### Evidence
- `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md` (C8 failure analysis)
- `reports/2026-01-test-suite-triage/phase_l/20251011T104618Z/detector_config/analysis.md` (Phase L targeted evidence)

### Interacting Findings
- `docs/findings.md` API-002 (pix0_vector override precedence)
- `docs/findings.md` CONVENTION-001 (CUSTOM convention offset behavior)

### Implementation
- `src/nanobrag_torch/config.py` (configuration dataclasses)
- `src/nanobrag_torch/models/detector.py` (beam center properties)
- `src/nanobrag_torch/__main__.py` (CLI parsing)

---

## 11. Success Metrics

**Phase C Exit:**
- 16/16 targeted tests pass
- C8 failure count: 1 → 0
- No new regressions in targeted bundle

**Phase D Exit (Full Suite):**
- Phase M chunked rerun: ≤13 failures (baseline: 13 failures pre-fix)
- C8 cluster marked ✅ RESOLVED in remediation tracker
- Correlation ≥0.999 for MOSFLM explicit beam center parity case

---

**Status:** ✅ DESIGN COMPLETE — Ready for Phase C implementation handoff per input.md directive.

**Next:** Update `docs/fix_plan.md` [DETECTOR-CONFIG-001] Phase B status → [D], proceed to Phase C implementation with this design as blueprint.
