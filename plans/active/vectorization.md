## Context
- Initiative: VECTOR-TRICUBIC-002 (successor to VECTOR-TRICUBIC-001); aligns with long-term Goal 1 (reactivate the vectorization roadmap starting from tricubic interpolation) and Goal 2 (close remaining vectorization gaps with measured performance deltas).
- Phase Goal: Reconstitute an actionable, dependency-aware execution plan that hands Ralph a clean sequence of tasks – from clearing upstream blockers to delivering new vectorization fixes with before/after benchmarks.
- Dependencies:
  - `specs/spec-a-core.md` §4 (sampling loops, source weighting, normalization) and §5 (detector absorption) — authoritative math + loop order.
  - `arch.md` §§2, 8, 15 — broadcast shapes, device/dtype guardrails, differentiability mandates.
  - `docs/architecture/pytorch_design.md` §1.1 — current tricubic/absorption vectorization evidence.
  - `docs/development/pytorch_runtime_checklist.md` — runtime guardrails to cite per phase.
  - `docs/development/testing_strategy.md` §§1.4–2 — authoritative pytest selectors & benchmarking cadence.
  - `plans/archive/vectorization.md` — historical Phase A–H evidence for tricubic/absorption vectorization.
  - `plans/active/vectorization-gap-audit.md` — open gap inventory + profiling backlog (Phase B blocked today).
  - `plans/active/source-weight-normalization.md` — prerequisite parity work gating profiler reliability.
  - `reports/2025-10-vectorization/` and `reports/2026-01-vectorization-gap/` — prior artifacts to cross-check during refresh.
- Status Snapshot (2025-12-24): Tricubic/absorption vectorization (Phases A–H) archived with CUDA parity; however, SOURCE-WEIGHT-001 Phase E parity evidence is still pending, leaving VECTOR-GAPS-002 Phase B1 blocked. The latest lambda sweep (`reports/2025-11-source-weights/phase_e/20251009T130433Z/lambda_sweep/`) shows PyTorch honouring sourcefile wavelengths (6.2 Å) while the C binary sticks to CLI `-lambda = 0.9768 Å`, so this plan remains gated on resolving that semantics mismatch plus the residual steps normalization delta. No current plan enumerates the path from clearing the blocker to executing the remaining vectorization backlog; this document reinstates that roadmap.

### Phase A — Dependency Gate & Ledger Sync
Goal: Clear upstream blockers so downstream profiling and implementation can proceed on trustworthy baselines.
Prereqs: Repository clean minus supervised work; latest fix_plan/galph_memory entries reviewed; C binary available via `NB_C_BIN`.
Exit Criteria: SOURCE-WEIGHT-001 Phase E artifacts captured, VECTOR-GAPS-002 Phase B1 unblocked in both plan and fix_plan, and updated status recorded in the ledger.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A0 | Align SOURCE-WEIGHT gating tasks with lambda semantics fix | [ ] | Review `plans/active/source-weight-normalization.md` Phase E rows alongside the lambda sweep bundle (`reports/2025-11-source-weights/phase_e/20251009T130433Z/lambda_sweep/summary.md`). Confirm Ralph's next loop covers forcing CLI `-lambda` through the PyTorch pipeline (or equivalent guard) plus reconciling the steps denominator (2 vs 4). Document the agreed path in `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` Attempts before requesting new parity evidence. |
| A1 | Finish SOURCE-WEIGHT-001 Phase E parity bundle | [ ] | After A0 confirms the implementation path, rerun TC-D1/TC-D3 by `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE python scripts/cli/run_weighted_source_parity.py --oversample 1 --outdir reports/2025-11-source-weights/phase_e/<STAMP>/` (or the manual CLI pair) and ensure the guard prints `Loaded 2 sources`. Capture `correlation.txt`, `sum_ratio.txt`, warning log, commands, simulator diagnostics (n_sources, steps, fluence), and env. Update `plans/active/source-weight-normalization.md` + `docs/fix_plan.md` Attempt with thresholds corr ≥0.999, |sum_ratio−1| ≤1e-3. |
| A2 | Propagate unblock signals | [ ] | Once A1 metrics pass, flip `plans/active/vectorization-gap-audit.md` Phase B1 state to [ ] (ready) and refresh `[VECTOR-GAPS-002]` Next Actions in `docs/fix_plan.md` to reference the new evidence path + timestamp. |
| A3 | Archive dependency memo | [ ] | Append galph_memory entry summarising the parity completion, metrics, and unblock status so future loops know profiling can resume. |

### Phase B — Evidence Refresh for Existing Vectorization Paths
Goal: Reconfirm the archived tricubic/absorption vectorization remains green after dependency churn; create fresh CPU+CUDA baselines to compare against upcoming changes.
Prereqs: Phase A complete; editable install; GPU accessible if available.
Exit Criteria: New logs stored under `reports/2026-01-vectorization-refresh/phase_b/<STAMP>/` covering pytest, benchmarks, and environment snapshots; fix_plan attempt summarises results.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Rerun regression suites | [ ] | `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py -v` and `pytest tests/test_at_abs_001.py -v -k "cpu or cuda"` (guard with `torch.cuda.is_available()`). Store logs, pytest exit codes, and collection proof. |
| B2 | Capture CPU/CUDA microbenchmarks | [ ] | `python scripts/benchmarks/tricubic_baseline.py --device cpu --device cuda --sizes 256 512 --repeats 200 --outdir reports/2026-01-vectorization-refresh/phase_b/<STAMP>/tricubic/`; repeat for absorption baseline. Record mean/std, compare against `reports/2025-10-vectorization/phase_e/` & `phase_f/`. |
| B3 | Summarise refresh results | [ ] | Draft `summary.md` noting deltas vs 2025-10 baselines (expect ≤5% drift). Update `docs/fix_plan.md` `[VECTOR-TRICUBIC-002]` Attempt with findings and highlight if revectorization regressions reappear. |

### Phase C — Gap Profiling & Prioritisation Relaunch
Goal: Resume VECTOR-GAPS-002 Phase B using the fresh parity baseline to identify the highest-impact residual loops.
Prereqs: Phase A (unblocked) and Phase B (refresh) complete.
Exit Criteria: Updated profiler traces, hotspot ranking, and backlog stored under `reports/2026-01-vectorization-gap/phase_b/<STAMP>/`; fix_plan vectorization and perf entries reference the new artifacts.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Capture warm-run profiler | [ ] | `KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts --outdir reports/2026-01-vectorization-gap/phase_b/<STAMP>/profile/`. Confirm correlation ≥0.99 and record `torch.compile` status. |
| C2 | Map profiler hotspots to loop inventory | [ ] | Use `scripts/analysis/vectorization_inventory.py --package src/nanobrag_torch --outdir reports/2026-01-vectorization-gap/phase_b/<STAMP>/inventory/`. Produce `hot_loops.csv` linking profiler %time to loop IDs and note dependencies (e.g., ROI cache rebuild, `_generate_mosaic_rotations`, RNG loops). |
| C3 | Publish prioritised backlog | [ ] | Write `backlog.md` ranking top 3–5 candidates with expected speedups, required acceptance tests, and blocking dependencies. Update `docs/fix_plan.md` `[VECTOR-GAPS-002]` Next Actions to reference these tasks explicitly. |

### Phase D — Implementation Packages & Delegation Prep
Goal: Translate the prioritised backlog into execution-ready packets for Ralph (design notes, harnesses, acceptance criteria).
Prereqs: Phase C backlog approved by supervisor (galph) and logged in fix_plan.
Exit Criteria: Each high-priority loop has a design bundle and microbenchmark harness; input.md snippets prepared for delegation.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Draft loop-specific design packets | [ ] | For each backlog item, create `reports/2026-01-vectorization-gap/phase_d/<loop_slug>/design.md` quoting relevant `nanoBragg.c` sections (Rule #11) and outlining tensor shapes, gradients, and device considerations. |
| D2 | Author microbenchmark harnesses | [ ] | Add scripts under `scripts/benchmarks/vectorization_<loop_slug>.py` with reproducible commands (record in `commands.txt`). Ensure harness respects PyTorch runtime checklist (no per-iteration `.to()`). |
| D3 | Prepare delegation guidance | [ ] | Update `docs/fix_plan.md` `[VECTOR-GAPS-002]` and `[PERF-PYTORCH-004]` Next Actions with specific Do Now templates referencing each design packet, acceptance tests, and artifact expectations. |

### Phase E — Validation, Documentation, and Closure
Goal: Ensure each implemented vectorization fix is measured, documented, and integrated into permanent guardrails; archive the plan once residuals are either resolved or defer-gated.
Prereqs: At least one backlog item implemented by Ralph with artifacts collected.
Exit Criteria: Before/after metrics stored, docs updated, fix_plan status flipped to done (or residuals documented), and plan moved to archive.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Capture before/after metrics | [ ] | For each implemented loop, store `before.json` / `after.json` (CPU + CUDA) under `reports/2026-01-vectorization-gap/phase_e/<loop_slug>/`. Require ≤5% regression; open PERF-PYTORCH-004 follow-up if exceeded. |
| E2 | Update permanent docs/checklists | [ ] | Amend `docs/architecture/pytorch_design.md` (vectorization subsection) and `docs/development/pytorch_runtime_checklist.md` with new guidance. Ensure `docs/development/testing_strategy.md` references any new regression tests or benchmarks. |
| E3 | Close ledger & archive | [ ] | Once backlog cleared or deferred with rationale, record final Attempt in `docs/fix_plan.md`, append closure note to galph_memory, and move this plan to `plans/archive/` with timestamped summary. |

## Interfaces & Reporting Expectations
- Artifacts for each phase live under `reports/<year>-<topic>/...` following the patterns noted above. Never commit report directories; reference them in fix_plan attempts.
- Authoritative commands for tests/benchmarks come from `docs/development/testing_strategy.md`; cite section numbers in fix_plan attempts and design packets.
- Every delegation to Ralph must include: (a) Do Now pytest selector(s) validated via `--collect-only`, (b) benchmark command(s) with `KMP_DUPLICATE_LIB_OK=TRUE`, (c) storage location for artifacts, and (d) reminders about Protected Assets, vectorization guardrails, and device/dtype neutrality.
- This plan handshakes with `plans/active/vectorization-gap-audit.md` (Phase C) and `plans/active/source-weight-normalization.md` (Phase A). Keep statuses synchronized whenever a gate flips.
