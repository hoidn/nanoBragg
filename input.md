Summary: Restore pix0 parity by correcting beam-center unit handling before normalization work resumes.
Phase: Implementation
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_flags.py::TestCLIPix0Override
Artifacts: reports/2025-10-cli-flags/phase_h5/unit_fix/
Do Now: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm — env KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_flags.py::TestCLIPix0Override
If Blocked: Capture pre/post traces with the harness, summarise deltas in reports/2025-10-cli-flags/phase_h5/unit_fix/attempts.md, then log the stall in docs/fix_plan.md Attempts History before escalating.
Priorities & Rationale:
- docs/fix_plan.md:448-462 mandates finishing Phase H5 (esp. H5e) prior to touching normalization tasks.
- plans/active/cli-noise-pix0/plan.md:123-129 enumerates H5e deliverables (unit fix, trace evidence, Attempt #33 log).
- src/nanobrag_torch/models/detector.py:500-512 currently multiplies mm beam centers by pixel size (m), recreating the 1.1 mm ΔF measured in reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/diff_notes.md.
- src/nanobrag_torch/__main__.py:906-931 shows Xbeam/Ybeam stay in mm, so Detector must convert before geometry math.
- specs/spec-a-cli.md:1-120 emphasises CLI geometry inputs are mm-based, aligning this fix with spec compliance.
How-To Map:
- Step 1 — Pre-flight reference: open reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/diff_notes.md to note the baseline ΔF, ΔS, ΔO that must fall below 5e-5 m.
- Step 2 — Implementation: within src/nanobrag_torch/models/detector.py (BEAM pivot branch) replace the pixel-scale multiplication with explicit mm→m conversion: convert beam_center_f/s via `/ 1000.0` (or `torch.tensor(..., dtype=...) / 1000`) before applying MOSFLM offsets; ensure tensors stay on detector device/dtype.
- Step 3 — Consistency audit: update any comments/docstrings around lines 500-512 to explain the unit conversion and cite nanoBragg.c:1184-1239 so future audits understand the mapping.
- Step 4 — Trace capture (post-fix):
  • `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py --out reports/2025-10-cli-flags/phase_h5/unit_fix/trace_py_post.log`
  • Optionally rerun the pre-fix trace (rename to trace_py_pre.log) if you need a local diff; do not overwrite existing archives.
  • Use `python reports/2025-10-cli-flags/phase_h5/tools/diff_trace.py --a reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/trace_py.log --b reports/2025-10-cli-flags/phase_h5/unit_fix/trace_py_post.log --out reports/2025-10-cli-flags/phase_h5/unit_fix/trace_diff.md` (create tool if missing, or diff manually and paste results into trace_diff.md).
- Step 5 — Metric summary: append a new section to reports/2025-10-cli-flags/phase_h5/parity_summary.md capturing before/after pix0 deltas, Fbeam/Sbeam values, and confirming <5e-5 m parity; stash any supplemental calculations in unit_fix/analysis.ipynb or .md.
- Step 6 — Regression test: `env KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_flags.py::TestCLIPix0Override | tee reports/2025-10-cli-flags/phase_h5/unit_fix/pytest.log`.
- Step 7 — Attempts log: record Attempt #33 in docs/fix_plan.md under CLI-FLAGS-003 with metrics (ΔF, ΔS, ΔO, test results, trace paths) and link to the new artifacts.
- Step 8 — Plan bookkeeping: flip H5e to [D] in plans/active/cli-noise-pix0/plan.md, confirm H5c tolerance satisfied, and note readiness for Phase K1 in reports/2025-10-cli-flags/phase_h5/unit_fix/README.md.
Pitfalls To Avoid:
- Do not re-enable pix0 overrides when custom vectors are present—the H5b guard remains mandatory.
- Avoid converting inside tight loops; perform mm→m once per configuration to keep vectorization intact.
- Keep tensors differentiable—no `.item()`, `.detach()`, or CPU-only literals in the geometry path.
- Respect device neutrality; use `.to(device=self.device, dtype=self.dtype)` when materialising new tensors.
- Maintain Protected Assets (docs/index.md); do not relocate/delete anything referenced there.
- Do not run nb-compare or full parity suites until pix0 and F_latt both meet tolerances.
- Skip fire-and-forget pushes; ensure Attempt entry and artifact paths exist before committing.
- Remember KMP_DUPLICATE_LIB_OK=TRUE for every python/pytest invocation touching torch.
- Keep comments succinct—update existing docstrings rather than adding narrative in code blocks.
- Check trace harness commits into reports/ only; never place new tooling under random folders.
Pointers:
- docs/fix_plan.md:448-462 — refreshed Next Actions referencing H5e unit correction.
- plans/active/cli-noise-pix0/plan.md:123-160 — Phase H5e task plus upcoming Phase K outline.
- src/nanobrag_torch/models/detector.py:500-580 — BEAM pivot pix0 assembly awaiting unit fix.
- src/nanobrag_torch/__main__.py:906-931 — shows beam centers stored in mm, validating conversion requirement.
- reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/diff_notes.md — baseline trace proving current ΔF≈-1.136e-03 m.
- specs/spec-a-cli.md:1-200 — canonical CLI units and precedence reminders.
- docs/architecture/detector.md (Section 5) — reinforcement of meter internal representation.
- docs/debugging/debugging.md:1-160 — parallel trace SOP to follow while comparing traces.
Next Up (optional): Phase K1 — swap the SQUARE lattice factor to sincg(π·h, Na) and capture updated scaling traces once H5e closes.
