Summary: Refresh the 4096² benchmark + nb-compare evidence so VECTOR-PARITY-001 Phase B can proceed to trace triage on current HEAD.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: pytest -v tests/test_at_parallel_*.py -k 4096
Artifacts: reports/2026-01-vectorization-parity/phase_b/$STAMP/{profile,nb_compare_full,summary.md,env.json,commands.txt}
Do Now: [VECTOR-PARITY-001] Phase B1 — export STAMP=$(date -u +%Y%m%dT%H%M%SZ); NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts; NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE nb-compare --resample --threshold 0.999 --outdir reports/2026-01-vectorization-parity/phase_b/$STAMP/nb_compare_full -- -default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -distance 100 -detpixels 4096.
If Blocked: If any command exits non-zero or fails to emit correlation/sum_ratio, capture stdout/stderr to reports/2026-01-vectorization-parity/phase_b/$STAMP/errors.log, note the failure in summary.md, record the partial bundle path in docs/fix_plan.md Attempt history, then stop—do not retry with altered parameters.
Priorities & Rationale:
- docs/fix_plan.md:4007 — VECTOR-PARITY-001 now blocks on a fresh Phase B1 bundle with git provenance and nb-compare metrics.
- plans/active/vectorization-parity-regression.md:23 — Phase B1 requires copying the benchmark outputs into phase_b/$STAMP and immediately running nb-compare for correlation + sum_ratio.
- specs/spec-a-core.md:151 — Normative equal-weight scaling sets the acceptance thresholds: correlation ≥0.999 and |sum_ratio−1| ≤5e-3.
- docs/development/pytorch_runtime_checklist.md:22 — Runtime guardrail reiterating the same thresholds and memo linkage.
- docs/development/testing_strategy.md:316 — Tier-1 closure demands artifact-backed correlation + sum totals before parity work can advance.
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
7. printf "%s\n" \
   "export STAMP=$STAMP" \
   "NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts" \
   "export BENCH_DIR=$BENCH_DIR" \
   "rsync -a $BENCH_DIR/ reports/2026-01-vectorization-parity/phase_b/$STAMP/profile/" \
   "NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE nb-compare --resample --threshold 0.999 --outdir reports/2026-01-vectorization-parity/phase_b/$STAMP/nb_compare_full -- -default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -distance 100 -detpixels 4096" \
   > reports/2026-01-vectorization-parity/phase_b/$STAMP/commands.txt
Pitfalls To Avoid:
- Evidence-only loop: do not modify simulator or benchmark scripts.
- Ensure BENCH_DIR references the fresh run before copying artifacts.
- Keep execution on CPU float32; switching devices/dtypes voids comparisons.
- Preserve the full profiler trace JSON when copying the benchmark bundle.
- Do not skip nb-compare; sum_ratio is mandatory for diagnosing the scaling failure.
- Avoid repeated benchmark runs this loop—copy the first output to prevent ambiguity.
- Retain NB_C_BIN=./golden_suite_generator/nanoBragg; using the frozen binary hides instrumentation.
- Record all commands verbatim in commands.txt for audit.
- If thresholds unexpectedly pass, document the surprise and stop for supervisor review.
- Never commit raw reports/benchmarks/<ts>; only the copied phase_b bundle belongs in git.
Pointers:
- docs/fix_plan.md:4007
- plans/active/vectorization-parity-regression.md:23
- specs/spec-a-core.md:151
- docs/development/pytorch_runtime_checklist.md:22
- docs/development/testing_strategy.md:316
Next Up: Phase B2 — pytest -v tests/test_at_parallel_*.py -k 4096 once the Phase B1 bundle is archived.
