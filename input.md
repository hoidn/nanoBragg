Summary: Refresh the φ=0 rotation memo with explicit spec citations and outline how we default to spec-compliant behavior while preserving a parity shim.
Mode: Docs
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md (rewrite), plans/active/cli-noise-pix0/plan.md (cross-link), docs/fix_plan.md (Attempt log), reports/2025-10-cli-flags/phase_l/rot_vector/collect_only.log
Do Now: CLI-FLAGS-003 L3k.3c.4 — update reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md with the spec-vs-C analysis, note the parity shim plan in docs/fix_plan.md, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py` and stash the log.
If Blocked: Capture the obstacle in docs/fix_plan.md Attempt history, save working notes under reports/2025-10-cli-flags/phase_l/rot_vector/blockers.md, and still run the collect-only selector for traceability.
Priorities & Rationale:
- specs/spec-a-core.md:211 — Normative requirement that every φ step rotates the reference lattice; memo must quote this to ground the fix.
- docs/bugs/verified_c_bugs.md:166 — C-PARITY-001 documents the carryover defect; use it to justify keeping the shim quarantined.
- src/nanobrag_torch/models/crystal.py:1097 — Current `_phi_last_cache` path proves PyTorch mirrors the bug; highlight this gap before code changes.
- plans/active/cli-noise-pix0/plan.md:6 — Plan now insists on spec compliance by default; the memo must align with it and spell out the toggle strategy.
- docs/development/testing_strategy.md:104 — SOP tells us to run collect-only for docs loops and to respect parity harness dependencies.
How-To Map:
- Rewrite diagnosis.md sections to include: (1) verbatim spec quote with line reference, (2) summary of the C bug evidence, (3) description of current PyTorch behavior with links to trace/code, (4) decision table for default spec path vs parity shim, (5) checklist updates gating code edits.
- Update plans/active/cli-noise-pix0/plan.md L3k.3c.4 guidance by linking the refreshed memo (no broader reflow needed).
- Append a new Attempt entry to docs/fix_plan.md for CLI-FLAGS-003 noting the memo refresh, references, and the pending action items.
- After documentation edits, execute `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py` and save the output to reports/2025-10-cli-flags/phase_l/rot_vector/collect_only.log.
Pitfalls To Avoid:
- Do not modify production code or tests while in Docs mode.
- Keep diagnosis.md diff surgical; avoid rewrapping unrelated sections.
- Cite exact line numbers for spec and bug references (no paraphrasing without anchors).
- Maintain `_phi_last_cache` description factual—no implementation decisions until the shim plan is ratified.
- Use existing reports directory hierarchy; no stray folders.
- Ensure fix_plan Attempt numbering increments correctly; never overwrite prior history.
- Remember to set KMP_DUPLICATE_LIB_OK=TRUE before running pytest.
- Skip full pytest runs; collect-only is sufficient per SOP.
- Leave device/dtype guidance intact—no CPU-only assumptions in examples.
- Document any open questions at the end of diagnosis.md to convert into future plan tasks.
Pointers:
- specs/spec-a-core.md:211
- docs/bugs/verified_c_bugs.md:166
- src/nanobrag_torch/models/crystal.py:1097
- plans/active/cli-noise-pix0/plan.md:6
- plans/active/cli-noise-pix0/plan.md:309
- docs/fix_plan.md:450
- docs/development/testing_strategy.md:104
Next Up (optional): 1) Draft the plan edits that introduce the parity toggle implementation sequence. 2) Prototype the code-side guard in Crystal.get_rotated_real_vectors after the memo lands.
