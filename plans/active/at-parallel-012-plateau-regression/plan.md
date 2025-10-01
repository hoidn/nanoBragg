# Plan: AT-PARALLEL-012 Plateau Regression Recovery

**Status:** Active (supervisor-created)
**Priority:** High — acceptance test currently diluted; spec requires ≥95% peaks within 0.5 px under default float32
**Related fix_plan item:** `[AT-PARALLEL-012-PEAKMATCH]` in docs/fix_plan.md
**Created:** 2025-10-07 by galph

## Context
- Initiative: DTYPE-DEFAULT-001 + AT-PARALLEL-012 parity
- Phase Goal: Restore spec-faithful peak-matching (≥95% of the top 50 peaks within 0.5 px) using native float32 physics without masking via dtype overrides or loosened tolerances.
- Dependencies: `specs/spec-a-parallel.md` §AT-012, `docs/architecture/pytorch_design.md` §4.2, archived plan `plans/archive/at-parallel-012-peakmatch/plan.md`, DTYPE plan Phase C tasks (reports/DTYPE-DEFAULT-001/...), golden comparison tooling under `tests/test_at_parallel_012.py`.

## Phase Overview
- **Phase A — Contract Reinstatement & Evidence Capture:** Revert temporary test loosening locally, reproduce the failure, and collect authoritative artifacts (images, peak tables, value histograms).
- **Phase B — Numerical Divergence Analysis:** Trace how PyTorch float32 accumulation diverges from C float32 (plateau fragmentation, peak offsets) and identify first differing operation.
- **Phase C — Mitigation Selection & Implementation:** Choose a corrective strategy (e.g., deterministic reduction order, compensated summation, peak post-processing) and implement it under `prompts/debug.md` with validation.
- **Phase D — Test & Documentation Closure:** Restore spec assertions (0.5 px, ≥95% of 50), remove dtype overrides, update docs/fix_plan.md and dtype plan checkpoints, archive artifacts.

---

### Phase A — Contract Reinstatement & Evidence Capture
Goal: Demonstrate the current regression under the proper spec contract and store reproducible evidence.
Prerqs: None (start immediately).
Exit Criteria: Commit-independent report under `reports/2025-10-AT012-regression/` containing pytest logs, peak tables, and plateau histograms with spec thresholds restored.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Restore local test expectations | [X] | Commit 1435c8e reinstated spec assertions (0.5 px, 95% of 50) and dropped the temporary float64 override. |
| A2 | Run targeted pytest and capture logs | [X] | `KMP_DUPLICATE_LIB_OK=TRUE pytest … -vv` output recorded at `reports/2025-10-AT012-regression/simple_cubic_baseline.log`; summary JSON stored alongside. |
| A3 | Quantify plateau fragmentation | [X] | Completed via `scripts/analyze_at012_plateau.py`. Results: PyTorch float32 shows 4.91× fragmentation (324 vs 66 unique values in C), float64 shows 4.56× fragmentation. Artifacts under `reports/2025-10-AT012-regression/` (CSV, histograms, summary). |
| A4 | Update fix_plan attempt log | [X] | Attempt #8 appended to `docs/fix_plan.md` with artifact links; status remains `in_progress` pending plateau fix. |

### Phase B — Numerical Divergence Analysis
Goal: Localize the divergence causing plateau fragmentation under float32.
Prerqs: Phase A artifacts available.
Exit Criteria: Documented first divergence (function + tensor) with side-by-side trace/computation notes stored under `reports/2025-10-AT012-regression/divergence.md`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Generate paired C & PyTorch traces | [X] | `reports/2025-10-AT012-regression/PHASE_B1_REPORT.md` + `traces/` directory capture side-by-side logs for the failing pixel (commit f2dddb8). |
| B2 | Analyze accumulation order | [X] | `reports/2025-10-AT012-regression/accumulation_order_analysis.md` documents the multi-stage vs single-stage reduction gap and quantifies 7.68× plateau fragmentation. |
| B3 | Evaluate peak detection sensitivity | [X] | Fixed `scripts/validate_single_stage_reduction.py` to honor dtype parameter. Ran float32 vs float64 experiments; results recorded in `reports/2025-10-AT012-regression/phase_b3_experiments.md`. **Key finding:** Both dtypes show ~5× fragmentation (float32=4.91×, float64=4.56×), confirming per-pixel FP operations (not multi-stage accumulation) as root cause. Single-stage reduction will NOT fix AT-012; Phase C must pursue alternative mitigations (peak clustering, FMA tuning, or documented float64 override). |

### Phase C — Mitigation Selection & Implementation
Goal: Select and implement a mitigation that addresses the per-pixel float32 fragmentation quantified in Phase B3 while keeping physics/parity and performance targets intact.
Prerqs: Phase A/B artifacts reviewed; decision should cite `reports/2025-10-AT012-regression/phase_b3_experiments.md`.
Exit Criteria: Decision memo + implemented fix + regression artifacts archived with supervisor sign-off recorded in fix_plan attempts.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Draft mitigation decision memo | [X] | Summarize Phase B3 findings and evaluate at least three options (peak clustering in matcher, controlled rounding/quantization in simulator, documented float64 exception). Store analysis under `reports/2025-10-AT012-regression/phase_c_decision.md` with go/no-go rationale tied to spec + DTYPE plan. Commit 2025-10-01: Decision memo completed, selected Option 1 (peak clustering). |
| C2 | Implement chosen mitigation under debug prompt | [~] | Apply the selected change in the appropriate module while running inside `prompts/debug.md`. Preserve vectorization/differentiability; update tests or helper scripts as needed. Note code locations and guard conditions in the memo. **Status:** Partial - tolerance-based detection + COM clustering implemented, achieves 43/50 (86%) vs 48/50 (95%) requirement. Systematic ~1px offsets persist despite perfect correlation. |
| C3 | Revalidate plateau + acceptance tests | [ ] | Run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_simple_cubic_correlation -vv` and `NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest tests/test_parity_matrix.py -k AT-PARALLEL-012`. Re-run `scripts/analyze_at012_plateau.py` to capture updated plateau histograms; ensure ROI unique-count ratio ≤1.5× C baseline. Archive outputs under `reports/2025-10-AT012-regression/phase_c_validation/`. **Blocked:** C2 incomplete. |
| C4 | Benchmark impact | [ ] | Re-run `scripts/benchmarks/benchmark_detailed.py --sizes 256 --device cpu --dtype float32 --iterations 3` (and CUDA if available) to confirm mitigation does not worsen PERF-PYTORCH-004 targets. Note deltas vs prior baseline in the memo. **Blocked:** C2 incomplete. |

### Phase D — Test & Documentation Closure
Goal: Reinstate canonical assertions and complete documentation/plan closures.
Prerqs: Phase C fix validated.
Exit Criteria: Spec-compliant tests merged, dtype overrides removed, plans archived.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Restore test assertions | [ ] | Revert tolerance loosening and dtype overrides in `tests/test_at_parallel_012.py`; ensure final diff matches spec (0.5 px, ≥95% of 50, default dtype). |
| D2 | Synchronize plans | [ ] | Update docs/fix_plan.md (Attempt summary + closure), DTYPE plan Phase C0 (drop float64 override) and Phase C1 artifact checklist, then archive this plan to `plans/archive/`. |
| D3 | Update documentation | [ ] | If mitigation alters behavior, update `docs/architecture/pytorch_design.md` and `docs/development/testing_strategy.md` with new plateau-handling rationale. |

## Notes & Guardrails
- All experimentation must preserve vectorization and differentiability; do not introduce Python loops or `.detach()`.
- Do **not** accept solutions that merely relax tests or run in float64 by default. Spec contract must hold for native float32 physics.
- Coordinate with DTYPE plan to ensure captured artifacts feed Phase C validation (reports/DTYPE-DEFAULT-001/... directories).
- Respect Protected Assets Rule when touching docs or reports referenced in `docs/index.md`.
