Summary: Regenerate and analyse the per-φ scaling traces so we can pinpoint the lattice-factor sign flip that blocks the supervisor command parity run.
Mode: Parity
Focus: CLI-FLAGS-003 – Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: [tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics]
Artifacts:
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling_20251119.log
- reports/2025-10-cli-flags/phase_l/per_phi/trace_py_scaling_20251119_per_phi.{log,json}
- reports/2025-10-cli-flags/phase_l/per_phi/comparison_summary_20251119.md
- reports/2025-10-cli-flags/phase_l/scaling_validation/{scaling_validation_summary_20251119.md,metrics.json,run_metadata.json}
Do Now: CLI-FLAGS-003 — run `PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --device cpu --dtype float32 --out trace_py_scaling_20251119.log`, then `KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling_20251119.log --out reports/2025-10-cli-flags/phase_l/scaling_validation/scaling_validation_summary_20251119.md`, finally `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics -q` to confirm instrumentation stability.
If Blocked: Capture the full harness stdout to `reports/2025-10-cli-flags/phase_l/per_phi/trace_py_scaling_20251119_raw.txt`, note whether any `TRACE_PY_PHI` lines appear, and log the failure mode plus commands under docs/fix_plan.md Attempt history before requesting supervisor guidance.
Priorities & Rationale:
- docs/fix_plan.md:460-463 promotes refreshed per-φ scaling validation as the top blocker before documentation or parity reruns.
- plans/active/cli-noise-pix0/plan.md:20-33,260-266 records that the existing per-φ artifact lacks `TRACE_PY_PHI`, and that Phase L3e remains open until new evidence is captured.
- reports/2025-10-cli-flags/phase_l/scaling_validation/analysis_20251119.md:1-41 links the residual 24% intensity gap directly to missing lattice-factor parity, prioritising renewed trace capture.
- reports/2025-10-cli-flags/phase_l/per_phi/comparison_summary_20251119.md:1-96 documents the previous instrumentation contract and expected schema, which the new run must reproduce.
- scripts/validation/compare_scaling_traces.py:1-320 formalises the tolerance envelope (≤1e-6) that L3e must satisfy before the plan can progress.
- reports/2025-10-cli-flags/phase_k/f_latt_fix/per_phi/per_phi_c_20251006-151228.log anchors the C reference that every refreshed per-φ trace must match within Δk < 5e-4.
How-To Map:
- Environment prep:
  1. `export PYTHONPATH=src`
  2. `export KMP_DUPLICATE_LIB_OK=TRUE`
  3. Confirm `which python` matches the virtualenv used for previous CLI loops.
- Harness execution (creates the new trace + per-φ files):
  `PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --device cpu --dtype float32 --out trace_py_scaling_20251119.log`
  * Expected stdout banners: “Main trace written to …/trace_py_scaling_20251119.log” and “Captured 10 TRACE_PY_PHI lines”.
  * Harness automatically writes environment and config snapshots alongside the trace; retain them.
- Verify harness output immediately:
  * `rg "TRACE_PY_PHI" reports/2025-10-cli-flags/phase_l/per_phi/trace_py_scaling_20251119_per_phi.log`
  * `head -n 20 reports/2025-10-cli-flags/phase_l/per_phi/trace_py_scaling_20251119_per_phi.json`
- Per-φ comparison against C:
  `python scripts/compare_per_phi_traces.py reports/2025-10-cli-flags/phase_l/per_phi/trace_py_scaling_20251119_per_phi.json reports/2025-10-cli-flags/phase_k/f_latt_fix/per_phi/per_phi_c_20251006-151228.log > reports/2025-10-cli-flags/phase_l/per_phi/comparison_summary_20251119.md`
  * Validate the summary contains a table with φ_tic entries and Δk columns.
  * If the script complains about a missing `traces` key, adapt the JSON (rename `per_phi_entries` → `traces`) in a copy before rerunning; document any such adjustments in Attempt notes.
- Scaling-factor diff rerun:
  `KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling_20251119.log --out reports/2025-10-cli-flags/phase_l/scaling_validation/scaling_validation_summary_20251119.md`
  * Confirm metrics.json reports ≤1e-6 deltas for r_e²/fluence/steps/capture_fraction, and highlight the first divergent factor.
  * Inspect run_metadata.json to ensure git SHA, torch version, and command strings match today’s environment.
- pytest collection check before running the targeted test:
  `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics`
- Targeted pytest execution (should pass on first run):
  `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics -q`
  * Archive the stdout under `reports/2025-10-cli-flags/phase_l/per_phi/pytest_trace_pixel_20251119.log`.
- Documentation + attempt logging:
  * Append an Attempt entry to docs/fix_plan.md with command log snippets, artifact paths, delta metrics, and any schema adjustments.
  * Update `reports/2025-10-cli-flags/phase_l/scaling_validation/analysis_20251119.md` with a short “2025-11-19 refresh” paragraph summarising new findings.
Pitfalls To Avoid:
- Do not modify simulator physics or tracing logic; all work must occur via harness scripts.
- Keep tensors/device aligned—avoid accidental `.cpu()` conversions or dtype casts while handling traces.
- Ensure the harness prints “Captured 10 TRACE_PY_PHI lines”; if it prints zero, treat that as failure and debug capture rather than forcing success.
- Preserve historical artifacts by writing new files with the `20251119` suffix; do not overwrite `trace_py_scaling_20251117.log` or older JSONs.
- Maintain Protected Assets from docs/index.md (especially `loop.sh`, `supervisor.sh`, `input.md`).
- Re-run `compare_scaling_traces.py` only after confirming the new trace file exists; stale paths silently reuse older metrics.
- Include environment metadata (git SHA, torch version) in Attempt notes; missing metadata blocks plan closure.
- If you edit `compare_per_phi_traces.py` for schema compatibility, isolate the change to tooling (no production modules) and mention the diff explicitly.
- Watch for accidental removal of `TRACE_PY` lines when filtering stdout—per-φ extraction must be additive.
- Do not escalate to production code changes until per-φ parity evidence proves where the sign flip occurs.
- Respect vectorization constraints: no Python loops added inside simulator or harness code paths that would regress batching.
- Remember to keep randomness deterministic (no new RNG seeds) so traces stay comparable run-to-run.
Pointers:
- docs/fix_plan.md:460-616 — active status, attempts, and refreshed next actions.
- plans/active/cli-noise-pix0/plan.md:20-33,260-266 — Phase L3 context and updated L3e task guidance.
- reports/2025-10-cli-flags/phase_l/scaling_validation/analysis_20251119.md:1-41 — root-cause narrative for current mismatch.
- reports/2025-10-cli-flags/phase_l/per_phi/comparison_summary_20251119.md:1-120 — documentation of prior per-φ instrumentation.
- scripts/validation/compare_scaling_traces.py:1-320 — authoritative scaling diff implementation and thresholds.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:240-333 — harness logic that should emit `TRACE_PY_PHI` lines.
- reports/2025-10-cli-flags/phase_k/f_latt_fix/per_phi/per_phi_c_20251006-151228.log:1-200 — C reference trace for comparison.
- docs/development/testing_strategy.md:1-120 — device/dtype discipline reminders for targeted parity loops.
- docs/architecture/pytorch_design.md:200-320 — simulator scaling overview; keep notes ready for Phase L3f documentation sync.
- prompts/debug.md:1-180 — routing expectations for parity loops; stay within diagnostic mode guidance when capturing traces.
Reporting Checklist:
- Record exact commands, exit codes, and runtimes in Attempt notes; include whether CUDA was available even if unused.
- Summarise key numeric deltas (Δk first divergence, ΔF_latt, ΔI_before_scaling) in both docs/fix_plan.md and the refreshed summary markdowns.
- Attach SHA256 hashes for any regenerated `.log` / `.json` artifacts to ease future verification diffs.
- Update galph_memory.md excerpt (if requested) with one-line status once artifacts are captured, so supervisor context stays fresh.
- If schema adjustments were needed (e.g., JSON key rename), cite the patch location and intended follow-up clean-up.
Success Criteria:
- `trace_py_scaling_20251119.log` exists, contains latest git SHA in header, and matches the supervisor pixel selection (685,1039).
- `trace_py_scaling_20251119_per_phi.log` lists 10 `TRACE_PY_PHI` entries whose `phi_tic` span 0–9.
- `comparison_summary_20251119.md` reports Δk values and highlights the first φ divergence (or confirms parity if Δk < 5e-4 throughout).
- `metrics.json` shows `status="PASS"` for r_e², fluence, steps, capture_fraction, and records the first divergence field name explicitly.
- Targeted pytest selector succeeds on cpu/float32; no new warnings about missing TRACE output appear.
- docs/fix_plan.md attempt entry references the new artifact paths and refreshed metrics, keeping chronological numbering intact.
Evidence Storage Expectations:
- Place auxiliary stdout/stderr snippets under `reports/2025-10-cli-flags/phase_l/per_phi/logs/` if they exceed a few dozen lines; reference them from the Attempt note instead of inlining.
- Keep raw harness outputs (`*_raw.txt`) until supervisor confirmation, then either archive or delete per Protected Assets policy.
- Mirror directory structure between per_phi and scaling_validation so that future automation can diff timestamps programmatically.
- Note any manual edits (e.g., JSON schema tweaks) inside a short README within the same directory to aid future reproducibility.
- If a rerun is required, suffix additional artifacts with `_rerun1`, `_rerun2`, etc., instead of overwriting the `_20251119` baseline.
- Should comparisons require temporary tooling patches, commit them on a scratch branch or stash, but document the diff hash in Attempt notes.
- Ensure timestamps in JSON outputs use UTC (`datetime.utcnow().isoformat() + 'Z'`) to maintain consistency with earlier artifacts.
- Back up the new artifacts to `reports/archive/` once parity work is complete; note relocation in fix_plan before closing the item.
Verification Notes:
- When inspecting `trace_py_scaling_20251119.log`, confirm the ordering of `TRACE_PY:` lines matches the C trace (pix0_vector → fdet_vec → … → I_pixel_final) to ensure harness capture was lossless.
- Cross-check `trace_py_scaling_20251119_per_phi.json` against the log to verify every entry appears in both files and that numeric formatting uses full precision.
- Re-run `rg "F_latt"` across both PyTorch and C traces to highlight sign differences before drafting the Attempt summary.
- If Δk remains ≈6 units after refreshing per-φ traces, flag this explicitly—the earlier MOSFLM rescale fixes should have collapsed that gap.
- Keep a scratch pad of intermediate calculations (e.g., manual sincg evaluation) under `reports/2025-10-cli-flags/phase_l/per_phi/notes_20251119.md` for rapid follow-up during Phase L3f.
- Share any anomalies (missing lines, unexpected zeroes) before touching production modules; the supervisor will decide on next investigative steps.
Next Up: Once per-φ parity is confirmed, inspect `_compute_structure_factor_components` to reconcile F_latt accumulation order, document findings in Phase L3f, and prepare the nb-compare rerun for Phase L4.
