Summary: Convert rotated lattice vectors to m⁻¹, rerun ROI parity, and retire NB_TRACE_SIM_F_LATT once metrics clear.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity — Phase D5
Branch: feature/spec-based-2
Mapped tests: pytest tests/test_at_parallel_012.py::test_high_resolution_variant -v
Artifacts: reports/2026-01-vectorization-parity/phase_d/$STAMP/roi_compare_post_fix/; reports/2026-01-vectorization-parity/phase_d/$STAMP/phase_d_summary.md; reports/2026-01-vectorization-parity/phase_d/$STAMP/py_traces_post_fix/pixel_1792_2048.log; reports/2026-01-vectorization-parity/phase_d/$STAMP/commands.txt; reports/2026-01-vectorization-parity/phase_d/$STAMP/env/trace_env.json
Do Now: docs/fix_plan.md item 10 (Phase D5 — Apply fix + parity smoke); after implementing the 1e10 Å→m⁻¹ conversion, run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/nb_compare.py --resample --roi 1792 2304 1792 2304 --outdir reports/2026-01-vectorization-parity/phase_d/$STAMP/roi_compare_post_fix -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05` followed by `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_parallel_012.py::test_high_resolution_variant -v`.
If Blocked: Capture a fresh NB_TRACE_SIM_F_LATT log reproducing the mismatch, park it under reports/2026-01-vectorization-parity/phase_d/$STAMP/blockers/ with notes, and halt for supervisor review.
Priorities & Rationale:
- docs/fix_plan.md:58 — Phase D5 exit criteria demand the lattice-vector unit fix plus ROI metrics within spec.
- plans/active/vectorization-parity-regression.md:64 — Plan now locks D4 as closed and points D5 at the 1e10 conversion before Phase E can proceed.
- specs/spec-a-core.md:43 & :135 — Spec states q is in m⁻¹ and requires cell vectors scaled by 1e-10 for dot products with q.
- reports/2026-01-vectorization-parity/phase_d/20251010T073708Z/simulator_f_latt.md — Attempt #14 evidence proving the h/k/l unit mismatch and the recommended fix.
- arch.md:70-73 — Architecture ADR-01 highlights the meters↔Å boundary we must treat consistently.
How-To Map:
1. `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; create `reports/2026-01-vectorization-parity/phase_d/$STAMP/{}` directories as needed.
2. Edit `src/nanobrag_torch/simulator.py` so the rotated lattice vectors passed into `_compute_physics_for_position` are scaled by `1e10` (Å→m⁻¹) without breaking broadcasting or device/dtype neutrality; keep the NB_TRACE_SIM_F_LATT guard intact.
3. `KMP_DUPLICATE_LIB_OK=TRUE NB_TRACE_SIM_F_LATT=1 python scripts/debug_pixel_trace.py --pixel 1792 2048 --tag post_fix --out-dir reports/2026-01-vectorization-parity/phase_d/$STAMP/py_traces_post_fix` (reuse prior commands.txt template) and verify h/k/l match the C trace within ≤1e-12.
4. Run the ROI parity command listed in Do Now; stash `summary.json`, `summary.md`, raw bins, and `commands.txt` under `$STAMP/roi_compare_post_fix/`.
5. `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_parallel_012.py::test_high_resolution_variant -v` and archive the log beside `phase_d_summary.md` with corr/sum_ratio annotations.
6. Remove or disable NB_TRACE_SIM_F_LATT instrumentation once parity is green; rerun `pytest --collect-only -q` to ensure the suite still collects.
7. Update docs/fix_plan.md Attempts + Next Actions and log the new bundle in attempts history.
Pitfalls To Avoid:
- Do not downcast tensors or detach gradients when applying the 1e10 factor; keep device/dtype neutrality.
- Avoid per-element Python loops; rely on existing batched tensors for rot_a/b/c.
- Do not leave NB_TRACE_SIM_F_LATT prints active by default after verification.
- Preserve ROI ordering `(slow, fast)` in nb-compare arguments.
- Keep the trace helper unchanged apart from updating outputs; no re-derivation of fluence or sincg.
- No full pytest run; stick to the mapped selector plus collect-only sanity check.
- Do not touch protected assets listed in docs/index.md.
- Maintain the same STAMP naming convention so reports stay discoverable.
- Confirm updated code still honours `KMP_DUPLICATE_LIB_OK=TRUE` env handling.
Pointers:
- docs/fix_plan.md:58 — Phase D5 task definition and thresholds.
- plans/active/vectorization-parity-regression.md:64 — Phase D table with D4 closure and D5 guidance.
- reports/2026-01-vectorization-parity/phase_d/20251010T073708Z/simulator_f_latt.md — Prior diagnosis transcript to mirror.
- specs/spec-a-core.md:135 — Canonical Å→m scaling requirement for lattice vectors.
Next Up: If parity lands quickly, prep Phase E1 full-frame rerun (benchmark + high-res pytest) per plans/active/vectorization-parity-regression.md.
