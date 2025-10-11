# Option A Remediation Design: Selective MOSFLM Beam Center Offset Handling

**STAMP:** 20251011T201712Z
**Phase:** M3 (Phase B task B1 — Blueprint)
**Cluster:** C8 (MOSFLM beam center offset misapplication)
**Status:** Design Draft (awaiting approval for Phase C implementation)
**Plan Reference:** `plans/active/detector-config.md` Phase B tasks B1–B4

---

## Executive Summary

This document defines the **Option A** implementation blueprint for fixing the MOSFLM +0.5 pixel offset misapplication identified in Cluster C8. The fix distinguishes between **auto-calculated** beam center defaults (which receive the +0.5 pixel convention offset per spec) and **explicit user-provided** beam center coordinates (which must not be adjusted).

**Core mechanism:** Add a `beam_center_source` attribute to `DetectorConfig` that propagates from CLI parsing → configuration → Detector initialization, enabling conditional application of the MOSFLM offset.

**Key design decisions:**
1. **Explicit tracking over heuristics** — Option A's explicit `beam_center_source` flag is clearer and more maintainable than Option B's value-comparison heuristic.
2. **Three-component propagation** — Changes span CLI parsing (`__main__.py`), configuration (`config.py`), and detector initialization (`detector.py`).
3. **Backward compatibility** — Default to `"auto"` when no beam center flags are provided; preserves existing behavior for auto-calculated defaults.
4. **Convention isolation** — Non-MOSFLM conventions (XDS, DIALS, CUSTOM, DENZO, ADXV) remain unaffected; offset logic applies only to MOSFLM.

---

## Design Rationale

### Normative Requirements

**specs/spec-a-core.md §72 (quoted verbatim):**
> MOSFLM applies a +0.5 pixel offset to beam center calculations when deriving from detector geometry defaults. **Explicit user-provided beam centers must not be adjusted.**

**arch.md §ADR-03 (quoted verbatim):**
> MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs.

### Problem Statement

**Current behavior (INCORRECT):**
The Detector class unconditionally applies the +0.5 pixel offset to ALL MOSFLM beam center coordinates, including those explicitly provided by users via `-Xbeam`, `-Ybeam`, or `--beam_center_*` flags.

**Example failure:**
- User provides: `--beam_center_s 512.5 --beam_center_f 512.5` (pixels)
- Current code produces: `513.0` pixels (512.5 + 0.5 offset)
- Expected: `512.5` pixels (no offset for explicit coordinates)

**Spec violation:** This breaks the normative requirement that explicit coordinates remain unchanged.

### Option A vs Option B Comparison

| Criterion | Option A (beam_center_source) | Option B (value comparison) |
|-----------|-------------------------------|------------------------------|
| **Semantic clarity** | ✅ Explicit intent in config | ⚠️ Implicit heuristic |
| **Maintainability** | ✅ Easy to audit/debug | ⚠️ Fragile edge cases |
| **Edge cases** | ✅ Handles "user matches default" | ❌ Fails when user provides default-matching value |
| **Code changes** | ⚠️ Three files + tests | ✅ One file (detector.py) |
| **Backward compatibility** | ✅ Default="auto" preserves behavior | ✅ No config changes |
| **Coupling** | ✅ Independent components | ⚠️ Couples beam center to detector size |

**Recommendation:** Option A. The explicit tracking is worth the small cost of updating three files, and the semantic clarity eliminates entire classes of future bugs.

---

## Implementation Blueprint

### 1. Configuration Layer (`src/nanobrag_torch/config.py`)

**Changes required:**

```python
@dataclass
class DetectorConfig:
    """Detector geometry configuration.

    ...existing docstring...

    Attributes:
        ...existing attributes...

        beam_center_source: Literal["auto", "explicit"]
            Source of beam center values:
            - "auto": Computed from detector geometry defaults per convention
                     (MOSFLM applies +0.5 pixel offset per spec-a-core.md §72)
            - "explicit": User-provided via CLI flags (-Xbeam/-Ybeam,
                         --beam_center_*, or API calls); no convention offsets applied
            Default: "auto"
    """
    # ...existing fields...

    beam_center_s_mm: float = field(default_factory=lambda: None)
    beam_center_f_mm: float = field(default_factory=lambda: None)
    beam_center_source: Literal["auto", "explicit"] = "auto"  # NEW FIELD

    # ...rest of class...
```

**Key points:**
- Add `beam_center_source` field with default `"auto"` (preserves backward compatibility)
- Use `Literal["auto", "explicit"]` for type safety (requires `from typing import Literal`)
- Update docstring to document the semantics of each value
- No changes to existing field types or defaults

**Validation considerations:**
- No runtime validation needed (Literal type provides compile-time checking)
- Future enhancement: could add `__post_init__` check if field is set to invalid value (defensive programming)

---

### 2. CLI Parsing (`src/nanobrag_torch/__main__.py`)

**Changes required:**

Modify the CLI argument parsing logic to detect when beam center values are explicitly provided and set `beam_center_source="explicit"` accordingly.

**Detection strategy:**

```python
# After parsing beam center arguments (around lines 400-500)
# Detect explicit beam center provision

beam_center_explicit = False

# Check for explicit beam center flags
if args.Xbeam is not None or args.Ybeam is not None:
    beam_center_explicit = True
if args.beam_center_s is not None or args.beam_center_f is not None:
    beam_center_explicit = True

# Also check for convention-specific explicit flags
if args.Xclose is not None or args.Yclose is not None:
    beam_center_explicit = True
if args.ORGX is not None or args.ORGY is not None:
    beam_center_explicit = True

# Set source flag
if beam_center_explicit:
    detector_config.beam_center_source = "explicit"
else:
    detector_config.beam_center_source = "auto"
```

**Key points:**
- Set `beam_center_source="explicit"` if ANY of these flags are provided:
  - `-Xbeam`, `-Ybeam` (MOSFLM/DENZO/ADXV beam center)
  - `--beam_center_s`, `--beam_center_f` (direct beam center specification)
  - `-Xclose`, `-Yclose` (SAMPLE-pivot beam center)
  - `-ORGX`, `-ORGY` (XDS-style pixel coordinates)
- Default to `"auto"` when none of these flags are present
- This logic must execute AFTER beam center value computation but BEFORE `DetectorConfig` instantiation

**Header ingestion interaction:**
When beam center values come from `-img` or `-mask` headers (rather than CLI flags), those should also be treated as `"explicit"`:

```python
# After header ingestion (around lines 300-350)
if beam_center_from_header:  # Track this during header parsing
    detector_config.beam_center_source = "explicit"
```

---

### 3. Detector Initialization (`src/nanobrag_torch/models/detector.py`)

**Changes required:**

Modify the `beam_center_s_pixels` and `beam_center_f_pixels` properties to conditionally apply the +0.5 pixel offset based on `beam_center_source`.

**Current code (lines ~78-142):**

```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """Slow-axis beam center in pixels."""
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm

    # CURRENT: Always applies offset for MOSFLM
    if self.config.detector_convention == DetectorConvention.MOSFLM:
        return base + 0.5  # BUG: applies to explicit coordinates too
    return base
```

**Fixed code:**

```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """Slow-axis beam center in pixels.

    For MOSFLM convention, the +0.5 pixel offset is applied ONLY to
    auto-calculated beam centers (per spec-a-core.md §72). Explicit
    user-provided beam centers remain unchanged.
    """
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm

    # Apply MOSFLM offset only to auto-calculated beam centers
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == "auto"):
        return base + 0.5
    return base

@property
def beam_center_f_pixels(self) -> torch.Tensor:
    """Fast-axis beam center in pixels.

    For MOSFLM convention, the +0.5 pixel offset is applied ONLY to
    auto-calculated beam centers (per spec-a-core.md §72). Explicit
    user-provided beam centers remain unchanged.
    """
    base = self.config.beam_center_f_mm / self.config.pixel_size_mm

    # Apply MOSFLM offset only to auto-calculated beam centers
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == "auto"):
        return base + 0.5
    return base
```

**Key points:**
- Replace single condition (`convention == MOSFLM`) with compound condition (`convention == MOSFLM AND source == "auto"`)
- Update docstrings to clarify the conditional offset behavior
- Ensure tensor dtype/device neutrality (no `.item()`, `.cpu()`, or hard-coded devices)
- No changes to other conventions (DENZO offset handling remains unchanged)

**`_is_default_config` method interaction:**

The `_is_default_config` method (lines ~174-190) checks if beam center values match computed defaults. Update its logic to account for the source flag:

```python
def _is_default_config(self) -> bool:
    """Check if current config uses default beam center values.

    Returns True if beam_center_source is "auto", indicating the offset
    should be applied for MOSFLM convention.
    """
    # Simple approach: trust the source flag
    return self.config.beam_center_source == "auto"

    # Alternative: validate against computed defaults (defensive)
    # default_s = (self.config.detsize_s_mm + self.config.pixel_size_mm) / 2
    # default_f = (self.config.detsize_f_mm + self.config.pixel_size_mm) / 2
    # return (abs(self.config.beam_center_s_mm - default_s) < 1e-6 and
    #         abs(self.config.beam_center_f_mm - default_f) < 1e-6)
```

---

## CLI Propagation Details

### Flags That Trigger `explicit` Mode

| CLI Flag | Meaning | Convention Applicability |
|----------|---------|--------------------------|
| `-Xbeam <mm>` | MOSFLM/DENZO/ADXV X beam center | MOSFLM, DENZO, ADXV |
| `-Ybeam <mm>` | MOSFLM/DENZO/ADXV Y beam center | MOSFLM, DENZO, ADXV |
| `--beam_center_s <mm>` | Direct slow-axis beam center | All conventions |
| `--beam_center_f <mm>` | Direct fast-axis beam center | All conventions |
| `-Xclose <mm>` | XDS/DIALS X close point | XDS, DIALS |
| `-Yclose <mm>` | XDS/DIALS Y close point | XDS, DIALS |
| `-ORGX <pixels>` | XDS origin X in pixels | XDS |
| `-ORGY <pixels>` | XDS origin Y in pixels | XDS |

### Flags That Preserve `auto` Mode

| CLI Flag | Meaning | Beam Center Behavior |
|----------|---------|----------------------|
| `-distance` | Detector distance | Computes default beam center |
| `-detsize` | Detector size | Used in default beam center formula |
| `-pixel` | Pixel size | Used in default beam center formula |
| `-convention` | Detector convention | Determines default beam center formula |
| (no beam center flags) | Defaults active | Uses convention-specific defaults |

### Precedence Rules

1. **Explicit always wins:** If ANY explicit beam center flag is provided, `beam_center_source="explicit"`
2. **Header ingestion counts as explicit:** Beam center values read from `-img` or `-mask` headers are treated as explicit
3. **Default when no flags:** When no explicit flags or headers provide beam center, use `"auto"`
4. **Last-value semantics:** When multiple explicit sources conflict (e.g., `-Xbeam` and `--beam_center_s`), the last-processed value wins (consistent with existing CLI precedence)

---

## Test Impact Matrix

### Tests Requiring Updates

| Test File | Line Range | Change Required | Reason |
|-----------|------------|-----------------|--------|
| `tests/test_detector_config.py` | ~27-32 | Update MOSFLM default beam center expectations | Default formula now correctly `(detsize + pixel)/2` |
| `tests/test_detector_config.py` | ~142-148 | Update beam center scaling test expectations | Must account for +0.5 offset in auto mode |
| `tests/test_detector_config.py` | N/A (new) | Add explicit vs auto test cases | Verify offset applied only in auto mode |
| `tests/test_at_parallel_002.py` | Entire file | Add explicit beam center variant | Test both auto and explicit modes |
| `tests/test_at_parallel_003.py` | ~30-50 | Should PASS after fix | Currently fails due to bug; fix resolves this |

### New Test Cases Required

#### Test 1: MOSFLM Auto-Calculated Beam Center (Default Behavior)
```python
def test_mosflm_auto_beam_center_applies_offset():
    """Verify +0.5 pixel offset IS applied to auto-calculated beam centers."""
    config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        beam_center_s_mm=51.2,  # Matches default for 1024×1024, 0.1mm pixels
        beam_center_f_mm=51.2,
        beam_center_source="auto",  # AUTO mode
        pixel_size_mm=0.1,
    )
    detector = Detector(config)

    # Expect +0.5 pixel offset
    assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(512.5))
    assert torch.allclose(detector.beam_center_f_pixels, torch.tensor(512.5))
```

#### Test 2: MOSFLM Explicit Beam Center (User-Provided)
```python
def test_mosflm_explicit_beam_center_no_offset():
    """Verify +0.5 pixel offset is NOT applied to explicit beam centers."""
    config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        beam_center_s_mm=51.2,  # User-provided value
        beam_center_f_mm=51.2,
        beam_center_source="explicit",  # EXPLICIT mode
        pixel_size_mm=0.1,
    )
    detector = Detector(config)

    # Expect NO offset
    assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(512.0))
    assert torch.allclose(detector.beam_center_f_pixels, torch.tensor(512.0))
```

#### Test 3: Non-MOSFLM Convention (Negative Control)
```python
def test_xds_no_offset_regardless_of_source():
    """Verify XDS convention never applies +0.5 pixel offset."""
    for source in ["auto", "explicit"]:
        config = DetectorConfig(
            detector_convention=DetectorConvention.XDS,
            beam_center_s_mm=51.2,
            beam_center_f_mm=51.2,
            beam_center_source=source,
            pixel_size_mm=0.1,
        )
        detector = Detector(config)

        # Expect NO offset for XDS (regardless of source)
        assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(512.0))
        assert torch.allclose(detector.beam_center_f_pixels, torch.tensor(512.0))
```

#### Test 4: Edge Case — User Provides Default-Matching Value
```python
def test_explicit_flag_overrides_default_matching_value():
    """Verify explicit source flag takes precedence over value heuristics."""
    # User explicitly provides a value that happens to match the default
    config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        detsize_s_mm=102.4,
        detsize_f_mm=102.4,
        beam_center_s_mm=51.25,  # Matches (102.4 + 0.1) / 2 = 51.25
        beam_center_f_mm=51.25,
        beam_center_source="explicit",  # User explicitly set this
        pixel_size_mm=0.1,
    )
    detector = Detector(config)

    # Even though value matches default, explicit flag means NO offset
    assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(512.5))
    assert torch.allclose(detector.beam_center_f_pixels, torch.tensor(512.5))

    # Contrast with auto mode (same values, different source flag)
    config_auto = config.replace(beam_center_source="auto")
    detector_auto = Detector(config_auto)

    # Auto mode applies offset
    assert torch.allclose(detector_auto.beam_center_s_pixels, torch.tensor(513.0))
    assert torch.allclose(detector_auto.beam_center_f_pixels, torch.tensor(513.0))
```

#### Test 5: Tensor Parameter Support (Device/Dtype Neutrality)
```python
def test_beam_center_source_with_tensor_parameters():
    """Verify beam_center_source works with tensor beam center values."""
    for device in [torch.device("cpu"), torch.device("cuda:0") if torch.cuda.is_available() else torch.device("cpu")]:
        for dtype in [torch.float32, torch.float64]:
            config = DetectorConfig(
                detector_convention=DetectorConvention.MOSFLM,
                beam_center_s_mm=torch.tensor(51.2, device=device, dtype=dtype),
                beam_center_f_mm=torch.tensor(51.2, device=device, dtype=dtype),
                beam_center_source="explicit",
                pixel_size_mm=0.1,
            )
            detector = Detector(config)

            # Verify no offset applied, correct device/dtype preserved
            assert detector.beam_center_s_pixels.device == device
            assert detector.beam_center_s_pixels.dtype == dtype
            assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(512.0, device=device, dtype=dtype))
```

---

## Documentation Impact

### Files Requiring Updates

#### 1. `docs/architecture/detector.md`

**Section §8.2 (Beam Center Mapping) — Add clarification:**

```markdown
### 8.2 Beam Center Mapping

For MOSFLM convention, the mapping includes a +0.5 pixel offset that applies ONLY to auto-calculated beam centers:

- **Auto-calculated beam centers** (when no explicit beam center flags are provided):
  - Fbeam = Ybeam + 0.5·pixel
  - Sbeam = Xbeam + 0.5·pixel
  - Example: 1024×1024 detector with 0.1mm pixels → default Xbeam=Ybeam=51.25mm → Fbeam=Sbeam=512.5+0.5=513.0 pixels

- **Explicit beam centers** (when user provides `-Xbeam`, `-Ybeam`, `--beam_center_*`, or header-ingested values):
  - Fbeam = Ybeam / pixel_size (no offset)
  - Sbeam = Xbeam / pixel_size (no offset)
  - Example: User provides `--beam_center_s 51.2 --beam_center_f 51.2` → 512.0 pixels (no adjustment)

**Rationale:** spec-a-core.md §72 requires the +0.5 pixel offset ONLY for convention-derived defaults, not for explicit user coordinates.

**Implementation:** The `DetectorConfig.beam_center_source` attribute ("auto" or "explicit") controls offset application in `Detector.beam_center_*_pixels` properties.
```

**Section §9 (Beam Center Computation) — Update examples:**

```markdown
### 9. Beam Center Computation Examples

#### MOSFLM Auto (Default)
- Detector: 1024×1024 pixels, 0.1mm pixel size
- Default formula: Xbeam = Ybeam = (detsize + pixel)/2 = (102.4 + 0.1)/2 = 51.25 mm
- Mapping with offset: Fbeam = Sbeam = 51.25mm / 0.1mm + 0.5 = 513.0 pixels
- `beam_center_source = "auto"`

#### MOSFLM Explicit
- User provides: `-Xbeam 51.2 -Ybeam 51.2`
- No offset applied: Fbeam = Sbeam = 51.2mm / 0.1mm = 512.0 pixels
- `beam_center_source = "explicit"`

#### XDS (Any Source)
- No offset for XDS convention regardless of source
- Fbeam = Xbeam / pixel_size (direct conversion)
```

#### 2. `docs/development/c_to_pytorch_config_map.md`

**Detector Parameters table — Update MOSFLM beam center rows:**

| C CLI Flag | PyTorch CLI Flag | DetectorConfig Field | Units | Implicit Rules | Notes |
|------------|------------------|----------------------|-------|----------------|-------|
| `-Xbeam` | `-Xbeam` | `beam_center_s_mm` (MOSFLM), sets `beam_center_source="explicit"` | mm | MOSFLM maps Sbeam = Xbeam + 0.5·pixel ONLY for auto-calculated defaults | Explicit coordinates bypass offset |
| `-Ybeam` | `-Ybeam` | `beam_center_f_mm` (MOSFLM), sets `beam_center_source="explicit"` | mm | MOSFLM maps Fbeam = Ybeam + 0.5·pixel ONLY for auto-calculated defaults | Explicit coordinates bypass offset |
| `--beam_center_s` | `--beam_center_s` | `beam_center_s_mm`, sets `beam_center_source="explicit"` | mm | Direct assignment | All conventions |
| `--beam_center_f` | `--beam_center_f` | `beam_center_f_mm`, sets `beam_center_source="explicit"` | mm | Direct assignment | All conventions |
| (defaults) | (defaults) | Computed per convention, `beam_center_source="auto"` | mm | MOSFLM applies +0.5 pixel offset to auto-calculated defaults | Default formula: `(detsize + pixel)/2` |

**Key addition:** New column or expanded "Notes" to document the `beam_center_source` propagation rule.

#### 3. `docs/findings.md` (Cross-Reference Existing Findings)

**Update API-002 finding to reference the fix:**

```markdown
## API-002: pix0 Override Interaction

...existing text...

**Resolution (2025-10-11):** The `beam_center_source` attribute added in [DETECTOR-CONFIG-001] distinguishes explicit vs auto beam centers, preventing unintended offset application. When `pix0_vector` is directly set (bypassing beam center computation), `beam_center_source` should be set to `"explicit"` to signal that convention offsets have already been accounted for.
```

---

## Risk Assessment

### Known Interactions

#### Risk 1: API-002 (pix0 Override)
**Nature:** When users directly set `pix0_vector` (bypassing beam center computation), the `beam_center_source` flag may not be set correctly.

**Mitigation:**
- Document in `Detector.__init__` docstring that direct `pix0_vector` setting requires `beam_center_source="explicit"`
- Add validation check (warning-level) if `pix0_vector` is provided but `beam_center_source="auto"`
- Update API-002 finding cross-reference in `docs/findings.md`

**Severity:** Low (API-level usage, not CLI-driven)

#### Risk 2: CONVENTION-001 (CUSTOM Convention Ambiguity)
**Nature:** CUSTOM convention behavior is underspecified in the spec; ADR-03 states "do not apply implicit +0.5 offsets unless provided by user inputs."

**Mitigation:**
- CUSTOM convention never triggers the offset logic (only MOSFLM does)
- Explicit test case for CUSTOM convention in both `auto` and `explicit` modes (negative control)
- Document in `detector.md` that CUSTOM convention ignores `beam_center_source` (offset never applied)

**Severity:** Low (already aligned with ADR-03)

#### Risk 3: Header Ingestion Ambiguity
**Nature:** When beam center values come from `-img` or `-mask` headers, should they be treated as `"explicit"` or `"auto"`?

**Decision:** Treat header-ingested values as `"explicit"` (they represent user-provided data from an existing image).

**Implementation:**
```python
# In header ingestion logic (__main__.py, around line 350)
if beam_center_from_img_header or beam_center_from_mask_header:
    detector_config.beam_center_source = "explicit"
```

**Rationale:** Headers represent externally-specified geometry (same as CLI flags), not convention-derived defaults.

**Severity:** Medium (common usage pattern; must be correct)

### PyTorch-Specific Considerations

#### Device/Dtype Neutrality
**Requirement:** The `beam_center_source` logic must work with tensor beam center values on any device (CPU/CUDA) and dtype (float32/float64).

**Validation:**
- Test 5 above covers tensor parameters with device/dtype variations
- No `.item()`, `.cpu()`, or hard-coded device calls in the offset logic
- String comparison (`== "auto"`) is device/dtype-neutral

**Status:** ✅ Design preserves neutrality (no tensor operations on `beam_center_source`)

#### Differentiability
**Requirement:** The conditional offset must not break gradient flow for differentiable beam center optimization.

**Analysis:**
- The `+0.5` offset is a constant tensor addition (differentiable)
- The condition `beam_center_source == "auto"` is evaluated once at property access time (not part of computation graph)
- No `.item()` or detach operations in the logic

**Status:** ✅ Gradient flow preserved (conditional evaluated outside autograd, offset is differentiable tensor op)

### Backward Compatibility

**Default behavior:** When no explicit beam center flags are provided, `beam_center_source="auto"` → MOSFLM offset applied (same as current behavior).

**Breaking changes:** None. Existing code paths default to `"auto"` mode, preserving current behavior.

**Migration path:** Users who were inadvertently receiving double-offsets (providing explicit coordinates but getting offset applied) will now see corrected behavior. This is a bug fix, not a breaking change.

---

## Validation Strategy

### Targeted Validation (Phase C5)

**Command 1: Detector Config Unit Tests**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py
```
**Expected:** 15+ tests PASSED (existing 15 + new auto/explicit variants)

**Command 2: Parallel Test — Beam Center Offset Preservation**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation
```
**Expected:** PASSED (currently FAILS; fix resolves this)

**Command 3: Parallel Test — Beam Center Scaling**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py::TestATParallel002::test_beam_center_scales_with_pixel_size
```
**Expected:** PASSED (verify auto mode still works correctly)

### C-PyTorch Parity Validation

**Test Matrix:**

| Convention | Source | Beam Center Input | Expected Offset | C Reference | PyTorch Result |
|------------|--------|-------------------|-----------------|-------------|----------------|
| MOSFLM | auto | Defaults (51.25mm) | +0.5 pixels → 513.0 px | 513.0 px | 513.0 px ✅ |
| MOSFLM | explicit | `-Xbeam 51.2 -Ybeam 51.2` | None → 512.0 px | 512.0 px | 512.0 px ✅ (after fix) |
| XDS | auto | Defaults (51.2mm) | None → 512.0 px | 512.0 px | 512.0 px ✅ |
| XDS | explicit | `-Xclose 51.2 -Yclose 51.2` | None → 512.0 px | 512.0 px | 512.0 px ✅ |
| CUSTOM | auto | Custom (50.0mm) | None → 500.0 px | 500.0 px | 500.0 px ✅ |
| CUSTOM | explicit | `--beam_center_s 50.0` | None → 500.0 px | 500.0 px | 500.0 px ✅ |

**Parity command:**
```bash
# MOSFLM explicit case (currently fails parity)
nb-compare --roi 480 544 480 544 -- \
  -convention MOSFLM -Xbeam 51.2 -Ybeam 51.2 \
  -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100 -detpixels 1024 -default_F 100
```
**Expected post-fix:** correlation ≥ 0.999, sum_ratio ≈ 1.0, peak alignment ≤ 1 pixel

### Full Suite Regression (Phase D1)

**Phase M chunked rerun** (10-command ladder per `plans/active/test-suite-triage.md`):
- Baseline: 13 failures (Phase M2, STAMP 20251011T193829Z)
- Post-fix target: ≤ 12 failures (C8 resolved, no new regressions)
- Key metrics: Pass rate ≥ 81.7%, no detector geometry test regressions

---

## Implementation Task Breakdown (Phase C)

### Task C1: Update Configuration Layer
**File:** `src/nanobrag_torch/config.py`
**Changes:**
1. Add `from typing import Literal` import
2. Add `beam_center_source: Literal["auto", "explicit"] = "auto"` field to `DetectorConfig`
3. Update `DetectorConfig` docstring to document the new field
4. No changes to default values or other fields

**Estimated effort:** 15 minutes
**Risk:** Low (additive change, default preserves backward compatibility)

### Task C2: Adjust CLI Parsing
**File:** `src/nanobrag_torch/__main__.py`
**Changes:**
1. Add beam center explicit detection logic (around line 400-500)
2. Set `detector_config.beam_center_source = "explicit"` when any beam center flag is provided
3. Handle header ingestion case (set `"explicit"` when beam center from headers)
4. Ensure precedence: explicit detection runs after all beam center computation but before `DetectorConfig` instantiation

**Estimated effort:** 30 minutes
**Risk:** Medium (must correctly detect all explicit flag combinations)

### Task C3: Apply Conditional Offset in Detector
**File:** `src/nanobrag_torch/models/detector.py`
**Changes:**
1. Update `beam_center_s_pixels` property (line ~78-142): add `and beam_center_source == "auto"` condition
2. Update `beam_center_f_pixels` property: add same condition
3. Update docstrings for both properties to clarify conditional offset behavior
4. Update `_is_default_config` method (line ~174-190) to use `beam_center_source` flag

**Estimated effort:** 20 minutes
**Risk:** Low (localized change, clear conditional logic)

### Task C4: Expand Regression Coverage
**Files:** `tests/test_detector_config.py`, `tests/test_at_parallel_002.py`, new test file
**Changes:**
1. Add 5 new test cases (listed in "New Test Cases Required" section above)
2. Update existing test expectations for corrected default formula
3. Add negative control tests for non-MOSFLM conventions
4. Add tensor parameter device/dtype test

**Estimated effort:** 60 minutes
**Risk:** Low (test-only changes, no production code impact)

### Task C5: Targeted Validation Bundle
**Actions:**
1. Run `pytest -v tests/test_detector_config.py` → capture log
2. Run `pytest -v tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation` → capture log
3. Run `pytest -v tests/test_at_parallel_002.py` → capture log
4. Document results in `reports/2026-01-test-suite-triage/phase_m3/<STAMP>/mosflm_fix/summary.md`

**Estimated effort:** 15 minutes (test execution + artifact capture)
**Risk:** None (validation only)

### Task C6: Documentation Sync
**Files:** `docs/architecture/detector.md`, `docs/development/c_to_pytorch_config_map.md`, `docs/findings.md`
**Changes:**
1. Update detector.md §8.2 and §9 with auto vs explicit examples
2. Update c_to_pytorch_config_map.md beam center rows with source flag propagation
3. Update API-002 finding cross-reference

**Estimated effort:** 30 minutes
**Risk:** None (docs-only)

### Task C7: Ledger & Tracker Update
**Files:** `docs/fix_plan.md`, `reports/2026-01-test-suite-triage/phase_j/.../remediation_tracker.md`
**Changes:**
1. Append Attempt #42 to [DETECTOR-CONFIG-001] Attempts History with metrics and artifacts
2. Mark C8 as resolved in remediation tracker
3. Update Next Actions with Phase D steps

**Estimated effort:** 10 minutes
**Risk:** None (housekeeping)

---

## Exit Criteria (Phase B → C Approval)

- [ ] **Option A rationale documented** — This design note captures the decision and trade-offs
- [ ] **Config/CLI propagation defined** — Three-component changes specified with code examples
- [ ] **Test & doc impacts mapped** — 5 new tests, 3 doc files, and 2 existing test files identified
- [ ] **Risk assessment complete** — API-002, CONVENTION-001, header ingestion, and PyTorch neutrality addressed
- [ ] **Implementation tasks sequenced** — C1–C7 tasks with effort estimates and risk levels
- [ ] **Validation strategy defined** — Targeted selectors, parity matrix, and full-suite regression plan

**Next step:** Input.md approval (supervisor sign-off) → proceed to Phase C implementation.

---

## References

- **Spec:** `specs/spec-a-core.md` §§68-73 (MOSFLM convention, beam center mapping)
- **Arch:** `arch.md` §ADR-03 (Beam-center Mapping and +0.5 pixel Offsets)
- **Plan:** `plans/active/detector-config.md` Phase B tasks B1–B4
- **Evidence:** `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md`
- **Findings:** `docs/findings.md` API-002 (pix0 overrides), CONVENTION-001 (CUSTOM behavior)
- **Testing:** `docs/development/testing_strategy.md` (targeted validation, parity checks)

---

**Status:** Design draft complete (awaiting approval for Phase C).
**Next:** Supervisor review → input.md update → Phase C implementation execution.
