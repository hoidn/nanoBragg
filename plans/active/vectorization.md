## Context
- Initiative: VECTOR-TRICUBIC-002 — relaunch the vectorization program beginning with tricubic interpolation and detector absorption, then expand to the remaining hot loops once parity resumes.
- Plan Goal: Deliver a phase-ordered playbook that keeps evidence refreshed, gates on 4096² parity restoration, and stages new vectorization work (starting with tricubic) with reproducible benchmarks and documentation updates.
- Dependencies:
  - specs/spec-a-core.md §§4–5 — authoritative sampling loops, normalization, and absorption physics.
  - arch.md §§2, 8, 15 — broadcast shapes, device/dtype guardrails, differentiability requirements.
  - docs/architecture/pytorch_design.md §1.1 & §1.1.5 — current vectorized flows and equal-weight source contract.
  - docs/development/pytorch_runtime_checklist.md — runtime guardrails to cite in every delegation.
  - docs/development/testing_strategy.md §§1.4–2 — authoritative pytest/benchmark commands.
  - plans/active/vectorization-parity-regression.md — parity gating workstream (Phase C1–C3 traces).
  - plans/active/vectorization-gap-audit.md — loop inventory/profiling follow-on once parity is restored.
  - reports/2025-10-vectorization/ & reports/2026-01-vectorization-refresh/ — prior evidence bundles to reuse when refreshing baselines.

## Status Snapshot (2026-01-06)
- Phase A dependency gate ✅ (Attempts logged Dec 2025; SOURCE-WEIGHT contract propagated to docs/fix_plan.md).
- Phase B regression refresh ✅ (Attempt #2 2025-10-09 captured CPU/CUDA tricubic + absorption suites under `reports/2026-01-vectorization-refresh/phase_b/20251010T013437Z/`).
- Phase C parity gate ⏳ in progress — C traces (Attempt #8) and Py traces (Attempt #9) exist; awaiting Phase C3 first_divergence.md before resuming profiling/backlog work.
- Downstream phases (D–G) remain locked until `[VECTOR-PARITY-001]` reports parity ≥0.999 with trace-backed diagnosis.

### Phase A — Dependency Gate & Ledger Sync
Goal: Ensure prerequisite parity decisions and guardrails are recorded so later profiling relies on trustworthy baselines.
Prereqs: Latest galph_memory.md notes incorporated; SOURCE-WEIGHT-001 closure accepted; NB_C_BIN available.
Exit Criteria: All dependency memos captured and linked in docs/fix_plan.md; VECTOR-GAPS-002 Phase B unblocked.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Confirm lambda override consensus | [D] | ✅ `reports/2025-11-source-weights/phase_e/20251009T131709Z/lambda_semantics.md`; logged in fix_plan Attempt #16 (2025-12-24). |
| A2 | Record SOURCE-WEIGHT parity decision | [D] | ✅ Attempt #16 propagated memo + thresholds to plan and docs. See `reports/2025-11-source-weights/phase_h/20251010T002324Z/parity_reassessment.md`. |
| A3 | Capture spec-compliance test availability | [D] | ✅ `tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_c_divergence_reference` noted in fix_plan; artifact under `reports/2025-11-source-weights/phase_h/20251010T002324Z/pytest.log`. |
| A4 | Archive dependency memo | [D] | ✅ 2025-12-28 galph_memory entry documents decisions + selector mapping; no further action required. |

### Phase B — Evidence Refresh For Existing Vectorization Paths
Goal: Reconfirm historical tricubic/absorption vectorization evidence post dependency churn and snapshot performance baselines (CPU + CUDA).
Prereqs: Phase A complete; editable install; CUDA available or explicitly noted absent.
Exit Criteria: Fresh regression + benchmark artifacts stored under `reports/2026-01-vectorization-refresh/phase_b/<STAMP>/` with summary logged in docs/fix_plan.md.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Rerun regression suites | [D] | ✅ Attempt #2 (2025-10-09) — `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py -v` and `pytest tests/test_at_abs_001.py -v -k "cpu or cuda"`; logs in `reports/2026-01-vectorization-refresh/phase_b/20251010T013437Z/`. |
| B2 | Refresh CPU/CUDA microbenchmarks | [D] | ✅ Same bundle; see `perf_summary.md` for timings (tricubic CPU 1.45 ms, CUDA 5.68 ms, absorption CPU 4.72 ms, CUDA 5.43 ms). |
| B3 | Update ledger with results | [D] | ✅ docs/fix_plan.md Attempt #2 summarises metrics and links artifacts; status now “Phase B regression refresh complete”. |

### Phase C — Parity Alignment Gate
Goal: Stay synchronized with `[VECTOR-PARITY-001]` and block new profiling until 4096² correlation ≥0.999 with trace-backed diagnosis.
Prereqs: `[VECTOR-PARITY-001]` Phase C1–C2 traces captured (done); C3 first divergence pending; supervisor input memo (input.md) drives Ralph’s instrumentation work.
Exit Criteria: `reports/2026-01-vectorization-parity/phase_c/<STAMP>/first_divergence.md` published, go/no-go decision recorded in docs/fix_plan.md, and parity regression either cleared or escalated.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Track trace capture completeness | [D] | ✅ Attempts #8–#9 delivered TRACE_C/TRACE_PY logs under `reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/` and `.../20251010T055346Z/`. Confirmed in docs/fix_plan.md. |
| C2 | Obtain first divergence analysis | [P] | Active — Await `first_divergence.md` from `[VECTOR-PARITY-001]` Phase C3 summarising earliest mismatched tap + units. Supervisor to review and log decision in galph_memory.md. |
| C3 | Update vectorization plan/ledger post-diagnosis | [ ] | Blocked on C2. When divergence documented, refresh this plan + docs/fix_plan.md with go/no-go, noting whether profiling can resume or additional parity work is needed. |

### Phase D — Warm-Run Profiling & Backlog Refresh
Goal: Once parity is restored, capture a clean 4096² warm-run profile and integrate it with the loop inventory to rank the next vectorization targets.
Prereqs: Phase C exit criteria met (parity ≥0.999, divergence understood); NB_C_BIN instrumentation no longer required for this phase.
Exit Criteria: `reports/2026-01-vectorization-gap/phase_b/<STAMP>/` contains new profiler trace + `hot_loops.csv`; prioritized backlog recorded in docs/fix_plan.md `[VECTOR-TRICUBIC-002]` and plans/active/vectorization-gap-audit.md.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Capture warm-run profiler trace | [ ] | Run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts --outdir reports/2026-01-vectorization-gap/phase_b/<STAMP>/profile/`. Archive `trace.json`, `summary.md`, env metadata. |
| D2 | Correlate trace with loop inventory | [ ] | Map profiler hotspots to Phase A inventory (plans/active/vectorization-gap-audit.md). Produce `hot_loops.csv` with inclusive % time, call counts, CPU vs CUDA deltas. |
| D3 | Publish prioritized backlog | [ ] | Write `backlog.md` summarising top candidates (≥1% inclusive time, spec-critical). Update docs/fix_plan.md Next Actions + galph_memory with decision rationale. |

### Phase E — Implementation Batch A (Tricubic Refresh)
Goal: Revalidate and, if necessary, extend tricubic vectorization to cover new requirements discovered during backlog refresh (e.g., mixed-precision variants, batched HKL caches) while preserving parity and performance.
Prereqs: Phase D backlog identifies tricubic work as first target; divergence resolved; design references gathered.
Exit Criteria: Updated tricubic implementation merged, tests passing on CPU/GPU, before/after metrics stored under `reports/2026-01-vectorization-refresh/phase_e/<STAMP>/`, documentation updated.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Draft tricubic design addendum | [ ] | Author `reports/2026-01-vectorization-refresh/phase_e/<STAMP>/design.md` quoting nanoBragg.c polin2/3 sections (Rule #11), enumerating tensor shapes, differentiability notes, and acceptance commands. |
| E2 | Prepare delegation package | [ ] | Update docs/fix_plan.md Next Actions + input.md with concrete Do Now (tests `tests/test_tricubic_vectorized.py`, nb-compare ROI, perf harness). Include rollback guard + artifact expectations. |
| E3 | Validate implementation & metrics | [ ] | After Ralph’s code changes, ensure targeted pytest, nb-compare (if applicable), and benchmarks run. Archive `before.json`/`after.json` and summarise outcomes in docs/fix_plan.md Attempt history. |

### Phase F — Implementation Batch B (Additional Hot Loops)
Goal: Apply the same design→delegate→verify pattern to the remaining prioritized loops (e.g., mosaic rotation generation, noise RNG, phi accumulation) with tracked performance gains.
Prereqs: Phase E complete; backlog from Phase D ranked.
Exit Criteria: Each selected loop has design packet, delegated implementation, verified performance delta, and documentation updates recorded.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| F1 | Select next target from backlog | [ ] | Choose top candidate from `backlog.md` (≥1% inclusive time or high physics risk). Document selection + rationale in galph_memory and fix_plan Next Actions. |
| F2 | Author design + harness | [ ] | Mirror Phase E1/E2 for the chosen loop; ensure reproducible commands (pytest selector, microbench). Store under `reports/2026-01-vectorization-refresh/phase_f/<loop_slug>/`. |
| F3 | Delegate implementation & verify | [ ] | Coordinate with Ralph via input.md; after completion, archive metrics + diff summary and update docs/fix_plan.md. |

### Phase G — Documentation & Closure
Goal: Fold the new vectorization work into permanent guardrails and retire the plan once maintenance hooks are established.
Prereqs: All targeted loops (Phase E/F) delivered or deferred with rationale; performance deltas recorded.
Exit Criteria: Documentation updated, fix_plan marked done, plan archived with closure summary.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| G1 | Update architecture/runtime docs | [ ] | Amend `docs/architecture/pytorch_design.md` and `docs/development/pytorch_runtime_checklist.md` with new vectorization guidance + thresholds; cite reports bundles. |
| G2 | Close ledger & archive plan | [ ] | Add final Attempt to docs/fix_plan.md (corr/speedup improvements, doc updates). Move this file to `plans/archive/` with closure note once maintenance cadence defined. |
