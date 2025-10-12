# DETECTOR-CONFIG-001: MOSFLM Beam Center Offset Remediation Design (Option A)

**STAMP:** 20251012T022620Z
**Phase:** B (Design)
**Cluster:** C8 (MOSFLM Beam Center Offset Misapplication)
**Approach:** Option A (Explicit Beam Center Source Tracking)
**Status:** Design Phase — Implementation Pending

---

## Executive Summary

This document specifies the **Option A** remediation design for C8 cluster failures (MOSFLM beam center offset misapplication). The design introduces explicit beam center source tracking to distinguish between auto-calculated convention defaults (which receive the MOSFLM +0.5 pixel offset) and explicit user-provided coordinates (which must be preserved exactly).

**Key Design Decision:** Add `beam_center_source` attribute to `DetectorConfig` with two states: `AUTO` (convention-based defaults) and `EXPLICIT` (user-provided values). This provides semantic clarity, auditability, and aligns with spec-a-core.md §72 normative requirements.

**Rationale for Option A over Option B:**
- **Explicit semantics**: Clear distinction at config level prevents heuristic fragility
- **Auditability**: CLI → config → detector pipeline is traceable
- **Maintainability**: No coupling between beam center and detector size logic
- **Testability**: Easy to verify correct source propagation

---

## Normative References

### Spec Requirements

**spec-a-core.md §72 (MOSFLM Convention):**
> "MOSFLM applies a +0.5 pixel offset to beam center calculations when deriving from detector geometry defaults. Explicit user-provided beam centers must not be adjusted."

**spec-a-core.md §68-73 (Geometry & Conventions):**
- MOSFLM default beam center: `Xbeam = (detsize_s + pixel)/2`, `Ybeam = (detsize_f + pixel)/2`
- MOSFLM mapping: `Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel`
- Pivot mode: BEAM (default for MOSFLM)

### Architecture Decisions

**arch.md §ADR-03 (Beam-center Mapping and +0.5 pixel Offsets):**
> "MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs."

**Key Insight:** The +0.5 pixel offset is a **convention-specific DEFAULT behavior**, not a mandatory transformation for ALL coordinates. The spec requires distinguishing between convention defaults and explicit user inputs.

---

## Problem Statement

### Current Incorrect Behavior

The `Detector` class currently applies the MOSFLM +0.5 pixel offset to ALL beam center coordinates, including explicit user-provided values:

```python
# Simplified pseudocode (INCORRECT)
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm
    if self.config.detector_convention == DetectorConvention.MOSFLM:
        return base + 0.5  # ALWAYS applied, even to explicit values
    return base
```

### Impact

When users provide explicit beam center coordinates (e.g., `--beam_center_s 512.5 --beam_center_f 512.5`), the detector applies an additional unintended +0.5 pixel shift, resulting in:
- **Spec violation**: User intent not preserved
- **Incorrect geometry**: Beam center shifted to 513.0 instead of 512.5 pixels
- **Test failure**: `test_at_parallel_003.py::test_detector_offset_preservation` FAILS

### Root Cause

The implementation lacks semantic distinction between:
1. **Auto-calculated defaults** (convention-dependent) → SHALL apply +0.5 offset
2. **Explicit user inputs** (convention-agnostic preservation) → SHALL NOT apply +0.5 offset

---

## Option A Design Specification

### 1. Configuration Layer Enhancement

**File:** `src/nanobrag_torch/config.py`

**Add BeamCenterSource Enum:**

```python
from enum import Enum

class BeamCenterSource(Enum):
    """
    Tracks whether beam center values are auto-calculated convention defaults
    or explicit user-provided coordinates.

    AUTO: Beam center derived from detector geometry defaults
          (MOSFLM SHALL apply +0.5 pixel offset)
    EXPLICIT: Beam center provided by user via CLI flags or API
              (SHALL preserve exactly as given, no convention adjustments)
    """
    AUTO = "auto"
    EXPLICIT = "explicit"
```

**Modify DetectorConfig Dataclass:**

```python
@dataclass
class DetectorConfig:
    # Existing fields...
    beam_center_s_mm: float
    beam_center_f_mm: float
    pixel_size_mm: float
    detector_convention: DetectorConvention
    detector_pivot: DetectorPivot

    # NEW FIELD
    beam_center_source: BeamCenterSource = BeamCenterSource.AUTO

    # ... other existing fields
```

**Backward Compatibility:**
- Default value `AUTO` preserves existing behavior for code not setting the field
- Explicit API users MUST set `beam_center_source=BeamCenterSource.EXPLICIT` when providing coordinates

---

### 2. CLI Detection Logic

**File:** `src/nanobrag_torch/__main__.py`

**Detection Function:**

```python
def determine_beam_center_source(args) -> BeamCenterSource:
    """
    Determine if beam center is explicit (user-provided) or auto-calculated.

    Explicit indicators (8 CLI flags):
    - --beam_center_s / --beam_center_f
    - -Xbeam / -Ybeam (MOSFLM/DENZO style)
    - -Xclose / -Yclose (forces SAMPLE pivot)
    - -ORGX / -ORGY (XDS style, in pixels)

    Header ingestion via -img/-mask also counts as explicit if header
    contains beam center keys.

    Returns:
        BeamCenterSource.EXPLICIT if any explicit flag present
        BeamCenterSource.AUTO otherwise (use convention defaults)
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

    # Check header ingestion (if -img/-mask provided)
    if args.img or args.mask:
        # Parse headers and check for beam center keys
        # If found, return EXPLICIT
        # (Implementation detail: check for BEAM_CENTER_X/Y,
        #  ADXV_CENTER_X/Y, MOSFLM_CENTER_X/Y, etc.)
        pass

    return BeamCenterSource.AUTO
```

**Integration into CLI Parsing:**

```python
def main():
    parser = argparse.ArgumentParser(...)
    # ... existing argument definitions ...

    args = parser.parse_args()

    # Determine beam center source
    beam_center_source = determine_beam_center_source(args)

    # Create DetectorConfig with source tracking
    detector_config = DetectorConfig(
        beam_center_s_mm=computed_beam_center_s,
        beam_center_f_mm=computed_beam_center_f,
        beam_center_source=beam_center_source,  # NEW
        # ... other fields ...
    )

    # ... continue with simulator setup ...
```

---

### 3. Detector Property Implementation

**File:** `src/nanobrag_torch/models/detector.py`

**Modified Beam Center Properties:**

```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """
    Compute beam center in slow-axis pixels.

    Per spec-a-core.md §72 and arch.md §ADR-03:
    - MOSFLM convention with AUTO source: apply +0.5 pixel offset
    - All other cases: no offset (preserve exact value)

    Returns:
        torch.Tensor: Beam center position in pixels (fast axis)
    """
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm

    # Two-condition guard: MOSFLM AND AUTO
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == BeamCenterSource.AUTO):
        return base + 0.5

    return base

@property
def beam_center_f_pixels(self) -> torch.Tensor:
    """
    Compute beam center in fast-axis pixels.

    Same logic as beam_center_s_pixels (see docstring).
    """
    base = self.config.beam_center_f_mm / self.config.pixel_size_mm

    # Two-condition guard: MOSFLM AND AUTO
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == BeamCenterSource.AUTO):
        return base + 0.5

    return base
```

**PyTorch Device/Dtype Neutrality:**
- Properties return `torch.Tensor` with same device/dtype as `pixel_size_mm`
- No hard-coded `.cpu()` or dtype conversions
- Scalar arithmetic (`+ 0.5`) broadcasts correctly

**Differentiability:**
- `+0.5` is a constant additive term (gradient flows through `base` calculation)
- Conditional logic based on config enums (non-differentiable control flow, but config values are not parameters requiring gradients)

---

### 4. Test Coverage Expansion

**File:** `tests/test_beam_center_source.py` (NEW)

**Test Cases:**

1. **Test MOSFLM Auto-Calculated Beam Center (offset SHALL be applied)**
   ```python
   def test_mosflm_auto_applies_offset():
       config = DetectorConfig(
           detector_convention=DetectorConvention.MOSFLM,
           beam_center_s_mm=51.2,
           beam_center_f_mm=51.2,
           pixel_size_mm=0.1,
           beam_center_source=BeamCenterSource.AUTO,  # Auto-calculated
       )
       detector = Detector(config)

       # Base: 51.2 / 0.1 = 512.0 pixels
       # MOSFLM offset: +0.5
       # Expected: 512.5 pixels
       assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(512.5), atol=1e-6)
       assert torch.allclose(detector.beam_center_f_pixels, torch.tensor(512.5), atol=1e-6)
   ```

2. **Test MOSFLM Explicit Beam Center (offset SHALL NOT be applied)**
   ```python
   def test_mosflm_explicit_no_offset():
       config = DetectorConfig(
           detector_convention=DetectorConvention.MOSFLM,
           beam_center_s_mm=51.2,
           beam_center_f_mm=51.2,
           pixel_size_mm=0.1,
           beam_center_source=BeamCenterSource.EXPLICIT,  # User-provided
       )
       detector = Detector(config)

       # Base: 51.2 / 0.1 = 512.0 pixels
       # NO offset for explicit
       # Expected: 512.0 pixels
       assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(512.0), atol=1e-6)
       assert torch.allclose(detector.beam_center_f_pixels, torch.tensor(512.0), atol=1e-6)
   ```

3. **Test Non-MOSFLM Conventions (no offset regardless of source)**
   ```python
   @pytest.mark.parametrize("convention", [
       DetectorConvention.XDS,
       DetectorConvention.DIALS,
       DetectorConvention.CUSTOM,
       DetectorConvention.ADXV,
       DetectorConvention.DENZO,
   ])
   @pytest.mark.parametrize("source", [
       BeamCenterSource.AUTO,
       BeamCenterSource.EXPLICIT,
   ])
   def test_non_mosflm_no_offset(convention, source):
       config = DetectorConfig(
           detector_convention=convention,
           beam_center_s_mm=51.2,
           beam_center_f_mm=51.2,
           pixel_size_mm=0.1,
           beam_center_source=source,
       )
       detector = Detector(config)

       # Expected: 512.0 pixels (no offset for non-MOSFLM)
       assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(512.0), atol=1e-6)
   ```

4. **Test CLI Detection Logic**
   ```python
   def test_cli_explicit_flag_detection():
       # Mock argparse args with explicit beam center flags
       args = argparse.Namespace(
           beam_center_s=12.8,
           beam_center_f=12.8,
           Xbeam=None,
           Ybeam=None,
           # ... other flags ...
       )

       source = determine_beam_center_source(args)
       assert source == BeamCenterSource.EXPLICIT

   def test_cli_auto_default():
       # Mock argparse args with NO explicit beam center flags
       args = argparse.Namespace(
           beam_center_s=None,
           beam_center_f=None,
           Xbeam=None,
           Ybeam=None,
           # ... other flags ...
       )

       source = determine_beam_center_source(args)
       assert source == BeamCenterSource.AUTO
   ```

5. **Test Edge Case: User Provides Value Matching Default**
   ```python
   def test_explicit_wins_even_if_matches_default():
       # User explicitly provides beam center that happens to match convention default
       config = DetectorConfig(
           detector_convention=DetectorConvention.MOSFLM,
           spixels=1024,
           fpixels=1024,
           pixel_size_mm=0.1,
           beam_center_s_mm=51.25,  # Matches MOSFLM default (102.4+0.1)/2 = 51.25
           beam_center_f_mm=51.25,
           beam_center_source=BeamCenterSource.EXPLICIT,  # But marked explicit
       )
       detector = Detector(config)

       # Base: 51.25 / 0.1 = 512.5 pixels
       # NO offset because explicit (even though value matches default)
       # Expected: 512.5 pixels
       assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(512.5), atol=1e-6)
   ```

**Existing Test Update:**
- `test_at_parallel_003.py::test_detector_offset_preservation` SHALL now PASS (currently FAILING)
- Verify this test exercises `EXPLICIT` source and expects no offset

---

### 5. Documentation Updates

**Files to Update:**

1. **docs/architecture/detector.md (§Beam Center Mapping)**
   - Add section explaining `beam_center_source` semantics
   - Update MOSFLM convention row to clarify auto vs explicit behavior
   - Include code examples showing correct API usage

2. **docs/development/c_to_pytorch_config_map.md (MOSFLM Convention Row)**
   - Add column for `beam_center_source` detection logic
   - Document 8 explicit CLI flags
   - Add "Critical Notes" warning about direct API usage

3. **docs/findings.md (New Entry)**
   - Title: "MOSFLM +0.5 Pixel Offset: Auto vs Explicit Semantics"
   - Document C8 cluster root cause
   - Capture Option A design rationale
   - Reference implementation files

4. **specs/spec-a-core.md (Reference Only)**
   - NO changes required (spec already normative)
   - Implementation now conforms to §72

---

## Phase B Task Breakdown (B1-B4)

### B1: Configuration Layer Implementation
**Effort:** 1 hour
**Files:** `src/nanobrag_torch/config.py`
**Tasks:**
1. Define `BeamCenterSource` enum with `AUTO` and `EXPLICIT` values
2. Add `beam_center_source` field to `DetectorConfig` dataclass
3. Set default value to `AUTO` for backward compatibility
4. Add docstrings explaining semantics

**Exit Criteria:**
- [ ] `BeamCenterSource` enum exists with correct values
- [ ] `DetectorConfig.beam_center_source` field present with default `AUTO`
- [ ] Docstrings reference spec-a-core.md §72

### B2: CLI Detection Logic Implementation
**Effort:** 2 hours
**Files:** `src/nanobrag_torch/__main__.py`
**Tasks:**
1. Implement `determine_beam_center_source()` function
2. Add detection for 8 explicit CLI flags
3. Handle header ingestion cases (-img/-mask)
4. Integrate into main() config construction
5. Add unit tests for detection logic

**Exit Criteria:**
- [ ] `determine_beam_center_source()` function implemented
- [ ] All 8 explicit flags detected correctly
- [ ] Header ingestion handled
- [ ] CLI integration complete
- [ ] Detection logic unit tests passing

### B3: Detector Property Logic Update
**Effort:** 1 hour
**Files:** `src/nanobrag_torch/models/detector.py`
**Tasks:**
1. Update `beam_center_s_pixels` property with two-condition guard
2. Update `beam_center_f_pixels` property (same logic)
3. Add docstrings referencing spec and ADR
4. Verify device/dtype neutrality preserved
5. Verify differentiability maintained

**Exit Criteria:**
- [ ] Both beam center properties implement two-condition guard
- [ ] Docstrings reference spec-a-core.md §72 and arch.md §ADR-03
- [ ] Device/dtype tests pass (CPU + CUDA if available)
- [ ] Gradient flow tests pass (if beam center is differentiable parameter)

### B4: Test Coverage Expansion
**Effort:** 3 hours
**Files:** `tests/test_beam_center_source.py` (NEW), `tests/test_at_parallel_003.py` (UPDATE)
**Tasks:**
1. Create `test_beam_center_source.py` with 5 test cases (see §4)
2. Update `test_at_parallel_003.py` to verify `EXPLICIT` source
3. Run targeted validation: `pytest tests/test_beam_center_source.py tests/test_at_parallel_003.py`
4. Verify all 16 tests pass (5 new + existing AT-003 tests)

**Exit Criteria:**
- [ ] 5 new test cases implemented and passing
- [ ] `test_at_parallel_003.py::test_detector_offset_preservation` PASSES
- [ ] Targeted validation: 16/16 tests pass
- [ ] Test runtime < 2 seconds

---

## Risk Assessment

### Low-Risk Items
- **Enum addition**: Isolated change, no side effects
- **Config field addition**: Default value preserves backward compatibility
- **Detector property logic**: Localized change with clear guard conditions

### Medium-Risk Items
- **CLI detection logic**: Must handle all 8 explicit flags correctly
  - **Mitigation**: Comprehensive unit tests for detection function
- **Header ingestion**: Must parse SMV headers for beam center keys
  - **Mitigation**: Reuse existing header parsing logic, add edge case tests

### Potential Issues
1. **Direct API Usage Warning**: Users constructing `DetectorConfig` directly in Python code must explicitly set `beam_center_source=EXPLICIT` when providing coordinates
   - **Mitigation**: Clear documentation, API examples, consider adding validation warning
2. **Test Suite Regression**: Other tests may rely on implicit MOSFLM offset behavior
   - **Mitigation**: Full-suite regression validation (Phase D)

---

## Phase C/D Preview (Implementation & Validation)

### Phase C: Implementation
**Tasks:**
- Execute B1-B4 tasks sequentially
- Run targeted validation after each task
- Commit changes incrementally with clear messages

**Targeted Validation Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE \
  pytest -v tests/test_beam_center_source.py tests/test_at_parallel_003.py
```

**Expected Result:** 16/16 tests pass

### Phase D: Full-Suite Validation
**Tasks:**
- Run complete pytest suite
- Verify no new regressions introduced
- Confirm C8 cluster resolved
- Update documentation

**Full-Suite Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE \
  pytest -v tests/ --maxfail=0
```

**Expected Result:**
- C8 test PASSES: `test_at_parallel_003.py::test_detector_offset_preservation` ✅
- No new failures introduced
- Pass rate improves by +1 (C8 resolved)

---

## Parity Validation Strategy

### C-PyTorch Equivalence Checks

**Case 1: MOSFLM Auto-Calculated (both apply +0.5)**
```bash
# C reference
./golden_suite_generator/nanoBragg -lambda 6.2 -N 5 \
  -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 256 -floatfile c_auto.bin

# PyTorch (default AUTO source)
nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 256 -floatfile py_auto.bin

# Validate: correlation ≥0.999
```

**Case 2: MOSFLM Explicit Beam Center (post-fix parity)**
```bash
# C reference
./golden_suite_generator/nanoBragg -lambda 6.2 -N 5 \
  -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 256 -Xbeam 12.8 -Ybeam 12.8 \
  -floatfile c_explicit.bin

# PyTorch (EXPLICIT source detected from -Xbeam/-Ybeam)
nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 256 -Xbeam 12.8 -Ybeam 12.8 \
  -floatfile py_explicit.bin

# Validate: correlation ≥0.999 (CURRENTLY FAILS, will pass post-fix)
```

**Case 3: XDS Convention (no offset for any source)**
```bash
# C reference
./golden_suite_generator/nanoBragg -lambda 6.2 -N 5 \
  -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 256 -convention XDS \
  -floatfile c_xds.bin

# PyTorch
nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 256 -convention XDS \
  -floatfile py_xds.bin

# Validate: correlation ≥0.999
```

---

## Success Metrics

### Phase B (Design) Exit Criteria
- [ ] Design document authored (this document) with B1-B4 task breakdown
- [ ] Normative spec passages quoted verbatim
- [ ] Risk assessment documented
- [ ] Parity validation strategy defined
- [ ] Test coverage plan specified

### Phase C (Implementation) Exit Criteria
- [ ] All B1-B4 tasks complete
- [ ] Targeted validation: 16/16 tests pass (< 2s runtime)
- [ ] Code changes committed with clear messages
- [ ] Documentation updates synchronized

### Phase D (Validation) Exit Criteria
- [ ] Full pytest suite passes (no new regressions)
- [ ] C8 test PASSES: `test_at_parallel_003.py::test_detector_offset_preservation`
- [ ] C-PyTorch parity validated for all 3 cases (correlation ≥0.999)
- [ ] docs/fix_plan.md updated with C8 cluster marked RESOLVED

---

## References

### Specifications
- `specs/spec-a-core.md` §68-73 (Geometry & Conventions)
- `specs/spec-a-core.md` §72 (MOSFLM Convention, normative offset behavior)

### Architecture
- `arch.md` §ADR-03 (Beam-center Mapping and +0.5 pixel Offsets)
- `arch.md` §7 (Geometry Model & Conventions, lines 223-227)

### Development Guides
- `docs/development/c_to_pytorch_config_map.md` (Configuration parity map)
- `docs/debugging/detector_geometry_checklist.md` (Debugging prerequisite)
- `docs/architecture/detector.md` (Detector component specification)

### Issue Tracking
- `docs/fix_plan.md` (C8 cluster entry, lines TBD)
- `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md` (Failure analysis)

---

## Appendix: Option B Rejection Rationale

**Option B Approach:** Check if beam center values match computed defaults; if they match, apply offset.

**Why Rejected:**
1. **Fragile Heuristic**: Floating-point comparison with defaults is unreliable
   - User might coincidentally provide value matching default
   - Tolerance tuning becomes arbitrary (`abs(value - default) < 1e-6`?)
2. **Coupling**: Beam center logic becomes coupled to detector size logic
   - Changes to default formulas break heuristic
   - Harder to reason about behavior
3. **Testability**: Difficult to test edge cases (e.g., user provides default + 1e-9)
4. **Semantic Clarity**: No explicit record of user intent at config level

**Option A Advantages:**
- Explicit intent captured at config construction
- No heuristic fragility
- Easy to audit and test
- Decoupled from detector geometry calculations

---

**Design Approval:** Pending supervisor review
**Next Phase:** Phase C (Implementation) upon approval
**Estimated Total Effort:** 7 hours (B1-B4)

