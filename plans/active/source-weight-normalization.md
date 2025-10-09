## Context
- Initiative: SOURCE-WEIGHT-001 — restore parity for weighted source runs so PyTorch matches the nanoBragg C semantics and long-term performance work can resume.
- Phase Goal: Align the PyTorch simulator with the spec requirement that source weights are **read but ignored**, guaranteeing equal weighting regardless of user-provided values while keeping trace metadata available for future extensions.
- Dependencies:
  - `specs/spec-a-core.md` §4 (Sources, Divergence & Dispersion) — authoritative statement that the weight column "is read but ignored".
  - `docs/architecture/pytorch_design.md` §1.1 & §2.3 — current description of the vectorised source pipeline.
  - `docs/development/c_to_pytorch_config_map.md` (Beam parameters table) — mapping between CLI flags and BeamConfig fields.
  - `docs/development/testing_strategy.md` §§1.4–2 — device/dtype discipline and authoritative commands for targeted pytest runs.
  - `golden_suite_generator/nanoBragg.c:2570-2720` — C reference showing weights copied from file but excluded from `steps` and accumulation.
  - Existing evidence bundles under `reports/2025-11-source-weights/phase_a/` (bias reproduction) and `phase_b/20251009T083515Z/` (spec-aligned gap confirmation).
- Status Snapshot (2025-12-24): Phases A–C complete — equal-weight accumulation merged (commits 47822ce, 321c91e, dffea55) and regression tests enforce the spec rule. Phase D evidence capture is outstanding: we still need fresh parity artifacts (pytest + CLI metrics) before `[VECTOR-GAPS-002]` and PERF profiling can resume.

### Phase A — Evidence Baseline (Complete)
Goal: Preserve reproducible proof of the weighted-source divergence.
Prereqs: Editable install; fixture committed.
Exit Criteria: CLI runs + metrics captured under `phase_a/20251009T071821Z/`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Build weighted source fixture | [D] | `reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt` (weights 1.0, 0.2). |
| A2 | Capture PyTorch bias | [D] | PyTorch CLI output + metrics stored under `phase_a/.../py/`; total intensity 1.52e5. |
| A3 | Capture C reference | [D] | C CLI output + metrics stored under `phase_a/.../c/`; total intensity 4.63e2. |

### Phase B — Spec & Gap Confirmation (Active)
Goal: Replace the outdated "sum of weights" design with a spec-aligned analysis that documents why PyTorch must ignore weights during accumulation.
Prereqs: Phase A artifacts reviewed; repository clean.
Exit Criteria: `reports/2025-11-source-weights/phase_b/<STAMP>/` contains spec quotations, PyTorch call-chain notes, CLI rerun metrics, commands.txt, env.json, and pytest collection proof.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Document spec & C behavior | [D] | Author `spec_alignment.md` quoting `specs/spec-a-core.md:150-190` and `golden_suite_generator/nanoBragg.c:2570-2720`; explain that C counts sources and never applies weights during accumulation. **Done:** 20251009T083515Z |
| B2 | Trace PyTorch weighting path | [D] | Produce `pytorch_accumulation.md` highlighting `src/nanobrag_torch/simulator.py:400-420` (weights_broadcast multiply) and `:850-1125` (steps normalization). Include a short call-chain table referencing `_compute_physics_for_position` inputs/outputs. **Done:** 20251009T083515Z |
| B3 | Reproduce current parity delta | [D] | Repeat the two CLI runs from Phase A plus `pytest --collect-only -q` (authoritative command). Store metrics in `analysis.md` and JSON under `phase_b/<STAMP>/`, confirming correlation ~0.916 and sum_ratio ≈0.728 after commit `321c91e`. **Done:** 20251009T083515Z - NOTE: Observed 52× divergence (not 0.728×) due to oversample auto-selection mismatch (C:1×, Py:2×) plus weighted accumulation still present at simulator.py:413,416. |

### Phase C — Implementation Adjustments (Pending)
Goal: Update the simulator so multi-source runs ignore weights exactly like the C code while retaining metadata for traces and future features.
Prereqs: Phase B artifacts approved; code pointers agreed.
Exit Criteria: PyTorch accumulation path ignores weights; regression tests cover both weighted and unweighted cases; vectorization/dtype guardrails respected.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Remove weighted accumulation | [D] | Implemented in `src/nanobrag_torch/simulator.py` (commits 321c91e/dffea55); equal-weight sum enforced with spec citation. |
| C2 | Simplify source cache handling | [D] | Metadata-only handling in `Simulator.__init__` retained; comments updated in `config.py` (commit dffea55). |
| C3 | Extend regression tests | [D] | `tests/test_cli_scaling.py::TestSourceWeights` expanded with TC-A/TC-B/TC-D coverage (CPU focus, CUDA optional). |

### Phase D — Validation & Documentation
Goal: Prove parity with the C reference on CPU (and CUDA when available) using the authoritative weighted-source fixture so the 4096² profiler regain trust, then refresh documentation/fix_plan entries.
Prereqs: Phase C merged locally; lint/tests green.
Exit Criteria: Phase D bundle contains parity metrics, pytest logs, updated docs, and fix_plan attempt recorded.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Run targeted parity test | [ ] | `NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeights::test_weighted_source_matches_c -v`. Archive log + collect-only proof under `phase_d/<STAMP>/pytest/`; this result gates `[VECTOR-GAPS-002]` Phase B1. |
| D2 | Capture CLI metrics | [ ] | Re-run C & PyTorch commands (force `-oversample 1`), store outputs in `phase_d/<STAMP>/metrics.json` + `summary.md`; confirm correlation ≥0.999 and |sum_ratio−1| ≤ 1e-3 before lifting the profiler block. |
| D3 | Update documentation | [ ] | Amend `docs/architecture/pytorch_design.md` (Sources subsection) and, if needed, `docs/development/testing_strategy.md` to note weights are ignored. Log Attempt in `docs/fix_plan.md` referencing artifact paths. |

### Phase E — Closure & Handoffs
Goal: Unlock dependent initiatives and archive the plan once parity is stable.
Prereqs: Phase D complete.
Exit Criteria: Fix-plan entry marked done or deferred with rationale; dependent initiatives notified.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Notify dependencies | [ ] | Update `[VECTOR-GAPS-002]` and `[PERF-PYTORCH-004]` attempts with sum_ratio/correlation results so profiling can resume. |
| E2 | Archive artifacts & plan | [ ] | Move stabilized bundles to `reports/archive/source-weights/<STAMP>/`, update plan status snapshot, and migrate this file to `plans/archive/` when complete. |
