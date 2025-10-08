Summary: Capture the Phase M4d parity evidence bundle so the CLI-FLAGS-003 normalization fix is backed by current traces, metrics, and ledger updates.
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests:
- pytest --collect-only -q tests/test_cli_scaling_phi0.py
- python -m pytest --collect-only tests/test_suite.py::TestTier1TranslationCorrectness::test_cli_scaling_trace_cpu
- (Do not execute targeted pytest or CUDA runs this loop; collect-only logs satisfy evidence requirements.)
Artifacts:
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/trace_py_scaling.log
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/compare_scaling_traces.txt
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/compare_scaling_traces.md (optional pretty version if you prefer markdown extension)
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/metrics.json
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/run_metadata.json
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/diff_trace.md
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/commands.txt (append new steps)
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/pytest_collect.log
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/env.json (update only if versions changed)
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/sha256.txt (refreshed after edits)
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/summary_pre_refresh.md (optional backup)
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md (Hypothesis H4 closure)
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/sha256.txt (refreshed after edit)
- reports/2025-10-cli-flags/phase_l/scaling_validation/scaling_validation_summary.md (updated if compare script regenerates global summary)
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/trace_py_scaling.log (reference path cited in documentation)
- docs/fix_plan.md (Attempt #190 entry with artifact pointers)
- galph_memory.md (add short note if new findings emerge)
Do Now: CLI-FLAGS-003 Phase M4d — KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --out reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/
If Blocked: Record the failing command and stderr in fix_20251008T223805Z/blockers.md, refresh sha256.txt, run pytest --collect-only -q tests/test_cli_scaling_phi0.py, append the blocker context to docs/fix_plan.md, and pause for supervisor guidance.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:60-79 keeps Phase M4 flagged [P] until M4d artifacts land; completing this unblocks Phase M5.
- docs/fix_plan.md:466-520 now call for compare_scaling_traces outputs, diff trace narrative, and hypotheses closure before CUDA/gradcheck work resumes.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/summary.md documents Attempts #188-#189 and explicitly requests the trace refresh and diff summary you will capture.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/c_trace_scaling.log is the canonical C trace; pairing it with the new Py trace keeps the comparison authoritative.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/metrics.json codifies the -14.6% deficit we expect to eliminate.
- galph_memory.md (2025-12-16 entry) identifies Phase M4d evidence as the last blocker before CUDA smoke tests; closing it keeps long-term goal #1 on track.
- plans/active/vectorization.md remains gated on CLI parity; finishing M4d removes that dependency so long-term goal #3 can proceed when scheduled.
- specs/spec-a-core.md:247-254 codifies the single-division normalization rule; parity metrics must reflect a null divergence to show compliance.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/commands.txt needs today’s command history appended prior to checksum refresh so the bundle remains reproducible.
- reports/2025-10-cli-flags/phase_l/scaling_validation/scaling_validation_summary.md should be refreshed if the compare script regenerates the consolidated markdown.
- prompts/supervisor.md references the CLI parity workflow; updated evidence ensures future loops cite current artifacts instead of stale bundles.
- plans/archive/cli-phi-parity-shim/plan.md remains as historical context; this evidence demonstrates the spec-only rotation path is now validated.
How-To Map:
- Prepare fix_20251008T223805Z/: ensure it is writable; copy summary.md to summary_pre_refresh.md if you want a before/after snapshot.
- Execute the Do Now harness command (CPU float64) so trace_py_scaling.log reflects commit fe3a328 with the corrected normalization path.
- Run compare_scaling_traces:
  python scripts/validation/compare_scaling_traces.py \
    --c reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/c_trace_scaling.log \
    --py reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/trace_py_scaling.log \
    --out reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/compare_scaling_traces.txt
- Inspect compare_scaling_traces.txt and metrics.json; if any factor remains divergent, capture the offending rows in diff_trace.md and halt for supervisor input.
- Draft diff_trace.md summarising the comparison, explicitly calling out that first_divergence is None once confirmed.
- Append the harness and compare commands (with timestamps) to commands.txt before recalculating sha256.txt.
- Update summary.md with a short Phase M4d addendum referencing the new trace, metrics files, and diff summary.
- Update reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md by closing Hypothesis H4 and citing the new compare_scaling_traces output.
- Refresh sha256.txt in fix_20251008T223805Z/ after all new files are staged.
- Refresh sha256.txt in 20251008T075949Z/ after editing lattice_hypotheses.md.
- Re-run pytest discovery: pytest --collect-only -q tests/test_cli_scaling_phi0.py | tee reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/pytest_collect.log
- Run python -c "import json, sys, torch; print(json.dumps({'python': sys.version, 'torch': torch.__version__, 'device': 'cpu', 'dtype': 'float64'}, indent=2))" and append the result to env.json if versions differ from the previous snapshot.
- If plan requires, regenerate scaling_validation_summary.md using the new compare output so downstream analysis stays aligned.
- Update docs/fix_plan.md with Attempt #190 (metrics, artifact paths, next steps) and note that Phase M5 moves to CUDA + gradcheck evidence.
- Add a short note to galph_memory.md confirming Phase M4d completion or documenting any blocker discovered.
- Capture git metadata for run_metadata.json: git rev-parse HEAD >> run_metadata.json if the script did not capture the correct SHA.
- Take a quick `ls -R` listing within fix_20251008T223805Z/ and stash it as dir_listing.txt if you add new files; this aids future audits.
Pitfalls To Avoid:
- Do not touch the spec_baseline directory beyond reading inputs; preserve historical evidence intact.
- Keep the harness run on CPU float64 to match the reference C trace values; no CUDA for this loop.
- Avoid modifying simulator or other production modules; this is an evidence-only iteration.
- Always set PYTHONPATH=src when invoking the harness or comparison script to prevent import drift.
- Refresh sha256.txt after every new file or modification; stale checksums invalidate the bundle.
- Maintain the Protected Assets list in docs/index.md; do not rename or remove any protected files.
- Capture complete command output in commands.txt, including ENV variables, so the bundle is reproducible.
- Do not introduce .cpu()/.item() calls in any helper edits; maintain device/dtype neutrality.
- Append new sections to summary.md instead of rewriting prior analysis to preserve historical context.
- Treat compare_scaling_traces divergences as blocking; stop and escalate rather than editing values by hand.
- Keep blockers.md updated if anything fails so future loops inherit accurate context.
- Preserve existing trace files; add new ones alongside rather than overwriting unless required by the script.
- Leave reports permissions unchanged; they are shared for future audits.
- Skip CUDA execution and targeted pytest until Phase M5 explicitly directs those checks.
- Do not edit archived plan files; all updates belong in active plan traces.
- Double-check commands.txt for chronological order; do not reorder historical entries.
Pointers:
- plans/active/cli-noise-pix0/plan.md:60-86 (Phase M4 checklist and guidance)
- docs/fix_plan.md:466-520 (Next Actions and Attempts log for CLI-FLAGS-003)
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/summary.md
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/commands.txt
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/commands.txt
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md
- reports/2025-10-cli-flags/phase_l/scaling_validation/scaling_validation_summary.md
- specs/spec-a-core.md:247-254
- galph_memory.md (latest supervisor notes on Phase M4 status)
- prompts/supervisor.md (CLI parity workflow references)
Next Up: After this Phase M4d bundle is green, advance to Phase M5 (CUDA parity + gradcheck reruns) per plans/active/cli-noise-pix0/plan.md:87-96.
Notes:
- After finishing, run git status to ensure only documentation/report files changed; no code edits expected.
- Capture git diff of docs/fix_plan.md and plans/active/cli-noise-pix0/plan.md for supervisor review if requested.
- If you create temporary files (e.g., intermediate diffs), remove them before refreshing sha256 manifests.
- Leave a breadcrumb in commands.txt when you regenerate any file so future loops know why timestamps changed.
- Ping supervisor if compare_scaling_traces reports divergence despite code fix; do not attempt further changes solo.
- Add report paths to Attempt #190 in chronological order (M1 baseline -> M4d fix).
- Update commands.txt end marker with a blank line so future entries stay separated.
