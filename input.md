Summary: Document φ-rotation parity evidence so future simulator fixes have a locked checklist and spec citations.
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_correction.md; reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md; docs/fix_plan.md; plans/active/cli-noise-pix0/plan.md; reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md; reports/2025-10-cli-flags/phase_l/rot_vector/test_collect_L3j.log; reports/2025-10-cli-flags/phase_l/rot_vector/attempt_notes.md
Do Now: CLI-FLAGS-003 Phase L3j.1–L3j.2 — pytest --collect-only -q
If Blocked: Capture a short narrative in reports/2025-10-cli-flags/phase_l/rot_vector/attempt_notes.md, stash any harness stdout under the same folder, and note the blocker plus file paths in docs/fix_plan.md Attempts for traceability.

Context Recap:
- Attempt #93 proved MOSFLM base vectors align within float32 precision and shifted suspicion to φ rotation (H5) per reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md.
- L3a–L3i tasks are ✅; per-φ traces and spindle audits exist, but no implementation checklist yet guards the upcoming fix.
- The supervisor command relies on phisteps=10, osc=0.1, so φ sampling at 0°, 0.05°, 0.1° captures the full motion envelope.
- docs/fix_plan.md Next Actions still reference L3i instrumentation; updating them prevents future loops from repeating now-complete evidence tasks.
- Long-term Goal #1 (run C vs PyTorch parity command) is blocked until φ rotation parity is restored, making this documentation loop a prerequisite.
- Vectorization backlog is paused; documenting CLI progress clarifies when resources can return to VECTOR-TRICUBIC-001.
- Protected Assets rule demands we leave docs/index.md references untouched; all new content must live in allowed directories (plans/, docs/, reports/).
- Mode Parity forbids running full pytest; only collect-only validation is expected after doc edits.
- Prior evidence loops already generated heavy traces; reuse them, avoid generating new large logs unless absolutely necessary.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:260 keeps Phase L3 sequencing; finishing memo/checklist flips L3j rows to [D], signalling readiness for code changes.
  Tie the memo content directly to the plan so future readers map doc artifacts to plan IDs without guessing.
- docs/fix_plan.md:450 needs Next Actions aligned to L3j.1–L3j.3; without this, automation scripts may queue stale instrumentation tasks.
  When updating fix_plan, cite artifact paths explicitly to maintain reproducibility.
- specs/spec-a-cli.md:1 enumerates CLI semantics; referencing §3.3 prevents documentation drift when summarising pix0 overrides and noise suppression expectations.
  Connect -nonoise behavior with the existing plan to remind reviewers the flag already works at CLI level.
- docs/architecture/detector.md:35 supplies BEAM/SAMPLE formulas; quoting them in the checklist anchors tolerances to the geometry spec and clarifies which components are meter-based.
  Include note about how these formulas interact with CUSTOM convention when pix0 overrides are present.
- docs/development/c_to_pytorch_config_map.md:42 documents implicit pivot/unit rules; the memo must cite it to explain why φ rotation is the remaining unmatched stage and to avoid re-litigating pivot logic.
  Highlight the pivot implications (twotheta implies SAMPLE) so checklist readers recall the default.
- docs/development/testing_strategy.md:120 standardises targeted pytest usage; the checklist needs explicit selectors drawn from this guidance to stay in compliance with testing SOP.
  Mention Tier 1 parity context to tie the collect-only run to spec-driven expectations.
- reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md:12 tracks current hypothesis ordering (H5 primary, H6/H7 secondary); memo must echo this so later loops continue where we left off.
  Carry over the quantitative deltas (e.g., k_frac mismatch, F_latt sign flip) into the new memo section.
- reports/2025-10-cli-flags/phase_l/rot_vector/c_trace_mosflm.log:63 and trace_py_rot_vector.log:16 form the evidence pair; quote them in the memo to justify threshold choices.
  Keep raw precision (up to 1e-12) when transcribing values.
- prompts/supervisor.md:18 houses the authoritative CLI command; the checklist should reference it verbatim for nb-compare reproduction to avoid parameter drift.
  Clarify environment variables (NB_C_BIN, KMP_DUPLICATE_LIB_OK) alongside the command.
- plans/active/vectorization.md:31 is non-blocking but stays queued; documenting CLI parity progress clarifies when we can pivot to tricubic work without mixing initiatives.
  Mention this in memo conclusions for cross-team visibility.

How-To Map:
- Re-read Attempt #93 artifacts (c_trace_mosflm.log, mosflm_matrix_diff.md) and extend mosflm_matrix_correction.md with a "Post-L3i Findings" section stating H3 is ruled out, H5 remains primary, H6/H7 secondary.
  Cite golden_suite_generator/nanoBragg.c:2050-2199 for C reference and src/nanobrag_torch/models/crystal.py:568-780 for PyTorch behavior.
- Summarise quantitative deltas: include b_Y delta 1.35e-07 Å, k_frac shift ≈0.018, F_latt sign flip, linking each to trace line numbers.
  Explain how these deltas propagate into intensity mismatches (I_before_scaling ~7.13e5 vs 9.44e5) referencing scaling logs.
- Outline φ sampling requirements (0°, 0.05°, 0.1°) and relate them to phisteps, osc, and beamsize to justify coverage.
  Note that per-φ JSON already exists; instruct checklist users to regenerate it only after applying code changes.
- Draft fix_checklist.md with table `[ID | Requirement | Owner | Artifact Path | Threshold / Notes]` containing at least three rows: per-φ harness rerun, targeted pytest, nb-compare ROI.
  For each row, list spec/doc references (specs/spec-a-cli.md §3.3, docs/debugging/debugging.md §Parallel Trace, docs/development/testing_strategy.md §1.5) and required thresholds (≤1e-6 relative, correlation ≥0.9995, etc.).
- Include an entry reminding future implementers to update docs/index.md references only if new artifacts become canonical, respecting Protected Assets Rule.
- After doc edits, run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` from repo root, capture output into reports/2025-10-cli-flags/phase_l/rot_vector/test_collect_L3j.log, and mention it in fix_plan Attempt.
  Do not upgrade to full pytest; collect-only suffices for import validation in this planning loop.
- Update docs/fix_plan.md CLI-FLAGS-003 Attempts with a new entry (“Attempt #94 — documentation loop”) summarising memo updates, checklist creation, and collect-only log.
  In Observations, reiterate H5 dominance and note that implementation is blocked pending checklist completion; list artifact paths in Artifacts subsection.
- Adjust plans/active/cli-noise-pix0/plan.md L3j guidance if the checklist adds new thresholds or artifact directories; maintain table formatting and state `[D]` only after verifying docs exist.
  Keep plan references to spec and doc paths aligned with actual file names.
- Commit only doc/report changes; leave src/ untouched. Prepare for future implementation loop by mentioning the new artifacts in galph_memory once done.

Pitfalls To Avoid:
- Do not modify src/ or scripts/ code; this is strictly a planning/documentation turn.
- Avoid regenerating large traces; reuse existing logs to quote values unless a blocker demands reruns.
- Keep all new doc references unit-consistent (meters for geometry, Å for physics) to avoid confusion.
- Do not collapse plan tables or reorder completed tasks; append notes if necessary.
- Skip running nb-compare or the supervisor command; checklist should document commands without executing them this loop.
- Guard against losing precision when transcribing values; use full numeric strings from logs.
- Respect Protected Assets (docs/index.md references); do not rename or delete listed files.
- Avoid editing prompts/main.md or automation harness scripts; not part of this scope.
- Do not relax tolerances below spec thresholds; maintain ≤1e-6 relative for scaling factors.
- Refrain from adding TODO markers without context; reference plan IDs or spec clauses when noting follow-ups.
- Ensure collect-only command runs with KMP_DUPLICATE_LIB_OK=TRUE to avoid MKL crashes; mention env var in logs.
- When editing markdown, keep ASCII characters only; follow repository editing constraints.

Pointers:
- specs/spec-a-cli.md:1 — Normative CLI rules for -nonoise and pix0 overrides.
- specs/spec-a-core.md:400 — Lattice factor equations and acceptance criteria to cite for F_latt thresholds.
- docs/architecture/detector.md:35 — pix0_vector derivation (BEAM/SAMPLE formulas) referenced in memo/checklist.
- docs/development/c_to_pytorch_config_map.md:42 — Detector pivot/unit mapping tied to φ rotation decisions.
- docs/development/testing_strategy.md:120 — Targeted pytest workflow (Tier 1 parity guidance) for checklist selectors.
- docs/debugging/debugging.md:24 — Parallel trace SOP; cite when directing per-φ harness reruns.
- plans/active/cli-noise-pix0/plan.md:271 — Detailed definitions of L3j.1–L3j.3 tasks to mirror in doc updates.
- docs/fix_plan.md:450 — CLI-FLAGS-003 ledger entry awaiting Attempt #94 documentation.
- reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md:12 — Current hypothesis ranking (H5 primary).
- reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_diff.md:40 — Component-level deltas backing the memo.
- reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_env.json:1 — Environment snapshot for reproducibility metadata.
- prompts/supervisor.md:18 — Exact supervisor command parameters; include in checklist.
- reports/2025-10-cli-flags/phase_l/scaling_validation/analysis_20251119.md:22 — Context for k_frac divergence to restate.
- reports/2025-10-cli-flags/phase_l/rot_vector/spindle_audit.log:5 — Evidence ruling out spindle normalization; mention in memo recap.
- reports/2025-10-cli-flags/phase_l/rot_vector/per_phi/trace_py_scaling_20251119_per_phi.json:1 — JSON structure to reference in checklist instructions.
- history/2025-10/cli-flags/README.md:1 — Prior archival summary if cross-links help orient reviewers (optional).

Next Up: 1) Once L3j checklist is in place, schedule the implementation loop targeting φ rotation parity per plan Phase L3; 2) If time remains, gather outstanding evidence for VECTOR-TRICUBIC-001 Phase C1 (gather fallback semantics) without touching production code.

Evidence Reminders:
- Keep numeric precision consistent (≥12 significant digits) when quoting trace outputs; mismatched rounding complicates parity comparisons later.
- When saving collect-only log, prepend timestamp and git SHA at top for reproducibility (see reports/2025-10-cli-flags/phase_l/rot_vector/test_collect_template.txt if helpful).
- Cross-link new memo sections with galph_memory entry once committed so future supervisor loops pick up the context without rereading whole plan.
- Ensure nb-compare command in checklist mentions expected output directory and correlation thresholds (≥0.9995) so implementer knows pass criteria before running it.
- If you identify any missing documentation references while drafting, note them inline with TODO[doc] markers tied to plan IDs for easy follow-up.
