# Option A Design: beam_center_source Tracking for MOSFLM Offset Fix

**STAMP:** 20251011T215645Z
**Phase:** M3 → C (Design complete, ready for implementation)
**Initiative:** DETECTOR-CONFIG-001
**Status:** Design ratified; awaiting Phase C implementation

---

## Executive Summary

This design document specifies the implementation of **Option A** ("Track Beam Center Source") to remediate the MOSFLM beam center offset misapplication bug documented in C8 cluster analysis.

**Core Problem:** The Detector class currently applies the MOSFLM convention +0.5 pixel offset to ALL beam center coordinates, including explicit user-provided values. Per spec-a-core.md §72 and arch.md §ADR-03, the offset should ONLY apply to auto-calculated defaults.

**Solution:** Introduce a `beam_center_source` attribute to `DetectorConfig` that tracks whether beam centers originated from explicit user input (`"explicit"`) or auto-calculated defaults (`"auto"`). The Detector layer conditionally applies the +0.5 pixel offset based on this provenance flag.

**Rationale:** Option A provides explicit semantic tracking, clear auditability across the CLI → config → detector pipeline, and minimal implementation complexity (3 files, ~40 lines of changes).

---

## 1. Normative Spec Requirements

### Spec-a-core.md §72 (MOSFLM Convention)

> **MOSFLM:**
>   - Beam b = [1 0 0]; f = [0 0 1]; s = [0 -1 0]; o = [1 0 0]; 2θ-axis = [0 0 -1]; p = [0 0 1]; u = [0 0 1].
>   - Default Xbeam = (detsize_s + pixel)/2, Ybeam = (detsize_f + pixel)/2.
>   - **Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel.** Pivot = BEAM.

### Spec-a-core.md §86 (Beam center relations)

> Fbeam/Sbeam (fast/slow coordinates in meters) are computed from Xbeam/Ybeam (mm converted to m) per convention (**note MOSFLM and DENZO introduce ±0.5 pixel shifts as shown above**).

### arch.md §ADR-03 (Beam-center Mapping)

> **MOSFLM:** Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). **CUSTOM (when active):** spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs.

### Critical Interpretation

The normative language describes the +0.5 pixel offset as part of the **default** MOSFLM beam center mapping formula. The spec states "Default Xbeam = ..., Ybeam = ..." and then applies the offset to those defaults. When users explicitly provide beam center values (via `-Xbeam`, `-Ybeam`, or header ingestion), those are **not** defaults—they are explicit overrides that must be preserved exactly.

**Key Insight:** The offset is a convention-specific transformation of the **auto-calculated default formula**, not a mandatory adjustment for all user-provided coordinates.

---

## 2. Implementation Design

### 2.1 Configuration Layer Changes

**File:** `src/nanobrag_torch/config.py`

**Changes:**

1. **Add BeamCenterSource enum:**
   ```python
   from enum import Enum

   class BeamCenterSource(str, Enum):
       """Provenance tracking for beam center coordinates."""
       AUTO = "auto"      # Derived from detector geometry defaults
       EXPLICIT = "explicit"  # User-provided via CLI/headers/API
   ```

2. **Extend DetectorConfig dataclass:**
   ```python
   @dataclass
   class DetectorConfig:
       # ... existing fields ...
       beam_center_s_mm: float
       beam_center_f_mm: float
       beam_center_source: BeamCenterSource = BeamCenterSource.AUTO
       # ... other fields ...
   ```

**Rationale:**
- Explicit enum prevents typos and documents valid states
- Default to `AUTO` for backward compatibility (existing code without explicit flag gets auto behavior)
- Follows existing pattern for `DetectorConvention`, `DetectorPivot` enums

### 2.2 CLI Parsing Layer Changes

**File:** `src/nanobrag_torch/__main__.py`

**Changes:**

1. **Add beam center source detection helper:**
   ```python
   def determine_beam_center_source(args: argparse.Namespace,
                                    header_provided_beam_center: bool = False) -> BeamCenterSource:
       """
       Detect whether beam center coordinates originated from explicit user input
       or should use auto-calculated convention defaults.

       Explicit sources (in priority order):
       1. CLI flags: -beam_center_s, -beam_center_f
       2. CLI flags: -Xbeam, -Ybeam (BEAM pivot style)
       3. CLI flags: -Xclose, -Yclose (SAMPLE pivot style)
       4. CLI flags: -ORGX, -ORGY (XDS style)
       5. Header ingestion: -img or -mask with beam center keys

       Returns:
           BeamCenterSource.EXPLICIT if any explicit source detected
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
           header_provided_beam_center,
       ]

       return BeamCenterSource.EXPLICIT if any(explicit_flags) else BeamCenterSource.AUTO
   ```

2. **Update config construction:**
   ```python
   # After parsing args and ingesting headers
   beam_center_source = determine_beam_center_source(args, header_provided_beam_center)

   detector_config = DetectorConfig(
       # ... existing fields ...
       beam_center_s_mm=computed_beam_center_s,
       beam_center_f_mm=computed_beam_center_f,
       beam_center_source=beam_center_source,
       # ... other fields ...
   )
   ```

**Rationale:**
- Centralized detection logic prevents inconsistencies
- 8 explicit flags cover all CLI beam center input methods
- Header ingestion flag handled via tracking during SMV/mask parsing
- Clear documentation of precedence order

### 2.3 Detector Layer Changes

**File:** `src/nanobrag_torch/models/detector.py`

**Changes:**

**Update beam center pixel properties** (lines ~78-142):

```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """
    Beam center slow-axis coordinate in pixels.

    For MOSFLM convention with auto-calculated beam centers, applies
    the normative +0.5 pixel offset per spec-a-core.md §72.

    Explicit user-provided beam centers are preserved exactly.
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

    For MOSFLM convention with auto-calculated beam centers, applies
    the normative +0.5 pixel offset per spec-a-core.md §72.

    Explicit user-provided beam centers are preserved exactly.
    """
    base = self.config.beam_center_f_mm / self.config.pixel_size_mm

    # Apply MOSFLM offset ONLY to auto-calculated defaults
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == BeamCenterSource.AUTO):
        return base + 0.5

    return base
```

**Rationale:**
- Single conditional in each property method (clear logic)
- No changes to `pix0_vector` calculation (uses these properties)
- Preserves existing device/dtype neutrality (uses tensors throughout)
- Clear inline documentation of spec reference

---

## 3. CLI Propagation Specification

### 3.1 Explicit Beam Center Flags

The following CLI flags indicate **explicit** beam center input and SHALL set `beam_center_source=EXPLICIT`:

| Flag Category | Flags | Description |
|---------------|-------|-------------|
| Direct API | `-beam_center_s <val>` | Explicit slow-axis center (mm) |
| Direct API | `-beam_center_f <val>` | Explicit fast-axis center (mm) |
| BEAM pivot style | `-Xbeam <val>` | MOSFLM/DENZO slow-axis beam (mm) |
| BEAM pivot style | `-Ybeam <val>` | MOSFLM/DENZO fast-axis beam (mm) |
| SAMPLE pivot style | `-Xclose <val>` | XDS/DIALS near-point X (mm) |
| SAMPLE pivot style | `-Yclose <val>` | XDS/DIALS near-point Y (mm) |
| XDS pixel style | `-ORGX <val>` | XDS origin X (pixels) |
| XDS pixel style | `-ORGY <val>` | XDS origin Y (pixels) |

### 3.2 Header Ingestion

**Files:** `-img <file>` and `-mask <file>`

**Detection Logic:**

When parsing SMV/mask headers in `io/smv.py` and `io/mask.py`:

```python
def parse_smv_header(file_path: str) -> Tuple[Dict, bool]:
    """
    Parse SMV header and detect beam center presence.

    Returns:
        (header_dict, has_beam_center)
    """
    header = {}
    has_beam_center = False

    # ... existing parsing logic ...

    beam_center_keys = [
        'BEAM_CENTER_X', 'BEAM_CENTER_Y',
        'ADXV_CENTER_X', 'ADXV_CENTER_Y',
        'MOSFLM_CENTER_X', 'MOSFLM_CENTER_Y',
        'DENZO_X_BEAM', 'DENZO_Y_BEAM',
    ]

    if any(key in header for key in beam_center_keys):
        has_beam_center = True

    return header, has_beam_center
```

**Propagation:** The `has_beam_center` flag is OR'd across all `-img`/`-mask` files and passed to `determine_beam_center_source()`.

### 3.3 Default Behavior

**When NO explicit flags or headers provide beam centers:**

- `beam_center_source = BeamCenterSource.AUTO`
- Detector calculates convention-specific defaults:
  - MOSFLM: `Xbeam = (detsize_s + pixel)/2`, `Ybeam = (detsize_f + pixel)/2`
  - Then applies +0.5 pixel offset: `Sbeam = Xbeam + 0.5·pixel`, `Fbeam = Ybeam + 0.5·pixel`

**Example CLI Commands:**

```bash
# AUTO behavior (no explicit flags)
nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 256
# Result: beam_center_source=AUTO, beam_center in pixels = 128.5 (MOSFLM default + offset)

# EXPLICIT behavior (user provides beam center)
nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 256 -Xbeam 12.8 -Ybeam 12.8
# Result: beam_center_source=EXPLICIT, beam_center in pixels = 128.0 (no offset)
```

---

## 4. Test Impact Matrix

### 4.1 New Test Cases Required

**File:** `tests/test_beam_center_source.py` (new file)

| Test ID | Purpose | Setup | Assertion |
|---------|---------|-------|-----------|
| `test_mosflm_auto_applies_offset` | Verify +0.5 offset for MOSFLM defaults | DetectorConfig with `convention=MOSFLM`, `source=AUTO`, `detpixels=256` | `beam_center_s_pixels == 128.5` |
| `test_mosflm_explicit_no_offset` | Verify no offset for explicit input | DetectorConfig with `convention=MOSFLM`, `source=EXPLICIT`, `beam_center_s_mm=12.8` | `beam_center_s_pixels == 128.0` |
| `test_xds_no_offset_regardless` | Verify XDS never applies offset | DetectorConfig with `convention=XDS`, both `AUTO` and `EXPLICIT` | `beam_center_s_pixels == beam_center_s_mm / pixel_size_mm` (no +0.5) |
| `test_cli_detection_explicit` | Verify CLI flag detection | Call `determine_beam_center_source()` with `args.Xbeam=12.8` | Returns `EXPLICIT` |
| `test_cli_detection_auto` | Verify CLI default detection | Call `determine_beam_center_source()` with no beam flags | Returns `AUTO` |

### 4.2 Existing Test Updates

**File:** `tests/test_at_parallel_003.py`

**Test:** `test_detector_offset_preservation`

**Current Status:** FAILING (expects 512.5, gets 513.0)

**Post-Fix Expected:** PASSING

**Change Required:** Update test setup to use `beam_center_source=EXPLICIT`:

```python
detector_config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    beam_center_s_mm=51.25,  # 512.5 pixels
    beam_center_f_mm=51.25,
    beam_center_source=BeamCenterSource.EXPLICIT,  # Add this line
    # ... other config ...
)
```

**File:** `tests/test_detector_config.py`

**Updates Required:**
- Add `beam_center_source` field to all `DetectorConfig` instantiations (default=AUTO)
- Add dedicated test for source propagation

### 4.3 Negative Control Tests

**Purpose:** Verify non-MOSFLM conventions never apply offset

**Conventions to test:** XDS, DIALS, DENZO, ADXV, CUSTOM

**Assertion:** For ALL conventions except MOSFLM, `beam_center_pixels == beam_center_mm / pixel_size_mm` (exact equality, no +0.5)

---

## 5. Documentation Impact

### 5.1 Architecture Documentation

**File:** `docs/architecture/detector.md`

**Section:** §8.2 Beam Center Mapping (lines ~230-245)

**Update Required:** Add subsection explaining source tracking:

```markdown
#### Beam Center Source Tracking (DETECTOR-CONFIG-001)

The detector tracks the **provenance** of beam center coordinates via `DetectorConfig.beam_center_source`:

- **AUTO:** Beam centers derived from convention-specific defaults (e.g., MOSFLM uses `(detsize + pixel)/2`)
  - For MOSFLM convention ONLY, the +0.5 pixel offset is applied: `Fbeam = Ybeam + 0.5·pixel`
- **EXPLICIT:** Beam centers provided by user via CLI flags or header ingestion
  - NO offset applied; coordinates preserved exactly as provided

**Rationale:** Per spec-a-core.md §72, the +0.5 pixel offset is part of the MOSFLM default formula,
not a universal transformation. Explicit user inputs must be honored without adjustment.

**CLI Detection:** The following flags indicate explicit input:
- `-beam_center_s`, `-beam_center_f` (direct API)
- `-Xbeam`, `-Ybeam` (BEAM pivot style)
- `-Xclose`, `-Yclose` (SAMPLE pivot style)
- `-ORGX`, `-ORGY` (XDS pixel style)
- Header keys: `BEAM_CENTER_X/Y`, `ADXV_CENTER_X/Y`, `MOSFLM_CENTER_X/Y`, `DENZO_X/Y_BEAM`
```

### 5.2 Configuration Mapping Documentation

**File:** `docs/development/c_to_pytorch_config_map.md`

**Section:** §Detector Parameters, MOSFLM convention row (line ~57)

**Update Required:** Clarify source-dependent offset:

```markdown
| `-Xbeam <val>` | `DetectorConfig.beam_center_s` | `Xbeam` | mm → meters | **MOSFLM default: (detsize_s+pixel)/2; maps to Sbeam = Xbeam + 0.5·pixel ONLY for auto-calculated defaults; explicit values preserved exactly** |
| `-Ybeam <val>` | `DetectorConfig.beam_center_f` | `Ybeam` | mm → meters | **MOSFLM default: (detsize_f+pixel)/2; maps to Fbeam = Ybeam + 0.5·pixel ONLY for auto-calculated defaults; explicit values preserved exactly** |
```

**Add New Section:** §Beam Center Source Detection (after existing table)

(Copy content from §3.1 and §3.2 of this design doc)

### 5.3 Findings Documentation

**File:** `docs/findings.md`

**Update Required:** Cross-reference API-002 and CONVENTION-001 interactions

**Entry to Add:**

```markdown
### DETECTOR-CONFIG-001: MOSFLM Beam Center Source Tracking

**Status:** Resolved (2025-10-11)
**Category:** Implementation Bug
**Severity:** P2.1 (High — spec violation)

**Problem:** Detector incorrectly applied MOSFLM +0.5 pixel offset to ALL beam centers, including explicit user inputs.

**Solution:** Introduced `BeamCenterSource` enum to track coordinate provenance. Offset now applies ONLY to auto-calculated defaults per spec-a-core.md §72.

**Interactions:**
- **API-002 (pix0 override):** Users can still override `pix0_vector` directly; when doing so, they bypass beam center logic entirely (explicit source has no effect on custom pix0)
- **CONVENTION-001 (CUSTOM convention):** CUSTOM convention never applies MOSFLM offset regardless of source (no default offset formula defined for CUSTOM per ADR-03)

**Verification:** AT-PARALLEL-003 now passes; C-PyTorch parity validated for explicit MOSFLM beam centers (correlation ≥0.999)

**References:**
- Plan: `plans/active/detector-config.md`
- Design: `reports/2026-01-test-suite-triage/phase_m3/20251011T215645Z/mosflm_offset/design.md`
- Summary: `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md`
```

---

## 6. Risk Assessment

### 6.1 API Compatibility

**Risk:** Existing code that constructs `DetectorConfig` directly (not via CLI) may not set `beam_center_source`

**Mitigation:**
- Default value `source=AUTO` preserves backward compatibility
- Direct API users who want explicit behavior MUST explicitly set `source=EXPLICIT` (documented in detector.md)

**Example Migration:**

```python
# OLD CODE (implicit AUTO behavior)
config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    beam_center_s_mm=12.8,
    beam_center_f_mm=12.8,
)

# NEW CODE (explicit source required)
config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    beam_center_s_mm=12.8,
    beam_center_f_mm=12.8,
    beam_center_source=BeamCenterSource.EXPLICIT,  # Required for correct behavior
)
```

**Impact:** Medium (requires user action for direct API usage)

### 6.2 Finding Interactions

#### API-002: pix0_vector Override

**Finding:** Users can directly set `DetectorConfig.pix0_vector` to bypass all beam center calculations

**Interaction:** When `pix0_vector` is explicitly provided, the Detector skips beam center → pix0 conversion entirely. The `beam_center_source` flag has no effect in this case.

**Risk:** None (orthogonal code paths)

**Verification:** Existing `test_detector_pix0_override.py` ensures pix0 override still works post-fix

#### CONVENTION-001: CUSTOM Convention Offset Behavior

**Finding:** CUSTOM convention has no defined offset formula per spec (ADR-03 states "no implicit offsets unless provided by user inputs")

**Interaction:** CUSTOM convention never applies +0.5 offset regardless of `beam_center_source` value

**Risk:** None (CUSTOM path already excludes offset logic)

**Verification:** Add negative control test: `test_custom_convention_no_offset_ever()`

### 6.3 Header Ingestion Edge Cases

**Scenario:** User provides `-img` with `BEAM_CENTER_X/Y` keys, then also provides `-Xbeam` CLI flag

**Expected Behavior:** CLI flag wins (last-write-wins per spec AT-PRE-001), and `source=EXPLICIT` because CLI flag detection occurs after header ingestion

**Risk:** Low (CLI precedence already documented)

**Verification:** Add test case to `test_beam_center_source.py`

### 6.4 PyTorch Device/Dtype Neutrality

**Requirement:** Implementation must work for CPU/GPU tensors and all dtypes without silent device transfers

**Analysis:**
- Beam center properties use tensor division (`beam_center_mm / pixel_size_mm`)
- `+0.5` offset uses scalar addition (automatically promotes to tensor device/dtype)
- No explicit `.cpu()` or `.cuda()` calls in modified code paths

**Risk:** None (change preserves existing tensor neutrality)

**Verification:** Existing `test_detector_device_neutrality.py` covers CPU/CUDA smoke tests

### 6.5 Differentiability Preservation

**Requirement:** All detector properties must maintain gradient flow for optimization

**Analysis:**
- Beam center properties use `@property` pattern (recalculated from base tensors)
- Conditional `+0.5` offset uses boolean selection (differentiable)
- No `.item()` calls or detached tensors introduced

**Risk:** None (change preserves existing gradient flow)

**Verification:** Existing `test_detector_gradients.py` covers gradcheck on beam center parameters

---

## 7. Implementation Steps (Phase C Tasks C1-C7)

### C1: Configuration Layer

**File:** `src/nanobrag_torch/config.py`

**Estimated Time:** 15 minutes

**Steps:**
1. Add `BeamCenterSource` enum after existing enums
2. Add `beam_center_source: BeamCenterSource = BeamCenterSource.AUTO` field to `DetectorConfig`
3. Update `DetectorConfig.__post_init__()` if validation needed

**Verification:** `python -c "from nanobrag_torch.config import BeamCenterSource, DetectorConfig; print(BeamCenterSource.AUTO)"`

### C2: CLI Parsing Layer

**File:** `src/nanobrag_torch/__main__.py`

**Estimated Time:** 30 minutes

**Steps:**
1. Implement `determine_beam_center_source()` helper function
2. Update header parsing in `io/smv.py` to return `has_beam_center` flag
3. Update `main()` to call helper and set `beam_center_source` in config construction

**Verification:** `nanoBragg -Xbeam 12.8 -Ybeam 12.8 ... --debug-config` (add temp debug flag to print source)

### C3: Detector Layer

**File:** `src/nanobrag_torch/models/detector.py`

**Estimated Time:** 20 minutes

**Steps:**
1. Update `beam_center_s_pixels` property with conditional offset logic
2. Update `beam_center_f_pixels` property with conditional offset logic
3. Update docstrings with spec references

**Verification:** Unit test both properties with AUTO vs EXPLICIT configs

### C4: Test Expansion

**Files:** `tests/test_beam_center_source.py` (new), `tests/test_at_parallel_003.py`

**Estimated Time:** 45 minutes

**Steps:**
1. Create `test_beam_center_source.py` with 5 test cases from §4.1
2. Update `test_at_parallel_003.py` with explicit source
3. Update `test_detector_config.py` with source field
4. Add negative control tests for non-MOSFLM conventions

**Verification:** `pytest -v tests/test_beam_center_source.py tests/test_at_parallel_003.py`

### C5: Targeted Validation Bundle

**Commands:**
```bash
# Test 1: Explicit beam center preservation (AT-PARALLEL-003)
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation

# Test 2: Source-specific behavior (new comprehensive suite)
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_beam_center_source.py
```

**Expected:** 16 tests pass (1 from AT-003, 15 from new suite)

**Artifact Location:** `reports/2026-01-test-suite-triage/phase_m3/20251011T215645Z/mosflm_fix/`

**Estimated Time:** 10 minutes (execution + artifact capture)

### C6: Documentation Sync

**Files:** `docs/architecture/detector.md`, `docs/development/c_to_pytorch_config_map.md`, `docs/findings.md`

**Estimated Time:** 30 minutes

**Steps:**
1. Add §Beam Center Source Tracking to detector.md (§5.1)
2. Update MOSFLM rows in c_to_pytorch_config_map.md (§5.2)
3. Add DETECTOR-CONFIG-001 entry to findings.md (§5.3)

**Verification:** `rg "beam_center_source" docs/` returns 3+ matches

### C7: Ledger & Tracker Update

**Files:** `docs/fix_plan.md`, (create if missing: `remediation_tracker.md`)

**Estimated Time:** 15 minutes

**Steps:**
1. Append Attempt #42 entry to fix_plan.md under [DETECTOR-CONFIG-001]
2. Mark C8 cluster as RESOLVED in remediation_tracker.md
3. Record targeted validation results and next action (Phase D)

**Verification:** Commit message includes Phase C completion summary

---

## 8. Phase D: Full-Suite Regression Plan

### D1: Chunked Rerun

**Command Ladder:** (from `plans/active/test-suite-triage.md` Phase M)

```bash
export STAMP=20251011T215645Z  # Use this design's STAMP
mkdir -p reports/2026-01-test-suite-triage/phase_m/$STAMP/chunks

# Execute 10-command ladder (see test-suite-triage.md for exact commands)
# Capture each chunk log separately
```

**Expected:** ≤13 failures (baseline), ideally 12 once C8 resolved

**Artifact:** `reports/.../phase_m/$STAMP/chunks/{01..10}.log` + summary.md

### D2: Synthesis & Publication

**Files to Update:**
- `reports/2026-01-test-suite-triage/phase_k/.../analysis/summary.md`
- `reports/2026-01-test-suite-triage/phase_m3/.../mosflm_offset/summary.md`

**Content:** Post-fix failure delta analysis, residual anomalies (if any)

### D3: Plan Archival

**Action:** Move `plans/active/detector-config.md` → `plans/archive/detector-config-complete-$(date -I).md`

**Update:** Mark [DETECTOR-CONFIG-001] as "done" in `docs/fix_plan.md`

---

## 9. Acceptance Criteria

- [ ] `BeamCenterSource` enum added to config.py with AUTO/EXPLICIT values
- [ ] `DetectorConfig.beam_center_source` field added with default=AUTO
- [ ] CLI detection helper `determine_beam_center_source()` implemented with 8 flag checks
- [ ] Detector beam center properties conditionally apply +0.5 offset (MOSFLM + AUTO only)
- [ ] `test_at_parallel_003.py::test_detector_offset_preservation` PASSES
- [ ] 5 new test cases in `test_beam_center_source.py` all PASS
- [ ] Negative control tests for XDS/DIALS/DENZO/ADXV/CUSTOM all PASS
- [ ] C-PyTorch parity validated for MOSFLM explicit beam center (correlation ≥0.999)
- [ ] `docs/architecture/detector.md` updated with source tracking explanation
- [ ] `docs/development/c_to_pytorch_config_map.md` clarified with source distinction
- [ ] `docs/findings.md` entry DETECTOR-CONFIG-001 added with interactions documented
- [ ] Phase M chunked rerun shows ≤13 failures (C8 resolved)
- [ ] `docs/fix_plan.md` updated with Phase C completion and artifacts

---

## 10. Code Examples

### Example 1: CLI Usage (AUTO behavior)

```bash
# MOSFLM convention with default beam center → AUTO source → +0.5 offset applied
nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 256 -convention MOSFLM

# Result: beam_center = 128.5 pixels (default 128.0 + 0.5 offset)
```

### Example 2: CLI Usage (EXPLICIT behavior)

```bash
# MOSFLM convention with explicit beam center → EXPLICIT source → NO offset
nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 256 -convention MOSFLM \
  -Xbeam 12.8 -Ybeam 12.8

# Result: beam_center = 128.0 pixels (explicit value preserved)
```

### Example 3: Python API (AUTO behavior)

```python
from nanobrag_torch.config import DetectorConfig, DetectorConvention, BeamCenterSource

config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    pixel_size_mm=0.1,
    detsize_s_mm=25.6,
    detsize_f_mm=25.6,
    distance_mm=100.0,
    # beam_center_source defaults to AUTO
)

detector = Detector(config)
print(detector.beam_center_s_pixels)  # 128.5 (default 128.0 + 0.5)
```

### Example 4: Python API (EXPLICIT behavior)

```python
from nanobrag_torch.config import DetectorConfig, DetectorConvention, BeamCenterSource

config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    pixel_size_mm=0.1,
    beam_center_s_mm=12.8,
    beam_center_f_mm=12.8,
    beam_center_source=BeamCenterSource.EXPLICIT,  # Required!
    distance_mm=100.0,
)

detector = Detector(config)
print(detector.beam_center_s_pixels)  # 128.0 (explicit value preserved)
```

### Example 5: XDS Convention (Never Applies Offset)

```python
from nanobrag_torch.config import DetectorConfig, DetectorConvention, BeamCenterSource

# XDS convention with AUTO source → NO offset (XDS has no offset formula)
config_auto = DetectorConfig(
    detector_convention=DetectorConvention.XDS,
    beam_center_s_mm=12.8,
    beam_center_source=BeamCenterSource.AUTO,
)

# XDS convention with EXPLICIT source → NO offset
config_explicit = DetectorConfig(
    detector_convention=DetectorConvention.XDS,
    beam_center_s_mm=12.8,
    beam_center_source=BeamCenterSource.EXPLICIT,
)

# Both produce identical results: beam_center = 128.0 pixels
```

---

## 11. References

- **Spec:** `specs/spec-a-core.md` §§68-73, §86
- **Architecture:** `arch.md` §ADR-03 (lines 79-80)
- **C8 Analysis:** `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md`
- **Plan:** `plans/active/detector-config.md` (this initiative)
- **Config Map:** `docs/development/c_to_pytorch_config_map.md` (§Detector Parameters)
- **Detector Spec:** `docs/architecture/detector.md` (§Beam Center Mapping)
- **Findings:** `docs/findings.md` (API-002, CONVENTION-001 interactions)

---

**Status:** Design ratified; ready for Phase C implementation handoff (estimated 3-5 hours total). No code changes required in this design loop—documentation artifact only.
