Summary: Restore the CUDA φ carryover trace by making the debug instrumentation device/dtype neutral and re-running M2h.2 evidence.
Mode: Parity
Focus: CLI-FLAGS-003 / plans/active/cli-noise-pix0/plan.md Phase M2h (carryover cache validation)
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>_carryover_cache_validation/{commands.txt,env.json,trace_py_scaling_cuda.log,trace_py_scaling_cpu.log,torch_collect_env.txt,diagnostics.md,cache_snapshot.txt,sha256.txt}
Do Now: CLI-FLAGS-003 M2h.2 — patch `src/nanobrag_torch/simulator.py` debug tensor factories to inherit `self.device`/`self.dtype`, then run `KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --phi-mode c-parity --device cuda --dtype float64 --out trace_py_scaling_cuda.log` inside a fresh timestamped `_carryover_cache_validation` folder.
If Blocked: If CUDA still hits a device mismatch, capture the full traceback plus a CPU retry in diagnostics.md, update docs/fix_plan.md Attempts with the blocker, and stop before further edits.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:128 flags M2h.2 as blocked until `_apply_debug_output` stops creating CPU-only HKL tensors.
- docs/fix_plan.md:3616-3644 lists the required fix and follow-up evidence before gradcheck (M2h.3) can start.
- docs/development/pytorch_runtime_checklist.md:11-15 reiterates the device/dtype neutrality rule you must restore.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T162542Z_carryover_cache_validation/diagnostics.md documents the current CUDA failure and expected artifact schema.
- src/nanobrag_torch/simulator.py:1487-1519 shows each bare `torch.tensor(...)` call that must be device/dtype aware.
How-To Map:
- `export ts=$(date -u +%Y%m%dT%H%M%SZ)`; `run_root=reports/2025-10-cli-flags/phase_l/scaling_validation`; `run_dir=$run_root/${ts}_carryover_cache_validation`; `mkdir -p "$run_dir"`.
- Log `pwd`, `git rev-parse HEAD`, `python --version`, `python - <<'PY'` snippet dumping torch/cuda availability, and the harness command into `${run_dir}/commands.txt`.
- After edits, run the CUDA harness command from repo root with stdout/err tee’d to `${run_dir}/trace_py_scaling_cuda.log`; record the exit status in diagnostics.md.
- If CUDA succeeds, immediately rerun the harness with `--device cpu` into `${run_dir}/trace_py_scaling_cpu.log` so both devices share the same artifact set.
- Capture environment metadata: `python - <<'PY'` (emit JSON into `${run_dir}/env.json`) and `python -m torch.utils.collect_env > ${run_dir}/torch_collect_env.txt`.
- Dump a short cache snapshot (first few entries of `_phi_cache_real_a/b/c`) into `${run_dir}/cache_snapshot.txt` to confirm previous-pixel data is present post-run.
- Finish diagnostics.md with summary bullets (command, pass/fail, F_latt value, cache observation) and update docs/fix_plan.md Attempts after committing.
Pitfalls To Avoid:
- Do not leave any new `torch.tensor(...)` without explicit `device=self.device` and matching dtype.
- Keep `_apply_debug_output` vectorized; do not introduce per-pixel Python loops beyond existing trace logic.
- Avoid `.detach()`/`.clone()` that would sever gradients for the cache tensors.
- Preserve existing trace output formatting; add at most minimal instrumentation tied to plan guidance.
- Don’t skip the CUDA retry—Phase M2h requires the GPU log before gradcheck can proceed.
- Re-run `pytest --collect-only …` after edits to confirm the selector still imports under the modified code.
- Honor Protected Assets; do not move or rename anything referenced in docs/index.md.
- Keep all debug tensors dtype-consistent (float64 for trace harness, default dtype elsewhere).
Pointers:
- plans/active/cli-noise-pix0/plan.md:1-160
- docs/fix_plan.md:3585-3644
- docs/development/pytorch_runtime_checklist.md:1-24
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T162542Z_carryover_cache_validation/diagnostics.md
- src/nanobrag_torch/simulator.py:1480-1524
Next Up: Once CUDA trace succeeds, tackle M2h.3 gradcheck packaging or advance to M2i trace parity per plan guidance.
