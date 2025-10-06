Summary: Restore MOSFLM lattice scaling so the supervisor CLI parity command matches nanoBragg C
Phase: Implementation
Focus: CLI-FLAGS-003 / Phase K3g1–K3g3
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py::test_f_latt_square_matches_c
Artifacts: reports/2025-10-cli-flags/phase_k/base_lattice/summary.md; reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/trace_py.log; reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/summary.md; reports/2025-10-cli-flags/phase_k/f_latt_fix/pytest_post_fix.log; reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain.md
Do Now: Execute CLI-FLAGS-003 – Phase K3g1 (Crystal MOSFLM rescale) and run `env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest tests/test_cli_scaling.py::test_f_latt_square_matches_c -v`
If Blocked: Update `reports/2025-10-cli-flags/phase_k/base_lattice/summary.md` with blocker notes, rerun `trace_harness.py` + `compare_traces.py` for delta capture, and log the setback in docs/fix_plan before pausing.

Priorities & Rationale:
- specs/spec-a-core.md §Geometry — Canonical flow: remove wavelength, cross products, multiply by `V_cell`, convert to meters; PyTorch must follow this to keep h/k/l parity.
- specs/spec-a-core.md §Units — Confirms Å ↔ meters conversions; real vectors must be Angstroms before conversion.
- golden_suite_generator/nanoBragg.c:3135-3210 — MOSFLM branch in C; instrumented logs show `V_cell≈2.4682×10^4 Å^3` and |a|≈26.75 Å before Angstrom→meter conversion.
- plans/active/cli-noise-pix0/plan.md (Phase K3f/K3g) — Documents Δh≈6 root cause and codifies the fix/test pipeline we must follow.
- docs/fix_plan.md#cli-flags-003 — Next Actions now reference Phase K3g tasks; completion evidence must feed Attempt #46.
- docs/development/c_to_pytorch_config_map.md — Verifies detector pivot and unit expectations so geometry edits don’t regress previous parity wins.
- docs/development/testing_strategy.md §2.5 — Authoritative parity commands; mandates `NB_RUN_PARALLEL=1` + C binary for scaling regression.
- reports/2025-10-cli-flags/phase_k/base_lattice/c_stdout.txt — C trace snapshot; use as ground truth for expected vectors/volumes.

How-To Map:
- Step 1 — Documentation prep (K3f4):
  - Open `reports/2025-10-cli-flags/phase_k/base_lattice/summary.md`.
  - Add a “Root Cause” section summarising that PyTorch leaves `V=1 Å^3` when MOSFLM A* is provided, while C recomputes `V_cell≈2.4682×10^4 Å^3` then rescales `b*×c*` before converting to meters.
  - Reference the specific trace lines from `c_stdout.txt` and `trace_py.log` when describing the magnitude mismatch (≈40.5× in reciprocal vectors, ≈4.05×10^5 in real vectors).
- Step 2 — Code modification (K3g1) inside `src/nanobrag_torch/models/crystal.py`:
  - Detect the MOSFLM branch (existing `mosflm_provided` logic) and introduce C-reference docstring citing nanoBragg.c lines 3135-3210 before implementation.
  - Convert raw MOSFLM vectors to tensors on `self.device` / `self.dtype` without breaking gradients.
  - Compute cross products (`b_star × c_star`, `c_star × a_star`, `a_star × b_star`) and `V_star = a_star · (b_star × c_star)`.
  - Derive `V_cell = 1 / V_star` (Å³) and multiply each cross product by `V_cell` to obtain real vectors in Angstroms before any conversion.
  - Update `self.cell_a`, `self.cell_b`, `self.cell_c` (Å) using the resulting magnitudes so sample clipping continues to operate on real dimensions.
  - Convert real vectors to meters by multiplying by `1e-10`, store them in tensors used downstream, and retain differentiability (no `.item()` usages).
  - Recompute reciprocal vectors from the real vectors using `V_actual = a · (b × c)` to maintain metric duality (`a·a* = 1`, etc.).
  - Ensure geometry cache invalidation still occurs when these tensors change (reuse existing cache logic or clear `_geometry_cache`).
- Step 3 — Regression coverage (K3g2):
  - Extend `tests/test_cli_scaling.py` or introduce a dedicated test file to assert that PyTorch’s MOSFLM-derived real vectors (converted to Å) match C values within 5e-4 per component.
  - Include comments pointing to `reports/2025-10-cli-flags/phase_k/base_lattice/c_stdout.txt` as the authoritative data source.
  - Guard the test so it runs on CPU by default but maintains device neutrality (parametrise over available devices if practical).
- Step 4 — Parity harness refresh:
  - `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_k/base_lattice/trace_harness.py --out reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/trace_py.log`.
  - `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_k/base_lattice/compare_traces.py --c reports/2025-10-cli-flags/phase_k/base_lattice/c_stdout.txt --py reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/trace_py.log --out reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/summary.md`.
  - Verify the diff summary shows |Δh|, |Δk|, |Δl| < 5e-4 and document the metrics in the summary file.
- Step 5 — Scaling regression (K3g3 + K3c):
  - Run `env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest tests/test_cli_scaling.py::test_f_latt_square_matches_c -v`.
  - Save the pytest log to `reports/2025-10-cli-flags/phase_k/f_latt_fix/pytest_post_fix.log`.
  - Update `reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain.md` with new ratios (F_latt, polarization, I_final) comparing PyTorch vs C, and note the restored parity.
  - Prepare nb-compare visuals if useful and store in an appropriate `post_fix/` subfolder.
- Step 6 — Fix-plan bookkeeping:
  - Append Attempt #46 (or next attempt number) in docs/fix_plan once parity evidence is archived.
  - Mention the updated artifacts and command outputs when logging the attempt.

Pitfalls To Avoid:
- Leaving `V` at the placeholder value (`1 Å^3`) when MOSFLM A* vectors are present; this is the core bug causing Δh ≈ 6.
- Forgetting to convert real vectors from Å to meters after rescaling; `Crystal.a`/`b`/`c` must remain meters for downstream physics.
- Using `.item()` or `.numpy()` on differentiable tensors; keep everything as tensors to preserve gradients per Core Rule #7.
- Allocating tensors on CPU while device is CUDA; use `.to(device=self.device)` or `.type_as()` to stay device/dtype neutral.
- Modifying pix0 override precedence or pivot logic; custom detector vectors must continue to force SAMPLE pivot and ignore `pix0_override`.
- Skipping reciprocal vector regeneration; without this step metric duality breaks and later tests will fail.
- Running the entire pytest suite; only run the targeted scaling node plus harness scripts to conserve loop time.
- Omitting `KMP_DUPLICATE_LIB_OK=TRUE` or `NB_RUN_PARALLEL=1`; parity command depends on both environment variables.
- Writing new tooling outside `reports/` or `scripts/validation/`; comply with Protected Assets and existing directory conventions.
- Neglecting to add/keep C-code references (Core Rule #11) when altering critical physics code.

Pointers:
- specs/spec-a-core.md — Units & geometry canonical reference.
- docs/architecture/pytorch_design.md §§2.3-2.4 — Crystal pipeline description & vectorization expectations.
- golden_suite_generator/nanoBragg.c:3135-3210 — MOSFLM handling baseline.
- plans/active/cli-noise-pix0/plan.md — Phase K3f/K3g tables, exit criteria, artifact expectations.
- docs/fix_plan.md#cli-flags-003 — Next Actions + Attempts log for this effort.
- reports/2025-10-cli-flags/phase_k/base_lattice/c_stdout.txt — C trace with authoritative lattice vectors.
- reports/2025-10-cli-flags/phase_k/base_lattice/trace_harness.py — PyTorch trace generator (already float64 & CPU by default).
- reports/2025-10-cli-flags/phase_k/base_lattice/compare_traces.py — Diff script to quantify Δh/Δk/Δl post-fix.
- tests/test_cli_scaling.py — Targeted scaling regression; extend here for MOSFLM assertions.
- docs/development/testing_strategy.md §2.5 — Environment and parity command mapping.

Next Up:
- If MOSFLM scaling parity succeeds quickly, close Phase K3c documentation and then resume vectorization plan Phase A.
- If issues persist, capture updated Δh/Δk/Δl data under `base_lattice/post_fix/` and request follow-up guidance before touching downstream phases.
