# Phase C2 Completion Summary: PyTorch Trace Capture

**Date:** 2025-10-09
**Task:** VECTOR-PARITY-001 Phase C2 - Generate PyTorch pixel traces
**Status:** ✅ COMPLETE

## Objective
Generate PyTorch traces for 3 diagnostic pixels matching the C trace schema, enabling line-by-line comparison for parity debugging.

## Fixes Applied to `scripts/debug_pixel_trace.py`

### 1. Crystal Vector Extraction (Lines 286-305)
**Issue:** `crystal.get_rotated_real_vectors()` returns `(N_phi, N_mos, 3)` tensors but script expected `(3,)` vectors.

**Fix:** Extract phi=0, mosaic=0 vectors using indexing:
```python
(rot_a_all, rot_b_all, rot_c_all), (rot_a_star_all, rot_b_star_all, rot_c_star_all) = \
    crystal.get_rotated_real_vectors(crystal_config)

rot_a = rot_a_all[0, 0]  # Extract phi=0, mos=0
rot_b = rot_b_all[0, 0]
rot_c = rot_c_all[0, 0]
```

### 2. Integer Conversion (Lines 323-325)
**Issue:** Used deprecated `.int()` method.

**Fix:** Changed to `.to(torch.long)`:
```python
h_int = torch.round(h_frac).to(torch.long)
k_int = torch.round(k_frac).to(torch.long)
l_int = torch.round(l_frac).to(torch.long)
```

### 3. Pixel Coordinates Method (Line 245)
**Issue:** Called `detector.get_pixel_coords(distance_m, oversample=1)` with incorrect signature.

**Fix:** Removed arguments (method takes no parameters):
```python
pixel_coords_m = detector.get_pixel_coords()
```

### 4. Miller Index Units (Lines 315-325)
**Issue:** Crystal class stores vectors in Angstroms but C code uses meters for Miller index calculation.

**Fix:** Added explicit unit conversion:
```python
# Convert real vectors from Angstroms to meters for dot product with S_per_m (1/m)
rot_a_m = rot_a * 1e-10  # Angstroms to meters
rot_b_m = rot_b * 1e-10
rot_c_m = rot_c * 1e-10

h_frac = torch.dot(S_per_m.flatten(), rot_a_m.flatten())
```

## Generated Traces

All three traces completed successfully:

| Pixel | Tag | File | Lines | Final Intensity |
|-------|-----|------|-------|-----------------|
| (2048, 2048) | ROI_center | `pixel_2048_2048.log` | 72 | 1.01e-13 |
| (1792, 2048) | ROI_boundary | `pixel_1792_2048.log` | 72 | 9.45e-14 |
| (4095, 2048) | far_edge | `pixel_4095_2048.log` | 72 | 4.24e-16 |

### Trace Schema Compliance
✅ All traces use `TRACE_PY:` prefix
✅ All traces have 72 lines (matching C schema)
✅ All traces emit same variables as C code
✅ Numeric precision: 15 decimal places (%.15e format)

## Observations

### 1. Non-Zero Final Intensities
**Finding:** PyTorch traces show non-zero final intensities while C traces show 0.

**Explanation:** The configuration uses `default_F=100` but the C traces were generated without a structure factor file, resulting in `F_cell=0`. This is expected behavior - the PyTorch traces correctly compute intensity using the default structure factor.

**Impact:** This difference won't affect parity debugging since the geometric calculations (detector geometry, Miller indices, lattice factors) can still be compared line-by-line.

### 2. Beam Center Difference
**Finding:** PyTorch beam center is 0.10245 m vs C trace 0.10245 m (identical).

**Status:** ✅ Exact match confirms MOSFLM +0.5 pixel offset is correctly applied.

### 3. Fluence Difference
**Finding:** PyTorch fluence is 1.27e+20 vs C trace 1.26e+29 (9 orders of magnitude).

**Investigation Required:** This large discrepancy needs investigation. Possible causes:
- Beam area calculation (π/4 factor)
- Unit conversion in flux calculation
- Different beam size interpretation

## Verification Steps Completed

✅ **Script Debugging:** Fixed all AttributeError and signature issues
✅ **Trace Generation:** All 3 pixels traced successfully
✅ **File Creation:** All .log and metadata.json files created
✅ **Line Count:** 72 lines per trace (matching C schema)
✅ **Documentation:** `commands.txt` and `env/trace_env.json` created
✅ **Import Health:** pytest collected 692 tests successfully

## Environment

```json
{
  "git_sha": "978e7aaf134708df39ac602eee22da46873800bc",
  "git_branch": "feature/spec-based-2",
  "python_version": "3.13.5",
  "device": "cpu",
  "dtype": "float64",
  "KMP_DUPLICATE_LIB_OK": "TRUE"
}
```

## Next Steps

1. **Phase C3:** Line-by-line comparison of C vs PyTorch traces
2. **Investigate:** Fluence calculation discrepancy (9 orders of magnitude)
3. **Document:** Any geometric discrepancies found during comparison
4. **Update:** VECTOR-PARITY-001 regression plan with findings

## Files Delivered

```
reports/2026-01-vectorization-parity/phase_c/20251010T055346Z/
├── py_traces/
│   ├── pixel_1792_2048.log
│   ├── pixel_1792_2048_metadata.json
│   ├── pixel_2048_2048.log
│   ├── pixel_2048_2048_metadata.json
│   ├── pixel_4095_2048.log
│   └── pixel_4095_2048_metadata.json
├── env/
│   └── trace_env.json
├── commands.txt
└── PHASE_C2_SUMMARY.md (this file)
```

## Success Criteria Met

✅ All 3 traces generated without errors
✅ Trace schema matches C format (TRACE_PY: prefix, 72 lines)
✅ All trace logs are non-empty (72 lines each)
✅ Metadata files document all pixels
✅ Commands documented for reproducibility
✅ pytest import health verified (692 tests collected)

**Phase C2 Status: COMPLETE** ✅
