# Phase A Summary — [DTYPE-NEUTRAL-001]

**Timestamp:** ${STAMP}
**Artifact Root:** reports/2026-01-test-suite-triage/phase_d/${STAMP}/dtype-neutral/phase_a/

## Commands Executed
- `KMP_DUPLICATE_LIB_OK=TRUE AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md pytest --collect-only -q`
- `KMP_DUPLICATE_LIB_OK=TRUE AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md pytest -v tests/test_at_parallel_013.py --maxfail=0 --durations=10`
- `KMP_DUPLICATE_LIB_OK=TRUE AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md pytest -v tests/test_at_parallel_024.py --maxfail=0 --durations=10`
- Inline minimal reproducer (see `minimal_repro.log`)

## Environment Snapshot
See `env.json` for Python/PyTorch versions (Python 3.13.5, torch 2.7.1+cu126, CUDA available= True, default dtype float32).

## Failure Signatures

### AT-PARALLEL-013 (`pytest -v tests/test_at_parallel_013.py`)
- Failures: `test_pytorch_determinism_same_seed`, `test_pytorch_determinism_different_seeds`, `test_pytorch_consistency_across_runs`, `test_numerical_precision_float64`
- Common error (first three failures): `RuntimeError: Float did not match Double` raised by `torch.allclose(self.fdet_vec, cached_f, atol=1e-15)` in `src/nanobrag_torch/models/detector.py:767`.
- The class-level deterministic setup forces `torch.set_default_dtype(torch.float64)`; the simulator instantiates the detector with `dtype=torch.float64` but immediately calls `Detector.to(dtype=torch.float32)` when the simulator's default dtype (torch.float32) is applied.
- `test_numerical_precision_float64` subsequently fails inside `torch.compile` (same stack as Attempt #1) once the dtype mismatch is bypassed; root cause captured for Phase C follow-up.

### AT-PARALLEL-024 (`pytest -v tests/test_at_parallel_024.py`)
- Failures: `test_pytorch_determinism`, `test_seed_independence`, `test_mosaic_rotation_umat_determinism`
- Identical dtype mismatch in `Detector.get_pixel_coords()` prevents simulator construction; `mosaic_rotation_umat` additionally fails because cached tensors feeding the rotation helper still hold float32 values in spite of float64 expectations.

## Minimal Reproducer
`minimal_repro.log` captures the smallest script that reproduces the cache mismatch:
1. Instantiate `Detector(config, dtype=torch.float64)`.
2. Call `detector.to(dtype=torch.float32)` — matches `Simulator.__init__` behaviour when the simulator default dtype is float32.
3. Invoke `detector.get_pixel_coords()` → `RuntimeError: Float did not match Double` because `_cached_basis_vectors` were cloned in float64 and never re-cast during `.to()`/`invalidate_cache()`.

## Comparison with Prior Evidence
- Confirms findings from `reports/2026-01-test-suite-triage/phase_d/20251010T171010Z/determinism/phase_a/summary.md` (Attempt #1). The new minimal repro isolates cache invalidation as the direct trigger and narrows the fix scope to `Detector.to()` / `Detector.invalidate_cache()` plus `_cached_basis_vectors` management.
- Additional Dynamo failure (numerical_precision test) persists; flag for Phase C remediation scope.

## Next Steps
1. Proceed to Phase B analysis per `plans/active/dtype-neutral.md` (static audit of detector caches, inventory of tensor factories, broader survey).
2. Update fix_plan attempts ledger with this evidence (Attempt #1 for `[DTYPE-NEUTRAL-001]`).
3. Coordinate with `[DETERMINISM-001]` plan once dtype neutrality remediation unblocks determinism selectors.

