Summary: Validate CLI-FLAGS-003 spec-mode coverage aligns with c-parity retirement and capture the audit trail.
Mode: Docs
Focus: CLI-FLAGS-003 / coverage audit (plan row C1)
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py
Artifacts: reports/2025-10-cli-flags/phase_phi_removal/phase_c/<timestamp>/
Do Now: CLI-FLAGS-003 — coverage audit per plan row C1 via `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py`, logging output under the row-C evidence directory and noting any gaps to patch.
If Blocked: Capture the failing collect output plus notes in coverage_audit.md, then diff against the 20251008T193106Z summary to identify missing spec assertions.

Priorities & Rationale
- docs/fix_plan.md:462-464 — Next Actions demand coverage audit and documentation sweep before scaling work resumes.
- plans/active/phi-carryover-removal/plan.md:29-49 — Plan rows B0–B5 are closed; table row C1 is now the active gate.
- plans/active/cli-noise-pix0/plan.md:17-33 — Status snapshot already references the removal artifacts; Next Actions outline the same coverage/doc tasks.
- reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T193106Z/summary.md — Confirms what changed during removal so you can verify remaining assertions.
- tests/test_cli_scaling_phi0.py — Current spec-mode coverage needs inspection to ensure all former parity guarantees persist.

How-To Map
- Run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py > reports/2025-10-cli-flags/phase_phi_removal/phase_c/<timestamp>/collect.log` before editing; include commands.txt + env.json + sha256.txt as usual.
- While auditing assertions, document findings in `coverage_audit.md` within the same folder; call out any Miller index or rotation checks that must be reintroduced.
- If you add or modify tests, re-run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py` and store the execution log as `pytest_cpu.log` in the row-C directory (CUDA optional but note availability).
- Update `docs/fix_plan.md` Attempts with the new timestamp once coverage gaps are addressed; reference the row-C artifact path.

Pitfalls To Avoid
- Do not resurrect c-parity code paths or references; spec mode is the only supported flow now.
- Keep tests device-neutral; any new assertions must operate on CPU and CUDA once scaling work resumes.
- Avoid editing protected assets (docs/index.md, loop.sh, supervisor.sh, input.md) beyond this memo.
- Preserve vectorization in any helper adjustments—no scalar φ loops.
- Remember to set `KMP_DUPLICATE_LIB_OK=TRUE` for every pytest/CLI invocation.
- Capture SHA256 hashes for every artifact dropped into reports/.
- Keep pytest selectors precise; no full-suite runs on this loop.
- Maintain ASCII formatting in test/doc files.

Pointers
- plans/active/phi-carryover-removal/plan.md:29-49 — Coverage tasks and guidance for current gate.
- plans/active/cli-noise-pix0/plan.md:17-33 — Mirrors required audit/document work for CLI-FLAGS-003.
- docs/fix_plan.md:451-465 — Ledger entry defining active Next Actions and acceptable outputs.
- reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T193106Z/summary.md — Completed removal scope for reference.
- tests/test_cli_scaling_phi0.py — Source file to extend/specify assertions.

Next Up
- Plan rows C2/C3: once coverage audit is green, sweep docs/bugs and testing strategy to remove residual c-parity instructions.
