Summary: Disable TorchDynamo in the determinism harness and align mosaic rotation dtype so AT-PARALLEL-013/024 can execute seed checks.
Mode: Parity
Focus: [DETERMINISM-001] PyTorch RNG determinism
Branch: main
Mapped tests: tests/test_at_parallel_013.py; tests/test_at_parallel_024.py
Artifacts: reports/2026-01-test-suite-triage/phase_d/<STAMP>/determinism/phase_a_fix/
Do Now: Update the determinism helpers to skip TorchDynamo when no CUDA device is available, standardise `mosaic_rotation_umat` dtype/device handling, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py --maxfail=0 --durations=10` and `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_024.py --maxfail=0 --durations=10`, archiving each log under the phase_a_fix stamp.
If Blocked: Capture the failing stack trace plus `python -c "import torch, json; print(json.dumps({'cuda_available': torch.cuda.is_available(), 'device_count': torch.cuda.device_count()}))"` into attempts history and stop.

Priorities & Rationale:
- plans/active/determinism.md — Phase A checklist now [D]; next gate is removing infrastructure blockers before Phase B callchain starts.
- docs/fix_plan.md (DETERMINISM-001) — Attempt #3 documents current Dynamo failure; unblocker is prerequisite for Sprint 1 remediation.
- specs/spec-a-parallel.md#L95 — AT-PARALLEL-013 determinism contract demands bitwise equality; torch.compile interference must be avoided.
- specs/spec-a-core.md#L520 — RNG seed contract requires mosaic/misset helpers to honour caller dtype/device to maintain differentiability expectations.
- docs/development/testing_strategy.md §1.4 — Device/dtype neutrality guardrail; mosaic helper should respect execution dtype.

How-To Map:
- Set `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and `BASE=reports/2026-01-test-suite-triage/phase_d/${STAMP}/determinism/phase_a_fix`; create `${BASE}/{logs,at_parallel_013,at_parallel_024}`.
- Code changes:
  1. In `tests/test_at_parallel_013.py` update `set_deterministic_mode()` to set `os.environ['TORCHDYNAMO_DISABLE'] = '1'` before calling `torch.use_deterministic_algorithms(...)`, and call `torch._dynamo.reset()` after toggling so other tests resume with defaults.
  2. In `src/nanobrag_torch/utils/c_random.py` accept `dtype: Optional[torch.dtype] = None` for `mosaic_rotation_umat()` and default to `torch.get_default_dtype()` when omitted.
  3. In `src/nanobrag_torch/models/crystal.py:728` pass `dtype=self.dtype` and `device=self.device` to `mosaic_rotation_umat(...)` so misset sampling respects the active execution settings.
- After edits run:
  * `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py --maxfail=0 --durations=10 | tee ${BASE}/at_parallel_013/pytest.log`
  * `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_024.py --maxfail=0 --durations=10 | tee ${BASE}/at_parallel_024/pytest.log`
  Store the commands in `${BASE}/commands.txt` and copy any additional summaries into `${BASE}/logs/` as needed.
- Update `docs/fix_plan.md` Attempt history for `[DETERMINISM-001]` with Attempt #4 (include pass/fail counts and notes on the Dynamo guard + dtype fix) and refresh `plans/active/determinism.md` Phase B status if blockers clear.

Pitfalls To Avoid:
- Keep the Dynamo disablement scoped to the determinism harness; do not wire `TORCHDYNAMO_DISABLE` globally in production code.
- Preserve existing docstring C references and surrounding comments when editing `c_random.py` and `crystal.py`.
- Do not introduce `.cpu()`/`.cuda()` calls in mosaic helpers; rely on provided dtype/device.
- Maintain differentiability—avoid `.detach()`/`.item()` when passing tensors between crystal and simulator.
- Run only the mapped tests; skip full-suite `pytest tests/` to save time.
- Respect Protected Assets listed in docs/index.md (no edits to loop.sh/input.md outside expected workflow).
- Capture the updated seed/determinism logs before moving on; they gate Phase B callchain work.
- Commit messages should cite the determinism plan item and list tests executed.

Pointers:
- docs/fix_plan.md:39 — determinism next actions snapshot.
- plans/active/determinism.md — Phase A completion notes and Phase B prerequisites.
- specs/spec-a-parallel.md#L95 — AT-PARALLEL-013 acceptance criteria.
- specs/spec-a-core.md#L520 — RNG seed and dtype expectations.
- tests/test_at_parallel_013.py — `set_deterministic_mode()` helper to tweak Dynamo env.
- src/nanobrag_torch/utils/c_random.py — `mosaic_rotation_umat` implementation.
- src/nanobrag_torch/models/crystal.py:720 — random misset call site.

Next Up: Prepare Phase B callchain tracing once determinism selectors execute without infrastructure failures.
