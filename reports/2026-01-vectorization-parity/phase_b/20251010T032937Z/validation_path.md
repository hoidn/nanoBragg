# Phase B3 Validation Path Recommendation
**Initiative**: [VECTOR-PARITY-001] Restore 4096² benchmark parity
**Author**: ralph
**Date**: 2025-10-10
**Context**: Phase B2 revealed no active 4096² pytest parity coverage; need validation strategy before debugging

---

## Problem Statement

The 4096² parity regression (correlation ~0.721, sum_ratio ~225x) is detected by benchmark/nb-compare tools but NOT validated by any pytest-based acceptance test. Phase B2 evidence (`reports/2026-01-vectorization-parity/phase_b/20251010T031841Z/summary.md`) confirmed:

- `pytest -k 4096` selects **0 tests** (128 deselected)
- Only reference is `tests/test_at_parallel_012.py::test_high_resolution_variant` (lines 364-377)
- That test is **skipped** with reason: "High-resolution variant requires large memory and golden data generation"
- Test docstring describes requirements but implementation is a `pass` stub

**Blocking Dependencies**:
- Phase B4 (ROI scope checks) waits on validation-path decision
- Phase C (trace localization) requires authoritative correlation measurement
- [VECTOR-GAPS-002] and [PERF-PYTORCH-004] remain blocked until correlation ≥0.999 restored

---

## Acceptance Criteria (from spec-a-parallel.md:90-99)

AT-PARALLEL-012 High-Resolution Variant SHALL enforce:

1. **Setup**: λ=0.5Å; detector 4096×4096, pixel 0.05mm, distance 500mm; cell 100,100,100; N=5
2. **ROI**: Compare on 512×512 ROI centered on beam center
3. **Pass Thresholds**:
   - No NaNs/Infs in output
   - C vs PyTorch correlation ≥ 0.95 on ROI
   - Top N=50 peaks in ROI within ≤ 1.0 px

**Note**: Current regression shows correlation ~0.06-0.72 (full frame), far below 0.95 threshold.

---

## Option Analysis

### Option A: Un-skip test_high_resolution_variant with Golden Data

**Approach**: Generate canonical 4096² golden data, implement test per spec requirements

**Pros**:
- Provides authoritative pytest-based validation per spec-a-parallel.md §AT-012
- ROI-based comparison (512×512) manageable memory footprint vs full 4096² (~1MB vs ~64MB)
- Aligns with existing AT-PARALLEL-012 test structure (simple_cubic, triclinic_P1, tilted variants)
- Creates reproducible baseline for CI/regression detection
- Spec explicitly defines this as normative acceptance test

**Cons**:
- Requires C binary run to generate 4096² golden reference (~64MB .bin file)
- Test execution time: ~30-60s per run (4096² detector) on CPU
- Memory footprint: ~128MB total (64MB C golden + 64MB PyTorch output)
- ROI-only comparison may miss full-frame correlation issues (current failure is full-frame)
- Golden data must be committed to repo (or generated on-demand)

**Implementation Checklist**:
1. Generate golden data via C binary:
   ```bash
   ./golden_suite_generator/nanoBragg \
     -lambda 0.5 \
     -cell 100 100 100 90 90 90 \
     -N 5 \
     -default_F 100 \
     -distance 500 \
     -detpixels 4096 \
     -pixel 0.05 \
     -floatfile tests/golden_data/high_resolution_4096/image.bin
   ```
2. Commit golden data to `tests/golden_data/high_resolution_4096/image.bin`
3. Document generation command in `tests/golden_data/README.md`
4. Implement test body with ROI extraction (center 512×512 window)
5. Remove `@pytest.mark.skip` decorator
6. Run test to verify thresholds (expect FAIL until regression fixed)

**Estimated Effort**: 1-2 hours (generation + test implementation + documentation)

---

### Option B: Add 4096² Case to Parity Harness (YAML-driven)

**Approach**: Extend `tests/parity_cases.yaml` with 4096² parametrized entry, leverage shared harness

**Pros**:
- Leverages existing `tests/test_parity_matrix.py` infrastructure
- Machine-readable YAML enables sweep variations (ROI sizes, tolerances)
- Consistency with other AT-PARALLEL parity cases
- Can add multiple 4096² variants (full-frame vs ROI) in single YAML entry
- Auto-generates comparison artifacts (metrics.json, diff.png) via harness

**Cons**:
- `tests/parity_cases.yaml` does NOT currently exist (per testing_strategy.md §2.5.0 bootstrap requirement)
- Requires **bootstrapping entire parity harness** before 4096² validation possible (blocking)
- Parity harness expects live C binary execution (`NB_RUN_PARALLEL=1`) — slower than golden data comparison
- Adds complexity: YAML schema design + harness implementation + per-case artifact management

**Implementation Checklist**:
1. **Bootstrap parity harness** (blocking prerequisite):
   - Create `tests/parity_cases.yaml` schema (see testing_strategy.md §2.5.0)
   - Implement `tests/test_parity_matrix.py` parametrized harness
   - Define threshold/sweep/option fields per spec
2. Add 4096² case to YAML:
   ```yaml
   - id: AT-PARALLEL-012-highres
     description: High-resolution 4096² detector variant
     base_args: "-lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05"
     thresholds:
       correlation: 0.95
       max_peak_distance_px: 1.0
     options:
       roi: [1792, 2304, 1792, 2304]  # Center 512×512 window
   ```
3. Validate harness runs and enforces thresholds

**Estimated Effort**: 4-6 hours (harness bootstrap dominates; actual 4096² addition is <30min)

---

### Option C: Benchmark/nb-compare-Only Validation (No pytest)

**Approach**: Document that 4096² parity is validated via `benchmark_detailed.py` and `nb-compare` tools, not pytest suite

**Pros**:
- Zero implementation effort — tools already exist and detected the regression
- Avoids pytest memory/execution-time overhead for developer workflow
- `nb-compare` provides detailed metrics (correlation, sum_ratio, RMSE, diff heatmaps)
- Benchmark captures performance (speedup) alongside correctness
- Acceptable for exploratory/profiling workflows where pytest overhead prohibitive

**Cons**:
- **NOT spec-compliant**: spec-a-parallel.md §AT-012 explicitly defines high-res variant as normative acceptance test
- No CI integration — manual invocation required
- Tooling discrepancy risk: Attempt #2-#4 showed benchmark (0.721) vs nb-compare (0.06) 12x disagreement
- Harder to enforce thresholds programmatically (exit codes, CI gates)
- Documentation burden: must maintain tool invocation instructions separate from pytest suite

**Implementation Checklist**:
1. Document 4096² validation commands in `docs/development/testing_strategy.md` §2.5
2. Add note to `tests/test_at_parallel_012.py::test_high_resolution_variant` docstring referencing tool-based validation
3. Update `specs/spec-a-parallel.md` conformance profile to clarify pytest vs tool validation split

**Estimated Effort**: <1 hour (documentation only)

---

## Recommendation

**Choice: Option A (Un-skip test_high_resolution_variant with Golden Data)**

### Rationale

1. **Spec Compliance**: spec-a-parallel.md §AT-012 explicitly defines high-res variant as normative acceptance test. Option C violates spec; Option B requires harness bootstrap that delays debugging.

2. **ROI Scope Matches Current Need**: Spec requires ROI-based comparison (512×512), which is tractable memory/time and aligns with Phase B4 ROI scope checks planned next.

3. **Fast Unblocking**: 1-2 hour effort vs 4-6 hours for Option B. Enables Phase C trace work to start today.

4. **Existing Pattern**: Follows same structure as `test_simple_cubic_correlation` (load golden, run PyTorch, compare). No new tooling needed.

5. **Mitigates Tool Discrepancy**: Pytest-based validation eliminates confusion from benchmark (0.721) vs nb-compare (0.06) disagreement — single authoritative measurement.

6. **CI-Ready**: Pytest exit codes and assertion messages integrate cleanly with CI; tools require manual threshold checking.

### Acceptance Steps (for this path)

1. ✅ **Phase B3** (this memo): Document options and recommend Option A
2. ⬜ **Phase B3.1** (next loop): Generate 4096² golden data via canonical C command
3. ⬜ **Phase B3.2** (next loop): Implement test body, remove skip, commit artifacts
4. ⬜ **Phase B3.3** (next loop): Run test to capture baseline FAIL metrics (correlation, peak distances)
5. ⬜ **Phase B4** (after B3 complete): Proceed to ROI scope checks per plan
6. ⬜ **Phase C** (debugging): Use pytest correlation as authoritative measurement for trace triage

### Known Limitations

- **Full-frame coverage**: ROI-only comparison may miss edge artifacts. Mitigate by running `nb-compare` full-frame checks in parallel (Phase B4).
- **Memory footprint**: 128MB peak usage may stress CI runners. Acceptable trade-off for authoritative validation.
- **Golden data staleness**: If C binary changes physics, golden must be regenerated. Mitigate via `tests/golden_data/README.md` versioning.

---

## Alternative: Hybrid Approach (A + C)

If ROI-only coverage feels insufficient, **combine Option A (pytest ROI) + Option C (nb-compare full-frame)**:

- Pytest enforces spec thresholds on ROI (fast, CI-friendly)
- nb-compare provides full-frame diagnostics (manual, detailed artifacts)
- Document both in testing_strategy.md with clear roles

This is the **belt-and-suspenders** approach. Recommend starting with pure Option A; add nb-compare workflow if ROI proves insufficient.

---

## Open Questions

1. **Golden data versioning**: Should 4096² .bin be committed to repo or generated on-demand per CI run?
   - **Recommendation**: Commit to repo (64MB acceptable for git-lfs or raw commit). Regeneration on CI adds complexity/flakiness.

2. **Tolerance relaxation**: Spec requires ≥0.95 correlation. Current failure is ~0.06-0.72. Should test use relaxed threshold during debugging?
   - **Recommendation**: Use spec threshold (0.95); XFAIL expected until regression fixed. Captures true acceptance bar.

3. **ROI centering**: How to compute "512×512 ROI centered on beam"?
   - **Recommendation**: Use beam_center_mm → pixel coordinates from DetectorConfig, extract [center-256:center+256, center-256:center+256].

---

## Next Actions (for supervisor handoff)

1. **Ratify path choice**: Confirm Option A or request alternative
2. **Phase B3.1**: If approved, generate golden data and commit to `tests/golden_data/high_resolution_4096/`
3. **Phase B3.2**: Implement test, remove skip, document in README
4. **Phase B4**: After test active, proceed to ROI scope checks per plan

---

## Supporting Evidence

- Spec reference: `specs/spec-a-parallel.md:90-99` (AT-PARALLEL-012 high-res variant definition)
- Test stub: `tests/test_at_parallel_012.py:364-377` (current skip + requirements)
- Phase B2 evidence: `reports/2026-01-vectorization-parity/phase_b/20251010T031841Z/summary.md` (0 pytest coverage confirmed)
- Regression metrics: Phase B1 attempts #2-#4 (correlation 0.06-0.72, sum_ratio 225-236x)
