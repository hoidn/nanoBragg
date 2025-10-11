Summary: Capture fresh MOSFLM detector evidence and push the post-fix suite rerun for [DETECTOR-CONFIG-001].
Mode: Parity
Focus: docs/fix_plan.md#[DETECTOR-CONFIG-001] Detector defaults audit
Branch: feature/spec-based-2
Mapped tests: tests/test_detector_config.py; tests/test_at_parallel_002.py::TestATParallel002::test_beam_center_scales_with_pixel_size; pytest chunk map per plans/active/test-suite-triage.md Phase M
Artifacts: reports/2026-01-test-suite-triage/phase_m3/$STAMP/mosflm_fix/; reports/2026-01-test-suite-triage/phase_m/$STAMP/chunks/; reports/2026-01-test-suite-triage/phase_m/$STAMP/summary.md
Do Now: docs/fix_plan.md#[DETECTOR-CONFIG-001] Detector defaults audit — env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_config.py --maxfail=0
If Blocked: If detector_config pytest fails unexpectedly, stop, capture the failing log under the stamped folder, and note the exit code plus hypothesis in attempts history; do not proceed to chunked runs.
Priorities & Rationale:
- specs/spec-a-core.md:72 — MOSFLM defaults require (detsize + pixel)/2 before applying the +0.5 mapping; need evidence that implementation now matches.
- docs/fix_plan.md:220 — Next actions demand a fresh targeted bundle and tracker sync before closing the cluster.
- plans/active/detector-config.md:42 — Phase C gate now hinges on rerunning chunked Phase M commands post-fix.
- plans/active/test-suite-triage.md:232 — Phase M instructions define the chunked rerun cadence and storage layout we must follow.
How-To Map:
- Export STAMP="$(date -u +%Y%m%dT%H%M%SZ)" once and reuse it for both bundles.
- Targeted bundle: run the Do Now command, then `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_002.py::TestATParallel002::test_beam_center_scales_with_pixel_size --maxfail=0`; save `commands.txt`, both pytest logs, and a short `summary.md` (note 513.0 px / 1024.5 px expectations) into `reports/2026-01-test-suite-triage/phase_m3/$STAMP/mosflm_fix/`.
- Tracker sync: once logs are captured, update `reports/2026-01-test-suite-triage/phase_k/20251011T072940Z/analysis/summary.md` and `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md` with the new status, then append the Attempt to docs/fix_plan.md.
- Chunked rerun: follow the 10-command map in `plans/active/test-suite-triage.md` (Chunk 01–10). Set up `reports/2026-01-test-suite-triage/phase_m/$STAMP/chunks/`, copy the command list to `commands.txt`, run each command prefixed with `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE`, and tee logs to `chunks/chunk_##/pytest.log`. Aggregate counts into `phase_m/$STAMP/summary.md` with pass/fail/skipped totals versus Phase M0.
- After tests, update docs/fix_plan.md Attempts history and note residual failure clusters; leave remediation_tracker diffs staged for review.
Pitfalls To Avoid:
- Do not rerun the entire suite without the chunk split; the single-command run times out.
- Keep `KMP_DUPLICATE_LIB_OK=TRUE` on every pytest invocation to avoid MKL crashes.
- Reuse the same STAMP for all artifacts in this loop; mismatched directories break audit trails.
- Avoid editing production code—this loop is evidence capture only.
- When updating trackers, change only the relevant cluster rows; retain historical counts.
- Don’t overwrite older `phase_m3` bundles; add a new stamped folder.
- Watch for GPU availability—if CUDA is absent, note it in summary.md and proceed CPU-only.
- Ensure pytest exits with `--maxfail=0` so we collect full failure sets.
- Keep docs/index.md referenced assets untouched (loop.sh, supervisor.sh, input.md).
- Document commands and runtimes inside each folder via `commands.txt` for reproducibility.
Pointers:
- specs/spec-a-core.md#L70 — MOSFLM default and mapping formula reference.
- docs/architecture/detector.md#L143 — Updated narrative for beam-center handling.
- docs/development/c_to_pytorch_config_map.md#L54 — Beam parameter mapping expectations.
- plans/active/detector-config.md#L40 — Phase C status + guidance.
- plans/active/test-suite-triage.md#L228 — Phase M chunk workflow and goals.
Next Up: If time remains, prep docs/fix_plan.md Attempt summary for the chunked rerun so we can transition to Phase M tracker updates next loop.
