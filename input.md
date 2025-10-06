# 2025-10-06 06:10:35Z | ba649f0 | galph
Active Focus: [CLI-FLAGS-003] Phase H lattice parity gating (beam vector fix landed, lattice evidence pending)
Summary: Capture new MOSFLM trace evidence after the beam-vector fix and map the remaining F_latt delta before authorising lattice code changes.
Phase: Evidence
Focus: plans/active/cli-noise-pix0/plan.md Phase H3 (trace rerun + lattice diagnosis)
Branch: feature/spec-based-2
Mapped tests: env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest tests/test_cli_flags.py::TestCLIBeamVector::test_custom_beam_vector_propagates -q
Artifacts: reports/2025-10-cli-flags/phase_h/trace_py_after_H2.log, reports/2025-10-cli-flags/phase_h/trace_py_after_H2.stderr, reports/2025-10-cli-flags/phase_h/trace_diff_after_H2.log, reports/2025-10-cli-flags/phase_h/trace_comparison_after_H2.md, reports/2025-10-cli-flags/phase_h/implementation_notes.md

Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — Execute Phase H3 trace parity workflow, then run mapped pytest node with env vars above.
If Blocked: If harness import or execution fails, capture stdout/stderr under reports/2025-10-cli-flags/phase_h/attempts/<timestamp>.log, run `pytest --collect-only -q` to prove discovery, and document the block plus log path in docs/fix_plan.md Attempt entry before stopping.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:96 — Phase H1/H2 closed; H3 is explicitly blocked on refreshed PyTorch trace evidence.
- docs/fix_plan.md:779 — Attempt #20 records simulator beam-vector delegation and orders the trace rerun before lattice tweaks.
- docs/debugging/debugging.md:22 — SOP mandates parallel trace comparison as the first action for any physics discrepancy.
- docs/development/testing_strategy.md:51 — Golden Suite definition requires PyTorch trace + diff artifacts per run.
- tests/test_cli_flags.py:302 — Regression test guarding the beam-vector path; running it validates the Evidence output.
- reports/2025-10-cli-flags/phase_h/trace_comparison.md — Existing divergence analysis baseline; must expand with after-H2 observations.
- docs/development/c_to_pytorch_config_map.md:15 — Confirms beam/detector config parity assumptions that underpin this trace.
- arch.md:213 — Detector/beam orientation contract; incident beam parity is prerequisite for lattice diagnosis.
- CLAUDE.md: Protected Assets rule prohibits touching docs/index.md entries while gathering evidence; recall before editing logs.
- plans/active/vectorization.md:1 (FYI) — Remains blocked until CLI parity completes; note to avoid scope drift.

How-To Map:
- Set env vars at shell start: `export KMP_DUPLICATE_LIB_OK=TRUE`; `export NANOBRAGG_DISABLE_COMPILE=1`; keep them for all following commands.
- Optional safety: `export NB_C_BIN=./golden_suite_generator/nanoBragg` so any future C reruns use the instrumented binary without extra prompts.
- Verify harness imports: `python -m compileall reports/2025-10-cli-flags/phase_h/trace_harness.py` to catch syntax issues before runtime (store success note in implementation_notes.md).
- Run PyTorch trace (stdout only): `python reports/2025-10-cli-flags/phase_h/trace_harness.py > reports/2025-10-cli-flags/phase_h/trace_py_after_H2.log 2> reports/2025-10-cli-flags/phase_h/trace_py_after_H2.stderr`.
- Immediately confirm incident beam line: `grep "TRACE_PY: incident_vec" reports/2025-10-cli-flags/phase_h/trace_py_after_H2.log` should print `0.00051387949 0 -0.99999986`.
- Capture Miller indices sanity check: `grep "TRACE_PY: hkl_frac"` and `grep "TRACE_PY: F_latt"` into implementation_notes.md with short comments (expected to mirror C soon).
- Diff vs C: `diff -u reports/2025-10-cli-flags/phase_g/traces/trace_c.log reports/2025-10-cli-flags/phase_h/trace_py_after_H2.log > reports/2025-10-cli-flags/phase_h/trace_diff_after_H2.log` (zero exit code ideal; non-zero still OK, document first differing token).
- If diff non-empty, open top hunk and record first divergence + magnitude in trace_comparison_after_H2.md (create file if absent) with bullet summary.
- Update reports/2025-10-cli-flags/phase_h/trace_comparison_after_H2.md: include headings for Incident Vector, h/k/l, F_latt, Intensity, referencing exact diff lines.
- Extend reports/2025-10-cli-flags/phase_h/implementation_notes.md with hypotheses (e.g., sincg argument vs NaNbNc scaling) and list follow-up calculations to run during implementation phase.
- Run mapped pytest: `pytest tests/test_cli_flags.py::TestCLIBeamVector::test_custom_beam_vector_propagates -q` and append pass/fail, runtime, and env string to reports/2025-10-cli-flags/phase_h/attempt_log.txt.
- After pytest, snapshot git status; if trace artifacts are large, ensure they are text; do not add binaries.
- Update docs/fix_plan.md `[CLI-FLAGS-003]` Attempt history with new evidence summary and artifact paths; note whether divergence resolved or persists (use bullet list per SOP).
- Optional cross-check (if time): load new trace into Python to compute `torch.allclose` vs C values for `rot_a_star`, `rot_b_star`, `rot_c_star`; log results in implementation_notes.md to justify focus on lattice vs other sources.
- Before finishing, confirm no code paths were edited; this loop should leave src/ untouched in git status.

Pitfalls To Avoid:
- Do not mutate `reports/2025-10-cli-flags/phase_h/trace_py.log`; keep original pre-fix artifact for regression history.
- Skip editing `plans/active/cli-noise-pix0/plan.md` outside logging new evidence; plan already marks H2 done.
- Avoid launching nb-compare or other heavy parity tools yet; Evidence phase is trace-only.
- No new pytest markers or parametrisation changes; stick to existing mapping.
- Do not clean up legacy artifacts (`trace_diff.log`, etc.); retention needed for audit trail.
- Prevent torch from defaulting to float32 by retaining dtype=torch.float64 in harness (no manual dtype tweaks).
- Resist the urge to chase polarization (Phase I); stay scoped to lattice evidence.
- Keep log files ASCII; no binary attachments in repo.
- If diff is empty, still document that result; absence of differences must be recorded to close H3 gating.
- Remember Protected Assets: never delete or rename files listed in docs/index.md (loop.sh, supervisor.sh, input.md, etc.).
- Maintain two-message limit per prompts/main.md; avoid re-running command without new rationale in attempt_log.
- Do not rely on interactive editors requiring GUI; use CLI-friendly tools only.

Pointers:
- plans/active/cli-noise-pix0/plan.md:96 — Phase H task table with gating criteria.
- docs/fix_plan.md:763 — Last logged evidence and required next steps.
- docs/debugging/debugging.md:22 — Step-by-step parallel trace SOP reference.
- docs/development/testing_strategy.md:51 — Golden Suite artifact requirements to satisfy Evidence gate.
- tests/test_cli_flags.py:302 — Regression test verifying beam-vector propagation path.
- reports/2025-10-cli-flags/phase_h/trace_comparison.md — Pre-fix divergence analysis to extend.
- docs/architecture/pytorch_design.md:145 — Detector/beam orientation ADR for context when reviewing incident vectors.
- golden_suite_generator/nanoBragg.c:3063 — C reference for F_latt calculations; cite when forming hypotheses.
- reports/2025-10-cli-flags/phase_g/traces/trace_c.log — Ground truth C trace for diffing (do not overwrite).
- docs/development/pytorch_runtime_checklist.md:12 — Device/dtype neutrality checklist to keep in mind when interpreting trace tensors.

Next Up:
- [CLI-FLAGS-003] Phase H3 implementation: adjust sincg usage or Na/Nb/Nc scaling once evidence captured.
- [CLI-FLAGS-003] Phase H4 parity rerun: nb-compare + float image validation after lattice fix lands.

Diagnostic Checklist:
- Verify `reports/2025-10-cli-flags/phase_h/trace_py_after_H2.stderr` only contains harness banner lines; note any warnings explicitly.
- Confirm `pixel_pos_meters` values stay within 1e-6 of C trace by manual comparison (record max delta in implementation_notes.md).
- Check `omega_pixel` and `obliquity_factor` entries to ensure detector geometry unchanged post-fix.
- Ensure `scattering_vec_A_inv` magnitude aligns with C; compute diff norm using `python - <<'PY'` snippet and log result.
- Inspect `hkl_rounded` tuple to confirm (2,2,-13); any deviation must be documented with raw floats.
- Recalculate `F_cell` from HKL cache (via Crystal.get_structure_factor) to rule out caching regressions.
- Review `F_latt_a/b/c` individually; if only one axis diverges, note which Na/Nb/Nc factor is suspect.
- Validate `I_before_scaling` and `I_pixel_final` both reflect squared amplitude (should match (F_cell*F_latt)^2 path).
- Confirm `fluence_photons_per_m2` line equals 1e24; mismatch hints at beam config drift.
- Cross-check `steps`, `oversample_*`, and `capture_fraction` output to ensure simulator loop counts unchanged.
- If diff empty, explicitly state "No divergence; beam and lattice parity achieved" in trace_comparison_after_H2.md.
- If diff persists, capture screenshot-equivalent by quoting first differing lines in Markdown for future debugging.

Reporting Requirements:
- Update docs/fix_plan.md Attempt log with bullet list: incident_vec status, hkl_frac delta, F_latt delta, intensity delta, pytest result.
- Note artifact filenames and command strings in Attempt log for reproducibility.
- Mention coin flip result (heads) in galph_memory.md for traceability of supervisory review cadence.
- Append new entry to reports/2025-10-cli-flags/phase_h/attempt_log.txt with timestamp, commands, results, and TODOs.
- If hypotheses identified (e.g., sincg argument), enumerate them with priority, confidence, next step inside implementation_notes.md.
- For any unexpected warnings or non-zero exit codes, include raw command output in evidence files.
- Keep new Markdown files under 120 columns width for readability; wrap long numeric explanations by inserting manual line breaks.
- Double-check git diff before handing back; ensure only reports/fix_plan/plan/input.md changed.
- When editing docs/fix_plan.md, retain existing chronology and add new Attempt number sequentially.
- Annotate any manual calculations (e.g., sin comparisons) with formula so future loops can verify quickly.

Context Reminders:
- Long-term Goal 1 still depends on successful execution of the 40+ parameter supervisor command; this evidence step unlocks final parity run.
- Long-term Goal 2 (vectorization) remains queued; do not attempt Phase A evidence this turn.
- Gradcheck initiative stays untouched; no gradient tests should be run during this loop.
- Protected Assets rule (CLAUDE.md:26) applies—never delete or rename files listed in docs/index.md during cleanup.
- Ensure `input.md` is not edited by Ralph; only galph writes this file each loop.
- Remember that CLI harness expects `A.mat` and `scaled.hkl` in repo root; verify they remain pristine post-trace.
- Torch default dtype should stay float32 globally, but trace harness explicitly uses float64; avoid altering dtype defaults.
- Keep `prompts/main.md` loop count increments accurate; record any unusual agent behavior in galph_memory.md.
- Refrain from pushing commits until evidence recorded; supervisor commits happen after documentation updates only.
- Document any outstanding questions for lattice mismatch so next implementation loop starts with clear targets.
