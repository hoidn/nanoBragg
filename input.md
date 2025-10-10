Summary: Consolidate good vs bad 4096² parity evidence so the new regression plan starts with a single authoritative baseline.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_a/$STAMP/artifact_matrix.md, reports/2026-01-vectorization-parity/phase_a/$STAMP/param_diff.md, reports/2026-01-vectorization-parity/phase_a/$STAMP/commands.txt
Do Now: [VECTOR-PARITY-001] Phase A1–A3 — export STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-vectorization-parity/phase_a/$STAMP; generate artifact_matrix.md + param_diff.md covering good run reports/benchmarks/20251009-161714 and failing runs under reports/2026-01-vectorization-gap/phase_b/20251009T*/ and 20251010T02*/; note unresolved items and record the exact commands used in commands.txt.
If Blocked: If any referenced artifact is missing, document the gap in artifact_matrix.md (Missing: <path>) and halt—do not fabricate metrics. Leave a note in docs/fix_plan.md attempt update describing the missing file before stopping.
Priorities & Rationale:
- docs/fix_plan.md:4007 — New entry requires Phase A evidence bundle before further debugging.
- plans/active/vectorization-parity-regression.md:14 — Phase A exit criteria define artifact_matrix.md, param_diff.md, and ledger update expectations.
- docs/development/testing_strategy.md:52 — Establishes parity thresholds (corr ≥0.999, |sum_ratio−1| ≤5e-3) to highlight in the matrix.
- docs/development/pytorch_runtime_checklist.md:18 — Reiterates equal-weighting guard, ensuring parameter diffs flag any deviation.
- reports/2026-01-vectorization-gap/phase_b/20251009T095913Z/summary.md — Provides primary failing metrics to capture in the matrix.
How-To Map:
1. export STAMP=$(date -u +%Y%m%dT%H%M%SZ)
2. mkdir -p reports/2026-01-vectorization-parity/phase_a/$STAMP
3. python - <<'PY'
import json, os
from pathlib import Path
stamp = os.environ['STAMP']
base = Path('reports/2026-01-vectorization-parity/phase_a') / stamp
base.mkdir(parents=True, exist_ok=True)
rows = []
# Known-good run
rows.append({
    "label": "good-20251009-161714",
    "path": "reports/benchmarks/20251009-161714/benchmark_results.json",
    "metrics": json.load(Path("reports/benchmarks/20251009-161714/benchmark_results.json").open())[0],
    "env": None,
})
# Failing runs (current HEAD bundles)
fail_globs = [Path('reports/2026-01-vectorization-gap/phase_b').glob('20251009T*/'),
              Path('reports/2026-01-vectorization-gap/phase_b').glob('20251010T02*/')]
for glob_iter in fail_globs:
    for directory in sorted(glob_iter):
        metrics_file = None
        for candidate in ['benchmark_results.json', 'failed/benchmark_results.json', 'profile/benchmark_results.json']:
            path = directory / candidate
            if path.exists():
                metrics_file = path
                break
        if not metrics_file:
            continue
        env = None
        env_path = directory / 'env.json'
        if env_path.exists():
            env = json.load(env_path.open())
        rows.append({
            "label": directory.name,
            "path": str(metrics_file),
            "metrics": json.load(metrics_file.open())[0],
            "env": env,
        })
md_lines = ["# Artifact Matrix\n", "| run | correlation_warm | sum_ratio | speedup_warm | git_sha | notes |", "| --- | --- | --- | --- | --- | --- |"]
for row in rows:
    metrics = row['metrics']
    corr = metrics.get('correlation_warm', 'n/a')
    sum_ratio = metrics.get('sum_ratio', 'n/a')
    speed = metrics.get('speedup_warm', 'n/a')
    git_sha = row['env'].get('git_sha') if row['env'] else 'missing'
    note = f"path={row['path']}"
    md_lines.append(f"| {row['label']} | {corr} | {sum_ratio} | {speed} | {git_sha} | {note} |")
# Placeholder for open questions
md_lines.append("\n## Open Questions\n- [ ] Capture git SHA for reports/benchmarks/20251009-161714 (not recorded).\n- [ ] Confirm whether any smaller ROI bundles exist for comparison.\n")
(base / 'artifact_matrix.md').write_text("\n".join(md_lines))
PY
4. python - <<'PY'
import os
from pathlib import Path
stamp = os.environ['STAMP']
base = Path('reports/2026-01-vectorization-parity/phase_a') / stamp
lines = ["# Parameter Diff\n"]
def append_run(title, cmd_path, env_path):
    lines.append(f"## {title}\n")
    if cmd_path.exists():
        lines.append('```\n' + cmd_path.read_text().strip() + '\n```\n')
    else:
        lines.append('_commands.txt missing_\n')
    if env_path.exists():
        lines.append('```json\n' + env_path.read_text().strip() + '\n```\n')
    else:
        lines.append('_env.json missing_\n')
append_run('failing 20251009T095913Z', Path('reports/2026-01-vectorization-gap/phase_b/20251009T095913Z/commands.txt'), Path('reports/2026-01-vectorization-gap/phase_b/20251009T095913Z/env.json'))
append_run('failing 20251010T022314Z', Path('reports/2026-01-vectorization-gap/phase_b/20251010T022314Z/commands.txt'), Path('reports/2026-01-vectorization-gap/phase_b/20251010T022314Z/env.json'))
append_run('good 20251009-161714', Path('reports/benchmarks/20251009-161714/commands.txt'), Path('reports/benchmarks/20251009-161714/env.json'))
(base / 'param_diff.md').write_text("\n".join(lines))
PY
5. {
    echo "export STAMP=$STAMP";
    echo "python artifact_matrix generation (see step 3)";
    echo "python param_diff generation (see step 4)";
} > reports/2026-01-vectorization-parity/phase_a/$STAMP/commands.txt
6. Review artifact_matrix.md: append any additional open questions or observations per Phase A3 guidance (e.g., parity thresholds, missing files).
7. Update docs/fix_plan.md [VECTOR-PARITY-001] with Attempt #1 summarising the Phase A bundle (paths, key metrics, noted gaps).
Pitfalls To Avoid:
- Do not rerun benchmark_detailed.py or modify profiler outputs; this loop reuses existing evidence only.
- Keep scripts read-only: never edit artifacts under reports/benchmarks/2025* beyond new summaries.
- Ensure python scripts gracefully handle missing files and record gaps instead of failing silently.
- Preserve device/dtype context in notes (CPU float32); flag any deviation in param_diff.md.
- Avoid touching production code or plans beyond the required ledger updates.
- Record every command you run into commands.txt; no ad-hoc shell history.
- Maintain ASCII output; avoid rich formatting beyond Markdown tables for compatibility with prompts.
- When updating docs/fix_plan.md, only add the new Attempt; do not alter existing historical entries.
- Run `pytest --collect-only` only if you end up editing test harness files (not expected this loop).
- If you discover additional failing bundles, append them to the matrix instead of overwriting; keep provenance clear.
Pointers:
- docs/fix_plan.md:4007
- plans/active/vectorization-parity-regression.md:14
- docs/development/testing_strategy.md:52
- docs/development/pytorch_runtime_checklist.md:18
- reports/2026-01-vectorization-gap/phase_b/20251009T095913Z/summary.md
Next Up: Phase B1 — rerun the 4096² benchmark on current HEAD once the evidence baseline is captured.
