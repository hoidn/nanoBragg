Summary: Capture full C/PyTorch traces for the supervisor command to localize beam-vector + pix0 divergence before touching implementation.
Phase: Evidence
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_e/c_trace_beam.log; reports/2025-10-cli-flags/phase_e/pytorch_trace_beam.log; reports/2025-10-cli-flags/phase_e/trace_diff_beam.txt; reports/2025-10-cli-flags/phase_e/trace_summary.md

Header:
- Timestamp: 2025-10-06T01:32:39Z
- Commit: ae11d23
- Author: galph
- Active Focus: CLI-FLAGS-003 Phase E — beam-vector + pix0 trace parity diagnostics

Do Now: [CLI-FLAGS-003] Phase E1/E2 trace capture — run NB_C_BIN=./golden_suite_generator/nanoBragg with -dump_pixel; diff with trace_harness.py output (see How-To Map).

If Blocked: If C trace command fails (e.g., missing NB_C_BIN or instrumentation), capture the exact stderr to reports/2025-10-cli-flags/phase_e/c_trace_failure.log, record the attempt in docs/fix_plan.md (Attempt #8), and fall back to verifying parser output only (beam_vector_check) until the binary is rebuilt.

Priorities & Rationale:
- docs/fix_plan.md:735-812 pinpoints unresolved geometry gaps (pix0 transform + ignored beam vector) blocking the supervisor parity goal; we must refresh trace evidence before implementing fixes.
- plans/active/cli-noise-pix0/plan.md Phase E tasks E0–E3 remain unchecked; completing them restores the diagnostic baseline needed for implementation.
- docs/debugging/debugging.md §Parallel Trace Comparison mandates trace-first workflow; skipping it risks reintroducing parity regressions.
- docs/development/c_to_pytorch_config_map.md §Detector Parameters clarifies CUSTOM convention expectations (beam + pix0 transforms), informing trace interpretation.
- reports/2025-10-cli-flags/phase_d/intensity_gap.md documents the intensity mismatch; fresh traces confirm whether beam-vector wiring explains the delta.

How-To Map:
1. `mkdir -p reports/2025-10-cli-flags/phase_e`
2. Ensure C binary is built with tracing: `timeout 120 make -C golden_suite_generator` (only if nanoBragg changed since last build).
3. Run C trace (target pixel 1039 685) capturing full stdout/stderr:
   ```bash
   NB_C_BIN=./golden_suite_generator/nanoBragg \
   timeout 180 "$NB_C_BIN" -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate \
     -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 \
     -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 \
     -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 \
     -odet_vector -0.000088 0.004914 -0.999988 \
     -sdet_vector -0.005998 -0.999970 -0.004913 \
     -fdet_vector 0.999982 -0.005998 -0.000118 \
     -pix0_vector_mm -216.336293 215.205512 -230.200866 \
     -beam_vector 0.00051387949 0.0 -0.99999986 \
     -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 \
     -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 \
     -dump_pixel 1039 685 2>&1 | tee reports/2025-10-cli-flags/phase_e/c_trace_beam.log
   ```
4. Generate PyTorch trace using the harness (stdout includes TRACE_PY lines):
   ```bash
   KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_e/trace_harness.py \
     2>&1 | tee reports/2025-10-cli-flags/phase_e/pytorch_trace_beam.log
   ```
5. Diff the two traces (filtering prefixes for clarity) and save summary:
   ```bash
   paste \
     <(grep '^TRACE_C' reports/2025-10-cli-flags/phase_e/c_trace_beam.log) \
     <(grep '^TRACE_PY' reports/2025-10-cli-flags/phase_e/pytorch_trace_beam.log) \
     > reports/2025-10-cli-flags/phase_e/trace_side_by_side.tsv
   diff -u \
     <(grep '^TRACE_C' reports/2025-10-cli-flags/phase_e/c_trace_beam.log) \
     <(grep '^TRACE_PY' reports/2025-10-cli-flags/phase_e/pytorch_trace_beam.log | sed 's/TRACE_PY:/TRACE_C:/') \
     > reports/2025-10-cli-flags/phase_e/trace_diff_beam.txt
   ```
6. Summarize the first divergence (variable name, C value, PyTorch value, hypothesised cause) in `reports/2025-10-cli-flags/phase_e/trace_summary.md` and log Attempt #8 in docs/fix_plan.md with artifact paths.

Pitfalls To Avoid:
- Do not modify Python or C sources yet; this loop is evidence-only.
- Keep `scaled.hkl.1` untouched now but plan to delete it later—avoid creating additional duplicates.
- Ensure `NB_C_BIN` points to the instrumented binary under `golden_suite_generator`; the frozen root binary lacks tracing.
- Retain `KMP_DUPLICATE_LIB_OK=TRUE` for all PyTorch commands to prevent MKL crashes.
- Avoid `.item()`/`.cpu()` when post-processing tensors in ad-hoc scripts.
- Preserve CUSTOM vector normalization; do not renormalize within the harness.
- Do not run pytest or other suites in this evidence pass.
- Capture command outputs verbatim—no manual reformatting of TRACE lines.
- Confirm directories exist before writing artifacts to keep plan cross-references valid.
- Leave `input.md` unchanged after reading; edits are supervisor-only.

Pointers:
- docs/fix_plan.md:735-812 (CLI-FLAGS-003 status & attempts)
- plans/active/cli-noise-pix0/plan.md (Phase E tasks E0–E3 guidance)
- docs/debugging/debugging.md:1-120 (parallel trace process)
- docs/development/c_to_pytorch_config_map.md:40-140 (detector parameter parity)
- reports/2025-10-cli-flags/phase_d/intensity_gap.md (prior intensity analysis context)
- reports/2025-10-cli-flags/phase_e/instrumentation_notes.md (C trace instructions)
- reports/2025-10-cli-flags/phase_e/pytorch_instrumentation_notes.md (PyTorch harness checklist)

Next Up: If traces align and beam vector remains divergent, proceed to plan Phase E3 analysis followed by implementation sketching for beam/pix0 fixes.
