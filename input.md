Summary: Capture C vs PyTorch scaling diagnostics for the supervisor command before touching simulator code. Establish the first mismatched factor in the normalization chain so we can plan fixes confidently.
Phase: Evidence
Focus: [CLI-FLAGS-003] Phase J — Intensity Scaling Evidence
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts:
- reports/2025-10-cli-flags/phase_j/trace_c_scaling.log
- reports/2025-10-cli-flags/phase_j/trace_py_scaling.log
- reports/2025-10-cli-flags/phase_j/scaling_chain.md
- reports/2025-10-cli-flags/phase_j/analyze_scaling.py
- reports/2025-10-cli-flags/phase_j/attempted_scaling_notes.md (only if fallback path required)
Do Now: CLI-FLAGS-003 Phase J1 — extend the existing trace harness to emit the full normalization chain, then run the C and PyTorch scaling traces for pixel (slow=1039, fast=685) and stash the raw logs in phase_j before editing any simulator code or tests.
If Blocked: If the harness update fails, fall back to logging `steps`, `omega`, `r_e^2`, and `fluence` via `scripts/debug_pixel_trace.py` for the same pixel, capture everything under `reports/2025-10-cli-flags/phase_j/attempted_scaling_notes.md`, and ping me before attempting another change.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:6 — The 1.24538e5× scaling miss is now the top blocker for Goal #1; Phase J must happen before any fixes land.
- plans/active/cli-noise-pix0/plan.md:122 — Tasks J1–J3 detail the evidence package (C/Py logs, ratio analysis, fix_plan update) required to unblock normalization work.
- docs/fix_plan.md:448 — Next actions explicitly command us to deliver Phase J artifacts and log Attempt #28 before touching implementation; ignoring this would desync the living plan.
- specs/spec-a-core.md:446 — Normative definition of the intensity accumulator clarifies the order of ω, r_e², and fluence multipliers we have to match.
- docs/development/testing_strategy.md:51 — Parallel trace-driven validation is the mandated debugging workflow; our harness updates must satisfy it.
- src/nanobrag_torch/simulator.py:904 — Current normalization divides by `steps` and applies ω; the trace needs to confirm whether this matches C step-for-step.

How-To Map:
- Step 1 — Prepare output directory: `mkdir -p reports/2025-10-cli-flags/phase_j`
- Step 2 — Run the canonical C trace with scaling focus:
  ```bash
  export NB_C_BIN=./golden_suite_generator/nanoBragg
  $NB_C_BIN \
    -mat A.mat \
    -floatfile img.bin \
    -hkl scaled.hkl \
    -nonoise \
    -nointerpolate \
    -oversample 1 \
    -exposure 1 \
    -flux 1e18 \
    -beamsize 1.0 \
    -spindle_axis -1 0 0 \
    -Xbeam 217.742295 \
    -Ybeam 213.907080 \
    -distance 231.274660 \
    -lambda 0.976800 \
    -pixel 0.172 \
    -detpixels_x 2463 \
    -detpixels_y 2527 \
    -odet_vector -0.000088 0.004914 -0.999988 \
    -sdet_vector -0.005998 -0.999970 -0.004913 \
    -fdet_vector 0.999982 -0.005998 -0.000118 \
    -pix0_vector_mm -216.336293 215.205512 -230.200866 \
    -beam_vector 0.00051387949 0.0 -0.99999986 \
    -Na 36 \
    -Nb 47 \
    -Nc 29 \
    -osc 0.1 \
    -phi 0 \
    -phisteps 10 \
    -detector_rotx 0 \
    -detector_roty 0 \
    -detector_rotz 0 \
    -twotheta 0 \
    -dump_pixel 1039 685 \
    > reports/2025-10-cli-flags/phase_j/trace_c_scaling.log
  ```
- Step 3 — Update `reports/2025-10-cli-flags/phase_e/trace_harness.py` so it prints `steps`, `I_before_scaling`, `omega`, `polarization`, `r_e_squared`, `fluence`, and the intermediate intensities. Keep the instrumentation rule: reuse production helpers, no re-derived physics.
- Step 4 — Run the PyTorch harness with the same pixel and write the log:
  ```bash
  KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src \
    python reports/2025-10-cli-flags/phase_e/trace_harness.py \
    --pixel-slow 1039 \
    --pixel-fast 685 \
    --emit-scaling \
    > reports/2025-10-cli-flags/phase_j/trace_py_scaling.log
  ```
- Step 5 — Build the ratio table and Markdown summary:
  ```bash
  KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src \
    python reports/2025-10-cli-flags/phase_j/analyze_scaling.py \
    --c-log reports/2025-10-cli-flags/phase_j/trace_c_scaling.log \
    --py-log reports/2025-10-cli-flags/phase_j/trace_py_scaling.log \
    --out reports/2025-10-cli-flags/phase_j/scaling_chain.md
  ```
- Step 6 — Append the key deltas and artifact list to docs/fix_plan.md Attempt #28 once the analysis is ready (do not change simulator code in this loop).

Pitfalls To Avoid:
- Do not modify `src/nanobrag_torch/simulator.py` yet; Evidence loop ends before implementation.
- Skip pytest and nb-compare entirely; running tests violates the Evidence phase gate.
- Always set `KMP_DUPLICATE_LIB_OK=TRUE` before importing torch to avoid MKL crashes.
- Keep the supervisor command arguments identical between C and PyTorch runs; even tiny deviations invalidate parity.
- Do not overwrite Phase H/I logs — store new assets under `phase_j/` only.
- Avoid `.cpu()`, `.cuda()`, or `.item()` on tensors that might become differentiable; the harness should remain device-neutral.
- Respect the instrumentation rule: reuse production helpers, no ad-hoc recomputation of physics constants.
- Do not delete or rename any files referenced in `docs/index.md`; Protected Assets rule still applies.
- Record every command (success or failure) in the scaling Markdown so Attempt #28 has a complete audit trail.
- Remember this is a single loop — no branching into Phase K tasks until the evidence is logged and acknowledged.

Pointers:
- plans/active/cli-noise-pix0/plan.md:122 — Full Phase J checklist and exit criteria.
- docs/fix_plan.md:448 — Next actions bound to Phase J artifacts (Attempt #28 expectations).
- reports/2025-10-cli-flags/phase_i/supervisor_command/README.md:1 — Baseline parity failure metrics (sum_ratio 124,538×) we are explaining.
- src/nanobrag_torch/simulator.py:904 — Present normalization path to compare against trace findings later.
- specs/spec-a-core.md:446 — Normative description of `I` and scaling factors to keep in mind while instrumenting.

Next Up: After Phase J artifacts are captured and Attempt #28 is logged, the following loop should tackle Phase K1 (implement the normalization fix using the new evidence) on a fresh pass.
