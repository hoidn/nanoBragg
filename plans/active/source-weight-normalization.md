## Context
- Initiative: SOURCE-WEIGHT-001 — converge the simulator, test suite, and documentation on the spec contract that **source weights are ignored** while documenting any residual C-only defects.
- Current Objective: Phase G parity recovery is complete (Attempt #35, 20251010T000742Z) with authoritative XPASS metrics; we now need to publish the parity reassessment memo, remove the legacy xfail, and propagate the decision through the ledger and downstream plans.
- Dependencies:
  - `specs/spec-a-core.md` §4 — normative statement: both weight and wavelength columns in sourcefile are ignored; CLI `-lambda` is authoritative.
  - `golden_suite_generator/nanoBragg.c:2570-2720` — C ingestion loop (will be quoted in the Phase H memo) confirming equal-weight accumulation.
  - `tests/test_cli_scaling.py` (`TestSourceWeights*`) — spec-first tests landed in Phase F; `test_c_divergence_reference` still marked xfail pending Phase H.
  - `docs/architecture/pytorch_design.md` §1.1 and `docs/development/pytorch_runtime_checklist.md` — must inherit the parity decision during Phase I.
  - Plans blocked by this initiative: `plans/active/vectorization.md` (Phase A2) and `plans/active/vectorization-gap-audit.md` (Phase B1).
  - Evidence bundles: `reports/2025-11-source-weights/phase_{a..f}/` (baseline traces + design packet) and `reports/2025-11-source-weights/phase_g/{20251009T235016Z,20251010T000742Z}/` (final parity bundle).
- Status Snapshot (2025-12-25): Phases A–F remain archival references. Phase G is ✅ complete with sanitised fixture (`reports/2025-11-source-weights/fixtures/two_sources_nocomments.txt`, SHA256 f23e1b1e60412c5378ee197542e0aca1ffc658198edd4e9584a3dffb57330c44) and matching PyTorch/C metrics (corr=0.9999886, ratio=1.0038). Remaining work: Phase H memo + test realignment, then Phase I documentation propagation before unblocking vectorization/perf plans. `[C-SOURCEFILE-001]` tracks the separate C comment parsing bug discovered while executing Phase G.

### Legacy Phases — Archived (No Further Action)
Goal: Preserve provenance; treat artifacts as immutable references.
- Phase A — Bias capture: `reports/2025-11-source-weights/phase_a/20251009T071821Z/` (sum_ratio≈3.28e2 baseline).
- Phase B — Spec confirmation & callchain: `reports/2025-11-source-weights/phase_b/20251009T083515Z/` (parallel trace + spec excerpts).
- Phase C — Implementation guards: commits 321c91e & dffea55 plus `tests/test_cli_scaling.py` updates; guard at `src/nanobrag_torch/simulator.py:399-423`.
- Phase D — Divergence design & harness: `reports/2025-11-source-weights/phase_d/{20251009T102319Z,20251009T104310Z}/` (options analysis, CLI harness draft).
- Phase E — Ledger propagation: `reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md` (now superseded once Phase H completes).
- Phase F — Test realignment design: `reports/2025-11-source-weights/phase_f/20251009T203823Z/test_plan.md` (selector inventory + acceptance criteria).

### Phase G — Parity Evidence Recovery (Complete)
Goal: Capture a clean, reproducible parity evidence bundle (PyTorch + C) that avoids the tricubic segfault, verifies spec-aligned equal weighting, and updates the ledger.
Prereqs: `NB_C_BIN` pointing at a freshly rebuilt debug binary; spec-first pytest suite already green (Phase F); review segfault write-up in `phase_g/20251009T215516Z/notes.md`; confirm the sanitised two-source fixture (comments removed) is available before rerunning CLI commands.
Exit Criteria: New `<STAMP>` bundle under `reports/2025-11-source-weights/phase_g/` containing PyTorch + C CLI outputs, metrics, and notes; fix_plan Attempt recorded with parity verdict and segfault guardrails.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| G0 | Harmonise fixture vs test parameters | [D] | Completed Attempt #31 (20251009T230946Z). Comment-free fixture published at `reports/2025-11-source-weights/fixtures/two_sources_nocomments.txt` with SHA256 + rationale in notes.md. |
| G1 | Canonicalise reproduction commands | [D] | Attempt #34 (20251009T235016Z) recorded canonical PyTorch/C commands (with `-interpolate 0`) in `commands.txt`; NB_C_BIN explicitly set. |
| G2 | Capture fresh parity bundle | [D] | Attempt #35 (20251010T000742Z) ran the targeted pytest selector and CLI pair; `metrics.json` records corr=0.9999886, |sum_ratio−1|=0.0038. |
| G3 | Update fix_plan attempt | [D] | Fix_plan Attempt #35 documents metrics, sanitised fixture checksum, segfault guardrails, and parity verdict. |
| G4 | Document segfault guard | [D] | ✅ Root cause captured in `reports/2025-11-source-weights/phase_g/20251009T215516Z/c_segfault/crash_analysis.md` (negative Fhkl index when interpolation auto-enables). Reference this note in new bundles so future runs pass `-interpolate 0` or ship a fixture HKL. |
| G5 | Cross-link comment parsing bug plan | [D] | Attempt #35 notes reference `[C-SOURCEFILE-001]`; fix_plan entry created 2025-12-25 keeps bug tracking decoupled. |

### Phase H — Parity Reassessment & Test Updates (Active)
Goal: Supersede the legacy spec-vs-C memo, update parity tests to expect PASS, and correct the bug ledger/docs.
Prereqs: Phase G completed with working C output and updated fix_plan Attempt.
Exit Criteria: New parity memo, updated tests (no xfail), and documentation reflecting that C honours equal weighting.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| H1 | Author parity reassessment memo | [ ] | Create `reports/2025-11-source-weights/phase_h/<STAMP>/parity_reassessment.md` quoting `nanoBragg.c:2570-2720`, contrasting Phase E assumptions vs Phase G evidence, and explicitly stating that C and PyTorch ignore source weights. Mark `spec_vs_c_decision.md` as historical in the new memo. |
| H2 | Update divergence test expectation | [ ] | Edit `tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_c_divergence_reference` to remove `@pytest.mark.xfail` and assert correlation ≥0.999 with |sum_ratio−1| ≤3e-3. Validate via targeted pytest selector and archive logs beside the memo. |
| H3 | Correct bug ledger references | [ ] | Audit `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` narrative and `docs/bugs/verified_c_bugs.md` to ensure C-PARITY-001 is no longer cited for source weights, and cross-reference `[C-SOURCEFILE-001]`. If warranted, file a short bug note for the interpolation segfault under `docs/bugs/c-parity-XXX.md`. |
| H4 | Notify dependent plans | [ ] | Update `plans/active/vectorization.md` (Phase A2), `plans/active/vectorization-gap-audit.md` (Phase B1), and related `docs/fix_plan.md` entries so they reference the Phase H memo instead of retired divergence thresholds. |

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
- Document CLI environment (`NB_C_BIN`, working directory, sanitised fixture path) inside each bundle’s `notes.md`.
- When parity metrics deviate from the thresholds, capture hypotheses and follow-up probes before advancing phases.
- Keep this plan in sync with `docs/fix_plan.md` `[SOURCE-WEIGHT-001]`; update both whenever a phase gate flips.
