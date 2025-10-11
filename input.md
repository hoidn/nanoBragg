Summary: Reconcile MOSFLM beam-centre mapping with the spec and lock in the detector regression evidence.
Mode: Parity
Focus: [DETECTOR-CONFIG-001] Detector defaults audit
Branch: feature/spec-based-2
Mapped tests: tests/test_at_parallel_002.py::TestATParallel002::test_beam_center_scales_with_pixel_size, tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation, tests/test_detector_config.py
Artifacts: reports/2026-01-test-suite-triage/phase_m3/$STAMP/mosflm_fix/
Do Now: [DETECTOR-CONFIG-001] MOSFLM spec alignment — env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py::TestATParallel002::test_beam_center_scales_with_pixel_size
If Blocked: Capture the blocker in reports/2026-01-test-suite-triage/phase_m3/$STAMP/mosflm_fix/blocked.md and log the issue under docs/fix_plan.md Attempts.

Priorities & Rationale:
- specs/spec-a-core.md:68-76 — MOSFLM defaults require `(detsize + pixel)/2` mm inputs plus a +0.5·pixel mapping; current code stores 51.2 mm and under-shoots the spec.
- golden_suite_generator/nanoBragg.c:1196-1230 — C reference shows Xbeam default set with +pixel/2 before adding the mapping offset; use this to confirm the target math.
- plans/active/detector-config.md:40-55 — Phase C rows now [P]; we need the spec audit, test realignment, and doc/tracker refresh to close them.
- docs/fix_plan.md:226-240 — Attempt #38 logged as partial; next actions call for spec reconciliation, doc sync, and a rerun of the chunked Phase L commands.
- reports/2026-01-test-suite-triage/phase_m3/20251011T182635Z/mosflm_fix/summary.md — Implementation bundle and logs to reuse when capturing the new STAMP.

How-To Map:
- Export STAMP=$(date -u +%Y%m%dT%H%M%SZ) and mkdir -p reports/2026-01-test-suite-triage/phase_m3/$STAMP/mosflm_fix/{commands,logs} before edits; tee every command into commands/commands.txt.
- Update tests/test_at_parallel_002.py and tests/test_detector_config.py to expect the spec values (51.25 mm defaults → 513.0 px after mapping) and add the XDS negative control from plan task B4; run the Do Now selector to observe the failure before touching implementation.
- Adjust src/nanobrag_torch/config.py so MOSFLM auto defaults remain `(detsize + pixel)/2` mm, and keep the +0.5 pixel mapping in src/nanobrag_torch/models/detector.py exactly once; confirm explicit user inputs still route through the mapping guard.
- Run the mapped selectors in order, teeing output to logs/pytest_targeted.log:
  1) env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py::TestATParallel002::test_beam_center_scales_with_pixel_size
  2) env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_003.py::TestATParallel003::test_detector_offset_preservation
  3) KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py
- After targeted parity holds, refresh docs (docs/architecture/detector.md §§8.2/9, docs/development/c_to_pytorch_config_map.md beam row) and remediation_tracker.md; document deltas in summary.md.
- Rerun the chunked Phase L commands (from plans/active/test-suite-triage.md Phase M0 table) with env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE …, storing each chunk under reports/2026-01-test-suite-triage/phase_m3/$STAMP/chunks/chunk_##/.

Pitfalls To Avoid:
- Do not leave DetectorConfig defaults at 51.2 mm; parity requires the spec formula `(detsize + pixel)/2`.
- Keep the +0.5 pixel offset MOSFLM-only and applied exactly once; avoid double-counting in pix0_vector or SMV header paths.
- Preserve device/dtype neutrality—no hard-coded CPU tensors or `.item()` calls on differentiable values.
- Don’t run `pytest tests/` monolithically; stick to the mapped selectors and the documented chunk workflow.
- Update docs/fix_plan.md Attempts and remediation_tracker.md in the same loop—no stale ledgers.
- Guard other conventions (XDS/DIALS/ADXV) while editing defaults; negative controls must stay green.
- Keep new artifacts under the stamped folder; avoid scattering logs in repo root.
- Validate the C vs PyTorch mapping before declaring done; cite nanoBragg.c lines in summary.

Pointers:
- specs/spec-a-core.md:68-86
- golden_suite_generator/nanoBragg.c:1178-1233
- plans/active/detector-config.md:30-55
- docs/fix_plan.md:226-240
- reports/2026-01-test-suite-triage/phase_m3/20251011T182635Z/mosflm_fix/summary.md

Next Up: Once MOSFLM aligns, prep the mixed-units hypotheses pack (Phase M3c) pulled from plans/active/test-suite-triage.md:186-214.
