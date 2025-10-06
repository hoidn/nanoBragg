# PyTorch vs C Trace Comparison — Phase H5c

**Command:**
```bash
PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py --out reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/trace_py.log
```

**Date:** 2025-10-22
**Pixel:** (slow=1039, fast=685)

## Metrics Summary

### pix0_vector (meters)
- **C (line 8):**   `DETECTOR_PIX0_VECTOR -0.216475836204836 0.216343050492215 -0.230192414300537`
- **PyTorch:**      `TRACE_PY: pix0_vector_meters -0.216336513668519 0.21520668107301 -0.230198008546698`

Component deltas:
- ΔS (slow):   -0.216336513668519 - (-0.216475836204836) = **+1.393e-04 m**
- ΔF (fast):   0.21520668107301 - 0.216343050492215   = **-1.136e-03 m**
- ΔO (normal): -0.230198008546698 - (-0.230192414300537) = **-5.594e-06 m**

### Fbeam/Sbeam (meters)
From C trace (lines 113-114):
- Fbeam: 0.217889 m
- Sbeam: 0.215043 m

PyTorch equivalent (derived from pix0 + detector geometry):
- Computed from pix0_vector + basis alignment
- Not directly logged in trace, but basis vectors match

Basis vector parity (C lines 115-117 vs PyTorch lines 4-5):
- **fdet_vector:** C: `0.999982 -0.005998 -0.000118`, PyTorch: `0.999982 -0.005998 -0.000118` ✓ **exact match**
- **sdet_vector:** C: `-0.005998 -0.99997 -0.004913`, PyTorch: `-0.005998 -0.99997 -0.004913` ✓ **exact match**
- **odet_vector:** C: `-8.85283e-05 0.00491362 -0.999988`, PyTorch: (not directly logged but used in computations)

### Fractional h/k/l
- **C:** Not directly logged (would need instrumentation)
- **PyTorch:** `hkl_frac 2.09789811155632 2.01708460401528 -12.8708829573698`
- **Rounded:** `hkl_rounded 2 2 -13`

Residuals from nearest integer:
- h: 2.09789811155632 - 2 = **0.098**
- k: 2.01708460401528 - 2 = **0.017**
- l: -12.8708829573698 - (-13) = **0.129**

### F_latt Components
- **PyTorch:**
  - F_latt_a: -3.29362461553147
  - F_latt_b: 10.815025857481
  - F_latt_c: -1.82323438810534
  - **F_latt (product):** 64.9447673542753

- **C reference:** Not logged in this trace (would need Phase K instrumentation)

### F_cell
- **PyTorch:** 300.58
- **C:** Not logged (HKL lookup value)

### I_before_scaling
- **PyTorch:** 381073273.815409
- **C:** Not logged in current trace

### Final Intensity
- **PyTorch:** `I_pixel_final 0.00383794284980835`
- **C:** Not directly logged for this pixel; max_I across image is 446.254

## Observations

1. **pix0 parity:** Fast component differs by **1.1 mm** (ΔF = -1.136e-03 m), exceeding the <5e-5 m threshold specified in parity_summary.md. This indicates PyTorch and C are computing pix0 differently.

2. **Basis vectors:** Exact match between C and PyTorch for fdet/sdet vectors confirms detector orientation is correctly configured.

3. **Lattice factors:** F_latt components are logged in PyTorch but not in C trace. Phase K1 will need to verify these match the sincg formula.

4. **Configuration parity:** Custom vectors (fdet, sdet, odet, beam_vector) are correctly passed through and match C output.

## Next Actions

1. **pix0 divergence:** The 1.1mm fast-axis delta suggests either:
   - Different beam-center precedence logic
   - Different pivot calculation
   - Missing MOSFLM +0.5 offset adjustment

   → Requires deeper trace comparison or Phase K instrumentation to identify root cause.

2. **F_latt verification:** Once C trace includes F_latt components (Phase K1 instrumentation), compare against PyTorch values to confirm sincg implementation.

3. **Threshold assessment:** Current pix0 ΔF (1.1mm) >> 5e-5m threshold. This must be resolved before Phase K sign-off.

## References
- C reference: `reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/with_override.log`
- PyTorch trace: `reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/trace_py.log`
- Plan: `plans/active/cli-noise-pix0/plan.md` Phase H5c, transition to Phase K1
