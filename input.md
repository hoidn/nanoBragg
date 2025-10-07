Summary: Capture spec-vs-parity guidance for φ=0 so we stop perpetuating the C carryover bug.
Mode: Docs
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling_phi0.py
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md (refresh), docs/fix_plan.md (Attempt log)
Do Now: CLI-FLAGS-003 L3k.3c.4 — update reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md with spec-vs-parity analysis and log the attempt; then run `pytest --collect-only -q tests/test_cli_scaling_phi0.py`.
If Blocked: Record the blocker in docs/fix_plan.md Attempt history, capture the collect-only output, and drop the raw notes under reports/2025-10-cli-flags/phase_l/rot_vector/blockers.md for follow-up.
Priorities & Rationale:
- specs/spec-a-core.md:211 — Spec mandates φ sampling uses fresh rotations each step; we must cite this to justify rejecting the carryover.
- docs/bugs/verified_c_bugs.md:166 — C-PARITY-001 documents the C bug; the memo needs this pointer to keep parity work quarantined.
- src/nanobrag_torch/models/crystal.py:1115 — Current implementation caches φ=last and reuses it, so the documentation must call out this divergence before we change code.
- plans/active/cli-noise-pix0/plan.md:309 — Plan still tells us to emulate the carryover; the refreshed memo must drive the upcoming plan edit and guard future attempts.
- docs/development/testing_strategy.md:1, 103 — Testing SOP requires collect-only confirmation for docs loops and references the parity harness; include the selector so the guard stays green.
How-To Map:
- Update reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md with sections covering: (1) normative spec quote, (2) summary of C-PARITY-001 evidence, (3) current PyTorch behavior, (4) compatibility plan (e.g., default spec path vs optional parity shim), and (5) checklist items that must flip before code edits.
- Cross-link the memo from plans/active/cli-noise-pix0/plan.md (L3k.3c.4 guidance) and add an Attempt entry in docs/fix_plan.md citing the refreshed diagnosis.
- After edits, run `pytest --collect-only -q tests/test_cli_scaling_phi0.py` and stash the log under reports/2025-10-cli-flags/phase_l/rot_vector/collect_only.log.
- Keep environment variable `KMP_DUPLICATE_LIB_OK=TRUE` exported in your shell before invoking pytest (per docs/development/testing_strategy.md §1.4).
Pitfalls To Avoid:
- Do not touch production code or tests beyond documentation this loop.
- Do not dilute the spec quote—cite exact language and line references.
- Avoid reflowing unrelated sections of diagnosis.md; keep diff tight for easier review.
- Respect Protected Assets (docs/index.md paths) when linking artifacts.
- Do not run the full pytest suite; collect-only selector is sufficient per SOP.
- Maintain device/dtype neutrality in any illustrative snippets (no `.cpu()` assumptions).
- Keep fix_plan.md attempt numbering consistent; append, don’t overwrite history.
- Store artifacts under the existing reports/2025-10-cli-flags tree; no ad-hoc directories.
- Document any open questions at the end of diagnosis.md so we can convert them into plan tasks next loop.
- If you need additional context, reference existing traces rather than regenerating them this turn.
Pointers:
- specs/spec-a-core.md:211
- docs/bugs/verified_c_bugs.md:166
- src/nanobrag_torch/models/crystal.py:1115
- plans/active/cli-noise-pix0/plan.md:5
- plans/active/cli-noise-pix0/plan.md:309
- docs/development/testing_strategy.md:103
Next Up (optional): 1) Draft the plan revisions that split default spec behavior from parity shim. 2) Prototype the toggle in Crystal.get_rotated_real_vectors once the memo lands.
