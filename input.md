Summary: Restore the CLI scaling trace harness so Phase L2b captures live TRACE_PY output for the supervisor command again, clearing the Attempt #70 blocker and unfreezing the normalization analysis queue.
Mode: Parity
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm (Phase L2b)
Branch: feature/spec-based-2
Mapped tests: tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log, reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_env.json, reports/2025-10-cli-flags/phase_l/scaling_audit/notes.md
Do Now: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm (Phase L2b) → KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --out trace_py_scaling.log (after fixing the harness to consume read_hkl_file’s (F_grid, metadata) return)
If Blocked: Capture the current failure (`ValueError: not enough values to unpack`) into Attempt History, stash stdout/stderr under reports/2025-10-cli-flags/phase_l/scaling_audit/, and describe why the metadata reconstruction could not be completed.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:90-126 — The L2b row explicitly requires adapting the harness to the new HKL API before any comparison work can resume; skipping this leaves Phase L stalled.
- plans/active/cli-noise-pix0/plan.md:128-220 — Downstream tasks (L2c–L3) depend on real TRACE_PY numbers; completing them without this fix would be speculative.
- docs/fix_plan.md:458-476 — The fix plan records L2b as open and targets the harness update as the first actionable step.
- docs/fix_plan.md:477-484 — Attempt #70 documents the present failure and demands a rerun with live values before progressing.
- tests/test_trace_pixel.py:22-120 — Regression coverage that enforces non-placeholder TRACE_PY output; keep it green throughout refactoring.
- docs/development/testing_strategy.md:1-140 — Tier-1 parity workflow and supervisor handoff expectations; use it to justify the targeted command set.

How-To Map:
- Step 1 — Adjust HKL loading in reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py.
  - Replace the old `F_grid, h_range, ... l_min` unpacking with `F_grid, metadata = read_hkl_file(...)`.
  - Extract `h_min`, `k_min`, `l_min`, `h_range`, `k_range`, `l_range` from the metadata dict.
  - Ensure the returned tensor is moved to the requested `device` and `dtype` before it is assigned to the crystal.
  - Preserve default_F semantics; any missing metadata entries should fallback to plan-documented values, but the new loader should have all keys populated.
- Step 2 — Rehydrate the crystal with the loaded HKL grid.
  - Assign `crystal.hkl_data = F_grid_tensor` and `crystal.hkl_metadata = metadata`.
  - Mirror the CLI path by recording `crystal.h_min`, `crystal.h_max`, etc., if the harness currently expects them.
  - Confirm that no `.cpu()` leaks occur when moving tensors; rely on `.to(device=device, dtype=dtype)`.
- Step 3 — Audit environment and argument flow before running.
  - Set `os.environ['KMP_DUPLICATE_LIB_OK']='TRUE'` prior to torch import to avoid MKL collisions.
  - Honor CLI-style overrides for dtype/device; thread them through the harness entrypoints so the captured trace matches the parity command.
  - Keep the pixel coordinate `(685, 1039)` consistent with the supervisor command and Phase L evidence trail.
- Step 4 — Execute the harness with stdout capture once code compiles.
  - Run `KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --out trace_py_scaling.log`.
  - Expect tensor values for `I_before_scaling`, `polar`, `capture_fraction`, `omega_pixel`, and `I_pixel_final` to appear in the log.
  - Check the console summary for the final intensity so you know the simulator returned successfully.
- Step 5 — Archive updated artifacts for parity review.
  - Replace `trace_py_scaling.log` only after saving a backup of the failing run (keep timestamps distinct).
  - Refresh `trace_py_env.json` and `notes.md` with the new timestamp, git SHA, and summary observations.
  - Keep `trace_py_fullrun.log` in place as evidence of the regression, but append the new successful command to `run_pytorch_trace.sh` if invocation changed.
- Step 6 — Validate tooling and tests.
  - Run `pytest --collect-only -q tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics` to ensure the selector remains discoverable.
  - Optionally execute the test itself after refactor if runtime permits; report any failures immediately.
  - Once the trace is live, execute `KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --c-log reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py-log reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log --out reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md` to resume Phase L2c.
- Step 7 — Log the outcome.
  - Add a fresh Attempt entry to docs/fix_plan.md summarizing the rerun, metrics, and artifacts.
  - Note any remaining divergences so the next supervisor pass can focus on normalization deltas rather than tooling gaps.

Validation Checklist:
1. trace_harness.py executes without raising `ValueError` and prints the pixel intensity summary.
2. reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log lists non-zero physics values (`I_before_scaling`, `polar`, `capture_fraction`).
3. reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_env.json captures the new timestamp and git SHA.
4. reports/2025-10-cli-flags/phase_l/scaling_audit/notes.md documents the rerun context and command line used.
5. pytest --collect-only -q tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics succeeds.
6. New Attempt entry committed to docs/fix_plan.md with artifact links.
7. scripts/validation/compare_scaling_traces.py produces an updated scaling_audit_summary.md (once live values exist).

Pitfalls To Avoid:
- Do not migrate tensors through numpy; keep all intermediate calculations in torch to preserve gradients and device placement.
- Avoid reinstating placeholder strings such as `NOT_EXTRACTED`; they invalidate both the regression test and parity evidence.
- Keep protected assets from docs/index.md untouched (input.md, loop.sh, supervisor.sh, etc.) in accordance with the Protected Assets rule.
- Respect pix0 precedence rules from Phase H; the harness should consume Detector output, not apply its own overrides.
- Refrain from introducing per-pixel Python loops or other de-vectorized paths when manipulating trace data.
- Ensure exceptions propagate; swallowing stack traces would undermine reproducibility of future failures.
- Retain previous evidence files; rename with date suffixes if necessary instead of deleting them.
- Preserve device/dtype neutrality; leverage `.to()` rather than hard-coding `.cpu()` or `.cuda()`.
- Keep run scripts (run_pytorch_trace.sh) and README notes synchronized with any new flags or parameters you introduce.
- Update docs/fix_plan.md immediately after gathering evidence; missing bookkeeping slows future supervision.

Pointers:
- plans/active/cli-noise-pix0/plan.md:38-220 — Phase tables covering the full CLI parity effort and detailed L2 guidance.
- docs/fix_plan.md:458-484 — Reopened L2b action items plus the recorded Failure (Attempt #70) that this loop must resolve.
- docs/development/testing_strategy.md:1-140 — Authoritative references for parity commands and supervisor/engineer test cadence.
- tests/test_trace_pixel.py:22-120 — Scaling trace regression expectations; use them to confirm instrumentation remains live.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_fullrun.log — Current failure stack trace for reference while patching.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling_refreshed.log — Placeholder-laden output that must disappear after the fix.
- docs/development/c_to_pytorch_config_map.md:1-120 — Parameter parity reference to ensure no unintended CLI drift occurs while editing the harness.
- docs/architecture/detector.md:1-200 — Detector geometry specification; helpful if live traces reveal new pix0 nuances post-fix.
- scripts/validation/compare_scaling_traces.py:1-250 — Comparison tool you will run immediately after restoring live TRACE_PY data.

Next Up: After the harness produces live values, rerun scripts/validation/compare_scaling_traces.py, document the first divergent factor in scaling_audit_summary.md, update docs/fix_plan.md with the comparison results, and hand back to supervision for Phase L2c sign-off.

Command Snippets:
- `KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --out trace_py_scaling.log`
- `pytest --collect-only -q tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics`
- `KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --c-log reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py-log reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log --out reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md`
- `git diff reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py`
- `git add reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py docs/fix_plan.md` (after evidence logging)
- `git commit -m "CLI-FLAGS-003: refresh scaling harness"` (adjust message once work is complete)

Notes:
- Keep an eye on F_cell values in the refreshed trace; if they remain zero we may need to revisit crystal orientation before normalization fixes.
- Update Attempt History with exact SHA256 hashes of the new trace and environment files to simplify future audits.
- If CUDA is unavailable on this machine, document the limitation in notes.md so the next loop knows why GPU runs were skipped.
- Should the harness require additional helper utilities, place them within the reports/2025-10-cli-flags/phase_l/scaling_audit/ directory to avoid polluting src/.
- Remember to push evidence to origin once supervisor review closes; clean branches make async iteration easier.
- If the harness still fails after API changes, capture the full traceback and a short reproduction note under reports/2025-10-cli-flags/phase_l/scaling_audit/failure_logs/ for archival.
- Ping the supervisor in Attempt History if additional upstream fixes (outside the harness) appear necessary; do not proceed into Phase L2c without alignment.
- Double-check docs/index.md after edits to confirm no protected artifacts were moved; acknowledge compliance in notes.md for transparency.
- Capture `git status -sb` output into the notes after work completes; it helps future loops see repository cleanliness instantly.
- Record time spent on the rerun in notes.md; future perf investigations rely on these breadcrumbs.
