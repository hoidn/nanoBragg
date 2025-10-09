## Context
- Initiative: SOURCE-WEIGHT-001 — align the PyTorch simulator, test suite, and documentation with the spec requirement that source weights are ignored while documenting the nanoBragg C divergence.
- Phase Goal: Establish a spec-first contract (weights ignored, wavelength from `-lambda`), realign automated tests accordingly, and unblock downstream profiling/vectorization efforts with clearly documented C-behaviour deviations.
- Dependencies:
  - `specs/spec-a-core.md` §4 (Sources, Divergence & Dispersion) — normative statement that weights/wavelengths in sourcefile are read but ignored.
  - `golden_suite_generator/nanoBragg.c:2570-2720` — C reference showing divergence grid population and use of `source_I`.
  - `tests/test_cli_scaling.py` (`TestSourceWeights*`) — current parity tests that enforce C-style weighting.
  - `docs/architecture/pytorch_design.md` & `docs/development/pytorch_runtime_checklist.md` — design guardrails that must reflect the spec-first contract.
  - `plans/active/vectorization.md` / `plans/active/vectorization-gap-audit.md` — profiling work gated on SOURCE-WEIGHT-001 completion.
  - Existing evidence bundles under `reports/2025-11-source-weights/phase_{a..e}/` (baseline traces, design notes, CLI commands).
- Status Snapshot (2025-12-24 refresh):
  - Legacy Phases A–D are complete (fixtures, spec confirmation, implementation guard, trace instrumentation).
  - Phase E1 done (decision memo locked 20251009T202432Z); Phase E2/E3 remain to update ledgers and dependent gates before Phase F can proceed.
  - Current blockers: `tests/test_cli_scaling.py::TestSourceWeights*` still assert C-style sum(weight) normalisation, keeping parity metrics <0.8 and blocking VECTOR-* initiatives until Phases F–G realign the suite.

### Legacy Evidence (Phases A–D) — Locked
Goal: Preserve provenance of the already-completed investigation.
- Phase A (Bias capture): `reports/2025-11-source-weights/phase_a/20251009T071821Z/` — fixtures + baseline metrics (`sum_ratio≈3.28e2`).
- Phase B (Spec confirmation & callchain): `reports/2025-11-source-weights/phase_b/20251009T083515Z/` — spec quotes, PyTorch callchain, parity reproduction.
- Phase C (Implementation adjustments): Commits 321c91e/dffea55 plus regression tests in `tests/test_cli_scaling.py`; guard landed at `src/nanobrag_torch/simulator.py:399-423`.
- Phase D (Divergence design & harness): `reports/2025-11-source-weights/phase_d/20251009T102319Z/` & `.../20251009T104310Z/` — divergence analysis, implementation options, acceptance harness draft.
- No further action required; treat artifacts as immutable references.

### Phase E — Spec vs C Alignment Decision (In Progress)
Goal: Codify the spec-first stance, document the C bug, and update ledgers so downstream work references the correct contract.
Prereqs: Review spec §4, divergence traces (`phase_e/20251009T192746Z/trace*`), and existing design notes.
Exit Criteria: Decision memo + ledger updates make it explicit that PyTorch is correct per spec and C diverges.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Draft decision memo | [X] | ✅ `reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md` (FINAL) captures spec citations, trace evidence, and locks the spec-first decision (C bug tagged `C-PARITY-001`). Memo inventories impacted tests (TestSourceWeights*, TC-D1/D3) and embeds reproduction commands. |
| E2 | Update ledgers with decision | [ ] | After E1, update `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` Next Actions and Observations to state the spec-first contract, cite the decision memo, and classify existing parity failures as expected. Log summary in `galph_memory.md`. |
| E3 | Propagate dependency gates | [ ] | Refresh `plans/active/vectorization.md` Phase A1/A2 guidance so VECTOR-TRICUBIC-002 unblocks once Phase F–G deliverables land (spec compliance replaces C correlation thresholds). |

### Phase F — Test Realignment Design (Ready)
Goal: Produce a concrete redesign for the source-weight tests and CLI harnesses so Ralph can implement without ambiguity.
Prereqs: Phase E ledger updates approved.
Exit Criteria: Design packet defines new acceptance criteria, fixture usage, and pytest selectors.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| F1 | Inventory affected tests | [ ] | Document in `reports/2025-11-source-weights/phase_f/<STAMP>/test_plan.md` which tests must change (`TestSourceWeights::test_weighted_source_matches_c`, `TestSourceWeightsDivergence::test_sourcefile_only_parity`, related fixtures). Provide current assertions and proposed replacements (spec-equality, warning checks). |
| F2 | Define new acceptance criteria | [ ] | Extend test_plan.md with explicit metrics: e.g., compare PyTorch against a spec-constructed reference (PyTorch run with weights stripped), require sum ratios within 1e-3, prohibit reliance on C totals. Reference `docs/development/testing_strategy.md` for tolerance policy. |
| F3 | Map pytest selectors & commands | [ ] | Validate selectors via `pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights` and record commands in `commands.txt`. Include CLI bundle for generating "spec vs C" comparison artifacts (store under `reports/2025-11-source-weights/phase_f/<STAMP>/cli/`). |

### Phase G — Implementation & Evidence (Blocked until Phase F)
Goal: Update the test suite and capture supporting artifacts demonstrating spec compliance.
Prereqs: Phase F design packet approved; existing guard in `src/nanobrag_torch/simulator.py` remains untouched.
Exit Criteria: Tests enforce spec behaviour, targeted pytest run + CLI bundle archived, fix_plan attempts updated.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| G1 | Update test suite | [ ] | Modify `tests/test_cli_scaling.py` per design packet: rename parity test to spec compliance, compare PyTorch weighted vs unweighted runs, ensure warnings use `pytest.warns`. Include C-run optional metrics, but mark as expected mismatch referencing decision memo. |
| G2 | Capture evidence bundle | [ ] | Execute `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence` and rerun the TC-D1/TC-D3 CLI commands capturing outputs under `reports/2025-11-source-weights/phase_g/<STAMP>/`. Store `metrics.json`, `correlation.txt`, and note expected C mismatch. |
| G3 | Update fix_plan attempts | [ ] | Record Attempt summarising new tests, selectors, metrics, and location of artifacts. Note that correlation vs C <0.8 is expected per spec decision. |

### Phase H — Documentation & Downstream Unblocks (Blocked until Phase G)
Goal: Sync architecture docs, runtime checklist, and dependent plans once tests pass and evidence is archived.
Prereqs: Phase G completed with passing tests and archived artifacts.
Exit Criteria: Documentation reflects spec-first stance; plan ready for archive.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| H1 | Update permanent docs | [ ] | Amend `docs/architecture/pytorch_design.md` (Sources subsection) and `docs/development/pytorch_runtime_checklist.md` to state weights are ignored and cite C divergence. Cross-link to decision memo and spec section. |
| H2 | Notify dependent initiatives | [ ] | Update `plans/active/vectorization-gap-audit.md`, `plans/active/vectorization.md`, and `docs/fix_plan.md` entries (`VECTOR-GAPS-002`, `PERF-PYTORCH-004`) so they reference the new spec-compliance tests instead of C correlation thresholds. |
| H3 | Prepare archival summary | [ ] | Once H1/H2 done, draft closure note for `plans/archive/` and update `[SOURCE-WEIGHT-001]` status to `done`, noting residual expected C divergence in observations. |

## Reporting Expectations
- Store new artifacts under `reports/2025-11-source-weights/phase_e/`, `/phase_f/`, `/phase_g/`, and `/phase_h/` with ISO timestamps. Do **not** commit report directories; reference them from fix_plan attempts.
- All test commands must include `KMP_DUPLICATE_LIB_OK=TRUE` and validated pytest selectors (`--collect-only`).
- Parity metrics against C should be recorded but explicitly labelled as "expected divergence" citing the decision memo.
- Keep this plan synchronised with `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` and dependent plans whenever a phase gate flips.
