timestamp: 2025-10-06T07:48:25Z
commit: 3c24855
author: galph
Active Focus: CLI-FLAGS-003 Phase H3b1 — capture pix0 override evidence

Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm (Phase H3b1) — gather paired C/Py traces via `NB_C_BIN=./golden_suite_generator/nanoBragg` and `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py`

If Blocked: If either trace command aborts, stash the stderr/stdout under `reports/2025-10-cli-flags/phase_h/implementation/blocked/` and record the failure in Attempts History before falling back to `pytest --collect-only -q`.

Priorities & Rationale:
- `plans/active/cli-noise-pix0/plan.md:96` — H3b now demands fresh override evidence before detector edits resume.
- `docs/fix_plan.md:458` — Next Actions call for dual trace runs plus a comparison memo.
- `reports/2025-10-cli-flags/phase_h/implementation/implementation_notes.md` — Attempt #22 documents why the projection scheme failed; today’s work replaces it with measured data.
- `docs/debugging/debugging.md:20` — Parallel trace discipline requires C and PyTorch artifacts before theorizing fixes.
- `docs/development/testing_strategy.md:32` — Evidence loops prioritize authoritative repro commands over speculative tests.

How-To Map:
- `export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md` and `export KMP_DUPLICATE_LIB_OK=TRUE` at the start of the loop.
- With override (C): run the full supervisor command from `prompts/supervisor.md` using `NB_C_BIN=./golden_suite_generator/nanoBragg`, redirect stdout to `reports/2025-10-cli-flags/phase_h/implementation/c_trace_with_override.log` (tee the console if helpful), and move any generated images into the same directory.
- Without override (C): rerun the same command but drop `-pix0_vector_mm`; capture to `c_trace_without_override.log` alongside the first log.
- With override (Py): `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py > reports/2025-10-cli-flags/phase_h/implementation/trace_py_with_override.log 2>&1`.
- Without override (Py): temporarily set `pix0_vector_mm = None` (or guard with an env flag) in the harness before rerunning to `trace_py_without_override.log`, then restore the file.
- Summarise the deltas (Fbeam/Sbeam/Fclose/Sclose/close_distance/pix0) in `reports/2025-10-cli-flags/phase_h/implementation/pix0_mapping_analysis.md`.

Pitfalls To Avoid:
- Don’t touch detector code or tests until H3b1 artifacts exist.
- Keep outputs under `reports/2025-10-cli-flags/phase_h/implementation/`; avoid cluttering repo root.
- Leave `scaled.hkl` / other Protected Assets untouched.
- Maintain device/dtype neutrality in any quick probes (use `PYTHONPATH=src`).
- Restore `trace_harness.py` after the no-override run; commit only deliberate edits.
- Skip full pytest sweeps; this loop is evidence-only.
- Document any script tweaks in Attempt log so the next loop knows what changed.
- Ensure `KMP_DUPLICATE_LIB_OK` is present for every Python invocation.
- Capture NB_C_BIN output even if the command times out; we need the partial trace.
- Do not delete the previously generated `pix0_expected.json`.

Pointers:
- `plans/active/cli-noise-pix0/plan.md:103` — H3b1 task definition.
- `docs/fix_plan.md:458` — Updated Next Actions for this item.
- `reports/2025-10-cli-flags/phase_h/implementation/implementation_notes.md:1` — Prior attempt summary for context.
- `prompts/supervisor.md:1` — Canonical parallel command parameters.
- `docs/debugging/debugging.md:20` — Trace workflow reference.

Next Up: Once H3b1 artifacts land, move to H3b2 to rework `Detector._calculate_pix0_vector` with the measured mapping.
