Timestamp: 2025-10-06 03:51:50Z
Commit: 2c424ed
Author: galph
Active Focus: [CLI-FLAGS-003] Phase F2 CUSTOM pix0 transform + parity rerun prep

Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py -k pix0 -v

If Blocked: Capture a fresh C/PyTorch parallel trace for the supervisor command, store it as reports/2025-10-cli-flags/phase_f/pix0_transform_blocked.md, and note the exact divergence before touching code again.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:74-79 — Phase F2 remains [P]; we must mirror nanoBragg.c CUSTOM math (Fclose/Sclose, rotations, distance recompute) before parity can move forward.
- docs/fix_plan.md:448-458 — Fix-plan next actions now explicitly demand F2 refit and fresh parity evidence; failing to follow breaks our coordination loop.
- docs/architecture/detector.md:35-120 — This section defines pivot-specific pix0 flows and coordinate conventions; implementation must align exactly to satisfy Core Rules 12–15.
- golden_suite_generator/nanoBragg.c:1733-1849 — The C reference shows the precise order of operations (ratio, close_distance, rotations, pix0 logging) we are missing; use it as the ground truth.
- reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/metrics.json — Attempt #12 shows correlation ≈−5e-06 and 116× intensity ratio; we must improve on that artifact and archive the follow-up run.
- docs/development/testing_strategy.md:25-92 — Authoritative commands + trace-first debugging reminders; keep AUTHORITATIVE_CMDS_DOC exported for every run.

How-To Map:
- Export NB_C_BIN first: `export NB_C_BIN=./golden_suite_generator/nanoBragg` to guarantee we hit the instrumented C binary when reproducing traces.
- Reproduce the C baseline using the full supervisor command (stored in docs/fix_plan.md and prompts/supervisor.md); capture stdout/stderr into reports/2025-10-cli-flags/phase_f2/c_baseline.log and copy DETECTOR_PIX0_VECTOR into the same directory.
- Implement the CUSTOM pix0 transform inside `_calculate_pix0_vector`: compute Fclose/Sclose from dot products, run through rotate/rotate_axis for SAMPLE pivot, and recompute `distance_corrected = close_distance / ratio` after you override close_distance.
- After code edits, run `env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py -k pix0 -v` (CPU) to ensure CLI coverage stays green; attach the log under reports/2025-10-cli-flags/phase_f2/pytest_pix0.log.
- If CUDA is available, repeat with `device=cuda` (`pytest tests/test_cli_flags.py -k pix0 --device cuda -v`) to respect device neutrality, or document unavailability in reports/2025-10-cli-flags/phase_f2/pytest_pix0_cuda.log.
- Validate geometry numerically: `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --config reports/2025-10-cli-flags/phase_e/trace_harness.yaml --pixel 1039 685 --out reports/2025-10-cli-flags/phase_f2/trace_after_transform.txt` and confirm pix0 + beam entries match C within ≤1e-12.
- Re-run parity smoke once F2 passes: `env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest --collect-only` (evidence step) followed by the full supervisor command in both C and PyTorch; stash metrics under reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/attempt13_metrics.json.
- Update docs/fix_plan.md Attempts and plans/active/cli-noise-pix0/plan.md (F2/F3 rows) with findings before ending the coding loop.

Pitfalls To Avoid:
- Do not re-introduce the early return in `_calculate_pix0_vector`; the override must flow through the shared pivot logic.
- Keep tensors on caller-supplied device/dtype; no `.cpu()`, `.numpy()`, or `.item()` in differentiable paths.
- Maintain vectorization; avoid new Python loops over pixels, phi steps, or thicksteps.
- Respect Protected Assets (docs/index.md) before editing or deleting referenced files.
- Follow prompts/debug.md rules for parity debugging; no ad-hoc shortcuts or trace-only rewrites.
- Do not delete or rename `scaled.hkl`, `scaled.hkl.1`, or other inputs until supervisor explicitly schedules hygiene.
- Ensure AUTHORITATIVE_CMDS_DOC stays exported for every pytest or parity invocation.
- Avoid inventing new scripts outside `scripts/`; reuse debug_pixel_trace.py and existing harnesses.
- Capture every significant run under `reports/2025-10-cli-flags/phase_f2/` or `/phase_f/` so plan evidence remains auditable.
- Remember -nonoise only suppresses noise image generation; base float/int outputs must still be written.

Pointers:
- plans/active/cli-noise-pix0/plan.md:74-99
- docs/fix_plan.md:448-520
- docs/architecture/detector.md:35-180
- docs/development/testing_strategy.md:25-120
- docs/debugging/debugging.md:20-120
- golden_suite_generator/nanoBragg.c:1733-1855
- reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/metrics.json
- reports/2025-10-cli-flags/phase_e/trace_summary.md
- prompts/supervisor.md: command block for parity harness

Next Up:
- Phase G — MOSFLM A* orientation retention (plan tasks G1–G3) once pix0 transform parity and parity smoke succeed.
- Phase H — Polarization parity (tasks H1–H3) after geometry aligns.
