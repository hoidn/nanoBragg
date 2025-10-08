# φ=0 Carryover Cache Architecture Diagnosis

**Date:** 2025-10-22
**Phase:** CLI-FLAGS-003 M2
**Loop:** Ralph i=151
**Engineer:** Ralph
**Git SHA:** (to be recorded post-commit)

## Executive Summary

The φ=0 carryover cache implementation (commit 3269f6d) correctly implements the **storage** and **retrieval** logic to emulate C-PARITY-001, but **fails due to an architectural mismatch** between the cache scope (per-invocation) and the required semantics (per-pixel within a run).

**Test status after configuration fix:**
- ✅ F_cell: **PASSES** (configuration parity restored)
- ❌ F_latt: **FAILS** with 158% relative error (φ=0 carryover not working)
- Expected: -2.383196653, Got: 1.379483851

**Root cause:** `Simulator.run()` calls `Crystal.get_rotated_real_vectors()` **once** for the entire image, computing all pixels' φ steps in a single vectorized operation. The cache stores/retrieves vectors between **different Simulator.run() calls** (different images), not between **consecutive pixels within the same image**.

## Problem Analysis

### 1. Configuration Parity Bug (FIXED)

**Before fix:** test used MOSFLM convention with swapped dimensions (spixels=2463, fpixels=2527)
**C trace used:** CUSTOM convention with dimensions (spixels=2527, fpixels=2463)

**Fix applied:** Updated `tests/test_cli_scaling_parity.py:92-112` to use:
- `DetectorConvention.CUSTOM`
- Correct dimensions (2527×2463)
- Custom detector vectors from `trace_harness.py`
- Custom pix0 override

**Result:** F_cell now matches (relative error effectively zero), but F_latt still fails.

### 2. Cache Architecture Mismatch (PRIMARY ISSUE)

#### C-Code Behavior (OpenMP firstprivate)

```c
// nanoBragg.c:2797
#pragma omp parallel for ... firstprivate(ap,bp,cp,...)

for(pixel_i=0; pixel_i < num_pixels; ++pixel_i) {  // Thread-local loop
    for(phi_tic=0; phi_tic<phisteps; ++phi_tic) {
        phi = phi0 + phistep*phi_tic;
        if( phi != 0.0 ) {
            rotate_axis(a0,ap,spindle_vector,phi);  // Update ap/bp/cp
        }
        // When phi==0: ap/bp/cp retain PREVIOUS PIXEL's φ=final values
    }
}
```

**Key point:** Each thread processes pixels **sequentially** → `ap/bp/cp` persist across pixel loop iterations.

#### PyTorch Current Implementation

```python
# Simulator.run() line ~820
rotated_real, rotated_recip = crystal.get_rotated_real_vectors(crystal_config)
# Shape: (N_phi, N_mos, 3) - computed ONCE for entire run
```

**Problem:** All pixels use the **same** rotated vectors tensor. No per-pixel state.

#### Current Cache Logic (crystal.py:1276-1313)

```python
if config.phi_carryover_mode == "c-parity":
    cache = self._phi_carryover_cache
    if cache['a'] is not None:
        # Replace φ=0 with cached vectors
        a_final[0] = cache['a']  # Reads from PREVIOUS run()

    # Store φ=final for NEXT run()
    cache['a'] = a_final[-1].detach().clone()  # ❌ .detach() breaks gradients
```

**Execution timeline:**
1. Run #1 (pixel 1): Cache empty → φ=0 uses fresh vectors → Cache stores φ=final
2. Run #2 (pixel 2, **different image**): Cache has Run#1 data → φ=0 uses Run#1 φ=final
3. **Within Run#1:** ALL pixels use the same φ=0 vectors (no carryover between pixels)

### 3. Additional Architectural Violations

1. **Gradient Breaking:** `.detach().clone()` (line 1308) severs computation graph
2. **In-place Modification:** `a_final[0] = cached_a` can break autograd in some scenarios
3. **Single-pixel test limitation:** First pixel has no "previous pixel" to carry over from

## Proposed Solutions

### Option 1: Pixel-Indexed Cache with Deferred Substitution (RECOMMENDED)

**Concept:** Store φ=final vectors per-pixel and apply carryover during physics computation.

**Changes required:**
1. Expand cache to `(S, F, N_mos, 3)` shape for each vector
2. Keep `get_rotated_real_vectors()` unchanged (returns fresh vectors)
3. Add `apply_phi_carryover(vectors, pixel_s, pixel_f)` method
4. Modify `_compute_physics_for_position()` to call carryover before Miller index calculation

**Pros:**
- ✅ Preserves vectorization (no Python loops)
- ✅ Maintains gradient flow (no .detach())
- ✅ Correct per-pixel semantics
- ✅ Device/dtype neutral

**Cons:**
- ⚠️ Memory: ~4-8 GB for full 2527×2463 detector at float32
- ⚠️ Complex: requires threading pixel coordinates through call stack

**Feasibility:** Medium-High (memory acceptable, implementation moderate complexity)

### Option 2: Sequential Pixel Batching (NOT RECOMMENDED)

Process pixels in sequential batches with per-pixel vector computation.

**Pros:** Simple semantics
**Cons:** ❌ Violates mandatory vectorization (Core Rule #16), 10-100× slower

### Option 3: Deferred Gradient Attachment (ALTERNATIVE)

Store detached vectors, re-attach to graph when used.

**Pros:** Lower memory, maintains gradient flow
**Cons:** Still requires per-pixel cache lookup, breaks pure vectorization

## Test Status

### Configuration Parity Test
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -xvs tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c
```

**Result:** FAILS at F_latt assertion
- Expected (C): -2.3831966530
- Got (PyTorch): 1.3794838506
- Relative error: 157.88% ❌
- Message: "This likely indicates φ=0 carryover not working correctly."

### What Changed
- ✅ F_cell matches (configuration parity fixed)
- ❌ F_latt still wrong (cache architecture issue)
- Root cause: Cache never fires between pixels in same image

## Next Steps

### Immediate (This Loop - Documentation)
1. ✅ Document diagnosis in this file
2. ✅ Update fix_plan.md with Attempt #151 entry
3. ✅ Update plan Phase M2 guidance with architecture decision
4. ✅ Commit documentation changes

### Phase M2 Implementation (Next Loop)
1. Design pixel-indexed cache structure (Option 1)
2. Implement cache in Crystal.__init__
3. Add apply_phi_carryover() method
4. Wire into _compute_physics_for_position()
5. Add multi-pixel test to verify carryover

### Phase M3 Validation
1. Run multi-pixel test (pixels 684,1039 → 685,1039)
2. Verify cache hit for second pixel
3. Run test_cli_scaling_parity.py (should pass)
4. Execute trace_harness.py with TRACE_PY_ROTSTAR
5. Regenerate metrics.json with first_divergence=None

## References

- Spec: `input.md:1-98` (Do Now directive for Phase M2)
- Plan: `plans/active/cli-noise-pix0/plan.md:59-108` (Phase M tasks)
- Bug docs: `docs/bugs/verified_c_bugs.md` (C-PARITY-001)
- C trace: `reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log`
- Test: `tests/test_cli_scaling_parity.py`
- Impl: `src/nanobrag_torch/models/crystal.py:1243-1313`

## Artifacts

- This diagnosis: `reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md`
- Test output: captured in fix_plan.md Attempt #151
- Configuration fix diff: tests/test_cli_scaling_parity.py lines 92-112

## Decision

**Proceed with Option 1 (Pixel-Indexed Cache) in next implementation loop.**

Rationale:
- Only option that satisfies all architectural constraints
- Memory cost acceptable (~4-8 GB) for modern hardware
- Preserves vectorization, gradient flow, and device neutrality
- Clear separation of concerns (generation vs substitution)
