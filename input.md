Summary: Map edge-pixel execution so we can target the full-frame parity failure before rerunning 4096x4096 benchmarks.
Mode: Parity
Focus: docs/fix_plan.md [VECTOR-PARITY-001] Restore 4096x4096 benchmark parity
Branch: feature/spec-based-2
Mapped tests: none - evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_e0/$STAMP/
Do Now: docs/fix_plan.md [VECTOR-PARITY-001] Restore 4096x4096 benchmark parity - follow prompts/callchain.md with analysis_question="Why does the 4096x4096 full-frame parity stay at 0.721 when the 512x512 ROI matches? Focus: edge/background factors." and initiative_id=vectorization-parity-edge
If Blocked: Record blockers in $OUTDIR/blockers.md with git SHA, command log, and which deliverable could not be produced; stop without rerunning the 4096x4096 benchmark.
Priorities & Rationale:
- plans/active/vectorization-parity-regression.md:12 - Phase snapshot shows full-frame parity still 0.721 after Attempt #21, so verification must wait for edge diagnostics.
- plans/active/vectorization-parity-regression.md:68 - New Phase E0 tasks require a callchain/tap plan before Phase E benchmarks resume.
- docs/fix_plan.md:54 - Next Actions now point at drafting the callchain brief and running the trace; Do Now aligns with that gating work.
- reports/2026-01-vectorization-parity/phase_e/20251010T091603Z/blockers.md - Captures ROI vs full-frame metrics we must reference in the new brief.
How-To Map:
- export AUTHORITATIVE_CMDS_DOC=docs/development/testing_strategy.md; export NB_C_BIN=./golden_suite_generator/nanoBragg; ensure python resolves inside the project venv.
- STAMP=$(date -u +%Y%m%dT%H%M%SZ); OUTDIR=reports/2026-01-vectorization-parity/phase_e0/$STAMP; mkdir -p "$OUTDIR"/trace "$OUTDIR"/callgraph "$OUTDIR"/env.
- Review prompts/callchain.md and jot the chosen variables (analysis_question, initiative_id=vectorization-parity-edge, scope_hints=["edge pixels","scaling","background"], roi_hint="single edge pixel", namespace_filter="nanobrag_torch", time_budget_minutes=30) into "$OUTDIR"/callchain_brief.md together with links to Attempt #21 evidence.
- Use docs/index.md -> docs/architecture/pytorch_design.md and docs/development/testing_strategy.md to map likely entry points before touching code; capture notes in the brief.
- Execute the callchain workflow: generate `callchain/static.md`, optional `callgraph/dynamic.txt` (small ROI only), `trace/tap_points.md`, `summary.md`, and `env/trace_env.json`, all under $OUTDIR, following the deliverable templates.
- For any dynamic trace, run a minimal PyTorch invocation targeting pixel (0,0) (optionally (4095,4095)) while keeping ROI tiny; record the exact command at the top of callgraph/dynamic.txt.
- After outputs are staged, update docs/fix_plan.md Attempt log in the Attempts History section with STAMP, location, and key findings.
Pitfalls To Avoid:
- Do not rerun the 4096x4096 benchmark or pytest selector until Phase E0 concludes.
- Keep ROI minimal; avoid GPU traces unless necessary and explicitly document if used.
- Do not edit production code or add instrumentation; rely on trace tooling per prompts/callchain.md.
- Preserve regenerated golden data; no writes outside reports/.
- Ensure all deliverables stay within $OUTDIR and remain untracked.
- Capture environment metadata in env/trace_env.json (python, torch, git SHA, NB_C_BIN checksum if available).
- Reference Attempt #21 blockers instead of rewriting the same metrics from memory.
- Maintain consistent variable names between static and dynamic artifacts to aid future diffing.
Pointers:
- plans/active/vectorization-parity-regression.md:68
- docs/fix_plan.md:43
- docs/development/testing_strategy.md:170
- prompts/callchain.md:1
Next Up: Once the tap plan is in place, we can delegate targeted instrumentation or partial simulator probes before retrying the full-frame run.
