# Phase M2 Chunk 03 Test Execution Summary

**Timestamp:** 20251011T193829Z
**Working Directory:** /home/ollie/Documents/tmp/nanoBragg
**Output Directory:** reports/2026-01-test-suite-triage/phase_m/20251011T193829Z/chunks/chunk_03/

---

## Execution Results

**Exit Code:** 1 (failures present)

**Test Counts:**
- **Passed:** 42
- **Failed:** 10
- **Skipped:** 10
- **XFailed:** 1 (expected failure)
- **Total:** 63 tests collected (62 run, 1 skipped during collection)

**Runtime:** 102.76 seconds (1 minute 42 seconds)

---

## Test Files Executed

1. `tests/test_at_cli_001.py` - CLI interface tests
2. `tests/test_at_flu_001.py` - Fluence calculation tests
3. `tests/test_at_io_004.py` - I/O format tests
4. `tests/test_at_parallel_009.py` - Parallel validation tests (SKIPPED - not in chunk)
5. `tests/test_at_parallel_020.py` - Comprehensive parallel tests (SKIPPED)
6. `tests/test_at_perf_001.py` - Performance tests
7. `tests/test_at_pre_002.py` - Preprocessor pivot mode tests
8. `tests/test_at_sta_001.py` - Statistics tests
9. `tests/test_configuration_consistency.py` - Configuration tests
10. `tests/test_gradients.py` - Gradient tests
11. `tests/test_show_config.py` - Configuration display tests

---

## Failed Tests (10)

All failures are in `tests/test_gradients.py` and are caused by the same root issue:

### Root Cause: PyTorch Compiled Function Donated Buffer Conflict

**Error Message:**
```
RuntimeError: This backward function was compiled with non-empty donated buffers
which requires create_graph=False and retain_graph=False. Please keep
backward(create_graph=False, retain_graph=False) across all backward() function
calls, or set torch._functorch.config.donated_buffer=False to disable donated buffer.
```

### Affected Tests:

1. `TestCellParameterGradients::test_gradcheck_cell_a`
2. `TestCellParameterGradients::test_gradcheck_cell_b`
3. `TestCellParameterGradients::test_gradcheck_cell_c`
4. `TestCellParameterGradients::test_gradcheck_cell_alpha`
5. `TestCellParameterGradients::test_gradcheck_cell_beta`
6. `TestCellParameterGradients::test_gradcheck_cell_gamma`
7. `TestAdvancedGradients::test_joint_gradcheck`
8. `TestAdvancedGradients::test_gradgradcheck_cell_params`
9. `TestAdvancedGradients::test_gradient_flow_simulation`
10. `TestPropertyBasedGradients::test_property_gradient_stability`

### Technical Details:

The issue occurs during `torch.autograd.gradcheck()` when it attempts to compute analytical gradients using VJP (vector-Jacobian product). The backward pass fails because:

1. The compiled backward function has "donated buffers" enabled
2. `gradcheck()` requires `create_graph=True` and `retain_graph=True` for second-order gradient computation
3. These settings are incompatible with donated buffers in PyTorch's functorch AOT autograd

**Suggested Fix:** Set `torch._functorch.config.donated_buffer = False` before running gradient tests.

---

## Passed Tests (42)

All functional tests passed successfully:

### CLI Tests (6/6 passed)
- Help flags (-h, --help)
- CLI invocability
- Help content verification (examples, wavelength synonyms, output synonyms)

### Fluence Tests (8/8 passed)
- Fluence calculations from flux/exposure/beamsize
- Edge cases (zero flux, zero exposure, zero beamsize)
- Flux recomputation
- Sample clipping warnings and behavior

### I/O Tests (7/7 passed)
- HKL file format parsing (4-column, 5-column, 6-column)
- Negative Miller indices
- Format equivalence
- FDUMP caching
- Comment/blank line handling

### Performance Tests (2/3 passed, 1 skipped)
- Vectorization scaling
- Memory scaling
- (Skipped: C performance parity test)

### Preprocessor Tests (6/6 passed)
- Pivot mode inference from xbeam/ybeam
- Pivot mode inference from xclose/yclose/orgx/orgy
- Explicit pivot overrides
- Distance vs close_distance defaults
- Convention-specific pivot defaults

### Statistics Tests (5/5 passed)
- Basic statistics computation
- ROI statistics
- Mask-based statistics
- Empty ROI handling
- Max location tracking

### Configuration Tests (1/6 passed, 4 skipped, 1 xfailed)
- (XFailed: Explicit defaults equal implicit - known issue)
- (Skipped: 4 tests - configuration echo, mode detection, trigger tracking)
- Show config basic functionality passed

### Property-Based Gradient Tests (2/4 passed)
- Metric duality property
- Volume consistency property
- (Failed: Gradient stability - donated buffer issue)

### Optimization Recovery Tests (2/2 passed)
- Cell parameter optimization recovery
- Multiple optimization scenarios

### Show Config Tests (4/4 passed)
- Basic configuration display
- Configuration with divergence
- Configuration with rotations
- Echo config alias

---

## Skipped Tests (10)

### test_at_parallel_020.py (4 skipped)
- `test_comprehensive_integration` - Full integration test
- `test_comprehensive_without_absorption` - Integration without absorption
- `test_phi_rotation_only` - Phi rotation test
- `test_comprehensive_minimal_features` - Minimal features test

**Reason:** These tests require golden data or are marked as slow/integration tests.

### test_at_perf_001.py (1 skipped)
- `test_performance_parity_with_c` - C performance comparison

**Reason:** Requires C binary comparison setup.

### test_configuration_consistency.py (5 skipped)
- `test_configuration_echo_present` - Configuration echo verification
- `test_mode_detection_accuracy` - Mode detection testing
- `test_trigger_tracking` - Trigger tracking verification
- `test_all_vector_parameters_trigger_custom` - Vector parameter triggers

**Reason:** These tests may require additional setup or are marked as optional.

---

## XFailed Tests (1)

### test_configuration_consistency.py
- `test_explicit_defaults_equal_implicit` - Known issue with default configuration handling

**Reason:** This is an expected failure documenting a known limitation.

---

## Performance Analysis

**Total Runtime:** 102.76 seconds
- Well under the 200-second target
- Includes gradient tests which are computationally intensive

**Slowest Tests:** (--durations=25 output captured in pytest.log)
The gradient tests (`test_gradients.py`) consumed significant time before failing due to the donated buffer issue.

---

## Conclusion

**Status:** FAILED (10 gradient test failures)

**Key Issues:**
1. **Critical:** All gradient tests fail due to PyTorch functorch donated buffer configuration incompatibility with `gradcheck()`
2. **Minor:** Several tests skipped, but this appears intentional for this chunk

**Recommended Actions:**
1. Disable donated buffers for gradient tests by setting `torch._functorch.config.donated_buffer = False`
2. Update `tests/test_gradients.py` to include this configuration at module level
3. Re-run this chunk to verify gradient test correctness

**Expected Outcome After Fix:**
- Exit code: 0
- Passed: 52 (42 + 10 gradient tests)
- Failed: 0
- Skipped: 10
- XFailed: 1
- Runtime: ~120-150 seconds (with passing gradient tests)
