# MOSFLM Beam Center Offset Remediation Design (Option A)

**STAMP:** 20251011T210514Z
**Phase:** M3 Phase B (Design & Blueprint)
**Cluster ID:** C8
**Status:** Design Complete — Ready for Phase C Implementation
**Owner:** ralph (implementation), galph (review)

---

## Executive Summary

This document specifies the **Option A** remediation approach for C8 (MOSFLM Beam Center Offset Misapplication). The implementation will introduce an explicit `beam_center_source` attribute to `DetectorConfig` to distinguish between **auto-calculated** and **explicit user-provided** beam centers, enabling correct application of the MOSFLM +0.5 pixel offset per spec-a-core.md §72 and arch.md §ADR-03.

**Key Principle:** The MOSFLM +0.5 pixel offset is a **convention-specific default behavior** for auto-calculated beam centers, NOT a mandatory transformation for all coordinate inputs.

**Design Decision:** Option A (explicit source tracking) is adopted over Option B (heuristic matching) for superior maintainability, semantic clarity, and architectural cleanliness.

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Normative Requirements](#2-normative-requirements)
3. [Design Rationale: Option A vs Option B](#3-design-rationale-option-a-vs-option-b)
4. [Detailed Design Specification](#4-detailed-design-specification)
5. [Configuration Layer Changes](#5-configuration-layer-changes)
6. [CLI Parsing Changes](#6-cli-parsing-changes)
7. [Detector Layer Changes](#7-detector-layer-changes)
8. [Test Impact Matrix](#8-test-impact-matrix)
9. [Documentation Impact](#9-documentation-impact)
10. [Risk Assessment](#10-risk-assessment)
11. [Implementation Checklist](#11-implementation-checklist)
12. [Exit Criteria](#12-exit-criteria)
13. [References](#13-references)

---

## 1. Problem Statement

### 1.1 Current Incorrect Behavior

The `Detector` class (src/nanobrag_torch/models/detector.py) currently applies the MOSFLM convention +0.5 pixel offset to **ALL** beam center coordinates, including explicit user-provided values.

**Code Location:** Beam center property (lines ~78-142)

**Incorrect Logic (Pseudocode):**
```python
if convention == MOSFLM:
    beam_center_pixels = (beam_center_mm / pixel_size_mm) + 0.5  # ALWAYS applied
```

### 1.2 Correct Behavior (Per Specification)

Per **spec-a-core.md §72** and **arch.md §ADR-03**, the +0.5 pixel offset should **ONLY** be applied to auto-calculated beam center defaults when using MOSFLM convention, **NOT** to explicit user inputs.

**Correct Logic (Pseudocode):**
```python
if convention == MOSFLM and beam_center_source == "auto":
    beam_center_pixels = (beam_center_mm / pixel_size_mm) + 0.5
else:
    beam_center_pixels = beam_center_mm / pixel_size_mm  # No offset for explicit
```

### 1.3 Impact

**User-Facing:** When users provide explicit beam center coordinates (e.g., `--beam_center_s 512.5 --beam_center_f 512.5`), the detector applies an additional unintended +0.5 pixel shift, resulting in incorrect geometry.

**Test Failure:** `test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation` fails because explicit beam centers are not preserved.

**C-PyTorch Parity:** PyTorch implementation diverges from C reference behavior for explicit beam center cases.

---

## 2. Normative Requirements

### 2.1 Specification References

**spec-a-core.md §72 (MOSFLM Convention):**
> "Default Xbeam = (detsize_s + pixel)/2, Ybeam = (detsize_f + pixel)/2."
> "Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel. Pivot = BEAM."

**Key Insight:** The specification describes the offset as part of the **default** beam center calculation, not as a universal transformation.

**arch.md §ADR-03 (Beam-center Mapping):**
> "MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs."

**Interpretation:** The offset is an **implicit convention behavior** for auto-derived values, not an explicit coordinate transformation.

### 2.2 Behavioral Contract

1. **Auto-Calculated Beam Centers (MOSFLM):**
   - When no explicit beam center is provided
   - When beam center defaults are used from detector geometry
   - **APPLY** +0.5 pixel offset per MOSFLM convention

2. **Explicit User-Provided Beam Centers:**
   - When user provides `-Xbeam`/`-Ybeam` or `--beam_center_*` flags
   - When beam center is set via direct API instantiation
   - When beam center is ingested from image/mask headers
   - **DO NOT APPLY** +0.5 pixel offset (preserve exact user input)

3. **Non-MOSFLM Conventions:**
   - XDS, DIALS, DENZO, ADXV, CUSTOM
   - **NEVER APPLY** +0.5 pixel offset regardless of source

---

## 3. Design Rationale: Option A vs Option B

### 3.1 Option A: Explicit Source Tracking (RECOMMENDED)

**Approach:** Add `beam_center_source` attribute to `DetectorConfig` to explicitly track the provenance of beam center values.

**Type Signature:**
```python
beam_center_source: Literal["auto", "explicit"] = "auto"
```

**Advantages:**
1. **Semantic Clarity:** Explicit intent is encoded in configuration
2. **Auditability:** Easy to trace CLI → config → detector pipeline
3. **Maintainability:** No fragile heuristics or floating-point comparisons
4. **Testability:** Clear contract for test assertions
5. **Future-Proof:** Extensible for additional provenance types (e.g., "header", "matrix_file")

**Disadvantages:**
1. **Config Changes:** Requires updating all `DetectorConfig` instantiations
2. **API Surface:** Adds one new field to public config API
3. **Documentation:** New field requires explanation in docs

**Trade-Off Analysis:** The advantages significantly outweigh the disadvantages. The config change is localized, the API expansion is minimal and well-justified, and the documentation burden is manageable.

### 3.2 Option B: Heuristic Default Matching (NOT RECOMMENDED)

**Approach:** Compare beam center values against computed defaults; if they match, infer "auto" source.

**Pseudocode:**
```python
def _is_auto_calculated(self) -> bool:
    default_s = (self.config.detsize_s_mm - self.config.pixel_size_mm) / 2
    default_f = (self.config.detsize_f_mm + self.config.pixel_size_mm) / 2
    return (abs(self.config.beam_center_s_mm - default_s) < 1e-6 and
            abs(self.config.beam_center_f_mm - default_f) < 1e-6)
```

**Advantages:**
1. **No Config Changes:** Backwards compatible API
2. **Transparent:** No new public fields

**Disadvantages:**
1. **Fragile Heuristic:** What if user coincidentally provides exact default value?
2. **Floating-Point Comparison:** Tolerance thresholds are arbitrary
3. **Coupling:** Beam center logic becomes coupled to detector size logic
4. **Non-Obvious:** Behavior is implicit and hard to reason about
5. **Hard to Test:** Edge cases multiply (what tolerance? what if detector size changes?)
6. **Maintenance Burden:** Future developers must understand hidden logic

**Trade-Off Analysis:** The heuristic approach trades short-term convenience for long-term fragility. The "coincidental default value" edge case is NOT theoretical—users may intentionally set beam centers to detector-centered values and expect no offset.

### 3.3 Decision: Option A Adopted

**Rationale:** Option A's explicit semantics, maintainability, and testability make it the superior choice. The config API expansion is minimal and well-documented, and the implementation is straightforward.

**Approval:** This design reflects the recommendation in `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md`.

---

## 4. Detailed Design Specification

### 4.1 Configuration Data Model

**File:** `src/nanobrag_torch/config.py`

**Changes:**
1. Add `beam_center_source` field to `DetectorConfig` dataclass
2. Default value: `"auto"` (preserves current behavior for unmodified code paths)
3. Type: `Literal["auto", "explicit"]` (consider `Enum` for type safety)

**Implementation:**
```python
from typing import Literal

@dataclass
class DetectorConfig:
    # ... existing fields ...
    beam_center_s_mm: float
    beam_center_f_mm: float

    # NEW FIELD
    beam_center_source: Literal["auto", "explicit"] = "auto"
    """
    Tracks the provenance of beam center values:
    - "auto": Beam center was auto-calculated from detector geometry defaults
    - "explicit": Beam center was explicitly provided by user (CLI, API, or header)

    Per spec-a-core.md §72 and arch.md §ADR-03, the MOSFLM +0.5 pixel offset
    applies ONLY to auto-calculated beam centers, not explicit user inputs.
    """

    # ... other fields ...
```

**Alternative (Type Safety):**
```python
from enum import Enum

class BeamCenterSource(str, Enum):
    AUTO = "auto"
    EXPLICIT = "explicit"

@dataclass
class DetectorConfig:
    # ... existing fields ...
    beam_center_source: BeamCenterSource = BeamCenterSource.AUTO
    # ...
```

**Recommendation:** Use `Literal` initially for simplicity; migrate to `Enum` if future expansion requires additional sources (e.g., `"header"`, `"matrix_file"`).

### 4.2 CLI Parsing Logic

**File:** `src/nanobrag_torch/__main__.py`

**Changes:**
1. Add `determine_beam_center_source()` helper function
2. Call helper during `DetectorConfig` construction
3. Set `beam_center_source="explicit"` when any explicit flag is detected

**Explicit Beam Center Flags (Detection List):**
- `-Xbeam <val>`
- `-Ybeam <val>`
- `-Xclose <val>` (SAMPLE pivot)
- `-Yclose <val>` (SAMPLE pivot)
- `-ORGX <val>` (XDS convention)
- `-ORGY <val>` (XDS convention)
- `--beam-center-s <val>` (if such flag exists)
- `--beam-center-f <val>` (if such flag exists)

**Header Ingestion:**
- `-img <file>` (if header contains `BEAM_CENTER_X`/`BEAM_CENTER_Y`)
- `-mask <file>` (if header contains `BEAM_CENTER_X`/`BEAM_CENTER_Y`)

**Implementation:**
```python
def determine_beam_center_source(args: argparse.Namespace) -> Literal["auto", "explicit"]:
    """
    Determine whether beam center is explicitly provided or auto-calculated.

    Per spec-a-core.md §72 and arch.md §ADR-03, the MOSFLM +0.5 pixel offset
    applies only to auto-calculated defaults, not explicit user inputs.

    Args:
        args: Parsed CLI arguments

    Returns:
        "explicit" if any explicit beam center flag is provided
        "auto" otherwise
    """
    explicit_flags = [
        args.Xbeam, args.Ybeam,
        args.Xclose, args.Yclose,
        args.ORGX, args.ORGY,
        # Add other explicit beam center flags as needed
    ]

    # Check for explicit flags
    if any(flag is not None for flag in explicit_flags):
        return "explicit"

    # Check for header ingestion
    # (Implementation note: Header parsing sets beam center values;
    #  we need to track whether those values came from headers.
    #  May require additional state tracking in header ingestion logic.)
    if hasattr(args, '_beam_center_from_header') and args._beam_center_from_header:
        return "explicit"

    return "auto"

# In main() or config construction:
detector_config = DetectorConfig(
    beam_center_s_mm=beam_center_s,
    beam_center_f_mm=beam_center_f,
    beam_center_source=determine_beam_center_source(args),
    # ... other fields ...
)
```

**Header Ingestion Handling:**

For `-img` and `-mask` flags, the header parsing logic must set a flag indicating beam center was ingested:

```python
def parse_smv_header(header_text: str) -> dict:
    # ... existing parsing logic ...
    parsed = {}
    if "BEAM_CENTER_X" in header_text:
        parsed['beam_center_f_mm'] = extract_value(...)
        parsed['_beam_center_from_header'] = True
    # ...
    return parsed
```

### 4.3 Detector Layer Logic

**File:** `src/nanobrag_torch/models/detector.py`

**Changes:**
1. Update `beam_center_s_pixels` property
2. Update `beam_center_f_pixels` property
3. Apply offset conditionally based on `beam_center_source`

**Implementation:**
```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """
    Beam center slow-axis coordinate in pixels.

    Per spec-a-core.md §72 and arch.md §ADR-03:
    - MOSFLM convention applies +0.5 pixel offset to AUTO-CALCULATED beam centers only
    - Explicit user-provided beam centers are preserved exactly
    - Non-MOSFLM conventions never apply offset

    Returns:
        Beam center in pixels (tensor, preserves device/dtype/differentiability)
    """
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm

    # Apply MOSFLM +0.5 pixel offset ONLY to auto-calculated beam centers
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == "auto"):
        return base + 0.5

    return base

@property
def beam_center_f_pixels(self) -> torch.Tensor:
    """
    Beam center fast-axis coordinate in pixels.

    Per spec-a-core.md §72 and arch.md §ADR-03:
    - MOSFLM convention applies +0.5 pixel offset to AUTO-CALCULATED beam centers only
    - Explicit user-provided beam centers are preserved exactly
    - Non-MOSFLM conventions never apply offset

    Returns:
        Beam center in pixels (tensor, preserves device/dtype/differentiability)
    """
    base = self.config.beam_center_f_mm / self.config.pixel_size_mm

    # Apply MOSFLM +0.5 pixel offset ONLY to auto-calculated beam centers
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == "auto"):
        return base + 0.5

    return base
```

**Device/Dtype Neutrality Verification:**
- `base` is a tensor (from division of tensors/scalars)
- `+ 0.5` is a scalar operation on tensor (preserves device/dtype)
- No explicit `.cpu()`/`.cuda()` calls
- No `.item()` calls (preserves differentiability)
- Operation is pure tensor arithmetic (device/dtype agnostic)

**Differentiability Verification:**
- No `.detach()` calls
- No `.item()` calls
- Pure tensor operations preserve computation graph
- `requires_grad` propagates correctly through `+` operation

---

## 5. Configuration Layer Changes

### 5.1 DetectorConfig Modifications

**File:** `src/nanobrag_torch/config.py`

**Change Summary:**
1. Add `beam_center_source` field
2. Add docstring explaining field semantics
3. Set default value to `"auto"` for backwards compatibility

**Migration Path:**
- Existing code that doesn't set `beam_center_source` will default to `"auto"`
- This preserves current behavior for unmodified instantiations
- No breaking changes to existing API consumers

**Type Safety:**
```python
# Option 1: Literal type (simple)
beam_center_source: Literal["auto", "explicit"] = "auto"

# Option 2: Enum type (type-safe, recommended for future)
beam_center_source: BeamCenterSource = BeamCenterSource.AUTO
```

**Recommendation:** Start with `Literal` for minimal disruption; migrate to `Enum` in future if additional source types are needed.

### 5.2 Dataclass Validation (Optional Enhancement)

**Optional:** Add `__post_init__` validation to catch invalid values:

```python
def __post_init__(self):
    if self.beam_center_source not in ("auto", "explicit"):
        raise ValueError(
            f"beam_center_source must be 'auto' or 'explicit', got {self.beam_center_source!r}"
        )
```

**Trade-Off:** Adds runtime validation but increases code complexity. Not strictly necessary if using `Literal` type hint (static type checkers will catch errors).

---

## 6. CLI Parsing Changes

### 6.1 Detection Logic

**File:** `src/nanobrag_torch/__main__.py`

**Function:** `determine_beam_center_source(args: argparse.Namespace) -> Literal["auto", "explicit"]`

**Detection Matrix:**

| CLI Flag | Maps To | Sets Source |
|----------|---------|-------------|
| `-Xbeam <val>` | `beam_center_s` | `"explicit"` |
| `-Ybeam <val>` | `beam_center_f` | `"explicit"` |
| `-Xclose <val>` | `beam_center_s` (SAMPLE) | `"explicit"` |
| `-Yclose <val>` | `beam_center_f` (SAMPLE) | `"explicit"` |
| `-ORGX <val>` | `beam_center_f` (XDS) | `"explicit"` |
| `-ORGY <val>` | `beam_center_s` (XDS) | `"explicit"` |
| `-img <file>` with header | from header | `"explicit"` |
| `-mask <file>` with header | from header | `"explicit"` |
| _(no flags)_ | auto-calculated | `"auto"` |

**Implementation Notes:**
1. Check all explicit flags in a single pass
2. Header ingestion requires tracking whether beam center came from header
3. Default to `"auto"` if no explicit flags detected

### 6.2 Header Ingestion Tracking

**Challenge:** Header parsing (SMV ingestion) sets beam center values but doesn't currently track provenance.

**Solution:** Add internal flag `_beam_center_from_header` during header parsing:

```python
def ingest_smv_header(file_path: str, args: argparse.Namespace):
    """Parse SMV header and update args namespace."""
    header = read_smv_header(file_path)

    if "BEAM_CENTER_X" in header:
        args.beam_center_f_mm = parse_beam_center_x(header)
        args._beam_center_from_header = True

    if "BEAM_CENTER_Y" in header:
        args.beam_center_s_mm = parse_beam_center_y(header)
        args._beam_center_from_header = True

    # ... other header keys ...
```

**Alternative:** Return a dict from header parsing indicating which fields were set, then check dict in `determine_beam_center_source()`.

### 6.3 API Usage (Direct Config Construction)

**Warning:** When constructing `DetectorConfig` directly in Python code (not via CLI), users **MUST** explicitly set `beam_center_source="explicit"` if providing explicit beam centers.

**Correct API Usage:**
```python
# Explicit beam center in direct API usage
config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    beam_center_s_mm=12.8,
    beam_center_f_mm=12.8,
    beam_center_source="explicit",  # Required for correct behavior
    # ... other fields ...
)
```

**Incorrect API Usage:**
```python
# INCORRECT: Missing beam_center_source (will apply unwanted offset)
config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    beam_center_s_mm=12.8,
    beam_center_f_mm=12.8,
    # beam_center_source defaults to "auto" → applies MOSFLM +0.5 offset
)
```

**Documentation Requirement:** This API usage pattern MUST be documented in:
1. `DetectorConfig` docstring
2. `docs/development/c_to_pytorch_config_map.md` (new section)
3. User-facing API documentation

---

## 7. Detector Layer Changes

### 7.1 Beam Center Properties

**File:** `src/nanobrag_torch/models/detector.py`

**Functions Modified:**
1. `beam_center_s_pixels` property (lines ~78-100)
2. `beam_center_f_pixels` property (lines ~100-122)

**Change Pattern:**
```python
# OLD (incorrect):
if self.config.detector_convention == DetectorConvention.MOSFLM:
    return base + 0.5

# NEW (correct):
if (self.config.detector_convention == DetectorConvention.MOSFLM and
    self.config.beam_center_source == "auto"):
    return base + 0.5
```

### 7.2 PyTorch Guardrails Verification

**Device/Dtype Neutrality:**
- ✅ No `.cpu()`/`.cuda()` calls
- ✅ No hard-coded device/dtype assumptions
- ✅ Pure tensor operations preserve caller's device/dtype
- ✅ `+ 0.5` scalar operation is device/dtype agnostic

**Differentiability:**
- ✅ No `.item()` calls
- ✅ No `.detach()` calls
- ✅ No `.numpy()` conversions
- ✅ Computation graph preserved through `+` operation
- ✅ `requires_grad` propagates correctly

**Vectorization:**
- ✅ No Python loops introduced
- ✅ Property access remains O(1)
- ✅ No per-pixel iteration

---

## 8. Test Impact Matrix

### 8.1 Existing Tests (Require Updates)

| Test File | Test Function | Change Required | Rationale |
|-----------|--------------|-----------------|-----------|
| `tests/test_detector_config.py` | `test_default_initialization` | Update expectation | Auto-calculated beam centers should now get +0.5 offset |
| `tests/test_detector_config.py` | `test_custom_config_initialization` | Add `beam_center_source` param | Explicit instantiation must specify source |
| `tests/test_at_parallel_003.py` | `test_detector_offset_preservation` | Should now PASS | Fix resolves root cause of failure |

### 8.2 New Tests Required

| Test Name | Purpose | Setup | Assertion |
|-----------|---------|-------|-----------|
| `test_mosflm_auto_beam_center_offset` | Verify +0.5 offset IS applied to auto-calculated beam centers | MOSFLM convention, `beam_center_source="auto"`, default beam centers | `beam_center_pixels == (beam_center_mm / pixel_size_mm) + 0.5` |
| `test_mosflm_explicit_beam_center_no_offset` | Verify +0.5 offset is NOT applied to explicit beam centers | MOSFLM convention, `beam_center_source="explicit"`, explicit coordinates | `beam_center_pixels == (beam_center_mm / pixel_size_mm)` (no offset) |
| `test_non_mosflm_no_offset` | Verify no offset applied regardless of source for non-MOSFLM conventions | XDS/DIALS/CUSTOM conventions, both `"auto"` and `"explicit"` sources | `beam_center_pixels == (beam_center_mm / pixel_size_mm)` |
| `test_beam_center_source_cli_detection` | Verify CLI flags correctly set `beam_center_source` | Various CLI invocations (`-Xbeam`, `-Ybeam`, etc.) | `config.beam_center_source == "explicit"` when flags present |
| `test_beam_center_source_api_direct` | Verify direct API usage requires explicit source | Direct `DetectorConfig` instantiation | Warning or error if explicit beam center provided without source flag |

### 8.3 Parity Validation Tests

**C↔PyTorch Equivalence:**
- **Case 1:** MOSFLM with auto-calculated beam centers (both should apply +0.5)
- **Case 2:** MOSFLM with explicit beam centers (both should NOT apply +0.5)
- **Case 3:** XDS with any beam center (both should NOT apply +0.5)

**Metrics:** Correlation ≥0.999, sum ratio within 0.1%

**Test Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 \
  NB_C_BIN=./golden_suite_generator/nanoBragg \
  pytest -v tests/test_mosflm_beam_center_parity.py
```

---

## 9. Documentation Impact

### 9.1 Architecture Documentation

**File:** `docs/architecture/detector.md`

**Sections to Update:**
1. §8.2 Beam Center Mapping (add `beam_center_source` explanation)
2. §9 Convention-Specific Behavior (clarify MOSFLM offset applies to defaults only)
3. Add new §9.1 "Beam Center Provenance Tracking"

**Content:**
```markdown
### 9.1 Beam Center Provenance Tracking

The `beam_center_source` attribute distinguishes between:
- **"auto"**: Beam center was auto-calculated from detector geometry defaults
- **"explicit"**: Beam center was explicitly provided by user (CLI, API, or header)

Per spec-a-core.md §72 and arch.md §ADR-03, the MOSFLM +0.5 pixel offset
applies ONLY to auto-calculated beam centers, not explicit user inputs.

**Example:**
```python
# Auto-calculated (applies MOSFLM +0.5 offset)
config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    beam_center_s_mm=51.2,  # auto-calculated default
    beam_center_source="auto",
)
# Result: beam_center_s_pixels = 512.5

# Explicit (no MOSFLM offset)
config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    beam_center_s_mm=51.2,
    beam_center_source="explicit",  # user-provided value
)
# Result: beam_center_s_pixels = 512.0
```
```

### 9.2 Configuration Mapping Documentation

**File:** `docs/development/c_to_pytorch_config_map.md`

**New Section (after Detector Parameters table):**

```markdown
### Beam Center Source Detection (DETECTOR-CONFIG-001)

**NEW in Phase C:** The CLI parsing layer automatically detects whether beam centers are explicitly provided and sets `DetectorConfig.beam_center_source` accordingly.

**Detection Logic:** The following CLI flags indicate **explicit** beam center input:

| Flag | Description | Maps To |
|------|-------------|---------|
| `-Xbeam <val>` | Explicit slow-axis beam center | `beam_center_source="explicit"` |
| `-Ybeam <val>` | Explicit fast-axis beam center | `beam_center_source="explicit"` |
| `-Xclose <val>` | Close distance X (forces SAMPLE pivot) | `beam_center_source="explicit"` |
| `-Yclose <val>` | Close distance Y (forces SAMPLE pivot) | `beam_center_source="explicit"` |
| `-ORGX <val>` | XDS-style origin X coordinate | `beam_center_source="explicit"` |
| `-ORGY <val>` | XDS-style origin Y coordinate | `beam_center_source="explicit"` |
| `-img <file>` | Header ingestion from SMV image | `beam_center_source="explicit"` (if header contains beam center) |
| `-mask <file>` | Header ingestion from mask file | `beam_center_source="explicit"` (if header contains beam center) |

**Default Behavior:** If **none** of these flags are provided, `beam_center_source="auto"` (default value).

[... include example CLI commands and API usage warnings ...]
```

### 9.3 Findings Documentation

**File:** `docs/findings.md`

**Update Entry:** API-002 (pix0 overrides beam center)

Add note about interaction with `beam_center_source`:

```markdown
**API-002 Interaction with beam_center_source:**
When `pix0_vector_mm` is explicitly provided, it takes precedence over all beam center
calculations. The `beam_center_source` flag does not affect pix0-based initialization.
However, tests should verify that explicit pix0 does not inadvertently trigger MOSFLM
offset application through indirect code paths.
```

---

## 10. Risk Assessment

### 10.1 API Compatibility Risks

**Risk:** Existing code that directly instantiates `DetectorConfig` without setting `beam_center_source` may behave incorrectly.

**Mitigation:**
1. Default value `"auto"` preserves current behavior
2. Add deprecation warning for direct API usage without explicit source (future enhancement)
3. Document API usage requirements prominently

**Residual Risk:** LOW (default behavior unchanged for most code paths)

### 10.2 Interaction with Findings

**API-002 (pix0 overrides beam center):**
- Risk: Explicit `pix0_vector_mm` may interact unexpectedly with `beam_center_source`
- Mitigation: Add test verifying pix0 precedence is preserved
- Verification: `test_pix0_override_precedence()` in test suite

**CONVENTION-001 (CUSTOM disables offset):**
- Risk: CUSTOM convention switching may not respect `beam_center_source`
- Mitigation: Verify CUSTOM convention never applies offset regardless of source
- Verification: `test_custom_convention_never_offsets()` in test suite

### 10.3 PyTorch Runtime Risks

**Device/Dtype Neutrality:**
- Risk: Offset logic introduces device/dtype mixing
- Mitigation: Verified no `.cpu()`/`.cuda()` calls, no hard-coded dtype
- Verification: Run CPU + CUDA smoke tests (per testing_strategy.md §1.4)

**Differentiability:**
- Risk: Conditional logic breaks computation graph
- Mitigation: Verified no `.item()`/`.detach()` calls, pure tensor operations
- Verification: Run gradient checks on beam center parameters

**Vectorization:**
- Risk: New logic introduces Python loops
- Mitigation: Property access remains O(1), no loops added
- Verification: Confirm no performance regression in benchmarks

### 10.4 Test Coverage Gaps

**Risk:** Edge cases not covered by initial test suite.

**Mitigation:** Comprehensive test matrix (§8.2) covers:
1. MOSFLM auto vs explicit
2. Non-MOSFLM conventions (all sources)
3. CLI detection (all explicit flags)
4. Header ingestion
5. Direct API usage
6. C↔PyTorch parity

**Residual Risk:** LOW (test matrix is comprehensive)

### 10.5 Backward Compatibility

**Risk:** Existing scripts/tests break after fix.

**Mitigation:**
1. Default `"auto"` preserves current behavior for unmodified instantiations
2. Only explicit user-provided beam centers change behavior (which is currently buggy)
3. Users explicitly setting beam centers WANT the fix (current behavior is wrong)

**Residual Risk:** VERY LOW (fix corrects broken behavior)

---

## 11. Implementation Checklist

### Phase C Implementation Tasks (from plans/active/detector-config.md)

- [ ] **C1: Update configuration layer**
  - [ ] Add `beam_center_source` field to `DetectorConfig` in `src/nanobrag_torch/config.py`
  - [ ] Add docstring explaining field semantics
  - [ ] Set default value to `"auto"`
  - [ ] (Optional) Add `__post_init__` validation

- [ ] **C2: Adjust CLI parsing**
  - [ ] Implement `determine_beam_center_source()` helper function in `src/nanobrag_torch/__main__.py`
  - [ ] Update CLI parsing to call helper and set `beam_center_source`
  - [ ] Add tracking for header-ingested beam centers (`_beam_center_from_header` flag)
  - [ ] Verify all 8 explicit flags are detected

- [ ] **C3: Apply conditional offset in Detector**
  - [ ] Update `beam_center_s_pixels` property in `src/nanobrag_torch/models/detector.py`
  - [ ] Update `beam_center_f_pixels` property
  - [ ] Add docstrings explaining MOSFLM offset logic
  - [ ] Verify device/dtype neutrality (no `.cpu()`/`.cuda()` calls)
  - [ ] Verify differentiability (no `.item()`/`.detach()` calls)

- [ ] **C4: Expand regression coverage**
  - [ ] Update `tests/test_detector_config.py` (2 existing tests)
  - [ ] Add 5 new test cases per §8.2
  - [ ] Add C↔PyTorch parity tests per §8.3
  - [ ] Verify all tests pass locally

- [ ] **C5: Targeted validation bundle**
  - [ ] Run: `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py`
  - [ ] Run: `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation`
  - [ ] Capture logs + artifacts under `reports/2026-01-test-suite-triage/phase_m3/<STAMP>/mosflm_fix/`
  - [ ] Generate `summary.md` with metrics

- [ ] **C6: Documentation sync**
  - [ ] Update `docs/architecture/detector.md` (§8.2, §9, new §9.1)
  - [ ] Update `docs/development/c_to_pytorch_config_map.md` (new section)
  - [ ] Update `docs/findings.md` (API-002 interaction note)
  - [ ] Add API usage warnings in config docstrings

- [ ] **C7: Ledger & tracker update**
  - [ ] Append Attempt log to `[DETECTOR-CONFIG-001]` in `docs/fix_plan.md`
  - [ ] Update `reports/2026-01-test-suite-triage/phase_j/.../remediation_tracker.md` (mark C8 resolved)
  - [ ] Update `plans/active/detector-config.md` (Phase C tasks → [D])

---

## 12. Exit Criteria

### 12.1 Code Completeness

- [ ] `DetectorConfig.beam_center_source` field added with proper typing
- [ ] CLI parsing detects all 8 explicit beam center flags
- [ ] Detector properties apply offset conditionally based on source
- [ ] No device/dtype neutrality violations introduced
- [ ] No differentiability breaks introduced

### 12.2 Test Coverage

- [ ] All existing tests updated and passing
- [ ] 5 new test cases added per §8.2
- [ ] C↔PyTorch parity validated for 3 cases per §8.3
- [ ] `test_at_parallel_003.py::test_detector_offset_preservation` PASSES
- [ ] Full targeted test suite passes: `pytest -v tests/test_detector_config.py tests/test_at_parallel_003.py tests/test_beam_center_offset.py`

### 12.3 Documentation

- [ ] `docs/architecture/detector.md` updated with new §9.1
- [ ] `docs/development/c_to_pytorch_config_map.md` updated with detection matrix
- [ ] `docs/findings.md` interaction note added
- [ ] API usage warnings added in config docstrings
- [ ] README_PYTORCH.md updated if user-facing changes

### 12.4 Parity Validation

- [ ] MOSFLM auto-calculated beam centers: C↔Py correlation ≥0.999
- [ ] MOSFLM explicit beam centers: C↔Py correlation ≥0.999
- [ ] XDS beam centers: C↔Py correlation ≥0.999
- [ ] All parity artifacts saved under `reports/.../mosflm_fix/parity/`

### 12.5 Regression Prevention

- [ ] Full Phase M chunked rerun executed (10-command ladder)
- [ ] Failure count ≤13 (Phase M baseline)
- [ ] No new failures introduced
- [ ] C8 cluster resolved (1 failure → 0 failures)
- [ ] Results documented in `reports/.../phase_m/<STAMP>/summary.md`

---

## 13. References

### 13.1 Normative Specifications

- **spec-a-core.md §§68-86:** Geometry & Conventions (MOSFLM beam center mapping)
- **arch.md §ADR-03:** Beam-center Mapping (MOSFLM) and +0.5 pixel Offsets
- **arch.md §7:** Geometry Model & Conventions (lines 223-227, MOSFLM row)

### 13.2 Architecture Documentation

- **docs/architecture/detector.md:** Detector component specification
- **docs/development/c_to_pytorch_config_map.md:** C-CLI to PyTorch configuration mapping
- **docs/debugging/detector_geometry_checklist.md:** Detector geometry debugging workflow

### 13.3 Testing Documentation

- **docs/development/testing_strategy.md:** Three-tier validation approach
- **docs/development/pytorch_runtime_checklist.md:** PyTorch runtime guardrails

### 13.4 Evidence & Analysis

- **reports/2026-01-test-suite-triage/phase_l/20251011T104618Z/detector_config/analysis.md:** Phase L targeted test results
- **reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md:** C8 cluster analysis and Option A recommendation

### 13.5 Planning Documents

- **plans/active/detector-config.md:** DETECTOR-CONFIG-001 implementation plan
- **plans/active/test-suite-triage.md:** Test suite triage and remediation phases
- **docs/fix_plan.md §[DETECTOR-CONFIG-001]:** Fix plan ledger entry

### 13.6 Related Findings

- **docs/findings.md API-002:** pix0 overrides beam center
- **docs/findings.md CONVENTION-001:** CUSTOM convention offset behavior

---

## Appendix A: Example CLI Commands

### A.1 Explicit Beam Center (No Offset)

```bash
nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 256 -Xbeam 12.8 -Ybeam 12.8

# Result: beam_center_source="explicit"
# MOSFLM +0.5 offset NOT applied
# beam_center in pixels = 128.0 exactly
```

### A.2 Auto-Calculated Beam Center (MOSFLM Offset Applied)

```bash
nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 256

# Result: beam_center_source="auto"
# MOSFLM +0.5 offset IS applied
# beam_center in pixels = 128.5 (default center + offset)
```

### A.3 Non-MOSFLM Convention (No Offset Regardless)

```bash
nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 256 -convention XDS

# Result: beam_center_source="auto" (or "explicit" if flags provided)
# XDS convention never applies offset
# beam_center in pixels = 128.0
```

---

## Appendix B: Test Code Examples

### B.1 MOSFLM Auto Beam Center Test

```python
def test_mosflm_auto_beam_center_offset():
    """Verify MOSFLM +0.5 offset IS applied to auto-calculated beam centers."""
    config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        beam_center_s_mm=51.2,
        beam_center_f_mm=51.2,
        pixel_size_mm=0.1,
        beam_center_source="auto",  # Auto-calculated default
        distance_mm=100.0,
        spixels=1024,
        fpixels=1024,
    )
    detector = Detector(config)

    # MOSFLM auto beam center should get +0.5 pixel offset
    expected_s = 51.2 / 0.1 + 0.5  # 512.5
    expected_f = 51.2 / 0.1 + 0.5  # 512.5

    assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(expected_s))
    assert torch.allclose(detector.beam_center_f_pixels, torch.tensor(expected_f))
```

### B.2 MOSFLM Explicit Beam Center Test

```python
def test_mosflm_explicit_beam_center_no_offset():
    """Verify MOSFLM +0.5 offset is NOT applied to explicit beam centers."""
    config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        beam_center_s_mm=51.2,
        beam_center_f_mm=51.2,
        pixel_size_mm=0.1,
        beam_center_source="explicit",  # User-provided value
        distance_mm=100.0,
        spixels=1024,
        fpixels=1024,
    )
    detector = Detector(config)

    # Explicit beam center should NOT get +0.5 pixel offset
    expected_s = 51.2 / 0.1  # 512.0 (no offset)
    expected_f = 51.2 / 0.1  # 512.0 (no offset)

    assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(expected_s))
    assert torch.allclose(detector.beam_center_f_pixels, torch.tensor(expected_f))
```

### B.3 Non-MOSFLM Convention Test

```python
@pytest.mark.parametrize("convention", [
    DetectorConvention.XDS,
    DetectorConvention.DIALS,
    DetectorConvention.CUSTOM,
])
@pytest.mark.parametrize("source", ["auto", "explicit"])
def test_non_mosflm_no_offset(convention, source):
    """Verify no offset applied for non-MOSFLM conventions regardless of source."""
    config = DetectorConfig(
        detector_convention=convention,
        beam_center_s_mm=51.2,
        beam_center_f_mm=51.2,
        pixel_size_mm=0.1,
        beam_center_source=source,
        distance_mm=100.0,
        spixels=1024,
        fpixels=1024,
    )
    detector = Detector(config)

    # Non-MOSFLM conventions should NEVER apply +0.5 offset
    expected = 51.2 / 0.1  # 512.0 (no offset)

    assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(expected))
    assert torch.allclose(detector.beam_center_f_pixels, torch.tensor(expected))
```

---

**Design Status:** ✅ Complete — Ready for implementation (Phase C)
**Next Step:** Supervisor approval → Implementation handoff to ralph
**Estimated Implementation Effort:** 2-3 hours (code changes + tests + docs)

