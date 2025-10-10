Summary: Run the authoritative 4096² AT parity selector to confirm the regression on current HEAD and log the results beside the Phase B1 bundle so VECTOR-PARITY-001 can advance to trace triage.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: pytest -v tests/test_at_parallel_*.py -k 4096
Artifacts: reports/2026-01-vectorization-parity/phase_b/$STAMP/{pytest_parallel.log,summary.md,commands.txt,env.json}
Do Now: [VECTOR-PARITY-001] Phase B2 — export STAMP=$(date -u +%Y%m%dT%H%M%SZ); KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_at_parallel_*.py -k 4096 | tee reports/2026-01-vectorization-parity/phase_b/$STAMP/pytest_parallel.log; add env.json + summary.md capturing exit status and any reported correlations; record the exact command in commands.txt.
If Blocked: If pytest errors or the selector fails to run, capture the full console output in pytest_parallel.log, note the failure (including tracebacks and exit code) in summary.md, update docs/fix_plan.md Attempts with the partial bundle path, and stop—do not rerun under modified parameters.
Priorities & Rationale:
- docs/fix_plan.md:4010-4031 — Next Actions now require Phase B2 pytest evidence before Phase C tracing can start.
- plans/active/vectorization-parity-regression.md:32-34 — Phase B1 is complete; Phase B2 parity selectors are the remaining gate.
- specs/spec-a-core.md:151-155 — Equal-weight contract sets the correlation/sum_ratio thresholds we must compare against.
- docs/development/pytorch_runtime_checklist.md:22-27 — Reinforces the equal-weight guardrail and references the parity memo.
- reports/2026-01-vectorization-parity/phase_b/20251010T030852Z/summary.md — Use this benchmark bundle as context when documenting pytest findings.
How-To Map:
1. export STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-vectorization-parity/phase_b/$STAMP.
2. KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_at_parallel_*.py -k 4096 | tee reports/2026-01-vectorization-parity/phase_b/$STAMP/pytest_parallel.log.
3. python - <<'PY'
import json, os, platform, subprocess
from pathlib import Path
stamp = os.environ['STAMP']
root = Path('reports/2026-01-vectorization-parity/phase_b') / stamp
root.mkdir(parents=True, exist_ok=True)
info = {
    "python": platform.python_version(),
    "torch": __import__('torch').__version__,
    "git_sha": subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip(),
    "device": "cpu",
    "dtype": "float32",
}
root.joinpath('env.json').write_text(json.dumps(info, indent=2))
PY
4. python - <<'PY'
import os
from pathlib import Path
stamp = os.environ['STAMP']
root = Path('reports/2026-01-vectorization-parity/phase_b') / stamp
log_path = root / 'pytest_parallel.log'
summary_lines = [
    "# Phase B2 Parity Selector Summary\n",
    "- Prior benchmark bundle: reports/2026-01-vectorization-parity/phase_b/20251010T030852Z/summary.md\n",
]
if log_path.exists():
    summary_lines.append("- pytest command: NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_at_parallel_*.py -k 4096\n")
    summary_lines.append("- Exit status: <fill after review>\n")
    summary_lines.append("- Notable outputs: <copy correlation values or failing test names from pytest_parallel.log>\n")
else:
    summary_lines.append("- pytest_parallel.log missing (see attempts history)\n")
summary_lines.append("- Thresholds: correlation ≥0.999, |sum_ratio−1| ≤5e-3 (specs/spec-a-core.md:151-155)\n")
summary_lines.append("- Notes: <document whether regression reproduced and any discrepancies vs benchmark metrics>\n")
root.joinpath('summary.md').write_text("".join(summary_lines))
PY
5. printf "%s\n" \
   "export STAMP=$STAMP" \
   "KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_at_parallel_*.py -k 4096" \
   > reports/2026-01-vectorization-parity/phase_b/$STAMP/commands.txt
Pitfalls To Avoid:
- Evidence-only loop: do not modify simulator or tests.
- Keep NB_RUN_PARALLEL=1 and NB_C_BIN pointing to ./golden_suite_generator/nanoBragg to match parity baseline.
- Do not reuse the 20251010T030852Z STAMP; create a fresh timestamp for this run.
- Capture the entire pytest log (including failures) before editing summary.md.
- If pytest prints correlation metrics, copy them verbatim into summary.md; otherwise note their absence.
- Stay on CPU float32; changing device/dtype invalidates comparisons.
- Record the exit code; if non-zero, flag it clearly in summary.md and fix_plan Attempt notes.
- Avoid running additional selectors; execute only the command above this loop.
- Ensure env.json is written after the run so git_sha matches the tested commit.
- Do not delete or overwrite prior Phase B1 artifacts when adding the new bundle.
Pointers:
- docs/fix_plan.md:4010-4097
- plans/active/vectorization-parity-regression.md:32-34
- specs/spec-a-core.md:151-155
- docs/development/pytorch_runtime_checklist.md:22-27
- reports/2026-01-vectorization-parity/phase_b/20251010T030852Z/summary.md
Next Up: Phase B3 ROI nb-compare sweep once pytest evidence is archived and analyzed.
