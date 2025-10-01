# DTYPE-DEFAULT-001 Float64 Usage Inventory

**Date:** 2025-09-30
**Phase:** A1 - Cataloguing float64 defaults
**Status:** Complete

## Summary

Total float64 occurrences across codebase: **37 instances** in **10 files**

### Distribution by File
1. `__main__.py`: 12 occurrences
2. `utils/auto_selection.py`: 7 occurrences
3. `io/source.py`: 6 occurrences
4. `io/hkl.py`: 5 occurrences
5. `simulator.py`: 2 occurrences
6. Other files (1 each): `models/crystal.py`, `models/detector.py`, `utils/c_random.py`, `utils/noise.py`, `utils/runtime_cache.py`

## Detailed Inventory

### 1. Core Defaults (MUST CHANGE)

#### `__main__.py`
- **Line 365**: CLI argument default: `default='float64'`
  - **Impact**: PRIMARY default for all CLI runs
  - **Action**: Change to `'float32'`

- **Line 1052**: dtype resolution: `dtype = torch.float32 if args.dtype == 'float32' else torch.float64`
  - **Impact**: Maps CLI arg to torch dtype
  - **Action**: Will inherit from CLI default change

#### `models/crystal.py`
- **Line 41**: Constructor default: `dtype=torch.float64`
  - **Impact**: Crystal model default precision
  - **Action**: Change to `dtype=torch.float32`

#### `models/detector.py`
- **Line 39**: Constructor default: `dtype=torch.float64`
  - **Impact**: Detector model default precision
  - **Action**: Change to `dtype=torch.float32`

#### `simulator.py`
- **Line 319**: Constructor default: `dtype=torch.float64`
  - **Impact**: Simulator default precision
  - **Action**: Change to `dtype=torch.float32`

- **Line 411**: Comment about dtype upcasting
  - **Impact**: Documentation only
  - **Action**: Review comment for continued relevance

### 2. Hard-coded Tensor Creation (SHOULD MAKE DTYPE-AWARE)

#### `__main__.py`
- **Lines 927, 929**: Beam direction tensors: `torch.tensor([...], dtype=torch.float64)`
  - **Impact**: Fixed dtype regardless of user choice
  - **Action**: Use resolved dtype variable instead

- **Lines 967-971**: Beam/polarization direction tensors (4 occurrences)
  - **Impact**: Fixed dtype regardless of user choice
  - **Action**: Use resolved dtype variable instead

- **Lines 1035, 1037**: HKL data tensors: `dtype=torch.float64`
  - **Impact**: Structure factor data precision
  - **Action**: Use resolved dtype variable instead

#### `utils/auto_selection.py`
- **Lines 256, 258**: Default beam/polarization: `dtype=torch.float64` (2 occurrences)
  - **Impact**: Auto-selection fallbacks
  - **Action**: Accept dtype parameter, default to float32

- **Lines 350-352, 355-356**: Source directions/weights/wavelengths (5 occurrences)
  - **Impact**: Source sampling tensors
  - **Action**: Accept dtype parameter, default to float32

#### `io/source.py`
- **Lines 46, 69, 73, 77**: Position/direction tensors (4 occurrences)
  - **Impact**: Source file parsing
  - **Action**: Accept dtype parameter from caller

- **Lines 111-112**: Weights/wavelengths arrays (2 occurrences)
  - **Impact**: Source data tensors
  - **Action**: Accept dtype parameter from caller

### 3. I/O and External Data (CONTEXT-DEPENDENT)

#### `io/hkl.py`
- **Line 19**: `read_hkl` function default: `dtype=torch.float64`
  - **Impact**: HKL file reading precision
  - **Action**: Change default to `float32`, allow override

- **Line 149**: NumPy export: `astype(np.float64)`
  - **Impact**: Fdump binary format (external contract)
  - **Action**: **KEEP** - binary format requires double precision

- **Line 156**: `read_fdump` function default: `dtype=torch.float64`
  - **Impact**: Reading Fdump binaries
  - **Action**: **KEEP** - must match binary format

- **Line 186**: NumPy read: `dtype=np.float64`
  - **Impact**: Reading Fdump binaries
  - **Action**: **KEEP** - binary format constraint

- **Line 215**: `write_hkl_text` default: `dtype=torch.float64`
  - **Impact**: Text file output precision
  - **Action**: Accept caller dtype, default to float32

### 4. Utilities and Edge Cases

#### `utils/noise.py`
- **Line 161**: Noise buffer: `dtype=torch.float64`
  - **Impact**: Poisson sampling precision
  - **Action**: Make dtype-aware via parameter

#### `utils/c_random.py`
- **Line 218**: Random matrix: `dtype=torch.float64`
  - **Impact**: C-compatible RNG output
  - **Action**: Make dtype-aware via parameter

#### `utils/runtime_cache.py`
- **Line 52**: Documentation comment only
  - **Impact**: None
  - **Action**: Update docs to mention float32 default

## Gradient-Critical Paths (Phase A3 Analysis)

### Must Support Float64 for Gradcheck

1. **Test suite gradient checks**: `tests/test_crystal_geometry.py`, `tests/test_gradients.py`
   - These tests explicitly pass `dtype=torch.float64` for numerical precision
   - **Action**: Ensure these tests continue to pass explicit dtype

2. **Crystal cell tensor computation**: `models/crystal.py:compute_cell_tensors()`
   - Used in gradient tests for metric duality
   - **Action**: Must accept dtype parameter for test overrides

3. **Detector geometry**: `models/detector.py` gradient tests
   - **Action**: Must accept dtype parameter for test overrides

### Can Use Float32

1. **Production simulation runs**: No gradient requirements
2. **Image generation**: No backward pass needed
3. **I/O operations**: Match output precision requirements

## Proposed Implementation Strategy

### Phase B Changes (in order)

1. **B1: Update core defaults**
   - Change CLI default: `__main__.py:365`
   - Change model defaults: `Crystal.__init__`, `Detector.__init__`, `Simulator.__init__`

2. **B2: Make constants dtype-aware**
   - Propagate dtype through `__main__.py` tensor creation
   - Add dtype parameters to `auto_selection.py` functions
   - Update `io/source.py` to accept dtype

3. **B3: Audit utilities**
   - Add dtype parameters to `noise.py`, `c_random.py`, `hkl.py` where appropriate
   - Preserve float64 for Fdump binary I/O (external contract)

### Exceptions (DO NOT CHANGE)

1. **Fdump binary format**: Lines 149, 156, 186 in `io/hkl.py`
   - **Rationale**: External binary format contract requires double precision

2. **Test overrides**: Any test explicitly requesting `dtype=torch.float64`
   - **Rationale**: Gradient checks need higher precision

## Documentation Updates Required (Phase A2)

### Files to Update

1. **`arch.md`**
   - Current: "dtype: float64 tensors for numerical stability"
   - Proposed: "dtype: float32 tensors by default for performance; float64 available via explicit override for gradient checks"

2. **`docs/development/pytorch_runtime_checklist.md`**
   - Add note about float32 default
   - Document float64 opt-in for gradcheck

3. **`docs/architecture/pytorch_design.md`**
   - Update Section 2.4 memory management discussion
   - Note performance benefits of float32 default

4. **`README_PYTORCH.md`** (if exists)
   - Document CLI `-dtype` flag behavior
   - Note default precision change

## Risk Assessment

### Low Risk
- Performance improvements expected (~2× memory reduction, ~1.5× speedup)
- Existing dtype parameter plumbing in place
- Tests can explicitly request float64

### Medium Risk
- Small numerical differences in output images
  - **Mitigation**: Run AT-PARALLEL suite to verify correlation > 0.9999
- Potential documentation drift
  - **Mitigation**: Comprehensive doc updates in Phase D

### High Risk
- Breaking external dependencies expecting float64
  - **Mitigation**: Preserve Fdump binary format at float64
  - **Mitigation**: CLI flag allows opt-in to float64

## Phase A Exit Criteria Checklist

- [x] Float64 usage catalogued (37 instances, 10 files)
- [x] Gradient-critical paths identified (gradcheck tests, cell tensors)
- [x] Proposed documentation changes drafted
- [x] Implementation strategy defined
- [x] Risk assessment complete

**Ready for Phase B implementation.**
