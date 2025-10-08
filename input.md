Summary: Instrument the φ carryover trace to capture scattering-vector taps and eliminate the 2.845e-05 Δk plateau.
Mode: Parity
Focus: CLI-FLAGS-003 — Phase L3k.3c.4 parity shim evidence
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c; tests/test_phi_carryover_mode.py::TestPhiCarryoverBehavior
Artifacts: reports/2025-10-cli-flags/phase_l/parity_shim/20251008T021659Z/
Do Now: CLI-FLAGS-003 Phase L3k.3c.4 — TS=$(date -u +%Y%m%dT%H%M%SZ); PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --pixel 685 1039 --config supervisor --phi-mode c-parity --device cpu --dtype float64 --out reports/2025-10-cli-flags/phase_l/parity_shim/$TS/trace_py_c_parity.log
If Blocked: Capture the best-effort trace output, append the failure note + hypothesis to docs/fix_plan.md Attempt history, and stop without code changes.
Priorities & Rationale:
- docs/fix_plan.md:461 keeps C4 open until Δk ≤ 1e-6; today’s task is the next diagnostic step.
- docs/fix_plan.md:684 logs Attempt #124 with residual 2.845e-05 drift, demanding deeper instrumentation.
- plans/active/cli-phi-parity-shim/plan.md:47 calls for fresh traces plus analysis before marking C4 [D].
- docs/bugs/verified_c_bugs.md:166 documents C-PARITY-001, confirming spec must stay clean while the shim matches the bug.
- specs/spec-a-core.md:211 enforces fresh φ rotations each step; any parity fix must preserve spec compliance when mode="spec".
How-To Map:
- Add `TRACE_PY_PHI` taps (or harness logging) for scattering vector components, φ-dependent reciprocal vectors, and V_actual; annotate with nanoBragg.c lines 3044-3058 per CLAUDE Rule #11 before coding.
- Re-run the harness for spec (`--phi-mode spec`) and parity (`--phi-mode c-parity`) using the Do Now command pattern (update $TS for each run) so new artifacts land under `reports/.../<timestamp>/`.
- Compare against the fresh C trace via `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/compare_per_phi_traces.py <py_json> <reports/.../$TS/c_trace_phi.log>` and stash stdout/markdown beside the traces.
- Update or regenerate `delta_metrics.json` with the new deltas and re-run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests/test_cli_scaling_phi0.py tests/test_phi_carryover_mode.py -q` to log selector health.
- Summarise findings in `reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md` plus add an Attempt entry once metrics are recorded.
Pitfalls To Avoid:
- Do not relax the ≤1e-6 / ≤1e-4 VG-1 tolerances; fix the physics instead.
- Keep all new logging vectorised; no per-φ Python loops in hot paths.
- Preserve float64 instrumentation (no silent dtype downgrades) and avoid `.item()` on tensors needed for gradients.
- Always set KMP_DUPLICATE_LIB_OK=TRUE for harness + pytest invocations.
- Don’t overwrite existing artifacts; create a fresh timestamped directory and regenerate SHA256 hashes.
- Leave spec mode untouched—shim changes must stay behind `phi_carryover_mode="c-parity"`.
- Avoid modifying protected docs/index.md entries or deleting tracked artifacts.
- No full `pytest` run; stick to targeted collect / harness commands.
Pointers:
- docs/fix_plan.md:461 — updated Next Actions for C4 diagnostics.
- docs/fix_plan.md:684 — Attempt #124 metrics + hypotheses.
- plans/active/cli-phi-parity-shim/plan.md:47 — C4 guidance and exit criteria.
- docs/bugs/verified_c_bugs.md:166 — definition of the φ=0 carryover C bug.
- specs/spec-a-core.md:211 — normative φ rotation formula.
- docs/debugging/debugging.md:24 — parallel trace comparison SOP.
Next Up:
- Once Δk ≤ 1e-6, move to Phase L3k.3c.5 documentation refresh and nb-compare gating (Phase L3k.3d).
