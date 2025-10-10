Summary: Capture a clean 4096² CPU profiler bundle so VECTOR-GAPS-002 Phase B can move forward with hotspot ranking.
Mode: Perf
Focus: [VECTOR-GAPS-002] Vectorization gap audit
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-gap/phase_b/$STAMP/profile/, reports/2026-01-vectorization-gap/phase_b/$STAMP/profile_run.log, reports/2026-01-vectorization-gap/phase_b/$STAMP/summary.md, reports/2026-01-vectorization-gap/phase_b/$STAMP/collect.log, reports/2026-01-vectorization-gap/phase_b/$STAMP/env.json, reports/2026-01-vectorization-gap/phase_b/$STAMP/commands.txt
Do Now: [VECTOR-GAPS-002] Phase B1 — export STAMP=$(date -u +%Y%m%dT%H%M%SZ) && NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts --outdir reports/2026-01-vectorization-gap/phase_b/$STAMP/profile/
If Blocked: If correlation_warm < 0.999 or |sum_ratio−1| > 5e-3, move the bundle to reports/2026-01-vectorization-gap/phase_b/$STAMP/failed/, capture NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q > reports/2026-01-vectorization-gap/phase_b/$STAMP/collect.log, and log the failure as a new Attempt on [VECTOR-GAPS-002] before stopping.
Priorities & Rationale:
- docs/fix_plan.md:3801 — Next Actions demand the fresh Phase B1 profiler capture with thresholds corr ≥0.999 and |sum_ratio−1| ≤5e-3.
- plans/active/vectorization-gap-audit.md:34 — Phase B1 row defines the exact benchmark command and cites the SOURCE-WEIGHT parity memo.
- docs/architecture/pytorch_design.md:101 — Confirms equal-weighting semantics and the validated correlation/sum_ratio tolerances we must hit.
- docs/development/pytorch_runtime_checklist.md:22 — Reinforces the equal-weighting guard and CLI parity requirements for this run.
How-To Map:
1. export STAMP=$(date -u +%Y%m%dT%H%M%SZ)
2. NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts --outdir reports/2026-01-vectorization-gap/phase_b/$STAMP/profile/ | tee reports/2026-01-vectorization-gap/phase_b/$STAMP/profile_run.log
3. python - <<'PY'
import json, os, textwrap
from pathlib import Path
stamp = os.environ['STAMP']
base = Path('reports/2026-01-vectorization-gap/phase_b') / stamp
metrics = json.load((base / 'profile' / 'benchmark_results.json').open())[0]
summary = textwrap.dedent(f"""
# Phase B1 profiler rerun ({stamp})
- Command: benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile
- correlation_warm: {metrics['correlation_warm']:.12f}
- sum_ratio: {metrics['sum_ratio']:.12f}
- speedup_warm: {metrics['speedup_warm']:.3f}
- notes: thresholds corr ≥ 0.999 and |sum_ratio − 1| ≤ 5e-3 per plans/active/vectorization-gap-audit.md Phase B1
""")
(base / 'summary.md').write_text(summary)
if metrics['correlation_warm'] < 0.999 or abs(metrics['sum_ratio'] - 1.0) > 5e-3:
    raise SystemExit('Parity threshold not met; follow blocked protocol in input.md')
PY
4. NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q > reports/2026-01-vectorization-gap/phase_b/$STAMP/collect.log
5. python - <<'PY'
import json, os, platform
from pathlib import Path
stamp = os.environ['STAMP']
data = {
    "python": platform.python_version(),
    "torch": __import__('torch').__version__,
    "git_sha": os.popen('git rev-parse HEAD').read().strip(),
}
base = Path('reports/2026-01-vectorization-gap/phase_b') / stamp
(base / 'env.json').write_text(json.dumps(data, indent=2))
with (base / 'commands.txt').open('w') as fh:
    fh.write("export STAMP='" + stamp + "'\n")
    fh.write("NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts --outdir reports/2026-01-vectorization-gap/phase_b/$STAMP/profile/\n")
    fh.write("NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q > reports/2026-01-vectorization-gap/phase_b/$STAMP/collect.log\n")
PY
6. Update docs/fix_plan.md [VECTOR-GAPS-002] and plans/active/vectorization-gap-audit.md Phase B1 with metrics, artifact paths, and attempt outcome; avoid Phase B2/B3 until thresholds are satisfied.
Pitfalls To Avoid:
- Do not reuse or overwrite any 20251009/20251010 profiler directories; always create a fresh $STAMP.
- Keep this loop evidence-only: no production code edits, no plan rewrites beyond logging metrics.
- Ensure KMP_DUPLICATE_LIB_OK=TRUE stays set or the run may crash due to MKL conflicts.
- Use NB_C_BIN=./golden_suite_generator/nanoBragg so the C reference matches prior parity bundles.
- Stay on CPU float32; skip CUDA until PERF-PYTORCH-004 resumes.
- Capture profile_run.log, env.json, and commands.txt even on failure.
- Treat correlation and sum_ratio gates as hard stops; if they fail, follow the blocked protocol before exiting.
- Verify benchmark_detailed.py completed without SIGKILL; large ROI runs are memory-intensive.
- Keep pytest --collect-only output for audit; missing it blocks ledger updates.
Pointers:
- docs/fix_plan.md:3801
- plans/active/vectorization-gap-audit.md:34
- docs/architecture/pytorch_design.md:101
- docs/development/pytorch_runtime_checklist.md:22
- reports/2025-11-source-weights/phase_h/20251010T002324Z/parity_reassessment.md
Next Up: Phase B2 — map ≥1% profiler hotspots to the Phase A loop inventory once B1 produces a green bundle.
