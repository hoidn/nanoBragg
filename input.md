Summary: Capture fresh 4096² benchmark and nb-compare evidence on current HEAD, logging both benchmark correlations and nb-compare totals so VECTOR-PARITY-001 Phase B can advance to trace triage.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: pytest -v tests/test_at_parallel_*.py -k 4096
Artifacts: reports/2026-01-vectorization-parity/phase_b/$STAMP/{profile,nb_compare_full,summary.md,env.json,commands.txt}
Do Now: [VECTOR-PARITY-001] Phase B1 — export STAMP=$(date -u +%Y%m%dT%H%M%SZ); NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts; NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE nb-compare --resample --threshold 0.999 --outdir reports/2026-01-vectorization-parity/phase_b/$STAMP/nb_compare_full -- -default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -distance 100 -detpixels 4096; update summary.md with both benchmark_results.json correlations and nb-compare metrics.
If Blocked: If any command exits non-zero or fails to emit correlation/sum_ratio, capture stdout/stderr under reports/2026-01-vectorization-parity/phase_b/$STAMP/errors.log, document the failure in summary.md (note which artifact is missing), update docs/fix_plan.md Attempt history with the partial bundle path, then stop—do not retry with altered parameters.
Priorities & Rationale:
- docs/fix_plan.md:4007 — VECTOR-PARITY-001 Next Actions now require Phase B1 to record benchmark correlation and nb-compare metrics together in summary.md.
- plans/active/vectorization-parity-regression.md:32 — Phase B1 guidance mandates copying the new benchmark bundle and running nb-compare immediately for correlation/sum_ratio capture.
- specs/spec-a-core.md:151 — Normative thresholds enforce correlation ≥0.999 and |sum_ratio−1| ≤5e-3 for source-weight scaling parity.
- docs/development/pytorch_runtime_checklist.md:22 — Runtime guardrail reiterates equal-weight expectations and artifact targets for source handling.
- docs/development/testing_strategy.md:316 — Tier-1 parity requires authoritative commands with archived metrics before proceeding to debugging.
How-To Map:
1. export STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-vectorization-parity/phase_b/$STAMP/{profile,nb_compare_full}.
2. NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts | tee reports/2026-01-vectorization-parity/phase_b/$STAMP/profile/benchmark_console.log.
3. export BENCH_DIR=$(ls -td reports/benchmarks/* | head -n1); rsync -a "$BENCH_DIR/" reports/2026-01-vectorization-parity/phase_b/$STAMP/profile/.
4. NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE nb-compare --resample --threshold 0.999 --outdir reports/2026-01-vectorization-parity/phase_b/$STAMP/nb_compare_full -- -default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -distance 100 -detpixels 4096.
5. python - <<'PY'
import json, os, platform, subprocess
from pathlib import Path
stamp = os.environ['STAMP']
root = Path('reports/2026-01-vectorization-parity/phase_b') / stamp
info = {
    "python": platform.python_version(),
    "torch": __import__('torch').__version__,
    "git_sha": subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip(),
    "device": "cpu",
    "dtype": "float32",
}
root.joinpath('env.json').write_text(json.dumps(info, indent=2))
PY
6. python - <<'PY'
import json, os
from pathlib import Path
stamp = os.environ['STAMP']
root = Path('reports/2026-01-vectorization-parity/phase_b') / stamp
bench_metrics = {}
bench_path = root / 'profile' / 'benchmark_results.json'
if bench_path.exists():
    data = json.load(bench_path.open())
    if isinstance(data, list) and data:
        bench_metrics = data[0]
nb_metrics = {}
nb_path = root / 'nb_compare_full' / 'summary.json'
if nb_path.exists():
    nb_metrics = json.load(nb_path.open())
lines = [
    "# Phase B1 Benchmark + Parity Summary\n",
    f"- Benchmark bundle: {os.environ.get('BENCH_DIR', '<unset>')}\n",
]
if bench_metrics:
    lines.append("- benchmark_results.json metrics:\n")
    for key in ("correlation_cold", "correlation_warm", "speedup_warm", "py_time_warm", "c_time"):
        if key in bench_metrics:
            lines.append(f"  - {key}: {bench_metrics[key]}\n")
else:
    lines.append("- benchmark_results.json metrics: missing (benchmark output not found)\n")
if nb_metrics:
    lines.append("- nb-compare metrics:\n")
    for key in ("correlation", "rmse", "c_sum", "py_sum", "sum_ratio"):
        if key in nb_metrics:
            lines.append(f"  - {key}: {nb_metrics[key]}\n")
else:
    lines.append("- nb-compare metrics: missing (see nb_compare_full/)\n")
lines.append("- Thresholds: correlation ≥0.999, |sum_ratio−1| ≤5e-3 (specs/spec-a-core.md:151; runtime checklist item #4)\n")
lines.append("- Notes: <add observations / anomalies, especially delta between benchmark and nb-compare correlations>\n")
root.joinpath('summary.md').write_text("".join(lines))
PY
7. printf "%s\n" \
   "export STAMP=$STAMP" \
   "NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts" \
   "export BENCH_DIR=$BENCH_DIR" \
   "rsync -a $BENCH_DIR/ reports/2026-01-vectorization-parity/phase_b/$STAMP/profile/" \
   "NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE nb-compare --resample --threshold 0.999 --outdir reports/2026-01-vectorization-parity/phase_b/$STAMP/nb_compare_full -- -default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -distance 100 -detpixels 4096" \
   > reports/2026-01-vectorization-parity/phase_b/$STAMP/commands.txt
Pitfalls To Avoid:
- Evidence-only loop: do not modify simulator or benchmark scripts.
- Ensure BENCH_DIR references the freshly produced reports/benchmarks/<ts> before copying.
- Stay on CPU float32; switching devices or dtypes invalidates parity comparisons.
- Preserve full profiler artifacts (trace.json, benchmark_results.json) within profile/.
- Do not skip nb-compare; sum_ratio is mandatory for diagnosing the scaling failure.
- Avoid rerunning the benchmark multiple times—copy the first fresh output to eliminate ambiguity.
- Keep NB_C_BIN pointed at ./golden_suite_generator/nanoBragg (instrumented binary).
- Update summary.md immediately after runs so benchmark vs nb-compare correlation deltas are explicit.
- Record any anomalies (unexpected success or missing files) in summary.md before ending the loop.
- Do not commit raw reports/benchmarks/<ts>; only the curated phase_b bundle belongs under version control.
Pointers:
- docs/fix_plan.md:4007
- plans/active/vectorization-parity-regression.md:30
- specs/spec-a-core.md:151
- docs/development/pytorch_runtime_checklist.md:22
- docs/development/testing_strategy.md:316
Next Up: Phase B2 — pytest -v tests/test_at_parallel_*.py -k 4096 once the Phase B1 bundle is archived.
