Summary: Capture Phase E performance evidence for the tricubic vectorization, compare it against the Phase A baseline, and draft the parity/perf narrative before tackling detector absorption.
Mode: Perf
Focus: VECTOR-TRICUBIC-001 Vectorize tricubic interpolation and detector absorption
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_tricubic_vectorized.py
Artifacts: reports/2025-10-vectorization/phase_e/perf/$STAMP/perf_summary.md; reports/2025-10-vectorization/phase_e/perf/$STAMP/perf_results.json; reports/2025-10-vectorization/phase_e/summary.md; reports/2025-10-vectorization/phase_e/perf/$STAMP/cpu/benchmark.log; reports/2025-10-vectorization/phase_e/perf/$STAMP/cuda/benchmark.log; reports/2025-10-vectorization/phase_e/perf/$STAMP/env.json; reports/2025-10-vectorization/phase_e/perf/$STAMP/pytest_tricubic_vectorized.log
Do Now: VECTOR-TRICUBIC-001 Phase E2/E3 — set `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/tricubic_baseline.py --sizes 256 512 --repeats 200 --device cpu --outdir reports/2025-10-vectorization/phase_e/perf/$STAMP/cpu | tee reports/2025-10-vectorization/phase_e/perf/$STAMP/cpu/benchmark.log`, repeat with `--device cuda` when `torch.cuda.is_available()` (otherwise document the absence explicitly); consolidate both runs into `reports/2025-10-vectorization/phase_e/perf/$STAMP/{perf_results.json,perf_summary.md}` plus `reports/2025-10-vectorization/phase_e/summary.md` that interprets speedups vs Phase A and restates corr≥0.9995 expectations; finish by executing `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_tricubic_vectorized.py` and append the Attempt with artifact paths + timing highlights to docs/fix_plan.md.
If Blocked: Stash partial outputs under `reports/attempts/vectorization/phase_e/$STAMP/` (include command transcripts, env snapshot, git rev), log the failure reason + next debug idea in docs/fix_plan.md Attempts, and notify supervisor in galph_memory before exiting.
Priorities & Rationale:
- plans/active/vectorization.md:60 spells out Phase E’s microbenchmark + summary deliverables; without them Phase F design lacks empirical grounding.
- plans/active/vectorization.md:61 emphasises parity + performance validation as the Phase E goal, so the new summary must explicitly address both aspects.
- plans/active/vectorization.md:68 leaves E2 unchecked, so we still lack the post-vectorization timing data needed to claim success over the scalar baseline.
- plans/active/vectorization.md:69 keeps E3 open; the written summary is required before we can archive Phase E evidence bundles.
- plans/active/vectorization.md:74 highlights that Phase F prerequisites include Phase E exit criteria, making this loop a hard dependency for future implementation.
- docs/fix_plan.md:3376 enumerates the same E2/E3 tasks in the official ledger, making them the gating items on VECTOR-TRICUBIC-001’s Next Actions.
- docs/fix_plan.md:3380 shows the Attempts history table where this loop’s timings must be recorded for traceability; skipping the entry would create drift.
- scripts/benchmarks/tricubic_baseline.py:184 documents the CLI surface (sizes, repeats, device, dtype, outdir) we must follow to keep results comparable.
- scripts/benchmarks/tricubic_baseline.py:52 explains the scalar baseline pattern; the new write-up should reference this when describing improvements.
- reports/2025-10-vectorization/phase_a/tricubic_baseline_results.json provides the scalar baseline; we need to compute deltas relative to these figures in the new summary.
- reports/2025-10-vectorization/phase_a/tricubic_baseline.md contains narrative context describing bottlenecks we expect the vectorized path to eliminate—reference it in summary.md to show improvement.
- docs/development/testing_strategy.md:20 insists on device/dtype neutrality, so we must either run CUDA or explicitly record that the hardware is CPU-only.
- docs/development/testing_strategy.md:24 reminds us to keep broadcast vectorization intact; the benchmark commentary should note that the new path stays fully batched.
- docs/development/testing_strategy.md:32 reiterates we should stay with targeted tests (no full suite) after the doc updates, guiding the pytest selection.
- docs/development/pytorch_runtime_checklist.md:18 highlights performance logging requirements that summary.md should acknowledge.
- docs/architecture/pytorch_design.md:42 articulates the vectorization strategy; citing it in summary.md reinforces that the perf gains match the ADR.
- docs/development/implementation_plan.md:145 flags vectorization as an open milestone, so delivering these artifacts keeps the master plan on schedule.
- docs/fix_plan.md:21 lists VECTOR-TRICUBIC-001 as High priority; leaving Phase E incomplete blocks multiple downstream initiatives (PERF-PYTORCH-004, detector absorption refactor).
- reports/2025-10-vectorization/phase_d/summary.md captures the implementation context we should reference when justifying the new benchmark configuration.
How-To Map:
- Export `STAMP` once; reuse it for every file path so the bundle stays coherent across cpu/cuda runs, JSON, markdown artifacts, and pytest logs.
- Create directory skeletons via `mkdir -p reports/2025-10-vectorization/phase_e/perf/$STAMP/{cpu,cuda}` before launching benchmarks to avoid interleaved outputs across devices.
- CPU run: `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/tricubic_baseline.py --sizes 256 512 --repeats 200 --device cpu --dtype float32 --outdir reports/2025-10-vectorization/phase_e/perf/$STAMP/cpu | tee reports/2025-10-vectorization/phase_e/perf/$STAMP/cpu/benchmark.log`; capture the exit code and note it in perf_summary.md.
- Capture the raw JSON emitted by the script (likely `benchmark_results.json`) and move it into `reports/2025-10-vectorization/phase_e/perf/$STAMP/cpu/` for archival before aggregating.
- Record CPU warm vs cold median timings, plus calculated calls/sec; include the numbers directly in perf_summary.md.
- CUDA run (if available): `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/tricubic_baseline.py --sizes 256 512 --repeats 200 --device cuda --dtype float32 --outdir reports/2025-10-vectorization/phase_e/perf/$STAMP/cuda | tee reports/2025-10-vectorization/phase_e/perf/$STAMP/cuda/benchmark.log`; if CUDA is missing, create the `cuda/` directory with a README explaining the absence and include that statement in perf_summary.md + summary.md.
- After each run, record hashes via `sha256sum reports/2025-10-vectorization/phase_e/perf/$STAMP/cpu/benchmark.log > .../cpu/sha256.txt` and the same for cuda; these hashes help future loops verify artifact integrity.
- Collect environment info with `python - <<'PY'
import json, os, torch, platform
print(json.dumps({
    "stamp": os.environ.get("STAMP"),
    "python": platform.python_version(),
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "cuda_device_count": torch.cuda.device_count(),
    "devices": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
}, indent=2))
PY > reports/2025-10-vectorization/phase_e/perf/$STAMP/env.json` so the summary can cite hardware context.
- Generate perf_results.json by merging the new benchmark JSON fragments: compare cold/warm medians to Phase A using either a helper script (if available) or manual editing matching the Phase A schema (keys `cold_seconds`, `warm_seconds`, `calls_per_second`, `size`, `device`).
- When computing speedups, explicitly calculate ratios like `baseline_cold / new_cold` and `baseline_calls_per_second / new_calls_per_second`; include both CPU and CUDA values in perf_summary.md.
- Add a table in perf_summary.md that lists baseline vs vectorized timings for each size/device, along with percentage improvement.
- Write a short “Interpretation” subsection in perf_summary.md describing whether launch overhead still dominates CUDA results and whether the batched gather removed the scalar bottleneck.
- Author `summary.md` at the phase level covering: quick recap of the microbench results, parity confirmation (point to prior nb-compare evidence and note corr target), gradient/device neutrality statement, acknowledgement of the runtime checklist, and any follow-up questions for Phase F.
- In summary.md include a bullet comparing CPU vs CUDA acceleration and noting any difference in relative gains.
- Add a checklist to summary.md confirming that all open Phase E risks (parity, gradients, device neutrality, perf) are satisfied or linked to evidence.
- Before concluding, double-check that perf_summary.md and perf_results.json reference the same set of detector sizes so downstream scripts do not misalign rows.
- Update docs/fix_plan.md Attempts for VECTOR-TRICUBIC-001 with the new artifact paths, timings (e.g., cpu warm seconds vs baseline), GPU availability notes, the pytest log path, and highlight whether corr≥0.9995 remains satisfied based on prior evidence.
- After documentation, run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_tricubic_vectorized.py | tee reports/2025-10-vectorization/phase_e/perf/$STAMP/pytest_tricubic_vectorized.log` so the Attempt can cite the log.
- Once everything is tracked, confirm git status shows only documentation changes; do not stage large reports directories (we archive paths in fix_plan instead of committing them).
- Before finishing, double-check that summary.md references baseline files with relative paths so future loops can reproduce easily.
Pitfalls To Avoid:
- Do not reduce `--repeats`; lower counts will reintroduce jitter and invalidate comparisons against Phase A.
- Avoid rerunning the script with different `STAMP` values in the same loop; consistency is key for traceability.
- Ensure `PYTHONPATH=src` is set; otherwise the benchmark may import an installed package and skew results.
- Do not forget to set `KMP_DUPLICATE_LIB_OK=TRUE`—MKL errors will abort the run mid-way and waste time.
- Keep benchmark output simple (no extra prints) so parsing into JSON remains trivial.
- Do not assume CUDA availability; explicitly check and document the result rather than silently skipping.
- Resist editing Phase A artifacts; they are the immutable baseline for this comparison.
- Do not touch production code paths or vectorized implementations during this evidence loop.
- Confirm the pytest run happens after artifact creation so failure would correctly reflect doc/bench changes.
- Remember to mention corr≥0.9995 expectation in summary.md even though no new nb-compare is run; parity tracking remains part of Phase E.
- Update docs/fix_plan.md only once—double entry will clutter the ledger.
- Record timings in consistent units (seconds with 6 decimal places) to align with existing Phase A data.
- Avoid summarising speedups as generic “faster”; specify quantitative ratios to match prior attempts.
- Don’t forget to capture env.json even if CUDA is absent; the doc needs to state the hardware reality.
- Do not leave perf_results.json half-populated; missing fields will break downstream trend analysis scripts.
- Avoid embedding personal notes in summary.md—keep it professional and reproducible per documentation standards.
- Do not delete or replace prior perf directories; new evidence should live alongside, not overwrite, historical bundles.
- Avoid copying Phase A numbers blindly; always recompute ratios from raw data to avoid transcription mistakes.
- Ensure pytest output is stored under the same STAMP so the Attempt entry can reference a single bundle.
- Do not forget to mention whether CUDA run was skipped; silence will cause confusion during audits.
- Avoid editing `scripts/benchmarks/tricubic_baseline.py` during the run; changes there would invalidate comparisons.
- Keep benchmark commands identical between cpu and cuda runs except for the `--device` flag; extra flag drift complicates diffing.
Pointers:
- plans/active/vectorization.md:60 — Phase E checklist describing microbenchmark and summary deliverables we are closing out.
- plans/active/vectorization.md:74 — Phase F prerequisites referencing Phase E completion; motivates the urgency of this loop.
- plans/active/vectorization.md:78 — Preview of Phase F tasks; feeds the “Next Up” context once E2/E3 are complete.
- docs/fix_plan.md:3375 — VECTOR-TRICUBIC-001 Next Actions list; confirms microbench + summary precede detector absorption.
- docs/fix_plan.md:3380 — Attempts history section where the new entry needs to land (keep numbering consistent).
- scripts/benchmarks/tricubic_baseline.py:200 — Argument definitions to keep CLI invocation aligned with Phase A.
- scripts/benchmarks/tricubic_baseline.py:52 — Function comment explaining the scalar baseline the vectorized path replaces; quote it when describing improvements.
- reports/2025-10-vectorization/phase_a/tricubic_baseline_results.json — Baseline metrics to reference in perf_summary.md when quoting speedups.
- reports/2025-10-vectorization/phase_a/tricubic_baseline.md — Narrative baseline commentary to contrast against the new findings.
- docs/development/testing_strategy.md:20 — Device-neutral execution rule to cite when explaining CPU/CUDA coverage in summary.md.
- docs/development/testing_strategy.md:24 — Broadcast/vectorization reminder that should echo in the summary.
- docs/development/testing_strategy.md:32 — Reminder on targeted pytest cadence for loops like this.
- docs/architecture/pytorch_design.md:42 — Vectorization strategy paragraph that explains the broadcast approach underpinning these gains.
- docs/development/pytorch_runtime_checklist.md:18 — Runtime checklist excerpt to acknowledge when documenting the measurement workflow.
- docs/development/pytorch_runtime_checklist.md:62 — Performance logging bullet that stresses capturing both cpu and cuda metrics.
- reports/2025-10-vectorization/phase_e/README.md (create if missing) — Optional index for future runs; mention in summary.md if you add it.
- docs/fix_plan_archive.md:210 — Historical vectorization notes useful for cross-checking expected speedups.
- docs/development/lessons_in_differentiability.md:75 — Reminder to maintain gradient connectivity when discussing future absorption work.
- reports/archive/cli-flags-003/watch.md:14 — Example formatting for watch summaries; emulate the clarity when drafting perf_summary.md.
Next Up: Draft Phase F1 design notes (`plans/active/vectorization.md:78`) once perf evidence is merged, focusing on detector absorption broadcasting and differentiability risks.
