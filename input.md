Summary: Break down the new spec-baseline scaling bundle so we know exactly which factors drive the 14.6% I_before_scaling gap and document the findings for Phase M2.
Mode: Docs
Focus: CLI-FLAGS-003 / Phase M2 – Partition divergence contributions (plans/active/cli-noise-pix0/plan.md)
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py
Artifacts:
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/analysis_20251008T212459Z.md (new narrative + tables)
  * Include numeric breakdowns (F_cell, F_latt, omega, steps), spec references, and conclusions.
- reports/2025-10-cli-flags/phase_l/scaling_validation/scaling_validation_summary.md (regenerated summary table)
  * Preserve historical context by appending a dated section for 20251008T212459Z.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md (append timestamped hypothesis block)
  * Document observations, ranked hypotheses, and proposed probes for the 14.6% delta.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/collect.log (pytest output for this loop)
  * Capture stdout/stderr from the collect-only run verbatim.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/commands.txt (append today’s commands + timestamps)
  * List compare_scaling_traces invocation, pytest collect, shasum updates.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/sha256.txt (refresh if new files added)
  * Ensure hashes cover analysis.md, collect.log, updated commands.txt, etc.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/git_sha.txt (update with current HEAD after analysis)
  * Keep provenance aligned with the evidence bundle.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/summary_addendum.md (brief note pointing future readers to analysis_20251008T212459Z.md)
  * Optional helper so auditors can jump straight to the new work product.
- docs/fix_plan.md Attempt #186 (CLI-FLAGS-003) referencing the new analysis bundle, key deltas, and collect log.
Do Now: CLI-FLAGS-003 / Phase M2 – Partition divergence contributions; KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py
If Blocked: Draft partial findings in analysis_20251008T212459Z.md, list open questions + blocked inputs, update docs/fix_plan.md Attempts with the partial bundle path and blocker summary, capture collect.log (even if failing) for traceability, and leave a short note in reports/.../analysis_20251008T212459Z.md before stopping.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:46-58 flags M2 as the actionable gate; we cannot move to M3 lattice probes until this analysis exists.
- docs/fix_plan.md:451-503 keeps CLI-FLAGS-003 focused on M2 diagnostics; adding Attempt #186 with quantified deltas is required before simulator edits.
- specs/spec-a-core.md:204-236 codifies lattice sinc products and scaling order; citing these equations legitimises deviation analysis.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/metrics.json identifies I_before_scaling (Δ_rel = -0.14643) as first divergence; without attribution we cannot hypothesise fixes.
- reports/2025-10-cli-flags/phase_l/scaling_validation/scaling_validation_summary.md still reflects pre-shim numbers; refreshing prevents stale tolerances from misleading downstream reviews.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/manual_sincg.md holds earlier sinc calculations; today’s analysis must reuse or supersede them for continuity.
- docs/development/testing_strategy.md:27-78 mandates documented parity evidence with discoverable selectors; collect-only output + commands.txt updates satisfy governance.
- galph_memory.md latest entry expects Phase M2 evidence before reassigning engineering loops; meeting that expectation unblocks future input.md scopes.
- commands.txt + sha256.txt guard reproducibility; updating them ensures future investigators trust the bundle.
- reports/2025-10-cli-flags/phase_l/scaling_validation/run_metadata.json should align with the new analysis; keeping metadata fresh preserves the bundle contract.
- scripts/validation/compare_scaling_traces.py outputs only summary markdown; metrics.json is the single source for raw deltas, so we must document them manually.
How-To Map:
- Re-generate the shared summary table so the canonical overview reflects the newest bundle:
  python scripts/validation/compare_scaling_traces.py \
    --c reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/c_trace_scaling.log \
    --py reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/trace_py_scaling.log \
    --out reports/2025-10-cli-flags/phase_l/scaling_validation/scaling_validation_summary.md
- Diff the regenerated summary (git diff) and call out key changes (new Δ_rel, removal of MINOR statuses) inside analysis_20251008T212459Z.md.
- Parse metrics.json into a working table (python or spreadsheet) isolating F_cell, F_latt, omega_pixel, steps, and any accumulator state; embed the table + commentary in the analysis doc.
- Walk trace_py_scaling.log and c_trace_scaling.log line-by-line to identify divergences prior to I_before_scaling; list variable names, values, and units (with references) in the analysis.
- Include a worked `sincg(π·h, Na)` vs `sincg(π·(h-h0), Na)` comparison using traced h values to confirm/refute the leading hypothesis; record calculations explicitly.
- Capture any additional discrepancies (e.g., rounding differences in hkl_rounded) and note their contribution (or lack thereof) to I_before_scaling.
- Translate the findings into a concise bullet list of hypotheses (e.g., lattice normalization, cache reuse) at the end of analysis_20251008T212459Z.md.
- Update lattice_hypotheses.md with a new `## 20251008T212459Z` section summarising observations, ranked hypotheses, and proposed probes (tie back to prior manual_sincg.md values).
- Refresh sha256.txt inside the spec_baseline directory if new files are introduced. Command: (cd spec_baseline && shasum -a 256 * > sha256.txt).
- Append today’s commands (summary regeneration, pytest collect, checksum update) to commands.txt with timestamps + git SHA; specify CPU/dtype context too.
- Record Attempt #186 in docs/fix_plan.md under [CLI-FLAGS-003]: include bullet list of commands, artifact paths, key numeric deltas, and collect log reference.
- Run KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py, tee output to collect.log under spec_baseline/, and cite it in docs/fix_plan.md.
- Double-check run_metadata.json (same directory) and update git SHA, timestamp, device/dtype, and analysis description if necessary.
- Validate that analysis_20251008T212459Z.md references relevant spec + nanoBragg.c lines (explicit citations) before finishing.
- After writes, run git status to ensure only planned files changed; stash or remove incidental files before handing back.
- Capture a short summary_addendum.md noting the location and purpose of the new analysis so future loops can find it quickly.
- Validate `sha256.txt` by running `shasum -c sha256.txt` to confirm hashes before finishing the loop.
- Insert a note in galph_memory.md (if appropriate) summarising the evidence bundle once the loop completes.
Pitfalls To Avoid:
- Do not modify simulator/physics source files—this loop is strictly analytical.
- Keep all new artifacts under reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/ to preserve bundle integrity.
- Avoid device- or dtype-specific shortcuts in helper scripts; preserve portability per runtime checklist.
- Respect Protected Assets: never move/delete entries referenced by docs/index.md (loop.sh, supervisor.sh, input.md, etc.).
- Cite spec and nanoBragg.c line numbers when quoting formulas (CLAUDE Rule #11) to keep trace-driven validation intact.
- Do not overwrite or remove older summaries; regenerate/append with clear timestamps + rationale.
- Update sha256.txt whenever files change; stale hashes break provenance.
- If pytest collect fails, stop immediately and record the failure—do not proceed with partial evidence.
- Use the exact timestamp `20251008T212459Z` everywhere for today’s work; mixing identifiers breaks cross-references.
- Maintain lattice_hypotheses.md structure (timestamp heading, observations, hypotheses, next probes) for downstream diffability.
- Keep commands.txt chronological; state whether commands were first-run or rerun.
- Avoid ad-hoc scratch files in the repo; delete temporary calculations before finishing.
- Ensure analysis_20251008T212459Z.md includes both numerical tables AND narrative conclusions; numbers alone are insufficient.
- When referencing older bundles (e.g., 20251008T072513Z), explain how their deltas differ from today’s baseline.
- Don’t forget to update run_metadata.json; missing metadata makes bundles hard to reuse.
- Verify collect.log is stored alongside metrics.json so future loops can correlate traces and test discovery.
- Ensure summary_addendum.md (if created) does not duplicate data—use it as a pointer to the deeper analysis.
- Keep commands.txt and analysis_20251008T212459Z.md in ASCII; avoid Unicode characters unless quoting existing data.
Pointers:
- plans/active/cli-noise-pix0/plan.md:46-58 — Phase M checklist and deliverables for M2.
- docs/fix_plan.md:451-503 — CLI-FLAGS-003 ledger, current Attempts, and Next Actions.
- specs/spec-a-core.md:204-236 — Normative lattice factor computations and scaling chain definitions.
- docs/development/testing_strategy.md:27-78 — Evidence cadence, collect-only expectations, documentation rules.
- docs/development/c_to_pytorch_config_map.md:1-120 — Parameter parity references for CLI flags.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/metrics.json — Source data for today’s analysis.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/trace_py_scaling.log — Detailed PyTorch trace for value extraction.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/c_trace_scaling.log — C reference trace for comparisons.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/manual_sincg.md — Prior manual sinc calculations to compare against.
- reports/2025-10-cli-flags/phase_l/scaling_validation/scaling_validation_summary_20251119.md — Example of historical summary formatting.
- galph_memory.md (latest entry) — Supervisor expectations and context for Phase M2 evidence.
- docs/architecture/pytorch_design.md:110-182 — Vectorization constraints relevant if hypotheses implicate batching.
- scripts/validation/compare_scaling_traces.py — Tool used to regenerate summary tables (document command in commands.txt).
- reports/2025-10-cli-flags/phase_l/scaling_validation/run_metadata.json — Ensure metadata matches new analysis.
- scripts/callchain/trace_harness.py (if needed) — Reference for how traces were produced.
Next Up:
- Phase M3: build targeted lattice probes (manual sincg table + per-φ cache taps) once M2 evidence is logged.
- Optionally, refresh phi_carryover_diagnosis.md with a closure note referencing the new analysis before instrumenting probes.
- Prepare CUDA parity checklist for Phase M5 so GPU validation can proceed immediately after the physics fix.
- Draft a template for nb-compare reporting (Phase N) using today’s analysis format as groundwork.
