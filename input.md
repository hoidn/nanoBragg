Summary: Refresh scaling-chain evidence after the SAMPLE-pivot fix so we know where normalization still diverges.
Phase: Evidence
Focus: CLI-FLAGS-003 Phase K2 — Recompute scaling chain & extend diagnostics
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after.log; reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after_<timestamp>.log; reports/2025-10-cli-flags/phase_k/f_latt_fix/metrics_after.json; reports/2025-10-cli-flags/phase_j/scaling_chain.md; reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_summary.md; docs/fix_plan.md Attempt update draft
Do Now: CLI-FLAGS-003 Phase K2 — run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py --out reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after.log` then recompute scaling ratios in `reports/2025-10-cli-flags/phase_j/scaling_chain.md`
If Blocked: Capture stdout/stderr to `reports/2025-10-cli-flags/phase_k/f_latt_fix/attempt_blocked.log`, append `python - <<'PY'` snippet printing `sys.version`, `torch.__version__`, `torch.cuda.is_available()`, and `torch.get_default_dtype()`, snapshot `git status --short`, and note blocker in docs/fix_plan Attempt log before pausing.

Priorities & Rationale:
- docs/fix_plan.md:448-461 — refreshed Next Actions make Phase K2 the gating step for long-term goal #1; we need new scaling evidence before touching normalization code.
- plans/active/cli-noise-pix0/plan.md:171-179 — Phase K2 explicitly demands updated traces explaining `test_metrics_failure.json` ratios.
- reports/2025-10-cli-flags/phase_k/f_latt_fix/test_metrics_failure.json — current correlation≈0.173 data predates the SAMPLE-pivot fix; rerunning will show whether F_latt or F_cell still diverge.
- specs/spec-a-cli.md:1-140 — CLI contract ensures lattice normalization must match C once pixel geometry is correct; cite if residual differences remain.
- docs/architecture/detector.md:5-90 — Confirms SAMPLE pivot geometry assumptions now in effect; scaling analysis should no longer be contaminated by pix0 drift.

How-To Map:
- Ensure clean tree except reports: `git status --short` (no code edits in this loop).
- Create working dir: `mkdir -p reports/2025-10-cli-flags/phase_k/f_latt_fix`.
- Record environment: `python - <<'PY'` writing commit hash, sys.version, torch versions, CUDA availability to `metrics_after.json` skeleton (append later with ratios).
- Run harness (Do Now command) to regenerate Py trace with SAMPLE pivot; immediately `cp trace_py_after.log trace_py_after_$(date +%H%M%S).log` for archival.
- Compare against C trace: `diff -u reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0.log reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after.log > reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_diff.txt || true`.
- Generate updated scaling markdown: `python reports/2025-10-cli-flags/phase_j/analyze_scaling.py --c-log reports/2025-10-cli-flags/phase_j/trace_c_scaling.log --py-log reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after.log` (script overwrites phase_j/scaling_chain.md).
- Capture numeric deltas via quick script: `python - <<'PY'` reading both traces, computing Py/C ratios for `F_cell`, `F_latt`, `I_before_scaling`, `steps`, `polar`, `omega`, writing results to `metrics_after.json` (include absolute diff and ratio fields).
- Summarize findings in `reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_summary.md` (reference metrics JSON, highlight first divergence, note if ROUND/GAUSS/TOPHAT need follow-up).
- Update docs/fix_plan Attempt draft (do not commit yet) with metrics, artifact paths, and next-step recommendation.

Pitfalls To Avoid:
- No pytest or nb-compare runs this loop; Evidence phase forbids tests.
- Do not edit simulator/crystal/detector code—only generate artifacts.
- Keep harness command prefixed with `PYTHONPATH=src`; without it you may read the installed wheel.
- Avoid overwriting existing `trace_py_scaling.log`; emit new file under phase_k instead.
- Express deltas in meters first (add micron equivalents in parentheses for clarity).
- Make sure `metrics_after.json` stays valid JSON (use `json.dump`, not manual string concatenation).
- If ROUND/GAUSS/TOPHAT not evaluated, note that explicitly—do not mark them complete implicitly.
- Do not delete older artifacts under phase_j/phase_h; append new sections instead.
- Watch for lingering root-level images from prior loops; leave them untouched but note in Attempt log if they interfere.
- Confirm `NB_C_BIN` is set before running any C comparison command; if unset, document that you relied on archived traces only.

Pointers:
- plans/active/cli-noise-pix0/plan.md:178-180 — K2 task definition and expected outputs.
- docs/fix_plan.md:458-461 — Supervisor expectations for this step before K3.
- reports/2025-10-cli-flags/phase_j/scaling_chain.md — Existing report that must be refreshed.
- reports/2025-10-cli-flags/phase_k/f_latt_fix/test_metrics_failure.json — Baseline metrics to supersede.
- docs/development/testing_strategy.md:1-120 — Device/dtype neutrality guidance to cite in notes.
- docs/architecture/pytorch_design.md:200-260 — Lattice factor description; update references if ratios remain off.
- tests/test_cli_scaling.py:1-80 — Regression test awaiting green after K3; note location for future loops.

Next Up: If ratios align after rerun, prep command + doc edits for Phase K3 (targeted pytest and doc updates) so the next loop can execute quickly.
