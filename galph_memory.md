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

## 2025-09-30 (galph loop current)
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
