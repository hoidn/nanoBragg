Summary: Close the MOSFLM scaling gap so CLI-FLAGS-003 can advance to Phase L with fresh parity evidence.
 - Phase: Evidence
 - Mode: Parity
Focus: CLI-FLAGS-003 Phase K3g3 — MOSFLM scaling parity
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py::TestFlattSquareMatchesC::test_f_latt_square_matches_c (collect-only verified 2025-11-08)
Artifacts: reports/2025-10-cli-flags/phase_k/f_latt_fix/post_fix/
Do Now: CLI-FLAGS-003 Phase K3g3 — env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest tests/test_cli_scaling.py::TestFlattSquareMatchesC::test_f_latt_square_matches_c -v
If Blocked: Capture new base-lattice traces via reports/2025-10-cli-flags/phase_k/base_lattice/run_c_trace.sh and trace_harness.py, stash outputs under reports/2025-10-cli-flags/phase_k/base_lattice/blocked/<timestamp>/, and log the stall in docs/fix_plan.md Attempt history before awaiting guidance.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md: K3g3 exit criteria demand rerunning the scaling pytest node and nb-compare with updated artifacts before entering Phase L.
- docs/fix_plan.md#cli-flags-003-handle-nonoise-and-pix0_vector_mm: Next Actions section explicitly calls for the same targeted pytest command and refreshed evidence.
- reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain.md: Currently frozen at the failed October run; needs new metrics to confirm MOSFLM rescale fix impact.
- reports/2025-10-cli-flags/phase_k/base_lattice/summary.md: Post-fix addendum shows cell tensors now match C; we must propagate that success into the scaling parity log.
- docs/development/testing_strategy.md#tier-1-translation-correctness: Requires artifact-backed parity before claiming spec compliance for new CLI flags.

How-To Map:
- Run env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest tests/test_cli_scaling.py::TestFlattSquareMatchesC::test_f_latt_square_matches_c -v and tee stdout to reports/2025-10-cli-flags/phase_k/f_latt_fix/post_fix/pytest.log.
- Immediately follow with nb-compare using the supervisor command: nb-compare --outdir reports/2025-10-cli-flags/phase_k/f_latt_fix/post_fix/nb_compare -- -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0.
- Use stamp=$(date +%Y%m%d%H%M%S) to keep filenames unique, then: sh reports/2025-10-cli-flags/phase_k/base_lattice/run_c_trace.sh | tee reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/c_trace_${stamp}.log.
- Generate the matching PyTorch trace with PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 python reports/2025-10-cli-flags/phase_k/base_lattice/trace_harness.py --out reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/trace_py_${stamp}.log --dtype float64 --device cpu.
- Diff the traces via python reports/2025-10-cli-flags/phase_k/base_lattice/compare_traces.py --c reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/c_trace_${stamp}.log --py reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/trace_py_${stamp}.log > reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/trace_diff_${stamp}.txt and summarize deltas in base_lattice/summary.md.
- Update scaling_chain.md and summary.md with new metrics, and append Attempt notes plus artifact paths to docs/fix_plan.md under CLI-FLAGS-003.

Pitfalls To Avoid:
- Do not run the full pytest suite; stay on the single selector until code changes land.
- Keep NB_C_BIN pointed at ./golden_suite_generator/nanoBragg for all trace and nb-compare runs.
- Avoid rerunning scripts/trace_per_phi.py until the scaling parity shows green; we need clean baseline first.
- Preserve device/dtype neutrality—when regenerating traces, use float64 CPU per plan but avoid hard-coding .cpu() into production code.
- Do not overwrite existing artifacts; rely on the ${stamp} suffix to preserve provenance.
- Remember Protected Assets rule: leave docs/index.md and loop.sh untouched.
- Skip git add/commit until the supervisor review closes the loop.
- Ensure KMP_DUPLICATE_LIB_OK=TRUE is set for every Python invocation that imports torch.
- Capture nb-compare stdout/stderr in the same post_fix directory for traceability.
- Document any deviation (like CUDA unavailability) directly in docs/fix_plan.md Attempt log.

Pointers:
- plans/active/cli-noise-pix0/plan.md:201 — Phase K3g3 tasks and guidance.
- docs/fix_plan.md:448 — CLI-FLAGS-003 ledger with latest Next Actions.
- reports/2025-10-cli-flags/phase_k/base_lattice/summary.md — Post-fix cell tensor notes.
- specs/spec-a-core.md:480 — Normalization and F_latt acceptance thresholds.
- docs/development/testing_strategy.md:120 — Tier-1 parity requirements.
- src/nanobrag_torch/models/crystal.py:650 — MOSFLM real-vector recomputation logic you just validated.

Next Up: When K3g3 passes, proceed to Phase L1 nb-compare rerun followed by the CLI regression sweep (tests/test_cli_flags.py tests/test_cli_scaling.py) before plan closeout.
