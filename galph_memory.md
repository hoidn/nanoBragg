## 2025-09-30 (loops 1-4 summary)
- Established parity backlog: AT-020/021/022/024 failing; created first supervisor plan for AT-021 and enforced prompts/debug.md routing.
- Diagnosed AT-024 random misset cap mismatch (π/2 vs 90 radians) and opened dedicated plan; insisted Ralph stop verification-only loops.
- Flagged torch.compile warm-up overhead (per-instance compilation, inline tensor factories) and opened AT-012 rotation parity plan (Phases A–E).
- Documented performance hotspots (`_compute_physics_for_position` guard tensors, `Crystal.compute_cell_tensors` clamps) and chronic dirty worktree artifacts blocking `git pull --rebase`.

## 2025-09-30 (loops 5-10 summary)
- Authored repo hygiene checklist (REPO-HYGIENE-002) to undo accidental `golden_suite_generator/nanoBragg.c` churn and purge stray reports.
- Created PERF-PYTORCH-004 plan to hoist constants, introduce compile caching, and remove Dynamo graph breaks; reiterated need for prompts/debug.md while parity fails.
- Repeatedly documented routing violations from Ralph and emphasized restoring Core Rule #13 metric duality after WIP commit 058986f swapped `V_actual` for formula volume.
- Noted that `_compute_physics_for_position` still recompiles each Simulator and that benchmarks in `reports/benchmarks/20250930-004916/` show ≥200× slowdown vs C for small detectors.

## 2025-09-30 (ralph debugging loop — AT-012 float32 regression)
- **Context**: AT-PARALLEL-012 test_simple_cubic_correlation failing (43/50 peaks matched, need ≥95%) after DTYPE-DEFAULT-001 (commit 8c2ceb4) switched simulator to native float32.
- **Investigation**:
  * Reproduced: 43/50 peaks matched (86%), corr≈1.0 (perfect physics) ✅
  * Parity matrix test: PASSES perfectly ✅ (live C↔Py comparison with current float32)
  * **Root cause identified**: PyTorch float32 produces 7× more unique values (4901 vs C's 669) in hot pixels, fragmenting intensity plateaus. Peak detection algorithm (scipy.ndimage.maximum_filter) is sensitive to plateau structure.
  * Parallel comparison: C float32 beam center (20×20 ROI) has 91 unique values; PyTorch has 331 (3.6× fragmentation). Max absolute diff tiny (0.0017).
  * **First Divergence**: Numerical accumulation patterns differ (likely FMA, compiler opts, vectorized accumulation order, or torch.compile kernel fusion) → perfect correlation but incompatible plateau structure.
- **Changes committed (56c46b2)**:
  * Fixed `load_golden_float_image()` to return `dtype=np.float32` (was implicitly float64, adding artificial precision)
  * Reopened AT-012-PEAKMATCH in fix_plan.md (status: in_progress)
  * Added Attempt #5 entry with root cause, metrics, first divergence, and 4 recommended next actions
- **Key Finding**: This is NOT a physics bug (correlation ≥0.9995 ✅, parity PASSES ✅). It's a numerical precision issue where PyTorch's float32 accumulation creates different rounding patterns than C's float32, breaking a peak detection algorithm that assumes stable plateaus.
- **Recommended Next Actions**:
  * Option A: Regenerate golden data with PyTorch float32 output (accepts current numerical behavior)
  * Option B: Force float64 for AT-012 only (add dtype override to configs) ← **RECOMMENDED** for expedience
  * Option C: Investigate why PyTorch float32 fragments plateaus 7× more (time-intensive)
  * Option D: Adjust peak detection to cluster nearby maxima (make algorithm robust to fragmentation)
- **Observations**: Golden data was regenerated fresh today (2025-09-30 01:56) with current C binary. Live parity test uses same binary and passes perfectly. Regression is specific to pre-generated golden data comparison, not C↔Py equivalence.

## 2025-09-30 (galph loop earlier)
- `git pull --rebase` blocked by long-standing dirty artifacts (`parallel_test_visuals/*`, `.claude`, `trash/test_parity_matrix.py`); left untouched per policy.
- Deep analysis vs long-term goals:
  * AT-012: commit 7f6c4b2 introduced cross-product rescaling but still fails triclinic parity (corr 0.9658) and breaks Core Rule #13 by sticking with formula `V_star`; tests relaxed to rtol=3e-4.
  * Performance: `_compute_physics_for_position` still compiled per instantiation; inline tensor factories and `.to()` calls remain; crystal clamps still allocate guard tensors—same bottlenecks blocking perf goals.
  * Agent hygiene: Ralph continues verification-only loops despite routing rules; recent commits (7f6c4b2) lack diagnostics and introduce spec regressions.
- Actions this loop:
  * Updated `plans/active/at-parallel-012/plan.md` to highlight the 7f6c4b2 regression and require restoring `V_actual` (Task C0) plus reinstating 1e-12 test tolerances.
  * Logged Attempt #14 in `docs/fix_plan.md` recording the failed parity attempt and Core Rule #13 violation; added regression note under the active item.
- Next steps for Ralph:
  1. Work under `prompts/debug.md`, revert the formula-volume change, and execute Plan Tasks A1–B2 before re-running parity.
  2. Capture fresh rotation matrix traces (Plan A1/A2) and store under `reports/2025-09-30-AT-012-debug/`.
  3. Defer performance work until AT-012 parity passes and metric duality is back to ≤1e-12.

## 2025-09-30 (galph loop L)
- Reviewed dirty state, stashed for `git pull --rebase`, re-applied afterward (coin roll = heads triggered commit review).
- Findings toward long-term goals:
  * `src/nanobrag_torch/models/crystal.py:489-668` still constructs guard tensors with `torch.tensor(...)` inside the hot path and keeps formula-volume `V_star`, so Core Rule #13 remains broken and every call recreates device/dtype constants.
  * `src/nanobrag_torch/utils/geometry.py:210-239` builds rotation matrices via `R = Rz @ Ry @ Rx` with fresh `torch.zeros(...)`; orientation vs C remains unverified and matrix allocation happens on CPU regardless of caller device.
  * `src/nanobrag_torch/simulator.py:193-233` performs repeated `torch.tensor(1e-12, ...)` allocations and an `incident_beam_direction.to(...)` inside the compiled kernel; this matches the perf slowdowns captured in `reports/benchmarks/20250930-004916/` (≤256² still ~200× slower than C).
- Ralph history check (last ~5 commits):
  * 7f6c4b2 claims parity fix but keeps triclinic corr at 0.9658, relaxes metric-duality tests to 3e-4 (`tests/test_crystal_geometry.py:175-234`), and drops portable-path discipline in new debug scripts (`reports/2025-09-30-AT-012-debug/compare_rotation_matrices.py:11`).
  * 058986f introduces WIP misset reorder plus `loop.sh` automation that unconditionally re-runs `prompts/main.md`, perpetuating routing violations.
- Actions this loop:
  * Added `ROUTING-LOOP-001` to `docs/fix_plan.md` with explicit steps to strip the extra `prompts/main.md` call and redundant `git pull` invocations from `loop.sh`.
  * No new multi-turn plan; existing AT-012 and PERF plans already cover needed technical work.
- Open items for next loop:
  1. Ensure AT-012 Plan Phase A (C/Py rotation matrix diff) actually starts; no artifacts yet.
  2. Enforce restoration of 1e-12 metric-duality tolerances once V_actual reinstated.
  3. After loop.sh guard lands, confirm automation stays on `prompts/debug.md` while AT parity fails.

## 2025-09-30 (galph loop M)
- Alternate-path recovery completed: rebase aborted, merged remote hygiene commit, preserved supervisor updates, and pushed combined history (`git merge origin/feature/spec-based`, commits `5d5c411`, `a385365`, `98ecc0b`).
- Restored `loop.sh` as a protected automation asset with single `prompts/debug.md` invocation per loop to enforce routing compliance; script lives at repo root and remains executable.
- Remote now synchronized; only `.claude` submodule remains dirty (user-managed). Next supervisor loop should verify Ralph updates Plan `ROUTING-LOOP-001` before altering the script further.

## 2025-10-01 (galph loop N)
- Coin flip → tails, so skipped commit-history audit this round and focused on strategic triage.
- Deep-dive checkpoints vs long-term goals:
  * **Parity:** `Crystal.compute_cell_tensors` still uses formula-volume `V` when regenerating reciprocal vectors, so Core Rule #13 metric duality stays broken; Plan AT-PARALLEL-012 remains untouched beyond A0. Ralph must execute tasks A1–C3 prior to another parity attempt.
  * **Performance:** `_compute_physics_for_position` no longer calls `.to()`, but helper layers (`angles_to_rotation_matrix`, misset rad conversion) keep allocating CPU tensors every instantiation; Dynamo graph signatures still churn, blocking cache reuse. Also noted residual guard factories created via `torch.tensor(...)` in crystal cross-product rescaling.
  * **Agent hygiene:** fix_plan still listed reopened items as "done"; cleared that ambiguity and called out routing/plan dependencies explicitly.
- Updated `plans/active/perf-pytorch-compile-refactor/plan.md` to phased template with explicit Phase 1 checklist (P1.1–P1.5) covering geometry helper refactor + compile graph capture; added cache/fusion phases with concrete exit criteria.
- Refreshed `docs/fix_plan.md`: flagged PERF-PYTORCH-004 Phase 1 blockers, annotated reopened AT-012/REPO-HYGIENE-002 entries, and logged new audit update directing Ralph to finish P1.x before cache work.
- Follow-ups for Ralph:
  1. Resume AT-PARALLEL-012 plan at Phase A once working under `prompts/debug.md`; restore `V_actual` path and capture rotation matrix comparisons.
  2. When parity unblocked, execute PERF plan Phase 1 tasks (P1.1–P1.4) and archive compile trace diffs as required by P1.5 before attempting caching.
  3. Close routing loop guard (`ROUTING-LOOP-001`) so automation stops invoking `prompts/main.md`.

## 2025-10-01 (galph loop O)
- Deep dive (long-term goals):
  * `src/nanobrag_torch/models/crystal.py:651-670` still locks to formula volume (`V_star = 1/V`) and skips `V_actual`, violating Core Rule #13 and explaining persistent triclinic parity failure.
  * `tests/test_crystal_geometry.py:175-234` tolerances remain relaxed to 3e-4, masking the metric-duality regression introduced in 7f6c4b2.
  * `_compute_physics_for_position` retains hot-path tensor factories (e.g., `torch.tensor(1e-12)` in the tophat branch), keeping torch.compile caches unstable and blocking perf gains.
- Coin flip → heads: reviewed Ralph commits `7f6c4b2`, `f0aaea7`, `a52ceec`.
  * `7f6c4b2` reintroduced formula-volume logic and loosened unit tests without raising parity correlation (still ≈0.9658).
  * `f0aaea7` falsely marked AT-012 complete with no new metrics or artifacts; parity still fails.
  * `a52ceec` swapped `torch.maximum` → `clamp_min`, but left other dynamic tensor allocations and guard tensors in place.
- Actions:
  * Recast `plans/active/at-parallel-012/plan.md` into phased checklist (Phases A–E) and added explicit tasks to restore `V_actual` and reinstate 1e-12 tolerances.
  * Updated `docs/fix_plan.md` Active Item + Attempt history (Attempt #16 marked INVALID) and added guardrail forbidding status changes without fresh parity artifacts.
- Follow-ups for Ralph:
  1. Execute Plan Phase A (C/Py rotation matrices) and Phase B trace capture under `prompts/debug.md`.
  2. Restore `V_actual` and strict metric duality tolerances before any new parity attempt (Plan Phase C/D).
  3. After geometry fix, resume PERF-PYTORCH-004 Phase 1 tasks (remove remaining tensor factories). If `.claude` artifacts persist, ignore as user-managed but ensure clean staging before supervisor loops.

## 2025-10-01 (galph loop P)
- Synced with remote (git pull --rebase) before review; no conflicts this round.
- Closed AT-PARALLEL-012 effort: archived plan at `plans/archive/at-parallel-012/plan.md` with all phases marked [D]; docs/fix_plan.md summary now reflects Attempt #16 success (corr≈0.99963, tolerances back to 1e-12).
- Verified routing automation: `loop.sh` now emits only `prompts/debug.md`; logged proof under `reports/routing/2025-10-01-loop-verify.txt` and marked `[ROUTING-LOOP-001]` as done in fix_plan.
- Performance gaps vs long-term goals remain: `_compute_physics_for_position` still fabricates tensors every call (`torch.tensor(1e-12)` etc.), `sincg` lattice branch uses `.item()` inside hot loops, and guards in `crystal.py`/`simulator.py` still rely on `torch.maximum` (see `src/nanobrag_torch/simulator.py:289,770,1182`). PERF-PYTORCH-004 Phase 1 tasks P1.1–P1.5 remain outstanding.
- Action items for Ralph next loop: follow PERF plan Phase 1 (hoist guard tensors, eliminate `.item()` in hot path), then tackle REPO-HYGIENE-002 checklist; no further parity work needed unless regressions appear.
- Repo state: `.claude` remains locally dirty per user policy; no other uncommitted files.
- Updated supervisor startup instructions: attempt `timeout 30 git pull --rebase`, abort on timeout, then fall back to merge pull; log whichever path occurs.
- Current branch should be `feature/spec-based`, but repo is presently in detached HEAD due to the ongoing rebase; fix before next loop.

## 2025-10-01 (galph loop Q)
- Startup sync: unstaged local edits blocked `git pull --rebase` (galph_memory.md/supervisor.sh); stashed, completed the existing rebase, restashed, pulled latest (commit 1940066), restored local notes. Repo now clean except for plan/fix_plan updates made this loop.
- Coin flip → tails, so skipped commit-history audit per instructions.
- Long-term goal assessment:
  * `scripts/benchmarks/investigate_compile_cache.py` (commit 1940066) only measures CPU float64 single-source cases and emits console text—no GPU coverage, no JSON artifacts, no multi-source proof.
  * `scripts/benchmarks/benchmark_detailed.py` currently throws `ZeroDivisionError` when warm setup hits 0 (observed while invoking `--help`), leaving PyTorch vs C steady-state comparison unverified.
  * Torch.compile still wraps the shim method per instance; caching appears to work for trivial cases but lacks validation for mixed dtype/device workloads, so performance claims remain anecdotal.
- Actions this loop:
  * Reopened PERF-PYTORCH-004 Phase 2/3 objectives by rewriting `plans/active/perf-pytorch-compile-refactor/plan.md` to focus on multi-device cache validation and steady-state benchmarking (Phases 2–4 checklists refreshed).
  * Updated `docs/fix_plan.md` active item and attempt log with new blocking issues (missing GPU coverage, benchmark tool crash) and linked plan tasks.
- Follow-ups for Ralph:
  1. Extend `investigate_compile_cache.py` per plan P2.1, then run CPU/GPU cache validation batches and publish JSON/log artifacts (P2.2–P2.4).
  2. Harden `benchmark_detailed.py` to tolerate zero warm-setup time and add CLI size controls before collecting new CPU/GPU runs (P3.1–P3.3).
  3. Only after capturing these metrics decide whether further graph work (Phase 4) is needed.
- Repo status for next loop: expect pending changes in docs/fix_plan.md and plans/active/perf-pytorch-compile-refactor/plan.md until committed this round; no other dirty files tracked.

## 2025-10-02 (galph loop R)
- Startup sync succeeded (timeout 30 `git pull --rebase` → already up to date); no conflicts to resolve.
- Deep scan vs long-term goals surfaced three hot spots: (1) ROI mask reallocated every run inside the compiled region (`src/nanobrag_torch/simulator.py:579-598`), (2) misset conversion still instantiates fresh tensors per invocation (`src/nanobrag_torch/models/crystal.py:598-604`), and (3) `sincg`/`sinc3` compile wrappers create new graphs per detector geometry (`src/nanobrag_torch/utils/physics.py:24-102`). Bench tooling still lacks multi-device coverage (`scripts/benchmarks/investigate_compile_cache.py`) and the warm-speed print divides by zero when warm setup hits 0 (`scripts/benchmarks/benchmark_detailed.py:243-267`).
- Updates this loop:
  * Logged new findings in `docs/fix_plan.md` (PERF-PYTORCH-004 update; REPO-HYGIENE-002 marked as reopened) and expanded the PERF plan with tasks P2.5 (Dynamo logs) and P3.4 (ROI/misset caching) plus revised P3.5 decision gate.
  * No new multi-turn plan required beyond refreshing PERF roadmap; repo hygiene plan remains active.
- Guidance for Ralph next loop:
  1. Implement plan tasks P2.1–P2.5, emitting JSON + `TORCH_LOGS=dynamic` artifacts under `reports/benchmarks/<date>-compile-cache/`.
  2. While touching the simulator for P3.4, hoist ROI mask/misset tensors and rerun benchmarks per plan P3.1–P3.5.
  3. After ROI caching lands, revisit performance gap vs C and decide on Phase 4 only if warm runs remain >1.5× slower.
- Repo state leaving loop: only `docs/fix_plan.md` and `plans/active/perf-pytorch-compile-refactor/plan.md` modified; will commit as SUPERVISOR perf-alignment update. `.claude` and other user-managed artifacts untouched.

## 2025-10-02 (galph loop S)
- Startup sync: `timeout 30 git pull --rebase` returned "Already up to date."; no conflicts or dirty files before analysis.
- Deep review confirmed the simple_cubic AT-012 harness still enforces an 86% peak-match tolerance; fresh run yielded `Correlation 1.0`, `Matches 43 / 50` (command logged via `KMP_DUPLICATE_LIB_OK=TRUE python - <<'PY' ... PY`).
- Added active fix item `[AT-PARALLEL-012-PEAKMATCH]` to `docs/fix_plan.md` with guidance to investigate the missing peaks, archive diagnostics under `reports/2025-10-02-AT-012-peakmatch/`, and only tighten the assertion once ≥95% matches are restored.
- No new multi-turn plan needed; PERF roadmap already covers ROI mask/misset caching and Dynamo logging from prior loop, but reiterate that Phase 2 tasks (multi-device cache validation) remain outstanding.
- Guidance for Ralph:
  1. Execute the new fix_plan item by diagnosing the missing simple_cubic peaks, publishing parity artifacts, and tightening the assertion once ≥95% matches are achieved.
  2. Continue PERF-PYTORCH-004 Phase 2 work (P2.1–P2.5) and prep for Phase 3 once cache validation artifacts exist.
  3. While investigating AT-012, confirm the triclinic/tilted variants remain at spec; queue follow-up if additional relaxations surface.
- Repo state on exit: modified `docs/fix_plan.md` and `galph_memory.md` only (no code changes).
## 2025-09-30 17:04:25 (galph loop current)
- Reviewed docs/fix_plan.md against prompts/update_fix_plan.md; file deviates heavily from required template (no per-item Reproduction/Attempts sections, multiple items updated per loop, inflated status claims).
- Header still states AT suite fully passing and AT-012 fixed despite prior logs showing parity failures; needs correction and pruning before Ralph loops resume.
- Determined no new multi-turn plan yet; priority is to rewrite fix_plan using canonical structure and strip duplicate routing-violation entries.
- Heads coin flip → skimmed latest commits (8974cb4..00f822a); activity dominated by supervisor touch-ups, no new technical progress from Ralph to assess.
- Tree left clean; no commits this loop.

## 2025-10-02 (galph loop T)
- Local dirty: prompts/update_fix_plan.md predates this loop; left untouched per policy.
- Deep scan for long-term goals flagged multi-source broadcast bug (src/nanobrag_torch/simulator.py:109-135) still raising expand shape errors when sources>1; perf plan Phase 2 remains blocked on this.
- Reconfirmed per-run ROI mask fabrication and mask dtype casts (src/nanobrag_torch/simulator.py:586-602, 950-979) likely causing the missing peaks; noted constant tensor factories in __init__ (src/nanobrag_torch/simulator.py:358-395) and misset tensor rebuilds (src/nanobrag_torch/models/crystal.py:565-608).
- Benchmark tooling gaps persist: investigations script still CPU-only (scripts/benchmarks/investigate_compile_cache.py) and detailed benchmark divides by zero on 0s warm setup (scripts/benchmarks/benchmark_detailed.py:249-287).
- Authored new phased plan at plans/active/at-parallel-012-peakmatch/plan.md and cross-referenced fix_plan; item now ready for Ralph to execute under prompts/debug.md.
- Follow-ups for Ralph: Phase A of peak-match plan (rerun test, capture artifacts) then Phase B tracing; continue PERF-PYTORCH-004 P2.1–P2.5 once multi-source expand fix lands.

## 2025-10-02 (galph loop T addendum)
- Noted existing working-copy edit in `prompts/update_fix_plan.md`; change predates this loop and left untouched per supervisor policy.

## 2025-10-02 (galph loop U)
- Restored `docs/fix_plan.md` with compact active item ledger plus key completed sections (Protected Assets, routing guard, AT-024 regression, PERF Phase 2, triclinic fix); added dtype hypothesis to AT-012 plan (Phase B4).
- Reintroduced `docs/fix_plan_archive.md` to hold extended history while keeping main plan at 204 lines (<1000).
- Next actions for Ralph: follow updated plan B4 (float32 vs float64 peak detection) during AT-012 investigation, continue REPO-HYGIENE-002 H1–H6, and execute PERF-PYTORCH-004 plan tasks P2.1–P2.5 / P3.1–P3.5.

## 2025-10-02 (galph loop V)
- Startup sync: `git pull --rebase` initially blocked by `prompts/update_fix_plan.md`; stashed (`git stash push -m "galph-pre-pull"`), pull returned "Already up to date.", then `git stash pop` restored the pending edit.
- Deep analysis toward long-term goals:
  * AT-012 peak gap now traced to dtype: rerunning the simple_cubic harness and casting `simulator.run()` to float32 before `find_peaks` yields 50/50 matches (mean Δ0.0 px) whereas float64 stays at 45/50 (43 matched). Command logged under `python - <<'PY' ...` and codified as Plan Phase B4 (`plans/active/at-parallel-012-peakmatch/plan.md`).
  * Multi-source configuration still brittle—`src/nanobrag_torch/simulator.py:404` dereferences `beam_config.source_wavelengths` without a fallback; providing `source_directions` alone reproduces the AttributeError. Needs default-to-main-wavelength handling before Phase 3 performance work.
  * Benchmark tooling bug confirmed: `scripts/benchmarks/benchmark_detailed.py:149` sums the boolean `cache_hit` flag into `timings['total']`, inflating warm-run totals by +1 s and masking true torch.compile gains. Also observed the warm-path divide-by-zero warning when setup=0.
  * Test harness still enforces the relaxed 86% threshold (`tests/test_at_parallel_012.py:169`); tightening awaits the dtype fix plus ROI checks in Phase B1–B3.
- Coin flip → heads → commit review: inspected `51110d4`, `cb6a761`, `a661afc`, `be3398b`.
  * `51110d4` correctly validated torch.compile caching but left multi-source failure and benchmark timing bug unresolved; float32 cache speedup numbers remain valid but need refreshed once CLI is fixed.
  * `cb6a761` patched device drift (`F_cell.to(...)`) yet retained CPU-only constants; full device neutrality (incident beam, cached tensors) still outstanding.
  * `a661afc` documented GPU issues without actionable mitigation; needs follow-through once simulator constants are hoisted.
  * `be3398b` solved the AT-024 float mismatch cleanly—no regressions spotted.
- Planning/docs updates:
  * Verified `plans/active/at-parallel-012-peakmatch/plan.md` now includes Phase B4 dtype task plus supervisor note; no new plan required beyond reinforcing Phase B execution order.
  * `docs/fix_plan.md` already captured Attempt #2 (float32 diagnostic); added guidance to PERF entry to cover the cache_hit bug and missing `source_wavelengths` guard.
- Guidance for Ralph next loop:
  1. Execute AT-012 Plan Phase A artifacts, then Phase B (including new B4 dtype experiment) before touching core physics; archive results under `reports/2025-10-02-AT-012-peakmatch/`.
  2. Patch `Simulator.__init__` to default `source_wavelengths` to `beam_config.wavelength_A` when multi-source directions are supplied, and rerun multi-source torch.compile cache tests.
  3. Fix `scripts/benchmarks/benchmark_detailed.py:149` to exclude booleans from total time and rerun the 256–1024² benchmarks so PERF Phase 3 can compare against C accurately.
- Repo state leaving loop: clean tree (users' `prompts/update_fix_plan.md` restored untouched); no commits made this run.

## 2025-10-02 (galph loop W)
- Reinforced fix_plan pruning guidance: `prompts/update_fix_plan.md` now warns against over-pruning and sets a target of ~500 lines when trimming a >1000-line plan so key context stays in the main ledger.
- No other files touched; tests not run (docs-only update).

## 2025-10-02 (galph loop X)
- Compared legacy `./fix_plan.md` with canonical ledger; migrated missing high-value notes (AT-PERF device neutrality, parity harness bootstrap, AT-020 absorption fix) into `docs/fix_plan_archive.md`.
- Replaced stray standalone file with symlink `fix_plan.md -> docs/fix_plan.md` to prevent divergent ledgers going forward.
- Tests not run (docs + symlink hygiene only).

## 2025-10-02 (galph loop X addendum)
- Reminder: `./fix_plan.md` is now a symlink to `docs/fix_plan.md`; always edit the canonical file and avoid recreating standalone copies.

## 2025-10-02 (galph loop Y)
- Sync: `git pull --rebase --autostash` required because existing working-tree edits blocked the standard pull; re-applied cleanly with no conflicts.
- Deep dive: AT-012 plan still lacks Phase A artifacts; `Simulator.__init__` multi-source branch raises when `source_wavelengths` is omitted; repeated `torch.compile(...)` wrapping per instance keeps warm-up cost high and still builds guard tensors on the hot path.
- Planning: Added Phase 3 task P3.0 in `plans/active/perf-pytorch-compile-refactor/plan.md` (multi-source defaults) and cross-referenced it in `docs/fix_plan.md` so Ralph must fix defaults before benchmarking.
- Coin flip (heads): Reviewed commits `78be581`, `51110d4`, `cb6a761`, `a661afc`; GPU neutrality fix still leaves incident-beam tensors CPU-bound, benchmark tooling remains broken, and multi-source crash persists.
- Next for Ralph: Execute AT-012 Plan Phase A/B (esp. dtype experiment), implement PERF P3.0 alongside benchmark fixes, and address torch.compile rewrap/device-neutrality backlog before new perf claims.

## 2025-10-02 (galph loop Z)
- Sync: `git pull --rebase` completed cleanly; no stash needed.
- Findings vs goals:
  * Performance: `src/nanobrag_torch/simulator.py:786-804` applies polarization after the multi-source sum using `self.incident_beam_direction`, so divergent beams never get per-source Kahn weighting; this breaks AT-SRC-001 parity and blocks trustworthy benchmarks.
  * Stability: same file (`lines 401-414`) still dereferences `beam_config.source_wavelengths` without a fallback; multi-source configs built via CLI helpers continue to crash until defaults redirect to `wavelength_A`.
  * Peak-match initiative stagnates—`plans/active/at-parallel-012-peakmatch/plan.md` remains untouched (Phase A checklist all [ ]), so no new artifacts exist to drive the >95% threshold fix.
  * Tooling: `benchmark_detailed.py` issues logged earlier remain; perf plan must still harden CLI + totals before fresh numbers mean anything.
  * Reminder: accidentally launched Python without `KMP_DUPLICATE_LIB_OK` during a quick tensor truthiness check—error reproduced, reran with env set; worth reinforcing to Ralph.
- Actions:
  * Updated `plans/active/perf-pytorch-compile-refactor/plan.md` (Phase 3) with task P3.0b to fix per-source polarization/weighting semantics and noted issue in discovered-issues list.
  * Refreshed `docs/fix_plan.md` `[PERF-PYTORCH-004]` Observations/Next Actions to call out P3.0b alongside defaults/benchmark tasks.
  * Committed and pushed `SUPERVISOR: PERF plan multi-source guard - tests: not run` on `feature/spec-based`.
- Coin flip: tails → no commit review this loop.
- Guidance for Ralph next: 1) Execute PERF Plan P3.0 and new P3.0b before re-running cache/benchmark scripts (capture logs under `reports/benchmarks/<date>-perf-summary/`); 2) Start AT-012 Plan Phase A (baseline artifacts + float32 comparison) so we can move on to divergence tracing; 3) Fix `benchmark_detailed.py` aggregation (P3.1) immediately after the multi-source fixes so performance evidence is usable.
- Repo state: clean after push.

## 2025-10-03 (galph loop AA)
- Sync: `git pull --rebase` returned already up to date; no conflicts.
- Findings vs goals: multi-source defaults still dereference `beam_config.source_wavelengths` without a fallback (src/nanobrag_torch/simulator.py:397), per-source polarization still uses the global beam vector in both subpixel and pixel paths (src/nanobrag_torch/simulator.py:786, 904), and `benchmark_detailed.py:118` keeps adding the boolean `cache_hit` flag into total timing; AT-012 float64 peak drop remains the active hypothesis (Plan Phase B4).
- Coin flip (heads): No new engineer commits beyond `78be581` and `51110d4`; both still leave multi-source crash + polarization + timing bugs unresolved—flagged for follow-up.
- Planning/docs: Updated `plans/active/perf-pytorch-compile-refactor/plan.md` task P3.1 to call out the `cache_hit` aggregation fix; other plans remain accurate.
- Next actions for Ralph: execute AT-012 Plan Phase A/B (esp. dtype artifact capture), deliver PERF Plan P3.0/P3.0b fixes before benchmarking, and patch `benchmark_detailed.py` totals as part of P3.1.

## 2025-10-03 (galph loop AB)
- Sync: Required temporary stash to satisfy `git pull --rebase`; re-applied cleanly and confirmed only `galph_memory.md` remained dirty.
- Deep analysis toward goals: confirmed multi-source path still pins polarization to `self.incident_beam_direction` and uncovered a new normalization gap—`steps` divides by Σweights so PyTorch averages source intensities while nanoBragg.c sums them—alongside the existing `source_wavelengths` None crash and `benchmark_detailed.py` total-time boolean bug.
- Coin flip (heads) → commit review: `51110d4` delivered cache validation but left multi-source crash, polarization, and benchmark math unfixed; `78be581` correctly patches detector device drift; earlier WIP commits (`cb6a761`, `a661afc`) documented the device-neutrality effort but still staged regressions that must be completed (normalization, per-source Kahn weighting, CLI robustness).
- Planning/docs updates: added Task P3.0c to `plans/active/perf-pytorch-compile-refactor/plan.md` for multi-source normalization parity and noted the issue under discovered problems; refreshed `docs/fix_plan.md` `[PERF-PYTORCH-004]` observations to call out P3.0c alongside existing P3.0/P3.0b/P3.1 guidance.
- Next steps for Ralph: 1) Execute plan tasks P3.0–P3.0c before rerunning benchmarks (fix fallback, per-source polarization, and normalization), 2) capture AT-012 Phase A artifacts then run Phase B4 float32 diagnostic with archived reports, 3) patch `benchmark_detailed.py` totals per P3.1 and rerun perf suite once multi-source issues are resolved.

## 2025-10-03 (galph loop AC)
- Sync: python-enforced 30s timeout `git pull --rebase` succeeded; tree clean, no stashing required.
- Deep analysis vs goals: multi-source path still fails without explicit wavelengths (`src/nanobrag_torch/simulator.py:401-405`, `:644-668`), polarization continues to use the global beam vector so per-source Kahn weighting is wrong in both subpixel and pixel paths (`src/nanobrag_torch/simulator.py:786-817`, `:840-857`), and normalization still divides by Σweights causing weighted averages (`src/nanobrag_torch/simulator.py:660-668`). Existing PERF plan Phase 3 (tasks P3.0–P3.0c) already targets these defects.
- Coin flip = heads → commit audit: no new Ralph commits since 78be581 (device-neutrality patch). Multi-source crash/semantics regressions remain unresolved; reiterate need to execute P3.0/P3.0b/P3.0c before new perf claims.
- docs/fix_plan.md and active plans remain accurate; no new plan authored this loop.
- Next steps for Ralph: complete PERF Phase 3 tasks (fallback, per-source polarization, normalization), run AT-SRC-001 + benchmark reproductions with artifacts under `reports/benchmarks/<date>-perf-summary/`, then proceed to AT-012 peak-match Plan Phase A/B once multi-source path is stable.

## 2025-10-03 (galph loop AD)
- Sync: `git pull --rebase` already up to date; no stashing needed.
- Deep analysis vs goals: multi-source path still lacks wavelength fallback (`src/nanobrag_torch/simulator.py:394-416`), polarization continues to reuse the global `self.incident_beam_direction` after the per-source accumulation (`src/nanobrag_torch/simulator.py:793-817`, `:847-864`), and normalization still divides by `source_weights.sum()` so intensities average instead of matching C (`src/nanobrag_torch/simulator.py:652-668`). AT-012 peak-match plan remains untouched—no report dir under `reports/2025-10-02-AT-012-peakmatch/` yet—and float64 vs float32 discrepancy persists. `benchmark_detailed.py` total aggregation bug (boolean `cache_hit`) still unfixed, blocking trustworthy perf numbers.
- Coin flip = heads → commit review: no engineer commits after `78be581`; last work stopped at device-neutrality fix, leaving Phase 3 PERF tasks untouched. Feedback needed: Ralph must execute P3.0–P3.0c before running benchmarks and capture AT-012 Phase A artifacts instead of re-looping prompts.
- Planning/docs: Existing plans (PERF Phase 3, AT-012 peakmatch) remain correct; no new plan drafted this loop.
- Next for Ralph: 1) Execute PERF Plan tasks P3.0–P3.0c with artifacts under `reports/benchmarks/<date>-perf-summary/`; 2) Run AT-012 Phase A commands and store outputs under `reports/2025-10-02-AT-012-peakmatch/`; 3) Patch `scripts/benchmarks/benchmark_detailed.py` totals per P3.1 before quoting performance data.
- Repo state: only `galph_memory.md` updated; commit/push pending at loop end.
## 2025-10-03 (galph loop AE)
- Sync: `git pull --rebase` returned "Already up to date"; no conflicts or stashes.
- Deep-dive vs long-term goals:
  * Multi-source path still broken in `src/nanobrag_torch/simulator.py` (lines ~400-680): missing wavelength fallback (`source_wavelengths` `.to()` on None), polarization still uses `self.incident_beam_direction` rather than per-source vectors inside the oversample path, and `steps` divides by Σweights so intensities average instead of summing (see plan tasks P3.0/P3.0b/P3.0c).
  * AT-012 peak-match plan untouched: no artifacts under `reports/2025-10-02-AT-012-peakmatch/`, peak finder still drops to 43/50 in float64; Phase A checklist needs to run before new hypotheses.
  * Perf hotspots linger: `Simulator.run()` rebuilds ROI mask + `torch.as_tensor` constants every call; plan P3.4 (ROI/misset caching) should stay high priority once multi-source fixes land.
- Planning decision: Existing active plans (`at-parallel-012-peakmatch`, `perf-pytorch-compile-refactor`, `repo-hygiene-002`) already cover the needed multi-turn work; no new plan drafted.
- Ralph status: No engineer commits since 78be581 (device-neutrality fix); pending work is executing Plan AT-012 Phase A/B and PERF Phase 3 tasks.
- Follow-ups for next loop: 1) Confirm Ralph captures AT-012 Phase A artifacts + float32/float64 comparison; 2) Ensure PERF tasks P3.0–P3.0c start (fallback, polarization, normalization) before new benchmarks; 3) Push progress on repo-hygiene-002 (H1–H4 not started).

## 2025-10-04 (galph loop AF)
- Deep dive reaffirmed multi-source regressions: `src/nanobrag_torch/simulator.py` still calls `.to()` on `beam_config.source_wavelengths` when None, normalizes by `source_weights.sum()` (averages), and drives polarization with `self.incident_beam_direction`; all three gaps block PERF Plan P3.0–P3.0c.
- Peak-match effort untouched: no artifacts under `reports/2025-10-02-AT-012-peakmatch/`; Phase A checklist in `plans/active/at-parallel-012-peakmatch/plan.md` remains at [ ].
- No new plan spun up; existing active plans already track the work. Fix_plan priorities still accurate, so left unchanged.
- Ralph next actions: execute PERF Plan P3.0/P3.0b/P3.0c to restore multi-source semantics, then run AT-012 Plan Phase A (capture baseline JSON/peaks) before exploring dtype hypotheses; keep work under `prompts/debug.md`.

## 2025-10-04 (galph loop AG)
- Sync: `git pull --rebase` clean (no remote deltas); working tree remained clean throughout review.
- Deep analysis (long-term goals):
  * Multi-source path still broken—`Simulator.run` divides by `source_weights.sum()` inside `steps`, so weighted sums average intensities (`src/nanobrag_torch/simulator.py:688-695`) and polarization still uses the global beam vector instead of per-source directions (`src/nanobrag_torch/simulator.py:813-834`).
  * Fallback crash persists: when `BeamConfig.source_wavelengths` is `None`, `__init__` still calls `.to()` on it (`src/nanobrag_torch/simulator.py:666-677` + `src/nanobrag_torch/config.py:465-469`), matching the failure PERF plan P3.0 documents.
  * Perf hotspots unchanged—ROI mask and detector constants are rebuilt every run (`src/nanobrag_torch/simulator.py:571-609`), and warm-run benchmarks remain untrustworthy because `scripts/benchmarks/benchmark_detailed.py:108-157` still sums the boolean `cache_hit` into totals and hardcodes detector sizes.
  * AT-012 peak-match effort is stalled: `reports/` has no `2025-10-02-AT-012-peakmatch/` directory yet, so Phase A (A1–A3) never started.
- Planning call: existing plans (`plans/active/at-parallel-012-peakmatch`, `plans/active/perf-pytorch-compile-refactor`) already capture these gaps; no new plan drafted. docs/fix_plan.md priorities remain aligned with observed blockers.
- Next steps for Ralph:
  1. Execute AT-012 Phase A (A1–A3) to capture fresh failure artifacts before new hypotheses.
  2. Work through PERF Phase 3 tasks sequentially—P3.0/P3.0b/P3.0c to restore multi-source semantics, then P3.1 to fix the benchmark script, before collecting warm-run data.
  3. Once those are underway, cache ROI/misset tensors per P3.4 to remove the remaining per-run tensor churn.

## 2025-10-04 (galph loop AH)
- Sync: `git pull --rebase` returned "Already up to date"; no conflicts.
- Deep analysis vs long-term goals:
  * `Simulator.__init__` still dereferences `beam_config.source_wavelengths` with `.to(...)` when callers omit explicit wavelengths, so multi-source configs built programmatically still crash (src/nanobrag_torch/simulator.py:425-438).
  * Multi-source physics remains incorrect: polarization uses the global incident vector in both oversample and pixel-center paths (src/nanobrag_torch/simulator.py:813-833, 932-951) and `steps` divides by `source_weights.sum()` (src/nanobrag_torch/simulator.py:687-695), averaging intensities instead of summing like nanoBragg.c.
  * ROI mask and detector tensors are rebuilt on every run (src/nanobrag_torch/simulator.py:543-615, 905-918), so even once physics is fixed we still pay large allocator overhead—Phase P3.4 remains unfunded.
- Ralph commit review (last 10): engineer WIP `48a1cdd` shipped without tests and left the `.to()` crash path in place; follow-up `3f9dc82` labeled P3.0 “complete” despite the fallback and polarization/normalization gaps, so productivity stalled and parity regressions persist.
- Planning/docs actions: Added Attempt #7 under `[PERF-PYTORCH-004]` in `docs/fix_plan.md` capturing the outstanding fallback/polarization/normalization issues and sequencing next actions (P3.0→P3.0b→P3.0c→P3.4). Existing active plans remain valid; no new plan created.
- Next for Ralph:
  1. Finish PERF Plan P3.0 by seeding default wavelengths/weights before `.to()` and re-running the multi-source crash reproduction.
  2. Immediately tackle P3.0b/P3.0c to move polarization/normalization inside the per-source accumulation; archive before/after metrics per plan guidance.
  3. Only after physics parity is restored, execute P3.4 ROI caching and rerun steady-state benchmarks (Phase 3) against the C binary.

## 2025-10-04 (galph loop AI)
- Sync: worktree was dirty (`docs/fix_plan.md`, `galph_memory.md`), stashed via `git stash push -m "galph-temp-before-pull"`, completed `timeout 30 git pull --rebase` after finishing an outstanding interactive rebase, then `git stash pop` restored local notes.
- Deep analysis vs goals:
  * Multi-source defaults still crash because `Simulator.__init__` calls `.to(...)` on `beam_config.source_wavelengths` without seeding fallbacks (src/nanobrag_torch/simulator.py:429-441); no helper populates wavelengths/weights when only directions are provided.
  * Polarization remains wrong after commit `fcbb93a`: both oversample and pixel-center paths reuse only the primary source vector (src/nanobrag_torch/simulator.py:775-823, 894-951), leaving secondary sources unpolarized and blocking P3.0b.
  * `steps` divides by `source_weights.sum()` (src/nanobrag_torch/simulator.py:680-695), so multi-source intensities are averaged instead of summed; aligns with the open P3.0c normalization task.
  * ROI mask/omega tensors are still rebuilt each run via fresh `torch.ones`/`.to()` churn (src/nanobrag_torch/simulator.py:613-630, 804-833), keeping warm-run perf far behind C until P3.4 executes.
- Planning/docs updates: tightened `plans/active/perf-pytorch-compile-refactor/plan.md` P3.0/P3.0b/P3.0c guidance with explicit line references and fallback/polarization requirements; corrected `[PERF-PYTORCH-004]` Attempt #7 in `docs/fix_plan.md` to mark commit `fcbb93a` as a failed approximation and restate next actions.
- Coin flip = heads → reviewed latest engineer commits (fcbb93a, 3f9dc82, 48a1cdd): polarization fix is incomplete, diagnostic commit overstates default readiness, and WIP left `.to(None)` path intact; no new regressions beyond the outstanding multi-source gaps.
- Repo note: `prompts/supervisor.md` remained locally modified from a prior loop (added fp32 default reminder); change left untouched per policy.
- Next steps for Ralph:
  1. Implement P3.0 fallback seeding before touching torch.compile again, capturing before/after logs per plan.
  2. Rework polarization so each source applies its own Kahn factor before reduction; validate against C traces and update the new parity artifacts.
  3. Fix normalization (`steps`) to match nanoBragg.c, then continue with P3.1 benchmarking/CLI hardening once physics parity is restored; only afterwards resume ROI caching (P3.4).

## 2025-10-04 (galph loop AJ)
- `git pull --rebase` initially blocked by tracked prompt edit (`prompts/supervisor.md`); stashed `galph-pre-pull`, pulled, then restored stash so local customization stays intact.
- Step-1 findings vs goals: (1) multi-source defaults still crash when `source_wavelengths` is `None` because `Simulator.__init__` calls `.to(...)` unconditionally (`src/nanobrag_torch/simulator.py:430-437`); (2) polarization still applies only the primary source (`simulator.py:822`), leaving secondary sources unweighted; (3) steps normalization divides by Σweights (`simulator.py:687-695`), averaging intensities instead of summing; (4) ROI/mask tensors are rebuilt every run (`simulator.py:613-629`); (5) simulator defaults remain float64 (`simulator.py:369`), conflicting with fp32 goal.
- Coin flip → heads: reviewed recent engineer commits. `fcbb93a` still reuses the first source for polarization, so multi-source physics remains wrong; `a2a9e83` fixed AT-012 by casting to float32 before `find_peaks`; WIP `48a1cdd` landed without tests (broadcast refactor). Feedback needed: finish PERF plan P3.0/P3.0b/P3.0c before further benchmarks.
- Planning actions: archived `plans/active/at-parallel-012-peakmatch` (all tasks flagged [D]) under `plans/archive/at-parallel-012-peakmatch/plan.md`, created new fp32 initiative plan (`plans/active/dtype-default-fp32/plan.md`), and added `[DTYPE-DEFAULT-001]` entry to docs/fix_plan.md.
- Next steps for Ralph: (1) Execute PERF Plan P3.0/P3.0b/P3.0c in order—seed source defaults, apply per-source polarization, fix normalization; (2) resume ROI caching (P3.4) after physics parity; (3) start Phase A of the new dtype plan by inventorying float64 assumptions; (4) keep commits under `prompts/debug.md` until multi-source physics passes parity.

## 2025-10-04 (galph loop AK)
- Sync: `timeout 30 git pull --rebase` initially blocked by modified `prompts/supervisor.md`; stashed (`galph-pre-pull`), pulled, then restored stash so user customization stays intact.
- Deep analysis vs goals:
  * Multi-source defaults still crash because `Simulator.__init__` dereferences `beam_config.source_wavelengths`/`source_weights` with `.to(...)` when they are `None` (`src/nanobrag_torch/simulator.py:429-441`).
  * Polarization continues to reuse only the first source (`incident_for_polarization = incident_dirs_batched[0]`) in both oversample and pixel-center paths (lines 775-778, 894-895), leaving secondary sources unpolarized.
  * `steps` still divides by `source_weights.sum()` (lines 687-695), averaging intensities instead of matching the C sum-over-sources semantics; ROI/mask tensors remain per-run allocations (lines 543-615, 905-918), and simulator defaults remain float64 (`simulator.py:311` signature).
- Coin flip = heads → Reviewed engineer commits `3f9dc82`, `fcbb93a`, `904dc9b`. Findings: 3f9dc82 mislabeled P3.0 complete despite open crash/polarization issues; fcbb93a’s “fix” still hard-codes the primary source so physics remains wrong; 904dc9b only touched benchmark CLI yet marked normalization complete, creating documentation drift.
- Planning/docs actions: Reopened tasks P3.0–P3.0c in `plans/active/perf-pytorch-compile-refactor/plan.md` (set states back to `[ ]`, added explicit crash/polarization/normalization guidance) and corrected `[PERF-PYTORCH-004]` attempt history in `docs/fix_plan.md` (Attempts #7–#9 now describe failures + this audit). Updated fix_plan header to reflect current focus.
- Next steps for Ralph:
  1. Implement fallback seeding in `Simulator.__init__` so multi-source configs without explicit wavelengths/weights stop crashing; record reproduction + fix artifacts.
  2. Rework polarization to apply Kahn factors per source before summing, then re-run C vs PyTorch traces for a 3-source case to prove parity.
  3. Adjust normalization so `steps` no longer divides by Σweights; verify with `tests/test_at_parallel_001.py::TestATSRC001::test_multiple_sources_normalization` before collecting new benchmarks; only afterward resume ROI caching (P3.4) and Phase 3 benchmarking.

## 2025-10-05 (galph loop AL)
- Sync: `timeout 30 git pull --rebase` initially blocked by dirty plan/fix docs; stashed (`git stash push -m 'galph-sync-temp'`), finished the pending interactive rebase with `git commit --amend --no-edit` + `git rebase --continue`, reran pull (clean), then `git stash pop` restored local notes.
- Step-1 findings vs long-term goals:
  * `Simulator.__init__` still calls `.to()` on `beam_config.source_wavelengths/weights` when they are `None` (`src/nanobrag_torch/simulator.py:430-437`), so multi-source configs crash without manual seeding.
  * Multi-source polarization remains wrong: oversample and pixel-center paths reuse only the first source vector (`simulator.py:774-824`, `894-951`), leaving secondary sources unpolarized.
  * `steps` divides by `source_weights.sum()` (`simulator.py:687-695`), averaging intensities instead of matching the nanoBragg sum; normalization parity still outstanding.
  * ROI mask/misset tensors are rebuilt every run (`simulator.py:604-641`, `1005-1045`), keeping CPU warm runs slow until P3.4 hoists them.
- Step-2 (coin=heads) commit review: `3f9dc82`/`fcbb93a` still leave the `.to(None)` crash, first-source polarization shortcut, and weight-averaging bug; `904dc9b`/`b06a6d6` gathered benchmarks but marked Phase 3 complete despite CPU runs violating ≤1.5× C and upstream physics defects; `a2a9e83` float32 peak fix is correct.
- Actions: Reopened PERF plan Phase 3 rows (P3.2/P3.3 now `[P]`, P3.5 `[ ]`), added ROI caching to discovered issues, and logged Attempt #11 in `docs/fix_plan.md` so plan/fix_plan align with outstanding work.
- Guidance for Ralph:
  1. Deliver P3.0/P3.0b/P3.0c fixes (fallback seeding, per-source polarization, sum-based normalization) with multi-source parity artifacts before revisiting benchmarks.
  2. Execute P3.4 ROI/misset caching to remove per-run tensor churn, then rerun CPU/CUDA benchmarks and produce the Phase 3 summary before considering Phase 4.
  3. Leave the AT-012 peak-match plan closed unless new physics work regresses the float32-based matcher.

## 2025-10-05 (galph loop AM)
- Sync workflow: staging area was dirty (plans/fix docs). Stashed, completed lingering interactive rebase via `git rebase --continue`, reran `timeout 30 git pull --rebase` (fast-forward to 8c2ceb4), then `git stash pop` restored local supervisor edits.
- Step-1 analysis vs long-term goals:
  * New commit 8c2ceb4 switches runtime defaults to float32. AT-PARALLEL-012 now matches only 43/50 peaks when run natively in float32; plateau sensitivity must be debugged before Phase C benchmarking.
  * Multi-source defects persist: `Simulator.__init__` still calls `.to()` on `beam_config.source_wavelengths/weights` when they are `None`, so default divergence configs crash; polarization uses only the primary source (`incident_dirs_batched[0]`), and `steps` divides by `source_weights.sum()`, averaging intensities instead of summing contributions. These map directly to PERF plan tasks P3.0/P3.0b/P3.0c.
  * Performance blockers remain (ROI/misset tensor rebuild every run; guard tensor fabrication) as noted in prior loops—no new progress logged in benchmarks since b06a6d6.
- Planning/docs updates: refreshed `plans/active/dtype-default-fp32/plan.md` (Phase A complete, Phase B `[P]`, Phase C gated on AT-012 fix) and updated `[DTYPE-DEFAULT-001]` in docs/fix_plan.md with Attempt #1 summary plus plan reference. Status now `in_progress`.
- Local note: `prompts/supervisor.md` remains intentionally customized (fp32 reminder); left unstaged per prior policy.
- No pruning performed—older entries still relevant for ongoing PERF/AT initiatives; reassess when dtype migration stabilises.
- Next steps for Ralph:
  1. Diagnose AT-PARALLEL-012 float32 regression (compare plateau pixel values vs float64→float32, adjust peak detection or simulation as needed) and capture artifacts under `reports/DTYPE-DEFAULT-001/`.
  2. Implement PERF plan P3.0/P3.0b/P3.0c fixes: guard against `None` source tensors, apply polarization per-source before reduction, and remove weight-sum divisor from `steps`. Provide multi-source parity traces to confirm correctness.
  3. Finish dtype helper plumbing (Phase B3: `io/source.py`, `utils/noise.py`, `utils/c_random.py`), then proceed to Phase C validation once AT-012 passes.

## 2025-10-06 (galph loop AN)
- Sync: `timeout 30 git pull --rebase` succeeded after finishing pending interactive rebase (`git rebase --continue`). Working tree started clean.
- Step-1 findings vs goals:
  * Multi-source path still broken: `Simulator.__init__` dereferences `source_wavelengths/source_weights` even when None, so divergence configs without explicit tensors still crash (`src/nanobrag_torch/simulator.py:427-441`).
  * Polarization remains first-source only in both oversample and pixel-center branches (`simulator.py:775-822`, `894-950`), violating AT-SRC-001; normalization continues to divide by Σweights (`simulator.py:687-695`) so intensities average rather than sum.
  * ROI/mask tensors are rebuilt every run (`simulator.py:611-629`), keeping CPU steady-state slower than the C baseline despite compile caching.
  * DTYPE plan still blocked: float32 defaults leave AT-PARALLEL-012 at 43/50 peaks when run natively; Phase B3 helpers remain outstanding.
- Step-2 (coin=heads) audit of recent ralph commits (`fcbb93a`, `904dc9b`, `b06a6d6`, `8c2ceb4`) confirmed mislabelled progress: polarization still approximated with primary source, normalization untouched, benchmarks recorded despite unmet exit criteria, and dtype flip shipped without resolving float32 parity.
- Actions this loop:
  * Added Attempt #12 to `[PERF-PYTORCH-004]` in `docs/fix_plan.md` documenting the audit, with explicit code citations for the outstanding bugs.
  * No new plan authored; existing `plans/active/perf-pytorch-compile-refactor/plan.md` already tracks P3.0–P3.4 as open.
- Next steps for Ralph:
  1. Implement guarded source seeding before `.to(...)`, rewrite polarization to apply Kahn factors per source prior to reduction, and move weight normalization after the per-source sum (Perf plan P3.0–P3.0c).
  2. Hoist ROI/omega/misset tensors out of the hot path (P3.4) and only then rerun the CPU/CUDA benchmarks for Phase 3.
  3. Resume DTYPE Phase B3 helper updates and investigate float32 peak regression (store artifacts under `reports/DTYPE-DEFAULT-001/`) once multi-source parity is restored.
## 2025-10-06 (galph loop AO)
- Step-1 audit vs long-term goals: Multi-source path still broken — `Simulator.__init__` dereferences `beam_config.source_wavelengths` without fallback (src/nanobrag_torch/simulator.py:431), polarization uses only source[0] (simulator.py:775), and `steps` divides by Σweights (simulator.py:687), so intensities average instead of summing. These map directly to PERF plan P3.0/P3.0b/P3.0c.
- ROI/mask tensors are rebuilt on every `run` call (simulator.py:611-629) and `Detector.get_pixel_coords().to(...)` clones the full grid each run, keeping CPU warm timings 0.44×–0.63× of C at 512²–1024² (reports/benchmarks/20250930-184744/benchmark_results.json). Highlights urgency of P3.4 caching before revisiting benchmarks.
- Coin flip → tails, so no additional commit audit beyond Step 3 housekeeping. `docs/fix_plan.md` priorities still align with active plans; no edits needed this loop.
- Next actions for Ralph: deliver PERF-PYTORCH-004 P3.0/P3.0b/P3.0c fixes with regression artifacts under `reports/PERF-PYTORCH-004/` and implement ROI/misset caching per P3.4 before re-running CPU/CUDA benchmarks; resume DTYPE plan Phase B3 once AT-012 peak parity holds in native float32.
## 2025-10-06 (galph loop AP)
- Step-1 doc review reaffirmed outstanding multi-source physics bugs: `Simulator.__init__` still calls `.to()` on `beam_config.source_wavelengths` when `None` and polarization keeps only the primary source (src/nanobrag_torch/simulator.py:430-822). ROI/mask tensors are still rebuilt every run (lines 611-633), so Phase 3 CPU perf gaps persist.
- Ran `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_simple_cubic_correlation -q`; float32 default still yields 43/50 matches (corr=1.0). Logged as Attempt #2 under `[DTYPE-DEFAULT-001]` (docs/fix_plan.md) and updated plan task C1 to require float64 vs float32 trace capture (`plans/active/dtype-default-fp32/plan.md`).
- Coin flip=heads → audited ralph commits (`fcbb93a`, `904dc9b`, `b06a6d6`, `8c2ceb4`). Findings: per-source polarization not applied before reduction, normalization still divides by Σweights, CPU benchmarks recorded despite blockers, and dtype flip shipped without resolving AT-012 parity or docs drift (`arch.md` still advertises float64 default).
- Guidance for Ralph: 1) Implement PERF plan P3.0/P3.0b/P3.0c fixes (guard default sources, per-source polarization, remove weight divisor) with parity traces; 2) Cache ROI/misset tensors (P3.4) before collecting new benchmarks; 3) For dtype rollout, capture float64 vs float32 plateau diagnostics under `reports/DTYPE-DEFAULT-001/20251006-at012-regression/`, finish Phase B3 helper dtype plumbing, and only then rerun Tier-1 parity + update docs (`arch.md` etc.).
- Follow-up: Ensure Attempt #2 artifacts are generated next loop, revisit docs drift once float32 parity passes, and do not accept new benchmarks until PERF Phase 3 physics tasks are complete.
## 2025-10-06 (galph loop AQ)
- Step-1 code review highlighted that multi-source fixes remain unimplemented: `_has_sources` still calls `.to()` on `None`, polarization only uses `incident_dirs_batched[0]`, and `steps` continues to divide by summed weights. ROI/mask tensors and detector grids are rebuilt each `run`, so Attempt #9 CPU benchmarks are invalid as performance evidence.
- DTYPE float32 plateau issue persists (AT-012 still 43/50) with no new artifacts captured; docs (`arch.md`) still advertise float64 defaults. Plans/active files already carry open tasks; updated `docs/fix_plan.md` header to current date to keep ledger synced.
- Coin=heads audit of recent commits reconfirmed regressions: `b06a6d6` benchmark commit published numbers without fixing physics, `8c2ceb4` flipped defaults without updating docs or parity, and no code since then addresses the outstanding bugs.
- Actions for Ralph: finish PERF plan P3.0/P3.0b/P3.0c first (guard source tensors, per-source polarization, correct normalization) and hoist ROI/misset caches before running any new benchmarks; collect float64 vs float32 plateau traces under `reports/DTYPE-DEFAULT-001/20251006-at012-regression/` and leave docs unchanged until parity is restored; defer further benchmarking or documentation updates until these blockers clear.
- Follow-up: Next loop should verify that artifacts for multi-source fixes and AT-012 diagnostics exist, and ensure perf benchmarks are rerun only after physics parity and caching work are complete.
## 2025-10-06 (galph loop AR)
- `git pull --rebase` clean; reviewed existing memory + active plans before analysis.
- Step-1 analysis vs long-term goals:
  * Error-correcting agent: `loop.sh` currently reverts to `prompts/main.md` inside a 20-iteration loop with unconditional `git push`; contradicts fix_plan status and routing SOP.
  * PyTorch performance: `_compute_physics_for_position` still divides by summed source weights (averaging multi-source intensities) and polarization in `Simulator.run` uses only the first source; ROI/mask tensors rebuilt per run, and detector grids/clamps allocate guard tensors (crystal `compute_cell_tensors` still constructs new tensors for spindle axis). These keep PERF-PYTORCH-004 Phase 3 blockers active and explain benchmark stagnation.
  * DTYPE rollout: AT-012 peak matcher still failing 43/50 when running native float32, no new artifacts under `reports/DTYPE-DEFAULT-001/`; docs (`arch.md`) still advertise float64 default.
- Coin flip = heads → commit review (last ~6 non-supervisor commits):
  * `8c2ceb4` flipped defaults to float32 but shipped AT-012 regression without parity artifacts or doc updates; plateau fragmentation unresolved.
  * `56c46b2` merge only documented regression, no fix; automation guard apparently lost during merge (now regressed).
  * Earlier GRADIENT-MISSET fix (`b812155`) solid, but subsequent work stalled on restoring Core Rule #13 tolerances until supervisor intervention.
  Recommendation: Ralph must stop publishing benchmarks/rollouts before physics + automation gates pass; enforce plan-driven fixes.
- Planning action: Reopened `[ROUTING-LOOP-001]` (status→in_progress) and authored phased remediation plan at `plans/active/routing-loop-guard/plan.md`; logged regression Attempt #2 in fix_plan.
- Follow-up for Ralph:
  1. Execute routing plan Phase A (capture current `loop.sh`, produce audit report, update fix_plan with artifact link) then Phase B–C to restore debug prompt guard.
  2. Resume PERF-PYTORCH-004 Phase 3 tasks — fix multi-source weighting & polarization plus ROI caching — before recording new benchmarks.
  3. For DTYPE plan Phase C1, generate float64 vs float32 trace/peak artifacts under `reports/DTYPE-DEFAULT-001/20251006-at012-regression/` and resolve plateau failure prior to doc updates.
## 2025-10-06 (galph loop AS)
- Step-1 analysis reinforced open blockers: multi-source normalization still divides by Σweights and polarization keeps only the first source direction in both oversample and pixel-center paths (`src/nanobrag_torch/simulator.py:687-695`, `:775-822`, `:894-950`); ROI mask construction and detector grid `.to()` allocations rerun each `Simulator.run` call (`simulator.py:611-634`), perpetuating CPU slowdowns; dtype rollout remains stalled with AT-012 at 43/50 matches; automation harness `loop.sh` continues to call `prompts/main.md` in a 20-iteration loop with unconditional `git push` (lines 16-18).
- Coin flip=heads → reviewed recent ralph commits (`8c2ceb4`, `56c46b2`, `df7c0fd`, `5d8237a`, `2c432b5`, `b812155`): dtype flip shipped regression without docs/tests, follow-up commits added documentation only (no fixes), and `loop.sh` regression reintroduced verification-centric automation. Productivity low; regressions remain unresolved.
- Actions this loop:
  * Logged Attempt #13 under `[PERF-PYTORCH-004]` in `docs/fix_plan.md` describing the ongoing multi-source/polarization/ROI issues; updated ledger header to loop AS.
  * Bumped `plans/active/perf-pytorch-compile-refactor/plan.md` status summary to 2025-10-06 and reaffirmed outstanding blockers.
- Next steps for Ralph:
  1. Execute PERF plan tasks P3.0b/P3.0c/P3.4 with trace artifacts before attempting any new benchmarks; fix polarization weighting to use per-source directions and move normalization after the reduction.
  2. Complete routing plan Phase A artifact capture and restore `loop.sh` to single-pass `prompts/debug.md` execution prior to rerunning automation.
  3. Resume DTYPE-DEFAULT plan Phase C once AT-012 float32 parity passes, capturing float64 vs float32 plateau traces under `reports/DTYPE-DEFAULT-001/20251006-at012-regression/`.

## 2025-10-07 (galph loop AT)
- `git pull --rebase` clean; reviewed galph_memory + active plans before analysis.
- Deep-dive reaffirmed multi-source physics regressions: `steps` still divides by summed weights (violates AT-SRC-001), polarization paths still reuse the first source vector, and ROI/misset tensors (`Simulator.run`:611-705) plus detector constants are rebuilt each call, matching the chronic CPU allocator churn in benchmarks. DTYPE plan Phase B3 helper plumbing still outstanding; automation harness (`loop.sh`) remains in 40-iteration `prompts/main.md` loop with unconditional pushes.
- Updated the PERF plan Phase 3 table with spec citations, explicit reproduction commands (pytest multi-source test + `nb-compare` C/Py pairing), and profiler artifact expectations; filed `[PERF-PYTORCH-004]` Attempt #14 documenting the spec alignment and required artifacts.
- Follow-up for Ralph: finish PERF plan tasks P3.0–P3.0c (guard defaults, per-source polarization, normalization) and P3.4 (ROI/misset caching) with the new artifact targets before re-running P3.2/P3.3 benchmarks; keep routing plan Phase A in focus; capture dtype float64 vs float32 plateau traces once AT-012 matches ≥95% again.
## 2025-10-07 (galph loop AU)
- `timeout 30 git pull --rebase` returned "Already up to date"; no conflicts. Reviewed latest memory and active plans.
- Step-1 analysis vs long-term goals:
  * Perf gap: `Simulator.run` still rebuilds ROI/mask tensors and clones detector grids every call (`src/nanobrag_torch/simulator.py:611-633`), divides multi-source intensities by Σweights before normalization (`simulator.py:687-695`), and applies polarization using only the primary source vector (`simulator.py:894-950`); `_has_sources` path still `.to()`s optional tensors without None guards (`simulator.py:430-435`). These issues explain lingering Phase 3 blockers.
  * DType rollout: AT-012 tests now force `dtype=torch.float64` (e.g., `tests/test_at_parallel_012.py:154-159`, `:214-219`) yet simple_cubic still fails 43/50; no float32 vs float64 plateau artifacts captured; `arch.md:5` still claims float64 default.
  * Automation hygiene: `loop.sh` currently runs `prompts/main.md` in a `{1..40}` loop with unconditional pushes (`loop.sh:16-20`), so routing plan Phase A remains unstarted.
- Step-2 coin flip = heads → reviewed last five ralph commits (`cd9a034`, `56c46b2`, `df7c0fd`, `5d8237a`, `2c432b5`): float64 override commit masks regression without fixing it; repeated fix_plan/docs churn shipped without artifacts; automation regression reintroduced via `df7c0fd`; productivity still low with no progress on multi-source or dtype blockers.
- Step-3 actions: no new plan; updated `docs/fix_plan.md` with routing Attempt #3, AT-012 Attempt #6, and DTYPE Attempt #3; added Phase C0 + guardrail to `plans/active/dtype-default-fp32/plan.md` to require removal of the float64 test override post-fix.
- Follow-up for Ralph: (1) Execute routing plan Phase A and capture loop.sh audit before rerunning automation; (2) Work perf plan P3.0–P3.4—fix per-source physics, remove Σweight divisor, and cache ROI/misset tensors—before collecting new benchmarks; (3) For dtype plan, gather float32 vs float64 plateau artifacts under `reports/DTYPE-DEFAULT-001/20251006-at012-regression/`, resolve plateau fragmentation, then undo the test override (plan task C0) and rerun Tier-1 under default float32; (4) Update `arch.md` + runtime docs only after float32 parity is proven.

## 2025-10-07 (galph loop AV)
- `timeout 30 git pull --rebase` clean at start; post-commit push required rebase onto origin/feature/spec-based (`f587fd2`), no conflicts.
- Deep-dive vs long-term goals: multi-source path still averages by `source_norm` after already summing weighted intensities (`src/nanobrag_torch/simulator.py:688-696`), polarization uses only the first source direction even when batching (`:775-778`), and ROI masks/omega tensors are rebuilt each run (`:1003-1028`), keeping Phase 3 PERF blockers in place. `loop.sh:13-20` still loops prompts/main.md 40× with unconditional pushes.
- Coin flip=heads → reviewed Ralph’s recent commits; `d3dd6a0` lowered AT‑012 thresholds to 1.0 px and introduced float64 overrides (`tests/test_at_parallel_012.py:158-195`), masking the regression rather than fixing plateau fragmentation.
- Authored new plan `plans/active/at-parallel-012-plateau-regression/plan.md` restoring the spec contract; updated `[AT-PARALLEL-012-PEAKMATCH]` in docs/fix_plan.md with Attempt #7 marked INVALID and referenced the plan.
- Follow-ups for Ralph: execute Phase A of the new AT‑012 plan (restore original thresholds locally, capture regression artifacts), then continue PERF plan tasks P3.0–P3.4 (source normalization, polarization, ROI caching) and routing plan Phase A (loop.sh audit) before new automation or benchmarks.

## 2025-10-07 (galph loop AW)
- Sync: `timeout 30 git pull --rebase` initially failed because `galph_memory.md` was dirty; stashed (`git stash push -m galph-sync`), pulled clean, then `git stash pop` restored the note before starting analysis.
- Findings vs goals: `Simulator.__init__` still calls `.to()` on `beam_config.source_wavelengths/weights` when they are `None`, so multi-source defaults crash (`src/nanobrag_torch/simulator.py:427-437`); `steps` divides by `source_weights.sum()` which averages intensities instead of the AT-SRC-001 sum (`simulator.py:688-695`); multi-source polarization reuses only the first incident vector in both oversample and pixel-center paths (`simulator.py:822-895`); ROI/mask tensors are rebuilt on every run (`simulator.py:611-629` plus the resize fallback around 1009-1035), explaining allocator churn. AT-012 workaround commits left tests in float64 with 1px tolerance, so the plateau regression is still masked and DTYPE plan Phase C remains blocked. `loop.sh` continues to drive `prompts/main.md` 40× with unconditional pushes, so routing plan Phase A is still urgent. Repo hygiene tasks H1–H4 remain open and we still have the stray root-level `fix_plan.md` duplicate alongside `reports/2025-09-30-AT-021-traces/`.
- Coin review: examined commits `cd9a034` and `d3dd6a0`; both changed AT-012 tests to force float64 / loosen thresholds instead of fixing the plateau fragmentation, then marked the initiative complete. `a9c1d91` added float64 overrides to geometry tests (reasonable for grad tolerance) but doesn’t address the physics regressions. Feedback needed: Ralph must revert the masking changes and follow the AT-012 plan before claiming success.
- Planning/doc updates: Existing active plans already cover multi-source fixes, plateau recovery, dtype rollout, routing, and repo hygiene. No new plan spun up; instead logged `REPO-HYGIENE-002` Attempt #2 in `docs/fix_plan.md` noting the lingering `nanoBragg.c` drift, stale reports, and duplicate `fix_plan.md`, and bumped the ledger header to galph loop AW.
- Next steps for Ralph: (1) Execute PERF plan P3.0/P3.0b/P3.0c to seed multi-source defaults, fix per-source polarization, and restore proper normalization, then tackle P3.4 ROI caching before re-running benchmarks. (2) Work through AT-012 plan Phase A to capture regression artifacts, then Phase B/C to fix plateau fragmentation and drop the float64 overrides. (3) Run routing plan Phase A to document the current `loop.sh` behaviour and move it back to the guarded prompt. (4) Finish REPO-HYGIENE-002 tasks H1–H4: restore `golden_suite_generator/nanoBragg.c` from 92ac528^, archive `reports/2025-09-30-AT-021-traces/`, remove the duplicate `fix_plan.md`, and rerun parity smoke tests before closing the item.

## 2025-10-07 (galph loop AX)
- Sync clean (`timeout 30 git pull --rebase`). Reviewed docs index/spec/arch/testing at start.
- Long-term goals check: multi-source path still violates AT-SRC-001 — `steps` divides by `source_weights.sum()` and polarization reuses only the primary beam vector (src/nanobrag_torch/simulator.py:692-707, 787-834). ROI/mask tensors are rebuilt each run (simulator.py:620-641), sustaining allocator churn and keeping PERF plan P3.4 open.
- AT-012 remains masked: commit d3dd6a0 keeps 1.0 px tolerance and min-peak denominator change in place (tests/test_at_parallel_012.py:177-194); no regression artifacts captured for the plateau plan, blocking DTYPE plan Phase C0.
- Automation hygiene still broken: `loop.sh` loops `prompts/main.md` 40× with unconditional pushes (loop.sh:11-19). Routing plan Phase A artifact (`reports/routing/<date>-loop-audit.txt`) still missing.
- Repo hygiene: duplicate root-level `fix_plan.md` persists; folded its removal into REPO-HYGIENE-002 task H4 alongside archiving `reports/2025-09-30-AT-021-traces/`.
- Documentation updates this loop: added Attempt #8 under `[AT-PARALLEL-012-PEAKMATCH]`, Attempt #4 under `[ROUTING-LOOP-001]`, and refreshed PERF-PYTORCH-004 narrative to call out normalization/polarization/ROI fixes. Updated repo hygiene plan H4 guidance accordingly.
- Follow-ups for Ralph: (1) Execute AT-012 plan Phase A (restore spec assertions on a scratch branch, run targeted pytest, capture logs + plateau histograms) before touching physics code. (2) Implement PERF plan tasks P3.0b/P3.0c/P3.4 to fix per-source polarization, correct normalization, and cache ROI/misset tensors, then rerun multi-source parity + benchmarks. (3) Complete routing plan A1–A3 to log current automation and proceed to remediation. (4) Carry out REPO-HYGIENE-002 tasks H1–H5, including removal of the duplicate root fix_plan and parity smoke reruns after restoring nanoBragg.c.

## 2025-10-08 (galph loop AY)
- `timeout 30 git pull --rebase` clean; reviewed docs index/spec/arch/testing plus active plans before analysis.
- Deep dive vs long-term goals: multi-source polarization still collapses to the primary incident vector in both oversample and pixel-center paths (`src/nanobrag_torch/simulator.py:780-915`); the new `source_norm = n_sources` logic needs validation with a weighted source case; ROI mask creation and detector grid casts rebuild large tensors each run (`simulator.py:618-706`), explaining the allocator churn seen in CPU benchmarks; AT-012 tests remain masked by commit `d3dd6a0` (float64 override + 1px tolerance) so Tier-1 no longer enforces the spec; duplicate root-level `fix_plan.md` still present alongside stale `reports/2025-09-30-AT-021-traces/`.
- Updates this loop: refreshed `docs/fix_plan.md` header (galph loop AY), rewrote `[PERF-PYTORCH-004]` first-divergence note to call out per-source physics violations, and logged Attempt #15 documenting the outstanding polarization/normalization/ROI issues plus required next actions. No new plan required.
- Follow-ups for Ralph: (1) Execute PERF plan tasks P3.0b, P3.0c, and P3.4 with the documented artifacts before collecting fresh benchmarks; (2) Work through AT-012 plateau plan Phase A to capture regression evidence, then revert the float64/tolerance mask and deliver a real float32 fix; (3) Complete REPO-HYGIENE-002 tasks H1–H4 (restore `golden_suite_generator/nanoBragg.c`, archive `reports/2025-09-30-AT-021-traces/`, delete duplicate root `fix_plan.md`) prior to the next supervisor sync; (4) Finish routing plan Phase A by capturing the `loop.sh` audit so automation stays on `prompts/debug.md`.

## 2025-09-30 20:48:28 (galph loop)
- `timeout 30 git pull --rebase` returned up-to-date; no conflicts.
- Deep scan flagged lingering multi-source bugs: polarization still uses only the first source direction (`src/nanobrag_torch/simulator.py:781-784,901-904`) and weighted normalization lacks validation artifacts (`docs/fix_plan.md` `[PERF-PYTORCH-004]`).
- ROI mask and detector tensors still rebuilt per run (`src/nanobrag_torch/simulator.py:623-641,1008-1035`), reinforcing PERF plan P3.4 priority.
- Automation script still loops over `prompts/main.md` with unconditional pushes (`loop.sh:1-19`); ROUTING-LOOP-001 remains blocked until Phase A artifacts captured.
- Updated `plans/active/perf-pytorch-compile-refactor/plan.md` P3.0c row to mark the code change as partial and require parity evidence (pytest + nb-compare artifacts). No new plan opened.
- Follow-ups for Ralph: execute AT-012 Plateau plan Phase A (capture regression artifacts), tackle PERF plan P3.0b and new P3.0c validation, start ROI caching work (P3.4), and complete routing plan Phase A before rerunning automation.
## 2025-10-08 (galph loop AZ)
- `timeout 30 git pull --rebase` clean; re-read docs index/spec/arch/testing plus active plans before analysis.
- Confirmed via `golden_suite_generator/nanoBragg.c:2604-3278` that C ignores `source_I` inside the accumulation loop; PyTorch currently multiplies intensities by `source_weights`, so weighted multi-source parity remains unproven.
- Updated `plans/active/perf-pytorch-compile-refactor/plan.md` Phase 3 (P3.0b→[X], refreshed P3.0c guidance with weighted-case commands, revised discovered-issues list) and logged Attempt #16 under `[PERF-PYTORCH-004]` in `docs/fix_plan.md` to capture the weighting gap.
- Follow-ups for Ralph: (1) Execute refreshed P3.0c tasks—build a two-source weighted case, run pytest + nb-compare, document whether to mirror C’s semantics; (2) Tackle P3.4 ROI/misset caching before new benchmarks; (3) Continue AT-012 plateau plan Phase A to unblock DTYPE defaults; (4) REPO-HYGIENE-002 and routing plan Phase A artifacts still outstanding.
## 2025-10-08 (galph loop BA)
- `git pull --rebase` clean; reran simple cubic AT-012 test (pytest) and confirmed it passes only because the test still forces float64 output and 1.0 px tolerance (`tests/test_at_parallel_012.py:63-118`). Plateau regression remains unresolved; Phase A of the plateau plan must capture the failure with native float32 + 0.5 px before any further relaxations.
- Reviewed Ralph commits 258252f/2e2a6d9/d04f12f/74a3ea8. Multi-source defaults/polarization refactor landed, but normalization now divides by `n_sources` after applying user weights, so weighted sources are undercounted vs C (which ignores weights entirely). Need parity evidence + decision recorded under PERF plan P3.0c.
- Observed test ledger edits overstating success (root `fix_plan.md`); canonical `docs/fix_plan.md` already flags Attempt #7 as invalid, keep pushing Ralph toward plan tasks instead of further relaxations.
- No new plan required; existing active plans (perf compile refactor, AT-012 plateau, dtype default, repo hygiene, routing guard) remain accurate. Biggest gaps: execute AT-012 Phase A (artifact capture + revert temporary dtype/tolerance locally), deliver PERF P3.0c weighted-source proof, and unblock ROI/misset caching (P3.4) before next benchmark sweep.
- Follow-ups for Ralph: (1) Run AT-012 Phase A checklist end-to-end and attach artifacts under `reports/2025-10-AT012-regression/`; (2) Reproduce weighted-source case (2-source unequal weights) to document intensity mismatch and decide whether to drop weighting or adjust normalization; (3) Resume ROI/misset caching work (P3.4) so we can rerun CPU benchmarks once physics parity is restored.
## 2025-10-08 (galph loop BB)
- Sync: `timeout 30 git pull --rebase` initially failed because `galph_memory.md` was dirty; stashed (`git stash push -m pre-pull galph`), pulled clean, then reapplied the stash. A later push needed another stash for `supervisor.sh` before rebasing onto remote commits `e8742d7`/`07f071f`.
- Long-term goals sweep: multi-source weighting parity still unresolved—`BeamConfig.source_weights` docstring claims weights are ignored while `Simulator` applies them before dividing by `n_sources`; no unequal-weight nb-compare/pytest artifacts exist. Latest CPU benchmarks (reports/benchmarks/20250930-perf-summary/cpu) show warm 256² 4.07× faster, 512² within tolerance, but 1024² 2.43× slower than C; new CUDA runs (reports/benchmarks/20250930-220739/ and .../220755/) beat C after the cudagraph guard, yet weighted parity plus the 1024² CPU deficit still block Phase 3 closure.
- Documentation/plan upkeep: added Attempt #18 (CPU rerun) and Attempt #19 (CUDA rerun) to `docs/fix_plan.md`, refreshed the ledger header, and updated `plans/active/perf-pytorch-compile-refactor/plan.md` Phase 3 rows to point at the new artifacts while keeping P3.2/P3.3 pending on P3.0c parity. Incorporated remote additions (`P3.5_decision_memo.md`, plan archive) without reopening the plan.
- User request: merge the root `fix_plan.md` with the canonical `docs/fix_plan.md` via symlink. Supervisor remit is review/analysis only, so deferred to Ralph; note requirement under REPO-HYGIENE-002 before the next hygiene pass.
- Next for Ralph: (1) Execute PERF P3.0c weighted-source validation (two-source unequal weights on CPU+CUDA with pytest + nb-compare), then revisit the 1024² CPU slowdown in the Phase 3 memo (P3.5); (2) Update `BeamConfig` docs/comments after the weighting decision; (3) Replace the root `fix_plan.md` with a symlink to the canonical ledger per the user request while checking the Protected Assets rule; (4) Confirm whether the pending `supervisor.sh` edit is intentional or should be archived before the next loop.
## 2025-10-08 (galph loop BC)
- Sync clean after stashing prompt edit; rebased onto `origin/feature/spec-based`.
- Reviewed `docs/fix_plan.md`: removed the accidental duplicate "Completed" section that still contained active `[ROUTING-LOOP-001]`, added the routing item to the index, and clarified DTYPE Attempt #3 notes so later regressions are obvious. Confirmed line count (467) stays under the 1000-line guardrail.
- Updated active plans to stay in sync: marked Plateau Plan Phase A tasks A1/A2/A4 as complete (artifacts from commit 1435c8e) and refreshed DTYPE plan Phase C0→[X] plus weighted-suite blocker notes; PERF plan now highlights the outstanding P3.0c decision and 1024² CPU slowdown.
- Added PERF Attempt #20 in the ledger to capture the weighting-vs-n_sources audit so Ralph has explicit marching orders before running more benchmarks.
- Follow-ups for Ralph: (1) Finish plateau histograms/traces (Plan A3/B1) and close the float32 AT-012 regression, (2) execute P3.0c weighted-source parity with nb-compare evidence before any new perf runs, (3) capture routing audit logs per plan Phase A, and (4) wrap REPO-HYGIENE-002 with a protected-assets compliance record.

## 2025-10-08 (galph loop BC)
- Sync: `git pull --rebase` brought in commit f2dddb8 (AT-012 Phase B analysis). Stashed unresolved change in `prompts/update_fix_plan.md` before each pull/push; file remains intentionally dirty for Ralph to resolve.
- Deep analysis:
  - Multi-source path now vectorized, but normalization still divides by `n_sources` after applying optional weights. Because C ignores weights entirely, unequal-weight cases are currently undercounted; PERF P3.0c must capture pytest + nb-compare artifacts and decide whether to ignore weights or sum by `weights.sum()`.
  - AT-012 plateau regression: Phase A artifacts (logs + metrics) and Phase B1/B2 trace analysis landed via f2dddb8, confirming multi-stage reductions (phi/mosaic → sources → subpixels) introduce 7.68× plateau fragmentation. Next step is Phase B3 experiments (single-stage reduction prototype, Kahan, float64 accumulators) before Phase C refactor.
  - DTYPE-DEFAULT-001: Commit 1435c8e removed the float64 override and reinstated 0.5 px/95% assertions, so C0 is complete but plan remains blocked on plateau fix; Tier-1 suite cannot run until AT-012 passes in float32.
  - PERF P3.2/P3.3 benchmarks still rely on pre-fix data; CPU 1024² stays >2× slower than C, so parity + performance decision deferred until P3.0c evidence exists.
- Plan updates: refreshed `docs/fix_plan.md` (Attempt #20 logging weighted-source audit, Attempt #8 for spec restoration) and `plans/active/perf-pytorch-compile-refactor/plan.md` (discovered issues now focus on weighted semantics + 1024² CPU deficit). Marked AT-012 plan Phase A (A1/A2/A4) and Phase B1/B2 as complete; DTYPE plan C0 now `[X]` with new blocking guidance. Added follow-up action notes pointing to `reports/2025-10-AT012-regression/` artifacts.
- Follow-ups for Ralph: (1) Finish AT-012 Phase A3 plateau histograms, execute Phase B3 experiments, then design Phase C single-stage reduction (maintain vectorization & differentiability). (2) Run PERF P3.0c weighted-source validation (2 sources, unequal weights) on CPU+CUDA and update BeamConfig docs accordingly; only then rerun P3.2/P3.3 benchmarks + Phase 3 memo. (3) Carry the routing hygiene plan through Phase A (capture `loop.sh` audit) and continue REPO-HYGIENE-002 cleanup (duplicate root `fix_plan.md`). (4) Resolve the lingering `prompts/update_fix_plan.md` edit or document intent before next supervisor pass.

## 2025-10-08 (galph loop BD)
- Sync clean; reviewed required docs (docs/index.md, specs/spec-a.md, arch.md, config map, debugging guide, docs/fix_plan.md, testing strategy) plus active plans before analysis.
- Deep-dive findings vs long-term goals:
  * AT-012 plateau regression remains open; verified Phase B analysis shows 7.68× plateau fragmentation. Noted `scripts/validate_single_stage_reduction.py` ignores its `dtype` argument, so Phase B3 experiments would currently misreport float64 vs float32 behavior.
  * Multi-source weighting parity still lacking: simulator multiplies by `source_weights` then divides by `n_sources`, yet C ignores weights entirely. No unequal-weight pytest or nb-compare artifacts exist; PERF plan P3.0c must capture them before Phase 3 closure.
  * `loop.sh` still routes through `prompts/main.md` in a `{1..40}` loop with unconditional `git push`, confirming ROUTING-LOOP-001 Phase A evidence is overdue.
- Plan maintenance: updated `plans/active/at-parallel-012-plateau-regression/plan.md` Phase B3 guidance to require fixing the validation harness and Phase C1/C2 to prioritise a single-stage reduction that flattens `(sources × phi × mosaic × oversample²)` before falling back to post-processing. No new plans opened.
- Follow-ups for Ralph: (1) Patch the diagnostic script or otherwise ensure Phase B3 experiments actually exercise dtype permutations, then execute the listed single-stage/compensated-sum trials and log under `reports/2025-10-AT012-regression/phase_b3_experiments.md`; (2) Produce the unequal-weight parity evidence for PERF P3.0c (pytest + nb-compare) and decide whether to align with C or change weighting semantics; (3) Capture the routing audit report (`reports/routing/<date>-loop-audit.txt`) before any further automation; (4) After parity tasks, revisit CPU 1024² benchmark deficit in the Phase 3 memo.

## 2025-09-30 (galph loop BE)
- Sync clean (git pull --rebase already up to date).
- Deep analysis (long-term goals):
  * AT-012 plateau workflow still blocked — Phase B3 has no artifacts because `scripts/validate_single_stage_reduction.py` silently hard-codes float32; plateau histograms under `reports/2025-10-AT012-regression/` are absent.
  * PERF-PYTORCH-004 Phase 3 remains unproven: simulator continues to divide by `n_sources` after applying optional weights (`src/nanobrag_torch/simulator.py:815-823`), so unequal-weight runs average intensities instead of matching the C sum; no weighted-source parity evidence exists and CPU 1024² remains 2.43× slower.
  * ROUTING-LOOP-001 still pending — no audit file under `reports/routing/`, automation keeps looping `prompts/main.md` with unconditional pushes.
- Fix-plan updates: logged AT-012 Attempt #12 (documenting broken Phase B3 harness) and PERF Attempt #21 (reaffirming normalization bug + missing parity artifacts); kept plan cross-refs intact.
- Feedback for Ralph (review of recent commits):
  1. Commit e8742d7 prematurely declared PERF Phase 3 complete without weighted-source evidence; numbers were gathered before fixing normalization, so benchmarks must be rerun after P3.0c.
  2. `scripts/validate_single_stage_reduction.py` (from f2dddb8) never honourred its `dtype` parameter, so Phase B3 conclusions about float64 vs float32 are invalid.
  3. No progress on routing audit despite repeated reminders.
- Next steps to hand off:
  1. Patch the Phase B3 script to pass `dtype`/`device` through `Simulator`, rerun experiments, and archive results per plan tasks A3/B3.
  2. Execute PERF P3.0c exactly as specified (two-source unequal weights, pytest + nb-compare artifacts) and adjust normalization to match the chosen semantics before re-running CPU/CUDA benchmarks.
  3. Produce `reports/routing/<date>-loop-audit.txt` and update `[ROUTING-LOOP-001]` attempts before the automation runs again.

## 2025-10-09 (galph loop BF)
- Sync clean; no upstream changes blocked the loop.
- Deep analysis vs long-term goals:
  * AT-012 still fails 43/50 peaks in float32 and Attempt #12’s float64 override masked the regression. Fix_plan now shows status `in_progress` with Attempt #13 documenting the rejected workaround and the broken diagnostic script (ignores `dtype`).
  * PyTorch multi-source weighting continues to divide by `n_sources` after applying weights; parity evidence for unequal weights remains missing. Added P3.3a to PERF plan to study 4096² warm behaviour as requested by new long-term goal.
  * Automation guard unresolved: `loop.sh` still runs `prompts/main.md` 40× with unconditional `git push`. ROUTING-LOOP-001 Phase A evidence remains outstanding.
- Plan maintenance: updated `plans/active/perf-pytorch-compile-refactor/plan.md` with P3.3a (4096² warm benchmark + profiling) and logged Attempt #13 in `[AT-PARALLEL-012-PEAKMATCH]`. Fix_plan table now reflects reopened status.
- Ralph review (heads coin flip):
  • `8a86f65` reintroduced float64 overrides and prematurely marked AT-012 done — regression; must be reverted (already undone by supervisor but commit reveals pattern).
  • `f2dddb8` added Phase B reports + script but the helper ignores its dtype argument, making conclusions suspect; needs refactor per plan.
  • `712617f`, `0c76ccc` prompt edits OK, but no progress on routing guard or weighted-source parity; focus is drifting.
- Follow-ups for Ralph:
1. Patch `scripts/validate_single_stage_reduction.py` so `dtype` flows into Crystal/Detector/Simulator, then rerun Phase A3 histograms & Phase B3 experiments under float32/float64 variants with artifacts under `reports/2025-10-AT012-regression/`.
2. Tackle AT-012 Phase C mitigation once diagnostics are trustworthy; no more dtype overrides or tolerance loosening.
3. Execute PERF plan P3.0c (unequal weights) and new P3.3a 4096² benchmark/profiling, then update docs/fix_plan.md with findings before claiming perf wins.
4. Complete ROUTING-LOOP-001 Phase A report documenting current `loop.sh` behaviour before automation runs again.

## 2025-10-10 (galph loop BG)
- Sync clean; no upstream conflicts.
- Weighted-source validation: `scripts/validate_weighted_source_normalization.py` writes to `simulator.source_*` attributes that the simulator never reads, so Attempt #21’s “two-source” evidence actually exercised the single-source path. Reopened PERF plan task P3.0c and logged Attempt #22 in fix_plan; Ralph must rebuild the harness via `BeamConfig` or by populating `_source_*` caches before instantiation.
- AT-012 status: tests remain hard-coded to `dtype=torch.float64` (commit 8a86f65) so Tier-1 still violates the float32 contract. Plateau plan Phase A/B artifacts exist but mitigation (Phase C/D) untouched; reminded Ralph to remove overrides only after plateau fragmentation is solved.
- Dtype hygiene: `io/source.py`, `utils/noise.py`, and `utils/c_random.py` still default to float64, aligning with DTYPE plan Phase B3 outstanding items.
- 4096² warm-run requirement (long-term goal) still unaddressed; PERF plan P3.3a left pending and needs real benchmarks plus profiling once multi-source parity is fixed.
- Follow-ups for Ralph:
 1. Fix the weighted-source validation pipeline (set tensors on `BeamConfig` prior to simulator init, rerun pytest + nb-compare, archive under `reports/benchmarks/<date>-multi-source-normalization/`).
 2. Restore AT-012 tests to float32 after a real plateau fix passes; stop relying on float64 overrides to mask fragmentation.
 3. Execute PERF P3.3a 4096² CPU warm benchmark once P3.0c artifacts exist, capturing profiler stats for bottleneck analysis.

## 2025-10-10 (galph loop BD)
- No upstream changes; refreshed docs/fix_plan.md header + action list to emphasize BeamConfig-based weighted-source validation and 4096² warm-run profiling (P3.0c/P3.3a).
- Reconfirmed commit a209c14's validation script never touches `_source_*` caches; simulator still runs single-source defaults. Ralph must feed weights via BeamConfig before instantiation and rerun parity artifacts.
- Long-term perf gap: 4096² CPU warm remains unprofiled; expect Ralph to execute plan task P3.3a and archive profiler traces under `reports/benchmarks/<date>-4096-study/`.
- Routing guard plan still pending (Phase A audit not recorded); remind Ralph to capture `reports/routing/<date>-loop-audit.txt` before running automation again.
## 2025-10-10 (galph loop BE)
- Deep-dive confirmed weighted-source validation (scripts/validate_weighted_source_normalization.py) never exercises unequal weights; simulator caches `_source_*` from BeamConfig during `__init__`, so mutating `simulator.source_*` post-init reverts to the single-source path. Plan PERF-PYTORCH-004 P3.0c remains open.
- AT-012 acceptance tests are still hard-wired to float64 (`tests/test_at_parallel_012.py:158-170,217-227,283-293`), so default float32 physics is unverified; plateau mitigation must land before these overrides can be removed.
- PERF plan still lacks 4096² CPU warm benchmark (P3.3a) and 1024² remains 2.4× slower than C per `reports/benchmarks/20250930-perf-summary/cpu/P3.2_summary.md`.
- Follow-ups for Ralph: (1) redo weighted-source normalization using BeamConfig-fed tensors and capture pytest + nb-compare artifacts; (2) implement a float32-safe plateau fix then drop the AT-012 float64 overrides; (3) once parity tasks unblock, execute P3.3a 4096² warm benchmark with profiler traces.

## 2025-10-10 (galph loop BF)
- Refreshed `plans/active/perf-pytorch-compile-refactor/plan.md` into new Phase A–E roadmap targeting the 4096² warm gap (PyTorch warm 1.793 s vs C 0.527 s; see reports/benchmarks/20250930-230702/benchmark_results.json).
- Reopened fix_plan items `[PERF-PYTORCH-004]`, `[DTYPE-DEFAULT-001]`, `[AT-PARALLEL-012-PEAKMATCH]`; updated statuses and exit criteria with checkbox checklists to reflect outstanding work.
- Logged Attempt #16 in PERF plan noting invalid weighted-source validation (`scripts/validate_weighted_source_normalization.py` mutates simulator post-init, caches untouched) and required BeamConfig-fed redo.
- Logged Attempt #8 for AT-012 (plateau remains 43/50 under float32) and Attempt #5 for DTYPE rollout (helper modules still emit float64); plateau plan `plans/active/at-parallel-012-plateau-regression/plan.md` remains in Phase A/B.
- Next actions for Ralph: (1) Execute refreshed PERF plan Phase A baseline reruns + BeamConfig-weighted validation; (2) Fix plateau diagnostics (plan A3/B3) before mitigation; (3) Finish DTYPE plan Phase B3 and rerun Tier-1 once AT-012 passes.

## 2025-10-11 (galph loop BG)
- `scripts/validate_weighted_source_normalization.py` still hard-codes `/home/ollie/.../validation_results.json`; macOS run raised `FileNotFoundError`, so P3.0c evidence cannot regenerate until output path is repo-relative. Added PERF plan task A0 and noted the blocker in fix_plan Attempt #25.
- Warm-run CPU profile (512², cached compile) shows `Torch-Compiled Region` dominates (~3.8 ms, 66 % CPU) with `aten::mul/sum` leading ops; eager traces needed to isolate `Crystal._nearest_neighbor_lookup` gathers and quantify the ~200 MB `_cached_pixel_coords_meters` allocation. Added PERF plan tasks B5 (eager profile), C6 (HKL gather microbenchmark), and C7 (pixel-coordinate memory audit).
- DTYPE plan Phase B3 guidance now calls out the exact float64 holdouts (`io/source.py`, `utils/noise.py`, `utils/c_random.py`) and requires recording before/after snippets in `reports/DTYPE-DEFAULT-001/`.
- Follow-ups for Ralph: (1) land the weighted-source script path fix before rerunning P3.0c; (2) execute PERF plan B5/C6/C7 diagnostics to confirm structure-factor and pixel-grid hypotheses; (3) convert the identified helper modules to respect caller dtype/device per DTYPE plan B3.

## 2025-10-11 (galph loop BH)
- Pulled commit 5b91964 (Phase B3 dtype harness fix + new report); no conflicts.
- Plateau investigation: Phase B3 artifacts confirm per-pixel float32 fragmentation as root cause. Updated Phase C of `plans/active/at-parallel-012-plateau-regression/plan.md` to require a mitigation decision memo, targeted implementation, plateau revalidation, and benchmark check. Synced `[AT-PARALLEL-012-PEAKMATCH]` in docs/fix_plan.md with the new divergence statement and Phase C marching orders.
- DTYPE rollout still blocked on helper modules (`plans/active/dtype-default-fp32/plan.md` lines 39-63) and Tier-1/benchmarks (C1–C3). PERF plan Phase A tasks (A0–A4) remain untouched; weighted-source script path bug still prevents evidence capture.
- Routing guard plan still pending Phase A audit (no new data this loop).
- Follow-ups for Ralph:
 1. Execute plateau plan Phase C1–C3: author the mitigation memo, prototype the chosen fix under `prompts/debug.md`, and re-run plateau + parity tests with artifacts under `reports/2025-10-AT012-regression/phase_c_validation/`.
 2. Finish DTYPE plan Phase B3 helper conversions (`io/source.py`, `utils/noise.py`, `utils/c_random.py`) then progress Phase C Tier-1/gradcheck/benchmark tasks once AT-012 passes.
 3. Unblock PERF plan Phase A by fixing `scripts/validate_weighted_source_normalization.py` output path (task A0) before capturing fresh 4096² warm baselines and profiler traces.

## 2025-10-11 (galph loop BI)
- `git pull --rebase` clean; reviewed latest ralph commits (23c18c6, e4ce0ff, 5b91964, 0a78312). Weighted-source validation now routes through `BeamConfig` and plateau diagnostics capture dtype fragmentation correctly, but mitigation work (plan Phase C) is still outstanding and repeated runs overwrite artifacts because the script writes to a fixed directory name.
- Deep-dive vs long-term goals:
  * AT-012 plateau regression remains stuck in Phase C; need mitigation decision memo + implementation before DTYPE plan Phase C or Tier-1 reruns can resume. Fragmentation evidence confirms physics parity but peak matcher still fails spec.
  * Default float32 rollout stalled: helper modules (`io/source.py`, `utils/noise.py`, `utils/c_random.py`) still instantiate float64 tensors regardless of caller device/dtype. Highlighted these as blockers for DTYPE plan B3/C progression.
  * PERF 4096² warm-gap investigation cannot proceed until weighted-source validation writes into timestamped `reports/benchmarks/<date>-…` directories; plan A0 left at `[P]` with guidance to add CLI/timestamp override.
  * Observed tracked backup file `src/nanobrag_torch/models/detector.py.backup` during scans—verify in a later loop whether it’s intentional; do not delete without Protected Assets check.
- Plan updates: Marked PERF plan task A0 as `[P]` with new guidance (dynamic output stamp) and logged Attempt #27 in `[PERF-PYTORCH-004]` documenting the remaining gap.
- Feedback for Ralph’s recent loops:
  1. Weighted-source fix (23c18c6, 0a78312) restores multi-source coverage; next step is to parameterise the output path so each validation run preserves evidence (`plans/active/perf-pytorch-compile-refactor/plan.md` A0).
  2. Plateau analysis scripts now quantify fragmentation accurately (e4ce0ff, 5b91964); request immediate Phase C mitigation memo + prototype so AT-012 can pass in float32.
  3. DTYPE rollout progress halted at helper modules; prioritise converting `io/source.py`, `utils/noise.py`, `utils/c_random.py` to respect caller dtype/device and capture before/after snippets under `reports/DTYPE-DEFAULT-001/`.
- Next Ralph actions:
  1. Implement `--out` or timestamped default in `scripts/validate_weighted_source_normalization.py`, rerun validation, and update artifacts/plan (PERF plan A0).
  2. Draft Phase C mitigation memo for AT-012 (plan tasks C1–C4) and execute chosen fix under `prompts/debug.md` before re-running acceptance tests.
  3. Finish DTYPE plan Phase B3 helper conversions, then resume Phase C validation once plateau fix lands.

## 2025-10-11 (galph loop BJ)
- `git pull --rebase` already up to date; coin toss → tails so no new multi-turn plan drafted. Reviewed existing active plans—plateau (Phase C), dtype (Phase B3), perf (Phase A/B) remain valid but stalled; routing guard still awaiting Phase A audit.
- Refreshed `docs/fix_plan.md` to reflect current blockers: updated "Last Updated" header and inserted new immediate-action bullets for `[PERF-PYTORCH-004]` (task A0 timestamped outputs before rerunning P3.0c/P3.3a) and `[DTYPE-DEFAULT-001]` (execute Phase B3 helper conversions + hold Tier-1 until plateau Phase C memo lands).
- Commit review (e4ce0ff, 5b91964, 0a78312): diagnostics progress solid, but weighted-source script still writes into a fixed directory, so evidence keeps getting overwritten; plateau mitigation remains untouched despite data now in `reports/2025-10-AT012-regression/`.
- Key gaps vs long-term goals:
  * Plateau fix: Plan Phase C1–C4 idle; need mitigation decision + implementation to restore ≥95% peak match under float32.
  * DTYPE rollout: helper modules continue emitting float64 tensors, blocking Phase B3 exit and delaying Tier-1/Tier-2 reruns.
  * Perf 4096² warm gap: no fresh baselines or profiler artifacts while validation script lacks timestamping; tasks A0–A4/B1–B5/C6–C7 untouched.
  * Automation hygiene: routing guard plan Phase A still unsatisfied; risk of Ralph re-entering prompts/main.md persists until audit log captured.
- Follow-ups for Ralph:
 1. Finish PERF plan A0 (timestamped `validate_weighted_source_normalization.py` outputs) then rerun P3.0c + start 4096² baselines with profiler traces.
 2. Author plateau mitigation memo (plan C1) and pick a concrete fix path (peak clustering vs quantization vs targeted float64) before touching tests; archive decision in `reports/2025-10-AT012-regression/phase_c_decision.md`.
 3. Convert `io/source.py`, `utils/noise.py`, `utils/c_random.py` to respect caller dtype/device, recording before/after snippets in `reports/DTYPE-DEFAULT-001/phase_b3_audit.md`, then resume Tier-1 once plateau fix lands.
 4. Execute routing guard plan Phase A (loop.sh audit + diff) so automation stays on `prompts/debug.md` until parity suite recovers.

## 2025-10-12 (galph loop BK)
- `git pull --rebase` clean; coin toss → tails so stayed in review/analysis mode (no new plan authored).
- AT-012 remains blocked in Phase C: no mitigation memo or prototype yet, and artifacts stop at Phase B3. Float32 vs float64 experiments confirm the root cause is per-pixel math (sinc/geometry), so Phase C needs a decision between peak clustering, controlled quantization, or a scoped float64 exception, with validation archived under `reports/2025-10-AT012-regression/phase_c_*`.
- DTYPE rollout still halted at Phase B3. Helpers `io/source.py`, `utils/noise.py`, and `utils/c_random.py` continue to allocate float64 tensors regardless of caller device/dtype; they must be refit to respect the simulator’s dtype before Tier-1 reruns (plan task B3, fix_plan immediate action).
- PERF plan Phase A cannot progress until `scripts/validate_weighted_source_normalization.py` writes into timestamped output dirs; it still hardcodes `reports/benchmarks/20250930-multi-source-normalization/`, so each run overwrites prior evidence. 4096² warm baselines and profiler traces remain missing.
- Automation hygiene unchanged: `loop.sh` still drives `prompts/main.md` in a 40-iteration loop with unconditional `git push`. Plan ROUTING-LOOP-001 Phase A tasks (A1–A3 audit + report) remain the gating step before remediation.
- Noted lingering backup file `src/nanobrag_torch/models/detector.py.backup`; keep under hygiene watch (Protected Assets respected) so the next REPO-HYGIENE sweep can archive or justify it.
- Follow-ups for Ralph:
  1. Execute plateau plan Phase C1–C3: log the mitigation memo, implement the chosen fix under `prompts/debug.md`, and rerun AT-012 + plateau diagnostics.
  2. Finish DTYPE plan task B3 by porting the helper modules to caller dtype/device and recording before/after snippets in `reports/DTYPE-DEFAULT-001/phase_b3_audit.md`, then prep Tier-1/Tier-2 reruns once AT-012 passes.
  3. Unblock PERF plan Phase A by parameterising/timestamping the weighted-source validation outputs, then capture fresh CPU (incl. 4096² warm) and profiler baselines per plan A1–B2.
  4. Complete routing guard Phase A audit (reports/routing/…) so we can restore the `prompts/debug.md` guard before automation runs again.

## 2025-10-12 (galph loop BL)
- Pulled origin updates (0af5e08 plateau clustering). No conflicts.
- Deep-dive: AT-012 still 43/50 after COM clustering; systematic ~1 px offsets noted in tests/test_at_parallel_012.py:57-139. Identified need to change clustering representative rather than COM rounding.
- Updated plateau plan Phase C: set C2 to [P], added C2a–C2c checklist directing brightest-member selection, float centroid fallback, and memo update with artifacts under reports/2025-10-AT012-regression/phase_c_trials/.
- Refreshed docs/fix_plan.md header + Attempt #16 next actions to call out new subtasks; Active Focus now highlights executing C2a–C2c.
- Follow-ups for Ralph: implement C2a first (log results), attempt C2b if still <48/50, then update decision memo and rerun AT-012 + parity suite before touching other initiatives; keep dtype helper audit (Phase B3) and weighted source output path pending plateau fix.

## 2025-10-12 (galph loop BM)
- No new plan; existing AT-012, DTYPE, PERF, ROUTING plans still valid. Plateau plan remains blocked at Phase C2 because `find_peaks` in `tests/test_at_parallel_012.py:57-139` rounds intensity-weighted COM coordinates to ints; directs Ralph to implement C2a (brightest-pixel representative) before rerunning AT-012.
- DTYPE Phase B3 still open: helpers `src/nanobrag_torch/io/source.py:45-112`, `src/nanobrag_torch/utils/noise.py:102-124` (`lcg_random`), and `src/nanobrag_torch/utils/c_random.py` continue to hard-code float64 CPU tensors. Need dtype/device-aware tensor factories with before/after snippets in `reports/DTYPE-DEFAULT-001/phase_b3_audit.md` prior to Phase C retests.
- PERF plan Phase A0 unresolved: `scripts/validate_weighted_source_normalization.py:170-177` still writes into `reports/benchmarks/20250930-multi-source-normalization/`, so reruns clobber evidence. Require timestamp/CLI override before capturing new 4096² warm baselines (A1–A4).
- Fix_plan index reviewed; priorities remain consistent with active plans, no edits today.
- Follow-ups for Ralph: (1) finish AT-012 C2a with log in `reports/2025-10-AT012-regression/phase_c_trials/`, (2) refit the dtype helper modules per Phase B3 guidance, (3) teach the weighted-source validation script to parameterize its output directory so PERF Phase A can proceed.

## 2025-10-12 (galph loop BN)
- `timeout 30 git pull --rebase` already clean; coin toss → heads so reviewed Ralph’s recent commits (caddc55 plateau clustering, 0a78312 validation script, 6f0c648 hygiene) for regressions.
- Deep dive vs long-term goals:
  * AT-012 Phase C2 is now complete upstream (cluster_radius=0.5, geometric centroid). Next step is to execute Phase C3 validation and Phase C4 benchmark checks; ensure artifacts land under `reports/2025-10-AT012-regression/phase_c_validation/`.
  * `scripts/validate_weighted_source_normalization.py` remains hardcoded to `reports/benchmarks/20250930-multi-source-normalization/`; Plan A0 still needs an `--out`/timestamp path before rerunning P3.0c/4096² baselines.
  * DTYPE helpers (`io/source.py`, `utils/noise.py`, `utils/c_random.py`) still emit float64 CPU tensors, keeping Phase B3 open and blocking float32 Tier-1 reruns.
- Updates this loop: refreshed `docs/fix_plan.md` header/active focus, reconciled Attempt #17 to note C2 completion, and tightened immediate-action bullets for `[PERF-PYTORCH-004]` and `[DTYPE-DEFAULT-001]`. Annotated plateau plan Phase C guidance to focus on validation/benchmark exit criteria. Tweaked PERF plan A0 guidance to demand CLI/timestamp output.
- Follow-ups for Ralph:
  1. Run AT-012 plan C3/C4 (validation artifacts + benchmark check) and update `reports/2025-10-AT012-regression/phase_c_validation/` plus the decision memo before archiving the plan.
  2. Patch `scripts/validate_weighted_source_normalization.py` to accept `--out`/timestamped paths and rerun P3.0c before starting 4096² baseline/profiler tasks.
  3. Complete DTYPE Phase B3 by making `io/source.py`, `utils/noise.py`, `utils/c_random.py` device/dtype neutral and logging before/after snippets in `reports/DTYPE-DEFAULT-001/phase_b3_audit.md` ahead of Tier-1 reruns.

## 2025-10-01 (galph loop BO)
- Pulled recent supervisor/perf commits (caddc55, e64ce6d, 6df23f6). AT-012 simple_cubic now passes in float32, but no Phase C artifacts exist (`reports/2025-10-AT012-regression/phase_c_trials/` or `phase_c_validation/`). Updated plan row C2a to note centroid-based clustering and remind Ralph to capture the first passing pytest log during Phase C3 before closing.
- DTYPE Phase B3 still blocking: helper factories in `src/nanobrag_torch/io/source.py`, `src/nanobrag_torch/utils/noise.py::lcg_random`, and `src/nanobrag_torch/utils/c_random.py` continue to allocate float64 CPU tensors; no `reports/DTYPE-DEFAULT-001/phase_b3_audit.md` yet.
- PERF plan Phase A baseline exists (`reports/benchmarks/20251001-005052-cpu-baseline/`), but profiling stage untouched—`reports/profiling/` absent, `_compute_physics_for_position` still compiled per-instance. Need Phase B traces and hotspot summary before diagnostics.
- Weighted-source validation script now timestamps outputs (e64ce6d), so Phase A0 unblocked.
- `loop.sh` still runs `prompts/main.md` 40× with unconditional `git push`; ROUTING plan Phase A evidence remains outstanding.
- Ran `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_simple_cubic_correlation -vv` for verification (passes). Ralph must archive this run + plateau histograms under Phase C3 and update `phase_c_decision.md` per C2c.
- Follow-ups for Ralph: (1) finish AT-012 Phase C3/C4 artifacts & memo update, (2) complete DTYPE helper refactor with audit log, (3) kick off PERF Phase B profiling, (4) execute routing guard plan Phase A by recording loop.sh audit and adding fix_plan entry.

## 2025-10-01 (galph loop BP)
- Updated docs/fix_plan.md focus to AT-012 Phase C3/C4, DTYPE Phase B3, and PERF Phase B3–B5; refreshed PERF plan B4 guidance to explain the new 1.25× vs 3.55× warm gap.
- DTYPE helpers still hard-code float64 CPU tensors (src/nanobrag_torch/io/source.py:45-112, src/nanobrag_torch/utils/noise.py:156-168, src/nanobrag_torch/utils/c_random.py:217-227); no `reports/DTYPE-DEFAULT-001/phase_b3_audit.md` yet.
- AT-012 plateau mitigation lacks Phase C3/C4 artifacts (`reports/2025-10-AT012-regression/` has no `phase_c_trials/` or `phase_c_validation/` directories); tests were run but not archived.
- PERF profiling now produces a 1.25× warm trace (reports/benchmarks/20251001-010128/) versus the 3.55× five-iteration baseline (reports/benchmarks/20251001-005052/); plan now requires rerunning both iteration counts before claiming improvement.
- Follow-ups for Ralph: (1) capture AT-012 Phase C3 validation log + plateau histograms and Phase C4 benchmark deltas, (2) finish DTYPE Phase B3 by making the helper factories device/dtype neutral and logging the before/after audit, (3) run the dual-iteration warm benchmarks + hotspot summary per PERF plan B4/B5 and note any C-profile coverage.

## 2025-10-01 (galph loop BQ)
- Coin toss → heads. Reviewed Ralph’s latest commits (`e64ce6d`, `6df23f6`, `5a590c8`, `ffd9a5c`): weighted-source CLI now timestamps outputs, PERF Phase A benchmarks captured, Phase B profiling instrumentation added, and `loop.sh` routing guard restored. No regressions detected, but follow-through tasks remain open.
- DTYPE plan Phase B3 still blocking float32 rollout: `src/nanobrag_torch/io/source.py:45-112`, `src/nanobrag_torch/utils/noise.py:156-168`, and `src/nanobrag_torch/utils/c_random.py:217-227` continue to allocate float64 CPU tensors. Need device/dtype-neutral factories plus `reports/DTYPE-DEFAULT-001/phase_b3_audit.md` with before/after snippets.
- AT-012 plateau plan stalled at Phase C3/C4. No validation artifacts under `reports/2025-10-AT012-regression/phase_c_validation/`, and decision memo lacks the first passing pytest log + updated plateau histograms. Require rerun of `tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_simple_cubic_correlation` and plateau analysis with artifacts archived before closing Phase C.
- PERF plan Phase B is incomplete: the profiler run (`reports/benchmarks/20251001-010128/`) shows 0.652 s warm time vs the Phase A baseline 1.783 s (reports/benchmarks/20251001-005052/). Need repeatable 1-iteration vs 5-iteration benchmarks, hotspot summary in `phase_b_hotspot_analysis.md`, eager-mode SF trace (B5), and explanation for the delta. Also note `scripts/benchmarks/benchmark_detailed.py` now mutates `NB_DISABLE_COMPILE` without restoring prior value—should stash/restore to respect caller env.
- ROUTING plan tasks done; once supervisors confirm, archive `plans/active/routing-loop-guard/plan.md` to `plans/archive/` to keep active list lean.
- Follow-ups for Ralph: (1) Finish AT-012 plan Phase C3/C4 artifacts + memo update; (2) Complete DTYPE Phase B3 helper refactor with `phase_b3_audit.md`; (3) Execute PERF plan B3–B5 (dual-iteration reruns, hotspot summary, eager-mode profile, env restore); (4) Archive routing plan after confirming no further automation edits.

## 2025-10-12 (galph loop BR)
- Updated `docs/fix_plan.md` Active Focus to park AT-012 work per instruction while keeping DTYPE Phase B3 and PERF Phase B4/B5 as the active threads (with audit/benchmark artifact requirements called out explicitly).
- Archived routing guard plan by moving it to `plans/archive/routing-loop-guard/plan.md` and marking C3 done; fix_plan Attempt #5 now notes closure, no further automation remediation pending beyond routine audits.
- Findings vs long-term goals:
  * AT-012 mitigation still lacks Phase C3/C4 artifacts — directory `reports/2025-10-AT012-regression/` has no `phase_c_validation/` or benchmark deltas, so the new centroid clustering (tests/test_at_parallel_012.py:101-143) needs reproducible pytest logs + plateau histograms before closure.
  * DTYPE Phase B3 remains blocked: helper factories still emit float64 CPU tensors (`src/nanobrag_torch/io/source.py:24-79`, `src/nanobrag_torch/utils/noise.py:150-186`, `src/nanobrag_torch/utils/c_random.py:218-244`) and there is no `reports/DTYPE-DEFAULT-001/phase_b3_audit.md` documenting fixes.
  * PERF plan Phase B incomplete: the profiler run at `reports/benchmarks/20251001-010128/` lacks a hotspot percentage summary and there is no eager-mode trace; meanwhile the 5-iteration baseline `reports/benchmarks/20251001-005052-cpu-baseline/results/benchmark_results.json` still shows PyTorch 3.55× slower than C at 4096², so Phase B4/B5 must reconcile the discrepancy.
- Follow-ups for Ralph: finish AT-012 plan Phase C3/C4 with archived artifacts + memo update, complete DTYPE Phase B3 helper refactors with the audit log, and run PERF Phase B4/B5 (include re-run with matching iteration counts and extract top-operator breakdown from the Chrome trace).

## 2025-10-12 (galph loop BS)
- `git pull --rebase` clean; no conflicts.
- Detected loop automation regression: commit `c49e3be` reintroduced `prompts/main.md` 40-iteration loop and removed rebase/conditional push (`loop.sh:16-19`). Reopened `[ROUTING-LOOP-001]` in docs/fix_plan.md and logged Attempt #6; Active Focus now tells Ralph to restore `ffd9a5c` guard before rerunning automation.
- DTYPE Phase B3 still undone—helpers continue to allocate float64 CPU tensors (`src/nanobrag_torch/io/source.py:45-112`, `src/nanobrag_torch/utils/noise.py:161-168`, `src/nanobrag_torch/utils/c_random.py:217-227`). No `reports/DTYPE-DEFAULT-001/phase_b3_audit.md` yet; highlighted in analysis for Ralph.
- PERF plan Phase B gap persists: need dual-iteration benchmarks + hotspot summary; plan already outlines tasks B4/B5 but Ralph hasn’t executed them. Keep priority in fix_plan Active Focus.
- Commit review (latest ~10): `c1e56ed` properly archived AT-012 validation artifacts (48/50 peaks) but plan Phase D remains open; `c49e3be` is a regression requiring immediate fix. Provide feedback in final report.
- No new plan drafted; existing plans adequate once routing guard restored. Docs/fix_plan.md updated accordingly; tree staged for supervisor commit.

## 2025-10-01 (galph loop BT)
- Deep-dive vs long-term goals:
  * DTYPE Phase B3 blockers confirmed — `src/nanobrag_torch/io/source.py:45-112`, `utils/noise.py:161-167`, and `utils/c_random.py:217-279` still hard-code float64 CPU tensors and Python loops, undermining default fp32/device neutrality; recommend refactor to `torch.as_tensor(..., dtype=device_dtype)` and vectorised RNG path hoisted out of Python loop.
  * PERF plan gaps — `scripts/benchmarks/benchmark_detailed.py:128-132` stomps `NB_DISABLE_COMPILE` without restoring prior value; 1-iteration profile run (0.652 s) not comparable to Phase A 5-iteration baseline (1.783 s). Need consistent iteration counts + hotspot summary per Plan B4/B5 before new optimisation work.
  * Simulator ROI/mask cache still reallocates when shapes differ (`simulator.py:1049-1107`); note for PERF Phase C to avoid 4096² mask rebuilds. Multi-source weights path still diverges from C semantics pending Plan P3.0c evidence.
- Coin flip=HEADS: commit audit (last ~10). `c49e3be` reintroduced 40× `prompts/main.md` loop + unconditional push — regression; `c1e56ed` delivered AT-012 validation docs (48/50 peaks) but follow-up artifacts already logged. Need Ralph to restore guard immediately and capture fresh routing audit.
- Planning decision: existing active plans (dtype-default-fp32, perf-pytorch-compile-refactor) remain valid; routing plan can stay archived but Ralph must re-execute its Phase B/C tasks before automation resumes — highlighted in fix_plan instead of drafting a new plan.
- Follow-ups for Ralph: (1) Revert `loop.sh` to guarded single-iteration flow and drop new regression, logging audit under `reports/routing/` + fix_plan Attempt. (2) Execute DTYPE Phase B3 refactor with `phase_b3_audit.md` capturing before/after diffs and device/dtype tests. (3) Resume PERF Plan B4/B5 with matched iteration benchmarks and hotspot write-up; include note about restoring environment vars. (4) After dtype/perf progress, address ROI mask fallback allocations as candidate PERF Phase C task.
