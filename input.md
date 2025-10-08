Summary: Fold Attempt #171 trace tooling evidence into the phi-carryover diagnosis notes and close plan row M2g.6 cleanly so cache analysis can resume.
Mode: Docs
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — plans/active/cli-noise-pix0/plan.md M2g.6 documentation sync
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling_phi0.py tests/test_phi_carryover_mode.py
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md; plans/active/cli-noise-pix0/plan.md; docs/fix_plan.md attempts log
Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — pytest --collect-only -q tests/test_cli_scaling_phi0.py tests/test_phi_carryover_mode.py
If Blocked: 1) Capture the blocker in docs/fix_plan.md attempts (see line 465) with timestamp + symptoms; 2) create reports/2025-10-cli-flags/phase_l/scaling_validation/cache_index_audit/<timestamp>/blocked.md summarising why M2g.6 stalled and what evidence is missing; 3) ping supervisor in galph_memory.md follow-up section.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:27 records Attempt #171 evidence; we must acknowledge it formally before touching cache diagnostics.
- plans/active/cli-noise-pix0/plan.md:115 keeps M2g.6 open, blocking the remainder of Phase M2; synchronising documentation removes that gate.
- docs/fix_plan.md:463 names the documentation sync as the next actionable step after the metrics gate, ensuring ledger alignment.
- docs/fix_plan.md:464-465 escalates the cache index audit; finishing M2g.6 prevents duplicated effort when that work starts.
- reports/2025-10-cli-flags/phase_l/trace_tooling_patch/20251008T175913Z/summary.md:1 holds the CPU/CUDA parity proof we must cite for reproducibility.
- reports/2025-10-cli-flags/phase_l/trace_tooling_patch/20251008T175913Z/run_metadata.json:1 documents environment details to embed in the memo.
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md:1 already aggregates prior Option B findings; keeping a single source of truth avoids drift.
- specs/spec-a-core.md:204-240 defines the spec rotation pipeline; the doc update must restate the contrast with C’s carryover bug.
- docs/bugs/verified_c_bugs.md:166 anchors C-PARITY-001; referencing it keeps parity shim rationale explicit.
- docs/development/testing_strategy.md:82-115 reiterates the evidence-first workflow; the memo should link to it when explaining why tooling proof precedes physics edits.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T174753Z/scaling_validation_summary.md:1 shows the current `I_before_scaling` failure; reiterating that status in the memo keeps the open gate visible.
- reports/2025-10-cli-flags/phase_l/scaling_validation/lattice_hypotheses.md:1 captures earlier diagnostic notes; reference it so the narrative stays chronological.
How-To Map:
- export AUTHORITATIVE_CMDS_DOC=docs/development/testing_strategy.md
- pytest --collect-only -q tests/test_cli_scaling_phi0.py tests/test_phi_carryover_mode.py
- ts=$(date -u +%Y%m%dT%H%M%SZ)
- note_dir=reports/2025-10-cli-flags/phase_l/scaling_validation && target_doc=$note_dir/phi_carryover_diagnosis.md
- grep -n "Attempt #171" $note_dir/phi_carryover_diagnosis.md || true  # validate insertion point (look near Option B section)
- Append a new subsection titled "## 20251008T175913Z — Trace Tooling Verification" describing CPU+CUDA runs, referencing summary.md, trace_cpu.log, trace_cuda.log, commands.txt, run_metadata.json, sha256.txt, and restating spec vs c-parity expectations.
- Explicitly link the subsection to specs/spec-a-core.md:204-240, docs/bugs/verified_c_bugs.md:166, and the Option B design memo in reports/2025-10-cli-flags/phase_l/scaling_validation/20251210_optionB_design/optionB_batch_design.md.
- Capture bullet points covering: instrumentation reuse rule, device/dtype neutrality confirmation, and parity thresholds (≤5e-5 for c-parity, ≤1e-6 for spec).
- Update plans/active/cli-noise-pix0/plan.md M2g.6 row to `[D]`, citing Attempt #171 and the refreshed diagnosis section; include artifact paths and call out that metrics gate M2i.2 remains open.
- Ensure plans/active/cli-noise-pix0/plan.md Next Actions list (lines 20-34) no longer references M2g.6 once done; keep entries for cache index audit and Phase N preparation untouched.
- Add a docs/fix_plan.md attempts entry under [CLI-FLAGS-003] summarising the memo update: include timestamp, plan row state change, collector command, and the new diagnosis subsection heading.
- Re-run git status; confirm only documentation + plan + fix_plan files staged.
- Produce a short changelog snippet (to be used later) capturing key bullets: evidence cited, spec references, plan row closure.
- After edits, rerun pytest --collect-only -q tests/test_cli_scaling_phi0.py tests/test_phi_carryover_mode.py to ensure imports still succeed.
- Run rg -n "Trace Tooling" $note_dir/phi_carryover_diagnosis.md to double-check that the new heading and citations render correctly.
- Append a brief note to reports/2025-10-cli-flags/phase_l/scaling_validation/README.md (if present) pointing to the updated diagnosis subsection for future investigators.
- Use python -m json.tool reports/2025-10-cli-flags/phase_l/trace_tooling_patch/20251008T175913Z/run_metadata.json to confirm the JSON is still valid before referencing values in prose.
- git diff --stat to verify scope, followed by git diff to sanity-check markdown formatting before handing back to supervisor.
- Prepare commit message draft in notes (no commit yet): "CLI-FLAGS-003: document trace tooling evidence".
- Verify that docs/bugs/verified_c_bugs.md still references the parity shim section once your edits are complete (no duplication required).
- Run sed -n '1,160p' $note_dir/phi_carryover_diagnosis.md after edits to confirm the new section sits near previous Option B documentation.
- Record the pytest collect-only output path in docs/fix_plan.md attempt bullet so future loops know which command was used.
- Cross-check reports/2025-10-cli-flags/phase_l/scaling_validation/implementation_notes.md for an existing heading; create one if missing and log the memo update there.
- Document in galph_memory.md (only if new blockers arise) the date, command, and artifact path for trace-tooling evidence for continuity.
- Save a local diff snapshot (git diff > /tmp/m2g6_doc_patch.diff) before reverting any temporary edits; delete the temp file after review.
- Confirm that no new directories were created under reports/ beyond the prescribed ones by running find reports -maxdepth 4 -type d | sort | tail; remediate any stray folders.
- Validate markdown lint (if available) with markdownlint-cli2 '**/*.md' --ignore node_modules || true to spot obvious formatting issues (do not fail the loop if the tool is unavailable).
- Note in docs/fix_plan.md whether the collect-only pytest command exited non-zero; include stderr snippet if failures occur.
- Review commit history (git log -1) to cite the correct git SHA in the docs/fix_plan attempt entry.
- Update reports/2025-10-cli-flags/phase_l/scaling_validation/CHANGELOG.md if that file exists; append a bullet referencing the new diagnosis subsection.
- After verifying all updates, remove /tmp/m2g6_doc_patch.diff to keep local filesystem clean: rm -f /tmp/m2g6_doc_patch.diff.
Pitfalls To Avoid:
- No simulator or harness code edits; this loop stays documentation-only.
- Maintain ASCII formatting and heading hierarchy in phi_carryover_diagnosis.md—no smart quotes or rogue whitespace.
- Cite artifact paths verbatim (relative paths) and include timestamps; vague references hinder reproducibility.
- Keep Protected Assets intact; the memo lives outside docs/index.md protected list, but double-check before touching anything else.
- Ensure the memo distinguishes spec versus c-parity tolerances; ambiguity will cause parity regressions later.
- Avoid paraphrasing C snippets—reference existing excerpts per CLAUDE Rule #11 rather than restating them from memory.
- Do not mark M2g.6 [D] until the memo and ledger entries are genuinely refreshed.
- When editing markdown tables in plan/fix_plan, preserve pipe alignment and `[ ]`/`[P]`/`[D]` syntax exactly.
- Explicitly mention that M2i.2 metrics remain red; we are not closing the physics gate yet.
- Re-run collect-only tests after documentation edits to catch accidental import regressions.
- Store any scratch calculations outside the repo; no temporary files under reports/ beyond the prescribed locations.
- Make sure the new diagnosis subsection notes that no new code landed with Attempt #171, so future engineers know evidence-only loops exist.
- Do not edit lattice_hypotheses.md during this pass; it will be updated once cache index diagnostics complete.
- Avoid duplicating evidence paths across multiple bullets—cite them once in the memo and once in fix_plan for clarity.
- Keep the Option B terminology consistent with the design memo; do not introduce new labels without updating that document too.
- Mention that gradcheck evidence (Attempt #167) is unaffected—avoid implying new gradient work happened.
- Retain chronological ordering of attempts within phi_carryover_diagnosis.md; add the new section after previously logged 2025-12-10 entry.
- When editing docs/fix_plan.md attempts, maintain third-level indentation (two spaces) for bullet structure.
- Avoid referencing unpublished artifacts; everything cited must exist under reports/2025-10-cli-flags/phase_l/.
Pointers:
- plans/active/cli-noise-pix0/plan.md:27
- plans/active/cli-noise-pix0/plan.md:115
- plans/active/cli-noise-pix0/plan.md:30
- docs/fix_plan.md:451
- docs/fix_plan.md:463
- docs/fix_plan.md:464
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md:1
- reports/2025-10-cli-flags/phase_l/trace_tooling_patch/20251008T175913Z/summary.md:1
- reports/2025-10-cli-flags/phase_l/trace_tooling_patch/20251008T175913Z/run_metadata.json:1
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251210_optionB_design/optionB_batch_design.md:1
- specs/spec-a-core.md:204
- docs/bugs/verified_c_bugs.md:166
- docs/development/testing_strategy.md:82
- docs/architecture/detector.md:412
- galph_memory.md:120 (latest directive log for CLI-FLAGS-003 context)
- reports/2025-10-cli-flags/phase_l/scaling_validation/lattice_hypotheses.md:1
- reports/2025-10-cli-flags/phase_l/scaling_validation/README.md:1
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T174753Z/scaling_validation_summary.md:1
- reports/2025-10-cli-flags/phase_l/scaling_validation/implementation_notes.md:1
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T165745Z_carryover_cache_validation/summary.md:1
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251210_optionB_design/README.md:1
- docs/architecture/pytorch_design.md:120
- docs/development/pytorch_runtime_checklist.md:14
Next Up:
- 1. Launch the cache index audit bundle (Next Actions item 2) once the documentation sync lands, focusing on `(slow, fast)` lookup evidence.
- 2. Sketch nb-compare harness commands and data staging steps for Phase N so the parity rerun can execute immediately after VG-2 is fixed.
