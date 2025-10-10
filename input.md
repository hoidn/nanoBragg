Summary: Restore the minimal `-default_F` CLI path so AT-CLI-002 produces non-zero intensities.
Mode: Parity
Focus: [CLI-DEFAULTS-001] Minimal -default_F CLI invocation
Branch: feature/spec-based-2
Mapped tests: pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F; pytest -v tests/test_at_cli_002.py
Artifacts: reports/2026-01-test-suite-triage/phase_d/<STAMP>/attempt_cli_defaults_fix/
Do Now: [CLI-DEFAULTS-001] run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F` after implementing the default_F fallback and archive commands/logs under `reports/2026-01-test-suite-triage/phase_d/<STAMP>/attempt_cli_defaults_fix/`.
If Blocked: Re-run the same selector and capture `float_stats.txt` (min/max/sum all zero) plus hypothesis notes in `attempt_notes.md`, then push the artifacts so we can escalate causes (structure-factor lookup vs fluence).
Priorities & Rationale:
- docs/fix_plan.md:62 — Fix plan hypotheses call out missing default_F fallback and fluence defaults.
- reports/2026-01-test-suite-triage/phase_d/20260113T000000Z/handoff.md:11 — Priority ladder puts `[CLI-DEFAULTS-001]` at the top of the remediation queue.
- specs/spec-a-cli.md:163 — AT-CLI-002 mandates successful renders when only `-default_F` supplies structure factors.
- plans/active/test-suite-triage.md:11 — Phase D is now complete; this loop activates the first P1 fix so triage momentum continues.
- tests/test_at_cli_002.py:28 — Acceptance test asserts the float image contains non-zero intensities for this scenario.
How-To Map:
- `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `mkdir -p reports/2026-01-test-suite-triage/phase_d/$STAMP/attempt_cli_defaults_fix` before code edits.
- Inspect `src/nanobrag_torch/models/crystal.py:210` to confirm the no-HKL path actually returns `default_F`; trace the call sites in `__main__` to verify the Crystal config carries the flag.
- Review `src/nanobrag_torch/config.py:514` to ensure BeamConfig retains a positive fluence without explicit flux/exposure; adjust only if the defaults zero the signal.
- Log every invocation in `commands.txt`; after implementation run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F | tee pytest.log`.
- Add a quick CLI smoke check (`python -m nanobrag_torch ...`) and write `float_stats.txt` capturing min/max/sum so we have numeric evidence of the non-zero image.
- When the targeted test passes, follow up with `pytest -v tests/test_at_cli_002.py` and store the log as `pytest_full.log` in the same artifact folder.
- Update `docs/fix_plan.md` `[CLI-DEFAULTS-001]` Attempts with the new stamp + findings and summarise outcomes in `attempt_notes.md`.
Pitfalls To Avoid:
- Avoid reintroducing Python loops; keep structure-factor fixes vectorised.
- Do not call `.item()` on tensors that should stay differentiable.
- Stick to the mapped tests; skip `pytest tests/` until broader remediation resumes.
- Always set `KMP_DUPLICATE_LIB_OK=TRUE` for torch runs.
- Keep new tensors device/dtype neutral (`type_as` / `.to()` helpers) to protect GPU flows.
- Leave existing artifacts intact; add new directories instead of overwriting prior attempts.
- Align CLI semantics with `docs/development/c_to_pytorch_config_map.md` — no ad-hoc flags or shortcuts.
- Document every executed command in `commands.txt` for provenance.
Pointers:
- docs/fix_plan.md:62
- reports/2026-01-test-suite-triage/phase_d/20260113T000000Z/handoff.md:11
- specs/spec-a-cli.md:163
- tests/test_at_cli_002.py:28
- src/nanobrag_torch/models/crystal.py:210
- src/nanobrag_torch/config.py:514
Next Up: `[DETERMINISM-001]` RNG determinism reproduction (`pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py`) once default_F passes.
