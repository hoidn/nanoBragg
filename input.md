Summary: Capture the Phase G parity bundle with the sanitised two-source fixture so downstream plans can rely on weighted-source evidence.
Mode: Parity
Focus: SOURCE-WEIGHT-001 — Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py::TestSourceWeights, tests/test_cli_scaling.py::TestSourceWeightsDivergence
Artifacts: reports/2025-11-source-weights/phase_g/<STAMP>/

Do Now: SOURCE-WEIGHT-001 — NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence
If Blocked: If the sanitised fixture or rebuilt C binary is missing, regenerate `two_sources_nocomments.txt` per Phase G0 and document the failure (commands, stderr, env) in `reports/2025-11-source-weights/phase_g/<STAMP>/notes.md` before stopping.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:22-83 keeps VECTOR and PERF work gated on completing Phase G bundle capture; finish G1–G3 before advancing.
- docs/fix_plan.md:4047-4175 requires metrics ≥0.999 correlation with |sum_ratio−1| ≤3e-3 plus a new Attempt referencing `[C-SOURCEFILE-001]` and the sanitised fixture.
- docs/fix_plan.md:3765-3797 (VECTOR-TRICUBIC-002) and 3795-3892 (VECTOR-GAPS-002) stay blocked until this evidence lands.
- specs/spec-a-core.md:151-180 codifies equal weighting and lambda override behaviour that the bundle must confirm.
- reports/2025-11-source-weights/phase_g/20251009T225052Z/notes.md documents the prior anomaly we must supersede.
How-To Map:
- Rebuild C binary: `make -C golden_suite_generator clean && make -C golden_suite_generator CFLAGS="-g -O0"`.
- Export env + timestamp: `export NB_C_BIN=./golden_suite_generator/nanoBragg` and `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` then `mkdir -p reports/2025-11-source-weights/phase_g/$STAMP`.
- Collect-only check: `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee reports/2025-11-source-weights/phase_g/$STAMP/collect.log`.
- Run mapped tests (Do Now command) and tee stdout to `reports/2025-11-source-weights/phase_g/$STAMP/pytest.log`.
- PyTorch CLI (sanitised fixture): `KMP_DUPLICATE_LIB_OK=TRUE nanoBragg -sourcefile reports/2025-11-source-weights/fixtures/two_sources_nocomments.txt -lambda 0.9768 -default_F 100 -cell 100 100 100 90 90 90 -distance 100 -detpixels_x 256 -detpixels_y 256 -pixel 0.1 -oversample 1 -phisteps 1 -mosaic_dom 1 -nointerpolate -nonoise -floatfile reports/2025-11-source-weights/phase_g/$STAMP/py_cli.bin > reports/2025-11-source-weights/phase_g/$STAMP/py_stdout.txt`.
- C CLI: `./golden_suite_generator/nanoBragg -sourcefile reports/2025-11-source-weights/fixtures/two_sources_nocomments.txt -lambda 0.9768 -default_F 100 -cell 100 100 100 90 90 90 -distance 100 -detpixels_x 256 -detpixels_y 256 -pixel 0.1 -oversample 1 -phisteps 1 -mosaic_dom 1 -interpolate 0 -nonoise -floatfile reports/2025-11-source-weights/phase_g/$STAMP/c_cli.bin > reports/2025-11-source-weights/phase_g/$STAMP/c_stdout.txt`.
- Metrics script:
```python
python - <<'PY'
import json, numpy as np, os
stamp = os.environ['STAMP']
base = f'reports/2025-11-source-weights/phase_g/{stamp}'
c = np.fromfile(f'{base}/c_cli.bin', dtype=np.float32)
py = np.fromfile(f'{base}/py_cli.bin', dtype=np.float32)
out = {
    "c_sum": float(c.sum()),
    "py_sum": float(py.sum()),
    "correlation": float(np.corrcoef(c, py)[0,1]),
    "sum_ratio": float(c.sum() / py.sum())
}
with open(f'{base}/metrics.json', 'w') as fh:
    json.dump(out, fh, indent=2)
print(out)
PY
```
- Document fixture checksum, env vars, and anomalies in `reports/2025-11-source-weights/phase_g/$STAMP/notes.md`; record `commands.txt` summarising every invocation before updating the ledger.
Pitfalls To Avoid:
- Never revert or reuse the commented fixture; always point both CLIs at `two_sources_nocomments.txt`.
- Keep runs inside the new STAMP directory so SMV/PGM noise files stay contained.
- Ensure `NB_C_BIN` points to the rebuilt binary; avoid stale executables.
- Always set `KMP_DUPLICATE_LIB_OK=TRUE` for pytest and CLI commands.
- Do not commit anything under `reports/`; mention paths only.
- Skip full-suite pytest; run only mapped selectors.
- Check correlation and sum-ratio thresholds before logging success; if outside bounds, stop and document findings.
- Respect Protected Assets (docs/index.md, loop.sh, supervisor.sh, input.md).
Pointers:
- plans/active/source-weight-normalization.md:22-83 — Phase G checklist and exit criteria.
- docs/fix_plan.md:4047-4175 — SOURCE-WEIGHT ledger expectations.
- docs/fix_plan.md:3765-3797, 3795-3892 — Dependency gates for vectorization/perf initiatives.
- plans/active/test-suite-index.md — new documentation initiative queued once parity evidence lands (Phase A will need collect-only output).
- specs/spec-a-core.md:151-180 — Normative equal-weight contract.
Next Up: Kick off TEST-INDEX-001 Phase A (collect-only inventory + subagent parsing) after the parity bundle is delivered.
