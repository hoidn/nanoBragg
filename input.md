Summary: Capture a clean SOURCE-WEIGHT parity bundle that matches the test geometry so we can unblock Phase H.
Mode: Parity
Focus: SOURCE-WEIGHT-001 Phase G (parity evidence refresh)
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py::TestSourceWeights; tests/test_cli_scaling.py::TestSourceWeightsDivergence
Artifacts: reports/2025-11-source-weights/phase_g/<STAMP>/{commands.txt,pytest.log,py_stdout.txt,c_stdout.txt,metrics.json,fixture.sha256}
Do Now: [SOURCE-WEIGHT-001] Phase G2-G3 parity bundle — NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence
If Blocked: Capture the C stdout/stderr (even on segfault) under <STAMP>/c_segfault/, note the failure in notes.md, and halt before updating docs/fix_plan.md.
Priorities & Rationale:
- specs/spec-a-core.md:151-153 — Spec mandates equal source weighting; refreshed evidence must prove PyTorch + C alignment under matching inputs.
- plans/active/source-weight-normalization.md Phase G — Tasks G1–G3 remain open; parity bundle is the gate for Phase H and downstream vectorization work.
- docs/fix_plan.md:4065 — `[SOURCE-WEIGHT-001]` next actions demand a sanitized fixture, parity metrics (corr ≥0.999, |sum_ratio−1| ≤3e-3), and a new Attempt entry.
- reports/2025-11-source-weights/phase_g/20251009T225052Z/notes.md — Previous divergence traced to comment parsing + geometry mismatch; we must remove both variables.
- tests/test_cli_scaling.py:600-665 — Use these arguments verbatim so CLI runs match the test that XPASSed.
How-To Map:
- Export env (run from repo root): `export KMP_DUPLICATE_LIB_OK=TRUE`, `export NB_RUN_PARALLEL=1`, `export NB_C_BIN=./golden_suite_generator/nanoBragg`.
- Create bundle dir: `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `OUT=reports/2025-11-source-weights/phase_g/$STAMP`; `mkdir -p "$OUT"` (do NOT commit reports/ contents).
- Record commands up front: `exec > >(tee "$OUT/commands.txt") 2>&1` or append each command manually after running.
- Fixture (match test geometry, no comments):
  ```bash
  cat <<'SRC' > "$OUT/weighted_sources_testgeom.txt"
  0.0 0.0 -1.0 1.0 1.0e-10
  0.1 0.0 -1.0 0.2 1.0e-10
  SRC
  sha256sum "$OUT/weighted_sources_testgeom.txt" | tee "$OUT/fixture.sha256"
  ```
- Pytest (captures XPASS log):
  ```bash
  NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v \
    tests/test_cli_scaling.py::TestSourceWeights \
    tests/test_cli_scaling.py::TestSourceWeightsDivergence \
    | tee "$OUT/pytest.log"
  ```
  Expect 7 pass + 1 xpass; stop if failures appear.
- PyTorch CLI (match test args, log stdout):
  ```bash
  KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch \
    -cell 100 100 100 90 90 90 \
    -default_F 300 \
    -N 5 \
    -distance 100 \
    -detpixels 128 \
    -pixel 0.1 \
    -lambda 1.0 \
    -oversample 1 \
    -phisteps 1 \
    -mosaic_dom 1 \
    -sourcefile "$OUT/weighted_sources_testgeom.txt" \
    -floatfile "$OUT/py_weighted.bin" \
    > "$OUT/py_stdout.txt" 2>&1
  ```
- C CLI (same args, capture logs):
  ```bash
  "$NB_C_BIN" \
    -cell 100 100 100 90 90 90 \
    -default_F 300 \
    -N 5 \
    -distance 100 \
    -detpixels 128 \
    -pixel 0.1 \
    -lambda 1.0 \
    -oversample 1 \
    -phisteps 1 \
    -mosaic_dom 1 \
    -sourcefile "$OUT/weighted_sources_testgeom.txt" \
    -floatfile "$OUT/c_weighted.bin" \
    > "$OUT/c_stdout.txt" 2>&1
  ```
  If this crashes, move logs to `$OUT/c_segfault/` and follow the Blocked guidance.
- Metrics script (shape 128x128):
  ```bash
  python <<'PY'
  import numpy as np, json
  from pathlib import Path

  out = Path("$OUT")
  shape = (128, 128)
  c = np.fromfile(out / "c_weighted.bin", dtype=np.float32).reshape(shape)
  py = np.fromfile(out / "py_weighted.bin", dtype=np.float32).reshape(shape)

  metrics = {
      "c_sum": float(c.sum()),
      "py_sum": float(py.sum()),
      "sum_ratio": float(py.sum() / c.sum()) if c.sum() else float('inf'),
      "correlation": float(np.corrcoef(c.ravel(), py.ravel())[0, 1]),
      "target_corr": 0.999,
      "target_sum_ratio": 3e-3
  }
  (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
  print(json.dumps(metrics, indent=2))
  PY
  ```
  Confirm `metrics.json` shows corr ≥0.999 and |sum_ratio−1| ≤3e-3.
- Summarise findings in `$OUT/notes.md` (tests run, metrics, fixture hash, anomalies, reference `[C-SOURCEFILE-001]`).
- Update docs/fix_plan.md `[SOURCE-WEIGHT-001]` Attempts with the new <STAMP> path, metrics, and sanitized fixture reference; keep Phase G state consistent with the plan.
Pitfalls To Avoid:
- Do not reintroduce comment lines into the fixture; the C parser bug will resurface.
- Keep CLI arguments identical between PyTorch and C (especially `-lambda`, `-mosaic_dom`, detector size).
- Ensure `NB_C_BIN` points to the rebuilt binary; otherwise pytest skip will mask coverage.
- Do not commit files under `reports/`; reference them only in notes and fix_plan.
- Avoid rerunning full pytest; stay on the mapped selectors to keep runtime reasonable.
- Preserve KMP_DUPLICATE_LIB_OK and NB_RUN_PARALLEL exports for every command (pytest + CLI).
- If correlation falls below threshold, stop and capture traces—do not edit production code.
- When updating docs/fix_plan.md, append a new Attempt instead of rewriting historical entries.
Pointers:
- specs/spec-a-core.md:151-153 — Equal-weight requirement & λ override.
- plans/active/source-weight-normalization.md (Phase G table) — Task definitions and thresholds.
- docs/fix_plan.md:4065-4170 — Active ledger expectations for `[SOURCE-WEIGHT-001]`.
- reports/2025-11-source-weights/fixtures/two_sources_nocomments.txt — Previous sanitized fixture (diff reference).
- tests/test_cli_scaling.py:600-665 — Canonical arguments used by the XPASSing reference test.
Next Up: Draft Phase H parity memo (`reports/2025-11-source-weights/phase_h/<STAMP>/parity_reassessment.md`) once metrics confirm alignment.
