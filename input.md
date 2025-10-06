Summary: Pin down the first pix0 divergence between C and PyTorch traces so CLI-FLAGS-003 can advance to normalization.
Phase: Evidence
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm (Phase H6c trace analysis)
Branch: main
Mapped tests: none — evidence-only
Artifacts:
- reports/2025-10-cli-flags/phase_h6/analysis.md (new section documenting first divergence, unit diagnosis, corrective hypothesis)
- reports/2025-10-cli-flags/phase_h6/trace_diff.txt (full diff output preserved for audit)
- reports/2025-10-cli-flags/phase_h5/parity_summary.md (H6c findings appended with metrics table update)
- reports/2025-10-cli-flags/phase_h6/py_trace/trace_py_pix0.log (existing trace referenced; leave intact but include checksum in analysis)
- reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0_clean.log (comparison anchor; cite SHA in analysis)
- docs/fix_plan.md (Attempt #38 entry referencing analysis + diff once documentation complete)
Do Now: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm — execute Phase H6c trace diff; `diff -u reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0_clean.log reports/2025-10-cli-flags/phase_h6/py_trace/trace_py_pix0.log > reports/2025-10-cli-flags/phase_h6/trace_diff.txt` (Evidence loop, no pytest)
If Blocked: Re-run PyTorch trace with editable import `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py --pixel 1039 685 > reports/2025-10-cli-flags/phase_h6/py_trace/trace_py_pix0_retry.log` and capture stderr/env snapshots before reattempting the diff.
Priorities & Rationale:
- specs/spec-a-cli.md:12-78 — Confirms SAMPLE pivot precedence when custom detector vectors exist; explains why -pix0_vector_mm is ignored in C so diff must focus on upstream units.
- docs/architecture/detector.md:95-210 — Details pix0 computation sequence (term_fast/term_slow/term_close) we must compare term-by-term; any drift indicates conversion bug.
- docs/development/c_to_pytorch_config_map.md:58-118 — Lists canonical mm→m conversions for Xbeam/Ybeam and Fclose/Sclose; diff already hints PyTorch still logging millimetres.
- reports/2025-10-cli-flags/phase_h6/c_trace/README.md — Baseline instrumentation choices and numeric ground truth required for a defensible analysis.
- reports/2025-10-cli-flags/phase_h5/parity_summary.md — Needs H6c update so downstream work (Phase H5c closure, Phase K2) references the latest diagnosis instead of stale metrics.
- plans/active/cli-noise-pix0/plan.md:130-188 — Defines H6 exit criteria; our documentation must satisfy those checkpoints before Phase H6 can close.
How-To Map:
- Set environment variables explicitly:
- `export PYTHONPATH=src`
- `export KMP_DUPLICATE_LIB_OK=TRUE`
- Confirm traces exist before diffing:
- `ls reports/2025-10-cli-flags/phase_h6/{c_trace,py_trace}`
- Produce the unified diff capturing complete context:
- `diff -u reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0_clean.log reports/2025-10-cli-flags/phase_h6/py_trace/trace_py_pix0.log > reports/2025-10-cli-flags/phase_h6/trace_diff.txt`
- Inspect the first mismatched block to verify units mismatch:
- `sed -n '1,40p' reports/2025-10-cli-flags/phase_h6/trace_diff.txt`
- Draft analysis narrative summarizing the divergence:
- `printf '\n## Phase H6c Findings\n\n' >> reports/2025-10-cli-flags/phase_h6/analysis.md`
- `echo '- First divergence: beam_center_m values differ by 10^3 due to mm vs m logging in TRACE_PY.' >> reports/2025-10-cli-flags/phase_h6/analysis.md`
- Supplement analysis with numeric table:
- `python - <<'PY'
import numpy as np
from pathlib import Path
c_line = 'TRACE_C:beam_center_m'
py_line = 'TRACE_PY:beam_center_m'
c_text = Path('reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0_clean.log').read_text()
py_text = Path('reports/2025-10-cli-flags/phase_h6/py_trace/trace_py_pix0.log').read_text()
print('| Source | Xclose (m) | Yclose (m) |')
print('| --- | --- | --- |')
for label, text in [('C', c_text), ('PyTorch', py_text)]:
    for line in text.splitlines():
        if line.startswith(label.replace('PyTorch','TRACE_PY') if label=='PyTorch' else 'TRACE_C') and 'beam_center_m' in line:
            parts = line.split('=' )[1].split()
            values = [p.split(':')[1] for p in parts]
            print(f"| {label} | {values[0]} | {values[1]} |")
            break
PY >> reports/2025-10-cli-flags/phase_h6/analysis.md`
- Update parity summary with hyperlink to new diff:
- `python - <<'PY'
from pathlib import Path
summary = Path('reports/2025-10-cli-flags/phase_h5/parity_summary.md')
text = summary.read_text()
marker = '### Phase H6 diagnostics'
snippet = '\n- 2025-10-26: Phase H6c first divergence recorded (beam_center_m in mm vs m). See phase_h6/analysis.md and trace_diff.txt.'
if marker in text:
    text = text.replace(marker, marker + snippet)
else:
    text += '\n\n### Phase H6 diagnostics' + snippet
summary.write_text(text)
PY`
- Append Attempt #38 stub after documentation is ready (no earlier):
- `python - <<'PY'
from pathlib import Path
plan = Path('docs/fix_plan.md')
text = plan.read_text()
entry = "  * [2025-10-26] Attempt #38 (ralph) — Result: evidence captured. Documented first divergence in Phase H6c with unit mismatch summary, diff artifact, and parity_summary update."
anchor = "* [2025-10-06] Attempt #37"
if entry not in text:
    text = text.replace(anchor, anchor + '\n' + entry)
plan.write_text(text)
PY`
- Review git status and stage only the documentation artifacts (no code changes expected):
- `git status --short`
- `git add docs/fix_plan.md plans/active/cli-noise-pix0/plan.md reports/2025-10-cli-flags/phase_h6/analysis.md reports/2025-10-cli-flags/phase_h6/trace_diff.txt reports/2025-10-cli-flags/phase_h5/parity_summary.md`
- Leave commit/push for supervisor handoff once evidence verified.
Pitfalls To Avoid:
- Do not run pytest, nb-compare, or any simulation beyond the trace harness during this evidence loop; keep runtime minimal.
- Do not regenerate or delete existing artifacts in phase_h6/c_trace or py_trace; new outputs must sit alongside with clear filenames.
- Do not modify detector geometry code or simulator physics; H6c is diagnostics-only by plan definition.
- Do not forget to set `PYTHONPATH=src`; skipping this loads the stale site-packages wheel and invalidates findings.
- Avoid unit ambiguity in analysis.md; always state "meters" or "millimeters" explicitly when quoting numbers.
- Preserve Protected Assets from docs/index.md; avoid moving input.md, loop.sh, supervisor.sh, or any listed files.
- Do not overwrite trace_diff.txt by reusing the filename without verifying contents; include checksum if rerun.
- Keep diff output complete; truncating context loses the ability to audit subsequent lines (term_fast, term_slow, etc.).
- Avoid editing docs/fix_plan.md until analysis artifacts exist; log Attempt #38 only when evidence is ready.
- Steer clear of branching or merging during the loop; stay on main to match supervisor expectations.
- Maintain device/dtype neutrality in any quick scripts (e.g., the analysis snippet) so it runs regardless of torch availability.
Pointers:
- plans/active/cli-noise-pix0/plan.md:130-188 — Phase H6 tasks, guardrails, and exit expectations.
- docs/fix_plan.md:448-560 — CLI-FLAGS-003 tracker, Next Actions, and Attempt history for context.
- reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0_clean.log — Golden C trace used for comparison (SAMPLE pivot, CUSTOM convention).
- reports/2025-10-cli-flags/phase_h6/py_trace/trace_py_pix0.log — PyTorch trace captured with editable import (Attempt #37 artifact).
- reports/2025-10-cli-flags/phase_h6/c_trace/README.md — Instrumentation notes and unit expectations (cite in analysis).
- reports/2025-10-cli-flags/phase_h5/parity_summary.md — Where H6c findings must be summarized for broader audience.
- docs/architecture/detector.md:95-210 — Detailed pix0 computation flow to cross-check against trace variables.
- docs/development/testing_strategy.md:120-210 — Parallel trace SOP reinforcing the requirement to document first divergence.
- specs/spec-a-cli.md:12-110 — CLI precedence rules ensuring interpretation of pix0 override and beam centers is correct.
- docs/development/c_to_pytorch_config_map.md:58-118 — Measurement conversions that should align once bug fixed.
- reports/2025-10-cli-flags/phase_h5/c_precedence_2025-10-22.md — Prior evidence showing pix0 override is inert with custom vectors; cite to avoid re-litigating precedence.
Next Up: Once H6c documented and Attempt #38 logged, proceed to H6d (update fix_plan via new findings) and then re-run H5c parity traces before resuming Phase K2 scaling work.
