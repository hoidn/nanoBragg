Summary: Reproduce the 4096² CPU warm profiler bundle so VECTOR-GAPS-002 Phase B can unblock backlog prioritisation.
Mode: Perf
Focus: [VECTOR-GAPS-002] Vectorization gap audit
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-gap/phase_b/$STAMP/profile/, reports/2026-01-vectorization-gap/phase_b/$STAMP/profile_run.log, reports/2026-01-vectorization-gap/phase_b/$STAMP/summary.md, reports/2026-01-vectorization-gap/phase_b/$STAMP/collect.log, reports/2026-01-vectorization-gap/phase_b/$STAMP/env.json, reports/2026-01-vectorization-gap/phase_b/$STAMP/commands.txt
Do Now: [VECTOR-GAPS-002] Phase B1 — export STAMP=$(date -u +%Y%m%dT%H%M%SZ) && NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts --outdir reports/2026-01-vectorization-gap/phase_b/$STAMP/profile/
If Blocked: If correlation_warm < 0.999 or |sum_ratio−1| > 5e-3, file the full output under reports/2026-01-vectorization-gap/phase_b/$STAMP/failed/, capture NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q > reports/2026-01-vectorization-gap/phase_b/$STAMP/collect.log, and document the failure as a new Attempt on [VECTOR-GAPS-002] before stopping.
Priorities & Rationale:
- docs/fix_plan.md:3791 — Phase B1 is the current gate; success requires corr ≥0.999 and |sum_ratio−1| ≤5e-3.
- plans/active/vectorization-gap-audit.md:31 — Phase B backlog work depends on this profiler rerun and artifact layout.
- docs/architecture/pytorch_design.md:93 — Source-weight parity memo underpins the correlation thresholds you must hit.
- docs/development/pytorch_runtime_checklist.md:1 — Perf loops must stay vectorized and run with KMP_DUPLICATE_LIB_OK=TRUE.
- docs/development/testing_strategy.md:18 — Use CPU float32 evidence first; GPU follow-ups wait until PERF-PYTORCH-004 resumes.
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
- notes: thresholds corr≥0.999, |sum_ratio−1|≤5e-3 per plans/active/vectorization-gap-audit.md Phase B1
""")
(base / 'summary.md').write_text(summary)
if metrics['correlation_warm'] < 0.999 or abs(metrics['sum_ratio'] - 1.0) > 5e-3:
    raise SystemExit('Parity threshold not met; follow blocked protocol')
PY
4. NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q > reports/2026-01-vectorization-gap/phase_b/$STAMP/collect.log
5. Record env metadata (python - <<'PY' import json, os, platform; from pathlib import Path; data={"python":platform.python_version(),"git_sha":os.popen('git rev-parse HEAD').read().strip(),"torch":__import__('torch').__version__}; Path('reports/2026-01-vectorization-gap/phase_b')/os.environ['STAMP']/ 'env.json').write_text(json.dumps(data, indent=2)) PY) and list every command in commands.txt
6. Update docs/fix_plan.md [VECTOR-GAPS-002] and plans/active/vectorization-gap-audit.md Phase B1 with metrics + artifact paths before ending the loop
Pitfalls To Avoid:
- No code or plan edits; evidence-only loop.
- Do not overwrite prior 20251009 profiler artifacts; always use a fresh $STAMP directory.
- Keep NB_C_BIN pointed at ./golden_suite_generator/nanoBragg for C parity.
- Maintain vectorization guardrails: never edit simulator loops or add Python-side batching tweaks here.
- KMP_DUPLICATE_LIB_OK=TRUE is mandatory; missing it can crash MKL.
- Treat parity thresholds as hard stops; escalate via fix_plan if violated.
- Capture profile_run.log, env.json, and commands.txt even when the profiler fails.
- Skip CUDA runs this loop; CPU float32 only.
Pointers:
- docs/fix_plan.md:3791
- plans/active/vectorization-gap-audit.md:31
- docs/architecture/pytorch_design.md:93
- docs/development/pytorch_runtime_checklist.md:1
- reports/2025-11-source-weights/phase_h/20251010T002324Z/parity_reassessment.md
Next Up: Phase B2 — map profiler hotspots with scripts/analysis/vectorization_inventory.py once parity thresholds are satisfied.
