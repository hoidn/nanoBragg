Summary: Capture the Phase K full-suite pytest run and refresh triage artifacts before resuming remediation.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: pytest tests/
Artifacts: reports/2026-01-test-suite-triage/phase_k/<STAMP>/{commands.txt,logs/pytest_full.log,artifacts/pytest_full.xml,analysis/triage_summary.md,analysis/classification_overview.md,summary.md,env/torch_env.txt}
Do Now: Phase K full-suite run — CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_k/$STAMP/artifacts/pytest_full.xml
If Blocked: Capture partial logs + junit under the same Phase K directory, author reports/2026-01-test-suite-triage/phase_k/$STAMP/blocked.md describing the failure (timeout, infra issue, etc.), and halt for supervisor review.
Priorities & Rationale:
- docs/fix_plan.md:3-46 — Phase K rerun is now the critical path; other remediation is paused until fresh results land.
- plans/active/test-suite-triage.md:11-152 — Phase K tasks (K1–K3) define the required artifacts and follow-up updates for this loop.
- plans/active/source-weighting.md:3-66 — Source-weighting work is explicitly paused pending Phase K outcomes; do not touch those files yet.
- docs/development/testing_strategy.md:18-33 — follow device/dtype guardrails and log the authoritative full-suite command with exact flags.
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-test-suite-triage/phase_k/$STAMP/{artifacts,logs,analysis,env} and record every shell command via `tee -a reports/2026-01-test-suite-triage/phase_k/$STAMP/commands.txt`.
- Run the Do Now command with `| tee reports/2026-01-test-suite-triage/phase_k/$STAMP/logs/pytest_full.log`; collect stderr too (append `2>&1`).
- After the run, copy `pytest --version` and `python -m torch.utils.collect_env` outputs into `env/torch_env.txt` for reproducibility.
- Summarise key metrics (pass/fail counts, runtime, top durations) in `reports/2026-01-test-suite-triage/phase_k/$STAMP/summary.md`.
- Rebuild `analysis/triage_summary.md` and `analysis/classification_overview.md` by diffing against Phase I results (`reports/2026-01-test-suite-triage/phase_i/20251011T042127Z/`) and tagging each failure as implementation bug vs deprecation candidate; note deltas.
- Update `reports/2026-01-test-suite-triage/phase_j/latest/remediation_tracker.md` with new counts/owners and document the adjustments in `phase_k/$STAMP/summary.md`.
- Log Attempt #13 in docs/fix_plan.md with artifact paths and classification highlights once artifacts are complete.
Pitfalls To Avoid:
- Do not edit production code or tests during this loop; evidence collection only.
- Keep the KMP_DUPLICATE_LIB_OK=TRUE and CUDA_VISIBLE_DEVICES=-1 env vars exactly as shown.
- Ensure the junit XML path matches `phase_k/$STAMP/artifacts/pytest_full.xml`; avoid mixing timestamps.
- Capture full stdout/stderr; no truncated logs or `--maxfail` overrides beyond the specified zero.
- Preserve previous Phase I/Phase J artifacts; do not overwrite or rename them when generating deltas.
- Stay off paused workstreams (`[SOURCE-WEIGHT-002]`, `[VECTOR-PARITY-001]`) until Phase K results are documented.
- If the suite fails early, note the last completed test and reason inside blocked.md before stopping.
Pointers:
- docs/fix_plan.md:3-155 — Active focus, reproduction command, and paused dependencies.
- plans/active/test-suite-triage.md:11-152 — Phase K checklist and artifact expectations.
- docs/development/testing_strategy.md:18-33 — Device/dtype + Do Now guidance.
Next Up: If time remains after updating artifacts, draft the Attempt #13 ledger note so the supervisor can review quickly next loop.
