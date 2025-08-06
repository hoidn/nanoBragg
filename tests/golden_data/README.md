# Golden Reference Data Generation

This document specifies the exact `nanoBragg.c` commands used to generate the golden reference data files stored in this directory. This ensures that the test suite is reproducible and provides a single source of truth for validation.

**Prerequisites:**
- The `nanoBragg` executable must be compiled from the C code in `golden_suite_generator/`.
- The necessary input files (`P1.hkl`, `A.mat`) must be present in the `golden_suite_generator/` directory.
- All commands should be run from within the `golden_suite_generator/` directory.

---

### 1. `simple_cubic` Test Case

This is the baseline test for a perfect cubic crystal with no mosaicity. It is used in `test_simple_cubic_reproduction`.

**Generated Files:**
- `simple_cubic.bin`
- `simple_cubic.img`

**Command:**
```bash
./nanoBragg -hkl P1.hkl -matrix A.mat \
  -lambda 6.2 \
  -N 5 \
  -default_F 100 \
  -distance 100 \
  -detsize 102.4 \
  -pixel 0.1 \
  -floatfile ../tests/golden_data/simple_cubic.bin \
  -intfile ../tests/golden_data/simple_cubic.img
```

Note: `-detsize 102.4` and `-pixel 0.1` result in a 1024x1024 pixel image.

---

### 2. `simple_cubic_mosaic` Test Case

This test validates the implementation of mosaicity. It is used in `test_simple_cubic_mosaic_reproduction`. The parameters here must match the configuration used in the PyTorch test.

**Generated Files:**
- `simple_cubic_mosaic.bin`
- `simple_cubic_mosaic.img`

**Command:**
```bash
./nanoBragg -hkl P1.hkl -matrix A.mat \
  -lambda 6.2 \
  -N 5 \
  -default_F 100 \
  -distance 100 \
  -detsize 100 \
  -pixel 0.1 \
  -mosaic_spread 1.0 \
  -mosaic_domains 10 \
  -floatfile ../tests/golden_data/simple_cubic_mosaic.bin \
  -intfile ../tests/golden_data/simple_cubic_mosaic.img
```

Note: `-detsize 100` and `-pixel 0.1` result in a 1000x1000 pixel image, matching the test's expectation.

---

### 3. `triclinic_P1` Test Case

This test validates the implementation of general triclinic unit cells. It uses a triclinic cell with parameters (70, 80, 90, 75, 85, 95).

**Generated Files:**
- `triclinic_P1/image.bin`
- `triclinic_P1/trace.log`
- `triclinic_P1/params.json`

**Command:**
```bash
./nanoBragg -misset -89.968546 -31.328953 177.753396 \
  -cell 70 80 90 75 85 95 \
  -default_F 100 \
  -N 5 \
  -lambda 1.0 \
  -detpixels 512 \
  -floatfile tests/golden_data/triclinic_P1/image.bin
```

**Parameters:**
- Unit cell: a=70Å, b=80Å, c=90Å, α=75°, β=85°, γ=95°
- Misset angles: (-89.968546°, -31.328953°, 177.753396°) for reproducible orientation
- Crystal size: 5x5x5 unit cells
- Wavelength: 1.0 Å
- Detector: 512x512 pixels, 100mm distance, 0.1mm pixel size (defaults)
- Structure factors: all reflections set to F=100

Note: The misset angles were generated randomly and saved for reproducibility. To regenerate this data, use the script at `tests/golden_data/triclinic_P1/regenerate_golden.sh`.

---

### 4. `cubic_tilted_detector` Test Case

This test validates the implementation of general detector geometry with rotations and tilts. It uses a cubic cell with a detector that has been rotated and positioned at a twotheta angle.

**Generated Files:**
- `cubic_tilted_detector/image.bin`
- `cubic_tilted_detector/trace.log`
- `cubic_tilted_detector/params.json`
- `cubic_tilted_detector/detector_vectors.txt`

**Command:**
```bash
./nanoBragg -lambda 6.2 \
  -N 5 \
  -cell 100 100 100 90 90 90 \
  -default_F 100 \
  -distance 100 \
  -detsize 102.4 \
  -detpixels 1024 \
  -Xbeam 61.2 -Ybeam 61.2 \
  -detector_rotx 5 -detector_roty 3 -detector_rotz 2 \
  -twotheta 15 \
  -oversample 1 \
  -floatfile tests/golden_data/cubic_tilted_detector/image.bin
```

**Parameters:**
- Unit cell: 100Å cubic cell
- Crystal size: 5x5x5 unit cells
- Wavelength: 6.2 Å
- Detector: 1024x1024 pixels, 100mm distance, 0.1mm pixel size
- Beam center: (61.2, 61.2) mm - offset by 10mm from detector center
- Detector rotations: rotx=5°, roty=3°, rotz=2° applied in that order
- Two-theta angle: 15° - detector swing around the sample
- Structure factors: all reflections set to F=100

To regenerate this data, use the script at `tests/golden_data/cubic_tilted_detector/regenerate_golden.sh`.

---

## Detector Trace Format

When nanoBragg.c is compiled with detector tracing enabled, it outputs the following vectors after all rotations have been applied:

- **DETECTOR_FAST_AXIS**: The unit vector pointing in the fast (x) direction of the detector
- **DETECTOR_SLOW_AXIS**: The unit vector pointing in the slow (y) direction of the detector  
- **DETECTOR_NORMAL_AXIS**: The unit vector normal to the detector plane (pointing from detector to sample)
- **DETECTOR_PIX0_VECTOR**: The 3D position of the first pixel (0,0) in the detector

All vectors are output in high precision (%.15g format) to enable accurate validation of the PyTorch implementation.