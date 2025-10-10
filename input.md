Summary: Capture Phase B callchain traces for the CLI default_F regression so we can pinpoint the first divergence between CLI and API paths.
Mode: Docs
Focus: [CLI-DEFAULTS-001] Minimal -default_F CLI invocation
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_d/<STAMP>/cli-defaults/phase_b/
Do Now: `[CLI-DEFAULTS-001]` Phase B — follow `prompts/callchain.md` to document the CLI vs API callchain for the default_F scenario, storing all required outputs under `reports/2026-01-test-suite-triage/phase_d/<STAMP>/cli-defaults/phase_b/`.
If Blocked: Record the partial findings in `phase_b/<STAMP>/summary.md`, note the blocker in `docs/fix_plan.md` Attempt log, and ping supervisor with the obstacle and any missing context.
Priorities & Rationale:
- `plans/active/cli-defaults/plan.md:30-40` lists Phase B tasks; finishing them unblocks remediation planning.
- `docs/fix_plan.md:62-86` Next Actions now target Phase B callchain evidence for `[CLI-DEFAULTS-001]`.
- `prompts/callchain.md:1-120` defines the deliverables and structure for the static callgraph, taps, and narrative.
- `docs/debugging/debugging.md:24-91` reiterates the trace-first workflow we must obey before attempting fixes.
- `tests/test_at_cli_002.py:28-60` supplies the canonical CLI command that the callchain should reference when capturing flow.
How-To Map:
- Export `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and set `ROOT=reports/2026-01-test-suite-triage/phase_d/${STAMP}/cli-defaults/phase_b/`; create `callchain/`, `api_callchain/`, `trace/`, and `env/` subfolders before starting.
- Draft `analysis.md` for B1 with `analysis_question="Why does the CLI default_F run emit zeros while the direct API run yields intensities?"`, `initiative_id="cli-defaults-b1"`, scope hints `['__main__.py', 'Simulator.run', 'output writing']`, ROI hint `(slow=16, fast=16)`, namespace filter `nanobrag_torch`, and time budget 30.
- For the CLI path (B2), follow `prompts/callchain.md` step-by-step: build the candidate entrypoint table, map config/core/normalization/sink anchors from `src/nanobrag_torch/__main__.py` and downstream modules, and capture any optional dynamic trace while running `KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -cell 100 100 100 90 90 90 -default_F 100 -detpixels 32 -pixel 0.1 -distance 100 -lambda 6.2 -N 5 -floatfile /tmp/cli.bin -intfile /tmp/cli.img`. Save outputs to `callchain/static.md`, `callgraph/dynamic.txt` (if captured), `trace/tap_points.md`, and `summary.md`.
- Mirror the process for the API control path (B3) using `KMP_DUPLICATE_LIB_OK=TRUE python debug_default_f.py`, documenting the matching anchors under `api_callchain/` and highlighting differences.
- Populate `env/trace_env.json` with runtime/tool versions, then synthesize `phase_b/${STAMP}/summary.md` (B4) that states the first divergent variable, cites file:line anchors, and recommends the confirmation step for Phase C. Update `plans/active/cli-defaults/plan.md` checklist marks only after all files are in place.
Pitfalls To Avoid:
- Evidence-only loop: do not modify production code or scripts; rely on documentation and tracing outputs.
- Keep CLI and API investigations on the same commit/device/dtype; avoid accidental GPU execution.
- Do not run additional pytest suites; stay within the documented commands and traces.
- Use ASCII in all new artifacts; no smart quotes or emojis.
- Maintain consistent tap names across CLI and API traces to simplify comparison.
- Store every artifact under the `ROOT` path; no ad-hoc folders elsewhere.
- Observe `KMP_DUPLICATE_LIB_OK=TRUE` for any command that imports torch.
- Reference file:line anchors rather than pasting code blocks into the deliverables.
- Capture blockers immediately if the callchain SOP cannot complete within the time budget.
Pointers:
- plans/active/cli-defaults/plan.md:14-40 — Phase A status + Phase B checklist.
- docs/fix_plan.md:3-86 — Ledger focus and updated Next Actions for `[CLI-DEFAULTS-001]`.
- specs/spec-a-cli.md:163 — AT-CLI-002 acceptance criteria grounding the investigation.
- prompts/callchain.md:1-160 — Required structure for callchain evidence.
- docs/debugging/debugging.md:24-91 — Parallel trace SOP expectations.
Next Up: After Phase B artifacts are logged, draft the Phase C remediation blueprint (plan C1–C3).
