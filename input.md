Summary: Capture and log a fresh 4096² profiler trace so Phase B of the vectorization-gap audit can resume.
Mode: Perf
Focus: [VECTOR-GAPS-002] Vectorization gap audit
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-gap/phase_b/$STAMP/profile/, reports/2026-01-vectorization-gap/phase_b/$STAMP/summary.md, reports/2026-01-vectorization-gap/phase_b/$STAMP/collect.log, reports/2026-01-vectorization-gap/phase_b/$STAMP/commands.txt, reports/2026-01-vectorization-gap/phase_b/$STAMP/env.json
Do Now: [VECTOR-GAPS-002] Phase B1 — export STAMP=$(date -u +%Y%m%dT%H%M%SZ) && NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts --outdir reports/2026-01-vectorization-gap/phase_b/$STAMP/profile/
If Blocked: If correlation_warm < 0.999 or |sum_ratio−1| > 5e-3, stash profile_run.log plus benchmark_results.json under reports/2026-01-vectorization-gap/phase_b/$STAMP/failed/, run NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q > reports/2026-01-vectorization-gap/phase_b/$STAMP/collect.log, and log the failure in docs/fix_plan.md before stopping.
Priorities & Rationale:
- docs/fix_plan.md:3791 — Entry sets Phase B1 as the current blocker and ties success to corr ≥0.999, |sum_ratio−1| ≤5e-3.
- docs/fix_plan.md:3801 — Updated Next Actions call for an immediate profiler rerun plus metric logging ahead of B2/B3.
- plans/active/vectorization-gap-audit.md:27 — Phase B rows define the profiling/backlog deliverables and artifact layout.
- docs/development/testing_strategy.md:18 — Device/dtype discipline requires CPU float32 parity evidence during perf loops.
How-To Map:
1. export STAMP=$(date -u +%Y%m%dT%H%M%SZ)
2. NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts --outdir reports/2026-01-vectorization-gap/phase_b/$STAMP/profile/ | tee reports/2026-01-vectorization-gap/phase_b/$STAMP/profile_run.log
3. python - <<'PY'
import json, os, textwrap
from pathlib import Path
base = Path('reports/2026-01-vectorization-gap/phase_b') / os.environ['STAMP'] / 'profile'
metrics = json.load((base / 'benchmark_results.json').open())[0]
summary = textwrap.dedent(f"""
# Phase B1 profiler rerun ({os.environ['STAMP']})
- Command: benchmark_detailed.py 4096 cpu float32 profile
- correlation_warm: {metrics['correlation_warm']:.12f}
- sum_ratio: {metrics['sum_ratio']:.12f}
- speedup_warm: {metrics['speedup_warm']:.3f}
""")
(base.parent / 'summary.md').write_text(summary)
if metrics['correlation_warm'] < 0.999 or abs(metrics['sum_ratio'] - 1.0) > 5e-3:
    raise SystemExit('Parity threshold not met; follow blocked protocol')
PY
4. NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q > reports/2026-01-vectorization-gap/phase_b/$STAMP/collect.log
5. Capture env metadata (`python scripts/support/dump_env.py` if available, otherwise manual) into reports/2026-01-vectorization-gap/phase_b/$STAMP/env.json and list commands in commands.txt
6. Update docs/fix_plan.md attempts with metrics and artifact paths before ending the loop
Pitfalls To Avoid:
- Do not touch production code or plans during this evidence loop.
- Use a fresh $STAMP directory; never overwrite archival 20251009 data.
- Keep NB_C_BIN pointed at ./golden_suite_generator/nanoBragg for C parity.
- Maintain KMP_DUPLICATE_LIB_OK=TRUE to avoid MKL duplicate symbol crashes.
- Treat correlation_warm < 0.999 or |sum_ratio−1| > 5e-3 as hard stop conditions.
- Record profile_run.log and env.json even if the command fails.
- No GPU runs on this pass; CPU float32 only per plan.
Pointers:
- docs/fix_plan.md:3791
- plans/active/vectorization-gap-audit.md:27
- docs/development/testing_strategy.md:18
- reports/2025-11-source-weights/phase_h/20251010T002324Z/parity_reassessment.md
Next Up: Begin Phase B2 hotspot mapping with scripts/analysis/vectorization_inventory.py once Phase B1 metrics clear the parity thresholds.
