Summary: Remove weighted-source scaling so PyTorch matches C and unblock downstream vectorization work.
Mode: Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: pytest tests/test_cli_scaling.py::TestSourceWeights -v | NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeights::test_weighted_source_matches_c -v
Artifacts: reports/2025-11-source-weights/phase_c/<STAMP>/ | reports/2025-11-source-weights/phase_d/<STAMP>/
Do Now: [SOURCE-WEIGHT-001] Correct weighted source normalization — after Phase C1–C3 edits, run NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeights::test_weighted_source_matches_c -v
If Blocked: Capture failure logs under reports/2025-11-source-weights/phase_c/<STAMP>/attempts/ with commands.txt + env.json and note blockers in docs/fix_plan.md Attempts before pausing.
Priorities & Rationale:
- specs/spec-a-core.md:151 – spec mandates the weight column is ignored; implementation must comply.
- plans/active/source-weight-normalization.md:1 – Phase C is the active gate; Phase D parity unlocks VECTOR-GAPS-002 and PERF-PYTORCH-004.
- docs/fix_plan.md:3963 – Next Actions now expect Phase C implementation and Phase D validations; keep ledger aligned.
- reports/2025-11-source-weights/phase_b/20251009T083515Z/analysis.md – documents current parity gap and oversample caveat to control during reruns.
- tests/test_cli_scaling.py:252 – existing TestSourceWeights cases need updates to assert equal totals for weighted inputs.
How-To Map:
- Implementation: Edit src/nanobrag_torch/simulator.py::_compute_physics_for_position to drop weights_broadcast from the accumulation path; adjust any cached metadata in Simulator.__init__ or run() so weights remain optional trace data. Keep tensor ops batched and gradient-friendly (no .item()).
- Tests: `pytest tests/test_cli_scaling.py::TestSourceWeights -v` (CPU) after edits; re-run with `pytest -k TestSourceWeights --maxfail=1 --disable-warnings` if you need a quick smoke.
- Parity proof: `NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeights::test_weighted_source_matches_c -v` (expect pass, collect log under phase_d/<STAMP>/pytest/).
- CLI metrics: Reproduce C vs PyTorch totals using the fixture `reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt`. Set `export NB_C_BIN=./golden_suite_generator/nanoBragg` before running parity steps.
  * C: `./golden_suite_generator/nanoBragg -mat A.mat -floatfile c_weight.bin -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10`.
  * PyTorch: `KMP_DUPLICATE_LIB_OK=TRUE nanoBragg -mat A.mat -floatfile py_weight.bin -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10`.
  * Capture stdout/stderr, metrics.json, and env.json under phase_d/<STAMP>/metrics/.
- Artifacts: Phase C implementation logs (collect-only proof, pytest logs, diff summary) go to reports/2025-11-source-weights/phase_c/<STAMP>/{commands.txt, implementation.md, pytest/*.log, env.json}. Phase D parity bundle goes to phase_d/<STAMP>/{pytest/, metrics/, commands.txt, summary.md}.
- Documentation: After metrics stabilise, update docs/architecture/pytorch_design.md Sources subsection and docs/development/testing_strategy.md Tier 1 mapping; note changes in docs/fix_plan.md Attempts and plans/active/source-weight-normalization.md status snapshot.
Pitfalls To Avoid:
- Do not reintroduce scalar loops; keep the batching path intact for sources × phi × mosaic × oversample.
- Preserve device/dtype neutrality — use existing tensors’ device when creating helpers (no implicit CPU tensors).
- Avoid .item()/.detach() on gradients; weighted paths must remain differentiable.
- Ensure oversample factors match between C and PyTorch runs (force `-oversample 1`).
- Keep tests parametrised for CUDA but skip gracefully if unavailable; do not hard-fail on missing GPU.
- Retain trace metadata: weights can still be logged but must not influence physics.
- Respect Protected Assets (docs/index.md) when editing docs; update references not deletions.
- Capture collect-only proof before running targeted pytest to document selector validity.
- Don’t forget to set NB_RUN_PARALLEL=1 for the parity test or it will skip.
- Archive env.json/checksums for every artifact bundle.
Pointers:
- specs/spec-a-core.md:151
- plans/active/source-weight-normalization.md:1
- docs/fix_plan.md:3963
- reports/2025-11-source-weights/phase_b/20251009T083515Z/analysis.md
- tests/test_cli_scaling.py:252
- src/nanobrag_torch/simulator.py:400
Next Up: 1) Once parity metrics land, notify VECTOR-GAPS-002 Phase B to resume profiling; 2) Refresh docs/development/pytorch_runtime_checklist.md if weighted-source guidance needs reinforcement.
