# CLI-FLAGS-003 Phase M2h.3: Gradcheck Evidence Summary

**Date:** 2025-10-08
**Git SHA:** e72f26e5ffdebe937e89b05855b0248b26b6c887
**Branch:** feature/spec-based-2
**Task:** M2h.3 gradcheck probe for phi carryover cache gradient flow

## Executive Summary

**✓ SUCCESS:** Gradient flow is maintained through the phi carryover cache on both CUDA and CPU devices.

The phi carryover cache implementation in `Crystal.store_phi_final()` and `Crystal.apply_phi_carryover()` correctly preserves gradient connectivity. The `cell_a` parameter successfully backpropagates through the cache store/retrieve cycle, confirming that Option B batch-indexed cache design does not break the computation graph.

## Test Configuration

- **Device Coverage:** CUDA (primary) + CPU (fallback verification)
- **Data Type:** float64 (for numerical precision)
- **ROI:** 2×2 pixel cache (minimal test case)
- **Loss Function:** Sum of retrieved real and reciprocal vectors
- **Differentiable Parameter:** `crystal_config.cell_a`

## Results

### CUDA Gradcheck (Primary)

**Command:**
```bash
env KMP_DUPLICATE_LIB_OK=TRUE python gradcheck_probe.py --device cuda --dtype float64
```

**Status:** ✓ PASS
**Loss:** 1.199520e+03
**Gradient Value:** 3.997600e+00
**Gradient Present:** True

**Output:**
```json
{
  "timestamp": "2025-10-08T17:00:31Z",
  "device": "cuda",
  "dtype": "torch.float64",
  "grad_present": true,
  "loss": 1199.5199400000001,
  "grad_value": 3.9976002,
  "success": true
}
```

### CPU Gradcheck (Fallback Verification)

**Command:**
```bash
env KMP_DUPLICATE_LIB_OK=TRUE python gradcheck_probe.py --device cpu --dtype float64
```

**Status:** ✓ PASS
**Loss:** 1.199520e+03
**Gradient Value:** 3.997600e+00
**Gradient Present:** True

**Output:**
```json
{
  "timestamp": "2025-10-08T17:00:42Z",
  "device": "cpu",
  "dtype": "torch.float64",
  "grad_present": true,
  "loss": 1199.51994,
  "grad_value": 3.9976002,
  "success": true
}
```

## Key Findings

1. **Gradient Connectivity Verified:** The cache implementation successfully maintains gradient flow from `cell_a` through:
   - Crystal property access (`.a`, `.b`, `.c`, `.a_star`, `.b_star`, `.c_star`)
   - Tensor operations (scaling, stacking, broadcasting)
   - Cache storage (`store_phi_final`)
   - Cache retrieval (`apply_phi_carryover`)
   - Loss computation and backpropagation

2. **Device Neutrality Confirmed:** Identical gradient values on CUDA and CPU devices demonstrate proper device-neutral implementation.

3. **No Detachment Breaks:** The cache does not use `.detach()`, `.clone()` (without gradient tracking), or `.item()` in ways that would sever the computation graph.

4. **Option B Design Validated:** The batch-indexed cache design from `reports/.../20251210_optionB_design/` successfully preserves gradients while operating on pixel tensors.

## Implementation Details Tested

### Cache Initialization
```python
crystal.initialize_phi_cache(spixels=2, fpixels=2)
```

Creates `(S, F, N_mos, 3)` shaped cache tensors on the same device/dtype as the crystal instance.

### Cache Storage
```python
crystal.store_phi_final(slow_indices, fast_indices, real_tuple, recip_tuple)
```

Stores φ=final rotation vectors for 4 pixels (indices [0,0], [0,1], [1,0], [1,1]) without breaking gradient connections.

### Cache Retrieval
```python
retrieved_real, retrieved_recip = crystal.apply_phi_carryover(
    slow_indices, fast_indices, fresh_real_tuple, fresh_recip_tuple
)
```

Retrieves cached vectors and replaces φ=0 entries using functional operations (`torch.where`), preserving gradients.

## Pytest Selector Note

The planned integration test `tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c` does not yet exist. This is expected per the plan - the test will be added once the cache implementation is complete and M2g.3/M2g.4 tasks are marked [D].

## Artifact Manifest

- `gradcheck_probe.py` — Gradcheck harness script
- `gradcheck.log` — CUDA probe output (174 bytes)
- `gradcheck_cpu.log` — CPU probe output (171 bytes)
- `commands.txt` — Reproduction commands
- `env.json` — Environment metadata
- `summary.md` — This report
- `sha256.txt` — Artifact checksums (pending)

## Next Actions (per input.md M2h.4)

1. **Fix Plan Update:** Append Attempt #167 to `docs/fix_plan.md` CLI-FLAGS-003 with:
   - **Result:** M2h.3 gradcheck PASS (both CUDA and CPU)
   - **Metrics:** gradient present=True, cell_a.grad=3.9976, loss=1199.52
   - **Artifacts:** `reports/.../20251008T165745Z_carryover_cache_validation/`
   - **Device Coverage:** CUDA + CPU verified
   - **Observations:** Cache implementation correctly preserves gradient flow; Option B design validated
   - **Next Actions:** Proceed to M2i.1 trace rerun with cache-enabled harness

2. **Plan Status Update:** Mark M2h.3 as [D] in `plans/active/cli-noise-pix0/plan.md` Phase M2h validation table.

3. **Trace Rerun:** Execute M2i.1 to regenerate cross-pixel traces with ROI 684-686×1039-1040 in c-parity mode.

## References

- **Plan:** `plans/active/cli-noise-pix0/plan.md` Phase M2h
- **Design:** `reports/.../20251210_optionB_design/optionB_batch_design.md`
- **Prototype:** `reports/.../20251210_optionB_design/prototype_batch_cache.py`
- **Bug:** `docs/bugs/verified_c_bugs.md:166-204` (C-PARITY-001)
- **C Reference:** `golden_suite_generator/nanoBragg.c:2797,3044-3095`
- **CLAUDE Rule:** Core Implementation Rules #3, #9, #10 (differentiability)

---

**Report Generated:** 2025-10-08T17:04:00Z
**Author:** ralph (CLI-FLAGS-003 diagnostic loop #167)
