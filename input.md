Summary: Enforce SAMPLE pivot for custom detector vectors and tidy parity artifacts.
Phase: Implementation
Focus: CLI-FLAGS-003 Phase H6f — custom-vector SAMPLE pivot
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_flags.py::TestCLIPivotSelection::test_custom_vectors_force_sample_pivot
Artifacts: reports/2025-10-cli-flags/phase_h6/visuals/; reports/2025-10-cli-flags/phase_h6/pivot_fix.md; reports/2025-10-cli-flags/phase_h6/pytest_pivot_fix.log
Do Now: CLI-FLAGS-003 Phase H6f — move the Phase H6 parity PNG/JPEGs under reports, add `tests/test_cli_flags.py::TestCLIPivotSelection::test_custom_vectors_force_sample_pivot`, then run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPivotSelection::test_custom_vectors_force_sample_pivot -v`
If Blocked: Capture the failing command + traceback in reports/2025-10-cli-flags/phase_h6/pivot_fix_attempt.log and leave Attempts History note before trying alternatives.
Priorities & Rationale:
- docs/fix_plan.md:457 — Next action now demands H6f pivot enforcement before normalization resumes.
- plans/active/cli-noise-pix0/plan.md:130 — Phase H6f checklist defines regression test + artifact expectations.
- docs/architecture/detector.md:51 — Pivot formulas; must flip to SAMPLE when custom vectors exist.
- specs/spec-a-cli.md:§3.4 — CLI precedence for custom geometry + pix0 overrides.
- reports/2025-10-cli-flags/phase_h6/pivot_parity.md — Evidence you just gathered; closing the gap depends on this change.
How-To Map:
- Relocate `img*_*.png`, `intimage_*.jpeg`, `noiseimage_preview.jpeg` into `reports/2025-10-cli-flags/phase_h6/visuals/` and update references in `pivot_parity.md` + `phase_h5/parity_summary.md`.
- Update `DetectorConfig.__post_init__` (or `from_cli_args`) to force SAMPLE pivot whenever any custom detector vectors or pix0 override is supplied; cite C reference lines and keep device/dtype neutrality.
- Add regression `TestCLIPivotSelection.test_custom_vectors_force_sample_pivot` covering: default BEAM, explicit SAMPLE override, and custom vectors forcing SAMPLE (cpu+cuda parametrization if feasible without blowing runtime).
- Log implementation decisions in `reports/2025-10-cli-flags/phase_h6/pivot_fix.md` and stash pytest output at `reports/2025-10-cli-flags/phase_h6/pytest_pivot_fix.log`.
- After tests pass, refresh trace via `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py --out reports/2025-10-cli-flags/phase_h6/post_fix/trace_py.log` for use in H6g (do not diff yet, just capture).
Pitfalls To Avoid:
- Do not drop the custom-vector precedence guard that skips pix0 override within BEAM mode.
- Keep tensors on caller device/dtype; no hard-coded `.cpu()` or float64 literals.
- Respect Evidence vs Implementation boundary: tests must run only after code changes staged.
- Maintain Protected Assets: leave docs/index.md, loop.sh, supervisor.sh untouched except via plans.
- Avoid re-running full test suite; stay scoped to targeted pytest + added trace harness.
- Do not overwrite existing reports; create new files or append with timestamps.
- Ensure new test skips or parametrizes when CUDA unavailable instead of failing.
- Preserve existing Attempt numbering in docs/fix_plan.md when logging outcomes.
- Keep `KMP_DUPLICATE_LIB_OK=TRUE` in environment for any PyTorch execution.
Pointers:
- docs/fix_plan.md#cli-flags-003-handle-nonoise-and-pix0_vector_mm
- plans/active/cli-noise-pix0/plan.md#phase-h6--pix0-divergence-isolation
- docs/architecture/detector.md:51
- specs/spec-a-cli.md
- reports/2025-10-cli-flags/phase_h6/pivot_parity.md
Next Up: H6g trace/nb-compare verification once SAMPLE pivot parity holds.
