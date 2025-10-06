# Phase H3b Implementation Notes

## Objective
Implement BEAM-pivot pix0 override transform to match C-code behavior for `-pix0_vector_mm` flag.

## Attempted Implementation

### Transform Logic (Implemented)
Based on input.md Phase H3b guidance, implemented the following transformation in `src/nanobrag_torch/models/detector.py` (lines 530-563):

1. Subtract beam term: `pix0_delta = pix0_override - distance_corrected * beam_vector`
2. Project onto detector axes:
   - `Fbeam_override = -dot(pix0_delta, fdet)`
   - `Sbeam_override = -dot(pix0_delta, sdet)`
3. Update beam_center_f/s tensors (maintaining differentiability)
4. Apply standard BEAM formula: `pix0 = -Fbeam*fdet - Sbeam*sdet + distance*beam`

### Test Results (Attempt #22)

**Test Command:** `pytest tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot[cpu] -v`

**Inputs (from supervisor command):**
- pix0_override_mm: (-216.336293, 215.205512, -230.200866)
- beam_vector: (0.00051387949, 0.0, -0.99999986)
- distance: 100mm
- convention: CUSTOM (triggered by -beam_vector and -pix0_vector_mm)

**Expected (from C trace):**
```
pix0_vector = (-0.216475836204836, 0.216343050492215, -0.230192414300537) meters
```

**Actual (PyTorch output):**
```
pix0_vector = (5.1387946e-05, 2.1520551e-01, -2.3020089e-01) meters
```

**Delta:** `max_error=2.165272e-01 m` (exceeds 5e-5 m threshold by 4330x)

### Manual Verification

Verified transform math manually:
```python
pix0_override = tensor([-0.2163,  0.2152, -0.2302])
beam_term = distance * beam_norm = tensor([ 5.1388e-05,  0.0000e+00, -1.0000e-01])
pix0_delta = pix0_override - beam_term = tensor([-0.2164,  0.2152, -0.1302])
Fbeam_override = -dot(pix0_delta, fdet) = 0.1302
Sbeam_override = -dot(pix0_delta, sdet) = 0.2152
pix0_computed = -Fbeam*fdet - Sbeam*sdet + distance*beam
              = tensor([ 5.1388e-05,  2.1521e-01, -2.3020e-01])
```

**Conclusion:** Transform IS being applied correctly per the guidance, but produces wrong result.

## Root Cause Hypothesis

The transform derivation in Phase H3b guidance may not match actual C-code behavior. The C code likely handles `-pix0_vector_mm` override differently than the described projection approach.

### Key Observations:
1. X-component mismatch is extreme: `5.14e-05` vs `-0.2165` (factor of ~4200)
2. Y,Z components are much closer (within ~1mm and ~0.008mm respectively)
3. This pattern suggests the transform is fundamentally incorrect, not just a sign/unit issue

## Next Actions

1. **Re-examine C trace generation**: Check if Phase A C trace was generated with correct instrumentation
2. **Alternative hypothesis**: Perhaps C code applies pix0_override more directly, bypassing the projection math
3. **Trace comparison needed**: Generate fresh C and PyTorch traces side-by-side for the supervisor command
4. **Consider simpler approach**: Maybe pix0_override should replace pix0 more directly in CUSTOM/BEAM mode

## Files Modified
- `src/nanobrag_torch/models/detector.py`: Lines 518-564 (BEAM pivot pix0 override logic)
- `tests/test_cli_flags.py`: Lines 473-548 (new regression test)
- `reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json`: Expected C pix0 vector

## Artifacts
- pytest_TestCLIPix0Override_cpu.log: Test failure log
- pix0_expected.json: C reference pix0 vector
- pix0_expected.txt: Raw C trace line
