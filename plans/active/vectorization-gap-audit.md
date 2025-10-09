## Context
- Initiative: VECTOR-GAPS-002 — follow-up to the tricubic/absorption vectorization work, aligned with long-term Goal 2 (identify and close remaining Python-loop hot paths).
- Phase Goal: Produce a repeatable backlog of non-vectorized surfaces with quantified impact so Ralph can implement the highest-value fixes without rediscovery.
- Dependencies:
  - specs/spec-a-core.md §4 (sampling loops and normalization requirements)
  - specs/spec-a-parallel.md §2.3 & §4 (parallel validation + performance acceptance tests)
  - arch.md §§2, 8, 15 (batch shapes, differentiability guardrails)
  - docs/architecture/pytorch_design.md §1.1 (current vectorized flows)
  - docs/development/pytorch_runtime_checklist.md (vectorization/device do/don'ts)
  - docs/development/testing_strategy.md §§1.4–2 (authoritative commands, perf cadence)
  - plans/active/vectorization.md (Phases A–G history)
  - plans/active/perf-pytorch-compile-refactor/plan.md (4096² warm benchmark harness & profiler usage)
  - reports/2025-10-vectorization/gaps/20251009T061928Z/analysis.md (prior gap evidence: divergence/dispersion source loops)
- Status Snapshot (2025-12-22): Phase A not started — tricubic/absorption work complete; no consolidated inventory exists for remaining scalar loops.

### Phase A — Loop Inventory & Evidence Capture
Goal: Build an auditable inventory of remaining Python loops touching the simulator hot path, with code locations and rough complexity estimates.
Prereqs: Editable install (`pip install -e .`), repo clean except for supervised work, profiler harness available (benchmark_detailed.py).
Exit Criteria: `reports/2026-01-vectorization-gap/phase_a/<STAMP>/` contains loop inventory JSON, annotated source listing, and summary.md; fix_plan attempt recorded with findings.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Author loop-inventory script | [ ] | Implement `scripts/analysis/vectorization_inventory.py` (AST walk over `src/nanobrag_torch/` detecting `ast.For` / `ast.While` in production modules). Emit JSON with keys: module, line, loop_header, loop_type, estimated_iteration_sources (hand-tuned heuristics). Include CLI options `--package src/nanobrag_torch --outdir <path>`. |
| A2 | Run inventory on HEAD | [ ] | Command: `python scripts/analysis/vectorization_inventory.py --package src/nanobrag_torch --outdir reports/2026-01-vectorization-gap/phase_a/<STAMP>/` (ensure directory exists). Capture stdout to `loop_inventory.json`; keep raw AST hits plus filtered list of likely hot loops (e.g., within simulator/crystal/utils). |
| A3 | Annotate findings | [ ] | Produce `summary.md` consolidating A2 results. For each loop mark: (a) runtime-critical guess, (b) already vectorized fallback (document why safe), (c) needs follow-up. Cross-reference existing evidence (e.g., `reports/2025-10-vectorization/gaps/*`). Log Attempt in docs/fix_plan.md with artifact paths. |

### Phase B — Profiling & Prioritisation
Goal: Combine static loop inventory with runtime profiling to rank candidates by impact and spec criticality.
Prereqs: Phase A artifacts ready; torch profiler installed (PyTorch ≥2.7).
Exit Criteria: Ranked backlog stored at `reports/2026-01-vectorization-gap/phase_b/<STAMP>/backlog.md` with per-candidate metrics; fix_plan updated with Next Actions for top items.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Capture warm-run profiler trace | [ ] | Command: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --keep-artifacts --iterations 1 --outdir reports/2026-01-vectorization-gap/phase_b/<STAMP>/profile/`. Extract python-level call stacks from trace.json focusing on simulator/crystal/utils functions. |
| B2 | Correlate loops with trace | [ ] | Map A2 loop entries to profiler hotspots (≥1% inclusive time). Produce `hot_loops.csv` with columns: module, line, loop_id, %time, call_count, notes. Flag loops absent from trace but potentially heavy for GPU (document rationale). |
| B3 | Publish prioritised backlog | [ ] | Draft `backlog.md` summarising top 3–5 candidates (e.g., `_generate_mosaic_rotations`, `utils/noise.lcg_random`, detector ROI rebuild). For each: expected speedup, affected acceptance tests, risks (grad/device). Update docs/fix_plan.md Attempt with backlog link and planned owners. |

### Phase C — Implementation Handoff & Design Prep
Goal: Translate the prioritised list into actionable implementation packages (design notes, harnesses, delegation guidance).
Prereqs: Phase B backlog approved by supervisor (galph) and recorded in fix_plan.
Exit Criteria: Each high-priority loop has a mini-design packet + benchmark harness; input.md Do Now prepared for first target.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Draft design packets | [ ] | For each HIGH target create `reports/2026-01-vectorization-gap/phase_c/<loop_slug>/design.md` quoting C references (Rule #11) and outlining tensor shapes + differentiability concerns. Include acceptance commands (pytest selectors, nb-compare if applicable). |
| C2 | Author microbench harnesses | [ ] | Add under `scripts/benchmarks/vectorization_gap_<loop_slug>.py`; baseline runtime + target metrics for before/after comparison. Record command templates in `commands.txt`. |
| C3 | Prepare execution roadmap | [ ] | Update docs/fix_plan.md Next Actions + `input.md` template snippets assigning first loop to Ralph (include reproduction commands, required artifacts). Obtain supervisor sign-off before delegating. |

### Phase D — Validation & Closure
Goal: Ensure each delegated vectorization fix is measured, documented, and integrated into permanent guardrails; close out the plan once backlog cleared or deferred with rationale.
Prereqs: At least one implementation batch complete (Ralph loops) with artifacts.
Exit Criteria: Updated performance docs/tests, fix_plan entry closed (status `done` or residuals documented), plan archived.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Capture before/after metrics | [ ] | For each loop fix, store `before.json` / `after.json` under `reports/2026-01-vectorization-gap/phase_d/<loop_slug>/` with profiler snapshots (CPU + CUDA when available). Require ≤5% regression threshold else open PERF-PYTORCH-004 follow-up. |
| D2 | Update documentation & checklists | [ ] | Amend `docs/architecture/pytorch_design.md` (vectorization subsection) and `docs/development/pytorch_runtime_checklist.md` with new guidance/evidence. Note relevant regression commands in testing_strategy.md if new tests added. |
| D3 | Close ledger & archive | [ ] | Once backlog cleared or deferred with rationale, add final Attempt to docs/fix_plan.md, move artifacts to `reports/archive/vectorization-gap/<STAMP>/`, and mark this plan ready for archive. |
