Summary: Capture CPU parity diagnostics for the Option B φ carryover cache and tee up Phase M2h debugging.
Mode: Parity
Focus: CLI-FLAGS-003 / plans/active/cli-noise-pix0/plan.md > Phase M2h (carryover cache validation)
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/carryover_cache_validation/{commands.txt,env.json,pytest_cpu.log,diagnostics.md,sha256.txt}
Do Now: CLI-FLAGS-003 M2h.1 — run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q`, capture stdout to `pytest_cpu.log`, and record commands/env metadata inside the new carryover_cache_validation folder.
If Blocked: Capture `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests/test_cli_scaling_parity.py -q` output and the exception trace into diagnostics.md in the same folder, note the blocker in docs/fix_plan.md Attempts, then stop short of further edits.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:18-40 — Phase M2g now flagged [P]; M2h evidence bundle is the immediate gate before any more code changes.
- docs/fix_plan.md:451-466 — Next Actions require archiving Attempt #163 and running M2h.1-3 diagnostics before touching simulator logic again.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T153142Z_carryover_cache_plumbing/pytest_run2.log — Current failure shows `F_latt` rel err 1.57884 and omega indexing crash; we must reproduce and document under a new timestamp.
- specs/spec-a-core.md:205 — Spec mode must stay untouched; only c-parity shim may emulate the C bug during diagnostics.
- docs/bugs/verified_c_bugs.md:166-204 — Confirms the bug we mirror; keep diagnostics within the shim path and leave spec mode green.
How-To Map:
- Export `ts=$(date -u +%Y%m%dT%H%M%SZ)` then `run_dir=reports/2025-10-cli-flags/phase_l/scaling_validation/${ts}_carryover_cache_validation` and create the directory with placeholders for commands/env/diagnostics/logs.
- Record every CLI invocation (pytest, python, date) into `commands.txt`; capture `python --version`, `python -c "import torch; print(torch.__version__)"`, `git rev-parse HEAD`, and CUDA availability into `env.json`.
- Run the targeted pytest command, tee stdout to `pytest_cpu.log`, and immediately append the observed `F_latt`/`I_before_scaling` values plus any secondary stack traces into `diagnostics.md`.
- After the run, generate checksums via `cd "$run_dir" && sha256sum * > sha256.txt`.
- Update docs/fix_plan.md Attempts with the new timestamp, metrics (including the 1.57884 delta or new values), and note whether omega index errors persist; sync plans/active/cli-noise-pix0/plan.md M2h status if anything changes.
- Leave simulator/crystal code untouched; subsequent loops will handle fixes after evidence lands. If time remains, sketch CUDA/gradcheck prep notes inside diagnostics.md without running them yet.
Pitfalls To Avoid:
- Do not modify spec mode behaviour or cache reset logic—diagnostics only.
- Keep vectorisation intact: no new Python loops beyond the existing row batching path.
- Avoid `.detach()`, `.clone()`, or `.item()` on tensors that participate in gradient flows.
- Do not silence omega trace errors in code; document them in diagnostics.md instead.
- Preserve device/dtype neutrality—new tensors must inherit caller device/dtype.
- Respect Protected Assets: leave docs/index.md listings (loop.sh, supervisor.sh, input.md) untouched.
- No full test suite runs; targeted pytest only unless explicitly escalated later.
- No ad-hoc scripts outside reports/… directories; reuse trace_harness only when instructed.
- Do not force `self._phi_cache_initialized` on Simulator; always go through `Crystal.initialize_phi_cache`.
Pointers:
- plans/active/cli-noise-pix0/plan.md:25-40,118-121
- docs/fix_plan.md:451-466,3536-3567
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T153142Z_carryover_cache_plumbing/pytest_run2.log
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251210_optionB_design/optionB_batch_design.md:1-80
- docs/bugs/verified_c_bugs.md:166-204
Next Up:
- Run M2h.2 CUDA parity smoke once CPU evidence is archived.
- Execute the 2×2 ROI gradcheck (M2h.3) after CUDA/CPU logs confirm cache gradients remain intact.
