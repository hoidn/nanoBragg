Summary: Capture C vs PyTorch single-pixel trace for TC-D1 to pinpoint the first parity divergence.
Mode: Parity
Focus: SOURCE-WEIGHT-001 / Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-11-source-weights/phase_e/<STAMP>/trace/{commands.txt,collect.log,pytest_tc_d_collect.log,py_trace.txt,c_trace.txt,diff.txt,env.json}
Do Now: [SOURCE-WEIGHT-001] export KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md; STAMP=$(date -u +%Y%m%dT%H%M%SZ); OUT=reports/2025-11-source-weights/phase_e/$STAMP/trace; mkdir -p "$OUT" && {
  {
    printf '# %s TC-D1 trace parity\n' "$(date -u)";
    printf 'export KMP_DUPLICATE_LIB_OK=TRUE\nexport NB_RUN_PARALLEL=1\nexport NB_C_BIN=%s\n' "$NB_C_BIN";
  } > "$OUT/commands.txt";
  pytest --collect-only -q tests/test_at_src_003.py | tee "$OUT/collect.log";
  NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee "$OUT/pytest_tc_d_collect.log";
  cmd_py=("python" "-m" "nanobrag_torch" -mat A.mat -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -default_F 100 -hdivsteps 0 -vdivsteps 0 -dispsteps 1 -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -trace_pixel 158 147 -floatfile "$OUT/py_tc_d1.bin");
  printf '%s\n' "${cmd_py[@]}" >> "$OUT/commands.txt";
  "${cmd_py[@]}" | tee "$OUT/py_trace.txt";
  cmd_c=("$NB_C_BIN" -mat A.mat -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -default_F 100 -hdivsteps 0 -vdivsteps 0 -dispsteps 1 -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -trace_pixel 158 147 -floatfile "$OUT/c_tc_d1.bin");
  printf '%s\n' "${cmd_c[@]}" >> "$OUT/commands.txt";
  NB_RUN_PARALLEL=1 "${cmd_c[@]}" | tee "$OUT/c_trace.txt";
  python - <<'PY' >>"$OUT/diff.txt"
from pathlib import Path
py_lines = Path("$OUT/py_trace.txt").read_text().splitlines()
c_lines = Path("$OUT/c_trace.txt").read_text().splitlines()
limit = min(len(py_lines), len(c_lines))
for idx in range(limit):
    if py_lines[idx].strip() != c_lines[idx].strip():
        print(f"First divergence at line {idx}:\nPY {py_lines[idx]}\nC  {c_lines[idx]}")
        break
else:
    if len(py_lines) != len(c_lines):
        print(f"No textual mismatch in prefix; lengths differ (py={len(py_lines)}, c={len(c_lines)})")
    else:
        print("No divergence detected")
PY
  python - <<'PY'
import json, os, torch
summary = {
    'STAMP': os.environ.get('STAMP'),
    'NB_C_BIN': os.environ.get('NB_C_BIN'),
    'torch_version': torch.__version__,
    'cuda_available': torch.cuda.is_available(),
    'trace_pixel': [158, 147]
}
with open("$OUT/env.json", 'w') as fh:
    json.dump(summary, fh, indent=2)
PY
}
If Blocked: If either trace command fails, capture stdout/stderr to "$OUT/attempt.log", note the failure in docs/fix_plan.md Attempts, and keep collect-only logs for discovery proof before stopping.
Priorities & Rationale:
- specs/spec-a-core.md:150-162 — authoritative rule that source weights/wavelengths are ignored; trace must confirm where PyTorch diverges from spec vs C.
- docs/fix_plan.md:4046-4070 — Phase E requires parity evidence; locating first trace divergence is prerequisite to close Attempt #22.
- plans/active/source-weight-normalization.md:53-78 — Phase E exit criteria depend on resolving TC-D1/TC-D3 parity; trace will identify missing normalization (zero-weight placeholders, source_I handling).
- golden_suite_generator/nanoBragg.c:2570-2720 — C implementation of source ingestion/steps; use trace logs to verify PyTorch matches this flow.
- src/nanobrag_torch/simulator.py:824-878 — PyTorch steps normalization and multi-source accumulation; targeted pixel trace will highlight discrepancies.
How-To Map:
- Respect slow/fast ordering: pass -trace_pixel 158 147 (slow index first) for both PyTorch and C.
- Use `tee` to capture full stdout from each trace into `$OUT/py_trace.txt` and `$OUT/c_trace.txt` while keeping console visibility.
- Keep floatfiles (`py_tc_d1.bin`, `c_tc_d1.bin`) inside `$OUT`; they stay untracked but allow ad-hoc inspection if needed.
- Append every executed command to `$OUT/commands.txt` before running it for reproducibility.
- Run the inline Python snippet to emit the first divergent line into `$OUT/diff.txt`; inspect this file before updating fix_plan attempts.
Pitfalls To Avoid:
- Do not swap trace_pixel order (C expects slow then fast).
- Don’t commit `$OUT` artifacts; reference paths in fix_plan attempts instead.
- Ensure NB_C_BIN points to the instrumented binary; rebuild if -trace_pixel is missing.
- Keep environment vars identical across PyTorch and C runs (KMP_DUPLICATE_LIB_OK, NB_RUN_PARALLEL).
- Avoid truncating logs; confirm tee completes before running diff script.
- Skip `pytest -v` here; collect-only proofs are sufficient for this evidence loop.
- If trace output is huge, compress after diff but leave raw logs in place for archival.
- Do not edit production code while gathering this evidence.
Pointers:
- docs/fix_plan.md:4046
- plans/active/source-weight-normalization.md:51
- specs/spec-a-core.md:150
- golden_suite_generator/nanoBragg.c:2570
- src/nanobrag_torch/simulator.py:824
Next Up: Once divergence is identified, implement the corresponding normalization fix (placeholder sources/weights) and rerun TC-D1/TC-D3 parity harness.
