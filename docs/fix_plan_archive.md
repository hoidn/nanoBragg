# Fix Plan Archive

Historical entries condensed for quick reference when deeper context is required.

## 2025-10-01
- **[AT-PERF-DEVICE-001] GPU Device Neutrality Violations** — Ensured detector pixel/close-distance tensors live on caller device; AT-PERF-007/008 GPU suites now green (commands: pytest tests/test_at_perf_007.py::TestATPerf007ComprehensiveBenchmark::test_gpu_performance -v, pytest tests/test_at_perf_008.py -v).
- **[PARITY-HARNESS-BOOTSTRAP] Shared C↔PyTorch parity runner** — Added `tests/test_parity_matrix.py` + YAML cases (initial coverage AT-PARALLEL-001/002/004/006/007); artifacts under reports/2025-09-29-AT-PARALLEL-{002,004}/.
- **[ROUTING-LOOP-001] loop.sh routing guard** — Verified automation now calls only `prompts/debug.md`; evidence in `reports/routing/2025-10-01-loop-verify.txt`.
- **[AT-PARALLEL-024-REGRESSION] PERF-PYTORCH-004 Test Compatibility** — Updated test inputs to tensors; `pytest tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_umat2misset_round_trip -v` passes, AT-PARALLEL suite 78/48 green.
- **[PROTECTED-ASSETS-001] docs/index.md safeguard** — `CLAUDE.md` and `docs/index.md` now mark automation assets as protected; hygiene plans reference the rule before deletions.
- **[PERF-PYTORCH-004-PHASE2] Cross-Instance Cache Validation** — CLI extensions plus JSON artifacts (`reports/benchmarks/20250930-165726-compile-cache/cache_validation_summary.json`, `...165757...`) show warm/cold speedups: CPU f64 37.09×, CPU f32 1485.90×, CUDA f32 1256.03×; explicit cache no longer required.
- **[AT-PARALLEL-012] Triclinic P1 correlation failure** — Restored Core Rule #13 metric duality (corr ≥0.9995). `pytest tests/test_at_parallel_012.py::TestATParallel012Triclinic::test_triclinic_p1 -vv` passes with tolerances reset to 1e-12.

## 2025-09-30
- **[AT-PARALLEL-020] Absorption Parallax Bug** — Restored sign-sensitive parallax handling and tightened thresholds (command: NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_at_parallel_020.py).
- **[REPO-HYGIENE-002] Initial cleanup** — Removed nested `golden_suite_generator/golden_suite_generator/` directory, archived `reports/2025-09-30-AT-021-traces/`, parity smoke (`AT-021/024`) succeeded in 20.38 s.
- **[AT-PARALLEL-020-REGRESSION] Comprehensive Integration** — Absorption parallax sign fix restored corr ≥0.99 (command: `pytest tests/test_at_parallel_020.py -vv`).
- **[AT-PARALLEL-024-PARITY] Random Misset reproducibility** — Fixed C parsing bug & PyTorch mosaicity; golden comparisons corr=1.0 for both seeds, artifacts in `reports/2025-09-30-AT-024/`.
- **[CORE-REGRESSION-001] Phi rotation unit test** — Updated unit test to match C loop formula (no midpoint); core suite stable at 98/7/1.
- **[PERF-PYTORCH-001..003] Early performance fixes** — Addressed multi-source vectorization regression, source tensor device drift, and CUDA benchmark gap; reference commits 7f6c4b2/058986f with pytest runs in `reports/benchmarks/20250930-*`.
- **Routing escalation log ([RALPH-VERIFICATION-001–011])** — Documented eleven consecutive Ralph-prompt routing violations; future loops must use `prompts/debug.md` while any AT parity test fails.

## 2026-01-05
- **[CLI-DTYPE-002] CLI dtype parity** — Paused pending renewed demand; reproduction script in `docs/fix_plan.md` (pre-refresh) validated parser accepts `-dtype float64`, but no fixes landed. Re-open when dtype overrides resurface in roadmap.
- **[ABS-OVERSAMPLE-001] Fix -oversample_thick subpixel absorption** — Deferred until detector absorption rework resumes; prior analysis recorded in `plans/active/oversample-thick-subpixel.md` Phase A bundle (`reports/2025-11-absorption/phase_a/`).
- **[C-SOURCEFILE-001] Sourcefile comment parsing bug** — Ownership moved to documentation backlog; evidence bundle `reports/2025-11-source-weights/phase_g/20251005T191102Z/` captures baseline. Await CLI flag implementation before reopening.
- **[ROUTING-SUPERVISOR-001] supervisor.sh automation guard** — Guard scripts staged, awaiting next automation window; see `plans/active/supervisor-loop-guard/plan.md` Phase B notes.
