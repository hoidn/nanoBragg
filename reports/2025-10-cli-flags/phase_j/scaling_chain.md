# Scaling Chain Analysis: C vs PyTorch

**Pixel:** (slow=1039, fast=685)

## Key Findings

**First Divergence:** `I_before_scaling`
- C value: 1.480792010454e+15
- PyTorch value: 5.344373483470e+08
- Ratio (Py/C): 3.609132e-07

**Final Intensity Ratio (Py/C):** 1.053e-05

## Full Factor Comparison

| Factor | C Value | PyTorch Value | Ratio (Py/C) | Match? |
|--------|---------|---------------|--------------|--------|
| I_before_scaling | 1.480792e+15 | 5.344373e+08 | 3.609132e-07 | ❌ |
| steps | 1.000000e+01 | 1.000000e+01 | 1.000000e+00 | ✅ |
| r_e_sqr | 7.940792e-30 | 7.940792e-30 | 1.000000e+00 | ✅ |
| fluence_photons_per_m2 | 1.000000e+24 | 1.000000e+24 | 1.000000e+00 | ✅ |
| polar | 9.125758e-01 | 1.000000e+00 | 1.095799e+00 | ❌ |
| omega_pixel | 4.158679e-07 | 4.166786e-07 | 1.001950e+00 | ❌ |
| I_pixel_final | 4.462541e+02 | 4.701254e-03 | 1.053493e-05 | ❌ |

## Artifacts

- C trace: `trace_c_scaling.log`
- PyTorch trace: `trace_py_scaling.log`
- Analysis script: `analyze_scaling.py`
