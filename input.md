Summary: Restore the lattice-shape acceptance tests by giving them a real Detector so Cluster C7 stops invoking Simulator with None.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Phase M1e — Cluster C7 lattice-shape fixtures
Branch: feature/spec-based-2
Mapped tests: tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_gauss_shape_model; tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_shape_model_comparison
Artifacts: reports/2026-01-test-suite-triage/phase_m1/$STAMP/shape_models/{env.txt,pytest_before.log,pytest_module.log,summary.md}
Do Now: [TEST-SUITE-TRIAGE-001] Phase M1e — env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_gauss_shape_model
If Blocked: Capture the failing log as reports/2026-01-test-suite-triage/phase_m1/$STAMP/shape_models/blocked.log, note the blocker + command in docs/fix_plan.md Attempt history and remediation_tracker.md, then halt for supervisor review.

Priorities & Rationale:
- docs/fix_plan.md:36-113 — Sprint 0 now only has Cluster C7 outstanding; Next Actions call for the lattice-shape quick fix before M2.
- plans/active/test-suite-triage.md:202-222 — Phase M1e directs us to supply a Detector fixture and validate with the shape-model tests.
- reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md:218-243 — Cluster C7 scope, failure message, and reproduction command.
- tests/test_at_str_003.py:1-220 — The failing fixtures currently pass detector=None and must be updated.
- src/nanobrag_torch/models/detector.py:24-140 — Constructor contract that requires a valid DetectorConfig (mirrors the AttributeError the tests hit).

How-To Map:
1. `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` then `mkdir -p reports/2026-01-test-suite-triage/phase_m1/$STAMP/shape_models` and record `env | sort > .../env.txt`.
2. Reproduce the failure and tee output: `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_str_003.py::TestAT_STR_003_LatticeShapeModels::test_gauss_shape_model | tee reports/.../pytest_before.log`.
3. Update `tests/test_at_str_003.py` so every Simulator invocation constructs a `Detector(self.detector_config, device="cpu", dtype=torch.float32)` (or the test’s dtype) and passes it positionally. Keep crystal/beam setups untouched.
4. Rerun the focused selector and the companion case: `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_str_003.py -k "TestAT_STR_003_LatticeShapeModels" | tee reports/.../pytest_module.log`.
5. Summarise edits, commands, pass counts, remaining skips (if any), and follow-ups in `reports/.../summary.md`; include pointers to updated code lines.
6. Update docs/fix_plan.md Attempt #27 (or next) with the new artifact path + pass counts and refresh plans/active/test-suite-triage.md row M1e to [D]; sync remediation_tracker.md with the reduced failure tally.

Pitfalls To Avoid:
- Do not leave any Simulator invocation with `detector=None`.
- Keep device/dtype neutrality—no `.cpu()` calls in the tests after results.
- Preserve existing assertions; only touch setup wiring needed for Detector construction.
- Ensure every pytest command includes `KMP_DUPLICATE_LIB_OK=TRUE` and runs with CUDA disabled.
- Store artifacts under the new `$STAMP/shape_models` folder without overwriting prior attempts.
- Avoid editing production Simulator code; this loop is test-fixture only.
- Update both docs/fix_plan.md and remediation_tracker.md in the same loop to keep counts consistent.
- Reference DetectorConfig defaults (beam centers) rather than hard-coding new coordinates.
- Leave gradient compilation guards (Phase M2 work) untouched for now.
- Keep the summary concise but include pass/fail deltas and any residual TODOs.

Pointers:
- docs/fix_plan.md:36-113
- plans/active/test-suite-triage.md:202-222
- reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md:218-243
- tests/test_at_str_003.py:1-220
- src/nanobrag_torch/models/detector.py:24-140

Next Up: Phase M1f — ledger + remediation tracker refresh once Cluster C7 passes.
