Summary: Capture the crashing scaling comparison run so we can document and unblock Phase M parity work.
Mode: Parity
Focus: CLI-FLAGS-003 Phase M1 tooling recovery
Branch: feature/spec-based-2
Mapped tests:
- pytest --collect-only tests/test_cli_scaling_phi0.py
- pytest --collect-only tests/test_phi_carryover_mode.py
- pytest -xvs tests/test_cli_scaling_phi0.py tests/test_phi_carryover_mode.py
Artifacts:
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/commands.txt
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling.log
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/compare_scaling_traces.stdout
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/env.json
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/sha256.txt
- plans/active/cli-noise-pix0/plan.md (M1 checklist updates)
- docs/fix_plan.md (Attempt noting repro + exit code)
Do Now: CLI-FLAGS-003 Phase M1a — `ts=$(date -u +%Y%m%dT%H%M%SZ); RUN_DIR=reports/2025-10-cli-flags/phase_l/scaling_validation/$ts; mkdir -p "$RUN_DIR"; KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --phi-mode c-parity --pixel 685 1039 --device cpu --dtype float64 --out "$RUN_DIR/trace_py_scaling.log" |& tee "$RUN_DIR/trace_harness.log"; KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py "$RUN_DIR/trace_py_scaling.log" --out "$RUN_DIR/scaling_validation_summary.md" |& tee "$RUN_DIR/compare_scaling_traces.stdout"; echo $? > "$RUN_DIR/compare_scaling_traces.exitcode"` (expect SIGKILL; capture exit code and dmesg snippet if present).
If Blocked: If the script exits 0 unexpectedly, keep all logs, note behaviour in `$RUN_DIR/blocked.md`, and halt so we can reassess before patching.
Priorities & Rationale:
- docs/fix_plan.md:461 — Next Actions demand completing the reopened Phase M1 tooling checklist before any physics fixes.
- plans/active/cli-noise-pix0/plan.md:17 — Status snapshot notes the SIGKILL regression blocking automation.
- plans/active/cli-noise-pix0/plan.md:71 — M1 row set to [P]; requires fresh repro plus canonical artifacts.
- plans/active/cli-noise-pix0/plan.md:82 — Checklist M1a–M1d outlines the exact deliverables for this loop.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T060721Z/commands.txt:1 — Prior failing command is the template you must refresh.
- scripts/validation/compare_scaling_traces.py:1 — Tool under test; fixes must preserve CLI and JSON schema.
How-To Map:
1. Export `ts` and `RUN_DIR` exactly as in Do Now; record `git rev-parse HEAD` and `git status -sb` at the top of `$RUN_DIR/commands.txt`.
2. Copy the authoritative supervisor command arguments from the plan into `$RUN_DIR/commands.txt` for provenance.
3. Run `trace_harness.py` command from Do Now; tee stdout/err to `trace_harness.log` and append a separator plus exit code to `commands.txt`.
4. Immediately invoke `compare_scaling_traces.py` with the paths above; tee output, capture the shell exit code into `compare_scaling_traces.exitcode`, and append both command + exit status to `commands.txt`.
5. If the process is killed, run `dmesg | tail -n 20 >> "$RUN_DIR/compare_scaling_traces.stdout"` to capture the kernel message.
6. Collect environment metadata via `python - <<'PY'` snippet (python version, torch version, CUDA availability, git SHA, timestamp) and write to `$RUN_DIR/env.json`.
7. After commands finish, list the directory contents (`ls -1 $RUN_DIR >> $RUN_DIR/commands.txt`), then compute checksums with `(cd "$RUN_DIR" && shasum -a 256 * > sha256.txt`).
8. Run the collect-only pytest selectors in Mapped tests, teeing output into `$RUN_DIR/pytest_collect.log`; if the crash prevented trace files from being written, note that before moving on.
9. Update `plans/active/cli-noise-pix0/plan.md` M1a row with the new timestamp and a short status note.
10. Append a docs/fix_plan.md Attempt entry describing the reproduced crash, exit code, and artifact paths (no implementation yet).
Pitfalls To Avoid:
- Do not edit `scripts/validation/compare_scaling_traces.py` until the repro is archived.
- Avoid overwriting the 20251008 directories; always use a new UTC timestamp.
- Keep `KMP_DUPLICATE_LIB_OK=TRUE` and `PYTHONPATH=src` on every python command.
- Preserve Protected Assets (`input.md`, `docs/index.md`, `loop.sh`, `supervisor.sh`).
- Do not run the full pytest suite; stick to the selectors listed.
- Capture exit codes explicitly—missing exitcode file blocks plan closure.
- Leave manual summaries untouched; this loop is evidence-only.
- Ensure commands.txt remains chronological and includes env + git info.
- Don’t delete previous traces; auditors rely on historical artifacts.
- Hold off on CUDA runs until the crash is understood.
Pointers:
- plans/active/cli-noise-pix0/plan.md:17
- plans/active/cli-noise-pix0/plan.md:71
- plans/active/cli-noise-pix0/plan.md:82
- docs/fix_plan.md:461
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T060721Z/commands.txt:1
- scripts/validation/compare_scaling_traces.py:1
Next Up: After the repro is locked down, move to M1b to patch compare_scaling_traces.py so scripted outputs are restored.
