Summary: Realign SOURCE-WEIGHT tests with the spec-first contract and capture the Phase G evidence bundle.
Mode: Docs+Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence
Artifacts: reports/2025-11-source-weights/phase_g/<STAMP>/{commands.txt,pytest.log,tc_d1_cmd.txt,tc_d3_cmd.txt,py_metrics.json,c_metrics.json,correlation.txt}
Do Now: Execute [SOURCE-WEIGHT-001] Phase G1 & G2; run KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence and rerun the TC-D1/TC-D3 CLI bundle, archiving commands/metrics under reports/2025-11-source-weights/phase_g/<STAMP>/.
If Blocked: Log partial outputs + blockers in reports/2025-11-source-weights/phase_g/<STAMP>/notes.md, update docs/fix_plan.md Attempts with the obstruction, and stop before changing simulator code.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:11-56 — Phase G is now the active gate; Phase E/F tasks are closed, so evidence must shift to spec-compliance tests.
- docs/fix_plan.md:4035-4053 — Next Actions demand completing Phase G1–G3 before downstream vectorization can resume.
- specs/spec-a-core.md:1-40 — Normative rule that source weights are ignored and CLI -lambda overrides sourcefile columns.
- docs/architecture/pytorch_design.md:80-140 — Reinforces equal-weight accumulation and vectorization constraints that tests must enforce.
- docs/development/testing_strategy.md:1-150 — Authoritative pytest cadence and tolerance policy for the updated suite.
How-To Map:
- export KMP_DUPLICATE_LIB_OK=TRUE
- STAMP=$(date -u +%Y%m%dT%H%M%SZ); OUT=reports/2025-11-source-weights/phase_g/$STAMP; mkdir -p "$OUT"
- pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee "$OUT"/collect.log
- Implement Phase G1 updates in tests/test_cli_scaling.py per test_plan.md (weights ignored, CLI lambda override, expected C divergence marked xfail) and note rationale in "$OUT"/notes.md
- KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee "$OUT"/pytest.log
- Record the PyTorch CLI command used (matching fix_plan reproduction) in "$OUT"/tc_d1_cmd.txt and rerun it, writing outputs to "$OUT"/py_float.bin
- Record the C CLI command in "$OUT"/tc_d3_cmd.txt and rerun it via "$NB_C_BIN", writing outputs to "$OUT"/c_float.bin
- python - <<'PY'
import json, numpy as np
import pathlib
out = pathlib.Path("$OUT")
data = np.fromfile(out / "py_float.bin", dtype=np.float32)
stats = {
    "sum": float(data.sum()),
    "mean": float(data.mean()),
    "max": float(data.max()),
    "nonzero": int((data != 0).sum())
}
with open(out / "py_metrics.json", "w") as fh:
    json.dump(stats, fh, indent=2)
PY
- python - <<'PY'
import json, numpy as np
import pathlib
out = pathlib.Path("$OUT")
data = np.fromfile(out / "c_float.bin", dtype=np.float32)
stats = {
    "sum": float(data.sum()),
    "mean": float(data.mean()),
    "max": float(data.max()),
    "nonzero": int((data != 0).sum())
}
with open(out / "c_metrics.json", "w") as fh:
    json.dump(stats, fh, indent=2)
PY
- python - <<'PY'
import numpy as np
import pathlib
out = pathlib.Path("$OUT")
py = np.fromfile(out / "py_float.bin", dtype=np.float32)
c = np.fromfile(out / "c_float.bin", dtype=np.float32)
mask = (py != 0) | (c != 0)
corr = float(np.corrcoef(py[mask], c[mask])[0, 1]) if mask.any() else float('nan')
with open(out / "correlation.txt", "w") as fh:
    fh.write(f"corr={corr}\n")
PY
- Append all commands executed to "$OUT"/commands.txt for traceability (including python snippets)
- Update docs/fix_plan.md Attempts once artifacts and metrics are ready (Phase G3 will finish in the next loop)
Pitfalls To Avoid:
- Do not touch simulator source logic; limit code edits to tests + supporting helpers per design packet.
- Preserve differentiability guardrails by avoiding `.item()` or tensor detaches in new helper code.
- Keep CLI commands aligned with fix_plan reproduction (no ad-hoc parameter tweaks).
- Store all artifacts under the timestamped phase_g folder; do not commit binaries/logs.
- Label C vs PyTorch metric mismatches as expected per `C-PARITY-001`.
- Maintain device/dtype neutrality in any helper tensors introduced for tests (use torch defaults, no `.cuda()` hard-coding).
- Validate pytest selectors with --collect-only before running the full node.
- Respect Protected Assets (input.md, loop.sh, docs/index.md references) — no deletion or relocation.
- Avoid introducing new fixtures without documenting them in the design packet notes.
- Update docs/fix_plan.md immediately if you need to defer or change scope.
Pointers:
- plans/active/source-weight-normalization.md:52-56
- docs/fix_plan.md:4046-4053
- tests/test_cli_scaling.py (current parity assertions to replace)
- specs/spec-a-core.md:1-40
- docs/development/testing_strategy.md:1-150
Next Up: Phase G3 — log the Attempt with artifact references and prep notes for Phase H documentation sync.
