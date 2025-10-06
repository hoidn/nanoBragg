Summary: Restore MOSFLM lattice scaling so the supervisor parity command matches nanoBragg C
Phase: Implementation
Focus: CLI-FLAGS-003 / Phase K3g1–K3g3
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py::test_f_latt_square_matches_c
Artifacts: reports/2025-10-cli-flags/phase_k/base_lattice/summary.md; reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/trace_py.log; reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/summary.md; reports/2025-10-cli-flags/phase_k/f_latt_fix/pytest_post_fix.log; reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain.md
Do Now: Execute CLI-FLAGS-003 – Phase K3g1 (Crystal MOSFLM rescale) and run `env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest tests/test_cli_scaling.py::test_f_latt_square_matches_c -v`
If Blocked: Update `reports/2025-10-cli-flags/phase_k/base_lattice/summary.md` with blocker notes, rerun `trace_harness.py` + `compare_traces.py` to capture new deltas, and log the stall in docs/fix_plan before pausing.

Priorities & Rationale:
- specs/spec-a-core.md §Geometry — Defines the canonical order: remove wavelength from MOSFLM matrix, compute cross products, scale by `V_cell`, then convert to meters. We must mirror this to keep h/k/l parity.
- specs/spec-a-core.md §Units — Reiterates Å to meter conversions; forgetting the `1e-10` factor caused the current Δh≈6 gap.
- golden_suite_generator/nanoBragg.c:3135-3210 — C implementation shows `V_star = a*·(b*×c*)`, `V_cell = 1/V_star`, and real vectors in Å before conversion. Use as the implementation template.
- reports/2025-10-cli-flags/phase_k/base_lattice/c_stdout.txt — Contains the instrumented C trace proving |a|=26.7514 Å and |a|=2.67514e-9 m after conversion; matches the spec.
- plans/active/cli-noise-pix0/plan.md — Phase K3f table now marked `[D]`, Phase K3g defines the implementation + regression steps we must execute.
- docs/fix_plan.md#cli-flags-003 — Next Actions cite Phase K3g1–K3g3; completion evidence must feed Attempt #46.
- docs/development/c_to_pytorch_config_map.md — Validates detector pivot + unit conventions to avoid regressions when editing `Crystal.compute_cell_tensors`.
- docs/development/testing_strategy.md §2.5 — Parity matrix commands; keep `NB_RUN_PARALLEL=1` and `NB_C_BIN=./golden_suite_generator/nanoBragg` in environment.

How-To Map:
- Step 1 — Document the diagnosis (K3f4):
  - Edit `reports/2025-10-cli-flags/phase_k/base_lattice/summary.md`.
  - Add a “Root Cause” section describing the 40.5× reciprocal and 4.05×10^5 real-vector magnitude errors.
  - Cite the specific lines from `c_stdout.txt` and `trace_py.log` showing `V_cell` vs `V_python`.
  - Mention that PyTorch leaves `self.cell_a/b/c = 1 Å`, so `V = 1 Å^3`, which causes the mismatch.
- Step 2 — Implement MOSFLM rescale (K3g1):
  - In `Crystal.compute_cell_tensors`, locate the existing `mosflm_provided` conditional.
  - Add a C-reference docstring citing nanoBragg.c lines 3135-3210 to satisfy Core Rule #11.
  - Convert each MOSFLM reciprocal vector into a tensor via `torch.as_tensor(..., device=self.device, dtype=self.dtype)`.
  - Compute `b_star_cross_c_star = torch.cross(b_star, c_star, dim=0)`.
  - Compute `c_star_cross_a_star = torch.cross(c_star, a_star, dim=0)`.
  - Compute `a_star_cross_b_star = torch.cross(a_star, b_star, dim=0)`.
  - Evaluate `V_star = torch.dot(a_star, b_star_cross_c_star)`.
  - Clamp `V_star` away from zero (e.g., `V_star = V_star.clamp_min(1e-18)`) to avoid blow-ups.
  - Derive `V_cell = 1.0 / V_star` (Å³) just like C.
  - Form `a_vec_ang = b_star_cross_c_star * V_cell` (Å).
  - Form `b_vec_ang = c_star_cross_a_star * V_cell` (Å).
  - Form `c_vec_ang = a_star_cross_b_star * V_cell` (Å).
  - Update `self.cell_a = torch.norm(a_vec_ang)` (Å).
  - Update `self.cell_b = torch.norm(b_vec_ang)` (Å).
  - Update `self.cell_c = torch.norm(c_vec_ang)` (Å).
  - Convert to meters: `a_vec = a_vec_ang * 1e-10`, same for `b_vec` and `c_vec`.
  - Calculate `a_cross_b = torch.cross(a_vec, b_vec, dim=0)`.
  - Calculate `b_cross_c = torch.cross(b_vec, c_vec, dim=0)`.
  - Calculate `c_cross_a = torch.cross(c_vec, a_vec, dim=0)`.
  - Compute `V_actual = torch.dot(a_vec, b_cross_c)` for metric duality.
  - Rebuild reciprocal vectors: `a_star = b_cross_c / V_actual`, etc.
  - Replace previous placeholder `V = 1 Å^3` with the actual `V_cell` (Å³) and keep `V_actual` (m³) as needed.
  - Reset `_geometry_cache = {}` to invalidate cached tensors.
- Step 3 — Regression coverage (K3g2):
  - Extend `tests/test_cli_scaling.py` (or add a new test module) to assert that PyTorch’s MOSFLM real vectors (converted back to Å) match the C trace within 5e-4 per component.
  - Load expected vectors directly from the plan (hard-coded constants) and include comments referencing `c_stdout.txt` for traceability.
  - Parameterize over available devices (`cpu`, `cuda` when available) to maintain device neutrality, but allow skipping if CUDA is unavailable.
  - Add assertions that the recomputed `V_cell` matches `24682.3 Å^3` within tolerance when MOSFLM inputs are used.
- Step 4 — Refresh parity traces:
  - Run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_k/base_lattice/trace_harness.py --out reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/trace_py.log`.
  - Execute `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_k/base_lattice/compare_traces.py --c reports/2025-10-cli-flags/phase_k/base_lattice/c_stdout.txt --py reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/trace_py.log --out reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/summary.md`.
  - Confirm the summary reports |Δh|, |Δk|, |Δl| < 5e-4 and document the metrics.
  - Archive the new PyTorch trace and diff summary alongside the existing evidence (`post_fix/` subdir).
- Step 5 — Scaling regression and documentation (K3g3 + K3c):
  - Run `env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest tests/test_cli_scaling.py::test_f_latt_square_matches_c -v`.
  - Save output to `reports/2025-10-cli-flags/phase_k/f_latt_fix/pytest_post_fix.log`.
  - Update `reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain.md` with new F_latt, polarization, and final intensity ratios.
  - Note in the write-up that the previous 21.6% F_latt error disappears once MOSFLM vectors are rescaled.
  - Generate nb-compare visuals if helpful and store them under `reports/2025-10-cli-flags/phase_k/f_latt_fix/post_fix/`.
- Step 6 — Fix-plan bookkeeping:
  - Log Attempt #46 (or next number) in docs/fix_plan summarising commands run, metrics observed, and artifact paths.
  - Cross-link the plan updates (Phase K3g rows) and confirm exit criteria are met.

Pitfalls To Avoid:
- Leaving `self.cell_a/b/c` at placeholder values; downstream sample clipping and gradient logic depend on accurate Å magnitudes.
- Forgetting to convert real vectors from Å to meters, which would flip the error sign instead of fixing it.
- Using `.item()`/`.numpy()` on tensors that require gradients; keep operations tensorised.
- Creating tensors on CPU when running on CUDA; always inherit device/dtype from existing tensors.
- Disturbing pix0 precedence rules (custom vectors force SAMPLE pivot, ignoring pix0 override).
- Skipping reciprocal regeneration; metric duality (`a·a* = 1`) must hold to avoid regressions elsewhere.
- Running the full pytest suite; stick to targeted nodes to keep the loop efficient.
- Forgetting `KMP_DUPLICATE_LIB_OK=TRUE` or `NB_RUN_PARALLEL=1`; parity command will fail without them.
- Writing ad-hoc scripts or storing artifacts outside `reports/`; follow existing directory structure and Protected Assets policy.
- Omitting the required C-code reference in `Crystal.compute_cell_tensors` when modifying MOSFLM logic.
- Ignoring device/dtype neutrality; keep operations vectorized and free of `.cpu()`/`.cuda()` shims inside the compiled path.

Pointers:
- specs/spec-a-core.md — Units, geometry, and lattice derivation rules.
- docs/architecture/pytorch_design.md §§2.3-2.4 — Crystal pipeline overview, highlighting where MOSFLM data should enter.
- golden_suite_generator/nanoBragg.c:3135-3210 — Exact MOSFLM sequence to replicate.
- plans/active/cli-noise-pix0/plan.md — Phase K3g table & exit criteria after today’s update.
- docs/fix_plan.md#cli-flags-003 — Active fix-plan entry with updated Next Actions.
- reports/2025-10-cli-flags/phase_k/base_lattice/c_stdout.txt — C trace ground truth for vectors and volumes.
- reports/2025-10-cli-flags/phase_k/base_lattice/trace_harness.py — PyTorch trace generator (float64, CPU) used for parity evidence.
- reports/2025-10-cli-flags/phase_k/base_lattice/compare_traces.py — Diff script to validate |Δh|, |Δk|, |Δl| thresholds.
- tests/test_cli_scaling.py — Scaling regression; extend for MOSFLM assertions.
- docs/development/testing_strategy.md §2.5 — Test command mapping for parity runs.

Next Up:
- If MOSFLM scaling parity succeeds, close Phase K3c documentation, then resume the vectorization initiative (plans/active/vectorization.md Phase A evidence).
- If parity still fails, capture updated Δh/Δk/Δl metrics under `base_lattice/post_fix/` and request follow-up guidance before touching downstream phases.
- After parity is stable, re-run the supervisor command end-to-end (per long-term goal) and archive nb-compare artifacts for final verification.
- Record any lingering questions in docs/fix_plan Attempts so future loops retain context.
- Once this goal completes, reassess long-term goal #2 (vectorization) to schedule Phase A baseline tasks.
