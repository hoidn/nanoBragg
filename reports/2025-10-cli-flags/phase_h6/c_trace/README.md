# Phase H6a: C Pix0 Trace Capture

## Objective
Capture detailed trace of pix0 calculation from instrumented C code to enable
line-by-line comparison with PyTorch implementation and identify first divergence.

## Command Executed
```bash
./golden_suite_generator/nanoBragg \
  -mat A.mat \
  -floatfile img.bin \
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
  2>&1 | tee reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0.log
```

## Build Context
- Date: 2025-10-24
- Binary: `golden_suite_generator/nanoBragg`
- Compiler flags: `-O2 -fno-fast-math -ffp-contract=off -DTRACING=1 -fopenmp`
- Built via: `make -C golden_suite_generator clean && make -C golden_suite_generator -j8`

## Git Context
cf0e4d1943ab39f18d1647a013721d1f55f279a1
cf0e4d1 [SYNC i=41] actor=ralph status=running

## Key Observations

### Convention and Pivot Mode
- Convention: CUSTOM (due to explicit detector vectors)
- Pivot: SAMPLE (due to custom vectors overriding any -pix0_vector_mm)
- Angles: all zero (rotx=0, roty=0, rotz=0, twotheta=0)

### Beam Center
- Xclose: 0.211818 m (211.818 mm)
- Yclose: 0.217322 m (217.322 mm)  
- pixel_mm: 0.172 mm

### Critical pix0 Calculation (SAMPLE pivot)
The pix0_vector is calculated BEFORE applying rotations:
```
pix0_before_rotation = term_fast + term_slow + term_close
                     = -Fclose*fdet - Sclose*sdet + close_distance*odet
                     = (-0.217738, 0.001306, 0.000026) 
                       + (0.001283, 0.213901, 0.001051)
                       + (-0.000020, 0.001136, -0.231269)
                     = (-0.216476, 0.216343, -0.230192)
```

### Rotation Application
With zero detector rotations, pix0 remains unchanged:
- pix0_before_rotation: (-0.216476, 0.216343, -0.230192) m
- pix0_after_rotz: (-0.216476, 0.216343, -0.230192) m  
- pix0_after_twotheta: (-0.216476, 0.216343, -0.230192) m

### Basis Vectors
Initial basis vectors (from custom vectors):
- fdet: (0.999982, -0.005998, -0.000118)
- sdet: (-0.005998, -0.999970, -0.004913)
- odet: (-0.000089, 0.004914, -0.999988)

After zero rotations, vectors remain unchanged.

### Distance Calculations
- close_distance: 0.231272 m (231.272 mm)
- ratio: 0.999988
- distance: 0.231275 m (231.275 mm)

## Artifacts
- Full trace: `trace_c_pix0.log`
- Clean TRACE_C lines: `trace_c_pix0_clean.log`
- Environment: `env_snapshot.txt`
- Checksum: `trace_c_pix0.log.sha256`

## Next Steps
Phase H6b: Generate matching PyTorch trace with same variable names/units for
direct comparison to identify first divergence in pix0 calculation.
