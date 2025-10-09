Summary: Capture Tier-2 gradcheck baseline evidence so the pending misset/beam gradchecks rest on a documented coverage audit with reproducible logs and consistent plan alignment.
Mode: none
Focus: docs/fix_plan.md §[AT-TIER2-GRADCHECK]
Branch: feature/spec-based-2
Mapped tests: env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest tests/test_suite.py::TestTier2GradientCorrectness -vv
Artifacts: reports/gradients/<STAMP>/tier2_baseline.md
Artifacts: reports/gradients/<STAMP>/gradcheck_phaseA.log
Artifacts: reports/gradients/<STAMP>/commands.txt
Artifacts: reports/gradients/<STAMP>/env.json
Artifacts: reports/gradients/<STAMP>/sha256.txt
Artifacts: plans/active/gradcheck-tier2-completion/plan.md (Phase A rows → [D])
Artifacts: docs/fix_plan.md (Attempt logging Phase A completion)
Artifacts: reports/gradients/<STAMP>/collect_only.log (optional but recommended)
Context Reminders:
- Phase A is evidence-only: no simulator/test code edits; focus on documentation, logs, and reproducibility bundles per plan checklist.
- The audit must enumerate existing gradcheck coverage with `file:line` anchors and explicitly highlight the remaining spec gaps (misset_rot_x, lambda_A, fluence).
- Bundle naming should mirror prior gradient evidence (e.g., `reports/gradients/20251015T...`) for continuity and straightforward archival diffing.
- `AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md` lists canonical selectors; cite it verbatim in tier2_baseline.md under Commands.
- torch.compile must remain disabled via `NANOBRAGG_DISABLE_COMPILE=1`; mention the rationale (torch.compile backward bugs) in the baseline write-up.
- Plan Phase B/C depend on environment-alignment decisions recorded now; document whether both `NB_DISABLE_COMPILE` and `NANOBRAGG_DISABLE_COMPILE` are set or aliased.
- Protected Assets (docs/index.md) include input.md, loop.sh, supervisor.sh; ensure none are modified while documenting.
- Use UTC timestamps for bundles so archives sort chronologically irrespective of local timezone.
- If gradcheck emits warnings, capture them verbatim in the log and summarize in tier2_baseline.md with mitigation notes or follow-up actions.
- Maintain vectorization/dtype guardrails referenced in docs/development/pytorch_runtime_checklist.md when describing the test setup (CPU float64, compile disabled).
- Confirm there are no lingering references to the retired phi carryover shim in gradient tests while auditing coverage; note any findings.
Do Now: AT-TIER2-GRADCHECK Phase A baseline audit — draft `reports/gradients/<STAMP>/tier2_baseline.md`, capture commands/env plus the pytest log for `env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest tests/test_suite.py::TestTier2GradientCorrectness -vv`, then flip plan rows A1–A3 and add an Attempt in docs/fix_plan.md referencing the new bundle.
If Blocked: Record failing selector output in `reports/gradients/<STAMP>/gradcheck_blockers.log`, include traceback + env details in tier2_baseline.md, leave plan rows open, and document the stall in docs/fix_plan.md Attempt before escalating to supervisor.
Priorities & Rationale:
- plans/active/gradcheck-tier2-completion/plan.md:17 — Phase A checklist (A1 catalogue, A2 baseline log, A3 env alignment) is the gate to progress; complete each subtask explicitly with citations.
- plans/active/gradcheck-tier2-completion/plan.md:31 — Phase B prerequisites depend on Phase A bundle being logged; document readiness for misset gradcheck.
- docs/fix_plan.md:8 — Active focus list calls out `[AT-TIER2-GRADCHECK]` Phase A as next action; satisfying it reduces top-level risk.
- docs/fix_plan.md:3350 — Item narrative reiterates that misset_rot_x, lambda_A, and fluence remain uncovered; baseline evidence must call this out to maintain accountability.
- docs/development/testing_strategy.md:385 — Spec §4.1 enumerates required gradcheck parameters; cite this section when documenting uncovered items.
- docs/development/testing_strategy.md:420 — Tiered gradient methodology emphasises float64 CPU runs; align the baseline with that requirement and note compliance.
- arch.md:318 — Differentiability guidelines demand compile-disabled float64 gradchecks; capture compliance decisions in the audit.
- docs/development/pytorch_runtime_checklist.md:42 — Device/dtype neutrality checklist requires CPU evidence with CUDA follow-up noted; mark CUDA as pending by design in tier2_baseline.md.
- galph_memory.md (latest entry) — Supervisor expectation stresses baseline evidence before implementation; this bundle closes that loop.
- specs/spec-a-core.md:211 — Reference fresh φ rotation pipeline in context to show why gradient coverage matters for orientation parameters.
- docs/bugs/verified_c_bugs.md:166 — Confirms phi-carryover bug is C-only; mention this while noting gradient tests now rely solely on spec-compliant rotations.
Reference Commands:
- export KMP_DUPLICATE_LIB_OK=TRUE
- export NANOBRAGG_DISABLE_COMPILE=1
- env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest tests/test_suite.py::TestTier2GradientCorrectness -vv
- pytest --collect-only -q tests/test_suite.py::TestTier2GradientCorrectness
- python - <<'PY' ... (dump env metadata to env.json)
- sha256sum reports/gradients/<STAMP>/* > reports/gradients/<STAMP>/sha256.txt
How-To Map:
- Step 1: Export `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; create `reports/gradients/${STAMP}/` and seed tier2_baseline.md with a header detailing initiative, date, git commit placeholder, and plan references.
- Step 2: Copy the A1–A3 checklist into tier2_baseline.md to track completion; mark checkboxes `[ ]` → `[X]` as tasks finish.
- Step 3: Audit existing gradcheck coverage via `rg -n "gradcheck" tests/test_suite.py` and `rg -n "gradcheck" tests/test_gradients.py`; list each parameter covered with file:line anchors.
- Step 4: Summarize uncovered parameters (misset_rot_x, lambda_A, fluence) referencing docs/development/testing_strategy.md:385 and plan lines; note absence of corresponding tests.
- Step 5: Execute the authoritative command `env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest tests/test_suite.py::TestTier2GradientCorrectness -vv | tee reports/gradients/${STAMP}/gradcheck_phaseA.log`; capture runtime, pass/skip counts, and warnings.
- Step 6: Record the exit status with `echo $? >> reports/gradients/${STAMP}/commands.txt` immediately after pytest.
- Step 7: Dump environment metadata via `python - <<'PY'` to collect python/torch/numpy versions, device availability, compile env vars, and git SHA into env.json; include `AUTHORITATIVE_CMDS_DOC` value.
- Step 8: Append executed commands, environment exports, working directory, and git SHA to commands.txt; note timestamp and operator.
- Step 9: Generate SHA256 checksums for tier2_baseline.md, gradcheck_phaseA.log, env.json, commands.txt, and optional collect-only log using `sha256sum` → sha256.txt.
- Step 10: Optional but encouraged — run `pytest --collect-only -q tests/test_suite.py::TestTier2GradientCorrectness | tee reports/gradients/${STAMP}/collect_only.log`; reference this in the report.
- Step 11: Flesh out tier2_baseline.md with sections: Context, Existing Coverage, Uncovered Parameters, Command & Results, Environment, Compile Disable Decision, Next Steps, and Checklist completion.
- Step 12: Update plans/active/gradcheck-tier2-completion/plan.md to mark A1–A3 as [D], citing `reports/gradients/${STAMP}/` in the guidance column; preserve table formatting and Markdown alignment.
- Step 13: Add a new Attempt entry under `[AT-TIER2-GRADCHECK]` in docs/fix_plan.md summarizing metrics (runtime, pass counts, warnings), compile-disable decision, and artifact paths.
- Step 14: Re-read docs/fix_plan.md Next Actions to confirm they now steer toward Phase B once Phase A is logged; adjust wording if necessary to mention the new bundle.
- Step 15: Run `git status --short` to verify only documentation/report files changed; avoid staging production code.
- Step 16: Optionally append a brief "Future Work" section in tier2_baseline.md outlining Phase B/C tasks with references for smooth hand-off.
Verification Checklist:
- [ ] tier2_baseline.md includes spec/testing citations for uncovered parameters.
- [ ] gradcheck_phaseA.log stored with runtime summary and pass counts.
- [ ] env.json lists python/torch versions, device availability, compile env vars, git SHA.
- [ ] commands.txt records every command and exit status in execution order.
- [ ] sha256.txt hashes all artifacts created in the bundle.
- [ ] plan Phase A rows marked [D] with bundle reference.
- [ ] docs/fix_plan.md Attempt references metrics + artifacts and notes compile-disable reasoning.
- [ ] Optional collect-only log captured and referenced (if executed).
Pitfalls To Avoid:
- Skipping explicit gap documentation leaves future loops without targets; list uncovered parameters with file:line evidence.
- Forgetting `NANOBRAGG_DISABLE_COMPILE=1` will cause gradcheck to crash under torch.compile; export it for each pytest run.
- Gradcheck must run in float64 CPU mode; do not alter dtype/device or rely on GPU for this baseline.
- Do not rename or delete prior gradient bundles; append new timestamped directories for archival integrity.
- Tier2_baseline.md should quote spec sections directly; avoid paraphrasing without citations to prevent drift.
- Plan and fix_plan edits must include artifact paths and metrics; missing references break traceability.
- Protected Assets listed in docs/index.md (input.md, loop.sh, supervisor.sh) must remain untouched.
- Resist adding instrumentation or logging to production code; this loop is documentation-only.
- Capture pytest output even on failure; rerunning without original logs erodes reproducibility.
- Keep environment metadata synchronized with commands; missing env.json details complicate audits.
- Avoid mixing timestamp formats; stick to UTC ISO8601 (YYYYMMDDTHHMMSSZ) for directories and references.
Pointers:
- plans/active/gradcheck-tier2-completion/plan.md:1
- docs/fix_plan.md:3350
- docs/development/testing_strategy.md:385
- docs/development/testing_strategy.md:420
- arch.md:318
- docs/development/pytorch_runtime_checklist.md:42
- specs/spec-a-core.md:211
- docs/bugs/verified_c_bugs.md:166
Next Up: Phase B misset_rot_x gradcheck implementation and targeted selector run once the Phase A bundle is merged cleanly; optionally queue beam parameter gradchecks for Phase C design review and document design notes ahead of implementation.
Additional Notes:
- Reconfirm that gradcheck tolerances (eps=1e-6, atol=1e-5, rtol=0.05) remain valid; document any deviations in tier2_baseline.md.
- Mention whether torch.autograd.gradgradcheck remains skipped to prevent confusion about second-order coverage.
- Clarify in the report that compile-disable env var naming (`NANOBRAGG_DISABLE_COMPILE`) supersedes legacy `NB_DISABLE_COMPILE` usage.
- Note any observed runtime changes compared to Attempt #1 logs to monitor drift.
- Flag open questions for Phase B (e.g., preferred loss function for misset_rot_x) in tier2_baseline.md to streamline next loop planning.
- Ensure bundle references are mirrored in galph_memory.md summary once supervisor reviews the submission.
