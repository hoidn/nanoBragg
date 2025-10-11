Summary: Phase D acceptance + spec/docs updates to finish [SOURCE-WEIGHT-002] and clear C3.
Mode: Docs
Focus: [SOURCE-WEIGHT-002] Simulator source weighting
Branch: feature/spec-based-2
Mapped tests: tests/test_at_src_001_simple.py::test_sourcefile_dtype_propagation, tests/test_at_src_001.py::TestAT_SRC_001_SourcefileAndWeighting::test_weighted_sources_integration, pytest tests/ --maxfail=5
Artifacts: reports/2026-01-test-suite-triage/phase_d/<STAMP>/source_weighting/
Do Now: [SOURCE-WEIGHT-002] Run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001_simple.py tests/test_at_src_001.py -x`
If Blocked: Capture the failing log + traceback in the new phase_d/<STAMP>/source_weighting/ folder, then note blockers in docs/fix_plan.md Attempt history before halting.
Priorities & Rationale:
- Align tests + spec (docs/fix_plan.md:155) so Sprint 1 C3 remediation can close cleanly.
- Follow Phase D checklist (plans/active/source-weighting.md:69) to meet acceptance + documentation gates.
- Update spec acceptance text (specs/spec-a-core.md:626) to match Option A parity already implemented in code/tests.
- Refresh runtime guardrail doc (docs/development/pytorch_runtime_checklist.md:1) with dtype reminder per Phase D scope.
- Record regression delta in remediation tracker once full suite run verifies C3 → 0.
How-To Map:
- Create timestamp: `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` then `outdir=reports/2026-01-test-suite-triage/phase_d/$STAMP/source_weighting` and `mkdir -p "$outdir"`.
- Phase D1: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001_simple.py tests/test_at_src_001.py -x | tee "$outdir/pytest_d1.log"`; capture `python -c "import torch;print(torch.cuda.is_available())"` to `$outdir/env.txt`.
- Phase D2 (after docs tweaks): `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/ --maxfail=5 | tee "$outdir/pytest_full.log"`; summarise pass/fail deltas in `$outdir/summary.md` and update `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/summary.md` counts.
- Phase D3 docs: edit `specs/spec-a-core.md` (AT-SRC-001 expectation) and add dtype reminder to `docs/development/pytorch_runtime_checklist.md`, noting references in summary + fix_plan Attempt entry.
- Phase D4: Update `plans/active/source-weighting.md` Phase D table and `docs/fix_plan.md` (Attempt #18) with artifact links; refresh remediation tracker/sequence counts.
Pitfalls To Avoid:
- Do not reintroduce per-source weighting in simulator; Option A parity must hold.
- Keep tensors device/dtype neutral; no `.cpu()`/`.numpy()` shortcuts in tests or docs examples.
- Preserve protected docs listed in docs/index.md; edits limited to scoped files.
- Archive every command/env file under the new phase_d stamp before updating ledgers.
- After spec edit, re-run `pytest --collect-only` if parser errors appear.
- No full-suite rerun without capturing log + summary in `$outdir`.
- Maintain warning expectations (λ mismatch) as acceptable; document rather than suppress unless spec demands.
- Update remediation tracker only after confirming new failure counts.
- Avoid touching vectorization plans; Sprint focus stays on test-suite triage.
- Include `KMP_DUPLICATE_LIB_OK=TRUE` env on all PyTorch pytest commands.
Pointers:
- docs/fix_plan.md:155
- plans/active/source-weighting.md:69
- reports/2026-01-test-suite-triage/phase_j/20251011T064811Z/source_weighting/summary.md:1
- specs/spec-a-core.md:635
- docs/development/pytorch_runtime_checklist.md:1
- docs/development/testing_strategy.md:80
Next Up: If time remains, prep spec diff notes for review before opening `[TEST-SUITE-TRIAGE-001]` Sprint 1 tracker update.
