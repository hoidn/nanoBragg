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
- Status Snapshot (2025-10-09): Phase A1/A2/A3 complete — loop inventory (20251009T064345Z) + classification (20251009T065238Z) delivered. Results: 4 vectorized, 17 safe, 2 todo (HIGH: noise.py LCG; MEDIUM: simulator.py phi-loop), 1 uncertain (pending profiler). Ready for Phase B profiling.

### Phase A — Loop Inventory & Evidence Capture
Goal: Build an auditable inventory of remaining Python loops touching the simulator hot path, with code locations and rough complexity estimates.
Prereqs: Editable install (`pip install -e .`), repo clean except for supervised work, profiler harness available (benchmark_detailed.py).
Exit Criteria: `reports/2026-01-vectorization-gap/phase_a/<STAMP>/` contains loop inventory JSON, annotated source listing, and summary.md; fix_plan attempt recorded with findings.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Author loop-inventory script | [D] | ✅ Completed 2025-10-09 (`scripts/analysis/vectorization_inventory.py`). Script scans `src/nanobrag_torch/` for `ast.For/ast.While`, emits JSON + summary. See `reports/2026-01-vectorization-gap/phase_a/20251009T064345Z/commands.txt` for invocation. |
| A2 | Run inventory on HEAD | [D] | ✅ Completed 2025-10-09. Artifacts: `loop_inventory.json`, `summary.md`, `pytest_collect.log`. Result: 24 loops detected; 12 flagged as likely hot (simulator/crystal/utils). |
| A3 | Annotate findings | [D] | ✅ Completed 2025-10-09. Artifacts: `reports/2026-01-vectorization-gap/phase_a/20251009T065238Z/{analysis.md, summary.md, checksums.txt, pytest_collect.log}`. Classification: Vectorized=4 (polin2/3 helpers), Safe=17 (I/O, config, debug), Todo=2 (noise.py:171 LCG loop [HIGH], simulator.py:1568 phi-loop [MEDIUM uncertain]), Uncertain=1 (needs Phase B profiler). Hot path coverage: 87.5% confirmed non-blocking. |

### Phase B — Profiling & Prioritisation
Goal: Combine static loop inventory with runtime profiling to rank candidates by impact and spec criticality.
Prereqs: Phase A artifacts ready; torch profiler installed (PyTorch ≥2.7).
Exit Criteria: Ranked backlog stored at `reports/2026-01-vectorization-gap/phase_b/<STAMP>/backlog.md` with per-candidate metrics; fix_plan updated with Next Actions for top items.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Capture warm-run profiler trace | [P] | ✅ BLOCKED on correlation fix. Profiler run complete (ralph loop #218, 2025-10-09T070458Z): 4096² warm 0.675s (C 0.78x faster), correlation 0.721 (❌ LOW vs >0.99), 1.7MB trace.json captured. BLOCKER: Low correlation (likely PERF-PYTORCH-004 P3.0b/P3.0c bugs) makes profiler hotspots untrustworthy; must fix correlation before Phase B2. Artifacts: `reports/2026-01-vectorization-gap/phase_b/20251009T070458Z/` (trace.json, benchmark_results.json, summary.md, commands.txt, env.json, pytest_collect.log). Rerun command after correlation fix: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --keep-artifacts --iterations 1`. |
| B2 | Correlate loops with trace | [B] | BLOCKED on B1 correlation fix. After valid profiler trace: Map Phase A entries to profiler hotspots (≥1% inclusive time). Produce `hot_loops.csv` with columns: module, line, loop_id, %time, call_count, notes. Flag GPU-relevant loops lacking CPU heat. |
| B3 | Publish prioritised backlog | [ ] | Draft `backlog.md` summarising the top 3–5 candidates (e.g., `_generate_mosaic_rotations`, ROI rebuild, RNG). Document expected speedups, affected acceptance tests, risks. Update docs/fix_plan Next Actions accordingly. |

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
| D2 | Update documentation & checklists | [ ] | Amend `docs/architecture/pytorch_design.md` (vectorization subsection) and `docs/development/pytorch_runtime_checklist.md` with new guidance/evidence. Reference new regression commands in `testing_strategy.md` if tests added. |
| D3 | Close ledger & archive | [ ] | Once backlog cleared or deferred with rationale, add final Attempt to docs/fix_plan.md, move artifacts to `reports/archive/vectorization-gap/<STAMP>/`, and mark this plan ready for archive. |
