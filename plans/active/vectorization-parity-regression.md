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
- Attempt #22 delivered Phase E0 callchain bundle (`reports/2026-01-vectorization-parity/phase_e0/20251010T092845Z/`) identifying last-value ω weighting as the top hypothesis.
- Attempt #23 quantified PyTorch ω bias at oversample=2 (edge last/mean≈1.000028), showing the effect is ≈0.003 % and insufficient to explain the 0.721 correlation — re-prioritise C taps and alternate hypotheses (F_cell defaults, water background) before code changes.
- Attempt #24 captured C omega taps (edge + centre) and produced `omega_comparison.md`, definitively refuting the omega hypothesis; next probes moved to Tap 4 (F_cell defaults) and Tap 6 (water background scaling).
- Attempt #25 recorded PyTorch Tap 4 metrics (`reports/2026-01-vectorization-parity/phase_e0/20251010T102752Z/`), confirming default_F usage at both edge and centre pixels (out_of_bounds=0).
- Attempt #27 mirrored Tap 4 on the C side (`reports/2026-01-vectorization-parity/phase_e0/20251010T103811Z/`) and uncovered a mismatch; Attempt #28 (20251010T105617Z) consolidated the PyTorch/C metrics, audited fallback logic, and refuted the default_F hypothesis. Phase E now pivots to Tap 5 `intensity_pre_norm` before considering Tap 6 water background or Phase F remediation.
- Attempt #30 (20251010T112334Z) completed the C Tap 5 capture: `I_before_scaling` differs by ~4× relative to PyTorch for the edge pixel while centre values agree (both zero). ω, capture, polar, and step counts match, so the discrepancy now isolates to how raw intensity is accumulated inside the C oversample loop.
- Attempt #31 (20251010T113608Z) merged Tap 5 metrics into `intensity_pre_norm.md` and ranked hypotheses in `tap5_hypotheses.md`, flagging the centre-pixel HKL `(0,0,0)` behaviour for validation. Attempts #32/#33 (20251010T115342Z / 20251010T120355Z) completed the PyTorch Tap 5.1 per-subpixel HKL audit: all subpixels report `out_of_bounds=False` with `F_cell=default_F`, refuting the HKL indexing hypothesis and pushing Phase E toward the C mirror + bounds parity tasks.
- Attempt #34 (20251010T121436Z) mirrored Tap 5.1 on the C side: edge pixel rounds to (-8,39,-39), centre to (0,0,0), both with `F_cell=default_F` and `out_of_bounds=0`; HKL indexing parity is now confirmed on both implementations, leaving HKL bounds (Tap 5.2) and oversample accumulation as the remaining probes before remediation.

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
Exit Criteria: Numeric taps proving or refuting the omega-last-value hypothesis (or successor hypothesis), remediation plan approved, and fix inputs staged for implementation.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E0a | Draft analysis question & callchain brief | [D] | Attempt #22 → `callchain_brief.md`; initiative `vectorization-parity-edge`. |
| E0b | Execute callchain + static map | [D] | Attempt #22 → `callchain/static.md`; entry→sink documented with file:line anchors. |
| E0c | Summarise findings & tap plan | [D] | Attempt #22 → `summary.md` & `trace/tap_points.md`; hypothesis: `omega_last` bias at edges. |
| E1 | Quantify PyTorch omega asymmetry | [D] | ✅ Attempt #23 (20251010T095445Z): measured `last_over_mean≈1.000028` (≈0.003 % bias) for edge pixel (0,0) vs ≈0 for center (2048,2048). Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T095445Z/{py_taps/omega_metrics.json,omega_analysis.md}`. Conclusion: last-value ω weighting is negligible at oversample=2 → pursue alternate hypotheses (C taps or F_cell/background). |
| E2 | Capture C omega taps for edge pixel | [D] | Attempt #24 (20251010T100102Z) instrumented `golden_suite_generator/nanoBragg.c:2976-2985` to log all four subpixels for pixels (0,0) and (2048,2048). Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T100102Z/c_taps/`. Result: C reuses the first subpixel's omega → identical values, no edge bias. |
| E3 | Compare C vs PyTorch omega handling | [D] | `omega_comparison.md` (Attempt #24) quantifies both runs and refutes the omega hypothesis (≤0.003 % delta). Decision: escalate Tap 4 (F_cell defaults) and Tap 6 (water background) before revisiting physics changes. |
| E4 | Update ledger & plan with outcomes | [D] | ✅ This loop — Attempt #24 recorded in `[VECTOR-PARITY-001]`; plan + ledger refreshed with Tap 4 focus and new Next Actions (E5–E7). |
| E5 | PyTorch Tap 4 — F_cell lookup stats | [D] | Attempt #25 (20251010T102752Z) captured edge/centre JSON + summary (`f_cell_summary.md`). Result: both pixels use default_F uniformly (out_of_bounds=0). Artifacts stored under `py_taps/`; env + commands logged. |
| E6 | C Tap 4 — HKL default usage | [D] | Attempt #27 (20251010T103811Z) instrumented `golden_suite_generator/nanoBragg.c:3337-3354` and captured `tap4_metrics.json`. Edge pixel matches PyTorch (default_F=100); centre pixel retrieves in-bounds HKL values of 0.0 (no default fallback). Clean rebuild verified (692 tests). |
| E7 | Compare F_cell distributions & decide next probe | [D] | Attempt #28 (20251010T105617Z) merged Tap 4 metrics into `f_cell_comparison.md`, audited fallback paths, and concluded default_F semantics align; default_F hypothesis closed, proceed to Tap 5. |
| E8 | PyTorch Tap 5 — intensity pre-normalisation | [D] | Attempt #29 (20251010T110735Z) extended `scripts/debug_pixel_trace.py` with `--taps intensity`, captured edge (0,0) & centre (2048,2048) JSON metrics. Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T110735Z/py_taps/{pixel_0_0_intensity_pre_norm.json, pixel_2048_2048_intensity_pre_norm.json, intensity_pre_norm_summary.md}`. Key findings: both pixels accumulate correctly pre-scaling (edge: I_before_scaling=3.54e4, normalized=7.54e-5; centre: I_before_scaling=1.54e8, normalized=0.385); steps=4 (oversample²), omega variation ≈1.13×, polar variation ≈1.04×. No anomalies detected in PyTorch pre-normalization path → proceed to C Tap 5 (E9). |
| E9 | C Tap 5 — intensity pre-normalisation | [D] | Attempt #30 (20251010T112334Z) added `TRACE_C_TAP5` guards (lines 3397-3410) to record `I_before_scaling`, `steps`, `omega_pixel`, `capture_fraction`, `polar`, and `I_pixel_final` for pixels (0,0) & (2048,2048). Edge pixel reports `I_before_scaling=1.4152e5` (≈4× PyTorch), centre pixel remains 0.0. ω, capture, polar, and steps all match Attempt #29. Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T112334Z/{c_taps/,comparison/intensity_pre_norm_c_notes.md,env/trace_env.json,PHASE_E9_SUMMARY.md}`. |
| E10 | Compare Tap 5 outputs & quantify delta | [D] | Attempt #31 → `reports/2026-01-vectorization-parity/phase_e0/20251010T113608Z/comparison/intensity_pre_norm.md` documents the 4× edge delta and centre-pixel HKL fallback, isolating `I_before_scaling` as the divergent factor (referencing `specs/spec-a-core.md:232-259`). |
| E11 | Rank next hypotheses & instrumentation gate | [D] | Attempt #31 → `tap5_hypotheses.md` ranks H1–H3 and recommends Tap 5.1 (per-subpixel HKL audit) + Tap 5.2 (grid bounds check) before touching production code. |
| E12 | PyTorch Tap 5.1 — per-subpixel HKL audit | [D] | Attempts #32/#33 → `reports/2026-01-vectorization-parity/phase_e0/20251010T115342Z/` and `20251010T120355Z/`; `scripts/debug_pixel_trace.py --taps hkl_subpixel` logs fractional HKL, rounded `(h0,k0,l0)`, `F_cell`, and `out_of_bounds` for pixels (2048,2048) & (0,0). Confirms all subpixels stay in-bounds and return `default_F` when no HKL file is loaded (`specs/spec-a-core.md:232-240`). |
| E13 | C Tap 5.1 — mirror HKL audit | [D] | Attempt #34 → `reports/2026-01-vectorization-parity/phase_e0/20251010T121436Z/c_taps/` confirms edge (0,0) → (-8,39,-39) and centre (2048,2048) → (0,0,0) with `F_cell=default_F`, `out_of_bounds=0`; HKL indexing parity achieved. |
| E14 | Tap 5.2 — HKL grid bounds parity | [ ] | Capture `TRACE_PY_HKL_BOUNDS` and `TRACE_C_HKL_BOUNDS` showing `[h_min,h_max]`, `[k_min,k_max]`, `[l_min,l_max]` for the loaded HKL grid to prove `(0,0,0)` is in range. Summarise in `tap5_hkl_bounds.md` and update plan/ledger with acceptance (bounds must match exactly). |
| E15 | Tap 5.3 — oversample accumulation instrumentation | [ ] | Draft instrumentation brief for logging per-subpixel `F_cell²·F_latt²` contributions and oversample ordering (C + PyTorch). Store plan under `reports/2026-01-vectorization-parity/phase_e0/<STAMP>/tap5_accum_plan.md` before implementation. |

### Phase F — Remediation & Full-Frame Validation (Pending)
Goal: Implement the validated fix (likely ω averaging), re-run full-frame parity, and unblock downstream initiatives.
Prereqs: Phase E evidence confirms the defect + chosen remedy; implementation owner assigned (Ralph unless delegated).
Exit Criteria: corr≥0.999 and |sum_ratio−1|≤5×10⁻³ for full-frame nb-compare; 4096² benchmark log + pytest selector stored under `reports/2026-01-vectorization-parity/phase_f/<STAMP>/`; docs/tests updated with new guardrails.

| ID | Task Description | State | Guidance |
| --- | --- | --- | --- |
| F1 | Implement validated Tap 5 remediation in simulator | [ ] | Apply the fix identified in Phase E (e.g., oversample accumulation, background scaling). Update `src/nanobrag_torch/simulator.py` with C-code reference snippet per Rule 11; maintain device/dtype neutrality. |
| F2 | Re-run full-frame benchmark + ROI nb-compare | [ ] | Use commands from Phase B bundles; store metrics in `phase_f_summary.md`; thresholds corr≥0.999, |sum_ratio−1|≤5e-3. |
| F3 | Refresh pytest evidence & documentation | [ ] | Run mapped selectors (high-res test, collect-only); update docs/fix_plan.md Attempts, `docs/architecture/pytorch_design.md` addendum if semantics change; ensure `plans/active/vectorization.md` gating lifted. |

## Exit Criteria for Plan Completion
- Phase E tasks E1–E14 complete with archived tap evidence and ledger updates confirming HKL indexing parity.
- Phase F parity rerun succeeds; `[VECTOR-PARITY-001]` marked done and downstream plans (VECTOR-GAPS-002, VECTOR-TRICUBIC-002) formally unblocked.
- Documentation & guardrails updated to capture the oversample omega rule (spec references + checklist updates).
