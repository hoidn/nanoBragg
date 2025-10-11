Summary: Finish dtype neutrality Phase E validation (rerun determinism tests, publish report, update docs).
Mode: Parity
Focus: [DTYPE-NEUTRAL-001] dtype neutrality guardrail
Branch: feature/spec-based-2
Mapped tests: tests/test_at_parallel_013.py; tests/test_at_parallel_024.py
Artifacts: reports/2026-01-test-suite-triage/phase_d/<STAMP>/dtype-neutral/phase_e/
Do Now: [DTYPE-NEUTRAL-001] Phase E1–E3 — run `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py --maxfail=0 --durations=10 --tb=short` and `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_024.py --maxfail=0 --durations=10 --tb=short`, archiving logs + validation.md under phase_e/, then apply the documented checklist/doc updates.
If Blocked: If TorchDynamo still hits device-index errors even with `CUDA_VISIBLE_DEVICES=-1`, capture the full stderr to phase_e/debug/ and halt before editing docs.
Priorities & Rationale:
- docs/fix_plan.md#L47 — Phase G addendum requires dtype Phase E close-out before other triage work can progress.
- docs/fix_plan.md#L540 — `[DTYPE-NEUTRAL-001]` Next Actions call for Phase E validation + documentation updates.
- plans/active/dtype-neutral.md#L68 — Phase E checklist (E1–E3) defines deliverables and artifact layout.
- reports/2026-01-test-suite-triage/phase_f/20251010T184326Z/pending_actions.md — Cluster C15 marked as critical blocker for determinism tests.
How-To Map:
- `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and `mkdir -p reports/2026-01-test-suite-triage/phase_d/${STAMP}/dtype-neutral/phase_e/{collect_only,at_parallel_013,at_parallel_024,docs}`.
- Optional sanity check: `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q | tee reports/2026-01-test-suite-triage/phase_d/${STAMP}/dtype-neutral/phase_e/collect_only/pytest.log`.
- Run the mapped determinism suites with CPU-only env; tee each log into `at_parallel_013/pytest.log` and `at_parallel_024/pytest.log`; note pass/fail counts and any remaining Dynamo skips.
- Summarise outcomes (dtype of cached tensors, remaining failures, Dynamo notes, CPU timing) in `reports/2026-01-test-suite-triage/phase_d/${STAMP}/dtype-neutral/phase_e/validation.md` alongside `commands.txt` and `env.json` (reuse Phase A template).
- Apply doc updates from `reports/2026-01-test-suite-triage/phase_d/20251010T174636Z/dtype-neutral/phase_c/docs_updates.md`: edit `docs/development/pytorch_runtime_checklist.md`, `docs/architecture/detector.md`, and any referenced guardrails, noting dtype cache requirements.
- Update `docs/fix_plan.md` Attempt history for `[DTYPE-NEUTRAL-001]` (Attempt #4) and `galph_memory.md` per plan task E3; mention whether `[DETERMINISM-001]` can proceed immediately.
Pitfalls To Avoid:
- Keep `CUDA_VISIBLE_DEVICES=-1` set throughout to avoid the known TorchDynamo GPU bug; if you lift it, document why.
- Do not mark `[DTYPE-NEUTRAL-001]` complete unless validation.md + doc updates are committed.
- Preserve Protected Assets listed in docs/index.md (e.g., `loop.sh`, `input.md`).
- No production code edits in this loop; limit changes to docs, reports, and metadata.
- Store every artifact under the stamped phase_e/ directory—no ad-hoc scratch folders.
- Note skipped tests explicitly in validation.md so future loops know whether GPU coverage still needs follow-up.
- When editing docs, cite the new artifact path and guardrails (avoid paraphrasing without references).
- Run `git diff` before staging docs to ensure only dtype-related edits appear.
- Maintain `KMP_DUPLICATE_LIB_OK=TRUE` on every pytest command to prevent MKL conflicts.
- Do not delete prior phase directories; append new STAMP.
Pointers:
- docs/fix_plan.md#L540
- plans/active/dtype-neutral.md#L68
- reports/2026-01-test-suite-triage/phase_g/20251011T030546Z/handoff_addendum.md#L1
- docs/development/testing_strategy.md#L19
Next Up: `[DETERMINISM-001]` Phase A rerun with TorchDynamo workaround once dtype Phase E attempt is logged.
