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
| H1 | Capture env snapshot + NB_C_BIN resolution | [ ] | `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; mkdir `reports/2026-01-test-suite-refresh/phase_h/$STAMP/{env,checks}`. Record `printenv NB_C_BIN` and fallbacks (`./golden_suite_generator/nanoBragg`, `./nanoBragg`). Cross-reference `docs/development/c_to_pytorch_config_map.md` NB_C_BIN precedence notes. |
| H2 | Validate C binary executability | [ ] | `NB_C_BIN=${NB_C_BIN:-./golden_suite_generator/nanoBragg}`; run `stat` + `ls -l` + `sha256sum` into `checks/c_binary.txt`. Execute `timeout 10 $NB_C_BIN -help > checks/c_binary_help.txt 2>&1`; failure indicates rebuild or PATH fix needed. |
| H3 | Verify golden asset availability | [ ] | Confirm `scaled.hkl` and `reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json` exist and match recorded hashes (see `reports/2025-10-cli-flags/phase_h/implementation/sha256.txt`). Store results in `checks/golden_assets.txt`. |
| H4 | Document pytest fixture strategy | [ ] | Draft `analysis/infrastructure_gate.md` describing proposed `conftest.py` fixture that asserts NB_C_BIN and asset readiness during collection. Cite `plans/active/cli-noise-pix0/plan.md` for asset provenance and `docs/development/testing_strategy.md` §1.5 for Do Now expectations. |

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

## Exit & Handoff
- Phase H completion is required before revisiting any cluster-specific remediation to avoid repeating transient "fixes".
- Once Phases H–J are complete, rerun the full suite (Phase K, to be scoped later) only after fixtures/timeouts are merged into the branch.
- Update `docs/fix_plan.md` Attempts History after each phase with STAMP references and artifacts, and refresh Next Actions accordingly.
- Reference this plan from `docs/fix_plan.md` `[TEST-SUITE-TRIAGE-002]` section so future loops locate it quickly.
