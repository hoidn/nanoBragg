# Fix Plan Ledger

**Last Updated:** 2025-10-02 (galph loop T)
**Active Focus:** Protect automation assets, finish nanoBragg hygiene cleanup, restore AT-012 peak matches, and capture authoritative performance evidence for PERF-PYTORCH-004.

## Index
| ID | Title | Priority | Status |
| --- | --- | --- | --- |
| [PROTECTED-ASSETS-001](#protected-assets-001-docsindexmd-safeguard) | Protect docs/index.md assets | Medium | in_progress |
| [REPO-HYGIENE-002](#repo-hygiene-002-restore-canonical-nanobraggc) | Restore canonical nanoBragg.c | Medium | in_progress |
| [PERF-PYTORCH-004](#perf-pytorch-004-fuse-physics-kernels) | Fuse physics kernels | High | in_progress |
| [AT-PARALLEL-012-PEAKMATCH](#at-parallel-012-peakmatch-restore-95-peak-alignment) | Restore 95% peak alignment | High | in_progress |

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
    Observations/Hypotheses: Need to fix multi-source broadcast, hoist ROI/misset tensors (Plan P3.4), add default `source_wavelengths` when missing (Plan P3.0), and correct timing aggregator before trusting new benchmarks.
    Next Actions: Implement plan tasks P2.1–P2.5 (CLI extension, CPU/CUDA runs, Dynamo logs), then P3.0–P3.5 (multi-source defaults, benchmark hardening, ROI caching, C comparison).
- Risks/Assumptions: Requires CUDA availability; must avoid `.item()` in differentiable paths when caching tensors.
- Exit Criteria (quote thresholds from spec):
  * Phase 2 artifacts demonstrating ≥50× warm/cold delta for CPU float64/float32 and CUDA float32 (multi-source included) committed.
  * Phase 3 report showing PyTorch warm runs ≤1.5× C runtime for 256²–1024² detectors.
  * Recorded go/no-go decision for Phase 4 graph work based on Phase 3 results.

---

## [AT-PARALLEL-012-PEAKMATCH] Restore 95% peak alignment
- Spec/AT: specs/spec-a-parallel.md §AT-012 Reference Pattern Correlation (≥95% of top 50 peaks within 0.5 px)
- Priority: High
- Status: in_progress
- Owner/Date: galph/2025-10-02
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
- Risks/Assumptions: Ensure triclinic/tilted variants remain passing; preserve differentiability (no `.item()` in hot path); guard ROI caching vs Protected Assets rule.
- Exit Criteria (quote thresholds from spec):
  * PyTorch run matches ≥48/50 peaks within 0.5 px and maintains corr ≥0.9995.
  * Acceptance test asserts `≥0.95` with supporting artifacts archived under `reports/2025-10-02-AT-012-peakmatch/`.
  * CPU + CUDA parity harness remains green post-fix.

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
