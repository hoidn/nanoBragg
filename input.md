Summary: Retire NB_TRACE_SIM_F_LATT instrumentation and prove ROI parity stays green after the cleanup.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity — Phase D6
Branch: feature/spec-based-2
Mapped tests: NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q
Artifacts: reports/2026-01-vectorization-parity/phase_d/$STAMP/cleanup/{commands.txt,phase_d_summary.md,roi_compare/summary.json}
Do Now: docs/fix_plan.md item 11 (Phase D6 — Cleanup instrumentation); once the NB_TRACE_SIM_F_LATT hook is removed, run `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` followed by `KMP_DUPLICATE_LIB_OK=TRUE python scripts/nb_compare.py --resample --roi 1792 2304 1792 2304 --outdir reports/2026-01-vectorization-parity/phase_d/$STAMP/cleanup/roi_compare -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05`.
If Blocked: Capture the regression (diff log + ROI summary) under reports/2026-01-vectorization-parity/phase_d/$STAMP/blockers/ and pause for supervisor review before reverting instrumentation.
Priorities & Rationale:
- docs/fix_plan.md:61 — Phase D6 mandates stripping the temporary simulator logging and revalidating parity.
- plans/active/vectorization-parity-regression.md:66 — Plan now tracks D6 as the remaining blocker before Phase E full-frame work.
- plans/active/vectorization.md:18 — Downstream vectorization profiling stays blocked until D6/E finish, so this cleanup unblocks Goal #1.
- specs/spec-a-core.md:20-44 — Confirms the meter↔Å unit contract that motivated the trace hook; cleanup must preserve that scaling.
- arch.md:69-74 — ADR-01 documents the hybrid unit boundary we must keep intact while removing the debug guard.
How-To Map:
1. `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; mkdir -p reports/2026-01-vectorization-parity/phase_d/$STAMP/cleanup/.
2. Edit `src/nanobrag_torch/simulator.py` to delete the NB_TRACE_SIM_F_LATT env guard and any related logging, leaving the production lattice-vector scaling intact; keep device/dtype neutrality untouched.
3. Record the command used and git diff path in `reports/2026-01-vectorization-parity/phase_d/$STAMP/cleanup/commands.txt` before running tools.
4. `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q | tee reports/2026-01-vectorization-parity/phase_d/$STAMP/cleanup/pytest_collect.log`.
5. `KMP_DUPLICATE_LIB_OK=TRUE python scripts/nb_compare.py --resample --roi 1792 2304 1792 2304 --outdir reports/2026-01-vectorization-parity/phase_d/$STAMP/cleanup/roi_compare -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05` and copy summary.json/png plus metrics into the cleanup directory.
6. Summarise metrics (corr, sum_ratio, thresholds) in `phase_d_summary.md`, update docs/fix_plan.md attempts, and log the artifact path in Attempts History.
Pitfalls To Avoid:
- Do not leave stray print/log statements in simulator.py after the cleanup.
- Keep lattice-vector scaling at 1e-10; avoid “helpful” refactors around the fixed math.
- Preserve ROI ordering `(slow, fast)` and detector size arguments when rerunning nb-compare.
- No full pytest suite; stick to collect-only plus the mapped ROI parity command.
- Maintain the STAMP directory convention so reports stay traceable.
- Do not touch other instrumentation guards (e.g., trace helper taps) without instruction.
- Ensure commands.txt captures exact env vars and working directory for reproducibility.
Pointers:
- docs/fix_plan.md:40-61 — Attempt #15 recap and Phase D6 directive.
- plans/active/vectorization-parity-regression.md:60-76 — Phase D/E tables with D6 requirements and upcoming Phase E checks.
- plans/active/vectorization.md:14-41 — Vectorization relaunch plan noting parity gate dependencies.
- specs/spec-a-core.md:20-44 — Unit conversion contract driving the lattice-vector scaling.
- arch.md:69-74 — ADR-01 guidance on geometry/physics unit boundaries relevant to the cleanup.
Next Up: Phase E1 full-frame benchmark + high-res pytest rerun once the cleanup holds.
