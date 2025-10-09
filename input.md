Summary: Regenerate TC-D1/TC-D3 weighted-source parity bundle so VECTOR work can resume.
Mode: Parity
Focus: SOURCE-WEIGHT-001 / Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_src_003.py -v
Artifacts: reports/2025-11-source-weights/phase_e/<STAMP>/{commands.txt,collect.log,pytest.log,py_tc_d1.bin,py_tc_d3.bin,c_tc_d1.bin,c_tc_d3.bin,py_stdout_tc_d1.log,py_stdout_tc_d3.log,c_stdout_tc_d1.log,c_stdout_tc_d3.log,metrics.txt,correlation.txt,sum_ratio.txt,simulator_diagnostics.txt,env.json}
Do Now: [SOURCE-WEIGHT-001] KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_src_003.py -v; STAMP=$(date -u +%Y%m%dT%H%M%SZ) FIXTURE=reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt OUT=reports/2025-11-source-weights/phase_e/$STAMP && mkdir -p "$OUT" && KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -mat reports/2025-11-source-weights/fixtures/A.mat -sourcefile "$FIXTURE" -default_F 100 -hdivsteps 0 -vdivsteps 0 -dispsteps 1 -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -floatfile "$OUT/py_tc_d1.bin" | tee "$OUT/py_stdout_tc_d1.log" && NB_RUN_PARALLEL=1 "$NB_C_BIN" -mat reports/2025-11-source-weights/fixtures/A.mat -sourcefile "$FIXTURE" -default_F 100 -hdivsteps 0 -vdivsteps 0 -dispsteps 1 -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -floatfile "$OUT/c_tc_d1.bin" | tee "$OUT/c_stdout_tc_d1.log" && KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -mat reports/2025-11-source-weights/fixtures/A.mat -default_F 100 -hdivrange 0.5 -hdivsteps 3 -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -floatfile "$OUT/py_tc_d3.bin" | tee "$OUT/py_stdout_tc_d3.log" && NB_RUN_PARALLEL=1 "$NB_C_BIN" -mat reports/2025-11-source-weights/fixtures/A.mat -default_F 100 -hdivrange 0.5 -hdivsteps 3 -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -floatfile "$OUT/c_tc_d3.bin" | tee "$OUT/c_stdout_tc_d3.log"
If Blocked: Capture partial outputs under reports/2025-11-source-weights/phase_e/<STAMP>/attempts/ and log the blocker in docs/fix_plan.md Attempts before exiting.
Priorities & Rationale:
- docs/fix_plan.md:4046 keeps Next Actions centered on TC-D1/TC-D3 parity evidence before downstream plans proceed.
- plans/active/source-weight-normalization.md:67 demands corr ≥0.999 and |sum_ratio−1| ≤1e-3 for both fixtures before Phase E closes.
- plans/active/vectorization.md:24 shows Phase A of VECTOR-TRICUBIC-002 remains blocked pending this bundle.
- docs/development/testing_strategy.md:24 mandates precise pytest selectors and timestamped artifact capture.
- docs/development/c_to_pytorch_config_map.md:19 enforces that CLI -lambda overrides sourcefile wavelengths; parity must reflect that behavior.
How-To Map:
- export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md; export KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1; set `STAMP`/`OUT` as above and append every shell step to `$OUT/commands.txt` (use `... | tee -a "$OUT/commands.txt"`).
- After the main pytest run, execute `pytest --collect-only -q | tee "$OUT/collect.log"` as proof of selector validity.
- Reuse the diagnostic snippet from `reports/2025-11-source-weights/phase_e/20251009T123427Z/commands.txt` (Python block that captures n_sources, phi_steps, mosaic_domains, oversample, steps, fluence). Run it twice—once with the TC-D1 argument list (include `-sourcefile "$FIXTURE" -hdivsteps 0 -vdivsteps 0 -dispsteps 1`) and once with the TC-D3 argument list (`-hdivrange 0.5 -hdivsteps 3`, omit `-sourcefile`). Prefix each block with `case=TC-D1` / `case=TC-D3` before appending to `$OUT/simulator_diagnostics.txt`.
- Compute parity metrics via:
```python
python - <<'PY'
import json, pathlib
import numpy as np
out = pathlib.Path("$OUT")
results = {}
for case in ("tc_d1", "tc_d3"):
    py = np.fromfile(out / f"py_{case}.bin", dtype=np.float32)
    c = np.fromfile(out / f"c_{case}.bin", dtype=np.float32)
    corr = float(np.corrcoef(py, c)[0, 1])
    ratio = float(py.sum() / c.sum())
    results[case] = {"correlation": corr, "sum_ratio": ratio}
with open(out / "metrics.txt", "w") as fh:
    fh.write("\n".join(f"{case} correlation={vals['correlation']:.6f} sum_ratio={vals['sum_ratio']:.6f}" for case, vals in results.items()))
with open(out / "correlation.txt", "w") as fh:
    fh.write("\n".join(f"{case}:{vals['correlation']:.6f}" for case, vals in results.items()))
with open(out / "sum_ratio.txt", "w") as fh:
    fh.write("\n".join(f"{case}:{vals['sum_ratio']:.6f}" for case, vals in results.items()))
print(json.dumps(results, indent=2))
PY
```
- Record environment details: `env | sort > "$OUT/env.txt"` then run:
```python
python - <<'PY'
import json, os, pathlib, torch
out = pathlib.Path("$OUT")
summary = {
    'NB_C_BIN': os.environ.get('NB_C_BIN'),
    'torch_version': torch.__version__,
    'cuda_available': torch.cuda.is_available(),
}
summary.update({k: os.environ[k] for k in ('AUTHORITATIVE_CMDS_DOC','KMP_DUPLICATE_LIB_OK','NB_RUN_PARALLEL') if k in os.environ})
with open(out / 'env.json', 'w') as fh:
    json.dump(summary, fh, indent=2)
PY
```
- Update docs/fix_plan.md `[SOURCE-WEIGHT-001]` Attempts once both fixtures meet thresholds; mirror status flips (Phase E3 done, VECTOR-TRICUBIC-002 Phase A2) and log the unblock in galph_memory.
Pitfalls To Avoid:
- Do not alter fixture geometry or divergence parameters; parity thresholds assume the recorded TC-D1/TC-D3 setup.
- Ensure `$NB_C_BIN` points to `./golden_suite_generator/nanoBragg`; rebuild there if missing instead of switching binaries silently.
- Keep warning output intact—no stderr filtering—so TC-D2 coverage remains trustworthy.
- Use a single STAMP directory for the whole bundle; never mix evidence from multiple timestamps.
- Run everything on CPU (no `.cuda()`); parity gates are calibrated for CPU runs.
- Avoid overwriting prior reports folders; always target the fresh `$OUT` path.
- Log blockers honestly in fix_plan if metrics miss thresholds instead of forcing success.
Pointers:
- docs/fix_plan.md:4046
- plans/active/source-weight-normalization.md:67
- plans/active/vectorization.md:24
- docs/development/testing_strategy.md:24
- reports/2025-11-source-weights/phase_d/20251009T104310Z/commands.txt
Next Up:
- 1. Update docs/architecture/pytorch_design.md sources subsection once parity holds.
- 2. Re-enable VECTOR-GAPS-002 Phase B profiler capture with fresh evidence.
