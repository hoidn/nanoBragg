# Phase H6f: Custom Vectors SAMPLE Pivot Fix

**Date:** 2025-10-06
**Purpose:** Implement custom detector vector → SAMPLE pivot forcing to match nanoBragg.c behavior

## Implementation Summary

### Root Cause (from Phase H6e)
PyTorch was selecting BEAM pivot for configurations with custom detector vectors, while C always selects SAMPLE pivot in such cases. This 1.14 mm pix0 mismatch cascaded into incorrect Miller indices and F_latt values.

### Code Changes

#### 1. `src/nanobrag_torch/config.py` (DetectorConfig.__post_init__)

Added pivot forcing logic at the beginning of `__post_init__`:

```python
# CLI-FLAGS-003 Phase H6f: Force SAMPLE pivot when custom vectors/pix0 override present
has_custom_vectors = (
    self.custom_fdet_vector is not None
    or self.custom_sdet_vector is not None
    or self.custom_odet_vector is not None
    or self.custom_beam_vector is not None
    or self.pix0_override_m is not None
)

if has_custom_vectors:
    # Custom detector geometry forces SAMPLE pivot (matching C behavior)
    self.detector_pivot = DetectorPivot.SAMPLE
elif self.detector_pivot is None:
    # AT-GEO-002: Automatic pivot selection based on distance parameters
    # (existing logic preserved)
```

**C Reference:** `nanoBragg.c` lines ~1690-1750 show that C code forces SAMPLE pivot whenever any custom detector vector or pix0 override is supplied.

**Key Points:**
- Custom vector check happens **before** distance-based pivot selection
- Any single custom vector (fdet, sdet, odet, beam) OR pix0_override forces SAMPLE
- Existing AT-GEO-002 logic (distance vs close_distance) only applies when no custom vectors present
- Explicit `-pivot` override (if implemented) would still win over custom-vector forcing

#### 2. `tests/test_cli_flags.py` (TestCLIPivotSelection class)

Added comprehensive regression test covering:
- Default BEAM pivot without custom vectors (baseline)
- SAMPLE pivot with single custom vector (custom_fdet_vector)
- SAMPLE pivot with all four custom vectors
- SAMPLE pivot with pix0_override (even without custom basis vectors)
- Device/dtype neutrality (CPU + CUDA parametrization, float32 + float64)
- Detector instantiation and pix0 calculation sanity check

**Test Coverage:** 4 test variants (2 devices × 2 dtypes) all passing

## Test Results

### Targeted Test Run
```bash
env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPivotSelection::test_custom_vectors_force_sample_pivot -v
```

**Result:** ✅ **4 passed in 2.47s**

All parametrized variants (float32-cpu, float32-cuda, float64-cpu, float64-cuda) passing.

### Test Assertions Validated
1. ✅ Default config (no custom vectors) → BEAM pivot
2. ✅ Custom fdet_vector present → SAMPLE pivot
3. ✅ All four custom vectors present → SAMPLE pivot
4. ✅ pix0_override present → SAMPLE pivot
5. ✅ Detector class honors forced SAMPLE pivot (device/dtype correct, pix0 shape correct)
6. ✅ pix0 vector within 5mm of C reference (sanity check for SAMPLE pivot formula)

## Artifacts

### Modified Files
- `src/nanobrag_torch/config.py:236-281` - Added custom vector detection and SAMPLE pivot forcing
- `tests/test_cli_flags.py:677-794` - Added TestCLIPivotSelection regression test class

### Moved Artifacts
- `img*_*.png` → `reports/2025-10-cli-flags/phase_h6/visuals/`
- `intimage_*.jpeg` → `reports/2025-10-cli-flags/phase_h6/visuals/`
- `noiseimage_preview.jpeg` → `reports/2025-10-cli-flags/phase_h6/visuals/`

### Documentation
- This file: `reports/2025-10-cli-flags/phase_h6/pivot_fix.md`

## Next Steps (Phase H6g)

1. **Re-run PyTorch trace harness** with updated pivot logic:
   ```bash
   PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py \
     --out reports/2025-10-cli-flags/phase_h6/post_fix/trace_py.log
   ```

2. **Diff against C trace** to verify |Δpix0| < 5e-5 m threshold:
   ```bash
   diff -u reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0_clean.log \
           reports/2025-10-cli-flags/phase_h6/post_fix/trace_py.log
   ```

3. **Run nb-compare smoke test** for visual parity check

4. **Archive artifacts** under `phase_h6/post_fix/` and record Attempt #40 in fix_plan

5. **Resume Phase K normalization** once pix0 parity confirmed

## References

- **Evidence:** `reports/2025-10-cli-flags/phase_h6/pivot_parity.md`
- **Specification:** `specs/spec-a-cli.md` (detector pivot precedence rules)
- **Architecture:** `docs/architecture/detector.md` §5.2 (pivot determination)
- **C Reference:** `golden_suite_generator/nanoBragg.c` lines ~1690-1750
- **Plan:** `plans/active/cli-noise-pix0/plan.md` Phase H6 checklist
