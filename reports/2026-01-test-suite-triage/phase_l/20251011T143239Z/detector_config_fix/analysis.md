# Phase L - Detector Config Fix Analysis

**Date:** 2025-10-11
**Workstream:** [DETECTOR-CONFIG-001] Detector defaults audit
**Loop Type:** Ralph implementation loop
**Git SHA:** (pending commit)

## Objective

Implement MOSFLM +0.5 pixel offset in beam center mm→pixel conversion per specs/spec-a-core.md §72 and arch.md §ADR-03 to resolve C8 cluster failures.

## Problem Statement

Phase L targeted rerun (Attempt #17) identified missing MOSFLM +0.5 pixel offset in `Detector.__init__` beam center conversion. Spec requires:

> **specs/spec-a-core.md:72** — "Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel"

Test failures showed:
- `test_default_initialization`: Expected 513.0 pixels, got 512.5 (missing +0.5)
- `test_custom_config_initialization`: Expected 1024.5 pixels, got 1024.0 (missing +0.5)

## Root Cause

`src/nanobrag_torch/models/detector.py:92-93` performed mm→pixel conversion WITHOUT applying MOSFLM-specific +0.5 offset:

```python
# OLD (INCORRECT):
beam_center_s_pixels = config.beam_center_s / config.pixel_size_mm
beam_center_f_pixels = config.beam_center_f / config.pixel_size_mm
# No offset applied!
```

This violated the spec contract for MOSFLM convention which requires adding 0.5 pixels AFTER division.

## Implementation

### Changes Made

**File:** `src/nanobrag_torch/models/detector.py`

1. **Lines 95-106** — Added MOSFLM offset during mm→pixel conversion in `__init__`:
```python
# Convert mm to pixels
beam_center_s_pixels = config.beam_center_s / config.pixel_size_mm
beam_center_f_pixels = config.beam_center_f / config.pixel_size_mm

# Apply MOSFLM +0.5 pixel offset AFTER mm→pixel conversion
if config.detector_convention == DetectorConvention.MOSFLM:
    beam_center_s_pixels = beam_center_s_pixels + 0.5
    beam_center_f_pixels = beam_center_f_pixels + 0.5
```

2. **Lines 525-529** — Removed double-offset in BEAM pivot `_calculate_pix0_vector`:
```python
# CRITICAL [DETECTOR-CONFIG-001]: The +0.5 offset was already applied in __init__
# (lines 104-106), so self.beam_center_f/s are now in pixels WITH the offset
# We just need to convert from pixels to meters:
Fbeam = self.beam_center_f * self.pixel_size  # pixels * (m/pixel) → meters
Sbeam = self.beam_center_s * self.pixel_size  # pixels * (m/pixel) → meters
```

3. **Lines 653-657** — Removed double-offset in SAMPLE pivot `_calculate_pix0_vector`:
```python
# CRITICAL [DETECTOR-CONFIG-001]: The +0.5 offset was already applied in __init__
# (lines 104-106 for MOSFLM), so self.beam_center_f/s are now in pixels WITH the offset
# We just need to convert from pixels to meters for all conventions:
Fclose = self.beam_center_f * self.pixel_size  # pixels * (m/pixel) → meters
Sclose = self.beam_center_s * self.pixel_size  # pixels * (m/pixel) → meters
```

4. **Lines 1068-1071** — Updated `verify_beam_center_preservation` method:
```python
# CRITICAL [DETECTOR-CONFIG-001]: beam_center_f/s now ALREADY have the +0.5 offset
# applied in __init__ (lines 104-106 for MOSFLM), so we just convert pixels→meters
Fbeam_original = self.beam_center_f * self.pixel_size
Sbeam_original = self.beam_center_s * self.pixel_size
```

5. **Lines 578-583** — Updated pix0_override handling:
```python
# CRITICAL [DETECTOR-CONFIG-001]: beam_center_f/s now STORE pixel values WITH offset already
# So we just convert Fbeam/Sbeam (which are in meters) back to pixels
self.beam_center_f = (Fbeam / self.pixel_size).to(device=self.device, dtype=self.dtype)
self.beam_center_s = (Sbeam / self.pixel_size).to(device=self.device, dtype=self.dtype)
```

### Design Rationale

The fix centralizes the MOSFLM offset application to a single location (`__init__`) instead of distributing it across multiple calculation methods. This:
1. Ensures consistency — offset is always present when `beam_center_f/s` are read
2. Prevents double-offsets — downstream code treats values as already-offset pixels
3. Maintains differentiability — tensors flow without `.item()` calls
4. Preserves device/dtype neutrality — no hardcoded CPU/GPU assumptions

## Verification

### Targeted Tests (Phase L)

```bash
CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py --maxfail=0
```

**Result:** ✅ ALL 15 TESTS PASSED (1.93s runtime)

- `test_default_initialization` — ✅ PASS (was FAIL)
- `test_custom_config_initialization` — ✅ PASS (was FAIL)
- All other 13 tests — ✅ PASS (no regressions)

### Full Suite Regression (Phase L)

```bash
STAMP=20251011T143239Z
CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0
```

**Result:** (running — see logs/pytest_full.log)

## Spec/Architecture Alignment

✅ **specs/spec-a-core.md:72** — MOSFLM beam-center formula correctly implemented
✅ **arch.md:ADR-03** — MOSFLM offset applied, CUSTOM conventions exempt
✅ **docs/development/c_to_pytorch_config_map.md:54-82** — Beam-center mapping now matches C semantics

## Artifacts

- Logs: `reports/2026-01-test-suite-triage/phase_l/20251011T143239Z/detector_config_fix/logs/pytest_full.log`
- Environment: `reports/2026-01-test-suite-triage/phase_l/20251011T143239Z/detector_config_fix/env/`
- Analysis: `reports/2026-01-test-suite-triage/phase_l/20251011T143239Z/detector_config_fix/analysis.md` (this file)

## Next Actions

1. ✅ Targeted tests pass — verification complete
2. ⏳ Full suite regression check — awaiting completion
3. ⏳ Update docs/fix_plan.md with Attempt #18 entry
4. ⏳ Commit changes with descriptive message
5. ⏳ Update remediation_tracker.md (C8 cluster resolved)

## Exit Criteria Status

- ✅ Detector initialization tests pass (15/15)
- ✅ Defaults match spec (MOSFLM +0.5 pixel offset applied)
- ✅ CLI mapping documented (comments reference spec §72, ADR-03)
- ⏳ Full suite regression clean (pending)
