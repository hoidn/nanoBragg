Summary: Capture the sanitised two-source parity bundle so SOURCE-WEIGHT-001 Phase G can close and unblock vectorization plans.
Mode: Parity
Focus: SOURCE-WEIGHT-001 — Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py::TestSourceWeights, tests/test_cli_scaling.py::TestSourceWeightsDivergence
Artifacts: reports/2025-11-source-weights/phase_g/$STAMP/

Do Now: SOURCE-WEIGHT-001 — NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence
If Blocked: If the sanitised fixture or rebuilt C binary is missing, regenerate `two_sources_nocomments.txt` per Phase G0 and rebuild `golden_suite_generator/nanoBragg`; document commands, stderr, and env in `reports/2025-11-source-weights/phase_g/$STAMP/notes.md` before stopping.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:22-115 keeps VECTOR and PERF initiatives gated until Phase G1–G3 land with fresh metrics.
- docs/fix_plan.md:4047-4175 mandates correlation ≥0.999 and |sum_ratio−1| ≤3e-3 plus a new Attempt referencing `[C-SOURCEFILE-001]`.
- specs/spec-a-core.md:147-165 codifies that CLI `-lambda` overrides sourcefile values and weights are ignored (equal weighting proof point).
- reports/2025-11-source-weights/phase_g/20251009T225052Z/notes.md captures the prior XPASS anomaly we must supersede.
- plans/active/c-sourcefile-comment-parsing.md:1-78 relies on this bundle to anchor the C-only bug documentation.
How-To Map:
- Export env + timestamp: `export NB_C_BIN=./golden_suite_generator/nanoBragg` and `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `mkdir -p reports/2025-11-source-weights/phase_g/$STAMP`.
- Verify fixture checksum: `sha256sum reports/2025-11-source-weights/fixtures/two_sources_nocomments.txt | tee reports/2025-11-source-weights/phase_g/$STAMP/fixture.sha256` (expect f23e1b1e60...).
- Rebuild C binary: `make -C golden_suite_generator clean && make -C golden_suite_generator CFLAGS="-g -O0"`.
- Collect-only proof: `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee reports/2025-11-source-weights/phase_g/$STAMP/collect.log`.
- Run mapped tests (Do Now command) teeing stdout to `reports/.../$STAMP/pytest.log`.
- PyTorch CLI: `KMP_DUPLICATE_LIB_OK=TRUE nanoBragg -sourcefile reports/2025-11-source-weights/fixtures/two_sources_nocomments.txt -lambda 0.9768 -default_F 100 -cell 100 100 100 90 90 90 -distance 100 -detpixels_x 256 -detpixels_y 256 -pixel 0.1 -oversample 1 -phisteps 1 -mosaic_dom 1 -nointerpolate -nonoise -floatfile reports/2025-11-source-weights/phase_g/$STAMP/py_cli.bin > reports/2025-11-source-weights/phase_g/$STAMP/py_stdout.txt`.
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
- Log env + commands in `reports/.../$STAMP/{env.json,commands.txt}`; note anomalies and XPASS/FAIL interpretation in `notes.md`, then update docs/fix_plan.md Attempt referencing `[C-SOURCEFILE-001]`.
Pitfalls To Avoid:
- Never swap back to the commented fixture; always use `two_sources_nocomments.txt`.
- Keep all artifacts inside the new `$STAMP` directory; do not commit `reports/` contents.
- Ensure `NB_C_BIN` resolves to the rebuilt binary before running CLI parity.
- Always set `KMP_DUPLICATE_LIB_OK=TRUE` for pytest and PyTorch CLI.
- Do not widen test scope beyond the mapped selectors this loop.
- Capture metrics before updating the ledger; stop if thresholds are missed and document findings.
- Avoid `.item()` or device shims if debugging scripts are touched.
- Respect Protected Assets: `docs/index.md`, `loop.sh`, `supervisor.sh`, `input.md`.
Pointers:
- plans/active/source-weight-normalization.md:22-115
- docs/fix_plan.md:4047-4175
- specs/spec-a-core.md:147-165
- plans/active/c-sourcefile-comment-parsing.md:1-78
- reports/2025-11-source-weights/phase_g/20251009T225052Z/notes.md
Next Up: Kick off TEST-INDEX-001 Phase A (collect-only inventory + subagent parsing) once the parity bundle and fix_plan update land.
