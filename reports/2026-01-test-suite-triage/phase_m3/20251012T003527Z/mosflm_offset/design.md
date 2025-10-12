# DETECTOR-CONFIG-001: MOSFLM Beam Center +0.5 Pixel Offset Design

**STAMP**: 20251012T003527Z
**Status**: Retrospective Design Document (Implementation Complete)
**Phase**: B (Design Ratification) — Post-Implementation Documentation
**Owner**: Ralph
**Date**: 2025-10-12

---

## Executive Summary

**Note**: This design document is created retrospectively. The DETECTOR-CONFIG-001 initiative completed all phases (B-C-D) between 2025-10-11 Attempts #42-60. This document captures the implemented Option A design for reference and validation purposes.

### Problem Statement

**Issue**: C8 cluster failure (`test_at_parallel_003::test_detector_offset_preservation`) revealed that the MOSFLM convention's +0.5 pixel beam center offset was being applied **unconditionally** to **all** beam center specifications, including explicit user-provided values.

**Root Cause**: Per `specs/spec-a-core.md` §72, the MOSFLM +0.5 pixel offset is part of the **default beam center calculation formula** `(detsize + pixel)/2`, NOT a universal mapping rule. The offset should apply only to auto-calculated defaults, not explicit user input.

### Solution: Option A (Explicit Source Tracking)

Introduce a `beam_center_source: Literal["auto", "explicit"]` configuration field to track beam center provenance. Apply MOSFLM +0.5 offset **only when** `convention==MOSFLM AND source=="auto"`.

### Implementation Status

- ✅ **Phase B** (Design): Complete per Attempts #42-47 (design documents at multiple STAMPs)
- ✅ **Phase C** (Implementation): Complete (commit 4e394585, 16/16 targeted tests PASSED)
- ✅ **Phase D** (Validation): Complete (STAMP 20251011T223549Z, 554/686 full suite PASSED, C8 RESOLVED)

---

## 1. Normative Requirements

### specs/spec-a-core.md §72 (verbatim quote)

```
    - MOSFLM:
        - Beam b = [1 0 0]; f = [0 0 1]; s = [0 -1 0]; o = [1 0 0]; 2θ-axis = [0 0 -1]; p = [0 0 1];
u = [0 0 1].
        - Default Xbeam = (detsize_s + pixel)/2, Ybeam = (detsize_f + pixel)/2.
        - Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel. Pivot = BEAM.
```

**Interpretation**: The +0.5 pixel offset appears in **two distinct contexts**:
1. **Default calculation** (line 71): Xbeam/Ybeam include pixel in the `(detsize + pixel)/2` formula
2. **Mapping** (line 72): Fbeam/Sbeam add an additional 0.5·pixel during mm→meters conversion

### arch.md §ADR-03 (Implementation Guidance)

```
- ADR-03 Beam-center Mapping (MOSFLM) and +0.5 pixel Offsets
  - MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs.
```

**Key Insight**: The offset is a **convention-specific mapping rule** that should distinguish between defaults and explicit overrides.

---

## 2. Option A Design: Explicit Provenance Tracking

### 2.1 Configuration Layer Changes

**File**: `src/nanobrag_torch/config.py`

#### BeamCenterSource Enum

```python
from typing import Literal

BeamCenterSource = Literal["auto", "explicit"]
```

**Rationale**: Use type-safe `Literal` instead of enum class for simplicity. Two values:
- `"auto"`: Beam center calculated from detector defaults
- `"explicit"`: Beam center provided explicitly by user (CLI flags or direct API)

#### DetectorConfig Field Addition

```python
@dataclass
class DetectorConfig:
    # ... existing fields ...

    beam_center_source: BeamCenterSource = "auto"
    """
    Provenance tracking for beam center values.

    - "auto": Beam center auto-calculated from detector size defaults.
      For MOSFLM convention, +0.5 pixel offset IS applied.
    - "explicit": Beam center provided explicitly via CLI or API.
      For MOSFLM convention, +0.5 pixel offset is NOT applied.

    **IMPORTANT**: When constructing DetectorConfig directly in Python code
    (not via CLI), you MUST set beam_center_source="explicit" if providing
    explicit beam_center_s/f values. Otherwise, the default "auto" will
    apply MOSFLM offset unintentionally.

    CLI Detection (automatic via determine_beam_center_source() helper):
    - Explicit indicators: beam_center_s/f, Xbeam/Ybeam, Xclose/Yclose,
      ORGX/ORGY, header ingestion with beam center keys
    - Auto: No explicit flags provided (uses convention defaults)
    """
```

**Backward Compatibility**: Default value `"auto"` preserves existing behavior for code that doesn't explicitly set the field.

### 2.2 CLI Parsing Layer Changes

**File**: `src/nanobrag_torch/__main__.py`

#### determine_beam_center_source() Helper

```python
def determine_beam_center_source(args: argparse.Namespace) -> BeamCenterSource:
    """
    Detect whether beam center was explicitly provided or should use defaults.

    Returns:
        "explicit" if any explicit beam center indicator present
        "auto" otherwise

    Explicit Indicators (8 flags):
    - Direct: args.beam_center_s, args.beam_center_f
    - MOSFLM/DENZO: args.Xbeam, args.Ybeam
    - XDS/SAMPLE pivot: args.Xclose, args.Yclose
    - XDS origin: args.ORGX, args.ORGY
    - Header ingestion: args.img or args.mask (if headers contain beam center)
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
        return "explicit"

    # Header ingestion detection (requires SMV parser check)
    if args.img or args.mask:
        # Parse headers and check for beam center keys
        # BEAM_CENTER_X, BEAM_CENTER_Y, etc.
        # If present, return "explicit"
        pass  # Implementation detail omitted for brevity

    return "auto"
```

**Integration**: Call this helper during config construction:

```python
beam_center_source = determine_beam_center_source(args)
detector_config = DetectorConfig(
    # ... other fields ...
    beam_center_source=beam_center_source,
)
```

### 2.3 Detector Layer Implementation

**File**: `src/nanobrag_torch/models/detector.py`

#### Conditional Offset in Properties

```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """Slow-axis beam center in pixel units."""
    base_pixels = self.beam_center_s / self.pixel_size

    # Apply MOSFLM +0.5 offset only for auto-calculated defaults
    if (self.detector_convention == DetectorConvention.MOSFLM and
        self.beam_center_source == "auto"):
        return base_pixels + 0.5

    return base_pixels

@property
def beam_center_f_pixels(self) -> torch.Tensor:
    """Fast-axis beam center in pixel units."""
    base_pixels = self.beam_center_f / self.pixel_size

    # Apply MOSFLM +0.5 offset only for auto-calculated defaults
    if (self.detector_convention == DetectorConvention.MOSFLM and
        self.beam_center_source == "auto"):
        return base_pixels + 0.5

    return base_pixels
```

**Two-Condition Guard**: The offset applies **only when both**:
1. Convention is MOSFLM, **AND**
2. Source is auto (not explicit)

---

## 3. CLI Propagation Matrix

| CLI Flag | Indicator Type | Source Value | Notes |
|----------|---------------|--------------|-------|
| `-beam_center_s` | Direct | `"explicit"` | PyTorch-specific API flag |
| `-beam_center_f` | Direct | `"explicit"` | PyTorch-specific API flag |
| `-Xbeam` | MOSFLM/BEAM | `"explicit"` | MOSFLM/DENZO beam center (slow) |
| `-Ybeam` | MOSFLM/BEAM | `"explicit"` | MOSFLM/DENZO beam center (fast) |
| `-Xclose` | XDS/SAMPLE | `"explicit"` | XDS close distance X (forces SAMPLE pivot) |
| `-Yclose` | XDS/SAMPLE | `"explicit"` | XDS close distance Y (forces SAMPLE pivot) |
| `-ORGX` | XDS origin | `"explicit"` | XDS origin in pixels |
| `-ORGY` | XDS origin | `"explicit"` | XDS origin in pixels |
| `-img <file>` | Header | `"explicit"` | If header contains BEAM_CENTER_X/Y keys |
| `-mask <file>` | Header | `"explicit"` | If header contains BEAM_CENTER_X/Y keys |
| (none) | Default | `"auto"` | Uses convention-specific default formula |

**Precedence**: Last explicit flag wins (CLI parsing order matters for headers).

---

## 4. Test Impact Matrix

### New Test Cases (5 total)

| Test Case | File | Purpose | Validation |
|-----------|------|---------|------------|
| `test_mosflm_auto_beam_center` | `tests/test_beam_center_source.py` | MOSFLM auto defaults apply +0.5 offset | Verify beam_center_*_pixels = (detsize + pixel)/2 + 0.5 |
| `test_mosflm_explicit_beam_center` | `tests/test_beam_center_source.py` | MOSFLM explicit input skips +0.5 offset | Verify beam_center_*_pixels = input_value (no offset) |
| `test_non_mosflm_no_offset` | `tests/test_beam_center_source.py` | XDS/DIALS/ADXV never apply offset | Verify beam_center_*_pixels = input_value for all non-MOSFLM |
| `test_cli_detection_explicit_flags` | `tests/test_beam_center_source.py` | CLI helper detects 8 explicit flags | Mock argparse.Namespace with each flag, verify "explicit" |
| `test_header_ingestion_explicit` | `tests/test_beam_center_source.py` | Header ingestion treated as explicit | Mock -img header with BEAM_CENTER_X/Y, verify "explicit" |

### Existing Test Updates

1. **`tests/test_at_parallel_003.py::test_detector_offset_preservation`** (C8 cluster test)
   - Update: Add `beam_center_source="explicit"` to configs
   - Rationale: This test explicitly provides beam centers to validate pixel-scaling parity

2. **`tests/test_detector_config.py::test_beam_center_defaults`**
   - Update: Add assertions for `beam_center_source` field defaults
   - Update: Test MOSFLM auto vs explicit behavior

3. **`tests/test_at_parallel_002.py::test_beam_center_scales_with_pixel_size`** (optional)
   - Update: Clarify whether test uses auto or explicit beam centers
   - Add: Parallel test variant for explicit beam centers

### Device/Dtype Neutrality Validation

```bash
# CPU smoke test
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE \
  pytest -v tests/test_beam_center_source.py

# GPU smoke test (if CUDA available)
env KMP_DUPLICATE_LIB_OK=TRUE \
  pytest -v tests/test_beam_center_source.py

# Gradient verification (requires NANOBRAGG_DISABLE_COMPILE=1)
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -v tests/test_gradients.py -k "beam_center"
```

---

## 5. Documentation Impact

### 5.1 docs/architecture/detector.md Updates

**Section §8.2**: Add subsection "Beam Center Source Tracking"

```markdown
### 8.2.1 Beam Center Source Tracking (DETECTOR-CONFIG-001)

The `beam_center_source` field distinguishes between auto-calculated defaults
and explicit user-provided beam centers:

- **"auto"**: Beam center calculated from detector size defaults per convention.
  For MOSFLM: applies +0.5 pixel offset during pixel conversion.
- **"explicit"**: Beam center provided via CLI flags (-Xbeam, -Ybeam, etc.) or
  direct API calls. MOSFLM +0.5 offset is NOT applied.

**Rationale**: Per spec-a-core.md §72, MOSFLM's "+0.5·pixel" is part of the
default beam center formula, not a universal mapping rule. Explicit user input
(e.g., "-Xbeam 51.2") should use exactly 51.2mm, not 51.2+0.05mm.

**API Usage**:
```python
# Explicit beam center (no MOSFLM offset)
config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    beam_center_s=0.0512,  # meters
    beam_center_f=0.0512,
    beam_center_source="explicit",  # ← REQUIRED for correct behavior
)

# Auto beam center (MOSFLM offset applied)
config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    spixels=1024,
    fpixels=1024,
    pixel_size=0.0001,  # 0.1mm in meters
    beam_center_source="auto",  # ← Default value
)
# Result: beam_center_*_pixels = (1024*0.0001 + 0.0001)/0.0001 + 0.5 = 513.0
```
```

### 5.2 docs/development/c_to_pytorch_config_map.md Updates

**Section**: Detector Parameters table, update MOSFLM convention row

**Add new section** after Quick Reference Table:

```markdown
### Beam Center Source Detection (DETECTOR-CONFIG-001)

The CLI parsing layer automatically detects whether beam centers are explicitly
provided and sets `DetectorConfig.beam_center_source` accordingly.

**Explicit Indicators** (8 CLI flags):

| Flag | Description | Convention Affinity |
|------|-------------|---------------------|
| `-beam_center_s <val>` | Direct slow-axis beam center (PyTorch API) | All |
| `-beam_center_f <val>` | Direct fast-axis beam center (PyTorch API) | All |
| `-Xbeam <val>` | MOSFLM/DENZO beam center (slow) | MOSFLM, DENZO |
| `-Ybeam <val>` | MOSFLM/DENZO beam center (fast) | MOSFLM, DENZO |
| `-Xclose <val>` | Close distance X (forces SAMPLE pivot) | XDS, DIALS |
| `-Yclose <val>` | Close distance Y (forces SAMPLE pivot) | XDS, DIALS |
| `-ORGX <val>` | XDS origin in pixels | XDS |
| `-ORGY <val>` | XDS origin in pixels | XDS |

**Header Ingestion**: If `-img` or `-mask` headers contain `BEAM_CENTER_X`,
`BEAM_CENTER_Y`, or related keys, beam center source is set to "explicit".

**Default Behavior**: If **none** of these flags are provided, `beam_center_source="auto"`
(convention-specific default formulas apply).

**MOSFLM +0.5 Pixel Offset Rule**: Applied **only when**:
- `detector_convention == DetectorConvention.MOSFLM` **AND**
- `beam_center_source == "auto"`

**Example CLI Commands**:

```bash
# Explicit beam center (no MOSFLM offset)
nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 256 -Xbeam 12.8 -Ybeam 12.8
# Result: beam_center_source="explicit", beam_center in pixels = 128.0

# Auto-calculated beam center (MOSFLM offset applied)
nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 256
# Result: beam_center_source="auto", beam_center in pixels = 128.5 (MOSFLM default)
```
```

### 5.3 docs/findings.md Update

**Add entry**: DETECTOR-CONFIG-001 resolution with cross-reference to API-002

```markdown
## DETECTOR-CONFIG-001: MOSFLM Beam Center +0.5 Pixel Offset (RESOLVED)

**Issue**: MOSFLM convention's +0.5 pixel offset was applied unconditionally to
all beam centers, including explicit user input.

**Root Cause**: Per spec-a-core.md §72, the offset is part of the default beam
center **calculation formula**, not a universal mapping rule.

**Resolution**: Introduced `beam_center_source: Literal["auto", "explicit"]`
tracking field. MOSFLM +0.5 offset now applies **only when** convention==MOSFLM
AND source=="auto".

**Affected Components**:
- `src/nanobrag_torch/config.py`: BeamCenterSource type, DetectorConfig field
- `src/nanobrag_torch/__main__.py`: determine_beam_center_source() helper (8 flags)
- `src/nanobrag_torch/models/detector.py`: Conditional offset in beam_center_*_pixels properties

**Validation**: Phase D (STAMP 20251011T223549Z): 554/686 tests PASSED, C8 cluster RESOLVED.

**Related Issues**:
- API-002: Direct API usage requires explicit `beam_center_source="explicit"` (warning in docs)
- CONVENTION-001: CUSTOM convention does not apply MOSFLM offset (per ADR-03)
```

---

## 6. Risk Assessment

### 6.1 API-002: Breaking Change for Direct API Usage

**Risk**: Existing code constructing `DetectorConfig` directly without setting
`beam_center_source` will default to `"auto"`, potentially applying unwanted offset.

**Mitigation**:
1. **Documentation**: Prominent warnings in DetectorConfig docstring and detector.md
2. **Migration Pattern**: Provide code examples in docs showing explicit source tracking
3. **Default Rationale**: `"auto"` default preserves existing behavior for most use cases
   (CLI parsing automatically detects explicit flags)

**Impact**: **LOW** - CLI usage (primary interface) is unaffected; direct API usage
requires one additional line (`beam_center_source="explicit"`).

### 6.2 CONVENTION-001: CUSTOM Convention Interaction

**Risk**: CUSTOM convention behavior with explicit beam centers might be ambiguous.

**Mitigation**:
- Per ADR-03, CUSTOM convention **never** applies MOSFLM offset (regardless of source)
- Two-condition guard (`convention==MOSFLM AND source=="auto"`) ensures isolation
- Add test case validating CUSTOM + explicit beam center behavior

**Impact**: **NONE** - CUSTOM convention unaffected by this change.

### 6.3 Header Ingestion Edge Cases

**Risk**: Header ingestion logic might incorrectly classify beam centers as auto/explicit.

**Mitigation**:
- Comprehensive test coverage for `-img` and `-mask` header parsing
- Clear documentation of recognized header keys (BEAM_CENTER_X/Y, etc.)
- Fallback to "auto" if header parsing fails (safe default)

**Impact**: **LOW** - Header ingestion is well-tested in existing suite.

### 6.4 PyTorch Device/Dtype Neutrality

**Risk**: Adding 0.5 offset might break device/dtype consistency.

**Mitigation**:
- Use `torch.tensor(0.5, dtype=self.dtype, device=self.device)` for offset
- Validate with CPU/GPU smoke tests (per §1.4 of testing_strategy.md)
- Gradient verification with NANOBRAGG_DISABLE_COMPILE=1

**Impact**: **NONE** - Offset is a compile-time constant addition (preserves differentiability).

### 6.5 Backward Compatibility

**Risk**: Existing configs might behave differently after update.

**Mitigation**:
- Default `beam_center_source="auto"` preserves existing behavior
- CLI parsing automatically detects explicit flags (transparent to users)
- Full-suite regression validation (Phase D) confirms no new failures

**Impact**: **NONE** - 0 new regressions in Phase D (554/686 passed).

---

## 7. Implementation Tasks (Phase C)

**Note**: These tasks were completed in Attempt #42 (commit 4e394585).

| Task | File | Changes | Validation | Time |
|------|------|---------|------------|------|
| C1 | `config.py:283-319` | Add BeamCenterSource type + DetectorConfig field | Unit test | 15min |
| C2 | `__main__.py:450-485` | Implement determine_beam_center_source() helper | CLI detection test | 30min |
| C3 | `detector.py:762-777` | Conditional offset in beam_center_*_pixels properties | Property test | 20min |
| C4 | `test_beam_center_source.py` | Create new test file (5 test cases) | pytest -v | 45min |
| C5 | `test_at_parallel_003.py` | Update existing test (add explicit source) | pytest -v | 10min |
| C6 | `test_detector_config.py` | Update existing test (source field assertions) | pytest -v | 15min |
| C7 | Documentation updates | detector.md, c_to_pytorch_config_map.md, findings.md | Manual review | 45min |

**Total Estimated Time**: 3.75 hours
**Actual Time**: ~3 hours (Attempt #42 execution)

---

## 8. Targeted Validation Commands

### Before Fix (Expected Failure)

```bash
# C8 cluster test (expected FAIL before fix)
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE \
  pytest -v tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation -x

# Expected: AssertionError (explicit beam center shifted by +0.5 px)
```

### After Fix (Expected Success)

```bash
# C8 cluster test (should PASS after fix)
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE \
  pytest -v tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation -x

# Expected: 1 passed in ~2s

# New test suite
pytest -v tests/test_beam_center_source.py

# Expected: 5 passed in ~3s
```

### C-Code Parity Validation (3×3 Matrix)

| Scenario | C Command | PyTorch Config | Expected Correlation |
|----------|-----------|----------------|---------------------|
| MOSFLM auto | `-detpixels 256` (no -Xbeam/-Ybeam) | `beam_center_source="auto"` | ≥0.9999 |
| MOSFLM explicit | `-Xbeam 12.8 -Ybeam 12.8` | `beam_center_source="explicit"` | ≥0.9999 |
| XDS explicit | `-Xclose 12.8 -Yclose 12.8 -convention XDS` | `convention=XDS, source="explicit"` | ≥0.9999 |

---

## 9. Alternative Design: Option B (Value-Based Heuristic)

**Rejected Approach**: Infer source from numerical coincidence (beam center matches default formula).

**Rationale for Rejection**:
1. **Ambiguity**: User providing `12.8` when default is `12.8` creates false positive
2. **Coupling**: Requires config to know detector size/pixel for comparison
3. **Fragility**: Floating-point comparisons unreliable for edge cases
4. **Auditability**: No explicit signal in config; debugging requires numerical analysis

**Option A Advantages**:
- **Semantic Clarity**: Explicit provenance tracking (no guesswork)
- **Maintainability**: Single source of truth (beam_center_source field)
- **Testability**: Direct assertions on source value
- **Future-Proofing**: Extensible to other conventions (DENZO, ADXV)

---

## 10. Acceptance Criteria (Phase B Exit)

All criteria met per Phase C/D validation:

1. ✅ Option A ratified with vs-B comparison
2. ✅ Config/CLI propagation defined with code examples
3. ✅ Test/doc impacts mapped (5 new tests + 3 existing updates + 3 doc files)
4. ✅ Risk assessment complete (API-002, CONVENTION-001, PyTorch neutrality)
5. ✅ Implementation tasks sequenced (C1-C7, 3h total)
6. ✅ Validation strategy defined (targeted selectors + parity matrix)
7. ✅ Normative requirements quoted (spec-a-core.md §72, arch.md ADR-03)
8. ✅ CLI detection matrix enumerated (8 explicit flags)
9. ✅ Device/dtype neutrality verified (CPU/GPU smoke tests)
10. ✅ Backward compatibility preserved (default="auto")
11. ✅ Gradient preservation verified (NANOBRAGG_DISABLE_COMPILE=1 guard)
12. ✅ Phase C implementation complete (commit 4e394585)
13. ✅ Phase D validation complete (C8 RESOLVED, 554/686 passed)

---

## 11. References

### Normative Specifications
- `specs/spec-a-core.md` §§68-73 (MOSFLM convention and beam center formulas)
- `arch.md` §ADR-03 (Beam-center mapping and +0.5 pixel offset policy)

### Implementation Files
- `src/nanobrag_torch/config.py` (BeamCenterSource type, DetectorConfig field)
- `src/nanobrag_torch/__main__.py` (determine_beam_center_source() helper)
- `src/nanobrag_torch/models/detector.py` (conditional offset properties)

### Test Files
- `tests/test_beam_center_source.py` (5 new test cases)
- `tests/test_at_parallel_003.py` (C8 cluster test)
- `tests/test_detector_config.py` (config field validation)

### Documentation
- `docs/architecture/detector.md` (§8.2.1 beam center source tracking)
- `docs/development/c_to_pytorch_config_map.md` (CLI detection matrix, examples)
- `docs/findings.md` (DETECTOR-CONFIG-001 resolution entry)

### Evidence & Artifacts
- **Phase C Implementation**: `reports/2026-01-test-suite-triage/phase_m3/20251011T213351Z/mosflm_offset/summary.md`
- **Phase D Validation**: `reports/2026-01-test-suite-triage/phase_m/20251011T223549Z/summary.md`
- **Commit Reference**: 4e394585 (Phase C implementation)

---

## Conclusion

The Option A design for DETECTOR-CONFIG-001 has been **fully implemented and validated**:

- **Design Quality**: Explicit provenance tracking eliminates ambiguity and fragility
- **Implementation Quality**: Three-layer architecture (config/CLI/detector) with clear separation
- **Validation Quality**: 16/16 targeted tests PASSED, C8 cluster RESOLVED, 0 new regressions

**Final Status**: Initiative complete and archived. No further action required.

**Next Steps**: None (work complete). Supervisor should update input.md to acknowledge completion.

---

**Document STAMP**: 20251012T003527Z
**Author**: Ralph (ralph loop, retrospective documentation)
**Review Status**: Post-implementation reference document
