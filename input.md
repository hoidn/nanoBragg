Summary: Capture ROI nb-compare metrics for the 4096² parity regression (Phase B4a) to unblock trace work.
Mode: Parity
Focus: VECTOR-PARITY-001 / Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_b/<STAMP>/roi_compare/
Do Now: VECTOR-PARITY-001 Phase B4a — run `NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE nb-compare --resample --roi 1792 2304 1792 2304 --outdir reports/2026-01-vectorization-parity/phase_b/$(date -u +%Y%m%dT%H%M%SZ)/roi_compare -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05`
If Blocked: Capture the failing command output (stdout/stderr) plus `nb-compare --help` under the intended reports/<STAMP>/roi_compare/ directory and note the blocker in summary.md; do not pivot to other tests.
Priorities & Rationale:
- spec-a-parallel.md:93 — high-resolution AT-012 ROI thresholds we must quantify.
- plans/active/vectorization-parity-regression.md:40 — Phase B4a tasks demand nb-compare ROI evidence before trace work.
- docs/fix_plan.md:4015 — Next Actions now center on ROI sweep + trace staging.
- docs/development/testing_strategy.md:76 — reuse canonical golden-data commands; nb-compare is the approved parity tool.
- docs/debugging/debugging.md:15 — trace SOP requires ROI context; ROI metrics guide the upcoming callchain.
How-To Map:
- From repo root: `export NB_C_BIN=./golden_suite_generator/nanoBragg`
- Run `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` then `OUTDIR=reports/2026-01-vectorization-parity/phase_b/$STAMP/roi_compare`
- `mkdir -p "$OUTDIR"`
- `KMP_DUPLICATE_LIB_OK=TRUE nb-compare --resample --roi 1792 2304 1792 2304 --outdir "$OUTDIR" -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05`
- After run: copy nb-compare stdout to `$OUTDIR/metrics.log`, ensure `summary.json`/PNGs land in same folder, then draft `$OUTDIR/summary.md` with correlation + sum_ratio values and mention if a 1024² ROI rerun happened.
Pitfalls To Avoid:
- Do not run `pytest` suites — `test_high_resolution_variant` currently fails by design.
- Keep ROI bounds exactly `1792 2304 1792 2304`; double-check order is slow,fast per spec.
- Ensure `NB_C_BIN` points at `./golden_suite_generator/nanoBragg`; the frozen binary may drift.
- Leave `reports/` artifacts uncommitted; reference them only in fix_plan attempts.
- Preserve Protected Assets; no edits to docs/index.md or CLAUDE.md.
- Keep `nb-compare` command with `--` separator; dropping it will ignore detector params.
- Monitor disk usage; 4096² outputs are large — delete temporary files outside `$OUTDIR`.
- Record SHA256 checksums only if new binaries created; none expected this run.
- Stay on default dtype/device; no `.cpu()` shims or CUDA toggles unless instructed.
Pointers:
- plans/active/vectorization-parity-regression.md:32-41 — Phase B table and ROI tasks.
- docs/fix_plan.md:4015-4032 — Next Actions + expectations for ROI bundle.
- specs/spec-a-parallel.md:93 — AT-012 high-res acceptance thresholds.
- docs/development/testing_strategy.md:76-104 — canonical golden-data commands and parity tooling.
- docs/debugging/debugging.md:15-35 — trace-first methodology we prep for after ROI metrics.
Next Up: Phase B4b — summarise ROI scope in `roi_scope.md` once metrics land.
