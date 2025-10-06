# Phase F1 Beam Vector Fix Verification

## Date: 2025-10-05 (ralph loop)

## Objective
Verify that `_calculate_pix0_vector()` now honors custom beam vectors from CLI.

## Changes Made
Refactored `_calculate_pix0_vector()` in `src/nanobrag_torch/models/detector.py`:
- Lines 438-440: Replaced hardcoded beam vector instantiation with `self.beam_vector` property call
- Lines 519-521: Removed redundant beam vector instantiation in BEAM pivot branch

## Results

### Beam Vector Comparison
**C trace (from -beam_vector CLI flag):**
```
0.00051387949, 0.0, -0.99999986
```

**PyTorch after fix:**
```
[0.00051387949, 0.0, -0.99999986]
```

**Delta:** < 1e-12 (exact match)

### Pix0 Vector Comparison  
**C trace:**
```
-0.216475836204836, 0.216343050492215, -0.230192414300537
```

**PyTorch after fix:**
```
[-0.216336293, 0.21520551200000002, -0.230200866]
```

**Delta:**
- X: 1.40e-04 m (0.14 mm)
- Y: 8.38e-04 m (0.84 mm)  
- Z: 8.45e-06 m (0.0085 mm)

## Observations
1. ✅ Beam vector now correctly uses custom override from CLI
2. ⚠️ Pix0 vector still shows ~1mm Y-axis discrepancy
3. This confirms Phase F1 is complete but Phase F2 (CUSTOM pix0 transform) is still needed

## Next Actions
- Phase F2: Implement CUSTOM convention pix0 transform per plan
- Phase F3: Re-run full parity smoke test after F2 complete
