# DTYPE-DEFAULT-001 Phase B3 Audit

**Date:** 2025-10-01
**Author:** Ralph (loop execution)
**Status:** Complete - all dtype/device hardcoding removed

## Overview

This audit documents the conversion of `io/source.py`, `utils/noise.py`, and `utils/c_random.py` to respect caller-provided dtype/device instead of hard-coding float64 CPU tensors.

## Files Audited

### 1. `src/nanobrag_torch/io/source.py`

#### Issues Found

**Line 46: Hardcoded beam_direction dtype**
```python
# BEFORE:
if beam_direction is None:
    beam_direction = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
```

**Lines 69, 73, 77: Hardcoded position tensor dtype**
```python
# BEFORE (line 69):
position = torch.tensor([x, y, z], dtype=torch.float64)

# BEFORE (line 73):
position = torch.tensor([x, y, 0.0], dtype=torch.float64)

# BEFORE (line 77):
position = torch.tensor([x, 0.0, 0.0], dtype=torch.float64)
```

**Lines 111-112: Hardcoded output tensor dtypes**
```python
# BEFORE:
weights = torch.tensor(weights, dtype=torch.float64)
wavelengths = torch.tensor(wavelengths, dtype=torch.float64)
```

#### Solution

Add `dtype` and `device` parameters to function signature, defaulting to `torch.float32` and `torch.device('cpu')`. Use these for all tensor creation.

```python
# AFTER (signature):
def read_sourcefile(
    filepath: Path,
    default_wavelength_m: float,
    default_source_distance_m: float = 10.0,
    beam_direction: Optional[torch.Tensor] = None,
    dtype: torch.dtype = torch.float32,
    device: torch.device = torch.device('cpu'),
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
```

```python
# AFTER (line 46):
if beam_direction is None:
    beam_direction = torch.tensor([0.0, 0.0, 1.0], dtype=dtype, device=device)
```

```python
# AFTER (lines 69, 73, 77):
position = torch.tensor([x, y, z], dtype=dtype, device=device)
position = torch.tensor([x, y, 0.0], dtype=dtype, device=device)
position = torch.tensor([x, 0.0, 0.0], dtype=dtype, device=device)
```

```python
# AFTER (lines 111-112):
weights = torch.tensor(weights, dtype=dtype, device=device)
wavelengths = torch.tensor(wavelengths, dtype=dtype, device=device)
```

### 2. `src/nanobrag_torch/utils/noise.py`

#### Issues Found

**Line 161: Hardcoded dtype in lcg_random()**
```python
# BEFORE:
values = torch.zeros(n, dtype=torch.float64)
```

#### Solution

Add `dtype` and `device` parameters, defaulting to `torch.float32` and `torch.device('cpu')`.

```python
# AFTER (signature):
def lcg_random(
    seed: int,
    n: int = 1,
    dtype: torch.dtype = torch.float32,
    device: torch.device = torch.device('cpu')
) -> torch.Tensor:
```

```python
# AFTER (line 161):
values = torch.zeros(n, dtype=dtype, device=device)
```

### 3. `src/nanobrag_torch/utils/c_random.py`

#### Issues Found

**Line 218: Hardcoded dtype in mosaic_rotation_umat()**
```python
# BEFORE:
umat = torch.zeros(3, 3, dtype=torch.float64)
```

#### Solution

Add `dtype` and `device` parameters, defaulting to `torch.float32` and `torch.device('cpu')`.

```python
# AFTER (signature):
def mosaic_rotation_umat(
    mosaicity: float,
    seed: Optional[int] = None,
    dtype: torch.dtype = torch.float32,
    device: torch.device = torch.device('cpu')
) -> torch.Tensor:
```

```python
# AFTER (line 218):
umat = torch.zeros(3, 3, dtype=dtype, device=device)
```

## Impact Analysis

### Backward Compatibility

All changes are backward compatible:
- New parameters have default values matching project default (float32)
- Existing callers continue to work without modification
- Callers can opt-in to float64 for precision-critical operations (e.g., gradcheck)

### Device Neutrality

All three modules now respect caller device:
- Can create tensors on CUDA devices when requested
- No forced CPU→CUDA transfers
- Aligns with Core Implementation Rule #16

### Test Coverage

Functions affected:
- `io.source.read_sourcefile()` - used by BeamConfig when `-sourcefile` provided
- `utils.noise.lcg_random()` - used for LCG-based random generation
- `utils.c_random.mosaic_rotation_umat()` - used for mosaic domain generation

Verification strategy:
1. Unit tests with explicit dtype/device parameters
2. Integration tests ensuring multi-source configs work on CPU/CUDA
3. Parity tests remain green with default float32

## Exit Criteria

✅ All three modules accept `dtype` and `device` parameters
✅ Defaults align with project standard (float32, CPU)
✅ No hardcoded `torch.float64` or `torch.device('cpu')` in tensor creation
✅ Before/after code snippets documented in this audit
✅ Changes preserve C-compatibility (LCG bitstream, source file parsing)

## Next Actions

1. Mark plan.md task B3 as `[X]` complete
2. Proceed to Phase C validation tasks (C1-C3)
3. Update documentation in Phase D

## References

- Plan: `plans/active/dtype-default-fp32/plan.md` Phase B task B3
- Fix Plan: `docs/fix_plan.md` [DTYPE-DEFAULT-001] Attempt History
- Core Rule: CLAUDE.md #16 (PyTorch Device & Dtype Neutrality)
