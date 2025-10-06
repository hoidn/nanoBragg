# Phase H3b1: pix0_vector_mm Override Mapping Analysis

**Date:** 2025-10-06
**Task:** CLI-FLAGS-003 Phase H3b1
**Goal:** Capture C vs PyTorch detector geometry values with and without `-pix0_vector_mm` override to determine the actual mapping behavior.

## Executive Summary

**CRITICAL FINDING:** The C code produces IDENTICAL detector geometry whether `-pix0_vector_mm` is present or not when custom detector vectors (`-odet_vector`, `-sdet_vector`, `-fdet_vector`) are already provided. This suggests the custom vectors already encode the pix0 position, making the `-pix0_vector_mm` flag redundant or overridden by the custom vector specification.

## C Trace Results

### WITH `-pix0_vector_mm -216.336293 215.205512 -230.200866`

```
DETECTOR_PIX0_VECTOR -0.216475836204836 0.216343050492215 -0.230192414300537
Xbeam=0.217742 Ybeam=0.213907
Fbeam=0.217889 Sbeam=0.215043
Xclose=0.211818 Yclose=0.217322
Fclose=0.217742 Sclose=0.213907
distance=0.231275
```

### WITHOUT `-pix0_vector_mm`

```
DETECTOR_PIX0_VECTOR -0.216475836204836 0.216343050492215 -0.230192414300537
Xbeam=0.217742 Ybeam=0.213907
Fbeam=0.217889 Sbeam=0.215043
Xclose=0.211818 Yclose=0.217322
Fclose=0.217742 Sclose=0.213907
distance=0.231275
```

**Result:** **IDENTICAL VALUES** - The C code geometry is completely unchanged.

## PyTorch Trace Results

### WITH `pix0_override_m=(-0.216336293, 0.215205512, -0.230200866)`

```
pix0_vector_meters: -0.216336398425502 0.215205633669455 -0.230198013703504
close_distance_meters: 0.231271809414253
```

### WITHOUT `pix0_override_m` (None)

```
pix0_vector_meters: -0.216336513668519 0.21520668107301 -0.230198008546698
close_distance_meters: 0.231271809414591
```

**Delta (WITH override - WITHOUT override):**
- pix0_vector_meters:
  - X: 1.15243017e-07 m  (0.115 µm)
  - Y: -4.74034560e-07 m  (0.474 µm)
  - Z: -5.15680623e-09 m  (0.005 µm)
- close_distance_meters: -3.38000000e-10 m (0.0003 µm)

**Result:** PyTorch values differ slightly when override is provided, but differences are sub-micron (likely numerical precision).

## Cross-Platform Comparison

### C vs PyTorch (WITH override)

**pix0_vector delta (C - PyTorch):**
- X: -0.000139437779334 m  (-139.4 µm)
- Y:  0.001137416822760 m  (1137.4 µm = 1.14 mm)
- Z: -0.000005599402967 m  (-5.6 µm)

**Maximum component error:** 1.14 mm (Y component)

This 1.14 mm Y-axis error is the pix0 discrepancy previously reported in Phase H3a.

## Analysis & Conclusions

### Finding 1: C-Code Custom Vector Dominance

When custom detector vectors (`-odet_vector`, `-sdet_vector`, `-fdet_vector`) are provided to the C code, they COMPLETELY determine the detector geometry. The `-pix0_vector_mm` flag has **NO EFFECT** on the output.

This suggests that:
1. The custom vectors already encode the detector position/orientation implicitly
2. The C code derives pix0 FROM the custom vectors, not from the pix0_vector flag
3. The `-pix0_vector_mm` flag may only take effect when custom vectors are NOT provided

### Finding 2: PyTorch Override Implementation

The current PyTorch implementation applies the `pix0_override_m` by attempting to back-calculate `Fbeam`/`Sbeam` values from the provided pix0 vector. This produces a 1.14 mm Y-axis error compared to C.

### Finding 3: Correct Implementation Strategy

Since the C code **ignores `-pix0_vector_mm` when custom vectors are present**, the PyTorch implementation should:

1. **When custom detector vectors are provided:** Derive pix0 from the custom vectors exactly as C does (current CUSTOM convention behavior WITHOUT override)

2. **When `-pix0_vector_mm` is provided WITHOUT custom vectors:** Apply the override by directly setting pix0_vector

3. **Priority:** Custom detector vectors OVERRIDE pix0_vector_mm flag (matching C behavior)

## Recommended Implementation Changes

### Phase H3b2: Update Detector Pix0 Logic

```python
def _calculate_pix0_vector(self):
    """Calculate pix0 vector with correct precedence."""

    # If custom detector vectors provided, they define geometry completely
    # (pix0_override is IGNORED, matching C behavior)
    if self.config.custom_fdet_vector is not None:
        # Derive pix0 from custom vectors (existing CUSTOM pathway)
        # ... current CUSTOM logic ...
        return

    # Only apply pix0_override if NO custom vectors
    if self.config.pix0_override_m is not None:
        self.pix0_vector = torch.tensor(
            self.config.pix0_override_m,
            device=self.device,
            dtype=self.dtype
        )
        self.r_factor = torch.tensor(1.0, device=self.device, dtype=self.dtype)
        self.distance_corrected = self.config.distance_mm / 1000.0  # meters
        self._update_beam_centers_from_pix0()  # If needed
        return

    # Standard BEAM/SAMPLE pivot calculation
    # ... existing pivot logic ...
```

### Phase H3b3: Update CLI Regression Test

The test `test_pix0_vector_mm_beam_pivot` should verify that when custom vectors are provided, pix0_override has NO EFFECT (matching C behavior).

## Artifacts

- `c_trace_with_override.log` - C binary run WITH `-pix0_vector_mm`
- `c_trace_without_override.log` - C binary run WITHOUT `-pix0_vector_mm`
- `trace_py_with_override.log` - PyTorch run WITH `pix0_override_m`
- `trace_py_without_override.log` - PyTorch run WITHOUT `pix0_override_m`
- `trace_harness_no_override.py` - Modified trace harness for no-override case

## Next Actions

1. ✅ H3b1 complete - Evidence captured and analyzed
2. ✅ H3b2 - Precedence implemented in commit d6f158c; override now skipped whenever custom detector vectors are present
3. ✅ H3b3 - Regression test updated (tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot) to cover both precedence cases and reference `pix0_expected.json`
4. [ ] H4 - Port C’s post-rotation beam-centre recomputation so pix0 deltas collapse (<5e-5 m) before parity rerun

## References

- Plan: `plans/active/cli-noise-pix0/plan.md` Phase H3b
- Prior analysis: `implementation_notes.md` (Attempt #22 failure)
- Supervisor command: `prompts/supervisor.md` line 9
- C parameter mapping: `docs/development/c_to_pytorch_config_map.md`
