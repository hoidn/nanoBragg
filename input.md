Summary: Document every remaining φ carryover shim touchpoint so we can deprecate the parity emulation path and return CLI-FLAGS-003 to the spec baseline.
Mode: Docs
Focus: CLI-FLAGS-003 / Phase A shim removal inventory
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling_phi0.py
Artifacts: reports/2025-10-cli-flags/phase_phi_removal/phase_a/<timestamp>/
Do Now: Execute plans/active/phi-carryover-removal/plan.md Phase A (tasks A1–A2) — record all `phi_carryover_mode` usages and capture a fresh collect-only run for the CLI scaling suite.
If Blocked: Note the blocker inside baseline_inventory.md, archive partial commands/env metadata in the Phase A report directory, and jot a draft Attempt bullet in docs/fix_plan.md for the next supervisor edit.
Priorities & Rationale:
- specs/spec-a-core.md:204-240 — normative φ rotation flow; cite these lines when describing why the shim must disappear.
- specs/spec-a-core.md:241-260 — follow-on language around φ steps; mention if any removal risk touches this section.
- docs/bugs/verified_c_bugs.md:166-204 — records C-PARITY-001; use as proof the bug is intentionally C-only post-removal.
- docs/bugs/verified_c_bugs.md:205-220 — contains suggested next steps; highlight that we’ll pursue “reset ap/bp/cp” via spec compliance instead of parity shim.
- plans/active/phi-carryover-removal/plan.md — newly written phased plan; today must close Phase A checklist entries before code edits start.
- plans/active/cli-noise-pix0/plan.md lines 20-40 — Next Actions now point at the removal plan; keep cross references accurate while logging findings.
- docs/fix_plan.md:451-520 — CLI-FLAGS-003 ledger expects a freeze note once inventory artifacts exist; prepare wording while gathering evidence.
- prompts/supervisor.md (commit 6ebc90d) — parity command instructions already dropped c-parity testing; ensure new notes align.
- tests/test_cli_scaling_phi0.py — spec acceptance suite; collect output to prove baseline remains stable.
- tests/test_phi_carryover_mode.py — targeted for deletion; document all fixtures/classes for future removal scopes.
- src/nanobrag_torch/__main__.py:360-410 — CLI parser; inventory the argparse option definitions and help strings for `--phi-carryover-mode`.
- src/nanobrag_torch/config.py:140-200 — CrystalConfig dataclass; capture property defaults and validation logic tied to the shim.
- src/nanobrag_torch/models/crystal.py:1040-1140 — rotation pipeline; note where `_apply_phi_carryover` hooks into the vectorized path.
- scripts/trace_harness.py — currently supports `--phi-mode`; list behaviors to update once shim is gone.
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md — dual-threshold write-up; add pivot note once inventory done.
- reports/2025-10-cli-flags/phase_l/parity_shim/`*` — keep as historical context; reference them in baseline_inventory.md so future readers know where evidence lives.
How-To Map:
- Export `KMP_DUPLICATE_LIB_OK=TRUE` before running any Python or pytest commands to satisfy PyTorch runtime guardrails.
- Create directory `reports/2025-10-cli-flags/phase_phi_removal/phase_a/<timestamp>/` (UTC timestamp, e.g., 20251212T235959Z) prior to executing commands.
- Command 1: `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py | tee reports/.../collect.log` — ensures spec suite still discovers tests.
- Command 2: `rg -n "phi_carryover_mode"` from repo root; pipe to `reports/.../phi_carryover_refs.txt` for raw hits across code and docs.
- Command 3: Optionally run `rg -n "phi carryover" docs` to find narrative references; append results to `phi_carryover_refs.txt` with separators.
- Command 4: Use a small Python script to emit `env.json` with fields: timestamp ISO8601, python_version, torch_version, cuda_available, git_head, branch, workstation identifier if known.
- Command 5: Populate `commands.txt` with each command executed (include working directory, env vars, expected outputs) to maintain reproducibility.
- Command 6: Run `find reports/.../ -type f -print0 | xargs -0 sha256sum > reports/.../sha256.txt` after files are in place.
- Documentation step: Create `baseline_inventory.md` summarising each reference; use headings for “Code”, “Tests”, “Docs”, “Scripts”, “Reports” with bullet entries listing path, context, removal impact, and any dependencies.
- Documentation step: Update `reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md` with a short “2025-12-12 pivot” paragraph referencing the new plan and artifact directory; mention that tolerances will revert to spec-only after removal.
- Documentation step: Add `reports/2025-10-cli-flags/phase_phi_removal/README.md` (if missing) outlining directory structure, active phases, and artifact naming scheme.
- Draft note: Inside baseline_inventory.md, include a short summary referencing plan tasks A1–A3 and indicating which items will be addressed in Phase B vs C.
- Draft note: Outline the expected deletion list (e.g., CLI flag, config field, parity tests, shim code, doc references) so Phase B has a ready-made checklist.
- Validation step: After commands run, re-check `git status --short`; the only changes should be new/modified docs and reports.
- Validation step: Confirm no `.py` code files changed inadvertently; if modifications appear, stash or revert before finishing.
- Optional step: If rg output is noisy, consider using `rg -n "carryover" -g"*.md" docs` to capture doc references separately.
- Optional step: If helpful, note any third-party references (e.g., CLAUDE.md instructions) that mention the shim for later cleanup.
Pitfalls To Avoid:
- Do not edit production Python modules, tests, or scripts during this loop; stick to documentation and reporting.
- Avoid deleting files; removal work begins in Phase B after the inventory is committed.
- Keep note files ASCII-only; avoid fancy tables or Unicode bullets.
- Respect Protected Assets from docs/index.md (input.md, loop.sh, supervisor.sh, etc.).
- Do not run heavy parity tools (trace_harness, nb-compare) until the shim is removed.
- Ensure collect-only pytest output is archived even if it fails; store failure logs in the same directory.
- When summarising references, include file purpose (CLI parsing, config validation, trace harness) to ease future edits.
- Do not modify docs/fix_plan.md during this loop unless recording a blocker; actual Attempt updates will happen next supervisor run.
- If CUDA is unavailable, state it explicitly in env.json; no need to fake GPU metadata.
- Confirm tests/test_phi_carryover_mode.py is listed as “to remove” but not executed.
- Maintain the new plan structure; do not rename sections or checklists.
- Ensure commands in commands.txt include both the command and a short comment describing purpose.
- Double-check timestamp formatting (YYYYMMDDTHHMMSSZ) for new directories.
- Ensure baseline_inventory.md references spec and plan sections to maintain traceability.
- Capture any helper utilities (e.g., dataset loaders) that touch the shim for completeness.
- Include note about `--phi-carryover-mode` usage in docs/user or README if present.
- Note whether any prompts or scripts still mention c-parity; include them in the inventory for later cleanup.
- Avoid running formatting tools (black, isort) to keep the loop documentation-only.
Pointers:
- specs/spec-a-core.md:204-260 — normative φ behavior; cite when describing why the shim is being removed.
- docs/bugs/verified_c_bugs.md:166-220 — C-only bug documentation; reference when explaining historical context.
- plans/active/phi-carryover-removal/plan.md — follow Phase A tasks; log progress in baseline_inventory.md.
- plans/active/cli-noise-pix0/plan.md:20-40 — Next Actions now delegate to the removal plan; ensure remarks stay aligned.
- docs/fix_plan.md:451-520 — status snapshot; prepare language for a future Attempt entry referencing Phase A artifacts.
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md — add pivot note referencing the new artifact path.
- reports/2025-10-cli-flags/phase_l/parity_shim/`*` — note as archival evidence for the shim; include pointer in inventory summary.
- tests/test_cli_scaling_phi0.py — confirm selector used in collect-only command; include link in commands.txt.
- tests/test_phi_carryover_mode.py — list with comment “scheduled for removal in Phase B.”
- src/nanobrag_torch/__main__.py:377-386 — parser definition of the shim flag; document exact argparse choices.
- src/nanobrag_torch/config.py:154-171 — CrystalConfig field; note default value and error messaging.
- src/nanobrag_torch/models/crystal.py:1084-1128 — shim implementation; mention vectorization constraints to preserve after removal.
- scripts/trace_harness.py — note `--phi-mode` options; plan to drop c-parity branch later.
- docs/development/testing_strategy.md §1.4-1.5 — reference collect-only requirement; cite in commands.txt.
- prompts/supervisor.md — confirm parity guidance matches new direction.
- CLAUDE.md — includes rules referencing the shim; list for Phase C documentation update.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T183020Z/metrics.json — reference as last c-parity metrics bundle.
- reports/2025-10-cli-flags/phase_l/per_phi/* — mention per-φ logs as historical context.
- history/ or archive directories that may mention c-parity; capture any relevant references.
- docs/development/pytorch_runtime_checklist.md — ensure inventory notes mention device/dtype neutrality requirement when touching crystal model.
- docs/user/known_limitations.md — verify no lingering references to c-parity remain; note findings.
- docs/user/cli_quickstart.md — check for CLI flag mentions; include in inventory if present.
- docs/development/implementation_plan.md — scan for shim milestones; record any sections to update later.
- docs/development/pytorch_runtime_checklist.md — reiterate device neutrality when summarising crystal changes.
- docs/development/c_to_pytorch_config_map.md — capture any inline notes tying CLI flags to config fields.
- docs/architecture/pytorch_design.md — ensure lattice rotation discussion stays aligned with shim removal.
- docs/architecture/c_function_reference.md — note any references to carryover required for future documentation updates.
- docs/architecture/undocumented_conventions.md — record if shim is mentioned in the conventions section.
- docs/debugging/debugging.md — highlight where parallel trace instructions reference c-parity; include in inventory summary.
- docs/debugging/detector_geometry_checklist.md — confirm it remains unaffected; note absence of shim references.
- reports/archive/cli-flags-003/* — check if archived notes mention the shim; log pointers in baseline_inventory.md.
- history/2025-10-cli-flags/*.md — scan for narrative references; include relevant files in inventory list.
- prompts/pyrefly.md — make sure static analysis guidance does not mention the shim; flag if updates needed later.
- scripts/validation/README.md — ensure CLI instructions remain spec compliant; note if shim removal will require updates.
- scripts/compare_scaling_traces.py — record plan to drop c-parity options post-removal.
- scripts/debug_pixel_trace.py — identify whether the shim is referenced; include in removal backlog if so.
- tests/__init__.py — verify no global fixtures refer to the shim; add to inventory if found.
- tests/conftest.py — inspect for shared fixtures or CLI helpers referencing c-parity; document findings.
- tests/parity_cases.yaml — confirm no cases rely on c-parity mode; mention outcome in baseline notes.
- README_PYTORCH.md — scan CLI documentation for shim references; include in inventory.
- PROJECT_STATUS.md — ensure current initiative description (None) is consistent with removal plan; mention if update needed.
- CLAUDE.md Protected Assets rule — reference in baseline notes to remind future editors not to move CLI artifacts listed in docs/index.md.
- supervisor.sh — ensure automation harness does not expect c-parity flag; note if updates required after removal.
- loop.sh — verify automation commands remain spec-mode only; record confirmation.
- scripts/debug_pixel_trace.py output schema — ensure removal will not break existing trace comparisons; note implications.
Next Up: If inventory wraps quickly, draft the Phase B design-review checklist (tasks B1–B3) under reports/2025-10-cli-flags/phase_phi_removal/phase_b/README.md so implementation handoff is ready for the following loop.
