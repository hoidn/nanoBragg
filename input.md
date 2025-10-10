Summary: Capture Tap 4 F_cell stats in PyTorch for edge vs centre pixels at oversample=2 and stage artifacts for Phase E5.
Mode: Docs
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_e0/$STAMP/py_taps/, reports/2026-01-vectorization-parity/phase_e0/$STAMP/f_cell_comparison.md (draft)
Do Now: docs/fix_plan.md [VECTOR-PARITY-001] Next Action 1 — run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel 0 0 --tag edge --oversample 2 --taps f_cell --out-dir reports/2026-01-vectorization-parity/phase_e0/$STAMP/py_taps --json` (then repeat with `--pixel 2048 2048 --tag centre`) after extending the script per plan.
If Blocked: Log the tooling gap in `reports/2026-01-vectorization-parity/phase_e0/$STAMP/attempt_fail.log`, note it in docs/fix_plan.md Attempts, and pause for supervisor guidance.
Priorities & Rationale:
- `docs/fix_plan.md:58-62` elevates Tap 4 instrumentation as the next unblocker now that omega bias is ruled out.
- `plans/active/vectorization-parity-regression.md:80-82` defines Phase E5–E7 deliverables and artifact expectations for F_cell diagnostics.
- `reports/2026-01-vectorization-parity/phase_e0/20251010T092845Z/trace/tap_points.md` lists the Tap 4 schema (keys + units) that the new tooling must emit.
How-To Map:
- Export `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and create `reports/2026-01-vectorization-parity/phase_e0/$STAMP/py_taps` before running commands.
- Update `scripts/debug_pixel_trace.py` to accept `--oversample` (default 1) and a `--taps` selector supporting at least `f_cell`, writing JSON alongside TRACE output without breaking existing CLI flags.
- Implement Tap 4 metrics (total_lookups, out_of_bounds_count, zero_f_count, mean_f_cell, HKL bounds) using production lattice/HKL helpers; avoid duplicating physics.
- Run the edge and centre commands in the Do Now line (same $STAMP) and archive stdout/stderr to `commands.txt` within the tap folder.
- Summarise results in `reports/2026-01-vectorization-parity/phase_e0/$STAMP/f_cell_summary.md` (numbers + quick interpretation) to seed the comparison memo next loop.
Pitfalls To Avoid:
- Do not introduce `.cpu()`/`.detach()` when gathering stats; keep tensors on caller device.
- Preserve existing TRACE output format; add new blocks after legacy lines.
- Keep new arguments optional so prior invocations remain compatible.
- Respect Protected Assets; write artifacts only under `reports/` with the stamped path.
- Avoid hard-coding STAMP values; use the exported variable consistently.
- No ad-hoc scripts outside `scripts/`; extend the existing helper per plan.
Pointers:
- docs/fix_plan.md:58-62 — Tap 4 Next Actions + expectations.
- plans/active/vectorization-parity-regression.md:80-82 — Phase E5/E6/E7 checklist.
- reports/2026-01-vectorization-parity/phase_e0/20251010T092845Z/trace/tap_points.md — Tap definitions (see Tap 4 block).
- docs/development/testing_strategy.md#1.5 — Command logging + artifact storage guardrails.
Next Up: Prep C Tap 4 instrumentation (Phase E6) once PyTorch stats land.
