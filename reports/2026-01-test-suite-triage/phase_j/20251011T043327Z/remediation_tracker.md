# Phase J Remediation Tracker
## Test Suite Failure Remediation Roadmap

**Timestamp:** 20251011T043327Z
**Initiative:** [TEST-SUITE-TRIAGE-001]
**Phase:** J — Remediation Launch & Tracking
**Data Source:** Phase I triage (reports/2026-01-test-suite-triage/phase_i/20251011T042127Z/)

---

## Executive Summary

This tracker maps all 36 active test failures across 16 clusters to their owning fix-plan items, defines reproduction commands, documents blocking dependencies, and specifies exit criteria. Use this document as the single source of truth for remediation execution order and progress tracking.

**Current Status:**
- **Total Failures:** 36 (down from 49 in Phase F, -26% improvement)
- **Active Clusters:** 16 (C1 resolved, C3/C15 eliminated/merged)
- **Implementation Bugs:** 35 (97.2%)
- **Likely Deprecations:** 1 (2.8% — C12 legacy suite)

**Blocker Notes:**
- [DTYPE-NEUTRAL-001] completion status requires verification (previously blocked [DETERMINISM-001])
- [VECTOR-PARITY-001] Tap 5 instrumentation paused pending Phase J sequencing

---

## Remediation Tracker Table

| Cluster ID | Category | Count | Owner | Fix Plan ID | Priority | Status | Blocker | Dependencies |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | CLI Defaults | 0 | ralph | [CLI-DEFAULTS-001] | ✅ RESOLVED | done | - | - |
| C2 | Determinism - Mosaic RNG | 2 | ralph | [DETERMINISM-001] | P1.1 | in_progress | [DTYPE-NEUTRAL-001]? | Verify dtype fix complete |
| C3 | Source Weighting | 6 | ralph | [SOURCE-WEIGHT-002] | P1.2 | in_planning | - | None |
| C4 | Lattice Shape Models | 2 | ralph | [LATTICE-SHAPE-001] | P1.4 | in_planning | - | None |
| C5 | Dual Runner Tooling | 1 | ralph | [TOOLING-DUAL-RUNNER-001] | P2.1 | in_planning | - | None |
| C6 | CLI Flags (pix0/HKL) | 2 | ralph | [CLI-FLAGS-003] | P2.2 | in_progress | - | None |
| C7 | Debug Trace | 4 | ralph | [DEBUG-TRACE-001] | P2.3 | in_planning | - | None |
| C8 | Detector Config | 2 | ralph | [DETECTOR-CONFIG-001] | P1.3 | in_planning | - | None |
| C9 | DENZO Convention | 1 | ralph | [DENZO-CONVENTION-001] | P3.3 | in_planning | - | None |
| C10 | Detector Pivots | 2 | ralph | [PIVOT-MODE-001] | P1.5 | in_planning | - | None |
| C11 | CUDA Graphs | 3 | ralph | [CUDA-GRAPHS-001] | P3.1 | in_planning | - | None |
| C12 | Legacy Test Suite | 5 | ralph | [LEGACY-SUITE-001] | P4.1 | in_planning | - | Spec review for deprecation |
| C13 | Tricubic Vectorization | 2 | galph | [VECTOR-TRICUBIC-002] | P2.4 | in_progress | - | Vectorization specialist |
| C14 | Mixed Units | 1 | ralph | [UNIT-CONV-001] | P3.2 | in_planning | - | None |
| C15 | Mosaic Determinism | 1 | ralph | [DETERMINISM-001] | P1.1 | in_progress | [DTYPE-NEUTRAL-001]? | Same as C2 |
| C16 | Gradient Flow | 1 | ralph | [GRADIENT-FLOW-001] | P1.6 | in_planning | - | None |
| C18 | Triclinic C Parity | 1 | ralph | [TRICLINIC-PARITY-001] | P1.7 | in_planning | - | None |

---

## Cluster Details with Reproduction Commands

### ✅ C1: CLI Defaults (RESOLVED)

**Status:** ✅ Fully resolved in [CLI-DEFAULTS-001] Attempt #6
**Exit Criteria:** Minimal `-default_F` CLI invocation emits non-zero intensities
**Validation:** Remains stable through Phase H rerun (no regressions)

---

### C2: Determinism - Mosaic RNG (2 failures)

**Fix Plan:** [DETERMINISM-001] (in_progress)
**Owner:** ralph
**Priority:** P1.1 (Critical — spec reproducibility requirement)

**Reproduction:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py::test_pytorch_determinism_same_seed tests/test_at_parallel_013.py::test_pytorch_determinism_different_seeds
```

**Blocker:** [DTYPE-NEUTRAL-001] status uncertain — verify completion before resuming
**Dependencies:** Phase H shows major improvement (6→2 failures); blocker may be resolved

**Exit Criteria:**
- Same-seed runs produce bitwise-identical output
- Different-seed runs produce documented divergence
- Seed propagation contract documented in code + docs

**Spec Reference:** spec-a-core.md §5.3 (RNG & Determinism)

**Next Actions:**
1. Verify [DTYPE-NEUTRAL-001] completion status in fix_plan.md
2. Re-run AT-PARALLEL-013 with CPU-only (`CUDA_VISIBLE_DEVICES=-1`) to bypass TorchDynamo blocker
3. Address remaining 2 failures (test_pytorch_determinism_same_seed, test_pytorch_determinism_different_seeds)

**Artifacts Expected:**
- Pytest log showing bitwise equality for same-seed runs
- Documentation update: seed semantics in `docs/development/testing_strategy.md`

---

### C3: Source Weighting (6 failures)

**Fix Plan:** [SOURCE-WEIGHT-002] (in_planning)
**Owner:** ralph
**Priority:** P1.2 (High — spec compliance §§3.4–3.5)

**Reproduction:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py
```

**Blocker:** None
**Dependencies:** None

**Exit Criteria:**
- Sourcefile parsing handles all column configurations (X,Y,Z, wavelength, weight)
- Multi-source runs apply weights correctly in normalization
- Flux normalization matches spec equations

**Spec Reference:** spec-a-core.md §§3.4–3.5 (Beam Sources & Weighting)

**Next Actions:**
1. Author follow-up plan ensuring `Simulator` multiplies source weights
2. Audit flux normalization path against spec
3. Add regression tests validating weighted multi-source runs

**Artifacts Expected:**
- Passing AT-SRC-001 test suite (6 tests)
- Source weighting implementation in `simulator.py`
- Documentation of weight normalization in architecture

---

### C4: Lattice Shape Models (2 failures)

**Fix Plan:** [LATTICE-SHAPE-001] (in_planning)
**Owner:** ralph
**Priority:** P1.4 (High — spec §8 compliance)

**Reproduction:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_str_003.py::test_gauss_shape_model tests/test_at_str_003.py::test_shape_model_comparison
```

**Blocker:** None
**Dependencies:** None

**Exit Criteria:**
- GAUSS lattice shape model implemented per spec formula
- TOPHAT lattice shape model implemented per spec formula
- Shape model comparison tests pass (SQUARE/ROUND/GAUSS/TOPHAT equivalence where expected)

**Spec Reference:** spec-a-core.md §8 (Lattice Shape Models)

**Next Actions:**
1. Implement GAUSS model: `F_latt = Na·Nb·Nc·exp(−Δr*²/2σ²)` with spec cutoff
2. Implement TOPHAT model: `F_latt = Na·Nb·Nc` inside cutoff, 0 outside
3. Validate normalization factors against C-code golden data

**Artifacts Expected:**
- Passing AT-STR-003 tests (2 tests)
- Implementation in `utils/physics.py` or `models/crystal.py`
- Parity validation with C-code for GAUSS/TOPHAT cases

---

### C5: Dual Runner Tooling (1 failure)

**Fix Plan:** [TOOLING-DUAL-RUNNER-001] (in_planning)
**Owner:** ralph
**Priority:** P2.1 (High — testing infrastructure)

**Reproduction:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_tools_001.py::test_script_integration
```

**Blocker:** None
**Dependencies:** Requires NB_C_BIN path resolution (precedence documented in testing_strategy.md §2.5)

**Exit Criteria:**
- Dual-runner harness executes both C and PyTorch with identical parameters
- Correlation/RMSE metrics computed and saved
- Integration test passes with correlation ≥0.999 threshold

**Spec Reference:** spec-a-parallel.md §2.5 (Tooling Requirements)

**Next Actions:**
1. Wire `scripts/comparison/` helpers into test harness
2. Ensure NB_C_BIN resolution follows documented precedence (env → golden_suite_generator → root)
3. Validate metric computation against existing parity matrix infrastructure

**Artifacts Expected:**
- Passing AT-TOOLS-001 test
- Updated dual-runner documentation in testing_strategy.md

---

### C6: CLI Flags (2 failures) ⬇️ IMPROVED

**Fix Plan:** [CLI-FLAGS-003] (in_progress)
**Owner:** ralph
**Priority:** P2.2 (High — CLI completeness)

**Reproduction:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_flags.py::test_pix0_vector_mm_beam_pivot tests/test_cli_flags.py::test_scaled_hkl_roundtrip
```

**Blocker:** None
**Dependencies:** None

**Exit Criteria:**
- `-pix0_vector_mm` flag parsed and applied to detector pix0 calculation
- HKL Fdump roundtrip (write → read → verify) preserves structure factors
- Both tests pass with device parity (CPU + CUDA)

**Spec Reference:** spec-a-cli.md (CLI surface area)

**Change:** -1 failure vs Phase F (3→2); partial progress observed

**Next Actions:**
1. Complete `-pix0_vector_mm` CLI parsing and detector wiring
2. Fix Fdump roundtrip logic (endianness, header format)
3. Validate against C-code parity for custom pix0 cases

**Artifacts Expected:**
- Passing CLI flags tests (2 tests)
- CLI parameter documentation update

---

### C7: Debug Trace (4 failures)

**Fix Plan:** [DEBUG-TRACE-001] (in_planning)
**Owner:** ralph
**Priority:** P2.3 (High — debugging tooling)

**Reproduction:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_debug_trace.py
```

**Blocker:** None
**Dependencies:** None

**Exit Criteria:**
- `--printout` flag emits configuration summary to stdout
- `--trace_pixel s f` emits detailed per-pixel calculation log
- Combined flags work together without conflict
- Out-of-bounds pixel indices handled gracefully (error or warning)

**Spec Reference:** spec-a-cli.md (Debug/Trace Requirements)

**Next Actions:**
1. Implement `--printout` flag in `__main__.py` (emit config after parsing)
2. Implement `--trace_pixel` flag (add instrumentation to simulator)
3. Wire trace output to follow schema from docs/debugging/debugging.md §Trace Schema

**Artifacts Expected:**
- Passing debug trace tests (4 tests)
- Trace output examples in documentation

---

### C8: Detector Config (2 failures)

**Fix Plan:** [DETECTOR-CONFIG-001] (in_planning)
**Owner:** ralph
**Priority:** P1.3 (High — spec §4 baseline)

**Reproduction:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py
```

**Blocker:** None
**Dependencies:** None

**Exit Criteria:**
- DetectorConfig dataclass defaults match spec-a-core.md §4 table
- Custom initialization preserves all user-specified parameters
- Default beam-center calculations respect convention (MOSFLM vs XDS)

**Spec Reference:** spec-a-core.md §4 (Detector Geometry), arch.md ADR-02

**Next Actions:**
1. Audit DetectorConfig defaults against spec table
2. Fix any mismatched defaults (distance, pixel_size, beam_center formulas)
3. Validate initialization paths (CLI → config → Detector)

**Artifacts Expected:**
- Passing detector config tests (2 tests)
- Documentation of default resolution in architecture

---

### C9: DENZO Convention (1 failure)

**Fix Plan:** [DENZO-CONVENTION-001] (in_planning)
**Owner:** ralph
**Priority:** P3.3 (Medium — less-common convention)

**Reproduction:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_conventions.py::test_denzo_beam_center_mapping
```

**Blocker:** None
**Dependencies:** None

**Exit Criteria:**
- DENZO convention beam-center mapping implemented: `Fbeam = Ybeam; Sbeam = Xbeam`
- DENZO basis vectors and twotheta axis match arch.md §7 specification
- Test validates beam-center preservation for DENZO mode

**Spec Reference:** arch.md §7 line 223 (DENZO convention)

**Next Actions:**
1. Add DENZO case to `Detector.setup_convention()` method
2. Implement DENZO-specific beam-center mapping (no +0.5 offset like MOSFLM)
3. Validate against spec table for basis vectors

**Artifacts Expected:**
- Passing DENZO convention test
- Architecture documentation update for DENZO support

---

### C10: Detector Pivots (2 failures)

**Fix Plan:** [PIVOT-MODE-001] (in_planning)
**Owner:** ralph
**Priority:** P1.5 (High — fundamental geometry)

**Reproduction:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_pivots.py
```

**Blocker:** None
**Dependencies:** None

**Exit Criteria:**
- BEAM pivot preserves beam center pixel indices under rotation
- SAMPLE pivot moves beam indices predictably with twotheta
- Both pivot modes pass parity checks against C-code

**Spec Reference:** arch.md ADR-02 (Rotation Order and Conventions)

**Next Actions:**
1. Audit `Detector.compute_pix0()` logic for BEAM vs SAMPLE formulas
2. Fix pivot mode detection from CLI flags (per c_to_pytorch_config_map.md)
3. Validate r-factor distance update per spec

**Artifacts Expected:**
- Passing pivot mode tests (2 tests)
- Pivot mode documentation in architecture

---

### C11: CUDA Graphs (3 failures) ⬇️ IMPROVED

**Fix Plan:** [CUDA-GRAPHS-001] (in_planning)
**Owner:** ralph
**Priority:** P3.1 (Medium — performance optimization)

**Reproduction:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_perf_pytorch_005_cudagraphs.py
```

**Blocker:** None
**Dependencies:** None

**Exit Criteria:**
- CUDA graphs capture/replay works for basic execution
- Gradient flow preserved with CUDA graphs enabled
- CPU/CUDA correlation maintained with graphs

**Note:** Performance feature; not blocking core functionality

**Change:** -3 failures vs Phase F (6→3); significant improvement

**Next Actions:**
1. Investigate torch.compile cache invalidation with CUDA graphs
2. Test dynamic shape handling compatibility
3. Add CUDA graphs compatibility note to performance guide

**Artifacts Expected:**
- Passing CUDA graphs tests (3 tests)
- Performance documentation update

---

### C12: Legacy Test Suite (5 failures) — DEPRECATION CANDIDATE

**Fix Plan:** [LEGACY-SUITE-001] (in_planning)
**Owner:** ralph
**Priority:** P4.1 (Low — likely deprecation)

**Reproduction:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_suite.py::test_sensitivity_to_cell_params tests/test_suite.py::test_performance_simple_cubic tests/test_suite.py::test_performance_triclinic tests/test_suite.py::test_extreme_cell_parameters tests/test_suite.py::test_rotation_compatibility
```

**Classification:** **Likely Deprecation**

**Blocker:** Spec review required
**Dependencies:** Determine if AT-PARALLEL suite provides equivalent coverage

**Rationale:**
- Tests not updated for recent architecture changes (Phase D lattice unit fix)
- AT-PARALLEL-020 provides comprehensive integration coverage
- Legacy test patterns may conflict with current spec

**Next Actions:**
1. Schedule spec review to determine deprecation vs rewrite
2. If deprecated: mark tests with `@pytest.mark.skip(reason="Superseded by AT-PARALLEL-020")`
3. If retained: update tests to match current architecture

**Artifacts Expected:**
- Spec review decision documented in issue/ADR
- Test suite cleanup or update as appropriate

---

### C13: Tricubic Vectorization (2 failures)

**Fix Plan:** [VECTOR-TRICUBIC-002] (in_progress)
**Owner:** galph (vectorization specialist)
**Priority:** P2.4 (High — vectorization guardrail)

**Reproduction:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_tricubic_vectorized.py
```

**Blocker:** None
**Dependencies:** Vectorization specialist expertise

**Exit Criteria:**
- Vectorized tricubic interpolation matches scalar implementation
- OOB warning fires exactly once per run (not per-pixel)
- Gather index handling preserves numerical equivalence

**Spec Reference:** docs/development/pytorch_runtime_checklist.md (vectorization guardrail)

**Next Actions:**
1. Fix gather index computation for vectorized tricubic path
2. Ensure OOB warning global flag resets correctly
3. Validate numerical equivalence with scalar reference

**Artifacts Expected:**
- Passing tricubic vectorization tests (2 tests)
- Vectorization documentation update

---

### C14: Mixed Units (1 failure)

**Fix Plan:** [UNIT-CONV-001] (in_planning)
**Owner:** ralph
**Priority:** P3.2 (Medium — narrow scope)

**Reproduction:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_015.py::test_mixed_units_comprehensive
```

**Blocker:** None
**Dependencies:** None

**Exit Criteria:**
- Mixed-unit test passes with correct conversion factors
- ADR-01 hybrid unit system edge case documented
- Unit conversion helpers validate boundary cases

**Spec Reference:** arch.md ADR-01 (Hybrid Unit System)

**Next Actions:**
1. Identify specific unit conversion edge case causing failure
2. Fix conversion formula or boundary handling
3. Add unit test for edge case to prevent regression

**Artifacts Expected:**
- Passing mixed units test
- Unit conversion documentation update

---

### C15: Mosaic Determinism (1 failure)

**Fix Plan:** [DETERMINISM-001] (in_progress)
**Owner:** ralph
**Priority:** P1.1 (High — same cluster as C2)

**Reproduction:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_024.py::test_mosaic_rotation_umat_determinism
```

**Blocker:** [DTYPE-NEUTRAL-001] status uncertain (same as C2)
**Dependencies:** Shared with C2 determinism work

**Exit Criteria:**
- Mosaic rotation matrices deterministic for same seed
- umat → misset roundtrip preserves values
- Test passes with bitwise equality

**Spec Reference:** spec-a-core.md §5.3 (RNG determinism)

**Note:** Other AT-024 tests now passing per Phase H; this is last remaining failure

**Next Actions:**
1. Same as C2 — verify blocker status and resume determinism work
2. Fix mosaic rotation matrix generation for determinism
3. Validate umat calculation preserves seed determinism

**Artifacts Expected:**
- Passing AT-024 mosaic determinism test
- Documentation update for mosaic RNG contract

---

### C16: Gradient Flow (1 failure)

**Fix Plan:** [GRADIENT-FLOW-001] (in_planning)
**Owner:** ralph
**Priority:** P1.6 (High — differentiability requirement)

**Reproduction:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_gradients.py::test_gradient_flow_simulation
```

**Blocker:** None
**Dependencies:** None

**Exit Criteria:**
- End-to-end gradient flow test passes
- All differentiable parameters preserve computation graph
- No `.item()` or `torch.linspace` violations in gradient path

**Spec Reference:** arch.md §15 / ADR-08 (Differentiability Guidelines)

**Next Actions:**
1. Isolate gradient break point using systematic tracing
2. Fix differentiability regression (likely `.item()` or similar)
3. Add gradient flow regression test to prevent future breaks

**Artifacts Expected:**
- Passing gradient flow test
- Differentiability documentation update

---

### C18: Triclinic C Parity (1 failure)

**Fix Plan:** [TRICLINIC-PARITY-001] (in_planning)
**Owner:** ralph
**Priority:** P1.7 (High — parity requirement)

**Reproduction:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_026.py::test_triclinic_absolute_peak_position_vs_c
```

**Blocker:** None
**Dependencies:** None

**Exit Criteria:**
- AT-PARALLEL-026 parity threshold met (correlation ≥0.999)
- Triclinic cell tensor calculation matches C-code
- Misset rotation application preserves metric duality

**Spec Reference:** spec-a-parallel.md (C↔PyTorch parity requirements)

**Next Actions:**
1. Generate parallel trace for triclinic case (C vs PyTorch)
2. Identify first divergence point in cell tensor or misset rotation
3. Fix triclinic-specific logic to match C-code

**Artifacts Expected:**
- Passing AT-PARALLEL-026 test
- Triclinic parity documentation

---

## Blocker Resolution Strategy

### [DTYPE-NEUTRAL-001] Status Verification

**Affected Clusters:** C2, C15 (Determinism)

**Current Uncertainty:**
- Phase F documented [DTYPE-NEUTRAL-001] as blocker for [DETERMINISM-001]
- Phase H shows major determinism improvement (6→2 failures)
- fix_plan.md lists [DTYPE-NEUTRAL-001] as "done" (Attempt #4, 20260116)

**Resolution Actions:**
1. Verify fix_plan.md [DTYPE-NEUTRAL-001] completion status
2. If complete: unblock [DETERMINISM-001] and resume work on C2/C15
3. If incomplete: document remaining dtype work and update blocker chain

**Gating Test:**
```bash
# Verify dtype neutrality for determinism tests
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py --tb=short
```

Expected: No dtype-related crashes; failures should be RNG-specific only

---

## Artifact Expectations

All remediation work MUST produce:

1. **Passing pytest output** — cite exact command and runtime
2. **Code changes** — list files modified with line ranges
3. **Documentation updates** — spec/arch/testing strategy as appropriate
4. **Parity validation** — C↔PyTorch correlation where applicable
5. **fix_plan.md Attempt entry** — with metrics and artifact paths

---

## Cross-References

- **Phase I triage:** reports/2026-01-test-suite-triage/phase_i/20251011T042127Z/docs/triage_summary.md
- **Fix plan ledger:** docs/fix_plan.md
- **Testing strategy:** docs/development/testing_strategy.md
- **Parity matrix:** docs/development/testing_strategy.md §2.5 (Parallel Validation Matrix)

---

**Tracker Status:** Phase J1 COMPLETE — ready for execution sequence definition (J2)
