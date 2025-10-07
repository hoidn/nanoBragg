Summary: Draft the φ=0 carryover parity-shim design so spec mode stays default while C parity becomes opt-in.
Mode: Docs
Focus: CLI-FLAGS-003 L3k.3c.4 — parity shim design
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_phi0.py (collect-only)
Artifacts: plans/active/cli-phi-parity-shim/plan.md; reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/design.md; reports/2025-10-cli-flags/phase_l/parity_shim/<timestamp>/collect_only.log
Do Now: CLI-FLAGS-003 L3k.3c.4 — KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py --collect-only -q (stash log under parity_shim/<timestamp>/)
If Blocked: Capture why the design note cannot progress in design.md (status, missing data), run the collect-only selector anyway, and log the attempt in docs/fix_plan.md before pausing.
Priorities & Rationale:
- plans/active/cli-phi-parity-shim/plan.md:26-35 set the design tasks (B1-B3) that must complete before any implementation.
- docs/fix_plan.md:450-463 promotes L3k.3c.4/5 as the next gate to unlock the supervisor command parity rerun.
- specs/spec-a-core.md:204-240 keeps φ rotation normative; the shim must not change this default path.
- docs/bugs/verified_c_bugs.md:166-204 documents C-PARITY-001; the shim design must trace back to this evidence.
- tests/test_cli_scaling_phi0.py:1-192 already encode the spec baseline; design must preserve these assertions and plan parity-only cases.
How-To Map:
- mkdir -p reports/2025-10-cli-flags/phase_l/parity_shim/$(date -u +%Y%m%dT%H%M%SZ) for the new evidence drop.
- Draft design.md covering trigger surface, data flow, validation commands; cite nanoBragg.c lines 3040-3095 verbatim per CLAUDE Rule #11.
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py --collect-only -q > parity_shim/.../collect_only.log
- Note planned trace commands (scripts/compare_per_phi_traces.py, nb-compare) and pytest selectors inside design.md, pointing to the new report directory.
Pitfalls To Avoid:
- Do not alter production code yet; this loop is design-only.
- Keep spec mode default—no plan for toggling without explicit opt-in.
- Maintain vectorization constraints when outlining implementation (no Python loops in design).
- Respect Protected Assets; do not move files listed in docs/index.md.
- Ensure collect-only log captures that the selector still discovers both φ tests.
- Reference C code via exact snippets; paraphrasing violates CLAUDE Rule #11.
- When proposing CLI flags, avoid collisions with existing options.
- Plan for device/dtype neutrality; design must cover CPU and CUDA traces.
- Preserve existing artifacts; new evidence goes under parity_shim/<timestamp>/.
Pointers:
- plans/active/cli-phi-parity-shim/plan.md:33-48 — design + implementation checklist.
- plans/active/cli-noise-pix0/plan.md:303-317 — L3k.3c rows now referencing the new plan.
- docs/fix_plan.md:450-463 — refreshed Next Actions for CLI-FLAGS-003.
- specs/spec-a-core.md:204-240 — normative φ rotation description.
- docs/bugs/verified_c_bugs.md:166-204 — C bug reference to emulate.
Next Up: 1) Promote the chosen API through Crystal/Simulator configs (plan C2). 2) Prepare pytest parity cases once mode exists (plan C3).
