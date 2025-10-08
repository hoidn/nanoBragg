# Phase M4 Normalization Fix — Design Memo

**Date:** 2025-10-22
**Initiative:** CLI-FLAGS-003 Phase M4
**Author:** ralph (loop i=103)
**Objective:** Restore the missing `intensity /= steps` normalization to match nanoBragg.c behavior

## Problem Statement

The PyTorch simulator is missing the critical normalization step that divides accumulated intensity by `steps` before applying physical scaling factors. This causes a systematic 14.6% deficit in `I_before_scaling` relative to the C reference implementation.

**Evidence:**
- `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/metrics.json`
- `first_divergence = "I_before_scaling"`
- C value: 943654.81, PyTorch value: 805473.79 (Δ_rel = -14.643%)

## Normative Contract

### From specs/spec-a-core.md:446

> - I: accumulator for intensity before applying r_e^2 and fluence.

### From specs/spec-a-core.md:576

> - AT-SAM-001 Steps normalization
>   - Setup: sources=1; mosaic_domains=1; oversample=1; phisteps=2 with identical physics across steps
>   - Expectation: Final per-pixel scale SHALL divide by steps=2 so intensity matches the single-step case

### From specs/spec-a-core.md:247-250

```
- Final per-pixel scaling:
    - Define steps = (number of sources) · (number of mosaic domains) · (phisteps) · (oversample^2).
    - After all loops (including all thickness layers and subpixels), compute:
        - S = r_e^2 · fluence · I / steps.
```

## C Reference Implementation

From `golden_suite_generator/nanoBragg.c`, lines 3336-3365:

```c
                        /* end of source loop */
                    }
                    /* end of sub-pixel y loop */
                }
                /* end of sub-pixel x loop */
            }
            /* end of detector thickness loop */

            /* convert pixel intensity into photon units */
            test = r_e_sqr*fluence*I/steps;

            /* do the corrections now, if they haven't been applied already */
            if(! oversample_thick) test *= capture_fraction;
            if(! oversample_polar) test *= polar;
            if(! oversample_omega) test *= omega_pixel;
            floatimage[imgidx] += test;
```

**Key observation:** Line 3358 performs `test = r_e_sqr*fluence*I/steps` BEFORE applying the optional last-value corrections.

## Current PyTorch Implementation

From `src/nanobrag_torch/simulator.py`, lines 1112-1116:

```python
physical_intensity = (
    normalized_intensity
    * self.r_e_sqr
    * self.fluence
)
```

**Problem:** The division by `steps` is completely missing!

## Proposed Fix

### Location
`src/nanobrag_torch/simulator.py`, around line 1112

### Current Code
```python
# Final intensity with all physical constants in meters
# Units: [dimensionless] × [steradians] × [m²] × [photons/m²] × [dimensionless] = [photons·steradians]
physical_intensity = (
    normalized_intensity
    * self.r_e_sqr
    * self.fluence
)
```

### Fixed Code
```python
# Final intensity with all physical constants in meters
# Per spec AT-SAM-001 and nanoBragg.c:3358, divide by steps for normalization
# C-Code Implementation Reference (from nanoBragg.c, lines 3336-3365):
# ```c
#             /* convert pixel intensity into photon units */
#             test = r_e_sqr*fluence*I/steps;
# ```
# Units: [dimensionless] / [dimensionless] × [m²] × [photons/m²] = [photons·m²]
physical_intensity = (
    normalized_intensity
    / steps
    * self.r_e_sqr
    * self.fluence
)
```

### Implementation Notes

1. **Preserve batched operations:** The division by `steps` (a scalar) maintains full vectorization
2. **No device/dtype issues:** `steps` is a Python int/float, so PyTorch will broadcast correctly
3. **Order of operations:** Place division BEFORE multiplication to match C semantics exactly
4. **Docstring requirement:** Include the C code snippet per CLAUDE Rule #11

## Validation Strategy

### Targeted Tests
1. `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py` (CPU)
2. Optional: Same test with `--device cuda` if available

### Trace Comparison
1. Rerun `scripts/validation/compare_scaling_traces.py` with supervisor config
2. Expected result: `first_divergence = None` (all factors within tolerance)
3. Store outputs under `fix_20251008T221702Z/`

### Expected Metrics
- `I_before_scaling` C vs PyTorch: match within ±1e-6 relative tolerance
- All downstream scaling factors unchanged (r_e², fluence already correct)
- Full test suite: no regressions

## References

- **Spec citations:** specs/spec-a-core.md:446, 576, 247-250, 633
- **C reference:** golden_suite_generator/nanoBragg.c:3336-3365
- **Config map:** docs/development/c_to_pytorch_config_map.md:34-56
- **Plan:** plans/active/cli-noise-pix0/plan.md Phase M4a-M4d
- **Evidence baseline:** reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/

## Exit Criteria

1. ✅ Design memo written before code changes (this document)
2. ⏳ Normalization fix implemented with C code docstring
3. ⏳ Targeted tests pass on CPU (and CUDA if available)
4. ⏳ Trace comparison shows `first_divergence = None`
5. ⏳ Full `pytest` suite passes without regressions
6. ⏳ Artifacts captured with commands/env/sha256
