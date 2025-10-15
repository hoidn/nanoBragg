## Context
- Initiative: [TEST-SUITE-TRIAGE-002] — Full pytest rerun and remediation refresh after Phase G evidence confirmed eight persistent failure clusters.
- Phase Goal: Translate the 20251015T163131Z Phase G baseline into actionable remediation guardrails before scheduling the next full-suite run. Focus on eliminating infrastructure regressions (C binary, golden assets) and stabilising the slow-gradient timeout pathway.
- Dependencies:
  - `docs/development/testing_strategy.md` §§1.4–2 for environment guards, slow-gradient timeout policy, and authoritative commands.
  - `arch.md` §2 (runtime layout) and §15 (gradient expectations) for device/dtype neutrality and timeout tolerances.
  - `docs/development/pytorch_runtime_checklist.md` §§2–5 for preflight environment checks and compile guards.
  - `reports/2026-01-test-suite-refresh/phase_g/20251015T163131Z/analysis/summary.md` for the latest failure breakdown.
  - `docs/fix_plan.md` — `[TEST-SUITE-TRIAGE-002]` Attempts History + Next Actions alignment.

### Phase H — Infrastructure Gate (C binary & golden assets)
Goal: Prove the test harness can resolve the nanoBragg C binaries and golden CLI assets *within* the pytest runtime environment before any physics tests execute.
Prereqs: Phase G artifacts available; no outstanding git conflicts; editable install up to date.
Exit Criteria: A STAMPed evidence bundle under `reports/2026-01-test-suite-refresh/phase_h/<STAMP>/` containing NB_C_BIN verification, binary exec check, and golden asset integrity notes, plus fix_plan Attempt logged.

| ID | Task Description | State | How/Why & Guidance (including API / document / artifact / source file references) |
| --- | --- | --- | --- |
| H1 | Capture env snapshot + NB_C_BIN resolution | [D] | ✅ STAMP `20251015T171757Z` bundle recorded under `phase_h/$STAMP/env/`; references `docs/development/c_to_pytorch_config_map.md`. |
| H2 | Validate C binary executability | [D] | ✅ Same STAMP — `checks/c_binary.txt` + `c_binary_help.txt` confirm fallback_golden binary runnable within 10s. |
| H3 | Verify golden asset availability | [D] | ✅ Hashes for `scaled.hkl` and `pix0_expected.json` captured in `checks/golden_assets.txt`; aligns with `reports/2025-10-cli-flags/phase_h/.../sha256.txt`. |
| H4 | Document pytest fixture strategy | [D] | ✅ `analysis/infrastructure_gate.md` authored (Phase H exit packet) outlining NB_C_BIN precedence + asset guard blueprint. |

### Phase I — Gradient Timeout Mitigation Study
Goal: Quantify variance of `test_property_gradient_stability` in isolation and establish the remediation path (timeout uplift vs. dedicated chunk vs. skip criteria).
Prereqs: Phase H evidence bundle complete & logged; gradient test runnable in isolation; `NANOBRAGG_DISABLE_COMPILE=1` guard set.
Exit Criteria: Runtime measurements captured under `reports/2026-01-test-suite-refresh/phase_i/<STAMP>/`, decision memo recommending the timeout/fixture change, and fix_plan Attempt referencing the data.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| I1 | Time isolated gradient test (CPU) | [D] | `/usr/bin/time -v -o analysis/gradient_cpu_time.txt timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest tests/test_gradients.py::test_property_gradient_stability -vv`. Capture pytest log + exit status. **COMPLETE (STAMP 20251015T173309Z):** Runtime 846.13s (6.5% margin below 905s), exit code 0. |
| I2 | Collect system load diagnostics | [D] | During run, record `lscpu`, `cpupower frequency-info` (if available), and `sensors` output into `env/system_load.txt` to diagnose throttling. **COMPLETE:** Captured at `env/system_load.txt`, no throttling detected. |
| I3 | Optional GPU comparison | [SKIP] | If CUDA available, repeat test once with `CUDA_VISIBLE_DEVICES=0` to gauge spread; store outputs in `analysis/gradient_gpu_time.txt`. **DEFERRED:** CPU measurement sufficient; Phase I validates 905s ceiling. |
| I4 | Draft timeout decision memo | [D] | Summarise timings, variance, and recommend either raising timeout (specify value with rationale) or splitting test into guarded chunk. Reference `docs/development/testing_strategy.md` §4.1 and Phase F metrics (`reports/2026-01-test-suite-refresh/phase_f/20251015T160436Z/analysis/summary.md`). **COMPLETE:** Memo at `analysis/timeout_decision.md` recommends ✅ **RETAIN 905s timeout** (no adjustment needed). |

### Phase J — Collection-Time Guard Rails
Goal: Implement and validate pytest-level guards that enforce infrastructure readiness and gradient policy before suite execution resumes.
Prereqs: Approved Phase I timeout decision; stakeholder sign-off (documented in fix_plan) on fixture/API changes.
Exit Criteria: Prototype fixtures/tests committed to feature branch (after implementation loop), dry-run pytest proving guard behavior, and documentation updates queued.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| J1 | Author infrastructure fixture design | [D] | Map fixture scope (`session` recommended) and failure messaging; ensure compatibility with existing `conftest.py`. Reference Phase H analysis and `pytest` docs for `pytest_sessionstart` hooks. **COMPLETE (STAMP 20251015T180301Z):** Authored `analysis/session_fixture_design.md` with complete implementation pseudocode, failure messaging, remediation steps, testing strategy, and 5 open questions for implementation loop. |
| J2 | Draft gradient policy fixture plan | [D] | Outline how to check `NANOBRAGG_DISABLE_COMPILE` and skip/xfail gradient tests when policy unmet. Tie to Phase I memo outcomes. **COMPLETE (STAMP 20251015T180301Z):** Delivered `analysis/gradient_policy_guard.md` with module-scoped fixture design, skip/xfail analysis (recommends skip), environment enforcement logic, integration notes, and 5 open questions. |
| J3 | Validation strategy | [D] | Define targeted pytest selectors to exercise new fixtures (e.g., `pytest -k infrastructure_gate --collect-only`). Plan to capture artifacts under `reports/2026-01-test-suite-refresh/phase_j/<STAMP>/`. **COMPLETE (STAMP 20251015T180301Z):** Created `analysis/validation_plan.md` with 9 targeted validation selectors (V1-V9) covering positive/negative/bypass/integration scenarios, expected artifacts, exit criteria, and summary template. |

### Phase K — Fixture Implementation & Validation
Goal: Turn the Phase J designs into working fixtures, validate them via targeted selectors, and update ledgers so the guarded full-suite rerun can resume without infrastructure regressions.
Prereqs: ✅ Stakeholder sign-off on Phase J deliverables (galph 2025-10-15; resolves Open Questions Q1–Q14 with emphasis on Q14). Ensure editable install remains current; confirm `reports/2026-01-test-suite-refresh/phase_j/20251015T180301Z/` artifacts are accessible.
Exit Criteria: Fixtures committed with validation evidence under `reports/2026-01-test-suite-refresh/phase_k/<STAMP>/`, fix_plan Attempt logged closing Next Action 18, and Phase L rerun gate unblocked.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| K1 | Implement `session_infrastructure_gate` | [D] | ✅ STAMP `20251015T182108Z`: Implemented in `tests/conftest.py` with C binary resolution, executability check, and golden asset validation. Includes `NB_SKIP_INFRA_GATE` bypass. |
| K2 | Implement `gradient_policy_guard` | [D] | ✅ STAMP `20251015T182108Z`: Implemented in `tests/test_gradients.py` as module-scoped autouse fixture. Requires `NANOBRAGG_DISABLE_COMPILE=1`, provides clear skip messages with remediation commands. |
| K3 | Run validation matrix V1–V9 | [D] | ✅ STAMP `20251015T182108Z`: All 9 validation scenarios executed successfully. Logs stored under `reports/2026-01-test-suite-refresh/phase_k/20251015T182108Z/validation/`. Exit codes all 0, behaviors match design expectations. Summary.md created with complete results matrix. |
| K4 | Update docs + ledgers | [D] | ✅ STAMP `20251015T182108Z`: Phase K tasks marked [D], validation summary created, commit prepared with all artifacts. |
| K5 | Prepare Phase L rerun brief | [D] | ✅ Deferred to commit message: Phase L can launch guarded `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/` with fixtures active. Validation bundle proves fixtures work correctly. |

### Phase L — Guarded Full-Suite Rerun
Goal: Validate the new infrastructure and gradient fixtures under a full `pytest tests/` run and capture the authoritative baseline before remediation restarts.
Prereqs: ✅ Phase K fixtures merged & validated (STAMP 20251015T182108Z); NB_C_BIN accessible (per Phase H checks); gradient timeout tolerance + documentation refreshed in Phase Q; repo clean with editable install current.
Exit Criteria: ✅ COMPLETE — Full-suite execution captured under `reports/2026-01-test-suite-refresh/phase_l/20251015T190350Z/` (logs, fixtures, env, summary) and fix_plan Next Action 19 updated with artifact links; focus now shifts to Phase M.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| L1 | Prepare rerun STAMP + brief | [D] | ✅ STAMP `20251015T190350Z` created under `phase_l/20251015T190350Z` (commands.txt + env snapshot) with mkdir/env prep captured. |
| L2 | Execute guarded full suite | [D] | ✅ Full-suite run executed from repo root (runtime 1661.37s, exit code 1) with log tee + junit + `/usr/bin/time -v`; artifacts at `reports/2026-01-test-suite-refresh/phase_l/20251015T190350Z/`. |
| L3 | Capture fixture diagnostics | [D] | ✅ `analysis/fixtures.md` summarises `session_infrastructure_gate` + `gradient_policy_guard` outputs (both PASS, CWD gap noted). |
| L4 | Summarize run vs prior baselines | [D] | ✅ `analysis/summary.md` compares Phase L vs Phase G baselines (identical failure set, +0.28% runtime drift). |
| L5 | Update ledgers & trackers | [D] | ✅ docs/fix_plan.md Attempt #20 recorded; galph_memory + tracker pending Phase M follow-up. |

### Phase M — Failure Synthesis & Remediation Hand-off
Goal: Translate the Phase L failure set into actionable remediation work, aligning clusters and priorities before delegating fixes.
Prereqs: Phase L STAMP `20251015T190350Z` available; remediation tracker bundle (`reports/2026-01-test-suite-triage/phase_j/20251015T043327Z/`) accessible; stakeholders aligned on the approved 905s gradient timeout policy.
Exit Criteria: Classification bundle under `reports/2026-01-test-suite-refresh/phase_m/<STAMP>/` (failures.json, cluster mapping, tracker delta, next-step memo) plus fix_plan Next Action 20 recorded; plan ready to hand off implementation tasks.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| M1 | Parse failure list | [ ] | Extract nodeids/stack traces from `phase_l/20251015T190350Z/logs/pytest_full.log` into `analysis/failures.json` (use `scripts/validation/pytest_failure_parser.py` if available). |
| M2 | Map to clusters & flag regressions | [ ] | Compare vs Phase G triage and remediation tracker; record results in `analysis/cluster_mapping.md` with cluster IDs (e.g., C2, C18) and supporting evidence links. Highlight new or cleared failures. |
| M3 | Refresh remediation tracker | [ ] | Update `reports/2026-01-test-suite-triage/phase_j/20251015T043327Z/remediation_tracker.md` (or add an addendum at `phase_m/$STAMP/tracker_update.md`) with new counts, owners, and statuses. |
| M4 | Publish next-step brief | [ ] | Draft `analysis/next_steps.md` summarizing recommended remediation order, gating requirements, and targeted selectors. Update `docs/fix_plan.md` (Next Action 20) and galph_memory entry with the hand-off. |

## Exit & Handoff
- Phases H–K are complete with evidence bundles stamped 20251015; Phase L (guarded rerun) and Phase M (failure synthesis) are now staged above and represent the next executable gates.
- Launch Phase L only after confirming Phase K artifacts are committed and the rerun brief is prepared; follow immediately with Phase M classification before delegating remediation code loops.
- After each phase, update `docs/fix_plan.md`, the remediation tracker, and galph_memory with STAMP references so the ledger stays aligned.
- Continue referencing this plan from `docs/fix_plan.md` `[TEST-SUITE-TRIAGE-002]` to guide subsequent supervisor and engineer loops.
