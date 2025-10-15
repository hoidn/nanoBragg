# Phase C — Failure Clustering Summary (STAMP 20251015T113531Z)

## Overview
- Initiative: TEST-SUITE-TRIAGE-002
- Source run: reports/2026-01-test-suite-refresh/phase_b/20251015T113531Z/
- Scope: 8 failing tests, clustered into 6 thematic buckets
- Guard env (inherit Phase A/B): `CUDA_VISIBLE_DEVICES=-1`, `KMP_DUPLICATE_LIB_OK=TRUE`, `NANOBRAGG_DISABLE_COMPILE=1`, `PYTEST_ADDOPTS="--maxfail=200 --timeout=905"`

## Cluster Table

| Cluster ID | Tests (nodeids) | Classification | Suspected Cause | Reproduction Command | Linked Plans / Notes |
| --- | --- | --- | --- | --- | --- |
| CLUSTER-CREF-001 | tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c | Infrastructure gap | `scripts/c_reference_runner` cannot locate NB_C_BIN → C run returns None | `NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c` | Depends on C binary setup; tie to `[TEST-GOLDEN-001]` refresh + `docs/development/testing_strategy.md §2.5` parity guard |
| CLUSTER-PERF-001 | tests/test_at_perf_003.py::TestATPERF003MemoryBandwidth::test_memory_bandwidth_utilization | Implementation/perf regression | Median runtime scaling at 2048² drops bandwidth to 0.176 GB/s (<50% of 512² baseline). Possible memory allocator regression or test tolerance drift. | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_perf_003.py::TestATPERF003MemoryBandwidth::test_memory_bandwidth_utilization` | Likely feeds into `[PERF-PYTORCH-004]` (kernel fusion/perf uplift). Needs profiler evidence before code changes. |
| CLUSTER-TOOLS-001 | tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration | Infrastructure gap | `scripts/nb_compare.py` path resolution fails (returncode=2). Probably due to CLI invoking script from repo root while file lives under `scripts/nb_compare`. | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration` | Coordinate with `[TOOLING-DUAL-RUNNER-001]`; ensure `scripts/validation/README.md` path contract upheld. |
| CLUSTER-CLI-001 | tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cpu] ; tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip | Infrastructure gap / missing golden assets | `pix0_expected.json` and `scaled.hkl` golden outputs absent. CLI scaffolding incomplete after CLI-DEFAULTS fixes. | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_flags.py -k "pix0_vector_mm_beam_pivot or scaled_hkl_roundtrip"` | Blocks `[CLI-FLAGS-003]` plan; also intersects findings API-001/API-002 (pix0 semantics). Requires golden regeneration + docs update before enabling tests. |
| CLUSTER-GRAD-001 | tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability | Critical performance regression | Timeout after 905 s (Phase Q baseline 839.14 s). Suggests new slowdown in grad path (possibly vectorization or torch.compile guard). | `timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability` | Highest priority per testing_strategy §1.4; tie to `[PERF-PYTORCH-004]` and 905 s tolerance uplift SOP (plans/active/test-suite-triage-rerun.md Phase B notes). |
| CLUSTER-VEC-001 | tests/test_tricubic_vectorized.py::TestTricubicGather::{test_vectorized_matches_scalar,test_oob_warning_single_fire} | Implementation regression | Float32 vs Float64 mismatch introduced in tricubic vectorized path (likely dtype guard removed). | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_matches_scalar` | Directly maps to `[VECTOR-TRICUBIC-002]` Phase relaunch; coordinate with plans/active/vectorization.md (tricubic focus) + findings CONVENTION-004/005/006 parity gates. |

## Supporting Evidence
- Failure details JSON: `reports/2026-01-test-suite-refresh/phase_c/20251015T113531Z/failures.json`
- Source log: `reports/2026-01-test-suite-refresh/phase_b/20251015T113531Z/pytest.log`
- JUnit XML: `reports/2026-01-test-suite-refresh/phase_b/20251015T113531Z/pytest.junit.xml`

## Prior Findings & Docs Cross-Reference
- Pix0 CLI regressions tracked under findings `API-001`, `API-002` (pix0 units & override semantics).
- Vectorization parity gaps: findings `CONVENTION-004`, `CONVENTION-005`, `CONVENTION-006` — ensure dtype fix preserves established unit contracts before closing cluster VEC-001.
- Gradient timeout tolerance: plans/archive/test-suite-triage.md Phase R (905 s ceiling) and `docs/development/testing_strategy.md §1.5` notes on runtime discipline.

## Recommended Sequencing
1. **Infrastructure unblockers** (clusters CREF-001, TOOLS-001, CLI-001) — stage asset generation / env setup so parity tests can execute.
2. **Critical regression** (GRAD-001) — capture detailed timing trace (profiling/Torch autograd) before code edits.
3. **Vectorization regression** (VEC-001) — reproduce on CPU+CUDA, confirm dtype expectations, then delegate fix via `[VECTOR-TRICUBIC-002]` Phase launch.
4. **Performance investigation** (PERF-001) — run targeted profiler to determine if failure is implementation or tolerance; keep open until evidence captured.

## Exit Criteria Check
- ✅ Clusters enumerated with reproduction commands and classifications.
- ✅ Prior findings / plans cross-referenced for downstream delegation.
- ✅ Artifacts captured under `phase_c/20251015T113531Z/` for reuse in Phase D briefs.
