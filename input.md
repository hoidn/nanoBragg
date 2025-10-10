Summary: Capture instrumented C TRACE_C logs for the failing 4096² parity case.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2026-01-vectorization-parity/phase_c/<STAMP>/{commands.txt,env/trace_env.json,c_traces/pixel_*.log}
Do Now: VECTOR-PARITY-001 Phase C1 — capture TRACE_C logs via the λ=0.5 Å / distance=500 mm 4096² command (see How-To Map) and run pytest --collect-only -q after any Python trace edits.
If Blocked: If the instrumented binary fails to build, stash the patch, write the compiler error to reports/2026-01-vectorization-parity/phase_c/<STAMP>/attempts/compile_failure.log, and revert the C edits before re-running the warm benchmark command.
Priorities & Rationale:
- docs/fix_plan.md:40 — Phase C1 directs guarded TRACE_C taps for the three target pixels.
- plans/active/vectorization-parity-regression.md:50 — Phase C1 checklist defines pixel set and output paths.
- reports/2026-01-vectorization-parity/phase_c/20251010T040739Z/trace_plan.md:62 — Pixel classes and acceptance criteria for the trace bundle.
- docs/development/testing_strategy.md:30 — Do Now requires an explicit pytest selector; collect-only run guards import health after scripting changes.
How-To Map:
- Set STAMP=$(date -u +%Y%m%dT%H%M%SZ) and mkdir -p reports/2026-01-vectorization-parity/phase_c/$STAMP/{c_traces,env} ; tee commands.txt in that directory with every build/run command used.
- Add or refresh TRACE_C print taps in golden_suite_generator/nanoBragg.c so pix0_vector, pixel_pos, scattering_vec_A_inv, hkl_frac, F_cell, F_latt, omega_pixel, steps, capture_fraction, and final intensity emit when tracing (match trace_plan schema); keep guards on trace_spixel/trace_fpixel.
- Rebuild instrumented binary: `(cd golden_suite_generator && make clean && make nanoBragg)`; verify NB_C_BIN points at ./golden_suite_generator/nanoBragg.
- For each pixel (2048,2048), (1792,2048), (4095,2048): run `NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE ./golden_suite_generator/nanoBragg -default_F 100 -cell 100 100 100 90 90 90 -lambda 0.5 -distance 500 -pixel 0.05 -detpixels 4096 -N 5 -convention MOSFLM -oversample 1 -trace_pixel {slow} {fast} -floatfile /tmp/c_trace_{slow}_{fast}.bin > reports/2026-01-vectorization-parity/phase_c/$STAMP/c_traces/pixel_{slow}_{fast}.log 2>&1`.
- Capture environment facts: `python - <<'PY'` block that dumps git SHA, python/torch versions, and KMP_DUPLICATE_LIB_OK into reports/2026-01-vectorization-parity/phase_c/$STAMP/env/trace_env.json.
- After any Python trace-hook edits (e.g., wiring pixel arguments into scripts/debug_pixel_trace.py), run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` and append the exit status to commands.txt.
Pitfalls To Avoid:
- Do not point NB_C_BIN at the frozen ./nanoBragg; always rebuild and use the golden_suite_generator binary.
- Keep TRACE_C logs raw; avoid piping through grep or truncating precision.
- Do not commit the instrumented C changes—capture logs, then leave the diff unstaged for review.
- Ensure KMP_DUPLICATE_LIB_OK=TRUE is set for every long-running command to prevent MKL crashes.
- Store outputs only under reports/…; never drop binaries or logs in tracked directories.
- Confirm trace_spixel/trace_fpixel stays within bounds (0–4095) before running the full frame.
- Avoid mixing devices in future PyTorch trace hooks; stay on CPU float64 per trace_plan guidance.
- Re-run make clean before rebuilding to guarantee the trace code is linked.
Pointers:
- docs/fix_plan.md:40
- plans/active/vectorization-parity-regression.md:50
- reports/2026-01-vectorization-parity/phase_c/20251010T040739Z/trace_plan.md:76
- docs/development/testing_strategy.md:32
Next Up: Phase C2 — extend scripts/debug_pixel_trace.py to emit matching TRACE_PY logs for the same pixel set.
