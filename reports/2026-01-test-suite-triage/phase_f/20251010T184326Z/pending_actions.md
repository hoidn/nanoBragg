# Pending Actions Table - Phase F (2026 Refresh)

**Date:** 2025-10-10
**Timestamp:** 20251010T184326Z
**Source:** Phase E failures (49 tests) + Phase C triage classification
**Status:** 17 active clusters, 1 resolved (C1)

## Priority 1: Critical Path (Unblock Other Work)

| Cluster | Fix Plan ID | Owner | Status | Reproduction Command | Expected Artifacts | Blocker | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C15 | [DTYPE-NEUTRAL-001] | ralph | in_progress | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_perf_pytorch_006.py` | `reports/dtype-neutral/phase_c/{remediation_plan.md,tests.md,docs_updates.md}` | None | **CRITICAL BLOCKER** for C2; Detector cache dtype mismatch |
| C2 | [DETERMINISM-001] | ralph | in_progress | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py` | `reports/determinism/phase_a/{summary.md,reproduction_logs/}` | [DTYPE-NEUTRAL-001] | Phase A complete; blocked until dtype fix lands |
| C11 | [DEBUG-TRACE-001] | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_debug_trace.py` | Plan under `plans/active/debug-trace.md`, implementation in `__main__.py` | None | Debugging infrastructure; `--printout` & `--trace_pixel` flags |

## Priority 2: Spec Compliance (High Severity)

| Cluster | Fix Plan ID | Owner | Status | Reproduction Command | Expected Artifacts | Blocker | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C4 | [DETECTOR-GRAZING-001] | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_017.py` | Plan under `plans/active/detector-grazing.md` | [VECTOR-PARITY-001] Tap 5 | Grazing incidence (near-90° angles); spec §4.6 |
| C7 | [SOURCE-WEIGHT-002] | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py` | Plan under `plans/active/source-weight.md`, fix in `simulator.py` | None | Regression after [SOURCE-WEIGHT-001] closed; simulator path broken |
| C12 | [DETECTOR-CONFIG-001] | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py` | Plan under `plans/active/detector-config.md`, audit of `config.py` + `detector.py` | None | Defaults audit; spec §4 alignment |
| C8 | [LATTICE-SHAPE-001] | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels` | Plan under `plans/active/lattice-shape.md`, implementation in `utils/physics.py` | None | GAUSS/TOPHAT models; spec §8 |
| C17 | [GRADIENT-FLOW-001] | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation` | Plan under `plans/active/gradient-flow.md`, audit of differentiability per arch.md §15 | None | End-to-end gradient flow broken; ADR-08 violation |
| C14 | [PIVOT-MODE-001] | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_pivots.py` | Plan under `plans/active/pivot-mode.md`, fix in `detector.py` pivot logic | None | BEAM vs SAMPLE pivot behavior; ADR-02 alignment |
| C18 | [TRICLINIC-PARITY-001] | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_026.py::TestAT_PARALLEL_026_TriclinicAbsolutePosition::test_triclinic_absolute_peak_position_vs_c` | Plan under `plans/active/triclinic-parity.md`, fix in `crystal.py` misset/cell logic | None | AT-PARALLEL-026 parity threshold; likely misset or cell tensor issue |

## Priority 3: Infrastructure & Tooling

| Cluster | Fix Plan ID | Owner | Status | Reproduction Command | Expected Artifacts | Blocker | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C9 | [TOOLING-DUAL-RUNNER-001] | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_tools_001.py::TestAT_TOOLS_001_DualRunnerComparison::test_script_integration` | Plan under `plans/active/dual-runner.md`, restoration of `scripts/dual_runner.py` | None | C vs PyTorch comparison harness; spec-a-parallel.md §2.5 |
| C10 | [CLI-FLAGS-003] | ralph | in_progress | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_flags.py` | Fixes in `__main__.py` argparse + `detector.py` pix0 override + `io/hkl.py` Fdump roundtrip | None | `-pix0_vector_mm` parsing + HKL Fdump roundtrip logic |
| C6 | [VECTOR-TRICUBIC-002] | galph | in_progress | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_tricubic_vectorized.py` | Fix in `utils/physics.py` or `models/crystal.py` gather/OOB logic | None | Vectorized tricubic parity; gather index or OOB warning regression |
| C3 | [CUDA-GRAPHS-001] | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_perf_pytorch_005_cudagraphs.py` | Plan under `plans/active/cuda-graphs.md`, investigation of torch.compile cache | None | CUDA graphs compatibility; medium priority (performance opt) |

## Priority 4: Low/Deferred

| Cluster | Fix Plan ID | Owner | Status | Reproduction Command | Expected Artifacts | Blocker | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C5 | [UNIT-CONV-001] | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive` | Plan under `plans/active/unit-conv.md`, fix in ADR-01 hybrid unit boundaries | None | Mixed-unit edge case; narrow scope |
| C13 | [DENZO-CONVENTION-001] | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_conventions.py::TestDetectorConventions::test_denzo_beam_center_mapping` | Plan under `plans/active/denzo-convention.md`, implementation in `detector.py` convention mapping | None | DENZO beam-center mapping; less common than MOSFLM/XDS |
| C16 | [LEGACY-SUITE-001] | ralph | in_planning | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_suite.py::TestTier1TranslationCorrectness -k "sensitivity or performance or extreme or rotation_compatibility"` | Plan under `plans/active/legacy-suite.md`, triage for deprecation vs rewrite | None | Older Tier 1 tests; candidate for deprecation (superseded by AT-PARALLEL) |

## Resolved Clusters (No Action Required)

| Cluster | Fix Plan ID | Owner | Status | Resolution Date | Notes |
| --- | --- | --- | --- | --- | --- |
| C1 | [CLI-DEFAULTS-001] | ralph | done | 2025-10-10 | HKL guard fix in `__main__.py`; targeted test now passes; fix_plan.md Attempt #6 |

## Cross-References

### Fix Plan Ledger
All pending actions link to entries in `docs/fix_plan.md`:
- Lines 13-37: Index table with all fix-plan IDs
- Lines 39-100+: Detailed entries with Attempts History and Next Actions

### Active Plans
Plans referenced in Expected Artifacts column:
- `plans/active/test-suite-triage.md` - This plan (Phase F current step)
- `plans/active/dtype-neutral.md` - P1.1 critical blocker
- `plans/active/determinism.md` - P1.2 (blocked)
- Individual cluster plans to be created as remediation proceeds

### Spec & Architecture References
- **Spec:** `specs/spec-a-core.md`, `specs/spec-a-cli.md`, `specs/spec-a-parallel.md`
- **Arch:** `arch.md` (esp. §7 conventions, §15 differentiability, ADR-01/ADR-02/ADR-08)
- **Testing:** `docs/development/testing_strategy.md`, `docs/development/pytorch_runtime_checklist.md`

## Blocker Resolution Sequencing

### Critical Path (Must Resolve First)
1. **[DTYPE-NEUTRAL-001]** (C15) - Phase C remediation blueprint needed
   - Unblocks: [DETERMINISM-001] (C2)
   - Priority: P1.1

2. **[DETERMINISM-001]** (C2) - Phase A complete, awaiting dtype fix
   - Blocked by: [DTYPE-NEUTRAL-001]
   - Priority: P1.2

3. **[VECTOR-PARITY-001]** (external) - Tap 5 completion
   - Unblocks: [DETECTOR-GRAZING-001] (C4)
   - Priority: External tracker

### Parallel Tracks (Can Proceed Independently)
- **P1.3:** [DEBUG-TRACE-001] (C11) - No blockers
- **P2:** [SOURCE-WEIGHT-002] (C7), [DETECTOR-CONFIG-001] (C12), [LATTICE-SHAPE-001] (C8) - No blockers
- **P3:** [TOOLING-DUAL-RUNNER-001] (C9), [CLI-FLAGS-003] (C10), [VECTOR-TRICUBIC-002] (C6) - Already in_progress

## Recommended Coordination Strategy

### Phase G Handoff (Next Supervisor Loop)
1. **Issue [DTYPE-NEUTRAL-001] Phase C blueprint** to ralph as highest priority
2. **Hold [DETERMINISM-001]** delegation until dtype fix attempt logged
3. **Monitor [VECTOR-PARITY-001]** for Tap 5 completion (external to triage)
4. **Delegate [DEBUG-TRACE-001]** as P1.3 (no blockers, high value)

### Parallel Execution Opportunities
Ralph can work P2/P3 items while waiting for blocker resolutions:
- [SOURCE-WEIGHT-002] (regression fix)
- [DETECTOR-CONFIG-001] (spec alignment)
- [LATTICE-SHAPE-001] (GAUSS/TOPHAT models)

Galph continues:
- [VECTOR-TRICUBIC-002] (vectorization parity)

### Expected Velocity
- **Week 1:** Resolve [DTYPE-NEUTRAL-001], unblock [DETERMINISM-001]
- **Week 2:** Complete [DETERMINISM-001], [DEBUG-TRACE-001], start P2 items
- **Week 3-4:** Clear P2 spec compliance items (C4, C7, C8, C12, C14, C17, C18)
- **Week 5+:** P3 infrastructure and P4 deferred items

## Artifact Expectations Summary

### Phase C Blueprints (Immediate Need)
- `reports/dtype-neutral/phase_c/remediation_plan.md` - [DTYPE-NEUTRAL-001]
- `plans/active/debug-trace.md` - [DEBUG-TRACE-001]

### Implementation Artifacts (Per Cluster)
- Plan file under `plans/active/<cluster>.md`
- Attempt logs under `reports/<initiative>/`
- Code changes in relevant modules (`__main__.py`, `detector.py`, `crystal.py`, `simulator.py`, `utils/`)
- Updated `docs/fix_plan.md` Attempts History

### Validation Artifacts
- Targeted pytest run logs (success)
- Full suite regression check (no new failures)
- Updated test status in `docs/test_status.md` (if applicable)

---

**Phase F3 Complete:** Pending actions table published with priorities, owners, reproduction commands, and blocker chains.

**Next:** Phase G coordination (handoff refresh + supervisor input template update).
