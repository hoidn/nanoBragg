Summary: Generate up-to-date c-parity scaling traces so Phase M1 can confirm the I_before_scaling gap with the current harness and unblock lattice-factor fixes.
Mode: Parity
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests:
- pytest tests/test_phi_carryover_mode.py::TestPhiCarryoverBehavior::test_c_parity_mode_stale_carryover
- pytest --collect-only -q tests/test_cli_scaling_phi0.py
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/summary.md; reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling_cpu.log; reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/metrics.json; reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/commands.txt; reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/sha256.txt; reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/env.json (optional but strongly encouraged)
Do Now: CLI-FLAGS-003 Phase M1 — run reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py for pixel (685,1039) in c-parity mode on CPU float32, compare against the C trace at 1e-6 tolerance, and capture the full evidence package under a fresh timestamp directory.
If Blocked: Preserve the failure by running the comparison anyway, archive summary.md + metrics.json + commands.txt + sha256.txt (and env.json if captured), note the blocker (e.g., delta still 21.9% or harness regression) inside summary.md, and log a docs/fix_plan.md Attempt referencing the new timestamp so we can triage next loop.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:46-56 keeps Phase M1 as the first gate before normalization work; fresh traces are prerequisite evidence.
- docs/fix_plan.md:484-507 mandates rerunning the harness with the phi-carryover shim after instrumentation; the new data has not been captured yet.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T043438Z/summary.md shows the stale 21.9% gap predating the --phi-mode flag; acting on outdated data risks misdiagnosis.
- docs/bugs/verified_c_bugs.md:166-191 clarifies C’s φ₀ carryover bug; parity investigations must therefore run in c-parity mode to stay aligned with the reference binary.
- specs/spec-a-core.md:204-248 reiterates the normative φ rotation pipeline; spec compliance remains the default mode and c-parity is validation-only.
- docs/development/testing_strategy.md:40-90 emphasises evidence-first workflows and device/dtype neutrality, reinforcing why we capture metrics before editing code.
- Long-term goal #1 (supervisor parity command) depends on driving this delta to ≤1e-6; without updated traces we cannot monitor progress toward that milestone.
- The harness and validation scripts already exist; this loop is about producing authoritative artifacts that will guide Phase M2 without guesswork.
- Fresh evidence also sanity-checks that the phi-mode plumbing works on the current git SHA and that no regressions crept in.
- Keeping evidence current simplifies future audits, especially when documenting Attempt entries and updating fix_checklist.md.
- Accurate metrics let us decide whether the fix belongs in lattice factor propagation, accumulation loops, or elsewhere.
- The timestamped artifact set continues the reproducibility story required by docs/fix_plan.md Attempts and downstream nb-compare runs.
How-To Map:
- Step 0: export KMP_DUPLICATE_LIB_OK=TRUE to avoid MKL loader conflicts before importing torch.
- Step 1: TS=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2025-10-cli-flags/phase_l/scaling_validation/$TS to isolate the new evidence set.
- Step 2: Optional guard — pytest --collect-only -q tests/test_cli_scaling_phi0.py so selector drift is caught before running longer commands.
- Step 3: Record git SHA via git rev-parse HEAD and stash it in a temporary note; metrics.json should include it.
- Step 4: Capture current branch (git branch --show-current) and working tree status (git status -sb) for env.json completeness.
- Step 5: PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --device cpu --dtype float32 --phi-mode c-parity --out reports/2025-10-cli-flags/phase_l/scaling_validation/$TS/trace_py_scaling_cpu.log
- Step 6: Immediately append the exact harness command, timestamp, and pwd into commands.txt (printf '...\n' >> .../commands.txt) so provenance stays accurate.
- Step 7: Save raw stderr/stdout if the harness emits warnings (e.g., tee the output into trace_py_scaling_cpu.log alongside the --out file).
- Step 8: Capture environment metadata using python - <<'PY' import json, torch, platform; print(json.dumps({"python":platform.python_version(),"torch":torch.__version__,"cuda_available":torch.cuda.is_available(),"git_sha":"$SHA","branch":"$BRANCH"}, indent=2)) PY > env.json
- Step 9: PYTHONPATH=src python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_validation/$TS/trace_py_scaling_cpu.log --out reports/2025-10-cli-flags/phase_l/scaling_validation/$TS/summary.md --tolerance 1e-6
- Step 10: Review summary.md for per-field deltas; highlight whether first divergence remains "I_before_scaling" and note any change in relative delta.
- Step 11: Construct metrics.json capturing key scalars (hkl_frac components, F_cell, F_latt parts, I_before_scaling_C, I_before_scaling_Py, relative_delta, steps, oversample, mosaic_domains, sources, first_divergence, command_hash).
- Step 12: Add optional per-φ trace: if TRACE_PY_PHI lines exist, copy them to trace_py_scaling_cpu_per_phi.log and include in sha256.txt.
- Step 13: Within the timestamp directory run shasum -a 256 * > sha256.txt so each artifact gains a checksum for reproducibility.
- Step 14: Run pytest tests/test_phi_carryover_mode.py::TestPhiCarryoverBehavior::test_c_parity_mode_stale_carryover and capture the exit status; add the command to commands.txt.
- Step 15: If time allows, run pytest --maxfail=1 --disable-warnings -q tests/test_cli_scaling_phi0.py::TestScalingParity::test_spec_mode_identity to ensure spec mode remains green (optional but nice to have).
- Step 16: Verify the timestamp directory lists at minimum: trace_py_scaling_cpu.log, summary.md, metrics.json, commands.txt, sha256.txt, env.json (optional), trace_py_scaling_cpu_per_phi.log (optional).
- Step 17: Do not edit docs/fix_plan.md yet; note bullet summaries for later (delta, first divergence, interesting observations).
- Step 18: Once artifacts look complete, consider diffing summary.md against the 20251008 baseline to spot improvements/regressions quickly.
- Step 19: Leave the working tree unchanged aside from reports/ additions so git status stays predictable for the supervisor.
- Step 20: Back up the TS path in case we need to reference it during handoff (e.g., echo $TS for future Attempt number).
- Step 21: Skim reports/2025-10-cli-flags/phase_l/scaling_audit/README.md (if present) to confirm no additional harness options are required.
- Step 22: Update commands.txt with the pytest commands (collect-only and targeted run) so the full command history is preserved.
- Step 23: Double-check that metrics.json lists units (e.g., Angstrom^-1, photons) where applicable to avoid ambiguity.
- Step 24: Snapshot the relative path to the timestamp directory in summary.md so later loops can jump straight to the evidence.
- Step 25: Leave a TODO comment at the end of summary.md (e.g., "TODO Phase M2: investigate accumulation order") to remind future loops of the immediate follow-up.
Pitfalls To Avoid:
- Avoid rerunning the entire pytest suite; stay with the mapped selectors to conserve time and comply with plan guidance.
- Do not alter production code, harness code, or validation helpers—this loop is evidence-only.
- Resist tweaking compare_scaling_traces.py tolerance; 1e-6 is mandatory per Phase M exit criteria.
- Never overwrite or delete historical directories (e.g., 20251008T043438Z); always create a new timestamp.
- Keep tensor flows device-neutral; avoid injecting .cpu()/.cuda() calls in ad-hoc diagnostics.
- Ensure commands.txt mirrors the actual execution order; missing steps complicate later audits.
- Capture stderr if the harness throws warnings or exceptions; include the log in the timestamp folder.
- Do not forget sha256.txt; fix_plan entries rely on checksums for reproducibility.
- Maintain ASCII in summary.md, metrics.json, and commands.txt unless a referenced artifact already uses Unicode.
- Preserve Protected Assets (docs/index.md, loop.sh, supervisor.sh, input.md) exactly as-is.
- Defer nb-compare, Phase M2 code edits, or vectorization work until this evidence loop is complete.
- Skip GPU or float64 experiments for now; Phase M1 explicitly targets CPU float32 evidence parity.
- Avoid running extra harness configurations (spec mode, CUDA) in this loop; focus on the one ROI to keep analysis sharp.
- Make sure env.json includes python, torch, CUDA availability, git SHA, and branch so future comparisons have context.
- Double-check that metrics.json uses consistent key casing to simplify downstream parsing.
- Remember to add newline at EOF for each text artifact; git diffs become cleaner and consistent.
- If you spot unusual values, jot them in summary.md immediately—memory fades fast after the run.
- When computing sha256.txt, ensure you run it in the timestamp directory so relative filenames stay correct.
- Keep the working tree otherwise clean; evidence-only loops should not add unrelated files.
- Do not forget to export KMP_DUPLICATE_LIB_OK=TRUE in every shell where you invoke torch programs.
Pointers:
- plans/active/cli-noise-pix0/plan.md:46-56 — Phase M goals, prerequisites, exit criteria, and task checklist that this loop feeds.
- docs/fix_plan.md:484-507 — Previous scaling attempt analysis plus prescribed follow-up actions.
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:260-320 — Canonical C trace for the supervisor ROI.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T043438Z/summary.md:1-40 — Historical PyTorch summary showing the 21.9% I_before_scaling discrepancy.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T043438Z/metrics.json:1-80 — Example structure for metrics.json keys/values.
- docs/bugs/verified_c_bugs.md:166-191 — φ carryover bug description and parity-mode tolerances to match.
- scripts/validation/compare_scaling_traces.py:1-220 — CLI usage and expectation for 1e-6 tolerance comparisons.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:40-210 — Harness options (including --phi-mode) and logging taps.
- specs/spec-a-core.md:204-248 — Normative φ rotation pipeline to keep spec mode straight.
- docs/development/pytorch_runtime_checklist.md:1-140 — Vectorization & device discipline checklist to remain compliant.
- reports/2025-10-vectorization/phase_e/pytest_cpu.log:1-120 — Example of fully captured CPU test evidence for future loops.
- reports/2025-10-vectorization/phase_e/pytest_cuda.log:1-120 — GPU counterpart; useful template for how to format logs when CLI-FLAGS reaches GPU smoke.
- docs/fix_plan.md:2621-2680 — [VECTOR-TRICUBIC-001] status for awareness when scheduling subsequent work.
- docs/development/c_to_pytorch_config_map.md:1-120 — Parameter parity references when verifying harness inputs.
- reports/2025-10-cli-flags/phase_l/per_phi/trace_py_c_parity_per_phi.log:1-200 — Prior per-φ trace showing expected c-parity values.
Next Up:
- Phase M2 lattice-factor propagation fix using the freshly captured evidence to target the accumulation bug.
- Phase M3 rerun of scaling comparisons on CPU and CUDA after the fix to confirm ≤1e-6 relative error across devices.
- Phase M4 documentation updates (fix_checklist.md VG-2 row, docs/fix_plan Attempt) once metrics turn green.
- Vectorization plan Phase E2/E3 (microbenchmarks + parity summary) once CLI-FLAGS-003 Phase M metrics fall within tolerances.
- Begin planning for Phase N nb-compare runs after scaling parity succeeds, incorporating nb-compare guidance in docs/development/testing_strategy.md.
- Log the new evidence under docs/fix_plan.md with Attempt details so the ledger reflects progress, then queue the Phase M2 implementation change.
- Circulate a brief update in galph_memory.md summarising the evidence outcome and whether it affects other initiatives (e.g., vectorization timing).
- Add a note to summary.md clarifying whether the comparison was run before or after any `torch.set_printoptions` changes, to aid reproducibility.
- Keep watch for environment drift (e.g., different torch versions); if detected, mention it explicitly in metrics.json.
- Ensure summary.md states explicitly whether c-parity mode was used so future readers do not assume spec mode.
- Keep watch for environment drift (e.g., different torch versions); if detected, mention it explicitly in metrics.json.
- Verify metrics.json numbers twice before saving; typos propagate quickly into fix_plan entries.
