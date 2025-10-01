# Fix Plan Ledger

**Last Updated:** 2025-10-05 (galph loop AM)
**Active Focus:** Protect automation assets, finish nanoBragg hygiene cleanup, restore AT-012 peak matches, correct multi-source physics regressions, and capture authoritative performance evidence for PERF-PYTORCH-004 (CPU+CUDA reruns after physics fixes).

## Index
| ID | Title | Priority | Status |
| --- | --- | --- | --- |
| [GRADIENT-MISSET-001](#gradient-misset-001-fix-misset-gradient-flow) | Fix misset gradient flow | High | done |
| [PROTECTED-ASSETS-001](#protected-assets-001-docsindexmd-safeguard) | Protect docs/index.md assets | Medium | in_progress |
| [REPO-HYGIENE-002](#repo-hygiene-002-restore-canonical-nanobraggc) | Restore canonical nanoBragg.c | Medium | in_progress |
| [PERF-PYTORCH-004](#perf-pytorch-004-fuse-physics-kernels) | Fuse physics kernels | High | in_progress |
| [DTYPE-DEFAULT-001](#dtype-default-001-migrate-default-dtype-to-float32) | Migrate default dtype to float32 | High | in_progress |
| [AT-PARALLEL-012-PEAKMATCH](#at-parallel-012-peakmatch-restore-95-peak-alignment) | Restore 95% peak alignment | High | done |

---

## [GRADIENT-MISSET-001] Fix misset gradient flow
- Spec/AT: arch.md §15 Differentiability Guidelines, Core Implementation Rule #9 (CLAUDE.md)
- Priority: High
- Status: done
- Owner/Date: ralph/2025-09-30
- Reproduction (C & PyTorch):
  * C: n/a (PyTorch-specific gradient correctness issue)
  * PyTorch: `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_crystal_geometry.py::TestCrystalGeometry::test_misset_gradient_flow -v`
  * Shapes/ROI: n/a (gradient test, not image comparison)
- First Divergence (if known): Crystal.compute_cell_tensors line 599 used `torch.tensor(angle, ...)` which breaks gradient flow when angle is already a tensor with requires_grad=True
- Attempts History:
  * [2025-09-30] Attempt #1 — Result: success. Fixed gradient-breaking `torch.tensor()` call by checking if input is already a tensor and using `.to()` instead.
    Metrics: test_misset_gradient_flow PASSED; all 39 core geometry tests pass (2 skipped).
    Artifacts: src/nanobrag_torch/models/crystal.py lines 599-608 (git diff).
    Observations/Hypotheses: The code used `torch.tensor(angle, dtype=..., device=...)` which creates a new tensor without gradients, even when `angle` is already a tensor with `requires_grad=True`. This is a Core Implementation Rule #9 violation. Fix: check `isinstance(angle, torch.Tensor)` and use `.to(dtype=..., device=...)` to preserve gradients.
    Next Actions: None - issue resolved. All gradient tests pass.
- Risks/Assumptions: Ensure all other code paths that accept tensor-or-scalar inputs use similar gradient-preserving patterns.
- Exit Criteria (quote thresholds from spec):
  * test_misset_gradient_flow passes (✅ satisfied).
  * No regressions in crystal/detector geometry tests (✅ 39 passed, 2 skipped).
  * Gradient flow maintained through misset parameters (✅ verified by torch.autograd.gradcheck).

---

## [PROTECTED-ASSETS-001] docs/index.md safeguard
- Spec/AT: Protected assets rule in `CLAUDE.md`; automation guard for files listed in `docs/index.md`
- Priority: Medium
- Status: in_progress
- Owner/Date: galph/2025-09-30
- Reproduction (C & PyTorch):
  * C: n/a (documentation/policy enforcement)
  * PyTorch: n/a
  * Shapes/ROI: n/a
- First Divergence (if known): n/a — policy task
- Attempts History:
  * [2025-09-30] Attempt #1 — Result: partial. Added Protected Assets rule to `CLAUDE.md` and marked `loop.sh` as protected in `docs/index.md`; plan still needs to ensure hygiene checklists reference the rule.
    Metrics: n/a
    Artifacts: CLAUDE.md, docs/index.md (git history).
    Observations/Hypotheses: Hygiene plans must require a docs/index.md scan before deletions; Ralph previously removed `loop.sh` during cleanup because this guard was missing.
    Next Actions: Update `plans/active/repo-hygiene-002/plan.md` task H4 guidance to reference Protected Assets, then verify the checklist is followed in the next hygiene pass.
- Risks/Assumptions: Future cleanup scripts must fail-safe against removing listed assets; ensure supervisor prompts reinforce this rule.
- Exit Criteria (quote thresholds from spec):
  * CLAUDE.md and docs/index.md enumerate the rule (✅ already satisfied).
  * Every hygiene-focused plan (e.g., REPO-HYGIENE-002) explicitly checks docs/index.md before deletions.
  * Verification log links demonstrating the rule was honored during the next hygiene loop.

---

## [REPO-HYGIENE-002] Restore canonical nanoBragg.c
- Spec/AT: Repository hygiene SOP (`docs/development/processes.xml` §C-parity) & commit 92ac528 regression follow-up
- Priority: Medium
- Status: in_progress
- Owner/Date: galph/2025-09-30
- Reproduction (C & PyTorch):
  * C: `git show 92ac528^:golden_suite_generator/nanoBragg.c > /tmp/nanoBragg.c.ref`
  * PyTorch: `env KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_parity_matrix.py -k "AT-PARALLEL-021 or AT-PARALLEL-024"`
  * Shapes/ROI: 1024×1024 detector, pixel 0.1 mm, full-frame ROI
- First Divergence (if known): n/a — hygiene task
- Attempts History:
  * [2025-09-30] Attempt #1 — Result: partial. Removed nested `golden_suite_generator/golden_suite_generator/` directory and archived `reports/2025-09-30-AT-021-traces`, but deleted `loop.sh` (a protected asset) before the rule existed; item reopened.
    Metrics: AT-021/024 parity corr=1.0; parity run 20.38 s.
    Artifacts: reports/archive/2025-09-30-AT-021-traces/
    Observations/Hypotheses: Need to restore canonical `nanoBragg.c` from 92ac528^ and execute plan tasks H1–H6 without touching protected assets.
    Next Actions: Complete plan H1–H6 (baseline snapshot, restore canonical file, purge stray reports, rerun parity smoke tests, log closure).
- Risks/Assumptions: Ensure Protected Assets guard is honored before deleting files; parity harness must remain green after cleanup.
- Exit Criteria (quote thresholds from spec):
  * Canonical `golden_suite_generator/nanoBragg.c` matches 92ac528^ exactly (byte-identical).
  * Reports from 2025-09-30 relocated under `reports/archive/`.
  * `NB_RUN_PARALLEL=1` parity smoke (`AT-PARALLEL-021`, `AT-PARALLEL-024`) passes without diff.

---

## [PERF-PYTORCH-004] Fuse physics kernels
- Spec/AT: PERF-PYTORCH-004 roadmap (`plans/active/perf-pytorch-compile-refactor/plan.md`), docs/architecture/pytorch_design.md §§2.4, 3.1–3.3
- Priority: High
- Status: in_progress
- Owner/Date: galph/2025-09-30
- Reproduction (C & PyTorch):
  * C: `NB_C_BIN=./golden_suite_generator/nanoBragg python scripts/benchmarks/benchmark_detailed.py --sizes 256,512,1024 --device cpu --iterations 2`
  * PyTorch: `env KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/investigate_compile_cache.py --instances 5 --size 256 --devices cpu,cuda --dtypes float64,float32 --sources 1`
  * Shapes/ROI: 256²–1024² detectors, pixel 0.1 mm, oversample 1, full-frame ROI
- First Divergence (if known): Multi-source expansion failure at `compute_physics_for_position` broadcast (src/nanobrag_torch/simulator.py:109-135) when `sources>1`
- Attempts History:
  * [2025-10-01] Attempt #4 — Result: success (Phase 0/1 complete). Refactored to pure function + hoisted guard tensors; torch.compile caching delivers ≥37× warm/cold speedup.
    Metrics: CPU float64 warm/cold 37.09×; CPU float32 1485.90×; CUDA float32 1256.03×; warm setup <50 ms.
    Artifacts: reports/benchmarks/20250930-165726-compile-cache/cache_validation_summary.json; reports/benchmarks/20250930-165757-compile-cache/cache_validation_summary.json.
    Observations/Hypotheses: Built-in caching sufficient; explicit cache unnecessary post refactor.
    Next Actions: Proceed to Phase 2 multi-device validation.
  * [2025-10-02] Attempt #5 — Result: partial diagnostic. Multi-source configs crash (`expand`: shape mismatch); `benchmark_detailed.py` divides by zero when warm setup=0 and adds boolean `cache_hit` into totals.
    Metrics: N/A (runs aborted on expand error).
    Artifacts: pending — rerun `investigate_compile_cache.py` with `TORCH_LOGS=dynamic` once broadcast fix lands; record logs under `reports/benchmarks/<date>-compile-cache/`.
    Observations/Hypotheses: Need to fix multi-source broadcast, hoist ROI/misset tensors (Plan P3.4), add default `source_wavelengths` when missing (Plan P3.0), ensure polarization uses per-source incident directions before the sum (Plan P3.0b), restore multi-source normalization so intensities sum rather than average (Plan P3.0c), and correct timing aggregator before trusting new benchmarks.
    Next Actions: Implement plan tasks P2.1–P2.5 (CLI extension, CPU/CUDA runs, Dynamo logs), then P3.0/P3.0b/P3.0c–P3.5 (multi-source defaults + polarization + normalization, benchmark hardening, ROI caching, C comparison).
  * [2025-09-30] Attempt #6 — Result: P3.0 complete, P3.0b blocker discovered. Fixed multi-source broadcast dimension handling; multi-source execution now stable (258.98× cache speedup). Discovered architectural issue: polarization calculation uses global `self.incident_beam_direction` instead of per-source incident directions.
    Metrics: Multi-source benchmark (n_sources=3, 256², cpu): 258.98× warm/cold speedup; AT-012: 3/4 passed.
    Artifacts: reports/benchmarks/20250930-180237-compile-cache/cache_validation_summary.json; commits 2c90a99, 1778a6b.
    Observations/Hypotheses: P3.0 complete — source defaults work correctly. P3.0b blocked by polarization issue at simulator.py:813 (oversample path) and :934 (no-oversample path). Both paths use `self.incident_beam_direction` (global) instead of per-source `incident_dirs_batched`. Multi-source runs compute incorrect polarization factors. Fix requires either (1) passing `incident_dirs_batched` to polarization in multi-source branch, or (2) moving polarization inside `compute_physics_for_position`.
    Next Actions: Fix P3.0b by refactoring polarization to use per-source incident directions; recommend approach (1) for minimal disruption. Then proceed to P3.0c normalization verification.
  * [2025-09-30] Attempt #7 — Result: failed (approximation only). Commit `fcbb93a` still reuses the primary source vector for polarization so secondary sources remain unpolarized; physics diverges from nanoBragg.c despite the reported speedups.
    Metrics: Multi-source benchmark (n_sources=3, 256², cpu): 13.13× warm/cold speedup (recorded, but not evidence of correctness).
    Artifacts: reports/benchmarks/20250930-181916-compile-cache/cache_validation_summary.json.
    Observations/Hypotheses: Need to push polarization inside the per-source accumulation (plan task P3.0b) so each source applies its own Kahn factor before reduction.
    Next Actions: Re-open P3.0b and validate against C traces (`scripts/debug_pixel_trace.py` vs instrumented nanoBragg.c) for a 3-source configuration.
  * [2025-09-30] Attempt #8 — Result: failed. Commit `904dc9b` hardened the benchmark script but left simulator normalization untouched; `steps` still divides by `source_weights.sum()` and the `.to()` crash remains when wavelengths/weights are None.
    Metrics: N/A (no physics validation executed).
    Artifacts: reports/benchmarks/20250930-184006/ (benchmark CLI run) — confirms script changes only.
    Observations/Hypotheses: Tasks P3.0–P3.0c remain unresolved; documentation overstated completion.
    Next Actions: Restore truthful status in plan and implement fallback seeding, per-source polarization, and proper normalization before gathering new benchmarks.
  * [2025-09-30] Attempt #9 — Result: invalid partial benchmark. Ralph ran P3.2/P3.3 despite P3.0–P3.0c remaining open; recordings kept for reference but cannot be trusted until multi-source physics is fixed.
    Metrics: CPU — 256²: 2.12× faster, 512²: 1.6× slower, 1024²: 2.3× slower; CUDA — 256²: 1.51× faster, 512²: 1.50× faster, 1024²: 2.40× faster.
    Artifacts: reports/benchmarks/20250930-184744/ (CPU), reports/benchmarks/20250930-184803/ (CUDA).
    Observations/Hypotheses: Because beam defaults/polarization/normalization are wrong, these benchmarks should be discarded once parity is restored; redo after P3.0–P3.0c succeed and ROI caching (P3.4) lands.
    Next Actions: Block further benchmarking until physics parity passes; revisit these measurements after completing P3.0–P3.0c and P3.4.
  * [2025-10-04] Attempt #10 — Result: supervisor audit; reopened P3.0–P3.0c and updated the active plan to reflect outstanding work. No code changes yet.
    Metrics: Analysis only.
    Artifacts: plans/active/perf-pytorch-compile-refactor/plan.md (revised), galph_memory.md 2025-10-04 entry.
    Observations/Hypotheses: Simulator still crashes when `source_wavelengths=None`, still reuses the primary source direction for polarization, and still averages intensities via `steps`.
    Next Actions: Ralph to execute plan tasks P3.0–P3.0c in order, capture multi-source trace comparisons, then proceed to benchmarking tasks once physics parity is restored.
  * [2025-10-05] Attempt #11 — Result: supervisor audit; synchronized plan/fix_plan statuses with outstanding CPU deficits. Marked P3.2/P3.3 as in-progress (baseline only) and deferred P3.5 decision until fresh benchmarks meet ≤1.5× criteria after P3.0–P3.4 land.
    Metrics: Analysis only (no new runs).
    Artifacts: plans/active/perf-pytorch-compile-refactor/plan.md (Phase 3 table updated), galph_memory.md 2025-10-05 entry.
    Observations/Hypotheses: Benchmark data collected under Attempt #9 remain valid only as "before" baselines; reruns must wait until multi-source defaults/polarization/normalization and ROI caching are fixed.
    Next Actions: Ralph to finish P3.0–P3.4, then rerun CPU/CUDA benchmarks and produce the Phase 3 summary per plan guidance before reconsidering Phase 4.
- Risks/Assumptions: Requires CUDA availability; must avoid `.item()` in differentiable paths when caching tensors.
- Exit Criteria (quote thresholds from spec):
  * Phase 2 artifacts demonstrating ≥50× warm/cold delta for CPU float64/float32 and CUDA float32 (multi-source included) committed.
  * Phase 3 report showing PyTorch warm runs ≤1.5× C runtime for 256²–1024² detectors.
  * Recorded go/no-go decision for Phase 4 graph work based on Phase 3 results.

---

## [AT-PARALLEL-012-PEAKMATCH] Restore 95% peak alignment
- Spec/AT: specs/spec-a-parallel.md §AT-012 Reference Pattern Correlation (≥95% of top 50 peaks within 0.5 px)
- Priority: High
- Status: done
- Owner/Date: galph/2025-09-30
- Reproduction (C & PyTorch):
  * C: `NB_C_BIN=./golden_suite_generator/nanoBragg -lambda 6.2 -cell 100 100 100 90 90 90 -default_F 100 -distance 100 -detpixels 1024 -floatfile c_simple_cubic.bin`
  * PyTorch: `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_simple_cubic_correlation -vv`
  * Shapes/ROI: 1024×1024 detector, pixel 0.1 mm, oversample auto (currently 1×), full-frame ROI
- First Divergence (if known): Not yet fully localized — suspected ROI mask zeroing & intensity scaling at `src/nanobrag_torch/simulator.py:586-603` / `:950-979`; float64 peak detection drops plateau maxima vs float32/golden outputs.
- Attempts History:
  * [2025-10-02] Attempt #1 — Result: failed. Correlation 0.9999999999999997 but only 43/50 peaks matched (86%) vs ≥95% requirement.
    Metrics: corr=1.0; matches=43/50; unmatched peaks on outer ring.
    Artifacts: baseline metrics pending under `reports/2025-10-02-AT-012-peakmatch/` (to capture during Plan Phase A).
    Observations/Hypotheses: ROI mask rebuilt each run; mask dtype casts may zero faint peaks; per-run tensor fabrication in simulator likely contributing.
    Next Actions: Execute Plan Phase A (baseline artifacts), then Phase B (trace missing peak via `scripts/debug_pixel_trace.py`).
  * [2025-10-02] Attempt #2 — Result: diagnostic. Casting PyTorch image to float32 prior to `find_peaks` returns 50/50 matched peaks (0.0 px mean delta); float64 path returns 45 peaks (43 matched).
    Metrics: corr=1.0; float64 matches=43/50; float32 matches=50/50.
    Artifacts: ad-hoc reproduction; formalize under `reports/2025-10-02-AT-012-peakmatch/` during Plan Phase A.
    Observations/Hypotheses: Double-precision rounding drops plateau duplicates at beam center; aligning dtype or peak tolerance may resolve without physics changes.
    Next Actions: Plan Phase B4 (dtype sensitivity), capture traces, then decide whether to quantize outputs or adjust matcher before tightening the assertion.
  * [2025-09-30] Attempt #3 — Result: PASS. Fixed peak detection by casting PyTorch output to float32 to match golden data precision.
    Metrics: simple_cubic: corr=1.0, matches=50/50 (100%), mean_dist=0.0px; triclinic_P1: PASS; cubic_tilted: PASS.
    Artifacts: reports/2025-09-30-AT-012-peakmatch/final_summary.json, reports/2025-09-30-AT-012-peakmatch/peak_detection_summary.json
    First Divergence: Not a physics divergence — float64 precision breaks plateau ties. Golden C output (float32) has 8 unique peak values creating plateaus. PyTorch float64 has 38 unique values due to numerical noise, causing scipy.ndimage.maximum_filter to find 45 local maxima instead of 52.
    Solution: Cast pytorch_image.astype(np.float32) before find_peaks() in all three test methods. This matches golden data precision and restores plateau ties, achieving 50/50 peak matches (100%) vs spec requirement of 48/50 (95%).
    Next Actions: None — AT-PARALLEL-012 complete and passing. Plan archived at `plans/archive/at-parallel-012-peakmatch/plan.md`; assertions tightened to ≥95%.
- Risks/Assumptions: Ensure triclinic/tilted variants remain passing; preserve differentiability (no `.item()` in hot path); guard ROI caching vs Protected Assets rule.
- Exit Criteria (quote thresholds from spec):
  * PyTorch run matches ≥48/50 peaks within 0.5 px and maintains corr ≥0.9995.
  * Acceptance test asserts `≥0.95` with supporting artifacts archived under `reports/2025-10-02-AT-012-peakmatch/`.
  * CPU + CUDA parity harness remains green post-fix.

---

## [DTYPE-DEFAULT-001] Migrate default dtype to float32
- Spec/AT: `arch.md` (Implementation Architecture header), prompts long-term goal (fp32 default), `docs/development/pytorch_runtime_checklist.md` §1.4
- Priority: High
- Status: in_progress
- Owner/Date: galph/2025-10-04 (execution by ralph)
- Reproduction (C & PyTorch):
  * Inventory: `rg "float64" src/nanobrag_torch -n`
  * Baseline simulator import: `python -c "from nanobrag_torch.simulator import Simulator"`
  * Smoke test: `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_parallel_012.py -vv`
- First Divergence (if known): AT-PARALLEL-012 plateau matching regressed to 43/50 peaks when running fully in float32 (prior float64→float32 cast path delivered 50/50).
- Attempts History:
  * [2025-09-30] Attempt #1 — Result: partial (Phase A+B complete; Phase C blocked by AT-012 regression). Catalogued 37 float64 occurrences and flipped defaults to float32 across CLI, Crystal/Detector/Simulator constructors, HKL readers, and auto-selection helpers while preserving float64 for Fdump binary format and gradcheck overrides. Metrics: CLI smoke test PASS; AT-012 correlation remains ≥0.9995 yet peak matching falls to 43/50 (needs ≥48/50). Artifacts: reports/DTYPE-DEFAULT-001/{inventory.md, proposed_doc_changes.md, phase_b_summary.md}; commit 8c2ceb4. Observations/Hypotheses: Native float32 plateau rounding differs from the float64→float32 cast path, so `scipy.ndimage` peak detection drops ties. Next Actions: debug AT-012 plateau behaviour (log correlations, inspect plateau pixels, decide on detector/matcher tweak), finish remaining B3 helper dtype plumbing (`io/source.py`, `utils/noise.py`, `utils/c_random.py`), then rerun Tier-1 suite on CPU+CUDA once peak matching is restored.
- Plan Reference: `plans/active/dtype-default-fp32/plan.md` (Phase A complete, Phase B `[P]`).
- Risks/Assumptions: Must preserve float64 gradcheck path; documentation currently states float64 defaults; small value shifts must stay within existing tolerances and acceptance comparisons.
- Exit Criteria (quote thresholds from spec):
  * Default simulator/config dtype switches to float32 and is documented in `arch.md` and runtime checklist.
  * Tier-1/Tier-2 acceptance suites pass on CPU & CUDA with float32 defaults.
  * Benchmarks under `reports/DTYPE-DEFAULT-001/` show ≤5 % regression vs previous float64 baseline.

---

### Completed Items — Key Reference
(See `docs/fix_plan_archive.md` for the full historical ledger.)

## [ROUTING-LOOP-001] loop.sh routing guard
- Spec/AT: Prompt routing rules (prompts/meta.md)
- Priority: High
- Status: done
- Owner/Date: galph/2025-10-01
- Reproduction (C & PyTorch):
  * C: `sed -n '1,40p' loop.sh`
  * PyTorch: n/a
  * Shapes/ROI: n/a
- First Divergence (if known): n/a — automation task
- Attempts History:
  * [2025-10-01] Attempt #1 — Result: success. `loop.sh` now runs a single `git pull` and invokes `prompts/debug.md` only; verification captured in `reports/routing/2025-10-01-loop-verify.txt`.
    Metrics: n/a
    Artifacts: reports/routing/2025-10-01-loop-verify.txt
    Observations/Hypotheses: Guard prevents Ralph from re-entering prompts/main.md while parity tests fail.
    Next Actions: Monitor automation once AT suite is fully green before permitting main prompt.
- Risks/Assumptions: Ensure future automation edits maintain routing guard.
- Exit Criteria (quote thresholds from spec): ✅ script executes debug prompt only; verification recorded (satisfied).

## [AT-PARALLEL-024-REGRESSION] PERF-PYTORCH-004 Test Compatibility
- Spec/AT: AT-PARALLEL-024 `test_umat2misset_round_trip`
- Priority: High
- Status: done
- Owner/Date: galph/2025-10-01
- Reproduction (C & PyTorch):
  * C: n/a (Python-only acceptance test)
  * PyTorch: `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_parallel_024.py::TestAT_PARALLEL_024::test_umat2misset_round_trip -v`
  * Shapes/ROI: 1024×1024 detector, MOSFLM convention
- First Divergence (if known): AttributeError (`float` lacks `.dtype`) at `geometry.py:196`
- Attempts History:
  * [2025-10-01] Attempt #1 — Result: success. Converted scalar inputs/outputs to tensors; restored compatibility after Phase 1 tensor hoisting.
    Metrics: AT-024 tests 6/6 passed; AT-PARALLEL suite 78 passed, 48 skipped.
    Artifacts: pytest log 2025-10-01 (not archived).
    Observations/Hypotheses: Phase 1 optimizations removed scalar fallbacks; tests must pass tensors going forward.
    Next Actions: None; continue PERF-PYTORCH-004 Phase 2 work.
- Risks/Assumptions: Maintain tensor inputs for geometry helpers.
- Exit Criteria: ✅ All AT-024 tests pass post tensor conversion.

## [PERF-PYTORCH-004-PHASE2] Cross-instance cache validation
- Spec/AT: PERF-PYTORCH-004 Phase 2 (plan P2.1–P2.4)
- Priority: High
- Status: done
- Owner/Date: galph/2025-09-30
- Reproduction (C & PyTorch):
  * C: n/a (analysis script compares simulator instances)
  * PyTorch: `env KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/investigate_compile_cache.py --instances 5 --size 256 --devices cpu,cuda --dtypes float64,float32 --sources 1`
  * Shapes/ROI: 256×256 detector, oversample 1, single source
- First Divergence (if known): n/a — benchmark task
- Attempts History:
  * [2025-09-30] Attempt #1 — Result: success. Extended CLI, generated JSON summaries, confirmed torch.compile cache hits across CPU/CUDA.
    Metrics: CPU float64 37.09×, CPU float32 1485.90×, CUDA float32 1256.03× warm/cold speedups; mean 761.49×.
    Artifacts: reports/benchmarks/20250930-165726-compile-cache/cache_validation_summary.json; reports/benchmarks/20250930-165757-compile-cache/cache_validation_summary.json.
    Observations/Hypotheses: Built-in caching sufficient; multi-source coverage deferred pending broadcast fix.
    Next Actions: Move to steady-state benchmarking (Phase 3).
- Risks/Assumptions: Multi-source broadcast still broken; revisit once fixed.
- Exit Criteria: ✅ Phase 2 artifact set captured and documented.

## [AT-PARALLEL-012] Triclinic P1 correlation failure
- Spec/AT: AT-PARALLEL-012 triclinic variant (Core Rule #13 metric duality)
- Priority: High
- Status: done
- Owner/Date: galph/2025-09-30
- Reproduction (C & PyTorch):
  * C: `NB_C_BIN=./golden_suite_generator/nanoBragg -lambda 6.2 -cell 83 91 97 89 92 94 -default_F 100 -distance 100 -detpixels 256 -floatfile triclinic.bin`
  * PyTorch: `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_parallel_012.py::TestATParallel012Triclinic::test_triclinic_p1 -vv`
  * Shapes/ROI: 256×256 detector, pixel 0.1 mm, triclinic cell
- First Divergence (if known): Metric duality violation (V_actual vs formula volume) at `Crystal.compute_cell_tensors`
- Attempts History:
  * [2025-09-30] Attempt #16 — Result: success. Restored Core Rule #13 exact duality (V_actual) and tightened tolerances back to 1e-12.
    Metrics: corr≈0.99963; metric duality matches within 1e-12.
    Artifacts: reports/2025-09-30-AT-012-debug/ (rotation traces).
    Observations/Hypotheses: Formula-volume shortcut caused 0.9658 correlation; V_actual fix resolves.
    Next Actions: Monitor while peak-match work proceeds.
- Risks/Assumptions: Keep V_actual path covered by regression tests.
- Exit Criteria: ✅ triclinic corr≥0.9995 with metric duality ≤1e-12.

---

### Archive
For additional historical entries (AT-PARALLEL-020, AT-PARALLEL-024 parity, early PERF fixes, routing escalation log), see `docs/fix_plan_archive.md`.
