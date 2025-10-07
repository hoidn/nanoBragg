Summary: Capture per-φ lattice traces so we can isolate the F_latt drift blocking CLI parity.
Mode: Parity
Focus: CLI-FLAGS-003 – Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: [tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics]
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling_per_phi.log; reports/2025-10-cli-flags/phase_l/per_phi/per_phi_py_20251119.json; reports/2025-10-cli-flags/phase_l/per_phi/comparison_summary_20251119.md
Do Now: CLI-FLAGS-003 — extend the scaling trace harness to emit per-φ `TRACE_PY_PHI` lattice entries and rerun the supervisor pixel; after instrumentation run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics -q`
If Blocked: Re-run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling_20251117.log --out reports/2025-10-cli-flags/phase_l/scaling_validation/scaling_validation_summary_20251119.md` and log findings in docs/fix_plan.md Attempt history.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md Phase L3e calls for scaling-factor validation before closing the CLI parity blocker.
- docs/fix_plan.md:450-540 records I_before_scaling as the first divergence; Attempt #83 highlights the remaining lattice-factor gap.
- specs/spec-a-cli.md ensures `-pix0_vector_mm` and custom vectors follow CUSTOM convention semantics; parity depends on matching C behavior.
- docs/architecture/detector.md §5 (pix0) and docs/development/c_to_pytorch_config_map.md (detector pivot rules) inform the existing geometry configuration used in the trace harness.
- reports/2025-10-cli-flags/phase_l/scaling_validation/analysis_20251119.md documents the F_latt sign mismatch we must localize.
How-To Map:
- Sanity-check selector: `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics`.
- Update `reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py` to preserve simulator debug output (no reimplementation) and capture per-φ events; redirect stdout to `trace_py_scaling_per_phi.log`.
- Emit structured JSON alongside the log (`per_phi_py_20251119.json`) capturing φ_tic, φ_deg, k_frac, F_latt_b, F_latt for reuse by comparison tooling.
- Compare against the archived C trace: `python scripts/compare_per_phi_traces.py reports/2025-10-cli-flags/phase_l/per_phi/per_phi_py_20251119.json reports/2025-10-cli-flags/phase_k/f_latt_fix/per_phi/per_phi_c_20251006-151228.log > reports/2025-10-cli-flags/phase_l/per_phi/comparison_summary_20251119.md`.
- After instrumentation, rerun `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics -q` and capture output for reports/2025-10-cli-flags/phase_l/per_phi/`.
- Re-run scaling chain diff to confirm the raw accumulation delta persists (or closes) and archive updated metrics under `reports/2025-10-cli-flags/phase_l/scaling_validation/`.
Pitfalls To Avoid:
- Do not touch production geometry math until per-φ evidence pinpoints the divergence.
- Reuse simulator debug hooks; no ad-hoc physics recomputation in tooling (per CLAUDE Rule 0 instrumentation discipline).
- Keep tensors on caller device/dtype; avoid `.cpu()` in instrumentation.
- Maintain Protected Assets (`docs/index.md`), especially `loop.sh`, `supervisor.sh`, `input.md`.
- No `.item()` on differentiable tensors when wiring debug output.
- Avoid rerunning the full pytest suite; targeted command only.
- Update docs/fix_plan.md Attempt history immediately after capturing evidence.
- Store artifacts under the prescribed `reports/2025-10-cli-flags/phase_l/` directories with timestamped names.
- Respect vectorization (no new Python loops inside simulator core).
- Mention `KMP_DUPLICATE_LIB_OK=TRUE` whenever invoking torch-based scripts.
Pointers:
- docs/fix_plan.md:450
- plans/active/cli-noise-pix0/plan.md:1
- reports/2025-10-cli-flags/phase_l/scaling_validation/analysis_20251119.md
- scripts/validation/compare_scaling_traces.py:1
- reports/2025-10-cli-flags/phase_k/f_latt_fix/per_phi/comparison_summary.md
Next Up: If per-φ parity confirms the lattice mismatch, prep a simulator patch (Phase L3f/L3g) to align `_compute_structure_factor_components` with C and rerun the supervisor command via nb-compare.
