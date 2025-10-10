## Context
- Initiative: VECTOR-PARITY-001 — unblock long-term Goals 1 and 2 by restoring ≥0.999 correlation for the 4096² warm-run benchmark so vectorization profiling (VECTOR-GAPS-002) and performance recovery (PERF-PYTORCH-004) can resume.
- Plan Goal: Deliver a phase-ordered recovery track that keeps evidence refreshed, closes the remaining edge/background residual, and revalidates full-frame parity before profiling restarts.
- Dependencies:
  - specs/spec-a-core.md §§4–5 — authoritative sampling, source handling, and scaling equations.
  - arch.md §§2, 8, 15 — broadcast shapes, device/dtype discipline, differentiability guardrails.
  - docs/architecture/pytorch_design.md §1.1.4–§1.1.5 — vectorized oversample/normalization flows.
  - docs/development/testing_strategy.md §§1.4–2 — parity thresholds, benchmark selectors, reporting rules.
  - docs/development/pytorch_runtime_checklist.md — runtime guardrails (item 4: source weighting).
  - prompts/callchain.md — callchain evidence SOP for Phase E0 taps.
  - reports/benchmarks/20251009-161714/ — last known good 4096² benchmark (corr=0.999998).

### Status Snapshot (2026-01-10)
- Phases A–D ✅ complete; ROI parity restored (corr≈1.000000, |sum_ratio−1|≈1.3e-5) and instrumentation cleanup verified.
- Attempt #22 delivered Phase E0 callchain bundle (`reports/2026-01-vectorization-parity/phase_e0/20251010T092845Z/`) with high-confidence hypothesis: PyTorch multiplies the accumulated oversample sum by the last subpixel’s solid angle (`omega_last`), whereas C is suspected to average ω over all subpixels.
- Next immediate work: quantify ω asymmetry per pixel, confirm C semantics, and, if mismatch is proven, implement averaged ω handling prior to re-running the 4096² comparison.

### Phase A — Evidence Audit & Baseline Ledger
Goal: Canonicalise good vs bad benchmark evidence so every loop uses the same provenance.
Prereqs: Review `[VECTOR-PARITY-001]` Attempts #0–#2 and gather artifact paths.
Exit Criteria: Artifact matrix, parameter diff, and commands log archived under `reports/2026-01-vectorization-parity/phase_a/<STAMP>/` with ledger references.

| ID | Task Description | State | How/Why & Guidance (including command references) |
| --- | --- | --- | --- |
| A1 | Build artifact matrix for good vs bad benchmarks | [D] | Attempt #1 → `reports/2026-01-vectorization-parity/phase_a/20251010T023622Z/artifact_matrix.md`; contrasts good bundle `reports/benchmarks/20251009-161714/` vs failing runs. |
| A2 | Parameter diff + environment capture | [D] | Attempt #1 → `param_diff.md` + `commands.txt` capture CLI/env parity; verified against `docs/development/c_to_pytorch_config_map.md`. |
| A3 | Record open questions & ledger hooks | [D] | Attempt #1 annotated missing sum_ratio + git provenance; docs/fix_plan.md updated with Phase B focus. |

### Phase B — Reproduction Scope & Test Matrix
Goal: Confirm regression on HEAD, define authoritative reproduction commands, and bound the scope.
Prereqs: Phase A artifacts published; NB_C_BIN set; repo clean.
Exit Criteria: Fresh benchmark bundle, pytest scope log, and ROI sanity checks under `reports/2026-01-vectorization-parity/phase_b/<STAMP>/` with ledger updates.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Re-run 4096² benchmark on HEAD | [D] | Attempt #4 → `reports/2026-01-vectorization-parity/phase_b/20251010T030852Z/`; command in `summary.md` reproduces corr≈0.721 / sum_ratio≈225. |
| B2 | Capture AT parity selectors (collect-only) | [D] | Attempt #5 → `pytest_parallel.log`; confirm AT suite lacks active 4096² coverage so nb-compare remains canonical. |
| B3 | Decide working validation path | [D] | Attempt #6 & #7 selected nb-compare ROI workflow; ROI bundle `reports/2026-01-vectorization-parity/phase_b/20251010T035732Z/` meets corr≥0.999. |

### Phase C — Trace Divergence Analysis
Goal: Produce parallel C↔Py traces and isolate the first divergent variable.
Prereqs: Instrumented C binary; `scripts/debug_pixel_trace.py` ready for custom taps.
Exit Criteria: Trace bundles (C + PyTorch) for on-peak, edge, and background pixels plus `first_divergence.md` enumerating hypotheses.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Capture TRACE_C logs (3 ROI pixels) | [D] | Attempt #8 → `reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/`; pixels (2048,2048), (1792,2048), (4095,2048). |
| C2 | Capture TRACE_PY logs with matched schema | [D] | Attempt #9 → `reports/2026-01-vectorization-parity/phase_c/20251010T055346Z/`; upgraded trace script with CLI options. |
| C3 | First divergence narrative | [D] | Attempt #10 → `first_divergence.md`; identified unit errors in scattering_vec, fluence, F_latt. |

### Phase D — Physics Remediation & ROI Lockdown
Goal: Sequentially fix the three physics defects, re-establish ROI parity, and remove temporary instrumentation.
Prereqs: Phase C hypotheses validated; repo clean; tests green.
Exit Criteria: ROI nb-compare passes, instrumentation removed, ledger captures lessons learned.

| ID | Task Description | State | Guidance |
| --- | --- | --- | --- |
| D1 | Fix scattering_vec units | [D] | Attempt #11 → `reports/2026-01-vectorization-parity/phase_d/20251010T062949Z/`; simulator uses meters consistently. |
| D2 | Fix fluence parity in trace helper | [D] | Attempt #12 → `reports/2026-01-vectorization-parity/phase_d/20251010T070307Z/`; validated `BeamConfig.fluence` usage. |
| D3 | Align F_latt normalization | [D] | Attempt #13 → `reports/2026-01-vectorization-parity/phase_d/20251010T071935Z/`; trace helper reuses production sincg. |
| D4 | Lattice unit fix in simulator | [D] | Attempt #14 → `reports/2026-01-vectorization-parity/phase_d/20251010T073708Z/`; ensures h·S dimensionless. |
| D5 | ROI nb-compare verification | [D] | Attempt #15 → `reports/2026-01-vectorization-parity/phase_d/20251010T081642Z/`; corr≈1.0, sum_ratio≈0.99999. |
| D6 | Remove instrumentation & confirm stability | [D] | Attempt #16 → `reports/2026-01-vectorization-parity/phase_d/20251010T083319Z/`; pytest collect-only (695 tests) + ROI parity retained. |

### Phase E — Edge Residual Diagnosis (Active)
Goal: Explain the remaining 0.721 correlation on full-frame runs by quantifying edge/oversample behavior and aligning PyTorch with C semantics.
Prereqs: Phase D complete; regenerate golden data (Attempt #19) acknowledged; callchain SOP ready.
Exit Criteria: Numeric taps proving or refuting the omega-last-value hypothesis, remediation plan approved, and fix inputs staged for implementation.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E0a | Draft analysis question & callchain brief | [D] | Attempt #22 → `callchain_brief.md`; initiative `vectorization-parity-edge`. |
| E0b | Execute callchain + static map | [D] | Attempt #22 → `callchain/static.md`; entry→sink documented with file:line anchors. |
| E0c | Summarise findings & tap plan | [D] | Attempt #22 → `summary.md` & `trace/tap_points.md`; hypothesis: `omega_last` bias at edges. |
| E1 | Quantify PyTorch omega asymmetry | [ ] | Run `KMP_DUPLICATE_LIB_OK=TRUE NB_TRACE_EDGE_PIXEL="0,0" python scripts/debug_pixel_trace.py --pixel 0 0 --oversample 2 --out-dir reports/2026-01-vectorization-parity/phase_e0/<STAMP>/py_taps/`; compute `relative_asymmetry` for edge vs center pixel (store in `omega_analysis.md`). |
| E2 | Capture C omega taps for edge pixel | [ ] | Instrument `golden_suite_generator/nanoBragg` oversample loop (see `trace/tap_points.md` Tap 3); command template in `callchain/static.md`; archive under `reports/2026-01-vectorization-parity/phase_e0/<STAMP>/c_taps/`. |
| E3 | Compare C vs PyTorch omega handling | [ ] | Produce `omega_comparison.md` summarising whether C averages ω; include numeric table + decision. Block advancement if evidence inconclusive. |
| E4 | Update ledger & plan with outcomes | [ ] | Upon completing E1–E3, add Attempt #23 summary to `[VECTOR-PARITY-001]`, refresh this plan (mark E1–E3 states), and draft remediation decision tree before implementation begins. |

### Phase F — Remediation & Full-Frame Validation (Pending)
Goal: Implement the validated fix (likely ω averaging), re-run full-frame parity, and unblock downstream initiatives.
Prereqs: Phase E evidence confirms the defect + chosen remedy; implementation owner assigned (Ralph unless delegated).
Exit Criteria: corr≥0.999 and |sum_ratio−1|≤5×10⁻³ for full-frame nb-compare; 4096² benchmark log + pytest selector stored under `reports/2026-01-vectorization-parity/phase_f/<STAMP>/`; docs/tests updated with new guardrails.

| ID | Task Description | State | Guidance |
| --- | --- | --- | --- |
| F1 | Implement ω averaging (or alternative fix) in simulator | [ ] | Update `src/nanobrag_torch/simulator.py` oversample branch; include C-code reference snippet per Rule 11; guard with device/dtype neutrality. |
| F2 | Re-run full-frame benchmark + ROI nb-compare | [ ] | Use commands from Phase B/Bundles; store metrics in `phase_f_summary.md`; thresholds corr≥0.999, |sum_ratio−1|≤5e-3. |
| F3 | Refresh pytest evidence & documentation | [ ] | Run mapped selectors (high-res test, collect-only); update docs/fix_plan.md Attempts, `docs/architecture/pytorch_design.md` addendum if semantics change; ensure `plans/active/vectorization.md` gating lifted. |

## Exit Criteria for Plan Completion
- Phase E tasks E1–E4 complete with archived tap evidence and ledger updates.
- Phase F parity rerun succeeds; `[VECTOR-PARITY-001]` marked done and downstream plans (VECTOR-GAPS-002, VECTOR-TRICUBIC-002) formally unblocked.
- Documentation & guardrails updated to capture the oversample omega rule (spec references + checklist updates).
