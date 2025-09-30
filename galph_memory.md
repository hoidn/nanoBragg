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
