Summary: Split chunk 03 remainder into two guard-friendly runs and aggregate results so the Phase O baseline reflects only C18 + C19.
Mode: Parity
Focus: TEST-SUITE-TRIAGE-001 / Next Action 9 (Phase O5 split remainder)
Branch: feature/spec-based-2
Mapped tests: chunk_03_selectors_part1.txt (tests/test_at_cli_001.py … tests/test_at_parallel_020.py); chunk_03_selectors_part2.txt (tests/test_at_perf_001.py … tests/test_show_config.py)
Artifacts: reports/2026-01-test-suite-triage/phase_o/${STAMP}/{commands.txt,gradients/*}; reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/{pytest_part1.log,pytest_part1.xml,pytest_part2.log,pytest_part2.xml,summary.md}; reports/2026-01-test-suite-triage/phase_o/${STAMP}/summary.md; reports/2026-01-test-suite-triage/remediation_tracker.md
Do Now: TEST-SUITE-TRIAGE-001 Next Action 9 — export STAMP=$(date -u +%Y%m%dT%H%M%SZ) && mkdir -p reports/2026-01-test-suite-triage/phase_o/${STAMP}/{gradients,chunks/chunk_03} && cp reports/2026-01-test-suite-triage/phase_o/20251015T014403Z/grad_guard/{summary.md,exit_code.txt,pytest.xml} reports/2026-01-test-suite-triage/phase_o/${STAMP}/gradients/ && timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part1.txt -k "not gradcheck" --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest_part1.xml 2>&1 | tee reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest_part1.log
If Blocked: If either part run still times out, capture stdout + exit status, escalate in docs/fix_plan.md Attempts, and either split into thirds or request harness timeout raise before retrying.
Priorities & Rationale:
- plans/active/test-suite-triage.md:300-337 — Phase O5a–O5e require the split workflow before we touch C18 tolerances.
- docs/fix_plan.md:56-71 — Next Action 9/10 remain partial; completing the split run unblocks the ledger + tracker refresh.
- reports/2026-01-test-suite-triage/phase_o/blocked_attempt_73.md — documents why the unsplit command fails (600 s ceiling, STAMP scope loss).
- reports/2026-01-test-suite-triage/phase_o/20251015T030233Z/chunks/chunk_03/summary.md — prior template for summary.md; reuse structure with new counts.
How-To Map:
1. Create selector shards (keep original list intact):
   ```bash
   head -n 5 reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors.txt > reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part1.txt
   tail -n 5 reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors.txt > reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part2.txt
   ```
   Add a leading `# Derived <date>` comment to each file noting provenance.
2. Run the Do Now command inside a single `bash -lc` invocation so `$STAMP` persists (log wall-clock time in phase_o/${STAMP}/commands.txt).
3. Without leaving the shell, execute part 2 with the same guards:
   ```bash
   timeout 600 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv @reports/2026-01-test-suite-triage/phase_o/chunk_03_selectors_part2.txt -k "not gradcheck" --maxfail=0 --durations=25 --junitxml reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest_part2.xml 2>&1 | tee reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/pytest_part2.log
   ```
4. Aggregate XML totals and record the helper command in commands.txt:
   ```bash
   python - <<'PY'
   import os, xml.etree.ElementTree as ET
   from collections import Counter
   stamp = os.environ['STAMP']
   paths = [
       f'reports/2026-01-test-suite-triage/phase_o/{stamp}/chunks/chunk_03/pytest_part1.xml',
       f'reports/2026-01-test-suite-triage/phase_o/{stamp}/chunks/chunk_03/pytest_part2.xml',
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
5. Copy the prior summary template and update counts + slowest tests:
   ```bash
   cp reports/2026-01-test-suite-triage/phase_o/20251015T030233Z/chunks/chunk_03/summary.md reports/2026-01-test-suite-triage/phase_o/${STAMP}/chunks/chunk_03/summary.md
   ```
   Edit to reflect part1/part2 runtimes and note the lone expected failures (C18 x2, C19 x1) with links to their logs.
6. Refresh `phase_o/${STAMP}/summary.md`, `reports/2026-01-test-suite-triage/remediation_tracker.md`, `docs/fix_plan.md` (mark Next Action 9 done, log Attempt with STAMP + runtimes), and `plans/active/test-suite-triage.md` (mark O5a–O5e [D], O6 pending until tracker sync complete). Move the old stray grad_guard pytest.xml into the new `${STAMP}/gradients/` folder before pruning timeout dirs.
7. Record an Attempts History entry (include both command timings and aggregation snippet) immediately after edits.
Pitfalls To Avoid:
- Do not overwrite chunk_03_selectors.txt; create new part files alongside it.
- Keep `$STAMP` exported in the same shell for both runs and the aggregation step.
- Ensure `NANOBRAGG_DISABLE_COMPILE=1` appears in both pytest invocations; missing it invalidates the gradcheck guard assumption.
- Record `pytest_part*.xml` even if a run times out; missing XML blocks the aggregation snippet.
- Skip editing simulator code — this loop is evidence + ledger only.
- Note xfail counts manually from logs; pytest’s XML may not capture custom xfail fields.
- When updating docs/fix_plan.md, retain historic attempts and append the new entry; do not collapse prior partial runs.
- After copying the summary template, update STAMP references and totals; stale numbers invalidate the tracker refresh.
- Capture exit codes (`printf '%s\n' "$?" > .../exit_code.txt`) if pytest succeeds; the tracker expects the file.
- Use `tee` paths without double slashes; verify directories exist before launching pytest.
Pointers:
- plans/active/test-suite-triage.md:300-337 — Phase O5 split-run checklist + aggregation snippet.
- docs/fix_plan.md:56-71 — Updated Next Actions 9–10 requirements and command template.
- reports/2026-01-test-suite-triage/phase_o/blocked_attempt_73.md — Timeout diagnosis to cite in Attempts.
- docs/development/testing_strategy.md:55-92 — Chunked execution + env guardrails reference.
Next Up: If time remains, draft the C18 tolerance analysis brief using phase_m3/20251015T002610Z evidence.
