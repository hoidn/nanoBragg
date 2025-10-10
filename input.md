Summary: Capture Tap 5.2 HKL bounds parity so both implementations prove (0,0,0) lives inside the loaded grid.
Mode: Parity
Focus: VECTOR-PARITY-001 Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2026-01-vectorization-parity/phase_e0/<STAMP>/bounds/, reports/2026-01-vectorization-parity/phase_e0/<STAMP>/comparison/, reports/2026-01-vectorization-parity/phase_e0/<STAMP>/env/
Do Now: Execute docs/fix_plan.md item [VECTOR-PARITY-001] Next Action 1 (Tap 5.2 HKL bounds parity); emit `TRACE_PY_HKL_BOUNDS` and `TRACE_C_HKL_BOUNDS`, capture logs for pixels (0,0) and (2048,2048), summarise in tap5_hkl_bounds.md, then run pytest --collect-only -q.
If Blocked: Archive the attempted instrumentation diff plus stderr output under `reports/2026-01-vectorization-parity/phase_e0/<STAMP>/bounds/attempt_log.md`, revert the binary to its previous TRACE_C_TAP5 state, and note blockers in comparison/tap5_hkl_bounds.md.
Priorities & Rationale:
- docs/fix_plan.md:72 — Next Action 1 now targets Tap 5.2 HKL bounds; completing it unblocks the oversample accumulation probe.
- plans/active/vectorization-parity-regression.md:94 — Phase E14 requires matched `[h_min,h_max]` etc. before Phase E15 instrumentation can start.
- plans/active/vectorization.md:17 — VECTOR-TRICUBIC backlog stays gated until Tap 5 bounds/accumulation evidence lands.
- specs/spec-a-core.md:232 — HKL lookup semantics demand we prove `(0,0,0)` is in range when no HKL file is loaded.
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ); OUTDIR=reports/2026-01-vectorization-parity/phase_e0/$STAMP
- mkdir -p "$OUTDIR"/bounds "$OUTDIR"/comparison "$OUTDIR"/env "$OUTDIR"/bounds/py "$OUTDIR"/bounds/c
- PyTorch bounds tap: extend `scripts/debug_pixel_trace.py` with `--taps hkl_bounds` that records `[h_min,h_max]`, `[k_min,h_max]`, `[l_min,l_max]`, and `default_F` for pixels (0,0) and (2048,2048). Command:
  `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python scripts/debug_pixel_trace.py --taps hkl_bounds --pixel 0 0 --out-dir "$OUTDIR"/bounds/py`
  and repeat with `--pixel 2048 2048`. Each run should write JSON/LOG pairs plus append to `$OUTDIR/bounds/py/commands.txt`.
- C bounds tap: add a `TRACE_C_HKL_BOUNDS` guard near the existing HKL lookup (around lines 3320-3345) that prints the six bounds and `default_F` once per traced pixel. Rebuild with `make -C golden_suite_generator nanoBragg`. Capture logs:
  `TRACE_C_HKL_BOUNDS=1 ./golden_suite_generator/nanoBragg -cell 100 100 100 90 90 90 -lambda 0.5 -distance 500 -detpixels 4096 -pixel 0.05 -mosflm -oversample 2 -default_F 100 -N 5 -trace_pixel 0 0 -roi 0 0 0 0 -floatfile /tmp/tap5_bounds_edge.bin > "$OUTDIR"/bounds/c/pixel_0_0_bounds.log 2>&1`
  and repeat with `-trace_pixel 2048 2048 -roi 2048 2048 2048 2048` writing `pixel_2048_2048_bounds.log`.
- Summarise results in `$OUTDIR/comparison/tap5_hkl_bounds.md` (one table per implementation, note whether `(0,0,0)` is inside bounds, record any mismatches).
- Record environment metadata (`git rev-parse HEAD`, `python - <<'PY' ...`) under `$OUTDIR/env/`.
- Run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q | tee "$OUTDIR"/comparison/pytest_collect.log`.
Pitfalls To Avoid:
- Keep new instrumentation under guards (`TRACE_PY_HKL_BOUNDS`, `TRACE_C_HKL_BOUNDS`) so binaries remain clean.
- Do not clobber existing Tap 5 artifacts; always write into the freshly stamped OUTDIR.
- Preserve MOSFLM convention and oversample=2 parameters exactly to match prior taps.
- Ensure logs include both edge and centre pixels; missing either invalidates the comparison.
- Avoid editing production physics beyond instrumentation; parity evidence only this loop.
- Capture every command in `commands.txt` within both `bounds/py` and `bounds/c` directories.
Pointers:
- docs/fix_plan.md:72
- plans/active/vectorization-parity-regression.md:94
- specs/spec-a-core.md:232
- plans/active/vectorization.md:17
Next Up: Prepare Tap 5.3 oversample accumulation instrumentation brief once HKL bounds parity is confirmed.
