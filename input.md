Summary: Land the Phase K guardrail fixtures and prove they work via the V1–V9 validation matrix so we can resume full-suite reruns.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-002] Next Action 18 — Phase K implementation loop
Branch: feature/spec-based-2
Mapped tests: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest --collect-only -q (V1); NB_SKIP_INFRA_GATE=1 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest --collect-only -q (V4); env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py (V9)
Artifacts: reports/2026-01-test-suite-refresh/phase_k/$STAMP/validation/
Do Now: [TEST-SUITE-TRIAGE-002] Next Action 18 — implement fixtures (K1/K2) then run `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest --collect-only -q` (V1) capturing output to `validation/v1_infra_gate_pass.log`.
If Blocked: If fixtures compile but V1 fails unexpectedly, capture `validation/v1_infra_gate_pass.log` and the traceback, then stop and log the issue before touching other validations.
Priorities & Rationale:
- Ensure infrastructure gate fixture matches the approved design so NB_C_BIN/asset regressions fail fast (plans/active/test-suite-triage-phase-h.md:46-57).
- Mirror the gradient policy guard plan so grad tests only run with compile disabled (reports/2026-01-test-suite-refresh/phase_j/20251015T180301Z/analysis/gradient_policy_guard.md:1-120).
- Follow the validation playbook to exercise success + failure paths before resuming full-suite work (reports/2026-01-test-suite-refresh/phase_j/20251015T180301Z/analysis/validation_plan.md:1-200).
- Record evidence under the Phase K STAMP so the ledger and future audits have the artifacts they expect (docs/fix_plan.md:15-18, plans/active/test-suite-triage-phase-h.md:51-57).
How-To Map:
- Set `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and create `reports/2026-01-test-suite-refresh/phase_k/$STAMP/validation` plus `analysis` and `notes` subdirs; tee every command there.
- Implement K1: add `session_infrastructure_gate` to `tests/conftest.py` per the pseudocode (resolve C binary → run `-help` with 10s timeout → check golden assets) and wire an env bypass (`NB_SKIP_INFRA_GATE=1`).
- Implement K2: add the module-scoped `gradient_policy_guard` in `tests/test_gradients.py` (or shared helper) that `pytest.skip`s when `NANOBRAGG_DISABLE_COMPILE != '1'`, with the canonical remediation message.
- Run validation suite sequentially, restoring assets between negatives:
  • V1: `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest --collect-only -q | tee validation/v1_infra_gate_pass.log`.
  • V2: temporarily mv C binaries aside, rerun the same command, capture to `validation/v2_infra_gate_missing_binary.log`, record exit code, then restore binaries.
  • V3: mv `scaled.hkl` aside, rerun command, capture to `validation/v3_infra_gate_missing_asset.log`, record exit code, restore asset.
  • V4: set `NB_SKIP_INFRA_GATE=1` and rerun collect-only to prove bypass; capture to `validation/v4_infra_gate_bypass.log`.
  • V5: run gradient module with env guard satisfied: `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -q tests/test_gradients.py | tee validation/v5_gradients_pass.log`.
  • V6: unset `NANOBRAGG_DISABLE_COMPILE` (or set to 0) and rerun gradient command, capture skip output in `validation/v6_gradients_skip.log` and restore env.
  • V7: set `NANOBRAGG_DISABLE_COMPILE=2` to capture wrong value messaging, log to `validation/v7_gradients_bad_value.log`.
  • V8: rerun `pytest --collect-only -q` with both fixtures active (no bypass) to confirm integration, capture to `validation/v8_integration.log`.
  • V9: full verbose gradient run with guard enabled `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_gradients.py | tee validation/v9_gradients_verbose.log` (expect passes, durations output).
- After each run, write `exit_code.txt` in the validation folder and fill out `reports/2026-01-test-suite-refresh/phase_k/$STAMP/validation/summary.md` (matrix of V1–V9 outcomes, remediation notes, restoration steps for negatives).
- Update docs: append Attempt #19 entry + sign-off note to `[TEST-SUITE-TRIAGE-002]` in docs/fix_plan.md, add Phase K completion notes to plans/active/test-suite-triage-phase-h.md, and drop a short `analysis/rerun_gate.md` with the Phase L criteria.
Pitfalls To Avoid:
- Do not leave binaries/assets renamed after negative tests; always restore before the next command.
- Keep fixtures device/dtype neutral—no hardcoded `.cpu()`/`.float64()` conversions.
- Maintain ASCII-only edits and avoid touching protected assets listed in docs/index.md (loop.sh, input.md, etc.).
- Ensure session fixture failure messages include remediation commands exactly as in the design doc.
- Capture environment variables in logs; missing them will invalidate the evidence bundle.
- Do not run the full `pytest tests/` suite this loop; stick to the targeted validations.
- Avoid suppressing the guard via try/except; let pytest surface the failure/skip directly.
Pointers:
- plans/active/test-suite-triage-phase-h.md:46-57 — Phase K checklist and exit criteria.
- reports/2026-01-test-suite-refresh/phase_j/20251015T180301Z/analysis/session_fixture_design.md:1-160 — infrastructure fixture blueprint.
- reports/2026-01-test-suite-refresh/phase_j/20251015T180301Z/analysis/gradient_policy_guard.md:1-160 — gradient guard design.
- reports/2026-01-test-suite-refresh/phase_j/20251015T180301Z/analysis/validation_plan.md:1-220 — V1–V9 commands and expectations.
- docs/development/testing_strategy.md:1-160 — authoritative device/dtype + Do Now requirements.
Next Up: If Phase K wraps cleanly, draft the guarded full-suite rerun checklist for Phase L so we can schedule the next `pytest tests/` execution.
