Summary: Capture a fresh Phase G parity bundle with the sanitised two-source fixture so downstream plans can trust the weighted-source evidence.
Mode: Parity
Focus: SOURCE-WEIGHT-001 — Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py::TestSourceWeights, tests/test_cli_scaling.py::TestSourceWeightsDivergence
Artifacts: reports/2025-11-source-weights/phase_g/<STAMP>/

Do Now: SOURCE-WEIGHT-001 — NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence
If Blocked: If the sanitised fixture is missing or the C binary fails to rebuild, regenerate `two_sources_nocomments.txt` per G0 and document the failure + commands in `reports/2025-11-source-weights/phase_g/<STAMP>/notes.md` before stopping.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:22-65 keeps Phase G gated on a clean CLI bundle; we must finish G1–G3 before Phase H can proceed.
- docs/fix_plan.md:4047-4175 expects a new Attempt with correlation ≥0.999 and |sum_ratio−1| ≤3e-3 plus linkage to `[C-SOURCEFILE-001]`.
- docs/fix_plan.md:3795-3892 shows VECTOR-GAPS and PERF work blocked until this parity evidence exists.
- specs/spec-a-core.md:151-180 defines equal weighting and lambda override behaviour that the bundle must confirm.
- reports/2025-11-source-weights/phase_g/20251009T225052Z/notes.md documents prior anomalies we need to supersede.
How-To Map:
- Rebuild C binary: `make -C golden_suite_generator clean && make -C golden_suite_generator CFLAGS="-g -O0"`.
- Export env + timestamp: `export NB_C_BIN=./golden_suite_generator/nanoBragg` and `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` then `mkdir -p reports/2025-11-source-weights/phase_g/$STAMP`.
- Collect-only check: `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee reports/2025-11-source-weights/phase_g/$STAMP/collect.log`.
- Run mapped tests (Do Now command) and tee stdout to `reports/2025-11-source-weights/phase_g/$STAMP/pytest.log`.
- PyTorch CLI (use sanitised fixture): `KMP_DUPLICATE_LIB_OK=TRUE nanoBragg -sourcefile reports/2025-11-source-weights/fixtures/two_sources_nocomments.txt -lambda 0.9768 -default_F 100 -cell 100 100 100 90 90 90 -distance 100 -detpixels_x 256 -detpixels_y 256 -pixel 0.1 -oversample 1 -phisteps 1 -mosaic_dom 1 -nointerpolate -nonoise -floatfile reports/2025-11-source-weights/phase_g/$STAMP/py_cli.bin > reports/2025-11-source-weights/phase_g/$STAMP/py_stdout.txt`.
- C CLI: `./golden_suite_generator/nanoBragg -sourcefile reports/2025-11-source-weights/fixtures/two_sources_nocomments.txt -lambda 0.9768 -default_F 100 -cell 100 100 100 90 90 90 -distance 100 -detpixels_x 256 -detpixels_y 256 -pixel 0.1 -oversample 1 -phisteps 1 -mosaic_dom 1 -interpolate 0 -nonoise -floatfile reports/2025-11-source-weights/phase_g/$STAMP/c_cli.bin > reports/2025-11-source-weights/phase_g/$STAMP/c_stdout.txt`.
- Metrics: `python - <<'PY'
import json, numpy as np, os
stamp = os.environ['STAMP']
base = f'reports/2025-11-source-weights/phase_g/{stamp}'
c = np.fromfile(f'{base}/c_cli.bin', dtype=np.float32)
py = np.fromfile(f'{base}/py_cli.bin', dtype=np.float32)
corr = float(np.corrcoef(c, py)[0,1])
ratio = float(c.sum() / py.sum())
out = {"c_sum": float(c.sum()), "py_sum": float(py.sum()), "correlation": corr, "sum_ratio": ratio}
with open(f'{base}/metrics.json', 'w') as fh:
    json.dump(out, fh, indent=2)
print(out)
PY`
- Document fixture checksum, env vars, and any anomalies in `reports/2025-11-source-weights/phase_g/$STAMP/notes.md`, then stage `commands.txt` summarising all invocations.
- Update docs/fix_plan.md `[SOURCE-WEIGHT-001]` Attempts with metrics, fixture path, and `[C-SOURCEFILE-001]` reference before handing back.
Pitfalls To Avoid:
- Do not reuse the commented fixture; always point both CLIs at `two_sources_nocomments.txt`.
- Keep runs inside the new STAMP directory so SMV/PGM noise files stay contained.
- Ensure `NB_C_BIN` resolves to the freshly rebuilt binary; rerun `which nanoBragg` only for PyTorch CLI.
- Always set `KMP_DUPLICATE_LIB_OK=TRUE`; missing it can crash PyTorch on import.
- Avoid committing anything under `reports/`; mention paths only.
- Do not touch files listed in docs/index.md (Protected Assets rule).
- Skip `pytest -q` on the whole suite; run only the mapped selectors.
- Don’t delete the existing parity logs—write fresh ones under the new STAMP.
- Confirm correlation and sum ratio thresholds before updating the ledger; otherwise stop and record the failure.
Pointers:
- plans/active/source-weight-normalization.md:22-65 — Phase G checklist and exit criteria.
- docs/fix_plan.md:4047-4175 — Active ledger expectations for SOURCE-WEIGHT-001.
- docs/fix_plan.md:3795-3892 — Downstream blocks that depend on this bundle.
- reports/2025-11-source-weights/phase_g/20251009T225052Z/notes.md — Previous anomaly to replace.
- specs/spec-a-core.md:151-180 — Normative equal-weight wording.
Next Up: Draft Phase H parity reassessment memo once the new bundle passes thresholds.
