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
| A3 | Quantify plateau fragmentation | [ ] | Use existing notebook/script (`reports/2025-09-30-AT-012-peakmatch/peak_detection_summary.json` as template) to compute unique value counts in 20×20 ROI (C vs PyTorch) and save histogram PNGs + CSV. |
| A4 | Update fix_plan attempt log | [X] | Attempt #8 appended to `docs/fix_plan.md` with artifact links; status remains `in_progress` pending plateau fix. |

### Phase B — Numerical Divergence Analysis
Goal: Localize the divergence causing plateau fragmentation under float32.
Prerqs: Phase A artifacts available.
Exit Criteria: Documented first divergence (function + tensor) with side-by-side trace/computation notes stored under `reports/2025-10-AT012-regression/divergence.md`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Generate paired C & PyTorch traces | [X] | `reports/2025-10-AT012-regression/PHASE_B1_REPORT.md` + `traces/` directory capture side-by-side logs for the failing pixel (commit f2dddb8). |
| B2 | Analyze accumulation order | [X] | `reports/2025-10-AT012-regression/accumulation_order_analysis.md` documents the multi-stage vs single-stage reduction gap and quantifies 7.68× plateau fragmentation. |
| B3 | Evaluate peak detection sensitivity | [ ] | Run the listed experiments (single-stage reduction prototype, compensated summation, float64 intermediate) and record outcomes in `reports/2025-10-AT012-regression/phase_b3_experiments.md`. Ensure the diagnostics script actually toggles dtype — `scripts/validate_single_stage_reduction.py` currently ignores its `dtype` parameter, so adjust the harness before trusting results. |

### Phase C — Mitigation Selection & Implementation
Goal: Implement the least invasive change that restores plateau stability while preserving performance goals.
Prerqs: Phase B identifies candidate mitigation with supporting data.
Exit Criteria: Candidate fix implemented with targeted tests/benchmarks captured; supervisor sign-off recorded in fix_plan attempt.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Choose mitigation strategy | [ ] | Prefer physics-path fixes first: prototype a single-stage accumulation that flattens `(sources × phi × mosaic × oversample²)` and performs one `torch.sum`, mirroring C's sequential `I += term`. Fall back to compensated summation or matcher tweaks only if single-stage refactor fails parity/perf requirements. Document the trade-off analysis (spec alignment, expected perf impact). |
| C2 | Implement under debug prompt | [ ] | Apply the selected change in simulator/test suite under `prompts/debug.md`. If using single-stage reduction, guard against device/dtype drift and keep vectorization (no Python loops). Maintain Core Rules (differentiability, batching). |
| C3 | Validate physics + regression tests | [ ] | Rerun `pytest tests/test_at_parallel_012.py -vv` plus parity harness (`NB_RUN_PARALLEL=1 NB_C_BIN=... pytest tests/test_parity_matrix.py -k AT-PARALLEL-012`). Archive logs under reports directory. |
| C4 | Benchmark impact | [ ] | Record timing vs main branch using `scripts/benchmarks/benchmark_detailed.py --sizes 256 --dtype float32`. Note Δ% to ensure we do not regress PERF-PYTORCH-004 targets. |

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
