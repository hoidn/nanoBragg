Summary: Finish Phase R chunk 03 under the guard env so the full-suite ladder has zero failures logged.
Mode: Parity
Focus: TEST-SUITE-TRIAGE-001 / Next Action 16 – Phase R chunk 03 rerun (R2)
Branch: feature/spec-based-2
Mapped tests: pytest -vv tests/test_at_cli_001.py tests/test_at_flu_001.py tests/test_at_io_004.py tests/test_at_parallel_009.py tests/test_at_parallel_020.py tests/test_at_perf_001.py tests/test_at_pre_002.py tests/test_at_sta_001.py tests/test_configuration_consistency.py tests/test_gradients.py tests/test_show_config.py --maxfail=0 --durations=25
Artifacts: reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_03/, reports/2026-01-test-suite-triage/phase_r/${STAMP}/summary.md, reports/2026-01-test-suite-triage/phase_r/${STAMP}/commands.txt
Do Now: TEST-SUITE-TRIAGE-001 / Next Action 16 – Phase R chunk 03 rerun (R2); set `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` then run `timeout 2400 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_at_cli_001.py tests/test_at_flu_001.py tests/test_at_io_004.py tests/test_at_parallel_009.py tests/test_at_parallel_020.py tests/test_at_perf_001.py tests/test_at_pre_002.py tests/test_at_sta_001.py tests/test_configuration_consistency.py tests/test_gradients.py tests/test_show_config.py --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_03/pytest.xml 2>&1 | tee reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_03/pytest.log`.
If Blocked: If the chunk exceeds 2400 s or aborts, save the partial log as `reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_03/timeout.log`, record the failing selector + reason in docs/fix_plan.md Attempt history, and stop for supervisor guidance.
Priorities & Rationale:
- plans/active/test-suite-triage.md:374-383 — Phase R tasks call for rerunning chunk 03 with extended timeout and recording the ladder manifest.
- docs/fix_plan.md:795-796 — Attempt #81 timed out; Next Action 16 requires an isolated rerun with longer timeout and complete artifact set.
- docs/development/testing_strategy.md:34-78 — Guardrail env vars (CPU-only, KMP, compile guard) mandated for full-suite parity captures.
- reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/commands.txt — Canonical chunk roster to mirror when generating `commands.txt`.
- docs/development/pytorch_runtime_checklist.md:12-48 — Reinforces device/dtype neutrality and compile guard expectations during test executions.
How-To Map:
- Prep directories: `mkdir -p reports/2026-01-test-suite-triage/phase_r/${STAMP}/{env,chunks/chunk_03}`.
- Reproduce the ladder manifest: `cp reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/commands.txt reports/2026-01-test-suite-triage/phase_r/${STAMP}/commands.txt` then edit the copy so the first line documents the guard env (`# CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1`).
- Capture environment snapshot:
  ```bash
  python - <<'PY' > reports/2026-01-test-suite-triage/phase_r/${STAMP}/env/python_env.json
import json, sys, platform
try:
    import torch
    torch_info = {
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda,
    }
except ModuleNotFoundError:
    torch_info = {"torch_version": None, "cuda_available": False, "cuda_version": None}
json.dump(
    {
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch_info,
    },
    sys.stdout,
    indent=2,
)
PY
  ```
- Execute the chunk command shown in Do Now; after it finishes, run `echo $? > reports/2026-01-test-suite-triage/phase_r/${STAMP}/chunks/chunk_03/exit_code.txt` and append timing stats to `reports/2026-01-test-suite-triage/phase_r/${STAMP}/summary.md` using the Attempt #81 layout as a template.
- Aggregate results so the summary shows updated totals:
  ```bash
  python - <<'PY'
import xml.etree.ElementTree as ET
from collections import Counter
import pathlib, os
stamp = os.environ['STAMP']
base = pathlib.Path('reports/2026-01-test-suite-triage/phase_r') / stamp / 'chunks'
totals = Counter()
for chunk in sorted(base.glob('chunk_*')):
    junit = chunk / 'pytest.xml'
    if junit.exists():
        suite = ET.parse(junit).getroot().find('testsuite')
        totals['tests'] += int(suite.attrib.get('tests', 0))
        totals['failures'] += int(suite.attrib.get('failures', 0))
        totals['errors'] += int(suite.attrib.get('errors', 0))
        totals['skipped'] += int(suite.attrib.get('skipped', 0))
passed = totals['tests'] - totals['failures'] - totals['errors'] - totals['skipped']
print(f"passes={passed} failures={totals['failures']} errors={totals['errors']} skipped={totals['skipped']}")
PY
  ```
- Update docs once the chunk completes: append Attempt details to docs/fix_plan.md and refresh `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md` with the new STAMP + zero-failure note.
Pitfalls To Avoid:
- Do not forget `NANOBRAGG_DISABLE_COMPILE=1`; missing it will resurrect donated-buffer gradcheck failures.
- Keep the STAMP constant across the manifest, chunk output, and summary files.
- Ensure `reports/.../chunk_03/` exists before piping output via `tee`, otherwise the command will fail.
- Avoid truncating the command list; every module from the chunk roster must be included to maintain parity with Phase O.
- Capture junit XML even on success; supervisors need it for aggregation scripts.
- Leave protected files from docs/index.md untouched (loop.sh, supervisor.sh, input.md, etc.).
- Use ASCII only when editing summary or tracker documents.
- Do not delete the partial Attempt #81 artifacts; add new STAMP rather than overwriting.
Pointers:
- plans/active/test-suite-triage.md:374-383
- docs/fix_plan.md:795-796
- reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/commands.txt
- docs/development/testing_strategy.md:34-78
- docs/development/pytorch_runtime_checklist.md:12-48
Next Up: If chunk 03 completes quickly, aggregate chunk totals and draft the closure note so Phase R R3 can finish next loop.
