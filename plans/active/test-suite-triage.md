## Context
- Initiative: TEST-SUITE-TRIAGE-001 — obey long-term directive to run the full PyTorch nanoBragg pytest suite, capture failures, and classify them for remediation sequencing.
- Phase Goal: Establish a reproducible, artifact-backed understanding of current test health (`pytest tests/`) before authorising any other feature work.
- Dependencies:
  - `docs/development/testing_strategy.md` — authoritative guidance for test ordering, environment variables, and smoke test expectations.
  - `arch.md` §2 & §15 — runtime guardrails (device/dtype, differentiability) that must stay intact during triage.
  - `docs/fix_plan.md` — ledger for logging attempts, failure classifications, and follow-up tasks.
  - `docs/development/pytorch_runtime_checklist.md` — sanity checklist before executing PyTorch-heavy tests (KMP env, device neutrality).
  - `prompts/callchain.md` — fallback SOP if targeted tracing is required for specific failures (defer until triage completes).

### Status Snapshot (2026-01-21)
- Phase A ✅ complete (Attempt #1 — `reports/2026-01-test-suite-triage/phase_a/20251010T131000Z/`); 692 tests collected, no errors.
- Phase B ✅ complete (Attempt #5 — `reports/2026-01-test-suite-triage/phase_b/20251010T135833Z/`); full suite executed in 1865 s with 50 failures captured across 18 clusters.
- Phase C ✅ complete (Attempt #6 — `reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/`); all 50 failures classified across 18 clusters, mapped to 10 existing + 8 new fix-plan IDs.
- Phase D ✅ complete (D1–D4). This loop issued the supervisor handoff for `[CLI-DEFAULTS-001]` (input stamp 20251010T153734Z) unlocking remediation attempts.
- Phase E ✅ complete (Attempt #7 — `reports/2026-01-test-suite-triage/phase_e/20251010T180102Z/`); 691 executed tests, 516 passed, 49 failed, 126 skipped. CLI defaults cluster cleared; other clusters unchanged.
- Phase F ✅ complete (Attempt #8 — `reports/2026-01-test-suite-triage/phase_f/20251010T184326Z/`); refreshed triage bundle with 49-failure classification, cluster deltas, and pending actions table. C1 resolved, 17 active clusters documented.
- Phase G ✅ progressing — Attempt #9 recorded the refreshed remediation ladder addendum at `reports/2026-01-test-suite-triage/phase_g/20251011T030546Z/`.
- Phase H ✅ complete (Attempt #10 — `reports/2026-01-test-suite-triage/phase_h/20251011T033418Z/` captured full-suite rerun, 36 failures remaining, gradient checks stable).
- Phase I ✅ complete (Attempt #11 — `reports/2026-01-test-suite-triage/phase_i/20251011T042127Z/` delivers triage_summary.md + classification_overview.md with 36 failures classified; fix_plan updated accordingly).
- Phase J ✅ tracker maintained — `remediation_tracker.md` and `remediation_sequence.md` refreshed (Attempt #16) with determinism clusters cleared; Phase D4 closure appended C3 ✅ resolved and Sprint 1 progress advanced to 30.6% (9/17 failures retired).
- Phase K ✅ complete — Attempt #15 (rerun) + Attempt #16 (analysis + tracker) delivered the 512/31/143 baseline; Attempt #19 Phase D closure now recorded in `analysis/summary.md`, yielding the current 516 passed / 27 failed / 143 skipped snapshot.
- Phase L ✅ complete (Attempt #17 — `reports/2026-01-test-suite-triage/phase_l/20251011T104618Z/detector_config/`); targeted detector-config rerun captured, failure brief authored, ledger pending tracker sync with `[DETECTOR-CONFIG-001]` remediation.
- Phase M0 ✅ complete — Attempt #21 (20251011T153931Z) executed the chunked rerun: 504 passed / 46 failed / 136 skipped, triage_summary.md refreshed with nine active clusters (C1–C9) and new quick-win priorities.
- Phase M1 🔄 in progress — Sprint 0 clusters C1/C3/C4/C5/C7 are all closed (Attempts #21/#22/#25/#26/#27). Pending follow-up: M1f ledger/tracker refresh and Phase M2 gradient guard bring-down before resuming MOSFLM remediation.
- Phase M ⏳ pending — retains post-remediation validation gate once MOSFLM offset fix lands (dependent on `[DETECTOR-CONFIG-001]` Phase C1–C3 completion and targeted retest).

### Phase A — Preflight & Inventory
Goal: Confirm environment readiness and enumerate suite metadata so the full run is reproducible and guarded.
Prereqs: None; execute prior to any full-suite invocation.
Exit Criteria: Preflight checklist logged in `reports/2026-01-test-suite-triage/phase_a/<STAMP>/preflight.md` with env summary, disk budget, and test inventory snapshot.

| ID | Task Description | State | How/Why & Guidance (including API / document / artifact / source file references) |
| --- | --- | --- | --- |
| A1 | Confirm guardrails & env | [D] | Attempt #1 → `preflight.md` records Python 3.13, PyTorch 2.7.1+cu126, CUDA 12.6 availability; referenced `docs/development/testing_strategy.md` §§1.4–1.5. |
| A2 | Disk & cache sanity check | [D] | Attempt #1 → `disk_usage.txt` shows 77 GB free (83 % used); cleanup not required. |
| A3 | Test inventory snapshot | [D] | Attempt #1 → `collect_only.log` captured 692 collected tests, 0 errors; summarised inside `preflight.md`. |
| A4 | Update fix_plan attempts ledger | [D] | Attempt #1 logged in `docs/fix_plan.md` under `[TEST-SUITE-TRIAGE-001]` with artifact paths and counts. |

### Phase B — Full Suite Execution & Logging
Goal: Execute `pytest tests/` once, capturing complete logs, timings, and failure summaries for downstream triage.
Prereqs: Phase A checklist complete (A1–A4).
Exit Criteria: Full run log + junit/xml archived under `reports/2026-01-test-suite-triage/phase_b/<STAMP>/`; failure summary extracted into `failures_raw.md`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Prepare reporting directory | [D] | Attempt #2 → Created `reports/2026-01-test-suite-triage/phase_b/20251010T132406Z/` with `logs/`, `artifacts/`. Documented command in `commands.txt`. |
| B2 | Execute full test suite | [D] | Attempt #5 → ✅ Completed with extended timeout (`reports/2026-01-test-suite-triage/phase_b/20251010T135833Z/`). Runtime 1864.76 s, 50 failures recorded, junit XML archived. Prior timeout resolved. |
| B3 | Extract failure list | [D] | Attempt #2 → Extracted 34 failures into `failures_raw.md`. Categorized by test area (determinism, sourcefile, grazing, detector, debug, CLI). Noted 172 tests not reached (25% coverage gap). |
| B4 | Update fix_plan attempt entry | [D] | Attempt #2 → Updated `docs/fix_plan.md` [TEST-SUITE-TRIAGE-001] with runtime=600s, failures=34 (partial), artifact path, and recommendations for split execution. |

### Phase C — Failure Classification & Triage Ledger
Goal: Categorise failures into implementation bugs vs deprecated/obsolete tests and map them to remediation owners or follow-up plans.
Prereqs: Phase B artifacts ready (Attempt #5 bundle).
Exit Criteria: Updated `triage_summary.md` covering the full 50-failure dataset, plus refreshed fix_plan mappings and pending-actions table referencing the new artifact timestamp.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Create triage worksheet | [D] | Attempt #3 → `reports/2026-01-test-suite-triage/phase_c/20251010T134156Z/triage_summary.md` captures classification table + context for the partial run. |
| C2 | Determine category for each failure | [D] | Attempt #3 → All 34 observed failures classified as implementation bugs (triage summary §Classification Table). Remaining tests flagged pending rerun. |
| C3 | Align with fix_plan | [D] | Attempt #4 → Mapped initial clusters to fix-plan entries (`[CLI-DEFAULTS-001]`, `[DETERMINISM-001]`, etc.). |
| C4 | Capture blockers & next steps | [D] | Attempt #4 → "Pending Actions" section added to `triage_summary.md` with cluster→fix-plan mapping + coverage gap callout. |
| C5 | Harvest Attempt #5 failure set | [D] | Attempt #6 → Created `reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/` and ingested `failures_raw.md`, summary, and commands from Attempt #5 (50 failures, 18 clusters). Artifacts: `{triage_summary.md,pending_actions.md,failures_raw.md}`. |
| C6 | Extend classification to full dataset | [D] | Attempt #6 → Authored refreshed `triage_summary.md` covering all 50 failures across 18 clusters (C1-C18), highlighting deltas vs Attempt #2/Attempt #4 (34 failures → 50 failures; +16 new). Detailed cluster→fix-plan mappings, priority sequences (P1-P4), and reproduction commands included. |
| C7 | Refresh fix_plan & plan linkages | [D] | Attempt #6 → Updated `pending_actions.md` with 8 new fix-plan IDs requiring creation plus status table for all 18 clusters. Plan tables (this file) refreshed to reference 20251010T135833Z timestamp. Ready for Phase D handoff. |

### Phase D — Remediation Roadmap Handoff
Goal: Produce a ready-to-execute backlog for Ralph (or subagents) to address failing tests without ambiguity.
Prereqs: Phase C checklist complete.
Exit Criteria: `handoff.md` summarising priority order, owners, and verifying commands; input.md instructions referencing highest-priority failure fix.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Synthesize remediation priorities | [D] | Documented in `reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/triage_summary.md` (Priority 1–4 ladders with spec cites). |
| D2 | Produce reproduction commands | [D] | Each cluster section in `triage_summary.md` records authoritative pytest selectors + env notes. |
| D3 | Update documentation touchpoints | [D] | Completed: `docs/fix_plan.md` refreshed with new IDs + handoff link, plan synced, `reports/2026-01-test-suite-triage/phase_d/20260113T000000Z/handoff.md` published. |
| D4 | Publish supervisor input template | [D] | ✅ 2026-01-13 — `input.md` updated with Parity-mode guidance targeting `[CLI-DEFAULTS-001]` (default_F fallback fix). |

### Phase E — Full Suite Refresh (2026 Re-run)
Goal: Capture an up-to-date end-to-end `pytest tests/` run so the failure ledger reflects current HEAD behaviour before remediation resumes.
Prereqs: Re-read `docs/development/testing_strategy.md` §§1.4–1.5, confirm `KMP_DUPLICATE_LIB_OK=TRUE` and CUDA availability, ensure ≥40 GB free disk for logs/JUnit.
Exit Criteria: New Attempt logged with full-suite runtime ≤3600 s, artifacts stored under `reports/2026-01-test-suite-triage/phase_e/<STAMP>/`, and `docs/fix_plan.md` updated with refreshed pass/fail counts and failure cluster mapping.

| ID | Task Description | State | How/Why & Guidance (including API / document / artifact / source file references) |
| --- | --- | --- | --- |
| E1 | Refresh preflight snapshot | [D] | Attempt #7 reused Phase A env snapshot; `collect_only.log` + `env.txt` captured under `reports/2026-01-test-suite-triage/phase_e/20251010T180102Z/`. |
| E2 | Execute full test suite | [D] | Attempt #7 — `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_e/20251010T180102Z/artifacts/pytest_full.xml`; runtime 1860.74 s, 49 failures logged. |
| E3 | Summarise 2026 results | [D] | Attempt #7 — `summary.md` + `failures_raw.{md,txt}` compare against Phase B Attempt #5; documented net delta (+1 pass, −1 failure). |
| E4 | Update ledgers | [D] | Attempt #7 — `docs/fix_plan.md` updated with refreshed counts and artifact paths (Attempt entry dated 2025‑10‑10). |

### Phase F — Failure Classification Refresh
Goal: Reclassify the refreshed failure set into implementation bugs vs deprecated tests and update downstream fix-plan item statuses.
Prereqs: Phase E artifacts ready (logs, summary, failures_raw); consult `reports/2026-01-test-suite-triage/phase_c/20251010T135833Z/triage_summary.md` for prior cluster definitions.
Exit Criteria: Updated `triage_summary.md` and `pending_actions.md` covering the 2026 run, plus synced `docs/fix_plan.md` links for any new or resolved clusters.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| F1 | Extend triage worksheet | [D] | Create `reports/2026-01-test-suite-triage/phase_f/<STAMP>/triage_summary.md`. Start from Phase C table, flag the cleared CLI defaults cluster, and annotate each of the 49 remaining nodes using `phase_e/20251010T180102Z/failures_raw.md` + `logs/pytest_full.log`. |
| F2 | Map failures to fix-plan IDs | [D] | Update `triage_summary.md` ownership columns + produce `cluster_deltas.md` noting count changes (e.g., C1 resolved). Ensure every failure maps to an existing or new fix-plan item; raise TODOs for missing entries. |
| F3 | Record pending actions table | [D] | Publish `reports/2026-01-test-suite-triage/phase_f/<STAMP>/pending_actions.md` with owner, priority, reproduction command, and artifact expectations per cluster; cross-link in `docs/fix_plan.md` and `galph_memory.md`. |

### Phase G — Remediation Coordination
Goal: Ensure remediation handoffs (determinism, CLI flags, dtype neutrality, etc.) remain prioritised in line with the refreshed failure ordering.
Prereqs: Phase F triage complete.
Exit Criteria: `handoff.md` appendix updated with 2026 priority ladder and supervisor input template refreshed for the leading remediation target.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| G1 | Update remediation ladder | [D] | Attempt #9 → Published Phase G addendum (`reports/2026-01-test-suite-triage/phase_g/20251011T030546Z/handoff_addendum.md`) superseding the Phase D ladder with status-aware priorities. |
| G2 | Sync supervisor playbook | [D] | Attempt #9 → `input.md` and galph_memory baton updated to reference the Phase G addendum and delegate `[DTYPE-NEUTRAL-001]` Phase E validation. |

### Phase H — 2026 Suite Relaunch
Goal: Execute a fresh `pytest tests/` run at current HEAD, capturing complete artifacts to supersede the October 2025 attempt and align with the 2026-01-17 supervisor directive.
Prereqs: Reconfirm Phase A guardrails (env sanity, disk space), pause downstream remediation per directive, ensure ≥60 GB free for duplicated logs/JUnit bundles.
Exit Criteria: `reports/2026-01-test-suite-triage/phase_h/<STAMP>/` contains env snapshot, full-suite log, junit XML, slowest-test table, and attempt metadata; `docs/fix_plan.md` logs Attempt #10 with refreshed pass/fail counts and artifact links.

| ID | Task Description | State | How/Why & Guidance (including API / document / artifact / source file references) |
| --- | --- | --- | --- |
| H1 | Stage timestamped workspace | [D] | `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` then `mkdir -p reports/2026-01-test-suite-triage/phase_h/${STAMP}/{collect_only,full_suite,artifacts,docs}`; capture commands in `commands.txt`. |
| H2 | Capture preflight snapshot | [D] | Optional: `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q | tee .../collect_only/pytest.log`; record env metadata (`python -V`, `pip list | grep torch`, `nvidia-smi`) into `.../collect_only/env.json`. |
| H3 | Run authoritative full suite | [D] | `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_h/${STAMP}/artifacts/pytest_full.xml | tee .../full_suite/pytest_full.log`; note exit code and runtime in `commands.txt`. |
| H4 | Summarise metrics | [D] | Draft `.../docs/summary.md` with runtime, pass/fail/skip counts, delta vs 20251010T180102Z, and top-25 duration table. |
| H5 | Update fix-plan attempt ledger | [D] | Add Attempt #10 under `[TEST-SUITE-TRIAGE-001]` with counts + artifact paths; cite Phase H tasks and new summary doc. |

### Phase I — Failure Classification Refresh
Goal: Reclassify Phase H failures, distinguishing implementation bugs from deprecation candidates, and refresh cluster mapping + ownership.
Prereqs: Phase H artifacts complete (summary, junit, logs); gather prior classifications (`reports/2026-01-test-suite-triage/phase_f/20251010T184326Z/`).
Exit Criteria: `reports/2026-01-test-suite-triage/phase_i/<STAMP>/` hosts updated cluster table, bug/deprecation rationale, and selector mapping; `docs/fix_plan.md` reflects refreshed classification and any new/remediated clusters.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| I1 | Build comparative failure table | [D] | Clone Phase F `triage_summary.md` template to `phase_i/${STAMP}/triage_summary.md`; parse Phase H junit/log to populate counts, mark deltas, and flag suspected deprecations. |
| I2 | Classify failure causes | [D] | For each failure annotate `Implementation Bug`, `Likely Deprecation`, or `Needs Verification`; cite supporting evidence (spec sections, doc notes) in an appended rationale column and summarise tallies in `classification_overview.md`. |
| I3 | Sync ledger + baton | [D] | Update `docs/fix_plan.md` Next Actions/Attempts with Phase I findings and add galph_memory note linking to the new artifacts and classification decisions. |

### Phase J — Remediation Launch & Tracking
Goal: Translate refreshed failure inventory into an actionable remediation roadmap and sequencing across fix-plan items.
Prereqs: Phase I classification complete; confirm dependent plans (`determinism.md`, `vectorization-parity-regression.md`, etc.) incorporate latest blocking signals.
Exit Criteria: `reports/2026-01-test-suite-triage/phase_j/<STAMP>/remediation_tracker.md` enumerates each active cluster with owner, fix-plan ID, reproduction command, and exit criteria; fix-plan items reference the tracker for execution order.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| J1 | Draft remediation tracker | [D] | Author `remediation_tracker.md` listing per-cluster owner, fix-plan ID, reproduction selector, blocking dependencies, and deliverable expectations (logs, doc updates, code patches). |
| J2 | Define execution sequence | [D] | Attempt #12 → `remediation_sequence.md` authored with 4-sprint roadmap (Pre-Sprint → Sprint 1 P1 [17 failures] → Sprint 2 P2 [9] → Sprint 3 P3 [5] → Sprint 4 P4 [5]), gating tests, success metrics (36→0 failures), parallel work opportunities. |
| J3 | Update fix_plan dependencies | [D] | Attempt #12 → `docs/fix_plan.md` Next Actions updated with Pre-Sprint blocker verification + Sprint 1 guidance; Attempt #12 entry logged with artifact paths and sequence highlights. |

### Phase K — 2026 Full-Suite Refresh
Goal: Capture a fresh `pytest tests/` run and recalibrate failure classification before restarting Sprint 1 remediation.
Prereqs: Phase J tracker current; confirm runtime checklist via Phase A artifacts; ensure disk budget for new artifacts.
Exit Criteria: Phase K directory populated with logs + junit XML + env snapshot; updated classification + tracker synced to fix plan; Attempt #15 recorded.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| K1 | Execute full suite (Phase K) | [D] | Attempt #15 (20251011T072940Z) captured the rerun with `timeout 3600`; artifacts include `logs/pytest_full.log`, `artifacts/pytest_full.xml`, `env/torch_env.txt`, and `summary.md`. |
| K2 | Refresh classification | [D] | Attempt #16 → `analysis/{triage_summary.md,classification_overview.md,summary.md}` reconciled Phase K failures with Phase I baseline (31 failures across 14 clusters; C1/C2/C15 resolved, C3 improved). |
| K3 | Sync tracker + ledger | [D] | Updated `remediation_tracker.md` (C2/C15 marked ✅ RESOLVED, C3 updated 6→4 with "⬇️ IMPROVED" flag + Phase K notes, Executive Summary refreshed: 36→31 failures / 16→14 clusters) and `remediation_sequence.md` (Sprint 1.1 marked ✅ COMPLETE with artifacts/validation, Sprint 1 progress table updated: 17.6% complete / 3/17 resolved / 31 remaining). Logged K3 tracker updates in `docs/fix_plan.md` Attempt #16 entry. |

### Phase L — Sprint 1.3 Launch (Detector Config)
Goal: Kick off Sprint 1.3 by refreshing detector configuration failure evidence and preparing the implementation backlog for `[DETECTOR-CONFIG-001]`.
Prereqs: Phase J tracker + sequence reflect C3 closure (27 failures baseline); `[SOURCE-WEIGHT-002]` marked done; authoritative reproduction command confirmed from `phase_k/triage_summary.md` lines 181-189.
Exit Criteria: Targeted detector-config rerun archived under `reports/2026-01-test-suite-triage/phase_l/<STAMP>/detector_config/`; failure brief summarises spec deltas; fix plan + tracker updated with Phase L attempt metadata so implementation delegation can start.

| ID | Task Description | State | How/Why & Guidance (including API / document / artifact / source file references) |
| --- | --- | --- | --- |
| L1 | Capture detector-config targeted run | [D] | Attempt #17 (20251011T104618Z) executed `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py --maxfail=0`; artifacts stored under `reports/2026-01-test-suite-triage/phase_l/20251011T104618Z/detector_config/` with `commands.txt`, env snapshot, and junit XML. |
| L2 | Draft detector-config failure brief | [D] | Attempt #17 produced `analysis.md` citing `specs/spec-a-core.md` §4 and `arch.md` §ADR-03; documents MOSFLM +0.5 pixel gap blocking `[DETECTOR-CONFIG-001]`. |
| L3 | Sync ledger + tracker | [P] | Fix plan `[TEST-SUITE-TRIAGE-001]` updated (Attempt #17). `remediation_tracker.md` still needs Phase L attempt row once `[DETECTOR-CONFIG-001]` remediation closes — leave open until post-fix validation. |

### Phase M0 — Directive Compliance Baseline
Goal: Honour the 2026-01-20 directive by capturing a fresh full-suite baseline (pre-MOSFLM remediation) and re-triaging failures so downstream fixes can be prioritised.
Prereqs: Phase L artifacts acknowledged; environment guardrails per `docs/development/testing_strategy.md` §§1.4–1.5 and `docs/development/pytorch_runtime_checklist.md` item 1 satisfied; confirm latest `pip install -e .` still valid.
Exit Criteria: Full-suite rerun artifacts archived under `reports/2026-01-test-suite-triage/phase_m0/<STAMP>/`; triage summary + fix_plan ledger updated with Attempt metadata and refined failure classification (implementation bug vs deprecation candidate).

| ID | Task Description | State | How/Why & Guidance (including API / document / artifact / source file references) |
| --- | --- | --- | --- |
| M0a | Refresh pre-run environment checklist | [D] | Attempt #21 → `reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/preflight/{collect_only.log,env.txt,pip_freeze.txt}` captured collect-only (687 tests) and env snapshot per `docs/development/testing_strategy.md` §1. |
| M0b | Execute chunked suite rerun | [D] | Attempt #21 executed all ten chunk commands (`commands.txt` + `chunks/chunk_##/pytest.{log,xml}`) with `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE`; total runtime ~502 s, exit codes logged beside each chunk. |
| M0c | Re-triage and classify failures | [D] | Attempt #21 authored `triage_summary.md` + `summary.md` under `phase_m0/20251011T153931Z/`, classifying 46 failures across clusters C1–C9 and syncing results into `docs/fix_plan.md` Attempt log (pending tracker refresh). |

**Runtime guard note (2026-01-21):** Retain the chunked-command workflow for any re-runs (hard 360 s CLI cap). Export `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` once per attempt, pre-create `.../phase_m0/$STAMP/chunks/`, and keep environment assignments on the same line as each pytest invocation to avoid `/bin/bash: CUDA_VISIBLE_DEVICES=-1: command not found` errors. The historical command list below remains authoritative for future baselines.

Chunk 01 (11 files): `tests/test_at_abs_001.py tests/test_at_cli_009.py tests/test_at_io_002.py tests/test_at_parallel_007.py tests/test_at_parallel_017.py tests/test_at_parallel_028.py tests/test_at_pol_001.py tests/test_at_src_002.py tests/test_cli_scaling.py tests/test_detector_pivots.py tests/test_physics.py`

Chunk 02 (11 files): `tests/test_at_bkg_001.py tests/test_at_crystal_absolute.py tests/test_at_io_003.py tests/test_at_parallel_008.py tests/test_at_parallel_018.py tests/test_at_parallel_029.py tests/test_at_pre_001.py tests/test_at_src_003.py tests/test_cli_scaling_phi0.py tests/test_divergence_culling.py tests/test_pivot_mode_selection.py`

Chunk 03 (11 files): `tests/test_at_cli_001.py tests/test_at_flu_001.py tests/test_at_io_004.py tests/test_at_parallel_009.py tests/test_at_parallel_020.py tests/test_at_perf_001.py tests/test_at_pre_002.py tests/test_at_sta_001.py tests/test_configuration_consistency.py tests/test_gradients.py tests/test_show_config.py`

Chunk 04 (11 files): `tests/test_at_cli_002.py tests/test_at_geo_001.py tests/test_at_noise_001.py tests/test_at_parallel_010.py tests/test_at_parallel_021.py tests/test_at_perf_002.py tests/test_at_roi_001.py tests/test_at_str_001.py tests/test_crystal_geometry.py tests/test_mosflm_matrix.py tests/test_suite.py`

Chunk 05 (11 files): `tests/test_at_cli_003.py tests/test_at_geo_002.py tests/test_at_parallel_001.py tests/test_at_parallel_011.py tests/test_at_parallel_022.py tests/test_at_perf_003.py tests/test_at_sam_001.py tests/test_at_str_002.py tests/test_custom_vectors.py tests/test_multi_source_integration.py tests/test_trace_pixel.py`

Chunk 06 (11 files): `tests/test_at_cli_004.py tests/test_at_geo_003.py tests/test_at_parallel_002.py tests/test_at_parallel_012.py tests/test_at_parallel_023.py tests/test_at_perf_004.py tests/test_at_sam_002.py tests/test_at_str_003.py tests/test_debug_trace.py tests/test_oversample_autoselect.py tests/test_tricubic_vectorized.py`

Chunk 07 (11 files): `tests/test_at_cli_005.py tests/test_at_geo_004.py tests/test_at_parallel_003.py tests/test_at_parallel_013.py tests/test_at_parallel_024.py tests/test_at_perf_005.py tests/test_at_sam_003.py tests/test_at_str_004.py tests/test_detector_basis_vectors.py tests/test_parity_coverage_lint.py tests/test_units.py`

Chunk 08 (10 files): `tests/test_at_cli_006.py tests/test_at_geo_005.py tests/test_at_parallel_004.py tests/test_at_parallel_014.py tests/test_at_parallel_025.py tests/test_at_perf_006.py tests/test_at_src_001.py tests/test_at_tools_001.py tests/test_detector_config.py tests/test_parity_matrix.py`

Chunk 09 (10 files): `tests/test_at_cli_007.py tests/test_at_geo_006.py tests/test_at_parallel_005.py tests/test_at_parallel_015.py tests/test_at_parallel_026.py tests/test_at_perf_007.py tests/test_at_src_001_cli.py tests/test_beam_center_offset.py tests/test_detector_conventions.py tests/test_perf_pytorch_005_cudagraphs.py`

Chunk 10 (10 files): `tests/test_at_cli_008.py tests/test_at_io_001.py tests/test_at_parallel_006.py tests/test_at_parallel_016.py tests/test_at_parallel_027.py tests/test_at_perf_008.py tests/test_at_src_001_simple.py tests/test_cli_flags.py tests/test_detector_geometry.py tests/test_perf_pytorch_006.py`

### Phase M1 — Sprint 0 Quick Fixes (C1, C3, C4, C5, C7)
Goal: Execute the Phase M0 priority ladder (Sprint 0) to retire 31 of 46 failures by addressing low-effort clusters owned by Ralph before gradient and MOSFLM work proceeds.
Prereqs: Phase M0 artifacts (`reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/`) reviewed; implementation handoffs for `[CLI-TEST-SETUP-001]`, `[DETECTOR-DTYPE-CONVERSION-001]`, `[DEBUG-TRACE-SCOPE-001]`, `[SIMULATOR-API-KWARGS-001]`, `[SIMULATOR-DETECTOR-REQUIRED-001]` acknowledged.
Exit Criteria: Targeted pytest selectors for C1/C3/C4/C5/C7 pass on CPU (and CUDA where applicable), ledger + tracker updated with Attempt IDs, and a consolidated summary captured under `reports/2026-01-test-suite-triage/phase_m1/<STAMP>/summary.md`.

| ID | Task Description | State | How/Why & Guidance (including API / document / artifact / source file references) |
| --- | --- | --- | --- |
| M1a | Harden CLI fixtures (Cluster C1) | [D] | Attempt #21 (`reports/2026-01-test-suite-triage/phase_m1/20251011T160713Z/cli_fixtures/`) added `-default_F 100` to 18 fixtures across `tests/test_cli_flags.py` and `tests/test_cli_scaling.py`; targeted selector now passes. |
| M1b | Tensorize detector beam centers (Cluster C3) | [D] | Attempt #22 (`reports/2026-01-test-suite-triage/phase_m1/20251011T162027Z/detector_dtype/notes.md`) updated `Detector.to()` to handle scalar beam centers; selector `pytest -v tests/test_suite.py::TestTier1TranslationCorrectness::test_sensitivity_to_cell_params` now passes and five C3 failures cleared. |
| M1c | Guard debug trace pre-polar accumulator (Cluster C4) | [D] | Attempt #25 (`reports/2026-01-test-suite-triage/phase_m1/20251011T164229Z/debug_trace/`) initialised `I_before_normalization_pre_polar` in both oversample branches and added the required "Final intensity"/"Position" summary lines. Selector `pytest -v tests/test_debug_trace.py` now passes; future regressions should capture before/after logs beside the new bundle. |
| M1d | Align simulator API usage (Cluster C5) | [D] | Attempt #26 (`reports/2026-01-test-suite-triage/phase_m1/20251011T165255Z/simulator_api/`) refreshed the CUDA graphs fixtures to instantiate `Simulator(crystal, detector, ...)` with positional arguments and captured before/after pytest logs. Module rerun now passes (3 passed, 3 skipped). |
| M1e | Provide detectors for lattice-shape tests (Cluster C7) | [D] | Attempt #27 (`reports/2026-01-test-suite-triage/phase_m1/20251011T170539Z/shape_models/summary.md`) added Detector instantiation in `tests/test_at_str_003.py`; targeted selector + module rerun now pass (7 tests). |
| M1f | Ledger + tracker update | [D] | Attempt #28 (20251011T171454Z) captured Sprint 0 closure in `phase_m1/20251011T171454Z/summary.md` (11 failures remain, 76% reduction), authored Phase M2 strategy brief (`phase_m2/20251011T171454Z/strategy.md`), and refreshed `remediation_tracker.md` Executive Summary + Tracker Table. Phase M2 now ready for delegation per strategy.md lines 127-145. |

### Phase M2 — Gradient Infrastructure Gate (Cluster C2)
Goal: Stabilise gradcheck coverage by resolving the donated-buffer compile constraint so gradient suites can run without manual intervention.
Prereqs: Phase M1 quick fixes merged; gradient owner (Ralph or designated specialist) available; consult `triage_summary.md:59`–`89` and `arch.md` §15.
Exit Criteria: Gradient selectors pass with `NANOBRAGG_DISABLE_COMPILE=1`, documentation updated with compile guard, and artifacts captured under `reports/2026-01-test-suite-triage/phase_m2/<STAMP>/`.

| ID | Task Description | State | How/Why & Guidance (including API / document / artifact / source file references) |
| --- | --- | --- | --- |
| M2a | Draft guardrail strategy | [ ] | Outline proposed compile-disable approach referencing `arch.md` §15 and `docs/development/pytorch_runtime_checklist.md`. Record rationale in `phase_m2/$STAMP/strategy.md`. |
| M2b | Implement/diff guard | [ ] | Apply minimal changes (likely `torch._dynamo.disable()` context or env flag) covering `tests/test_gradients.py` cases. Selector: `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py -k "gradcheck"`. |
| M2c | Cross-device sanity (if CUDA available) | [ ] | Repeat key gradcheck on GPU per testing strategy §1.4; stash logs under `phase_m2/$STAMP/gradients_gpu/`. |
| M2d | Documentation + ledger sync | [ ] | Update `[VECTOR-PARITY-001]` / `[TEST-SUITE-TRIAGE-001]` entries with compile guard instructions; file `phase_m2/$STAMP/summary.md` capturing pass counts (expected +10). |

### Phase M3 — Specialist Follow-Through (C6, C8, C9)
Goal: Stage remaining clusters for their owning initiatives so Phase M (post-fix validation) unblocks once MOSFLM and physics investigations complete.
Prereqs: Phase M1 + M2 closed; coordinate with `[DETECTOR-CONFIG-001]`, `[VECTOR-GAPS-002]`, and `[VECTOR-PARITY-001]` owners.
Exit Criteria: Each cluster mapped to its canonical plan with up-to-date status; interim reproduction commands verified.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| M3a | Sync MOSFLM remediation (C6) | [ ] | Ensure `plans/active/detector-config.md` Phase B/C incorporate Phase M0 findings (`triage_summary.md:186`–`214`). Capture targeted pytest log refresh if parameters drift. |
| M3b | Assign detector orthogonality owner (C8) | [ ] | Coordinate with geometry specialist; record scope in `phase_m3/$STAMP/detector_ortho/notes.md`. Selector: `pytest -v tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_detector_tilts`. |
| M3c | Scope mixed-units zero intensity (C9) | [ ] | Promote to `[VECTOR-PARITY-001]` Tap backlog; add callchain requirement referencing `triage_summary.md:277`–`303`. Store hypotheses in `phase_m3/$STAMP/mixed_units/hypotheses.md`. |

### Exit Criteria (Plan Completion)
- Phases A–K marked `[D]` once delivered (Phase H–K added for 2026 rerun, classification refresh, and remediation sequencing).
- Phase M0 artifacts archived with failure count +46 and Sprint ladder documented.
- Phase M1 + Phase M2 deliver expected failure reductions (≤15 failures remaining) with evidence bundles under `phase_m1/` and `phase_m2/`.
- All artifacts stored under `reports/2026-01-test-suite-triage/` with timestamped folders and referenced in `docs/fix_plan.md`.
- `triage_summary.md` (Phase I) identifies categories for every failing test and maps each to a next action (bug fix, test removal request, infrastructure follow-up).
- `handoff addendum` plus Phase J tracker are approved (by supervisor) and actively steering remediation; once backlog execution is underway, archive this plan.

### Phase M — Post-Fix Validation & Suite Refresh
Goal: Confirm detector-config remediation clears C8 and refresh overall failure counts before the next sprint.
Prereqs: Phase M1 + Phase M2 closed; `[DETECTOR-CONFIG-001]` Phase C1–C3 complete; targeted detector-config pytest passes locally.
Exit Criteria: Phase M directory contains targeted + full-suite rerun artifacts, fix plan/tracker synced with updated failure counts.

| ID | Task Description | State | How/Why & Guidance (including API / document / artifact / source file references) |
| --- | --- | --- | --- |
| M1 | Retest detector-config after fix | [ ] | Once MOSFLM offset patch merges, rerun `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py --maxfail=0`; archive under `reports/2026-01-test-suite-triage/phase_m/<STAMP>/detector_config/` with diff vs Attempt #17. |
| M2 | Full-suite validation sweep | [ ] | Execute `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_m/<STAMP>/artifacts/pytest_full.xml`; ensure runtime guardrails per testing_strategy §§1.4–1.5. |
| M3 | Tracker + ledger sync | [ ] | Update `[TEST-SUITE-TRIAGE-001]`, `[DETECTOR-CONFIG-001]`, and `remediation_tracker.md` with new pass/fail counts; note residual failing clusters for Sprint 1.4 planning. |

### Metrics & Reporting Guidelines
- Capture total runtime, pass/fail counts, and slowest tests (top 25) from `--durations=25` output.
- For each failure category, note whether GPU/CPU impact differs (device neutrality check).
- Maintain Attempt numbering continuity in `docs/fix_plan.md`; include `pytest` exit code and timestamp.

### Risks & Mitigations
- **Long runtime / timeouts:** If the full suite exceeds loop budget, split run via `pytest tests/test_*pattern*.py`; document split and recombine results in `triage_summary.md`.
- **Environment drift:** Re-run Phase A if dependencies change (new torch version, GPU availability changes).
- **Protected Assets:** Ensure `docs/index.md` references (`loop.sh`, `input.md`) remain untouched; do not delete artifacts listed there during cleanup.
- **Flaky tests:** Mark with `Needs Reproduction` status; capture rerun commands and conditions.

### References
- `docs/development/testing_strategy.md`
- `docs/architecture/pytorch_design.md`
- `specs/spec-a-core.md`
- `docs/fix_plan.md`
- `reports/` index for previous pytest attempts (search `reports/*pytest_full.log`)
