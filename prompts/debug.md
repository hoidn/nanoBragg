# Debugging Loop Prompt (Single-Loop, Trace-Driven, No‑Cheating)

Purpose
- This prompt governs any loop labeled “debugging” and any loop triggered by AT‑PARALLEL failures, correlation below thresholds, large max absolute differences, or visible structured discrepancies.
- It encodes strict guardrails, mandatory parallel trace‑driven validation, geometry‑first triage, quantitative checkpoints beyond correlation, clear success/fail gates with rollback, and a mandatory fix plan update process.

Use When (Triggers)
- Any AT‑PARALLEL test fails or correlation < required threshold in specs/spec‑a‑parallel.md
- Max absolute diff is large or diff heatmap shows structured errors
- Beam/geometry invariances break (e.g., pixel‑size invariance, beam center in pixels)
- Suspected detector/convention/unit/pivot issues

Non‑Negotiable Guardrails
1) Never change tests, tolerances, or acceptance thresholds to “pass.” Do not weaken spec gates.
2) Mandatory parallel trace‑driven debugging for equivalence issues. Produce both C and PyTorch traces and identify the FIRST DIVERGENCE.
3) Geometry‑first triage: units, conventions, pivots, MOSFLM +0.5 pixel, F/S mapping, twotheta axis → CUSTOM switch, r‑factor/close_distance.
4) Quantitative checkpoints beyond correlation: report correlation, MSE/RMSE, max abs diff, total sums and ratios, and attach a diff heatmap.
5) Rollback: If metrics regress or equivalence is not achieved without changing tests, revert functional changes in this loop and escalate with artifacts.
6) Fix Plan Updates are MANDATORY at loop START and END using `prompts/update_fix_plan.md`:
   - At START: select exactly one high‑value item and mark it `in_progress` (“one item per loop” means one item ATTEMPTED per loop).
   - At END: update Attempts History with metrics, artifacts, first divergence, and Next Actions. If failed/partial, KEEP the item active (do not mark done) and add diagnostics for future loops.

Authoritative Inputs (consult before acting)
- CLAUDE.md (core rules, detector gotchas, “Parallel Trace Debugging is Mandatory”)
- specs/spec‑a.md, specs/spec‑a‑core.md, specs/spec‑a‑parallel.md, specs/spec‑a‑cli.md
- docs/development/testing_strategy.md (parallel trace SOP; golden parity)
- docs/debugging/*: detector_geometry_checklist.md, debugging.md, convention_selection_flowchart.md
- docs/architecture/*: detector.md, c_to_pytorch_config_map.md, c_code_overview.md
- prompts/main.md (loop mechanics). For debugging loops, this prompt supersedes where stricter.

Loop Objective (single loop)
- Fix one root‑cause class deterministically, validated by traces and metrics. No test edits. No threshold edits. Produce artifacts.

Progress & Tools Integration
- Use brief preambles (what’s next) and update_plan for steps (reproduce → trace → triage → fix → verify). Prefer `rg` for search. Save artifacts under a dated folder.

SOP — Step‑by‑Step (follow in order)
0) Setup & Context
   - Identify the failing AT(s), exact thresholds, and reproduction commands. Pin device/dtype (float64 for debug). Reduce to a small ROI if needed (spec allows ROI for debug).
   - Update docs/fix_plan.md at LOOP START using `prompts/update_fix_plan.md`: pick one item, set `Status: in_progress`, record reproduction commands and planned approach.

1) Reproduce Canonically
   - Subagent: test-failure-analyzer — Provide the failing test path/pattern and context. Capture canonical error messages, stack traces, clustered failures, and exact repro commands. Attach its report, then run the reproduced command(s) to verify.
   - Reproduce the exact failing case (e.g., AT‑PARALLEL‑002 pixel sizes: 0.05, 0.1, 0.2, 0.4 mm; fixed detector size; fixed beam center in mm). Record: image shape, correlation, MSE/RMSE, max abs diff, total sums and sum ratio.
   - Save diff heatmap (log1p|Δ|) and peak diagnostics if relevant.

2) Geometry‑First Triage (Detector Checklist)
   - Units: detector geometry in meters; physics in Å. Verify conversions at boundaries.
   - Convention: MOSFLM axis/basis, +0.5 pixel on beam centers; F/S mapping; CUSTOM switch when `-twotheta_axis` is explicit.
   - Pivot: BEAM vs SAMPLE per flags/headers; r‑factor ratio; close_distance update and distance = close_distance / r.
   - Invariances: beam center in pixels scales as 1/pixel_size; pixel coordinate mapping; omega formula Ω=(pixel_size²/R²)·(close_distance/R) or 1/R² (point‑pixel). Validate.
   - Subagent (conditional): architect-review — If triage indicates geometry/convention/pivot/omega‑formula changes, validate ADR alignment and propose ADR updates. Include a 1–3 line ADR impact summary in artifacts.

3) Mandatory Parallel Trace‑Driven Validation
   - Choose an on‑peak pixel (or two) in the failing condition. Generate instrumented C trace (meters/Å per spec) and matching PyTorch trace with IDENTICAL variable names (e.g., pix0_vector, fdet/sdet/odet, Fbeam/Sbeam, R, omega, incident/diffracted, q, h,k,l, F_cell, F_latt, S-step factors).
   - Compare line‑by‑line to find the FIRST DIVERGENCE. Stop and root‑cause that divergence before changing anything else.
   - Subagent: debugger — Drive the isolate‑first‑divergence workflow and propose the minimal corrective change. Follow its reproduce/isolate steps; keep edits surgical.

4) Quantitative Checkpoints & Visuals (always attach)
   - Metrics: correlation, MSE, RMSE, max abs diff, total sums (C_sum, Py_sum) and their ratio, and optional SSIM. Count matched peaks and pixel errors if peak alignment applies.
   - Visuals: diff heatmap(s) for failing case(s). Save `c_trace.log`, `py_trace.log`, and `summary.json` with metrics.

5) Narrow & Fix (surgical)
   - Apply the smallest code change that fixes the FIRST DIVERGENCE. Prioritize geometry (pix0/F/S, axes, units, r‑factor, pivot behavior) before physics stack. Do not change tests.
   - Re‑run the specific failing case and closest neighbors (e.g., pixel sizes ±1 step). Re‑generate traces if geometry/units changed.

6) Pass/Fail Gates & Rollback
   - Pass only if ALL relevant spec gates pass:
     • AT‑specific thresholds (e.g., AT‑PARALLEL‑002: correlation ≥ 0.9999; beam center in pixels = 25.6/pixel_size ±0.1 px; peaks scale inversely with pixel size)
     • No NaNs/Infs; max abs diff within expected numerics; diff heatmaps show only low‑level residue
     • Sum ratios plausible (e.g., within 10% unless spec states otherwise)
   - If fails, revert this loop’s code edits, keep artifacts, and escalate hypotheses + traces in fix_plan. Do not touch tests/thresholds.

7) Finalize
   - Run the full test suite if targeted checks pass. Attach artifact paths.
   - Update docs/fix_plan.md at LOOP END using `prompts/update_fix_plan.md`:
     • Always append to Attempts History with corr/RMSE/MSE/max|Δ|/sum ratio and artifact paths.
     • Record FIRST DIVERGENCE (variable + file:line) and hypotheses.
     • If PASS: mark `Status: done` and quote spec thresholds satisfied.
     • If FAIL/PARTIAL: DO NOT mark done — keep item active and add concrete Next Actions; include rollback note if code changes were reverted.
   - Subagent (post‑parity): issue — If the root‑cause class wasn’t covered or was weakly covered by Acceptance Tests/spec, propose precise spec shard edits/additions (IDs, shard, measurable expectations) without weakening thresholds; add a TODO to fix_plan.md.
   - Subagent (pre‑commit): code-reviewer — Run on the changed scope to catch security/performance/config risks introduced by the fix; address high/critical findings before committing.

Acceptance Metrics Reference (examples)
- Use the exact thresholds from specs/spec‑a‑parallel.md for each AT. Examples:
  • AT‑PARALLEL‑002: correlation ≥ 0.9999; beam center (px) = 25.6/pixel_size ± 0.1; inverse scaling of peak positions; no large structured diff.
  • General: simple_cubic ≥ 0.9995; triclinic reference ≥ 0.9995; tilted ≥ 0.9995 unless spec states otherwise.
  • Always include max abs diff and sum ratio.

Artifacts (required)
- c_trace.log, py_trace.log (aligned names/units), diff_heatmap.png, summary.json (correlation, RMSE, MSE, max_abs_diff, sums/ratio, peak stats if used), and reproduction commands.

Guarded Anti‑Patterns (block)
- Changing tests, thresholds, or loosening tolerances.
- Submitting “fixes” without traces and metrics.
- Ignoring detector checklist (units/conventions/pivot/+0.5/r‑factor).
- Relying on correlation alone without max abs diff and visuals.

Commit & PR Notes (when loop succeeds)
- Commit message MUST mention the AT(s) fixed and FIRST DIVERGENCE. Include a short metrics line (corr/RMSE/max|Δ|/sum_ratio) and artifact paths.
- Do not include runtime artifacts in the repo; store under reports/ or a temp artifacts folder per the project’s convention.

Rollback Conditions (hard requirements)
- If correlation or metrics regress for any previously passing AT‑PARALLEL within this loop, revert code changes and document in fix_plan. Do not merge.

Loop Checklist (self‑audit)
- Reproduced failing case with canonical flags
- Ran detector geometry checklist
- Produced C & Py traces; identified FIRST DIVERGENCE
- Implemented a minimal, surgical fix (no test edits)
- Reported metrics: corr/MSE/RMSE/max|Δ|/sum ratio; heatmap attached
- Verified spec thresholds; ran full suite; updated fix_plan with trace links
- No thresholds changed; no unrelated changes sneaked in
 - Updated docs/fix_plan.md at START and END per `prompts/update_fix_plan.md` (one item attempted; failure recorded without being dropped)
