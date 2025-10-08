# M2d Cross-Pixel Carryover Evidence

**Date:** 2025-10-08T10:07:34Z
**Git SHA:** f9ffd890cdfae1ae511f9eb9480ee16e0d28466e
**Engineer:** Ralph (loop i=152)
**Phase:** CLI-FLAGS-003 M2d

## Executive Summary

**CRITICAL FINDING**: Consecutive pixels (684,1039) and (685,1039) show **identical** φ=0 rotated real-space vectors, proving the current cache implementation does NOT achieve per-pixel carryover. This confirms the diagnosis in `phi_carryover_diagnosis.md` that the cache operates between **separate run() invocations** (different images), not between **consecutive pixels within the same image**.

## Evidence

### Pixel 1 (684, 1039)
- φ_tic=0: `ap_y=-21.8717928453817 bp_y=0.717320030990266 cp_y=-24.3892962470766`
- φ_tic=9: `ap_y=-21.8805340763623 bp_y=0.671588233999813 cp_y=-24.4045855811067`

### Pixel 2 (685, 1039)
- φ_tic=0: `ap_y=-21.8717928453817 bp_y=0.717320030990266 cp_y=-24.3892962470766` ← **IDENTICAL to Pixel 1 φ=0**
- φ_tic=9: `ap_y=-21.8805340763623 bp_y=0.671588233999813 cp_y=-24.4045855811067`

### Expected Behavior (C-PARITY-001)

If carryover were working correctly:
- Pixel 2 φ_tic=0 should match Pixel 1 φ_tic=9 values
- Instead, both pixels independently compute φ=0 from base vectors

## Root Cause Confirmation

The trace harness executes:
1. **Pixel 1**: `simulator = Simulator(...); detector = Detector(...); crystal = Crystal(...); simulator.run()`
2. **Pixel 2**: NEW `simulator = Simulator(...); detector = Detector(...); crystal = Crystal(...); simulator.run()`

Each `run()` creates fresh rotated vectors → no state persists between pixels.

## Architectural Implications

### Current Implementation (Broken)
```python
# Crystal.get_rotated_real_vectors() computes ONCE per run()
rotated_real = self._compute_all_phi_steps()  # Shape: (N_phi, N_mos, 3)
# ALL pixels in the same run() use the same tensor
```

### Required Semantics (C-PARITY-001)
```c
// C code (OpenMP firstprivate ap/bp/cp)
for (pixel=0; pixel<num_pixels; pixel++) {  // Sequential per thread
    for (phi_tic=0; phi_tic<phisteps; phi_tic++) {
        if (phi != 0.0) {
            rotate_axis(a0, ap, spindle_vector, phi);  // Update ap
        }
        // When phi==0: ap retains PREVIOUS PIXEL's final φ value
    }
}
```

## Option 1 Requirements (Tensor Design)

Per `input.md` Do Now, we must document:

### 1. Tensor Shapes
- **Cache storage**: `(S, F, N_mos, 3)` per vector (a, b, c)
  - S = slow pixels (2527 for supervisor case)
  - F = fast pixels (2463)
  - N_mos = mosaic domains (1 for supervisor case)
  - 3 = vector components (x, y, z)
- **Memory footprint** (float32):
  - 3 vectors × 2527 × 2463 × 1 × 3 × 4 bytes ≈ 224 MB
  - Full detector @ float32 with N_mos=10 → ~2.2 GB (acceptable)

### 2. Cache Initialization/Clear Rules
- **Allocate** at `Simulator.__init__()` after detector size is known
- **Populate** during first `run()` pass: after computing φ=final for each pixel, store in cache[slow, fast, :, :]
- **Apply** on subsequent pixel calculations: when computing φ=0, replace fresh vectors with `cache[slow, fast, :, :]`
- **Clear** on ROI boundary changes or new simulation run (if detector geometry changes)

### 3. Call Sequence
```
Simulator.run()
  └─ for each pixel (slow, fast):
      ├─ Crystal.get_rotated_real_vectors() → returns (N_phi, N_mos, 3)
      ├─ Crystal.apply_phi_carryover(slow, fast, vectors_phi0) → modifies φ=0 slice in-place OR returns corrected tensor
      └─ _compute_physics_for_position(pixel, vectors) → uses carryover-adjusted vectors
```

Alternative (deferred substitution):
```
_compute_physics_for_position()
  └─ if phi_tic == 0 and carryover_mode == "c-parity":
      └─ use Crystal.get_cached_phi_final(slow, fast) instead of fresh φ=0 vectors
```

### 4. Gradient Preservation
- **No `.detach()`**: Store tensors with `requires_grad` intact
- **Use tensor indexing**: `cache[s, f] = vectors[-1]` (last φ step)
- **Advanced indexing for batch ops**: When vectorizing across pixels, use `cache[slow_indices, fast_indices]`
- **Device/dtype neutrality**: Allocate cache on same device/dtype as input vectors

### 5. C-Code Reference Mapping
- Cache storage → C variables `ap[3], bp[3], cp[3]` (OpenMP firstprivate)
- Carryover condition → `if (phi != 0.0)` (nanoBragg.c:3044-3095)
- Per-pixel loop → `#pragma omp parallel for ... firstprivate(ap,bp,cp,...)` (line 2797)

## Test Validation Strategy

### Immediate (M2e)
1. Run `pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c`
2. Expect **FAIL** with current cache (this probe confirms why)
3. Cite this analysis in Attempt log

### Post-Implementation (M2h)
1. Rerun this two-pixel probe with Option 1 cache active
2. **Expected**: Pixel 2 φ_tic=0 matches Pixel 1 φ_tic=9
3. Verify `ΔF_latt < 1e-6` for both pixels
4. Run gradcheck with 2×2 ROI to confirm gradient flow

## Artifacts

- Commands: `commands.txt`
- Pixel 1 trace: `trace_pixel1.log`
- Pixel 2 trace: `trace_pixel2.log`
- ROTSTAR comparison: `pixel1_rotstar.txt`, `pixel2_rotstar.txt`
- Environment: `env.json`
- SHA256 checksums: `sha256.txt`

## Next Steps (per input.md)

1. ✅ M2d complete - Evidence gathered
2. **M2f** - Update `phi_carryover_diagnosis.md` with tensor shape details (this loop)
3. **M2g** - Implement pixel-indexed cache (next Ralph loop)
4. **M2h** - Validate gradients and device parity
5. **M2i** - Regenerate cross-pixel traces with working cache

## References

- Plan: `plans/active/cli-noise-pix0/plan.md:80-95`
- Diagnosis: `reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md`
- C bug spec: `docs/bugs/verified_c_bugs.md:166-204` (C-PARITY-001)
- Spec: `specs/spec-a-core.md:205-233` (normative φ behavior)
