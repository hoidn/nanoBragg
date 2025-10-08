Summary: Refresh the Option 1 φ-carryover cache design notes so scaling work can resume with clear spec references.
Mode: Docs
Focus: [CLI-FLAGS-003] Phase M2g.1 Option 1 design refresh
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/20251208_option1_refresh/{analysis.md,commands.txt,env.json}
Do Now: [CLI-FLAGS-003] Phase M2g.1 Option 1 design refresh — run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q`, then draft `reports/2025-10-cli-flags/phase_l/scaling_validation/20251208_option1_refresh/analysis.md` summarising the current Option 1 requirements vs `phi_carryover_diagnosis.md` and spec lines 205-233.
If Blocked: Capture the exact failure (stdout/stderr) into `reports/2025-10-cli-flags/phase_l/scaling_validation/20251208_option1_refresh/attempts/` and note it in docs/fix_plan.md Attempts before escalating.
Priorities & Rationale:
- specs/spec-a-core.md:211 — Confirms φ-rotation recomputes from the reference lattice each step; cite this to show carryover remains a C-only bug.
- docs/fix_plan.md:451 — Active Next Actions flag the Option 1 cache as the blocker; our summary must tee up the architecture decision (Action 0).
- plans/active/cli-phi-parity-shim/plan.md:11 — New status note mandates C5 `summary.md` cite the spec section; today’s memo should provide the wording.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T100653Z/analysis.md — Existing Option 1 design notes; diff against them to identify new constraints (e.g., rotation tensor shapes).
- docs/bugs/verified_c_bugs.md:166 — Documents C-PARITY-001 as C-only; cross-reference to keep the bug ledger consistent with the shim summary.
How-To Map:
- `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` — prove the environment imports cleanly before documentation edits.
- `python scripts/compare_scaling_traces.py --help` (no execution) — skim usage so the memo can call out which taps depend on cache layout.
- Read `reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md` and highlight any deltas needed in the new memo.
- Record commands used (collect-only, file inspections) in `commands.txt`; capture `python - <<'PY'` snippets if you inspect tensor shapes.
- Save `env.json` via `python scripts/tools/dump_env.py > env.json` (create if missing) to snapshot torch/device info for the memo.
Pitfalls To Avoid:
- Do not edit production code or toggle the pixel loop; this is a docs-only loop.
- Keep artifacts under `reports/2025-10-cli-flags/...` to preserve plan cross-references.
- No `.detach()` or cache design edits yet—capture requirements first.
- Maintain device/dtype neutrality in any example tensors you discuss; note expected shapes without committing code.
- Do not alter specs/spec-a-core.md; only quote the relevant lines.
- Avoid rerunning heavy parity scripts; stick to collect-only evidence per Mode: Docs.
- Respect Protected Assets: leave files listed in docs/index.md untouched.
- When quoting C code in the memo, copy exact lines (nanoBragg.c:2797,3044-3095) per CLAUDE Rule #11.
Pointers:
- specs/spec-a-core.md:205 — φ step definition.
- docs/bugs/verified_c_bugs.md:166 — C-PARITY-001 classification.
- plans/active/cli-noise-pix0/plan.md:75 — M2 phase objectives and Option 1 checklist.
- plans/active/cli-phi-parity-shim/plan.md:11 — New spec citation requirement.
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md — Prior Option 1 design baseline.
Next Up: If the memo lands quickly, start outlining the architecture decision matrix (Options A/B/C) in the same report so we can pick one next loop.
