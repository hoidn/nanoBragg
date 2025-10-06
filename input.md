Summary: Align the PyTorch SQUARE lattice factor with the nanoBragg.c reference so the supervisor command can finally run end-to-end.
Phase: Implementation
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm (Phase K1 SQUARE F_latt fix)
Branch: feature/spec-based-2
Mapped tests: planned tests/test_cli_scaling.py::test_f_latt_square_matches_c | existing tests/test_cli_flags.py::TestCLIPix0Override (sanity)
Artifacts: reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after.log
Artifacts: reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_c_after.log
Artifacts: reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain_after.md
Artifacts: reports/2025-10-cli-flags/phase_k/f_latt_fix/pytest.log
Do Now: CLI-FLAGS-003 Phase K1 — Align SQUARE F_latt with C; author tests/test_cli_scaling.py::test_f_latt_square_matches_c then run `env KMP_DUPLICATE_LIB_OK=TRUE NB_C_BIN=./golden_suite_generator/nanoBragg pytest tests/test_cli_scaling.py::test_f_latt_square_matches_c -v`
If Blocked: Capture a delta table with `scripts/debug_flatt_difference.py` and park the attempt under reports/2025-10-cli-flags/phase_k/f_latt_fix/attempts/, then log the stall and metrics in docs/fix_plan.md before calling for help.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:160 spells out Phase K1, so finishing that row is prerequisite to every downstream parity task.
- specs/spec-a-core.md:218 defines SQUARE lattice factor as Π sincg(π·h, Na), making `(h-h0)` a spec violation that we must remove.
- golden_suite_generator/nanoBragg.c:3069-3079 is the authoritative C loop; the PyTorch branch has to match those sincg arguments exactly.
- docs/fix_plan.md:484-497 (Attempt #28) already diagnosed the 463× F_latt gap; ignoring it blocks the top long-term goal.
- reports/2025-10-cli-flags/phase_j/trace_py_scaling.log still shows F_latt≈7.69e1 instead of 3.56e4, proving the bug remains live.
- docs/development/testing_strategy.md:37-120 requires targeted pytest automation and evidence, not manual screenshots.

How-To Map:
- Step 0a — Ensure editable install is current (`pip install -e .` already done; rerun only if dependencies changed last loop).
- Step 0b — Export `NB_C_BIN=./golden_suite_generator/nanoBragg` before any parity command.
- Step 0c — Every python/pytest invocation must include `KMP_DUPLICATE_LIB_OK=TRUE` to avoid MKL conflicts.
- Step 1a — Copy baseline traces (`trace_py_scaling.log`, `trace_c_scaling.log`) into the Phase K directory so before/after comparisons sit next to each other.
- Step 1b — Note the baseline F_latt components from Attempt #28 in a scratchpad for later diffing.
- Step 2a — In `src/nanobrag_torch/simulator.py:200-280`, replace each `sincg(torch.pi * (h - h0), Na)` with `sincg(torch.pi * h, Na)` while preserving Na>1 guards.
- Step 2b — Do the same for k and l branches; double-check that temporary tensors stay on `h.device` to maintain device neutrality.
- Step 2c — Update the block docstring right above the lattice factor to include the nanoBragg.c snippet per Core Rule #11 before touching code.
- Step 2d — Ensure the diagnostic trace block (the one gated by debug flag near line 1258) also prints the updated values using the same formula.
- Step 3a — Run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_flatt_difference.py > reports/2025-10-cli-flags/phase_k/f_latt_fix/delta_table.txt` to confirm old vs new ratios collapse to ~1.
- Step 3b — Execute `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_flatt_implementation.py > reports/2025-10-cli-flags/phase_k/f_latt_fix/implementation_check.txt` for sanity on triclinic samples.
- Step 4a — Regenerate the PyTorch scaling trace: `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_scaling_pipeline.py --pixel 1039 685 --out reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after.log`.
- Step 4b — Regenerate the matching C trace via `KMP_DUPLICATE_LIB_OK=TRUE NB_C_BIN=./golden_suite_generator/nanoBragg ./scripts/trace_c_at012_pixel.sh 1039 685 > reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_c_after.log` (adjust script params if required and note it in README).
- Step 4c — Run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_j/analyze_scaling.py --py reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after.log --c reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_c_after.log --out reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain_after.md` to confirm the first divergence disappears.
- Step 5a — Author `tests/test_cli_scaling.py` (if absent) with `test_f_latt_square_matches_c`, parametrize over device (cpu/cuda) and dtype (float32/float64) when feasible.
- Step 5b — Within that test, drive PyTorch + C via the existing scaling harness (respect NB_C_BIN) and assert |ratio-1| < 1e-3 for F_latt and I_before_scaling as spelled out in plan row K3.
- Step 5c — Run `env KMP_DUPLICATE_LIB_OK=TRUE NB_C_BIN=./golden_suite_generator/nanoBragg pytest tests/test_cli_scaling.py::test_f_latt_square_matches_c -v | tee reports/2025-10-cli-flags/phase_k/f_latt_fix/pytest.log`.
- Step 5d — Re-run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override -v | tee -a reports/2025-10-cli-flags/phase_k/f_latt_fix/pytest.log` as a guardrail to ensure the pix0 work stays green.
- Step 6a — Update `reports/2025-10-cli-flags/phase_k/README.md` with bullet points summarising trace results, ratios, and pytest outcomes.
- Step 6b — Add Attempt #34 to docs/fix_plan.md (CLI-FLAGS-003 section) capturing metrics, trace paths, and the new regression test.
- Step 6c — Flip Phase K1 to [D] in plans/active/cli-noise-pix0/plan.md and note readiness for Phase K2.
- Step 6d — Commit artifacts under reports/…; do not store large binaries outside this folder hierarchy.

Pitfalls To Avoid:
- Leaving `(h-h0)` anywhere in code or traces will reintroduce the 463× error—double-check before final diff.
- Creating new CPU tensors during CUDA runs will crash the targeted pytest; always reuse device from existing tensors.
- Forgetting Na>1 guards will yield NaN/Inf when reflections sit exactly on integers; copy C conditional logic precisely.
- Adding unconditional print statements in hot loops will tank performance and break vectorization tests.
- Skipping the docstring C snippet violates Core Rule #11; add it before editing implementation lines.
- Running nb-compare now wastes time; parity check happens after Phase K completes.
- Forgetting to set `NB_C_BIN` will silently fall back to the wrong binary; always export before commands.
- Missing Attempt log or plan updates will force redo loops; capture evidence before pushing.
- Deleting or moving anything listed in docs/index.md (Protected Assets) is prohibited.
- Introducing `.item()` on differentiable tensors (e.g., Na) would break gradients; stay tensor-native.

Pointers:
- plans/active/cli-noise-pix0/plan.md:160-162 — Phase K checklist we are executing now.
- specs/spec-a-core.md:218 — Formal SQUARE lattice factor formula to cite in docstring.
- golden_suite_generator/nanoBragg.c:3069-3079 — C code to mirror inside simulator.
- docs/fix_plan.md:484-511 — Attempt history confirming F_latt as root cause and listing required artifacts.
- reports/2025-10-cli-flags/phase_j/scaling_chain.md — Baseline ratios to update post-fix.
- src/nanobrag_torch/simulator.py:200-280 — Current PyTorch implementation to adjust.
- docs/architecture/pytorch_design.md:420-470 — Physics pipeline narrative to keep aligned with code changes.
- docs/debugging/debugging.md:1-160 — Parallel trace SOP; follow during trace comparison.
- docs/development/testing_strategy.md:37-120 — Command sourcing and targeted test policy.
- scripts/debug_flatt_implementation.py:1-160 — Supplemental harness verifying sincg parity.
- scripts/debug_scaling_pipeline.py:1-200 — Scaling trace generator referenced above.

Next Up: After Phase K1 passes, move straight to Phase K2 (scaling-chain refresh) before attempting Phase L nb-compare.

Evidence Targets:
- F_latt ratio (Py/C) within 1e-3 at pixel (1039,685) documented in scaling_chain_after.md.
- I_before_scaling ratio (Py/C) within 1e-3 recorded in the same report.
- Traces should show `TRACE_PY: F_latt` ≈ 3.56e4; diff against C trace must read `< 5e-3 relative` in each component line.
- pytest log must include both cpu and cuda parametrisations with a `@pytest.mark.cuda` skip guard.
- Attempt #34 entry should list artifact paths and cite reports/2025-10-cli-flags/phase_k/f_latt_fix/.
- Updated docstring should embed the exact nanoBragg.c snippet with line numbers to simplify future audits.

Gradient Safeguards:
- Run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_gradients.py::TestCrystal::test_tricubic_gradient -k "square"` if available to confirm no regressions.
- If gradients fail, stash the diff, revert to previous commit locally, and log the failure before proceeding.
- Ensure new tensors are created via `torch.as_tensor(Na, device=h.device, dtype=h.dtype)` rather than bare constructors.

Reporting Checklist:
- Update reports/2025-10-cli-flags/phase_k/README.md with bullet points for implementation notes, metrics, and follow-up.
- Store any scratch notebooks under reports/…/notebooks/ to keep repo tidy.
- If scripts needed tweaks, capture those diffs and mention them explicitly in docs/fix_plan.md.

Communication Notes:
- Mention in docs/fix_plan.md whether CUDA run was executed or skipped (with reason) for transparency.
- Flag any lingering pix0 deltas in parity_summary.md even if below tolerance to preserve traceability.
- Call out in plan update whether normalization work (Phase K2) is now unblocked.

Sanity Cross-Checks:
- Compare new sincg outputs against numpy equivalent in debug harness to guard against dtype surprises.
- Verify that `Simulator._compute_physics_for_position` still returns the same shape tensors when oversample>1.
- Confirm the code path remains compilation-friendly (no new Python loops) for future torch.compile work.

Archive Guidance:
- Do not delete existing Phase J artifacts; create Phase K directory sibling and cross-link from README.
- Include md5 sums or short metrics table in scaling_chain_after.md for easier diffing later.
- If new helper functions are necessary, place them in `nanobrag_torch/utils/physics.py` with tests and doc citations.

Ready-to-Publish Signals:
- `nb-compare` should not be touched yet; wait for supervisor go/no-go after reviewing scaling_chain_after.md.
- Once supervisor signs off, prepare to trigger Phase K2 tasks (re-run scaling chain on other shapes) immediately.
