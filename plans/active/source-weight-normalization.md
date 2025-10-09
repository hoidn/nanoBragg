## Context
- Initiative: SOURCE-WEIGHT-001 — converge the simulator, test suite, and documentation on the spec contract that **source weights are ignored** while documenting any residual C-only defects.
- Current Objective: After the 20251009 parity evidence unexpectedly XPASSed (`correlation≈0.99999`, `sum_ratio≈1.0038`), re-establish a trustworthy parity bundle, supersede the stale "C diverges" memo, and unblock downstream vectorization/perf work.
- Dependencies:
  - `specs/spec-a-core.md` §4 — normative statement: both weight and wavelength columns in sourcefile are ignored; CLI `-lambda` is authoritative.
  - `golden_suite_generator/nanoBragg.c:2570-2720` — C ingestion loop showing `source_I` handling (needs fresh review to confirm weights are ignored).
  - `tests/test_cli_scaling.py` (`TestSourceWeights*`) — spec-first tests landed in Phase F; `test_c_divergence_reference` still marked xfail.
  - `docs/architecture/pytorch_design.md` §1.1 and `docs/development/pytorch_runtime_checklist.md` — must reflect the spec-first stance once parity confirmed.
  - Plans blocked by this initiative: `plans/active/vectorization.md` (Phase A2) and `plans/active/vectorization-gap-audit.md` (Phase B1).
  - Evidence bundles: `reports/2025-11-source-weights/phase_{a..f}/` (baseline traces + design packet) and `reports/2025-11-source-weights/phase_g/20251009T215516Z/` (XPASS + C segfault diagnostics).
- Status Snapshot (2025-12-24): Phases A–F remain locked; Phase G must be rerun because the current bundle lacks C output (segfault) and contradicts the legacy decision memo. Vectorization remains gated until Phase H updates land and dependent plans receive the new selectors/artifacts.

### Legacy Phases — Archived (No Further Action)
Goal: Preserve provenance; treat artifacts as immutable references.
- Phase A — Bias capture: `reports/2025-11-source-weights/phase_a/20251009T071821Z/` (sum_ratio≈3.28e2 baseline).
- Phase B — Spec confirmation & callchain: `reports/2025-11-source-weights/phase_b/20251009T083515Z/` (parallel trace + spec excerpts).
- Phase C — Implementation guards: commits 321c91e & dffea55 plus `tests/test_cli_scaling.py` updates; guard at `src/nanobrag_torch/simulator.py:399-423`.
- Phase D — Divergence design & harness: `reports/2025-11-source-weights/phase_d/{20251009T102319Z,20251009T104310Z}/` (options analysis, CLI harness draft).
- Phase E — Ledger propagation: `reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md` (now superseded once Phase H completes).
- Phase F — Test realignment design: `reports/2025-11-source-weights/phase_f/20251009T203823Z/test_plan.md` (selector inventory + acceptance criteria).

### Phase G — Parity Evidence Recovery (Active)
Goal: Capture a clean, reproducible parity evidence bundle (PyTorch + C) that avoids the tricubic segfault, verifies spec-aligned equal weighting, and updates the ledger.
Prereqs: `NB_C_BIN` pointing at a freshly rebuilt debug binary; spec-first pytest suite already green (Phase F); review segfault write-up in `phase_g/20251009T215516Z/notes.md`.
Exit Criteria: New `<STAMP>` bundle under `reports/2025-11-source-weights/phase_g/` containing PyTorch + C CLI outputs, metrics, and notes; fix_plan Attempt recorded with parity verdict and segfault guardrails.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| G1 | Canonicalise reproduction commands | [ ] | Validate PyTorch + C CLI commands that match TC-D1/TC-D3 geometry while avoiding the interpolation crash (add `-interpolate 0` or provide minimal HKL). Record both commands in `reports/2025-11-source-weights/phase_g/<STAMP>/commands.txt`; confirm `NB_C_BIN` in env and run from the bundle directory so SMV/PGM outputs stay scoped. |
| G2 | Capture fresh parity bundle | [ ] | Execute the targeted pytest selector (`NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence`) followed by the canonical PyTorch and C CLI commands. Store stdout/stderr, floatfiles, and recomputed metrics (`metrics.json`, `correlation.txt`) under the same `<STAMP>`. Target correlation ≥0.999 and |sum_ratio−1| ≤3e-3; if parity fails, annotate in `notes.md` with hypotheses. |
| G3 | Update fix_plan attempt | [ ] | Append a new Attempt to `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` summarising the bundle (tests run, metrics, CLI commands, anomalies). Explicitly retire the "expected divergence" narrative and mark whether parity now matches spec. |
| G4 | Document segfault guard | [D] | ✅ Root cause captured in `reports/2025-11-source-weights/phase_g/20251009T215516Z/c_segfault/crash_analysis.md` (negative Fhkl index when interpolation auto-enables). Reference this note in new `notes.md` so future bundles pass `-interpolate 0` or ship a fixture HKL.

### Phase H — Parity Reassessment & Test Updates (Queued)
Goal: Supersede the legacy spec-vs-C memo, update parity tests to expect PASS, and correct the bug ledger/docs.
Prereqs: Phase G completed with working C output and updated fix_plan Attempt.
Exit Criteria: New parity memo, updated tests (no xfail), and documentation reflecting that C honours equal weighting.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| H1 | Author parity reassessment memo | [ ] | Create `reports/2025-11-source-weights/phase_h/<STAMP>/parity_reassessment.md` quoting `nanoBragg.c:2570-2720`, contrasting Phase E assumptions vs Phase G evidence, and explicitly stating that C and PyTorch ignore source weights. Mark `spec_vs_c_decision.md` as historical in the new memo. |
| H2 | Update divergence test expectation | [ ] | Edit `tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_c_divergence_reference` to remove `@pytest.mark.xfail` and assert correlation ≥0.999 with |sum_ratio−1| ≤3e-3. Validate via targeted pytest selector and archive logs beside the memo. |
| H3 | Correct bug ledger references | [ ] | Audit `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` narrative and `docs/bugs/verified_c_bugs.md` to ensure C-PARITY-001 (phi carryover) is no longer cited for source weights. If warranted, file a new bug note for the interpolation segfault under `docs/bugs/c-parity-XXX.md`. |

### Phase I — Documentation & Downstream Unblocks (Blocked)
Goal: Propagate the parity decision through permanent docs and unblock dependent plans.
Prereqs: Phase H deliverables published and tests passing.
Exit Criteria: Architecture/runtime docs updated, dependent plans ungated, plan ready for archive.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| I1 | Update permanent docs | [ ] | Revise `docs/architecture/pytorch_design.md` (sources subsection), `docs/development/pytorch_runtime_checklist.md`, and any acceptance text in `specs/spec-a-core.md` to reference the new parity memo and emphasise equal weighting. Capture diffs + commands in `reports/2025-11-source-weights/phase_i/<STAMP>/`. |
| I2 | Ungate dependent plans | [ ] | Refresh `plans/active/vectorization.md` (Phase A2) and `plans/active/vectorization-gap-audit.md` (Phase B1) with the new selectors/artifacts, and update `docs/fix_plan.md` entries (`VECTOR-TRICUBIC-002`, `VECTOR-GAPS-002`, `PERF-PYTORCH-004`) so they cite the parity memo instead of the retired divergence thresholds. |
| I3 | Archive initiative | [ ] | Draft closure summary for `plans/archive/source-weight-normalization.md`, update `[SOURCE-WEIGHT-001]` status to `done`, and log a final galph_memory entry noting residual risks (e.g., interpolation segfault remains a C bug). |

## Reporting Expectations
- Store new artifacts under `reports/2025-11-source-weights/phase_g/<STAMP>/`, `/phase_h/<STAMP>/`, and `/phase_i/<STAMP>/`; list paths (do not commit report dirs).
- All tests must include `KMP_DUPLICATE_LIB_OK=TRUE`; validate selectors with `--collect-only` before execution.
- Document CLI environment (`NB_C_BIN`, working directory) inside each bundle’s `notes.md`.
- When parity metrics deviate from the thresholds, capture hypotheses and follow-up probes before advancing phases.
- Keep this plan in sync with `docs/fix_plan.md` `[SOURCE-WEIGHT-001]`; update both whenever a phase gate flips.
