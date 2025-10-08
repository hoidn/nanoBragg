Summary: Capture the Phase D spec-mode φ-removal evidence bundle and point CLI-FLAGS-003 back to scaling parity work.
Mode: Parity
Focus: CLI-FLAGS-003 Phase D proof-of-removal
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py
Artifacts: reports/2025-10-cli-flags/phase_phi_removal/phase_d/${STAMP}/
Do Now: CLI-FLAGS-003 Phase D1a — export STAMP=$(date -u +%Y%m%dT%H%M%SZ) && KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --phi-mode spec --pixel 685 1039 --device cpu --dtype float64 --emit-c-trace --out reports/2025-10-cli-flags/phase_phi_removal/phase_d/${STAMP}/trace_py_spec.log
If Blocked: Stop immediately, archive the partial directory under reports/.../phase_phi_removal/phase_d/${STAMP}/ with stderr in commands.txt, and record the blocker plus harness output snippet in summary.md before pinging me.

Priorities & Rationale
- plans/active/phi-carryover-removal/plan.md:51-62 — Phase D rows define D1a–D1c deliverables (trace bundle, pytest proof, rg sweep) we must close before scaling work resumes.
- docs/fix_plan.md:451-467 — Next Actions expect the Phase D bundle path and ledger sync, so producing the evidence unblocks the remaining bullets.
- docs/bugs/verified_c_bugs.md:166-204 — C-PARITY-001 now documents shim removal; the new bundle needs to corroborate the "spec-only" statement with live traces.
- docs/development/testing_strategy.md:32-63 — Reiterates targeted-test cadence and device neutrality; the pytest run supplies the spec tolerance proof without pulling the full suite.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py — Existing harness already wired for supervisor inputs; rerunning it in spec mode confirms the shim codepath is gone.

How-To Map
- export STAMP once and reuse it for every artifact (traces, pytest logs, env metadata) to keep the Phase D directory cohesive.
- After the Do Now command, verify both trace_py_spec.log and trace_c_spec.log exist, then run the same harness with `--device cuda` only if `torch.cuda.is_available()`; otherwise note "CUDA N/A" in summary.md.
- Capture command history (`script -q commands.txt`) and environment metadata (`python -m json.tool <<<"$TRACE_ENV"` → env.json) inside reports/2025-10-cli-flags/phase_phi_removal/phase_d/${STAMP}/.
- Run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py | tee reports/.../phase_phi_removal/phase_d/${STAMP}/pytest.log` and save the collector output separately via `--collect-only` if you need to debug failures.
- Execute `rg --files-with-matches "phi_carryover" src tests scripts prompts docs | sort > reports/.../phase_phi_removal/phase_d/${STAMP}/rg_scan.txt` and summarize the (expected empty) result in summary.md.
- Populate summary.md with: trace commands + success status, pytest max |Δk_frac|, rg results, CUDA availability, and any follow-up needed for D2/D3.
- Once artifacts are ready, stage sha256 hashes (`sha256sum * > sha256.txt`) and update docs/fix_plan.md Attempt log with the exact ${STAMP} path before closing the loop.

Pitfalls To Avoid
- Do not edit production code or the harness; this loop is evidence-only.
- Keep STAMP consistent—mixing directories will make the ledger update impossible.
- Always prefix Python commands with `PYTHONPATH=src` and `KMP_DUPLICATE_LIB_OK=TRUE` per runtime checklist.
- Skip CUDA runs unless the device is available; do not fake metrics.
- Do not delete historical shim artifacts under reports/; only add the new Phase D bundle.
- Avoid full pytest suites; the targeted selector is sufficient and mandated by testing_strategy.md.
- Ensure rg excludes reports/ and archive directories to prevent false positives.
- Maintain ASCII output in summary.md and commands.txt.
- Record non-zero exits immediately in summary.md; reruns must use a new STAMP.
- Before handing off, double-check that summary.md cites the plan rows it satisfies.

Pointers
- plans/active/phi-carryover-removal/plan.md:51-62 — Phase D checklist we are executing.
- docs/fix_plan.md:451-467 — Fix-plan linkage that will reference the new Phase D bundle.
- docs/development/testing_strategy.md:25-63 — Targeted test cadence and evidence requirements.
- docs/bugs/verified_c_bugs.md:166-204 — Narrative that this bundle must substantiate.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py — Harness invoked for the Do Now command.

Next Up
- Phase D2 ledger sync (docs/fix_plan.md + plan archive) once the evidence directory is committed.
