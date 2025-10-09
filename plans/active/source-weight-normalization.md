## Context
- Initiative: Simulator normalization correctness — align weighted multi-source runs with physical fluence.
- Phase Goal: Ensure per-source weighting matches the nanoBragg C semantics so total fluence reflects `sum(source_weights)` instead of `n_sources`.
- Dependencies: specs/spec-a-core.md §5 (Source intensity), docs/architecture/pytorch_design.md §2.3 (Source handling), docs/development/c_to_pytorch_config_map.md §Beam/Source, `nanoBragg.c` lines 2480-2595 (source weighting), `scripts/validation/compare_scaling_traces.py` outputs for weighted sources.
- Current gap snapshot (2025-11-17): `Simulator.run` (src/nanobrag_torch/simulator.py:837-925) divides accumulated intensity by `n_sources` even when custom `source_weights` are supplied, leading to biased fluence whenever weights ≠ 1.0.
- Status Snapshot (2025-12-22): Phase A evidence bundle `20251009T071821Z` confirms the 327.9× scaling error and is referenced by `[VECTOR-GAPS-002]` as the blocker for profiler correlation. Phase B design work is still outstanding; completing B1–B3 will unblock PERF-PYTORCH-004 Phase P3.0b/P3.0c and allow vectorization-gap profiling to resume.

## Phase A — Evidence & Reproduction
Goal: Capture failing behaviour and establish contractual expectations.
Prereqs: Editable install, access to sample source file, baseline command reference.
Exit Criteria: Reproduction logs showing discrepancy between PyTorch and C/normative expectation.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Build weighted source fixture | [D] | Created `reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt` with weights 1.0 and 0.2. |
| A2 | Reproduce bias in PyTorch | [D] | Captured PyTorch output showing max intensity 101.1, total 151963.1 under `phase_a/20251009T071821Z/py/`. |
| A3 | Capture C baseline | [D] | Captured C output showing max intensity 0.009, total 463.4 under `phase_a/20251009T071821Z/c/`. Ratio = 327.9× discrepancy confirmed. |

## Phase B — Design & Strategy
Goal: Decide how to adjust normalization without breaking existing behaviours.
Prereqs: Evidence captured, understanding of current scaling chain.
Exit Criteria: Written strategy covering code changes, edge cases, and tests.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Trace normalization math | [D] | DONE 2025-10-09T07:35:30Z. `reports/2025-11-source-weights/phase_b/20251009T072937Z/normalization_flow.md` — Traced simulator.py:557-1137 scaling path; identified fix location (line 868). |
| B2 | Define update approach | [D] | DONE 2025-10-09T07:35:30Z. `reports/2025-11-source-weights/phase_b/20251009T072937Z/strategy.md` — Decision: divide by sum(source_weights). No coupling with polarization (P3.0b). |
| B3 | Plan regression coverage | [D] | DONE 2025-10-09T07:35:30Z. `reports/2025-11-source-weights/phase_b/20251009T072937Z/tests.md` — 5 test cases defined (TC-A through TC-E), tolerance tiers specified (CPU/CUDA). |

## Phase C — Implementation
Goal: Implement corrected weighting with minimal churn and full docstring references.
Prereqs: Design approved; branch ready.
Exit Criteria: Code updated, tests written, artifacts captured.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Update step normalization | [ ] | Modify `Simulator.run` to divide by `source_weights.sum()` (fallback to `n_sources` when equal weights). Ensure device/dtype neutrality. |
| C2 | Adjust weighted blending | [ ] | Revisit `Simulator._accumulate_source_contribution` (if needed) so weights are consistently applied without double scaling. |
| C3 | Add regression tests | [ ] | Extend `tests/test_cli_scaling.py` (or new test file) to cover unequal source weights; assert PyTorch matches C within tolerance. |

## Phase D — Validation & Documentation
Goal: Validate across devices, update docs, and log closure.
Prereqs: Implementation complete, tests passing locally.
Exit Criteria: Evidence archived, docs updated, fix_plan closed.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Run targeted pytest | [ ] | `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeights -v` (CPU/CUDA). Store logs under `reports/.../phase_d/tests/`. |
| D2 | Refresh scaling trace | [ ] | Re-run `scripts/validation/compare_scaling_traces.py` using weighted source scenario to confirm normalization. |
| D3 | Update docs & ledger | [ ] | Amend `docs/architecture/pytorch_design.md` and `docs/development/testing_strategy.md` to document weighting behaviour, then mark fix_plan attempt completed. |
