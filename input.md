Summary: Finish Phase O6 housekeeping so the 552/3/137 baseline is recorded and old guard artifacts are archived.
Mode: Docs
Focus: [TEST-SUITE-TRIAGE-001] Phase O6 ledger + artifact cleanup
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/commands.txt; reports/2026-01-test-suite-triage/phase_o/archive/; docs/fix_plan.md; reports/2026-01-test-suite-triage/remediation_tracker.md
Do Now: [TEST-SUITE-TRIAGE-001] Phase O6 ledger cleanup — export STAMP=20251015T043128Z, relocate the guard pytest.xml into ${STAMP}/gradients/, archive the timeout bundles, and log every command in reports/2026-01-test-suite-triage/phase_o/${STAMP}/commands.txt (no pytest run required).
If Blocked: If any directory still contains unique evidence you are unsure about, stop, note the path + reason in commands.txt, and ping supervisor before moving or pruning it.
Priorities & Rationale:
- plans/active/test-suite-triage.md:300-316 keeps O6 in [P] until the ledger + artifact cleanup land.
- docs/fix_plan.md:1-60 now points Next Actions at the Phase O6 refresh; we need artifacts aligned before advancing to C18/C19.
- reports/2026-01-test-suite-triage/remediation_tracker.md:1-120 assumes the 552/3/137 baseline; the filesystem must match so future evidence stays consistent.
- reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/summary.md needs to stay authoritative; commands.txt should chronicle every follow-up edit.
How-To Map:
- `export STAMP=20251015T043128Z`
- `printf "\n$(date -u +%FT%TZ) Phase O6 cleanup start\n" >> reports/2026-01-test-suite-triage/phase_o/${STAMP}/commands.txt`
- `mv reports/2026-01-test-suite-triage/phase_o/\$\(date\ -u\ +%Y%m%dT%H%M%SZ\)/grad_guard/pytest.xml reports/2026-01-test-suite-triage/phase_o/${STAMP}/gradients/` (verify destination exists first)
- `mkdir -p reports/2026-01-test-suite-triage/phase_o/archive` then `mv reports/2026-01-test-suite-triage/phase_o/20251015T020729Z reports/2026-01-test-suite-triage/phase_o/archive/` and repeat for `20251015T023954Z`, `20251015T030233Z`, `20251015T034633Z`, `20251015T041005Z` after ensuring summaries are copied.
- Run the aggregation verifier (keep output in commands.txt):
  `python - <<'PY'
import os, xml.etree.ElementTree as ET
stamp = os.environ['STAMP']
paths = [
    f'reports/2026-01-test-suite-triage/phase_o/{stamp}/chunks/chunk_03/pytest_part1.xml',
    f'reports/2026-01-test-suite-triage/phase_o/{stamp}/chunks/chunk_03/pytest_part2.xml',
    f'reports/2026-01-test-suite-triage/phase_o/{stamp}/chunks/chunk_03/pytest_part3a.xml',
    f'reports/2026-01-test-suite-triage/phase_o/{stamp}/chunks/chunk_03/pytest_part3b.xml',
]
passed = failures = errors = skipped = 0
for path in paths:
    suite = ET.parse(path).getroot().find('testsuite')
    passed += int(suite.attrib.get('tests', 0)) - int(suite.attrib.get('failures', 0)) - int(suite.attrib.get('errors', 0)) - int(suite.attrib.get('skipped', 0))
    failures += int(suite.attrib.get('failures', 0))
    errors += int(suite.attrib.get('errors', 0))
    skipped += int(suite.attrib.get('skipped', 0))
print(f"chunk03 passes={passed} failures={failures} errors={errors} skipped={skipped}")
PY`
- `printf "$(date -u +%FT%TZ) Phase O6 cleanup complete\n" >> reports/2026-01-test-suite-triage/phase_o/${STAMP}/commands.txt`
Pitfalls To Avoid:
- Do not delete `phase_o/20251015T043128Z/`; only archive the timeout bundles once their summaries exist elsewhere.
- Keep the stray `commands.txt` updated; every move/rename must be recorded.
- Verify the destination directories before moving files so `mv` does not create unintended names.
- Skip `rm -rf` to avoid losing context; prefer `mv` into `archive/`.
- Preserve timestamps and filenames when moving logs—use plain mv without renaming unless necessary.
- Leave selector manifests untouched; future reruns reuse them.
- No pytest or other commands that mutate the baseline during this loop.
Pointers:
- plans/active/test-suite-triage.md:300-316
- docs/fix_plan.md:1-80
- reports/2026-01-test-suite-triage/remediation_tracker.md:1-160
- reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/summary.md:1
- reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/chunks/chunk_03/summary.md:1
Next Up: 1. Draft `[GRADIENT-FLOW-001]` callchain/plan for `test_gradient_flow_simulation`. 2. Review C18 tolerance thresholds using the 845.68s timing data.
