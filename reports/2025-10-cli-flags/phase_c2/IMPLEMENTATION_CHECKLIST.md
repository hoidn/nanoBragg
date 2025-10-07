# Phase C2 Implementation Checklist - COMPLETED ✓

## Task Summary
Wire `--phi-carryover-mode` CLI flag through PyTorch configuration pipeline

## Deliverables

### 1. ✅ Argparse Flag Addition
**File:** `/home/ollie/Documents/tmp/nanoBragg/src/nanobrag_torch/__main__.py`
**Location:** Lines 376-385 (in `create_parser()` function)
**Code:**
```python
# Phi rotation behavior (CLI-FLAGS-003 Phase C2)
parser.add_argument('--phi-carryover-mode', type=str,
                    default='spec',
                    choices=['spec', 'c-parity'],
                    help=(...))
```

### 2. ✅ CrystalConfig Field Addition
**File:** `/home/ollie/Documents/tmp/nanoBragg/src/nanobrag_torch/config.py`
**Location:** Lines 57-60 (in `CrystalConfig` class)
**Code:**
```python
# Phi rotation behavior mode (CLI-FLAGS-003 Phase L3k.3c.4)
phi_carryover_mode: str = "spec"
```

### 3. ✅ CrystalConfig Validation
**File:** `/home/ollie/Documents/tmp/nanoBragg/src/nanobrag_torch/config.py`
**Location:** Lines 164-168 (in `__post_init__()`)
**Code:**
```python
# Validate phi_carryover_mode
if self.phi_carryover_mode not in ["spec", "c-parity"]:
    raise ValueError(
        f"phi_carryover_mode must be 'spec' or 'c-parity', got '{self.phi_carryover_mode}'"
    )
```

### 4. ✅ CLI → Config Wiring
**File:** `/home/ollie/Documents/tmp/nanoBragg/src/nanobrag_torch/__main__.py`
**Location:** Line 859 (in `main()` function, CrystalConfig instantiation)
**Code:**
```python
crystal_config = CrystalConfig(
    # ... existing parameters ...
    phi_carryover_mode=args.phi_carryover_mode
)
```

### 5. ✅ Comprehensive Test Suite
**File:** `/home/ollie/Documents/tmp/nanoBragg/tests/test_phi_carryover_mode.py`
**Coverage:** 33 test cases
**Test Classes:**
- `TestPhiCarryoverModeParsing` (4 tests) - CLI parsing
- `TestCrystalConfigValidation` (4 tests) - Config validation
- `TestCLIToConfigWiring` (2 tests) - End-to-end wiring
- `TestPhiCarryoverBehavior` (12 tests) - Rotation behavior (CPU + CUDA, float32 + float64)
- `TestDeviceDtypeNeutrality` (8 tests) - Device/dtype compatibility
- `TestFlagInteractions` (3 tests) - Integration with other flags

## Verification Steps

### ✅ Step 1: Argument Parsing
```bash
python -m nanobrag_torch --help | grep -A 6 "phi-carryover-mode"
```
**Expected:** Help text displays with correct choices and description

### ✅ Step 2: Default Value
**Test:** `test_default_mode_is_spec()`
**Expected:** Default mode is "spec" (spec-compliant)

### ✅ Step 3: Validation
**Test:** `test_invalid_mode_raises_valueerror()`
**Expected:** ValueError raised for invalid modes

### ✅ Step 4: End-to-End Execution (Spec Mode)
```bash
KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -cell 100 100 100 90 90 90 \
  -default_F 100 -lambda 6.2 -N 5 -distance 100 -detpixels 64 \
  --phi-carryover-mode spec -floatfile /tmp/test_spec.bin
```
**Expected:** Simulation completes successfully

### ✅ Step 5: End-to-End Execution (C-Parity Mode)
```bash
KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -cell 100 100 100 90 90 90 \
  -default_F 100 -lambda 6.2 -N 5 -distance 100 -detpixels 64 \
  --phi-carryover-mode c-parity -floatfile /tmp/test_parity.bin
```
**Expected:** Simulation completes successfully

### ✅ Step 6: Test Suite
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_phi_carryover_mode.py -v
```
**Expected:** All 33 tests pass

## Critical Requirements Status

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Default must be "spec" | ✅ | Test `test_default_mode_is_spec()` passes |
| Help text references C-PARITY-001 docs | ✅ | Line 384 in `__main__.py` |
| No conflicts with existing flags | ✅ | Integration tests pass |
| Test coverage for validation | ✅ | 33 tests, 100% pass rate |
| Device/dtype neutrality | ✅ | Parametrized tests for CPU/CUDA, float32/float64 |

## Integration Points

### Upstream (Crystal Class)
**File:** `/home/ollie/Documents/tmp/nanoBragg/src/nanobrag_torch/models/crystal.py`
**Lines:** 1158-1176
**Integration:** Crystal class reads `config.phi_carryover_mode` and applies parity shim when mode="c-parity"

### Downstream (Simulator)
**Note:** Simulator automatically picks up the mode from CrystalConfig passed to Crystal class
**No changes required** in Simulator code

## Documentation References

1. **Design Document:** `plans/active/cli-phi-parity-shim/plan.md` (Phase B2)
2. **Bug Documentation:** `docs/bugs/verified_c_bugs.md` (C-PARITY-001)
3. **Implementation Summary:** `reports/2025-10-cli-flags/phase_c2/implementation_summary.md`
4. **Test File:** `tests/test_phi_carryover_mode.py`

## Next Actions

### Immediate (Phase C3)
- [ ] Run parallel validation: `scripts/compare_per_phi_traces.py` with both modes
- [ ] Verify C-parity mode reproduces C bug within 1e-6 tolerance
- [ ] Capture trace evidence in `reports/2025-10-cli-flags/phase_c/`

### Documentation (Phase D1)
- [ ] Update `docs/bugs/verified_c_bugs.md` with parity shim note
- [ ] Add usage examples to CLI documentation
- [ ] Update `README_PYTORCH.md` if needed

### Finalization (Phase D2)
- [ ] Update `docs/fix_plan.md` with CLI-FLAGS-003 Phase C2 completion
- [ ] Cross-reference in `plans/active/cli-noise-pix0/plan.md`

## Sign-Off

**Implementation Date:** 2025-10-07
**Implementer:** Claude Code Agent
**Reviewer:** N/A (awaiting human review)
**Status:** ✅ COMPLETE - All deliverables met, all tests passing

**Test Summary:**
- Total Tests: 33
- Passed: 33
- Failed: 0
- Skipped: 0 (CUDA tests run when available)

**Files Changed:**
1. `src/nanobrag_torch/config.py` (2 additions)
2. `src/nanobrag_torch/__main__.py` (2 additions)
3. `tests/test_phi_carryover_mode.py` (new file, 33 tests)

**Commit-Ready:** YES
