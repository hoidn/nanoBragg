Summary: Align MOSFLM reciprocal-vector handling so Phase M2 lattice parity clears and the supervisor command can advance.
Mode: Parity
Focus: CLI-FLAGS-003 — Phase M2 Fix lattice factor propagation
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_phi0.py::TestScalingParity::test_I_before_scaling_matches_c
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<new timestamp>/
Do Now: CLI-FLAGS-003 — Phase M2 Fix lattice factor propagation; KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestScalingParity::test_I_before_scaling_matches_c
If Blocked: Capture a fresh trace harness run (CPU float64 c-parity) under reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/attempts/ and note blockers in docs/fix_plan.md Attempt history.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md#L62 — Phase M2 stays open until the 0.13% F_latt drift is eliminated; nb-compare (Phase N) and supervisor rerun (Phase O) are blocked until this parity passes.
- docs/fix_plan.md#L451 — Next Actions demand that I_before_scaling land within ≤1e-6 relative before resuming VG-3/VG-4 metrics.
- specs/spec-a-core.md#L204 — Spec requires recomputing reciprocal vectors per φ from freshly rotated reals; our trace must uphold metric duality (a·a* = 1) despite MOSFLM matrices.
- docs/development/c_to_pytorch_config_map.md#L105 — MOSFLM orientation ingestion must maintain exact geometry parity; deviations in pix0 or close_distance ripple into scattering vector mismatches.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/scaling_validation_summary.md — Latest evidence pinpoints the k_frac offset and reciprocal-vector drift; resolve these before gathering new artifacts.
- plans/active/cli-phi-parity-shim/plan.md#L120 — Parity shim already guards carryover behaviour; remaining deltas are lattice-only, so no further φ-mode tweaks should be attempted.
How-To Map:
- export PYTHONPATH=src; KMP_DUPLICATE_LIB_OK=TRUE python reports/2025_10_cli_flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --phi-mode c-parity --device cpu --dtype float64 --emit-rot-stars --out reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/trace_py_scaling.log
- python scripts/validation/compare_scaling_traces.py --py reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/trace_py_scaling.log --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --json reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/metrics.json --summary reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/scaling_validation_summary.md
- python - <<'PY'
from pathlib import Path
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.io.mosflm import read_mosflm_matrix, reciprocal_to_real_cell
import torch
# Load MOSFLM matrix and build Crystal at float64
mat_path = Path('A.mat')
a_star,b_star,c_star = read_mosflm_matrix(str(mat_path), 0.9768)
cell = reciprocal_to_real_cell(a_star,b_star,c_star)
crystal = Crystal(CrystalConfig(
    cell_a=cell[0], cell_b=cell[1], cell_c=cell[2],
    cell_alpha=cell[3], cell_beta=cell[4], cell_gamma=cell[5],
    mosflm_a_star=torch.tensor(a_star, dtype=torch.float64),
    mosflm_b_star=torch.tensor(b_star, dtype=torch.float64),
    mosflm_c_star=torch.tensor(c_star, dtype=torch.float64),
    N_cells=(36,47,29),
    phi_start_deg=0.0, osc_range_deg=0.1, phi_steps=10,
), dtype=torch.float64)
tensors = crystal.compute_cell_tensors()
print(tensors['a_star'], tensors['b_star'], tensors['c_star'])
PY > reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/cell_tensors_before_fix.log
- After code edits, repeat the snippet and diff against the C trace (reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log) to confirm reciprocal vector parity before rerunning the harness.
- Once traces align, run KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestScalingParity::test_I_before_scaling_matches_c and archive the log under reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/pytest.log.
- Update docs/fix_plan.md Attempts (CLI-FLAGS-003) with the new timestamp, metrics.json delta summary, pytest selector, and git commit SHA.
Pitfalls To Avoid:
- Do not downcast tensors; keep Crystal/Detector/Simulator on dtype passed from CLI.
- Preserve vectorization in compute_cell_tensors and compute_physics_for_position; no new Python loops over φ or mosaic indices.
- Leave Protected Assets listed in docs/index.md untouched (loop.sh, input.md, supervisor.sh, etc.).
- Avoid `.item()` on tensors that need gradients in production paths; restrict scalar extraction to trace-only code.
- Keep parity shim optional; spec mode must remain bug-free and continue to pass existing tests.
- Ensure compare_scaling_traces.py runs against the same C trace (reports/.../scaling_audit/c_trace_scaling.log); mismatched baselines invalidate evidence.
- Record SHA256 checksums for new artifacts in reports/.../<ts>/sha256.txt before updating plan or fix_plan entries.
- No full pytest suite unless code changed and the targeted selector already passes; follow testing_strategy.md device cadence.
- Retain device/dtype neutrality when adding diagnostics; no hard-coded `.cpu()` or `.double()` conversions inside production functions.
- Share findings in reports/.../lattice_hypotheses.md, appending a new section rather than overwriting earlier attempts.
Pointers:
- plans/active/cli-noise-pix0/plan.md#L60
- docs/fix_plan.md#L451
- specs/spec-a-core.md#L204
- docs/development/c_to_pytorch_config_map.md#L105
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/scaling_validation_summary.md
Next Up: If M2 closes early, prep nb-compare rerun per plan Phase N1–N3 with fresh C/PyTorch float binaries, then revisit plan Phase O supervisor command once VG-3/VG-4 gates pass.
Execution Steps:
1. Reproduce current drift: reuse 20251008T075949Z artifacts to confirm baseline numbers (k_diff ≈ -6.78e-06, F_latt rel diff ≈ -1.28e-03) before editing; log results in attempts/baseline.txt.
2. Instrument Crystal.compute_cell_tensors() to emit pre-/post-MOSFLM reciprocal vectors for MOSFLM vs manual cell flow; capture to reports/.../<ts>/cell_debug_before.md.
3. Adjust MOSFLM branch so recomputed real vectors, reciprocal vectors, and actual volume match C trace (dot(a,b×c) = 24682.2566301113 Å³); rerun debug snippet and record diffs.
4. Validate scattering vector: run python scripts/validation/compare_scaling_traces.py --dump-scattering reports/.../<ts>/scattering_diff.json and confirm deltas fall below 1e-9 relative.
5. After code changes, re-run trace harness (CPU float64, c-parity) and ensure TRACE_PY_PHI lines show k_diff within ±1e-9 and a_star_y/b_star_y/c_star_y match C to ≤1e-9.
6. Execute targeted pytest selector; stash logs plus env snapshot (python -V, torch --version) in reports/.../<ts>/env.json.
7. Update docs/fix_plan.md Attempt # in CLI-FLAGS-003 with new evidence paths, summary of k_diff and I_before_scaling ratio, pytest command, and git SHA.
8. Stage changes, run pre-commit lint if required, and prepare commit titled "CLI-FLAGS-003 Phase M2 lattice parity" once selector passes.
9. Leave a note in reports/.../lattice_hypotheses.md describing how reciprocal-vector parity was restored (include before/after table).
10. Only after the above, notify galph via git sync (SYNC commit) so the next supervisor loop can pivot to Phase N.

Validation Targets:
- |k_frac_py - k_frac_c| ≤ 1e-9 for all φ steps 0–9.
- |F_latt_py - F_latt_c| / |F_latt_c| ≤ 1e-6.
- scattering_vec component deltas ≤ 1e-3 absolute (≈1e-9 relative at scale 1e9).
- I_before_scaling_pre_polar ratio (PyTorch / C) within 1 ± 1e-6.
- Crystal.compute_cell_tensors() invariants: a·a* = b·b* = c·c* = 1 to 1e-10; cross-axis dot products ≈ 0.

Documentation Updates After Fix:
- Append a short note to reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/summary.md describing the reciprocal-vector correction and quoting the relevant nanoBragg.c lines.
- Update reports/2025-10-cli-flags/phase_l/scaling_validation/lattice_hypotheses.md with a "Resolved" subsection linking to the new timestamp directory and summarising validation metrics.
- Refresh plans/active/cli-noise-pix0/plan.md Phase M2 table (mark M2 as [D], transition to M3) with references to new evidence.
- Add the new timestamp to docs/fix_plan.md Attempts list (VG-2) together with pytest selector and SHA256 manifest path.
- Confirm docs/bugs/verified_c_bugs.md remains unchanged (phi carryover bug still C-only; no documentation drift introduced).

Notes:
- Use float64 end-to-end for the debug snippet; avoid implicit casts by passing dtype=torch.float64 when constructing tensors.
- When comparing JSON dumps, use python scripts/validation/diff_json.py (if unavailable, add a helper under scripts/validation/ matching repo conventions).
- If CUDA smoke is desired after CPU success, mirror the harness command with --device cuda but keep CPU logs as authoritative for parity signoff.
- Keep trace files small by filtering with grep 'TRACE_PY_PHI' > per_phi.log before archiving.
- Remember to record git status (clean/dirty) in reports/.../<ts>/git_status.txt before finalizing Attempt entry.
Re-run Checklist Before Hand-off:
- Verify reports/.../<ts>/sha256.txt covers trace, summary, metrics, pytest log, env.json, and git_status.txt.
- Ensure commands.txt in the new timestamp directory lists every reproduction step with working directories and env vars.
- Drop a short README.md in the timestamp directory highlighting key metrics and sign-off criteria for future audits.
- Confirm that attempts_history.md (if you maintain one locally) references the new timestamp so the supervisor can find evidence without digging.
- Leave a brief note in reports/2025-10-cli-flags/phase_l/scaling_validation/README.md summarizing how to reproduce the fixed run.
- Double-check git diff for unintended trace or plan edits before staging.
