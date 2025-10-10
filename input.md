Summary: Capture CLI vs API baselines for the default_F regression and package Phase A evidence for `[CLI-DEFAULTS-001]`.
Mode: Parity
Focus: [CLI-DEFAULTS-001] Minimal -default_F CLI invocation
Branch: feature/spec-based-2
Mapped tests: tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F
Artifacts: reports/2026-01-test-suite-triage/phase_d/<STAMP>/cli-defaults/phase_a/
Do Now: `[CLI-DEFAULTS-001]` Phase A — run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F`, capture the zero-output CLI reproduction, collect `-show_config` output, and reproduce the working API path via `debug_default_f.py`, storing everything under the Phase A artifact root.
If Blocked: Re-run the pytest selector with `-vv` and append stderr/stdout plus `float_stats.txt`; note blocking detail in `summary.md` and log the attempt in `docs/fix_plan.md`.
Priorities & Rationale:
- `docs/fix_plan.md` ([CLI-DEFAULTS-001]) now references `plans/active/cli-defaults/plan.md`; Phase A completion unblocks P1 suite triage follow-ups.
- `specs/spec-a-cli.md` §AT-CLI-002 demands non-zero output for default_F-only runs; evidence must show present gap.
- `specs/spec-a-core.md` §§3–4 describe structure-factor fallback and fluence defaults—use these while comparing CLI vs API configs.
- `docs/debugging/debugging.md` mandates trace-first workflow; Phase A evidence sets the scene for Phase B callchain work.
- `tests/test_at_cli_002.py:15-76` provides authoritative parameters; reuse them verbatim to avoid drift.
How-To Map:
- `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F` → save full stdout/stderr to `phase_a/<STAMP>/cli_pytest/pytest.log`; run `python - <<'PY'` snippet to dump floatfile stats into `float_stats.txt`.
- `KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -cell 100 100 100 90 90 90 -default_F 100 -detpixels 32 -pixel 0.1 -distance 100 -lambda 6.2 -N 5 -floatfile float.bin -intfile int.img -show_config` (use tmpdir) → redirect stdout to `config_dump.txt` and include `commands.txt`.
- `KMP_DUPLICATE_LIB_OK=TRUE python debug_default_f.py` → store stdout in `phase_a/<STAMP>/api_control/run.log`; capture torch stats via `python - <<'PY'` if additional tensors inspected.
- Write `phase_a/<STAMP>/summary.md` comparing CLI vs API min/max/mean/non-zero plus initial hypotheses; mention identical device/dtype.
- Update `docs/fix_plan.md` Attempts list with the new timestamp and Phase A completion notes once artifacts are ready.
Pitfalls To Avoid:
- Do not shortcut artifact paths; follow `reports/2026-01-test-suite-triage/phase_d/<STAMP>/cli-defaults/phase_a/` exactly.
- Keep device/dtype consistent between CLI and API runs; no accidental GPU toggle.
- Preserve vectorization by avoiding ad-hoc script edits; this loop is evidence-only.
- Respect Protected Assets listed in `docs/index.md` (e.g., `input.md`, `loop.sh`).
- Do not delete or alter `debug_default_f.py`; treat it as read-only evidence.
- Ensure `KMP_DUPLICATE_LIB_OK=TRUE` is set on every torch-invoking command.
- Log attempt metadata (exit codes, runtimes) in `commands.txt` for each subtask.
- Avoid running additional pytest modules; stick to the mapped selector.
- Remember to sync timestamps/paths in `summary.md` and `docs/fix_plan.md`.
Pointers:
- plans/active/cli-defaults/plan.md — Phase A checklist and artifact policy.
- docs/fix_plan.md:62 — `[CLI-DEFAULTS-001]` ledger entry.
- tests/test_at_cli_002.py:28-63 — canonical CLI command arguments.
- src/nanobrag_torch/__main__.py:1070-1180 — CLI simulator invocation path (for context only).
- docs/debugging/debugging.md:24-91 — trace-first SOP framing Phase B.
Next Up: Begin Phase B callchain tracing per `plans/active/cli-defaults/plan.md` once Phase A evidence is logged.
