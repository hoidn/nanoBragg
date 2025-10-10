Summary: Capture Phase E benchmark + pytest evidence to confirm full-frame parity holds after D6 cleanup.
Mode: Parity
Focus: VECTOR-PARITY-001 / Phase E — Full validation sweep
Branch: feature/spec-based-2
Mapped tests: tests/test_at_parallel_012.py::test_high_resolution_variant
Artifacts: reports/2026-01-vectorization-parity/phase_e/$STAMP/{benchmark/,nb_compare_full/,pytest_highres.log,phase_e_summary.md}
Do Now: [VECTOR-PARITY-001] item 12 — rerun Phase E benchmark bundle then NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_parallel_012.py::test_high_resolution_variant -v
If Blocked: Capture partial outputs under reports/2026-01-vectorization-parity/phase_e/$STAMP/attempt_failed/ and note the failure in docs/fix_plan.md Attempts.
Priorities & Rationale:
- docs/fix_plan.md:5 keeps Phase E validation as the active focus.
- docs/fix_plan.md:64 defines the exact deliverables for the Phase E sweep.
- plans/active/vectorization-parity-regression.md:12 confirms ROI parity and readiness to enter Phase E.
- plans/active/vectorization-parity-regression.md:75 lists benchmark + pytest commands and success thresholds for E1.
- docs/development/testing_strategy.md:18 warns to respect device/dtype discipline while running parity checks.
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ)
- NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts
- BENCH_DIR="$(ls -td reports/benchmarks/20* | head -n1)" && rsync -a "$BENCH_DIR/" "reports/2026-01-vectorization-parity/phase_e/$STAMP/benchmark/"
- NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/nb_compare.py --resample --threshold 0.999 --outdir reports/2026-01-vectorization-parity/phase_e/$STAMP/nb_compare_full -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05
- NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_parallel_012.py::test_high_resolution_variant -v | tee reports/2026-01-vectorization-parity/phase_e/$STAMP/pytest_highres.log
- Summarise corr, sum_ratio, runtime deltas, and pytest outcome in reports/2026-01-vectorization-parity/phase_e/$STAMP/phase_e_summary.md
Pitfalls To Avoid:
- Do not reuse old STAMP directories; create a fresh timestamp before each run.
- Keep NB_C_BIN pointed at ./golden_suite_generator/nanoBragg for parity comparability.
- Preserve `--resample` on nb_compare to avoid shape mismatches.
- Capture command transcripts for every step (tee or commands.txt) alongside metrics.
- Avoid running additional pytest suites beyond the mapped selector.
- Do not commit large raw trace dumps; reference them in docs instead.
- Ensure numerical thresholds meet corr ≥0.999 and |sum_ratio−1| ≤5e-3 before marking success.
- Maintain device/dtype neutrality—no `.cpu()` guardrails in ad-hoc probes.
Pointers:
- docs/fix_plan.md:5
- docs/fix_plan.md:64
- plans/active/vectorization-parity-regression.md:12
- plans/active/vectorization-parity-regression.md:75
- docs/development/testing_strategy.md:18
Next Up: If time remains, draft ledger updates for Phase E2 (docs/fix_plan.md + plans/active/vectorization.md) using the new metrics.
