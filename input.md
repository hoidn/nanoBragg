Summary: Capture the φ-carryover proof-of-removal bundle (spec-mode traces + pytest evidence) so we can close the shim cleanup.
Mode: Parity
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_phi0.py
Artifacts: reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/
Do Now: [CLI-FLAGS-003] proof-of-removal bundle — export STAMP=$(date -u +%Y%m%dT%H%M%SZ); KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --out reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/trace_py_spec.log; NB_C_BIN=./golden_suite_generator/nanoBragg $NB_C_BIN -mat A.mat -floatfile /tmp/c_trace.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 -trace_pixel 685 1039 2>&1 | tee reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/trace_c_spec.log; KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py | tee reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/pytest.log
If Blocked: Capture stdout/stderr plus the failing command in reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/, note the blocker in summary.md (cite specs/spec-a-core.md:205), and log the attempt in docs/fix_plan.md before stopping.
Priorities & Rationale:
- plans/active/phi-carryover-removal/plan.md:59 — D1 tasks demand fresh Py + C traces and pytest proof in a new timestamp bundle.
- docs/fix_plan.md:466 — Next steps explicitly call for this proof-of-removal bundle before ledger sync.
- reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T201125Z/summary.md — Documents the previous blocker; we must replace it with a successful rerun.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:1 — Harness now emits spec-only traces; use it without any phi-mode flag.
- scripts/validation/compare_scaling_traces.py:15 — Canonical tool for computing scaling deltas and metrics.json for the bundle.
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ) && mkdir -p reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP
- KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --out reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/trace_py_spec.log (copy trace_py_env.json into the same directory afterwards)
- NB_C_BIN=./golden_suite_generator/nanoBragg $NB_C_BIN -mat A.mat ... -trace_pixel 685 1039 2>&1 | tee reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/trace_c_spec.log (match geometry exactly and keep the floatfile disposable)
- KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --py reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/trace_py_spec.log --c reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/trace_c_spec.log --out reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/scaling_trace_summary.md (produces metrics.json and run_metadata.json)
- KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py | tee reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/pytest.log; also save pytest --collect-only output to collect.log if rerun is cheap
- rg --files-with-matches "phi_carryover" src tests scripts prompts docs | sort > reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/rg_phi_carryover.txt (expect empty)
- Write summary.md (cite specs/spec-a-core.md:205) and commands.txt inside the timestamp directory; include Δk_frac max from pytest.log and key deltas from metrics.json; generate sha256.txt via (cd reports/.../$STAMP && sha256sum * > sha256.txt)
Pitfalls To Avoid:
- Do not pass any legacy phi-mode flags or edit production code; harness already matches spec.
- Keep PYTHONPATH=src for every Python invocation so we hit the editable install.
- Ensure both traces come from the same commit and timestamp; mixing earlier logs invalidates the comparison.
- Maintain dtype/device neutrality: keep tensor dtype arguments explicit (float64 for the harness run), but avoid hard-coded .cpu() edits.
- Store every artifact in the new timestamp directory; never overwrite the historical scaling audit files under reports/2025-10-cli-flags/phase_l/.
- Verify commands.txt mirrors the exact sequence executed (including env exports and tee targets).
- Add the rg sweep output even when empty; it proves no residual references remain.
- Capture env metadata (trace_py_env.json, run_metadata.json) before running sha256 to avoid hash drift.
- Stop immediately if the comparison script flags large deltas; attach stdout to the bundle and abort instead of editing code.
Pointers:
- plans/active/phi-carryover-removal/plan.md:59
- docs/fix_plan.md:466
- reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T201125Z/summary.md
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:1
- scripts/validation/compare_scaling_traces.py:15
Next Up: ledger sync (docs/fix_plan.md update and plan archival) once the new bundle is captured.
