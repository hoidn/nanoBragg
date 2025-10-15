Summary: Restore CLI golden assets so targeted pix0/HKL parity tests pass and archive evidence for CLUSTER-CLI-001.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-002] Next Action 5 — CLI golden asset regeneration
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cpu]; tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip
Artifacts: reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-CLI-001/
Do Now: Execute docs/fix_plan.md Next Action 5 — regenerate pix0_expected.json + scaled.hkl (per plans/active/cli-noise-pix0/plan.md) and rerun `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_flags.py -k "pix0_vector_mm_beam_pivot or scaled_hkl_roundtrip"`, capturing logs and checksums under the cluster directory.
If Blocked: Capture failure reason in `cluster_CLUSTER-CLI-001/blocked.md`, add commands.txt + logs, and update docs/fix_plan.md Attempts with the blocker and remediation plan before proceeding elsewhere.
Priorities & Rationale:
- docs/fix_plan.md:55 — Next Actions 5–8 set the remediation queue (CLI first).
- plans/active/test-suite-triage-rerun.md:70 — Phase D cluster checklist tracks closure requirements.
- reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-CLI-001.md — Cluster brief outlining reproduction and exit criteria.
- plans/active/cli-noise-pix0/plan.md:6 — Canonical supervisor command and pix0 context for asset generation.
- docs/development/testing_strategy.md:120 — Authoritative parity workflow + artifact expectations for golden data.
How-To Map:
- `STAMP=$(date -u +%Y%m%dT%H%M%SZ); CLUSTER_DIR=reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-CLI-001/$STAMP; mkdir -p "$CLUSTER_DIR"` (log commands, env, and sha256 here).
- Verify pix0 reference: `cp reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json "$CLUSTER_DIR"/` and record provenance; if values drift, rerun the Phase H trace harness (`python reports/2025-10-cli-flags/phase_h/trace_harness.py --out "$CLUSTER_DIR"/pix0_expected.json`).
- Regenerate structure factors: follow CLAUDE.md pipeline (`refmac5 …`, `mtz_to_P1hkl.com … FC_ALL_LS`) to rebuild `scaled.hkl`, or retrieve the supervisor version from archived evidence if already present; store the regenerated file in repo root and copy to `$CLUSTER_DIR/` with `sha256sum scaled.hkl > "$CLUSTER_DIR"/sha256.txt`.
- Set env and rerun targeted tests: `KMP_DUPLICATE_LIB_OK=TRUE NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_cli_flags.py -k "pix0_vector_mm_beam_pivot or scaled_hkl_roundtrip" | tee "$CLUSTER_DIR"/pytest.log`; record exit code in `$CLUSTER_DIR/run_exit_code.txt`.
- Summarize actions + outcomes in `$CLUSTER_DIR/summary.md` (include asset provenance, test results, next follow-ups) and update docs/fix_plan.md Attempts on completion.
Pitfalls To Avoid:
- Do not delete or relocate assets listed in docs/index.md (Protected Assets rule).
- Keep vectorization/device neutrality intact; no `.cpu()` coercions when inspecting outputs.
- Avoid editing production code until assets/tests confirm the failure mode.
- Ensure C binary rebuilds stay under golden_suite_generator/ to preserve the frozen root binary.
- Capture all commands/env vars in commands.txt; no ad-hoc scripts outside reports/ hierarchy.
- Use repo root paths when tests expect static locations (no temp dirs that break relative lookups).
Pointers:
- docs/fix_plan.md:55 — Next Actions queue for TEST-SUITE-TRIAGE-002.
- plans/active/test-suite-triage-rerun.md:70 — Phase D guidance + checklist.
- reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-CLI-001.md — Detailed brief for this cluster.
- plans/active/cli-noise-pix0/plan.md — CLI parity command & dependencies.
- docs/development/testing_strategy.md §2.3 — Golden data regeneration contract.
Next Up: (1) CLUSTER-TOOLS-001 dual-runner path fix once CLI assets land.
