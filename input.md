Summary: Pin down the pix0 divergence by adding matched C/Py instrumentation before resuming normalization work.
Phase: Evidence
Focus: CLI-FLAGS-003 Phase H6 — Pix0 Divergence Isolation
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0.log
Artifacts: reports/2025-10-cli-flags/phase_h6/py_trace/trace_py_pix0.log
Artifacts: reports/2025-10-cli-flags/phase_h6/analysis.md
Do Now: CLI-FLAGS-003 Phase H6a — capture C pix0 trace; run `NB_C_BIN=./golden_suite_generator/nanoBragg ./golden_suite_generator/nanoBragg -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 2>&1 | tee reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0.log`
If Blocked: Capture stderr/stdout to `reports/2025-10-cli-flags/phase_h6/attempt_log.md`, note the failing step (instrumentation, build, or run), and halt for supervisor guidance.

Instrumentation Checklist:
- Add `TRACE_C:` lines near pix0 math in `golden_suite_generator/nanoBragg.c` (beam center parsing, Fbeam/Sbeam, r_factor, close_distance, pix0 components).
- Touch `reports/2025-10-cli-flags/phase_h/trace_harness.py` only through hooks; avoid embedding business logic in the script body.
- Keep trace variable names identical between C and PyTorch (`TRACE_C: Fbeam_mm`, `TRACE_PY: Fbeam_mm`, etc.).
- Record git hashes (`git rev-parse HEAD`, `git -C golden_suite_generator rev-parse HEAD`) inside each trace README.
- Store environment snapshot with `env | sort > .../env_snapshot.txt` to replicate runs later.
- Use `shasum -a 256` for each log and include the checksum inside the README.
- After instrumentation, rebuild C binary via `make -C golden_suite_generator` and note compiler flags.
- Preserve existing trace harness CLI; add new options only if strictly necessary and document them in the README.
- Ensure all new directories live under `reports/2025-10-cli-flags/phase_h6/` to keep provenance tidy.
- Update docs/fix_plan.md Attempt #36 immediately after capturing both traces.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:134-153 documents Phase H6 tasks required before K2 resumes.
- docs/fix_plan.md:455-484 now mandates H6 instrumentation and a fresh Attempt #36 log before normalization.
- docs/architecture/detector.md:35-82 contains the canonical BEAM pivot pix0 formula we must validate line-by-line.
- specs/spec-a-cli.md:120-152 reiterates CUSTOM convention precedence and pivot side-effects relevant to pix0 overrides.

How-To Map:
- Step 1: Apply C instrumentation (H6a) — insert `TRACE_C` outputs around `pix0_vector` calculation, rebuild with `make -C golden_suite_generator -j8`, and document changes in `c_trace/README.md`.
- Step 2: Run the Do Now command, tee stdout, and clip the `TRACE_C` lines into `c_trace/trace_c_pix0.log`; append `git status --short` results to the README.
- Step 3: Extend the PyTorch trace harness (H6b) to emit mirrored variables from `_calculate_pix0_vector()`; route output to `phase_h6/py_trace/trace_py_pix0.log` plus a matching README and env snapshot.
- Step 4: Diff the traces (H6c) using `diff -u` or a notebook; summarize the first mismatch (units + magnitude) in `phase_h6/analysis.md` with direct line citations to both logs.
- Step 5: Update `reports/2025-10-cli-flags/phase_h5/parity_summary.md` with a new section “Attempt #36 (Phase H6 diagnostics)” showing Δpix0/ΔFbeam/ΔSbeam values and the identified divergence.
- Step 6: Edit docs/fix_plan.md Attempt history for CLI-FLAGS-003 with Attempt #36, referencing all new artifacts and proposed fix.
- Step 7: Stage only reports/docs plus temporary instrumentation patches; if `nanoBragg.c` must stay instrumented for multiple loops, document the intent in Attempt history.

Pitfalls To Avoid:
- Do not alter production simulator logic while instrumenting; confine changes to trace hooks and guard with `#ifdef TRACE_PIX0` if necessary.
- Avoid rerunning pytest or nb-compare; Evidence phase forbids tests.
- Keep Protected Assets untouched (docs/index.md, loop.sh, supervisor.sh, input.md).
- Ensure C trace uses meters for pix0 components; note any mm intermediate conversions explicitly.
- Prevent CLIs from emitting ANSI colour codes—use plain text for diffability.
- Do not delete prior H5 assets; they remain the baseline comparator.
- Revert instrumentation diffs after logs are captured unless further loops require them (capture rationale in Attempt #36).
- Maintain device/dtype neutrality in PyTorch trace — no forced `.cpu()` or `.double()` just for logging.
- Respect two-message loop policy: avoid triggering additional automation tracks.
- Keep git history linear; avoid merge commits while instrumentation is in flight.

Pointers:
- plans/active/cli-noise-pix0/plan.md:120-167
- docs/fix_plan.md:448-530
- docs/architecture/detector.md:35-112
- docs/development/c_to_pytorch_config_map.md:60-110
- docs/debugging/debugging.md:20-88

Telemetry Targets:
- Record harness runtime and CPU info in each README.
- Log the executed Do Now command verbatim for reproducibility.
- Archive raw `TRACE_C/PY` snippets inside analysis.md for quick reference.
- Tag Attempt #36 with `Phase H6` in docs/fix_plan.md to keep history searchable.
- Catalog any instrumentation flags (e.g., `TRACE_PIX0=1`) used during builds.

Next Up: Once pix0 parity (<5e-5 m) is proven, transition to Phase H5c closure followed by Phase K2 scaling-chain refresh.
