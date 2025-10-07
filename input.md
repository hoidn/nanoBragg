Summary: Capture aligned nanoBragg C and PyTorch MOSFLM traces so we can pinpoint the real-space lattice drift before modifying simulator code.
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/c_trace_mosflm.log
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/c_trace_mosflm.sha256
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/py_raw_vectors.json
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/py_tensor_vectors.json
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_diff.md
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/attempt_notes.md
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/collect_only.log
Do Now: CLI-FLAGS-003 Phase L3i.a instrumentation — rebuild `golden_suite_generator/nanoBragg` with detailed `TRACE_C` taps around the MOSFLM pipeline and run `NB_C_BIN=./golden_suite_generator/nanoBragg "$NB_C_BIN" -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 > reports/2025-10-cli-flags/phase_l/rot_vector/c_trace_mosflm.log 2>&1`
If Blocked: If the C build or trace command fails, capture stdout/stderr under `reports/2025-10-cli-flags/phase_l/rot_vector/attempt_log.txt`, revert instrumentation, and log the failure (command, exit code, artifact path) as a new CLI-FLAGS-003 Attempt before moving on.
Priorities & Rationale:
- `plans/active/cli-noise-pix0/plan.md:147` shows Phase L3i/L3j blocking the supervisor parity rerun; instrumentation is the first checkbox.
- `reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_correction.md:1` documents the suspected transpose/rescale bug and explicitly calls for the diff you’ll capture.
- `docs/fix_plan.md:462` now lists instrumentation and the Py diff as top priorities; completing them keeps fix_plan credible.
- `specs/spec-a-cli.md:63` nails the MOSFLM convention (beam along +X, +0.5 pixel offset) you must preserve when validating trace output.
- `docs/architecture/detector.md:56` provides the BEAM pivot formula so you can sanity-check `pix0` lines in the new trace.
- `docs/development/c_to_pytorch_config_map.md:29` reminds us how CLI flags map to config fields; ensures both traces share configuration parity.
- `reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:265` already exposes the mismatched real vectors; a refreshed log with richer taps lets us explain the difference.
- `reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md:1` maintains hypothesis history; update it after the diff to keep context in sync.
- `arch.md:189` reinforces the misset pipeline (reciprocal → real → reciprocal); your logs should confirm each stage stays intact.
How-To Map:
- Step 0 — Baseline checks:
  - `git status --short` (note any pre-existing dirt in `attempt_notes.md`).
  - `export KMP_DUPLICATE_LIB_OK=TRUE`
  - `export NB_C_BIN=./golden_suite_generator/nanoBragg`
  - `export PYTHONPATH=src`
  - Record the git SHA via `git rev-parse HEAD >> reports/2025-10-cli-flags/phase_l/rot_vector/attempt_notes.md`.
- Step 1 — Instrument nanoBragg.c:
  - Add `TRACE_C` logs after raw matrix read (`golden_suite_generator/nanoBragg.c:2054`), after wavelength scaling, and after misset rotation.
  - Inject logs for each cross product and for `V_star`/`V_cell` computations (`golden_suite_generator/nanoBragg.c:2121-2153`).
  - Append logs for the scaled real vectors and regenerated reciprocals (`golden_suite_generator/nanoBragg.c:2162-2185`).
  - Keep new logs grouped and comment the block with `/* Phase L3i instrumentation */` for reviewers.
- Step 2 — Rebuild and verify the binary:
  - `make -C golden_suite_generator`
  - `ls -lh golden_suite_generator/nanoBragg`
  - `grep -n "TRACE_C:" golden_suite_generator/nanoBragg.c`
  - Note the rebuild completion time in `attempt_notes.md`.
- Step 3 — Capture the C trace:
  - Run the full supervisor command using the instrumented binary (command in Do Now).
  - `sha256sum reports/2025-10-cli-flags/phase_l/rot_vector/c_trace_mosflm.log > reports/2025-10-cli-flags/phase_l/rot_vector/c_trace_mosflm.sha256`
  - `tail -n 40 reports/2025-10-cli-flags/phase_l/rot_vector/c_trace_mosflm.log` (confirm new logs exist).
  - Record runtime duration in `attempt_notes.md` for reproducibility.
- Step 4 — Extend the Py harness:
  - In `reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py:39`, dump the raw numpy `a_star/b_star/c_star` arrays (with wavelength and scaling factor) to `py_raw_vectors.json`.
  - Capture tensor equivalents immediately before the cross products and after real-vector reconstruction in `py_tensor_vectors.json`.
  - Write helper functions inside the harness to keep logging tidy (e.g., `_serialize_vector(name, tensor)`).
- Step 5 — Run the Py harness with float64 CPU:
  - `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --pixel 685 1039 --config supervisor --device cpu --dtype float64`
  - `python -m json.tool reports/2025-10-cli-flags/phase_l/rot_vector/py_raw_vectors.json > /dev/null`
  - `python -m json.tool reports/2025-10-cli-flags/phase_l/rot_vector/py_tensor_vectors.json > /dev/null`
  - Add a short summary of key numbers (a few vector components) to `attempt_notes.md` for quick reference.
- Step 6 — Build the diff memo:
  - Compare C and Py values stage by stage; emphasise the first divergence (expect `b` Y component).
  - Document findings in `reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_diff.md` (include tables + commentary).
  - Update `reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md` with a concise hypothesis update referencing the diff.
- Step 7 — Guard-rail commands:
  - `pytest --collect-only -q | tee reports/2025-10-cli-flags/phase_l/rot_vector/collect_only.log`
  - Record the exit code in `attempt_notes.md`.
- Step 8 — Fix-plan updates:
  - Add a new CLI-FLAGS-003 Attempt in `docs/fix_plan.md` summarising artifacts, first divergence, and next recommended actions.
  - Confirm `plans/active/cli-noise-pix0/plan.md` shows L3i as `[D]` and note any prerequisites for L3j.
- Step 9 — Optional sanity passes:
  - `sed -n '260,320p reports/2025-10-cli-flags/phase_l/rot_vector/c_trace_mosflm.log'` (verify k_frac lines).
  - `sed -n '12,40p reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_rot_vector.log'` (cross-check Py outputs).
  - `diff -u reports/2025-10-cli-flags/phase_l/rot_vector/c_trace_mosflm.log reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log | head` (spot-check instrumentation vs legacy trace).
Pitfalls To Avoid:
- Do not delete existing `TRACE_C` lines; append new logs to keep diffs reviewable.
- Keep harness updates local to the script; production modules should remain untouched this loop.
- Ensure all dumps include device and dtype metadata to aid future GPU validation.
- Rebuild the C binary after every instrumentation tweak; stale binaries produce misleading logs.
- Run the Py harness with float64 CPU to minimise precision drift during comparison.
- Respect the Protected Assets list in `docs/index.md`; avoid moving or deleting listed files.
- Store every artifact under `reports/2025-10-cli-flags/phase_l/rot_vector/` with descriptive filenames.
- Document environment variables and command timings in `attempt_notes.md` for reproducibility.
- Skip full pytest runs; `--collect-only` is mandatory in evidence mode.
- Stage intentional changes before finishing; highlight any intentional dirt in your handoff note.
- Avoid mixing tabs and spaces in the new C logs; stick to existing formatting for consistency.
- Document any TODOs left in code comments so reviewers know they are intentional.
- Back up the original nanoBragg.c snippet before instrumentation in case you need to revert quickly.
Pointers:
- `plans/active/cli-noise-pix0/plan.md:147` — Phase L3i/L3j checklist.
- `reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_correction.md:1` — corrective strategy memo.
- `golden_suite_generator/nanoBragg.c:2054` — MOSFLM matrix load/scaling block.
- `golden_suite_generator/nanoBragg.c:2121` — cross-product and real-vector reconstruction section.
- `src/nanobrag_torch/models/crystal.py:568` — PyTorch MOSFLM branch (reference only).
- `reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py:39` — harness entry point for new dumps.
- `reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:265` — legacy C trace highlighting the drift.
- `reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md:1` — hypothesis tracker to update.
- `docs/development/c_to_pytorch_config_map.md:29` — parity guardrails for CLI flags.
- `specs/spec-a-cli.md:63` — MOSFLM acceptance tests.
- `docs/architecture/detector.md:56` — BEAM pivot formula reference.
- `arch.md:189` — misset pipeline reminder.
- `docs/debugging/debugging.md:18` — Parallel trace SOP (useful checklist while diffing).
- `reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_probe.md:1` — Prior MOSFLM probe outputs for context.
- `reports/2025-10-cli-flags/phase_l/rot_vector/spindle_audit.log:1` — Confirms spindle normalization is ruled out.
Next Up: (1) Author `reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md` with verification thresholds so the implementation loop can proceed safely; (2) Once the checklist exists, execute the simulator fix and rerun nb-compare per Phase L4.
