# Plan: AT-PARALLEL-024 Random Misset Parity Debug

**Status:** Archived 2025-09-30 (completed; parity restored)
**Priority:** Critical parity blocker
**Related fix_plan item:** `[AT-PARALLEL-024-PARITY]` (docs/fix_plan.md)
**Created:** 2025-09-30 (updated 2025-09-30 by galph)

## Why this plan exists
- Parity harness for AT-PARALLEL-024 (`tests/parity_cases.yaml`, runs `random-misset-seed-{12345,54321}`) shows catastrophic divergence: correlation ≈ 0.01 and sum ratio ≈ 1.06/1.13 (`reports/2025-09-30-AT-PARALLEL-024/*.json`).
- Spec (`specs/spec-a-parallel.md`, AT-PARALLEL-024) requires C/PyTorch to produce identical diffraction patterns for the same random misset seed. Determinism + parity both fail.
- Root-cause hypothesis confirmed during supervisor analysis: PyTorch random misset generator clamps the rotation cap to π/2 radians (`src/nanobrag_torch/models/crystal.py:595`), whereas `nanoBragg.c` calls `mosaic_rotation_umat(90.0, …)` (`golden_suite_generator/nanoBragg.c:2010-2022`). Because the C code treats the argument as **degrees but feeds it directly into trig functions**, the effective rotation cap is 90 **radians**, yielding a near-uniform orientation distribution. PyTorch’s π/2 cap limits rotations to ±90° and produces a very different pattern.
- Fixing this is prerequisite for downstream acceptance tests that rely on random orientation equivalence and for validating stochastic sampling against the reference implementation.

## Objectives
1. Reproduce and document the divergence (baseline metrics already collected; confirm quickly to ensure environment parity).
2. Validate RNG parity: confirm the PyTorch CLCG (`src/nanobrag_torch/utils/c_random.py`) matches `ran1()` outputs in `nanoBragg.c` for shared seeds.
3. Correct the misset rotation sampling so PyTorch generates the same orientation distribution as C (restore the full 90-radian cap semantics while maintaining determinism and differentiability constraints).
4. Verify that both parity runs meet thresholds (corr ≥ 0.99, sum_ratio within [0.98, 1.02], max|Δ| < 500) and that repeated PyTorch runs with the same seed are deterministic.
5. Update documentation (`docs/fix_plan.md` Attempts History) with findings, diversion point, fix summary, and post-fix metrics. Archive artifacts under `reports/<date>-AT-PARALLEL-024/`.

## Mandatory context before coding
- `specs/spec-a-parallel.md` — AT-PARALLEL-024 acceptance criteria.
- `docs/architecture/pytorch_design.md` — rotation pipeline expectations.
- `docs/development/c_to_pytorch_config_map.md` — mapping for `-misset` / misset seeds.
- `docs/debugging/detector_geometry_checklist.md` — re-read for unit sanity (even though detector stays default).
- `src/nanobrag_torch/models/crystal.py` — random misset block (`compute_cell_tensors`, `_apply_static_orientation`).
- `src/nanobrag_torch/utils/c_random.py` — `CLCG`, `mosaic_rotation_umat`, `umat2misset`.
- `golden_suite_generator/nanoBragg.c` (lines ~2009-2036, 3707-3755) — authoritative C behavior for random misset.

## Reproduction checklist
1. Set environment variables per project policy: `export NB_C_BIN=./golden_suite_generator/nanoBragg` (if not already), `export NB_RUN_PARALLEL=1`, and prefix commands with `KMP_DUPLICATE_LIB_OK=TRUE`.
2. Run failing parity cases:
   ```bash
   KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 \
   NB_C_BIN=$NB_C_BIN pytest tests/test_parity_matrix.py -k "AT-PARALLEL-024" -v
   ```
   Confirm correlation ≈ 0.01 to ensure the failure still reproduces.
3. (Optional) Capture misset angles printed by C by running the minimal C command (e.g., `./golden_suite_generator/nanoBragg -cell 100 100 100 90 90 90 -default_F 100 -lambda 1.0 -N 5 -detpixels 8 -pixel 0.1 -distance 100 -mosflm -misset random -misset_seed 12345 -floatfile /tmp/at024.bin`) and grepping for `random orientation misset angles`.

## Investigation phases

### Phase A — RNG parity spot check (no code changes)
- Use `scripts/benchmarks` or a small Python snippet to compare the first several outputs of `CLCG.ran1()` against the C implementation: compile a tiny C harness if necessary (or instrument existing binary) to print `ran1()` outputs for seed 12345.
- Confirm `mosaic_rotation_umat` with identical numeric inputs (angle cap, seed) produces the same rotation matrix as C. If C instrumentation is noisy, reuse the pure-Python port to back-compute expected Euler angles from `nanoBragg.c` (the math matches when the same cap is used).

### Phase B — Diagnose the misset angle discrepancy
- In PyTorch, log the angles currently produced:
  ```python
  from nanobrag_torch.utils.c_random import mosaic_rotation_umat, umat2misset
  import math
  for seed in (12345, 54321):
      print('π/2 cap', seed, [deg for deg in ...])
  ```
- Compare with `nanoBragg.c` output for the same seeds (should roughly match when PyTorch uses `90.0`). Document the deltas in `docs/fix_plan.md` Attempts History.
- Verify that PyTorch currently limits |angle| ≤ 90°, which explains the low correlation (C’s angles often exceed ±90° due to effectively treating 90 as radians).

### Phase C — Implement the fix
- Update `compute_cell_tensors` in `src/nanobrag_torch/models/crystal.py` so the random misset cap matches C. Likely minimal change: replace `math.pi/2.0` with `90.0` (and document the intentionally “incorrect” unit to mirror C). Add concise comment referencing `nanoBragg.c:2013`.
- Ensure we preserve CLCG determinism and do not introduce `.item()` on differentiable tensors.
- Consider exposing a helper constant (e.g., `MISSET_RANDOM_MAX = 90.0`) for clarity.
- If needed, update `umat2misset` or downstream recalculation to accommodate large rotations (no change expected, but confirm shapes/dtypes remain correct).

### Phase D — Validation
1. Rerun AT-PARALLEL-024 parity cases (both seeds). Ensure metrics meet thresholds and note exact numbers.
2. Repeat PyTorch-only run twice with the same seed to confirm determinism (correlation 1.0 across runs, identical `np.allclose`).
3. Spot-check that other parity cases (e.g., AT-PARALLEL-021, AT-PARALLEL-022) remain passing to guard against unintended regressions.
4. Capture updated misset angles (PyTorch vs C) in the report for transparency.

### Phase E — Documentation & follow-up
- Update `docs/fix_plan.md` `[AT-PARALLEL-024-PARITY]` section with attempt history: baseline metrics, first divergence (angle cap), change summary, post-fix metrics, and artifact paths.
- Add any newly generated scripts or helper snippets under `scripts/debug/` if they aid future misset investigations.
- Once parity passes, leave a supervisor note to archive this plan (move to `plans/history/`) in the next galph loop.

## Exit criteria
- Both parity runs for seeds 12345 and 54321 pass with corr ≥ 0.99 and sum_ratio within ±2%.
- PyTorch misset angles/logs match the C outputs within numerical tolerance when using identical seeds.
- Determinism confirmed for repeated PyTorch runs with fixed seed.
- `docs/fix_plan.md` updated with attempt summary and marked `Status: done`.
- No regressions introduced in previously passing parity/acceptance cases.

## Artifact expectations
- Updated parity metrics under `reports/<date>-AT-PARALLEL-024/` (include new timestamp).
- Optional: short text file summarizing misset angle comparisons for quick reference.
