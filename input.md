Summary: Get the MOSFLM beam-centre offset fix landed and prove the detector geometry selectors pass.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: tests/test_at_parallel_002.py::TestATParallel002::test_beam_center_scales_with_pixel_size, tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation, tests/test_detector_config.py
Artifacts: reports/2026-01-test-suite-triage/phase_m3/$STAMP/mosflm_fix/{commands.txt,pytest_targeted.log,summary.md}
Do Now: [DETECTOR-CONFIG-001] Phase C1–C3 — env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py::TestATParallel002::test_beam_center_scales_with_pixel_size
If Blocked: Capture the blocker in reports/2026-01-test-suite-triage/phase_m3/$STAMP/mosflm_fix/blocked.md and halt; note the issue in docs/fix_plan.md Attempts History.

Priorities & Rationale:
- MOSFLM’s +0.5 pixel rule is normative (specs/spec-a-core.md:68-86) and currently violated, driving Cluster C6.
- Detector remediation blueprint already pins the edit sites and tests (plans/active/detector-config.md:30-44); this loop is for executing C1–C3.
- Fix-plan next actions now require this attempt before any further triage (docs/fix_plan.md:38-58, 226-241).
- Phase M3a evidence maps the failing selectors and expected artifacts (reports/2026-01-test-suite-triage/phase_m3/20251011T175917Z/mosflm_sync/summary.md:38-88).

How-To Map:
- Set STAMP=$(date -u +%Y%m%dT%H%M%SZ) and mkdir -p reports/2026-01-test-suite-triage/phase_m3/$STAMP/mosflm_fix/ before touching code; capture every command in commands.txt under that folder.
- Implement the MOSFLM-only +0.5 pixel adjustment inside src/nanobrag_torch/models/detector.py (reuse detector-config plan guidance); ensure tensors keep caller dtype/device and avoid .item().
- Extend tests/test_detector_config.py per plan (new MOSFLM expectations plus XDS negative control) and update any fixtures that rely on old values; run pytest --maxfail=1 -vv on the new cases before the full module if helpful.
- Run the targeted commands in order, teeing output to reports/…/pytest_targeted.log:
  1) env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py::TestATParallel002::test_beam_center_scales_with_pixel_size
  2) env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation
  3) KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py
- Update docs: refresh docs/architecture/detector.md and docs/development/c_to_pytorch_config_map.md with the explicit MOSFLM offset note; log results in docs/fix_plan.md Attempt history and remediation_tracker.md.
- Summarise outcomes in summary.md (what changed, tests run, remaining risks) and note next validation gate (Phase M full-suite rerun deferred until instructed).

Pitfalls To Avoid:
- Don’t apply the +0.5 offset to non-MOSFLM conventions—guard on DetectorConvention.MOSFLM only.
- Preserve device/dtype neutrality; reuse existing tensor factories instead of hard-coding torch.tensor(..., device="cpu").
- No `.item()`/`.numpy()` on differentiable tensors; keep gradients intact (arch.md §15).
- Keep protected assets (`input.md`, `loop.sh`, docs/index.md references) untouched except where mandated.
- Run only the mapped selectors; postpone full pytest tests/ until a supervisor requests it.
- Capture artifacts under the stamped folder; don’t scatter logs in /tmp or repo root.
- Maintain consistent STAMP usage across commands.txt, pytest logs, and summary.md.
- Update documentation and tracker in the same loop; don’t leave the plan in an inconsistent state.
- Verify new tests use indexing="ij" conventions where grids appear and respect float tolerances already in suite.
- When editing docs, avoid drifting from spec wording; quote where necessary instead of paraphrasing loosely.

Pointers:
- plans/active/detector-config.md:30-46 — blueprint for C1–C4 implementation tasks.
- docs/fix_plan.md:38-58,226-241 — active next actions and exit criteria for this focus area.
- reports/2026-01-test-suite-triage/phase_m3/20251011T175917Z/mosflm_sync/summary.md:38-88 — failing selectors, commands, and spec citations.
- specs/spec-a-core.md:68-86 — MOSFLM beam-centre convention requirements.
- arch.md:79-86 — ADR-03 beam-centre mapping decisions to mirror in code/docs.

Next Up: Phase M3c mixed-units hypotheses pack once MOSFLM C6 passes and tracker is updated.
