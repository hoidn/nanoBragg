Summary: Capture fresh scaling evidence and quantify the MOSFLM orientation mismatch before touching normalization code.
Phase: Evidence
Focus: CLI-FLAGS-003 Phase K2/K2b — Normalization Diagnostics
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after.log; reports/2025-10-cli-flags/phase_k/f_latt_fix/metrics_after.json; reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_summary.md; reports/2025-10-cli-flags/phase_k/f_latt_fix/orientation_delta.md; reports/2025-10-cli-flags/phase_k/f_latt_fix/mosflm_rescale.py
Do Now: CLI-FLAGS-003 Phase K2/K2b — run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py --out reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after.log`, then author `reports/2025-10-cli-flags/phase_k/f_latt_fix/mosflm_rescale.py` to log C vs PyTorch lattice-vector deltas per plan guidance.
If Blocked: Capture stdout/stderr to `reports/2025-10-cli-flags/phase_k/f_latt_fix/attempt_blocked.log`, record env snapshot (commit hash, python/torch versions, CUDA availability), run `git status --short`, describe the blocker in docs/fix_plan Attempt history, and stop.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:170 — K2 now requires refreshed scaling metrics plus explicit orientation deltas before implementation starts.
- plans/active/cli-noise-pix0/plan.md:171 — K2b mandates a minimal script proving the `vector_rescale` mismatch; artifacts must live alongside scaling logs.
- docs/fix_plan.md:455 — Updated Next Actions call out the rescale + polarization blockers; evidence is prerequisite for K3 fixes.
- reports/2025-10-cli-flags/phase_k/f_latt_fix/metrics_after.json — Current ratios still show F_latt_b ≈1.216 and polar=1.0; need annotated rerun.
- golden_suite_generator/nanoBragg.c:2145 — Reference implementation only rescales cross products when `user_cell` is set, so evidence must compare to this branch.
How-To Map:
- Ensure report directory exists: `mkdir -p reports/2025-10-cli-flags/phase_k/f_latt_fix`.
- Refresh PyTorch trace: `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py --out reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after.log`.
- Update scaling ratios: `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_j/analyze_scaling.py --c-log reports/2025-10-cli-flags/phase_j/trace_c_scaling.log --py-log reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after.log`.
- Draft `mosflm_rescale.py` (start from earlier interactive snippet) to print C-style vs PyTorch real vectors; run it with `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_k/f_latt_fix/mosflm_rescale.py > reports/2025-10-cli-flags/phase_k/f_latt_fix/orientation_delta.md`.
- Sync `metrics_after.json`/`scaling_summary.md` with new findings and cite the new orientation artifact.
Pitfalls To Avoid:
- No pytest or nb-compare invocations this loop—Evidence phase only.
- Do not edit simulator/crystal/detector code yet; gather evidence first.
- Keep env var `KMP_DUPLICATE_LIB_OK=TRUE` on every torch script run.
- Reuse `PYTHONPATH=src`; avoid import-from-installed copies.
- Store new scripts under the existing reports path (Protected Assets rule—no root clutter).
- When writing markdown, stick to ASCII and avoid overwriting prior evidence sections.
- Note beam/polarization values exactly; no rounding beyond 6 sig figs.
- Leave previous artifacts in place; append new sections rather than replacing.
- Confirm `NB_C_BIN` is set before referencing C traces; document if you relied on archived logs instead of rerunning C.
- Respect two-message loop rule—submit Attempt logs after supervisor review.
Pointers:
- plans/active/cli-noise-pix0/plan.md:164
- docs/fix_plan.md:452
- reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_summary.md
- golden_suite_generator/nanoBragg.c:2140
- docs/architecture/pytorch_design.md:200
- docs/development/testing_strategy.md:1
Next Up: Prep BeamConfig default fix and regression test updates for K3 once evidence lands.
