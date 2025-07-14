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