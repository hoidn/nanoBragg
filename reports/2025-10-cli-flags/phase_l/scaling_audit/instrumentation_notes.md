# Phase L2a C-Code Instrumentation Notes

**Date:** 2025-10-17
**Engineer:** Ralph (loop i=61)
**Plan Reference:** `plans/active/cli-noise-pix0/plan.md` Phase L2a
**Task:** Instrument nanoBragg.c scaling chain and capture trace for supervisor command

## Instrumentation Status

**No additional instrumentation needed.** The C code at `golden_suite_generator/nanoBragg.c` already contains comprehensive scaling trace instrumentation at lines 3367-3382.

### Existing Instrumentation (lines 3367-3382)

The following trace outputs are already present when `-trace_pixel` is specified:

```c
/* trace final pixel intensity */
if(fpixel==trace_fpixel && spixel==trace_spixel) {
    printf("TRACE_C: I_before_scaling %.15g\n", I);
    printf("TRACE_C: r_e_meters %.15g\n", sqrt(r_e_sqr));
    printf("TRACE_C: r_e_sqr %.15g\n", r_e_sqr);
    printf("TRACE_C: fluence_photons_per_m2 %.15g\n", fluence);
    printf("TRACE_C: steps %d\n", steps);
    printf("TRACE_C: oversample_thick %d\n", oversample_thick);
    printf("TRACE_C: oversample_polar %d\n", oversample_polar);
    printf("TRACE_C: oversample_omega %d\n", oversample_omega);
    printf("TRACE_C: capture_fraction %.15g\n", capture_fraction);
    printf("TRACE_C: polar %.15g\n", polar);
    printf("TRACE_C: omega_pixel %.15g\n", omega_pixel);
    printf("TRACE_C: cos_2theta %.15g\n", dot_product(incident,diffracted));
    printf("TRACE_C: I_pixel_final %.15g\n", test);
    printf("TRACE_C: floatimage_accumulated %.15g\n", floatimage[imgidx]);
}
```

### Scaling Formula (line 3358)

```c
test = r_e_sqr*fluence*I/steps;
```

### Last-Value Corrections (lines 3361-3363)

```c
if(! oversample_thick) test *= capture_fraction;
if(! oversample_polar) test *= polar;
if(! oversample_omega) test *= omega_pixel;
```

## Traced Pixel

- **Pixel coordinates:** (spixel=685, fpixel=1039)
- **Rationale:** This pixel had the maximum intensity in Phase I parity run (max_I = 446.254)

## Command Line

```bash
./golden_suite_generator/nanoBragg \
  -mat A.mat \
  -floatfile /dev/null \
  -hkl scaled.hkl \
  -nonoise \
  -nointerpolate \
  -oversample 1 \
  -exposure 1 \
  -flux 1e18 \
  -beamsize 1.0 \
  -spindle_axis -1 0 0 \
  -Xbeam 217.742295 \
  -Ybeam 213.907080 \
  -distance 231.274660 \
  -lambda 0.976800 \
  -pixel 0.172 \
  -detpixels_x 2463 \
  -detpixels_y 2527 \
  -odet_vector -0.000088 0.004914 -0.999988 \
  -sdet_vector -0.005998 -0.999970 -0.004913 \
  -fdet_vector 0.999982 -0.005998 -0.000118 \
  -pix0_vector_mm -216.336293 215.205512 -230.200866 \
  -beam_vector 0.00051387949 0.0 -0.99999986 \
  -Na 36 \
  -Nb 47 \
  -Nc 29 \
  -osc 0.1 \
  -phi 0 \
  -phisteps 10 \
  -detector_rotx 0 \
  -detector_roty 0 \
  -detector_rotz 0 \
  -twotheta 0 \
  -trace_pixel 685 1039
```

## Captured Scaling Metrics

From `c_trace_scaling.log`:

| Variable | Value | Units | Notes |
|----------|-------|-------|-------|
| I_before_scaling | 943654.80923755 | photons/steradian | Raw accumulated intensity before normalization |
| r_e_sqr | 7.94079248018965e-30 | m² | Thomson cross section (classical electron radius squared) |
| fluence | 1e+24 | photons/m² | X-ray fluence from flux × exposure / beamsize² |
| steps | 10 | count | sources × mosaic_domains × phisteps × oversample² = 1×1×10×1 |
| capture_fraction | 1 | dimensionless | Detector absorption (no thickness, so =1) |
| polar | 0.91463969894451 | dimensionless | Kahn polarization factor |
| omega_pixel | 4.20412684465831e-07 | steradians | Solid angle subtended by pixel |
| I_pixel_final | 2.88139542684698e-07 | photons | Final scaled intensity after all corrections |

## Scaling Chain Breakdown

1. **Base formula:** `I_pixel_final = r_e_sqr × fluence × I_before_scaling / steps`
2. **Last-value corrections (when oversample_* flags are 0):**
   - `I_pixel_final *= capture_fraction` (if oversample_thick == 0)
   - `I_pixel_final *= polar` (if oversample_polar == 0)
   - `I_pixel_final *= omega_pixel` (if oversample_omega == 0)

3. **Verification:**
   ```
   base = 7.94079248018965e-30 × 1e24 × 943654.80923755 / 10
        = 7.49481917434272e-07

   with corrections:
   final = base × 1.0 × 0.91463969894451 × 4.20412684465831e-07
        ≈ 2.88139542684698e-07 ✓ (matches trace)
   ```

## Source Code Locations

- **Main scaling calculation:** `golden_suite_generator/nanoBragg.c:3358`
- **Last-value corrections:** `golden_suite_generator/nanoBragg.c:3361-3363`
- **Trace output:** `golden_suite_generator/nanoBragg.c:3367-3382`
- **Trace pixel CLI parsing:** `golden_suite_generator/nanoBragg.c:1114-1118`

## Next Actions

- **Phase L2b:** Create PyTorch trace harness that logs the same variables
- **Phase L2c:** Compare C and PyTorch traces to identify first divergence
