Summary: Land Phase D3 F_latt normalization and document parity evidence so Phase D4 can proceed.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q; NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestFlattSquareMatchesC::test_f_latt_square_matches_c
Artifacts: reports/2026-01-vectorization-parity/phase_d/$STAMP/f_latt_parity.md; reports/2026-01-vectorization-parity/phase_d/$STAMP/py_traces_post_fix/
Do Now: docs/fix_plan.md [VECTOR-PARITY-001] item 8 — KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel 1792 2048 --tag f_latt_post_fix --out-dir reports/2026-01-vectorization-parity/phase_d/$STAMP/py_traces_post_fix/
If Blocked: Capture current TRACE_PY F_latt values and log the mismatch in reports/2026-01-vectorization-parity/phase_d/$STAMP/blockers.md with reproduction commands.
Priorities & Rationale:
- plans/active/vectorization-parity-regression.md:60 — Phase D3 remains [ ] and needs parity evidence before D4/E1 unblock.
- docs/fix_plan.md:52 — Next Actions now gate on producing f_latt_parity.md for H3 before moving to consolidated smoke.
- specs/spec-a-core.md:221 — SQUARE shape requires sincg(π·h, Na)⋯; current TRACE_PY logs violate Na×Nb×Nc scaling.
- docs/development/testing_strategy.md:120 — Parallel validation matrix mandates ROI correlation ≥0.999 after physics fixes.
- reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/c_traces/pixel_1792_2048.log — C-side F_latt reference that the fix must match.
How-To Map:
- Implement fix: adjust src/nanobrag_torch/utils/physics.py (sincg helper + F_latt aggregation) so the lattice factors multiply to Na×Nb×Nc at the Bragg peak; retain broadcasted tensor math, no Python loops.
- Capture traces: export STAMP=$(date -u +%Y%m%dT%H%M%SZ) then run KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel 1792 2048 --tag f_latt_post_fix --out-dir reports/2026-01-vectorization-parity/phase_d/$STAMP/py_traces_post_fix/; reuse the same STAMP for all Phase D3 artifacts.
- Compare parity:
  python - <<'PY'
import os
from decimal import Decimal
from pathlib import Path
stamp = os.environ['STAMP']
c_path = Path('reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/c_traces/pixel_1792_2048.log')
py_path = Path(f'reports/2026-01-vectorization-parity/phase_d/{stamp}/py_traces_post_fix/pixel_1792_2048.log')
keys = ['F_latt_a', 'F_latt_b', 'F_latt_c', 'F_latt']
def grab(path, token):
    for line in path.read_text().splitlines():
        if token in line:
            return Decimal(line.split()[-1])
rows = []
for key in keys:
    c_val = grab(c_path, key)
    py_val = grab(py_path, key)
    rel_err = abs((py_val - c_val) / c_val)
    rows.append((key, c_val, py_val, rel_err))
for key, c_val, py_val, rel_err in rows:
    print(f"{key}: C={c_val:.12e} Py={py_val:.12e} rel_err={rel_err:.3e}")
PY
  Paste the output and command list into reports/2026-01-vectorization-parity/phase_d/$STAMP/f_latt_parity.md with ≤1e-2 tolerance noted.
- ROI guard: KMP_DUPLICATE_LIB_OK=TRUE python scripts/nb_compare.py --resample --roi 1792 2304 1792 2304 --outdir reports/2026-01-vectorization-parity/phase_d/$STAMP/roi_compare/ -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05; confirm corr ≥0.999 and |sum_ratio−1| ≤5e-3.
- Tests: run pytest --collect-only -q first, then NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestFlattSquareMatchesC::test_f_latt_square_matches_c; attach logs to Attempts History.
Pitfalls To Avoid:
- Do not reintroduce scalar loops in sincg; retain full tensor broadcasting.
- Avoid deriving fluence or other values inside trace helper again—reuse configs.
- Keep TRACE_PY schema stable (no renamed keys) so compare scripts continue to work.
- Ensure tensors stay on caller device/dtype; no forced .cpu() allocations.
- Preserve doc references to C-code snippets; do not remove quotes until feature complete.
- Maintain ROI directory structure (`phase_d/$STAMP/...`) with STAMP set before generating artifacts.
- Don’t skip pytest collection; harness health is a hard gate.
- Record relative error thresholds in f_latt_parity.md (≤1e-2) per plan; no vague prose.
- Respect Protected Assets list in docs/index.md (input.md, loop.sh, etc.).
- No full test suite runs; stick to mapped selectors and nb-compare evidence.
Pointers:
- plans/active/vectorization-parity-regression.md:60
- docs/fix_plan.md:52
- specs/spec-a-core.md:221
- reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/c_traces/pixel_1792_2048.log:54
- scripts/debug_pixel_trace.py:370
Next Up: Phase D4 consolidated parity smoke once f_latt parity is verified.
