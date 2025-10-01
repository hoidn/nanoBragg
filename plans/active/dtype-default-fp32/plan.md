# Plan: DTYPE-DEFAULT-001 Float32 Default Rollout

**Status:** Active (supervisor-created)
**Priority:** High – aligns runtime defaults with long-term performance goals
**Related fix_plan item:** `[DTYPE-DEFAULT-001]` Migrate simulator defaults to float32 — see docs/fix_plan.md
**Created:** 2025-10-04 by galph

## Context
- Initiative: DTYPE-DEFAULT-001 (ensure PyTorch implementation uses float32 by default)
- Phase Goal: Shift simulator/config defaults from float64 to float32 without regressing parity, gradients, or documentation contracts.
- Dependencies: `arch.md` (currently claims float64 default), `docs/development/pytorch_runtime_checklist.md`, `docs/architecture/pytorch_design.md` §2.4, acceptance tests (`tests/test_at_*`), perf harness under `reports/benchmarks/`.

## Phase Overview
- **Phase A — Inventory & Spec Harmonisation:** Document every location assuming float64 defaults and align ADR/spec narrative before code edits.
- **Phase B — Implementation Update:** Change default dtype plumbing (configs, simulator constants, tensor factories) while preserving caller overrides.
- **Phase C — Validation & Regression Sweep:** Prove parity, gradients, and performance hold (CPU/GPU) with float32 defaults.
- **Phase D — Documentation & Rollout:** Update architecture docs, runtime checklist, and fix_plan with new expectations; archive plan.

---

### Phase A — Inventory & Spec Harmonisation
Goal: Enumerate all float64 default assumptions and settle doc parity (arch vs spec vs long-term goal).
Prerqs: None (can start immediately).
Exit Criteria: Inventory markdown summarising impacted code paths + proposed doc updates, supervisor sign-off recorded in fix_plan attempt log.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Catalogue float64 defaults in code | [X] | `rg "float64" src/nanobrag_torch -n`; results recorded 2025-09-30 in `reports/DTYPE-DEFAULT-001/inventory.md`. |
| A2 | Reconcile spec/architecture statements | [X] | Proposed wording adjustments captured in `reports/DTYPE-DEFAULT-001/proposed_doc_changes.md`; awaits documentation update in Phase D. |
| A3 | Identify gradient-critical paths | [X] | Inventory lists gradcheck-only float64 requirements (Crystal/Detector tensors, tests) under "Gradient-Critical Paths" section. |

### Phase B — Implementation Update
Goal: Switch runtime defaults to float32 while allowing tests to request float64 explicitly.
Prerqs: Phase A inventory approved.
Exit Criteria: All constructors default to float32; float64 usage limited to gradcheck/test overrides; code passes lint/unit style checks.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Update config and simulator defaults | [X] | Defaults flipped to float32 across CLI, Crystal/Detector/Simulator, and HKL loaders (commit 8c2ceb4; see `reports/DTYPE-DEFAULT-001/phase_b_summary.md`). |
| B2 | Adjust constant initialisation | [X] | Beam/polarisation tensors and HKL arrays now use caller dtype; smoke test `python -m nanobrag_torch --help` logged on 2025-09-30. |
| B3 | Audit helper functions | [P] | Auto-selection helpers updated; remaining float64 literals in `io/source.py` (`read_sourcefile` defaults), `utils/noise.py` (Poisson buffers), and `utils/c_random.py` (rotation matrices) must accept caller dtype/device. Capture before/after snippets in `reports/DTYPE-DEFAULT-001/phase_b3_audit.md` before flipping to float32. |

### Phase C — Validation & Regression Sweep
Goal: Demonstrate float32 defaults maintain parity, gradients, and performance targets.
Prerqs: Phase B merged to working branch.
Exit Criteria: Test matrix recorded in fix_plan; benchmark delta ≤~5 % vs prior float64 baseline; gradients validated.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C0 | Remove temporary float64 overrides in AT-012 tests | [X] | Commit 1435c8e restored default float32 assertions (0.5 px, 95% of 50). Simple_cubic now fails 43/50; artifacts logged under `reports/2025-10-AT012-regression/`. |
| C1 | Run Tier-1 parity suite on CPU/GPU | [ ] | Blocked until AT-012 plateau fix lands. Reuse artifacts from `reports/2025-10-AT012-regression/` for baseline, then capture paired float64 vs float32 runs under `reports/DTYPE-DEFAULT-001/` before rerunning the full Tier-1 matrix (`NB_RUN_PARALLEL=1 … tests/test_at_parallel_012.py -vv`). |
| C2 | Execute gradcheck focus tests | [ ] | `pytest tests/test_crystal_geometry.py::TestMetricDuality::test_metric_duality_grad` et al with explicit `dtype=torch.float64` to verify opt-in precision still works post-default switch. |
| C3 | Benchmark warm/cold performance | [ ] | `python scripts/benchmarks/benchmark_detailed.py --sizes 256,512 --device cuda --dtype float32 --iterations 3`; compare to float64 baselines and store in `reports/DTYPE-DEFAULT-001/benchmarks/`. |

### Phase D — Documentation & Rollout
Goal: Align documentation/tooling and close the initiative.
Prerqs: Validation artifacts reviewed.
Exit Criteria: Docs updated, plan archived, fix_plan attempt recorded with links.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Update docs & checklists | [ ] | Revise `arch.md`, `docs/development/pytorch_runtime_checklist.md`, and any README references to note float32 default + float64 gradcheck usage. |
| D2 | Communicate change downstream | [ ] | Ensure prompts (e.g., `prompts/debug.md`) remind engineers to request float64 explicitly for gradcheck; update CLAUDE.md if necessary. |
| D3 | Archive plan & log completion | [ ] | Move this plan to `plans/archive/dtype-default-fp32/` and update `[DTYPE-DEFAULT-001]` attempts history with validation artifacts. |

---

## Notes & Guardrails
- Preserve ability to run float64 paths for gradcheck/tests; do not remove dtype arguments.
- Do **not** mask Tier-1 regressions by forcing tests to float64; default float32 must pass before plan closure.
- Re-run performance comparisons vs C after defaults change to quantify improvement.
- Ensure Protected Assets compliance when touching docs referenced in `docs/index.md`.

## Phase Status Snapshot (2025-09-30 update)
- Phase A: [X]
- Phase B: [P]
- Phase C: [ ]
- Phase D: [ ]
