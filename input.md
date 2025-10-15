Summary: Capture Phase H infrastructure gate evidence so the suite rerun no longer surprises us with missing binaries or assets.
Mode: Parity
Focus: TEST-SUITE-TRIAGE-002 (Next Action 18 — Phase H infrastructure gate)
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-refresh/phase_h/$STAMP/{env/env.txt,checks/{nb_c_bin.txt,c_binary.txt,c_binary_help.txt,golden_assets.txt},analysis/infrastructure_gate.md}
Do Now: TEST-SUITE-TRIAGE-002#18 — (export STAMP=$(date -u +%Y%m%dT%H%M%SZ); BASE=reports/2026-01-test-suite-refresh/phase_h/$STAMP; mkdir -p $BASE/{env,checks,analysis}; printenv | sort > $BASE/env/env.txt; printf 'NB_C_BIN=%s
fallback_golden=./golden_suite_generator/nanoBragg
fallback_root=./nanoBragg
' "${NB_C_BIN:-<unset>}" > $BASE/checks/nb_c_bin.txt; NB_C_BIN_PATH=${NB_C_BIN:-./golden_suite_generator/nanoBragg}; ls -l "$NB_C_BIN_PATH" > $BASE/checks/c_binary.txt; stat "$NB_C_BIN_PATH" >> $BASE/checks/c_binary.txt; sha256sum "$NB_C_BIN_PATH" >> $BASE/checks/c_binary.txt; timeout 10 "$NB_C_BIN_PATH" -help > $BASE/checks/c_binary_help.txt 2>&1 || true; ls -l scaled.hkl > $BASE/checks/golden_assets.txt; sha256sum scaled.hkl >> $BASE/checks/golden_assets.txt; ls -l reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json >> $BASE/checks/golden_assets.txt; sha256sum reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json >> $BASE/checks/golden_assets.txt; cat <<EOF2 > $BASE/analysis/infrastructure_gate.md
# Phase H Infrastructure Gate Notes

- NB_C_BIN resolved: ${NB_C_BIN:-<unset>}
- Primary binary used: ${NB_C_BIN_PATH}
- Golden asset hashes recorded in checks/golden_assets.txt
- Next steps: outline pytest collection-time fixture assertions per plans/active/test-suite-triage-phase-h.md
EOF2
)
If Blocked: If the binary check fails (missing or non-executable), stop after capturing the failure output, note it in analysis/infrastructure_gate.md, and update docs/fix_plan.md Attempts History with the blocking signature before proceeding.
Priorities & Rationale:
- docs/fix_plan.md:3-47 elevates Phase H gate as the critical next action before any new suite runs.
- plans/active/test-suite-triage-phase-h.md:6-47 spells out the deliverables we need (env snapshot, C binary exec check, golden asset audit, fixture sketch).
- reports/2026-01-test-suite-refresh/phase_g/20251015T163131Z/analysis/summary.md:35-120 shows why infrastructure gaps keep resurfacing when we only run isolated tests.
How-To Map:
- After running Do Now, append reasoning and fixture ideas to $BASE/analysis/infrastructure_gate.md (add bullet list for collection-time assertions, gradient policy hook references, and unanswered questions).
- Run `sha256sum $NB_C_BIN_PATH scaled.hkl reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json >> $BASE/checks/golden_assets.txt` again if hashes were missing or stderr warned about permissions.
- Capture `python -m torch.utils.collect_env > $BASE/env/torch_env.txt` if you need device/dtype context for fix_plan logging.
- Once evidence is ready, log Attempt #16 under docs/fix_plan.md `[TEST-SUITE-TRIAGE-002]` with the STAMP, file list, and findings, then stage the new plan reference for Phase I (Next Action 19).
Pitfalls To Avoid:
- No pytest suites this loop; only the `-help` probe is allowed.
- Keep outputs ASCII; avoid clipboard manipulations that inject smart quotes.
- Do not rebuild nanoBragg binaries—only verify existing artefacts.
- Respect Protected Assets; never move files listed in docs/index.md.
- Preserve the STAMP directory structure exactly; duplicate STAMPs require supervisor signoff.
Pointers:
- docs/fix_plan.md:3-47
- plans/active/test-suite-triage-phase-h.md:6-99
- reports/2026-01-test-suite-refresh/phase_g/20251015T163131Z/analysis/summary.md:1-220
Next Up: Phase I gradient timeout mitigation study (Next Action 19) once the infrastructure gate evidence is logged.
