Summary: Capture a clean Py↔C parity bundle for source weights and retire the stale divergence assumption.
Mode: Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: main
Mapped tests:
- tests/test_cli_scaling.py::TestSourceWeights
- tests/test_cli_scaling.py::TestSourceWeightsDivergence
Artifacts: reports/2025-11-source-weights/phase_g/<STAMP>/
Do Now: [SOURCE-WEIGHT-001] Correct weighted source normalization — NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence
If Blocked: Capture gdb backtrace under reports/2025-11-source-weights/phase_g/<STAMP>/c_segfault/ and log the workaround in notes.md before retrying.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:22 — Phase G requires a fresh parity bundle before downstream work can resume.
- docs/fix_plan.md:4046 — Ledger next actions explicitly call for Phase G1–G3 completion with new metrics.
- specs/spec-a-core.md:151 — Spec mandates equal weighting, so the XPASS must be validated and documented.
- reports/2025-11-source-weights/phase_g/20251009T215516Z/notes.md — Existing evidence records the segfault root cause; we must replace it with a successful run.
How-To Map:
- `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `mkdir -p reports/2025-11-source-weights/phase_g/$STAMP && cd reports/2025-11-source-weights/phase_g/$STAMP` before running anything.
- `NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence` then execute the mapped `pytest -v` command above; save logs as `logs/{collect,pytest}.log`.
- `KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -sourcefile ../../phase_a/20251009T071821Z/fixtures/two_sources.txt -lambda 0.9768 -default_F 100 -cell 100 100 100 90 90 90 -distance 100 -detpixels_x 256 -detpixels_y 256 -pixel 0.1 -oversample 1 -phisteps 1 -mosaic_domains 1 -nointerpolate -nonoise -floatfile py_tc_d1.bin`.
- `"$NB_C_BIN" -sourcefile ../../phase_a/20251009T071821Z/fixtures/two_sources.txt -lambda 0.9768 -default_F 100 -cell 100 100 100 90 90 90 -distance 100 -detpixels_x 256 -detpixels_y 256 -pixel 0.1 -oversample 1 -phisteps 1 -mosaic_domains 1 -nointerpolate -nonoise -floatfile c_tc_d3.bin`.
- `python - <<'PY'` block to compute metrics and emit `metrics.json`:
```
import json, numpy as np
from pathlib import Path
py = np.fromfile('py_tc_d1.bin', dtype=np.float32)
c = np.fromfile('c_tc_d3.bin', dtype=np.float32)
py_sum, c_sum = float(py.sum()), float(c.sum())
ratio = float(py_sum / c_sum) if c_sum else float('nan')
corr = float(np.corrcoef(py, c)[0, 1])
Path('metrics.json').write_text(json.dumps({
    'py_sum': py_sum,
    'c_sum': c_sum,
    'sum_ratio': ratio,
    'correlation': corr
}, indent=2))
print(f'correlation={corr:.12f}')
print(f'sum_ratio={ratio:.6f}')
PY
```
- Record environment + command list in `notes.md`, then update `docs/fix_plan.md` Attempts once metrics satisfy thresholds or document deviations.
Pitfalls To Avoid:
- Forgetting `-nointerpolate` on the C CLI (triggers the tricubic segfault).
- Running commands outside the `<STAMP>` directory (scatters outputs across the repo).
- Omitting `NB_C_BIN` or using the frozen root binary without debug symbols.
- Skipping `--collect-only` prior to pytest (violates testing SOP for mapped selectors).
- Committing generated `.bin`/log artifacts; list paths in notes instead.
- Leaving the xfail expectation untouched if parity actually fails—capture numbers first, then escalate.
Pointers:
- plans/active/source-weight-normalization.md:22
- docs/fix_plan.md:4046
- specs/spec-a-core.md:151
- reports/2025-11-source-weights/phase_g/20251009T215516Z/notes.md
Next Up:
- Draft `phase_h/<STAMP>/parity_reassessment.md` once new metrics are archived.
