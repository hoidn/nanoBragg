## Context
- Initiative: DETERMINISM-001 — restore PyTorch RNG determinism across mosaic and misset sampling so Acceptance Tests AT-PARALLEL-013 and AT-PARALLEL-024 pass and `[TEST-SUITE-TRIAGE-001]` ladder can progress.
- Plan Goal: Produce a phased remediation blueprint covering evidence capture, seed callchain tracing, fix scoping, and validation for PyTorch determinism regressions.
- Dependencies:
  - `specs/spec-a-core.md` §5.3 & §15 — normative seed contracts (noise, mosaic, misset) and determinism requirements.
  - `specs/spec-a-parallel.md` AT-PARALLEL-013/024 — acceptance criteria for deterministic runs and random misset parity.
  - `docs/development/testing_strategy.md` §§1.4–2 — authoritative pytest commands, device/dtype guardrails.
  - `docs/development/pytorch_runtime_checklist.md` — runtime guardrails for vectorization/device neutrality.
  - `plans/active/test-suite-triage.md` — triage priorities and cluster mappings (C2 determinism failures).
  - `reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/` — Attempt #6 triage summary & pending actions.
  - `src/nanobrag_torch/models/crystal.py`, `src/nanobrag_torch/utils/c_random.py`, and `src/nanobrag_torch/simulator.py` — seed handling surfaces.
- Artifact Policy: All new work lands under `reports/2026-01-test-suite-triage/phase_d/<STAMP>/determinism/` with subfolders per phase (`phase_a`, `phase_b`, …). Each attempt captures `commands.txt`, `env.json`, raw logs, and `summary.md`; diffs/traces live under `trace/` or `callchain/` as appropriate.

### Status Snapshot (2026-01-16)
- Dependency cleared — `[DTYPE-NEUTRAL-001]` Attempt #3 removed the detector dtype crash, so Phase A reproduction can resume.
- Next step: capture fresh AT-PARALLEL-013/024 logs (expect TorchDynamo CUDA device failures) and update fix_plan Attempt history before launching Phase B callchain tracing.

### Phase A — Reproduce & Baseline Seed Drift
Goal: Capture authoritative reproductions of the determinism failures, plus working controls, so later fixes have comparable baselines.
Prereqs: Editable install (`pip install -e .`), clean workspace, GPU optional but document availability.
Exit Criteria: Failure logs for AT-PARALLEL-013/024 with environment snapshot, plus control run showing API baseline behaviour (if any) stored under `phase_a/<STAMP>/`.

| ID | Task Description | State | How/Why & Guidance (including API / document / artifact / source file references) |
| --- | --- | --- | --- |
| A1 | Collect environment + seed baseline | [ ] | Run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` and log torch/numpy/OMP seeds in `env.json`. Cite `docs/development/testing_strategy.md` §1.4 for device guardrails. |
| A2 | Reproduce AT-PARALLEL-013 failures | [ ] | Command: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py --maxfail=0 --durations=10`. Capture full log → `phase_a/<STAMP>/at_parallel_013/pytest.log`. Include `commands.txt`. |
| A3 | Reproduce AT-PARALLEL-024 failures | [ ] | Command: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_024.py --maxfail=0 --durations=10`. Store logs under `phase_a/<STAMP>/at_parallel_024/`. Record failing assertions. |
| A4 | Capture control run (if any) | [ ] | If a direct API script (e.g., `debug_misset_seed.py`) exists, run it to confirm seed reproducibility expectations; otherwise note absence. Summarise findings in `phase_a/<STAMP>/summary.md`. |

### Phase B — Seed Callchain & Trace Mapping
Goal: Identify where seed propagation diverges between CLI/API and within simulator components using `prompts/callchain.md` SOP.
Prereqs: Phase A artifacts (logs + env). Ensure deterministic reproduction commands documented.
Exit Criteria: Callchain bundle pinpointing first divergent taps for mosaic/misset seed usage in PyTorch, with matching documentation of expected C behaviour.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Define analysis question & scope hints | [ ] | Prepare `analysis.md` with `<analysis_question>` (e.g., "Why do AT-PARALLEL-024 misset seeds drift between runs?") referencing triage summary §C2. Set `initiative_id=determinism-b1`, `scope_hints` = ["Crystal.misset_seed", "Simulator.seed_all", "torch.manual_seed"]. |
| B2 | Execute callchain tracing for Crystal/Simulator seed flow | [ ] | Follow `prompts/callchain.md`; capture `callchain/static.md`, `callgraph/dynamic.txt` (optional), and `trace/tap_points.md` under `phase_b/<STAMP>/callchain/`. Focus on config parsing → `CrystalConfig` → `Crystal` random misset logic. |
| B3 | Compare against C reference | [ ] | Document expected seed handling from `nanoBragg.c` sections (noise/misset seeds). If needed, add TODO to instrument `golden_suite_generator/nanoBragg` seed logs. Summarise differences in `phase_b/<STAMP>/summary.md`. |
| B4 | Update docs/fix_plan ledger | [ ] | Append Attempt entry for Phase B in `[DETERMINISM-001]` (docs/fix_plan.md) noting discovered divergence + artifact path. |

### Phase C — Remediation Blueprint & Test Strategy
Goal: Synthesize the fix approach without code changes; enumerate touchpoints, acceptance tests, and documentation updates required.
Prereqs: Phase B tap findings that explain seed drift.
Exit Criteria: Remediation plan and regression coverage doc ready for implementation handoff.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Draft remediation plan | [ ] | Author `phase_c/<STAMP>/remediation_plan.md` covering: config seeding contract, required changes to `parse_and_validate_args`, `Simulator` seed hookup, and interactions with mosaic/random misset. Cite spec sections and `c_random.py` semantics. |
| C2 | Define regression coverage | [ ] | Produce `phase_c/<STAMP>/tests.md` listing pytest selectors (AT-PARALLEL-013/024, targeted unit tests for `Crystal` seeding, potential new deterministic smoke). Include CPU/GPU expectations per runtime checklist. |
| C3 | Document doc/test touchpoints | [ ] | Add `phase_c/<STAMP>/docs_updates.md` noting spec/README adjustments if behaviour changes and update requirements in `docs/development/testing_strategy.md` if new commands introduced. |
| C4 | Refresh fix_plan + input blueprint | [ ] | Update `[DETERMINISM-001]` entry with Phase C status and upcoming implementation tasks; prepare supervisor input template (without dispatching fix). |

### Phase D — Validation Gate (post-fix, pending implementation)
Goal: Define validation checklist to execute immediately after code changes land.
Prereqs: Implementation attempt completes per Phase C blueprint.
Exit Criteria: Documented validation script/test suite ensuring determinism hold on CPU (and CUDA when available) with artifact expectations.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Author validation checklist | [ ] | Create `phase_d/checklist.md` outlining targeted pytest selectors, required `nb-compare` or trace captures, and thresholds (bitwise equality for same-seed runs, correlation ≤0.7 for differing seeds). |
| D2 | Define documentation updates post-validation | [ ] | Note updates to `README_PYTORCH.md` or user guides demonstrating deterministic workflows. |

### Exit Criteria (Overall Plan)
- Phases A–C completed with `[D]` statuses and artifacts stored under timestamped subdirectories in `reports/2026-01-test-suite-triage/phase_d/`.
- `[DETERMINISM-001]` in `docs/fix_plan.md` references this plan and lists latest completed phase + artifact timestamp.
- Phase D remains templated until code changes land; checklist ready for execution.

### References
- `tests/test_at_parallel_013.py`
- `tests/test_at_parallel_024.py`
- `src/nanobrag_torch/models/crystal.py`
- `src/nanobrag_torch/simulator.py`
- `src/nanobrag_torch/utils/c_random.py`
- `prompts/callchain.md`
- `reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/triage_summary.md`
