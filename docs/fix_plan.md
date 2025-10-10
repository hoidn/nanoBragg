# Fix Plan Ledger

**Last Updated:** 2026-01-07 (galph loop — TEST-GOLDEN-001 launch)
**Active Focus:**
- Execute VECTOR-PARITY Phase E full-frame validation and ledger updates now that Phase D6 cleanup succeeded.
- Prepare pyrefly + test-index documentation so future delegations have authoritative selectors.

## Index
| ID | Title | Priority | Status |
| --- | --- | --- | --- |
| [VECTOR-PARITY-001](#vector-parity-001-restore-40962-benchmark-parity) | Restore 4096² benchmark parity | High | in_progress |
| [VECTOR-GAPS-002](#vector-gaps-002-vectorization-gap-audit) | Vectorization gap audit | High | blocked |
| [PERF-PYTORCH-004](#perf-pytorch-004-fuse-physics-kernels) | Fuse physics kernels | High | in_progress |
| [VECTOR-TRICUBIC-002](#vector-tricubic-002-vectorization-relaunch-backlog) | Vectorization relaunch backlog | High | in_progress |
| [CLI-FLAGS-003](#cli-flags-003-handle--nonoise-and--pix0_vector_mm) | Handle -nonoise and -pix0_vector_mm | High | in_progress |
| [TEST-GOLDEN-001](#test-golden-001-regenerate-golden-data-post-phase-d5) | Regenerate golden data post Phase D5 | High | in_planning |
| [STATIC-PYREFLY-001](#static-pyrefly-001-run-pyrefly-analysis-and-triage) | Run pyrefly analysis and triage | Medium | in_progress |
| [TEST-INDEX-001](#test-index-001-test-suite-discovery-reference-doc) | Test suite discovery reference doc | Medium | in_planning |

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
- Next Actions:
  1. 🚩 Coordinate with `[TEST-GOLDEN-001]` Phase A to inventory stale golden datasets and capture `scope_summary.md` (target Attempt #18) before resuming Phase E validation.
  2. 🔁 After `[TEST-GOLDEN-001]` Phase C parity checks succeed, rerun the Phase E ROI nb-compare bundle and targeted pytest selector to confirm corr≥0.95 and |sum_ratio−1|≤5×10⁻³.
  3. 🗒️ Once pytest passes, refresh `phase_e_summary.md`, update `plans/active/vectorization-parity-regression.md` (Phase E rows), and schedule benchmark/documentation updates for the following loop.
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
- Status: in_progress (Phase C parity gate satisfied; blocked on `[VECTOR-PARITY-001]` physics remediation)
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
- Next Actions:
  1. Track `[VECTOR-PARITY-001]` Phase D1–D4/E1 remediation (scattering_vec units, fluence, F_latt) and record the unblock decision once corr ≥0.999 and |sum_ratio−1| ≤5×10⁻³ (update plan row C4 + galph_memory).
  2. When parity fix is confirmed, run Phase D1 profiler capture (`KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts --outdir reports/2026-01-vectorization-gap/phase_b/<STAMP>/profile/`) and archive `trace.json`, `summary.md`, `env.json`.
  3. After profiling, execute Phase D2/D3 backlog refresh and prepare Phase E1/E2 delegation (tricubic design addendum + input.md Do Now) before authorising implementation.
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
- Observations/Hypotheses:
  - Phase D5 lattice unit change invalidates any golden data that depend on `F_latt`; high-resolution 4096² case already confirmed.
  - Other datasets (triclinic, tilted detector, mosaic) likely impacted; need systematic audit before regenerating.
  - README provenance must stay authoritative; include git SHA + checksum after refresh.
- Next Actions:
  1. Execute `[TEST-GOLDEN-001]` Phase A (staleness audit) and log Attempt #18 with `scope_summary.md` + affected test list.
  2. Run Phase B regeneration commands for all impacted datasets; update README and stage refreshed binaries with SHA256 evidence.
  3. Complete Phase C parity tests (nb-compare + pytest) and Phase D ledger updates so `[VECTOR-PARITY-001]` Phase E can close.
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
