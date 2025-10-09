Summary: Capture weighted-source parity evidence so we can unblock the vectorization gap.
Mode: Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2025-11-source-weights/phase_a/<STAMP>/fixtures/two_sources.txt
Artifacts: reports/2025-11-source-weights/phase_a/<STAMP>/py/py_stdout.log
Artifacts: reports/2025-11-source-weights/phase_a/<STAMP>/c/c_stdout.log
Artifacts: reports/2025-11-source-weights/phase_a/<STAMP>/summary.md
Artifacts: reports/2025-11-source-weights/phase_a/<STAMP>/env.json
Artifacts: reports/2025-11-source-weights/phase_a/<STAMP>/pytest_collect.log
Do Now: [SOURCE-WEIGHT-001] Correct weighted source normalization — Phase A evidence capture. Build the weighted two-source fixture, run the PyTorch CLI (`python -m nanobrag_torch ...`) and the C binary with the same inputs, store outputs under the timestamped phase_a directory, then summarize the intensity mismatch.
If Blocked: If either CLI run fails, capture the full command and stderr in summary.md, keep the failing artifacts, and stop after logging the attempt in docs/fix_plan.md.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:8 — Phase A must deliver fixture + parity logs before any design work.
- docs/fix_plan.md:3965 — Next action requires Phase A artifacts to unblock VECTOR-GAPS-002 Phase B2.
- docs/fix_plan.md:3412 — Vectorization gap stay blocked until weighted-source correlation exceeds 0.99.
- specs/spec-a-core.md:248 — Final scaling divides by loop steps; evidence ensures weighting changes respect the spec.
- docs/architecture/pytorch_design.md:76 — Broadcast rules assume correct source normalization; parity data will drive any adjustments.
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ); base=reports/2025-11-source-weights/phase_a/$STAMP; mkdir -p "$base"/fixtures "$base"/py "$base"/c
- cat <<'SRC' > "$base"/fixtures/two_sources.txt
# Weighted two-source fixture
# X Y Z weight wavelength(m)
0.0 0.0 10.0 1.0 6.2e-10
0.0 0.0 10.0 0.2 6.2e-10
SRC
- printf "%s\n" "$(date -Is) fixture_created $base/fixtures/two_sources.txt" >> "$base"/commands.txt
- KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python -m nanobrag_torch -mat A.mat -floatfile "$base"/py/py_weight.bin -sourcefile "$base"/fixtures/two_sources.txt -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -nonoise -nointerpolate | tee "$base"/py/py_stdout.log; printf "%s\n%s\n" "$(date -Is) pytorch_cli" "PYTHONPATH=src python -m nanobrag_torch -mat A.mat -floatfile $base/py/py_weight.bin -sourcefile $base/fixtures/two_sources.txt -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -nonoise -nointerpolate" >> "$base"/commands.txt
- NB_C_BIN=${NB_C_BIN:-./golden_suite_generator/nanoBragg}; "$NB_C_BIN" -mat A.mat -floatfile "$base"/c/c_weight.bin -sourcefile "$base"/fixtures/two_sources.txt -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -nonoise -nointerpolate > "$base"/c/c_stdout.log 2>&1; printf "%s\n%s\n" "$(date -Is) c_cli" "${NB_C_BIN} -mat A.mat -floatfile $base/c/c_weight.bin -sourcefile $base/fixtures/two_sources.txt -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -nonoise -nointerpolate" >> "$base"/commands.txt
- python - <<PY
import numpy as np, pathlib, json
base = pathlib.Path("$base")
shape = (256, 256)
py = np.fromfile(base/"py"/"py_weight.bin", dtype='<f4').reshape(shape)
c = np.fromfile(base/"c"/"c_weight.bin", dtype='<f4').reshape(shape)
summary = {
    "py_total": float(py.sum()),
    "c_total": float(c.sum()),
    "ratio_py_over_c": float(py.sum()/c.sum()) if c.sum() else None,
    "py_max": float(py.max()),
    "c_max": float(c.max()),
    "nonzero_py": int((py>0).sum()),
    "nonzero_c": int((c>0).sum())
}
(base/"summary.md").write_text("# Weighted Source Phase A\n\n" + "\n".join(f"- {k}: {v}" for k, v in summary.items()))
(base/"analysis.json").write_text(json.dumps(summary, indent=2))
PY
- python - <<'PY' > "$base"/env.json
import os, json, torch, platform
print(json.dumps({
    "python": platform.python_version(),
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "nb_c_bin": os.environ.get("NB_C_BIN", "./golden_suite_generator/nanoBragg"),
    "git_head": os.popen('git rev-parse HEAD').read().strip()
}, indent=2))
PY
- pytest --collect-only -q | tee "$base"/pytest_collect.log; printf "%s\n" "$(date -Is) pytest_collect" "pytest --collect-only -q" >> "$base"/commands.txt
Pitfalls To Avoid:
- Do not reuse prior fixtures or bins; always write into the new timestamp directory.
- Keep commands.txt in chronological order; missing entries will block supervisor review.
- Leave NB_C_BIN pointing at golden_suite_generator unless you confirm another binary.
- Avoid shrinking detector size unless the run fails; we need 256×256 parity to mirror fix_plan expectations.
- Capture stdout/stderr with tee/redirection; no clipped logs.
- Do not delete existing artifacts under reports/2025-11-source-weights; add new stamps only.
- Stay in evidence-only mode: no production code changes, no benchmark tweaks.
- Ensure summary.md remains ASCII; no fancy formatting.
- Watch for KMP warnings; record them in summary.md rather than suppressing them.
- Skip full pytest runs; collect-only suffices for this loop.
Pointers:
- plans/active/source-weight-normalization.md:8
- docs/fix_plan.md:3963
- docs/fix_plan.md:3412
- specs/spec-a-core.md:248
- docs/architecture/pytorch_design.md:76
- plans/active/vectorization-gap-audit.md:34
Next Up: VECTOR-GAPS-002 Phase B2 hotspot correlation once weighted-source correlation evidence lands.
