# Phase B Summary: Golden Data Regeneration

**Timestamp:** 2025-10-10T08:51:24Z
**Git SHA:** 0b2fa6d74da8774a007a7bb248965150f5c2ac54
**C Binary:** `./golden_suite_generator/nanoBragg`
**C Binary SHA256:** `889165595bbca5b51278fac465f82062532d7c76e4d974eea914377cbafebf61`

## Datasets Regenerated

All 5 golden datasets have been successfully regenerated with the Phase D5-fixed C binary:

### 1. simple_cubic
- **Command:** `./nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 -distance 100 -detsize 102.4 -pixel 0.1 -floatfile ../tests/golden_data/simple_cubic.bin -intfile ../tests/golden_data/simple_cubic.img`
- **Files:**
  - `simple_cubic.bin` - SHA256: `ecec0d4ddeef51652de4326be03edb4d331c1e5d5f6510d553297ff53ffb5bd4`
  - `simple_cubic.img` - SHA256: `1d8cc1c8ad9859cd8a0443a94171555f4622b74af1ba566ea854aff07e2f516e`
- **Detector:** 1024×1024 pixels, 0.1mm pixel size, 100mm distance
- **Crystal:** 100Å cubic, 5×5×5 cells
- **Beam:** λ=6.2Å

### 2. simple_cubic_mosaic
- **Command:** `./nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 -distance 100 -detsize 100 -pixel 0.1 -mosaic_spread 1.0 -mosaic_domains 10 -floatfile ../tests/golden_data/simple_cubic_mosaic.bin -intfile ../tests/golden_data/simple_cubic_mosaic.img`
- **Files:**
  - `simple_cubic_mosaic.bin` - SHA256: `e1ce259133d6990d1ea356fd58e94f5444b5a2584aeeb1c9aaa02639495c17c9`
  - `simple_cubic_mosaic.img` - SHA256: `0169b5f2ccb36409b1795bcf5d99ce3839c326520f76f47424d56bc0425e7c1d`
- **Detector:** 1000×1000 pixels, 0.1mm pixel size, 100mm distance
- **Crystal:** 100Å cubic, 5×5×5 cells
- **Beam:** λ=6.2Å, 1.0° mosaic spread, 10 domains

### 3. triclinic_P1
- **Command:** `./nanoBragg -misset -89.968546 -31.328953 177.753396 -cell 70 80 90 75 85 95 -default_F 100 -N 5 -lambda 1.0 -detpixels 512 -floatfile ../tests/golden_data/triclinic_P1/image.bin`
- **Files:**
  - `image.bin` - SHA256: `b95f9387f2b2f852358b4749797343981aeb1e9e1854dba8c9a457ab6d708663`
- **Detector:** 512×512 pixels, 0.1mm pixel size, 100mm distance
- **Crystal:** Triclinic (70,80,90Å; 75°,85°,95°), 5×5×5 cells with misset orientation
- **Beam:** λ=1.0Å

### 4. cubic_tilted_detector
- **Command:** `./nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 -distance 100 -detsize 102.4 -detpixels 1024 -Xbeam 61.2 -Ybeam 61.2 -detector_rotx 5 -detector_roty 3 -detector_rotz 2 -twotheta 15 -oversample 1 -floatfile ../tests/golden_data/cubic_tilted_detector/image.bin`
- **Files:**
  - `image.bin` - SHA256: `2837abc0dec85d4d4e6a42cb7f2bc5f40bf45efbf741d75e8336ae708786317e`
- **Detector:** 1024×1024 pixels, 0.1mm pixel size, 100mm distance, rotx=5°, roty=3°, rotz=2°, twotheta=15°
- **Crystal:** 100Å cubic, 5×5×5 cells
- **Beam:** λ=6.2Å, beam center offset (61.2, 61.2)mm

### 5. high_resolution_4096
- **Command:** `./nanoBragg -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05 -floatfile ../tests/golden_data/high_resolution_4096/image.bin`
- **Files:**
  - `image.bin` - SHA256: `2df24451e8cbb5f18e3184e1b8e131a67fae239dea0abe9a4270ba7bef887912`
- **Detector:** 4096×4096 pixels (204.8mm square), 0.05mm pixel size, 500mm distance
- **Crystal:** 100Å cubic, 5×5×5 cells
- **Beam:** λ=0.5Å (high-energy)
- **File Size:** 64MB (16,777,216 floats)

## Physics Changes from Phase D5

All regenerated datasets incorporate the Phase D5 lattice unit fix (commit bc36384c → 0b2fa6d7):
- **Root Cause:** Prior to Phase D5, lattice vectors remained in Angstroms instead of being converted to meters before Miller index calculation
- **Fix:** Applied 1e-10 conversion factor to `rot_a/b/c` in `simulator.py:306-308`
- **Impact:** Miller indices (h,k,l) now have correct dimensionless values, fixing ~32× intensity mismatch
- **Validation:** ROI parity achieved corr=0.999999999, sum_ratio=0.999987 (Phase D5 Attempt #15)

## Artifacts

All command logs, stdout/stderr captures, and SHA256 checksums archived under:
```
reports/2026-01-golden-refresh/phase_b/20251010T085124Z/
├── repo_sha.txt
├── c_binary_checksum.txt
├── simple_cubic/
│   ├── command.log
│   └── checksums.txt
├── simple_cubic_mosaic/
│   ├── command.log
│   └── checksums.txt
├── triclinic_P1/
│   ├── command.log
│   └── checksums.txt
├── cubic_tilted_detector/
│   ├── command.log
│   └── checksums.txt
└── high_resolution_4096/
    ├── command.log
    └── checksums.txt
```

## Next Actions

1. Update `tests/golden_data/README.md` with new provenance metadata
2. Stage regenerated binaries with `git add tests/golden_data/`
3. Proceed to Phase C parity validation (ROI nb-compare + targeted pytest)

## Exit Criteria Status

- ✅ All 5 datasets regenerated with documented commands
- ✅ SHA256 checksums recorded for all files
- ✅ Command logs captured with full stdout/stderr
- ✅ Git SHA and C binary checksum recorded
- ⏳ README.md update pending
- ⏳ Phase C validation pending
