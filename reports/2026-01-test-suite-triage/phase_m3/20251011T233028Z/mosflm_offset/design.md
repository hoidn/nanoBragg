# Option A Remediation Design: MOSFLM Beam Center Source Tracking

**STAMP:** 20251011T233028Z
**Phase:** M3 (Post-Resolution Documentation)
**Cluster:** C8 (MOSFLM Beam Center Offset Misapplication)
**Status:** ✅ IMPLEMENTED (documenting completed work)

---

## Executive Summary

This document captures the **Option A** design decision for resolving C8 (MOSFLM beam center offset misapplication). The implementation was completed successfully in Phase M3 (STAMP: 20251011T213351Z - 20251011T223549Z), with this design document serving as post-implementation documentation of the technical approach and rationale.

**Core Design Decision:** Add explicit `beam_center_source` tracking to distinguish auto-calculated vs user-provided beam centers, enabling correct application of MOSFLM convention's +0.5 pixel offset only to auto-calculated defaults.

**Result:** Spec compliance restored, AT-PARALLEL-003 passing, no regressions introduced (13 failures remain from Phase M2 baseline).

---

## Design Context & Requirements

### Normative Specification Requirements

**From `specs/spec-a-core.md` §68-86 (Geometry & Conventions):**

> **MOSFLM Convention (§72):**
> - Default Xbeam = (detsize_s + pixel)/2, Ybeam = (detsize_f + pixel)/2.
> - **Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel.** Pivot = BEAM.

**Critical Interpretation (from arch.md §ADR-03):**
> "MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). **CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs.**"

**Key Insight:** The +0.5 pixel offset is a **convention-specific default behavior**, NOT a mandatory transformation for all beam center coordinates. The offset applies to auto-calculated defaults derived from detector geometry, but explicit user-provided coordinates must be preserved exactly.

### Problem Statement

**Pre-Implementation Bug:** The Detector class incorrectly applied MOSFLM +0.5 pixel offset to ALL beam center coordinates, including explicit user inputs.

**Failure Mode (AT-PARALLEL-003):**
```python
# User provides explicit beam center
config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    beam_center_s=512.5,  # Explicit user input (mm)
    # ...
)

# Bug: Detector applies unwanted offset
# beam_center_s_pixels = 512.5 / 0.1 + 0.5 = 5125.5 pixels (INCORRECT)
# Expected: beam_center_s_pixels = 512.5 / 0.1 = 5125.0 pixels
```

**Impact:** Users providing explicit beam centers experienced unintended +0.5 pixel geometry shifts, causing incorrect diffraction patterns.

---

## Option A Design: Beam Center Source Tracking

### Architecture Overview

**Three-Layer Provenance Tracking:**

1. **Configuration Layer** (`src/nanobrag_torch/config.py`):
   - New `BeamCenterSource` enum with `AUTO` and `EXPLICIT` values
   - `DetectorConfig.beam_center_source` field (default: `AUTO`)

2. **CLI Detection Layer** (`src/nanobrag_torch/__main__.py`):
   - Automatic detection of 8 explicit beam center flags
   - Sets `beam_center_source=EXPLICIT` when any explicit flag present

3. **Detector Property Layer** (`src/nanobrag_torch/models/detector.py`):
   - Two-condition guard: `MOSFLM + AUTO` → apply offset
   - All other cases → no offset

### Implementation Details

#### Phase B1: Configuration Data Model

**File:** `src/nanobrag_torch/config.py`

```python
from enum import Enum

class BeamCenterSource(Enum):
    """Provenance tracking for beam center coordinates."""
    AUTO = "auto"        # Convention-derived defaults → apply MOSFLM offset
    EXPLICIT = "explicit"  # User-provided values → preserve exactly

@dataclass
class DetectorConfig:
    # ... existing fields ...

    beam_center_source: BeamCenterSource = BeamCenterSource.AUTO
    """
    Beam center provenance flag.

    - AUTO: Beam center derived from detector geometry defaults.
            For MOSFLM convention, +0.5 pixel offset will be applied.
    - EXPLICIT: Beam center explicitly provided by user via CLI flags
                or direct API usage. No convention-based offsets applied.

    Spec Reference: specs/spec-a-core.md §72 (MOSFLM mapping)
    Arch Reference: arch.md §ADR-03 (Beam-center Mapping)
    """
```

**Rationale:**
- Enum provides type safety and semantic clarity
- Default `AUTO` preserves backward compatibility with existing convention-based defaults
- Explicit docstring references normative spec sections for auditability

#### Phase B2: CLI Detection Logic

**File:** `src/nanobrag_torch/__main__.py`

```python
def determine_beam_center_source(args) -> BeamCenterSource:
    """
    Detect whether beam center coordinates are explicitly provided.

    Explicit beam center flags (any of these → EXPLICIT):
    - --beam_center_s / --beam_center_f (direct coordinates)
    - -Xbeam / -Ybeam (MOSFLM-style beam center)
    - -Xclose / -Yclose (SAMPLE pivot near-point)
    - -ORGX / -ORGY (XDS-style origin)
    - --img <file> with beam center header keys
    - --mask <file> with beam center header keys

    Returns:
        BeamCenterSource.EXPLICIT if any explicit flag present
        BeamCenterSource.AUTO otherwise (convention defaults)
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
        # Note: --img/--mask header ingestion handled separately
    ]

    if any(explicit_flags):
        return BeamCenterSource.EXPLICIT

    # Check for header ingestion (if headers contain beam center keys)
    if args.img or args.mask:
        # Header parsing sets beam_center values before this check
        # If headers contain BEAM_CENTER_X/Y or equivalents, treat as explicit
        # (Implementation detail: header ingestion updates args namespace)
        if hasattr(args, '_header_provided_beam_center'):
            return BeamCenterSource.EXPLICIT

    return BeamCenterSource.AUTO
```

**CLI Integration Point:**

```python
# In main() function, after argument parsing
beam_center_source = determine_beam_center_source(args)

detector_config = DetectorConfig(
    # ... other parameters ...
    beam_center_source=beam_center_source,
)
```

**Rationale:**
- Exhaustive flag coverage ensures all user-provided coordinates detected
- Header ingestion handling preserves explicit source semantics for SMV files
- Centralized detection logic simplifies auditing and testing

#### Phase B3: Detector Property Implementation

**File:** `src/nanobrag_torch/models/detector.py`

```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """
    Beam center slow-axis coordinate in pixels.

    For MOSFLM convention with auto-calculated defaults, applies +0.5 pixel offset
    per spec-a-core.md §72. Explicit user-provided coordinates preserved exactly.

    Returns:
        Beam center slow coordinate in pixels (tensor, device/dtype neutral)
    """
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm

    # Apply MOSFLM offset ONLY to auto-calculated defaults
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == BeamCenterSource.AUTO):
        return base + 0.5

    return base

@property
def beam_center_f_pixels(self) -> torch.Tensor:
    """
    Beam center fast-axis coordinate in pixels.

    For MOSFLM convention with auto-calculated defaults, applies +0.5 pixel offset
    per spec-a-core.md §72. Explicit user-provided coordinates preserved exactly.

    Returns:
        Beam center fast coordinate in pixels (tensor, device/dtype neutral)
    """
    base = self.config.beam_center_f_mm / self.config.pixel_size_mm

    # Apply MOSFLM offset ONLY to auto-calculated defaults
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == BeamCenterSource.AUTO):
        return base + 0.5

    return base
```

**Two-Condition Guard Semantics:**

| Condition 1 | Condition 2 | Result | Rationale |
|-------------|-------------|--------|-----------|
| `MOSFLM` | `AUTO` | **Offset applied** | Spec-mandated default behavior |
| `MOSFLM` | `EXPLICIT` | No offset | User coordinates preserved |
| `Non-MOSFLM` | `AUTO` | No offset | Other conventions don't use offset |
| `Non-MOSFLM` | `EXPLICIT` | No offset | Consistent explicit handling |

**Rationale:**
- Explicit two-condition conjunction makes spec compliance auditable
- Device/dtype neutral (operates on tensors without device assumptions)
- Identical logic for both slow/fast axes ensures consistency

#### Phase B4: Test Coverage Strategy

**File:** `tests/test_beam_center_source.py` (new)

**Test Cases:**

1. **MOSFLM Auto-Calculated Offset Application**
   ```python
   def test_mosflm_auto_applies_offset():
       """Verify MOSFLM +0.5 offset applied to auto-calculated defaults."""
       config = DetectorConfig(
           detector_convention=DetectorConvention.MOSFLM,
           beam_center_s_mm=51.2,
           beam_center_f_mm=51.2,
           pixel_size_mm=0.1,
           beam_center_source=BeamCenterSource.AUTO,  # Auto-calculated
       )
       detector = Detector(config)

       # Expected: (51.2 / 0.1) + 0.5 = 512.5 pixels
       assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(512.5), atol=1e-6)
       assert torch.allclose(detector.beam_center_f_pixels, torch.tensor(512.5), atol=1e-6)
   ```

2. **MOSFLM Explicit Coordinate Preservation**
   ```python
   def test_mosflm_explicit_no_offset():
       """Verify MOSFLM explicit coordinates preserved exactly (no offset)."""
       config = DetectorConfig(
           detector_convention=DetectorConvention.MOSFLM,
           beam_center_s_mm=51.2,
           beam_center_f_mm=51.2,
           pixel_size_mm=0.1,
           beam_center_source=BeamCenterSource.EXPLICIT,  # User-provided
       )
       detector = Detector(config)

       # Expected: (51.2 / 0.1) = 512.0 pixels (no offset)
       assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(512.0), atol=1e-6)
       assert torch.allclose(detector.beam_center_f_pixels, torch.tensor(512.0), atol=1e-6)
   ```

3. **Non-MOSFLM Conventions No Offset**
   ```python
   @pytest.mark.parametrize("convention", [
       DetectorConvention.XDS,
       DetectorConvention.DIALS,
       DetectorConvention.CUSTOM,
       DetectorConvention.DENZO,
       DetectorConvention.ADXV,
   ])
   def test_non_mosflm_no_offset_regardless_of_source(convention):
       """Verify non-MOSFLM conventions never apply offset."""
       for source in [BeamCenterSource.AUTO, BeamCenterSource.EXPLICIT]:
           config = DetectorConfig(
               detector_convention=convention,
               beam_center_s_mm=51.2,
               beam_center_f_mm=51.2,
               pixel_size_mm=0.1,
               beam_center_source=source,
           )
           detector = Detector(config)

           # Expected: Always (51.2 / 0.1) = 512.0 pixels
           assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(512.0), atol=1e-6)
   ```

4. **CLI Detection Correctness**
   ```python
   def test_cli_detection_explicit_flags():
       """Verify CLI detection identifies all explicit beam center flags."""
       # Simulate argparse namespace with explicit flag
       args = argparse.Namespace(
           beam_center_s=512.5,  # Explicit coordinate
           beam_center_f=None,
           Xbeam=None, Ybeam=None,
           Xclose=None, Yclose=None,
           ORGX=None, ORGY=None,
           img=None, mask=None,
       )

       source = determine_beam_center_source(args)
       assert source == BeamCenterSource.EXPLICIT

   def test_cli_detection_auto_defaults():
       """Verify CLI detection defaults to AUTO when no explicit flags."""
       args = argparse.Namespace(
           beam_center_s=None, beam_center_f=None,
           Xbeam=None, Ybeam=None,
           Xclose=None, Yclose=None,
           ORGX=None, ORGY=None,
           img=None, mask=None,
       )

       source = determine_beam_center_source(args)
       assert source == BeamCenterSource.AUTO
   ```

5. **Edge Case: Explicit Matches Default**
   ```python
   def test_explicit_wins_when_matching_default():
       """Verify explicit source overrides heuristic when value matches default."""
       # MOSFLM default: (detsize_s + pixel)/2 = (102.4 + 0.1)/2 = 51.25 mm
       # User explicitly provides this same value → should NOT apply offset
       config = DetectorConfig(
           detector_convention=DetectorConvention.MOSFLM,
           beam_center_s_mm=51.25,  # Coincidentally matches default
           beam_center_f_mm=51.25,
           pixel_size_mm=0.1,
           spixels=1024, fpixels=1024,
           beam_center_source=BeamCenterSource.EXPLICIT,
       )
       detector = Detector(config)

       # Expected: 512.5 pixels (no offset, explicit wins)
       assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(512.5), atol=1e-6)
   ```

**Coverage Analysis:**

| Test Case | Validates | Risk Mitigated |
|-----------|-----------|----------------|
| Test 1 | MOSFLM AUTO behavior | Regression: offset not applied when it should be |
| Test 2 | MOSFLM EXPLICIT behavior | Original bug: offset applied when it shouldn't be |
| Test 3 | Non-MOSFLM conventions | Cross-convention contamination |
| Test 4 | CLI detection logic | Missed explicit flags (false AUTO) |
| Test 5 | Edge case resolution | Heuristic-based ambiguity |

---

## Alternative Design (Option B) — Rejected

### Approach: Value-Based Heuristic

```python
def _is_auto_calculated(self) -> bool:
    """Check if beam center matches convention default values."""
    default_s = (self.config.detsize_s_mm - self.config.pixel_size_mm) / 2
    default_f = (self.config.detsize_f_mm + self.config.pixel_size_mm) / 2

    return (abs(self.config.beam_center_s_mm - default_s) < 1e-6 and
            abs(self.config.beam_center_f_mm - default_f) < 1e-6)

@property
def beam_center_s_pixels(self) -> torch.Tensor:
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm

    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self._is_auto_calculated()):
        return base + 0.5

    return base
```

### Rejection Rationale

**Critical Flaws:**

1. **Ambiguity:** User coincidentally providing default-matching value creates undefined behavior
   - Test case 5 above would fail under Option B (heuristic would incorrectly apply offset)
   - No way to distinguish "user explicitly wants default" from "auto-calculated default"

2. **Coupling:** Beam center logic tightly couples to detector size logic
   - Changes to default beam center formula require updating heuristic
   - Violates separation of concerns (geometry vs provenance)

3. **Auditability:** Harder to verify correctness
   - Need to trace default calculation logic to understand offset application
   - Debugging requires numerical comparison instead of semantic flag inspection

4. **Float Precision:** 1e-6 tolerance arbitrary and fragile
   - Different precision contexts (float32 vs float64) may cause false positives/negatives
   - Unit conversion rounding errors could trigger misclassification

**Comparison Summary:**

| Criterion | Option A (Source Tracking) | Option B (Heuristic) |
|-----------|---------------------------|----------------------|
| **Semantic Clarity** | ✅ Explicit provenance flag | ❌ Implicit value comparison |
| **Edge Case Handling** | ✅ User intent always respected | ❌ Ambiguous when values match |
| **Maintainability** | ✅ Single source of truth | ❌ Coupled to geometry defaults |
| **Auditability** | ✅ Boolean flag inspection | ❌ Numerical tolerance tuning |
| **Config Changes Required** | ⚠️ 1 new field | ✅ None |
| **Test Complexity** | ✅ Straightforward | ⚠️ Requires precision edge cases |

**Conclusion:** Option A's explicit semantic tracking outweighs the cost of adding one config field.

---

## Implementation Risks & Mitigations

### API-002: Breaking Change for Direct API Users

**Risk:** Existing code directly instantiating `DetectorConfig` without `beam_center_source` parameter will default to `AUTO`, potentially changing behavior.

**Mitigation:**
- Default value `BeamCenterSource.AUTO` preserves existing convention-based behavior
- Only users explicitly providing beam centers affected → migration path clear
- Documentation updates in `detector.md` and `c_to_pytorch_config_map.md` highlight new field

**Migration Pattern:**
```python
# Old code (implicit AUTO)
config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    beam_center_s=12.8,  # Was incorrectly offset
)

# New code (explicit EXPLICIT for user-provided coordinates)
config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    beam_center_s=12.8,
    beam_center_source=BeamCenterSource.EXPLICIT,  # NEW: Required for correct behavior
)
```

### CONVENTION-001: CUSTOM Convention Interaction

**Risk:** CUSTOM convention behavior undefined in spec; unclear whether to apply offsets.

**Current Behavior (per arch.md §ADR-03):**
> "CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs."

**Design Decision:** CUSTOM convention NEVER applies offset regardless of source (consistent with other non-MOSFLM conventions).

**Rationale:**
- CUSTOM implies user has full control over geometry
- Implicit convention-based adjustments violate "custom" semantics
- Test case 3 validates this behavior

### Device/Dtype Neutrality Preservation

**Requirement (from PyTorch Runtime Guardrails):**
> "Do not introduce `.cpu()`/`.cuda()` or per-call `.to()` shims inside compiled paths."

**Validation:**
- `beam_center_s_pixels` and `beam_center_f_pixels` operate on tensors without device transfers
- Offset addition (`+ 0.5`) compatible with any device/dtype
- Test suite MUST include CPU and CUDA smoke tests (when available)

**Canonical Smoke Test:**
```bash
# CPU validation
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_beam_center_source.py

# GPU validation (when CUDA available)
env KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_beam_center_source.py -k "not cpu_only"
```

---

## Phase C Implementation Tasks (B1-B4)

### B1: Configuration Layer (config.py)
- ✅ Add `BeamCenterSource` enum
- ✅ Add `beam_center_source` field to `DetectorConfig`
- ✅ Add docstring with spec references

### B2: CLI Detection Layer (__main__.py)
- ✅ Implement `determine_beam_center_source()` helper
- ✅ Integrate into main() config construction
- ✅ Handle 8 explicit beam center flags
- ✅ Handle header ingestion edge case

### B3: Detector Property Layer (detector.py)
- ✅ Update `beam_center_s_pixels` property with two-condition guard
- ✅ Update `beam_center_f_pixels` property with two-condition guard
- ✅ Add spec reference comments

### B4: Test Coverage Expansion (test_beam_center_source.py)
- ✅ Test 1: MOSFLM AUTO applies offset
- ✅ Test 2: MOSFLM EXPLICIT preserves coordinates
- ✅ Test 3: Non-MOSFLM conventions no offset
- ✅ Test 4: CLI detection correctness
- ✅ Test 5: Edge case (explicit matches default)

### B5: Targeted Validation
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_beam_center_source.py
```
**Expected:** 5/5 tests PASSED

### B6: Documentation Updates
- ✅ `docs/architecture/detector.md` (§Beam Center Mapping)
- ✅ `docs/development/c_to_pytorch_config_map.md` (MOSFLM convention row, new §70-125)
- ✅ `docs/findings.md` (C8 resolution entry)

### B7: Fix Plan Ledger Update
- ✅ Mark C8 cluster RESOLVED in `docs/fix_plan.md`
- ✅ Record implementation metrics (test pass rate, artifacts)

---

## Phase D Acceptance Criteria

### D1: Full Test Suite Regression Check
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v
```
**Threshold:** No new failures introduced (13 baseline failures from Phase M2 acceptable)

### D2: AT-PARALLEL-003 Validation
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation
```
**Threshold:** PASSED (correlation ≥0.999, exact beam center match)

### D3: C-PyTorch Parity Validation
```bash
env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py -k "AT-PARALLEL-003"
```
**Threshold:** Correlation ≥0.999, sum ratio ≤1.005

### D4: Documentation Consistency Audit
- ✅ All spec references (spec-a-core.md §72, arch.md §ADR-03) cited in code comments
- ✅ Config map updated with new `beam_center_source` field
- ✅ Detector architecture doc reflects two-condition guard logic

---

## Implementation Metrics (Actual Results — Phase M3)

**Phase C (STAMP: 20251011T213351Z):**
- **Targeted tests:** 16/16 PASSED (1.95s runtime)
- **Files modified:** 3 (config.py, __main__.py, detector.py)
- **Test coverage added:** 5 new test cases (test_beam_center_source.py)
- **Documentation updated:** 3 files (detector.md, c_to_pytorch_config_map.md, findings.md)

**Phase D (STAMP: 20251011T223549Z):**
- **Full suite:** 554/686 PASSED (80.8% pass rate)
- **Failures:** 13 (all pre-existing from Phase M2 baseline)
- **New regressions:** 0
- **AT-PARALLEL-003:** ✅ PASSED (correlation 0.9999, beam center exact match)

**Artifacts:**
- Design document: `reports/.../20251011T214422Z/mosflm_offset/design.md` (23KB)
- Implementation summary: `reports/.../20251011T213351Z/mosflm_fix/summary.md`
- Full-suite validation: `reports/.../20251011T223549Z/summary.md`

---

## References

### Normative Specifications
- **spec-a-core.md §68-86:** Geometry & Conventions (MOSFLM +0.5 pixel offset mapping)
- **spec-a-core.md §72:** MOSFLM convention beam center formula
- **arch.md §ADR-03:** Beam-center Mapping (MOSFLM) and +0.5 pixel Offsets

### Implementation Contracts
- **docs/architecture/detector.md:** Detector component specification (beam center properties)
- **docs/development/c_to_pytorch_config_map.md:** C-CLI to PyTorch configuration mapping
- **docs/debugging/detector_geometry_checklist.md:** Detector debugging prerequisites

### Test Strategy
- **docs/development/testing_strategy.md:** Three-tier validation approach
- **tests/test_beam_center_source.py:** Beam center source tracking test suite
- **tests/test_at_parallel_003.py:** AT-PARALLEL-003 offset preservation test

### Related Issues
- **C8 Cluster Summary:** `reports/.../phase_m3/20251011T193829Z/mosflm_offset/summary.md`
- **Phase M3a Handoff:** `reports/.../phase_m3/20251011T175917Z/mosflm_sync/summary.md`
- **Fix Plan:** `docs/fix_plan.md` (DETECTOR-CONFIG-001 item)

---

## Conclusion

**Option A (Beam Center Source Tracking) provides:**

1. **Spec Compliance:** Correctly implements spec-a-core.md §72 MOSFLM offset semantics
2. **Semantic Clarity:** Explicit provenance flag eliminates ambiguity
3. **Auditability:** Clear mapping from CLI → config → detector → offset application
4. **Maintainability:** Decoupled from geometry default calculations
5. **Edge Case Safety:** Handles "explicit matches default" scenario correctly

**Implementation Status:** ✅ COMPLETE (Phase M3, STAMP 20251011T213351Z - 20251011T223549Z)

**Test Coverage:** 5/5 targeted tests + AT-PARALLEL-003 passing + full suite regression clean

**Next Steps (Post-Phase D):**
- Monitor C-PyTorch parity for MOSFLM cases in future test runs
- Extend documentation with user migration guide for direct API users
- Consider future work: DENZO convention offset behavior (if needed)

---

**Design Status:** ✅ APPROVED AND IMPLEMENTED
**Validation Status:** ✅ COMPLETE (Phase D acceptance criteria met)
**Documentation Status:** ✅ SYNCED (detector.md, c_to_pytorch_config_map.md, findings.md)

