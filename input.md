Summary: Capture C Tap 4 default_F metrics so we can compare against PyTorch before picking the next parity tap.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2026-01-vectorization-parity/phase_e0/<STAMP>/c_taps/
Do Now: [VECTOR-PARITY-001] Next Action #1 — `./golden_suite_generator/nanoBragg -default_F 100 -cell 100 100 100 90 90 90 -lambda 0.5 -distance 500 -detpixels 4096 -pixel 0.05 -N 5 -oversample 2 -floatfile /tmp/tap4.bin`
If Blocked: Fall back to capturing logs with oversample=1 to validate instrumentation, then note the deviation in Attempts History.
Priorities & Rationale:
- docs/fix_plan.md:61-64 nails the immediate Tap 4 mirror requirement before progressing to Tap 5/6.
- plans/active/vectorization-parity-regression.md:74-83 keeps Phase E5 marked done and E6/E7 open pending C evidence and comparison.
- reports/2026-01-vectorization-parity/phase_e0/20251010T102752Z/f_cell_summary.md grounds the PyTorch-side findings we must mirror on C.
- reports/2026-01-vectorization-parity/phase_e0/20251010T100102Z/c_taps/omega_comparison.md shows the expected logging style for the new C instrumentation bundle.
How-To Map:
- `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and `OUTDIR=reports/2026-01-vectorization-parity/phase_e0/${STAMP}/c_taps`; create the directory and start commands/env logs.
- Edit `golden_suite_generator/nanoBragg.c` near the Tap 4 hook point (same block as E2 omega tap, ~line 2965) to emit TRACE lines capturing HKL indices, default_F hits, and lookup counts for the target pixel; follow `tap_points.md` schema.
- `make -C golden_suite_generator` to rebuild the instrumented binary, then run the Do Now command piping stdout to `${OUTDIR}/tap4_raw.log`; keep the TRACE lines intact and copy the full command into `${OUTDIR}/commands.txt`.
- Post-process the log (`grep TRACE_C_TAP4`) into `${OUTDIR}/tap4_metrics.json` (one entry per pixel with total_lookups/out_of_bounds/zero_F/hkl_bounds) and capture environment info in `${OUTDIR}/env/trace_env.json`.
- Remove instrumentation (`git checkout -- golden_suite_generator/nanoBragg.c`), rebuild clean, and run `pytest --collect-only -q | tee reports/2026-01-vectorization-parity/phase_e0/${STAMP}/c_taps/pytest_collect.log` to confirm Python import health.
- Summarise preliminary deltas vs Attempt #25 inside `${OUTDIR}/notes.md`; leave the formal `f_cell_comparison.md` for the next Next Action once C metrics are confirmed.
Pitfalls To Avoid:
- Do not commit the instrumented C changes; restore the file before ending the loop.
- Keep all artifacts untracked under `reports/`; no PNGs or logs should enter git.
- Ensure `NB_C_BIN` points at the instrumented binary and unset it after capture.
- Preserve the same STAMP for all files in this bundle for traceability.
- Avoid changing PyTorch codepaths or detector defaults while instrumenting the C binary.
- Set `KMP_DUPLICATE_LIB_OK=TRUE` for any Python commands you run during validation.
- Capture SHA or checksum info if you rerun the C binary to avoid provenance gaps.
- Don't skip the clean rebuild after removing instrumentation—the binary must return to its golden state.
- Watch for large tap logs; trim to TAP lines before storing in reports.
- Respect Protected Assets (docs/index.md, loop scripts) and leave them untouched.
Pointers:
- docs/fix_plan.md:61-64 — Next Actions queue for this parity push.
- plans/active/vectorization-parity-regression.md:74-83 — Phase E checkpoints and schema expectations.
- reports/2026-01-vectorization-parity/phase_e0/20251010T102752Z/f_cell_summary.md — PyTorch Tap 4 reference metrics.
- reports/2026-01-vectorization-parity/phase_e0/20251010T100102Z/c_taps/commands.txt — Prior C tap command template.
Next Up: 1) Draft `f_cell_comparison.md` once C metrics land; 2) Scope Tap 5 (pre-normalisation intensity) instrumentation if F_cell parity holds.
