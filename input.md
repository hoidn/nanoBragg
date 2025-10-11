Summary: Implement the Phase M2 gradient compile guard and prove the gradcheck suite passes under NANOBRAGG_DISABLE_COMPILE=1.
Mode: none
Focus: [TEST-SUITE-TRIAGE-001] Phase M2 — Gradient Infrastructure Gate
Branch: feature/spec-based-2
Mapped tests: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py -k "gradcheck" --tb=short; (optional GPU) env CUDA_VISIBLE_DEVICES=0 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py -k "gradcheck" --tb=short
Artifacts: reports/2026-01-test-suite-triage/phase_m2/$STAMP/gradient_guard/; reports/2026-01-test-suite-triage/phase_m2/$STAMP/gradients_cpu/; reports/2026-01-test-suite-triage/phase_m2/$STAMP/gradients_gpu/ (if run); reports/2026-01-test-suite-triage/phase_m2/$STAMP/summary.md
Do Now: Execute docs/fix_plan.md [TEST-SUITE-TRIAGE-001] Next Actions #1 — implement Phase M2b guard and run `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py -k "gradcheck" --tb=short`
If Blocked: Capture the failure log under reports/2026-01-test-suite-triage/phase_m2/$STAMP/blocked.md with command/output and stop for supervisor guidance.

Priorities & Rationale:
- docs/fix_plan.md:40-120 — Next Actions now target Phase M2b-d (compile guard + gradient reruns + documentation updates).
- plans/active/test-suite-triage.md:11-260 — Phase M1 closed; Phase M2 table lists the required guard, test reruns, and documentation touch points.
- reports/2026-01-test-suite-triage/phase_m2/20251011T171454Z/strategy.md:1 — Strategy brief defining guard mechanics, commands, and documentation scope.
- arch.md:120-220 — Differentiability guidelines the guard must respect when disabling torch.compile.
- docs/development/testing_strategy.md:52-140 — Authoritative commands and gradient test expectations.

How-To Map:
1. `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` then `mkdir -p reports/2026-01-test-suite-triage/phase_m2/$STAMP/{gradient_guard,gradients_cpu}` (and `gradients_gpu` if CUDA run).
2. Update `src/nanobrag_torch/simulator.py` so `NANOBRAGG_DISABLE_COMPILE=1` reliably skips `torch.compile` (ensure the flag is read before any compile call) and set the env flag at the top of `tests/test_gradients.py` before importing torch; record the command summary in `gradient_guard/commands.txt` plus a short rationale in `gradient_guard/notes.md`.
3. Run the CPU selector: `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py -k "gradcheck" --tb=short`; save stdout to `gradients_cpu/pytest.log`, capture `env.txt` via `python - <<'PY'
import torch, json, platform
print(json.dumps({"python": platform.python_version(), "torch": torch.__version__}, indent=2))
PY`.
4. If `torch.cuda.is_available()`, repeat Step 3 with `CUDA_VISIBLE_DEVICES=0` and store results in `gradients_gpu/`. Afterwards update `arch.md` §15, `docs/development/testing_strategy.md` §1.4, `docs/development/pytorch_runtime_checklist.md`, `remediation_tracker.md`, and append the new Attempt + summary path to `[TEST-SUITE-TRIAGE-001]`; summarise everything in `phase_m2/$STAMP/summary.md` with commands/env/exit status.

Pitfalls To Avoid:
- Set `os.environ['NANOBRAGG_DISABLE_COMPILE'] = '1'` **before** importing torch in tests to avoid Dynamo caching the compiled graph.
- Do not remove existing compile support—only gate it; production runs must still compile when the env var is unset.
- Keep artifact directories unique per STAMP and avoid overwriting prior Attempt bundles.
- Capture pytest output with `--tb=short` for readability; no full-suite invocations this loop.
- Maintain ASCII text; avoid non-standard Unicode in docs or logs.
- Update documentation sections atomically—reference precise subsections when editing.
- If CUDA smoke fails, stop after logging under `gradients_gpu/` and do not patch around the failure.
- Ensure `remediation_tracker.md` counts align with the new pass totals before closing.
- Record the new Attempt in docs/fix_plan.md without renumbering prior entries.
- Leave `NANOBRAGG_DISABLE_COMPILE` unset after tests to avoid surprising other suites.

Pointers:
- docs/fix_plan.md:40-120
- plans/active/test-suite-triage.md:25-250
- reports/2026-01-test-suite-triage/phase_m2/20251011T171454Z/strategy.md:1-200
- arch.md:120-220
- docs/development/testing_strategy.md:52-140

Next Up: If time remains, start Phase M2d documentation updates per summary checklist.
