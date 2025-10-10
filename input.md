Summary: Capture fresh 4096² parity evidence with the regenerated golden data so vectorization gating can clear.
Mode: Parity
Focus: docs/fix_plan.md [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_high_resolution_variant
Artifacts: reports/2026-01-vectorization-parity/phase_e/$STAMP/
Do Now: docs/fix_plan.md [VECTOR-PARITY-001] Restore 4096² benchmark parity — KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_high_resolution_variant
If Blocked: Capture failing command output to $OUTDIR/attempt_failed.log, note env vars + git SHA in $OUTDIR/blockers.md, and stop; do not lower thresholds without supervisor sign-off.
Priorities & Rationale:
- plans/active/vectorization-parity-regression.md:75 — Phase E1 is waiting on a new 4096² benchmark + high-res pytest run with the regenerated assets.
- docs/fix_plan.md:143 — `[VECTOR-TRICUBIC-002]` stays blocked until this Phase E evidence lands.
- plans/active/vectorization.md:14 — Status snapshot now expects Phase E artifacts before restarting profiler/backlog work.
- docs/development/testing_strategy.md:174 — Defines AT-PARALLEL-012 correlation and sum_ratio thresholds the rerun must satisfy.
How-To Map:
- export AUTHORITATIVE_CMDS_DOC=docs/development/testing_strategy.md; export NB_C_BIN=./golden_suite_generator/nanoBragg; ensure `command -v python` reports the expected venv.
- Set STAMP=$(date -u +%Y%m%dT%H%M%SZ) and OUTDIR=reports/2026-01-vectorization-parity/phase_e/$STAMP; mkdir -p "$OUTDIR"/{benchmark,full_frame,logs}.
- Benchmark (CPU, full frame): `KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --iterations 1 --profile --keep-artifacts --outdir "$OUTDIR"/benchmark/ | tee "$OUTDIR"/logs/benchmark.log`.
- Full-frame nb-compare for correlation: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/nb_compare.py --resample --outdir "$OUTDIR"/full_frame -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05 -floatfile tests/golden_data/high_resolution_4096/image.bin | tee "$OUTDIR"/logs/nb_compare.log`.
- Targeted pytest (Do Now command): `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_high_resolution_variant | tee "$OUTDIR"/logs/pytest_highres.log`.
- Summarise corr, sum_ratio, RMSE, benchmark speedup, and pytest result in "$OUTDIR"/phase_e_summary.md (cite thresholds from testing_strategy §2.5); include hash of tests/golden_data/high_resolution_4096/image.bin from `reports/2026-01-golden-refresh/phase_b/20251010T085124Z/high_resolution_4096/checksums.txt`.
Pitfalls To Avoid:
- Do not change regenerated golden datasets or commit `reports/` artifacts.
- Keep env vars (`KMP_DUPLICATE_LIB_OK`, `NB_RUN_PARALLEL`, `NB_C_BIN`) set for every command; missing any will invalidate parity evidence.
- Full-frame compare is heavy; ensure system has ≥16 GB free before running to avoid swap-induced noise.
- Preserve command logs exactly; reruns must use new $STAMP paths.
- No extra pytest selectors or `pytest -k 4096`; run only the mapped node to stay within scope.
- Verify benchmark script finishes with corr ≥0.999; if not, document immediately instead of rerunning blindly.
- Avoid torch.cuda unless explicitly needed; parity gating remains CPU-focused until sign-off.
- Leave `reports/...` untracked; check `git status` before ending the loop.
- Record git SHA and NB_C_BIN checksum in summary for traceability.
Pointers:
- plans/active/vectorization-parity-regression.md:68 — Phase E requirements and artifact expectations.
- docs/fix_plan.md:141 — `[VECTOR-TRICUBIC-002]` dependency on this evidence.
- plans/active/vectorization.md:12 — Updated status snapshot referencing the Phase E gating artifact.
- docs/development/testing_strategy.md:170 — nb-compare + acceptance thresholds for AT-PARALLEL-012.
Next Up: Once corr ≥0.999 evidence is archived, follow Phase E2 to update ledgers and unblock vectorization backlog.
