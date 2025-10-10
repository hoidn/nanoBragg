Summary: Reproduce the 4096² parity regression with fresh benchmark + nb-compare evidence so Phase B can move to trace triage.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: pytest -v tests/test_at_parallel_*.py -k 4096
Artifacts: reports/2026-01-vectorization-parity/phase_b/$STAMP/{profile,nb_compare_full,summary.md,env.json,commands.txt}
Do Now: [VECTOR-PARITY-001] Phase B1 — export STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-vectorization-parity/phase_b/$STAMP/{profile,nb_compare_full}; NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts; NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE nb-compare --resample --threshold 0.999 --outdir reports/2026-01-vectorization-parity/phase_b/$STAMP/nb_compare_full -- -default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -distance 100 -detpixels 4096.
If Blocked: If benchmark or nb-compare fails (exit ≠ 0 or correlation missing), capture stdout/stderr to reports/2026-01-vectorization-parity/phase_b/$STAMP/errors.log, note the failure in summary.md, update docs/fix_plan.md Attempt with the blocker, and stop—do NOT rerun with altered parameters.
Priorities & Rationale:
- docs/fix_plan.md:4007 — Phase B1 reproduction (benchmark + nb-compare copied under phase_b/$STAMP) is the front gate to unblock parity diagnosis.
- plans/active/vectorization-parity-regression.md:12 — Status snapshot + Phase B1 guidance call for full provenance, profiler trace, and sum_ratio capture.
- specs/spec-a-core.md:151 — Normative equal-weight contract; evidence must report correlation ≥0.999 and |sum_ratio−1| ≤5e-3.
- docs/development/pytorch_runtime_checklist.md:22 — Runtime guardrail reiterating the same thresholds/memo for source normalization parity.
- docs/development/testing_strategy.md:316 — Artifact-backed closure requires correlation + C_sum/Py_sum/sum_ratio before claiming parity restored.
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
(root / 'env.json').write_text(json.dumps(info, indent=2))
PY
6. python - <<'PY'
import json, os
from pathlib import Path
stamp = os.environ['STAMP']
root = Path('reports/2026-01-vectorization-parity/phase_b') / stamp
summary_path = root / 'nb_compare_full' / 'summary.json'
metrics = {}
if summary_path.exists():
    metrics = json.load(summary_path.open())
lines = [
    "# Phase B1 Benchmark + Parity Summary\n",
    f"- Benchmark bundle: {os.environ.get('BENCH_DIR', '<unset>')}\n",
    "- nb-compare metrics:" + (" see nb_compare_full/summary.json" if metrics else " missing (nb-compare failed)") + "\n",
]
if metrics:
    for key in ("correlation", "rmse", "c_sum", "py_sum", "sum_ratio"):
        if key in metrics:
            lines.append(f"  - {key}: {metrics[key]}\n")
lines.append("- Thresholds: correlation ≥0.999, |sum_ratio−1| ≤5e-3 (specs/spec-a-core.md:151; runtime checklist item #4)\n")
lines.append("- Notes: <add observations / anomalies>\n")
(root / 'summary.md').write_text("".join(lines))
PY
7. printf "%s\n" "export STAMP=$STAMP" "NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts" "export BENCH_DIR=$BENCH_DIR" "rsync -a $BENCH_DIR/ reports/2026-01-vectorization-parity/phase_b/$STAMP/profile/" "NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE nb-compare --resample --threshold 0.999 --outdir reports/2026-01-vectorization-parity/phase_b/$STAMP/nb_compare_full -- -default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -distance 100 -detpixels 4096" > reports/2026-01-vectorization-parity/phase_b/$STAMP/commands.txt
Pitfalls To Avoid:
- Do not edit benchmark_detailed.py or nb-compare; this is an evidence-only run.
- Confirm BENCH_DIR points to the fresh run before copying (check benchmark_console.log).
- Keep execution on CPU float32; deviating devices/dtypes invalidate comparisons.
- Maintain NB_C_BIN=./golden_suite_generator/nanoBragg; absence of the instrumented binary is blocking.
- Do not skip nb-compare; sum_ratio is mandatory for parity metrics.
- Preserve profiler trace JSON when copying; downstream analysis needs it.
- Avoid multiple benchmark runs in one loop—copy the first result to prevent confusion.
- Never commit raw artifacts under reports/benchmarks/; only copied evidence in phase_b/$STAMP belongs in the bundle.
- Record every command in commands.txt for auditability.
- If correlation already ≥0.999 with |sum_ratio−1| ≤5e-3, document the surprise in summary.md and halt further debugging pending supervisor review.
Pointers:
- docs/fix_plan.md:4007
- plans/active/vectorization-parity-regression.md:12
- specs/spec-a-core.md:151
- docs/development/pytorch_runtime_checklist.md:22
- docs/development/testing_strategy.md:316
Next Up: Phase B2 — run pytest -v tests/test_at_parallel_*.py -k 4096 after the parity bundle is archived.
