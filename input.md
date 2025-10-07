Summary: Instrument TRACE_PY to emit the real C-matching scaling factors so the supervisor command parity run can progress.
Mode: Parity
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_trace_pixel.py::test_scaling_trace_matches_physics (collect-only)
Mapped tests: tests/test_cli_scaling.py::test_f_latt_square_matches_c (reference selector, do not rerun yet)
Mapped tests: pytest --collect-only -q tests/test_trace_pixel.py::test_scaling_trace_matches_physics (after authoring the test)
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_env.json
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/harness_run.log
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/notes.md
Artifacts: reports/2025-10-cli-flags/phase_j/trace_c_scaling.log (C baseline keep in view)
Do Now: CLI-FLAGS-003 — Implement TRACE_PY scaling instrumentation, author tests/test_trace_pixel.py::test_scaling_trace_matches_physics, then run `pytest --collect-only -q tests/test_trace_pixel.py::test_scaling_trace_matches_physics`
Do Now: Ensure new trace fields exactly match C naming (`TRACE_PY: I_before_scaling ...`, `TRACE_PY: polar ...`, etc.) before logging attempt updates
If Blocked: Capture updated per-φ traces via `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/trace_per_phi.py --outdir reports/2025-10-cli-flags/phase_k/f_latt_fix/per_phi/blocked__$(date +%Y%m%d-%H%M%S)` and log findings in scaling_audit_summary.md
If Blocked: Document the blocker in docs/fix_plan.md Attempt history with timestamp + pointer, then pause coding changes
Priorities & Rationale:
- docs/fix_plan.md:448-462 marks Phase L2b instrumentation as the blocking step before normalization fixes
- docs/fix_plan.md:457 describes the k_frac≈−9.899 vs −3.857 delta that still needs first divergence evidence
- plans/active/cli-noise-pix0/plan.md:12-16 records placeholder TRACE_PY output after the latest harness run and the requirement to expose real tensors
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log currently prints `I_before_scaling NOT_EXTRACTED` and `polar 0`, underscoring missing instrumentation
- reports/2025-10-cli-flags/phase_j/trace_c_scaling.log lines 183-203 provide the exact C-side values to mirror
- reports/2025-10-cli-flags/phase_l/scaling_audit/harness_run.log notes the zero final intensity for pixel (685,1039), confirming the normalization gap
- reports/2025-10-cli-flags/phase_l/scaling_audit/config_snapshot.json verifies beam/flux/oversample flags now flow correctly after Attempt #66
- scripts/trace_per_phi.py:37-117 shows geometry assumptions (pix0 subtraction, spindle axis) that must stay in sync with Simulator logic
- specs/spec-a-cli.md (via docs/index.md) enforces that CLI flags like -nonoise and -pix0_vector_mm follow C precedence; normalization evidence must respect that contract
- docs/development/testing_strategy.md:74-112 reiterates that parity evidence must precede performance tweaks; stay aligned with the tiered strategy
- docs/development/c_to_pytorch_config_map.md:16-40 keeps the pivot + beam defaults authoritative; instrumentation changes must not violate those mappings
How-To Map:
- Edit `src/nanobrag_torch/simulator.py` within the TRACE_PY block to reuse `_apply_polarization` outputs and the absorption capture tensor; avoid recomputation
- Thread the tensors through existing debug structures (e.g., `debug_values`) rather than creating new global state
- Confirm the instrumentation path is still gated by `trace_pixel` flags to prevent perf regressions during normal runs
- After code updates, run `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --out reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log --device cpu --dtype float32` to refresh TRACE_PY output
- Check stdout/stderr in `harness_run.log`; archive the new run under a timestamped subdir if multiple iterations are needed
- Compare traces via `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log --out reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md`
- When the regression test is authored, confirm collection with `pytest --collect-only -q tests/test_trace_pixel.py::test_scaling_trace_matches_physics` (no execution yet in evidence mode)
- Update docs/fix_plan.md Attempts with metrics (fluence, steps, polar, omega) immediately after capturing new evidence
- If CUDA smoke is desired later, mirror the harness command with `--device cuda --dtype float32` once CPU path is green
- Keep edits focused: instrumentation + regression test + plan updates; defer normalization implementation to Phase L3
Pitfalls To Avoid:
- Do not detach tensors with `.item()` or `.cpu()`; maintain gradient paths for future gradchecks
- Avoid duplicating physics logic inside the trace; reference the production tensors per CLAUDE Rule #8
- No new Python loops over pixels or φ; preserve vectorization guarantees in simulator
- Respect Protected Assets listed in docs/index.md (input.md, loop.sh, supervisor.sh, etc.) when moving files
- Do not overwrite existing reports; create timestamped copies or append sections
- Ensure nb-compare tooling remains untouched this loop; focus on trace capture first
- Refrain from running the full pytest suite; supervisor evidence gate limits us to collect-only
- Keep environment variable `KMP_DUPLICATE_LIB_OK=TRUE` in every parity command to avoid MKL crashes
- Maintain SAMPLE pivot enforcement when custom detector vectors are present; no regression to BEAM pivot
- Confirm `trace_pixel` gating uses meters (not mm) to prevent unit drift in logs
- Avoid editing scaled.hkl or A.mat directly; treat them as fixtures referenced by the harness
- Document any blockers immediately in docs/fix_plan.md to avoid context loss
Pointers:
- docs/fix_plan.md:448-462 (CLI-FLAGS-003 next actions)
- plans/active/cli-noise-pix0/plan.md:12-120 (Phase L2 guidance)
- reports/2025-10-cli-flags/phase_l/scaling_audit/notes.md (workflow log)
- reports/2025-10-cli-flags/phase_j/scaling_chain.md (factor ratios and prior diagnosis)
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log (C reference trace)
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log (current placeholder output)
- scripts/validation/compare_scaling_traces.py (to be updated/used for trace diff)
- scripts/trace_per_phi.py:1-160 (per-φ diagnostic script; mind duplicate pix0 subtraction)
- src/nanobrag_torch/simulator.py:930-1200 (TRACE_PY logging zone)
- docs/development/testing_strategy.md:70-120 (parity evidence expectations)
- docs/architecture/pytorch_design.md:200-320 (scaling + normalization ADRs)
Next Up: Begin Phase L2c comparison and prep Phase L3 scaling fix once TRACE_PY emits non-placeholder values
Context Notes:
- The supervisor command uses CUSTOM convention with explicit detector vectors; SAMPLE pivot enforcement is mandatory.
- The harness now passes `-nonoise`, so expect no noisefile artifacts; verify CLI respects this when running.
- Ensure `DetectorConfig` continues to ignore `pix0_vector_mm` when custom vectors are present; instrumentation must not bypass this guard.
- Phase K3 diagnostics identified the sincg mismatch; capturing accurate `I_before_scaling` will confirm whether F_latt drift persists post-rescale fix.
- Keep Attempt numbering consistent (next log entry should follow Attempt #66 context).
- Use UTC timestamps in new notes; convert local time to ISO format if needed.
- Trace logs should print 12–15 significant digits per CLAUDE debug spec.
Reminders:
- Work under prompts/debug.md context while parity fails.
- Keep golden_suite_generator/nanoBragg instrumentation aligned with TRACE_PY variable names.
- Store comparison CSV/JSON outputs under `reports/2025-10-cli-flags/phase_l/scaling_audit/` with timestamps.
- After instrumentation, rerun `reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --dry-run` if you need to validate CLI parsing changes without writing logs.
- Consider adding asserts in the trace path to guarantee `capture_fraction` tensor shape matches expectations (scalar or (S,F) broadcast).
- When authoring the regression test, fixture out the C trace values to avoid brittle string comparisons.
- Use `pytest.param(..., marks=pytest.mark.skipif(...))` to guard CUDA variants if device unavailable.
- Update `reports/2025-10-cli-flags/phase_l/scaling_audit/notes.md` with execution timestamps and git SHA for reproducibility.
TODO Outline:
- [ ] Modify simulator trace logging to emit `I_before_scaling`, `polar`, `capture_fraction`, and total `steps`.
- [ ] Update existing trace unit tests (if any) to expect the new fields.
- [ ] Add `tests/test_trace_pixel.py::test_scaling_trace_matches_physics` covering CPU float32 baseline.
- [ ] Optionally parametrize the new test for CUDA; mark xfail if device not present.
- [ ] Regenerate `trace_py_scaling.log` and confirm nonzero intensity.
- [ ] Run compare script and summarize deltas.
- [ ] Log Attempt update with metrics and artifacts in docs/fix_plan.md.
Constraints:
- Supervisor evidence mode forbids full pytest runs; limit to collect-only or targeted failing test confirmations.
- No code commits from galph beyond docs/input updates; let Ralph push implementation changes.
- Maintain ASCII encoding; avoid introducing unicode characters in new logs/tests.
- Keep script paths under scripts/validation/ or scripts/benchmarks/ as per tooling ADR.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
Note: keep monitoring k_frac deltas; target |Δk| ≤ 5e-4 before Phase L3.
