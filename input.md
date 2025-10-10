Summary: Capture fresh 4096² profiler trace after source-weight parity to unblock vectorization-gap backlog.
Mode: Perf
Focus: [VECTOR-GAPS-002] Vectorization gap audit
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-gap/phase_b/$STAMP/profile/, reports/2026-01-vectorization-gap/phase_b/$STAMP/summary.md, reports/2026-01-vectorization-gap/phase_b/$STAMP/commands.txt, reports/2026-01-vectorization-gap/phase_b/$STAMP/env.json
Do Now: [VECTOR-GAPS-002] Phase B1 — export STAMP=$(date -u +%Y%m%dT%H%M%SZ) && NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts --outdir reports/2026-01-vectorization-gap/phase_b/$STAMP/profile/
If Blocked: If the profiler aborts or correlation_warm < 0.999, capture profile_run.log and benchmark_results.json under reports/2026-01-vectorization-gap/phase_b/$STAMP/failed/, run pytest --collect-only -q, and record the failure in docs/fix_plan.md attempts before stopping.
Priorities & Rationale:
- docs/fix_plan.md:3791 — Next Actions call for resuming Phase B profiling now that SOURCE-WEIGHT-001 parity is locked.
- plans/active/vectorization-gap-audit.md:34 — Task B1 defines the exact profiler command and artifact layout for this phase.
- docs/architecture/pytorch_design.md:105 — Parity memo sets corr ≥0.999 and |sum_ratio−1| ≤5e-3 thresholds that this rerun must confirm.
- docs/development/testing_strategy.md:18 — Device/dtype discipline requires the CPU float32 run and captures the authoritative command in the ledger.
How-To Map:
1. STAMP=$(date -u +%Y%m%dT%H%M%SZ);
2. NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts --outdir reports/2026-01-vectorization-gap/phase_b/$STAMP/profile/ | tee reports/2026-01-vectorization-gap/phase_b/$STAMP/profile_run.log;
3. python - <<'PY'
import json, os
from pathlib import Path
base = Path('reports/2026-01-vectorization-gap/phase_b') / os.environ['STAMP'] / 'profile'
metrics = json.load((base / 'benchmark_results.json').open())[0]
print(f"correlation_warm={metrics['correlation_warm']:.9f}, speedup_warm={metrics['speedup_warm']:.3f}")
if metrics['correlation_warm'] < 0.999:
    raise SystemExit('Correlation below parity threshold; halt and log failure')
PY
4. python - <<'PY'
import json, os, textwrap
from pathlib import Path
stamp = os.environ['STAMP']
base = Path('reports/2026-01-vectorization-gap/phase_b') / stamp
metrics = json.load((base / 'profile' / 'benchmark_results.json').open())[0]
summary = textwrap.dedent(f"""
# Phase B1 profiler rerun ({stamp})
- Command: benchmark_detailed.py 4096 cpu float32 profile
- correlation_warm: {metrics['correlation_warm']:.12f}
- speedup_warm: {metrics['speedup_warm']:.3f}
- Notes: confirm NB_C_BIN path, capture torch.compile warnings if any (expected: none)
""")
(base / 'summary.md').write_text(summary)
PY
5. NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q > reports/2026-01-vectorization-gap/phase_b/$STAMP/collect.log;
6. Update docs/fix_plan.md attempts with metrics after review.
Pitfalls To Avoid:
- Do not modify production code or plans during this evidence loop.
- Use a fresh $STAMP directory; never overwrite the 20251009 artifacts.
- Keep --device cpu and --dtype float32 exactly; no GPU run on this pass.
- Ensure NB_C_BIN points at ./golden_suite_generator/nanoBragg for C parity.
- Capture profile_run.log and env.json; the script should emit env.json automatically.
- Watch for torch.profiler errors or graph-break warnings; treat them as blockers.
- Do not delete or move files listed in docs/index.md.
- Maintain KMP_DUPLICATE_LIB_OK=TRUE throughout to avoid MKL crashes.
Pointers:
- docs/fix_plan.md:3791
- plans/active/vectorization-gap-audit.md:34
- docs/architecture/pytorch_design.md:101
- docs/development/testing_strategy.md:18
- reports/2026-01-vectorization-gap/phase_a/20251009T065238Z/summary.md#L1
Next Up (optional): Begin Phase B2 by mapping the new trace to hot loops (python scripts/analysis/vectorization_inventory.py --package src/nanobrag_torch --outdir reports/2026-01-vectorization-gap/phase_b/$STAMP/inventory/).
