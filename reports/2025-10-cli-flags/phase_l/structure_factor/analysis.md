# Structure-Factor Coverage Analysis

**Date:** 2025-10-07T06:29:16.691340Z
**Task:** CLI-FLAGS-003 Phase L3a
**Goal:** Verify structure-factor source for supervisor pixel
**Status:** Evidence complete — C amplitude cannot be reproduced from available HKL data

## Target Reflection

- **Miller index:** h=-7, k=-1, l=-14
- **C reference F_cell:** 190.27
- **Source:** `reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:143-164`

## Data Sources Tested

See `probe.log` for detailed output from:
- `scaled.hkl` (HKL text file)
- Fdump binaries: not tested (files do not exist in this repo)

## Findings

### HKL File Coverage

- **File content:** Single reflection `1 12 3 100.0` (confirmed via `cat scaled.hkl`)
- **Grid shape:** `torch.Size([1, 1, 1])`
- **H range:** [1, 1]
- **K range:** [12, 12]
- **L range:** [3, 3]
- **Target in range:** **NO** — Target reflection `(-7, -1, -14)` is completely outside the HKL grid
- **Retrieved F_cell:** N/A (out of range, would return `default_F=0.0`)
- **Delta from C:** N/A (cannot compare)

### Fdump Coverage

No Fdump binaries were available for testing. The probe was designed to test:
- `golden_suite_generator/Fdump.bin`
- `tmp/Fdump.bin`

Both files are absent from the repository.

## Critical Discovery

**The C implementation must be synthesizing F_cell=190.27 through a mechanism not represented in the minimal `scaled.hkl` file.**

This explains why PyTorch reports `F_cell=0` in the scaling audit trace:
1. Pixel (685,1039) → scattering geometry → Miller index ≈ `(-7, -1, -14)`
2. PyTorch calls `Crystal.get_structure_factor(h=-7, k=-1, l=-14)`
3. The HKL grid only contains `(1, 12, 3)`, so the reflection is out of range
4. PyTorch correctly returns `default_F=0.0`
5. This propagates through the scaling chain → `I_before_scaling=0`

## Hypothesis: C Amplitude Source

The C code likely generates F_cell=190.27 via one of the following mechanisms (listed by probability):

1. **Fdump generation during execution**
   `nanoBragg.c:2333-2490` may synthesize a full Fdump grid at runtime using the `default_F` parameter or sinc interpolation, even when only a minimal HKL file is provided. The supervisor command may write `Fdump.bin` to disk during the C run.

2. **Symmetry expansion**
   C code may expand P1 reflections via symmetry operations (though the spec states "P1 only, no Friedel pairing").

3. **Fallback to sinc evaluation**
   Instead of returning `default_F=0`, C may compute structure factors from atomic positions using a sinc kernel.

4. **External Fdump loading**
   The C binary may silently load a pre-existing `Fdump.bin` from the working directory, bypassing the HKL file entirely.

## Evidence Needed for Phase L3b

To determine the correct ingestion strategy, we need:

1. **C Fdump inspection:**
   - Capture whether the C binary writes `Fdump.bin` during execution
   - If yes, copy it to `reports/.../structure_factor/` and rerun the probe with `--fdump`
   - Compare the Fdump grid ranges against target `(-7, -1, -14)`

2. **C code audit:**
   - Review `nanoBragg.c:2333-2490` (HKL ingestion)
   - Review `nanoBragg.c:2604-3278` (structure-factor lookup during simulation)
   - Identify whether C synthesizes amplitudes procedurally or requires pre-generated Fdump

3. **Command-line flag check:**
   - Verify whether supervisor command includes hidden flags like `-nonorm`, `-nointerpolate`, or `-fdump` that alter structure-factor behavior

## Next Actions (Phase L3b)

Per `plans/active/cli-noise-pix0/plan.md:256`:

1. **Capture C Fdump artifact:**
   ```bash
   # Run supervisor command and check for Fdump.bin output
   cd golden_suite_generator
   ./nanoBragg [supervisor flags] 2>&1 | tee c_run.log
   ls -lh Fdump.bin
   # If exists, copy to reports/2025-10-cli-flags/phase_l/structure_factor/
   ```

2. **Rerun probe with C-generated Fdump:**
   ```bash
   KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/structure_factor/probe.py \
       --pixel 685 1039 \
       --hkl scaled.hkl \
       --fdump golden_suite_generator/Fdump.bin \
       --dtype float64 \
       --device cpu
   ```

3. **Document findings:**
   - Update `analysis.md` with Fdump grid ranges and retrieved amplitude
   - Compare against C reference F_cell=190.27
   - State whether PyTorch ingestion requires Fdump loading, HKL grid expansion, or sinc fallback

4. **Reconcile with plan Phase L3c:**
   Once the structure-factor source is confirmed, proceed with normalization refactor knowing the correct data dependency.
