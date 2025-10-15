Summary: Capture a clean Phase O chunk 03 guard rerun by splitting into three parts, then refresh the baseline artifacts/ledgers.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Full pytest run and triage
Branch: feature/spec-based-2
Mapped tests: 
  - timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part1.txt -k "not gradcheck" --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_03/pytest_part1.xml
  - timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part2.txt -k "not gradcheck" --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_03/pytest_part2.xml
  - timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part3.txt -k "not gradcheck" --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/$STAMP/chunks/chunk_03/pytest_part3.xml
Artifacts: reports/2026-01-test-suite-triage/phase_o/$STAMP/{gradients/*,chunks/chunk_03/pytest_part{1,2,3}.{log,xml},chunks/chunk_03/summary.md,summary.md}, reports/2026-01-test-suite-triage/remediation_tracker.md, plans/active/test-suite-triage.md, docs/fix_plan.md
Do Now: [TEST-SUITE-TRIAGE-001] Next Action 9 — run chunk 03 (parts 1/2/3) with guard and update summaries using the commands above (export STAMP in this shell first).
If Blocked: If any part still times out or fails unexpectedly, stop immediately, capture the log + exit code in the new STAMP directory, and log the attempt in docs/fix_plan.md without retrying; ping me with the failure context.
Priorities & Rationale:
- docs/fix_plan.md:60-75 spells out the revised three-part workflow we must satisfy before touching C18 tolerances.
- plans/active/test-suite-triage.md:304-310 enumerates Phase O tasks (O5a–O6) gating this effort.
- reports/2026-01-test-suite-triage/phase_o/20251015T034633Z/chunks/chunk_03/summary.md:1 documents the prior timeout and why gradients must be isolated.
- reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part1.txt ensures the first shard includes test_at_parallel_009.py which we dropped during the last attempt.
- reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part3.txt constrains the gradients payload so the guard run can finish within the 600 s harness cap.
How-To Map:
1. In a fresh shell, chain the setup so STAMP persists:
   `export STAMP=$(date -u +%Y%m%dT%H%M%SZ) && mkdir -p reports/2026-01-test-suite-triage/phase_o/${STAMP}/{gradients,chunks/chunk_03}`
2. Copy the validated guard evidence into the new STAMP bundle:
   `cp reports/2026-01-test-suite-triage/phase_o/20251015T014403Z/grad_guard/* reports/2026-01-test-suite-triage/phase_o/${STAMP}/gradients/`
3. Log the shard rationale before running commands:
   `printf 'part1=cli_001,flu_001,io_004,parallel_009,parallel_020\npart2=perf_001,pre_002,sta_001,configuration_consistency,show_config\npart3=gradients_only\n' >> reports/2026-01-test-suite-triage/phase_o/${STAMP}/commands.txt`
4. Execute the three mapped pytest commands in order (parts 1→3) in the same shell so `$STAMP` stays defined; each command should `tee` into the chunk directory paths shown above.
5. After each run, append elapsed wall time (`/usr/bin/time -f 'elapsed=%E'` optional) and exit code to `commands.txt` for provenance.
6. Aggregate totals once all three XML files exist:
   ```bash
   python - <<'PY' > reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/totals.txt
import os
import xml.etree.ElementTree as ET
from collections import Counter
stamp = os.environ['STAMP']
paths = [
    f'reports/2026-01-test-suite-triage/phase_o/{stamp}/chunks/chunk_03/pytest_part1.xml',
    f'reports/2026-01-test-suite-triage/phase_o/{stamp}/chunks/chunk_03/pytest_part2.xml',
    f'reports/2026-01-test-suite-triage/phase_o/{stamp}/chunks/chunk_03/pytest_part3.xml',
]
totals = Counter()
for path in paths:
    suite = ET.parse(path).getroot().find('testsuite')
    totals['tests'] += int(suite.attrib.get('tests', 0))
    totals['failures'] += int(suite.attrib.get('failures', 0))
    totals['errors'] += int(suite.attrib.get('errors', 0))
    totals['skipped'] += int(suite.attrib.get('skipped', 0))
passed = totals['tests'] - totals['failures'] - totals['errors'] - totals['skipped']
print(f"passes={passed} failures={totals['failures']} errors={totals['errors']} skipped={totals['skipped']}")
PY
   ```
   Append the printed totals to `chunks/chunk_03/summary.md`, and manually note xfail counts + slowest tests from the logs right below the totals.
7. Update `reports/2026-01-test-suite-triage/phase_o/${STAMP}/summary.md` with the new global pass/fail/skip counts and cite which clusters remain.
8. Move the stray `reports/2026-01-test-suite-triage/phase_o/$(date -u +%Y%m%dT%H%M%SZ)/grad_guard/pytest.xml` into the new `${STAMP}/gradients/` folder, then prune the older timeout STAMP directories only after confirming all data is copied.
9. Refresh documentation:
   - Update `reports/2026-01-test-suite-triage/remediation_tracker.md` (C2 counts should drop to 0) and sync Phase O status in plans/active/test-suite-triage.md (mark O5a–O5f as [D]).
   - Amend docs/fix_plan.md Attempts History with the new STAMP and mark Next Actions 9–10 as complete once artifacts + ledgers match.
10. Commit the evidence updates but leave production code untouched; record the exact pytest selectors and STAMP in the commit message.
Pitfalls To Avoid:
- Do not spawn a new shell between exporting STAMP and running the pytest commands; `$STAMP` must stay in scope.
- Keep `NANOBRAGG_DISABLE_COMPILE=1` on every command; missing it will resurrect the gradcheck failures.
- Do not edit the selectors files again—only use the existing manifests we just staged.
- Avoid deleting any directory referenced in docs/index.md; move the stray pytest.xml instead.
- If part 3 nears the 600 s limit, stop rather than guessing at new filters, and escalate.
- Ensure `commands.txt` captures timings + exit codes; we need this for remediation tracker math.
- When updating docs/fix_plan.md, preserve existing Attempt order—no reflowing unrelated sections.
- Do not rerun the full pytest ladder; stay scoped to chunk 03 + documentation updates.
- Remember to set `KMP_DUPLICATE_LIB_OK=TRUE` and keep CUDA disabled (`CUDA_VISIBLE_DEVICES=-1`).
- Double-check that gradient logs only live under the new STAMP before pruning old folders.
Pointers:
- docs/fix_plan.md:60-75 — Revised three-part instructions and guard requirements.
- plans/active/test-suite-triage.md:304-310 — Phase O task table defining O5a–O6 deliverables.
- reports/2026-01-test-suite-triage/phase_o/20251015T034633Z/chunks/chunk_03/summary.md:1 — Prior timeout evidence for context.
- reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part1.txt:1 — Current part 1 manifest (includes test_at_parallel_009.py).
- reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part3.txt:1 — Gradient-only manifest to run in isolation.
Next Up: If time remains after clean baseline & ledger sync, start scoping the remaining C18 tolerance failures (see reports/2026-01-test-suite-triage/phase_o/20251015T011629Z/summary.md) for Sprint 1.5 planning.
