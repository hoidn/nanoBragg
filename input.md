Summary: Audit every golden dataset touched by the lattice fix and document which files require regeneration before rerunning Phase E parity.
Mode: Parity
Focus: TEST-GOLDEN-001 / Regenerate golden data post Phase D5
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-golden-refresh/phase_a/$STAMP/
Do Now: [TEST-GOLDEN-001] Phase A — run the high-resolution 4096² ROI nb-compare audit and begin `scope_summary.md`; command: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/nb_compare.py --resample --roi 1792 2304 1792 2304 --outdir reports/2026-01-golden-refresh/phase_a/$STAMP/high_resolution_4096 -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05`
If Blocked: Capture stderr + params under `reports/2026-01-golden-refresh/phase_a/$STAMP/attempt_failed/`, note the blocker in docs/fix_plan.md Attempts, and halt.
Priorities & Rationale:
- docs/fix_plan.md:9 lists TEST-GOLDEN-001 as new high-priority work blocking Phase E.
- docs/fix_plan.md:170 records Attempt #17 failure details and the need for a golden refresh.
- plans/active/test-golden-refresh.md:1 defines Phase A deliverables (scope audit + summary artefacts).
- tests/golden_data/README.md:120 contains canonical commands and provenance requirements per dataset.
- plans/active/vectorization-parity-regression.md:4 notes Phase E remains blocked until refreshed assets exist.
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ)
- mkdir -p reports/2026-01-golden-refresh/phase_a/$STAMP/high_resolution_4096
- KMP_DUPLICATE_LIB_OK=TRUE python scripts/nb_compare.py --resample --roi 1792 2304 1792 2304 --outdir reports/2026-01-golden-refresh/phase_a/$STAMP/high_resolution_4096 -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05 | tee reports/2026-01-golden-refresh/phase_a/$STAMP/high_resolution_4096/commands.txt
- Parse tests/golden_data/README.md for remaining datasets; enumerate them in reports/2026-01-golden-refresh/phase_a/$STAMP/scope_summary.md with planned commands and current status (✓/todo).
- List consuming tests for each dataset (grep `tests/test_*.py`); record paths + selectors in the same scope summary.
- Copy key metrics (corr, sum_ratio) from nb-compare summary.json into phase_a_summary.md alongside hypotheses about which physics changes affected them.
Pitfalls To Avoid:
- Do not overwrite binaries in tests/golden_data/ during Phase A — audit only.
- Keep NB_C_BIN pointed at ./golden_suite_generator/nanoBragg for comparability.
- Avoid reusing STAMP directories; create a fresh timestamp per audit run.
- Do not commit the reports/ scratch output; reference paths in docs instead.
- Maintain device/dtype neutrality if additional probes are needed (no hard-coded `.cpu()` calls in scripts).
- Respect Protected Assets (`docs/index.md` items) when planning future regenerations.
- Capture exact commands/environment in commands.txt for reproducibility.
- Stop after Phase A scope capture — defer regeneration or pytest runs to later phases.
Pointers:
- docs/fix_plan.md:9
- docs/fix_plan.md:170
- plans/active/test-golden-refresh.md
- plans/active/vectorization-parity-regression.md
- reports/2026-01-vectorization-parity/phase_e/20251010T082240Z/phase_e_summary.md
Next Up: Phase B regeneration runs (C golden rebuilds with SHA tracking) once the scope audit lands.
