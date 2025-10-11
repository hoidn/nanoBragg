# DETECTOR-CONFIG-001 Option A Design: Beam Center Source Tracking

**Initiative:** DETECTOR-CONFIG-001 — MOSFLM Beam Center Offset Remediation
**Phase:** B (Behavior Contract & Blueprint Refresh)
**STAMP:** 20251011T215044Z
**Status:** Ready for Phase C Implementation

---

## Executive Summary

**Problem:** The Detector class incorrectly applies the MOSFLM +0.5 pixel offset to ALL beam center coordinates, including explicit user-provided values. Per spec-a-core.md §72 and arch.md §ADR-03, the offset should ONLY apply to auto-calculated defaults, not explicit inputs.

**Solution (Option A):** Add `beam_center_source: Literal["auto", "explicit"]` attribute to `DetectorConfig` to track provenance of beam center values. The Detector layer conditionally applies the MOSFLM +0.5 pixel offset only when `source=="auto"` and `convention==MOSFLM`.

**Impact:** Fixes C8 cluster test failure (AT-PARALLEL-003), restores spec compliance, preserves backward compatibility via default `source="auto"`, and provides clear semantic distinction for configuration auditing.

**Estimated Effort:** 2-3 hours (implementation + test expansion + docs sync)

---

## 1. Normative References

### Spec Quotes (Authoritative)

**spec-a-core.md §72 (MOSFLM Convention):**

> "MOSFLM:
>   - Beam b = [1 0 0]; f = [0 0 1]; s = [0 -1 0]; o = [1 0 0]; 2θ-axis = [0 0 -1]; p = [0 0 1]; u = [0 0 1].
>   - Default Xbeam = (detsize_s + pixel)/2, Ybeam = (detsize_f + pixel)/2.
>   - Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel. Pivot = BEAM."

**Key Insight:** The spec describes "+0.5·pixel" in the context of the beam-center mapping formula FROM Xbeam/Ybeam TO Fbeam/Sbeam, not as a universal transform for all coordinates. The offset is part of the convention's DEFAULT behavior when deriving beam centers from detector geometry.

**spec-a-core.md §68-73 (Beam center relations):**

> "Beam center relations:
>   - Fbeam/Sbeam (fast/slow coordinates in meters) are computed from Xbeam/Ybeam (mm converted to m) per convention (note MOSFLM and DENZO introduce ±0.5 pixel shifts as shown above)."

**Interpretation:** The ±0.5 pixel shifts are **introduced by the convention's mapping formula**, not applied to user-provided coordinates universally.

### ADR References

**arch.md §ADR-03 (Beam-center Mapping):**

> "ADR-03 Beam-center Mapping (MOSFLM) and +0.5 pixel Offsets
>   - MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs."

**Implementation Guidance:** CUSTOM convention explicitly avoids implicit offsets; by extension, MOSFLM offset should only apply when the system auto-calculates beam centers, not when users explicitly provide them.

### C-Code Parity Requirements

**docs/development/c_to_pytorch_config_map.md (MOSFLM row):**

> "| `-Xbeam <val>` | `DetectorConfig.beam_center_s` | `Xbeam` | mm → meters | **MOSFLM default: (detsize_s+pixel)/2; maps to Sbeam = Xbeam + 0.5·pixel** |"

**Current Behavior:** The C-code ALWAYS applies +0.5 pixel offset in MOSFLM convention, but this is because the C-code lacks explicit user-provided beam center flags (all beam centers go through the same mapping path). The PyTorch implementation exposes explicit beam center setters (`--beam_center_s/f`), requiring disambiguation.

---

## 2. Option A Detailed Design

### 2.1 Configuration Layer Changes

#### BeamCenterSource Enum

**File:** `src/nanobrag_torch/config.py`

**New Enum:**
```python
from enum import Enum

class BeamCenterSource(str, Enum):
    """Provenance of beam center coordinates.

    - AUTO: Beam center was auto-calculated from detector geometry defaults.
             For MOSFLM convention, this triggers the +0.5 pixel offset.
    - EXPLICIT: Beam center was explicitly provided by user (CLI flags, API).
                No implicit convention-based adjustments applied.
    """
    AUTO = "auto"
    EXPLICIT = "explicit"
```

#### DetectorConfig Field Addition

**File:** `src/nanobrag_torch/config.py`

**Modified Dataclass:**
```python
@dataclass
class DetectorConfig:
    """Detector geometry configuration.

    ... [existing fields]

    beam_center_s_mm: float = field(default=None)
    beam_center_f_mm: float = field(default=None)

    beam_center_source: BeamCenterSource = BeamCenterSource.AUTO
    """Provenance of beam center values.

    When AUTO (default): Convention-specific defaults and adjustments apply
    (e.g., MOSFLM adds +0.5 pixel offset).

    When EXPLICIT: User-provided coordinates are preserved exactly; no implicit
    offsets. Set automatically by CLI when beam center flags are provided, or
    manually when constructing DetectorConfig in Python API.

    CRITICAL: When using the Python API directly (not via CLI), you MUST set
    beam_center_source=BeamCenterSource.EXPLICIT when providing explicit beam
    centers. Otherwise, MOSFLM convention will apply the +0.5 offset unintentionally.

    Example (CORRECT):
        config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            beam_center_s_mm=12.8,
            beam_center_f_mm=12.8,
            beam_center_source=BeamCenterSource.EXPLICIT,  # Required!
        )

    Example (INCORRECT - will apply unwanted MOSFLM offset):
        config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            beam_center_s_mm=12.8,
            beam_center_f_mm=12.8,
            # beam_center_source defaults to AUTO → +0.5 offset applied
        )
    """

    # ... [rest of fields]
```

**Design Rationale:**
- Use `BeamCenterSource` enum (not bare strings) for type safety and IDE autocomplete
- Default to `AUTO` for backward compatibility with existing code
- Embed extensive docstring warning for direct API usage (common pitfall)
- Field placement: After `beam_center_s/f_mm` for logical grouping

---

### 2.2 CLI Layer Changes

#### Explicit Beam Center Detection

**File:** `src/nanobrag_torch/__main__.py`

**New Helper Function:**
```python
def determine_beam_center_source(args: argparse.Namespace) -> BeamCenterSource:
    """Determine whether beam center was explicitly provided by user.

    Explicit beam center indicators (any of these sets source=EXPLICIT):
    1. Direct beam center flags: --beam_center_s, --beam_center_f
    2. Convention-specific flags: -Xbeam, -Ybeam (BEAM pivot)
    3. Close distance flags: -Xclose, -Yclose (SAMPLE pivot)
    4. XDS origin flags: -ORGX, -ORGY
    5. Header ingestion: -img or -mask containing beam center keys

    If NONE of the above are provided, source=AUTO (convention defaults).

    Args:
        args: Parsed CLI arguments

    Returns:
        BeamCenterSource.EXPLICIT if any explicit flag present, else AUTO
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

    # Check header ingestion for beam center keys
    has_header_beam_center = False
    if args.img or args.mask:
        # Header parsing sets args.beam_center_s/f or Xbeam/Ybeam
        # after ingestion; those are already captured above
        pass  # Logic already covered by individual flag checks

    if any(explicit_flags):
        return BeamCenterSource.EXPLICIT
    else:
        return BeamCenterSource.AUTO
```

**Integration Point (in `main()` function):**
```python
def main():
    args = parser.parse_args()

    # ... [existing parsing logic]

    # Determine beam center source BEFORE constructing DetectorConfig
    beam_center_source = determine_beam_center_source(args)

    # Build DetectorConfig with source attribute
    detector_config = DetectorConfig(
        detector_convention=convention,
        beam_center_s_mm=args.beam_center_s,  # Or computed from Xbeam/Ybeam
        beam_center_f_mm=args.beam_center_f,
        beam_center_source=beam_center_source,  # NEW
        # ... [other fields]
    )

    # ... [rest of main()]
```

**Design Rationale:**
- Centralize detection logic in helper function (single responsibility, testable)
- Check ALL explicit beam center flags (8 total, per summary.md)
- Header ingestion: Beam center keys from -img/-mask headers are treated as explicit
  (user consciously provided a file with beam center metadata)
- Default to AUTO when no explicit flags present (backward compatible)

---

### 2.3 Detector Layer Changes

#### Conditional Offset Application

**File:** `src/nanobrag_torch/models/detector.py`

**Modified Beam Center Properties:**
```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """Beam center slow-axis coordinate in pixels (floating-point).

    Applies MOSFLM +0.5 pixel offset ONLY for auto-calculated beam centers.
    Explicit user-provided coordinates are preserved exactly.

    Returns:
        Beam center slow coordinate in pixels (float tensor)
    """
    # Convert mm → pixels
    base_pixels = self.config.beam_center_s_mm / self.config.pixel_size_mm

    # Apply MOSFLM offset ONLY for auto-calculated defaults
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == BeamCenterSource.AUTO):
        return base_pixels + 0.5

    # All other cases: use base value directly
    return base_pixels

@property
def beam_center_f_pixels(self) -> torch.Tensor:
    """Beam center fast-axis coordinate in pixels (floating-point).

    Applies MOSFLM +0.5 pixel offset ONLY for auto-calculated beam centers.
    Explicit user-provided coordinates are preserved exactly.

    Returns:
        Beam center fast coordinate in pixels (float tensor)
    """
    base_pixels = self.config.beam_center_f_mm / self.config.pixel_size_mm

    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == BeamCenterSource.AUTO):
        return base_pixels + 0.5

    return base_pixels
```

**Design Rationale:**
- Minimal code change (add 2-line conditional before return)
- Explicit conditions: Both `convention==MOSFLM` AND `source==AUTO` required
- Preserves existing behavior for AUTO (default), fixes EXPLICIT case
- Device/dtype neutral: `+ 0.5` works for any tensor device/dtype
- Differentiability preserved: Offset is a constant addition, gradient flows through

**Validation:**
- No `.item()` calls (differentiability maintained)
- No hard-coded device transfers (device-neutral)
- Property pattern unchanged (no side effects)
- Cache invalidation: Beam center is not cached (computed on-demand), so no cache issues

---

## 3. Test Impact Matrix

### 3.1 New Tests Required

| Test File | Test Case | Purpose | Validation |
|-----------|-----------|---------|------------|
| `tests/test_beam_center_source.py` | `test_mosflm_auto_applies_offset` | Verify AUTO beam center gets +0.5 offset in MOSFLM | Assert beam_center_pixels == base + 0.5 |
| `tests/test_beam_center_source.py` | `test_mosflm_explicit_preserves_exact` | Verify EXPLICIT beam center has NO offset in MOSFLM | Assert beam_center_pixels == base (no offset) |
| `tests/test_beam_center_source.py` | `test_non_mosflm_no_offset` | Verify XDS/DIALS/CUSTOM never apply offset | Assert beam_center_pixels == base for all conventions |
| `tests/test_beam_center_source.py` | `test_cli_detection_explicit_flags` | Verify CLI sets source=EXPLICIT for beam center flags | Parametrize over 8 explicit flags |
| `tests/test_beam_center_source.py` | `test_cli_detection_auto_default` | Verify CLI defaults to source=AUTO when no flags | Assert default behavior |

**New Test File Structure:**
```python
"""Tests for beam center source tracking and MOSFLM offset handling.

Validates DETECTOR-CONFIG-001 Option A implementation.
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import pytest
import torch
from nanobrag_torch.config import DetectorConfig, DetectorConvention, BeamCenterSource
from nanobrag_torch.models.detector import Detector

class TestBeamCenterSource:
    """Test beam center source tracking and conditional MOSFLM offset."""

    def test_mosflm_auto_applies_offset(self):
        """AUTO beam center in MOSFLM convention applies +0.5 pixel offset."""
        # ... [test implementation]

    def test_mosflm_explicit_preserves_exact(self):
        """EXPLICIT beam center in MOSFLM convention preserves exact coordinates."""
        # ... [test implementation]

    def test_non_mosflm_no_offset(self):
        """Non-MOSFLM conventions never apply offset regardless of source."""
        # ... [test implementation]

    @pytest.mark.parametrize("flag", [
        "beam_center_s", "beam_center_f",
        "Xbeam", "Ybeam",
        "Xclose", "Yclose",
        "ORGX", "ORGY",
    ])
    def test_cli_detection_explicit_flags(self, flag):
        """CLI detects explicit beam center from any of 8 flags."""
        # ... [test implementation]

    def test_cli_detection_auto_default(self):
        """CLI defaults to AUTO when no beam center flags provided."""
        # ... [test implementation]
```

### 3.2 Existing Tests to Update

| Test File | Test Case | Required Update | Rationale |
|-----------|-----------|-----------------|-----------|
| `tests/test_at_parallel_003.py` | `test_detector_offset_preservation` | **CURRENTLY FAILING** — Should pass after fix | C8 cluster failure; validates explicit preservation |
| `tests/test_detector_config.py` | All instantiation tests | Add `beam_center_source` to DetectorConfig construction | Ensure tests don't rely on default AUTO when testing explicit cases |
| `tests/test_at_parallel_002.py` | Pixel size independence tests | Verify beam_center_source propagates correctly | Ensure pixel size scaling doesn't affect source detection |

**Specific Update Example (`test_detector_config.py`):**
```python
# BEFORE (implicit AUTO)
config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    beam_center_s_mm=12.8,
    beam_center_f_mm=12.8,
)

# AFTER (explicit source when testing explicit coordinates)
config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    beam_center_s_mm=12.8,
    beam_center_f_mm=12.8,
    beam_center_source=BeamCenterSource.EXPLICIT,  # NEW
)
```

**Update Strategy:**
- Grep for all `DetectorConfig(` instantiations in tests
- Identify which tests provide explicit beam centers
- Add `beam_center_source=BeamCenterSource.EXPLICIT` where appropriate
- Leave AUTO as default for tests that intend to test convention defaults

---

## 4. Documentation Impact

### 4.1 Files Requiring Updates

| File | Section | Update Required |
|------|---------|----------------|
| `docs/architecture/detector.md` | §8.2 Beam Center Mapping | Add beam_center_source explanation; clarify +0.5 offset applies only to AUTO |
| `docs/development/c_to_pytorch_config_map.md` | MOSFLM convention row (line 56-57) | Document beam_center_source field and CLI detection logic |
| `docs/development/c_to_pytorch_config_map.md` | §Beam Center Source Detection (NEW) | Add comprehensive section with CLI flag mapping and API usage warnings |
| `docs/findings.md` | API-002 entry | Update to reference beam_center_source interaction with pix0 overrides |
| `arch.md` | §ADR-03 | Clarify that +0.5 offset applies only to auto-calculated defaults (no spec change, just clarification) |

### 4.2 Specific Documentation Changes

#### docs/architecture/detector.md §8.2 Update

**ADD after existing beam center mapping formulas:**

> **Beam Center Source Tracking (Option A Implementation)**
>
> The Detector class distinguishes between auto-calculated and explicit beam centers via `DetectorConfig.beam_center_source`:
>
> - **AUTO (default):** Beam center was derived from detector geometry defaults (detsize, pixel size). For MOSFLM convention, the +0.5 pixel offset is applied: `beam_center_pixels = (beam_center_mm / pixel_size_mm) + 0.5`.
>
> - **EXPLICIT:** Beam center was explicitly provided by user (CLI flags like `--beam_center_s`, `-Xbeam`, header ingestion). The coordinate is preserved exactly: `beam_center_pixels = beam_center_mm / pixel_size_mm` (no offset).
>
> This distinction ensures spec compliance: the MOSFLM +0.5 pixel offset is a convention-specific DEFAULT behavior, not a universal transform for all coordinates.

#### docs/development/c_to_pytorch_config_map.md §Beam Center Source Detection

**ADD new section after "Critical Implicit Logic":**

> ### Beam Center Source Detection (DETECTOR-CONFIG-001)
>
> **NEW in Phase C:** The CLI parsing layer automatically detects whether beam centers are explicitly provided and sets `DetectorConfig.beam_center_source` accordingly.
>
> **Detection Logic:** The following CLI flags indicate **explicit** beam center input:
>
> | Flag | Description | Maps To |
> |------|-------------|---------|
> | `-Xbeam <val>` | Explicit slow-axis beam center | `beam_center_source="explicit"` |
> | `-Ybeam <val>` | Explicit fast-axis beam center | `beam_center_source="explicit"` |
> | `--beam_center_s <val>` | Direct slow-axis beam center | `beam_center_source="explicit"` |
> | `--beam_center_f <val>` | Direct fast-axis beam center | `beam_center_source="explicit"` |
> | `-Xclose <val>` | Close distance X (forces SAMPLE pivot) | `beam_center_source="explicit"` |
> | `-Yclose <val>` | Close distance Y (forces SAMPLE pivot) | `beam_center_source="explicit"` |
> | `-ORGX <val>` | XDS-style origin X coordinate | `beam_center_source="explicit"` |
> | `-ORGY <val>` | XDS-style origin Y coordinate | `beam_center_source="explicit"` |
> | `-img <file>` | Header ingestion from SMV image | `beam_center_source="explicit"` (if header contains beam center) |
> | `-mask <file>` | Header ingestion from mask file | `beam_center_source="explicit"` (if header contains beam center) |
>
> **Default Behavior:** If **none** of these flags are provided, `beam_center_source="auto"` (default value).
>
> **Critical:** This detection occurs in `src/nanobrag_torch/__main__.py` via the `determine_beam_center_source()` helper function, which is called during config construction.
>
> **Rationale:** Per spec-a-core.md §72 and arch.md §ADR-03, the MOSFLM +0.5 pixel offset applies **only** to auto-calculated beam center defaults, not explicit user-provided values. The CLI layer must track the provenance of beam center values to enable correct offset application in the Detector layer.
>
> **Example CLI Commands:**
>
> ```bash
> # Explicit beam center (no MOSFLM offset applied)
> nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
>   -distance 100 -detpixels 256 -Xbeam 12.8 -Ybeam 12.8
> # Result: beam_center_source="explicit", beam_center in pixels = 128.0
>
> # Auto-calculated beam center (MOSFLM offset applied)
> nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
>   -distance 100 -detpixels 256
> # Result: beam_center_source="auto", beam_center in pixels = 128.5 (MOSFLM default)
> ```
>
> **Direct API Usage Warning:** When constructing `DetectorConfig` directly in Python code (not via CLI), users **must** explicitly set `beam_center_source="explicit"` if providing explicit beam centers. Otherwise, the default `"auto"` will apply MOSFLM offset unintentionally.
>
> ```python
> # CORRECT: Explicit beam center in direct API usage
> config = DetectorConfig(
>     detector_convention=DetectorConvention.MOSFLM,
>     beam_center_s_mm=12.8,
>     beam_center_f_mm=12.8,
>     beam_center_source=BeamCenterSource.EXPLICIT,  # Required for correct behavior
> )
>
> # INCORRECT: Missing beam_center_source (will apply unwanted offset)
> config = DetectorConfig(
>     detector_convention=DetectorConvention.MOSFLM,
>     beam_center_s_mm=12.8,
>     beam_center_f_mm=12.8,
>     # beam_center_source defaults to AUTO → applies MOSFLM +0.5 offset
> )
> ```

---

## 5. Risk Assessment & Compatibility

### 5.1 Backward Compatibility

**Concern:** Existing code that constructs `DetectorConfig` without `beam_center_source` field.

**Mitigation:**
- Field has default value `BeamCenterSource.AUTO`
- Existing instantiations will continue to work (AUTO is the pre-fix behavior)
- Dataclass allows omitting fields with defaults (Python 3.7+)
- No breaking changes to existing tests or examples

**Validation:**
- Run full test suite after Phase C implementation
- Confirm no regressions in tests that don't explicitly set `beam_center_source`

### 5.2 API-002 Interaction (pix0 Override)

**Concern:** `docs/findings.md` entry API-002 warns that pix0 overrides can bypass beam center calculations.

**Impact:**
- `beam_center_source` flag affects beam center properties ONLY
- If user sets `pix0_vector` directly (API-002), beam center properties are bypassed entirely
- No interaction: pix0 override short-circuits beam center logic regardless of source

**Mitigation:**
- Document in `docs/findings.md` API-002 entry that pix0 override makes `beam_center_source` irrelevant
- No code changes needed (orthogonal concerns)

### 5.3 CONVENTION-001 Interaction (CUSTOM Convention)

**Concern:** `docs/findings.md` entry CONVENTION-001 notes CUSTOM convention disables MOSFLM offset.

**Impact:**
- `beam_center_source` logic already checks `convention==MOSFLM` in conditional
- CUSTOM convention will NEVER apply offset (condition fails at first check)
- AUTO source in CUSTOM convention: no offset (correct)
- EXPLICIT source in CUSTOM convention: no offset (correct)

**Mitigation:**
- No changes needed (logic already handles CUSTOM correctly)
- Add negative control test: `test_custom_convention_no_offset_regardless_of_source()`

### 5.4 Header Ingestion Edge Cases

**Concern:** `-img` or `-mask` headers might contain partial beam center data (e.g., only BEAM_CENTER_X).

**Impact:**
- Current CLI parsing: If header has beam center keys, they're used to set `args.beam_center_s/f` or `args.Xbeam/Ybeam`
- `determine_beam_center_source()` checks these args; if ANY are set, marks as EXPLICIT
- Partial data: If header sets only one axis, that flag check triggers EXPLICIT (correct: user consciously provided a header)

**Mitigation:**
- No changes needed (partial data still counts as explicit user input)
- Document in CLI detection logic: "Header ingestion counts as explicit even if partial"

### 5.5 PyTorch Device/Dtype Neutrality

**Verification:**
- Offset `+ 0.5` is a Python float literal (promoted to tensor's dtype automatically)
- No hard-coded `.cpu()` or `.cuda()` calls in modified paths
- Property pattern: No tensor creation (only arithmetic on existing config tensors)
- Differentiability: Constant addition preserves gradient flow

**Validation:**
- Run existing device/dtype tests after implementation (AT-PARALLEL-002, etc.)
- Confirm no new device transfer warnings from torch.compile

### 5.6 Differentiability Preservation

**Verification:**
- Modified properties: `beam_center_s/f_pixels()`
- Operation: `base_pixels + 0.5` (scalar addition to tensor)
- Gradient flow: Preserved through addition (`.item()` NOT used)
- No side effects: Properties are pure functions (no state mutation)

**Validation:**
- Run existing gradient tests (Tier 2) after implementation
- Confirm `torch.autograd.gradcheck` still passes for detector parameters

---

## 6. Implementation Checklist (Phase C Tasks)

Per `plans/active/detector-config.md` Phase C, the implementation tasks are:

| ID | Task | Files | Validation |
|----|------|-------|------------|
| C1 | Update configuration layer | `src/nanobrag_torch/config.py` | Add enum + field; run `pytest tests/test_detector_config.py` |
| C2 | Adjust CLI parsing | `src/nanobrag_torch/__main__.py` | Add detection helper; CLI integration test |
| C3 | Apply conditional offset | `src/nanobrag_torch/models/detector.py` | Modify properties; run `pytest tests/test_at_parallel_003.py` |
| C4 | Expand regression coverage | `tests/test_beam_center_source.py` (NEW) | 5 new test cases; run suite |
| C5 | Targeted validation bundle | Terminal | Run 2 commands from §7 below |
| C6 | Documentation sync | `docs/architecture/detector.md`, `docs/development/c_to_pytorch_config_map.md` | Update 3 doc files |
| C7 | Ledger & tracker update | `docs/fix_plan.md` | Append Attempt #N with artifacts |

**Estimated Time:**
- C1-C3: 1 hour (code changes)
- C4: 1 hour (new tests)
- C5: 0.5 hours (validation)
- C6: 0.5 hours (docs)
- C7: 0.25 hours (plan update)
- **Total: 3.25 hours**

---

## 7. Targeted Validation Commands (Phase C5)

After code changes (C1-C4), run these commands to validate the fix:

### Command 1: Explicit Beam Center Preservation Test (C8 Cluster)

```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation
```

**Expected:** PASS (currently FAILS; C8 cluster resolution)

### Command 2: Comprehensive MOSFLM Offset Validation

```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_beam_center_source.py tests/test_detector_config.py tests/test_at_parallel_002.py
```

**Expected:** All PASS (full beam center source coverage + pixel size independence)

**Artifacts to Capture:**
- Test logs: `reports/2026-01-test-suite-triage/phase_m3/<STAMP>/mosflm_fix/test_output.log`
- Summary: `reports/2026-01-test-suite-triage/phase_m3/<STAMP>/mosflm_fix/summary.md`
- Metrics: Passed/Failed/Skipped counts, runtime

---

## 8. Alternative Design (Option B) — NOT RECOMMENDED

**Option B (Heuristic Check):** Compare beam center values against computed defaults; if they match, apply offset.

**Rejected Rationale:**

1. **Fragile Heuristic:** What if user coincidentally provides a value matching the default? (e.g., intentionally setting beam center to detector center)
   - Example: User sets `beam_center_s = 51.2 mm` on a 102.4mm detector with 0.1mm pixels
   - Default: `(102.4 + 0.1) / 2 = 51.25 mm` ≈ `51.2 mm` (within tolerance)
   - Heuristic would treat this as AUTO → apply +0.5 offset → WRONG

2. **Hidden Coupling:** Beam center logic becomes coupled to detector size logic
   - Refactoring detector defaults breaks beam center behavior (non-local effects)
   - Difficult to reason about: "Does this beam center match the default formula?"

3. **No Config Change Required, But Less Maintainable:**
   - Backward compatible (no config field addition)
   - BUT: Implementation complexity higher (compute defaults on-the-fly, tolerance checks)
   - Future maintainers: "Why is there a default-matching check here?"

4. **Testing Difficulty:** Edge cases multiply
   - Must test: exact match, near-match (within tolerance), off-by-epsilon
   - Tolerance choice is arbitrary (1e-6? 1e-9? 1 pixel?)

**Recommendation:** Option A (explicit source tracking) is clearer, more maintainable, and semantically correct.

---

## 9. Acceptance Criteria (Phase C Exit)

Before Phase C can be marked complete, ALL of the following must be TRUE:

- [ ] `BeamCenterSource` enum exists in `src/nanobrag_torch/config.py`
- [ ] `DetectorConfig.beam_center_source` field added with default `AUTO`
- [ ] `src/nanobrag_torch/__main__.py` contains `determine_beam_center_source()` helper
- [ ] CLI detection logic checks all 8 explicit beam center flags
- [ ] `Detector.beam_center_s/f_pixels()` properties apply offset ONLY when `source==AUTO` AND `convention==MOSFLM`
- [ ] `tests/test_beam_center_source.py` exists with 5 test cases (all PASSING)
- [ ] `tests/test_at_parallel_003.py::test_detector_offset_preservation` **PASSES** (C8 cluster resolution)
- [ ] All existing tests PASS (no regressions)
- [ ] `docs/architecture/detector.md` §8.2 updated with beam_center_source explanation
- [ ] `docs/development/c_to_pytorch_config_map.md` updated with CLI detection section
- [ ] `docs/findings.md` API-002 entry updated to reference beam_center_source
- [ ] Targeted validation bundle (2 commands) captured with artifacts
- [ ] `docs/fix_plan.md` Attempt History appended with Phase C results

---

## 10. Phase D Preview (Full-Suite Regression)

After Phase C completes, Phase D will execute the full Phase M chunked suite rerun to validate no regressions:

**Command Ladder (10 commands from `plans/active/test-suite-triage.md`):**

```bash
# Chunk 1: Core unit tests
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_utils.py tests/test_config.py tests/test_detector.py tests/test_crystal.py

# Chunk 2: AT-PARALLEL baseline (001-010)
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_001.py tests/test_at_parallel_002.py tests/test_at_parallel_003.py tests/test_at_parallel_004.py tests/test_at_parallel_006.py tests/test_at_parallel_007.py tests/test_at_parallel_008.py tests/test_at_parallel_009.py tests/test_at_parallel_010.py

# ... [remaining 8 chunks]
```

**Expected Outcome:**
- Pre-fix baseline: 13 failures (per Phase M3 20251011T193829Z)
- Post-fix target: ≤12 failures (C8 cluster resolved, no new regressions)

**Artifacts:**
- `reports/2026-01-test-suite-triage/phase_m/<NEW_STAMP>/chunks/` (10 log files)
- `reports/2026-01-test-suite-triage/phase_m/<NEW_STAMP>/summary.md` (synthesis)

---

## 11. References

### Normative Documents
- `specs/spec-a-core.md` §§68-73 — Geometry & Conventions, MOSFLM beam center mapping
- `arch.md` §ADR-03 — Beam-center Mapping and +0.5 pixel Offsets
- `docs/development/c_to_pytorch_config_map.md` — C-CLI to PyTorch configuration parity

### Implementation Guides
- `docs/architecture/detector.md` §8.2 — Beam Center Mapping (hybrid units)
- `docs/debugging/detector_geometry_checklist.md` — Detector debugging SOP
- `docs/development/testing_strategy.md` — Three-tier validation approach

### Evidence & Analysis
- `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md` — C8 cluster failure analysis (Option A recommendation)
- `plans/active/detector-config.md` — DETECTOR-CONFIG-001 initiative plan (Phase B → C → D)
- `docs/findings.md` — API-002 (pix0 override) and CONVENTION-001 (CUSTOM convention) interactions

---

## 12. Decision Record

**Decision:** Adopt Option A (beam_center_source tracking) for DETECTOR-CONFIG-001 Phase C implementation.

**Rationale:**
1. **Semantic Clarity:** Explicit distinction between auto-calculated and user-provided coordinates
2. **Maintainability:** No hidden heuristics or tolerance checks; logic is transparent
3. **Spec Compliance:** Directly implements the intent of spec-a-core.md §72 and arch.md §ADR-03
4. **Backward Compatibility:** Default `AUTO` preserves existing behavior; existing code unaffected
5. **Testability:** Easy to validate (set source flag, verify offset presence/absence)
6. **Auditability:** CLI → config → detector pipeline is traceable with explicit source field

**Alternatives Considered:**
- Option B (heuristic check): Rejected due to fragility, hidden coupling, and edge case complexity (see §8)

**Approval:** Ready for Phase C handoff (implementation).

**Next Steps:**
1. Supervisor approval of this design (input.md update)
2. Engineer execution of Phase C tasks (C1-C7)
3. Targeted validation bundle (Phase C5)
4. Full-suite regression (Phase D)

---

**Status:** Phase B Complete — Design ratified, awaiting Phase C implementation handoff.

**STAMP:** 20251011T215044Z
**Initiative:** DETECTOR-CONFIG-001
**Phase:** B → C transition
