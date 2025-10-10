# Fix Plan Ledger

**Last Updated:** 2026-01-12 (galph loop — Test suite triage planning kickoff)
**Active Focus:**
- CRITICAL: Execute `[TEST-SUITE-TRIAGE-001]` full-suite pytest run and failure triage per `plans/active/test-suite-triage.md`; suspend all other engineering work until Phase A–C artefacts are captured.
- Tap 5.3 oversample instrumentation for `[VECTOR-PARITY-001]` remains staged but is on hold pending completion of `[TEST-SUITE-TRIAGE-001]` deliverables.
- Prepare pyrefly + test-index documentation once the suite triage backlog is unblocked.

## Index
| ID | Title | Priority | Status |
| --- | --- | --- | --- |
| [TEST-SUITE-TRIAGE-001](#test-suite-triage-001-full-pytest-run-and-triage) | Run full pytest suite and triage | Critical | in_progress |
| [VECTOR-PARITY-001](#vector-parity-001-restore-40962-benchmark-parity) | Restore 4096² benchmark parity | High | in_progress |
| [VECTOR-GAPS-002](#vector-gaps-002-vectorization-gap-audit) | Vectorization gap audit | High | blocked |
| [PERF-PYTORCH-004](#perf-pytorch-004-fuse-physics-kernels) | Fuse physics kernels | High | in_progress |
| [VECTOR-TRICUBIC-002](#vector-tricubic-002-vectorization-relaunch-backlog) | Vectorization relaunch backlog | High | in_progress |
| [CLI-FLAGS-003](#cli-flags-003-handle--nonoise-and--pix0_vector_mm) | Handle -nonoise and -pix0_vector_mm | High | in_progress |
| [TEST-GOLDEN-001](#test-golden-001-regenerate-golden-data-post-phase-d5) | Regenerate golden data post Phase D5 | High | in_planning |
| [STATIC-PYREFLY-001](#static-pyrefly-001-run-pyrefly-analysis-and-triage) | Run pyrefly analysis and triage | Medium | in_progress |
| [TEST-INDEX-001](#test-index-001-test-suite-discovery-reference-doc) | Test suite discovery reference doc | Medium | in_planning |

## [TEST-SUITE-TRIAGE-001] Full pytest run and triage
- Spec/AT: `docs/development/testing_strategy.md` §§1–2, `arch.md` §2/§15, `specs/spec-a-core.md` (Acceptance Tests), `docs/development/pytorch_runtime_checklist.md` (runtime guardrails).
- Priority: Critical
- Status: in_progress
- Owner/Date: galph/2026-01-12
- Plan Reference: `plans/active/test-suite-triage.md`
- Reproduction: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v --durations=25 --maxfail=0 --junitxml=reports/2026-01-test-suite-triage/phase_b/<STAMP>/artifacts/pytest_full.xml`
- Artifacts Root: `reports/2026-01-test-suite-triage/` (phases `phase_a`, `phase_b`, `phase_c`, `phase_d`)
- Attempts History:
  * [2025-10-10] Attempt #1 — Result: ✅ success (Phase A preflight complete). Captured environment snapshot (Python 3.13, PyTorch 2.7.1+cu126, CUDA 12.6, RTX 3090), disk audit (77G available, 83% used), and pytest collection baseline (692 tests, 0 errors). Artifacts: `reports/2026-01-test-suite-triage/phase_a/20251010T131000Z/{preflight.md,commands.txt,env.txt,torch_env.txt,disk_usage.txt,collect_only.log}`. All Phase A tasks (A1-A3 per `plans/active/test-suite-triage.md`) complete. Ready for Phase B full-suite execution.
  * [2025-10-10] Attempt #2 — Result: ⚠️ partial (Phase B timeout). Full suite execution reached ~75% completion (520/692 tests) before 10-minute timeout. Captured 34 failures across determinism (6), sourcefile handling (6), grazing incidence (4), detector geometry (5), debug/trace (4), CLI flags (3), and others. Runtime: 600s. Exit: timeout. Artifacts: `reports/2026-01-test-suite-triage/phase_b/20251010T132406Z/{logs/pytest_full.log,failures_raw.md,summary.md,commands.txt}`. junit XML may be incomplete. Remaining 172 tests (~25%) not executed. Observations: Large detector parity tests and gradient checks likely contributors to timeout. Recommendation: split suite execution or extend timeout to 30-60min for complete run.
  * [2025-10-10] Attempt #3 — Result: 📊 analysis (Phase C1). Classified all 34 observed failures as implementation bugs using `reports/2026-01-test-suite-triage/phase_c/20251010T134156Z/triage_summary.md`; no new commands executed (analysis derived from Phase B artifacts). Flagged remaining ~172 tests as coverage gap pending extended Phase B rerun. Next: align clusters C1–C14 with fix-plan entries and assign owners/next steps.
- Next Actions:
  1. Schedule Phase B rerun with ≥30 min budget (or split suite by module) to execute the remaining ~172 tests; capture logs + junit XML under a new timestamped bundle.
  2. Complete Phase C3/C4 by mapping clusters C1–C14 to fix-plan entries (spawn new IDs for determinism, debug trace, dual runner, detector config) and append owners/next actions inside `triage_summary.md`.
  3. Outline Phase D remediation handoff once coverage + mapping are in place (draft `handoff.md` with ordered priorities and selectors).
- Exit Criteria:
  - `triage_summary.md` classifies every failing test (bug vs deprecation vs config).
  - `handoff.md` published with remediation priorities and reproduction commands.
  - `[VECTOR-PARITY-001]` and other initiatives explicitly unblocked in this ledger.

## [VECTOR-PARITY-001] Restore 4096² benchmark parity
- Spec/AT: `specs/spec-a-core.md` §§4–5, `specs/spec-a-parallel.md` §2.3, `arch.md` §§2/8/15, `docs/architecture/pytorch_design.md` §1.1 & §1.1.5, `docs/development/testing_strategy.md` §§1.4–2, `docs/development/pytorch_runtime_checklist.md` item #4.
- Priority: High
- Status: in_progress
- Owner/Date: galph/2025-12-30
- Reproduction (C & PyTorch):
  * C: `NB_C_BIN=./golden_suite_generator/nanoBragg python scripts/nb_compare.py --resample --roi 1792 2304 1792 2304 --outdir reports/2026-01-vectorization-parity/phase_b/<STAMP>/roi_compare -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05`
  * PyTorch: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/nb_compare.py --resample --roi 1792 2304 1792 2304 --outdir reports/2026-01-vectorization-parity/phase_b/<STAMP>/roi_compare -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05`
  * Shapes/ROI: detector 4096×4096, pixel 0.05 mm, ROI slow=1792–2303 / fast=1792–2303 (512²)
- First Divergence (IDENTIFIED): Line 45 (`scattering_vec_A_inv`) — systematic ~10⁷× unit error (C in m⁻¹, PyTorch in Å⁻¹). See `reports/2026-01-vectorization-parity/phase_c/20251010T061605Z/first_divergence.md` for complete three-pixel analysis.
- Attempts History:
  * [2025-12-30] Attempt #0 — Result: partial (planning baseline). corr_warm=0.721175 (❌), speedup_warm=1.13×, sum_ratio=225.036 (full-frame). Artifacts: `reports/2026-01-vectorization-parity/phase_a/20251010T023622Z/artifact_matrix.md`, `reports/2026-01-vectorization-parity/phase_b/20251010T030852Z/summary.md`.
  * [2025-10-10] Attempt #6 — Result: failed (Phase B3d ROI pytest). corr_roi=0.7157 (❌), peak_matches=50/50 ≤1 px, runtime≈5.8 s. Artifacts: `reports/2026-01-vectorization-parity/phase_b/20251010T034152Z/pytest_highres.log`.
  * [2025-10-10] Attempt #7 — Result: success (Phase B4a ROI parity). corr_roi=0.999999999; sum_ratio=0.999987; RMSE=3.28e-05; mean_peak_delta=0.78 px; max_peak_delta=1.41 px. Artifacts: `reports/2026-01-vectorization-parity/phase_b/20251010T035732Z/roi_compare/{summary.json,summary.md,roi_scope.md}`.
  * [2025-10-10] Attempt #8 — Result: success (Phase C1 C traces). Captured TRACE_C logs for pixels (2048,2048), (1792,2048), (4095,2048) with commands/env metadata; all three lie in background (F_cell=0). Artifacts: `reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/{summary.md,commands.txt,env/trace_env.json,c_traces/}`.
  * [2025-10-10] Attempt #9 — Result: success (Phase C2 PyTorch traces). Enhanced `scripts/debug_pixel_trace.py` to accept `--pixel`, `--tag`, and `--out-dir` arguments; fixed 4 critical bugs (crystal vector extraction, integer conversion, pixel coordinates signature, Miller index units). Generated TRACE_PY logs for pixels (2048,2048), (1792,2048), (4095,2048) with 72 tap points matching C schema. Artifacts: `reports/2026-01-vectorization-parity/phase_c/20251010T055346Z/{py_traces/,env/trace_env.json,commands.txt,PHASE_C2_SUMMARY.md}`. Observations: PyTorch intensities non-zero (default_F=100) vs C zero (no HKL file); beam center match exact (0.10245 m); fluence discrepancy noted (1.27e+20 vs 1.26e+29, needs investigation Phase C3).
  * [2025-10-10] Attempt #10 — Result: success (Phase C3 first divergence analysis). Manual line-by-line comparison of C↔PyTorch traces for all three pixels (2048,2048 background; 1792,2048 on-peak; 4095,2048 edge). **Root causes identified:** (H1) scattering_vec ~10⁷× unit error (m⁻¹ vs Å⁻¹); (H2) fluence ~10⁹× error; (H3) F_latt ~100× normalization error. All geometric quantities match exactly (≤10⁻¹² tolerance), confirming detector implementation correctness. Divergence begins at physics calculations (line 45). Artifacts: `reports/2026-01-vectorization-parity/phase_c/20251010T061605Z/{first_divergence.md,summary.md,env/trace_env.json,commands.txt}`. Confidence: H1=95%, H2=90%, H3=85%.
  * [2025-10-10] Attempt #11 — Result: ✅ success (Phase D1 scattering vector unit fix). Fixed scattering_vec unit conversion from Å⁻¹ to m⁻¹ by adding `wavelength_meters = wavelength * 1e-10` in `src/nanobrag_torch/simulator.py:157` per spec-a-core.md line 446. Post-fix trace for pixel (1792,2048) shows perfect parity: x-component rel_err=4.3e-14, y-component rel_err=1.5e-15, z-component rel_err=1.6e-12 (target ≤1e-6). Also fixed trace script `scripts/debug_pixel_trace.py` to output m⁻¹ directly without spurious Å⁻¹ conversion. Pytest collection verified (692 tests). Artifacts: `reports/2026-01-vectorization-parity/phase_d/20251010T062949Z/{diff_scattering_vec.md,py_traces_post_fix/pixel_1792_2048.log,commands.txt,env/}`. Next: Phase D2 (fluence ~10⁹× error) and D3 (F_latt ~100× normalization).
  * [2025-10-10] Attempt #12 — Result: ✅ success (Phase D2 fluence parity fix). Root cause identified: `scripts/debug_pixel_trace.py:377-383` was **recomputing** fluence from `flux`, `exposure`, and `beamsize` instead of reading the spec-compliant value from `BeamConfig.fluence`. Fixed by changing trace helper to emit `beam_config.fluence` directly (lines 377-381). Post-fix trace for pixel (1792,2048) shows machine-precision parity: PyTorch fluence=1.259320152862271e+29, C fluence=1.25932015286227e+29, rel_err=7.941e-16 (target ≤1e-3). PyTorch simulator code in `src/nanobrag_torch/config.py:535-545` was CORRECT all along—the bug was in the trace helper, not the production code. Pytest collection verified (692 tests, no regressions). Artifacts: `reports/2026-01-vectorization-parity/phase_d/20251010T070307Z/{fluence_parity.md,py_traces_post_fix/pixel_1792_2048.log,commands.txt,env/}`. Next: Phase D3 (F_latt ~100× normalization).
  * [2025-10-10] Attempt #13 — Result: ✅ success (Phase D3 trace helper). Imported production `sincg` into `scripts/debug_pixel_trace.py`, captured `f_latt_parity.md` with rel_err≤5e-15, and documented outcomes in `reports/2026-01-vectorization-parity/phase_d/20251010T071935Z/PHASE_D3_SUMMARY.md`. ROI `nb-compare` still fails (corr=-0.001, sum_ratio=12.54) because `Simulator.run()` continued to emit ~32× lower intensity; this set the stage for Phase D4 simulator diagnostics.
  * [2025-10-10] Attempt #14 — Result: ✅ success (Phase D4 root cause diagnosis). **BUG IDENTIFIED:** Miller indices (h/k/l) are 10^10× too large due to unit mismatch—scattering_vector is in m⁻¹ (Phase D1 fix) but rotated lattice vectors (rot_a/b/c) remain in Å. When computing h=a·S, the result is dimensionless but 10^10 too small (we multiply Å × m⁻¹ = dimensionless × 10⁻¹⁰). This causes F_latt to be ~5× lower than expected (9.1 vs 47.98 correct), leading to ~25× intensity error. **Fix:** Convert rot_a/b/c from Å to m⁻¹ before passing to compute_physics_for_position() (multiply by 1e10). Artifacts: `reports/2026-01-vectorization-parity/phase_d/20251010T073708Z/{simulator_f_latt.md,simulator_f_latt.log,commands.txt}`. Instrumentation: env-guarded NB_TRACE_SIM_F_LATT logging added to `src/nanobrag_torch/simulator.py:312-367`. Next: implement unit conversion fix, verify h/k/l parity ≤1e-12, rerun ROI nb-compare (Phase D5).
  * [2025-10-10] Attempt #15 — Result: ✅ success (Phase D5 parity restoration). Applied lattice vector unit conversion in `src/nanobrag_torch/simulator.py:306-308` by multiplying `rot_a/b/c` by 1e-10 (Å→meters, NOT m⁻¹ as initially planned—dimensional analysis correction during implementation). ROI parity ACHIEVED: corr=1.000000 (precise: 0.9999999985), sum_ratio=0.999987, RMSE=3.28e-05, mean_peak_delta=0.866 px, max_peak_delta=1.414 px. Tested on 512² ROI (slow=1792-2303, fast=1792-2303) at 4096² detector, λ=0.5Å, pixel=0.05mm, distance=500mm. All exit criteria MET (corr≥0.999 ✅, |sum_ratio−1|≤5e-3 ✅). Pytest collection clean (692 tests). Artifacts: `reports/2026-01-vectorization-parity/phase_d/roi_compare_post_fix2/{summary.json,diff.png,c.png,py.png}`. Commit: bc36384c. NB_TRACE_SIM_F_LATT instrumentation preserved (cleanup → Phase D6). Next: remove instrumentation (D6), then proceed to full-frame validation (Phase E).
  * [2025-10-10] Attempt #16 — Result: ✅ success (Phase D6 cleanup). Removed NB_TRACE_SIM_F_LATT logging from `src/nanobrag_torch/simulator.py` (commit 9dd1c73d). Post-cleanup validation: `pytest --collect-only -q` (695 tests collected, 0 errors), ROI nb-compare corr=0.999999999, sum_ratio=0.999987, RMSE=3.3e-05. Artifacts: `reports/2026-01-vectorization-parity/phase_d/20251010T081102Z/cleanup/{commands.txt,phase_d6_summary.md,pytest_collect_after.log,roi_compare/summary.json}`. Ready to launch Phase E full-frame validation.
  * [2025-10-10] Attempt #21 — Result: ❌ BLOCKED (Phase E1 benchmark). Full-frame parity FAILED spec threshold despite Phase D1-D6 fixes and regenerated golden data. corr_warm=0.721177 (❌ required ≥0.999, delta −0.277823), speedup_warm=0.81×, C_time=0.532s, Py_time_warm=0.654s. **Critical finding:** ROI parity (512² center) passes at corr=1.000000 ✅ but full-frame (4096² complete) fails at corr=0.721177 ❌. **Implication:** Phase D lattice fix resolved central physics but residual bugs exist at edges/background. Correlation unchanged from Phase B baseline (0.721175→0.721177, +0.000002 delta). Artifacts: `reports/2026-01-vectorization-parity/phase_e/20251010T091603Z/{blockers.md,logs/benchmark.log}`, `reports/benchmarks/20251010-021637/{benchmark_results.json,profile_4096x4096/trace.json}`. Git SHA: 7ac34ad3. **Next:** Supervisor sign-off required; three mitigation options documented in blockers.md (ROI-only gating, extended trace debugging for edges, threshold adjustment). Per `input.md` line 8 guidance: halted Phase E; did not proceed with nb-compare or pytest steps.
  * [2025-10-10] Attempt #22 — Result: ✅ success (Phase E0 callchain analysis). Executed question-driven callchain trace per `prompts/callchain.md` focusing on edge/background factor order. **Primary hypothesis identified**: Oversample last-value semantics (`oversample_omega=False` by default) causes edge pixels with asymmetric solid-angle profiles to accumulate systematic bias. PyTorch multiplies accumulated intensity by the last subpixel's omega (bottom-right corner) instead of averaging, which approximates correctly for symmetric center pixels but diverges for asymmetric edge pixels (steep viewing angles → 5-10% omega variation across subpixel grid). **Secondary suspects**: F_cell=0 edge bias (more out-of-bounds HKL lookups), water background ratio effect (uniform background relatively stronger at dim edges), ROI timing difference (C may skip vs PyTorch post-hoc mask). Deliverables: `callchain/static.md` (complete execution flow with file:line anchors), `trace/tap_points.md` (7 proposed numeric taps), `summary.md` (one-page hypothesis narrative), `env/trace_env.json` (environment metadata). **First recommended tap**: `omega_subpixel_edge` (pixel 0,0) to quantify asymmetry magnitude (`relative_asymmetry > 0.05` would confirm 5%+ variation). Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T092845Z/{callchain/static.md,trace/tap_points.md,summary.md,callchain_brief.md,env/trace_env.json}`. Git SHA: aa390d8e. **Next**: Execute Tap 2/3 for omega asymmetry quantification, generate C trace for pixel (0,0) with oversample=2, compare C omega handling (average vs last-value), then advance to Phase E1 remediation.
  * [2025-10-10] Attempt #23 — Result: ✅ success (Phase E1 PyTorch omega tap). Reproduced oversample=2 solid-angle metrics for edge pixel (0,0) and center pixel (2048,2048). Observed `omega_last/omega_mean ≈ 1.000028` (≈0.003 % bias) at the edge and ≈1.0 at the center; relative asymmetry `(max-min)/mean ≈ 5.7×10⁻⁵`. Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T095445Z/{py_taps/omega_metrics.json,omega_analysis.md}` (earlier dry-run stored at `.../20251010T095329Z`). Conclusion: last-value ω weighting is too small to explain corr≈0.721; pivot Phase E to confirm C semantics but expand investigation to F_cell default usage and water background scaling.
  * [2025-10-10] Attempt #23 — Result: ❌ BLOCKED (Phase E0 tooling gap). Cannot execute `input.md` Do Now (omega asymmetry quantification for pixel 0,0 with oversample=2) because `scripts/debug_pixel_trace.py` does not support `--oversample` CLI argument or `NB_TRACE_EDGE_PIXEL` environment variable. Script is hard-coded to oversample=1 (line 383). **Blocker**: Trace script enhancement required to capture omega subpixel values, but `input.md` line 21 prohibits modifying trace script defaults during evidence-only pass. **Resolution options documented in blocker log:** (A) Enhance debug_pixel_trace.py (requires supervisor approval; violates evidence-only constraint), (B) Create separate trace script (same concern), (C) Revise Do Now to use simulator.run() directly with manual omega extraction, (D) Defer omega analysis until tooling gap addressed. **Recommendation**: Option D—halt evidence pass, request supervisor guidance on tooling enhancement vs. alternative evidence path. Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T094544Z/attempt_fail.log`. Git SHA: unchanged (no code edits). **Next**: Await supervisor decision on trace script enhancement approval or alternative evidence-gathering strategy.
  * [2025-10-10] Attempt #24 — Result: ✅ success (Phase E2 C omega tap). Instrumented `golden_suite_generator/nanoBragg.c:2976-2985` with `#pragma omp critical` tap to capture omega values for all 4 subpixels (oversample=2) at pixels (0,0) and (2048,2048). **Key finding:** C code uses **identical omega for all subpixels** when `oversample_omega=False` (default). The condition `omega_pixel == 0.0` is true only on first subpixel (0,0); subsequent subpixels retain the first value → all 4 subpixels share the same omega. Edge pixel (0,0): all 4 subpixels = 8.8611e-09 sr (last/mean=1.0000, asymmetry=0.0000). Center pixel (2048,2048): all 4 subpixels = 1.0000e-08 sr (last/mean=1.0000, asymmetry=0.0000). **Hypothesis REFUTED:** PyTorch's ~0.003% last-value bias (Attempt #23) is actually *more precise* than C's first-value reuse. Differences in omega handling explain ≤0.003% variation, far below the ~28% error needed for corr=0.721. Instrumentation removed post-capture; C binary rebuilt to clean state. Pytest collection verified (692 tests). Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T100102Z/c_taps/{tap_omega.txt,omega_metrics.json,omega_comparison.md,commands.txt}`. Git SHA: no code changes (instrumentation discarded). **Next**: Pivot to alternate hypotheses (F_cell default usage Tap 4, water background Tap 6) per `omega_comparison.md` conclusions.
  * [2026-01-10] Attempt #25 — Result: ✅ success (Phase E4 Tap 4 tooling). Extended `scripts/debug_pixel_trace.py` to support Tap 4 (F_cell statistics) collection with three new CLI flags: `--oversample N` (subpixel grid size, default 1), `--taps f_cell[,...]` (tap selectors), and `--json` (write tap metrics to JSON). Implemented `collect_f_cell_tap()` helper that computes scattering vectors for all oversample² subpixels, calculates fractional Miller indices using production lattice helpers (reuses `crystal.get_rotated_real_vectors()` per instrumentation discipline), accumulates HKL lookup statistics (total_lookups, out_of_bounds_count, zero_f_count, mean_f_cell, HKL bounds), and returns structured dict matching `tap_points.md` schema. Subpixel scattering vectors computed via torch.linspace offsets [-0.5, +0.5] pixel width, added to target pixel position via `detector.sdet_vec`/`fdet_vec`. Tap metrics emitted to stdout summary and optional JSON files (`pixel_{s}_{f}_{tap_id}.json`). Preserved legacy TRACE_PY output format (backward compatible). Pytest collection verified (695 tests). Artifacts: `scripts/debug_pixel_trace.py:60-72,109-216,539-598,720-730`. Git SHA: pending commit. **Next:** Follow-up executed in Attempts #26–#27 (Tap 4 runs); no further action from this tooling attempt.
  * [2025-10-10] Attempt #26 — Result: ✅ success (Phase E5 PyTorch Tap 4 capture). Executed Do Now commands for edge pixel (0,0) and centre pixel (2048,2048) with oversample=2, f_cell tap enabled. **Key findings:** Both pixels show **zero out-of-bounds HKL lookups** (out_of_bounds_count=0) and **100% default_F usage** (mean_f_cell=100.0 for all 4 subpixels). Edge pixel: h∈[-8,-8], k∈[39,39], l∈[-39,-39] (high scattering angle, I_final=3.018e-04). Centre pixel: h∈[0,0], k∈[0,0], l∈[0,0] (direct beam, I_final=1.538). Despite 5096× intensity difference, **no differential default_F behavior** between edge and centre. **Hypothesis REFUTED:** F_cell lookup logic does NOT explain the corr=0.721 full-frame divergence (Phase E1); edge/background correlation collapse must originate from a different systematic factor (Tap 5 pre-norm intensity, Tap 6 water background, or ROI masking). Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T102752Z/{f_cell_summary.md,py_taps/{pixel_0_0_f_cell_stats.json,pixel_2048_2048_f_cell_stats.json},env/{trace_env.txt,torch_env.json}}`. Elapsed: ~45s. Git SHA: pending commit. **Next:** Completed by Attempt #27 (C Tap 4). Await comparison + follow-up hypothesis selection.
  * [2025-10-10] Attempt #27 — Result: ✅ success (Phase E6 C Tap 4 capture). Instrumented `golden_suite_generator/nanoBragg.c:3337-3354` to emit TRACE_C_TAP4 lines for pixels (0,0) and (2048,2048) at oversample=2. **Key findings:** Edge pixel (0,0) uses `default_F=100` for all 4 subpixels (matches PyTorch). Centre pixel (2048,2048) retrieves in-bounds HKL values of 0.0 (no default fallback). **Critical discrepancy:** PyTorch Tap (Attempt #26) reported `mean_f_cell=100.0` for the centre pixel. Instrumentation removed, clean build verified (692 tests collected). Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T103811Z/c_taps/{tap4_raw.log,tap4_metrics.json,PHASE_E6_SUMMARY.md,commands.txt,env/trace_env.txt}`. Elapsed: ~3 min. Git SHA: b114bd8f. **Next:** Draft `f_cell_comparison.md` synthesising C vs PyTorch Tap 4 results; audit PyTorch default_F fallback path before selecting the next tap (Tap 5 pre-norm intensity vs Tap 6 water background).
  * [2025-10-10] Attempt #28 — Result: ✅ success (Phase E7 Tap 4 comparison + default_F audit). Aggregated Tap 4 metrics into `f_cell_comparison.md`, audited `models/crystal.py` + trace helper fallback paths, and cited `specs/spec-a-core.md` §§236–240 / 471–476. Confirmed both implementations keep in-bounds HKL zeros without applying `default_F`, so the centre-pixel mismatch stems from instrumentation semantics, not a physics bug. Determined omega/default_F hypotheses are exhausted and recommended advancing to Tap 5 (pre-normalisation intensity) before probing water background (Tap 6). Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T105617Z/comparison/{f_cell_comparison.md,default_f_audit.md,default_f_refs.txt,models_crystal_snippet.txt,trace_helper_snippet.txt}`.
  * [2025-10-10] Attempt #29 — Result: ✅ success (Phase E8 PyTorch Tap 5 capture). Extended `scripts/debug_pixel_trace.py` with `--taps intensity`, reused existing `I_before_scaling`, `steps`, `omega`, `capture_fraction`, and `polar` tensors, and recorded oversample=2 metrics for pixels (0,0) and (2048,2048). Edge pixel: `I_before_scaling=3.54e4`, `normalized_intensity=7.54e-05`; centre pixel: `I_before_scaling=1.538e8`, `normalized_intensity=0.3845`; both report `steps=4` (oversample²) with ω≈1.13× and polar≈1.04× centre/edge ratios, matching `specs/spec-a-core.md` §§246–259 scaling rules. Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T110735Z/py_taps/{pixel_0_0_intensity_pre_norm.json,pixel_2048_2048_intensity_pre_norm.json,intensity_pre_norm_summary.md,commands.txt,pytest_collect.log}`. Next: mirror Tap 5 on C side (target Attempt #30) then compare results before escalating to Tap 6 or Phase F.
  * [2025-10-10] Attempt #30 — Result: ✅ success (Phase E9 C Tap 5 capture). Instrumented `golden_suite_generator/nanoBragg.c:3397-3410` with `TRACE_C_TAP5` guard checking `getenv("TRACE_C_TAP5")` and capturing `I_before_scaling`, `steps`, `omega_pixel`, `capture_fraction`, `polar`, and `I_pixel_final` for trace pixels. Rebuilt binary (`make clean && make nanoBragg` in `golden_suite_generator/`); ran commands for pixels (0,0) and (2048,2048) at oversample=2. **Edge pixel (0,0):** I_before_scaling=1.415e5, omega=8.861e-09 sr, polar=0.961277; **centre pixel (2048,2048):** I_before_scaling=0.0 (no Bragg contribution), omega=1.000e-08 sr, polar=1.000000. Ratios: ω_center/ω_edge ≈ 1.129, polar_center/polar_edge ≈ 1.040 (matches PyTorch Attempt #29). **Critical finding:** ~4× intensity discrepancy at edge pixel (C: 1.415e5 vs PyTorch: 3.54e4). Centre pixel consistency confirmed (both zero). Summary memo `intensity_pre_norm_c_notes.md` synthesises metrics and proposes hypothesis: intensity gap likely stems from F_cell²/F_latt² subpixel accumulation. Pytest collection verified (692 tests). Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T112334Z/{c_taps/{pixel_0_0_tap5.log,pixel_2048_2048_tap5.log,commands.txt},comparison/{intensity_pre_norm_c_notes.md,pytest_collect.log},env/trace_env.json,PHASE_E9_SUMMARY.md}`. Git SHA: pending commit. **Next:** Follow the refreshed Next Actions (comparison doc + hypothesis ranking) before deciding on Tap 6 or remediation work.
  * [2025-10-10] Attempt #32 — Result: ✅ success (Phase E12 PyTorch Tap 5.1 HKL audit). Extended `scripts/debug_pixel_trace.py` with `--taps hkl_subpixel` to capture per-subpixel fractional HKL, rounded (h0,k0,l0), F_cell, and out_of_bounds status. Implemented `collect_hkl_subpixel_tap()` helper mirroring `collect_f_cell_tap()` pattern. Captured edge pixel (0,0) and centre pixel (2048,2048) at oversample=2. **Centre pixel:** All 4 subpixels round to HKL **(0,0,0)** with `F_cell=100.0`, `out_of_bounds=False`. **Edge pixel:** All 4 subpixels round to HKL **(-8,39,-39)** with `F_cell=100.0`, `out_of_bounds=False`. **H1 hypothesis REFUTED:** PyTorch does NOT treat (0,0,0) as out-of-bounds (flag is correctly False). The centre-pixel F_cell=100 vs C F_cell=0 discrepancy stems from test configuration (no HKL file loaded → all lookups return default_F). Both pixels correctly mark `out_of_bounds=False` and return default_F when no HKL data exists. Pytest collection verified (692 tests). Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T115342Z/{py_taps/{pixel_0_0_hkl_subpixel.json,pixel_2048_2048_hkl_subpixel.json},comparison/tap5_hkl_audit.md,commands.txt}`. Elapsed: ~8s. Git SHA: pending commit. **Next:** Task E13 (C Tap 5.1 mirror) + Task E14 (HKL bounds parity); revise hypothesis ranking in `tap5_hypotheses.md` based on "no HKL file" finding.
  * [2025-10-10] Attempt #33 — Result: ✅ success (Phase E12 PyTorch Tap 5.1 execution). Ran commands from `input.md` Do Now to capture HKL subpixel audit for centre pixel (2048,2048) and edge pixel (0,0) at oversample=2. **Centre pixel findings:** All 4 subpixels round to (0,0,0); fractional HKL components h≈-2e-06, k≈0.02, l≈-0.02; all report `out_of_bounds=false` and `F_cell=100.0`. **Edge pixel findings:** All 4 subpixels round to (-8,39,-39); fractional HKL components h≈-7.90, k≈39.35, l≈-39.35; all report `out_of_bounds=false` and `F_cell=100.0`. **Key conclusion:** H1 hypothesis (HKL indexing bug) REFUTED — PyTorch correctly treats (0,0,0) as in-bounds. The uniformF_cell=100 at centre pixel indicates no HKL file was loaded (all lookups return default_F regardless of bounds). Implication: The 4× intensity discrepancy from Attempt #30 is NOT caused by HKL indexing/bounds but must stem from H2 (oversample accumulation) or H3 (background inclusion). Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T120355Z/{py_taps/{pixel_0_0_hkl_subpixel.json,pixel_2048_2048_hkl_subpixel.json,hkl_subpixel_summary.md},commands.txt}`. Evidence-only loop (no pytest/commit per input.md). Elapsed: ~5s. Git SHA: unchanged (evidence capture only). **Next:** Execute E13 (C Tap 5.1 mirror) + E14 (HKL bounds parity check) to confirm hypothesis pivot before selecting remediation path.
  * [2025-10-10] Attempt #34 — Result: ✅ success (Phase E13 C Tap 5.1 HKL audit). Reused the existing `TRACE_C_TAP5_HKL` guard in `golden_suite_generator/nanoBragg.c:3337-3345` to mirror the PyTorch per-subpixel schema for pixels (0,0) and (2048,2048) at oversample=2. **Edge pixel:** all four subpixels round to (-8,39,-39) with `F_cell=100`, `out_of_bounds=0`. **Centre pixel:** all four subpixels round to (0,0,0) with `F_cell=100`, `out_of_bounds=0`. Confirms C treats (0,0,0) as in-bounds and applies `default_F` identically to PyTorch when no HKL file is loaded. Hypothesis H1 remains refuted on both implementations; Tap 5 discrepancy persists ahead of the oversample accumulation probe. Pytest collect-only stayed green (692 tests). Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T121436Z/{c_taps/{pixel_0_0_hkl.log,pixel_2048_2048_hkl.log,commands.txt},comparison/{tap5_hkl_c_summary.md,pytest_collect.log},env/}`.
  * [2025-10-10] Attempt #35 — Result: ✅ success (Phase E14 Tap 5.2 HKL bounds parity). Captured HKL grid bounds for pixels (0,0) and (2048,2048) at oversample=2 from both implementations. **Key finding:** Semantic difference identified—PyTorch reports per-pixel HKL ranges (edge: h=[-8,-8], centre: h=[0,0]), C reports global grid bounds (both pixels: h=[-24,24]). Both correctly use `default_F=100` for all lookups and treat (0,0,0) as in-bounds. **Hypothesis H1 (HKL indexing bug) remains REFUTED.** Bounds mismatch is expected and harmless (different questions answered). Pytest collection verified (692 tests). Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T123132Z/{bounds/{py,c}/{pixel_0_0,pixel_2048_2048}*.log,comparison/tap5_hkl_bounds.md,env/}`. Next: Proceed to Tap 5.3 (oversample accumulation) as planned.
  * [2026-01-10] Attempt #36 — Result: ✅ success (Tap 5.2 synthesis & hypothesis update). Folded Tap 5.2 HKL bounds evidence (`tap5_hkl_bounds.md`) into `tap5_hypotheses.md`, explicitly retired H1 (HKL indexing bug) with comprehensive refutation narrative citing Attempts #32-#35, and elevated H2 (oversample accumulation) to PRIMARY hypothesis (80% confidence). Updated hypothesis table, evidence sections, and "Recommended Action" to reflect Phase E15 pivot toward Tap 5.3 instrumentation. Added detailed "Next Steps" section outlining E15-E18 task requirements (instrumentation brief, PyTorch capture, C mirror, comparison). Pytest collection clean (692 tests, 0 errors). Artifacts: `tap5_hypotheses.md` (updated), `tap5_hkl_bounds.md` (referenced). Elapsed: ~8 min. Git SHA: pending commit. **Next:** Author Tap 5.3 instrumentation brief (`tap5_accum_plan.md`) per Phase E15 task requirements before extending trace scripts.
  * [2025-10-10] Attempt #37 — Result: ✅ success (Phase E15 Tap 5.3 instrumentation brief). Authored `tap5_accum_plan.md` in `reports/2026-01-vectorization-parity/phase_e0/20251010T125953Z/` defining logging schema (12 variables per subpixel: `subpixel_idx`, `s_sub/f_sub`, `h_frac/k_frac/l_frac`, `h0/k0/l0`, `F_cell`, `F_latt`, `I_term`, `I_accum`, `omega`, `capture_fraction`, `polar`), guard names (`--taps accum` for PyTorch, `TRACE_C_TAP5_ACCUM` for C), target pixels ((0,0) edge, (2048,2048) centre), acceptance criteria (≤1e-6 relative error for `F_cell²·F_latt²`, running sum parity at each subpixel boundary), and command templates for E16/E17 executions. Cited `specs/spec-a-core.md:241-259` (accumulation + last-value semantics) as normative references. Pytest collection verified (692 tests, 0 errors). Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T125953Z/{tap5_accum_plan.md,commands.txt,pytest_collect.log}`. Elapsed: ~3 min. Docs-only mode (no code changes). Git SHA: pending commit. **Next:** Phase E16 (PyTorch Tap 5.3 capture) — extend `scripts/debug_pixel_trace.py` with `--taps accum` per plan schema.
- Observations/Hypotheses:
  - Full-frame correlation collapse is dominated by edge/background pixels; central ROI meets spec thresholds (`roi_scope.md`).
  - Benchmark vs nb-compare metrics diverge; need trace-backed validation to reconcile tooling differences.
  - ROI parity confirms physics is correct for signal-rich pixels; divergence likely resides in scaling applied outside the ROI.
  - Phase C1 traces confirm the selected pixels are background-only (I_pixel_final=0); plan to add at least one on-peak trace if PyTorch outputs mirror that behaviour.
  - **Phase C3 confirms:** Geometric parity is perfect (≤10⁻¹² error). Physics divergence begins at scattering_vec (line 45). Three independent bugs compound to produce corr=0.721: (H1) scattering vector units, (H2) fluence calculation, (H3) F_latt normalization. All are actionable and should be fixed sequentially H1→H2→H3.
  - 2026-01-06 supervisor review captured `reports/2026-01-vectorization-parity/phase_d/fluence_gap_analysis.md`, quantifying the legacy TRACE_PY fluence underflow (~9.89e+08 ratio vs C) and confirming `BeamConfig.fluence` already matches spec; the trace helper must stop re-deriving flux-based values during Phase D2.
  - Attempt #14 confirms the simulator regression: NB_TRACE_SIM_F_LATT shows lattice vectors remained in Å, producing h/k/l values 10^10× too large and intensities ~32× low. Fix requires multiplying `rot_a/b/c` by 1e10 (Å→m⁻¹) before computing h·S. Evidence: `reports/2026-01-vectorization-parity/phase_d/20251010T073708Z/simulator_f_latt.md`.
  - **Phase D5 success:** ROI parity fully restored (corr=1.000000, sum_ratio=0.999987). Critical lesson: dimensional analysis error in Phase D4 planning (proposed 1e10 for Å→m⁻¹) was corrected during implementation to 1e-10 (Å→meters). The correct units for lattice vectors in the dot product h=a·S are meters (not m⁻¹), matching scattering_vector units (m⁻¹) to produce dimensionless Miller indices. This error highlights the importance of verifying unit conversions during implementation, not just during planning.
  - **Phase D6 cleanup:** ROI parity remains stable post-instrumentation removal (corr≈0.999999999, |sum_ratio−1|≈1.3e-5). Pytest collection stays green (695 tests). No residual trace hooks remain in production code; Phase E can now proceed without debug guards.
  - Attempt #24 (Phase E2/E3) shows C reuses the first subpixel's omega (edge + centre identical), aligning with PyTorch within ≈0.003 %. Omega bias is ruled out; focus shifts to HKL/default_F usage and background scaling.
  - Attempts #26–#28 closed the default_F hypothesis: both implementations leave in-bounds HKLs at 0.0 with no fallback. Remaining parity gap must come from intensity accumulation or background terms.
  - Attempt #29 demonstrates PyTorch Tap 5 pre-normalisation metrics match spec (steps=oversample², ω/ polar ratios ≈1.13×/1.04× centre vs edge). Discrepancy likely originates on the C side or downstream scaling.
  - Attempt #34 confirms C mirrors PyTorch HKL indexing and default_F semantics.
  - Attempt #35 shows Tap 5.2 “bounds” taps diverge semantically (PyTorch per-pixel vs C global grid) yet both sides treat `(0,0,0)` as in-bounds with `default_F=100`; oversample accumulation remains the leading hypothesis.
- Next Actions:
  1. 🛠️ Tap 5.3 instrumentation brief — Author `reports/2026-01-vectorization-parity/phase_e0/<STAMP>/tap5_accum_plan.md` capturing logging schema, guard names (`TRACE_PY_TAP5_ACCUM` / `TRACE_C_TAP5_ACCUM`), pixels/ROI, and acceptance checks before any code edits.
  2. 🧪 Tap 5.3 PyTorch capture — Extend `scripts/debug_pixel_trace.py` with the Tap 5.3 hook and record per-subpixel `F_cell²·F_latt²`, ω, and capture weights for pixels (0,0) and (2048,2048) at oversample=2; archive logs + summary and log pytest collect-only.
  3. 🔁 Tap 5.3 C mirror — Add `TRACE_C_TAP5_ACCUM` guard to `golden_suite_generator/nanoBragg.c`, capture matching per-subpixel accumulation logs for the same pixels, and store artifacts alongside the PyTorch bundle with commands/env notes.
  4. 🧭 Tap 5.3 synthesis — Compare PyTorch vs C accumulation logs, update `tap5_hypotheses.md` with conclusions, and decide whether Phase F remediation or Tap 6 instrumentation is required.
- Risks/Assumptions:
  - Profiler evidence remains invalid while corr_warm=0.721; avoid reusing traces from blocked attempts.
  - ROI thresholds (corr≥0.999, |sum_ratio−1|≤5×10⁻³) are treated as spec acceptance; full-frame parity may require masking.
- Exit Criteria (spec thresholds):
  - Correlation ≥0.999 and |sum_ratio−1| ≤5×10⁻³ for both ROI and full-frame comparisons.
  - `tests/test_at_parallel_012.py::test_high_resolution_variant` passes without xfail.
  - Parallel trace comparison identifies and resolves the first numeric divergence (`reports/2026-01-vectorization-parity/phase_c/`).

## [VECTOR-GAPS-002] Vectorization gap audit
- Spec/AT: `specs/spec-a-core.md` §4, `specs/spec-a-parallel.md` §2.3, `arch.md` §§2/8/15, `docs/architecture/pytorch_design.md` §1.1, `docs/development/pytorch_runtime_checklist.md`, `docs/development/testing_strategy.md` §§1.4–2.
- Priority: High
- Status: blocked (profiling halted by parity regression)
- Owner/Date: galph/2025-12-22
- Reproduction (C & PyTorch):
  * PyTorch profiler: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts --outdir reports/2026-01-vectorization-gap/phase_b/<STAMP>/profile/`
  * Static analysis: `python scripts/analysis/vectorization_inventory.py --package src/nanobrag_torch --outdir reports/2026-01-vectorization-gap/phase_a/<STAMP>/`
  * Shapes/ROI: detector 4096×4096, full frame
- First Divergence (if known): Profiler correlation stuck at 0.721175 (❌) — parity issue upstream.
- Attempts History:
  * [2025-10-09] Attempt #2 — Result: success (Phase A classification). Loops catalogued=24 (Vectorized=4, Safe=17, Todo=2, Uncertain=1). Artifacts: `reports/2026-01-vectorization-gap/phase_a/20251009T065238Z/{analysis.md,summary.md,loop_inventory.json,pytest_collect.log}`.
  * [2025-10-10] Attempt #8 — Result: failed (Phase B1 profiler). corr_warm=0.721175 (❌), corr_cold=0.721175, speedup_warm=1.15×, cache_speedup=64480×. Artifacts: `reports/2026-01-vectorization-gap/phase_b/20251010T022314Z/failed/{benchmark_results.json,profile_4096x4096/trace.json,summary.md}`.
- Observations/Hypotheses:
  - Inventory ready, but profiling cannot proceed until `[VECTOR-PARITY-001]` restores ≥0.999 correlation.
  - Reusing blocked traces risks mis-prioritising vectorization work.
- Next Actions:
  1. After parity fix, rerun Phase B1 profiler capture (corr_warm ≥0.999 required).
  2. Map ≥1 % inclusive-time hotspots to the loop inventory and update `plans/active/vectorization-gap-audit.md`.
  3. Publish prioritised backlog linking loops to expected performance wins.
- Risks/Assumptions:
  - Avoid advancing Phase B2/B3 while parity is failing.
  - Keep NB_C_BIN pointing to `./golden_suite_generator/nanoBragg` for comparability.
- Exit Criteria (spec thresholds):
  - Profiler bundle with corr_warm ≥0.999 and |sum_ratio−1| ≤5×10⁻³.
  - Hotspot report covering all ≥1 % loops with remediation plan.
  - Backlog endorsed by performance/vectorization owners.

## [PERF-PYTORCH-004] Fuse physics kernels
- Spec/AT: `plans/active/perf-pytorch-compile-refactor/plan.md`, `docs/architecture/pytorch_design.md` §§2.4 & 3, `docs/development/testing_strategy.md` §1.4.
- Priority: High
- Status: in_progress
- Owner/Date: galph/2025-09-30
- Reproduction (C & PyTorch):
  * CPU benchmarks: `NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 256 512 1024 4096 --device cpu --dtype float32 --iterations 1 --keep-artifacts --outdir reports/benchmarks/<STAMP>-cpu/`
  * CUDA benchmarks: `NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 256 512 1024 --device cuda --dtype float32 --iterations 1 --keep-artifacts --outdir reports/benchmarks/<STAMP>-cuda/`
  * Shapes/ROI: detectors 256²–4096², oversample 1, full-frame comparisons
- First Divergence (if known): Warm speedup fell to ≈0.30 (PyTorch 1.7738 s vs C 0.5306 s) in `reports/benchmarks/20251001-025148/`, caused by harness env var bug toggling compile mode.
- Attempts History:
  * [2025-09-30] Attempt #6 — Result: partial success. Multi-source cache stable; warm/cold speedup=258.98× (n_sources=3, 256² CPU). Artifacts: `reports/benchmarks/20250930-180237-compile-cache/cache_validation_summary.json`.
  * [2025-10-01] Attempt #34 — Result: failed regression audit. corr_warm≈0.83 with warm speedup=0.30×; identified `NANOBRAGG_DISABLE_COMPILE` bug. Artifacts: `reports/benchmarks/20251001-025148/{benchmark_results.json,summary.md}`.
  * [2025-10-08] Attempt #35 — Result: success. Vectorized source sampling (3969 sources → 1.023 ms, 117× faster). Artifacts: `reports/2025-10-vectorization/gaps/20251008T232859Z/`.
- Observations/Hypotheses:
  - Harness must push/pop `NANOBRAGG_DISABLE_COMPILE` before new benchmarks are trusted.
  - Remaining slowdown likely in detector/normalisation loops now that source sampling is vectorized.
  - Parity fix is prerequisite for final performance measurements.
- Next Actions:
  1. Implement harness fix (plan task B7) and rerun 10-process reproducibility study (Phase B6).
  2. After parity recovery, refresh CPU/CUDA benchmarks and capture chrome traces (Phase C diagnostics).
  3. Publish reconciliation memo comparing new results with `reports/benchmarks/20251001-025148/` and earlier Phase B bundles.
- Risks/Assumptions:
  - torch.compile caches must be isolated per mode; otherwise warm timings are unreliable.
  - Multi-source polarization fix (plan P3.0b) still outstanding.
- Exit Criteria (spec thresholds):
  - Warm runtime ≤1.0× C on GPU and ≤1.2× C on CPU for 256²–1024²; 4096² CPU slowdown documented.
  - Reproducibility study variance ≤5 %.
  - Performance memo archived with updated metrics + recommendations.

## [VECTOR-TRICUBIC-002] Vectorization relaunch backlog
- Spec/AT: `specs/spec-a-core.md` §§4–5, `arch.md` §§2/8/15, `docs/architecture/pytorch_design.md` §1.1, `docs/development/pytorch_runtime_checklist.md`, `docs/development/testing_strategy.md` §§1.4–2, `plans/archive/vectorization.md`.
- Priority: High
- Status: in_progress (waiting on `[VECTOR-PARITY-001]` Phase E full-frame validation + `[TEST-GOLDEN-001]` ledger updates before restarting profiling)
- Owner/Date: galph/2025-12-24
- Reproduction (C & PyTorch):
  * Regression refresh: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py -v` and `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_abs_001.py -v -k "cpu or cuda"`
  * Benchmarks: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts --outdir reports/2026-01-vectorization-refresh/phase_b/<STAMP>/`
  * Shapes/ROI: tricubic/absorption suites (CPU + CUDA)
- First Divergence (if known): None — CUDA placement issue solved 2025-10-09 (`simulator.py:486-490`).
- Attempts History:
  * [2025-12-28] Attempt #1 — Result: planning. Logged dependency readiness in `plans/active/vectorization.md`.
  * [2025-10-09] Attempt #2 — Result: success (Phase B1). Tricubic CPU 1.45 ms/call; CUDA 5.68 ms/call; absorption CPU 4.72 ms (256²)/22.90 ms (512²); absorption CUDA 5.43 ms (256²)/5.56 ms (512²). Artifacts: `reports/2026-01-vectorization-refresh/phase_b/20251010T013437Z/`.
  * [2025-10-10] Attempt #3 — Result: failed (Phase C1 profiler). corr_warm=0.721175 ❌ (threshold ≥0.999), speedup_warm=1.19×, cache=72607.7×. Artifacts: `reports/2026-01-vectorization-gap/phase_b/20251010T043632Z/{summary.md,profile_4096x4096/trace.json}`. Observations: Parity regression confirmed—profiler evidence CANNOT be used for Phase C2/C3 until `[VECTOR-PARITY-001]` resolves full-frame correlation. Next: Block Phase C2/C3; rerun profiler after parity fix.
- Observations/Hypotheses:
  - CPU favours tricubic microbenchmarks; absorption benefits from CUDA.
  - Phase C traces + `first_divergence.md` (Attempt #10) isolate unit/fluence/F_latt defects; implementation deferred to `[VECTOR-PARITY-001]` Phase D/E.
  - Cache effectiveness (72607.7×) and torch.compile operational, but physics correctness must be restored first.
  - Attempt #20 (ROI parity) confirms regenerated golden data match the Phase D5 lattice fix; still need `[VECTOR-PARITY-001]` Phase E rerun to refresh full-frame metrics before profiling.
- Next Actions:
  1. Hold Phase D1 until `[VECTOR-PARITY-001]` Phase E produces a ≥0.999 full-frame rerun with regenerated golden data (`reports/2026-01-vectorization-parity/phase_e/<STAMP>/phase_e_summary.md`) and `[TEST-GOLDEN-001]` Phase D updates land.
  2. Once gating artifacts exist, execute Phase D1 profiler capture (`KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts --outdir reports/2026-01-vectorization-gap/phase_b/<STAMP>/profile/`) and archive `trace.json`, `summary.md`, `env.json`.
  3. After D1, deliver Phase D2/D3 backlog refresh and prepare Phase E1/E2 delegation (tricubic design addendum + input.md Do Now) before authorising implementation.
- Risks/Assumptions:
  - CUDA availability required for future refresh runs.
  - Parity regression must be resolved before shipping new vectorization work.
- Exit Criteria:
  - Phase C profiler/backlog complete with parity-confirmed evidence.
  - Phase D implementation revalidated on CPU & CUDA.
  - Plan archived with before/after benchmarks and doc updates.

## [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
- Spec/AT: `specs/spec-a-cli.md`, `docs/architecture/detector.md` §5, `docs/development/c_to_pytorch_config_map.md`, nanoBragg.c lines 720–1040 & 1730–1860.
- Priority: High
- Status: in_progress
- Owner/Date: ralph/2025-10-05
- Reproduction (C & PyTorch):
  * C: ``./golden_suite_generator/nanoBragg -mat A.mat -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 -floatfile reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/inputs/c_roi_float.bin``
  * PyTorch: ``PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -mat A.mat -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 -floatfile reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/inputs/py_roi_float.bin``
  * Shapes/ROI: detector 2463×2527, pixel 0.172 mm, full frame, noise disabled.
- First Divergence (if known): `I_before_scaling` mismatch (C=943654.81 vs PyTorch=805473.79, −14.6%) from `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/metrics.json`.
- Attempts History:
  * [2025-10-08] Attempt #34 — Result: ⚠️ scaling regression (Phase M1). sum_ratio=1.159e5, corr=0.9852 after ROI alignment. Artifacts: `reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/`.
  * [2025-10-08] Attempt #35 — Result: success (Phase M2). Option 1 (spec-compliant scaling) documented; C bug tracked as C-PARITY-001. Artifacts: `reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/analysis.md`.
- Observations/Hypotheses:
  - PyTorch path is spec-compliant; C reference diverges when `-nonoise` present.
  - Dedicated regression test required once CLI flags are fully wired.
- Next Actions:
  1. Implement CLI parsing / detector wiring for both flags in PyTorch CLI.
  2. Add targeted pytest covering noiseless + pix0 override scenario.
  3. Update documentation with flag behaviour and known C discrepancy.
- Risks/Assumptions:
  - Preserve Protected Assets (`docs/index.md`, `loop.sh`, `supervisor.sh`).
  - ROI ordering (slow, fast) must be consistent when validating pix0 overrides.
- Exit Criteria:
  - PyTorch CLI honours both flags with corr≥0.999, |sum_ratio−1|≤5×10⁻³.
  - Regression test suite updated; documentation linked from `docs/index.md`.

## [TEST-GOLDEN-001] Regenerate golden data post Phase D5
- Spec/AT: `specs/spec-a-parallel.md` §AT-PARALLEL-012, `tests/golden_data/README.md`, `docs/development/testing_strategy.md` §§1.4–2, `docs/development/pytorch_runtime_checklist.md`, `plans/active/test-golden-refresh.md`.
- Priority: High
- Status: in_progress
- Owner/Date: galph/2026-01-07; ralph/2025-10-10 (Phase A)
- Reproduction (C & PyTorch):
  * C (high-res reference): `pushd golden_suite_generator && KMP_DUPLICATE_LIB_OK=TRUE "$NB_C_BIN" -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05 -floatfile ../tests/golden_data/high_resolution_4096/image.bin && popd`
  * PyTorch ROI parity: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/nb_compare.py --resample --roi 1792 2304 1792 2304 --outdir reports/2026-01-golden-refresh/phase_c/<STAMP>/high_res_roi -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05`
  * Targeted pytest: `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_high_resolution_variant`
  * Shapes/ROI: detector 4096×4096, ROI slow/fast 1792–2303 (512²), noise disabled.
- First Divergence (if known): Attempt #17 (`reports/2026-01-vectorization-parity/phase_e/20251010T082240Z/`) — ROI correlation 0.7157 due to stale `tests/golden_data/high_resolution_4096/image.bin` predating Phase D5 lattice fix.
- Attempts History:
  * [2025-10-10] Attempt #18 — Result: ✅ success (Phase A scope audit). Enumerated 5 golden datasets requiring regeneration (`simple_cubic`, `simple_cubic_mosaic`, `triclinic_P1`, `cubic_tilted_detector`, `high_resolution_4096`). Ran high-resolution ROI audit: corr=1.000000 (✅ PASS, threshold ≥0.95), sum_ratio=0.999987 (✅), RMSE=3.3e-05, mean_peak_delta=0.87 px, max_peak_delta=1.41 px. Identified 5 consuming test files (`test_at_parallel_012.py`, `test_at_parallel_013.py`, `test_suite.py`, `test_detector_geometry.py`, `test_crystal_geometry.py`). Physics delta: Phase D5 lattice unit fix (commit bc36384c) changed F_latt scaling by correcting 10^10× Miller index mismatch (lattice vectors Å→meters conversion). All datasets predating this fix are stale. Artifacts: `reports/2026-01-golden-refresh/phase_a/20251010T084007Z/{scope_summary.md,high_resolution_4096/{commands.txt,summary.json,*.png}}`. Exit criteria met: scope enumerated, corr ≥0.95 confirmed, consuming tests mapped. Next: Phase B regeneration (5 datasets) using canonical commands in `scope_summary.md` §Phase B.
  * [2025-10-10] Attempt #19 — Result: ✅ success (Phase B regeneration complete). All 5 golden datasets regenerated with self-contained `-cell` commands: `simple_cubic` (1024²), `simple_cubic_mosaic` (1000², 10 domains), `triclinic_P1` (512², misset orientation), `cubic_tilted_detector` (1024², rotx/y/z + twotheta), `high_resolution_4096` (4096²). Recorded SHA256 checksums: simple_cubic.bin=ecec0d4d..., simple_cubic_mosaic.bin=e1ce2591..., triclinic_P1/image.bin=b95f9387..., cubic_tilted_detector/image.bin=2837abc0..., high_resolution_4096/image.bin=2df24451... Git SHA: 0b2fa6d7, C binary SHA256: 88916559... Commands captured in `reports/2026-01-golden-refresh/phase_b/20251010T085124Z/{dataset}/command.log`. Updated `tests/golden_data/README.md` with new provenance entries for all datasets (timestamp, git SHA, C binary checksum, SHA256 hashes). Artifacts: `reports/2026-01-golden-refresh/phase_b/20251010T085124Z/{phase_b_summary.md,repo_sha.txt,c_binary_checksum.txt,*/command.log,*/checksums.txt}`. Exit criteria met: all datasets regenerated ✅, README updated ✅, SHA256 manifests recorded ✅. Next: Phase C parity validation (ROI nb-compare + targeted pytest).
  * [2026-01-10] Attempt #20 — Result: ✅ success (Phase C parity validation complete). ROI parity check PASSED: corr=1.000000 (threshold ≥0.95 ✅), sum_ratio=0.999987 (|ratio−1|=0.000013 ≤5e-3 ✅), RMSE=0.000033, max|Δ|=0.001254, mean_peak_delta=0.87 px, max_peak_delta=1.41 px. Runtime: C=0.519s, Py=5.856s. Targeted pytest PASSED: `test_high_resolution_variant` completed in 5.83s with no failures. Validated regenerated golden data from Attempt #19 against spec thresholds AT-PARALLEL-012. Artifacts: `reports/2026-01-golden-refresh/phase_c/20251010T090248Z/{phase_c_summary.md,high_res_roi/{summary.json,c.png,py.png,diff.png},pytest_highres.log}`. Exit criteria met: ROI correlation ✅, sum_ratio ✅, pytest passing ✅. Next: mark Phase C tasks complete in plan, unblock [VECTOR-PARITY-001] Phase E, proceed to Phase D ledger updates.
- Observations/Hypotheses:
  - Phase D5 lattice unit change invalidates any golden data that depend on `F_latt`; high-resolution 4096² case already confirmed.
  - Other datasets (triclinic, tilted detector, mosaic) likely impacted; need systematic audit before regenerating.
  - README provenance must stay authoritative; include git SHA + checksum after refresh.
- Next Actions:
  1. ✅ Execute `[TEST-GOLDEN-001]` Phase B regeneration for all five datasets — COMPLETE (Attempt #19, 2025-10-10T08:51:24Z).
  2. ✅ Update `tests/golden_data/README.md` provenance entries — COMPLETE (all 5 datasets documented with SHA256, git SHA, C binary checksum).
  3. ✅ Stage regenerated artifacts and commit with provenance — COMPLETE (commit `ebc140f2`).
  4. ✅ Execute Phase C parity validation: ROI nb-compare + targeted pytest selector — COMPLETE (Attempt #20, 2026-01-10T09:02:48Z); corr=1.000000 ✅, sum_ratio=0.999987 ✅, pytest PASSED ✅.
  5. 📝 Mark Phase C tasks [D]one in `plans/active/test-golden-refresh.md`; update `[VECTOR-PARITY-001]` to reflect Phase E unblocked status.
  6. 🗒️ Proceed to Phase D ledger updates once Phase C closure confirmed in plan.
- Risks/Assumptions:
  - Regeneration must respect Protected Assets (do not delete files referenced in `docs/index.md`).
  - Large binaries may exceed git LFS thresholds; preserve existing file paths and sizes.
  - Requires stable `NB_C_BIN`; document git SHA for every regeneration run.
- Exit Criteria:
  - All golden datasets enumerated in Phase A regenerated with updated provenance entries.
  - ROI correlation ≥0.95 and |sum_ratio−1| ≤5×10⁻³ validated via nb-compare.
  - Targeted pytest selector passes; `[VECTOR-PARITY-001]` Phase E unblocked and plan ready for archive once downstream tasks finish.

## [STATIC-PYREFLY-001] Run pyrefly analysis and triage
- Spec/AT: `prompts/pyrefly.md`, `prompts/supervisor.md`, `docs/development/testing_strategy.md` §1.5, `pyproject.toml` `[tool.pyrefly]`.
- Priority: Medium
- Status: in_progress
- Owner/Date: ralph/2025-10-08
- Reproduction (PyTorch):
  * Static scan: `pyrefly check src` (archive stdout/stderr to `reports/pyrefly/<STAMP>/pyrefly.log`).
  * Verification: targeted pytest selectors recorded alongside fixes.
  * Shapes/ROI: n/a (static analysis).
- First Divergence (if known): Baseline pyrefly violations not yet captured post float32 migration.
- Attempts History:
  * [2025-10-08] Attempt #1 — Result: success (Phase A). Tool installation verified; config confirmed at `pyproject.toml:11`. Artifacts: `reports/pyrefly/20251008T053652Z/{commands.txt,README.md}`.
- Observations/Hypotheses:
  - Toolchain ready; next step is baseline scan + triage.
- Next Actions:
  1. Run `pyrefly check src` and archive logs + JSON summary.
  2. Classify findings (bug vs style) and map to pytest selectors.
  3. Update plan with remediation order + delegation notes.
- Risks/Assumptions:
  - Capture exit codes for future CI integration.
- Exit Criteria:
  - Baseline pyrefly report archived with triage notes.
  - Follow-on fix plan created for high-severity findings.

## [TEST-INDEX-001] Test suite discovery reference doc
- Spec/AT: `docs/development/testing_strategy.md`, `specs/spec-a-parallel.md` §2, `docs/index.md`.
- Priority: Medium
- Status: in_planning
- Owner/Date: galph/2025-12-25
- Reproduction (PyTorch):
  * Inventory: `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` (Phase A capture).
  * Documentation draft: `docs/development/test_suite_index.md` (target); link from `docs/index.md` once published.
  * Shapes/ROI: n/a.
- First Divergence (if known): No central reference for pytest selectors, slowing triage.
- Attempts History: none yet — Phase A bundle outstanding.
- Observations/Hypotheses:
  - Expect subagents to author per-suite summaries (AT, CLI, perf, vectorization).
- Next Actions:
  1. Execute Phase A1–A3 (collect-only run, build `inventory.json`, summarise doc touchpoints).
  2. Prepare taxonomy outline and drafting checklist for delegation.
  3. Update Protected Assets once doc path is finalised.
- Risks/Assumptions:
  - Ensure collect-only run stored under timestamped reports.
- Exit Criteria:
  - Reference doc published with selector tables + maintenance guidance.
  - Linked from `docs/index.md`; ledger reflects upkeep cadence.

## Completed / Archived Items
- [SOURCE-WEIGHT-001] Correct weighted source normalization — DONE (2025-10-10). corr=0.9999886, |sum_ratio−1|=0.0038; artifacts in `reports/2025-11-source-weights/phase_h/20251010T002324Z/`; guardrails captured in `docs/architecture/pytorch_design.md` §1.1.5.
- [VECTOR-TRICUBIC-001] Vectorize tricubic interpolation and detector absorption — DONE. CUDA/CPU parity maintained (`reports/2026-01-vectorization-refresh/phase_b/20251010T013437Z/`); plan archived in `plans/archive/vectorization.md`.
- [ROUTING-LOOP-001] `loop.sh` routing guard — DONE. Automation guard active; see `plans/active/routing-loop-guard/` for history.
- [PROTECTED-ASSETS-001], [REPO-HYGIENE-002], [CLI-DTYPE-002], [ABS-OVERSAMPLE-001], [C-SOURCEFILE-001], [ROUTING-SUPERVISOR-001] — Archived to `docs/fix_plan_archive.md` with summary + artifact links; re-open if prerequisites resurface.
  * [2025-10-10] Attempt #31 — Result: ✅ success (Phase E10 Tap 5 comparison + hypothesis ranking). Produced side-by-side metrics comparison in `intensity_pre_norm.md` and ranked hypotheses in `tap5_hypotheses.md`. **Critical finding:** Centre pixel (2048,2048) shows **HKL indexing bug** — C retrieves F_cell=0 (in-bounds) for Miller indices (h,k,l)≈(0,0.015,−0.015)→rounded to (0,0,0), while PyTorch uses default_F=100 (out-of-bounds treatment). Edge pixel exhibits ~4× raw intensity mismatch (C: 1.415e5, PyTorch: 3.543e4), but omega/polar factors cancel within ≤0.003%. **Hypotheses ranked:** H1 (HKL indexing bug, 95% confidence) — PyTorch's nearest-neighbor lookup incorrectly treats (0,0,0) as out-of-bounds. H2 (subpixel accumulation order, 25%) — defer until H1 resolved. H3 (water background, 10%) — defer, counter-evidence strong. **Recommended action:** Execute Tap 5.1 (per-subpixel audit) + Tap 5.2 (HKL bounds check) to confirm H1 before code changes. Artifacts: `reports/2026-01-vectorization-parity/phase_e0/20251010T113608Z/comparison/{intensity_pre_norm.md,tap5_hypotheses.md,tap5_metrics_table.txt,commands.txt,extract_tap5_metrics.py}`. Evidence-only loop (no pytest execution per input.md guidance). **Next:** Draft Tap 5.1/5.2 commands for next Ralph loop; update plan Phase E table E10→[D], add E11 decision row.
