Summary: Produce the Option B batch-design artifacts for the φ carryover cache before returning to implementation.
Mode: Docs
Focus: CLI-FLAGS-003 / plans/active/cli-noise-pix0/plan.md > Phase M2g.2c–M2g.2d
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only tests/test_cli_scaling_parity.py
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/{optionB_batch_design.md,prototype.md,metrics.json,commands.txt,gradcheck.log,env.json,sha256.txt}
Do Now: CLI-FLAGS-003 M2g.2c/M2g.2d — draft the Option B batch-design memo and 4×4 ROI prototype, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests/test_cli_scaling_parity.py -q` to confirm selector health.
If Blocked: If design questions remain unresolved, capture open issues in the memo, run the collect-only command, and stop without touching production code.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:30 — Next Actions now require design/prototype artifacts before wiring resumes.
- plans/active/cli-noise-pix0/plan.md:109 — Checklist items M2g.2c/M2g.2d spell out the needed memo/prototype deliverables.
- docs/fix_plan.md:456 — Next Actions highlight the same prerequisite artifacts and cite the analysis refresh.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251208_option1_refresh/analysis.md — Captures the architecture blocker and Option B constraints you must address.
- specs/spec-a-core.md:205 — Normative φ rotation resets; the memo must show spec mode stays untouched.
How-To Map:
- Create a new timestamped folder under `reports/2025-10-cli-flags/phase_l/scaling_validation/` and document all commands in `commands.txt`.
- Author `optionB_batch_design.md` summarising batching granularity (row/tile choice), tensor shapes, cache lifecycle, memory/dtype/gradient guardrails, and the validation plan (pytest selectors + trace harness). Cite `specs/spec-a-core.md:205-233`, `docs/bugs/verified_c_bugs.md:166-204`, `nanoBragg.c:2797,3044-3095`, and the 20251208 Option 1 refresh memo.
- Build a disposable 4×4 ROI prototype (Python script or notebook saved as text) that allocates mock cache tensors, applies the proposed batch substitution, and runs a tiny `torch.autograd.gradcheck`; capture results in `prototype.md`, `metrics.json`, and `gradcheck.log`.
- Record environment details (`python --version`, `torch.__version__`) in `env.json` and stash checksums in `sha256.txt`.
- After artifacts exist, validate the mapped selector with `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests/test_cli_scaling_parity.py -q` and append the output to `commands.txt`.
- Update `docs/fix_plan.md` Attempts with the new artifact path and summarize key findings once the memo is complete.
Pitfalls To Avoid:
- Do not edit production Python files during this design loop.
- Keep tensors in the prototype device/dtype neutral; no hard-coded `.cpu()` / `.cuda()` conversions.
- Avoid `.item()` / `.detach()` in prototype pathways except where gradients are intentionally cut.
- Respect `(slow, fast)` ordering when building index tensors; be explicit about shapes in the memo.
- Keep Protected Assets untouched and do not rename files listed in `docs/index.md`.
- Limit testing to the collect-only selector; do not run the full suite.
- Store artifacts under ASCII filenames and include SHA256 manifests.
- Ensure citations include the exact spec and C-code line references per CLAUDE Rule #11.
Pointers:
- plans/active/cli-noise-pix0/plan.md:25
- plans/active/cli-noise-pix0/plan.md:109
- docs/fix_plan.md:456
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T145905Z/m2g_blocker/analysis.md
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251208_option1_refresh/analysis.md
- specs/spec-a-core.md:205
- docs/bugs/verified_c_bugs.md:166
Next Up: Once the design artifacts are complete, resume M2g.3 cache allocation or refresh the parity tooling per M2g.5 depending on review feedback.
