# MOSFLM Beam Center Offset Remediation Design — Option A

**STAMP:** 20251012T010911Z
**Phase:** M3
**Plan Reference:** `plans/active/detector-config.md` (Phases B1–B4)
**Status:** Design Complete — Ready for Implementation
**Document Type:** Normative Design Specification

---

## Executive Summary

### Problem Statement

The PyTorch Detector class incorrectly applies the MOSFLM convention +0.5 pixel offset to **all** beam center coordinates, including explicit user-provided values. Per `specs/spec-a-core.md` §72 and `arch.md` §ADR-03, the +0.5 pixel offset **MUST** only be applied to auto-calculated beam centers when using MOSFLM convention, **NOT** to explicit user inputs.

**Normative Spec Language (spec-a-core.md §72):**
> "Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel. Pivot = BEAM."

**Architectural Interpretation (arch.md §ADR-03):**
> "MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs."

**Key Insight:** The spec describes the MOSFLM _default calculation formula_ but is silent on whether this offset applies to _explicit user-provided coordinates_. C-code behavior (verified in Phase L analysis) shows the offset is **only** applied when the beam center is derived from detector geometry defaults, **not** when explicitly set by the user via CLI flags.

### Impact

- **Test Failure:** `test_at_parallel_003.py::test_detector_offset_preservation` expects explicit `beam_center_s=512.5` to be preserved exactly, but receives `513.0` (512.5 + 0.5)
- **User Experience:** Users providing explicit beam center coordinates experience unintended +0.5 pixel geometry shifts
- **C-PyTorch Parity:** PyTorch diverges from C reference implementation for explicit beam center cases

### Proposed Solution: Option A (Beam Center Source Tracking)

Add a `beam_center_source` attribute to `DetectorConfig` to explicitly distinguish between:
- **AUTO**: Beam center derived from convention defaults → apply MOSFLM +0.5 offset
- **EXPLICIT**: Beam center provided by user CLI flags → do **not** apply offset

This design provides semantic clarity, maintains auditability, and requires minimal code changes (3 files).

---

## Design Rationale

### Why Option A (Explicit Source Tracking)?

| Criterion | Option A (Source Tracking) | Option B (Value Heuristic) |
|-----------|---------------------------|----------------------------|
| **Semantic Clarity** | ✅ Explicit config attribute | ❌ Implicit heuristic |
| **Auditability** | ✅ Easy to trace AUTO vs EXPLICIT | ❌ Must reverse-engineer from values |
| **Edge Case Safety** | ✅ User providing default-matching value handled correctly | ❌ Fragile: user coincidentally providing default triggers wrong path |
| **Maintainability** | ✅ Single source of truth in config | ❌ Coupled logic across config/detector |
| **Test Coverage** | ✅ Direct tests of source assignment | ❌ Indirect tests of value matching |
| **API Changes** | ⚠️ Requires config field addition | ✅ No config changes |

**Decision:** Option A provides superior semantic clarity and robustness. The config change is localized and backward-compatible (AUTO default preserves existing behavior).

### Rejected Alternatives

**Option B: Default Value Heuristic**
- **Approach:** Compare beam center values against computed defaults; if they match, apply offset
- **Rejection Reason:** Fragile heuristic that fails when user intentionally provides coordinates matching defaults; couples beam center logic to detector size logic; harder to reason about behavior

**Option C: CLI Flag Override (-explicit_beam_center)**
- **Approach:** Add new CLI flag to signal explicit coordinates
- **Rejection Reason:** Redundant with existing flags; increases CLI surface area unnecessarily; source can be inferred from presence of explicit beam center flags

---

## Normative Specification References

### spec-a-core.md §72 (MOSFLM Convention)

```
- MOSFLM:
    - Beam b = [1 0 0]; f = [0 0 1]; s = [0 -1 0]; o = [1 0 0]; 2θ-axis = [0 0 -1]; p = [0 0 1];
u = [0 0 1].
    - Default Xbeam = (detsize_s + pixel)/2, Ybeam = (detsize_f + pixel)/2.
    - Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel. Pivot = BEAM.
```

**Interpretation:**
The formula `Fbeam = Ybeam + 0.5·pixel` describes how to compute `Fbeam` from `Ybeam` when `Ybeam` is derived from the default formula `(detsize_f + pixel)/2`. The spec does **not** explicitly state whether this offset applies when `Ybeam` is user-provided via `-Ybeam` CLI flag.

### arch.md §ADR-03 (Beam-center Mapping)

```
- ADR-03 Beam-center Mapping (MOSFLM) and +0.5 pixel Offsets
  - MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs.
```

**Interpretation:**
The ADR clarifies that for CUSTOM convention, implicit offsets are **not** applied. This establishes a precedent that offset application is **conditional**, not universal. For MOSFLM, the offset is part of the **default calculation**, but the ADR does not specify behavior for explicit user inputs under MOSFLM.

### C-Code Behavior (Verified Phase L)

**Reference:** `reports/2026-01-test-suite-triage/phase_l/20251011T104618Z/detector_config/analysis.md`

The C code applies the +0.5 offset **only** when beam center is computed from detector geometry defaults. When explicit `-Xbeam` or `-Ybeam` flags are provided, the C code uses those values **directly** without applying the offset.

**Parity Requirement:**
PyTorch implementation **MUST** match C behavior to maintain cross-implementation equivalence.

---

## Implementation Design

### Phase B: Design (This Document)

#### Task B1: Capture Normative Language

**Spec References (Verbatim):**

1. **spec-a-core.md §72:**
   > "Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel. Pivot = BEAM."

2. **arch.md §ADR-03:**
   > "MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs."

3. **spec-a-core.md §85-86 (Beam center relations):**
   > "Fbeam/Sbeam (fast/slow coordinates in meters) are computed from Xbeam/Ybeam (mm converted to m) per convention (note MOSFLM and DENZO introduce ±0.5 pixel shifts as shown above)."

**Interpretation:** The +0.5 offset is a **convention-specific default behavior**, not a mandatory transformation for all coordinates.

#### Task B2: Option A Technical Design

**1. Configuration Layer (`src/nanobrag_torch/config.py`)**

Add an enum to represent beam center source:

```python
from enum import Enum

class BeamCenterSource(Enum):
    """Source of beam center coordinates."""
    AUTO = "auto"        # Derived from convention defaults → apply MOSFLM offset
    EXPLICIT = "explicit"  # User-provided via CLI → no offset
```

Update `DetectorConfig` dataclass:

```python
@dataclass
class DetectorConfig:
    # ... existing fields ...
    beam_center_s_mm: float
    beam_center_f_mm: float

    # New field (backward compatible via default)
    beam_center_source: BeamCenterSource = BeamCenterSource.AUTO

    # ... remaining fields ...
```

**Backward Compatibility:**
Default value `BeamCenterSource.AUTO` ensures existing code that doesn't set this field will continue to apply MOSFLM offsets as before.

**2. CLI Detection Logic (`src/nanobrag_torch/__main__.py`)**

Detect explicit beam center CLI flags and set `beam_center_source` accordingly:

```python
# List of CLI flags that signal explicit beam center
EXPLICIT_BEAM_CENTER_FLAGS = [
    'beam_center_s', 'beam_center_f',  # Direct beam center flags
    'Xbeam', 'Ybeam',                   # MOSFLM/DENZO style
    'Xclose', 'Yclose',                 # SAMPLE pivot style
    'ORGX', 'ORGY'                      # XDS style (pixels)
]

# After parsing beam center arguments
if any(getattr(args, flag, None) is not None for flag in EXPLICIT_BEAM_CENTER_FLAGS):
    detector_config.beam_center_source = BeamCenterSource.EXPLICIT
else:
    detector_config.beam_center_source = BeamCenterSource.AUTO
```

**Rationale:**
Any of the 8 explicit beam center flags indicate user intent to provide coordinates. This covers all CLI input pathways:
- `--beam_center_s` / `--beam_center_f` (direct Cartesian)
- `-Xbeam` / `-Ybeam` (MOSFLM/DENZO convention)
- `-Xclose` / `-Yclose` (SAMPLE pivot near-point)
- `-ORGX` / `-ORGY` (XDS pixel coordinates)

**3. Detector Properties (`src/nanobrag_torch/models/detector.py`)**

Update beam center pixel conversion properties to conditionally apply offset:

```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """
    Convert beam center slow coordinate from mm to pixels.

    MOSFLM convention applies +0.5 pixel offset ONLY to auto-calculated defaults,
    NOT to explicit user-provided coordinates.

    Per spec-a-core.md §72 and arch.md §ADR-03.
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
    Convert beam center fast coordinate from mm to pixels.

    MOSFLM convention applies +0.5 pixel offset ONLY to auto-calculated defaults,
    NOT to explicit user-provided coordinates.

    Per spec-a-core.md §72 and arch.md §ADR-03.
    """
    base = self.config.beam_center_f_mm / self.config.pixel_size_mm

    # Apply MOSFLM offset ONLY to auto-calculated defaults
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == BeamCenterSource.AUTO):
        return base + 0.5

    return base
```

**Two-Condition Guard:**
Both conditions must be true for offset application:
1. `detector_convention == MOSFLM` (convention-specific behavior)
2. `beam_center_source == AUTO` (applies only to defaults, not explicit inputs)

#### Task B3: CLI Propagation & Test Matrix

**CLI Input Pathways:**

| CLI Flags | Source Assignment | MOSFLM Offset Applied? |
|-----------|-------------------|------------------------|
| `--beam_center_s 512.5 --beam_center_f 512.5` | EXPLICIT | ❌ No |
| `-Xbeam 51.2 -Ybeam 51.2` | EXPLICIT | ❌ No |
| `-Xclose 0 -Yclose 0` | EXPLICIT | ❌ No |
| `-ORGX 512.5 -ORGY 512.5` | EXPLICIT | ❌ No |
| _(no beam center flags)_ | AUTO | ✅ Yes (MOSFLM only) |
| _(defaults from detector size)_ | AUTO | ✅ Yes (MOSFLM only) |

**pix0 Override Interaction (API-002 Risk):**

When `--pix0_vector` is provided:
- `beam_center_source` remains AUTO (pix0 is separate from beam center)
- MOSFLM offset is **still applied** to auto-calculated beam center
- `pix0_vector` overrides the final detector origin after beam center calculation

**Rationale:**
`pix0_vector` is a low-level geometry override, not a beam center specification. Users providing `pix0_vector` are bypassing normal beam center → origin calculation, so the source assignment remains AUTO unless explicit beam center flags are also present.

**CUSTOM Convention Interaction (CONVENTION-001 Risk):**

When `detector_convention == CUSTOM`:
- No offset is **ever** applied (per arch.md §ADR-03 and spec silence)
- `beam_center_source` is set but ignored in offset logic
- CUSTOM convention check short-circuits before source check

**Rationale:**
CUSTOM convention has no normative offset behavior. The two-condition guard ensures CUSTOM is excluded from offset application regardless of source.

#### Task B4: Risk Assessment

**High-Risk Areas:**

1. **API-002: pix0_vector Override Interaction**
   - **Risk:** Users providing both `--pix0_vector` and explicit beam center may expect no offset
   - **Mitigation:** `pix0_vector` presence does **not** set source=EXPLICIT; explicit beam center flags must be present
   - **Test:** Verify `pix0_vector + AUTO` applies offset; `pix0_vector + EXPLICIT` does not

2. **CONVENTION-001: CUSTOM Convention Behavior**
   - **Risk:** CUSTOM convention may apply offset if source=AUTO
   - **Mitigation:** Convention check is **first condition** in guard; CUSTOM short-circuits before source check
   - **Test:** Verify CUSTOM + AUTO and CUSTOM + EXPLICIT both produce no offset

3. **Header Ingestion Precedence**
   - **Risk:** `-img` / `-mask` headers may contain beam center; source assignment may be ambiguous
   - **Mitigation:** Header-derived beam centers are **not** CLI-provided; remain AUTO
   - **Test:** Verify header beam center with MOSFLM applies offset (AUTO behavior)

**Medium-Risk Areas:**

4. **Test Fixture Updates**
   - **Risk:** All tests instantiating `DetectorConfig` must handle new field
   - **Mitigation:** Default `AUTO` preserves existing behavior; only tests explicitly checking EXPLICIT need updates
   - **Test:** Run full test suite after config change; expect no new failures

5. **Device/Dtype Neutrality**
   - **Risk:** New code paths may introduce device-specific logic
   - **Mitigation:** All changes are CPU-side config/logic; no tensor operations modified
   - **Test:** Run targeted tests with `CUDA_VISIBLE_DEVICES=-1` and `device=cuda` (when available)

**Low-Risk Areas:**

6. **Gradient Flow**
   - **Risk:** New properties may break differentiability
   - **Mitigation:** Properties return tensors directly (no `.item()` or `.detach()`); offset is additive (differentiable)
   - **Test:** Existing gradient tests should pass unchanged

### Phase C: Implementation

#### Task C1: config.py Changes

**File:** `src/nanobrag_torch/config.py`

**Changes:**
1. Add `BeamCenterSource` enum (7 lines)
2. Add `beam_center_source: BeamCenterSource = BeamCenterSource.AUTO` to `DetectorConfig` (1 line + docstring)

**Verification:**
- Import config module in Python REPL
- Instantiate `DetectorConfig` with and without `beam_center_source`
- Verify default is `BeamCenterSource.AUTO`

#### Task C2: __main__.py Changes

**File:** `src/nanobrag_torch/__main__.py`

**Changes:**
1. Define `EXPLICIT_BEAM_CENTER_FLAGS` list (8 flags, ~10 lines with comments)
2. Add source assignment logic after beam center argument parsing (~5 lines)

**Insertion Point:**
After beam center value assignment, before `DetectorConfig` instantiation (likely in `parse_arguments()` or `main()` after argparse)

**Verification:**
- Run CLI with explicit flags: `nanoBragg --beam_center_s 512.5 --beam_center_f 512.5 -default_F 1 -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100 -detpixels 64 -floatfile /tmp/test.bin`
- Add debug print: `print(f"beam_center_source: {detector_config.beam_center_source}")`
- Verify output: `beam_center_source: BeamCenterSource.EXPLICIT`

#### Task C3: detector.py Changes

**File:** `src/nanobrag_torch/models/detector.py`

**Changes:**
1. Update `beam_center_s_pixels` property (add 3-line conditional guard + docstring update)
2. Update `beam_center_f_pixels` property (identical changes)

**Existing Code (Approximate):**
```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm
    if self.config.detector_convention == DetectorConvention.MOSFLM:
        return base + 0.5
    return base
```

**Updated Code:**
```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """
    Convert beam center slow coordinate from mm to pixels.

    MOSFLM convention applies +0.5 pixel offset ONLY to auto-calculated defaults,
    NOT to explicit user-provided coordinates (per spec-a-core.md §72, arch.md §ADR-03).
    """
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == BeamCenterSource.AUTO):
        return base + 0.5
    return base
```

**Verification:**
- Run `tests/test_at_parallel_003.py::test_detector_offset_preservation` (expect PASS after changes)
- Add debug prints to property to log convention and source during test

#### Task C4: Test Coverage

**File:** `tests/test_beam_center_source.py` (new file)

**Test Cases:**

```python
import pytest
import torch
from nanobrag_torch.config import DetectorConfig, DetectorConvention, BeamCenterSource
from nanobrag_torch.models.detector import Detector

class TestBeamCenterSource:
    """Test MOSFLM +0.5 pixel offset behavior for AUTO vs EXPLICIT beam centers."""

    def test_mosflm_auto_applies_offset(self):
        """MOSFLM convention with AUTO source should apply +0.5 pixel offset."""
        config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            beam_center_s_mm=51.2,
            beam_center_f_mm=51.2,
            pixel_size_mm=0.1,
            beam_center_source=BeamCenterSource.AUTO,
            # ... other required fields ...
        )
        detector = Detector(config)

        expected_pixels = 51.2 / 0.1 + 0.5  # 512 + 0.5 = 512.5
        assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(expected_pixels))
        assert torch.allclose(detector.beam_center_f_pixels, torch.tensor(expected_pixels))

    def test_mosflm_explicit_no_offset(self):
        """MOSFLM convention with EXPLICIT source should NOT apply offset."""
        config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            beam_center_s_mm=51.2,
            beam_center_f_mm=51.2,
            pixel_size_mm=0.1,
            beam_center_source=BeamCenterSource.EXPLICIT,
            # ... other required fields ...
        )
        detector = Detector(config)

        expected_pixels = 51.2 / 0.1  # 512.0 (no offset)
        assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(expected_pixels))
        assert torch.allclose(detector.beam_center_f_pixels, torch.tensor(expected_pixels))

    def test_xds_no_offset_regardless_of_source(self):
        """XDS convention should NEVER apply offset (AUTO or EXPLICIT)."""
        for source in [BeamCenterSource.AUTO, BeamCenterSource.EXPLICIT]:
            config = DetectorConfig(
                detector_convention=DetectorConvention.XDS,
                beam_center_s_mm=51.2,
                beam_center_f_mm=51.2,
                pixel_size_mm=0.1,
                beam_center_source=source,
                # ... other required fields ...
            )
            detector = Detector(config)

            expected_pixels = 51.2 / 0.1  # 512.0 (no offset for XDS)
            assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(expected_pixels))
            assert torch.allclose(detector.beam_center_f_pixels, torch.tensor(expected_pixels))

    def test_cli_detection_explicit_flags(self):
        """CLI parser should set source=EXPLICIT when beam center flags provided."""
        # This test would mock argparse args and verify source assignment
        # Implementation depends on CLI architecture
        pass  # Placeholder for CLI integration test

    def test_edge_case_explicit_matches_default(self):
        """User providing explicit beam center matching default should still be EXPLICIT."""
        # Setup: detector size 1024x1024, pixel 0.1mm
        # Default would be: (1024*0.1 + 0.1)/2 = 51.25mm
        # User explicitly provides: --beam_center_s 51.25

        config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            beam_center_s_mm=51.25,  # Matches default
            beam_center_f_mm=51.25,
            pixel_size_mm=0.1,
            beam_center_source=BeamCenterSource.EXPLICIT,  # User provided
            # ... other required fields ...
        )
        detector = Detector(config)

        # Even though value matches default, source=EXPLICIT means no offset
        expected_pixels = 51.25 / 0.1  # 512.5 (no offset for EXPLICIT)
        assert torch.allclose(detector.beam_center_s_pixels, torch.tensor(expected_pixels))
```

**Test Execution:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_beam_center_source.py
```

**Expected Result:** All tests PASS

#### Task C5: Targeted Validation

**Command:**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation tests/test_detector_config.py
```

**Success Criteria:**
- `test_detector_offset_preservation` changes from FAIL → PASS
- All `test_detector_config.py` tests remain PASS (no regressions)
- Runtime < 5 seconds

**Failure Triage:**
- If `test_detector_offset_preservation` still fails: verify source assignment logic in __main__.py
- If `test_detector_config.py` fails: check DetectorConfig default value propagation
- If new errors appear: review import statements and enum usage

#### Task C6: Documentation Sync

**Files to Update:**

1. **docs/architecture/detector.md (§Beam Center Mapping)**
   - Add subsection "AUTO vs EXPLICIT Beam Center Semantics"
   - Document `BeamCenterSource` enum and its effect on MOSFLM offset
   - Provide examples of AUTO vs EXPLICIT CLI invocations

2. **docs/development/c_to_pytorch_config_map.md (MOSFLM row)**
   - Update MOSFLM convention row with `beam_center_source` column
   - Clarify offset applies only to AUTO (default) calculations
   - Add "Explicit User Input" column noting no offset for EXPLICIT

3. **docs/findings.md (New Entry)**
   - Title: "MOSFLM +0.5 Pixel Offset Auto vs Explicit Semantics"
   - Date: 2025-10-12
   - Finding: "MOSFLM offset is convention-specific default behavior, not universal transformation"
   - Resolution: "Added BeamCenterSource enum to distinguish AUTO (offset) vs EXPLICIT (no offset)"
   - Tests: Link to `test_beam_center_source.py` and Phase M3 artifacts

**Documentation Verification:**
- Run `grep -r "beam_center_source" docs/` to ensure all references are consistent
- Verify no stale documentation claims "MOSFLM always applies +0.5 offset"

#### Task C7: Fix Plan Ledger Update

**Update:** `docs/fix_plan.md` → `[DETECTOR-CONFIG-001]` section

**Changes:**
- Update Status: `in_progress` → `pending_validation` (after C1-C6 complete)
- Add Attempt entry documenting Phase B (design) + Phase C (implementation)
- Record metrics: files changed (3), tests added (5 new cases), targeted validation pass/fail counts
- Document artifacts: design.md, test_beam_center_source.py, updated detector.py/config.py/__main__.py
- Note next actions: Phase D full-suite validation

**C8 Cluster Status:**
- Mark C8 as `RESOLVED` pending Phase D validation
- Link to Phase M3 design (this document) and Phase C implementation artifacts

### Phase D: Validation

#### Task D1: Full Suite Execution

**Pre-Run Checklist:**
- [ ] All Phase C changes committed
- [ ] Virtual environment refreshed (`pip install -e .`)
- [ ] No uncommitted changes in working directory
- [ ] Previous STAMP captured: Phase M2 `20251011T193829Z` (561 passed / 13 failed / 112 skipped)

**Command:**
```bash
export STAMP=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p reports/2026-01-test-suite-triage/phase_m/$STAMP/{artifacts,logs,analysis,env}

# Full suite execution (10-chunk ladder per Phase M0 pattern)
for chunk in {0..9}; do
    env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ \
        -v --maxfail=0 --durations=20 \
        --junitxml=reports/2026-01-test-suite-triage/phase_m/$STAMP/artifacts/chunk_${chunk}.xml \
        2>&1 | tee reports/2026-01-test-suite-triage/phase_m/$STAMP/logs/chunk_${chunk}.log &
done
wait

# Aggregate results
cat reports/2026-01-test-suite-triage/phase_m/$STAMP/logs/chunk_*.log \
    > reports/2026-01-test-suite-triage/phase_m/$STAMP/logs/pytest_full.log
```

**Timeout:** 3600s (60 minutes) per chunk maximum

**Success Criteria:**
- C8 test `test_at_parallel_003::test_detector_offset_preservation` **PASSES**
- No new test failures introduced (net failures ≤ 13 from Phase M2 baseline)
- Pass rate ≥ 81.8% (Phase M2 baseline: 561/686 = 81.8%)

#### Task D2: Regression Analysis

**Compare Phase M vs Phase M2 (20251011T193829Z):**

| Metric | Phase M2 Baseline | Phase M (Post-Fix) | Delta |
|--------|-------------------|-------------------|-------|
| Total Tests | 686 | 686 | 0 |
| Passed | 561 (81.8%) | _TBD_ | _TBD_ |
| Failed | 13 (1.9%) | _TBD_ | _TBD_ |
| Skipped | 112 (16.3%) | _TBD_ | _TBD_ |
| C8 Cluster | 1 FAIL | 0 FAIL | **-1 FAIL** ✅ |
| New Failures | N/A | _TBD_ | **0 expected** |

**Regression Criteria:**
- **Pass:** No new failures; C8 resolved
- **Conditional Pass:** 1-2 new failures in unrelated clusters (e.g., C2 gradients, C16 orthogonality); C8 still resolved
- **Fail:** New failures in detector geometry tests (C4, C6, C8 related); requires immediate triage

#### Task D3: C-PyTorch Parity Validation

**Test Matrix:**

| Scenario | C Behavior | PyTorch Behavior (Pre-Fix) | PyTorch Behavior (Post-Fix) |
|----------|------------|----------------------------|----------------------------|
| MOSFLM + AUTO | Applies +0.5 offset | ✅ Applies +0.5 | ✅ Applies +0.5 |
| MOSFLM + EXPLICIT | No offset | ❌ Applies +0.5 | ✅ No offset |
| XDS + AUTO | No offset | ✅ No offset | ✅ No offset |
| XDS + EXPLICIT | No offset | ✅ No offset | ✅ No offset |

**Parity Commands:**

```bash
# MOSFLM EXPLICIT case (primary fix target)
nanoBragg --convention MOSFLM --beam_center_s 512.5 --beam_center_f 512.5 \
    -default_F 1 -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100 -detpixels 64 \
    -floatfile /tmp/pytorch_mosflm_explicit.bin

$NB_C_BIN -convention MOSFLM -Xbeam 51.2 -Ybeam 51.2 \
    -default_F 1 -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100 -detpixels 64 \
    -floatfile /tmp/c_mosflm_explicit.bin

# Compare
python scripts/compare_float_images.py \
    /tmp/c_mosflm_explicit.bin /tmp/pytorch_mosflm_explicit.bin \
    --expected_shape 64 64

# Success criterion: correlation ≥ 0.999
```

**Expected Correlation:**
- Pre-fix: ~0.99 (slight geometry mismatch from unintended offset)
- Post-fix: ≥0.999 (C-PyTorch parity restored)

---

## Test Plan & Acceptance Criteria

### Unit Tests (New)

**File:** `tests/test_beam_center_source.py`

1. **test_mosflm_auto_applies_offset** — Verify AUTO + MOSFLM = offset applied
2. **test_mosflm_explicit_no_offset** — Verify EXPLICIT + MOSFLM = no offset
3. **test_xds_no_offset_regardless_of_source** — Verify XDS never applies offset
4. **test_cli_detection_explicit_flags** — Verify CLI parser sets source=EXPLICIT correctly
5. **test_edge_case_explicit_matches_default** — Verify explicit source overrides value matching

**Acceptance:** All 5 tests PASS

### Integration Tests (Existing)

**File:** `tests/test_at_parallel_003.py`

- **test_detector_offset_preservation** — Changes from FAIL → PASS

**File:** `tests/test_detector_config.py`

- All existing tests remain PASS (no regressions from config change)

### Parity Tests

**C vs PyTorch correlation ≥ 0.999 for:**
- MOSFLM + AUTO (baseline behavior)
- MOSFLM + EXPLICIT (fixed behavior)
- XDS + AUTO (unchanged)
- XDS + EXPLICIT (unchanged)

### Full Suite Acceptance

**Phase D Exit Criteria:**
- [ ] C8 cluster (1 failure) resolved to 0 failures
- [ ] No new failures in detector geometry clusters (C4, C6)
- [ ] Pass rate ≥ 81.8% (Phase M2 baseline)
- [ ] Total failures ≤ 13 (Phase M2 baseline)
- [ ] Parity validation: MOSFLM EXPLICIT case correlation ≥ 0.999

---

## Risk Mitigation

### API-002: pix0_vector Override Interaction

**Risk:** Users providing `--pix0_vector` and explicit beam center may have ambiguous expectations

**Mitigation:**
- `pix0_vector` presence does **not** set source=EXPLICIT
- `pix0_vector` is a low-level override applied **after** beam center → origin calculation
- If user provides both `pix0_vector` and explicit beam center flags, source is set EXPLICIT (beam center flags take precedence)

**Test:**
```python
def test_pix0_vector_does_not_set_explicit():
    # CLI: --pix0_vector 0.1 0.05 -0.05 (no beam center flags)
    config = DetectorConfig(
        beam_center_source=BeamCenterSource.AUTO,  # Default (no explicit flags)
        pix0_vector_m=[0.1, 0.05, -0.05],
        # ...
    )
    # Verify source is AUTO despite pix0 override
    assert config.beam_center_source == BeamCenterSource.AUTO
```

### CONVENTION-001: CUSTOM Convention Behavior

**Risk:** CUSTOM convention may incorrectly apply offset if source=AUTO

**Mitigation:**
- Two-condition guard in detector properties checks **convention first**
- CUSTOM short-circuits before source check: `if (convention == MOSFLM and source == AUTO)`
- CUSTOM is excluded from offset logic by design

**Test:**
```python
def test_custom_convention_never_applies_offset():
    for source in [BeamCenterSource.AUTO, BeamCenterSource.EXPLICIT]:
        config = DetectorConfig(
            detector_convention=DetectorConvention.CUSTOM,
            beam_center_source=source,
            # ...
        )
        detector = Detector(config)
        # Verify no offset for CUSTOM regardless of source
        expected = config.beam_center_s_mm / config.pixel_size_mm
        assert detector.beam_center_s_pixels == expected
```

### Device/Dtype Neutrality

**Risk:** New code paths may introduce device-specific logic

**Mitigation:**
- All changes are CPU-side config/logic (no GPU operations)
- Detector properties return tensors (device-agnostic)
- Enum comparisons are Python-level (no device interaction)

**Test:**
```bash
# Run targeted tests on CPU
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_beam_center_source.py

# Run targeted tests on GPU (when available)
env KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_beam_center_source.py
```

**Expected:** Both pass with identical results

### Gradient Flow

**Risk:** New properties may break differentiability

**Mitigation:**
- Properties return tensors directly (no `.item()` or `.detach()`)
- Offset is additive operation (differentiable)
- No new computation graph breaks introduced

**Test:**
```bash
# Run existing gradient tests
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py -k "gradcheck"
```

**Expected:** All gradient tests remain PASS (no regressions)

---

## Artifacts & Deliverables

### Phase B Artifacts (This Document)

- [x] B1: Normative spec language captured (§§72, 85-86, ADR-03)
- [x] B2: Option A technical design documented
- [x] B3: CLI propagation plan with test matrix
- [x] B4: Risk assessment and mitigation strategies

### Phase C Deliverables (Implementation)

- [ ] C1: `config.py` updated with `BeamCenterSource` enum
- [ ] C2: `__main__.py` updated with CLI detection logic
- [ ] C3: `detector.py` updated with conditional offset properties
- [ ] C4: `tests/test_beam_center_source.py` created with 5 test cases
- [ ] C5: Targeted validation (`test_at_parallel_003` + `test_detector_config`) executed and passing
- [ ] C6: Documentation synced (detector.md, c_to_pytorch_config_map.md, findings.md)
- [ ] C7: Fix plan ledger updated with Phase C metrics

### Phase D Deliverables (Validation)

- [ ] D1: Full test suite executed (10-chunk ladder, 3600s timeout per chunk)
- [ ] D2: Regression analysis vs Phase M2 baseline (561/13/112)
- [ ] D3: C-PyTorch parity validation (MOSFLM EXPLICIT correlation ≥ 0.999)

### Final Artifacts Bundle

**Location:** `reports/2026-01-test-suite-triage/phase_m3/20251012T010911Z/mosflm_offset/`

**Contents:**
- `design.md` (this document)
- `implementation_summary.md` (Phase C outcomes, file diffs, test results)
- `validation_report.md` (Phase D full-suite results, regression analysis, parity metrics)
- `commands.txt` (all executed commands for reproducibility)

---

## Timeline & Effort Estimate

| Phase | Tasks | Estimated Effort | Dependencies |
|-------|-------|-----------------|--------------|
| **Phase B** (Design) | B1-B4 | 2 hours | Phase M2 complete |
| **Phase C** (Implementation) | C1-C7 | 3-4 hours | Phase B approved |
| **Phase D** (Validation) | D1-D3 | 2-3 hours | Phase C complete |
| **Total** | — | **7-9 hours** | — |

**Critical Path:**
- Phase B (design approval) gates Phase C
- Phase C (all tests passing) gates Phase D
- Phase D (full-suite clean) gates C8 resolution

**Parallel Work Opportunities:**
- C6 (documentation) can proceed in parallel with C4-C5 (testing)
- D2 (regression analysis) can proceed in parallel with D3 (parity validation)

---

## Next Steps (Post-Design Approval)

1. **Supervisor Review:** Galph reviews this design document and provides approval or requests changes
2. **Phase C Kickoff:** Ralph begins implementation following Tasks C1-C7
3. **Continuous Validation:** After C5 (targeted validation), execute Phase D full-suite
4. **C8 Resolution:** Mark C8 cluster as RESOLVED in Phase M3 tracker
5. **Documentation Handoff:** Update `plans/active/detector-config.md` with Phase B-C-D completion status
6. **Next Cluster:** Proceed to next priority cluster from Phase M3 roadmap (e.g., C16 orthogonality, C15 mixed units)

---

**Design Status:** ✅ **COMPLETE — Ready for Implementation**
**Next Action:** Supervisor approval → Phase C implementation
**Estimated Completion:** Phase D validation by 2025-10-12 (9 hours total effort)

---

## Appendix: Alternative Designs Considered

### Option B: Default Value Heuristic (REJECTED)

**Approach:**
```python
def _is_auto_calculated(self) -> bool:
    default_s = (self.config.detsize_s_mm - self.config.pixel_size_mm) / 2
    default_f = (self.config.detsize_f_mm + self.config.pixel_size_mm) / 2
    return (abs(self.config.beam_center_s_mm - default_s) < 1e-6 and
            abs(self.config.beam_center_f_mm - default_f) < 1e-6)

@property
def beam_center_s_pixels(self) -> torch.Tensor:
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm
    if self.config.detector_convention == DetectorConvention.MOSFLM and self._is_auto_calculated():
        return base + 0.5
    return base
```

**Pros:**
- No config changes required
- Backward compatible

**Cons:**
- Fragile heuristic: user coincidentally providing default value triggers wrong path
- Couples beam center logic to detector size logic
- Harder to audit: must reverse-engineer whether offset was applied from final values
- Cannot distinguish "user provided default" from "user provided nothing (use default)"

**Rejection Reason:**
Semantic ambiguity and edge case fragility outweigh backward compatibility convenience.

### Option C: CLI Flag Override (-explicit_beam_center) (REJECTED)

**Approach:**
Add new CLI flag `--explicit_beam_center` to signal user intent:
```bash
nanoBragg --explicit_beam_center --beam_center_s 512.5 --beam_center_f 512.5 ...
```

**Pros:**
- Explicit user control
- No need to infer from presence of other flags

**Cons:**
- Increases CLI surface area unnecessarily
- Redundant: presence of beam center flags already signals intent
- Adds user friction (extra flag to remember)
- Poor UX: users must remember to add flag when providing beam center

**Rejection Reason:**
Source can be reliably inferred from existing CLI flags; adding a new flag is unnecessary complexity.

---

**END OF DESIGN DOCUMENT**
