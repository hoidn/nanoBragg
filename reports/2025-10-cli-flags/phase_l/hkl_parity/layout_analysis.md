# Fdump Binary Layout Analysis

**Phase:** CLI-FLAGS-003 Phase L1b
**Purpose:** Characterize binary layout discrepancies between HKL text and Fdump cache
**References:**
- specs/spec-a-core.md §Structure Factors & Fdump (line 474)
- golden_suite_generator/nanoBragg.c:2484-2487 (C writer loop)

## Input Files

- **HKL:** `scaled.hkl`
- **Fdump:** `reports/2025-10-cli-flags/phase_l/hkl_parity/Fdump_scaled_20251006181401.bin`

## Grid Dimensions

### HKL Text File
- Bounds: h=[-24, 24], k=[-28, 28], l=[-31, 30]
- Ranges: h_range=49, k_range=57, l_range=62
- Expected grid size: 49 × 57 × 62 = 173,166 voxels
- Populated entries: 64,333

### Fdump Binary Cache
- Bounds (header): h=[-24, 24], k=[-28, 28], l=[-31, 30]
- Ranges: h_range=49, k_range=57, l_range=62
- Nominal grid size: 49 × 57 × 62 = 173,166 voxels
- **C allocated size:** (49+1) × (57+1) × (62+1) = 182,700 voxels
- Entries read (within bounds): 173,166

**⚠️ Off-by-One Allocation:** C allocates `(h_range+1) × (k_range+1) × (l_range+1)` per lines 2427-2437, creating 9,534 padding voxels (76,272 bytes).

## Parity Analysis

- **Total mismatches:** 0
- **Parity ratio:** 100.00%

## Hypotheses

1. **Grid Over-Allocation (Confirmed):** C code allocates `(h_range+1) × (k_range+1) × (l_range+1)` per lines 2427-2437 and writes all entries via loops `for(h0=0; h0<=h_range; h0++)` (line 2484), creating 9,534 padding voxels. These contain zeros from `calloc` and represent indices beyond the HKL bounds.


## Next Actions (Phase L1c)

1. Update `src/nanobrag_torch/io/hkl.py::read_fdump()` to match C layout (h→k→l order with +1 padding).
2. Update `write_fdump()` to replicate C writer loop exactly.
3. Add regression test ensuring `read_hkl_file()` ≡ `read_fdump()` for same input.
4. Re-run parity script (Phase L1d) and verify mismatches → 0.
