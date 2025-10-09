Summary: Map the full CLI normalization path before the next supervisor rerun so Phase O can restart on solid evidence.
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling_phi0.py
Artifacts: reports/cli-flags-o-blocker/
Do Now: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm — Follow prompts/callchain.md with analysis_question "Why does the supervisor CLI run miss the /steps normalization while targeted tests pass?", initiative_id "cli-flags-o-blocker", scope_hints ["CLI","normalization","Simulator"], and capture the required files under reports/cli-flags-o-blocker/.

The Option 1 ROI parity run (20251009T020401Z) is our current green baseline, while the supervisor rerun (20251009T024433Z) still shows a 1.26e5× sum ratio. The goal for this loop is to explain that gap without touching production code. Lean on the new fix_plan bullet (docs/fix_plan.md:475) and treat this as the gating evidence bundle before any more parity reruns.

Context reminders:
- You are operating under evidence-only constraints; scripts/nb_compare.py must not be invoked for a fresh rerun yet.
- All deliverables belong under reports/cli-flags-o-blocker/ using the structure promised in prompts/callchain.md.
- Capture enough detail that the next implementation loop can target the exact normalization hook or config mismatch.

If Blocked: Record the obstacle in reports/cli-flags-o-blocker/blocked.md, note attempted commands plus stderr, then log the blocker in docs/fix_plan.md Attempt history so we keep the ledger honest.

Priorities & Rationale:
- docs/fix_plan.md:452 anchors the Phase O blocker diagnostics now required before rerunning nb-compare.
- plans/active/cli-noise-pix0/plan.md:93 keeps Phase O open until supervisor metrics are trustworthy.
- specs/spec-a-cli.md:11 confirms CLI flag semantics; mismatched normalization violates this shard.
- docs/bugs/verified_c_bugs.md:166 limits acceptable divergence to the documented C-PARITY-001 behavior.
- prompts/callchain.md:1 defines the deliverables and workflow for the evidence-only trace.

While preparing the callchain outputs, reference the supervisor analysis bundle. Summaries that restate raw numbers without anchors will not unblock Phase O; we need a defensible explanation tied to entry→sink ordering, config handoff, and scaling stages.

How-To Map:
- Review prompts/callchain.md start-to-finish so the deliverables follow the expected schema; note the requirement for candidate entry points, factor ordering, and numeric taps.
- While tracing, extract the effective steps/normalization factors from both ROI (20251009T020401Z) and supervisor (20251009T024433Z) bundles; record the comparison in summary.md together with any insights from py_stdout/c_stdout.
- Walk through src/nanobrag_torch/__main__.py, config.py, simulator.py, and relevant helpers, anchoring each path in callchain/static.md with file:line references; highlight where steps is computed, propagated, and consumed.
- After artifacts are written, run pytest --collect-only -q tests/test_cli_scaling_phi0.py and save the log under reports/cli-flags-o-blocker/pytest_collect.log as collection proof.
- Close the loop by appending an Attempt entry to docs/fix_plan.md summarising the evidence bundle, the extracted steps values, and the next confirming action you recommend.

Pitfalls To Avoid:
- No production code edits; this loop is evidence-only.
- Keep every new file under reports/cli-flags-o-blocker/; do not touch protected assets from docs/index.md.
- Do not rerun the full supervisor nb-compare yet; focus on diagnostics.
- Maintain device/dtype neutrality if any dynamic probe is run; avoid forcing CPU/GPU moves or adding .cpu() shims.
- Do not add new CLI flags or scripts without plan approval; capture observations instead.
- Avoid paraphrasing specs without citations; each flow description needs doc or code anchors.
- Resist the urge to assume the cause is in simulator.py only; trace the CLI/config pipeline first.
- Skip wide-scope pytest runs; collection-only proof is sufficient for this loop.

Pointers:
- docs/fix_plan.md:475 — new blocker diagnostics bullet you will satisfy.
- plans/active/cli-noise-pix0/plan.md:95 — O1 rerun expectations once the blocker is cleared.
- reports/2025-10-cli-flags/phase_l/supervisor_command/20251009T024433Z/analysis.md — prior failure metrics to reference.
- reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/summary.json — ROI baseline metrics for comparison.
- src/nanobrag_torch/__main__.py:1 and src/nanobrag_torch/simulator.py:900 are likely anchors for entry vs scaling; verify during the callchain.

Operational cadence:
- Start with documentation walkthrough (spec shards + plan) so the candidate entrypoint table reflects the normative flow.
- Proceed to code anchors only after the docs table is written; note any mismatches in the "Gaps/Unknowns" subsection of static.md.
- If dynamic tracing is warranted, constrain it to the nanobrag_torch namespace and keep ROI minimal (a single pixel or a stub run) to prevent heavy execution.
- When drafting trace/tap_points.md, propose taps that can be wired into existing debug harnesses (trace_harness.py or compare_scaling_traces.py) without duplicating physics code.
- Record environment metadata (python --version, torch.__version__, git rev-parse HEAD, NB_C_BIN if relevant) in env/trace_env.json so later loops can reproduce the same setup.

Documentation updates expected after completion:
- New attempt entry under CLI-FLAGS-003 summarising findings, referencing reports/cli-flags-o-blocker/summary.md, and listing the recommended next step (e.g., CLI config audit or normalization tap insertion).
- Optional galph_memory note (if significant insights emerge) so the supervisor log stays in sync with fix_plan.

Next Up:
- 1) If the callchain isolates the missing normalization hook, prepare a targeted implementation plan for the CLI config path.
- 2) Should the CLI path prove correct, escalate to compare_scaling_traces instrumentation pointing at scaling factors prior to the writer so we can validate the sink behavior.

Existing Metrics Snapshot:
- ROI nb-compare (20251009T020401Z) sum_ratio 1.159e5 with correlation 0.9852.
- Supervisor nb-compare (20251009T024433Z) sum_ratio 1.26451e5 with correlation 0.9966.
- C output max intensity 446.254 vs PyTorch 5.874e7 in the supervisor bundle.
- Steps reported in targeted tests currently 10 (phisteps), but the CLI path may omit the division; validate during tracing.

Evidence Goals:
- Document the precise entrypoint flow from CLI parsing through SimulatorConfig generation.
- Identify where steps/exposure/flux normalization is assembled and whether CLI values differ from the targeted harness.
- Confirm whether any conditional paths (e.g., skip noise, skip interpolation) alter scaling order when invoked together.
- Produce a numeric tap plan that can be wired into trace_harness.py without re-deriving physics.

Reporting Expectations:
- callchain/static.md should include a table of candidates, the selected entry sequence, and annotated scaling chain (with file:line anchors).
- summary.md needs to narrate the normalization path, highlight the first suspicious divergence, and recommend the very next verification.
- trace/tap_points.md must list 5–7 taps with owning functions and expected units, prioritising steps, exposure, fluence, and final scaling factors.
- env/trace_env.json should capture Python, PyTorch, OS, git SHA, and NB_C_BIN (even if unset) to keep parity reproducible.

Tap Suggestions to Prioritize:
- Capture SimulatorConfig.steps immediately after CLI parsing (likely in src/nanobrag_torch/__main__.py around the config assembly).
- Observe the normalization factor inside Simulator._compute_scaling (src/nanobrag_torch/simulator.py lines near 1100) to see if steps division occurs.
- Inspect the final buffer before writing in io/noise.py or io/smv.py to confirm no extra scaling is injected during output.
- Track fluence/flux/exposure interplay in config.py to ensure CLI flags recompute fluence identically to targeted tests.

Additional Notes:
- If any assumption from documentation conflicts with what you read in code, flag it explicitly in static.md under Gaps/Unknowns; do not silently reconcile.
- Prefer referencing existing artifacts (analysis.md, summary.json) instead of manually recomputing metrics; cite file paths when quoting numbers.
- Maintain chronological clarity in the Attempt entry you add; include timestamps for both ROI and supervisor bundles so the ledger ties back to evidence.
- When you run pytest --collect-only, include the command and exit code inside reports/cli-flags-o-blocker/commands.txt along with any callchain helper commands.

Closing Reminder:
- The output of this loop should make it obvious where to place a targeted fix or instrumentation without guessing. Treat the write-up as the blueprint for the next implementation attempt.
Action Log: After completing deliverables, list every command executed (callchain steps, pytest, cat, etc.) in reports/cli-flags-o-blocker/commands.txt so future audits can replay the workflow.
Documentation Sync: Reference docs/fix_plan.md:475 in your Attempt entry so auditors can correlate the new evidence with the blocker diagnostics requirement.
Ready Gate: Ping galph in Attempts History once artifacts land so the next supervisor loop sees the bundle immediately.
