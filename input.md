Summary: Capture rich φ-step lattice traces so we can localize the F_latt drift before touching simulator math.
Mode: Parity
Focus: CLI-FLAGS-003 – Phase M2 lattice factor propagation
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<new_ts>/, reports/2025-10-cli-flags/phase_l/per_phi/<new_ts>/
Do Now: CLI-FLAGS-003 Phase M2 — extend trace_harness + simulator trace taps to emit per-φ `ap/bp/cp`, `rot_*_star`, and `V_actual`, then run `KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --dtype float64 --emit-rot-stars`
If Blocked: If you can’t wire the new taps quickly, dump the existing tensors by instrumenting a one-off script that calls `Crystal.get_rotated_vectors()` for φ ticks 0–9 and store the tensors under the same timestamp (commands.txt + torch.save).
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:63-84 — Phase M2 checklist now expects enhanced lattice evidence before implementation.
- docs/fix_plan.md:600-666 — Attempt #149 documents hypotheses we must validate; next action is richer trace capture.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md — Baseline numbers you must reproduce/extend.
- specs/spec-a-core.md:205-233 — φ rotation pipeline defines expected per-step vector reset; use as correctness oracle.
- docs/bugs/verified_c_bugs.md:166-204 — C parity bug reminder; keep spec mode untouched while tracing.
How-To Map:
- Export env: `export KMP_DUPLICATE_LIB_OK=TRUE; export PYTHONPATH=src`
- After adding taps, run `python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --dtype float64 --emit-rot-stars --phi-mode c-parity`
- Capture stdout/stderr into `<new_ts>/trace_harness.log` and dump per-φ data to `per_phi/.../trace_py_scaling_per_phi_rotstars.log`
- Re-run `scripts/validation/compare_scaling_traces.py` against the new traces; store `metrics.json`, `summary.md`, and SHA256 sums under the same timestamp
- Update `commands.txt` with every invocation and note git SHA via `git rev-parse HEAD`
Pitfalls To Avoid:
- Do not remove existing TRACE_PY lines; append new ones with stable prefixes (e.g., `TRACE_PY_ROTSTAR`)
- Keep vectorization: no Python φ loops outside trace-only blocks
- Maintain device/dtype neutrality; pull tensors’ existing device/dtype when logging
- Respect Protected Assets; don’t touch files listed in docs/index.md
- Avoid `.item()` on tensors feeding gradients
- Don’t skip `pytest --collect-only -q tests/test_cli_scaling_phi0.py tests/test_phi_carryover_mode.py` after edits; record output if run
- Ensure new harness flags default to off so production runs stay unchanged
- Store artifacts under timestamped directories with SHA256 manifest
- Keep C and Py trace filenames distinct (`trace_py_*` vs `trace_c_*`)
Pointers:
- plans/active/cli-noise-pix0/plan.md:81 — M2c now [D]; next step is instrumentation + implementation prep
- docs/fix_plan.md:600-666 — Attempt #148/#149 context and expectations
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md — Current hypotheses to validate
- specs/spec-a-core.md:205 — φ rotation spec baseline (no carryover)
- docs/bugs/verified_c_bugs.md:166 — C-PARITY-001 quarantine notes
Next Up: (1) Float64 rerun without new taps to isolate precision effects, (2) Draft targeted pytest for `test_I_before_scaling_matches_c` once trace evidence is green.
