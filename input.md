Summary: Capture a guarded full-suite rerun with the new collection fixtures and log parity deltas against Phase G.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-002] Next Action 19 — Phase L guarded full-suite rerun
Branch: feature/spec-based-2
Mapped tests: timeout 3600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=200 --timeout=905" pytest -vv tests/
Artifacts: reports/2026-01-test-suite-refresh/phase_l/$STAMP/

Do Now: [TEST-SUITE-TRIAGE-002] Next Action 19 (Phase L guarded full-suite rerun) — timeout 3600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=200 --timeout=905" pytest -vv tests/
If Blocked: Capture fixture failure output under reports/2026-01-test-suite-refresh/phase_l/$STAMP/blockers/ and halt for supervisor guidance.

Priorities & Rationale:
- `docs/fix_plan.md:77` promotes Phase L as the next executable gate now that Phase K is closed.
- `plans/active/test-suite-triage-phase-h.md:60` details the Phase L tasks and artifact expectations.
- `docs/development/testing_strategy.md:30` requires the supervisor handoff to include the exact pytest command and cadence.
- `docs/development/pytorch_runtime_checklist.md:29` mandates setting `NANOBRAGG_DISABLE_COMPILE=1` for gradient-bearing suites.

How-To Map:
- Export `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and create `reports/2026-01-test-suite-refresh/phase_l/$STAMP/{env,logs,artifacts,analysis}`; record env guard to `env/env.txt` using `printenv` and `python -m torch.utils.collect_env`.
- Run the guarded suite (`timeout 3600 env ... pytest -vv tests/`) capturing tee output to `logs/pytest_full.log`, `--junitxml=artifacts/pytest.junit.xml`, `/usr/bin/time -v` → `artifacts/time.txt`, and exit status in `artifacts/exit_code.txt`.
- Immediately note `session_infrastructure_gate` / `gradient_policy_guard` messages in `analysis/fixtures.md`, and draft `analysis/summary.md` comparing counts vs Phase G STAMP 20251015T163131Z.
- Update `commands.txt` with the executed command, append findings to `docs/fix_plan.md` Attempt history, and ping galph if guards abort execution.

Pitfalls To Avoid:
- Do not set `NB_SKIP_INFRA_GATE`; the guard must run in production mode.
- Keep the command on one line so env vars apply to pytest.
- Respect the 3600s outer timeout; abort instead of re-running blindly if exceeded.
- Do not edit fixtures or production code during this evidence pass.
- Ensure logs stay under the STAMPed directory; no ad-hoc locations.
- Double-check `NB_C_BIN` resolves before starting to avoid wasting the 3600s window.
- Preserve Protected Assets listed in `docs/index.md` while staging artifacts.
- Record wall-clock runtime and failure deltas before proceeding to Phase M.

Pointers:
- plans/active/test-suite-triage-phase-h.md:60
- docs/fix_plan.md:77
- docs/development/pytorch_runtime_checklist.md:29
- reports/2026-01-test-suite-refresh/phase_k/20251015T182108Z/validation/summary.md

Next Up: Next Action 20 — Phase M failure synthesis & tracker refresh (prepare once Phase L bundle is complete).
