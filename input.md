Summary: Capture Phase A preflight for the full-suite rerun so we can relaunch test triage with fresh env + collection artifacts.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-002] Full pytest rerun and triage refresh
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests; pytest -vv tests/
Artifacts: reports/2026-01-test-suite-refresh/phase_a/$STAMP/; reports/2026-01-test-suite-refresh/phase_b/$STAMP/
Do Now: [TEST-SUITE-TRIAGE-002] Phase A — Preflight & env guard; run `KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest --collect-only -q tests`
If Blocked: Capture stderr/stdout to phase_a/$STAMP/pytest-collect.log, update summary.md with failure signature, and stop for supervisor review.
Priorities & Rationale:
- docs/fix_plan.md:39 — New critical directive requires immediate full-suite refresh before other initiatives continue.
- plans/active/test-suite-triage-rerun.md:23 — Phase A checklist mandates STAMP creation, env capture, and collection log.
- docs/development/testing_strategy.md:34 — Collect-only smoke is the sanctioned preflight before running `pytest tests/`.
- plans/archive/test-suite-triage.md:13 — 905 s timeout tolerance validated in prior initiative; reuse ceiling during rerun planning.
- docs/development/pytorch_runtime_checklist.md:41 — Slow gradient tests legitimately reach 905 s, so guard commands must preserve that tolerance.
How-To Map:
- Preflight setup: `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `mkdir -p reports/2026-01-test-suite-refresh/phase_a/$STAMP` (record STAMP for later phases).
- Env capture: `printenv | sort > reports/2026-01-test-suite-refresh/phase_a/$STAMP/env.txt`; `python -m torch.utils.collect_env > reports/2026-01-test-suite-refresh/phase_a/$STAMP/torch_env.txt`.
- Commands ledger: write the exact `pytest --collect-only` invocation to `commands.txt` in the phase folder before running it.
- Collection run: `KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest --collect-only -q tests | tee reports/2026-01-test-suite-refresh/phase_a/$STAMP/pytest-collect.log`; inspect exit code and note collected test count in `summary.md`.
- If collection succeeds, reuse the same STAMP for Phase B preparation and start staging commands for the full suite (`timeout 3600 env CUDA_VISIBLE_DEVICES=-1 ... pytest -vv tests/`) but defer execution until logs + summaries from Phase A are complete.
Pitfalls To Avoid:
- Do not skip the STAMP folder or env capture; future loops depend on reproducible preflight state.
- Keep `CUDA_VISIBLE_DEVICES=-1` unless explicitly instructed to gather GPU data.
- No code edits during this loop; treat this as evidence gathering only.
- Preserve Protected Assets (see docs/index.md); never move/delete `loop.sh`, `input.md`, or archived plans.
- Ensure `pytest --collect-only` output is captured to file; console-only logs are insufficient for archival.
- Don’t change the 905 s timeout unless supervisor approves a new ceiling.
- Avoid running the full suite before summarizing Phase A results.
- If `pytest` auto-configures cached bytecode, leave it in place—no manual cleanup.
- Watch for lingering `.pytest_cache`; note it in summary if it grows unusually large.
- Confirm `pip install -e .` remains valid; note if dependencies are missing before running tests.
Pointers:
- docs/fix_plan.md:39
- plans/active/test-suite-triage-rerun.md:23
- docs/development/testing_strategy.md:34
- plans/archive/test-suite-triage.md:13
- docs/development/pytorch_runtime_checklist.md:41
Next Up: After Phase A artifacts are committed, proceed to Phase B full-suite execution using the same STAMP.
