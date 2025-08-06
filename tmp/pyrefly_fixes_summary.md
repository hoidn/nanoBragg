# PyRefly Fixes Summary

## Overview
Successfully fixed all 19 pyrefly static analysis errors in the src/ directory.

## Files Modified (but not staged due to pre-existing changes):
1. **src/nanobrag_torch/models/crystal.py** - 8 errors fixed
2. **src/nanobrag_torch/models/detector.py** - 5 errors fixed  
3. **src/nanobrag_torch/simulator.py** - 6 errors fixed

## Changes Made:

### crystal.py
- Added `Optional` import and used `Optional[CrystalConfig]` for config parameter
- Added type annotation `Optional[torch.Tensor]` for `hkl_data` attribute
- Replaced `**2` with `torch.pow(x, 2)` for tensor operations
- Added `isinstance` checks for tensor vs float handling for:
  - `phi_angles` 
  - `config.mosaic_spread_deg`
  - `torch.deg2rad` conversion

### detector.py
- Added type annotations for `beam_center_s` and `beam_center_f` attributes
- Wrapped tensor operations in `torch.tensor()` for non-tensor inputs
- Fixed return type by wrapping result in `bool()` for `_is_default_config`
- Added type annotation `Optional[torch.Tensor]` for `_pixel_coords_cache`

### simulator.py
- Used `Optional[CrystalConfig]` and `Optional[BeamConfig]` for config parameters
- Replaced `**2` operations with multiplication (`x * x`) for tensor compatibility

## Verification
All errors have been resolved as confirmed by:
```bash
pyrefly check src/
# Output: INFO 0 errors
```

## Note
The changes were not staged because all modified files had pre-existing changes from the current feature branch work.