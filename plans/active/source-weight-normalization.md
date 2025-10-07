## Context
- Initiative: Simulator normalization correctness — align weighted multi-source runs with physical fluence.
- Phase Goal: Ensure per-source weighting matches the nanoBragg C semantics so total fluence reflects `sum(source_weights)` instead of `n_sources`.
- Dependencies: specs/spec-a-core.md §5 (Source intensity), docs/architecture/pytorch_design.md §2.3 (Source handling), docs/development/c_to_pytorch_config_map.md §Beam/Source, `nanoBragg.c` lines 2480-2595 (source weighting), `scripts/validation/compare_scaling_traces.py` outputs for weighted sources.
- Current gap snapshot (2025-11-17): `Simulator.run` (src/nanobrag_torch/simulator.py:837-925) divides accumulated intensity by `n_sources` even when custom `source_weights` are supplied, leading to biased fluence whenever weights ≠ 1.0.

## Phase A — Evidence & Reproduction
Goal: Capture failing behaviour and establish contractual expectations.
Prereqs: Editable install, access to sample source file, baseline command reference.
Exit Criteria: Reproduction logs showing discrepancy between PyTorch and C/normative expectation.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Build weighted source fixture | [ ] | Create a minimal sourcefile (e.g., two points with weights 1.0 and 0.2) under `reports/2025-11-source-weights/fixtures/weighted_source.json`. |
| A2 | Reproduce bias in PyTorch | [ ] | Run `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python scripts/run_simulation.py --sourcefile <fixture>` (or equivalent CLI command) and log the summed intensity showing incorrect normalization. |
| A3 | Capture C baseline | [ ] | Execute the same configuration via nanoBragg C using `NB_C_BIN` and record the resulting fluence for comparison. |

## Phase B — Design & Strategy
Goal: Decide how to adjust normalization without breaking existing behaviours.
Prereqs: Evidence captured, understanding of current scaling chain.
Exit Criteria: Written strategy covering code changes, edge cases, and tests.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Trace normalization math | [ ] | Document the current multiplication/division path (steps, fluence, capture_fraction) and identify where weight sum should enter. Save notes to `reports/.../phase_b/normalization_flow.md`. |
| B2 | Define update approach | [ ] | Decide between scaling by `source_weights.sum()` or pre-normalizing weights; handle default (all ones) efficiently. |
| B3 | Plan regression coverage | [ ] | Specify pytest additions (e.g., new case in `tests/test_cli_scaling.py`) and acceptable tolerances. |

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
