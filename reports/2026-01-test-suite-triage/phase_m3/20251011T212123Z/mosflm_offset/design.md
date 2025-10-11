# MOSFLM Beam Center Offset Remediation Design (Option A)

**Initiative:** DETECTOR-CONFIG-001
**Design Date:** 2026-01-21
**Author:** ralph
**Status:** Phase B Design — Awaiting Supervisor Approval
**STAMP:** 20251011T212123Z

## Executive Summary

This design specifies the **Option A** approach to implementing specification-compliant MOSFLM beam center handling, which explicitly distinguishes between **auto-calculated** and **explicitly user-provided** beam centers via a `beam_center_source` provenance flag.

**Core Decision:** Add a `beam_center_source` field (Literal["auto", "explicit"]) to `DetectorConfig` and conditionally apply the MOSFLM +0.5 pixel offset **only when `beam_center_source == "auto"`**.

**Rationale:** This approach:
- Preserves exact spec compliance (spec-a-core.md §72: "+0.5·pixel offset applies to **defaults**, not explicit values")
- Eliminates ambiguity (no heuristics; provenance is tracked explicitly)
- Maintains backward compatibility (defaults remain correct)
- Supports future extensions (explicit/auto distinction generalizes to other conventions)

## 1. Normative Requirements

### 1.1 Specification Contract (spec-a-core.md §§68-73)

The normative requirement from the spec is:

> **MOSFLM Convention** (§72):
> - Default Xbeam = (detsize_s + pixel)/2, Ybeam = (detsize_f + pixel)/2.
> - **Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel.** Pivot = BEAM.

**Critical Interpretation:** The "+0.5·pixel" offset is part of the **mapping formula** from (Xbeam, Ybeam) → (Sbeam, Fbeam), not a universal adjustment to all beam center inputs.

Per arch.md §ADR-03 and c_to_pytorch_config_map.md (Detector Parameters §Beam Center Source Detection), this offset:
- **SHALL apply** to auto-calculated defaults (when no explicit beam center flags are provided)
- **SHALL NOT apply** to explicitly user-provided beam centers (via CLI flags or API)

### 1.2 Current Failure Mode

Phase L analysis (`reports/.../phase_l/20251011T104618Z/detector_config/analysis.md`) confirms:

**Failing Tests:**
- `tests/test_detector_config.py::TestDetectorConfig::test_default_initialization`
- `tests/test_detector_config.py::TestDetectorConfig::test_custom_config_initialization`

**Root Cause:** Current implementation divides `beam_center_s_mm / pixel_size_mm` without adding the MOSFLM +0.5 pixel offset, producing incorrect beam center pixel values.

**Expected vs Actual:**
- Expected (MOSFLM auto): `513.0` pixels (512.5 + 0.5 offset)
- Actual (current): `512.5` pixels (missing offset)
- Expected (explicit): `128.0` pixels (no offset)
- Actual (current): `128.0` pixels (correct by accident)

## 2. Design Specification

### 2.1 Configuration Layer Changes

**File:** `src/nanobrag_torch/config.py`

**Modification:** Add `beam_center_source` field to `DetectorConfig`:

```python
from typing import Literal

@dataclass
class DetectorConfig:
    # ... existing fields ...

    beam_center_source: Literal["auto", "explicit"] = "auto"
    """
    Provenance of beam center values:
    - "auto": Beam center was auto-calculated from detector defaults
              (MOSFLM convention applies +0.5 pixel offset per spec §72)
    - "explicit": User explicitly provided beam center via CLI or API
                  (no offset applied; values used as-is)

    Spec: spec-a-core.md §72, arch.md §ADR-03
    """
```

**Device/Dtype Neutrality:** This field is a string literal (not a tensor), so device/dtype concerns do not apply.

**Differentiability:** This field does not participate in gradient computation (metadata only).

### 2.2 CLI Detection Logic

**File:** `src/nanobrag_torch/__main__.py`

**Modification:** Add helper function `determine_beam_center_source()` and update argparse handling:

```python
def determine_beam_center_source(args: argparse.Namespace) -> Literal["auto", "explicit"]:
    """
    Determine beam center provenance from CLI arguments.

    Returns "explicit" if any of these flags are present:
    - -Xbeam, -Ybeam (MOSFLM/DENZO/ADXV style)
    - --beam-center-s, --beam-center-f (direct API)
    - -Xclose, -Yclose (XDS/DIALS SAMPLE pivot)
    - -ORGX, -ORGY (XDS origin pixels)
    - -img, -mask (header ingestion, if beam center keys present)

    Otherwise returns "auto" (beam center will be calculated from defaults).

    Spec: spec-a-core.md §72, c_to_pytorch_config_map.md §Beam Center Source Detection
    """
    explicit_flags = [
        args.Xbeam is not None,
        args.Ybeam is not None,
        args.beam_center_s is not None,  # If we add API flags
        args.beam_center_f is not None,
        args.Xclose is not None,
        args.Yclose is not None,
        args.ORGX is not None,
        args.ORGY is not None,
        # Header ingestion check (simplified; actual logic needs header parse)
        # For now: if -img/-mask provided, assume explicit if header contains beam center
        # (Full implementation: parse header first, check for BEAM_CENTER_X/Y keys)
    ]

    return "explicit" if any(explicit_flags) else "auto"

# In main() argparse handling:
# ...
detector_config = DetectorConfig(
    # ... other fields ...
    beam_center_s=beam_center_s,  # mm, from CLI or defaults
    beam_center_f=beam_center_f,  # mm, from CLI or defaults
    beam_center_source=determine_beam_center_source(args),
)
```

**Note on Header Ingestion:** The full implementation should parse `-img`/`-mask` headers **before** calling `determine_beam_center_source()` and check for the presence of `BEAM_CENTER_X`/`BEAM_CENTER_Y` keys. If present, set source to `"explicit"`.

### 2.3 Detector Layer Offset Application

**File:** `src/nanobrag_torch/models/detector.py`

**Modification:** Update beam center pixel conversion properties to conditionally apply offset:

```python
@property
def beam_center_s_pixels(self) -> torch.Tensor:
    """
    Beam center slow-axis position in pixels.

    For MOSFLM convention with auto-calculated beam centers,
    applies the required +0.5 pixel offset per spec §72.

    For explicit user-provided beam centers, uses values as-is.

    Returns: scalar tensor (device/dtype matches self.device/self.dtype)
    """
    # Convert mm → pixels
    beam_center_s_px = self.config.beam_center_s / self.config.pixel_size_mm

    # Apply MOSFLM +0.5 offset for auto-calculated defaults only
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == "auto"):
        beam_center_s_px = beam_center_s_px + 0.5

    # Ensure tensor, preserve device/dtype
    if not isinstance(beam_center_s_px, torch.Tensor):
        beam_center_s_px = torch.tensor(
            beam_center_s_px,
            device=self.device,
            dtype=self.dtype
        )

    return beam_center_s_px.to(device=self.device, dtype=self.dtype)

@property
def beam_center_f_pixels(self) -> torch.Tensor:
    """
    Beam center fast-axis position in pixels.

    For MOSFLM convention with auto-calculated beam centers,
    applies the required +0.5 pixel offset per spec §72.

    For explicit user-provided beam centers, uses values as-is.

    Returns: scalar tensor (device/dtype matches self.device/self.dtype)
    """
    # Convert mm → pixels
    beam_center_f_px = self.config.beam_center_f / self.config.pixel_size_mm

    # Apply MOSFLM +0.5 offset for auto-calculated defaults only
    if (self.config.detector_convention == DetectorConvention.MOSFLM and
        self.config.beam_center_source == "auto"):
        beam_center_f_px = beam_center_f_px + 0.5

    # Ensure tensor, preserve device/dtype
    if not isinstance(beam_center_f_px, torch.Tensor):
        beam_center_f_px = torch.tensor(
            beam_center_f_px,
            device=self.device,
            dtype=self.dtype
        )

    return beam_center_f_px.to(device=self.device, dtype=self.dtype)
```

**Device/Dtype Safety:**
- Properties use `self.device` and `self.dtype` for all tensor construction
- Explicit `.to(device=..., dtype=...)` calls coerce cached values to current dtype (supports dtype switching)
- No hard-coded `.cpu()` or `.cuda()` calls

**Differentiability:**
- Offset is a compile-time constant (0.5), not a parameter
- Conditional logic uses string comparison (does not break gradient flow)
- Beam center tensors preserve `requires_grad` if input config values have it

### 2.4 Cache Invalidation

**Impact:** The beam center pixel properties are computed on-demand (no caching currently). If caching is introduced in the future, cache invalidation must trigger on:
- `config.beam_center_s` / `config.beam_center_f` changes
- `config.beam_center_source` changes
- `config.detector_convention` changes

**Current Implementation:** No changes required (no beam center caching exists).

## 3. Test Impact Matrix

| Test File | Change Type | Rationale |
|-----------|-------------|-----------|
| `tests/test_detector_config.py` | **Modify** | Add explicit `beam_center_source="auto"` to default initialization tests; add new test `test_explicit_beam_center_no_offset` to verify explicit values bypass MOSFLM offset |
| `tests/test_at_parallel_002.py` | **Verify** | Rerun to ensure pixel size independence still holds with offset fix |
| `tests/test_at_parallel_003.py` | **Add** | New test `test_detector_offset_preservation` verifying explicit beam centers match defaults numerically |
| **New:** `tests/test_beam_center_source.py` | **Create** | Comprehensive unit tests for CLI detection logic and API usage patterns |
| **New:** `tests/test_mosflm_offset_parity.py` | **Create** | C↔PyTorch parity test comparing MOSFLM auto vs explicit beam centers |

### 3.1 New Test: Explicit vs Auto Beam Center

**File:** `tests/test_detector_config.py` (append)

```python
def test_explicit_beam_center_no_offset():
    """
    Verify explicit beam centers do not receive MOSFLM +0.5 offset.

    AT-PARALLEL-003 requirement: explicit values used as-is.
    """
    config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        pixel_size_mm=0.1,
        beam_center_s=12.8,  # 128.0 pixels exact
        beam_center_f=12.8,  # 128.0 pixels exact
        beam_center_source="explicit",  # CRITICAL: explicit source
    )
    detector = Detector(config)

    # Explicit source: no offset
    assert torch.isclose(
        detector.beam_center_s_pixels,
        torch.tensor(128.0, dtype=detector.dtype),
        rtol=1e-9
    )
    assert torch.isclose(
        detector.beam_center_f_pixels,
        torch.tensor(128.0, dtype=detector.dtype),
        rtol=1e-9
    )

def test_auto_beam_center_with_offset():
    """
    Verify auto beam centers receive MOSFLM +0.5 offset.

    Spec: spec-a-core.md §72
    """
    config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=None,  # Will default to (1024*0.1 + 0.1)/2 = 51.25 mm
        beam_center_f=None,  # Will default to (1024*0.1 + 0.1)/2 = 51.25 mm
        beam_center_source="auto",  # Auto-calculated
    )
    detector = Detector(config)

    # Auto source with MOSFLM: +0.5 offset
    # 51.25 mm / 0.1 mm = 512.5 pixels → 512.5 + 0.5 = 513.0 pixels
    assert torch.isclose(
        detector.beam_center_s_pixels,
        torch.tensor(513.0, dtype=detector.dtype),
        rtol=1e-9
    )
```

### 3.2 Non-MOSFLM Conventions (Negative Control)

Add tests verifying other conventions (XDS, DIALS, DENZO, ADXV, CUSTOM) do **not** apply the offset regardless of `beam_center_source` value:

```python
@pytest.mark.parametrize("convention", [
    DetectorConvention.XDS,
    DetectorConvention.DIALS,
    DetectorConvention.DENZO,
    DetectorConvention.ADXV,
    DetectorConvention.CUSTOM,
])
def test_non_mosflm_no_offset(convention):
    """
    Verify non-MOSFLM conventions never apply +0.5 offset.

    Spec: Only MOSFLM has the offset per spec-a-core.md §72-73.
    """
    config = DetectorConfig(
        detector_convention=convention,
        pixel_size_mm=0.1,
        beam_center_s=12.8,
        beam_center_f=12.8,
        beam_center_source="auto",  # Even auto should not offset for non-MOSFLM
    )
    detector = Detector(config)

    # No offset regardless of source
    assert torch.isclose(
        detector.beam_center_s_pixels,
        torch.tensor(128.0, dtype=detector.dtype),
        rtol=1e-9
    )
```

## 4. Documentation Impact

| Document | Section | Change |
|----------|---------|--------|
| `docs/architecture/detector.md` | §8.2 Beam Center Mapping | Add explicit/auto distinction; document `beam_center_source` field; note MOSFLM offset applies **only to auto** |
| `docs/development/c_to_pytorch_config_map.md` | Detector Parameters table | Update MOSFLM beam center rows with source-dependent offset formula; add `beam_center_source` row |
| `docs/findings.md` | API-002 (pix0 override) | Note interaction: pix0 overrides affect `beam_center_source` interpretation (if user provides pix0 directly, should be treated as explicit) |
| `README_PYTORCH.md` | Quick Reference | Add example CLI commands showing explicit vs auto beam center behavior |

### 4.1 Updated c_to_pytorch_config_map.md Entry

```markdown
| C-CLI Flag | PyTorch Config Field | C Variable | Units/Convention | Critical Notes |
|------------|---------------------|------------|------------------|----------------|
| `-Xbeam <val>` | `DetectorConfig.beam_center_s` | `Xbeam` | mm → meters | **MOSFLM default: (detsize_s+pixel)/2; maps to Sbeam = Xbeam + 0.5·pixel ONLY for auto-calculated defaults. Explicit `-Xbeam` sets `beam_center_source="explicit"` and bypasses offset.** |
| `-Ybeam <val>` | `DetectorConfig.beam_center_f` | `Ybeam` | mm → meters | **MOSFLM default: (detsize_f+pixel)/2; maps to Fbeam = Ybeam + 0.5·pixel ONLY for auto-calculated defaults. Explicit `-Ybeam` sets `beam_center_source="explicit"` and bypasses offset.** |
| *(new)* | `DetectorConfig.beam_center_source` | *(implicit)* | Literal["auto", "explicit"] | **Auto vs explicit provenance flag. Defaults to "auto". Set to "explicit" when any CLI beam center flag is provided. Controls MOSFLM +0.5 pixel offset application.** |
```

## 5. Risk Assessment

### 5.1 Interacting Findings

**API-002 (pix0 override):**
- **Risk:** If user provides `-pix0_vector_mm` directly, does this count as "explicit" beam center?
- **Mitigation:** Current design focuses on beam center flags only. pix0 override is a separate mechanism (overrides entire detector origin, not just beam center). No immediate collision, but document the interaction in findings.md.
- **Action:** Update API-002 finding to note: "pix0 override bypasses all beam center calculations (both auto and explicit). When pix0 is provided, `beam_center_source` is irrelevant."

**CONVENTION-001 (CUSTOM convention offset):**
- **Risk:** CUSTOM convention spec is silent on +0.5 offset. Current ADR-03 decision: no offset for CUSTOM.
- **Mitigation:** Code explicitly checks `detector_convention == DetectorConvention.MOSFLM` before applying offset. CUSTOM is excluded by design.
- **Action:** No changes needed; existing logic is safe.

### 5.2 Header Ingestion Edge Case

**Scenario:** User provides `-img header.img` where header contains `BEAM_CENTER_X=51.2` (explicit value). Current simplified detection in §2.2 may not parse header before `determine_beam_center_source()` is called.

**Mitigation:** Full implementation must:
1. Parse `-img`/`-mask` headers **before** config construction
2. Check for presence of `BEAM_CENTER_X` and `BEAM_CENTER_Y` keys
3. If present, set `beam_center_source="explicit"`

**Action:** Add TODO comment in CLI parsing code; document in implementation plan (Phase C task C2).

### 5.3 Backward Compatibility

**Impact:** Existing code that constructs `DetectorConfig` directly **without** setting `beam_center_source` will default to `"auto"`, which is the correct behavior for auto-calculated beam centers.

**Verification:**
- Default value (`"auto"`) preserves current behavior for internal usage
- Tests that construct configs directly **must** add explicit `beam_center_source="explicit"` when testing explicit beam centers

**Action:** Audit all test files for direct `DetectorConfig()` instantiation and add `beam_center_source` where appropriate (Phase C task C4).

### 5.4 Device/Dtype Neutrality

**Verification:** Offset application occurs during property evaluation, using `self.device` and `self.dtype` for all tensor operations.

**Tests Required:**
- Smoke test: run detector config tests on both CPU and CUDA (when available)
- Dtype test: verify offset works correctly with float32, float64

**Action:** Add parametrized test in `tests/test_detector_config.py`:

```python
@pytest.mark.parametrize("device", ["cpu", pytest.param("cuda", marks=pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available"))])
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_beam_center_offset_device_dtype_neutral(device, dtype):
    """Verify MOSFLM offset works on all devices/dtypes."""
    config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        pixel_size_mm=0.1,
        beam_center_s=12.8,
        beam_center_f=12.8,
        beam_center_source="auto",
    )
    detector = Detector(config, device=device, dtype=dtype)

    expected = torch.tensor(128.5, device=device, dtype=dtype)  # 128.0 + 0.5
    assert torch.isclose(detector.beam_center_s_pixels, expected, rtol=1e-7)
```

### 5.5 Differentiability

**Impact:** Beam center offset is a compile-time constant (0.5), not a learnable parameter. Conditional logic uses string comparison (does not affect autograd graph).

**Verification:** If beam center values themselves are differentiable tensors (e.g., `requires_grad=True`), gradients should flow through the addition:

```python
def test_beam_center_gradient_flow():
    """Verify gradients flow through beam center offset."""
    beam_s_mm = torch.tensor(12.8, requires_grad=True, dtype=torch.float64)

    config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        pixel_size_mm=0.1,
        beam_center_s=beam_s_mm,
        beam_center_source="auto",
    )
    detector = Detector(config)

    # Forward: beam_s_mm → beam_s_px = (beam_s_mm / 0.1) + 0.5
    beam_s_px = detector.beam_center_s_pixels
    assert beam_s_px.requires_grad

    # Backward
    beam_s_px.backward()
    assert beam_s_mm.grad is not None
    assert torch.isclose(beam_s_mm.grad, torch.tensor(10.0, dtype=torch.float64))  # d(beam_px)/d(beam_mm) = 1/pixel_size = 10
```

**Action:** Add gradient test to `tests/test_gradients.py` (Phase C task C4).

## 6. Implementation Sequence

Mapped to `plans/active/detector-config.md` Phase C tasks:

| Task | File(s) | Description | Exit Criteria |
|------|---------|-------------|---------------|
| C1 | `src/nanobrag_torch/config.py` | Add `beam_center_source` field with default="auto" | Field exists, type-checked |
| C2 | `src/nanobrag_torch/__main__.py` | Implement `determine_beam_center_source()` and integrate into config construction | CLI detection works for all 8 explicit flags |
| C3 | `src/nanobrag_torch/models/detector.py` | Update `beam_center_s_pixels` and `beam_center_f_pixels` properties with conditional offset | Properties apply offset only for MOSFLM + auto |
| C4 | `tests/test_detector_config.py` | Add explicit/auto/non-MOSFLM/device/dtype/gradient tests | All new tests pass |
| C5 | Run targeted validation bundle | Execute detector config + AT-PARALLEL-003 tests | Logs captured under phase_m3/<STAMP>/mosflm_fix/ |
| C6 | Update documentation | Sync detector.md, c_to_pytorch_config_map.md, findings.md | Docs reflect new explicit/auto distinction |
| C7 | Update fix_plan.md and tracker | Log attempt, mark C8 resolved | Plan and tracker in sync |

## 7. Validation Strategy

### 7.1 Targeted Tests (Phase C task C5)

Execute these test selectors and capture logs:

```bash
# Primary detector config tests
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE \
  pytest -v tests/test_detector_config.py \
  --tb=short > detector_config_pytest.log 2>&1

# AT-PARALLEL-003 offset preservation
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE \
  pytest -v tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation \
  --tb=short > at_parallel_003_pytest.log 2>&1

# Device/dtype smoke (if CUDA available)
env KMP_DUPLICATE_LIB_OK=TRUE \
  pytest -v tests/test_detector_config.py::test_beam_center_offset_device_dtype_neutral \
  --tb=short > device_dtype_smoke.log 2>&1

# Gradient flow verification
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -v tests/test_gradients.py::test_beam_center_gradient_flow \
  --tb=short > gradient_flow.log 2>&1
```

**Artifacts:** Store under `reports/2026-01-test-suite-triage/phase_m3/<STAMP>/mosflm_fix/`:
- `detector_config_pytest.log`
- `at_parallel_003_pytest.log`
- `device_dtype_smoke.log`
- `gradient_flow.log`
- `summary.md` (synthesized validation report)

**Success Criteria:**
- All tests in `test_detector_config.py` pass (13/13 → 15/15 after adding new tests)
- AT-PARALLEL-003 passes (if new test added)
- Device/dtype smoke passes on CPU + CUDA (when available)
- Gradient flow test passes

### 7.2 Full-Suite Rerun (Phase D task D1)

After targeted validation succeeds, execute the Phase M chunked rerun per `plans/active/test-suite-triage.md` to verify no regressions:

**Expected Outcome:**
- Failure count: 13 → 12 (C8 cluster resolved: 2 detector config failures eliminated)
- No new failures introduced
- Pass rate improves by ~0.3pp

## 8. Alternative Approaches Considered

### 8.1 Option B: Heuristic Detection

**Description:** Infer explicit vs auto by comparing user-provided beam center to calculated defaults.

**Rejected Because:**
- Fragile: fails when user intentionally sets beam center equal to defaults
- Ambiguous: cannot distinguish "user wants default" from "user calculated and provided matching value"
- Debugging nightmare: behavior changes based on numerical coincidence

### 8.2 Option C: Separate Config Fields

**Description:** Split into `beam_center_s_explicit` and `beam_center_s_auto` fields.

**Rejected Because:**
- API bloat: doubles number of beam center fields
- Mutual exclusivity: requires validation logic to ensure only one is set
- Poor ergonomics: users must choose correct field instead of letting framework track provenance

## 9. Open Questions & Future Work

### 9.1 Header Ingestion Timing

**Question:** Should header parsing occur before or after `determine_beam_center_source()` call?

**Current Answer:** Before. Headers must be parsed first to check for beam center keys, then `determine_beam_center_source()` can inspect both CLI args **and** parsed header values.

**Action:** Update CLI parsing order in §2.2 implementation.

### 9.2 DENZO Convention Offset

**Question:** Spec shows DENZO uses `Fbeam = Ybeam, Sbeam = Xbeam` (no +0.5 offset). Should DENZO also distinguish explicit vs auto?

**Current Answer:** Not required. DENZO has **no offset** in the mapping formula, so explicit/auto distinction is irrelevant. The offset is unique to MOSFLM.

**Action:** Document in detector.md §8.2 that DENZO and other conventions do not need source tracking.

### 9.3 Future Conventions

**Question:** If new conventions are added with their own offset rules, does `beam_center_source` generalize?

**Current Answer:** Yes. The explicit/auto pattern is convention-agnostic. New conventions can check `beam_center_source` and apply their own offset rules for auto-calculated defaults.

**Action:** No immediate changes; design supports future extension.

## 10. Sign-Off Checklist

- [x] Spec citations complete (spec-a-core.md §§68-73, arch.md §ADR-03)
- [x] Option A vs B comparison documented
- [x] CLI propagation logic specified with code examples
- [x] Detector layer changes specified with code examples
- [x] Test impact matrix complete (5 test files)
- [x] Documentation impact table complete (4 docs)
- [x] Risk assessment covers API-002, CONVENTION-001, header ingestion, backward compat, device/dtype, differentiability
- [x] Implementation sequence mapped to Phase C tasks (C1-C7)
- [x] Validation strategy with exact pytest selectors and artifact paths
- [x] Alternative approaches documented with rejection rationale
- [x] Open questions captured with current answers

## 11. Next Steps (Post-Approval)

1. **Supervisor Approval:** Wait for input.md update authorizing Phase C implementation
2. **Implementation Loop:** Execute Phase C tasks C1-C7 per sequence in §6
3. **Targeted Validation:** Capture artifacts per §7.1
4. **Full-Suite Rerun:** Execute Phase D chunked rerun per §7.2
5. **Plan Archival:** Move `plans/active/detector-config.md` → `plans/archive/` once complete

## References

- **Spec:** `specs/spec-a-core.md` §§68-73 (normative MOSFLM mapping)
- **Architecture:** `arch.md` §ADR-03 (offset implementation decision)
- **Config Map:** `docs/development/c_to_pytorch_config_map.md` (CLI↔config parity)
- **Phase L Evidence:** `reports/2026-01-test-suite-triage/phase_l/20251011T104618Z/detector_config/analysis.md`
- **Phase M3 Summary:** `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mosflm_offset/summary.md`
- **Detector Plan:** `plans/active/detector-config.md`
