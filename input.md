Summary: Execute Phase L3k to deliver the φ-rotation fix for CLI-FLAGS-003 before the supervisor parity rerun.
Mode: Docs
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py -k lattice
Artifacts: reports/2025-10-cli-flags/phase_l/implementation/; reports/2025-10-cli-flags/phase_l/rot_vector/per_phi/trace_py_phi_0.00.log; reports/2025-10-cli-flags/phase_l/rot_vector/per_phi/trace_py_scaling_per_phi.json; reports/2025-10-cli-flags/phase_l/rot_vector/pytest_lattice_$(date +%Y%m%d).log; reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix/summary.json; reports/2025-10-cli-flags/phase_l/rot_vector/rot_vector_comparison.md

Do Now: CLI-FLAGS-003 Phase L3k.1–L3k.3 — prepare the φ-rotation implementation memo, update the docstring, land the patch, then run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py -k lattice -v` after the fix.
If Blocked: Capture the failure (trace, traceback, or design question) in `reports/2025-10-cli-flags/phase_l/implementation/attempt_notes.md`, append an Attempt entry under docs/fix_plan.md with the obstacle, and stop without editing simulator code further.

Context Recap:
- `reports/2025-10-cli-flags/phase_l/rot_vector/rot_vector_comparison.md` still lists a +6.8% b_Y drift at φ=0.05°; closing Phase L3k must drive this delta below 1e-6.
- `reports/2025-10-cli-flags/phase_l/rot_vector/c_trace_mosflm.log` provides the verified C baseline (b_Y=0.71732 Å, k=-0.607) for all φ; diff all new traces against these values.
- `reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md` names `I_before_scaling` as the first divergence, so the φ fix must restore that intensity before Phase L4 metrics.
- `docs/fix_plan.md:465` logs Attempt #95 and the new L3k focus, ensuring the ledger is ready for the implementation Attempt once gates pass.
- `plans/active/cli-noise-pix0/plan.md:277` clarifies the Exit Criteria: docstring reference, all VG rows ✅, and synchronised plan/fix_plan updates.

Pre-Fix Validation Snapshot:
- `fix_checklist.md` rows remain ⏸️, signalling that no φ rotation fix has been validated yet.
- Per-φ traces (`per_phi/trace_py_phi_0.05.log`) currently show k_frac ≈ -0.589 vs C’s -0.607, confirming the magnitude of drift to eliminate.
- `pytest` lattice runs are green but still reflect the pre-fix behavior; expect failures if assertions are tightened later.
- nb-compare results from Previous Attempts show correlation ≈0.9965 and sum_ratio ≈1.26e5, underscoring the urgency of normalization repair.

Priorities & Rationale:
- `plans/active/cli-noise-pix0/plan.md:276` — Phase L3k now holds the implementation checklist; completing its rows unlocks Phase L4 parity work.
- `docs/fix_plan.md:450` — Next Actions explicitly call for Phase L3k.1–L3k.4; staying in sync with this ledger keeps Ralph’s attempts traceable.
- `reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md:13` — Verification gates (VG-1⇢VG-5) define the evidentiary bar for the φ rotation fix; each artifact must be refreshed post-patch.
- `specs/spec-a-cli.md:60` — Normative CLI spec confirms `-pix0_vector` semantics and CUSTOM convention side effects that the patch must respect.
- `docs/architecture/detector.md:35` — Detector pix0 workflow details the BEAM/SAMPLE formulas that must remain untouched while rotating about φ.
- `docs/development/testing_strategy.md:20` — Device/dtype discipline and targeted-test cadence apply once the patch is in place; record both CPU and CUDA outcomes if feasible.

How-To Map:
- Append a concise implementation note to `reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_correction.md` capturing the C snippet (nanoBragg.c ~2050–2199) and the intended PyTorch changes before editing code.
- Insert the mandatory C-code reference docstring in `src/nanobrag_torch/models/crystal.py` (targeting `get_rotated_real_vectors`) per CLAUDE Rule #11, then implement the φ pipeline fix while preserving vectorization/device neutrality.
- Regenerate per-φ traces via `cd reports/2025-10-cli-flags/phase_l/rot_vector && python trace_harness.py --phi 0.0 --output per_phi/trace_py_phi_0.00.log` (repeat for 0.05 and 0.10) and update `trace_py_scaling_per_phi.json`.
- Run the targeted regression `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py -k lattice -v 2>&1 | tee reports/2025-10-cli-flags/phase_l/rot_vector/pytest_lattice_$(date +%Y%m%d).log` to confirm lattice factors across φ.
- Execute the supervisor ROI comparison `nb-compare --roi 100 156 100 156 --resample --outdir reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix -- [supervisor flags]` with `NB_C_BIN` set, capturing summary metrics.
- Update `rot_vector_comparison.md`, mark each VG row ✅ inside `fix_checklist.md`, and log the completed Attempt with metrics (k_frac delta, b_Y delta, correlation, sum_ratio) in docs/fix_plan.md before moving to Phase L4.

Supervisor Command Reference:
```
nanoBragg -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0
```
- Use this exact flag set for nb-compare and trace harness parity; any deviation must be documented and justified in the Attempt notes.

Gate Outcome Targets:
- Correlation ≥0.9995 and sum_ratio 0.99–1.01 in `nb_compare_phi_fix/summary.json` (VG-3.2/3.3).
- |b_Y(C) − b_Y(Py)| ≤ 1e-6 Å and Δk_frac ≤ 1e-6 (VG-4.1/4.2) extracted from per-φ traces.
- `I_before_scaling` ratio within 0.99–1.01 according to `scaling_validation` logs (VG-4.4).
- No sign mismatches in `F_latt_b` across φ per the refreshed JSON export (VG-4.3).

Trace Fields Checklist:
- `TRACE_PY: rot_b_angstroms`, `TRACE_PY: k_frac`, `TRACE_PY: F_latt_b`, and `TRACE_PY: I_before_scaling` must appear for each φ sample.
- Confirm `TRACE_PY: phi_deg` matches the requested angle (0°, 0.05°, 0.1°) after the fix.
- Ensure `TRACE_PY: spindle_axis_raw/normalized` still report unit vectors (regression guard from Phase L3g).
- Verify HKL metadata (`h_min`, `k_min`, etc.) stays identical between harness and CLI after the new patch.

Documentation Updates Checklist:
- Append the implementation summary (with file:line references) to `mosflm_matrix_correction.md` under a "Post-Implementation" heading.
- Mark each VG row ✅ inside `fix_checklist.md`, adding links to the new artifacts.
- Add Attempt #96 entry to `docs/fix_plan.md` summarizing metrics and referencing all new logs.
- Note the plan completion in `plans/active/cli-noise-pix0/plan.md` by flipping L3k rows to [D] after artifacts are in place.

Metrics To Capture:
- Record correlation, RMSE, sum_ratio, and mean_peak_distance from `nb_compare_phi_fix/summary.json` in the Attempt notes.
- Capture k_frac, b_Y, and F_latt deltas for each φ angle in `rot_vector_comparison.md` tables.
- Log the exact pytest runtime and device/dtype matrix inside `pytest_lattice_*.log`.
- Store SHA256 hashes for key traces (`trace_py_phi_*.log`, `c_trace_mosflm.log`) to simplify future audits.

Attempt Logging Notes:
- Reference git SHA, date/time, and environment metadata in the Attempt entry to keep reproduction straightforward.
- Link to every new artifact (per-φ traces, pytest log, nb-compare summary, updated docs) so future reviewers can navigate quickly.
- Summarize whether each VG gate passed on first try or required rework; flag any deviations from spec tolerances.
- Indicate follow-up items (if any) for Phase L4 before marking Phase L3k complete.

Pitfalls To Avoid:
- `docs/index.md` lists protected assets; double-check before touching automation scripts or report directories.
- Skip Phase L3k.1 at your peril—add the C-code docstring reference before even staging code changes.
- Maintain differentiability/device neutrality (no `.item()`, implicit CPU tensors, or `.to("cpu")` shims inside physics loops).
- Preserve vectorization in `get_rotated_real_vectors`; no scalar loops or temporary Python lists when adjusting rotations.
- Use the canonical seeds/flags (`trace_harness.py` commands, supervisor ROI, `KMP_DUPLICATE_LIB_OK=TRUE`) so parity evidence remains comparable.
- Record artifacts + Attempt notes immediately after each gate to keep `docs/fix_plan.md` synchronized with the plan.

Pointers:
- `plans/active/cli-noise-pix0/plan.md:276` — Phase L3k overview plus Exit Criteria checklist.
- `reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md:13` — Gate definitions and artifact paths to tick ✅ after implementation.
- `reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_correction.md:150` — Extend the memo with the implementation summary and code references.
- `reports/2025-10-cli-flags/phase_l/rot_vector/rot_vector_comparison.md` — Update delta tables once the φ fix lands.
- `reports/2025-10-cli-flags/phase_l/rot_vector/c_trace_mosflm.log` — Use as the authoritative C baseline during trace diffs.
- `docs/development/c_to_pytorch_config_map.md:1` — Reinforces CLI↔config parity rules to keep pix0/noise semantics aligned with C.

Next Up:
1. Phase L4 — Run the supervisor command parity suite and archive artifacts once Phase L3k passes.
2. CLI noise toggle audit — revisit the `-nonoise` code path to confirm we still match C semantics with the new rotation fix.

Post-Fix Handoff:
- Ping supervisor with the new Attempt ID and artifact list so the next loop can verify Phase L4 readiness quickly.
- Stage updated docs (`mosflm_matrix_correction.md`, `fix_checklist.md`, plan) alongside code before committing to keep history coherent.
- Queue nb-compare artifacts for archival (`reports/archive/...`) once parity thresholds pass; note the archive path in fix_plan.
- Outline any residual questions (e.g., further detector conventions) in `implementation/notes.md` to inform follow-on work.
