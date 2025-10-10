Summary: Capture PyTorch Tap 4 F_cell metrics for edge vs centre pixels at oversample=2 and package them as Phase E5 evidence.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_e0/$STAMP/py_taps/, reports/2026-01-vectorization-parity/phase_e0/$STAMP/f_cell_summary.md
Do Now: [VECTOR-PARITY-001] Phase E5 PyTorch Tap 4 capture — run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel 0 0 --tag edge --oversample 2 --taps f_cell --json --out-dir reports/2026-01-vectorization-parity/phase_e0/$STAMP/py_taps` and repeat with `--pixel 2048 2048 --tag centre` using the same $STAMP.
If Blocked: Capture stdout/stderr to `reports/2026-01-vectorization-parity/phase_e0/$STAMP/attempt_fail.log`, note the failure and command in docs/fix_plan.md Attempts, and stop for supervisor review.
Priorities & Rationale:
- `docs/fix_plan.md:3-6` flags Tap 4 diagnostics as the active unblocker after omega bias was cleared.
- `docs/fix_plan.md:48-49` records Attempt #25 (tooling landed) and expects the actual Tap 4 run next.
- `plans/active/vectorization-parity-regression.md:80-82` defines Phase E5 deliverables (PyTorch tap metrics, JSON archive, comparison prep).
- `reports/2026-01-vectorization-parity/phase_e0/20251010T092845Z/trace/tap_points.md` lists the Tap 4 schema you must populate (total_lookups, HKL bounds, default_F hits).
How-To Map:
- Export `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` then `OUTDIR=reports/2026-01-vectorization-parity/phase_e0/$STAMP/py_taps`; create directories for `py_taps`, `env`, and `notes` (`mkdir -p "$OUTDIR" reports/2026-01-vectorization-parity/phase_e0/$STAMP/env reports/2026-01-vectorization-parity/phase_e0/$STAMP/notes`).
- Record environment metadata with `env | sort > reports/2026-01-vectorization-parity/phase_e0/$STAMP/env/trace_env.txt` and `python - <<'PY'` snippet to dump `torch.__version__` + device availability to `env/torch_env.json`.
- Run the edge command first, tee stdout to `$OUTDIR/pixel_0_0_stdout.log` (`... --tag edge ... | tee $OUTDIR/pixel_0_0_stdout.log`); ensure JSON + metadata files land alongside TRACE logs.
- Run the centre command reusing the same $STAMP and tee stdout to `$OUTDIR/pixel_2048_2048_stdout.log`; append both invocations (with exact timestamps) to `$OUTDIR/commands.txt`.
- Parse the two `pixel_*_f_cell_stats.json` files and draft `reports/2026-01-vectorization-parity/phase_e0/$STAMP/f_cell_summary.md` summarising totals, mean F_cell, HKL bounds, and any edge/centre deltas; call out whether out_of_bounds_count differs (if zero, emphasise default_F usage).
- Update `[VECTOR-PARITY-001]` Attempts in `docs/fix_plan.md` with Attempt #26 (Phase E5 PyTorch tap capture) referencing the new artifact paths.
Pitfalls To Avoid:
- Use the same `$STAMP` for both pixels so artifacts collocate; do not mix directories.
- Keep tensors on the requested device; avoid adding `.cpu()`/`.detach()` during analysis.
- Do not commit anything under `reports/`; leave artifacts untracked.
- Preserve existing TRACE output ordering; tap output must append without altering legacy lines.
- Confirm JSON files exist before drafting the summary; rerun command if a file is missing.
- Respect Protected Assets (no edits to docs/index.md or tracked golden data).
- After edits to docs/fix_plan.md, run `pytest --collect-only -q` only if you touched code (not required for pure evidence loop).
- Use UTC timestamps in notes/summary for consistency with earlier bundles.
Pointers:
- docs/fix_plan.md:3-6 — Active focus statement for Tap 4.
- docs/fix_plan.md:48-49 — Attempt #25 context and expectation for Phase E5 follow-up.
- plans/active/vectorization-parity-regression.md:80-82 — Phase E5/E6/E7 checklist and artifact contract.
- docs/development/testing_strategy.md#1.5 — Logging commands and storing artifacts under reports/.
Next Up: Stage Phase E6 C Tap 4 instrumentation once PyTorch metrics are archived.
