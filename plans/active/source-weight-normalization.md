## Context
- Initiative: SOURCE-WEIGHT-001 — converge the simulator, test suite, and documentation on the spec contract that **source weights are ignored** while documenting any residual C-only defects.
- Current Objective: Phase H deliverables (memo + test flip) and Phase I1 documentation updates landed (Attempt #38, 20251010T005717Z). Phase I2 ledger propagation closed in Attempt #39 (20251010T011249Z); remaining work: assemble the archival hand-off (Phase I3).
- Dependencies:
  - `specs/spec-a-core.md` §4 — normative statement: both weight and wavelength columns in sourcefile are ignored; CLI `-lambda` is authoritative.
  - `golden_suite_generator/nanoBragg.c:2570-2720` — C ingestion loop (will be quoted in the Phase H memo) confirming equal-weight accumulation.
  - `tests/test_cli_scaling.py` (`TestSourceWeights*`) — spec-first tests landed in Phase F; `test_c_divergence_reference` still marked xfail pending Phase H.
  - `docs/architecture/pytorch_design.md` §1.1 and `docs/development/pytorch_runtime_checklist.md` — must inherit the parity decision during Phase I.
  - Plans blocked by this initiative: `plans/active/vectorization.md` (Phase A2) and `plans/active/vectorization-gap-audit.md` (Phase B1).
  - Evidence bundles: `reports/2025-11-source-weights/phase_{a..f}/` (baseline traces + design packet) and `reports/2025-11-source-weights/phase_g/{20251009T235016Z,20251010T000742Z}/` (final parity bundle).
- Status Snapshot (2025-12-27): Phases A–G remain archival references and Phase H (Attempts #31–#37) is now fully complete — ledger, bug docs, and dependent plans all cite the Phase H memo (`reports/2025-11-source-weights/phase_h/20251010T002324Z/`). Phase I1 documentation updates (pytorch_design.md, pytorch_runtime_checklist.md, specs/spec-a-core.md) are complete (`reports/2025-11-source-weights/phase_i/20251010T005717Z/`). Phase I2 ledger propagation finished in Attempt #39 (20251010T011249Z), leaving Phase I3 archival as the final gate. `[C-SOURCEFILE-001]` continues to track the C comment parsing bug uncovered during Phase G.

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

### Phase H — Parity Reassessment & Test Updates (Complete)
Goal: Supersede the legacy spec-vs-C memo, update parity tests to expect PASS, and correct the bug ledger/docs.
Prereqs: Phase G completed with working C output and updated fix_plan Attempt.
Exit Criteria: New parity memo, updated tests (no xfail), and documentation reflecting that C honours equal weighting.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| H1 | Author parity reassessment memo | [D] | ✅ `reports/2025-11-source-weights/phase_h/20251010T002324Z/parity_reassessment.md` is the authoritative memo quoting `nanoBragg.c:2570-2720`, superseding the Phase E decision and documenting equal weighting. |
| H2 | Update divergence test expectation | [D] | ✅ `tests/test_cli_scaling.py:585-692` now expects PASS with correlation ≥0.999 and |sum_ratio−1| ≤5e-3; pytest log stored with the Phase H memo (20251010T002324Z) shows the selector passing. |
| H3 | Correct bug ledger references | [D] | ✅ 2025-12-27 (galph) — Updated `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` status/Next Actions and reconfirmed `docs/bugs/verified_c_bugs.md` scopes C-PARITY-001 to φ-carryover while pointing sourcefile issues to `[C-SOURCEFILE-001]`; parity memo + thresholds now cited everywhere. |
| H4 | Notify dependent plans | [D] | ✅ 2025-12-27 (galph) — Refreshed `plans/active/vectorization.md` status snapshot and dependent fix_plan entries (`VECTOR-TRICUBIC-002`, `VECTOR-GAPS-002`, `PERF-PYTORCH-004`) to quote the Phase H memo and corr ≥0.999 / |sum_ratio−1| ≤5e-3 thresholds before profiling restarts. |

### Phase I — Documentation & Downstream Unblocks (Active)
Goal: Propagate the parity decision through permanent docs and unblock dependent plans.
Prereqs: Phase H deliverables published and tests passing.
Exit Criteria: Architecture/runtime docs updated, dependent plans ungated, plan ready for archive.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| I1 | Update permanent docs | [D] | ✅ Attempt #38 (20251010T005717Z) revised `docs/architecture/pytorch_design.md` (§1.1.5), `docs/development/pytorch_runtime_checklist.md` (item #4), and `specs/spec-a-core.md:151-155`, citing the Phase H parity memo and parity thresholds. Artifacts stored under `reports/2025-11-source-weights/phase_i/20251010T005717Z/` with pytest collect-only proof. |
| I2 | Ungate dependent plans | [D] | ✅ Attempt #39 (20251010T011249Z). Refreshed `plans/active/vectorization.md` (Phase A2) and `plans/active/vectorization-gap-audit.md` (Phase B1) with parity memo citations, and updated `docs/fix_plan.md` entries (`VECTOR-TRICUBIC-002`, `VECTOR-GAPS-002`, `PERF-PYTORCH-004`) to reference `docs/architecture/pytorch_design.md` §1.1.5 and `docs/development/pytorch_runtime_checklist.md` item #4. Artifacts: `reports/2025-11-source-weights/phase_i/20251010T011249Z/`. |
| I3 | Archive initiative | [ ] | Draft closure summary for `plans/archive/source-weight-normalization.md`, update `[SOURCE-WEIGHT-001]` status to `done`, and log a final galph_memory entry noting residual risks (e.g., interpolation segfault remains a C bug). |

## Reporting Expectations
- Store new artifacts under `reports/2025-11-source-weights/phase_g/<STAMP>/`, `/phase_h/<STAMP>/`, and `/phase_i/<STAMP>/`; list paths (do not commit report dirs).
- All tests must include `KMP_DUPLICATE_LIB_OK=TRUE`; validate selectors with `--collect-only` before execution.
- Document CLI environment (`NB_C_BIN`, working directory, sanitised fixture path) inside each bundle’s `notes.md`.
- When parity metrics deviate from the thresholds, capture hypotheses and follow-up probes before advancing phases.
- Keep this plan in sync with `docs/fix_plan.md` `[SOURCE-WEIGHT-001]`; update both whenever a phase gate flips.
