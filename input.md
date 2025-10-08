Summary: Finish Phase D proof-of-removal by fixing the trace harness and capturing spec-mode evidence for φ carryover removal.
Mode: Parity
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_phi0.py
Artifacts: reports/2025-10-cli-flags/phase_phi_removal/phase_d/<STAMP>/
Do Now: [CLI-FLAGS-003] Phase D0→D1 — refresh the trace harness, then run `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --out reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/trace_py_spec.log` followed by `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py`
If Blocked: Capture the failure output under `reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/` and append a new summary.md describing the blocker; update docs/fix_plan.md Attempt log with the timestamp.
Priorities & Rationale:
- plans/active/phi-carryover-removal/plan.md:58 — Phase D now requires a D0 harness refresh before D1 can proceed.
- docs/fix_plan.md:451 — Next actions call for Phase D0–D1 execution to close the shim removal effort.
- reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T201125Z/summary.md — Documents the current blocker (legacy `phi_carryover_mode` argument) that D0 must resolve.
- specs/spec-a-core.md:205 — Normative statement that every φ step must use freshly rotated vectors; use this citation in the new summary.md.
- plans/active/cli-noise-pix0/plan.md:33 — Main CLI parity plan now points at the same D0/D1 work before scaling tasks resume.
How-To Map:
- `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and `mkdir -p reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP`
- Edit `reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py` to remove `--phi-mode` parsing and the `phi_carryover_mode` keyword before rerunning (keep changes scoped to tooling).
- `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --out reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/trace_py_spec.log`
- Reproduce the C trace with the supervisor command: `NB_C_BIN=./golden_suite_generator/nanoBragg $NB_C_BIN -mat A.mat -floatfile /tmp/c_trace.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 -trace_pixel 685 1039 2>&1 | tee reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/trace_c_spec.log`
- `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py | tee reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/pytest.log`
- `rg --files-with-matches "phi_carryover" src tests scripts prompts docs | sort > reports/2025-10-cli-flags/phase_phi_removal/phase_d/$STAMP/rg_phi_carryover.txt`
- Write `summary.md`, `commands.txt`, and `metrics.json` (include k_frac deltas) inside the timestamp directory and record SHA256 hashes.
Pitfalls To Avoid:
- Do not reintroduce `phi_carryover_mode` to production modules; keep edits confined to the harness.
- Preserve device/dtype neutrality when updating the harness (no hard-coded `.cpu()` or float64 defaults outside debug paths).
- Always set `KMP_DUPLICATE_LIB_OK=TRUE` before importing torch or running pytest.
- Keep Protected Assets untouched (docs/index.md, loop.sh, supervisor.sh, input.md).
- Document every command executed in `commands.txt` to keep audit trails reproducible.
- Ensure the C trace command mirrors the supervisor geometry exactly; mismatched flags invalidate comparisons.
- Store artifacts only under the new Phase D timestamp directory; avoid overwriting historical Phase L files.
- Run pytest only after the harness update succeeds; do not skip the `--collect-only` sanity unless collection already proven.
- Use `git diff` to verify harness edits before committing; no stray whitespace or debug prints.
- When copying existing traces, note provenance in summary.md instead of overwriting originals.
Pointers:
- plans/active/phi-carryover-removal/plan.md:58
- docs/fix_plan.md:451
- reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T201125Z/summary.md
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:1
- specs/spec-a-core.md:205
Next Up: 1) Phase D2 ledger sync once the new bundle exists; 2) Resume Phase L scaling parity (VG-2) per plans/active/cli-noise-pix0/plan.md.
