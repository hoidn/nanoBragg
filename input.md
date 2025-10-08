Summary: Guard tricubic trace instrumentation so Phase M scaling parity can resume safely.
Mode: Parity
Focus: CLI-FLAGS-003 Phase M0 instrumentation hygiene
Branch: feature/spec-based-2
Mapped tests:
- pytest --collect-only tests/test_cli_scaling_phi0.py
- pytest --collect-only tests/test_phi_carryover_mode.py
Artifacts:
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/instrumentation_audit.md
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/commands.txt
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/env.json
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling.log
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling_spec.log
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling_per_phi.log
- reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/sha256.txt
Do Now: CLI-FLAGS-003 Phase M0a–M0c instrumentation hygiene; run `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --phi-mode c-parity --pixel 685 1039 --out reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling.log --device cpu --dtype float64`, guard `_last_tricubic_neighborhood`, verify device/dtype neutrality, and update plan plus fix_plan with the new findings.
If Blocked: Capture stdout/stderr + traceback in instrumentation_audit.md, record the failing command and exit code in commands.txt, halt before production edits, and ping supervisor with the artifact path.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:46 — Phase M0 tasks must flip to [D] before Phase M1 traces are rerun.
- docs/fix_plan.md:460 — Next Actions now add C5/D3 documentation follow-up; instrumentation evidence needs to feed that attempt.
- plans/active/cli-phi-parity-shim/plan.md:48 — Upcoming C5 checklist depends on spec citations captured in the audit summary.
- docs/development/testing_strategy.md:35 — Device/dtype discipline applies to debug helpers; avoid CPU-only tensors.
- docs/bugs/verified_c_bugs.md:166 — Reference context for φ carryover bug when summarising results.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:1 — Harness entry point; keep command arguments consistent with supervisor plan.
How-To Map:
- Step 1: `ts=$(date -u +%Y%m%dT%H%M%SZ)`; `mkdir -p reports/2025-10-cli-flags/phase_l/scaling_validation/$ts` and export `RUN_DIR`.
- Step 2: Start instrumentation_audit.md with objective + checklist referencing plan IDs (M0a–M0c, C5a–C5c).
- Step 3: Append git state using `git status --short` and `git rev-parse HEAD >> commands.txt`.
- Step 4: Record env exports `echo "export KMP_DUPLICATE_LIB_OK=TRUE" >> commands.txt` and `echo "export PYTHONPATH=src" >> commands.txt`.
- Step 5: Verify editable install (`pip show nanobragg-torch` or `pip list | grep nanobragg`) and log result.
- Step 6: `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests/test_cli_scaling_phi0.py | tee -a commands.txt` (same for `tests/test_phi_carryover_mode.py`).
- Step 7: Run Do Now harness command (c-parity). Immediately rerun with `--phi-mode spec` writing to trace_py_scaling_spec.log.
- Step 8: Optional: repeat with `--dtype float32` (CPU) and, if CUDA available, `--device cuda --dtype float32`; capture successes/failures.
- Step 9: In a Python REPL, confirm `_last_tricubic_neighborhood` clears outside trace mode; document behavior in instrumentation_audit.md.
- Step 10: If guard changes were required, rerun Steps 6–8 to confirm no regressions, then capture env metadata via `python - <<'PY'` block writing env.json.
- Step 11: Finalise commands.txt (chronological), compute checksums via `shasum -a 256 * >> sha256.txt`, and snapshot plan/fix_plan updates in the Attempt log.
Pitfalls To Avoid:
- Do not leave `_last_tricubic_neighborhood` populated after non-trace runs.
- Avoid allocating CPU tensors inside trace helpers when running on CUDA.
- Keep instrumentation opt-in; no unconditional tricubic dumps in production path.
- Preserve vectorization—no Python loops when guarding debug data.
- Respect Protected Assets (input.md, docs/index.md, loop.sh).
- Do not modify specs/spec-a-core.md; reference it instead.
- No full pytest runs this loop; collect-only only per evidence gate.
- Ensure env vars exported before running harness commands.
- Record every command chronologically; missing provenance blocks plan completion.
- Leave trace harness unchanged except for scoped guard adjustments.
Pointers:
- plans/active/cli-noise-pix0/plan.md:46
- plans/active/cli-phi-parity-shim/plan.md:48
- docs/fix_plan.md:460
- docs/development/testing_strategy.md:35
- docs/bugs/verified_c_bugs.md:166
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:1
Next Up:
- Complete `plans/active/cli-phi-parity-shim/plan.md` C5 checklist (summary + spec citation) once instrumentation audit is logged.
