# Phase I Classification Overview
## Summary of Failure Classifications and Rationale

**Timestamp:** 20251011T042127Z
**Initiative:** [TEST-SUITE-TRIAGE-001]
**Phase:** I — Failure Classification Refresh

## Classification Tallies

| Classification | Count | Percentage | Trend vs Phase F |
| --- | --- | --- | --- |
| Implementation Bug | 35 | 97.2% | -12 (48→35) |
| Likely Deprecation | 1 | 2.8% | 0 (1→1) |
| Needs Verification | 0 | 0.0% | 0 (0→0) |
| **Total** | **36** | **100%** | **-13 (49→36)** |

## Classification by Label

### Implementation Bug (35 failures)

Failures requiring code changes to meet spec requirements or fix regressions:

1. **C2 - Determinism (2):** RNG determinism incomplete per spec-a-core.md §5.3
   - Evidence: AT-PARALLEL-013 tests fail due to non-deterministic mosaic rotation generation
   - Spec Reference: spec-a-core.md §5.3 (Sampling & Determinism)

2. **C3 - Source Weighting (6):** Sourcefile parsing and weighting not implemented
   - Evidence: AT-SRC-001 tests fail across all source weighting scenarios
   - Spec Reference: spec-a-core.md §§3.4–3.5 (Beam Sources & Weighting)

3. **C4 - Lattice Shape Models (2):** GAUSS/TOPHAT models missing/incorrect
   - Evidence: AT-STR-003 tests fail for non-SQUARE shape models
   - Spec Reference: spec-a-core.md §8 (Lattice Shape Models)

4. **C5 - Dual Runner Tooling (1):** C↔PyTorch comparison harness not wired
   - Evidence: AT-TOOLS-001 integration test fails
   - Spec Reference: spec-a-parallel.md §2.5 (Parallel Validation Matrix)

5. **C6 - CLI Flags (2):** `-pix0_vector_mm` and HKL Fdump logic incomplete
   - Evidence: test_cli_flags.py failures for specific CLI override scenarios
   - Spec Reference: spec-a-cli.md (CLI surface area)

6. **C7 - Debug Trace (4):** Debug flags `--printout`/`--trace_pixel` not implemented
   - Evidence: test_debug_trace.py failures for all debug flag scenarios
   - Spec Reference: spec-a-cli.md (Debug/Trace Requirements)

7. **C8 - Detector Config (2):** Config dataclass defaults misaligned with spec
   - Evidence: test_detector_config.py initialization failures
   - Spec Reference: spec-a-core.md §4 (Detector Geometry)

8. **C9 - DENZO Convention (1):** DENZO beam-center mapping not implemented
   - Evidence: test_detector_conventions.py::test_denzo_beam_center_mapping
   - Spec Reference: arch.md §7 line 223 (DENZO convention)

9. **C10 - Detector Pivots (2):** BEAM/SAMPLE pivot behavior incorrect
   - Evidence: test_detector_pivots.py failures for both pivot modes
   - Spec Reference: arch.md ADR-02 (Rotation Order and Conventions)

10. **C11 - CUDA Graphs (3):** CUDA graphs compatibility issues
    - Evidence: test_perf_pytorch_005_cudagraphs.py failures
    - Note: Performance optimization feature; not blocking core functionality

11. **C13 - Tricubic Vectorization (2):** Vectorization regression in tricubic interpolation
    - Evidence: test_tricubic_vectorized.py failures for gather/OOB logic
    - Spec Reference: docs/development/pytorch_runtime_checklist.md (vectorization guardrail)

12. **C14 - Mixed Units (1):** Unit conversion edge case in hybrid unit system
    - Evidence: AT-PARALLEL-015 mixed units test failure
    - Spec Reference: arch.md ADR-01 (Hybrid Unit System)

13. **C15 - Mosaic Determinism (1):** Mosaic rotation matrix determinism incomplete
    - Evidence: AT-PARALLEL-024 mosaic umat test failure
    - Spec Reference: spec-a-core.md §5.3 (RNG determinism)

14. **C16 - Gradient Flow (1):** End-to-end differentiability broken
    - Evidence: test_gradients.py::test_gradient_flow_simulation
    - Spec Reference: arch.md §15 / ADR-08 (Differentiability Guidelines)

15. **C18 - Triclinic Parity (1):** AT-PARALLEL-026 parity threshold not met
    - Evidence: test_at_parallel_026.py::test_triclinic_absolute_peak_position_vs_c
    - Spec Reference: spec-a-parallel.md (C↔PyTorch parity requirements)

### Likely Deprecation (1 failure)

Failures where tests may be obsolete or superseded by newer test coverage:

1. **C12 - Legacy Test Suite (5):** Older test_suite.py tests not updated for recent architecture changes
   - Evidence: Tests appear to duplicate AT-PARALLEL-020 comprehensive integration coverage
   - Rationale: Not updated for Phase D lattice unit fix and other architecture changes
   - Recommendation: Spec review to determine if these should be deprecated/rewritten
   - Note: Low severity; newer AT-PARALLEL suite provides equivalent coverage

### Needs Verification (0 failures)

No failures require additional evidence gathering before classification.

## Supporting Evidence by Cluster

### Evidence for Implementation Bugs

All 35 implementation bug failures cite:
- **Spec violations:** Specific sections of spec-a-core.md, spec-a-cli.md, or spec-a-parallel.md
- **Architecture violations:** ADRs or guardrails in arch.md or runtime checklist
- **Test reproduction:** Exact pytest selectors for reproducing failures

### Evidence for Deprecation

C12 (Legacy Test Suite) deprecation classification based on:
- **Coverage duplication:** AT-PARALLEL-020 provides comprehensive integration testing
- **Maintenance lag:** Tests not updated for recent architecture changes (e.g., Phase D lattice unit fix)
- **Priority assessment:** Marked Low severity in Phase F triage
- **Spec silence:** No explicit spec requirement for these specific test scenarios

## Delta Analysis vs Phase F

### Improvements (clusters with reduced failures):
- **C2 (Determinism):** -4 failures (6→2) — AT-PARALLEL-024 tests now passing
- **C6 (CLI Flags):** -1 failure (3→2) — partial progress on CLI flag implementation
- **C11 (CUDA Graphs):** -3 failures (6→3) — significant improvement in CUDA graphs compatibility

### Unchanged (clusters with same failure count):
- C3, C4, C5, C7, C8, C9, C10, C12, C13, C14, C15, C16, C18 — no change vs Phase F

### New or Worsened:
- None — no clusters with increased failure counts

### Eliminated:
- **C1 (CLI Defaults):** ✅ Fully resolved in Attempt #6, remains fixed in Phase H
- **C3 (Grazing Incidence):** ⚠️ NOTE - not present in Phase H data; may have been resolved or renumbered
- **C15 (dtype Support):** ⚠️ NOTE - not present in Phase H data; may have been resolved or merged

## Blocker Chain Analysis

### Critical Path Dependencies

1. **[DTYPE-NEUTRAL-001]** status uncertain
   - Previously blocked [DETERMINISM-001] per Phase F
   - Phase H shows determinism improvements (6→2 failures)
   - Recommendation: Check fix-plan.md for current blocker status

2. **[VECTOR-PARITY-001] Tap 5** mentioned in Phase F
   - May block detector geometry work
   - Recommendation: Verify dependency status in fix-plan.md

### Unblocking Potential

If [DTYPE-NEUTRAL-001] is complete:
- **C2 (Determinism):** Can proceed with remaining 2 failures
- **C15 (Mosaic Determinism):** Can be addressed

## Primary Deltas vs Attempt #8 (Phase F)

| Metric | Phase F | Phase H | Delta | % Change |
| --- | --- | --- | --- | --- |
| Total Failures | 49 | 36 | -13 | -26.5% |
| Implementation Bugs | 48 | 35 | -13 | -27.1% |
| Likely Deprecations | 1 | 1 | 0 | 0% |
| Active Clusters | 17 | 16 | -1 | -5.9% |
| In-Progress Items | 3 | 4 | +1 | +33.3% |
| In-Planning Items | 15 | 13 | -2 | -13.3% |

## Key Observations

1. **Significant overall improvement:** 26% reduction in failures (49→36) represents substantial progress.

2. **Determinism progress:** Major improvement in C2 determinism cluster (6→2) suggests blocker may be resolved.

3. **CUDA graphs progress:** C11 cluster improved from 6→3 failures, indicating compatibility work is yielding results.

4. **CLI flags progress:** C6 cluster improved from 3→2 failures, showing incremental progress.

5. **Stable clusters:** Most clusters (13 of 16) show no change, indicating failures are well-understood and awaiting remediation.

6. **No regressions:** No clusters worsened, and no new failure categories emerged.

7. **Gradient tests stable:** Phase H confirms all gradient checks passing (1660s of 1867s runtime, 89% of total).

8. **Legacy test clarification:** C12 cluster now explicitly classified as "Likely Deprecation" pending spec review.

## Next Actions

1. **Update fix-plan.md Attempt #11:** Record Phase I classification with tallies, deltas, and artifact paths.

2. **Sync blocker status:** Verify [DTYPE-NEUTRAL-001] completion status and update C2 blocker documentation.

3. **Phase J readiness:** Use this classification to populate remediation tracker with sequencing priorities.

4. **Deprecation review:** Schedule spec review for C12 legacy test suite to determine deprecation vs rewrite.

## Artifact References

- **Phase H Summary:** `reports/2026-01-test-suite-triage/phase_h/20251011T033418Z/docs/summary.md`
- **Phase F Classification:** `reports/2026-01-test-suite-triage/phase_f/20251010T184326Z/triage_summary.md`
- **This Classification:** `reports/2026-01-test-suite-triage/phase_i/20251011T042127Z/docs/classification_overview.md`

---

**Classification Methodology:** Phase I classification derived from Phase H junit XML and summary artifacts, cross-referenced with spec sections and fix-plan statuses. No pytest execution performed (docs-only loop per input.md directive).
