Summary: Finish C18 Phase Q by pinning pytest-timeout in manifests and capturing the guarded slow-gradient rerun (≤900 s).
Mode: Perf
Focus: TEST-SUITE-TRIAGE-001 / Next Action 13 — Phase Q tolerance rollout
Branch: feature/spec-based-2
Mapped tests: tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability
Artifacts: reports/2026-01-test-suite-triage/phase_q/$STAMP/
Do Now: STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-test-suite-triage/phase_q/$STAMP/chunk_03 && python -m pip show pytest-timeout > reports/2026-01-test-suite-triage/phase_q/$STAMP/dependency_audit.md && timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_q/$STAMP/chunk_03/pytest_part3b.xml | tee reports/2026-01-test-suite-triage/phase_q/$STAMP/chunk_03/pytest_part3b.log
If Blocked: If the command exits via timeout (124) or pytest-timeout is still missing, stop immediately, drop a note in reports/2026-01-test-suite-triage/phase_q/$STAMP/blocked.md with stderr/stdout, and ping me before rerunning.
Priorities & Rationale:
- docs/fix_plan.md:61 — Next Action 13 now explicitly requires dependency bookkeeping plus the tolerance rollout.
- plans/active/test-suite-triage.md:362 — Phase Q Q1-Q3 remain open until manifests, validation, and ledger updates land.
- reports/2026-01-test-suite-triage/phase_p/20251015T060354Z/c18_timing.md:112 — 900 s tolerance is conditioned on rerunning the slow-gradient shard with matching guards.
- reports/2026-01-test-suite-triage/phase_q/20251015T064831Z/summary.md:31 — Previous attempt timed out; we need a clean rerun with STAMPed artifacts.
How-To Map:
- Before running anything, add `pytest-timeout` to requirements.txt and to a new `[project.optional-dependencies.test]` list in pyproject.toml (keep entries alphabetised); leave a short note in reports/2026-01-test-suite-triage/phase_q/$STAMP/config_update.md summarising both edits.
- After edits, run `python -m pip show pytest-timeout >> reports/2026-01-test-suite-triage/phase_q/$STAMP/dependency_audit.md` to prove the plugin is discoverable from the editable install.
- Execute the Do Now command; once it finishes, capture the wall-clock duration from pytest output into reports/2026-01-test-suite-triage/phase_q/$STAMP/chunk_03/pytest_part3b_timing.txt and record the exit code in .../chunk_03/exit_code.txt.
- Snap environment fingerprints: `python --version`, `pip list | grep torch`, and `lscpu | grep "Model name"` into env_python.txt, env_torch.txt, and env_cpu.txt under the same STAMP directory.
- Summarise the outcome (runtime, pass/fail, tolerance margin) in reports/2026-01-test-suite-triage/phase_q/$STAMP/summary.md, citing the new artifacts and noting that docs + ledger updates remain for Q4/Q6.
- Stage the dependency edits + new artifacts once verified; do not touch docs or trackers until the validation results are green.
Pitfalls To Avoid:
- Do not rerun the full chunk list yet; only execute the singled-out gradient selector.
- Keep the timeout env vars on the same line as pytest to avoid `/bin/bash: CUDA_VISIBLE_DEVICES=-1: command not found`.
- Ensure NANOBRAGG_DISABLE_COMPILE=1 stays set; gradient timings rely on the compile guard.
- Avoid rewriting the existing slow marker description; just append the new slow_gradient entry.
- Preserve ASCII in all manifests and summaries; no Unicode symbols.
- Don’t delete the previous STAMP directories; create a fresh one for this run.
- Resist installing packages globally—edit manifests so future setups reproduce the plugin.
Pointers:
- docs/fix_plan.md:59-65
- plans/active/test-suite-triage.md:346-369
- reports/2026-01-test-suite-triage/phase_p/20251015T060354Z/c18_timing.md:90-160
- reports/2026-01-test-suite-triage/phase_q/20251015T064831Z/config_update.md
- pyproject.toml:41-59
- tests/test_gradients.py:571-580
Next Up: Phase Q Q4 documentation refresh once the guarded rerun artifacts are locked in.
