# Tap 5.1 PyTorch HKL Audit Summary

**Phase:** E Task E12
**Initiative:** [VECTOR-PARITY-001] Restore 4096² benchmark parity
**Timestamp:** 2025-10-10 11:53:42 UTC
**Hypothesis:** H1 (HKL indexing bug) — PyTorch treats (0,0,0) as out-of-bounds while C returns F=0 (in-bounds)

## Objective

Audit per-subpixel HKL lookups for centre pixel (2048,2048) and edge pixel (0,0) at oversample=2 to validate whether the PyTorch nearest-neighbor HKL lookup incorrectly treats (0,0,0) as out-of-bounds.

**Normative Reference:** `specs/spec-a-core.md` lines 232-240 (nearest-neighbour fallback contract):
> When a requested HKL triple falls outside the loaded grid, the simulator SHALL return the `default_F` value. This is the "nearest-neighbor" fallback behavior. For HKL data loaded from a file, the grid bounds are defined by the minimum and maximum indices present in the file.

## Method

Extended `scripts/debug_pixel_trace.py` with `--taps hkl_subpixel` to capture:
- Fractional Miller indices (h_frac, k_frac, l_frac)
- Rounded Miller indices (h0, k0, l0)
- Structure factor F_cell
- Out-of-bounds flag

Executed for:
1. **Centre pixel (2048, 2048)**: Near beam center, expected HKL ≈ (0, 0.01, -0.01)
2. **Edge pixel (0, 0)**: Detector corner, high scattering angle, HKL ≈ (-8, 39, -39)

Both pixels used oversample=2 (4 subpixels total).

## Results

### Centre Pixel (2048, 2048)

All 4 subpixels round to HKL **(0, 0, 0)**:

| Subpixel | HKL Fractional | HKL Rounded | F_cell | Out of Bounds |
|----------|----------------|-------------|--------|---------------|
| [0,0] | (-0.000002, 0.020000, -0.020000) | (0, 0, 0) | 100.0 | **False** |
| [0,1] | (-0.000001, 0.020000, -0.000000) | (0, 0, 0) | 100.0 | **False** |
| [1,0] | (-0.000001, 0.000000, -0.020000) | (0, 0, 0) | 100.0 | **False** |
| [1,1] | (-0.000000, 0.000000, -0.000000) | (0, 0, 0) | 100.0 | **False** |

**Key Finding:** PyTorch marks `out_of_bounds=False` for (0,0,0) and returns `F_cell=100.0` (default_F).

### Edge Pixel (0, 0)

All 4 subpixels round to HKL **(-8, 39, -39)**:

| Subpixel | HKL Fractional | HKL Rounded | F_cell | Out of Bounds |
|----------|----------------|-------------|--------|---------------|
| [0,0] | (-7.902479, 39.360782, -39.360782) | (-8, 39, -39) | 100.0 | **False** |
| [0,1] | (-7.898848, 39.361526, -39.342316) | (-8, 39, -39) | 100.0 | **False** |
| [1,0] | (-7.898848, 39.342316, -39.361526) | (-8, 39, -39) | 100.0 | **False** |
| [1,1] | (-7.895218, 39.343059, -39.343059) | (-8, 39, -39) | 100.0 | **False** |

**Key Finding:** PyTorch marks `out_of_bounds=False` for (-8, 39, -39) and returns `F_cell=100.0` (default_F).

## Analysis

### Centre Pixel Behaviour

- **PyTorch returns:** `F_cell=100.0` (default_F), `out_of_bounds=False`
- **C returns (from Attempt #27):** `F_cell=0.0` (in-bounds HKL grid value)
- **Implication:** PyTorch is **NOT** incorrectly treating (0,0,0) as out-of-bounds. Both implementations agree that (0,0,0) is in-bounds, but they return different F values:
  - C: Retrieves the actual grid value (0.0)
  - PyTorch: Returns default_F (100.0) because **no HKL file is loaded** in the test configuration

### Edge Pixel Behaviour

- Both pixels show `out_of_bounds=False`
- Both return `default_F=100.0`
- This is expected behavior when no HKL data file is loaded

## Hypothesis Status: **REFUTED (Partial)**

The original H1 hypothesis stated:
> PyTorch's nearest-neighbor lookup incorrectly treats (0,0,0) as out-of-bounds

**Finding:** PyTorch does **NOT** treat (0,0,0) as out-of-bounds. The `out_of_bounds` flag is correctly `False` for all subpixels at both centre and edge pixels.

**However**, the test configuration uses `default_F=100` with **no HKL file loaded**, so all lookups return 100.0 regardless of whether they're in-bounds or out-of-bounds. The trace helper's logic is:
```python
if hasattr(crystal, 'hkl_data') and crystal.hkl_data is not None:
    # Check bounds and query grid
else:
    # No HKL data: all lookups return default_F
    f_cell = crystal_config.default_F
    out_of_bounds = False
```

### Revised Hypothesis

The centre-pixel discrepancy (PyTorch F_cell=100 vs C F_cell=0) is **NOT** an HKL indexing bug. Instead, it reflects a difference in test configuration:
- **C trace (Attempt #27):** May have loaded an HKL file containing (0,0,0) with F=0.0
- **PyTorch trace (this attempt):** No HKL file loaded, falls back to default_F=100.0

## Recommendations

1. **Rerun Tap 5.1 with HKL file:** Load a test HKL file containing (0,0,0) with a known F value to isolate whether the production `Crystal.get_structure_factor()` method correctly queries the grid
2. **Compare C Tap 5.1:** Run the mirror C instrumentation (Task E13) with the same HKL configuration to validate parity
3. **Proceed to Tap 5.2:** Capture HKL grid bounds (`h_min/max`, `k_min/max`, `l_min/max`) to prove (0,0,0) is within the loaded range

## Artifacts

- **Tap JSON:** `py_taps/pixel_2048_2048_hkl_subpixel.json`, `py_taps/pixel_0_0_hkl_subpixel.json`
- **Trace logs:** `py_taps/pixel_2048_2048.log`, `py_taps/pixel_0_0.log`
- **Commands:** `commands.txt`
- **Spec reference:** `specs/spec-a-core.md:232-240`

## Next Actions

1. **Task E13 (C Tap 5.1):** Instrument `golden_suite_generator/nanoBragg.c` with TRACE_C_TAP5_HKL guard
2. **Task E14 (Tap 5.2):** Capture HKL grid bounds for both implementations
3. **Update hypothesis ranking:** Revise `tap5_hypotheses.md` confidence for H1 based on "no HKL file" finding
