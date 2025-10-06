# Scaling Chain Analysis: C vs PyTorch

**Pixel:** (slow=1039, fast=685)

## Key Findings

**First Divergence:** `I_before_scaling`
- C value: 1.480792010454e+15
- PyTorch value: 1.806530429487e+14
- Ratio (Py/C): 1.219976e-01

**Final Intensity Ratio (Py/C):** 1.114e+00

## Full Factor Comparison

| Factor | C Value | PyTorch Value | Ratio (Py/C) | Match? |
|--------|---------|---------------|--------------|--------|
| I_before_scaling | 1.480792e+15 | 1.806530e+14 | 1.219976e-01 | ❌ |
| steps | 1.000000e+01 | 1.000000e+01 | 1.000000e+00 | ✅ |
| r_e_sqr | 7.940792e-30 | 7.940792e-30 | 1.000000e+00 | ✅ |
| fluence_photons_per_m2 | 1.000000e+24 | 1.000000e+24 | 1.000000e+00 | ✅ |
| polar | 9.125758e-01 | 1.000000e+00 | 1.095799e+00 | ❌ |
| omega_pixel | 4.158679e-07 | 4.158604e-07 | 9.999821e-01 | ❌ |
| I_pixel_final | 4.462541e+02 | 4.971766e+02 | 1.114111e+00 | ❌ |

## Artifacts

- C trace: `trace_c_scaling.log`
- PyTorch trace: `trace_py_after.log`
- Analysis script: `analyze_scaling.py`
