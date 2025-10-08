# Option B Batch-Indexed φ Carryover Cache Design

**Date:** 2025-12-10
**Loop:** Ralph i=162 (docs mode)
**Phase:** CLI-FLAGS-003 M2g.2c
**Purpose:** Design specification for batch-indexed pixel cache before implementation (M2g.3–M2g.6)

---

## Executive Summary

This memo specifies the **Option B (Batch-Indexed Pixel Cache)** architecture for emulating the C-code φ carryover bug (C-PARITY-001) while preserving vectorization, gradient flow, and device/dtype neutrality. The design threads pixel indices through the simulator, processes pixels in batches to maintain vectorization, and uses advanced indexing to substitute cached φ=final vectors into the φ=0 slot without introducing Python loops or `.detach()` calls.

**Key Decisions:**
1. **Batching Granularity:** Row-wise processing (iterate over slow dimension, vectorize across fast dimension)
2. **Memory Footprint:** ~3 MB per row @ float32 (supervisor case), ~224 MB full-frame cache
3. **API Extension:** Add `(slow_indices, fast_indices)` parameters to rotation methods
4. **Validation Plan:** CPU + CUDA pytest selectors, 4×4 ROI gradcheck, cross-pixel trace comparison

---

## 1. Architecture Blocker from Attempt #161

### 1.1 Problem Statement

The current vectorized simulator computes rotation tensors once per run with shape `(N_phi, N_mos, 3)` — **no pixel dimension exists**. Per-pixel φ carryover requires substituting different φ=0 vectors for each (s,f) coordinate, which is impossible without access to pixel indices in the rotation pipeline.

### 1.2 Rejected Alternative (Option A)

**Expand rotation stack to `(S, F, N_phi, N_mos, 3)`:**
- ✅ Minimal API changes
- ❌ Memory explosion: 2527 × 2463 × 10 × 1 × 3 × 4 bytes × 3 vectors = **2.24 GB** (supervisor full-frame)
- ❌ Infeasible for large detectors (>1024²)

**Verdict:** REJECTED per memory constraint (ADR-01 hybrid system already uses meters internally; adding pixel dims violates practicality).

### 1.3 Chosen Alternative (Option B)

**Batch-process pixels with explicit indexing:**
- ⚠️ Medium refactoring complexity (thread indices through simulator)
- ✅ Preserves gradients via advanced indexing (no `.detach()`)
- ✅ Partial vectorization (batch-level, not per-pixel loops)
- ✅ Memory-efficient (~3 MB per row, ROI-scalable to ~113 KB)

**Verdict:** FEASIBLE and architecturally compliant (CLAUDE Rules #8-10, #16).

---

## 2. Spec & C-Code References

### 2.1 Normative Spec Baseline

**specs/spec-a-core.md:211-213:**
> φ step: φ = φ0 + (step index)*phistep; rotate the reference cell (a0,b0,c0)
> about u by φ to get (ap,bp,cp).
> Mosaic: for each domain, apply the domain's rotation to (ap,bp,cp) to get (a,b,c).

**Interpretation:** Spec requires **fresh rotation from (a0,b0,c0) every φ step** — no accumulation or carryover. PyTorch default (`phi_carryover_mode="spec"`) follows this contract exactly. The c-parity shim reproduces the C bug for golden data matching only.

### 2.2 C-Code φ Carryover Bug (C-PARITY-001)

**Source:** `docs/bugs/verified_c_bugs.md:166-204`
**C-Code Reference (CLAUDE Rule #11):**

**nanoBragg.c:2797-2807 (OpenMP firstprivate declaration):**
```c
#pragma omp parallel for ... \
    firstprivate(a,b,c,ap,bp,cp,a_star,b_star,c_star, ...)
for(pixel_i=0; pixel_i < num_pixels; ++pixel_i) {
    // Thread-local ap/bp/cp persist across pixel iterations
    // ...
}
```

**nanoBragg.c:3044-3095 (Conditional φ rotation skip):**
```c
if( phi != 0.0 )
{
    /* rotate about spindle if necessary */
    rotate_axis(a0,ap,spindle_vector,phi);
    rotate_axis(b0,bp,spindle_vector,phi);
    rotate_axis(c0,cp,spindle_vector,phi);
}
// When phi==0: ap/bp/cp retain PREVIOUS PIXEL's φ=final values
```

**Semantic Equivalent:** Thread processes pixels sequentially → per-thread state (`ap/bp/cp`) persists across pixel loop. PyTorch requires explicit `(s,f)`-indexed cache to simulate thread-local persistence since all pixels are processed in a single vectorized batch.

---

## 3. Option B Design Details

### 3.1 Batching Granularity: Row-Wise Processing

**Choice:** Iterate over slow dimension (rows), vectorize across fast dimension (columns).

**Rationale:**
1. **Memory efficiency:** Process one row at a time → peak memory = 1 row × fpixels × N_phi × N_mos × 3 × 4 bytes × 3 vectors
   - Supervisor: 1 × 2463 × 10 × 1 × 3 × 4 × 3 = **889 KB per row** (vs 2.24 GB full-frame)
2. **Vectorization preserved:** Inner loop vectorizes across all fast pixels in the row (2463 elements)
3. **Cache indexing:** Advanced indexing `cache[slow, :]` retrieves full row in single operation
4. **ROI compatibility:** ROI reduces both dimensions proportionally (e.g., 56×56 → 56 rows of 56 pixels = 9.4 KB peak)

**Alternative considered (tile-based):** More complex cache addressing, minimal memory savings vs row-wise, rejected for simplicity.

### 3.2 Cache Tensor Shape & Lifecycle

**Cache tensors (3 total):**
```python
_phi_cache_a: torch.Tensor  # Shape: (S, F, N_mos, 3)
_phi_cache_b: torch.Tensor  # Shape: (S, F, N_mos, 3)
_phi_cache_c: torch.Tensor  # Shape: (S, F, N_mos, 3)
```

**Dimensions:**
- `S = detector.spixels` (e.g., 2527 for supervisor)
- `F = detector.fpixels` (e.g., 2463 for supervisor)
- `N_mos = crystal_config.mosaic_domains` (e.g., 1 for supervisor, 10 typical max)
- `3 = vector components (x, y, z)`

**Memory footprint (float32):**
- Supervisor full-frame: 3 vectors × 2527 × 2463 × 1 × 3 × 4 bytes = **224 MB**
- With N_mos=10: 3 × 2527 × 2463 × 10 × 3 × 4 = **2.24 GB** (still acceptable for modern GPUs)
- ROI (56×56): 3 × 56 × 56 × 1 × 3 × 4 = **113 KB** (negligible)

**Lifecycle:**
1. **Allocation:** On first `Simulator.run()` call, allocate caches with shape based on `detector.spixels/fpixels`
2. **Device/dtype:** Match `crystal.a0_vec.device` and `.dtype` (caller-controlled, no hard-coded `.cpu()/.cuda()`)
3. **Invalidation:** Clear caches when:
   - Detector geometry changes (spixels/fpixels)
   - Crystal cell parameters change (a0/b0/c0 vectors)
   - Mode switches between "spec" and "c-parity"
4. **Reset per run:** Initialize to zero or NaN at start of each `run()` to detect uninitialized reads

### 3.3 API Extensions: Threading Pixel Indices

**Current API (global rotation):**
```python
def get_rotated_real_vectors(self, config: CrystalConfig) -> Tuple[Tensor, Tensor]:
    # Returns: (rotated_real, rotated_recip)
    # Shape: (N_phi, N_mos, 3) — NO pixel dimension
```

**Extended API (batch rotation):**
```python
def get_rotated_real_vectors_for_batch(
    self,
    config: CrystalConfig,
    slow_indices: Tensor,  # Shape: (batch_size,) — slow pixel coordinates
    fast_indices: Tensor,  # Shape: (batch_size,) — fast pixel coordinates
) -> Tuple[Tensor, Tensor]:
    """
    Compute rotated lattice vectors for a batch of pixels, applying cached
    φ=0 substitution when phi_carryover_mode="c-parity".

    C-Code Implementation Reference (from nanoBragg.c, lines 3044-3095):
    ```c
    if( phi != 0.0 )
    {
        rotate_axis(a0,ap,spindle_vector,phi);
        rotate_axis(b0,bp,spindle_vector,phi);
        rotate_axis(c0,cp,spindle_vector,phi);
    }
    // When phi==0: ap/bp/cp retain PREVIOUS PIXEL's φ=final values (carryover)
    ```

    Args:
        config: Crystal configuration with phi_carryover_mode
        slow_indices: Slow pixel indices for this batch (1D tensor)
        fast_indices: Fast pixel indices for this batch (1D tensor)

    Returns:
        rotated_real: Shape (batch_size, N_phi, N_mos, 3)
        rotated_recip: Shape (batch_size, N_phi, N_mos, 3)
    """
    # 1. Compute fresh rotations for all φ steps (standard spec path)
    rotated_real = self._compute_phi_rotations(config)  # (N_phi, N_mos, 3)

    # 2. Expand to batch dimension: (batch_size, N_phi, N_mos, 3)
    rotated_real = rotated_real.unsqueeze(0).expand(len(slow_indices), -1, -1, -1)

    # 3. Apply c-parity carryover substitution if enabled
    if config.phi_carryover_mode == "c-parity":
        # Replace φ=0 slice with cached vectors from prior pixel
        cached_vecs = self._phi_cache_a[slow_indices, fast_indices]  # (batch_size, N_mos, 3)
        rotated_real[:, 0, :, :] = cached_vecs  # Substitute into φ=0 slot

        # Store φ=final for next pixel (update cache in-place)
        self._phi_cache_a[slow_indices, fast_indices] = rotated_real[:, -1, :, :]

    return rotated_real, rotated_recip
```

**Gradient Preservation:**
- Advanced indexing `cache[slow_indices, fast_indices]` preserves `requires_grad` (no `.detach()` needed)
- In-place update `cache[indices] = new_values` maintains computation graph
- Batch expansion via `.expand()` shares storage → no gradient duplication

### 3.4 Simulator Integration Pseudocode

**Modified `Simulator.run()` (row-wise batch loop):**
```python
def run(self, ...) -> Tensor:
    # ... [detector/crystal/beam setup] ...

    # Allocate cache tensors if not present
    if self.crystal._phi_cache_a is None:
        self.crystal.initialize_phi_cache(detector.spixels, detector.fpixels, config.mosaic_domains)

    # Row-wise batch processing
    for slow in range(detector.spixels):
        # Batch indices for this row: all fast pixels
        fast_indices = torch.arange(detector.fpixels, device=device, dtype=torch.long)
        slow_indices = torch.full_like(fast_indices, slow)  # Broadcast slow index

        # Get rotated vectors for this row (with carryover if c-parity mode)
        rotated_real, rotated_recip = crystal.get_rotated_real_vectors_for_batch(
            config, slow_indices, fast_indices
        )
        # Shape: (fpixels, N_phi, N_mos, 3)

        # Compute pixel positions for this row
        pixel_positions = detector.get_pixel_coords_batch(slow_indices, fast_indices)
        # Shape: (fpixels, 3)

        # Vectorized physics for entire row
        row_intensities = self._compute_physics_for_batch(
            pixel_positions, rotated_real, rotated_recip, ...
        )
        # Shape: (fpixels,)

        # Accumulate into output image
        image[slow, :] = row_intensities

    return image
```

**Key Properties:**
1. **No Python pixel loops:** Inner dimension (fast) fully vectorized
2. **Cache operations batched:** Single `cache[slow, :]` retrieval per row
3. **Gradient flow maintained:** All tensor ops differentiable (no `.item()`, no `.detach()`)
4. **Spec mode unaffected:** When `phi_carryover_mode="spec"`, cache lookup/store skipped entirely

---

## 4. Memory & Performance Analysis

### 4.1 Memory Estimates

**Full-Frame (Supervisor Case):**
| Component | Shape | Memory @ float32 |
|-----------|-------|------------------|
| Cache (3 vectors) | (2527, 2463, 1, 3) × 3 | 224 MB |
| Row batch rotation | (2463, 10, 1, 3) × 3 | 889 KB |
| Pixel positions | (2463, 3) | 30 KB |
| **Peak (cache + 1 row)** | — | **~225 MB** |

**ROI (56×56 typical):**
| Component | Shape | Memory @ float32 |
|-----------|-------|------------------|
| Cache (3 vectors) | (56, 56, 1, 3) × 3 | 113 KB |
| Row batch rotation | (56, 10, 1, 3) × 3 | 20 KB |
| **Peak (cache + 1 row)** | — | **~133 KB** |

**Conclusion:** Memory footprint acceptable for both full-frame and ROI workflows. GPU memory (8-16 GB typical) can easily accommodate the cache.

### 4.2 Performance Tradeoff

**Vectorization comparison:**
- **Baseline (spec mode):** Compute rotations once → apply to all pixels (pure broadcast)
- **Option B (c-parity mode):** Compute rotations per row → apply to row pixels (batched broadcast)

**Expected overhead:**
- Row loop introduces `O(S)` iterations (2527 for supervisor)
- Each iteration vectorizes over `F` pixels (2463)
- Cache lookup/store: `O(1)` per row via advanced indexing
- **Estimated slowdown:** <10% (empirical validation needed via prototype)

**Mitigation:**
- ROI workflows (most common for debugging) see negligible overhead (<1%)
- Full-frame runs acceptable if within 2× baseline (spec permits slower c-parity mode for accuracy)

---

## 5. Gradient & Device Guardrails

### 5.1 Differentiability Requirements

**CLAUDE Rule #8 (ADR-08):**
> Never Use `.item()` on Differentiable Tensors

**Compliance:**
- ✅ No `.item()` calls in cache lookup/store paths
- ✅ Advanced indexing `cache[indices]` preserves `requires_grad`
- ✅ In-place updates via `cache[indices] = values` maintain computation graph

**CLAUDE Rule #9:**
> Avoid `torch.linspace` for Gradient-Critical Code

**Compliance:**
- ✅ φ angle generation uses manual arithmetic: `phi0 + phistep * torch.arange(...)`
- ✅ No `torch.linspace` with tensor endpoints in rotation pipeline

**CLAUDE Rule #10:**
> Boundary Enforcement for Type Safety

**Compliance:**
- ✅ Cache allocation inherits device/dtype from `crystal.a0_vec` (caller-controlled)
- ✅ Batch indices created with explicit `device=` parameter
- ✅ No `isinstance(param, torch.Tensor)` checks in hot path

### 5.2 Device/Dtype Neutrality (CLAUDE Rule #16)

**Requirements:**
- Accept tensors on any device (CPU/CUDA/MPS)
- Respect caller's dtype (float32/float64)
- No hard-coded `.cpu()`/`.cuda()` conversions

**Implementation:**
```python
def initialize_phi_cache(self, spixels, fpixels, mosaic_domains):
    # Inherit device/dtype from existing crystal tensors
    device = self.a0_vec.device
    dtype = self.a0_vec.dtype

    # Allocate cache tensors on correct device
    self._phi_cache_a = torch.zeros(
        (spixels, fpixels, mosaic_domains, 3),
        device=device, dtype=dtype
    )
    self._phi_cache_b = torch.zeros(...)  # Same device/dtype
    self._phi_cache_c = torch.zeros(...)
```

**Validation:**
- CPU smoke test: `pytest tests/test_cli_scaling_parity.py -k "cpu"`
- CUDA smoke test: `pytest tests/test_cli_scaling_parity.py -k "cuda"` (when available)
- Mixed-dtype test: Run with `dtype=torch.float64` to verify no silent downcasts

---

## 6. Validation Plan

### 6.1 Pytest Selectors (M2h.1)

**CPU Parity Test (mandatory):**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q
```

**Expected outcome:**
- F_latt relative error < 0.001 (0.1%)
- I_before_scaling ratio within [0.999, 1.001]
- Test duration < 60 seconds

**CUDA Parity Probe (optional, M2h.2):**
```bash
python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py \
    --pixel 685 1039 --config supervisor --phi-mode c-parity \
    --device cuda --dtype float64 --out trace_py_scaling_cuda.log
```

### 6.2 Gradient Check Harness (M2h.3)

**4×4 ROI gradcheck script:**
```python
import torch
from nanobrag_torch.config import CrystalConfig, DetectorConfig
from nanobrag_torch.simulator import Simulator

def test_phi_carryover_gradients():
    # Minimal 4×4 detector, float64 for numerical precision
    detector = DetectorConfig(
        spixels=4, fpixels=4, pixel_size_mm=0.1, distance_mm=100.0,
        ...
    )

    # Cell parameter as differentiable input
    cell_a = torch.tensor(100.0, requires_grad=True, dtype=torch.float64)
    crystal = CrystalConfig(
        cell_a=cell_a, cell_b=100.0, cell_c=100.0,
        phi_carryover_mode="c-parity", ...
    )

    # Simulate and extract scalar loss
    simulator = Simulator(detector, crystal, ...)
    image = simulator.run()
    loss = image.sum()

    # Verify gradient flow
    loss.backward()
    assert cell_a.grad is not None, "Gradient lost through carryover cache!"
    assert torch.isfinite(cell_a.grad), "Gradient is NaN/Inf!"

    # Numerical gradient check
    torch.autograd.gradcheck(
        lambda a: Simulator(detector, CrystalConfig(cell_a=a, ...), ...).run().sum(),
        cell_a, eps=1e-6, atol=1e-4
    )
```

**Artifacts:**
- `gradcheck.log`: stdout from gradcheck run
- `metrics.json`: grad magnitude, finite check results
- Exit code 0 → gradients valid; non-zero → gradient break detected

### 6.3 Cross-Pixel Trace Comparison (M2i.1–M2i.3)

**ROI trace harness:**
```bash
python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py \
    --roi 684 686 1039 1040 --phi-mode c-parity --dtype float64 \
    --out trace_py_scaling_carryover.log
```

**Expected outcome (M2i.2):**
- Pixel (684,1039): φ=0 uses fresh rotation (no prior pixel in sequence)
- Pixel (685,1039): φ=0 uses cached φ=final from (684,1039)
- `first_divergence=None` in metrics.json (C/PyTorch traces match)

**Documentation update (M2i.3):**
- Refresh `lattice_hypotheses.md` with new trace deltas
- Update `scaling_validation_summary.md` with VG-2 closure evidence
- Flip M2 plan rows to [D] once metrics green

---

## 7. Implementation Risks & Mitigation

### 7.1 Identified Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Gradient break in advanced indexing | HIGH | Mandatory gradcheck (M2h.3) before merging |
| Cache dimension mismatch | MEDIUM | Validate shapes in `initialize_phi_cache()` |
| Performance regression >2× | MEDIUM | Profile 4×4 ROI prototype, document slowdown |
| Device transfer (CPU→GPU leak) | MEDIUM | Smoke test on CUDA, check for implicit `.cpu()` |
| NaN propagation in cache | LOW | Initialize cache to zeros, add NaN assertions |

### 7.2 Rollback Plan

If gradient checks fail or performance degrades >2×:
1. **Park Option B implementation** (do not merge to main)
2. **Document failure mode** in `phi_carryover_diagnosis.md`
3. **Escalate to supervisor** for architecture decision (Option C or alternative)
4. **Maintain spec mode as default** (c-parity remains experimental)

---

## 8. Spec Mode Isolation Guarantee

**Critical requirement:** Default behavior (`phi_carryover_mode="spec"`) **MUST NOT** be affected by Option B implementation.

**Enforcement:**
```python
def get_rotated_real_vectors_for_batch(self, config, slow_indices, fast_indices):
    # Spec mode: bypass cache entirely
    if config.phi_carryover_mode != "c-parity":
        # Compute fresh rotations, no cache interaction
        rotated_real = self._compute_phi_rotations(config)
        return rotated_real.unsqueeze(0).expand(len(slow_indices), -1, -1, -1), ...

    # C-parity mode: apply cached substitution
    rotated_real = self._compute_phi_rotations(config)
    cached_vecs = self._phi_cache_a[slow_indices, fast_indices]
    rotated_real[:, 0, :, :] = cached_vecs  # φ=0 substitution
    ...
```

**Verification:**
- Run baseline spec mode tests: `pytest tests/test_cli_scaling_phi0.py -v`
- Confirm no performance regression in spec mode
- Validate that cache is never allocated when `phi_carryover_mode="spec"`

---

## 9. C-Code Citation Summary (CLAUDE Rule #11)

Per CLAUDE.md Core Implementation Rule #11, all ported logic must include exact C-code references:

**nanoBragg.c:2797-2807 (Thread-local state via `firstprivate`):**
```c
#pragma omp parallel for ... \
    firstprivate(a,b,c,ap,bp,cp,a_star,b_star,c_star, ...)
```
**Interpretation:** OpenMP captures `ap/bp/cp` per-thread → values persist across pixel loop iterations within the same thread.

**nanoBragg.c:3044-3059 (Conditional φ rotation skip):**
```c
if( phi != 0.0 )
{
    rotate_axis(a0,ap,spindle_vector,phi);
    rotate_axis(b0,bp,spindle_vector,phi);
    rotate_axis(c0,cp,spindle_vector,phi);
}
```
**Interpretation:** When `phi==0.0`, rotation is skipped → `ap/bp/cp` retain values from prior pixel's φ=final step (carryover bug).

**PyTorch equivalent:** Use `(S,F,N_mos,3)` cache tensors indexed by `(slow, fast)` to simulate per-thread persistence in vectorized batch context.

---

## 10. Next Actions (M2g.2d → M2g.3)

### 10.1 Prototype ROI Script (M2g.2d)

**Deliverable:** `prototype.md` + disposable Python script demonstrating 4×4 ROI batch wiring.

**Scope:**
- Mock cache allocation (4×4×1×3 shape)
- Batch rotation call with `(slow_indices=[0,1,2,3], fast_indices=[0,1,2,3])`
- Cache lookup/store via advanced indexing
- Gradcheck on scalar lattice function
- Record: stdout, metrics.json, gradcheck.log

**Exit criteria:**
- Gradcheck passes (numerical gradient error < 1e-4)
- Cache indexing produces expected shapes
- No device transfer warnings (run on CPU)

### 10.2 Production Implementation (M2g.3–M2g.6)

Once prototype validates:
1. **M2g.3:** Allocate pixel-indexed caches in `Crystal.__init__()`
2. **M2g.4:** Wire `get_rotated_real_vectors_for_batch()` into `Simulator.run()` row loop
3. **M2g.5:** Update trace harness + parity scripts to exercise new pathway
4. **M2g.6:** Document architecture decision in `phi_carryover_diagnosis.md`

---

## 11. References

### Specifications & Plans
- `specs/spec-a-core.md:205-233` — Normative φ rotation pipeline (no carryover)
- `specs/spec-a-cli.md` — CLI semantics for `--phi-carryover-mode` flag
- `plans/active/cli-noise-pix0/plan.md:109` — M2g task breakdown
- `plans/active/cli-phi-parity-shim/plan.md` — Parity shim plan (Phases A–D)

### C-Code References
- `nanoBragg.c:2797-2807` — OpenMP `firstprivate` declaration
- `nanoBragg.c:3044-3095` — Conditional φ rotation skip (carryover bug)

### Documentation
- `docs/bugs/verified_c_bugs.md:166-204` — C-PARITY-001 classification
- `docs/architecture/pytorch_design.md` — Vectorization strategy (ADR-11)
- `arch.md` — ADR-08 (Differentiability Preservation), ADR-01 (Hybrid Unit System)
- `CLAUDE.md` — Rules #8-11 (gradient preservation), #16 (device/dtype neutrality)

### Evidence Artifacts
- `reports/2025-10-cli-flags/phase_l/scaling_validation/20251208_option1_refresh/analysis.md` — Option 1 refresh memo
- `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T100653Z/phi_carryover_diagnosis.md` — Original Option 1 proposal
- `reports/2025-10-cli-flags/phase_l/rot_vector/20251007T212159Z/` — Spec baseline evidence (VG-1)

---

## Metadata

- **Commit SHA:** (to be recorded post-commit)
- **Test Collection:** ✅ `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` passed (1 test collected)
- **Mode:** Docs (no production code changes per input.md directive)
- **Artifacts Directory:** `reports/2025-10-cli-flags/phase_l/scaling_validation/20251210_optionB_design/`
- **Next Loop:** M2g.2d (prototype) → M2g.3–M2g.6 (implementation) upon design approval
