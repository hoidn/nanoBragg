Summary: Produce a fresh spec-mode scaling baseline after shim removal so we know the current F_cell/F_latt/I_before_scaling deltas.
Mode: Parity
Focus: CLI-FLAGS-003 – Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_phi0.py (collect-only for this loop)
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/spec_baseline/{commands.txt,metrics.json,summary.md,env.json,compare_scaling_traces.stdout,sha256.txt}
Do Now: CLI-FLAGS-003 Phase M1 — run `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --out reports/2025-10-cli-flags/phase_l/scaling_validation/$STAMP/spec_baseline/` followed by `python scripts/validation/compare_scaling_traces.py --trace-dir reports/2025-10-cli-flags/phase_l/scaling_validation/$STAMP/spec_baseline/` and `pytest --collect-only -q tests/test_cli_scaling_phi0.py` (set `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` first).
If Blocked: If trace_harness.py fails, capture stdout/stderr into the same spec_baseline directory, add a brief blocker note to summary.md, and ping me before retrying; do not tweak simulator code yet.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md — Phase M insists on a new spec baseline before we touch physics again.
- docs/fix_plan.md:451 — Next Actions now hinge on rows M1–M2; without this bundle we are blind.
- specs/spec-a-core.md:204 — Confirms lattice math we must validate in the new trace.
- docs/development/testing_strategy.md#14-pytorch-device--dtype-discipline — Requires we log dtype/device and prove selectors are discoverable.
- reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T203504Z/summary.md — Reference proof that shim removal is complete; today’s run must stay spec-only.
How-To Map:
- `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`
- `mkdir -p reports/2025-10-cli-flags/phase_l/scaling_validation/$STAMP/spec_baseline`
- `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --out reports/2025-10-cli-flags/phase_l/scaling_validation/$STAMP/spec_baseline/ | tee reports/2025-10-cli-flags/phase_l/scaling_validation/$STAMP/spec_baseline/trace_harness.stdout`
- `python scripts/validation/compare_scaling_traces.py --trace-dir reports/2025-10-cli-flags/phase_l/scaling_validation/$STAMP/spec_baseline/ | tee reports/2025-10-cli-flags/phase_l/scaling_validation/$STAMP/spec_baseline/compare_scaling_traces.stdout`
- `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py | tee reports/2025-10-cli-flags/phase_l/scaling_validation/$STAMP/spec_baseline/pytest_collect.log`
- Write `summary.md` capturing metrics (first_divergence, F_cell/F_latt ratios), note git SHA, and list follow-ups for Phase M2.
- Record environment via `python - <<'PY'
import json, os, torch
print(json.dumps({"python": os.sys.version, "torch": torch.__version__}, indent=2))
PY > reports/2025-10-cli-flags/phase_l/scaling_validation/$STAMP/spec_baseline/env.json`
- `sha256sum reports/2025-10-cli-flags/phase_l/scaling_validation/$STAMP/spec_baseline/* > reports/2025-10-cli-flags/phase_l/scaling_validation/$STAMP/spec_baseline/sha256.txt`
Pitfalls To Avoid:
- Do not resurrect `phi_carryover_mode` arguments; stays spec-only.
- Avoid overwriting older bundles; always use a new timestamp.
- Keep tensors on the harness-selected device; no ad-hoc `.cpu()` casts in repro scripts.
- Do not edit production code or tests in this loop.
- Capture full command logs; partial summaries aren’t enough for parity analysis.
- Remember Protected Assets (`docs/index.md`); do not move listed files.
- No nb-compare runs yet—Phase N waits for green VG-2 evidence.
- Leave Option B cache prototypes untouched; focus is baseline evidence.
- Ensure PYTHONPATH=src so harness resolves local modules.
- Keep `trace_harness` in float64 per plan; no dtype shortcuts.
Pointers:
- plans/active/cli-noise-pix0/plan.md — Phase M table (rows M1–M3).
- docs/fix_plan.md:451 — CLI-FLAGS-003 ledger + updated Next Actions.
- specs/spec-a-core.md:204 — Lattice factor contract to cite in summary.
- reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T203504Z/summary.md — Proof that today’s run must remain spec.
- scripts/validation/compare_scaling_traces.py — Tool for M1 diff capture.
Next Up: Phase M2 — extend analysis.md + lattice_hypotheses.md with the new metric breakdown.
