Summary: Update vectorization docs and close out VECTOR-TRICUBIC-001 Phase G
Mode: Docs
Focus: [VECTOR-TRICUBIC-001] Vectorize tricubic interpolation and detector absorption — Phase G documentation closure
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts:
- reports/2025-10-vectorization/phase_g/<timestamp>/commands.txt
- reports/2025-10-vectorization/phase_g/<timestamp>/summary.md
- reports/2025-10-vectorization/phase_g/<timestamp>/collect.log
- reports/2025-10-vectorization/phase_g/<timestamp>/env.json
Do Now: [VECTOR-TRICUBIC-001] Phase G1 (doc updates + collect proof); run: pytest --collect-only -q
If Blocked: Capture decision notes in phase_g/summary.md and flag blocker in docs/fix_plan.md Attempts history
Priorities & Rationale:
- plans/active/vectorization.md:12 — Status snapshot lists Phase G as the only open gate before retiring the initiative
- plans/active/vectorization.md:83 — G1 checklist outlines the exact doc updates, collect-only proof, and CUDA handoff deliverables
- docs/fix_plan.md:3397 — Next Actions require executing Phase G1/G2 and documenting the CUDA follow-up delegation
- reports/2025-10-vectorization/phase_f/summary.md:1 — Consolidated metrics and references for tricubic/absorption work must feed the doc updates
- docs/development/testing_strategy.md:1 — Tier-1/2 guidance needs audit so tests reflect the new vectorized suites
- docs/development/pytorch_runtime_checklist.md:1 — Runtime guardrails have to mention the Phase F evidence and CUDA rerun expectation
How-To Map:
- Step 01: Confirm you are on feature/spec-based-2 with git status before editing
- Step 02: Create reports/2025-10-vectorization/phase_g/<timestamp>/ using mkdir -p and record the timestamp in summary.md
- Step 03: Start commands.txt and log every action (git rev-parse HEAD, editors invoked, pytest command)
- Step 04: Re-read plans/active/vectorization.md G1a–G1d to align scope before touching documentation
- Step 05: Open docs/architecture/pytorch_design.md and locate the vectorization section header for insertion
- Step 06: Draft a new subsection highlighting tricubic gather, batched polynomials, and detector absorption vectorization with citations to Phase C–F bundles
- Step 07: Mention the CUDA blocker explicitly and reference PERF-PYTORCH-004 in that subsection
- Step 08: Add nanoBragg.c citation numbers where you reference C code (CLAUDE Rule #11 compliance)
- Step 09: Save the doc and record the edit in commands.txt (include line numbers touched if helpful)
- Step 10: Edit docs/development/pytorch_runtime_checklist.md to expand the vectorization and device bullets with new evidence requirements
- Step 11: Add explicit mention that CUDA reruns resume once the device-placement defect (Attempt #14) clears
- Step 12: Include the new regression commands (tests/test_tricubic_vectorized.py, tests/test_at_abs_001.py -k "cpu") in the checklist notes
- Step 13: Review docs/development/testing_strategy.md; if guidance already covers the new tests, note the rationale in phase_g/summary.md
- Step 14: If testing_strategy needs updates, edit the Tier-1 and Tier-2 sections to name the new test modules and expected commands
- Step 15: Capture any choice not to edit testing_strategy as an explicit “no change required” entry in phase_g/summary.md with supporting reasoning
- Step 16: Update summary.md with bullet points for each modified doc, including git diff highlights and artifact citations
- Step 17: Record system metadata (uname -a, python --version, torch.__version__) and store as env.json in the phase_g directory
- Step 18: Run pytest --collect-only -q, tee the output to reports/.../collect.log, and confirm exit code 0
- Step 19: Append the pytest command and exit code to commands.txt for reproducibility
- Step 20: Review git diff to ensure only documentation, plan, and fix_plan changes appear—no src/ modifications
- Step 21: Update docs/fix_plan.md by adding the new Attempt entry referencing phase_g artifacts and refreshed docs
- Step 22: In the same Attempt, call out the CUDA follow-up delegation to PERF-PYTORCH-004 (Attempt #14) per plan row G2c
- Step 23: Edit plans/active/vectorization.md to flip G1a–G2c states as progress is made, culminating in a refreshed Status Snapshot
- Step 24: In commands.txt document each plan/fix_plan edit with the exact file path and rationale
- Step 25: Ensure phase_g/summary.md lists open follow-ups (CUDA rerun) and documents the verification command outcome
- Step 26: Verify docs/index.md references remain untouched to honor the Protected Assets rule
- Step 27: Run pytest --collect-only -q a second time only if edits change doc imports; otherwise rely on the single logged run
- Step 28: When satisfied, stage doc edits, plan update, and fix_plan update but defer commit until supervisor review (leave working tree staged or note in summary)
- Step 29: If unforeseen doc drift is uncovered (e.g., outdated gradients guidance), document it in summary.md and decide whether to fix now or schedule follow-up
- Step 30: Before handing back, double-check commands.txt and summary.md for completeness and clarity so future audits have a full trail
- Step 31: Screenshoot git diff or copy key snippets into summary.md so reviewers can trace changes quickly
- Step 32: Verify phase_g/summary.md links to both phase_f/summary.md and phase_e/summary.md for continuity
- Step 33: Note in summary.md whether testing_strategy was edited or explicitly left untouched with justification
- Step 34: Update docs/fix_plan.md Attempt description with bullet points covering each updated document and artifact path
- Step 35: After staging, run git diff --staged to confirm only intended files are included before finalizing the loop
- Step 36: Ensure commands.txt records the pytest command with absolute path or repository-relative path for reproducibility
- Step 37: Include the output of git rev-parse HEAD in commands.txt to tie artifacts to a commit
- Step 38: Add SHA256 checksums for summary.md and collect.log to the phase_g directory if time permits (optional but preferred)
- Step 39: Note any open questions for PERF-PYTORCH-004 in summary.md so the follow-up plan has immediate context
- Step 40: Leave TODO markers only in summary.md; avoid placing TODOs inside permanent documentation files
- Step 41: Re-run rg "phase_g" to verify no lingering TODO placeholders remain in source docs after edits
- Step 42: Capture git status output inside commands.txt at the end of the loop for auditability
- Step 43: Verify that env.json includes torch.cuda.is_available() result to document the CUDA blocker context
- Step 44: If you touch testing_strategy, update its table of contents anchors as needed to keep links valid
- Step 45: Before finishing, reread phase_g/summary.md to ensure it calls out any deferred follow-up tasks explicitly by plan/attempt ID
Pitfalls To Avoid:
- Do not modify simulator or test code during this documentation loop
- Keep edits ASCII and preserve headings, tables, and indentation conventions in every doc
- Cite nanoBragg.c snippets verbatim when referencing C implementation details
- Respect Protected Assets listed in docs/index.md; no deletions or renames
- Maintain explicit mention of CUDA follow-up rather than removing GPU guidance
- Reference exact report timestamps from Phase E/F bundles to avoid ambiguity
- Avoid ad-hoc helper scripts; use existing tooling and log invocations verbatim
- Do not skip the collect-only proof even though this is a docs loop
- Limit docs/fix_plan.md changes to one new Attempt entry describing the Phase G deliverables
- Leave clear notes in phase_g/summary.md for anything deferred to PERF-PYTORCH-004
Pointers:
- plans/active/vectorization.md:12
- plans/active/vectorization.md:83
- docs/fix_plan.md:3397
- docs/architecture/pytorch_design.md:1
- docs/development/pytorch_runtime_checklist.md:1
- docs/development/testing_strategy.md:1
- reports/2025-10-vectorization/phase_f/summary.md:1
- docs/bugs/verified_c_bugs.md:166
- specs/spec-a-core.md:204
- docs/architecture/c_function_reference.md:1
- docs/development/pytorch_runtime_checklist.md:20
- reports/2025-10-vectorization/phase_e/summary.md:1
- reports/2025-10-vectorization/phase_c/implementation_notes.md:1
- reports/2025-10-vectorization/phase_d/polynomial_validation.md:1
- reports/2025-10-vectorization/phase_f/validation/20251222T000000Z/summary.md:1
- docs/development/pytorch_runtime_checklist.md:40
- docs/architecture/README.md:1
- docs/index.md:1
- docs/development/implementation_plan.md:1
- plans/active/vectorization.md:1
Next Up: Coordinate with PERF-PYTORCH-004 once the device-placement fix lands and rerun the CUDA benchmarks/tests captured in phase_f/summary.md appendix
