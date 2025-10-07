Summary: Capture C vs PyTorch scaling traces for the supervisor command to isolate the intensity normalization divergence.
Mode: Parity
Focus: CLI-FLAGS-003 / Phase L2 scaling chain audit
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/{c_trace_scaling.log,trace_py_scaling.log,scaling_audit_summary.md}
Do Now: CLI-FLAGS-003 L2a — instrument nanoBragg.c then run `NB_C_BIN=./golden_suite_generator/nanoBragg nanoBragg -mat A.mat -floatfile /dev/null -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 2>&1 | tee reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log`
If Blocked: Capture the failing instrumentation or command output under `reports/2025-10-cli-flags/phase_l/scaling_audit/attempt_blocked.log`, annotate the issue in docs/fix_plan.md Attempts/L2c guidance, and pause for supervisor direction.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:233 — Phase L2 defines the scaling audit prerequisites for unblocking normalization fixes.
- docs/fix_plan.md:448 — CLI-FLAGS-003 entry now calls for L2a–L2c before any further nb-compare runs.
- specs/spec-a-core.md:300 — Scaling constants (r_e², fluence, steps) are normative and must be matched term-by-term.
- docs/architecture/pytorch_design.md:180 — Describes the expected normalization order in the PyTorch simulator.
- docs/development/testing_strategy.md:200 — Parallel validation requires identifying the first divergence before implementing fixes.
How-To Map:
- export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md
- Edit `golden_suite_generator/nanoBragg.c` around lines 3005–3335 to add `TRACE_C` logs for I_before_scaling, omega, polarization, capture_fraction, steps, r_e², fluence, and final intensity; rebuild with `make -C golden_suite_generator` before running the Do Now command.
- Create `reports/2025-10-cli-flags/phase_l/scaling_audit/` ahead of time (`mkdir -p ...`) so logs land in a clean directory.
- After gathering the C trace, duplicate the logged variable list in the PyTorch harness (`reports/2025-10-cli-flags/phase_i/supervisor_command/trace_harness.py` or new Phase L copy) and execute with `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py > reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log`.
- Align the two traces using a small diff script (`python reports/2025-10-cli-flags/phase_l/scaling_audit/compare_scaling_traces.py ...`) and summarise deltas in `scaling_audit_summary.md`.
- Supervisor evidence gate: only run `pytest --collect-only -q tests/test_cli_scaling.py` if you need to confirm selectors; do not execute tests fully this loop.
Pitfalls To Avoid:
- Do not leave instrumentation committed; capture patches separately and revert once traces are collected.
- Always set `KMP_DUPLICATE_LIB_OK=TRUE` before any Python command touching torch.
- Keep new artifacts under `reports/2025-10-cli-flags/phase_l/`; no ad-hoc paths.
- Preserve device/dtype neutrality in the PyTorch harness (avoid `.cpu()`/`.item()` on differentiable tensors).
- Respect Protected Assets (docs/index.md) — no deletions or renames of indexed files.
- Do not rerun nb-compare until scaling audit identifies the root cause.
- Avoid running the full pytest suite; stick to targeted collection checks only.
- Ensure beam/detector inputs exactly match the supervisor command; no shortcuts or simplified configs.
- Record any deviations or intermediate findings immediately in docs/fix_plan.md Attempt history.
Pointers:
- plans/active/cli-noise-pix0/plan.md:233
- docs/fix_plan.md:448
- specs/spec-a-core.md:300
- docs/architecture/pytorch_design.md:180
- docs/development/testing_strategy.md:200
Next Up: Phase L2b PyTorch trace capture once the C scaling log lands.
