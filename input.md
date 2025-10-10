Summary: Enable the 4096² high-resolution parity test (Option A) and capture the expected failure evidence.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_high_resolution_variant
Artifacts: tests/golden_data/high_resolution_4096/image.bin; reports/2026-01-vectorization-parity/phase_b/$STAMP/{c_golden/,summary.md,pytest_highres.log,roi_compare/}
Do Now: [VECTOR-PARITY-001] Execute Phase B3a–B3d Option A tasks — generate the C golden image, document provenance, implement the ROI-based pytest, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_high_resolution_variant` (expected FAIL) while capturing artifacts under reports/2026-01-vectorization-parity/phase_b/$STAMP/.
If Blocked: Record the obstacle in reports/2026-01-vectorization-parity/phase_b/$STAMP/blockers.md (include commands/output) and note it in docs/fix_plan.md Attempt history before pausing.
Priorities & Rationale:
- plans/active/vectorization-parity-regression.md:12 — Phase B3 Option A is now the gate before ROI scoping.
- plans/active/vectorization-parity-regression.md:36 — Tasks B3a–B3e define the execution sequence for Option A.
- docs/fix_plan.md:4012 — Next actions mandate generating golden data, updating docs, and running the high-res pytest.
- specs/spec-a-parallel.md:90 — AT-PARALLEL-012 defines λ=0.5Å, 512×512 ROI, corr ≥0.95, ≤1.0 px peaks.
- tests/test_at_parallel_012.py:364 — Current skip stub that must be replaced with ROI assertions.
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-vectorization-parity/phase_b/$STAMP/{c_golden,roi_compare}.
- Generate golden data: `NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE $NB_C_BIN -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05 -floatfile tests/golden_data/high_resolution_4096/image.bin 2>&1 | tee reports/2026-01-vectorization-parity/phase_b/$STAMP/c_golden/command.log`; capture env via `python scripts/validation/dump_env.py > .../env.json` (or note manually) and compute sha256sum.
- Update documentation: append command + ROI/tolerances to tests/golden_data/README.md (and testing_strategy.md §2.5 if needed); summarise in reports/.../summary.md.
- Implement test: replace skip stub with loading the new binary, cut ROI `slice(1792, 2304)` in both axes, assert no NaNs/Infs, compute Pearson correlation, detect 50 peaks, and enforce ≤1.0 px offsets.
- Run targeted pytest (expected FAIL) and tee output to reports/.../pytest_highres.log; record observed correlation/peak stats in summary.md and add Attempt note in docs/fix_plan.md.
- Optional (if time permits): run `nb-compare --resample --roi 1792 2304 1792 2304 --outdir reports/2026-01-vectorization-parity/phase_b/$STAMP/roi_compare -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05` to prep for Phase B4a.
Pitfalls To Avoid:
- Do not commit the new binary without updating tests/golden_data/README.md and citing the command.
- Keep ROI centered (1792:2304 for both axes) and maintain float32 precision to match spec tolerances.
- Preserve vectorization/device neutrality — no `.cpu()` shim inside the test implementation.
- Verify no NaNs/Infs before correlation; fail fast if detected.
- Respect Protected Assets (docs/index.md references); update index only after doc changes are final.
- Ensure pytest failure is captured (expected) and recorded; do not mark xfail.
- Watch repo size; confirm acceptable policy before committing 64MB binary (use git lfs if required by repo policy).
- Maintain ASCII formatting when editing docs/tests.
- Capture exact commands in commands.txt/summary.md; no ad-hoc scripts in repo root.
Pointers:
- plans/active/vectorization-parity-regression.md:12
- plans/active/vectorization-parity-regression.md:36
- docs/fix_plan.md:4012
- specs/spec-a-parallel.md:90
- tests/test_at_parallel_012.py:364
Next Up: Phase B4a ROI nb-compare sweep once the high-res pytest evidence is in place.
