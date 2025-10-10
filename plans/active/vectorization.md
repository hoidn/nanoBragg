## Context
- Initiative: VECTOR-TRICUBIC-002 (successor to VECTOR-TRICUBIC-001); aligns with long-term Goal 1 (reactivate the vectorization roadmap starting from tricubic interpolation) and Goal 2 (close remaining vectorization gaps with measured performance deltas).
- Phase Goal: Reconstitute an actionable, dependency-aware execution plan that hands Ralph a clean sequence of tasks - from clearing upstream blockers to delivering new vectorization fixes with before/after benchmarks.
- Dependencies:
  - specs/spec-a-core.md Section 4 (sampling loops, source weighting, normalization) and Section 5 (detector absorption) - authoritative math + loop order.
  - arch.md Sections 2, 8, 15 - broadcast shapes, device/dtype guardrails, differentiability mandates.
  - docs/architecture/pytorch_design.md Section 1.1 - current tricubic/absorption vectorization evidence.
  - docs/development/pytorch_runtime_checklist.md - runtime guardrails to cite per phase.
  - docs/development/testing_strategy.md Sections 1.4-2 - authoritative pytest selectors and benchmarking cadence.
  - plans/archive/vectorization.md - historical Phase A-H evidence for tricubic/absorption vectorization.
  - plans/active/vectorization-gap-audit.md - open gap inventory plus profiling backlog (Phase B blocked today).
  - plans/active/source-weight-normalization.md - prerequisite parity work gating profiler reliability.
  - reports/2025-10-vectorization/ and reports/2026-01-vectorization-gap/ - prior artifacts to cross-check during refresh.
- Status Snapshot (2025-12-26): Tricubic and absorption vectorization (Phases A-H) remain archived with CUDA parity. SOURCE-WEIGHT-001 Phase H1–H2 delivered the parity memo (`reports/2025-11-source-weights/phase_h/20251010T002324Z/`) and flipped the divergence test to PASS (corr ≥0.999, |sum_ratio−1| ≤5e-3). Outstanding work: Phase H3/H4 ledger + plan propagation so dependent initiatives can consume the new evidence before profiler refresh. VECTOR-GAPS-002 Phase B1 stays blocked until that propagation lands.

### Phase A - Dependency Gate And Ledger Sync
Goal: Clear upstream blockers so downstream profiling and implementation can proceed on trustworthy baselines.
Prereqs: Repository clean minus supervised work; latest docs/fix_plan.md and galph_memory.md entries reviewed; C binary available via NB_C_BIN.
Exit Criteria: SOURCE-WEIGHT-001 Phase E artifacts captured, VECTOR-GAPS-002 Phase B1 unblocked in both plan and fix_plan, and updated status recorded in the ledger.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A0 | Confirm lambda override consensus | [D] | ✅ Attempt #16 (2025-12-24 galph loop) logged Option B as the authoritative approach, citing `reports/2025-11-source-weights/phase_e/20251009T131709Z/lambda_semantics.md` and updating `docs/fix_plan.md`/`plans/active/source-weight-normalization.md`. No further action required. |
| A1 | Record SOURCE-WEIGHT parity decision | [D] | ✅ Parity memo available at `reports/2025-11-source-weights/phase_h/20251010T002324Z/parity_reassessment.md`; fix_plan now treats C behaviour as spec-compliant equal weighting (comment parsing defect tracked via `[C-SOURCEFILE-001]`). |
| A2 | Capture spec-compliance test availability | [D] | ✅ SOURCE-WEIGHT-001 Phase H3/H4 ledger propagation complete (2025-12-26 ralph loop #268). Authoritative pytest selector: `tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_c_divergence_reference` (now PASSing). Parity memo: `reports/2025-11-source-weights/phase_h/20251010T002324Z/parity_reassessment.md`. Normative thresholds: corr ≥0.999, |sum_ratio−1| ≤5e-3. Phase H2 test logs: `reports/2025-11-source-weights/phase_h/20251010T002324Z/pytest.log`. `[VECTOR-GAPS-002]` Phase B1 unblocked. |
| A3 | Archive dependency memo | [ ] | Once A1–A2 complete, append a galph_memory note summarising readiness (spec decision, test selectors, artifact paths) so future loops can resume profiling without chasing C parity. |

### Phase B - Evidence Refresh For Existing Vectorization Paths
Goal: Reconfirm the archived tricubic and absorption vectorization work remains green after dependency churn; create fresh CPU and CUDA baselines for upcoming changes.
Prereqs: Phase A complete; editable install; CUDA available if possible.
Exit Criteria: New logs stored under reports/2026-01-vectorization-refresh/phase_b/<STAMP>/ covering pytest, benchmarks, and environment snapshots; docs/fix_plan.md attempt summarises results.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Rerun regression suites | [ ] | `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py -v` and `pytest tests/test_at_abs_001.py -v -k "cpu or cuda"` (guard CUDA with `torch.cuda.is_available()`). Store logs, pytest exit codes, and collection proof. |
| B2 | Capture CPU/CUDA microbenchmarks | [ ] | `python scripts/benchmarks/tricubic_baseline.py --device cpu --device cuda --sizes 256 512 --repeats 200 --outdir reports/2026-01-vectorization-refresh/phase_b/<STAMP>/tricubic/`; repeat for absorption baseline. Record mean/std, compare against reports/2025-10-vectorization/phase_e/ and phase_f/. |
| B3 | Summarise refresh results | [ ] | Draft summary.md noting deltas versus 2025-10 baselines (expect <=5% drift). Update docs/fix_plan.md [VECTOR-TRICUBIC-002] Attempt with findings and highlight if revectorization regressions reappear. |

### Phase C - Gap Profiling And Prioritisation Relaunch
Goal: Resume VECTOR-GAPS-002 Phase B using the fresh parity baseline to identify the highest-impact residual loops.
Prereqs: Phase A unblocked and Phase B refresh complete.
Exit Criteria: Updated profiler traces, hotspot ranking, and backlog stored under reports/2026-01-vectorization-gap/phase_b/<STAMP>/; fix_plan vectorization and perf entries reference the new artifacts.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Capture warm-run profiler | [ ] | `KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts --outdir reports/2026-01-vectorization-gap/phase_b/<STAMP>/profile/`. Confirm correlation >=0.99 and record torch.compile status. |
| C2 | Map profiler hotspots to loop inventory | [ ] | Use `python scripts/analysis/vectorization_inventory.py --package src/nanobrag_torch --outdir reports/2026-01-vectorization-gap/phase_b/<STAMP>/inventory/`. Produce hot_loops.csv linking profiler percentage to loop IDs and note dependencies (ROI cache rebuild, _generate_mosaic_rotations, RNG loops). |
| C3 | Publish prioritised backlog | [ ] | Write backlog.md ranking the top 3-5 candidates with expected speedups, required acceptance tests, and blocking dependencies. Update docs/fix_plan.md [VECTOR-GAPS-002] Next Actions to reference these tasks explicitly. |

### Phase D - Implementation Packages And Delegation Prep
Goal: Translate the prioritised backlog into execution-ready packets for Ralph (design notes, harnesses, acceptance criteria).
Prereqs: Phase C backlog approved by galph and logged in fix_plan.
Exit Criteria: Each high-priority loop has a design bundle and microbenchmark harness; input.md snippets prepared for delegation.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Draft loop-specific design packets | [ ] | For each backlog item, create `reports/2026-01-vectorization-gap/phase_d/<loop_slug>/design.md` quoting relevant nanoBragg.c sections (Rule 11) and outlining tensor shapes, gradients, and device considerations. |
| D2 | Author microbenchmark harnesses | [ ] | Add scripts under `scripts/benchmarks/vectorization_<loop_slug>.py` with reproducible commands (record in commands.txt). Ensure harnesses respect the PyTorch runtime checklist (no per-iteration `.to()`). |
| D3 | Prepare delegation guidance | [ ] | Update docs/fix_plan.md [VECTOR-GAPS-002] and [PERF-PYTORCH-004] Next Actions with specific Do Now templates referencing each design packet, acceptance tests, and artifact expectations. |

### Phase E - Validation, Documentation, And Closure
Goal: Ensure each implemented vectorization fix is measured, documented, and integrated into permanent guardrails; archive the plan once residuals are resolved or defer-gated.
Prereqs: At least one backlog item implemented by Ralph with artifacts collected.
Exit Criteria: Before/after metrics stored, docs updated, fix_plan status flipped to done (or residuals documented), and plan moved to archive.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Capture before/after metrics | [ ] | For each implemented loop, store before.json and after.json (CPU and CUDA) under `reports/2026-01-vectorization-gap/phase_e/<loop_slug>/`. Require <=5% regression; open PERF-PYTORCH-004 follow-up if exceeded. |
| E2 | Update permanent docs/checklists | [ ] | Amend docs/architecture/pytorch_design.md (vectorization subsection) and docs/development/pytorch_runtime_checklist.md with new guidance. Ensure docs/development/testing_strategy.md references any new regression tests or benchmarks. |
| E3 | Close ledger and archive | [ ] | Once backlog cleared or deferred with rationale, record final Attempt in docs/fix_plan.md, append a closure note to galph_memory, and move this plan to plans/archive/ with a timestamped summary. |

## Interfaces And Reporting Expectations
- Store artifacts for each phase under reports/<year>-<topic>/ as noted above; do not commit report directories, only reference them in fix_plan attempts.
- Source authoritative commands for tests and benchmarks from docs/development/testing_strategy.md; cite section numbers in fix_plan attempts and design packets.
- Every delegation to Ralph must include: (a) Do Now pytest selectors validated via `--collect-only`, (b) benchmark commands with `KMP_DUPLICATE_LIB_OK=TRUE`, (c) artifact storage location, and (d) reminders about Protected Assets, vectorization guardrails, and device/dtype neutrality.
- Keep this plan synchronised with plans/active/vectorization-gap-audit.md (Phase C hand-off) and plans/active/source-weight-normalization.md (Phase A dependency). Update statuses together whenever a gate flips.
