Summary: Refresh the Py scaling trace using the full supervisor flag set so Phase L2 comparison reflects the real command.
Mode: Parity
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm
Branch: main
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log; reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_env.json; reports/2025-10-cli-flags/phase_l/scaling_audit/notes.md
Do Now: CLI-FLAGS-003 — run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --out reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log --device cpu --dtype float32` and capture fresh notes on scaling factors.
If Blocked: copy stderr/stdout plus command into reports/2025-10-cli-flags/phase_l/scaling_audit/attempt_log.md, annotate the obstacle in Attempts History, and halt pending supervisor guidance.
Context Reminders:
- Phase L2 remained inconclusive because prior traces omitted -beam_vector and auto-selected oversample=4, corrupting h/k/l and scaling factors.
- The supervisor command in reports/2025-10-cli-flags/phase_i/supervisor_command/README.md is the authoritative template; mirror it exactly.
- plans/active/cli-noise-pix0/plan.md documents the parity journey; refresh Phase L tables after generating new evidence.
- docs/development/c_to_pytorch_config_map.md stresses SAMPLE pivot when custom vectors appear; confirm harness output obeys that rule.
- specs/spec-a-cli.md §3.2 lists required CLI flags; every value in the supervisor command must appear in the harness parameter dict or CLI call.
- docs/architecture/detector.md §5.3 describes pix0 precedence; retaining SAMPLE pivot ensures pix0 parity remains validated once scaling is fixed.
- docs/development/testing_strategy.md §2 requires reproducible commands for evidence; archive the rerun details under reports/2025-10-cli-flags/phase_l/.
- Trace environment snapshots should include Python, torch, device, dtype, and git SHA so future loops know the context of the evidence.
- The existing C trace `c_trace_scaling.log` already covers pixel (685,1039); Py trace must target the same coordinates.
- Reports under phase_l are shared assets; add new files, do not overwrite C artifacts.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md Phase L2b pre-step (added 2025-11-11) demands a trace harness rerun with the full flag set before any normalization diagnosis resumes.
- docs/fix_plan.md:458-467 elevates Phase L2b0 to the top of the action list; satisfying that checkpoint unblocks instrumentation follow-ups.
- Existing Py trace shows `incident_vec 0 0 1` proving the command omitted the custom beam vector; the rerun must demonstrate the correct beam direction.
- Steps currently read 160 (auto oversample 4×4); rerunning with `-oversample 1` verifies PyTorch honors the CLI override and aligns with the C log.
- Fluence discrepancies (~1e29) were side-effects of missing `-flux`/`-beamsize`; including those flags tests the true normalization chain.
- Polarization reported as 1.0; with a correct beam vector we expect ≈0.9146 as in C, validating `_apply_polarization` output.
- pix0 parity already validated post Phase H6; keeping SAMPLE pivot via custom vectors ensures geometry stays locked while scaling is debugged.
- CLI -nonoise flag suppresses noise path; including it keeps runtime short and avoids unnecessary SMV writes in evidence mode.
- Running the harness consolidates artifacts under phase_l, satisfying the evidence chain mandated by testing_strategy.md §2.1.
- The rerun feeds into L2c comparison; without this data we cannot identify the first divergence accurately.
How-To Map:
- From repo root export `PYTHONPATH=src` (or prefix the command) so the harness finds the installed package modules.
- Ensure `KMP_DUPLICATE_LIB_OK=TRUE` prefixes the command to dodge libomp initialization crashes.
- Use CPU + float32 for this pass; record runtime so a future float64/CUDA rerun can be compared if needed.
- Command options: `--config supervisor` selects the embedded supervisor parameter set; no manual flag editing required.
- `--pixel 685 1039` uses slow, fast ordering to match C trace fields; double-check this before running.
- `--out .../trace_py_scaling.log` overwrites the stale trace; stash the previous file if you need historical reference before rerun.
- Confirm `A.mat` and `scaled.hkl` sit in repo root; the harness reads them directly.
- After execution open `trace_py_env.json` and verify timestamp, device, dtype, and git SHA updated.
- Append a short delta summary (steps, fluence, polar, capture_fraction) to `notes.md`; note any remaining divergence vs C.
- If the harness raises missing HKL range warnings, delete any stale `.hkl.1` copies and rerun so the loader finds the canonical file.
Verification Checklist:
- [ ] Command executed with PYTHONPATH and KMP env vars set.
- [ ] Harness stdout/stderr captured into the reports directory.
- [ ] trace_py_scaling.log regenerated and reflects the new beam vector and steps count.
- [ ] trace_py_env.json refreshed with current timestamp/device/dtype.
- [ ] notes.md updated with comparison metrics versus C trace.
- [ ] No additional artifacts leaked outside reports/2025-10-cli-flags/phase_l/.
Pitfalls To Avoid:
- Do not edit simulator or detector source files this turn; evidence only.
- Avoid running the full parity script (`nb-compare`) until the trace is trustworthy.
- Keep tensor operations device-neutral—no `.cpu()` when inspecting results in notes.
- Do not regenerate C traces; the existing log remains ground truth for Phase L2.
- Respect Protected Assets: leave docs/index.md, loop.sh, supervisor.sh untouched.
- Refrain from running `pytest` suites; evidence-mode allows `--collect-only` at most, which is unnecessary here.
- Ensure the working directory remains clean apart from the refreshed reports files.
- Do not convert notes to Markdown tables; stick with ASCII bullet/paragraph for quick diffs.
- Double-check the harness uses SAMPLE pivot (detector config shows DetectorPivot.SAMPLE) before trusting pix0 parity.
- Remember to retain the old trace file in version control history; no manual backups needed outside git.
Additional Guidance:
- If CUDA testing becomes necessary later, reuse the same harness with `--device cuda --dtype float32` after confirming GPU availability.
- Consider copying the old trace to `trace_py_scaling_prev.log` before overwriting if you want an immediate diff; otherwise rely on git.
- If runtime exceeds expectations, use `time` command wrapper to log execution duration next to the trace.
- After updating notes.md, include a mini-table or bullet list summarizing steps/polar/fluence differences versus the C trace for quick reference.
- Capture any unexpected warnings (e.g., HKL cache rebuild) in notes.md so subsequent loops know the context.
- Should you notice a mismatch in pix0 or beam centers, flag it immediately—geometry regressions must be halted before normalization work.
- Keep an eye on memory usage; if the harness strains RAM, narrow the ROI inside the script before rerunning (document the tweak).
- Use `git status` after the run to ensure only intended artifacts changed; if other files appear, investigate before proceeding.
- Update Attempts History with the rerun details (command, runtime, high-level deltas) once artifacts are saved.
- Prepare to hand the refreshed data into Phase L2c by noting which factor diverges first after the rerun.
Pointers:
- plans/active/cli-noise-pix0/plan.md (Phase L2 table) — authoritative checklist for scaling parity.
- docs/fix_plan.md:458-467 — supervisor item status and updated next steps.
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log — C reference factors.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log — Py trace to regenerate and compare.
- specs/spec-a-cli.md §3.2 — CLI flag behaviour and precedence rules for this command.
Next Up: Once the new trace confirms the authoritative command, tackle Phase L2b instrumentation regression test (`tests/test_trace_pixel.py::test_scaling_trace_matches_physics`) before moving to L2c diff tooling.
Reference Commands:
- To compare traces quickly later, prepare `python scripts/validation/diff_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log` (implementation pending Phase L2c).
- For sanity, `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch --help | head` reminds which flags the CLI exposes if questions arise mid-run.
- Use `git rev-parse HEAD` after the rerun to embed the commit SHA in notes.md for traceability.
- `ls -lh reports/2025-10-cli-flags/phase_l/scaling_audit/` helps verify file sizes changed as expected (trace log should update timestamp and size).
- `tail -n 60 reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log` should show the refreshed beam vector, steps, F_latt, fluence, and intensity fields.
- The C log can be inspected quickly via `grep -n "F_latt" reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log` for cross-checking values mentioned in notes.
- If you need to sanity-check HKL coverage, `head -n 20 scaled.hkl` will confirm the file is present and not empty.
- In case `trace_harness.py` raises module import errors, run `pip install -e .` to reestablish the editable install (document in Attempts if executed).
- To double-check oversample handling, search the simulator with `rg "auto-selected" src/nanobrag_torch/simulator.py` and confirm it no longer triggers once oversample=1 is set.
- When updating notes, include a pointer to docs/fix_plan.md Attempt #27 so the new findings sit alongside prior evidence.
Documentation Hooks:
- Mention in notes the exact commit SHA and date of this rerun for future archaeological digs.
- Cross-link the note entry to `plans/active/cli-noise-pix0/plan.md` Phase L2b so the engineer loop can trace provenance.
- If fluence remains mismatched, cite the relevant BeamConfig lines (src/nanobrag_torch/config.py around 430-470) in the note.
- Document any difference in `hkl_frac` vs C; specify whether the first divergence is still in fractional indices or in scaling terms.
- Record the observed `polar` value and relate it to the expected 0.9146 from C to show improvement/regression.
- Highlight changes in `steps` value; note if oversample stayed at 1 or reverted to auto selection.
- Note capture_fraction even if it remains 1.0; state that thickness absorption remains disabled.
- For completeness, mention `omega_pixel` difference (should remain within sub-percent of C).
- If `F_cell` reads 0, investigate HKL lookup in `crystal.get_structure_factor` and log the suspicion for Phase L3.
- Clarify whether the incident vector equals `[5.1388e-04, 0.0, -1.0]`; quote the log line so others can grep quickly.
Audit Trail: update docs/fix_plan.md Attempt log after the rerun so future loops know Phase L2b0 is satisfied.
