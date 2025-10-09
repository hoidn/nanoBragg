Summary: Refresh the 4096² CPU profiler capture for VECTOR-GAPS-002 Phase B1 now that parity fixes landed, and document the ≥0.99 correlation evidence for the Phase B backlog.
Mode: Perf
Focus: [VECTOR-GAPS-002] Vectorization gap audit — Phase B1 profiler rerun
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2026-01-vectorization-gap/phase_b/<STAMP>/commands.txt; reports/2026-01-vectorization-gap/phase_b/<STAMP>/pytest_collect.log; reports/2026-01-vectorization-gap/phase_b/<STAMP>/profile/run.log; reports/2026-01-vectorization-gap/phase_b/<STAMP>/profile/benchmark_results.json; reports/2026-01-vectorization-gap/phase_b/<STAMP>/profile/trace.json; reports/2026-01-vectorization-gap/phase_b/<STAMP>/correlation.txt; reports/2026-01-vectorization-gap/phase_b/<STAMP>/summary.md; reports/2026-01-vectorization-gap/phase_b/<STAMP>/env.json; reports/2026-01-vectorization-gap/phase_b/<STAMP>/torch_env.txt
Do Now: [VECTOR-GAPS-002] Phase B1 — run `pytest --collect-only -q | tee reports/2026-01-vectorization-gap/phase_b/$(date -u +%Y%m%dT%H%M%SZ)/pytest_collect.log` then `export STAMP=$(date -u +%Y%m%dT%H%M%SZ) && mkdir -p reports/2026-01-vectorization-gap/phase_b/$STAMP/{profile,notes} && KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --keep-artifacts --iterations 1 --outdir reports/2026-01-vectorization-gap/phase_b/$STAMP/profile/ | tee reports/2026-01-vectorization-gap/phase_b/$STAMP/profile/run.log`
If Blocked: Capture the failing stdout/stderr into reports/2026-01-vectorization-gap/phase_b/<STAMP>/blocking.md, note the exit code in commands.txt, and append a docs/fix_plan.md attempt describing the failure mode before stopping.
Priorities & Rationale:
- plans/active/vectorization-gap-audit.md (§Phase B1) names the profiler rerun as the gate to proceed; Source-weight and tricubic blockers are cleared and we must replace the stale 0.72 correlation evidence.
- docs/fix_plan.md:3765-3773 now requires the new run to log correlation ≥0.99 into correlation.txt and summary.md so Phase B2 can trust hotspot ordering.
- reports/2025-11-source-weights/phase_d/20251222T000000Z/summary.md shows parity restored; this profiler capture validates that fix on full-size workloads.
- docs/development/testing_strategy.md §1.4 mandates CPU-first evidence with explicit device settings; this command conforms to the authoritative workflow.
- reports/2026-01-vectorization-gap/phase_a/20251009T065238Z/summary.md provides loop classifications that Phase B2 will map against once this capture lands.
How-To Map:
- Export `AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md` before running anything so logs capture the source of truth.
- Append every command (directory prep, git status, pytest, profiler) to commands.txt via `printf` so the audit trail survives future reviews.
- After the profiler finishes, produce correlation.txt with:
  `python - <<'PY'
import json, pathlib, os
stamp = os.environ['STAMP']
base = pathlib.Path('reports/2026-01-vectorization-gap/phase_b') / stamp
metrics = json.loads((base / 'profile' / 'benchmark_results.json').read_text())
with open(base / 'correlation.txt', 'w') as fh:
    fh.write(f"correlation={metrics['correlation']:.6f}\n")
print(f"correlation={metrics['correlation']:.6f}")
PY`
  and cite that number in summary.md.
- Capture env.json via the documented snippet (python version, torch version, CUDA availability, device count, git SHA) and dump `python -m torch.utils.collect_env > reports/2026-01-vectorization-gap/phase_b/$STAMP/torch_env.txt` for hardware context.
- Generate a quick top-k table from trace.json with:
  `python - <<'PY'
import json, pathlib, collections, os
stamp = os.environ['STAMP']
trace_path = pathlib.Path('reports/2026-01-vectorization-gap/phase_b') / stamp / 'profile' / 'trace.json'
trace = json.loads(trace_path.read_text())
durations = collections.Counter()
for evt in trace.get('traceEvents', []):
    if evt.get('ph') == 'X' and 'name' in evt:
        durations[evt['name']] += evt.get('dur', 0)
with open(trace_path.with_name('top_kernels.txt'), 'w') as fh:
    for name, dur in durations.most_common(10):
        fh.write(f"{name}\t{dur/1e6:.3f} ms\n")
PY`
  then summarise those kernels in summary.md to tee up Phase B2 mapping.
- Update docs/fix_plan.md attempts with timestamp, cold/warm timings, correlation value, and any anomalies spotted in top_kernels.txt.
Pitfalls To Avoid:
- Do not reuse 20251009T070458Z or 20251009T094735Z directories; create a fresh UTC-stamped folder.
- Keep the profiler on CPU; flipping to CUDA mid-run will make the results incomparable to Phase A evidence.
- Ensure `--keep-artifacts` is present; losing trace.json blocks Phase B2 callgraph correlation.
- Avoid editing simulator code or adding instrumentation—this loop is evidence only.
- Do not skip writing correlation.txt; downstream automation expects it when ranking loops.
- Confirm `pytest --collect-only -q` exits 0 before running the profiler; unresolved import errors invalidate the capture.
- Watch disk usage; trace.json is ~2 MB, but accidental large dumps (>500 MB) should be removed before completion (never touch files listed in docs/index.md).
- Record both cold and warm timings from benchmark_results.json in summary.md; these values feed the PERF-PYTORCH-004 backlog.
- If correlation <0.99, halt after updating fix_plan with the failure—Phase B2 stays blocked until parity passes.
Pointers:
- plans/active/vectorization-gap-audit.md (Phase B table and guidance)
- docs/fix_plan.md:3763-3810 ([VECTOR-GAPS-002] ledger context and attempts)
- docs/development/testing_strategy.md §1.4 (device & dtype discipline expectations)
- docs/development/pytorch_runtime_checklist.md (vectorization/runtime guardrails to cite in summary)
- reports/2025-10-vectorization/phase_h/20251009T092228Z/summary.md (latest CUDA parity reference for comparison)
Next Up: Phase B2 — parse the new trace, map hotspots to the loop inventory, and draft hot_loops.csv with inclusive-time percentages.
