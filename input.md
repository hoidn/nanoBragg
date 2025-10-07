Summary: Capture the PyTorch scaling trace for the supervisor command so we can diff against C and locate the normalization divergence.
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm — Phase L2 scaling audit
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts:
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_stdout.txt
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_stderr.txt
- reports/2025-10-cli-flags/phase_l/scaling_audit/config_snapshot.json
- reports/2025-10-cli-flags/phase_l/scaling_audit/notes.md
- reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md
- reports/2025-10-cli-flags/phase_l/scaling_audit/compare_scaling_traces.json
Do Now: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm — Phase L2 scaling audit — PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --out reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log > reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_stdout.txt 2> reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_stderr.txt && pytest --collect-only -q tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics
If Blocked: Capture stdout/stderr into reports/2025-10-cli-flags/phase_l/scaling_audit/attempt_failed.log, append the traceback plus command line to notes.md, stash git diff under reports/.../trace_harness_blocker.patch, and pause for supervisor guidance.
Priorities & Rationale:
- docs/fix_plan.md:237 keeps Phase L2 open until TRACE_PY mirrors the C scaling factors.
- plans/active/cli-noise-pix0/plan.md:232 spells out L2b step 3 (harness rerun) before L2c analysis.
- docs/debugging/debugging.md:24 mandates the parallel trace workflow we are completing.
- arch.md:216 reminds us the final intensity chain is r_e² · fluence · I / steps × (polar · ω · capture), so each factor must be logged accurately.
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:1 holds the ground-truth values we must match.
How-To Map:
- Run the Do Now command from the repo root so the harness finds A.mat, scaled.hkl, and img.bin in-place.
- Inspect reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_stderr.txt; if non-empty, summarize the issue in notes.md before retrying.
- Verify the new trace contains `TRACE_PY: steps`, `polar`, `capture_fraction`, and `omega_pixel` with non-placeholder values by grepping the log (e.g., `rg 'TRACE_PY: (steps|polar|capture_fraction|omega_pixel)' .../trace_py_scaling.log`).
- Generate a quick comparison skeleton by running `python - <<'PY'` to extract the C/Py values for I_before_scaling, steps, omega, polar, capture_fraction, r_e_sqr, and fluence, then write a Markdown table to scaling_audit_summary.md; store the parsed numbers in compare_scaling_traces.json for reuse in L2c.
- Update reports/2025-10-cli-flags/phase_l/scaling_audit/notes.md with the command used, git SHA, key deltas, and whether the first divergence appears prior to F_latt or downstream.
- Confirm the pytest selector in Do Now completes (collect-only) to ensure the new regression guard still imports cleanly; attach the short log to notes.md if it exposes warnings.
Pitfalls To Avoid:
- Do not modify production code or docs during this evidence pass.
- Keep `trace_pixel` ordering as (slow, fast); the harness already encodes this expectation.
- Ensure PYTHONPATH=src and KMP_DUPLICATE_LIB_OK=TRUE are set together to avoid MKL crashes and import misses.
- Avoid rerunning the full pytest suite; stay within evidence-scope commands.
- Preserve existing artifacts (c_trace_scaling.log, instrumentation_notes.md); do not overwrite without archival copies.
- Work from the repo root so relative paths in trace_harness.py stay valid.
- Respect Protected Assets; do not touch docs/index.md or input.md outside this memo.
- Do not rerun nb-compare yet; gather trace evidence first.
- Keep device/dtype neutrality—if you spot device-specific values in the trace, note them but don’t coerce tensors via `.cpu()`.
Pointers:
- docs/fix_plan.md:239
- plans/active/cli-noise-pix0/plan.md:239
- docs/debugging/debugging.md:24
- arch.md:216
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:1
Next Up: Phase L2c — build compare_scaling_traces.py to diff the C/Py logs once the new trace lands.
