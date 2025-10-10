## Context
- Initiative: TEST-GOLDEN-001 — regenerate and validate all golden reference artifacts that were invalidated by the Phase D5 lattice unit fix so Phase E parity gates can close cleanly.
- Plan Goal: Restore trustworthy golden data for every test that consumes `tests/golden_data/`, reverify parity thresholds, and leave maintenance hooks so future physics fixes trigger coordinated refreshes instead of ad-hoc edits.
- Dependencies:
  - `specs/spec-a-parallel.md` §AT-PARALLEL-012 and related parity requirements.
  - `tests/golden_data/README.md` — canonical C commands for each dataset.
  - `docs/development/testing_strategy.md` §§1.4–2 — authoritative pytest selectors + ROI thresholds.
  - `docs/development/pytorch_runtime_checklist.md` — vectorization/device guardrails to cite in fix-plan updates.
  - `plans/active/vectorization-parity-regression.md` Phase E — blocked until golden refresh completes.
  - `reports/2026-01-vectorization-parity/phase_e/20251010T082240Z/phase_e_summary.md` — evidence of the current failure state (corr≈0.7157 on stale golden data).

### Status Snapshot (2026-01-07)
- Phase A staleness audit completed via Attempt #18 (`reports/2026-01-golden-refresh/phase_a/20251010T084007Z/`).
- Phase B regeneration + README provenance refresh finished in Attempt #19 (`reports/2026-01-golden-refresh/phase_b/20251010T085124Z/`).
- Phase C parity validation (ROI nb-compare + targeted pytest sweep) now blocks `[VECTOR-PARITY-001]` Phase E handoff.

### Phase A — Scope Confirmation & Staleness Audit
Goal: Enumerate which golden artifacts are invalidated, capture before/after metrics, and confirm the physics deltas introduced by Phase D5.
Prereqs: Access to historical bundles (`reports/2026-01-vectorization-parity/phase_*`) and ability to run collect-only pytest.
Exit Criteria: Timestamped bundle under `reports/2026-01-golden-refresh/phase_a/<STAMP>/` capturing (1) list of affected datasets, (2) correlation deltas using the existing files, (3) summary of physics change that necessitates regeneration, logged in docs/fix_plan.md.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Compare current PyTorch output vs each golden dataset | [D] | ✅ Attempt #18 (20251010T084007Z) captured ROI metrics; see `reports/2026-01-golden-refresh/phase_a/20251010T084007Z/` and sibling PNG/JSON artifacts. |
| A2 | Record provenance & impacted tests | [D] | ✅ Attempt #18 enumerated consuming tests in `scope_summary.md`; reuse the table when staging Phase B regeneration. |
| A3 | Summarise physics delta | [D] | ✅ Attempt #18 documented the Phase D5 lattice correction with references to `phase_d_summary.md`; no further action required. |

### Phase B — Regenerate Golden Artifacts (C Reference)
Goal: Reproduce all affected golden files with the fixed C binary, capturing commands, checksums, and environment metadata.
Prereqs: Phase A bundle approved; `NB_C_BIN` pointing at `./golden_suite_generator/nanoBragg`; required HKL/matrix inputs present.
Exit Criteria: Fresh binaries under `tests/golden_data/` (git-tracked), with provenance logs under `reports/2026-01-golden-refresh/phase_b/<STAMP>/` and README updated.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Execute canonical C commands | [D] | ✅ Attempt #19 (2025-10-10T08:51:24Z) captured all five command logs + checksums under `reports/2026-01-golden-refresh/phase_b/20251010T085124Z/<dataset>/`. |
| B2 | Update README provenance | [D] | ✅ Same attempt refreshed every provenance block in `tests/golden_data/README.md`; see git commit `ebc140f2`. |
| B3 | Commit regenerated artifacts | [D] | ✅ Commit `ebc140f2` (`[TEST-GOLDEN-001] Phase B: Regenerate all 5 golden datasets post Phase D5 lattice fix`) staged binaries + README updates. |

### Phase C — PyTorch Parity Validation & Test Repair
Goal: Prove regenerated golden data yields passing parity metrics and unblock Phase E pytest selector.
Prereqs: Regenerated files staged; editable install intact; PyTorch parity fix (D5) already landed.
Exit Criteria: ROI correlation ≥ spec thresholds, targeted pytest passing, documentation/logs updated.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Validate ROI parity | [ ] | Run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/nb_compare.py --resample --roi 1792 2304 1792 2304 --outdir reports/2026-01-golden-refresh/phase_c/<STAMP>/high_res_roi -- -lambda 0.5 ...` etc. Capture summary JSON/PNG; document corr and sum_ratio in `phase_c_summary.md`. |
| C2 | Run targeted pytest selector | [ ] | `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_high_resolution_variant`. Archive log under `phase_c/<STAMP>/pytest_highres.log`. |
| C3 | Sweep dependent tests | [ ] | Execute additional selectors from Phase A mapping (e.g., triclinic, tilted detector) to ensure no regressions. Record pass/fail in `phase_c_summary.md`; capture evidence for failures. |

### Phase D — Ledger Updates & Maintenance Hooks
Goal: Integrate the refreshed state into plans/fix_plan, protect the new assets, and define monitoring cadence.
Prereqs: Phase C parity confirmed.
Exit Criteria: docs/fix_plan.md updated, galph memory entry added, maintenance SOP documented, plan ready for archive once adoption verified.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Update fix_plan & plans | [ ] | Record Attempt numbers and artifact paths in `[TEST-GOLDEN-001]` and update `[VECTOR-PARITY-001]` to mark Phase E unblocked. Reference this plan in both locations. |
| D2 | Document maintenance cadence | [ ] | Capture `reports/2026-01-golden-refresh/phase_d/<STAMP>/maintenance.md` describing triggers (any physics change touching F_latt/unit conversions) and responsible roles. |
| D3 | Prepare archival checklist | [ ] | Once downstream work stabilises, move this plan to `plans/archive/` with closure summary and note any residual risks (e.g., need for automated checksum verification). |

## Interfaces & Expectations
- Artifacts: Use `reports/2026-01-golden-refresh/phase_<phase>/<STAMP>/` as the canonical scratchpad; do **not** commit these directories.
- Commands: Source canonical C invocations from `tests/golden_data/README.md`; document any deviations with rationale.
- Protected Assets: After README updates, ensure `docs/index.md` references remain valid; treat newly refreshed golden data as protected in fix_plan notes.
- Parallelism: Follow CLAUDE.md guidance when delegating to subagents — include full prompt context, file list, and expected outputs.
- Exit gating: `[VECTOR-PARITY-001]` Phase E cannot close until Phase C tasks here succeed; Phase D ensures future regenerations remain disciplined.
