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

### Status Snapshot (2026-01-17)
- Phase A ✅ complete (Attempts #1–#3) — determinism reproductions and environment baselines captured under `reports/2026-01-test-suite-triage/phase_d/20251011T045211Z/determinism/phase_a/`.
- Phase B ✅ complete (Attempt #5) — C-side seed contract documented at `reports/determinism-callchain/phase_b3/20251011T051737Z/`, complementing the PyTorch callchain bundle from Attempt #4.
- Phase C 🔄 pending — need to publish remediation blueprint + documentation updates (seed side-effect contract, Dynamo guard instructions) before closing `[DETERMINISM-001]`.
- Phase D remains templated for future regression checks once documentation tasks land.

### Phase A — Reproduce & Baseline Seed Drift
Goal: Capture authoritative reproductions of the determinism failures, plus working controls, so later fixes have comparable baselines.
Prereqs: Editable install (`pip install -e .`), clean workspace, GPU optional but document availability.
Exit Criteria: Failure logs for AT-PARALLEL-013/024 with environment snapshot, plus control run showing API baseline behaviour (if any) stored under `phase_a/<STAMP>/`.

| ID | Task Description | State | How/Why & Guidance (including API / document / artifact / source file references) |
| --- | --- | --- | --- |
| A1 | Collect environment + seed baseline | [D] | Attempt #3 (20260117) — `logs/collect_only.log` + `env.json` under `reports/2026-01-test-suite-triage/phase_d/20251011T045211Z/determinism/phase_a/` capture global env + seed state. |
| A2 | Reproduce AT-PARALLEL-013 failures | [D] | Attempt #3 — `pytest` selector executed; failure log stored at `reports/2026-01-test-suite-triage/phase_d/20251011T045211Z/determinism/phase_a/at_parallel_013/pytest.log`, confirming TorchDynamo CUDA probe still blocks determinism asserts. |
| A3 | Reproduce AT-PARALLEL-024 failures | [D] | Attempt #3 — `reports/2026-01-test-suite-triage/phase_d/20251011T045211Z/determinism/phase_a/at_parallel_024/pytest.log` documents RNG determinism success plus residual `mosaic_rotation_umat` dtype mismatch. |
| A4 | Capture control run (if any) | [D] | No standalone control script available; absence documented in `summary.md` for Attempt #3 (Phase A). |

### Phase B — Seed Callchain & Trace Mapping
Goal: Identify where seed propagation diverges between CLI/API and within simulator components using `prompts/callchain.md` SOP.
Prereqs: Phase A artifacts (logs + env). Ensure deterministic reproduction commands documented.
Exit Criteria: Callchain bundle pinpointing first divergent taps for mosaic/misset seed usage in PyTorch, with matching documentation of expected C behaviour.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Define analysis question & scope hints | [D] | Recorded analysis question + scope inside `reports/determinism-callchain/callchain/static.md` (20260117T) per callchain SOP; scope hints captured alongside taps for Crystal/Simulator seed flow. |
| B2 | Execute callchain tracing for Crystal/Simulator seed flow | [D] | Callchain artifacts captured under `reports/determinism-callchain/` (`callchain/static.md`, `trace/tap_points.md`, placeholder `callgraph/dynamic.txt`) highlighting missing `mosaic_seed` usage. |
| B3 | Compare against C reference | [D] | Attempt #5 (20251011T051737Z) — `reports/determinism-callchain/phase_b3/20251011T051737Z/` captures grep outputs, `c_rng_excerpt.c`, and `c_seed_flow.md` summarising `misset_seed`/`mosaic_seed` propagation and the pointer-side-effect contract. |
| B4 | Update docs/fix_plan ledger | [D] | Attempt #4 logged in `[DETERMINISM-001]` (docs/fix_plan.md) with findings + `reports/determinism-callchain/` artifacts; ready to proceed to Phase B3. |

### Phase C — Documentation & Remediation Blueprint
Goal: Codify the PyTorch-side fixes, update permanent documentation (seed contract + deterministic run instructions), and stage the close-out handoff for `[DETERMINISM-001]`.
Prereqs: Phase B artifacts (`reports/determinism-callchain/…/phase_b3/`) and Attempt #6 implementation logs confirming tests pass.
Exit Criteria: Remediation summary + doc updates published, fix_plan/input refreshed for final closure.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Author remediation summary | [ ] | Create `reports/determinism-callchain/phase_c/<STAMP>/remediation_summary.md` describing env guards (TorchDynamo disable), dtype propagation fixes, and how seeds reach `mosaic_rotation_umat`. Reference Attempt #6 artifacts. |
| C2 | Update RNG documentation | [ ] | Draft `docs_updates.md` capturing where to document the pointer-side-effect seed contract (target: `docs/architecture/c_function_reference.md` RNG section + `src/nanobrag_torch/utils/c_random.py` docstring). Log concrete edit checklist. |
| C3 | Update testing strategy | [ ] | Extend `docs/development/testing_strategy.md` §1.4/§2 with deterministic run instructions (env vars, pytest selectors, artifact expectations). Capture diff plan in `phase_c/<STAMP>/testing_strategy_notes.md`. |
| C4 | Refresh fix_plan + input blueprint | [ ] | Update `[DETERMINISM-001]` Next Actions to point at Phase C doc tasks and prepare supervisor input (Docs mode) for execution. |

### Phase D — Validation Gate (post-fix, pending implementation)
Goal: Define validation checklist to execute immediately after code changes land.
Prereqs: Implementation attempt completes per Phase C blueprint.
Exit Criteria: Documented validation script/test suite ensuring determinism hold on CPU (and CUDA when available) with artifact expectations.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Author validation checklist | [ ] | Create `phase_d/checklist.md` outlining targeted pytest selectors, required `nb-compare` or trace captures, and thresholds (bitwise equality for same-seed runs, correlation ≤0.7 for differing seeds). |
| D2 | Define documentation updates post-validation | [ ] | Note updates to `README_PYTORCH.md` or user guides demonstrating deterministic workflows. |

### Exit Criteria (Overall Plan)
- Phases A–C completed with `[D]` statuses and artifacts stored under timestamped subdirectories in `reports/2026-01-test-suite-triage/phase_d/` (Phase A) and the supervisor callchain bundle `reports/determinism-callchain/` (Phase B).
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
