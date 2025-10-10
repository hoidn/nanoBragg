Summary: Capture C-side 4096² pixel traces for Phase C1 of the parity investigation.
Mode: Parity
Focus: VECTOR-PARITY-001 Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_c/<STAMP>/{c_traces,commands.txt,env.json}
Do Now: VECTOR-PARITY-001 — Phase C1 C-trace: instrument `golden_suite_generator/nanoBragg.c` for pixels (2048,2048)/(1791,2048)/(4095,2048), rebuild via `make -C golden_suite_generator nanoBragg`, then run `NB_C_BIN=./golden_suite_generator/nanoBragg ./golden_suite_generator/nanoBragg -default_F 100 -cell 100 100 100 90 90 90 -lambda 0.5 -distance 500 -pixel 0.05 -detpixels 4096 -N 5 -convention MOSFLM -oversample 1 -floatfile /tmp/c_trace.bin 2>&1 | tee reports/2026-01-vectorization-parity/phase_c/<STAMP>/c_traces/pixel_<slow>_<fast>.log | grep TRACE_C:` for each pixel.
If Blocked: Capture the failing compiler/run output under `reports/2026-01-vectorization-parity/phase_c/<STAMP>/attempts/blocked.log`, revert the instrumentation snippets, and log the issue in docs/fix_plan.md Attempt notes before stopping.
Priorities & Rationale:
- docs/fix_plan.md:19 – Next Action #3 explicitly requires Phase C1 C traces on the λ=0.5, distance=500 mm setup.
- plans/active/vectorization-parity-regression.md:12 – Phase C is blocked until C/Py traces exist for (2048,2048), (1791,2048), (4095,2048).
- reports/2026-01-vectorization-parity/phase_c/20251010T040739Z/trace_plan.md:53 – Trace plan locks pixel selection and target tap points for Phase C.
- docs/debugging/debugging.md:51 – Parallel trace SOP mandates a C trace before PyTorch instrumentation.
- docs/development/testing_strategy.md:51 – Tier 1 translation correctness depends on golden C trace logs.
How-To Map:
- Set `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and `OUTDIR=reports/2026-01-vectorization-parity/phase_c/$STAMP`; create `$OUTDIR/c_traces` and `$OUTDIR/attempts` (if needed).
- In `golden_suite_generator/nanoBragg.c`, wrap trace prints in `if (spixel == S && fpixel == F)` blocks for each target pixel; include tap points listed in the trace plan (pix0_vector, pixel_pos, diffracted_vec, scattering_vec_A_inv, hkl_frac, F_cell, F_latt, omega_pixel, steps, intensity).
- Rebuild the instrumented binary: `make -C golden_suite_generator nanoBragg` (ensure `NB_C_BIN` points to the rebuilt executable).
- For each pixel tuple `"2048 2048"`, `"1792 2048"`, `"4095 2048"`, run:
  `slow=...; fast=...; NB_C_BIN=./golden_suite_generator/nanoBragg ./golden_suite_generator/nanoBragg -default_F 100 -cell 100 100 100 90 90 90 -lambda 0.5 -distance 500 -pixel 0.05 -detpixels 4096 -N 5 -convention MOSFLM -oversample 1 -floatfile /tmp/c_trace.bin 2>&1 | tee $OUTDIR/c_traces/pixel_${slow}_${fast}.log | grep "TRACE_C:" > /dev/null`.
- Append the exact commands executed to `$OUTDIR/commands.txt` and record environment metadata (git SHA, NB_C_BIN path, compiler flags) in `$OUTDIR/env.json`.
- Leave instrumentation in place for the next Py trace loop but keep the logs untracked; update docs/fix_plan.md Attempt history with artifact paths when finished.
Pitfalls To Avoid:
- Do not widen the trace beyond the three approved pixels; guard conditions must stay tight to avoid multi-GB logs.
- Keep `NB_C_BIN` pointing at the instrumented binary (not the frozen root `./nanoBragg`).
- Ensure the command uses λ=0.5 Å, distance=500 mm, pixel=0.05 mm exactly; no rounding or unit drift.
- Do not commit the trace logs or instrumented binary; only reference paths under `reports/`.
- Avoid altering spec/arch files or Protected Assets while instrumenting.
- Stay on CPU; no CUDA-specific flags during this evidence run.
- After rebuilding, confirm `make` rebuilt cleanly; if compilation fails, revert edits before rerunning.
- Document any deviations (missing tap, alternate path) immediately in `$OUTDIR/attempts/notes.md` and fix_plan Attempt entry.
- Preserve differentiability guardrails—do not refactor simulator logic while adding prints.
- Maintain reproducible timestamps (UTC) for directory names and logs.
Pointers:
- docs/fix_plan.md:19
- plans/active/vectorization-parity-regression.md:12
- reports/2026-01-vectorization-parity/phase_c/20251010T040739Z/trace_plan.md:53
- docs/debugging/debugging.md:51
- docs/development/testing_strategy.md:51
Next Up: Once C traces land, extend `scripts/debug_pixel_trace.py` for Phase C2 Py traces.
