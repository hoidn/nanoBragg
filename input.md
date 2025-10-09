Summary: Capture Phase G parity bundle with the C CLI forced to `-interpolate 0` so we can retire the stale divergence memo.
Mode: Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: main
Mapped tests:
- tests/test_cli_scaling.py::TestSourceWeights
- tests/test_cli_scaling.py::TestSourceWeightsDivergence
Artifacts: reports/2025-11-source-weights/phase_g/<STAMP>/
Do Now: [SOURCE-WEIGHT-001] Correct weighted source normalization — NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence
If Blocked: If the C CLI crashes even with `-interpolate 0`, capture a `gdb` backtrace to `reports/2025-11-source-weights/phase_g/<STAMP>/c_segfault/backtrace.txt`, note the failing command in `notes.md`, and stop for supervisor review.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:22 — Phase G is still open until we ship a fresh Py↔C evidence bundle with a working C run.
- docs/fix_plan.md:4046 — Next actions require the new bundle to use `-interpolate 0` and to log metrics before advancing to Phase H.
- specs/spec-a-core.md:151 — Spec states that weight and wavelength columns are ignored, so we need updated numbers proving the implementation matches the contract.
- reports/2025-11-source-weights/phase_g/20251009T215516Z/notes.md:75 — Previous run crashed in tricubic interpolation; the updated workflow must document the workaround and gather parity metrics.
How-To Map:
- `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `export OUTDIR="reports/2025-11-source-weights/phase_g/$STAMP"`; `mkdir -p "$OUTDIR"/logs`.
- `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee "$OUTDIR"/logs/collect.log`.
- `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee "$OUTDIR"/logs/pytest.log`.
- `export NB_C_BIN=${NB_C_BIN:-./golden_suite_generator/nanoBragg}` (rebuild beforehand if the binary is stale).
- `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -lambda 0.9768 -default_F 100 -cell 100 100 100 90 90 90 -distance 100 -detpixels_x 256 -detpixels_y 256 -pixel 0.1 -oversample 1 -phisteps 1 -mosaic_domains 1 -interpolate 0 -nonoise -floatfile "$OUTDIR"/py_cli.bin 2>&1 | tee "$OUTDIR"/logs/py_cli.log`.
- `"$NB_C_BIN" -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -lambda 0.9768 -default_F 100 -cell 100 100 100 90 90 90 -distance 100 -detpixels_x 256 -detpixels_y 256 -pixel 0.1 -oversample 1 -phisteps 1 -mosaic_dom 1 -interpolate 0 -nonoise -floatfile "$OUTDIR"/c_cli.bin 2>&1 | tee "$OUTDIR"/logs/c_cli.log`.
- `python - <<'PY'
import json, numpy as np
from pathlib import Path
out = Path("$OUTDIR")
py = np.fromfile(out / "py_cli.bin", dtype=np.float32)
c = np.fromfile(out / "c_cli.bin", dtype=np.float32)
py_sum = float(py.sum())
c_sum = float(c.sum())
ratio = float(py_sum / c_sum) if c_sum else float('nan')
if py.std() == 0 or c.std() == 0:
    corr = float('nan')
else:
    corr = float(np.corrcoef(py, c)[0, 1])
metrics = {
    "py_sum": py_sum,
    "c_sum": c_sum,
    "sum_ratio": ratio,
    "correlation": corr
}
(out / "metrics.json").write_text(json.dumps(metrics, indent=2))
print(f"correlation={corr:.12f}")
print(f"sum_ratio={ratio:.6f}")
PY`.
- Append `notes.md` in `$OUTDIR` summarising commands, environment variables, metrics, and any anomalies; then add a new Attempt under `[SOURCE-WEIGHT-001]` once thresholds are satisfied.
Pitfalls To Avoid:
- Skipping the `--collect-only` step or neglecting to stash the log alongside the pytest run.
- Forgetting `-interpolate 0` on either CLI, which recreates the tricubic segfault.
- Running commands from another directory so outputs land outside `$OUTDIR`.
- Leaving `py_cli.bin`/`c_cli.bin` tracked in git; report paths only.
- Reusing stale binaries or metrics from older STAMPs; rebuild and rerun everything fresh.
- Omitting `KMP_DUPLICATE_LIB_OK=TRUE`, which can crash torch before tests begin.
Pointers:
- plans/active/source-weight-normalization.md:22
- docs/fix_plan.md:4046
- specs/spec-a-core.md:151
- reports/2025-11-source-weights/phase_g/20251009T215516Z/notes.md:75
Next Up: Draft the Phase H parity reassessment memo once a clean bundle is archived.
