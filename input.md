Summary: Gather Phase F3 CPU absorption benchmarks, refresh the perf evidence bundle, and align plan + ledger for VECTOR-TRICUBIC-001.
Mode: Perf
Focus: docs/fix_plan.md §[VECTOR-TRICUBIC-001]
Branch: feature/spec-based-2
Mapped tests: CUDA_VISIBLE_DEVICES="" KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_abs_001.py
Artifacts: reports/2025-10-vectorization/phase_f/perf/<timestamp>/commands.txt
Artifacts: reports/2025-10-vectorization/phase_f/perf/<timestamp>/bench.log
Artifacts: reports/2025-10-vectorization/phase_f/perf/<timestamp>/perf_results.json
Artifacts: reports/2025-10-vectorization/phase_f/perf/<timestamp>/perf_summary.md
Artifacts: reports/2025-10-vectorization/phase_f/perf/<timestamp>/env.json
Artifacts: reports/2025-10-vectorization/phase_f/perf/<timestamp>/sha256.txt
Artifacts: reports/2025-10-vectorization/phase_f/perf/<timestamp>/pytest_cpu.log
Artifacts: plans/active/vectorization.md (Phase F3 row updated)
Artifacts: docs/fix_plan.md (new Attempt entry for Phase F3 CPU evidence)
Do Now: VECTOR-TRICUBIC-001 Phase F3 (CPU benchmarks) — execute `CUDA_VISIBLE_DEVICES="" PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/absorption_baseline.py --sizes 256 512 --thicksteps 5 --repeats 200 --device cpu`, archive logs under `reports/2025-10-vectorization/phase_f/perf/<timestamp>/`, validate tests on CPU, then document the metrics in plan + ledger.
If Blocked: Record the failure details in `reports/2025-10-vectorization/phase_f/perf/<timestamp>/attempt_notes.md`, add a docs/fix_plan.md Attempt describing the blocker (with command output + stacktrace), and leave plan row F3 marked [ ] pending resolution.
Priorities & Rationale:
- plans/active/vectorization.md:78-81 — shows F2 [D] with validation artifacts and F3 still open; next gate is CPU perf evidence.
- docs/fix_plan.md:3396-3399 — requires running the CPU benchmark with 200 repeats and logging metrics before any CUDA retry.
- reports/2025-10-vectorization/phase_f/validation/20251222T000000Z/summary.md — captures functional validation; perf bundle must cite this to show parity before perf tuning.
- docs/development/testing_strategy.md#1.4 — mandates CPU proof when CUDA is deferred, ensuring device neutrality is still documented.
- docs/development/pytorch_runtime_checklist.md — checklist to reference in fix_plan Attempt when summarising vectorization/device compliance.
- scripts/benchmarks/absorption_baseline.py — authoritative harness; using anything else would violate plan instructions.
- reports/2025-10-vectorization/phase_a/absorption_baseline_results.json — baseline numbers required for meaningful regression comparison.
- docs/bugs/verified_c_bugs.md:166-204 — background on C-PARITY-001 reminding us why spec-compliant rotations remain essential when discussing perf deltas.
How-To Map:
- Step 1: Define `$STAMP=$(date -u +%Y%m%dT%H%M%SZ)` so directories align with existing evidence conventions.
- Step 2: Create the destination with `mkdir -p reports/2025-10-vectorization/phase_f/perf/$STAMP` to avoid polluting older bundles.
- Step 3: Set `export PERF_DIR=reports/2025-10-vectorization/phase_f/perf/$STAMP` for reuse across commands.
- Step 4: Append to `$PERF_DIR/commands.txt` the git commit (`git rev-parse HEAD`), branch (`git rev-parse --abbrev-ref HEAD`), and the benchmark command you plan to run.
- Step 5: Capture current status with `git status -sb >> $PERF_DIR/commands.txt` so reviewers see the working tree was clean before evidence collection.
- Step 6: Run the benchmark: `CUDA_VISIBLE_DEVICES="" PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/absorption_baseline.py --sizes 256 512 --thicksteps 5 --repeats 200 --device cpu > $PERF_DIR/bench.log 2>&1`.
- Step 7: Append the executed command to `$PERF_DIR/commands.txt` immediately after running it to preserve order.
- Step 8: Generate a SHA checksum with `sha256sum $PERF_DIR/bench.log > $PERF_DIR/sha256.txt` and record the filename + hash inside commands.txt as well.
- Step 9: If the benchmark writes JSON, move or copy it into `$PERF_DIR/perf_results.json`; otherwise, parse `bench.log` via `python scripts/benchmarks/parse_absorption_benchmark.py` (if available) or a small inline script to emit JSON.
- Step 10: Compute deltas vs Phase A3 baseline: compare px/s for 256² and 512² detectors against `reports/2025-10-vectorization/phase_a/absorption_baseline_results.json` and `phase_a/absorption_baseline.md`.
- Step 11: Summaries should include per-size mean runtime, standard deviation, throughput, and percentage delta; write these into `$PERF_DIR/perf_summary.md` with a short narrative referencing both baselines and the validation bundle.
- Step 12: Document environment details with `python - <<'PY'` to dump platform info, Python version, torch version, CUDA availability, and MKL/OpenMP info into `$PERF_DIR/env.json`.
- Step 13: After benchmarking, run `CUDA_VISIBLE_DEVICES="" KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_abs_001.py > $PERF_DIR/pytest_cpu.log 2>&1` to confirm the validation tests still pass on CPU.
- Step 14: Append the pytest command and exit code to `$PERF_DIR/commands.txt`, noting that CUDA runs remain deferred per Next Actions.
- Step 15: Run `pytest --collect-only -q > $PERF_DIR/pytest_collect.log 2>&1` and capture the command in commands.txt to satisfy the docs/testing_strategy requirement.
- Step 16: Update `$PERF_DIR/perf_summary.md` with bullet points summarising benchmark results, pytest outcome, and the outstanding CUDA blocker reference (mention docs/fix_plan.md:3399).
- Step 17: Edit `plans/active/vectorization.md` row F3 to set `[D]` once satisfied, referencing `$STAMP` and quoting throughput numbers; keep F4 [ ] with guidance untouched.
- Step 18: Add a new Attempt entry in docs/fix_plan.md under VECTOR-TRICUBIC-001 capturing command(s), metrics, artifact paths, checklist references, and the note that CUDA benchmarks stay blocked by the device-placement defect.
- Step 19: Inside the Attempt summary, cite the runtime checklist and testing strategy sections you consulted so future reviewers see compliance.
- Step 20: Link the new perf bundle from the Attempt (commands file + summary + env + logs) and reference the validation bundle (20251222) for context.
- Step 21: Mention in docs/fix_plan.md whether px/s improved, regressed, or matched baseline, including numeric comparisons (≤1.05× regression threshold per plan).
- Step 22: Once ledger updates are staged, ensure `plans/active/vectorization.md` and docs/fix_plan.md both reflect the same status for F3 and reference identical artifact paths.
- Step 23: Before finishing, run `git status -sb >> $PERF_DIR/commands.txt` again so the artifact logs a clean working tree after documentation.
- Step 24: Prepare for commit (handled by supervisor) by leaving all changes staged but uncommitted; document in Attempt if any file remains intentionally unmodified due to blockers.
- Step 25: Compare the new perf_results.json against historical data in `reports/2025-10-vectorization/phase_e/perf/20251009T034421Z/perf_results.json` to note any long-term drift trends.
- Step 26: Note in perf_summary.md whether cache warm-up time differs from Phase A3, and, if so, hypothesise if compile caching or new torch version explains it.
- Step 27: Create `$PERF_DIR/attempt_notes.md` summarising observations that do not belong in the public ledger (e.g., ideas for future optimisations) so the supervisor has raw notes for Phase F4.
- Step 28: After all artifacts are written, run `find $PERF_DIR -maxdepth 1 -type f -print | sort >> $PERF_DIR/commands.txt` to log final file inventory.
- Step 29: Cross-check that every file listed in commands.txt exists; run `python - <<'PY'` to assert `len(list(Path('$PERF_DIR').glob('*'))) >= 7` and capture output in commands.txt for traceability.
- Step 30: Record wall-clock runtime for the benchmark using `/usr/bin/time -p` (repeat the command prefixed with the timer) and append the timing block to perf_summary.md to contextualise throughput numbers.
- Step 31: Note in docs/fix_plan.md Attempt whether the benchmark triggered any warnings (search `grep -i warning $PERF_DIR/bench.log`); include the grep command in commands.txt even if no warnings found.
- Step 32: Before wrapping, verify no `.npy` or other binary artifacts leaked into `$PERF_DIR`; list directories with `ls -Al $PERF_DIR >> $PERF_DIR/commands.txt` and confirm only text files are present.
- Step 33: When updating docs/fix_plan.md, include a short quote from perf_summary.md to tie the ledger narrative back to the artifact bundle verbatim.
- Step 34: After plan + ledger edits, run `rg -n "$STAMP" plans/active/vectorization.md docs/fix_plan.md` to ensure both references match the new timestamp.
- Step 35: Stage changes with `git add plans/active/vectorization.md docs/fix_plan.md input.md` once satisfied, but avoid committing; we will handle the commit in the supervisor loop.
- Step 36: Add a reminder in `$PERF_DIR/commands.txt` noting whether Gradcheck Tier-2 work depends on these perf numbers (just state "no" if unrelated) to aid future cross-initiative reviews.
Pitfalls To Avoid:
- Avoid running the benchmark without `CUDA_VISIBLE_DEVICES=""`; otherwise the script may attempt CUDA, hitting the known blocker.
- Do not touch the benchmark source or simulator implementation; evidence-only work should leave src/ untouched.
- Keep outputs text-based; do not gzip logs or embed binary plots inside perf_summary.md.
- Do not overwrite or delete `reports/2025-10-vectorization/phase_f/validation/20251222T000000Z/*`; cross-reference instead.
- Ensure env.json captures torch + CUDA versions; skipping this impedes reproducibility.
- Do not forget to mention the runtime checklist in docs/fix_plan.md Attempt; missing this violates the guardrail documentation rule.
- Avoid editing unrelated plan entries; restrict changes to F3/F4 so earlier phases remain traceable.
- Do not promote CUDA benchmarks in this loop; explicitly mark them deferred to avoid confusion with unresolved blockers.
- Remember Protected Assets: leave docs/index.md, loop.sh, supervisor.sh untouched.
- When parsing benchmark output, avoid floating-point rounding until after delta calculations to preserve precision in perf_results.json.
- Skip manual timing on a warm laptop battery; plug in AC power to avoid frequency scaling skewing throughput measurements.
- Refrain from running concurrent heavy workloads during benchmarks; close other GPU/CPU-intensive processes first.
- Do not assume the benchmark script wrote JSON; check for the file before referencing it in docs/fix_plan.md.
- Avoid editing `$PERF_DIR/commands.txt` retroactively; append new information instead of rewriting history.
- Double-check timezone usage (UTC) so timestamps in directories and perf_summary.md match expectations.
Pointers:
- plans/active/vectorization.md:78-81 — authoritative checklist for Phase F tasks (F1–F4) with status snapshot.
- docs/fix_plan.md:3396-3400 — Next Actions enumerating CPU benchmark requirement and CUDA deferral.
- reports/2025-10-vectorization/phase_f/validation/20251222T000000Z/summary.md — validation evidence to cite alongside performance data.
- reports/2025-10-vectorization/phase_a/absorption_baseline_results.json — baseline metrics for delta comparisons.
- scripts/benchmarks/absorption_baseline.py — benchmark entrypoint you must use.
- docs/development/testing_strategy.md#1.4 — device/dtype neutrality rule requiring documentation of CPU-only execution.
- docs/development/pytorch_runtime_checklist.md — vectorization + device guardrail reference for ledger entry.
- docs/index.md — Protected Assets list (read-only reminder before editing documentation).
- CLAUDE.md — compliance guardrails (especially `.item()` avoidance and vectorization mandates) worth citing if you open a follow-up issue.
- reports/2025-10-vectorization/phase_a/absorption_baseline.md — narrative baseline description to quote when comparing perf_summary results.
- reports/2025-10-vectorization/phase_e/perf/20251009T034421Z/perf_summary.md — previous post-vectorization perf snapshot to include in comparison tables.
- PROMPTS: `prompts/perf_benchmark_sop.md` (if present) — cross-check for formatting expectations before finalising perf_summary.md.
- git log -- docs/fix_plan.md history around Attempt #12 — optional reference to keep narrative consistent with earlier perf updates.
- plans/active/perf-pytorch-compile-refactor/plan.md — sanity-check compile cache expectations if the new throughput deviates significantly.
- reports/2025-10-vectorization/phase_f/design_notes.md — revisit Section 8 for gradient + device validation context cited in Attempt #14.
- docs/development/implementation_plan.md — confirm downstream milestones that depend on detector absorption performance before closing VECTOR-TRICUBIC-001.
Next Up: 1) After CPU metrics land, draft Phase F4 `phase_f/summary.md` consolidating validation + perf logs and update docs/fix_plan.md accordingly.
Next Up: 2) Track the CUDA device-placement fix so the deferred benchmark can be scheduled immediately once the blocker clears.
Next Up: 3) Revisit gradcheck-tier2-completion plan once perf evidence is logged to ensure detector gradients remain unaffected by absorption throughput changes.
Next Up: 4) If throughput regresses beyond 5%, open an investigation stub in docs/fix_plan.md linking to perf results and flag it for the PERF-PYTORCH-004 initiative.
Next Up: 5) Queue a supervisor review of benchmark harness options (scripts/benchmarks/*.py) to standardise logging before broader performance sweeps resume.
