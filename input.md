Summary: Validate refreshed golden datasets by completing Phase C ROI parity + targeted pytest so VECTOR-PARITY Phase E can resume.
Mode: Parity
Focus: docs/fix_plan.md [TEST-GOLDEN-001] Regenerate golden data post Phase D5
Branch: feature/spec-based-2
Mapped tests: tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_high_resolution_variant
Artifacts: reports/2026-01-golden-refresh/phase_c/$STAMP/
Do Now: docs/fix_plan.md [TEST-GOLDEN-001] Regenerate golden data post Phase D5 — KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_high_resolution_variant
If Blocked: Capture failing command + stderr in reports/2026-01-golden-refresh/phase_c/$STAMP/attempt_failed.txt, note ROI parameters used, then ping supervisor with summary + artifacts.
Priorities & Rationale:
- docs/fix_plan.md:180 — Phase C parity validation is the lone open Next Action after Attempt #19 regeneration.
- plans/active/test-golden-refresh.md — Status snapshot now directs focus to Phase C ROI nb-compare + pytest sweep.
- tests/golden_data/README.md — authoritative commands + provenance to reuse when validating ROI metrics.
- docs/development/testing_strategy.md:120 — Specifies corr ≥0.95 and |sum_ratio−1|≤5e-3 thresholds for AT-PARALLEL-012 parity.
- reports/2026-01-golden-refresh/phase_a/20251010T084007Z/scope_summary.md — Lists dependent tests to retarget once ROI passes.
How-To Map:
- export AUTHORITATIVE_CMDS_DOC=docs/development/testing_strategy.md and NB_C_BIN=./golden_suite_generator/nanoBragg; confirm binary checksum archived in reports/2026-01-golden-refresh/phase_b/20251010T085124Z/c_binary_checksum.txt.
- Set STAMP=$(date -u +%Y%m%dT%H%M%SZ) and BASE=reports/2026-01-golden-refresh/phase_c/$STAMP; mkdir -p "$BASE"/high_res_roi.
- ROI parity: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/nb_compare.py --resample --roi 1792 2304 1792 2304 --outdir "$BASE"/high_res_roi -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05 -floatfile tests/golden_data/high_resolution_4096/image.bin`; tee stdout to `$BASE/high_res_roi/commands.txt` and retain summary.json/png outputs.
- After ROI run, record corr, RMSE, and sum_ratio in `$BASE/phase_c_summary.md` (include thresholds + pass/fail call).
- Targeted parity pytest: `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_high_resolution_variant | tee "$BASE"/pytest_highres.log`.
- If pytest fails, capture `pytest_highres.log`, note failure signature in `phase_c_summary.md`, and leave tests/golden_data artifacts untouched until supervisor review.
- Once both steps succeed, append dependent test follow-ups (from scope_summary) to `phase_c_summary.md` and flag any additional selectors needing reruns next loop.
Pitfalls To Avoid:
- Stay within ROI bounds (1792–2303 slow & fast) — mismatched ROI yields misleading metrics.
- Do not modify regenerated golden binaries; evidence-only loop.
- Ensure `scripts/nb_compare.py` arguments stay in `(slow fast)` order to preserve orientation.
- Maintain `KMP_DUPLICATE_LIB_OK=TRUE` for all torch invocations to avoid MKL crashes.
- Keep reports/ artifacts untracked; verify with `git status` before finishing.
- No full pytest suite — run only the mapped selector.
- Preserve ASCII formatting in summary notes; no fancy quoting that breaks diff readability.
- Confirm `NB_RUN_PARALLEL=1` is exported during pytest or parity harness will skip live C checks.
- If CUDA is available, document why ROI validation stays on CPU for parity comparability.
- Avoid rerunning ROI command without a new $STAMP; duplicates should be archived separately.
Pointers:
- docs/fix_plan.md:200 — `[TEST-GOLDEN-001]` Next Actions + thresholds.
- plans/active/test-golden-refresh.md:5 — Phase C task definitions.
- tests/golden_data/README.md:1 — high_resolution_4096 canonical command + provenance context.
- docs/development/testing_strategy.md:175 — nb-compare usage guidance.
- reports/2026-01-vectorization-parity/phase_e/20251010T082240Z/phase_e_summary.md — Baseline failure metrics for comparison.
Next Up: If ROI + pytest pass, prepare follow-up selector sweep for other regenerated datasets next loop.
