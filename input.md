Summary: Fix C17 polarization regression so Phase O baseline can be rerun without AttributeError.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage
Branch: main
Mapped tests: tests/test_at_pol_001.py::TestATPOL001KahnModel::test_oversample_polar_last_value_semantics; tests/test_at_pol_001.py::TestATPOL001KahnModel::test_polarization_with_tilted_detector
Artifacts: reports/2026-01-test-suite-triage/phase_m3/$STAMP/c17_polarization_guard/
Do Now: [TEST-SUITE-TRIAGE-001] Guard the nopolar path before reshaping `physics_intensity_pre_polar_flat`, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest -vv tests/test_at_pol_001.py::TestATPOL001KahnModel::test_oversample_polar_last_value_semantics tests/test_at_pol_001.py::TestATPOL001KahnModel::test_polarization_with_tilted_detector --maxfail=1 --tb=short`
If Blocked: Capture the failure stack trace under reports/…/blocked.log and push the partial patch with notes in docs/fix_plan.md Attempts History.
Priorities & Rationale:
- Polarization guard per specs/spec-a-core.md (AT-POL-001) — `nopolar` must keep intensities finite, current crash blocks C17 fixes.
- Attempt #46 baseline (reports/2026-01-test-suite-triage/phase_o/20251015T003950Z/summary.md) shows this regression gates Phase O rerun and Sprint 1.4 status updates.
- plans/active/test-suite-triage.md Phase O marks O2 `[P]`; resolving this unblock moves Phase O forward.
- docs/fix_plan.md Next Actions #5–6 require this guard before the next chunk ladder rerun.
How-To Map:
1. Edit `src/nanobrag_torch/simulator.py` around lines 960-995 so the single-source branch skips reshaping/logging when `physics_intensity_pre_polar_flat is None` (BeamConfig.nopolar). Ensure downstream uses (e.g., `I_before_normalization_pre_polar`) tolerate the optional tensor.
2. Rerun the targeted tests: `env KMP_DUPLICATE_LIB_OK=TRUE pytest -vv tests/test_at_pol_001.py::TestATPOL001KahnModel::test_oversample_polar_last_value_semantics tests/test_at_pol_001.py::TestATPOL001KahnModel::test_polarization_with_tilted_detector --maxfail=1 --tb=short`.
3. Export `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; collect command log + pytest output under `reports/2026-01-test-suite-triage/phase_m3/$STAMP/c17_polarization_guard/{commands.txt,pytest.log,summary.md}` (record pass/fail counts and note the guard change).
4. Update docs/fix_plan.md Attempts History and plans/active/test-suite-triage.md Phase O table with the new result; note readiness for rerunning chunk 10.
Pitfalls To Avoid:
- Do not drop multi-source handling; the guard must only bypass reshape when the pre-polar tensor is actually None.
- Preserve vectorization (no per-subpixel Python loops) and keep device/dtype neutrality.
- Maintain trace instrumentation expectations (don’t remove `I_before_normalization_pre_polar` logging when available).
- Avoid `.item()` on tensors that require gradients; keep Torch ops differentiable.
- Don’t rerun the full pytest ladder yet; targeted tests only until guard is fixed.
- Keep Protected Assets intact (`docs/index.md`, `loop.sh`, `supervisor.sh`).
Pointers:
- specs/spec-a-core.md §AT-POL-001 (polarization semantics)
- reports/2026-01-test-suite-triage/phase_o/20251015T003950Z/summary.md
- plans/active/test-suite-triage.md:302-315 (Phase O tasks)
- docs/fix_plan.md:5-6, 19-21 (Next Actions #5–6)
Next Up: After the guard lands, rerun Phase O chunk ladder with refreshed chunk 10 selectors.
