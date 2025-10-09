# Trace Review Checklist

## First Divergent Variable + Value
**PRIMARY DIVERGENCE FOUND: Steps normalization count**

- **PyTorch**: `steps = 2` (counts only actual sources from sourcefile)
- **C**: `steps = 4` (counts 2 actual + 2 zero-weight divergence placeholders)
- **Expected impact**: 2× scaling discrepancy in final intensity

## Source Count Lines
- **PyTorch**: "Loaded 2 sources from ..." — counts only actual sources with non-zero entries
- **C**: "created a total of 4 sources" — includes 2 zero-weight divergence placeholders
- **C detail**: "4 sources" confirmed; "-1 divergence steps" indicates divergence handling

## Source Intensity & Fluence
- **PyTorch fluence**: `1.25932017574725e+29` photons/m²
- **C fluence**: `1.25932015286227e+29` photons/m²
- **Fluence match**: ✅ Values agree within numerical precision (~0.002% relative error)

## Intensity Values
- **PyTorch max intensity**: `4.267e+01` at pixel (158, 147)
- **C max intensity**: Not directly visible in trace (would need full C trace analysis)
- **Previous parity data** (Attempt #19): PyTorch max=42.67 vs C max=0.0104 → **~4100× inflation**

## Analysis Notes
1. **Confirmed root cause**: PyTorch counts `steps=2` while C counts `steps=4`
2. **Expected scaling**: The 2× steps discrepancy should cause 2× intensity inflation
3. **Observed scaling**: Previous parity run showed ~47× inflation (TC-D1) and ~120× inflation (TC-D3)
4. **Gap**: 2× steps error explains only part of the ~47-120× divergence
5. **Hypothesis**: Additional scaling factors must be incorrect:
   - Source weighting may still be applied incorrectly
   - Normalization formula may have other errors
   - Zero-weight sources may contribute intensity when they shouldn't

## Key Variables Extracted
- [x] n_sources (PyTorch: 2; C: 4)
- [x] steps normalization value (PyTorch: 2; C: 4) ← **PRIMARY DIVERGENCE**
- [x] fluence calculation (PyTorch: 1.259e+29; C: 1.259e+29) ← Match ✅
- [ ] source_I or beam intensity per-source (need deeper C trace inspection)
- [ ] Final per-source contribution to intensity accumulation
- [ ] Zero-weight source handling in accumulation loop

## Trace Format Notes
- **PyTorch trace format**: Uses `TRACE_PY:` prefix with variable names followed by values
- **C trace format**: Uses `TRACE_C:` prefix with different variable names and formatting
- **Line counts**: Python emits 45 TRACE_PY lines, C emits 72 TRACE_C lines
- **First PyTorch trace line**: `pix0_vector_meters 0.231274664402008 0.0221880003809929 -0.0221880003809929`
- **First C trace line**: `fdet_after_rotz=0 0 1` (detector basis vector)

## Recommendation
1. **Immediate fix required**: Implement zero-weight source placeholder counting in PyTorch simulator
   - Location: `src/nanobrag_torch/simulator.py` steps calculation
   - Rule: Count ALL sources including zero-weight divergence placeholders per C convention
   - Reference: `nanoBragg.c:2700-2720`
2. **After steps fix**: Rerun TC-D1/TC-D3 parity and expect sum_ratio to drop from ~47-120× to ~23-60×
3. **If still inflated**: Additional investigation needed for:
   - Per-source intensity accumulation logic
   - Source weight handling in reduction
   - Zero-weight source contribution to pixel intensity

## Evidence Bundle Complete
All required artifacts captured:
- ✅ `commands.txt` — Reproduction commands
- ✅ `collect.log` — Test collection proof (7 tests for test_at_src_003.py)
- ✅ `pytest_tc_d_collect.log` — CLI scaling tests collection (4 tests)
- ✅ `py_trace.txt` — PyTorch trace for pixel (158, 147)
- ✅ `c_trace.txt` — C trace for pixel (158, 147)
- ✅ `diff.txt` — Automated diff output
- ✅ `env.json` — Environment metadata (torch 2.7.1+cu126, CUDA available)
- ✅ `trace_notes.md` — This analysis document
- ✅ `py_tc_d1.bin` / `c_tc_d1.bin` — Binary outputs for ad-hoc inspection
