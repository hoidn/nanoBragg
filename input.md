Summary: Build the authoritative SOURCE-WEIGHT spec-vs-C decision memo so future loops can stop chasing C parity.
Mode: Docs
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence
Artifacts: reports/2025-11-source-weights/phase_e/<STAMP>/{spec_vs_c_decision.md,commands.txt,collect.log,env.json,notes.md}
Do Now: Execute SOURCE-WEIGHT-001 Phase E1 by drafting spec_vs_c_decision.md, validating the targeted pytest selectors with --collect-only, and recording all commands + environment metadata in the new reports directory.
Do Now Steps:
- Step 1 — Create a fresh timestamp via `date -u +%Y%m%dT%H%M%SZ` and make reports/2025-11-source-weights/phase_e/<STAMP>/.
- Step 2 — Inside that folder capture commands in commands.txt (shell transcripts, pytest selectors, git status summary).
- Step 3 — Run pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence and pipe stdout to collect.log.
- Step 4 — Capture environment metadata (Python, torch, git commit, NB_C_BIN value) into env.json using a small Python snippet.
- Step 5 — Draft spec_vs_c_decision.md with structured sections: Summary, Spec Citations, C Evidence, PyTorch Evidence, Impacted Tests, Expected Outcomes, Next Steps.
- Step 6 — Include a table that lists each impacted test (current assertion vs proposed assertion vs acceptance tolerance).
- Step 7 — Quote specs/spec-a-core.md:151 verbatim; annotate with path references so future readers can trace the authority.
- Step 8 — Summarise the key findings from reports/2025-11-source-weights/phase_e/20251009T195032Z/trace_source2/trace_notes.md.
- Step 9 — Add a paragraph documenting the documented C bug ID (`C-PARITY-001`) and how it manifests in TC-D1/TC-D3 metadata.
- Step 10 — Close the memo with explicit decision statements: what remains acceptable, what becomes expected divergence, what tests must change, and which downstream plans unblock.
If Blocked:
- Record the partial findings in notes.md within the same reports directory, including which data was missing or ambiguous.
- Update docs/fix_plan.md `[SOURCE-WEIGHT-001]` Attempts with the blocked context so we have breadcrumbs for the next loop.
Priorities & Rationale:
- specs/spec-a-core.md:151 — Requirement that weights are read but ignored must be cited to justify spec-first stance.
- docs/development/c_to_pytorch_config_map.md:6 — Reinforces configuration parity rules and the weight-handling mandate.
- plans/active/source-weight-normalization.md:24 — Phase E checkpoints define the memo as the current gate.
- docs/fix_plan.md:4035 — Next Actions now depend on memorialising the decision before any implementation resumes.
- plans/active/vectorization.md:12 — Vectorization remains blocked pending this memo; highlighting dependency keeps the roadmap consistent.
How-To Map:
- Command: `pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence > reports/.../collect.log`.
- Command: `python - <<'PY'` block to emit env.json with python version, torch version, git rev-parse HEAD, NB_C_BIN, NB_RUN_PARALLEL.
- Reference: use rg to gather snippets, e.g., `rg -n "source_weights" src/nanobrag_torch -g"*.py"` and log results in commands.txt.
- Memo Outline: start with Executive Summary (3 bullet sentences), then Normative Sources, then Evidence (C trace, PyTorch diagnostics), followed by Impacted Tests, then Decision & Consequences, then Next Steps/Owners.
- Cite Artifacts: reference prior reports (phase_a, phase_b, phase_d, trace_source2) with paths so the memo is self-contained.
- After memo completion, update docs/fix_plan.md `[SOURCE-WEIGHT-001]` Attempts with bullet: timestamp, artifact path, summary of decision, note that C divergence is expected.
- Keep `KMP_DUPLICATE_LIB_OK=TRUE` mention in notes for future code loops even though this turn is documentation-only.
- Ensure all numbers (corr, sum_ratio) copied from prior reports retain scientific notation/precision when embedded in the memo.
- Use Markdown tables for comparison (columns: Scenario, PyTorch metric, C metric, Delta, Interpretation).
- After drafting, run `mdformat spec_vs_c_decision.md` if available or manually ensure consistent indentation.
- Consider adding a short appendix listing outstanding questions (e.g., divergence placeholder handling) for Phase F.
- Capture git status output into commands.txt after memo completion to show clean tree or staged files.
- If you cite numeric deltas, include both ratio and absolute difference for clarity.
- Note any assumptions about fixture locations (reports/2025-11-source-weights/fixtures/two_sources.txt) and verify existence via `ls` command.
- Tag each references section in the memo with relative paths (../phase_d/..., etc.) so readers can navigate easily.
- Add a references list at the end of the memo with bullet entries for each artifact and spec section.
- End commands.txt with a checksum (`shasum`) of spec_vs_c_decision.md to help future runners detect drift.
- Consider using `pandoc` locally (if installed) to preview the memo; note the command in notes.md even if pandoc missing.
- Double-check that commands.txt logs absolute paths for fixtures (two_sources.txt) so reproduction remains trivial.
Pitfalls To Avoid:
- Do not modify simulator, tests, or configs during this documentation loop.
- Avoid speculative fixes; the memo must stick to observed evidence and spec quotes.
- Do not remove or rewrite existing artifacts—reference them instead.
- Resist the urge to chase fresh C runs; summarise existing data unless explicit gap emerges.
- Keep memo language unambiguous—state whether behaviour is expected, bug, or follow-up.
- Ensure any TODOs are framed as Phase F/G work items, not implicit assumptions.
- Maintain ASCII only; avoid fancy Unicode in memo tables or bullet labels.
- Do not commit the reports directory; leave it referenced via fix_plan and memo content.
- Keep pytest collect-only output for future validation; do not delete.
- Double-check git status before finishing to ensure only intended files are touched.
- Keep docstrings and comments untouched; memo only.
- Do not move fixtures; reference them and verify presence.
- Avoid editing docs/fix_plan.md until memo is ready so the Attempt entry references final paths.
- Make sure commands.txt is chronological; note retries separately.
Pointers:
- specs/spec-a-core.md:142
- docs/development/c_to_pytorch_config_map.md:6
- plans/active/source-weight-normalization.md:24
- docs/fix_plan.md:4035
- reports/2025-11-source-weights/phase_e/20251009T195032Z/trace_source2/trace_notes.md
- reports/2025-11-source-weights/phase_d/20251009T102319Z/divergence_analysis.md
- tests/test_cli_scaling.py:252
- tests/test_cli_scaling.py:473
- docs/architecture/pytorch_design.md:1
- plans/active/vectorization.md:12
Next Up:
- Phase F design packet: draft test_plan.md enumerating new assertions and metric tolerances once the decision memo is merged.
- Step 11 — Summarise the legacy attempts (Attempts #19-#21) in a short chronology so future readers know why we deemed parity impossible.
- Step 12 — Include a risk section: outline consequences if someone reverts to C parity, and note testing gaps to be covered in Phase F.
- Step 13 — Add an explicit "Decision" call-out block quoting the exact wording to use in fix_plan and galph_memory (copy/paste ready).
- Step 14 — Cross-link the memo to plans/active/vectorization.md Phase A so the dependency trail is obvious.
- Step 15 — Review spelling/grammar and ensure the memo renders under GitHub Markdown preview (tables, code fences, bullet nesting).
- Step 16 — Before leaving the reports directory, `ls -R` and append the listing to commands.txt for reproducibility.
