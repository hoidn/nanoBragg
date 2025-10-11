# Phase M1d — Simulator API Alignment (Cluster C5)

**Date:** 2025-10-11
**Attempt:** #26
**Task:** Update CUDA graphs fixtures to use positional Simulator API

## Context

The `test_perf_pytorch_005_cudagraphs.py` test module was failing because it used deprecated keyword arguments (`crystal_config=`, `detector_config=`) when instantiating the `Simulator` class. The current API requires:

1. Create `Crystal` and `Detector` objects from configurations
2. Pass them positionally to `Simulator(crystal, detector, crystal_config, beam_config)`

## Changes Made

Updated all test methods in `test_perf_pytorch_005_cudagraphs.py`:
- Added imports: `Crystal` from `nanobrag_torch.models.crystal`, `Detector` from `nanobrag_torch.models.detector`
- Modified `test_basic_execution`: Creates Crystal/Detector objects before Simulator
- Modified `test_cuda_multiple_runs`: Creates Crystal/Detector objects before Simulator
- Modified `test_gradient_flow_preserved`: Creates Crystal/Detector objects before Simulator
- Modified `test_cpu_cuda_correlation`: Creates separate Crystal/Detector pairs for CPU and CUDA

## Test Results

### Before Fix
```
tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_basic_execution[cpu] FAILED
```
Error: `TypeError: Simulator.__init__() got an unexpected keyword argument 'detector_config'`

### After Fix
```
3 passed, 3 skipped in 10.40s
```

All tests pass on CPU. CUDA tests skipped (no CUDA device available).

## Rationale

The Simulator API evolved to accept `Crystal` and `Detector` objects directly rather than configurations. This allows:
- Better separation of concerns (configuration vs model)
- More explicit instantiation patterns
- Easier device/dtype management

The keyword argument pattern was deprecated in favor of positional arguments matching the current architecture in `src/nanobrag_torch/simulator.py:429-438`.

## Artifacts

- Before: `reports/2026-01-test-suite-triage/phase_m1/20251011T165255Z/simulator_api/pytest_before.log`
- After: `reports/2026-01-test-suite-triage/phase_m1/20251011T165255Z/simulator_api/pytest_module.log`
- Environment: `reports/2026-01-test-suite-triage/phase_m1/20251011T165255Z/simulator_api/env.txt`
- Updated file: `tests/test_perf_pytorch_005_cudagraphs.py`

## References

- Triage summary: `reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md:157-182`
- Simulator source: `src/nanobrag_torch/simulator.py:429-438`
- Reference pattern: `tests/test_at_parallel_017.py:77-79`
- Plan task: `plans/active/test-suite-triage.md:212` (M1d)
