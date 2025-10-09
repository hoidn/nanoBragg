Summary: Produce Phase D2 design notes so we can choose how to handle divergence sources alongside sourcefiles before re-running parity.
Mode: Docs
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2025-11-source-weights/phase_d/<STAMP>/{design_notes.md,commands.txt,pytest_collect.log,summary.md}
Do Now: [SOURCE-WEIGHT-001] Correct weighted source normalization — KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q
If Blocked: Document the roadblock in reports/2025-11-source-weights/phase_d/<STAMP>/attempts.md and run KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q to capture the failure context.
Priorities & Rationale:
- specs/spec-a-core.md:140 — Spec says weights are ignored; divergence+sourcefile semantics remain undefined and need a recommendation.
- plans/active/source-weight-normalization.md — Phase D2 now expects a design_notes.md deliverable before implementation.
- reports/2025-11-source-weights/phase_d/20251009T102319Z/divergence_analysis.md — D1 artifact summarises steps mismatch (4 vs 2) and enumerates remediation options A/B/C.
- docs/fix_plan.md:4035 — Next Actions require D2 design + D3 harness before Phase E resumes.
- docs/development/testing_strategy.md:40 — Device/dtype discipline to cite when proposing implementation touchpoints.
How-To Map:
- Create a fresh UTC-stamped folder under reports/2025-11-source-weights/phase_d/ (e.g. using date --utc +%Y%m%dT%H%M%SZ) and record commands in commands.txt.
- Re-read divergence_analysis.md and extract quantitative deltas (steps, correlation, sum_ratio) plus option tradeoffs; summarise them in design_notes.md.
- For each remediation option, list impacted modules/functions (e.g. src/nanobrag_torch/utils/auto_selection.py, src/nanobrag_torch/simulator.py:400) and outline vectorization/device risks referencing docs/development/pytorch_runtime_checklist.md.
- Recommend one path, justify with spec adherence + parity expectations, and define acceptance metrics (correlation ≥0.999, |sum_ratio−1| ≤1e-3) plus required pytest selector (start from TestSourceWeights suite).
- Capture pytest --collect-only -q output into pytest_collect.log to prove selectors still load; add a short summary.md framing next steps for D3 harness work.
Pitfalls To Avoid:
- Do not edit production code; this is an analysis loop.
- Keep divergence options grounded in spec wording; avoid inventing new behaviour without noting spec deltas.
- Maintain device/dtype neutrality in proposed changes—no `.cpu()`/`.cuda()` shims.
- Respect Protected Assets (docs/index.md items) when creating or referencing scripts.
- Use existing fixtures (two_sources.txt) and avoid adding new files under reports/ outside the timestamped folder.
- Note that nb-compare / CLI runs are deferred until Phase E; do not execute them now.
- When citing C code, use Rule #11 docstring snippets; no paraphrasing.
- Do not change pyproject.toml or pyrefly config.
- Avoid renaming or relocating any files referenced in docs/index.md.
- Keep Attempt history in docs/fix_plan.md unchanged until the new artifact is ready.
Pointers:
- reports/2025-11-source-weights/phase_d/20251009T102319Z/divergence_analysis.md
- plans/active/source-weight-normalization.md
- docs/fix_plan.md:4029
- specs/spec-a-core.md:140
- docs/development/pytorch_runtime_checklist.md:10
- docs/development/testing_strategy.md:38
Next Up: Prepare the Phase D3 acceptance harness once the design decision lands.
