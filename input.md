Summary: Capture a fresh SOURCE-WEIGHT spec evidence bundle and log the Phase G Attempt.
Mode: Docs+Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence
Artifacts: reports/2025-11-source-weights/phase_g/<STAMP>/{commands.txt,collect.log,pytest.log,tc_d1_cmd.txt,tc_d3_cmd.txt,py_metrics.json,c_metrics.json,correlation.txt,notes.md}
Do Now: Execute `[SOURCE-WEIGHT-001]` Phase G2/G3 — archive a new timestamped spec-compliance bundle with pytest + TC-D1/TC-D3 CLI metrics, then update docs/fix_plan.md Attempts with the results (noting expected C divergence).
If Blocked: Capture partial logs/metrics in the same folder, document blockers in notes.md and the Attempt entry (state "BLOCKED"), and stop before editing simulator/tests.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:15-140 — Phase G2/G3 remain the blocker; tests already landed so only evidence + ledger work remain.
- docs/fix_plan.md:4046-4060 — Next Actions now call for new CLI/pytest artifacts and a fresh Attempt before Phase H.
- specs/spec-a-core.md:140-166 — Normative rule that source weights and wavelengths are ignored; metrics must demonstrate PyTorch compliance.
- tests/test_cli_scaling.py:252 — Spec-first tests already cover the behaviours; this loop validates them via evidence capture.
- reports/2025-11-source-weights/phase_f/20251009T203823Z/test_plan.md — Provides command templates and tolerance targets for the evidence bundle.
How-To Map:
- export KMP_DUPLICATE_LIB_OK=TRUE; export NB_RUN_PARALLEL=1 for the parity/xfail tests.
- STAMP=$(date -u +%Y%m%dT%H%M%SZ); OUT=reports/2025-11-source-weights/phase_g/$STAMP; mkdir -p "$OUT"
- pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee "$OUT"/collect.log
- KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee "$OUT"/pytest.log
- Record the PyTorch CLI command (TC-D1 equivalent) to "$OUT"/tc_d1_cmd.txt then run it, writing the float image to "$OUT/py_tc_d1.bin"; append the exact command to "$OUT"/commands.txt after execution.
- Record the C CLI command (TC-D3 equivalent, using "$NB_C_BIN" or fallback) to "$OUT"/tc_d3_cmd.txt, run it, and write its float output to "$OUT/c_tc_d3.bin"; append the executed command to commands.txt.
- python - <<'PY'
import json, numpy as np
from pathlib import Path
out = Path("$OUT")
py = np.fromfile(out / "py_tc_d1.bin", dtype=np.float32)
stats = {"sum": float(py.sum()), "mean": float(py.mean()), "max": float(py.max()), "nonzero": int((py != 0).sum())}
(out / "py_metrics.json").write_text(json.dumps(stats, indent=2))
PY
- python - <<'PY'
import json, numpy as np
from pathlib import Path
out = Path("$OUT")
c = np.fromfile(out / "c_tc_d3.bin", dtype=np.float32)
stats = {"sum": float(c.sum()), "mean": float(c.mean()), "max": float(c.max()), "nonzero": int((c != 0).sum())}
(out / "c_metrics.json").write_text(json.dumps(stats, indent=2))
PY
- python - <<'PY'
import numpy as np
from pathlib import Path
out = Path("$OUT")
py = np.fromfile(out / "py_tc_d1.bin", dtype=np.float32)
c = np.fromfile(out / "c_tc_d3.bin", dtype=np.float32)
mask = (py != 0) | (c != 0)
if mask.any():
    corr = float(np.corrcoef(py[mask], c[mask])[0, 1])
else:
    corr = float("nan")
(out / "correlation.txt").write_text(f"corr={corr}\n")
PY
- Write "$OUT"/notes.md summarising tolerances hit, expected C divergence (C-PARITY-001), and any anomalies; ensure every command executed is captured in commands.txt (including python snippets).
- Update docs/fix_plan.md `[SOURCE-WEIGHT-001]` Attempts with a new entry referencing the STAMP, pytest outcome, metrics, and expected <0.8 correlation before concluding the loop.
Pitfalls To Avoid:
- Do not modify simulator or tests — this loop is evidence/ledger only.
- Use the repo fixture `reports/2025-11-source-weights/fixtures/two_sources.txt`; skip gracefully if missing.
- Ensure env vars KMP_DUPLICATE_LIB_OK and NB_RUN_PARALLEL stay set for all parity runs.
- Store outputs under the new timestamped folder; do not overwrite the 20251009 artifacts and do not commit binaries.
- Confirm `$NB_C_BIN` resolves before running C; if absent, document in notes.md and stop.
- Capture command text verbatim (include working directory hints if you changed directories) to keep commands.txt reproducible.
- Rebase not required this loop, but if fix_plan.md conflicts arise, resolve carefully without dropping prior Attempts.
Pointers:
- plans/active/source-weight-normalization.md:15
- docs/fix_plan.md:4046
- specs/spec-a-core.md:140
- reports/2025-11-source-weights/phase_f/20251009T203823Z/test_plan.md
- tests/test_cli_scaling.py:252
Next Up: Phase H1 documentation updates once the new Attempt is logged.
