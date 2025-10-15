# Cluster CLUSTER-VEC-001 — Tricubic Vectorization Regression

## Summary
- Tests: `tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_matches_scalar` and `tests/test_tricubic_vectorized.py::TestTricubicGather::test_oob_warning_single_fire`
- Classification: Implementation regression (vectorization parity)
- Failure mode: Vectorized tricubic path returns float32 results while scalar reference stays float64, causing tolerance mismatch and warning test to fire multiple times.
- Evidence: `reports/2026-01-test-suite-refresh/phase_b/20251015T113531Z/pytest.log` (dtype mismatch assertion + multiple warnings at lines 3290-3370).

## Reproduction Command
```bash
KMP_DUPLICATE_LIB_OK=TRUE \
pytest -v tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_matches_scalar
```
- Optional: run both nodeids with `-k "TestTricubicGather and (vectorized_matches_scalar or oob_warning_single_fire)"` to see combined output.

## Downstream Plan Alignment
- Primary owner: `[VECTOR-TRICUBIC-002]` — Vectorization relaunch backlog (tricubic focus).
- Supporting docs: `plans/active/vectorization.md` (ensure Phase 1 covers tricubic dtype guard), findings `CONVENTION-004`, `CONVENTION-005`, `CONVENTION-006` (unit/normalization issues to validate during fix).
- Related initiatives: `[VECTOR-PARITY-001]` for broader vectorization parity tracking.

## Recommended Next Actions
1. Run reproduction command on CPU (and GPU if available) to capture dtype/shape diagnostics; log outputs under this cluster directory.
2. Inspect `src/nanobrag_torch/utils/tricubic.py` vectorized path for dtype enforcement; confirm no `.to(torch.float32)` remains from previous experiments.
3. Draft fix plan ensuring vectorized path matches scalar baseline and respects gradient/dtype neutrality; integrate into `[VECTOR-TRICUBIC-002]` Phase plan.
4. Once fix ready, rerun both nodeids and attach passing logs + `pytest --maxfail=1` output to this cluster directory.

## Exit Criteria
- Diagnostic reproduction logs committed (including dtype dump, device coverage).
- `[VECTOR-TRICUBIC-002]` plan updated with explicit tasks referencing this brief.
- Tests pass locally with documented commands and artifacts stored under the cluster directory.
