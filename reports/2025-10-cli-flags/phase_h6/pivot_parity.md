# Phase H6e: Pivot Parity Evidence

**Date:** 2025-10-06
**Purpose:** Document the confirmed mismatch between C and PyTorch detector pivot modes when custom detector vectors are supplied.

## Evidence Summary

### C Implementation Behavior
```
$ grep -i "pivoting" reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0.log
pivoting detector around sample
```

**Result:** C code selects **SAMPLE pivot** for the supervisor command configuration.

### PyTorch Implementation Behavior
```python
PYTHONPATH=src python - <<'PY'
from nanobrag_torch.config import DetectorConfig, DetectorConvention
config = DetectorConfig(
    spixels=2463,
    fpixels=2527,
    pixel_size_mm=0.172,
    distance_mm=231.274660,
    detector_convention=DetectorConvention.CUSTOM,
    beam_center_s=213.907080,
    beam_center_f=217.742295,
    pix0_override_m=(-216.336293/1000, 215.205512/1000, -230.200866/1000),
    custom_fdet_vector=(0.999982, -0.005998, -0.000118),
    custom_sdet_vector=(-0.005998, -0.999970, -0.004913),
    custom_odet_vector=(-0.000088, 0.004914, -0.999988),
    custom_beam_vector=(0.00051387949, 0.0, -0.99999986)
)
print(config.detector_pivot)
PY

Output: DetectorPivot.BEAM
```

**Result:** PyTorch selects **BEAM pivot** for the identical configuration.

## Pivot Mismatch Diagnosis

**Status:** ❌ **PARITY FAILURE**

| Aspect | C Implementation | PyTorch Implementation | Status |
|--------|------------------|------------------------|--------|
| Pivot Mode | SAMPLE | BEAM | ❌ MISMATCH |
| Custom Detector Vectors | Present (4 vectors) | Present (4 vectors) | ✅ Match |
| Pix0 Override | Present (`-pix0_vector_mm`) | Present (`pix0_override_m`) | ✅ Match |
| Convention | CUSTOM | CUSTOM | ✅ Match |

## Root Cause Analysis

### C Code Pivot Selection Logic
According to `nanoBragg.c` and `docs/architecture/detector.md` §5.2:
- When custom detector vectors are provided (`fdet_vector`, `sdet_vector`, `odet_vector`, `beam_vector`), the C code **forces SAMPLE pivot mode**
- This occurs regardless of beam center parameters or distance settings
- The SAMPLE pivot ensures pix0 is computed relative to the sample position, not the beam spot

### PyTorch Current Behavior
`DetectorConfig` pivot selection (as of 2025-10-06):
- Defaults to BEAM pivot for CUSTOM convention
- Does not automatically switch to SAMPLE when custom vectors are present
- Missing the C code's implicit pivot rule for custom geometry

## Impact on Pix0 Calculation

The pivot mismatch directly explains the persistent 1.14 mm pix0 delta documented in Phase H5c:

```
ΔFbeam = −1.136 mm
ΔSbeam = +0.139 mm
```

**Mechanism:**
1. **BEAM pivot** (PyTorch): `pix0 = -Fbeam·fdet - Sbeam·sdet + distance·beam` (after rotations)
2. **SAMPLE pivot** (C): `pix0 = -Fclose·fdet - Sclose·sdet + close_distance·odet`, then rotate pix0 with detector

These formulas produce different pix0 vectors even with identical basis vectors and beam centers, cascading into:
- Different pixel positions → different scattering vectors
- Different h,k,l fractional values → different F_latt
- Different intensities (124,538× ratio documented in Attempt #27)

## Specification References

### specs/spec-a-cli.md
From the detector pivot precedence rules:
> When custom detector basis vectors are provided via `-fdet_vector`, `-sdet_vector`, `-odet_vector`, or `-beam_vector`, the implementation SHALL use SAMPLE pivot mode to ensure geometric consistency with the overridden detector orientation.

### docs/architecture/detector.md §5.2
Pivot determination checklist item #3:
> **Custom geometry override:** If any custom detector vectors are supplied (fdet/sdet/odet/beam), force SAMPLE pivot regardless of other parameters.

## Next Steps (Phase H6f)

**Implementation Required:**
1. Update `DetectorConfig.__post_init__` or `from_cli_args` to detect custom vector presence
2. When **any** of `custom_fdet_vector`, `custom_sdet_vector`, `custom_odet_vector`, `custom_beam_vector`, or `pix0_override_m` are supplied, force `detector_pivot = DetectorPivot.SAMPLE`
3. Add regression test: `tests/test_cli_flags.py::test_custom_vectors_force_sample_pivot`
4. Document the fix in `reports/2025-10-cli-flags/phase_h6/pivot_fix.md`

**Validation Path:**
- Re-run PyTorch trace harness (Phase H6g)
- Require |Δpix0| < 5e-5 m before closing H6
- Verify F_latt components align within 0.5%
- Resume normalization work (Phase K2)

## Conclusion

**Finding:** PyTorch defaults to BEAM pivot while C uses SAMPLE pivot for the supervisor command configuration.

**Confidence:** High (direct trace evidence from both implementations)

**Blocking:** Yes (prevents pix0 parity and cascades into lattice factor mismatch)

**Remediation:** Implement custom-vector-to-SAMPLE-pivot forcing rule in DetectorConfig (Phase H6f)
