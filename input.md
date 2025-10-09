Summary: Realign SOURCE-WEIGHT tests with the spec-first contract and capture the Phase G evidence bundle.
Mode: Docs+Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence
Artifacts: reports/2025-11-source-weights/phase_g/<STAMP>/{commands.txt,collect.log,pytest.log,tc_d1_cmd.txt,tc_d3_cmd.txt,py_metrics.json,c_metrics.json,correlation.txt,notes.md}
Do Now: Execute [SOURCE-WEIGHT-001] Phase G1 & G2; run KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence and rerun the TC-D1/TC-D3 CLI bundle, archiving commands/metrics under reports/2025-11-source-weights/phase_g/<STAMP>/.
If Blocked: Log partial outputs + blockers in reports/2025-11-source-weights/phase_g/<STAMP>/notes.md, update docs/fix_plan.md Attempts with the obstruction, and stop before changing simulator code.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:52-143 — Phase G tasks are the active gate; design packet defines specific test edits and evidence expectations.
- docs/fix_plan.md:4035-4065 — Next Actions require completing Phase G1–G3 (spec-compliant tests + evidence) before dependent plans can progress.
- specs/spec-a-core.md:140-166 — Normative rule that source weights/wavelength columns are ignored (basis for new assertions).
- docs/architecture/pytorch_design.md:90-155 — Reinforces equal-weight accumulation; tests must enforce this behavior.
- docs/development/testing_strategy.md:1-150 — Authoritative pytest cadence, tolerances, and artifact policy for updated suite.
How-To Map:
- export KMP_DUPLICATE_LIB_OK=TRUE
- STAMP=$(date -u +%Y%m%dT%H%M%SZ); OUT=reports/2025-11-source-weights/phase_g/$STAMP; mkdir -p "$OUT"
- pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee "$OUT"/collect.log
- Update tests/test_cli_scaling.py per Phase G1 design (add spec-compliance tests, remove legacy C-parity checks, tighten warnings, add optional xfail for C divergence); capture rationale in "$OUT"/notes.md
- KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee "$OUT"/pytest.log
- Record PyTorch CLI command in "$OUT"/tc_d1_cmd.txt and rerun it (match fix_plan reproduction), saving float output to "$OUT"/py_float.bin
- Record C CLI command in "$OUT"/tc_d3_cmd.txt and rerun via "$NB_C_BIN", saving float output to "$OUT"/c_float.bin (note: correlation <0.8 expected per C-PARITY-001)
- python - <<'PY'
import json, numpy as np
from pathlib import Path
out = Path("$OUT")
py = np.fromfile(out / "py_float.bin", dtype=np.float32)
stats = {"sum": float(py.sum()), "mean": float(py.mean()), "max": float(py.max()), "nonzero": int((py != 0).sum())}
(out / "py_metrics.json").write_text(json.dumps(stats, indent=2))
PY
- python - <<'PY'
import json, numpy as np
from pathlib import Path
out = Path("$OUT")
c = np.fromfile(out / "c_float.bin", dtype=np.float32)
stats = {"sum": float(c.sum()), "mean": float(c.mean()), "max": float(c.max()), "nonzero": int((c != 0).sum())}
(out / "c_metrics.json").write_text(json.dumps(stats, indent=2))
PY
- python - <<'PY'
import numpy as np
from pathlib import Path
out = Path("$OUT")
py = np.fromfile(out / "py_float.bin", dtype=np.float32)
c = np.fromfile(out / "c_float.bin", dtype=np.float32)
mask = (py != 0) | (c != 0)
if mask.any():
    corr = float(np.corrcoef(py[mask], c[mask])[0, 1])
else:
    corr = float("nan")
(out / "correlation.txt").write_text(f"corr={corr}\n")
PY
- Append every command executed to "$OUT"/commands.txt for traceability (python snippets included)
- Update docs/fix_plan.md Attempts (Phase G3) once artifacts exist, noting spec compliance and expected C divergence
Pitfalls To Avoid:
- Restrict code edits to tests and helper utilities; simulator behavior stays untouched this loop.
- Preserve differentiability guardrails (no `.item()` on tensors in new helpers).
- Ensure pytest selectors are validated with --collect-only before full execution.
- Use the archived fixture two_sources.txt; skip tests if the file is missing rather than inlining new fixtures.
- Store all artifacts under the timestamped phase_g folder; do not commit binaries/logs.
- Call out expected C divergence explicitly in notes.md and fix_plan Attempt.
- Keep NB_C_BIN resolution logic untouched; honor Protected Assets (input.md, docs/index.md, loop.sh).
- Rebase or note conflicts before editing docs/fix_plan.md; do not overwrite existing attempts.
- Sync design decisions with spec_vs_c_decision.md when summarising results.
Pointers:
- plans/active/source-weight-normalization.md:75-143
- reports/2025-11-source-weights/phase_f/20251009T203823Z/test_plan.md
- docs/fix_plan.md:4035-4065
- reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md
- tests/test_cli_scaling.py (SourceWeights sections)
Next Up: Phase G3 — log the Attempt with artifact references and prep notes for Phase H documentation sync.
