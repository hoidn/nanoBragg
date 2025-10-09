# Phase N2 TODO - nb-compare Execution

## Prerequisites (completed in N1)
- [x] C float image generated: `c_roi_float.bin` (24 MB, SHA256: 85b66e23...)
- [x] PyTorch float image generated: `py_roi_float.bin` (24 MB, SHA256: dd91f34b...)
- [x] Pytest smoke tests passed (2/2)
- [x] Commands documented in `commands.txt`
- [x] Environment metadata captured

## Next Steps (Phase N2)
- [ ] Run nb-compare with ROI and resampling:
  ```bash
  nb-compare --roi 100 156 100 156 --resample --threshold 0.98 \
    --outdir reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/ \
    -- -mat A.mat -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 \
    -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 \
    -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 \
    -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 \
    -odet_vector -0.000088 0.004914 -0.999988 \
    -sdet_vector -0.005998 -0.999970 -0.004913 \
    -fdet_vector 0.999982 -0.005998 -0.000118 \
    -pix0_vector_mm -216.336293 215.205512 -230.200866 \
    -beam_vector 0.00051387949 0.0 -0.99999986 \
    -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 \
    -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0
  ```

- [ ] Capture metrics (correlation, sum_ratio, RMSE, peak alignment)
- [ ] Save PNG previews and summary.json
- [ ] Verify correlation ≥0.9995, sum_ratio 0.99-1.01 per plan exit criteria
- [ ] Update fix_plan.md with N2 Attempt

## Expected Behavior
Per Option 1 spec compliance (reports/.../option1_spec_compliance/20251009T013046Z/):
- I_before_scaling shows expected -14.6% delta (φ=0 carryover difference)
- All downstream factors (F_cell, F_latt, omega) should match ≤1e-6
- Image correlation should be high (≥0.9995) despite intensity scale difference
