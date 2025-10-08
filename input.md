Summary: Capture CUDA + gradcheck diagnostics for the φ carryover cache and confirm whether the cache reads the previous pixel’s φ=final vectors.
Mode: Parity
Focus: CLI-FLAGS-003 / plans/active/cli-noise-pix0/plan.md > Phase M2h (carryover cache validation)
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>_carryover_cache_validation/{commands.txt,env.json,trace_py_scaling_cuda.log,gradcheck.{py,log},diagnostics.md,cache_snapshot.txt,torch_collect_env.txt,sha256.txt}
Do Now: CLI-FLAGS-003 M2h.2 — run `KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --phi-mode c-parity --device cuda --dtype float64 --out trace_py_scaling_cuda.log`, capture stdout/stderr, and record metadata inside a fresh `<ts>_carryover_cache_validation` folder.
If Blocked: If CUDA is unavailable or the harness exits non‑zero, rerun with `--device cpu`, store the failing output and traceback in diagnostics.md, update the Attempt log with the blocker, and stop before attempting gradcheck or cache inspection.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:28-60 — M2h.2/M2h.3 evidence precedes the new Step 4 cache-index audit; completing them unblocks Phase M2i.
- docs/fix_plan.md:451-505 — Next Actions now insist on CUDA + gradcheck logs plus an explicit cache-index review before simulator edits resume.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T160802Z_carryover_cache_validation/diagnostics.md — CPU parity failure context and reusable gradcheck skeleton live here; replicate structure for consistency.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251210_optionB_design/optionB_batch_design.md:150-260 — Design requires the cache to substitute previous pixel φ=final values; verify current implementation respects that contract.
- src/nanobrag_torch/models/crystal.py:245-360,430-520 — `apply_phi_carryover` and `store_phi_final` paths must be checked against observed cache contents during this loop.
- src/nanobrag_torch/simulator.py:750-1130 — Row-wise batching currently feeds `(slow_indices, fast_indices)` directly; confirm whether this keeps previous-pixel semantics or needs adjustment.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T153142Z_carryover_cache_plumbing/pytest_run2.log — Earlier failure shows the sign flip; use it as comparison when reviewing new CUDA output.
- docs/bugs/verified_c_bugs.md:166-204 — C-PARITY-001 description clarifies what the shim must emulate; reference while interpreting the cache snapshots.
- specs/spec-a-core.md:200-260 — Normative φ rotation makes clear spec mode should not carry over; retain as baseline when contrasting with c-parity evidence.
- docs/architecture/pytorch_design.md:90-170 — Vectorization guidance reminds us to keep batched flows intact once the cache is fixed.
- galph_memory.md (latest entry) — Supervisor notes call out the suspected index mismatch; keep diagnosis aligned with that context.
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md — Contains tolerance decisions; ensure new evidence does not regress VG-1 guarantees.
- CLAUDE.md (rules 8-11,16) — Reinforces gradient/device guardrails to keep in mind during diagnostics scripts.
How-To Map:
- Export `ts=$(date -u +%Y%m%dT%H%M%SZ)`; set `run_root=reports/2025-10-cli-flags/phase_l/scaling_validation` and `run_dir=${run_root}/${ts}_carryover_cache_validation`; create the directory with `mkdir -p "$run_dir"`.
- Seed `commands.txt` with timestamp, working directory, `git rev-parse HEAD`, `python --version`, `python -c "import torch; print(torch.__version__)"`, and `nvidia-smi || echo no_cuda`.
- Copy the authoritative supervisor command parameters into the top of diagnostics.md so future loops can align context quickly.
- Note the CPU evidence folder (`20251008T160802Z_carryover_cache_validation`) in diagnostics.md to show lineage before adding new data.
- Run the CUDA trace harness using Do Now command; tee stdout/stderr to `${run_dir}/trace_py_scaling_cuda.log` and append the exact invocation to commands.txt.
- Record the harness exit code, `F_latt` value from the log, and any trace anomalies in diagnostics.md immediately after the run.
- Check `torch.cuda.is_available()` and `torch.cuda.get_device_name(0)` in a small snippet; append results to env.json for reproducibility.
- Emit environment metadata via `python - <<'PY' ...` into `${run_dir}/env.json`, matching key names used in the CPU attempt (python_version, torch_version, cuda_version, git_sha, hostname, device).
- Capture `python -m torch.utils.collect_env > ${run_dir}/torch_collect_env.txt` for completeness; link it from diagnostics.md.
- Before gradcheck, open a Python REPL that imports the simulator, ensures the cache is initialized, and dump `crystal._phi_cache_real_a[0, :5, :, :]` to `${run_dir}/cache_snapshot.txt` labelled “pre-harness”.
- After the CUDA run, repeat the cache snapshot dump labelled “post-harness” to observe changes; annotate whether values shift toward previous fast index.
- Generate `${run_dir}/gradcheck.py` from the template in diagnostics.md; ensure it seeds deterministic data (`torch.manual_seed(1234)`), uses float64, and drives the Option B cache paths.
- Execute gradcheck with `KMP_DUPLICATE_LIB_OK=TRUE python gradcheck.py | tee ${run_dir}/gradcheck.log`; include asserts that cache gradients are non-null and comment results inside the script.
- Capture any warnings or failures from gradcheck in diagnostics.md with timestamps; mention tolerance used (e.g., `eps=1e-4`, `rtol=1e-3`).
- Inspect cache tensors manually: evaluate `crystal._phi_cache_real_a[slow_indices, fast_indices]` vs `crystal._phi_cache_real_a[slow_indices, (fast_indices-1)%F]`; document which entry matches the logged φ=final vector.
- Compute a quick diff `torch.norm(curr - prev)` for fast indices 0, 1, 2 and log numeric values to substantiate conclusions.
- Summarize CUDA vs CPU parity deltas (F_latt, I_before_scaling) in diagnostics.md; highlight whether sign flip persists across devices.
- Run `sha256sum * > sha256.txt` inside the run directory to seal the artifact set.
- Update docs/fix_plan.md Attempts with timestamp, CUDA parity outcome, gradcheck result, cache-index conclusion, and references to cache_snapshot.txt and torch_collect_env.txt.
- Flip M2h.2 and M2h.3 rows to [D] in plans/active/cli-noise-pix0/plan.md once artifacts are in place; mention the cache-index takeaways in the plan notes if applicable.
- Leave a TODO in diagnostics.md for Step 4 (cache index audit) if definitive proof is still pending so the next loop knows what remains.
Cache Audit Notes:
- Expect the correct carryover to use previous pixel’s φ=final vector `(fast-1)` within the same row; column 0 should wrap to the last fast index of the preceding row.
- When inspecting cache snapshots, look for identical values across the row (current code likely stores same tensor everywhere); flag if substitution never occurs.
- Confirm whether `cache_valid` gating masks per pixel or blanket-applies substitution; note any discrepancy.
- Document whether `store_phi_final` fires before or after physics accumulation in the row loop; this may explain sign flip behavior.
- If cached entries remain zero after CUDA run, record that fact—the cache may not populate at all, indicating earlier phases did not hook storage correctly.
- Compare traced `TRACE_PY: ap_phi_final` from the CUDA log with cache contents to see if they match expected tensors.
- Note if `apply_phi_carryover` returns identical tensors for all fast indices; this would confirm the suspected indexing bug.
- Check whether reciprocal cache tensors (`_phi_cache_recip_a` etc.) mirror behaviors seen in real-space caches.
- Observe whether fast-index wrap-around draws from previous row; note any off-by-one effects.
Deliverables Checklist:
- `${run_dir}/trace_py_scaling_cuda.log` containing the full CUDA harness output.
- `${run_dir}/env.json` summarizing runtime versions and device metadata.
- `${run_dir}/torch_collect_env.txt` produced by `python -m torch.utils.collect_env`.
- `${run_dir}/cache_snapshot.txt` with pre/post cache dumps and annotations.
- `${run_dir}/gradcheck.py` (script) and `${run_dir}/gradcheck.log` (console output).
- `${run_dir}/diagnostics.md` capturing metrics, hypotheses, and cache-index conclusions.
- `${run_dir}/commands.txt` listing every CLI invocation (including gradcheck, cache probes, checksum command).
- `${run_dir}/sha256.txt` listing digests for every artifact in the directory.
- docs/fix_plan.md Attempt entry referencing the timestamp, metrics, and artifacts.
- plans/active/cli-noise-pix0/plan.md updates marking M2h.2/M2h.3 [D] once evidence is captured.
- Optional `${run_dir}/cache_diff.csv` if you tabulate per-pixel cache deltas; include if generated.
- Optional `${run_dir}/cuda_vs_cpu_summary.md` summarizing device parity if you prepare a concise comparison.
Pitfalls To Avoid:
- Do not touch simulator/crystal code this loop; evidence only.
- Keep `phi_carryover_mode` set to `"c-parity"`; spec mode evidence is not useful here.
- Avoid reusing timestamp directories; each attempt must live in its own folder for auditability.
- Retain failed logs; never delete or overwrite them even if a later rerun succeeds.
- Ensure cache snapshots and other debugging scripts maintain device/dtype parity—no implicit `.cpu()` without noting it in diagnostics.
- Refrain from `.detach()`, `.clone()`, or `.item()` on cache tensors during inspection; copy to CPU tensors only after documenting the operation.
- Confirm gradcheck uses double precision and clean tolerances; a loose tolerance can mask genuine gradient drops.
- Do not run the full pytest suite; targeted harness + gradcheck only per evidence-mode gate.
- Respect Protected Assets from docs/index.md (loop.sh, supervisor.sh, input.md) and avoid rewriting them.
- When interpreting cache data, note row iteration order—row 0 column 0 should inherit the previous row’s last column.
- Verify the harness respects `KMP_DUPLICATE_LIB_OK=TRUE`; missing env var can trip MKL errors mid-run.
- Avoid checking cache tensors before calling `initialize_phi_cache`; uninitialized tensors will raise index errors.
- Capture environment variables (CUDA_VISIBLE_DEVICES, TORCH_LOGS, TORCHINDUCTOR_CACHE_DIR) if set—they influence reproducibility.
- Keep diagnostics.md purely ASCII; avoid inserting tab characters or fancy Unicode.
- Do not mix CPU and CUDA results in the same cache snapshot without clearly labelling sections.
Pointers:
- plans/active/cli-noise-pix0/plan.md:28-132
- docs/fix_plan.md:451-505
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T160802Z_carryover_cache_validation/diagnostics.md
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251210_optionB_design/optionB_batch_design.md:150-260
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T153142Z_carryover_cache_plumbing/pytest_run2.log
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/summary.md
- reports/2025-10-cli-flags/phase_l/scaling_validation/scaling_validation_summary.md
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py
- tests/test_cli_scaling_parity.py:1-140
- src/nanobrag_torch/models/crystal.py:245-360,430-520
- src/nanobrag_torch/simulator.py:750-1130
- docs/bugs/verified_c_bugs.md:166-204
- docs/development/testing_strategy.md:30-120
- galph_memory.md (latest section)
- CLAUDE.md: Protected Assets rule for reference when handling artifacts.
- scripts/validation/compare_scaling_traces.py — Use for cross-checks if needed after evidence is gathered.
Next Up: Kick off M2i.1 ROI trace rerun once CUDA + gradcheck diagnostics land and cache-index notes confirm whether the cache reads previous-pixel state.
