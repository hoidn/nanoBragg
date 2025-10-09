Summary: Bake φ-carryover safeguards into our hygiene docs and add the nb-compare watch ledger before we close CLI-FLAGS-003.
Mode: Docs
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: docs/fix_plan.md; plans/active/phi-carryover-removal/plan.md; reports/archive/cli-flags-003/watch.md
Do Now: CLI-FLAGS-003 Phase P1/P2 — add the quarterly trace + rg sweep guidance and publish watch.md, then run `pytest --collect-only -q` to prove collection stays clean.
If Blocked: Capture the attempted commands and rg output under `reports/attempts/cli-flags-003/<timestamp>/` and log the blocker in docs/fix_plan.md Attempts before stopping.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:103 keeps P1/P2 open; we need the hygiene + watch scaffolding before parking the initiative.
- plans/active/phi-carryover-removal/plan.md:72 leaves Phase E (E1/E2) pending, so hygiene must call out the rg sweep and quarterly trace cadence.
- docs/bugs/verified_c_bugs.md:166 documents C-PARITY-001 as C-only, reinforcing why the guardrails live in docs instead of code shims.
- specs/spec-a-core.md:211 locks the fresh-φ rotation contract; the hygiene reminders must cite this spec so future cleanups stay aligned.
How-To Map:
- Update the Protected-Assets/cleanup guidance in docs/fix_plan.md to spell out the `rg "phi_carryover"` sweep and reference `reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T203504Z/commands.txt` as the canonical spec-trace command.
- Create `reports/archive/cli-flags-003/watch.md` summarising the quarterly trace harness step plus the biannual nb-compare smoke (`nb-compare -- -default_F 100 ...` reused from `reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/summary.json`) and the expected metrics (corr≈0.985, sum_ratio≈1.2e5).
- After edits, mark P1/P2 and E1/E2 progress in the respective plans and append a new Attempt in docs/fix_plan.md capturing the updates, then run `pytest --collect-only -q`.
Pitfalls To Avoid:
- Do not touch production code—this loop is documentation-only.
- Keep Protected Assets intact (`docs/index.md`, loop.sh, supervisor.sh).
- Preserve device/dtype neutrality when citing commands; no cpu-only assumptions.
- Reference existing artifacts rather than inventing new commands; stay consistent with archived bundles.
- Include env/command snippets in watch.md so future runs are reproducible.
- Avoid deleting historical shim evidence; only add forward-looking guidance.
- Ensure rg examples use project-relative paths and note expected zero hits post-shim.
- Keep tests light: just `pytest --collect-only -q` once edits are staged.
- Update both plan checklists (cli-noise-pix0 Phase P, phi-carryover Phase E) after writing the docs.
Pointers:
- docs/fix_plan.md:10 — Active Focus now calls for Phase P watch tasks and phi-carryover hygiene.
- plans/active/cli-noise-pix0/plan.md:103 — Open checklist rows for P1/P2 describe the required hygiene + watch outputs.
- plans/active/phi-carryover-removal/plan.md:74 — Phase E spells out the rg sweep + watch.md deliverables you need to fulfill.
Next Up: Vectorization Phase E2 benchmarks (plans/active/vectorization.md) once the watch scaffolding lands.
