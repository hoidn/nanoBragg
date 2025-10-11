# Phase J Remediation Sequence
## Execution Order & Gating Strategy for Test Suite Remediation

**Timestamp:** 20251011T043327Z
**Initiative:** [TEST-SUITE-TRIAGE-001]
**Phase:** J — Remediation Launch & Tracking
**Data Source:** Phase I triage + remediation tracker

---

## Overview

This document defines the **execution order** for fixing the 36 active test failures across 16 clusters. The sequence is designed to:

1. **Maximize unblocking** — resolve critical-path blockers first
2. **Preserve stability** — avoid cascading regressions by gating with incremental test runs
3. **Follow spec priorities** — address fundamental spec compliance before optimization features
4. **Enable parallel work** — allow independent clusters to proceed concurrently where safe

**Guiding Principles:**
- **One cluster at a time** within each sprint (avoid mixing concerns)
- **Incremental validation** — run targeted tests after each fix before proceeding
- **Full-suite gating** — run complete suite at sprint boundaries to catch regressions
- **Blocker resolution first** — verify [DTYPE-NEUTRAL-001] status before starting Sprint 1

---

## Pre-Sprint: Blocker Resolution (CRITICAL GATE)

**Goal:** Verify [DTYPE-NEUTRAL-001] completion status to unblock determinism work

### Actions:
1. **Read fix_plan.md [DTYPE-NEUTRAL-001] entry** — verify "done" status is accurate
2. **Run determinism smoke test:**
   ```bash
   CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py::test_pytorch_determinism_same_seed -x
   ```
3. **Verify no dtype crashes** — test should fail on RNG logic, NOT dtype mismatches
4. **Decision:**
   - If dtype errors persist → complete [DTYPE-NEUTRAL-001] work before Sprint 1
   - If RNG-only failures → proceed with Sprint 1 (determinism unblocked)

### Deliverable:
- **Blocker status documented** in fix_plan.md with smoke test results
- **Go/No-Go decision** for Sprint 1 recorded in remediation tracker

### Timeline:
- **Estimated:** 30 minutes (docs + 1 test run)

---

## Sprint 1: Critical Path — Spec Compliance Foundations (Priority 1)

**Duration:** 5–7 engineer loops
**Focus:** Fundamental spec requirements that gate other work
**Gating Test:** Full suite at sprint end must show ≤30 failures (current: 36)

### Sprint 1.1: Determinism (C2 + C15)

**Fix Plan:** [DETERMINISM-001]
**Failures:** 3 total (C2: 2, C15: 1)
**Owner:** ralph

**Execution Steps:**
1. Verify [DTYPE-NEUTRAL-001] blocker resolution (Pre-Sprint action)
2. Fix RNG seeding for mosaic rotation generation
3. Implement bitwise-deterministic mode per spec-a-core.md §5.3
4. Fix test dtype harmonization (AT-024:356 dtype mismatch)

**Gating Tests:**
```bash
# Targeted validation (run after each fix step)
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py
```

**Exit Criteria:**
- All 3 determinism tests pass
- Same-seed runs produce bitwise-identical output
- Seed propagation documented

**Rationale:** Determinism is a spec requirement (§5.3) and affects scientific reproducibility. Must be resolved before other physics work to ensure test stability.

---

### Sprint 1.2: Source Weighting (C3)

**Fix Plan:** [SOURCE-WEIGHT-002]
**Failures:** 6
**Owner:** ralph

**Execution Steps:**
1. Implement sourcefile parsing for all column configurations
2. Wire source weights into simulator normalization
3. Validate flux calculation against spec §§3.4–3.5 formulas
4. Add weighted multi-source regression tests

**Gating Tests:**
```bash
# Targeted validation
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py
```

**Exit Criteria:**
- All 6 source weighting tests pass
- Sourcefile parsing handles missing columns gracefully
- Multi-source normalization matches spec

**Rationale:** Source weighting is a spec §§3.4–3.5 requirement affecting beam intensity calculations. Needed before more complex physics work.

---

### Sprint 1.3: Detector Config (C8)

**Fix Plan:** [DETECTOR-CONFIG-001]
**Failures:** 2
**Owner:** ralph

**Execution Steps:**
1. Audit DetectorConfig dataclass defaults against spec-a-core.md §4 table
2. Fix mismatched defaults (distance, pixel_size, beam_center formulas)
3. Validate initialization paths (CLI → config → Detector)
4. Add convention-aware default tests

**Gating Tests:**
```bash
# Targeted validation
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py
```

**Exit Criteria:**
- Detector config tests pass (2 tests)
- Defaults match spec table exactly
- Convention-dependent defaults (MOSFLM vs XDS) work correctly

**Rationale:** Correct detector initialization is foundational for all geometry work. Must be solid before tackling pivots/rotations.

---

### Sprint 1.4: Lattice Shape Models (C4)

**Fix Plan:** [LATTICE-SHAPE-001]
**Failures:** 2
**Owner:** ralph

**Execution Steps:**
1. Implement GAUSS lattice model per spec formula
2. Implement TOPHAT lattice model per spec formula
3. Validate normalization factors against C-code golden data
4. Add shape model comparison tests

**Gating Tests:**
```bash
# Targeted validation
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_str_003.py::test_gauss_shape_model tests/test_at_str_003.py::test_shape_model_comparison
```

**Exit Criteria:**
- GAUSS and TOPHAT models pass tests (2 tests)
- Shape models match C-code parity (correlation ≥0.999)
- Models correctly handle cutoff/falloff per spec

**Rationale:** Lattice shape models affect structure factor calculations. Spec §8 compliance required for accurate physics.

---

### Sprint 1.5: Detector Pivots (C10)

**Fix Plan:** [PIVOT-MODE-001]
**Failures:** 2
**Owner:** ralph

**Execution Steps:**
1. Audit `Detector.compute_pix0()` logic for BEAM vs SAMPLE formulas
2. Fix pivot mode detection from CLI flags (per c_to_pytorch_config_map.md)
3. Validate r-factor distance update per spec
4. Add pivot mode parity tests against C-code

**Gating Tests:**
```bash
# Targeted validation
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_pivots.py
```

**Exit Criteria:**
- BEAM pivot preserves beam center under rotation (tolerance 1e-6)
- SAMPLE pivot moves beam indices with twotheta (tolerance 3.5e-2)
- Both modes match C-code behavior

**Rationale:** Pivot modes are fundamental to detector geometry (ADR-02). Required for correct rotation handling.

---

### Sprint 1.6: Gradient Flow (C16)

**Fix Plan:** [GRADIENT-FLOW-001]
**Failures:** 1
**Owner:** ralph

**Execution Steps:**
1. Isolate gradient break point using systematic tracing
2. Fix differentiability regression (check for `.item()`, `torch.linspace` violations)
3. Add gradient flow regression test
4. Validate end-to-end gradient propagation

**Gating Tests:**
```bash
# Targeted validation
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_gradients.py::test_gradient_flow_simulation
```

**Exit Criteria:**
- Gradient flow test passes
- All differentiable parameters preserve computation graph
- No ADR-08 violations in gradient path

**Rationale:** Gradient correctness is a fundamental PyTorch port requirement (arch.md §15). Must work for optimization capabilities.

---

### Sprint 1.7: Triclinic C Parity (C18)

**Fix Plan:** [TRICLINIC-PARITY-001]
**Failures:** 1
**Owner:** ralph

**Execution Steps:**
1. Generate parallel trace for triclinic case (C vs PyTorch)
2. Identify first divergence in cell tensor or misset rotation
3. Fix triclinic-specific logic to match C-code
4. Validate metric duality preservation

**Gating Tests:**
```bash
# Targeted validation
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_026.py::test_triclinic_absolute_peak_position_vs_c
```

**Exit Criteria:**
- AT-PARALLEL-026 parity threshold met (correlation ≥0.999)
- Triclinic cell tensors match C-code
- Misset rotation preserves metric duality

**Rationale:** Triclinic parity is a spec-a-parallel.md requirement. Critical for validating general crystallographic correctness.

---

### Sprint 1 Gate: Full Suite Validation

**Action:**
```bash
CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/sprint1_gate/pytest_full.xml
```

**Success Criteria:**
- **Failures ≤ 19** (current 36 - Sprint 1 target 17 fixes)
- **No new failures** introduced (regression check)
- **Runtime ≤ 2000s** (similar to Phase H baseline)

**On Failure:**
- Identify regressions introduced during Sprint 1
- Fix regressions before proceeding to Sprint 2
- Update remediation tracker with findings

**Deliverable:**
- Sprint 1 summary document with metrics, artifact paths, and regression analysis

---

## Sprint 2: Infrastructure & Tooling (Priority 2)

**Duration:** 4–5 engineer loops
**Focus:** Testing infrastructure and developer tooling
**Gating Test:** Full suite at sprint end must show ≤10 failures

### Sprint 2.1: Dual Runner Tooling (C5)

**Fix Plan:** [TOOLING-DUAL-RUNNER-001]
**Failures:** 1
**Owner:** ralph

**Execution Steps:**
1. Wire `scripts/comparison/` helpers into test harness
2. Ensure NB_C_BIN resolution follows documented precedence
3. Implement correlation/RMSE metric computation
4. Validate against parity matrix infrastructure

**Gating Tests:**
```bash
# Targeted validation
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_tools_001.py::test_script_integration
```

**Exit Criteria:**
- Dual-runner harness executes C + PyTorch with identical params
- Correlation ≥0.999 threshold enforced
- NB_C_BIN resolution documented

**Rationale:** Dual-runner tooling is essential for ongoing parity validation. Enables faster C↔PyTorch comparison workflows.

---

### Sprint 2.2: CLI Flags Completion (C6)

**Fix Plan:** [CLI-FLAGS-003]
**Failures:** 2
**Owner:** ralph

**Execution Steps:**
1. Complete `-pix0_vector_mm` CLI parsing and detector wiring
2. Fix Fdump roundtrip logic (endianness, header format)
3. Validate against C-code parity for custom pix0 cases
4. Add device parity tests (CPU + CUDA)

**Gating Tests:**
```bash
# Targeted validation
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_flags.py::test_pix0_vector_mm_beam_pivot tests/test_cli_flags.py::test_scaled_hkl_roundtrip
```

**Exit Criteria:**
- Both CLI flags tests pass
- `-pix0_vector_mm` correctly overrides default pix0 calculation
- HKL Fdump roundtrip preserves structure factors

**Rationale:** CLI completeness required for feature parity with C-code. Partial progress already observed (3→2 failures).

---

### Sprint 2.3: Debug Trace Flags (C7)

**Fix Plan:** [DEBUG-TRACE-001]
**Failures:** 4
**Owner:** ralph

**Execution Steps:**
1. Implement `--printout` flag (emit config summary to stdout)
2. Implement `--trace_pixel` flag (per-pixel calculation log)
3. Wire trace output to follow docs/debugging/debugging.md schema
4. Handle out-of-bounds pixel indices gracefully

**Gating Tests:**
```bash
# Targeted validation
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_debug_trace.py
```

**Exit Criteria:**
- All 4 debug trace tests pass
- Trace output matches documented schema
- Combined flags work without conflict

**Rationale:** Debug tooling essential for developer productivity and parallel trace validation. High value for ongoing development.

---

### Sprint 2.4: Tricubic Vectorization (C13)

**Fix Plan:** [VECTOR-TRICUBIC-002]
**Failures:** 2
**Owner:** galph (vectorization specialist)

**Execution Steps:**
1. Fix gather index computation for vectorized tricubic path
2. Ensure OOB warning global flag resets correctly
3. Validate numerical equivalence with scalar reference
4. Add vectorization parity regression test

**Gating Tests:**
```bash
# Targeted validation
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_tricubic_vectorized.py
```

**Exit Criteria:**
- Vectorized tricubic matches scalar implementation
- OOB warning fires exactly once per run
- Numerical equivalence preserved (tolerance ≤1e-12)

**Rationale:** Vectorization parity is a runtime guardrail (docs/development/pytorch_runtime_checklist.md). Must maintain for performance.

---

### Sprint 2 Gate: Full Suite Validation

**Action:**
```bash
CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/sprint2_gate/pytest_full.xml
```

**Success Criteria:**
- **Failures ≤ 10** (Sprint 1 target 19 - Sprint 2 target 9 fixes)
- **No new failures** introduced
- **Runtime ≤ 2000s**

**Deliverable:**
- Sprint 2 summary with infrastructure improvements documented

---

## Sprint 3: Medium Severity & Edge Cases (Priority 3)

**Duration:** 3–4 engineer loops
**Focus:** Less-common features and edge cases
**Gating Test:** Full suite at sprint end must show ≤5 failures

### Sprint 3.1: CUDA Graphs (C11)

**Fix Plan:** [CUDA-GRAPHS-001]
**Failures:** 3
**Owner:** ralph

**Execution Steps:**
1. Investigate torch.compile cache invalidation with CUDA graphs
2. Test dynamic shape handling compatibility
3. Fix graph capture/replay for basic execution
4. Validate gradient flow preservation with graphs enabled

**Gating Tests:**
```bash
# Targeted validation
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_perf_pytorch_005_cudagraphs.py
```

**Exit Criteria:**
- All 3 CUDA graphs tests pass
- Performance improvement documented
- Compatibility note added to performance guide

**Rationale:** Performance optimization feature; not blocking core functionality but valuable for production use.

---

### Sprint 3.2: Mixed Units (C14)

**Fix Plan:** [UNIT-CONV-001]
**Failures:** 1
**Owner:** ralph

**Execution Steps:**
1. Identify specific unit conversion edge case causing failure
2. Fix conversion formula or boundary handling
3. Add unit test for edge case to prevent regression
4. Document ADR-01 hybrid unit system edge case

**Gating Tests:**
```bash
# Targeted validation
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_015.py::test_mixed_units_comprehensive
```

**Exit Criteria:**
- Mixed units test passes
- Unit conversion edge case documented
- Regression test added

**Rationale:** Narrow scope correctness issue; fixes ADR-01 hybrid unit system edge case.

---

### Sprint 3.3: DENZO Convention (C9)

**Fix Plan:** [DENZO-CONVENTION-001]
**Failures:** 1
**Owner:** ralph

**Execution Steps:**
1. Add DENZO case to `Detector.setup_convention()` method
2. Implement DENZO beam-center mapping (Fbeam=Ybeam, Sbeam=Xbeam)
3. Validate basis vectors and twotheta axis against arch.md §7
4. Add DENZO parity test

**Gating Tests:**
```bash
# Targeted validation
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_conventions.py::test_denzo_beam_center_mapping
```

**Exit Criteria:**
- DENZO convention test passes
- Beam-center mapping matches spec
- Architecture documentation updated

**Rationale:** Convention completeness; DENZO less common than MOSFLM/XDS but needed for full spec compliance.

---

### Sprint 3 Gate: Full Suite Validation

**Action:**
```bash
CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/sprint3_gate/pytest_full.xml
```

**Success Criteria:**
- **Failures ≤ 5** (Sprint 2 target 10 - Sprint 3 target 5 fixes)
- **No new failures** introduced
- **Runtime ≤ 2000s**

**Deliverable:**
- Sprint 3 summary with edge case fixes documented

---

## Sprint 4: Deprecation Review (Priority 4)

**Duration:** 1–2 engineer loops
**Focus:** Legacy test suite disposition
**Gating Test:** Full suite at sprint end must show 0 failures

### Sprint 4.1: Legacy Test Suite Review (C12)

**Fix Plan:** [LEGACY-SUITE-001]
**Failures:** 5
**Owner:** ralph

**Classification:** **Likely Deprecation** (pending spec review)

**Execution Steps:**
1. **Schedule spec review** — determine if tests should be deprecated vs rewritten
2. **Option A (Deprecation):**
   - Mark tests with `@pytest.mark.skip(reason="Superseded by AT-PARALLEL-020")`
   - Document deprecation rationale in commit message
   - Update testing strategy to note AT-PARALLEL suite as primary
3. **Option B (Update):**
   - Update tests to match current architecture (Phase D lattice unit fix, etc.)
   - Align with AT-PARALLEL patterns
   - Validate against current spec expectations

**Gating Tests:**
```bash
# After decision:
# Option A: Verify tests skipped
pytest -v tests/test_suite.py -k "sensitivity or performance or extreme or rotation_compatibility"

# Option B: Verify tests pass
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_suite.py::test_sensitivity_to_cell_params tests/test_suite.py::test_performance_simple_cubic tests/test_suite.py::test_performance_triclinic tests/test_suite.py::test_extreme_cell_parameters tests/test_suite.py::test_rotation_compatibility
```

**Exit Criteria:**
- Spec review decision documented (deprecate or update)
- If deprecated: tests skipped, documentation updated
- If updated: tests pass, aligned with current spec

**Rationale:** Low priority; AT-PARALLEL-020 provides comprehensive integration coverage. Resolve to clean up test suite.

---

### Sprint 4 Gate: Full Suite Validation (Final)

**Action:**
```bash
CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/sprint4_gate/pytest_full.xml
```

**Success Criteria:**
- **Failures = 0** (all remediation complete)
- **Pass rate ≥ 95%** (accounting for skipped tests)
- **Runtime ≤ 2000s**
- **No regressions** introduced across all sprints

**Deliverable:**
- **Final remediation summary** with complete metrics, artifact paths
- **Updated testing strategy** documenting new baselines
- **Celebration note** in fix_plan.md 🎉

---

## Cross-Sprint Coordination

### Parallel Work Opportunities

**Safe to run in parallel** (no dependencies):
- Sprint 1.2 (Source Weighting) ∥ Sprint 1.3 (Detector Config)
- Sprint 1.4 (Lattice Shape Models) ∥ Sprint 1.6 (Gradient Flow)
- Sprint 2.1 (Dual Runner) ∥ Sprint 2.2 (CLI Flags)
- Sprint 3.1 (CUDA Graphs) ∥ Sprint 3.2 (Mixed Units)

**Must run sequentially:**
- Pre-Sprint blocker resolution → Sprint 1.1 (Determinism unblocked)
- Sprint 1.3 (Detector Config) → Sprint 1.5 (Detector Pivots)
- All Sprint N items → Sprint N Gate (full suite validation)

### Regression Prevention

**After each cluster fix:**
1. Run targeted tests for that cluster
2. Run related tests that might be affected (e.g., detector config → detector pivots)
3. Check for new failures before committing

**At each sprint gate:**
1. Run full suite with `--maxfail=0` to capture all failures
2. Compare failure count to previous gate (must decrease or stay same)
3. Investigate any new failures as potential regressions
4. Do not proceed to next sprint until gate criteria met

### Documentation Updates

**Continuous updates throughout sprints:**
- `docs/fix_plan.md` — Attempt entries after each cluster fix
- `arch.md` — ADR updates when implementation clarifies decisions
- `docs/development/testing_strategy.md` — Test command updates
- `README_PYTORCH.md` — Feature completion notes

---

## Success Metrics

### Overall Goals
- **36 → 0 failures** across 4 sprints
- **Zero regressions** introduced
- **All spec requirements** met (spec-a-core, spec-a-cli, spec-a-parallel)
- **Documentation complete** for all implemented features

### Sprint-by-Sprint Targets

| Sprint | Clusters Fixed | Failures Resolved | Target Remaining | Cumulative % Complete |
| --- | --- | --- | --- | --- |
| Pre-Sprint | Blocker verification | 0 | 36 | 0% |
| Sprint 1 | C2, C3, C4, C8, C10, C15, C16, C18 | 17 | ≤19 | 47% |
| Sprint 2 | C5, C6, C7, C13 | 9 | ≤10 | 72% |
| Sprint 3 | C9, C11, C14 | 5 | ≤5 | 86% |
| Sprint 4 | C12 | 5 | 0 | 100% |

### Quality Gates
- **No cluster marked complete** without passing targeted tests
- **No sprint marked complete** without passing full-suite gate
- **All fixes** include regression tests to prevent future breaks
- **All documentation** updated to reflect new features/fixes

---

## Contingency Planning

### If Sprint Gate Fails
1. **Identify regressions** introduced during sprint
2. **Fix regressions immediately** before new work
3. **Update gate criteria** if justified by new evidence
4. **Document findings** in remediation tracker

### If Blocker Resurfaces
1. **Pause dependent work** immediately
2. **Resolve blocker** before resuming
3. **Update dependency chain** in tracker
4. **Re-plan sprint sequence** if needed

### If Timeline Exceeds Estimate
1. **Assess complexity** of remaining work
2. **Re-prioritize** if needed (defer P3/P4 to future sprint)
3. **Document lessons learned** for future estimation

---

## Artifact Management

### Required Artifacts per Sprint
- **Sprint plan** — clusters, sequence, gating tests
- **Pytest logs** — targeted tests + gate run
- **Metrics summary** — pass/fail counts, runtime, deltas
- **Code changes** — commit SHAs and file lists
- **Documentation diffs** — spec/arch/testing updates

### Artifact Locations
- **Sprint plans:** `reports/2026-01-test-suite-triage/sprints/sprint_N/plan.md`
- **Gate logs:** `reports/2026-01-test-suite-triage/sprints/sprint_N/gate/pytest_full.log`
- **Summaries:** `reports/2026-01-test-suite-triage/sprints/sprint_N/summary.md`

---

## References

- **Remediation tracker:** reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md
- **Phase I triage:** reports/2026-01-test-suite-triage/phase_i/20251011T042127Z/docs/triage_summary.md
- **Fix plan ledger:** docs/fix_plan.md
- **Testing strategy:** docs/development/testing_strategy.md
- **Spec (core):** specs/spec-a-core.md
- **Spec (CLI):** specs/spec-a-cli.md
- **Spec (parallel):** specs/spec-a-parallel.md
- **Architecture:** arch.md

---

**Sequence Status:** Phase J2 COMPLETE — ready for fix_plan dependency updates (J3)
