Summary: Re-run SOURCE-WEIGHT Phase G evidence with rebuilt C binary and complete artifact capture.
Mode: Docs+Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence
Artifacts: reports/2025-11-source-weights/phase_g/<STAMP>/{collect.log,pytest.log,commands.txt,tc_d1_cmd.txt,tc_d3_cmd.txt,py_metrics.json,c_metrics.json,correlation.txt,notes.md,py_stdout.txt,c_stdout.txt}
Do Now: Execute `[SOURCE-WEIGHT-001]` Phase G2/G3 rerun — rebuild the C binary, run the mapped pytest selector plus TC-D1/TC-D3 CLI commands, capture metrics under a new <STAMP> folder, then log the Attempt in docs/fix_plan.md with observations.
If Blocked: Capture what you can (collect.log, pytest.log, stderr) under the new <STAMP> folder, note the blocker in notes.md and docs/fix_plan.md Attempt (state RESULT=BLOCKED), and stop—do not edit simulator/tests until supervisor follow-up.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:55 — Phase G2 requires a clean evidence bundle with rebuilt C binary and explicit anomaly handling.
- docs/fix_plan.md:4046 — Next Actions reopen Phase G2/G3; dependent plans remain blocked until a valid bundle exists.
- specs/spec-a-core.md:149 — Normative statement that source weights/wavelengths from sourcefile are ignored; metrics must demonstrate PyTorch compliance.
- reports/2025-11-source-weights/phase_f/20251009T203823Z/commands.txt — Authoritative CLI/test commands and tolerance thresholds for the bundle.
- tests/test_cli_scaling.py:591 — `test_c_divergence_reference` must land as XFAIL documenting C bug `C-PARITY-001`.
How-To Map:
- export KMP_DUPLICATE_LIB_OK=TRUE; export NB_RUN_PARALLEL=1; export NB_C_BIN=./golden_suite_generator/nanoBragg.
- make -C golden_suite_generator  # rebuild C binary; fail hard if compilation errors.
- STAMP=$(date -u +%Y%m%dT%H%M%SZ); OUT=reports/2025-11-source-weights/phase_g/$STAMP; mkdir -p "$OUT".
- pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee "$OUT"/collect.log.
- NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee "$OUT"/pytest.log; expect 7 pass, 1 xfail (`test_c_divergence_reference`).
- Record PyTorch CLI command (TC-D1) into "$OUT"/tc_d1_cmd.txt, then run:
  python -m nanobrag_torch -sourcefile reports/2025-11-source-weights/fixtures/two_sources.txt -lambda 0.9768 -default_F 100 -cell 100 100 100 90 90 90 -distance 100 -detpixels 256 -pixel 0.1 -oversample 1 -phisteps 1 -mosaic_dom 1 -floatfile "$OUT/py_tc_d1.bin" > "$OUT/py_stdout.txt" 2>&1
- Record C CLI command (TC-D3) into "$OUT"/tc_d3_cmd.txt, then run:
  "$NB_C_BIN" -sourcefile reports/2025-11-source-weights/fixtures/two_sources.txt -lambda 0.9768 -default_F 100 -cell 100 100 100 90 90 90 -distance 100 -detpixels_x 256 -detpixels_y 256 -pixel 0.1 -oversample 1 -phisteps 1 -mosaic_dom 1 -floatfile "$OUT/c_tc_d3.bin" > "$OUT/c_stdout.txt" 2>&1
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
if not mask.any():
    corr = float('nan')
else:
    corr = float(np.corrcoef(py[mask], c[mask])[0, 1])
(out / "correlation.txt").write_text(f"corr={corr}\n")
PY
- Summarise tolerances, any anomalies (XPASS, missing binary, unexpected correlation) in "$OUT"/notes.md and append every executed command to "$OUT"/commands.txt.
- Update docs/fix_plan.md `[SOURCE-WEIGHT-001]` Attempts with the new STAMP, metrics, pytest outcome, and whether C divergence met expectation; leave Phase G open if correlation ≥0.8 or other blockers persist.
Pitfalls To Avoid:
- Do not proceed if `make -C golden_suite_generator` fails — fix or report before running tests.
- Ensure `-default_F` is present in both CLI commands; missing it re-triggers the "Need -hkl" error.
- Expect `test_c_divergence_reference` to XFAIL; if it XPASSes, document immediately and halt further Phase H work.
- Keep the new reports folder untracked; do not `git add` binaries or logs.
- Leave simulator/tests untouched; this loop is evidence-only.
- Capture stdout/stderr for both CLI runs to aid debugging.
- Preserve existing `unexpected_c_parity` artifact until the new attempt supersedes it — do not delete without supervisor direction.
- Verify `NB_RUN_PARALLEL=1` is set for parity tests so C path executes.
- Reset env vars after the loop if they might impact other tests.
- Resolve any pytest failures before rerunning CLI to avoid stale metrics.
Pointers:
- plans/active/source-weight-normalization.md:55
- docs/fix_plan.md:4046
- specs/spec-a-core.md:149
- reports/2025-11-source-weights/phase_f/20251009T203823Z/commands.txt
- tests/test_cli_scaling.py:591
Next Up: Phase H1 doc updates once the Phase G evidence bundle is accepted.
