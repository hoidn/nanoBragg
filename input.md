Summary: Validate the MOSFLM scaling fix so CLI parity evidence can advance toward the supervisor command.
 - Mode: Parity
Focus: CLI-FLAGS-003 K3g3 — MOSFLM scaling parity rerun
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py::TestFlattSquareMatchesC::test_f_latt_square_matches_c (use --collect-only first if unsure)
Artifacts: reports/2025-10-cli-flags/phase_k/f_latt_fix/post_fix/; reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/
Do Now: CLI-FLAGS-003 K3g3 — env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest tests/test_cli_scaling.py::TestFlattSquareMatchesC::test_f_latt_square_matches_c -v
If Blocked: Capture fresh base-lattice traces via reports/2025-10-cli-flags/phase_k/base_lattice/run_c_trace.sh and trace_harness.py, archive under reports/2025-10-cli-flags/phase_k/base_lattice/blocked/<timestamp>/, note the stall in docs/fix_plan.md Attempt history, then follow prompts/debug.md trace-first SOP.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:201 — K3g3 exit criteria require the targeted pytest node plus refreshed nb-compare and scaling artifacts before Phase L.
- docs/fix_plan.md:448 — Next Actions call for the same pytest command, scaling_chain.md refresh, and nb-compare rerun to prove the MOSFLM rescale fix.
- reports/2025-10-cli-flags/phase_k/base_lattice/summary.md — Post-fix addendum shows cell tensors match C, but the main diff is still pre-fix; regenerate with new traces after the pytest run.
- reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain.md — Frozen at the October failure; needs updated factors to confirm the normalization pipeline is corrected.
- specs/spec-a-cli.md: detector & normalization clauses demand matching intensity scaling for -pix0_vector_mm runs before the supervisor command can succeed.
- docs/development/testing_strategy.md:120 — Tier-1 parity requires artifact-backed validation of each CLI addition; K3g3 supplies that proof.

How-To Map:
- export KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg
- STAMP=$(date +%Y%m%d%H%M%S)
- pytest --collect-only -q tests/test_cli_scaling.py::TestFlattSquareMatchesC::test_f_latt_square_matches_c (optional check)
- pytest -v tests/test_cli_scaling.py::TestFlattSquareMatchesC::test_f_latt_square_matches_c | tee reports/2025-10-cli-flags/phase_k/f_latt_fix/post_fix/pytest_${STAMP}.log
- nb-compare --outdir reports/2025-10-cli-flags/phase_k/f_latt_fix/post_fix/nb_compare_${STAMP} -- -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 | tee reports/2025-10-cli-flags/phase_k/f_latt_fix/post_fix/nb_compare_${STAMP}.log
- sh reports/2025-10-cli-flags/phase_k/base_lattice/run_c_trace.sh > reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/c_trace_${STAMP}.log
- PYTHONPATH=src python reports/2025-10-cli-flags/phase_k/base_lattice/trace_harness.py --out reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/trace_py_${STAMP}.log --dtype float64 --device cpu
- python reports/2025-10-cli-flags/phase_k/base_lattice/compare_traces.py --c reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/c_trace_${STAMP}.log --py reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/trace_py_${STAMP}.log > reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/trace_diff_${STAMP}.txt
- Update reports/2025-10-cli-flags/phase_k/base_lattice/summary.md and reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain.md with new metrics; append Attempt notes with artifact paths in docs/fix_plan.md.

Pitfalls To Avoid:
- Do not rerun the full pytest suite; stay on the targeted selector unless production code changes later demand broader coverage.
- Preserve Protected Assets (docs/index.md, loop.sh, supervisor.sh, input.md).
- Set KMP_DUPLICATE_LIB_OK=TRUE for every torch import; missing it can crash parity scripts.
- Avoid overwriting earlier artifacts; use STAMP=$(date +%Y%m%d%H%M%S) before running commands.
- Keep NB_C_BIN pointing to ./golden_suite_generator/nanoBragg so C traces use the instrumented binary.
- Maintain device/dtype neutrality in production code—no .cpu()/.cuda() edits while gathering evidence.
- Follow prompts/debug.md trace-first SOP if parity still fails; log divergences before editing code.
- Record any CUDA unavailability or deviations in docs/fix_plan.md attempts and the plan checklist.
- Double-check env NB_RUN_PARALLEL=1 whenever running parity tests; missing it invalidates results.
- Update Attempt history immediately after each major action to keep supervisor context accurate.

Pointers:
- plans/active/cli-noise-pix0/plan.md#L200
- docs/fix_plan.md#CLI-FLAGS-003-handle-nonoise-and-pix0_vector_mm
- reports/2025-10-cli-flags/phase_k/base_lattice/summary.md
- reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain.md
- specs/spec-a-cli.md
- docs/development/testing_strategy.md#tier-1-translation-correctness
- src/nanobrag_torch/models/crystal.py:650

Next Up: When K3g3 artifacts pass parity, proceed to the supervisor command replay (plan item L1) followed by the CLI regression sweep (tests/test_cli_flags.py tests/test_cli_scaling.py) before requesting closure.
