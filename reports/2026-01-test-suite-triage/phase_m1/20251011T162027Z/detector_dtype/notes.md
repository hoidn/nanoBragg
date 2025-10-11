# Phase M1b: Detector dtype conversion fix (Cluster C3)

## Problem Statement
Tests failing with `AttributeError: 'float' object has no attribute 'to'` when Detector's `to()` method is called.

## Root Cause
The `Detector.to()` method (lines 238-240) was unconditionally calling `.to()` on `beam_center_s` and `beam_center_f` attributes, assuming they were always tensors. However, these could be floats when `detector.beam_center_s = 128.5` was called directly (as in the test).

## Solution
Updated `Detector.to()` method (src/nanobrag_torch/models/detector.py lines 238-255) to handle both tensor and scalar cases, mirroring the defensive pattern used in `__init__` (lines 109-125):

```python
# Move beam center tensors (handle both tensor and scalar cases)
if isinstance(self.beam_center_s, torch.Tensor):
    self.beam_center_s = self.beam_center_s.to(device=self.device, dtype=self.dtype)
else:
    self.beam_center_s = torch.tensor(
        self.beam_center_s,
        device=self.device,
        dtype=self.dtype,
    )

if isinstance(self.beam_center_f, torch.Tensor):
    self.beam_center_f = self.beam_center_f.to(device=self.device, dtype=self.dtype)
else:
    self.beam_center_f = torch.tensor(
        self.beam_center_f,
        device=self.device,
        dtype=self.dtype,
    )
```

## Validation
### Baseline (before fix)
```
tests/test_suite.py::TestTier1TranslationCorrectness::test_sensitivity_to_cell_params FAILED
AttributeError: 'float' object has no attribute 'to'
```

### After fix
```
tests/test_suite.py::TestTier1TranslationCorrectness::test_sensitivity_to_cell_params PASSED [100%]
Runtime: 9.62s
```

## Evidence Types
- `type(detector.beam_center_s)` before `.to()`: `<class 'float'>`
- `type(detector.beam_center_s)` after `.to()`: `<class 'torch.Tensor'>`

## Impact
This fix ensures device/dtype neutrality per `docs/development/testing_strategy.md` §1.4, allowing tests to move detectors between devices without runtime type errors.

## Files Modified
- `src/nanobrag_torch/models/detector.py` (lines 238-255)

## Cluster C3 Status
✅ RESOLVED - Single failure from `test_sensitivity_to_cell_params` now passes
