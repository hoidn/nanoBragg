# MOSFLM Beam Center Offset Remediation Design (Option A)

**STAMP:** 20251011T231914Z
**Phase:** B (Design & Planning)
**Target Initiative:** [DETECTOR-CONFIG-001] Detector defaults audit
**Cluster:** C8 (MOSFLM Beam Center Offset Misapplication)
**Status:** Ready for Phase C implementation approval

---

## 1. Executive Summary

This document specifies the **Option A** remediation approach for fixing the MOSFLM beam center offset misapplication bug (C8). The current implementation incorrectly applies the MOSFLM convention +0.5 pixel offset to ALL beam center coordinates, including explicit user-provided values. The fix will introduce explicit tracking of beam center provenance (auto-calculated vs user-provided) to apply the offset only when appropriate per spec requirements.

**Key Design Decision:** Add `beam_center_source: Literal["auto", "explicit"]` attribute to `DetectorConfig` to distinguish auto-calculated defaults from explicit user inputs.

**Affected Components:**
- `src/nanobrag_torch/config.py` (DetectorConfig dataclass)
- `src/nanobrag_torch/__main__.py` (CLI parsing logic)
- `src/nanobrag_torch/models/detector.py` (beam center pixel conversion properties)

**Exit Criteria:** All tests pass, explicit beam centers preserved exactly, MOSFLM auto-calculated defaults include +0.5 offset per spec.

---

## 2. Normative Requirements (Spec & Arch)

### 2.1 From `specs/spec-a-core.md` §72

> **MOSFLM Convention:**
> - Default Xbeam = (detsize_s + pixel)/2, Ybeam = (detsize_f + pixel)/2.
> - **Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel.** Pivot = BEAM.

**Key requirement:** The +0.5 pixel offset mapping applies when converting from Xbeam/Ybeam (mm) to Fbeam/Sbeam (fast/slow pixel coordinates). This is part of the MOSFLM beam center calculation formula.

### 2.2 From `arch.md` §ADR-03

> **ADR-03 Beam-center Mapping (MOSFLM) and +0.5 pixel Offsets**
> - MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels).
> - CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs.

**Critical interpretation:** The +0.5 pixel offset is a **convention-specific mapping** that applies to the default beam center calculation, NOT to arbitrary user-provided values.

### 2.3 Implicit Requirement (from bug analysis)

When a user explicitly provides beam center coordinates via CLI flags (`-Xbeam`, `-Ybeam`, `-beam_center_s`, `-beam_center_f`, etc.), these values represent the INTENDED beam center and should be used EXACTLY as provided, without applying additional convention-based offsets.

**Rationale:** User-provided coordinates are already in the target coordinate system and should not be modified by internal convention mappings.

---

## 3. Problem Statement

### 3.1 Current Buggy Behavior

The `Detector` class currently applies the MOSFLM +0.5 pixel offset unconditionally in the `beam_center_*_pixels` properties:

```python
# Current buggy implementation (detector.py ~line 520)
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm
    if self.config.detector_convention == DetectorConvention.MOSFLM:
        return base + 0.5  # ❌ WRONG: applies to ALL values
    return base
```

**Problem:** This applies the offset to BOTH auto-calculated defaults AND explicit user inputs, violating the spec requirement that the offset is part of the default calculation formula, not a universal transformation.

### 3.2 Failing Test Case

**Test:** `tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation`

**Scenario:**
- User provides explicit `beam_center_s=512.5` pixels
- Expected: Detector uses exactly 512.5 pixels
- Actual: Detector returns 513.0 pixels (512.5 + 0.5 offset)

**Root Cause:** The detector cannot distinguish between auto-calculated defaults (which should include the offset) and explicit user values (which should not).

---

## 4. Solution Design (Option A)

### 4.1 Core Approach

Introduce explicit provenance tracking for beam center values via a new `beam_center_source` attribute in `DetectorConfig`. This attribute indicates whether the beam center was auto-calculated from defaults or explicitly provided by the user.

**Values:**
- `"auto"`: Beam center was calculated using default formula (should apply MOSFLM offset)
- `"explicit"`: Beam center was provided explicitly by user (should NOT apply additional offset)

**Default:** `"auto"` for backward compatibility with existing code that relies on default calculations.

### 4.2 Implementation Blueprint

#### Component 1: Config Layer (`src/nanobrag_torch/config.py`)

**Change:** Add `beam_center_source` field to `DetectorConfig` dataclass:

```python
@dataclass
class DetectorConfig:
    # ... existing fields ...
    beam_center_s_mm: float
    beam_center_f_mm: float
    beam_center_source: Literal["auto", "explicit"] = "auto"  # NEW FIELD
    # ... other fields ...
```

**Rationale:** Storing provenance at the config level makes it available to all downstream consumers (Detector, validation, tests) without complex logic duplication.

#### Component 2: CLI Layer (`src/nanobrag_torch/__main__.py`)

**Change:** Detect explicit beam center flags during CLI parsing and set `beam_center_source="explicit"`:

```python
# Beam center source detection (add after beam center calculation)
beam_center_source = "auto"  # default

# Check for ANY explicit beam center flag
explicit_flags = [
    args.beam_center_s,
    args.beam_center_f,
    args.Xbeam,
    args.Ybeam,
    args.Xclose,
    args.Yclose,
    args.ORGX,
    args.ORGY,
]

if any(flag is not None for flag in explicit_flags):
    beam_center_source = "explicit"

# Also check header ingestion (if -img or -mask provided)
if args.img or args.mask:
    # Header parsing sets beam center values
    # If header contains beam center, treat as explicit
    beam_center_source = "explicit"

# Pass to config
detector_config = DetectorConfig(
    beam_center_s_mm=beam_center_s,
    beam_center_f_mm=beam_center_f,
    beam_center_source=beam_center_source,  # NEW
    # ... other params ...
)
```

**Explicit Flags Matrix:**

| CLI Flag | Description | Sets source="explicit" |
|----------|-------------|----------------------|
| `-Xbeam <val>` | Direct slow-axis beam center (mm) | ✅ Yes |
| `-Ybeam <val>` | Direct fast-axis beam center (mm) | ✅ Yes |
| `-beam_center_s <val>` | Slow-axis beam center alias | ✅ Yes |
| `-beam_center_f <val>` | Fast-axis beam center alias | ✅ Yes |
| `-Xclose <val>` | Close distance X (SAMPLE pivot) | ✅ Yes |
| `-Yclose <val>` | Close distance Y (SAMPLE pivot) | ✅ Yes |
| `-ORGX <val>` | XDS origin X coordinate | ✅ Yes |
| `-ORGY <val>` | XDS origin Y coordinate | ✅ Yes |
| `-img <file>` | SMV header ingestion | ✅ Yes (if header contains beam center) |
| `-mask <file>` | Mask header ingestion | ✅ Yes (if header contains beam center) |

**Precedence Rule:** If ANY explicit flag is present, `beam_center_source="explicit"`. Only when NO explicit flags are provided does it remain `"auto"`.

#### Component 3: Detector Layer (`src/nanobrag_torch/models/detector.py`)

**Change:** Update `beam_center_*_pixels` properties to conditionally apply MOSFLM offset based on provenance:

```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """Convert beam center slow coordinate from mm to pixels.

    For MOSFLM convention with auto-calculated defaults, adds +0.5 pixel offset
    per spec-a-core.md §72: "Sbeam = Xbeam + 0.5·pixel"

    For explicit user-provided values, uses exact coordinate without offset.
    """
    base = self.config.beam_center_s_mm / self.config.pixel_size_mm

    # Apply MOSFLM offset ONLY for auto-calculated defaults
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == "auto"):
        return base + torch.tensor(0.5, dtype=base.dtype, device=base.device)

    return base

@property
def beam_center_f_pixels(self) -> torch.Tensor:
    """Convert beam center fast coordinate from mm to pixels.

    For MOSFLM convention with auto-calculated defaults, adds +0.5 pixel offset
    per spec-a-core.md §72: "Fbeam = Ybeam + 0.5·pixel"

    For explicit user-provided values, uses exact coordinate without offset.
    """
    base = self.config.beam_center_f_mm / self.config.pixel_size_mm

    # Apply MOSFLM offset ONLY for auto-calculated defaults
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == "auto"):
        return base + torch.tensor(0.5, dtype=base.dtype, device=base.device)

    return base
```

**Key Design Details:**
- Offset created as a tensor (`torch.tensor(0.5, ...)`) with matching dtype/device for PyTorch neutrality
- Offset is a **compile-time constant** (0.5) so it doesn't break differentiability
- Conditional logic is clean: `convention==MOSFLM AND source=="auto"`

---

## 5. Option A vs Option B Comparison

### 5.1 Option B: Value-Based Heuristic (REJECTED)

**Approach:** Compare current beam center values against computed defaults. If they match, assume auto-calculated and apply offset:

```python
def _is_auto_calculated(self) -> bool:
    default_s = (self.config.detsize_s_mm + self.config.pixel_size_mm) / 2
    default_f = (self.config.detsize_f_mm + self.config.pixel_size_mm) / 2
    return (abs(self.config.beam_center_s_mm - default_s) < 1e-6 and
            abs(self.config.beam_center_f_mm - default_f) < 1e-6)
```

**Why Rejected:**
1. **Numerical coincidence problem:** User could legitimately want beam center at the default position explicitly (e.g., to override a header value back to center)
2. **Fragile heuristic:** Floating-point comparison with tolerance is brittle across devices/dtypes
3. **Maintenance burden:** Logic must be duplicated or centralized, adding complexity
4. **Spec misalignment:** Conflates "value happens to match default" with "value was calculated as default"

### 5.2 Option A: Explicit Provenance (RECOMMENDED)

**Advantages:**
1. **Unambiguous:** Provenance is tracked explicitly, no numerical heuristics needed
2. **Spec-aligned:** Directly implements the distinction between auto-calculated and explicit values
3. **Maintainable:** Single source of truth (`beam_center_source` field)
4. **Extensible:** Easy to add more provenance types in future (e.g., `"header_ingested"`, `"computed_from_rotation"`)
5. **Backward compatible:** Default value `"auto"` preserves existing behavior for code not using explicit flags

**Trade-off:** Requires one additional field in `DetectorConfig`, but the benefit far outweighs the minimal API expansion.

---

## 6. Test Impact Matrix

### 6.1 New Test Cases Required

1. **Test: Explicit beam center preservation (MOSFLM)**
   - File: `tests/test_detector_config.py`
   - Scenario: Provide explicit `beam_center_s=512.5`, verify detector uses exactly 512.5 pixels (no +0.5)
   - Convention: MOSFLM
   - Expected: PASS after fix

2. **Test: Auto-calculated beam center with MOSFLM offset**
   - File: `tests/test_detector_config.py`
   - Scenario: No explicit beam center, detector size 1024×1024, pixel 0.1mm
   - Convention: MOSFLM
   - Expected: beam_center should be (detsize+pixel)/2 = 51.25mm → 512.5 pixels (includes +0.5)
   - Status: Should already pass (validates default formula)

3. **Test: Explicit beam center with non-MOSFLM convention**
   - File: `tests/test_detector_config.py`
   - Scenario: Explicit `beam_center_s=512.5`, convention=XDS
   - Expected: Exactly 512.5 pixels (no offset for XDS)
   - Status: Should already pass (XDS doesn't apply offset)

4. **Test: Header-ingested beam center treated as explicit**
   - File: `tests/test_at_parallel_003.py` or `tests/test_detector_config.py`
   - Scenario: Load `-img` file with beam center header, verify no additional MOSFLM offset
   - Expected: PASS (header values used exactly)
   - Status: NEW

5. **Test: Device/dtype neutrality with beam center offset**
   - File: `tests/test_detector_config.py`
   - Scenario: Run MOSFLM auto-calculated case on CPU and CUDA with float32/float64
   - Expected: Identical results across devices/dtypes
   - Status: NEW (validates PyTorch neutrality of fix)

### 6.2 Existing Tests Requiring Updates

1. **File:** `tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation`
   - **Change:** Should PASS after fix (currently FAILS)
   - **Validation:** Explicit beam center preserved exactly

2. **File:** `tests/test_detector_config.py` (default beam center tests)
   - **Change:** Verify default formula calculations include +0.5 offset for MOSFLM
   - **Status:** Likely already correct, but verify after fix

3. **File:** `tests/test_at_parallel_002.py::TestATParallel002::test_beam_center_scales_with_pixel_size`
   - **Change:** Verify scaling behavior with both explicit and auto-calculated beam centers
   - **Status:** Should PASS (validates scaling invariance)

### 6.3 Validation Commands

**Targeted selector (C8 regression test):**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation
```

**Module-level validation (all detector config tests):**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_detector_config.py
```

**Cluster-level validation (all AT-PARALLEL-003 tests):**
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
  tests/test_at_parallel_003.py
```

**Device/dtype smoke test (CPU + CUDA if available):**
```bash
# CPU
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py

# CUDA (if available)
env KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py
```

**Expected Results After Fix:**
- Before: 1 failure in test_detector_offset_preservation
- After: 0 failures, all tests PASS

---

## 7. Documentation Impact

### 7.1 Architecture Documentation

**File:** `docs/architecture/detector.md`

**Updates Required:**
1. **§8.2 Beam Center Defaults:** Document the `beam_center_source` attribute and its role in offset application
2. **§9 MOSFLM Convention:** Clarify that +0.5 pixel offset applies ONLY to auto-calculated defaults, not explicit inputs
3. **Add example:** Show CLI commands with explicit vs auto beam centers and their different behaviors

**Example addition to §9:**
```markdown
### MOSFLM +0.5 Pixel Offset Application

The MOSFLM convention +0.5 pixel offset (per spec-a-core.md §72) applies **only** to auto-calculated beam center defaults:

**Auto-calculated (offset applies):**
```bash
nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 1024
# Result: beam_center = (detsize+pixel)/2 = 51.25mm → 512.5 pixels (includes +0.5)
```

**Explicit user input (no offset):**
```bash
nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 1024 -Xbeam 51.2 -Ybeam 51.2
# Result: beam_center = 51.2mm → 512.0 pixels exactly (no +0.5 applied)
```
```

### 7.2 Configuration Mapping Documentation

**File:** `docs/development/c_to_pytorch_config_map.md`

**Updates Required:**
- Add `beam_center_source` to Detector Parameters table
- Update MOSFLM beam center description to clarify offset semantics
- Add notes about explicit flag detection

**Table addition:**
| C-CLI Flag | PyTorch Config Field | C Variable | Units/Convention | Critical Notes |
|------------|---------------------|------------|------------------|----------------|
| (detection logic) | `DetectorConfig.beam_center_source` | N/A | `"auto"` or `"explicit"` | **NEW:** Tracks provenance of beam center; `"auto"` when using defaults, `"explicit"` when user provides -Xbeam/-Ybeam/etc. Controls whether MOSFLM +0.5 offset is applied. |

### 7.3 Findings Documentation

**File:** `docs/findings.md`

**Cross-reference addition:**
- Update API-002 entry (if exists) to reference the `beam_center_source` fix
- Add note about MOSFLM offset semantics and the explicit vs auto distinction

---

## 8. Risk Assessment & Interactions

### 8.1 API-002: pix0 Override Interaction

**Risk:** If user provides both explicit beam center AND `-pix0_vector` override, which takes precedence?

**Mitigation:**
- Current behavior: `-pix0_vector` overrides beam center calculation entirely
- Proposed: No change needed—`pix0_vector` override is a higher-level operation that bypasses beam center logic entirely
- Document: Add note to detector.md that `-pix0_vector` supersedes beam center calculations

### 8.2 CONVENTION-001: Other Conventions

**Risk:** Does this change affect XDS, DIALS, DENZO, ADXV, or CUSTOM conventions?

**Analysis:**
- XDS/DIALS/ADXV/CUSTOM: Do NOT apply +0.5 offset, so `beam_center_source` check is not needed for these
- DENZO: Currently uses same +0.5 mapping as MOSFLM per spec (Fbeam = Ybeam, Sbeam = Xbeam)
  - Question: Should DENZO also distinguish explicit vs auto?
  - Per spec-a-core.md: "DENZO: Same as MOSFLM bases, Fbeam = Ybeam, Sbeam = Xbeam"
  - **Decision:** DENZO does NOT add +0.5 offset (different from MOSFLM), so no change needed

**Verdict:** MOSFLM is the ONLY convention requiring this fix. Other conventions unaffected.

### 8.3 Header Ingestion Edge Cases

**Risk:** When `-img` or `-mask` headers provide beam center, should they be treated as explicit?

**Decision:** YES, treat header-ingested values as `"explicit"`:
- Rationale: Header values represent a deliberate configuration (often from previous refinement), not a default calculation
- Implementation: Set `beam_center_source="explicit"` when header parsing modifies beam center values

**Edge case:** What if header is missing beam center?
- Fallback to computed defaults with `beam_center_source="auto"` (existing behavior)

### 8.4 PyTorch Device/Dtype Neutrality

**Risk:** Does the offset tensor `torch.tensor(0.5, ...)` break device/dtype agnostic code?

**Mitigation:**
- Use `.dtype` and `.device` from `base` tensor to create offset: `torch.tensor(0.5, dtype=base.dtype, device=base.device)`
- This ensures offset lives on same device/dtype as beam center calculation
- Add smoke test validating CPU/CUDA execution

### 8.5 Differentiability

**Risk:** Does adding offset tensor break gradient flow?

**Analysis:**
- Offset is a compile-time constant (0.5), not a learnable parameter
- Adding a constant to a tensor preserves `requires_grad` property
- No `.item()`, `.detach()`, or `.numpy()` calls in the implementation
- **Verdict:** Gradient flow is preserved

**Validation:** Run existing gradcheck tests after fix to confirm no regressions.

### 8.6 Backward Compatibility

**Risk:** Does default `beam_center_source="auto"` break existing code?

**Analysis:**
- Existing code (tests, scripts) that doesn't set `beam_center_source` will get `"auto"` by default
- For MOSFLM convention with auto-calculated defaults, this preserves current behavior (offset IS applied)
- For explicit CLI usage, the CLI layer will detect flags and set `"explicit"` automatically
- **Verdict:** Fully backward compatible

---

## 9. Implementation Sequence (Phase C Tasks)

### Task Checklist (aligned with `plans/active/detector-config.md` Phase C)

**C1. Update DetectorConfig (config.py)** — 10 min
- [ ] Add `beam_center_source: Literal["auto", "explicit"] = "auto"` field
- [ ] Add docstring explaining provenance tracking
- [ ] Verify dataclass initialization with new field

**C2. Implement CLI detection (__main__.py)** — 30 min
- [ ] Create `determine_beam_center_source()` helper function
- [ ] Check all 8 explicit flags (Xbeam, Ybeam, beam_center_*, Xclose, Yclose, ORGX, ORGY)
- [ ] Check header ingestion flags (-img, -mask)
- [ ] Set `beam_center_source` in DetectorConfig construction
- [ ] Add unit test for detection logic

**C3. Update Detector properties (detector.py)** — 20 min
- [ ] Modify `beam_center_s_pixels` property with conditional offset
- [ ] Modify `beam_center_f_pixels` property with conditional offset
- [ ] Add docstrings explaining MOSFLM offset semantics
- [ ] Ensure device/dtype neutrality (use `.dtype`/`.device` from base tensor)

**C4. Write new test cases** — 45 min
- [ ] Test explicit preservation (MOSFLM, explicit source)
- [ ] Test auto-calculated offset (MOSFLM, auto source)
- [ ] Test non-MOSFLM explicit (XDS, explicit source)
- [ ] Test header ingestion (treat as explicit)
- [ ] Test device/dtype neutrality (CPU + CUDA)

**C5. Update existing tests** — 15 min
- [ ] Verify test_at_parallel_003 now passes
- [ ] Verify test_detector_config.py default tests still pass
- [ ] Verify test_at_parallel_002 scaling test still passes

**C6. Documentation updates** — 30 min
- [ ] Update detector.md §8.2 and §9 with offset semantics
- [ ] Update c_to_pytorch_config_map.md Detector Parameters table
- [ ] Add cross-reference to findings.md (API-002 if applicable)
- [ ] Add CLI examples to detector.md showing explicit vs auto

**C7. Validation bundle** — 20 min
- [ ] Run targeted selector (test_detector_offset_preservation)
- [ ] Run module-level validation (test_detector_config.py)
- [ ] Run cluster-level validation (test_at_parallel_003.py)
- [ ] Run device/dtype smoke tests (CPU + CUDA if available)
- [ ] Capture logs, metrics, and summary in Phase C artifacts

**Total Estimated Time:** 3 hours

---

## 10. Exit Criteria (Phase C Completion)

### 10.1 Code Changes Complete
- [ ] `config.py`: `beam_center_source` field added and documented
- [ ] `__main__.py`: Explicit flag detection logic implemented and tested
- [ ] `detector.py`: Conditional offset logic implemented with device/dtype neutrality

### 10.2 Tests Pass
- [ ] `test_at_parallel_003::test_detector_offset_preservation` PASSES (was FAILING)
- [ ] `test_detector_config.py` full suite PASSES (15/15 tests)
- [ ] All 5 new test cases PASS (explicit preservation, auto offset, non-MOSFLM, header, device/dtype)
- [ ] No regressions in existing test suite (run full `pytest tests/`)

### 10.3 Documentation Updated
- [ ] `detector.md` updated with offset semantics and CLI examples
- [ ] `c_to_pytorch_config_map.md` updated with `beam_center_source` row
- [ ] `findings.md` cross-references updated (if applicable)

### 10.4 Validation Artifacts
- [ ] Targeted selector log captured (test_detector_offset_preservation PASS)
- [ ] Module-level validation log captured (test_detector_config.py 15/15 PASS)
- [ ] Device/dtype smoke test logs captured (CPU + CUDA results)
- [ ] Summary document created at `reports/.../phase_c/<STAMP>/validation_summary.md`

### 10.5 Gradient & Neutrality Verification
- [ ] Existing gradcheck tests still pass (no gradient flow breakage)
- [ ] CPU execution works (CUDA_VISIBLE_DEVICES=-1)
- [ ] CUDA execution works (if available, no device mixing warnings)
- [ ] float32 and float64 both supported

### 10.6 Plan Sync
- [ ] Update `docs/fix_plan.md` [DETECTOR-CONFIG-001] with Phase C completion
- [ ] Update `reports/.../remediation_tracker.md` cluster C8 status
- [ ] Archive Phase C artifacts with STAMP timestamp

---

## 11. Artifact Expectations

### 11.1 Implementation Artifacts
- **Config change:** `git diff src/nanobrag_torch/config.py` showing `beam_center_source` field
- **CLI change:** `git diff src/nanobrag_torch/__main__.py` showing detection logic
- **Detector change:** `git diff src/nanobrag_torch/models/detector.py` showing conditional offset

### 11.2 Test Artifacts
- **New tests:** 5 new test functions in `tests/test_detector_config.py` or `tests/test_at_parallel_003.py`
- **Test results:** `pytest` logs showing all new tests PASS

### 11.3 Validation Artifacts (Phase C5)
- **Targeted log:** `reports/.../phase_c/<STAMP>/test_detector_offset_preservation.log`
- **Module log:** `reports/.../phase_c/<STAMP>/test_detector_config.log`
- **Cluster log:** `reports/.../phase_c/<STAMP>/test_at_parallel_003.log`
- **Device smoke:** `reports/.../phase_c/<STAMP>/{cpu_smoke.log, cuda_smoke.log}` (if CUDA available)
- **Summary:** `reports/.../phase_c/<STAMP>/validation_summary.md` with metrics and results

### 11.4 Documentation Artifacts
- **Detector doc:** Updated `docs/architecture/detector.md` (§8.2, §9 with examples)
- **Config map:** Updated `docs/development/c_to_pytorch_config_map.md` (Detector Parameters table)
- **Findings:** Updated `docs/findings.md` (API-002 cross-ref if applicable)

---

## 12. References

### 12.1 Specification & Architecture
- **Spec:** `specs/spec-a-core.md` §§68-73 (MOSFLM convention, beam center formulas)
- **Arch:** `arch.md` §ADR-03 (Beam-center Mapping and +0.5 pixel offsets)
- **Detector contract:** `docs/architecture/detector.md` (§8 Beam Center Calculations, §9 Conventions)

### 12.2 Related Issues & Plans
- **Fix plan:** `docs/fix_plan.md` [DETECTOR-CONFIG-001]
- **Test suite triage:** `plans/active/test-suite-triage.md` Phase M3
- **Cluster summary:** `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md`
- **Remediation tracker:** `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md` (C8 cluster)

### 12.3 Test Cases
- **Failing test:** `tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation`
- **Unit tests:** `tests/test_detector_config.py` (beam center validation)
- **Parity tests:** `tests/test_at_parallel_002.py` (beam center scaling)

### 12.4 Development Guidelines
- **C-to-PyTorch map:** `docs/development/c_to_pytorch_config_map.md`
- **Testing strategy:** `docs/development/testing_strategy.md` §2 (Configuration Parity)
- **PyTorch runtime:** `docs/development/pytorch_runtime_checklist.md` (device/dtype discipline)

---

## 13. Approval Checklist (for Supervisor)

Before approving Phase C implementation, verify:

- [ ] **Spec alignment:** Design correctly interprets spec-a-core.md §72 MOSFLM formula
- [ ] **Arch alignment:** Consistent with arch.md §ADR-03 offset policy
- [ ] **Option A rationale:** Explicit provenance tracking justified over value-based heuristic (Option B)
- [ ] **Implementation scope:** Changes limited to 3 files (config, __main__, detector)
- [ ] **Test coverage:** 5 new tests adequately validate fix + edge cases
- [ ] **Documentation plan:** All affected docs identified and update plan clear
- [ ] **Risk mitigation:** API-002, CONVENTION-001, header ingestion, device/dtype, differentiability addressed
- [ ] **Effort estimate:** 3-hour implementation sequence reasonable
- [ ] **Exit criteria:** Clear, measurable, and comprehensive

**Approval Signature:** _________________________
**Date:** _________________________

---

## Appendix A: CLI Examples

### A.1 Auto-Calculated Beam Center (MOSFLM, default formula)

```bash
nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 1024 -pixel 0.1
```

**Result:**
- `beam_center_source = "auto"`
- Default: Xbeam = (detsize_s + pixel)/2 = (102.4 + 0.1)/2 = 51.25 mm
- Default: Ybeam = (detsize_f + pixel)/2 = (102.4 + 0.1)/2 = 51.25 mm
- Pixel conversion with MOSFLM offset: 51.25 / 0.1 = 512.5 pixels (includes +0.5)

### A.2 Explicit Beam Center (MOSFLM, user-provided)

```bash
nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 1024 -pixel 0.1 -Xbeam 51.2 -Ybeam 51.2
```

**Result:**
- `beam_center_source = "explicit"` (triggered by `-Xbeam -Ybeam`)
- User: Xbeam = 51.2 mm, Ybeam = 51.2 mm
- Pixel conversion without additional offset: 51.2 / 0.1 = 512.0 pixels exactly

### A.3 Explicit Beam Center (XDS, user-provided)

```bash
nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 1024 -pixel 0.1 -convention XDS -ORGX 512.5 -ORGY 512.5
```

**Result:**
- `beam_center_source = "explicit"` (triggered by `-ORGX -ORGY`)
- XDS: Does NOT apply +0.5 offset (Fbeam = Xbeam; Sbeam = Ybeam)
- User: ORGX = 512.5, ORGY = 512.5 → beam center = 512.5 pixels exactly

### A.4 Header-Ingested Beam Center (MOSFLM, from SMV file)

```bash
nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -img reference.img
```

**Result:**
- `beam_center_source = "explicit"` (header parsing detected)
- Header contains: BEAM_CENTER_X = 51.2, BEAM_CENTER_Y = 51.2
- Treated as explicit user input → 512.0 pixels exactly (no additional offset)

---

## Appendix B: Test Templates

### B.1 Explicit Preservation Test (MOSFLM)

```python
def test_explicit_beam_center_preserved_mosflm():
    """Explicit beam center should be preserved exactly without MOSFLM offset."""
    config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        beam_center_s_mm=51.2,
        beam_center_f_mm=51.2,
        beam_center_source="explicit",  # Explicit user input
        pixel_size_mm=0.1,
        distance_mm=100.0,
        spixels=1024,
        fpixels=1024,
    )
    detector = Detector(config)

    # Explicit values should NOT get +0.5 offset
    assert detector.beam_center_s_pixels == pytest.approx(512.0, abs=1e-6)
    assert detector.beam_center_f_pixels == pytest.approx(512.0, abs=1e-6)
```

### B.2 Auto-Calculated Offset Test (MOSFLM)

```python
def test_auto_beam_center_mosflm_offset():
    """Auto-calculated MOSFLM beam center should include +0.5 pixel offset."""
    config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        beam_center_s_mm=51.25,  # Default formula: (102.4 + 0.1)/2
        beam_center_f_mm=51.25,
        beam_center_source="auto",  # Auto-calculated default
        pixel_size_mm=0.1,
        distance_mm=100.0,
        spixels=1024,
        fpixels=1024,
    )
    detector = Detector(config)

    # Auto-calculated MOSFLM should include +0.5 offset
    assert detector.beam_center_s_pixels == pytest.approx(512.5, abs=1e-6)
    assert detector.beam_center_f_pixels == pytest.approx(512.5, abs=1e-6)
```

### B.3 Device/Dtype Neutrality Test

```python
@pytest.mark.parametrize("device", ["cpu", "cuda"] if torch.cuda.is_available() else ["cpu"])
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_beam_center_offset_device_dtype_neutral(device, dtype):
    """MOSFLM offset should work correctly across devices and dtypes."""
    config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        beam_center_s_mm=torch.tensor(51.25, device=device, dtype=dtype),
        beam_center_f_mm=torch.tensor(51.25, device=device, dtype=dtype),
        beam_center_source="auto",
        pixel_size_mm=torch.tensor(0.1, device=device, dtype=dtype),
        distance_mm=torch.tensor(100.0, device=device, dtype=dtype),
        spixels=1024,
        fpixels=1024,
    )
    detector = Detector(config)

    # Verify offset tensor has correct device/dtype
    result_s = detector.beam_center_s_pixels
    assert result_s.device.type == device
    assert result_s.dtype == dtype

    # Verify numerical result
    assert result_s.item() == pytest.approx(512.5, abs=1e-6)
```

---

**End of Design Document**
