# Option A: Beam Center Source Tracking Design

**STAMP:** 20251011T221246Z
**Phase:** M3
**Initiative:** DETECTOR-CONFIG-001
**Status:** Design Complete → Ready for Implementation

---

## Executive Summary

This design specifies the **Option A** remediation for the MOSFLM beam center offset misapplication bug (C8 cluster). The implementation will track whether beam center coordinates originate from explicit user input or auto-calculated defaults, applying the MOSFLM +0.5 pixel offset **only** to auto-calculated values per spec-a-core.md §72 and arch.md §ADR-03.

**Key Decision:** Add `beam_center_source` enumeration to `DetectorConfig` with two values: `AUTO` (apply MOSFLM offset) and `EXPLICIT` (preserve user input exactly).

**Estimated Effort:** 3-5 hours (implementation + test expansion + parity validation + documentation sync)

---

## 1. Normative Specification References

### 1.1 spec-a-core.md §72 (MOSFLM Convention)

> "MOSFLM:
>         - Beam b = [1 0 0]; f = [0 0 1]; s = [0 -1 0]; o = [1 0 0]; 2θ-axis = [0 0 -1]; p = [0 0 1];
> u = [0 0 1].
>         - Default Xbeam = (detsize_s + pixel)/2, Ybeam = (detsize_f + pixel)/2.
>         - **Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel.** Pivot = BEAM."

**Key Insight:** The +0.5 pixel offset is specified as a **transformation applied to the default beam center formula**, not a mandatory adjustment to all beam center coordinates. The spec defines "Default Xbeam/Ybeam" followed by the offset mapping, implying the offset is part of the default calculation pipeline.

### 1.2 arch.md §ADR-03 (Beam-center Mapping)

> "ADR-03 Beam-center Mapping (MOSFLM) and +0.5 pixel Offsets
>   - MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). **CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs.**"

**Interpretation:** The parenthetical note about CUSTOM convention clarifies that the +0.5 offset is an **implicit convention-specific behavior**, not a universal transformation. This implies that explicit user inputs (which could come from any convention context) should not receive implicit adjustments.

### 1.3 Current Implementation Bug

**Location:** `src/nanobrag_torch/models/detector.py` (beam center properties, lines ~78-142)

**Current (Incorrect) Behavior:**
```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm
    if self.config.detector_convention == DetectorConvention.MOSFLM:
        return base + 0.5  # ALWAYS applied - INCORRECT
    return base
```

**Problem:** The offset is applied unconditionally to ALL MOSFLM beam centers, including explicit user-provided values like `--beam_center_s 512.5`.

---

## 2. Option A Design: Explicit Source Tracking

### 2.1 Design Rationale

**Why Option A over Option B (heuristic matching)?**

| Criterion | Option A (Explicit Flag) | Option B (Heuristic) |
|-----------|-------------------------|----------------------|
| **Semantic Clarity** | ✅ Clear intent in config | ❌ Implicit inference |
| **Maintainability** | ✅ Easy to audit CLI→config→detector pipeline | ❌ Fragile (what if user coincidentally provides default?) |
| **Testing** | ✅ Simple boolean branch coverage | ❌ Must test edge cases (near-default values) |
| **Future-Proofing** | ✅ Supports header ingestion provenance tracking | ❌ Couples beam center logic to detector size |
| **API Transparency** | ✅ Users can explicitly set source in direct API usage | ❌ No API control; relies on value matching |

**Recommendation:** Option A provides **explicit semantic distinction** that scales to future requirements (e.g., tracking header ingestion source for diagnostics).

### 2.2 Configuration Layer Changes

#### 2.2.1 New Enumeration (config.py)

```python
from enum import Enum

class BeamCenterSource(str, Enum):
    """
    Provenance tracking for beam center coordinates.

    AUTO: Beam center calculated from detector geometry defaults.
          MOSFLM convention applies +0.5 pixel offset.
    EXPLICIT: Beam center explicitly provided by user (CLI flag, API, or header).
              No convention-specific offsets applied.
    """
    AUTO = "auto"
    EXPLICIT = "explicit"
```

**Rationale:** Using `str` base class for Enum ensures JSON serialization compatibility and clear debugging output.

#### 2.2.2 DetectorConfig Extension

```python
@dataclass
class DetectorConfig:
    # ... existing fields ...
    beam_center_s_mm: float
    beam_center_f_mm: float

    # NEW FIELD:
    beam_center_source: BeamCenterSource = BeamCenterSource.AUTO
    """
    Provenance of beam center coordinates.

    AUTO: Derived from detector defaults; MOSFLM applies +0.5 pixel offset.
    EXPLICIT: User-provided; no convention offsets applied.

    When constructing DetectorConfig directly in Python (not via CLI),
    set source=EXPLICIT if providing specific beam centers to avoid
    unintended MOSFLM offset application.
    """
```

**Backward Compatibility:** Default value `AUTO` preserves existing behavior for code that doesn't set the field explicitly.

---

## 3. CLI Detection Logic

### 3.1 Explicit Beam Center Flags

The CLI parser must detect the following **8 explicit beam center indicators**:

| Flag | Description | Convention Context |
|------|-------------|-------------------|
| `--beam_center_s <val>` | Direct API slow-axis beam center | All conventions |
| `--beam_center_f <val>` | Direct API fast-axis beam center | All conventions |
| `-Xbeam <val>` | MOSFLM/DENZO/ADXV X coordinate | BEAM pivot conventions |
| `-Ybeam <val>` | MOSFLM/DENZO/ADXV Y coordinate | BEAM pivot conventions |
| `-Xclose <val>` | Close distance X (SAMPLE pivot) | SAMPLE pivot conventions |
| `-Yclose <val>` | Close distance Y (SAMPLE pivot) | SAMPLE pivot conventions |
| `-ORGX <val>` | XDS origin X in pixels | XDS convention |
| `-ORGY <val>` | XDS origin Y in pixels | XDS convention |

**Header Ingestion:** When `-img <file>` or `-mask <file>` flags are provided:
- If header contains `BEAM_CENTER_X` or `BEAM_CENTER_Y` keys → set `source=EXPLICIT`
- If header contains `ORGX`/`ORGY` → set `source=EXPLICIT`
- If header contains `MOSFLM_CENTER_X/Y` or `DENZO_X_BEAM/Y_BEAM` → set `source=EXPLICIT`

### 3.2 CLI Implementation (__main__.py)

```python
def determine_beam_center_source(args) -> BeamCenterSource:
    """
    Determine if beam center was explicitly provided by user.

    Returns EXPLICIT if any of the following flags are set:
    - Direct beam center coordinates (--beam_center_s/f)
    - Convention-specific beam centers (-Xbeam/-Ybeam)
    - Close distance coordinates (-Xclose/-Yclose)
    - XDS origin (-ORGX/-ORGY)
    - Header ingestion with beam center keys (-img/-mask with headers)

    Otherwise returns AUTO (use convention defaults with offsets).
    """
    # Direct API flags
    if args.beam_center_s is not None or args.beam_center_f is not None:
        return BeamCenterSource.EXPLICIT

    # BEAM pivot convention flags
    if args.Xbeam is not None or args.Ybeam is not None:
        return BeamCenterSource.EXPLICIT

    # SAMPLE pivot convention flags
    if args.Xclose is not None or args.Yclose is not None:
        return BeamCenterSource.EXPLICIT

    # XDS origin flags
    if args.ORGX is not None or args.ORGY is not None:
        return BeamCenterSource.EXPLICIT

    # Header ingestion (check if headers contain beam center keys)
    if args.img or args.mask:
        # Header parsing happens earlier in CLI flow
        # If beam_center_s/f were populated from headers, flag it
        if hasattr(args, '_beam_center_from_header') and args._beam_center_from_header:
            return BeamCenterSource.EXPLICIT

    # Default: auto-calculated from detector geometry
    return BeamCenterSource.AUTO


# In parse_args():
def parse_args():
    # ... existing argparse setup ...

    # After parsing all arguments:
    args.beam_center_source = determine_beam_center_source(args)

    # Construct DetectorConfig:
    detector_config = DetectorConfig(
        beam_center_s_mm=args.beam_center_s,
        beam_center_f_mm=args.beam_center_f,
        beam_center_source=args.beam_center_source,  # NEW
        # ... other fields ...
    )

    return args
```

**Critical Note:** Header ingestion occurs during `parse_smv_header()` before config construction. The parser must set a flag `_beam_center_from_header` when headers populate beam center values.

---

## 4. Detector Layer Implementation

### 4.1 Conditional Offset Application (detector.py)

```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """
    Beam center slow-axis coordinate in pixels.

    For MOSFLM convention with AUTO source, applies +0.5 pixel offset
    per spec-a-core.md §72. Explicit user inputs preserved exactly.
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

    For MOSFLM convention with AUTO source, applies +0.5 pixel offset
    per spec-a-core.md §72. Explicit user inputs preserved exactly.
    """
    base = self.config.beam_center_f_mm / self.config.pixel_size_mm

    # Apply MOSFLM offset ONLY to auto-calculated defaults
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == BeamCenterSource.AUTO):
        return base + 0.5

    return base
```

**Verification:** These properties are used in `pix0_vector` computation (lines ~520), which feeds all downstream geometry calculations. No other code paths require changes.

---

## 5. Test Coverage Impact Matrix

### 5.1 New Tests Required

| Test File | Test Name | Purpose | Expected Behavior |
|-----------|-----------|---------|-------------------|
| `tests/test_beam_center_source.py` | `test_mosflm_auto_applies_offset` | Validate +0.5 offset for AUTO source | `beam_center_s/f_pixels = base + 0.5` |
| `tests/test_beam_center_source.py` | `test_mosflm_explicit_preserves_exact` | Validate no offset for EXPLICIT source | `beam_center_s/f_pixels = base` |
| `tests/test_beam_center_source.py` | `test_xds_ignores_source` | Validate non-MOSFLM conventions unaffected | No offset regardless of source |
| `tests/test_beam_center_source.py` | `test_custom_convention_explicit` | Validate CUSTOM with explicit beam centers | No offset (per ADR-03) |
| `tests/test_beam_center_source.py` | `test_cli_detection_explicit_flags` | Validate all 8 CLI flags trigger EXPLICIT | Each flag sets `source=EXPLICIT` |

### 5.2 Existing Tests Requiring Updates

| Test File | Change Required | Rationale |
|-----------|-----------------|-----------|
| `tests/test_at_parallel_003.py` | Add explicit `beam_center_source=EXPLICIT` to test setup | Currently failing; fix validates the remediation |
| `tests/test_detector_config.py` | Add default value checks for new field | Ensure backward compatibility |
| `tests/test_detector_geometry.py` | Update assertions for MOSFLM AUTO vs EXPLICIT cases | Verify geometry calculations respect source |

### 5.3 Parity Validation Tests

**Purpose:** Ensure C-PyTorch equivalence after fix.

| Case | C Command | PyTorch Config | Expected Correlation |
|------|-----------|----------------|---------------------|
| **MOSFLM AUTO** (defaults) | `-lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 -distance 100 -detpixels 256` | `beam_center_source=AUTO` | ≥0.9999 |
| **MOSFLM EXPLICIT** | `-lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 -distance 100 -detpixels 256 -Xbeam 12.8 -Ybeam 12.8` | `beam_center_source=EXPLICIT` | ≥0.9999 |
| **XDS** (non-MOSFLM) | `-lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 -distance 100 -detpixels 256 -convention XDS` | Any source | ≥0.9999 |

**Commands:**
```bash
# MOSFLM AUTO (should match C - both apply offset)
env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg \
  pytest -v tests/test_parity_matrix.py -k "AT-PARALLEL-002"

# MOSFLM EXPLICIT (currently fails parity; will pass after fix)
env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg \
  pytest -v tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation
```

---

## 6. Documentation Impact

### 6.1 Files Requiring Updates

| File | Section | Change Description |
|------|---------|-------------------|
| `docs/architecture/detector.md` | §8.2 Beam Center Mapping | Add subsection explaining AUTO vs EXPLICIT source distinction |
| `docs/development/c_to_pytorch_config_map.md` | MOSFLM convention row (line 57-58) | Update to note "+0.5 offset applies to AUTO source only" |
| `docs/findings.md` | API-002 entry | Add note: "beam_center_source=EXPLICIT preserves pix0 overrides exactly" |

### 6.2 New Documentation

**Location:** `docs/architecture/detector.md` §8.2.1 (new subsection)

```markdown
#### 8.2.1 Beam Center Source Provenance

The MOSFLM convention applies a +0.5 pixel offset to beam center coordinates
derived from detector geometry defaults. This offset is NOT applied to explicit
user-provided beam centers.

**AUTO Source (default):**
- Beam center calculated from detector size: `(detsize + pixel) / 2`
- MOSFLM applies transformation: `Fbeam = Ybeam + 0.5·pixel`
- Rationale: Convention-specific default mapping per spec-a-core.md §72

**EXPLICIT Source:**
- User provides beam center via CLI flags, API, or header ingestion
- Coordinates preserved exactly (no convention offsets)
- Rationale: Explicit inputs represent user intent; implicit adjustments violate principle of least surprise

**CLI Detection:**
The following flags indicate EXPLICIT source:
- Direct API: `--beam_center_s`, `--beam_center_f`
- Convention-specific: `-Xbeam/-Ybeam`, `-Xclose/-Yclose`, `-ORGX/-ORGY`
- Header ingestion: `-img/-mask` with beam center keys

**Direct API Usage Warning:**
When constructing `DetectorConfig` directly in Python:
```python
# CORRECT: Explicit beam center
config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    beam_center_s_mm=12.8,
    beam_center_f_mm=12.8,
    beam_center_source=BeamCenterSource.EXPLICIT,  # Required!
)

# INCORRECT: Missing source (will apply unwanted +0.5 offset)
config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    beam_center_s_mm=12.8,
    beam_center_f_mm=12.8,
    # beam_center_source defaults to AUTO → applies MOSFLM offset
)
```
```

---

## 7. Risk Assessment & Interactions

### 7.1 Known Interactions

#### 7.1.1 API-002: pix0 Overrides

**Finding:** `DetectorConfig.pix0_override` allows direct specification of detector origin vector, bypassing beam center calculations.

**Interaction:** When `pix0_override` is set, beam center properties are not used. The `beam_center_source` field has no effect.

**Mitigation:** Document in API-002 finding entry that pix0 overrides are independent of beam_center_source. Add validation test confirming pix0 override ignores beam_center_source.

#### 7.1.2 CONVENTION-001: CUSTOM Convention Switching

**Finding:** Providing detector axis vectors (fast/slow/normal) implicitly switches to CUSTOM convention unless `-convention` flag is explicit.

**Interaction:** CUSTOM convention does not apply MOSFLM offset per ADR-03. If user provides both custom axes AND explicit beam centers, source should be EXPLICIT (no offset).

**Mitigation:** CLI detection logic already handles this: explicit beam center flags trigger EXPLICIT source regardless of convention. Document in CONVENTION-001 that CUSTOM + explicit beam centers is safe.

#### 7.1.3 Header Ingestion Precedence

**Finding:** `-img` and `-mask` headers can populate beam center values. Last file read wins for shared keys.

**Interaction:** If header contains beam centers, they should be treated as EXPLICIT (user-curated data file).

**Mitigation:** Header parsing must set `_beam_center_from_header` flag. CLI detection function checks this flag. Document in `docs/architecture/detector.md` §10 (Header Ingestion).

### 7.2 PyTorch-Specific Constraints

#### 7.2.1 Device/Dtype Neutrality

**Constraint:** All tensor operations must work on CPU and CUDA, float32 and float64.

**Impact:** The +0.5 offset is a scalar constant addition. No device/dtype concerns.

**Verification:** Existing device/dtype smoke tests in `tests/test_at_parallel_002.py` cover this path.

#### 7.2.2 Differentiability

**Constraint:** Beam center coordinates must remain differentiable for optimization.

**Impact:** The conditional offset application uses boolean logic (`if` statement) which does not break gradients. The `+0.5` constant addition is differentiable.

**Verification:** Existing gradient tests in `tests/test_gradients.py::test_detector_geometry_gradients` validate beam center differentiability. Rerun after fix to confirm.

#### 7.2.3 torch.compile Compatibility

**Constraint:** Conditional logic must not break torch.compile graph capture.

**Impact:** `if` statements with Enum comparisons compile cleanly. The conditional is resolved at config construction time (not within compiled simulation loop).

**Verification:** Run `env KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py` with torch.compile enabled (default behavior). Should pass.

### 7.3 Backward Compatibility

**API Change:** Adding new field to `DetectorConfig` with default value `AUTO`.

**Impact Analysis:**

| Usage Pattern | Before Fix | After Fix | Compatible? |
|---------------|-----------|-----------|-------------|
| CLI usage (default beam centers) | MOSFLM offset applied | MOSFLM offset applied | ✅ Yes (AUTO default) |
| CLI usage (explicit `-Xbeam/-Ybeam`) | MOSFLM offset applied (WRONG) | No offset (CORRECT) | ⚠️ **Behavior change** (but fixing spec violation) |
| Direct API (no source specified) | MOSFLM offset applied | MOSFLM offset applied | ✅ Yes (AUTO default) |
| Direct API (explicit source=EXPLICIT) | N/A (field doesn't exist) | No offset | ✅ New capability |

**Breaking Change Assessment:** The fix corrects spec-violating behavior. Users who relied on the bug (providing explicit beam centers and expecting additional offset) will see corrected geometry. This is acceptable since the current behavior contradicts the spec.

---

## 8. Implementation Task Breakdown (Phase C)

### C1: Update Configuration Layer [Estimated: 30 min]

**Files:**
- `src/nanobrag_torch/config.py`

**Changes:**
1. Add `BeamCenterSource` enum with AUTO/EXPLICIT values
2. Add `beam_center_source: BeamCenterSource = BeamCenterSource.AUTO` field to `DetectorConfig`
3. Add docstring explaining provenance tracking and direct API usage warning

**Validation:** Run `pytest -v tests/test_detector_config.py` (may need to add placeholder test for new field)

### C2: Adjust CLI Parsing [Estimated: 45 min]

**Files:**
- `src/nanobrag_torch/__main__.py`

**Changes:**
1. Implement `determine_beam_center_source()` function with 8 flag checks
2. Add header ingestion flag `_beam_center_from_header` in `parse_smv_header()`
3. Call `determine_beam_center_source(args)` after argument parsing
4. Pass `beam_center_source` to `DetectorConfig` constructor

**Validation:** Add unit test for `determine_beam_center_source()` covering all 8 explicit flags + AUTO fallback

### C3: Apply Conditional Offset in Detector [Estimated: 20 min]

**Files:**
- `src/nanobrag_torch/models/detector.py`

**Changes:**
1. Update `beam_center_s_pixels` property with conditional logic
2. Update `beam_center_f_pixels` property with conditional logic
3. Update property docstrings to explain AUTO vs EXPLICIT behavior

**Validation:** Run `pytest -v tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation` (should pass after fix)

### C4: Expand Regression Coverage [Estimated: 60 min]

**Files:**
- Create `tests/test_beam_center_source.py`
- Update `tests/test_at_parallel_003.py`

**Changes:**
1. Add 5 new tests per Test Coverage Impact Matrix §5.1
2. Update `test_at_parallel_003.py` to set explicit source
3. Add negative controls for non-MOSFLM conventions

**Validation:** Run `pytest -v tests/test_beam_center_source.py tests/test_at_parallel_003.py` → all pass

### C5: Targeted Validation Bundle [Estimated: 30 min]

**Commands:**
```bash
# Test 1: Detector config with new field
env KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py

# Test 2: MOSFLM offset preservation (was failing; should pass)
env KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation

# Test 3: New beam center source tests
env KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_beam_center_source.py
```

**Artifacts:** Capture logs + summary.md at `reports/2026-01-test-suite-triage/phase_m3/<STAMP>/mosflm_fix/`

### C6: Documentation Sync [Estimated: 45 min]

**Files:**
- `docs/architecture/detector.md`
- `docs/development/c_to_pytorch_config_map.md`
- `docs/findings.md`

**Changes:**
1. Add §8.2.1 "Beam Center Source Provenance" to detector.md
2. Update MOSFLM convention row in c_to_pytorch_config_map.md (line 57-58)
3. Append interaction note to API-002 finding entry

**Validation:** Read updated sections; verify cross-references are correct

### C7: Ledger & Tracker Update [Estimated: 15 min]

**Files:**
- `docs/fix_plan.md`
- `plans/active/test-suite-triage.md` (remediation_tracker.md reference)

**Changes:**
1. Add Attempt #N to `[DETECTOR-CONFIG-001]` entry with task summary
2. Mark C8 cluster as RESOLVED in tracker
3. Cite design artifact path and targeted validation results

**Total Estimated Effort:** 3.75 hours (excluding time for parity validation runs and full suite rerun in Phase D)

---

## 9. Exit Criteria (Phase B Complete)

- [x] **B1: Remediation option ratified** — Option A selected; rationale documented in §2.1
- [x] **B2: Config/CLI propagation defined** — Enum, DetectorConfig field, CLI detection logic specified in §§2-4
- [x] **B3: Test & doc impacts mapped** — Test coverage matrix (§5), doc changes enumerated (§6)
- [x] **B4: Risk assessment complete** — API-002/CONVENTION-001 interactions documented (§7.1), PyTorch constraints validated (§7.2), backward compatibility analyzed (§7.3)

**Design Status:** ✅ **COMPLETE** — Ready for Phase C implementation handoff.

---

## 10. References

### Specification Documents
- `specs/spec-a-core.md` §72 — MOSFLM convention beam center mapping
- `arch.md` §ADR-03 — Beam-center mapping decision
- `arch.md` §7 — Geometry Model & Conventions (MOSFLM row, lines 223-227)

### Failure Analysis
- `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md` — C8 cluster failure analysis recommending Option A

### Implementation Plan
- `plans/active/detector-config.md` — Phase B tasks (B1-B4) completed by this design
- `plans/active/detector-config.md` — Phase C tasks (C1-C7) defined in §8

### Testing & Validation
- `docs/development/testing_strategy.md` — Parity validation workflow (§2.5)
- `docs/development/c_to_pytorch_config_map.md` — CLI↔config mapping authoritative reference

### Cross-Cutting Concerns
- `docs/findings.md` — API-002 (pix0 overrides), CONVENTION-001 (CUSTOM switching)
- `docs/debugging/detector_geometry_checklist.md` — Geometry debugging workflow

---

**Next Steps:** Supervisor approval → Implementation loop (Phase C, tasks C1-C7) → Full suite rerun (Phase D)
