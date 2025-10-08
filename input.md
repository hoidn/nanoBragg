Summary: Verify φ=0 rotations stay spec-compliant and capture fresh documentation before expanding the parity shim.
Mode: Docs
Focus: CLI-FLAGS-003 – Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c, tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_matches_spec
Artifacts: reports/2025-12-cli-flags/phase_l/spec_baseline_refresh/
Do Now: CLI-FLAGS-003 Phase L3k.3c.3 (spec baseline enforcement) — KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_matches_spec -q
If Blocked: Run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests/test_cli_scaling_phi0.py -q`, log the collector output under `reports/2025-12-cli-flags/phase_l/spec_baseline_refresh/collect.log`, and note the blockage in docs/fix_plan.md Attempt history before proceeding.
Priorities & Rationale:
- specs/spec-a-core.md:211 — Normative φ loop mandates fresh rotations each step; reconfirming this guards against the C carryover bug bleeding into spec docs.
- docs/bugs/verified_c_bugs.md:166 — Documents C-PARITY-001 as an implementation defect; the spec must continue to flag it as non-normative.
- src/nanobrag_torch/models/crystal.py:1106 — Default code path already enforces spec rotations; capturing evidence ensures regressions are caught early.
- tests/test_cli_scaling_phi0.py:17 — Regression tests assert the spec baseline; rerunning them satisfies the plan’s VG-1 gate.
- plans/active/cli-phi-parity-shim/plan.md:70 — Phase C4 waits on refreshed traces/documentation; this loop feeds its prerequisites without yet touching parity math.
How-To Map:
- Set env before tests: `export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md` and `export KMP_DUPLICATE_LIB_OK=TRUE` per runtime checklist.
- Execute targeted spec tests (CPU first): `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_matches_spec -q > reports/2025-12-cli-flags/phase_l/spec_baseline_refresh/pytest_cpu.log`.
- If CUDA available, rerun with `--device cuda` fixture enabled: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_matches_spec -q --device cuda > reports/2025-12-cli-flags/phase_l/spec_baseline_refresh/pytest_cuda.log`.
- Capture a short narrative in `reports/2025-12-cli-flags/phase_l/spec_baseline_refresh/summary.md` citing the command(s), pass/fail status, and confirming that spec mode remains default.
- Update docs/fix_plan.md Attempt for CLI-FLAGS-003 with log references and note that documentation refresh (Phase D1) can proceed once parity shim evidence is ready.
Pitfalls To Avoid:
- Do not edit specs to mention the carryover bug as normative.
- Leave `phi_carryover_mode` default set to "spec"; no testing with c-parity in this loop.
- Avoid running the full pytest suite—stick to the mapped selectors.
- Keep new artifacts under the `reports/2025-12-cli-flags/phase_l/spec_baseline_refresh/` timestamped subfolder; do not overwrite earlier evidence.
- Maintain device/dtype neutrality when adding any future instrumentation (no `.cpu()` conversions in core code).
- Respect Protected Assets: do not touch files listed in docs/index.md (e.g., loop.sh, supervisor.sh, input.md template).
- Record timestamps/commands in a `commands.txt` alongside the logs for reproducibility.
- If CUDA is unavailable, explicitly mention that in summary.md and skip the GPU run rather than forcing CPU fallback.
- Do not modify parity shim implementation yet; this pass is documentation/evidence only.
- Keep environment variables local to the session; no persistent shell RC edits.
Pointers:
- specs/spec-a-core.md:211
- docs/bugs/verified_c_bugs.md:166
- src/nanobrag_torch/models/crystal.py:1106
- tests/test_cli_scaling_phi0.py:17
- plans/active/cli-noise-pix0/plan.md:309
Next Up: Once documentation is refreshed, resume Phase C4 of the parity shim plan to tighten the c-parity per-φ trace deltas.
