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
  - Phase E ledger propagation finished this loop (E2/E3 ✅); spec-first stance and dependency gates now live in `docs/fix_plan.md` and the vectorization plans.
  - Phase F design packet archived at `reports/2025-11-source-weights/phase_f/20251009T203823Z/`; Phase G implementation/evidence remains the active gate before downstream profiling can resume.
  - Current blockers: Attempt `20251009T214016Z` surfaced two anomalies — `test_c_divergence_reference` XPASSed (C parity observed) and the TC-D3 C command segfaulted. We must (a) capture a fresh evidence bundle with parity metrics once the segfault is resolved and (b) re-assess the spec vs C decision before downstream plans may resume.

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
| E2 | Update ledgers with decision | [X] | ✅ `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` now cites the spec-first decision memo (`reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md`) and classifies C correlation gaps as expected (`C-PARITY-001`). Summary logged in `galph_memory.md` (2025-12-24 loop). |
| E3 | Propagate dependency gates | [X] | ✅ `plans/active/vectorization.md`/`plans/active/vectorization-gap-audit.md` updated to gate Phase A2/B1 on SOURCE-WEIGHT spec-compliance instead of C correlation; fix_plan cross-references now point to these phases. |

### Phase F — Test Realignment Design (Ready)
Goal: Produce a concrete redesign for the source-weight tests and CLI harnesses so Ralph can implement without ambiguity.
Prereqs: Phase E ledger updates approved.
Exit Criteria: Design packet defines new acceptance criteria, fixture usage, and pytest selectors.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| F1 | Inventory affected tests | [X] | ✅ `reports/2025-11-source-weights/phase_f/20251009T203823Z/test_plan.md` enumerates all impacted tests (`TestSourceWeights*`) with current vs proposed assertions and fixture notes. |
| F2 | Define new acceptance criteria | [X] | ✅ Same design packet documents spec-computed reference expectations (weights ignored, CLI lambda override) with tolerances ≤1e-3, citing `docs/development/testing_strategy.md`. |
| F3 | Map pytest selectors & commands | [X] | ✅ `reports/2025-11-source-weights/phase_f/20251009T203823Z/commands.txt` captures `pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence` plus the supporting CLI bundle commands. |

### Phase G — Implementation & Evidence (Blocked until Phase F)
Goal: Update the test suite and capture supporting artifacts demonstrating spec compliance.
Prereqs: Phase F design packet approved; existing guard in `src/nanobrag_torch/simulator.py` remains untouched.
Exit Criteria: Tests enforce spec behaviour, targeted pytest run + CLI bundle archived, fix_plan attempts updated.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| G1 | Update test suite | [X] | ✅ Landed in HEAD — `tests/test_cli_scaling.py` now enforces spec-first behaviour (weighted vs equal check, CLI lambda override, C-divergence marker). Retain the Phase F design packet for provenance. |
| G2 | Capture evidence bundle (refresh) | [ ] | Rebuild the C binary if missing (`make -C golden_suite_generator`) and rerun the Phase F command set. Archive a new timestamped folder `reports/2025-11-source-weights/phase_g/<STAMP>/` containing `collect.log`, `pytest.log`, `commands.txt`, `tc_d1_cmd.txt`, `tc_d3_cmd.txt`, `py_metrics.json`, `c_metrics.json`, `correlation.txt`, `notes.md`, and stdout/stderr captures. Expect PyTorch vs C correlation ≥0.999 and |sum_ratio−1| ≤3e-3 (spec-compliance). If `test_c_divergence_reference` XPASSes or C segfaults, record the anomaly in `notes.md`, preserve partial artifacts, and transition to Phase H without deleting the bundle. |
| G3 | Update fix_plan attempts | [ ] | After capturing (or documenting) the refreshed bundle, log a new `[SOURCE-WEIGHT-001]` Attempt summarising pytest outcomes, CLI commands, metrics, anomaly observations, and artifact paths. Flag whether parity matched spec expectations and whether C segfault triage is still open. |
| G4 | Diagnose TC-D3 C segfault | [ ] | Rebuild the instrumented C binary with debug symbols (`make -C golden_suite_generator clean && make -C golden_suite_generator CFLAGS="-g -O0"`). Reproduce the segfault with the TC-D3 command, capture `gdb`/`backtrace` output, and store logs under `reports/2025-11-source-weights/phase_g/<STAMP>/c_segfault/`. Identify whether the crash stems from command configuration, missing fixture, or code regression and summarise findings for Phase H. |

### Phase H — Parity Reassessment & Test Alignment (New)
Goal: Reconcile the `C-PARITY-001` classification with new C parity evidence, update acceptance artefacts, and ensure the test suite encodes the correct expectation (pass, not xfail).
Prereqs: Phase G bundle captured (even if anomalous) and TC-D3 segfault triage notes recorded.
Exit Criteria: Parity memo updated, tests adjusted to expect pass, and spec acceptance references aligned.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| H1 | Reproduce parity metrics under controlled run | [ ] | Execute the targeted selector `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_c_divergence_reference` and the paired CLI commands in a fresh tmpdir. Capture metrics/artifacts under `reports/2025-11-source-weights/phase_h/<STAMP>/parity_reassessment/` to confirm correlation ≥0.999 and |sum_ratio−1| ≤3e-3. |
| H2 | Author parity reassessment memo | [ ] | Draft `reports/2025-11-source-weights/phase_h/<STAMP>/parity_reassessment.md` quoting nanoBragg.c lines 2570-2720 to demonstrate weights are ignored, summarising the new evidence, and superseding `spec_vs_c_decision.md` (mark legacy memo as "historical" in the new document). Include explicit conclusions for test expectations and downstream plans. |
| H3 | Update tests to expect pass | [ ] | Modify `tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_c_divergence_reference` to remove `@pytest.mark.xfail`, tighten tolerances to correlation ≥0.999 / |sum_ratio−1| ≤3e-3, and ensure failure logs still capture `unexpected_c_parity/metrics.json`. Validate via targeted pytest selector and store logs alongside the memo. |
| H4 | Align spec acceptance text | [ ] | Update `specs/spec-a-core.md` (AT-SRC-001) and any dependent docs to reflect the equal-weight expectation (remove lingering "applies weight" wording), citing the new parity memo. Record commands and diffs in the same reports directory. |

### Phase I — Documentation & Downstream Unblocks (Blocked until Phase H)
Goal: Sync architecture docs, runtime checklist, and dependent plans once parity reassessment and test updates are complete.
Prereqs: Phase H completed with passing tests, updated memo, and archived artifacts.
Exit Criteria: Documentation reflects spec-first stance and parity alignment; plan ready for archive.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| I1 | Update permanent docs | [ ] | Amend `docs/architecture/pytorch_design.md` (Sources subsection) and `docs/development/pytorch_runtime_checklist.md` to state weights are ignored, reference the parity reassessment memo, and remove references to the deprecated divergence classification. |
| I2 | Notify dependent initiatives | [ ] | Update `plans/active/vectorization-gap-audit.md`, `plans/active/vectorization.md`, and `docs/fix_plan.md` entries (`VECTOR-GAPS-002`, `PERF-PYTORCH-004`) so they reference the new spec-compliance tests and parity memo instead of C divergence thresholds. |
| I3 | Prepare archival summary | [ ] | Once I1/I2 done, draft closure note for `plans/archive/` and update `[SOURCE-WEIGHT-001]` status to `done`, noting that C/PyTorch parity has been validated and recording any remaining risks. |

## Reporting Expectations
- Store new artifacts under `reports/2025-11-source-weights/phase_e/`, `/phase_f/`, `/phase_g/`, `/phase_h/`, and `/phase_i/` with ISO timestamps. Do **not** commit report directories; reference them from fix_plan attempts.
- All test commands must include `KMP_DUPLICATE_LIB_OK=TRUE` and validated pytest selectors (`--collect-only`).
- Parity metrics against C should target correlation ≥0.999 and |sum_ratio−1| ≤3e-3; label anomalies explicitly and link to the parity reassessment memo.
- Keep this plan synchronised with `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` and dependent plans whenever a phase gate flips.
