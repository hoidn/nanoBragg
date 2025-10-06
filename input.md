Summary: Re-run MOSFLM scaling parity after the rescale fix and capture fresh evidence
Phase: Evidence
Mode: Parity
Focus: CLI-FLAGS-003 / Phase K3g3 — scaling parity refresh
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py::test_f_latt_square_matches_c
Artifacts: reports/2025-10-cli-flags/phase_k/f_latt_fix/pytest_post_fix.log, reports/2025-10-cli-flags/phase_k/f_latt_fix/nb_compare_post_fix/, reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain.md
Do Now: CLI-FLAGS-003 Phase K3g3 — env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest tests/test_cli_scaling.py::test_f_latt_square_matches_c -v

If Blocked: Run env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests/test_cli_scaling.py::test_f_latt_square_matches_c to confirm selector, then post the failure log under reports/2025-10-cli-flags/phase_k/f_latt_fix/attempts/ with notes in Attempt History.

Priorities & Rationale:
- specs/spec-a-cli.md:60 documents CUSTOM pix0 handling; the supervisor CLI command depends on MOSFLM vectors so parity must hold before Phase L reruns. Action: cite this clause when summarising results in docs/fix_plan.md so we keep spec traceability.
- plans/active/cli-noise-pix0/plan.md:214 keeps K3g3 open until the scaling test, nb-compare artifacts, and updated summaries exist. Action: mark K3g3 as [D] only after the updated artifacts and logs are linked inside the plan.
- docs/development/testing_strategy.md:172 mandates NB_RUN_PARALLEL=1 with the golden-suite binary for live C↔PyTorch parity, so the command in Do Now is non-negotiable. Action: include the env block in every shell snippet you capture under reports/.
- reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain.md:7 still lists the 0.12 intensity ratio gap; we need fresh data to demonstrate the MOSFLM rescale fix resolved it. Action: overwrite the ratios and call out the new numbers in Attempt #48.
- reports/2025-10-cli-flags/phase_k/base_lattice/summary.md:81 notes that traces must be regenerated post-fix, making this loop the right moment to refresh the evidence bundle. Action: append a dated subsection with Δh/Δk/Δl < 5e-4 to close the trace requirement.

How-To Map:
- env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest tests/test_cli_scaling.py::test_f_latt_square_matches_c -v | tee reports/2025-10-cli-flags/phase_k/f_latt_fix/pytest_post_fix.log
  Expect: sum_ratio within 0.99–1.01 and no skips; capture stdout/err in the log for traceability.
- KMP_DUPLICATE_LIB_OK=TRUE NB_C_BIN=./golden_suite_generator/nanoBragg nb-compare --resample --outdir reports/2025-10-cli-flags/phase_k/f_latt_fix/nb_compare_post_fix --threshold 0.999 -- -cell 100 100 100 90 90 90 -default_F 300 -N 10 -lambda 1.0 -distance 100 -detpixels 512 -pixel 0.1 -oversample 1 -phisteps 1 -mosaic_dom 1
  Expect: correlation ≥0.999, RMSE <1e-3, peak distance ≤1 px; stash metrics.json + PNG diff.
- KMP_DUPLICATE_LIB_OK=TRUE NB_PYTORCH_DTYPE=float32 python reports/2025-10-cli-flags/phase_k/f_latt_fix/analyze_scaling.py > reports/2025-10-cli-flags/phase_k/f_latt_fix/analyze_output_post_fix.txt; repeat with NB_PYTORCH_DTYPE=float64 for dtype_sweep refresh
  Expect: traces saved under dtype_sweep/ with updated fractional h,k,l and F_latt values.
- KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_k/base_lattice/trace_harness.py --out reports/2025-10-cli-flags/phase_k/base_lattice/trace_py.log
  Expect: TRACE_PY_BASE lines aligned with C output; note commit hash in summary.md.
- diff -u reports/2025-10-cli-flags/phase_j/trace_c_scaling.log reports/2025-10-cli-flags/phase_k/base_lattice/trace_py.log > reports/2025-10-cli-flags/phase_k/base_lattice/trace_diff_post_fix.txt
  Expect: empty diff aside from header (Δh/Δk/Δl < 5e-4 tolerance) confirming geometry parity.
- python - <<'PY'
from pathlib import Path
summary = Path('reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain.md')
print('Update scaling_chain.md with new ratios once analysis completes; cite metrics_after_post_fix.json if you emit one.')
PY
  Expect: reminder appears in console; follow through by editing the markdown file immediately after analysis.
- After the commands, edit reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain.md to replace the legacy ratios, and note the command/environment in the header (commit hash, dtype, date).
  Expect: table rows reflect Py/C ratio ≈1.00 and polar factor parity.
- Append a new section to reports/2025-10-cli-flags/phase_k/base_lattice/summary.md capturing the diff results and confirming Δh/Δk/Δl < 5e-4.
  Expect: summary references trace_diff_post_fix.txt and updated trace paths.
- Update docs/fix_plan.md Attempt #47 (or next) with the new metrics, referencing nb_compare_post_fix metrics.json and pytest log.
  Expect: Next Actions list shifts focus to Phase L once evidence is archived.
- When done, snapshot nb_compare_post_fix/metrics.json and PNGs for parity review, then stage them under reports/2025-10-cli-flags/phase_k/f_latt_fix/nb_compare_post_fix/.
  Expect: directory contains metrics.json, diff.png, overlays for supervisor review.
- Run git status frequently; stage artifacts once verified so we avoid losing trace logs to cleanup scripts.
  Expect: clean working tree except for intentional evidence files prior to handoff.
- Sequence recap: (1) run parity pytest, (2) run nb-compare, (3) regenerate traces & scaling analysis, (4) update markdown summaries, (5) log fix_plan attempt, (6) only then request supervisor review.
  Expect: tasks checked off in plan.md and logged in docs/fix_plan.md with Attempt # IDs.

Pitfalls To Avoid:
- Do not skip NB_RUN_PARALLEL=1 or the parity test will be silently skipped.
- Keep instrumentation scripts unmodified except for output paths; reuse production helpers per tracing rules.
- Avoid deleting prior artifacts—append new logs under the same phase_k directory.
- Do not edit docs/index.md or other protected assets while collecting evidence.
- Make no code changes outside the planned scaling/parity scope unless blockers demand it (coordinate first).
- Preserve device/dtype neutrality in any ad-hoc probes (no hard-coded .cpu()/.cuda()).
- Do not downgrade tolerances in tests; fix physics instead.
- Keep nb-compare outputs under reports/…/nb_compare_post_fix/ so earlier attempts remain intact.
- Skip running the full pytest suite this loop; evidence collection only.
- Follow Core Rule 0: reuse main code paths for any trace/analysis scripts.

Pointers:
- plans/active/cli-noise-pix0/plan.md:205 (Phase K3 context and exit criteria)
- reports/2025-10-cli-flags/phase_k/base_lattice/summary.md:63 (current divergence notes)
- reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain.md:7 (scaling mismatch summary)
- specs/spec-a-cli.md:60 (pix0 override semantics for CUSTOM MOSFLM)
- docs/development/testing_strategy.md:172 (authoritative parity env guidance)
- reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/cell_tensors_py.txt:1 (validation of the MOSFLM rescale computation)

Next Up (optional):
- Phase L1 nb-compare rerun for the full supervisor command if K3g3 metrics pass.
- Regenerate phase_k/f_latt_fix/scaling_summary.md with updated numbers before closing CLI-FLAGS-003.

Context Recap:
Ensure the new traces prove that the MOSFLM branch now rebuilds real vectors and duals exactly; the earlier 40× discrepancy should disappear entirely.
Confirm the polarization factor defaults to 0.0 in BeamConfig so the scaling table shows polar parity with the C trace (≈0.913 for the supervisor command).
Document any remaining residuals (if Δh/Δk/Δl are non-zero) and flag them in docs/fix_plan.md so we can triage before Phase L.
If nb-compare exposes residual intensity drift, gather hot-pixel data via scripts/validation/analyze_scaling.py and attach it under reports/2025-10-cli-flags/phase_k/f_latt_fix/diagnostics/.
Keep attempt numbering consistent; note whether this is Attempt #48 or a continuation of #47 when you update the ledger.
If dtype_sweep still shows float32/float64 divergence, note it explicitly and stop short of Phase L; regroup with a fresh supervisor memo.
Match the naming convention for new artifact files (e.g., metrics_post_fix.json) so future diffs are easy to locate.
Cross-check NB_C_BIN resolves to golden_suite_generator/nanoBragg; if not, document the fallback path you used in the attempt log.
Capture command transcripts in reports/2025-10-cli-flags/phase_k/f_latt_fix/cmd_history_post_fix.txt so we can replay the exact environment later.
Summarise any lingering TODOs at the end of docs/fix_plan.md entry to keep plan and evidence synced.
Record wall-clock timings for each command to contrast with earlier attempts; include them in the summary appended to scaling_chain.md.
If any command fails, archive stderr under reports/2025-10-cli-flags/phase_k/f_latt_fix/errors/ with a short README before retrying.
Remember to set KMP_DUPLICATE_LIB_OK=TRUE inside any ad-hoc Python shell you open; missing it can invalidate parity attempts.
Before ending the loop, double-check that no temporary .npy files remain outside the designated reports directories.
When updating markdown summaries, preserve previous findings by adding a new dated section rather than rewriting history; note delta values explicitly.
Add a quick sanity check comparing py_image.npy vs c_image.npy (if generated) to confirm no accidental swap occurred; log any diff results.
Re-run git status after each major step and jot the staged files list into your attempt notes so we have auditable provenance.
After committing artifacts, run nb-compare again if metrics appear borderline; better to verify twice than to chase ambiguous regressions later.
If nb-compare emits warnings about resampling, capture the stdout snippet and mention it in the attempt summary.
Where possible, mirror file naming from prior attempts (e.g., trace_py_after.log) to keep diffs clean; if you introduce new names, document the rationale in the report README.
Before handing back, verify that nb_compare_post_fix/ contains README.md summarising metrics; create one if absent so future reviewers know how to interpret the artifacts.
Finally, leave a short note in galph_memory.md summarising the evidence you gathered so the next supervisor loop can pivot immediately.
Confirm NB_RUN_PARALLEL stays enabled throughout the session; if you need to disable it for debugging, rerun the parity test afterwards.
Re-run pytest with -vv if any assertion message needs fuller context, but avoid rerunning the entire suite as per Evidence-phase guardrails.
Before exiting, snapshot the environment variables you used into reports/2025-10-cli-flags/phase_k/f_latt_fix/env_post_fix.txt for reproducibility.
Remember to leave Attempt notes in docs/fix_plan.md immediately after capturing artifacts so evidence and guidance stay in sync.
Ping the supervisor in commits if unexpected behavior remains after K3g3 so we can triage before scheduling Phase L.
