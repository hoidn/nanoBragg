Summary: Capture the full Phase L guarded pytest rerun with complete artifacts to unblock remediation synthesis.
Mode: Parity
Focus: docs/fix_plan.md#test-suite-triage-002-full-pytest-rerun-and-triage (Next Action 19 — Phase L guarded full-suite rerun)
Branch: feature/spec-based-2
Mapped tests: timeout 3600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=200 --timeout=905" pytest -vv tests/
Artifacts: reports/2026-01-test-suite-refresh/phase_l/$STAMP/{env,logs,artifacts,analysis}
Do Now: docs/fix_plan.md#test-suite-triage-002-full-pytest-rerun-and-triage — Run `timeout 3600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=200 --timeout=905" pytest -vv tests/` from repo root while teeing to `logs/pytest_full.log`, then capture `/usr/bin/time -v` to `artifacts/time.txt`, exit code to `artifacts/exit_code.txt`, and `--junitxml=artifacts/pytest.junit.xml`.
If Blocked: Capture the failing setup or fixture output under `reports/2026-01-test-suite-refresh/phase_l/$STAMP/analysis/blockers.md` and notify galph in Attempts History.
Priorities & Rationale:
- plans/active/test-suite-triage-phase-h.md:65 — Phase L tasks L1-L5 require full artifact bundle before Phase M synthesis can start.
- docs/fix_plan.md:19 — Next Action 19 is blocked until a complete rerun with logs/JUnit/summary exists; Attempt #85 only captured env files.
- docs/development/testing_strategy.md:Section 1.4 — Must honour device/dtype guardrails and gradient timeout policy during full-suite execution.
- arch.md:Section 2 — Run from canonical workspace to ensure fixtures and NB_C_BIN resolution fire correctly.
- reports/2026-01-test-suite-refresh/phase_g/20251015T163131Z/analysis/summary.md — Use as prior baseline when writing Phase L `analysis/summary.md` deltas.
How-To Map:
- `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`
- `BASE=reports/2026-01-test-suite-refresh/phase_l/$STAMP`
- `mkdir -p $BASE/{env,logs,artifacts,analysis}`
- `python - <<'PY'
import os
from pathlib import Path
print(Path.cwd())
PY` (expect `/home/ollie/Documents/nanoBragg4/nanoBragg`; abort if different)
- `env > $BASE/env/env.txt`
- `python - <<'PY'
import torch, json, platform
info = {
    "python": platform.python_version(),
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
}
print(json.dumps(info, indent=2))
PY > $BASE/env/torch_env.txt`
- `timeout 3600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=200 --timeout=905" pytest -vv tests/ --junitxml=$BASE/artifacts/pytest.junit.xml | tee $BASE/logs/pytest_full.log`
- `echo $? > $BASE/artifacts/exit_code.txt`
- `(/usr/bin/time -v env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=200 --timeout=905" pytest -vv tests/ > $BASE/artifacts/time.txt) 2>&1` (capture after main run to measure runtime; stop if >3600s)
- Parse fixture output from the tee’d log and summarise in `$BASE/analysis/fixtures.md` (note session fixtures, guardrails, NB_C_BIN resolution).
- Write `$BASE/analysis/summary.md` comparing pass/fail/skip counts and runtime against Phase G STAMP 20251015T163131Z; highlight new/resolved clusters.
Pitfalls To Avoid:
- Do not execute from `/home/ollie/Documents/tmp/nanoBragg`; run from repo root so session fixtures load.
- Do not omit `tee` to `logs/pytest_full.log`; this artifact is mandatory for Phase M parsing.
- Do not skip `/usr/bin/time -v`; Phase L needs runtime evidence to confirm timeout margin.
- Keep `NANOBRAGG_DISABLE_COMPILE=1` set to preserve gradcheck behaviour.
- Do not set `NB_SKIP_INFRA_GATE`; infrastructure guard must exercise.
- Avoid rerunning without resetting `$STAMP`; each attempt needs isolated directory.
- Ensure `pytest` exits before writing summary; if it times out, capture partial log and exit code.
- Do not delete or move artifacts referenced in docs/index.md (protected assets).
- Maintain CPU-only execution (`CUDA_VISIBLE_DEVICES=-1`) unless plan explicitly changes.
- After run, update Attempts History with outcomes/stamps.
Pointers:
- docs/fix_plan.md:19-20 — Blocking notes and remediation expectations.
- plans/active/test-suite-triage-phase-h.md:62-88 — Full Phase L + M checklist.
- docs/development/testing_strategy.md:Section 1.4 & 4.1 — Device discipline + gradient timeout guardrails.
- reports/2026-01-test-suite-refresh/phase_g/20251015T163131Z/analysis/summary.md — Prior baseline for comparison.
- scripts/validation/pytest_failure_parser.py — Optional helper for next phase classification.
Next Up: If time remains, begin Phase M parsing per plans/active/test-suite-triage-phase-h.md:73-88 after recording Phase L results.
