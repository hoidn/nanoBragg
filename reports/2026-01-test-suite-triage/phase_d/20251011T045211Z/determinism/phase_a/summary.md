# Phase A Reproduction Summary — DETERMINISM-001
- Timestamp: 20251011T045211Z
- Focus: Reproduce AT-PARALLEL-013/024 determinism regressions per plans/active/determinism.md Phase A.

## Artifacts
- collect_only.log — `logs/collect_only.log`
- Environment snapshot — `env.json`
- AT-PARALLEL-013 log — `at_parallel_013/pytest.log`
- AT-PARALLEL-024 log — `at_parallel_024/pytest.log`

## Results Overview
| Test Selector | Outcome | Key Failure Signal |
| --- | --- | --- |
| `tests/test_at_parallel_013.py` | **Failed** (4/6 tests) | `torch._dynamo` attempts to query CUDA device properties even after deterministic CPU configuration, raising `IndexError: list index out of range` from `torch/_dynamo/device_interface.py:218` when `torch.cuda.device_count()==0`. Prevents PyTorch determinism checks from running. |
| `tests/test_at_parallel_024.py` | **Failed** (1/6 tests) | `mosaic_rotation_umat` returns `float32` tensors, so unitary check comparing against `float64` identity raises `RuntimeError: Float did not match Double`. Deterministic image checks pass; failure isolated to helper dtype. |

## Notes
- Collect-only run confirms suite inventory (692 collected tests) with current environment (Python 3.13.5, torch 2.7.1+cu126).
- AT-PARALLEL-013 failures block Phase B callchain work until we decide whether to disable `torch._dynamo`/`torch.compile` for deterministic runs or to ensure Triton probing handles zero CUDA devices when `CUDA_VISIBLE_DEVICES=''`.
- AT-PARALLEL-024 regression is localized to `nanobrag_torch/utils/c_random.mosaic_rotation_umat`; we need to audit dtype/device propagation before proceeding to callchain tracing.
