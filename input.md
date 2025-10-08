Summary: Capture enhanced φ-rotation traces (M5a) so we can quantify the rot_* mismatch before implementing the fix.
Mode: Parity
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling_phi0.py
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/fix_${TS}/trace_py_scaling.log; reports/2025-10-cli-flags/phase_l/scaling_validation/fix_${TS}/trace_py_scaling_per_phi.log; reports/2025-10-cli-flags/phase_l/scaling_validation/fix_${TS}/trace_stdout.txt; reports/2025-10-cli-flags/phase_l/scaling_validation/fix_${TS}/commands.txt
Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — TS=$(date -u +%Y%m%dT%H%M%SZ) KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --emit-rot-stars --out reports/2025-10-cli-flags/phase_l/scaling_validation/fix_${TS}/trace_py_scaling.log
If Blocked: Capture the stdout + error into reports/2025-10-cli-flags/phase_l/scaling_validation/fix_${TS}/attempt.log, add a short blockers.md summarising symptoms, and ping me in docs/fix_plan.md Attempts.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:74 — Phase M5a expects fresh per-φ traces with rot_* fields before we touch simulator code.
- docs/fix_plan.md:466 — Next Actions now call for enhanced trace capture plus rotation realignment sequencing.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md — H4 documents rot_b drifting 6.8%; we need richer traces to confirm.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/diff_trace.md — shows normalization fixed yet I_before_scaling deficit persists; new traces must target the same pixel.
- specs/spec-a-core.md:204 — Normative φ rotation pipeline we must match when interpreting the trace.
How-To Map:
- export TS=$(date -u +%Y%m%dT%H%M%SZ)
- mkdir -p reports/2025-10-cli-flags/phase_l/scaling_validation/fix_${TS}
- KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --emit-rot-stars --out reports/2025-10-cli-flags/phase_l/scaling_validation/fix_${TS}/trace_py_scaling.log | tee reports/2025-10-cli-flags/phase_l/scaling_validation/fix_${TS}/trace_stdout.txt
- mv reports/2025-10-cli-flags/phase_l/per_phi/trace_py_scaling_per_phi.log reports/2025-10-cli-flags/phase_l/scaling_validation/fix_${TS}/trace_py_scaling_per_phi.log (same for .json) so the bundle is self-contained; regenerate per_phi JSON by rerunning harness if needed.
- printf '%s\n' "KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --emit-rot-stars --out reports/2025-10-cli-flags/phase_l/scaling_validation/fix_${TS}/trace_py_scaling.log" > reports/2025-10-cli-flags/phase_l/scaling_validation/fix_${TS}/commands.txt
- pytest --collect-only -q tests/test_cli_scaling_phi0.py | tee reports/2025-10-cli-flags/phase_l/scaling_validation/fix_${TS}/pytest_collect.log
Pitfalls To Avoid:
- Do not skip --emit-rot-stars; without it we miss the rot_* values needed for M5a.
- Keep PYTHONPATH=src and KMP_DUPLICATE_LIB_OK=TRUE so torch loads cleanly.
- No edits to production rotation logic yet; today is instrumentation-only.
- Preserve device/dtype neutrality in any temporary helpers (stay float64 for traces, no .cpu() inserts).
- Do not overwrite the spec_baseline artifacts; use a new fix_${TS} directory.
- Avoid renaming files listed in docs/index.md (Protected Assets rule).
- Keep stdout captures under 1 MB; trim or compress if verbose.
- Update sha256.txt only after files settle; add entries via shasum >> file.
- Log Attempt details in docs/fix_plan.md once artifacts are in place.
Pointers:
- plans/active/cli-noise-pix0/plan.md:74
- docs/fix_plan.md:466
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/diff_trace.md
- specs/spec-a-core.md:204
Next Up: Draft rotation_fix_design.md (Phase M5b) outlining the per-φ recompute steps before touching simulator.py.
