Summary: Capture matching C and PyTorch pixel traces for the 4096² parity regression so we can pinpoint the first divergence.
Mode: Parity
Focus: VECTOR-PARITY-001 / Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_c/<STAMP>/{c_traces,py_traces,first_divergence.md}
Do Now: VECTOR-PARITY-001 Phase C1/C2 — instrument `golden_suite_generator/nanoBragg` to log aggregated tap points for pixels (2048,2048), (1791,2048), (4095,2048) and run the 4096² parity command; extend `scripts/debug_pixel_trace.py` to emit the identical tap set for those pixels (float64 CPU); store logs and the initial `first_divergence.md` skeleton under `reports/2026-01-vectorization-parity/phase_c/$STAMP/`.
If Blocked: Capture the blocker and partial data in `reports/2026-01-vectorization-parity/phase_c/$STAMP/first_divergence.md` (prefix with `BLOCKED:`) and summarise the issue in docs/fix_plan Attempt notes before pausing instrumentation.
Priorities & Rationale:
- plans/active/vectorization-parity-regression.md:12 — Phase C now unblocked; instrumentation is the gate to resume VECTOR-GAPS-002/PERF-PYTORCH-004.
- plans/active/vectorization-parity-regression.md:50 — C1/C2 tasks require traces for pixels (2048,2048), (1791,2048), (4095,2048) with git-clean artifact handling.
- docs/fix_plan.md:37 — Next Actions 2–5 log supervisor decisions and mandate aggregated tap points + clean `reports/` handling.
- docs/debugging/debugging.md:21 — Parallel trace SOP (naming/precision) must be followed when adding print taps.
- docs/development/testing_strategy.md:52 — Use the documented 4096² parity command as the authoritative reproduction.
How-To Map:
- `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `OUTDIR=reports/2026-01-vectorization-parity/phase_c/$STAMP`; `mkdir -p "$OUTDIR"/c_traces "$OUTDIR"/py_traces`.
- After adding guarded `fprintf` blocks for each pixel (aggregated totals only), rebuild: `make -C golden_suite_generator`.
- Run the C parity config, keeping stderr for trace logs: `NB_C_BIN=./golden_suite_generator/nanoBragg $NB_C_BIN -default_F 100 -cell 100 100 100 90 90 90 -N 5 -lambda 6.2 -distance 100 -detpixels 4096 -pixel 0.1 -floatfile /tmp/c_trace.bin 2> "$OUTDIR"/c_traces/pixels.log` (split into per-pixel files if needed).
- Update `scripts/debug_pixel_trace.py` to accept `--pixel <slow> <fast>` and emit the same tap names/precision; run per pixel with float64 CPU tensors, e.g. `KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel 2048 2048 --device cpu --dtype float64 2> "$OUTDIR"/py_traces/pixel_2048_2048.log`.
- After each run confirm `git status --short` stays clean (no new tracked `reports/` content); if files appear, move them out of git control before proceeding.
- Start `first_divergence.md` in `$OUTDIR` noting the command SHAs, tap list, and any immediate mismatches; leave TODO markers for the diff step once both traces exist.
Pitfalls To Avoid:
- Do not downgrade to float32 for traces; stay on CPU float64 for determinism.
- Keep tap names/units identical between C and PyTorch (see debug SOP) to simplify diffs.
- Avoid printing per-source/per-phi loops initially; capture aggregated totals first as agreed.
- Ensure pixel order is `(slow, fast)` and indices are zero-based to match C loop counters.
- Do not commit new artifacts under `reports/`; leave them untracked and referenced only.
- Re-run `pytest --collect-only -q` after modifying the PyTorch trace script.
- Respect `NB_C_BIN` precedence; do not run the frozen root binary by accident.
- Preserve existing trace plan structure; document deviations in `first_divergence.md`.
Pointers:
- plans/active/vectorization-parity-regression.md:12,50-52 — Phase C context and checklist.
- docs/fix_plan.md:37-42 — Supervisor-approved Next Actions for instrumentation.
- docs/debugging/debugging.md:21-80 — Required trace schema and SOP steps.
- reports/2026-01-vectorization-parity/phase_b/20251010T035732Z/roi_compare/roi_scope.md — ROI findings motivating pixel selection.
Next Up: If traces land cleanly, proceed to Phase C3 diffing (`first_divergence.md`) before considering any new ROI sweeps.
