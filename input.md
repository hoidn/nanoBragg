Summary: Land φ=0 carryover parity and fix per-φ instrumentation so CLI-FLAGS-003 can clear VG-1.
Mode: Parity
Focus: CLI-FLAGS-003 — Phase L3k.3c.3 φ=0 carryover fix
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q ; pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c -v
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<new_timestamp>/ ; reports/2025-10-cli-flags/phase_l/per_phi/reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<new_timestamp>/ ; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<new_timestamp>/comparison_summary.md
Do Now: CLI-FLAGS-003 L3k.3c.3 — regenerate per-φ traces via `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --pixel 685 1039 --config supervisor --dtype float64 --device cpu --out reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<new_timestamp>/trace_py_rot_vector.log` and confirm the fix with `pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c -v` plus `python scripts/compare_per_phi_traces.py reports/2025-10-cli-flags/phase_l/per_phi/reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<new_timestamp>/trace_py_rot_vector_per_phi.json reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/c_trace_phi_20251123.log`.
If Blocked: If the harness fails to emit TRACE_PY_PHI lines, rerun `pytest --collect-only -q`, capture the failure log under reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/blockers/<date>/`, and note the blocker in docs/fix_plan.md Attempt history before attempting any workaround.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:286 — L3k.3c.3 explicitly calls for φ carryover plus VG-1 evidence, so we must implement that change now.
- docs/fix_plan.md:450 — Next Actions already gate L3k.3d on the φ=0 fix; completing this unblocks the long-term CLI parity goal.
- src/nanobrag_torch/models/crystal.py:1008 — Existing rotation loop is vectorised but lacks the φ_last reuse that nanoBragg.c applies.
- src/nanobrag_torch/simulator.py:1444 — Per-φ instrumentation currently divides osc_range by (phi_steps-1), producing φ=0.011111° samples; correcting this keeps traces aligned with the C loop formula.
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/delta_metrics.json — Shows Δk(φ₀)=1.8116e-02, our acceptance benchmark for the fix.
How-To Map:
- Set env: `export NB_C_BIN=./golden_suite_generator/nanoBragg` and `export KMP_DUPLICATE_LIB_OK=TRUE` before any torch import; keep `PYTHONPATH=src` when running harness scripts.
- Rebuild PyTorch trace after coding: `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --pixel 685 1039 --config supervisor --dtype float64 --device cpu --out reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<new_timestamp>/trace_py_rot_vector.log` (the harness will also emit the per-φ JSON under the matching per_phi/ path).
- Run comparison: `python scripts/compare_per_phi_traces.py reports/2025-10-cli-flags/phase_l/per_phi/reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<new_timestamp>/trace_py_rot_vector_per_phi.json reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/c_trace_phi_20251123.log | tee reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<new_timestamp>/compare_latest.txt`.
- Execute targeted pytest: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c -v` (expected to go green only after Δk, Δb_y < 1e-6).
- After pytest, rerun `pytest --collect-only -q` to log collection sanity and stash both logs under the new timestamp directory.
Pitfalls To Avoid:
- Do not reintroduce Python-side φ loops; keep rotations batched and device/dtype neutral.
- Preserve the cached reciprocal recomputation (CLAUDE Rule #13); carryover must reuse tensor caches, not detach to NumPy.
- Avoid `.cpu()`/`.item()` inside the simulation hot path; grab scalar diagnostics only in harnesses.
- Leave the red guard tests in `tests/test_cli_scaling_phi0.py` untouched until gradients pass, then flip them by implementing the fix.
- Maintain Protected Assets: no renaming/removing files referenced in docs/index.md.
- Keep φ step instrumentation change confined to tracing; do not alter production φ generation semantics that already match C.
- Update `fix_checklist.md` and `diagnosis.md` once metrics hit the new thresholds; missing documentation will block sign-off.
- Ensure new artifacts use fresh timestamped directories to keep Attempt history reproducible.
Pointers:
- plans/active/cli-noise-pix0/plan.md:287
- docs/fix_plan.md:458
- src/nanobrag_torch/models/crystal.py:1008
- src/nanobrag_torch/simulator.py:1444
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/diagnosis.md
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md:19
Next Up: 1) CLI-FLAGS-003 L3k.3d — nb-compare ROI parity once VG-1 is green; 2) CLI-FLAGS-003 L3k.3e — documentation + attempt logging.
