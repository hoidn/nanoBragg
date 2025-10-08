Summary: Strip the obsolete φ carryover CLI surface and align docs toward spec-only behavior before touching downstream plumbing.
Mode: Docs
Focus: CLI-FLAGS-003 / Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Context Recap:
- Phase A inventory and Phase B0 design review are complete (reports/2025-10-cli-flags/phase_phi_removal/phase_a/, .../phase_b/20251008T185921Z/).
- The carryover shim still exists in code but only spec mode is active; today begins the removal sequence with CLI surfaces.
- plans/active/cli-noise-pix0/plan.md now expects B1 execution before any scaling retry, so we must unblock that plan.
- No production edits have been committed since the design review; this loop establishes the first implementation change for removal.
- Protected Assets guardrails remain in effect; confirm docs/index.md references before editing any documentation.
Mapped tests:
- pytest --collect-only -q tests/test_cli_scaling_phi0.py (pre-change import sanity).
- KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py (CPU regression after edits).
- Optional: KMP_DUPLICATE_LIB_OK=TRUE CUDA_VISIBLE_DEVICES=0 pytest -v tests/test_cli_scaling_phi0.py (capture only if GPU accessible without delay).
Artifacts:
- reports/2025-10-cli-flags/phase_phi_removal/phase_b/<timestamp>/commands.txt — chronological command log including git status and sha256 step.
- reports/2025-10-cli-flags/phase_phi_removal/phase_b/<timestamp>/collect_pre.log — pytest collect-only output before edits.
- reports/2025-10-cli-flags/phase_phi_removal/phase_b/<timestamp>/pytest_cpu.log — targeted CPU pytest run after edits.
- reports/2025-10-cli-flags/phase_phi_removal/phase_b/<timestamp>/pytest_cuda.log — targeted CUDA pytest run if executed.
- reports/2025-10-cli-flags/phase_phi_removal/phase_b/<timestamp>/summary.md — narrative of edits, tests, follow-ups.
- reports/2025-10-cli-flags/phase_phi_removal/phase_b/<timestamp>/env.json — Python/PyTorch/git/device metadata via scripted dump.
- reports/2025-10-cli-flags/phase_phi_removal/phase_b/<timestamp>/sha256.txt — checksum list for all artifacts in the folder.
- reports/2025-10-cli-flags/phase_phi_removal/phase_b/<timestamp>/grep.log — output of rg search for residual `phi_carryover_mode` references.
- reports/2025-10-cli-flags/phase_phi_removal/phase_b/<timestamp>/diff.txt — optional dump of git diff for archival traceability.
Do Now: CLI-FLAGS-003 Phase B1 — Deprecate CLI surfaces; run `pytest --collect-only -q tests/test_cli_scaling_phi0.py` before edits, then `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py` after removing the flag and refreshing docs.
If Blocked: Document the blocker in summary.md (who/what/why), add console output to commands.txt, log a docs/fix_plan.md Attempt referencing the timestamp, and pause code changes until we align on next steps.
Success Criteria:
- CLI argparse help and usage text no longer mention `--phi-carryover-mode`.
- Spec-mode regression tests in tests/test_cli_scaling_phi0.py still pass with existing tolerances.
- No residual references to `phi_carryover_mode` remain outside components explicitly deferred to Phase B2/B3.
- Documentation now states that PyTorch lacks a carryover reproduction mode and follows spec behavior only.
- Artifact bundle is complete with hashes, environment metadata, and linked back to the Phase B0 design review.
Priorities & Rationale:
- plans/active/phi-carryover-removal/plan.md:29-38 elevates B1 as the next gate now that B0 is [D]; finishing it unlocks the rest of Phase B.
- docs/fix_plan.md:461-465 directs today’s iteration to execute Plan B1–B3 in order, so B1 is mandatory.
- specs/spec-a-core.md:211-224 mandates fresh φ rotations; deleting the CLI toggle prevents user regression to the C bug.
- docs/bugs/verified_c_bugs.md:166-204 identifies carryover as a C-only defect; removing the shim keeps PyTorch honest to spec.
- reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T185921Z/design_review.md defines the removal sequence; we must cite it in new evidence.
- plans/active/cli-noise-pix0/plan.md:26-33 assumes the design bundle exists and expects B1 completion before parity work resumes.
- CLAUDE.md Protected Assets section reminds us to respect docs/index.md and other guarded files while editing CLI docs.
How-To Map:
- Create a UTC timestamp (`ts=$(date -u +%Y%m%dT%H%M%SZ)`) and `mkdir -p reports/2025-10-cli-flags/phase_phi_removal/phase_b/${ts}`.
- Run `pytest --collect-only -q tests/test_cli_scaling_phi0.py | tee reports/.../${ts}/collect_pre.log` to capture the baseline state.
- Begin commands.txt immediately (`script -q -c "your command"` or manual append) so every action is recorded chronologically.
- Edit src/nanobrag_torch/__main__.py: remove the argument definition, help text, and config wiring for `phi_carryover_mode` while keeping formatting tidy.
- After CLI edits, rerun `pytest --collect-only -q tests/test_cli_scaling_phi0.py` if you need a syntax check; log short outputs in commands.txt only.
- Update README_PYTORCH.md and prompts/supervisor.md to reflect that the flag no longer exists; describe the update in summary.md.
- Update docs/bugs/verified_c_bugs.md to clarify PyTorch no longer exposes an opt-in shim; cite the spec passage in the note.
- Search for remaining references: `rg "phi_carryover_mode" -n | tee reports/.../${ts}/grep.log` and annotate any leftover call sites for Phase B2.
- Execute `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py | tee reports/.../${ts}/pytest_cpu.log` and verify tolerances remain unchanged.
- If CUDA is available, run `KMP_DUPLICATE_LIB_OK=TRUE CUDA_VISIBLE_DEVICES=0 pytest -v tests/test_cli_scaling_phi0.py | tee reports/.../${ts}/pytest_cuda.log`; otherwise note the omission in summary.md.
- Capture environment metadata via Python (git SHA, Python version, torch version, CUDA availability) into env.json.
- Summarize edits, tests, deferred follow-ups, and references to the design bundle inside summary.md; include explicit links to spec and bug docs.
- Generate sha256.txt with `cd reports/.../${ts} && sha256sum * > sha256.txt` once artifacts are present.
- Review git status to confirm only expected files changed; adjust if unexpected files appear.
- Stage edits, craft commit message referencing Phase B1, and prepare to log results in docs/fix_plan.md Attempt once ready.
Pitfalls To Avoid:
- Do not delete or rename files listed in docs/index.md (Protected Assets rule).
- Do not touch Crystal or Simulator carryover plumbing yet; that is Phase B2 territory.
- Avoid introducing scalar loops or other de-vectorized logic when editing CLI plumbing.
- Preserve device/dtype neutrality; no implicit `.cpu()` or `.double()` conversions in argument handling.
- Keep CLI help text grammatically correct after removal (no double spaces or dangling punctuation).
- Capture every command in commands.txt; missing entries complicate reproducibility.
- Stick to mapped pytest selectors; full-suite runs are out of scope for this loop.
- Do not modify the C reference harness or reports outside the targeted directory.
- Resist opportunistic refactors; keep diffs tightly scoped to Phase B1 requirements.
- Log artifact hashes; skipping sha256.txt breaks archival integrity.
- Remember to update docs/fix_plan.md only after artifacts exist; premature edits cause churn.
- Ensure summary.md explicitly mentions the timestamped folder and references the B0 design review.
Reporting Requirements:
- summary.md must cross-link to reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T185921Z/design_review.md and explain how B1 fulfilled the plan.
- commands.txt should include environment setup, test invocations, git diff, and checksum generation in chronological order.
- env.json must state whether CUDA was used (`"cuda_available": true/false`) and include torch version strings.
- grep.log should either be empty or list residual references annotated in summary.md as B2/B3 follow-ups.
- When updating docs/fix_plan.md Attempts, include metrics (pass/fail, tolerances) and artifact path for traceability.
Documentation Touchpoints:
- README_PYTORCH.md CLI flag descriptions and usage examples.
- prompts/supervisor.md instructions that may reference carryover modes or testing expectations.
- docs/bugs/verified_c_bugs.md C-PARITY-001 section to clarify PyTorch behavior post-removal.
- docs/development/testing_strategy.md passages that described dual-mode tolerances (update to spec-only wording).
- Any user or history docs mentioning the shim; mark them as legacy or update language to past tense.
Successor Planning:
- Record in summary.md the config/simulator call sites still referencing `phi_carryover_mode` for Phase B2 planning.
- Note which tests or tooling will require deletion or updates during Phase B3 (e.g., tests/test_phi_carryover_mode.py).
- Identify documentation that will be tackled in Phase C (testing strategy, reports) and list them for future loops.
Pointers:
- plans/active/phi-carryover-removal/plan.md:29-38 — Phase B roadmap and current status.
- plans/active/cli-noise-pix0/plan.md:24-33 — Umbrella Next Actions expecting B1 completion.
- docs/fix_plan.md:451-465 — Ledger directives and attempt logging requirements.
- specs/spec-a-core.md:211-224 — Normative φ rotation rules to cite in docs.
- docs/bugs/verified_c_bugs.md:166-204 — Bug dossier justifying removal.
- reports/2025-10-cli-flags/phase_phi_removal/phase_b/20251008T185921Z/design_review.md — B0 artifact to reference in summary.md.
- CLAUDE.md:120-160 — Protected Assets rule refresher before editing documentation.
- docs/development/testing_strategy.md:40-70 — Device/dtype cadence guidance for targeted tests.
- scripts/validation/README.md — Reusable tooling overview should you need parity helpers.
- input.md (this memo) is read-only for you; do not modify it.
Implementation Notes:
- Removing the flag will change argparse defaults; verify there are no downstream consumers relying on the option object.
- Ensure usage examples in README_PYTORCH.md no longer suggest passing the flag; replace with spec-mode wording.
- Confirm supervisor.sh or loop automation docs do not mention the flag; update if necessary.
- Double-check that generated help text still fits within console formatting expectations (no oddly wrapped lines).
- If argparse formatting changes, capture before/after snippet in summary.md for archival context.
Metrics to Capture:
- Number of references removed (from grep.log) and remaining references flagged for B2/B3.
- Pytest runtime for CPU run (record in summary.md).
- Git diff summary (files changed) noted in summary.md.
- Any documentation sections updated should be listed with line anchors where practical.
Ledger Update Checklist:
- Add Attempt entry under CLI-FLAGS-003 with timestamp, artifact path, tests executed, and remaining work.
- Mention in docs/fix_plan.md that Phase B1 is complete and B2/B3 remain.
- Update plans/active/phi-carryover-removal/plan.md to flip B1 to [D] after verification.
- Mirror any Next Actions adjustments into plans/active/cli-noise-pix0/plan.md if wording needs refreshing.
Validation Order:
- Baseline collect-only run before edits.
- CLI/docs edits plus grep sweep.
- Targeted pytest CPU run (and CUDA if possible).
- Final documentation review and ledger updates.
Time Budget Guidance:
- Allocate first 10 minutes to set up artifact folder and baseline tests.
- Spend up to 25 minutes editing CLI code and documentation with incremental checks.
- Reserve 10 minutes for testing and artifact capture.
- Leave final 10 minutes for summary writing, ledger updates, and git hygiene.
Additional Reminders:
- Maintain vectorization and differentiability principles even if edits seem benign.
- Re-run `rg "carryover"` to ensure textual references align with new messaging.
- Keep commit message in the SUPERVISOR format if you hand back to galph for commits.
- Confirm `pip install -e .` is still valid after CLI change if documentation references it.
- If you uncover doc drift unrelated to this phase, log it under open questions rather than fixing it now.
Next Up: If you finish B1 early, inventory the config/crystal/simulator call sites requiring edits for Phase B2 and capture them in summary.md without modifying code.
