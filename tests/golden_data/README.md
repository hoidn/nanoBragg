# Golden Reference Data Generation

This document specifies the exact `nanoBragg.c` commands used to generate the golden reference data files stored in this directory. This ensures that the test suite is reproducible and provides a single source of truth for validation.

**Prerequisites:**
- Prefer the instrumented `nanoBragg` built under `golden_suite_generator/` (recommended for tracing and golden data).
- Alternatively, you may use the frozen reference binary at the repo root `./nanoBragg` for non‑instrumented runs.
- The necessary input files (`P1.hkl`, `A.mat`) must be present in the `golden_suite_generator/` directory when running the canonical commands below.
- All commands shown here assume you run from within the `golden_suite_generator/` directory.

Tip: You can also set `NB_C_BIN` from the repo root and replace `./nanoBragg` with `"$NB_C_BIN"` in the commands below, for example:

```bash
export NB_C_BIN=./golden_suite_generator/nanoBragg
"$NB_C_BIN" -hkl P1.hkl -matrix A.mat -lambda 6.2 -N 5 -default_F 100 \
  -distance 100 -detsize 102.4 -pixel 0.1 -floatfile ../tests/golden_data/simple_cubic.bin
```

---

### 1. `simple_cubic` Test Case

This is the baseline test for a perfect cubic crystal with no mosaicity. It is used in `test_simple_cubic_reproduction`.

**Generated Files:**
- `simple_cubic.bin`
- `simple_cubic.img`

**⚠️ CANONICAL C-CODE COMMAND (COPY-PASTEABLE):**
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

**Key Parameters:**
- **Crystal**: 100Å cubic cell, 5×5×5 unit cells
- **Beam**: λ=6.2Å, structure factor F=100 (uniform)
- **Detector**: 100mm distance, 0.1mm pixels, 102.4mm detector size → **1024×1024 pixels**
- **Beam Center**: Default (center of detector) = 51.2mm from edge
- **Pivot Mode**: Default C-code pivot mode

Note: `-detsize 102.4` and `-pixel 0.1` result in a 1024×1024 pixel image.

**Provenance:**
- Generated: 2025-10-10T08:51:24Z
- Git SHA: 0b2fa6d74da8774a007a7bb248965150f5c2ac54
- C Binary SHA256: 889165595bbca5b51278fac465f82062532d7c76e4d974eea914377cbafebf61
- Dataset SHA256: ecec0d4ddeef51652de4326be03edb4d331c1e5d5f6510d553297ff53ffb5bd4 (simple_cubic.bin), 1d8cc1c8ad9859cd8a0443a94171555f4622b74af1ba566ea854aff07e2f516e (simple_cubic.img)
- Command log: `reports/2026-01-golden-refresh/phase_b/20251010T085124Z/simple_cubic/command.log`

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

**Provenance:**
- Generated: 2025-10-10T08:51:24Z
- Git SHA: 0b2fa6d74da8774a007a7bb248965150f5c2ac54
- C Binary SHA256: 889165595bbca5b51278fac465f82062532d7c76e4d974eea914377cbafebf61
- Dataset SHA256: e1ce259133d6990d1ea356fd58e94f5444b5a2584aeeb1c9aaa02639495c17c9 (simple_cubic_mosaic.bin), 0169b5f2ccb36409b1795bcf5d99ce3839c326520f76f47424d56bc0425e7c1d (simple_cubic_mosaic.img)
- Command log: `reports/2026-01-golden-refresh/phase_b/20251010T085124Z/simple_cubic_mosaic/command.log`

---

### 3. `triclinic_P1` Test Case

This test validates the implementation of general triclinic unit cells. It uses a triclinic cell with parameters (70, 80, 90, 75, 85, 95).

**Generated Files:**
- `triclinic_P1/image.bin`
- `triclinic_P1/trace.log`
- `triclinic_P1/params.json`

**⚠️ CANONICAL C-CODE COMMAND (COPY-PASTEABLE):**
```bash
./nanoBragg -misset -89.968546 -31.328953 177.753396 \
  -cell 70 80 90 75 85 95 \
  -default_F 100 \
  -N 5 \
  -lambda 1.0 \
  -detpixels 512 \
  -floatfile tests/golden_data/triclinic_P1/image.bin
```

**Key Parameters:**
- **Crystal**: Triclinic cell a=70Å, b=80Å, c=90Å, α=75°, β=85°, γ=95°, 5×5×5 unit cells
- **Orientation**: Misset angles (-89.968546°, -31.328953°, 177.753396°) for reproducible orientation
- **Beam**: λ=1.0Å, structure factor F=100 (uniform)
- **Detector**: 100mm distance, 0.1mm pixels, **-detpixels 512** → **512×512 pixels**
- **Beam Center**: Default (center of 512×512 detector) = 25.6mm from edge
- **Pivot Mode**: BEAM pivot ("pivoting detector around direct beam spot")

**⚠️ CRITICAL:** This case uses `-detpixels 512`, NOT `-detsize`. This creates a 512×512 detector with 0.1mm pixels, beam center at 25.6mm.

Note: The misset angles were generated randomly and saved for reproducibility. To regenerate this data, use the script at `tests/golden_data/triclinic_P1/regenerate_golden.sh`.

**Provenance:**
- Generated: 2025-10-10T08:51:24Z
- Git SHA: 0b2fa6d74da8774a007a7bb248965150f5c2ac54
- C Binary SHA256: 889165595bbca5b51278fac465f82062532d7c76e4d974eea914377cbafebf61
- Dataset SHA256: b95f9387f2b2f852358b4749797343981aeb1e9e1854dba8c9a457ab6d708663
- Command log: `reports/2026-01-golden-refresh/phase_b/20251010T085124Z/triclinic_P1/command.log`

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

**Provenance:**
- Generated: 2025-10-10T08:51:24Z
- Git SHA: 0b2fa6d74da8774a007a7bb248965150f5c2ac54
- C Binary SHA256: 889165595bbca5b51278fac465f82062532d7c76e4d974eea914377cbafebf61
- Dataset SHA256: 2837abc0dec85d4d4e6a42cb7f2bc5f40bf45efbf741d75e8336ae708786317e
- Command log: `reports/2026-01-golden-refresh/phase_b/20251010T085124Z/cubic_tilted_detector/command.log`

---

### 5. `high_resolution_4096` Test Case (AT-PARALLEL-012 High-Resolution Variant)

This test validates the high-resolution variant with a 4096×4096 detector, comparing on a 512×512 ROI centered on the beam.

**Generated Files:**
- `high_resolution_4096/image.bin`

**⚠️ CANONICAL C-CODE COMMAND (COPY-PASTEABLE):**
```bash
./nanoBragg -lambda 0.5 \
  -cell 100 100 100 90 90 90 \
  -N 5 \
  -default_F 100 \
  -distance 500 \
  -detpixels 4096 \
  -pixel 0.05 \
  -floatfile tests/golden_data/high_resolution_4096/image.bin
```

**Key Parameters:**
- **Crystal**: 100Å cubic cell, 5×5×5 unit cells
- **Beam**: λ=0.5Å (high-energy photons), structure factor F=100 (uniform)
- **Detector**: 500mm distance, 0.05mm pixels, **4096×4096 pixels** (204.8mm square detector)
- **Beam Center**: Default (center of detector) = 102.4mm from edge
- **ROI**: 512×512 window centered on beam (slice [1792:2304, 1792:2304])
- **Pivot Mode**: Default C-code pivot mode (BEAM)
- **File Size**: 64MB (4096×4096×4 bytes)

**Acceptance Criteria (from spec-a-parallel.md AT-PARALLEL-012):**
- No NaNs/Infs in output
- C vs PyTorch correlation ≥ 0.95 on 512×512 ROI
- Top N=50 peaks in ROI within ≤ 1.0 px

**Provenance:**
- Generated: 2025-10-10T08:51:24Z
- Git SHA: 0b2fa6d74da8774a007a7bb248965150f5c2ac54
- C Binary SHA256: 889165595bbca5b51278fac465f82062532d7c76e4d974eea914377cbafebf61 (`./golden_suite_generator/nanoBragg`)
- Dataset SHA256: 2df24451e8cbb5f18e3184e1b8e131a67fae239dea0abe9a4270ba7bef887912
- Command log: `reports/2026-01-golden-refresh/phase_b/20251010T085124Z/high_resolution_4096/command.log`
- Physics change: Phase D5 lattice unit fix (1e-10 conversion Å→meters for Miller indices, commit bc36384c→0b2fa6d7)

Note: This large test case is used for validating performance and numerical stability at high resolution. The ROI-based comparison keeps validation tractable while still exercising the full simulation.

---

## Detector Trace Format

When nanoBragg.c is compiled with detector tracing enabled, it outputs the following vectors after all rotations have been applied:

- **DETECTOR_FAST_AXIS**: The unit vector pointing in the fast (x) direction of the detector
- **DETECTOR_SLOW_AXIS**: The unit vector pointing in the slow (y) direction of the detector  
- **DETECTOR_NORMAL_AXIS**: The unit vector normal to the detector plane (pointing from detector to sample)
- **DETECTOR_PIX0_VECTOR**: The 3D position of the first pixel (0,0) in the detector

All vectors are output in high precision (%.15g format) to enable accurate validation of the PyTorch implementation.
