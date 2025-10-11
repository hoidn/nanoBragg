## Context
- Initiative: DETERMINISM-001 — restore PyTorch RNG determinism across mosaic and misset sampling so Acceptance Tests AT-PARALLEL-013 and AT-PARALLEL-024 pass and `[TEST-SUITE-TRIAGE-001]` ladder can progress.
- Plan Goal: Produce a phased remediation blueprint covering evidence capture, seed callchain tracing, documentation integration, and validation for PyTorch determinism regressions.
- Dependencies:
  - `specs/spec-a-core.md` §5.3 & §15 — normative seed contracts (noise, mosaic, misset) and determinism requirements.
  - `specs/spec-a-parallel.md` AT-PARALLEL-013/024 — acceptance criteria for deterministic runs and random misset parity.
  - `docs/development/testing_strategy.md` §§1.4–2 — authoritative pytest commands, device/dtype guardrails.
  - `docs/development/pytorch_runtime_checklist.md` — runtime guardrails for vectorization/device neutrality.
  - `plans/active/test-suite-triage.md` — triage priorities and cluster mappings (C2 determinism failures).
  - `reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/` — Attempt #6 triage summary & pending actions.
  - `src/nanobrag_torch/models/crystal.py`, `src/nanobrag_torch/utils/c_random.py`, and `src/nanobrag_torch/simulator.py` — seed handling surfaces.
- Artifact Policy: All new work lands under `reports/2026-01-test-suite-triage/phase_d/<STAMP>/determinism/` with subfolders per phase (`phase_a`, `phase_b`, …). Each attempt captures `commands.txt`, `env.json`, raw logs, and `summary.md`; docs-only work uses `reports/determinism-callchain/<phase>/` as established in Phases B–C.

- Phase A ✅ complete (Attempts #1–#3) — determinism reproductions, environment baselines, and controls captured under `reports/2026-01-test-suite-triage/phase_d/20251011T050024Z/determinism/phase_a/`.
- Phase B ✅ complete (Attempts #4–#5) — PyTorch callchain bundle captured; C seed contract documented at `reports/determinism-callchain/phase_b3/20251011T051737Z/`.
- Phase C ✅ complete (Attempt #7) — Remediation summary, documentation checklist, and testing strategy notes published at `reports/determinism-callchain/phase_c/20251011T052920Z/`.
- Phase D underway — D1 ✅ (architecture reference updated per `reports/determinism-callchain/phase_d/20251011T054542Z/docs_integration/`); D2–D4 pending (docstrings, ADR, testing strategy integration).
- **Phase E (pending)** — Final validation + ledger closure once documentation is merged and determinism selectors re-run.

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
| C1 | Author remediation summary | [D] | ✅ Created `reports/determinism-callchain/phase_c/20251011T052920Z/remediation_summary.md` describing env guards (TorchDynamo disable), dtype propagation fixes, and how seeds reach `mosaic_rotation_umat`. |
| C2 | Update RNG documentation checklist | [D] | ✅ Drafted `docs_updates.md` capturing required edits for architecture docs, source docstrings, and README/testing strategy touchpoints. |
| C3 | Update testing strategy notes | [D] | ✅ Extended deterministic run instructions captured in `phase_c/<STAMP>/testing_strategy_notes.md`. Complete workflow documentation covering env vars, pytest selectors, validation metrics, artifact expectations, CI integration, and known limitations. |
| C4 | Refresh fix_plan + input blueprint | [D] | ✅ Updated `[DETERMINISM-001]` Next Actions in `docs/fix_plan.md` with Phase C summary and documentation checklist. Attempt #7 logged with complete Phase C artifact descriptions. |

### Phase D — Documentation Integration
Goal: Apply the Priority 1–2 edits from `docs_updates.md` so the RNG contract and determinism workflow live in permanent docs and source docstrings.
Prereqs: Phase C artifacts in hand; repo clean; Protected Assets respected.
Exit Criteria: Architecture docs, source docstrings, and testing strategy updated; edits cross-referenced in fix_plan with artifact paths under `reports/determinism-callchain/phase_d/<STAMP>/docs_integration/`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Update `docs/architecture/c_function_reference.md` RNG section | [D] | Attempt #8 → `reports/determinism-callchain/phase_d/20251011T054542Z/docs_integration/` captures the merged overview, seed domain table, pointer warning, and invocation site audit. |
| D2 | Expand `src/nanobrag_torch/utils/c_random.py` docstrings | [D] | Attempt #9 (20251011T055456Z) → `reports/determinism-callchain/phase_d/20251011T055456Z/docs_integration/` captures 88-line diff with module + function docstring enhancements. Module docstring: algorithm overview, seed contract, key functions, determinism requirements, validation refs. Function docstring: RNG consumption (3 values), C equivalent, seed state progression example. Pytest collection: 692 tests, 2.65s, no errors. |
| D3 | Enhance `arch.md` ADR-05 with pointer-side-effect note | [D] | Attempt #10 (20251011T060454Z) — Added 4-line implementation note to arch.md ADR-05 explaining C `ran1(&seed)` pointer mutation vs PyTorch `LCGRandom(seed).uniform()` state advancement equivalence; cross-referenced AT-PARALLEL-024 verification. |
| D4 | Integrate determinism workflow into `docs/development/testing_strategy.md` | [D] | Attempt #10 (20251011T060454Z) — Integrated 116-line §2.7 into testing_strategy.md documenting env guards, validation metrics, reproduction commands, artifact expectations, known limitations. |
| D5 | Optional: add deterministic workflow vignette to `README_PYTORCH.md` | [ ] | Only execute if time permits; highlight CLI invocation plus pytest selectors. Mark `[P]` or leave `[ ]` and note optional in guidance. |

### Phase E — Validation & Closure
Goal: Re-run determinism selectors post-documentation, record final evidence, and close the fix-plan item.
Prereqs: Phase D edits merged locally; repo clean; documentation changes staged for review.
Exit Criteria: Determinism tests pass with documented env guards; fix_plan updated with closure notes; plan archived or marked ready for archive.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Execute determinism regression suite | [D] | Attempt #10 (20251011T060454Z) — Executed determinism tests with env guards: 10 passed, 2 skipped, 5.52s runtime. All thresholds met (correlation 1.0, bitwise equality true, float64 precision maintained). |
| E2 | Summarise results & sync ledgers | [D] | Attempt #10 — Phase E summary.md produced with test breakdown, validation metrics, artifact inventory, exit criteria assessment. docs/fix_plan.md Attempt #10 logged with complete results. |
| E3 | Prepare closure handoff | [D] | Attempt #10 — Closure handoff prepared in Phase E summary.md; all exit criteria met; docs/fix_plan.md status updated to 'done'; plan ready for archive after commit. |

### Exit Criteria (Overall Plan)
- Phases A–C `[D]`, Phase D `[D]` after documentation merged, Phase E `[D]` post-validation.
- Architecture docs, source docstrings, and testing strategy updated with RNG pointer semantics and determinism workflow (Priority 1–2 from `docs_updates.md`).
- Determinism pytest selectors pass with env guards recorded; artifacts stored under `reports/determinism-callchain/phase_e/<STAMP>/validation/`.
- `[DETERMINISM-001]` entry in `docs/fix_plan.md` updated with final attempt summary and marked `done` once documentation + validation complete.

### References
- `reports/determinism-callchain/phase_c/20251011T052920Z/docs_updates.md`
- `reports/determinism-callchain/phase_c/20251011T052920Z/testing_strategy_notes.md`
- `reports/determinism-callchain/phase_b3/20251011T051737Z/c_seed_flow.md`
- `tests/test_at_parallel_013.py`, `tests/test_at_parallel_024.py`
- `specs/spec-a-core.md` §5.3, `specs/spec-a-parallel.md` AT-PARALLEL-013/024
