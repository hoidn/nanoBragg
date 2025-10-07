# Phase B Design Notes: Tricubic Interpolation Vectorization

**Document Version:** 1.0
**Date:** 2025-10-07
**Git SHA:** aedb82e (feature/spec-based-2)
**Initiative:** VECTOR-TRICUBIC-001 (PERF-PYTORCH-004 backlog)
**References:**
- Plan: `plans/active/vectorization.md` Phase B (tasks B1–B3)
- Baseline: `reports/2025-10-vectorization/phase_a/tricubic_baseline.md`
- Spec: `specs/spec-a-core.md` §4 (Structure factors)
- Architecture: `docs/architecture/pytorch_design.md` §§2.2–2.4
- C Reference: `nanoBragg.c` lines 4021–4058 (polint/polin2/polin3)
- Current Implementation: `src/nanobrag_torch/models/crystal.py` lines 350–409, `src/nanobrag_torch/utils/physics.py` lines 315–445

---

## Executive Summary

This memo defines the tensor shape design, broadcasting plan, and gradient/device requirements for vectorizing the tricubic interpolation pipeline in nanoBragg PyTorch. The current scalar-only implementation (≈5.5 ms/call on CUDA, ≈1.4 ms/call on CPU per Phase A baselines) limits performance when processing batched detector pixels. Vectorization will eliminate Python loops over neighborhood gathering and polynomial evaluation, enabling GPU parallelism and torch.compile optimization.

**Key Decision:** Adopt a two-stage vectorization approach: (1) **Phase C** implements batched neighborhood gather to construct `(B, 4, 4, 4)` subcubes from Miller indices, where `B` is an arbitrary batch dimension encompassing `(S, F)` detector pixels plus any additional batching (oversample, phi, mosaic); (2) **Phase D** vectorizes `polint`/`polin2`/`polin3` to consume these batched subcubes without Python loops. This preserves the existing fallback logic (out-of-bounds → default_F, single warning emission) while enabling compile-friendly batching.

---

## 1. Context & Motivation

### 1.1 Current Scalar Implementation Limitations

The existing `Crystal._tricubic_interpolation` method (lines 313–409 in `crystal.py`) detects batched inputs (`h.numel() > 1`) and falls back to nearest-neighbor lookup with a warning:
```python
if h.numel() > 1:
    # Batched input detected - fall back to nearest neighbor
    if not self._interpolation_warning_shown:
        print("WARNING: tricubic interpolation not yet supported for batched inputs")
        ...
    return self._nearest_neighbor_lookup(h, k, l)
```

**Reason:** The `polin3`/`polin2`/`polint` helpers (`utils/physics.py` lines 315–445) expect scalar query points and 1D/2D/3D grids; they cannot handle batched tensors. Additionally, the current code builds a single `(4, 4, 4)` subcube (`sub_Fhkl`) regardless of how many query points are provided, which is incorrect for vectorized operation where each query needs its own neighborhood.

**Performance Impact (from Phase A):**
- CPU: ~1.4 ms/call (100 scalar calls in benchmark)
- CUDA: ~5.5 ms/call (100 scalar calls in benchmark)
- Per-call overhead remains constant regardless of batch size because the loop is external to the method

### 1.2 Goals for Vectorization

1. **Eliminate Python Loops:** Process all `(S, F)` detector pixels in a single tensor operation to enable GPU parallelism and torch.compile fusion
2. **Preserve Physics:** Maintain exact numerical parity with the C-code `polint`/`polin2`/`polin3` algorithms (Lagrange 4-point interpolation)
3. **Maintain Differentiability:** Ensure gradients flow through cell parameters → reciprocal vectors → Miller indices → interpolated F values
4. **Device Neutrality:** Work correctly on CPU and CUDA without `.cpu()`/`.cuda()` casts (per Core Rule #16)
5. **Backward Compatibility:** Keep the scalar code path functional for debugging and preserve existing test behavior

---

## 2. Tensor Shape Design (Task B1)

### 2.1 Input Shapes

The `get_structure_factor` method receives Miller indices with shape:
```
h, k, l: (S, F) or (S, F, oversample, oversample) or (phi, mosaic, S, F, ...)
```
where the leading dimensions depend on the caller's batching strategy (detector grid, subpixel sampling, phi/mosaic sweeps).

**Key Observation:** We do not need to know the specific batch dimensions; we can flatten all leading dims into a single batch dimension `B = S × F × ...` and operate on `(B,)` tensors internally.

### 2.2 Neighborhood Gathering Output Shape

For each query point `(h, k, l)`, tricubic interpolation requires a 4×4×4 neighborhood of structure factors. The target shape after batched gather is:
```
sub_Fhkl: (B, 4, 4, 4)
```
where:
- `B` is the flattened batch dimension
- The `(4, 4, 4)` dimensions correspond to offsets `[-1, 0, 1, 2]` along each of the `(h, k, l)` axes

**Memory Footprint Example:**
- 1024×1024 detector: B = 1048576 → sub_Fhkl shape `(1048576, 4, 4, 4)` = ~268 MB at float32
- With oversample=2: B = 4194304 → ~1.07 GB at float32

### 2.3 Coordinate Arrays for Polynomial Evaluation

Following the C-code convention, we need coordinate arrays for each interpolation axis:
```
h_indices: (B, 4) -- values [h_flr-1, h_flr, h_flr+1, h_flr+2] for each query point
k_indices: (B, 4) -- values [k_flr-1, k_flr, k_flr+1, k_flr+2]
l_indices: (B, 4) -- values [l_flr-1, l_flr, l_flr+1, l_flr+2]
```

These will be used as the `xa`, `x1a`, `x2a`, `x3a` arguments to the vectorized polynomial helpers.

### 2.4 Query Point Shape

The interpolation target coordinates remain:
```
h, k, l: (B,) -- flattened query points
```

### 2.5 Output Shape

After tricubic interpolation:
```
F_cell: (B,) -- interpolated structure factor at each query point
```
This tensor is then reshaped to match the original input shape before returning.

### 2.6 Broadcasting Plan Diagram

```
Input Miller indices:
  h, k, l: (S, F) or (S, F, oversample²) or (phi, mosaic, S, F, ...)
         ↓ flatten leading dims
  h_flat, k_flat, l_flat: (B,)
         ↓ compute floor indices
  h_flr, k_flr, l_flr: (B,) int64
         ↓ build offset array
  offsets: (4,) = [-1, 0, 1, 2]
         ↓ broadcast to (B, 4) via unsqueeze + expand
  h_grid: (B, 4), k_grid: (B, 4), l_grid: (B, 4)
         ↓ advanced indexing into hkl_data[H, K, L]
  sub_Fhkl: (B, 4, 4, 4)
         ↓ vectorized polin3
  F_cell_flat: (B,)
         ↓ reshape to original
  F_cell: original_shape
```

**Critical Broadcasting Rule:** Use `h_flr.unsqueeze(-1) + offsets` to create `(B, 4)` grids; then use advanced indexing with proper broadcasting:
```python
sub_Fhkl = hkl_data[h_grid[:, :, None, None], k_grid[:, None, :, None], l_grid[:, None, None, :]]
```
This indexing pattern produces the required `(B, 4, 4, 4)` output.

---

## 3. C-Code Polynomial Semantics Mapping (Task B2)

### 3.1 Reference Implementation Analysis

The C-code implements Lagrange polynomial interpolation via three nested functions:
- `polint(xa[4], ya[4], x)` → 1D 4-point interpolation
- `polin2(x1a[4], x2a[4], ya[4][4], x1, x2)` → 2D via 4× 1D interpolations
- `polin3(x1a[4], x2a[4], x3a[4], ya[4][4][4], x1, x2, x3)` → 3D via 4× 2D interpolations

**Key Observation:** The nesting structure creates temporary arrays (`ymtmp[4]`) at each level. For vectorization, we must replicate this nesting while operating on batched tensors.

### 3.2 Lagrange Basis Functions (polint)

The 1D interpolation computes:
```
y = Σᵢ₌₀³ yᵢ × Lᵢ(x)
```
where the Lagrange basis function is:
```
Lᵢ(x) = ∏_{j≠i} (x - xⱼ) / (xᵢ - xⱼ)
```

**C-code expansion (from lines 4021–4029):**
```c
x0 = (x-xa[1])*(x-xa[2])*(x-xa[3])*ya[0]/((xa[0]-xa[1])*(xa[0]-xa[2])*(xa[0]-xa[3]));
x1 = (x-xa[0])*(x-xa[2])*(x-xa[3])*ya[1]/((xa[1]-xa[0])*(xa[1]-xa[2])*(xa[1]-xa[3]));
x2 = (x-xa[0])*(x-xa[1])*(x-xa[3])*ya[2]/((xa[2]-xa[0])*(xa[2]-xa[1])*(xa[2]-xa[3]));
x3 = (x-xa[0])*(x-xa[1])*(x-xa[2])*ya[3]/((xa[3]-xa[0])*(xa[3]-xa[1])*(xa[3]-xa[2]));
*y = x0+x1+x2+x3;
```

**Vectorization Strategy:**

Instead of computing each term separately, precompute Vandermonde-like weight matrices. For equally-spaced grids (offsets `[-1, 0, 1, 2]`), the denominators `(xᵢ - xⱼ)` are constants that can be cached.

**Proposed PyTorch Implementation:**
```python
def polint_vectorized(xa: torch.Tensor, ya: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
    """
    Vectorized 1D 4-point Lagrange interpolation.

    Args:
        xa: (B, 4) x-coordinates
        ya: (B, 4) y-values
        x: (B,) query points

    Returns:
        (B,) interpolated values
    """
    # Compute Lagrange basis: shape (B, 4)
    x_expanded = x.unsqueeze(-1)  # (B, 1)
    numerator = (x_expanded - xa).prod(dim=-1, keepdim=True)  # (B, 1) -- product over all (x - xa[j])

    # For each i, divide out the (x - xa[i]) term and compute denominator
    basis = torch.zeros_like(ya)  # (B, 4)
    for i in range(4):
        # Numerator for basis i: product of (x - xa[j]) for j ≠ i
        num_i = torch.ones_like(x)
        denom_i = torch.ones_like(x)
        for j in range(4):
            if j != i:
                num_i = num_i * (x - xa[:, j])
                denom_i = denom_i * (xa[:, i] - xa[:, j])
        basis[:, i] = num_i / denom_i

    # Interpolated value: weighted sum
    return (basis * ya).sum(dim=-1)
```

**Performance Note:** The double loop `for i in range(4): for j in range(4)` is acceptable because it operates on fixed small constants (4 iterations) and the inner operations are batched. Torch.compile will unroll these loops. Alternatively, we can precompute the weight matrices if `xa` follows a predictable pattern (e.g., always integer-spaced).

### 3.3 Nested 2D Interpolation (polin2)

The C-code (lines 4033–4042) implements:
```c
for (j=1; j<=4; j++) {
    polint(x2a, ya[j-1], x2, &ymtmp[j-1]);  // Interpolate along x2 for each row
}
polint(x1a, ymtmp, x1, y);  // Interpolate along x1
```

**Vectorization Strategy:**

Process all 4 rows in parallel, then apply final polint:
```python
def polin2_vectorized(x1a: torch.Tensor, x2a: torch.Tensor, ya: torch.Tensor,
                      x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
    """
    Vectorized 2D polynomial interpolation.

    Args:
        x1a: (B, 4) first dimension coordinates
        x2a: (B, 4) second dimension coordinates
        ya: (B, 4, 4) values at grid points
        x1, x2: (B,) query points

    Returns:
        (B,) interpolated values
    """
    # Interpolate along x2 for each of the 4 rows
    # Shape: ya[:, i, :] is (B, 4) for row i
    ymtmp = torch.stack([
        polint_vectorized(x2a, ya[:, i, :], x2) for i in range(4)
    ], dim=-1)  # (B, 4)

    # Interpolate along x1
    return polint_vectorized(x1a, ymtmp, x1)  # (B,)
```

**Gradient Flow:** The `torch.stack` operation preserves the computation graph; gradients backpropagate through both interpolation stages.

### 3.4 Nested 3D Interpolation (polin3)

The C-code (lines 4045–4058) nests polin2 calls:
```c
for (j=1; j<=4; j++) {
    polin2(x2a, x3a, &ya[j-1][0], x2, x3, &ymtmp[j-1]);
}
polint(x1a, ymtmp, x1, y);
```

**Vectorization Strategy:**

Stack 4 polin2 results and apply final polint:
```python
def polin3_vectorized(x1a: torch.Tensor, x2a: torch.Tensor, x3a: torch.Tensor,
                      ya: torch.Tensor, x1: torch.Tensor, x2: torch.Tensor, x3: torch.Tensor) -> torch.Tensor:
    """
    Vectorized 3D tricubic interpolation.

    Args:
        x1a: (B, 4) h-coordinates
        x2a: (B, 4) k-coordinates
        x3a: (B, 4) l-coordinates
        ya: (B, 4, 4, 4) structure factors at grid points
        x1, x2, x3: (B,) query points (h, k, l)

    Returns:
        (B,) interpolated F values
    """
    # Interpolate 4 2D slices
    ymtmp = torch.stack([
        polin2_vectorized(x2a, x3a, ya[:, i, :, :], x2, x3) for i in range(4)
    ], dim=-1)  # (B, 4)

    # Final 1D interpolation
    return polint_vectorized(x1a, ymtmp, x1)  # (B,)
```

### 3.5 Alternative: Precomputed Weights (Future Optimization)

For regularly-spaced grids (offsets = [-1, 0, 1, 2]), the Lagrange weights are constants. We could precompute a `(4, 4, 4, 4)` weight tensor and perform a single einsum:
```python
# Precompute once at init:
weights = compute_tricubic_weights()  # (4, 4, 4, 4)

# At runtime:
F_cell = torch.einsum('bhkl,hkl0->b', ya, weights)  # (B,)
```

**Decision:** Defer this optimization to Phase D or later. The nested loop approach is easier to verify against the C-code and should be sufficient for initial vectorization gains.

---

## 4. Gradient & Device Checklist (Task B3)

### 4.1 Differentiability Requirements

Per `docs/development/pytorch_runtime_checklist.md` and `arch.md` Section 15, the vectorized implementation MUST:

1. **Avoid `.item()` calls:** All intermediate tensors must remain on the computation graph
2. **Avoid `torch.linspace` with tensor endpoints:** Use manual arithmetic (`start + step * torch.arange(...)`)
3. **Use @property or functional patterns for derived quantities:** Never overwrite class attributes with detached values
4. **Maintain tensor inputs throughout:** No isinstance checks inside core methods

**Audit Points for Implementation:**

| Location | Check | Enforcement |
|----------|-------|-------------|
| Neighborhood gather | Ensure `h_flr`, `k_flr`, `l_flr` computed via `torch.floor(h)` (not `.long()` which detaches) | Use `.to(dtype=torch.long)` after ensuring gradients already stopped |
| Offset array | `offsets = torch.arange(-1, 3, device=device)` — no tensor endpoints | ✅ Already safe |
| Advanced indexing | `hkl_data[h_grid, k_grid, l_grid]` preserves gradients if `hkl_data` requires_grad | ✅ Native PyTorch |
| Polynomial helpers | All operations use tensor arithmetic (no scalar extraction) | Verify in Phase D implementation |

**Gradient Test Plan (Phase E):**
```python
def test_tricubic_vectorized_gradients():
    """Verify gradients flow through vectorized tricubic path."""
    cell_a = torch.tensor(100.0, requires_grad=True, dtype=torch.float64)
    config = CrystalConfig(cell_a=cell_a, ...)
    crystal = Crystal(config)

    # Batched input
    h = torch.tensor([[1.5, 2.3], [3.1, 4.7]], requires_grad=False)
    k = torch.tensor([[0.5, 1.2], [2.8, 3.5]], requires_grad=False)
    l = torch.tensor([[0.0, 0.5], [1.0, 1.5]], requires_grad=False)

    F_cell = crystal.get_structure_factor(h.flatten(), k.flatten(), l.flatten())
    loss = F_cell.sum()
    loss.backward()

    assert cell_a.grad is not None, "Gradient should flow to cell parameter"
    assert torch.autograd.gradcheck(
        lambda a: Crystal(CrystalConfig(cell_a=a, ...)).get_structure_factor(...),
        cell_a, eps=1e-6, atol=1e-4
    ), "Numerical gradient check failed"
```

### 4.2 Device Neutrality Requirements

Per Core Rule #16 (PyTorch Device & Dtype Neutrality), the implementation MUST:

1. **Accept tensors on any device:** CPU or CUDA
2. **Avoid hard-coded `.cpu()` or `.cuda()` calls:** Use `.to(device=other_tensor.device)` or `.type_as(other_tensor)`
3. **Ensure all intermediate tensors live on the same device:** No silent transfers
4. **Run smoke tests on both CPU and CUDA**

**Device Harmonization Strategy:**

```python
def _tricubic_interpolation(self, h, k, l):
    # Infer device from input tensors
    device = h.device
    dtype = h.dtype

    # Ensure offset array matches input device
    offsets = torch.arange(-1, 3, device=device, dtype=torch.long)

    # Ensure hkl_data is on the same device (move once at init if needed)
    if self.hkl_data is not None and self.hkl_data.device != device:
        # Warn and transfer (or enforce at init time)
        warnings.warn(f"HKL data on {self.hkl_data.device}, moving to {device}")
        self.hkl_data = self.hkl_data.to(device=device)

    # All subsequent operations inherit device from input tensors
    ...
```

**Smoke Test Plan (Phase E):**
```bash
# CPU test
env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py -k "cpu" -v

# CUDA test (when available)
env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py -k "cuda" -v

# Parametrized test covering both
@pytest.mark.parametrize("device", ["cpu", pytest.param("cuda", marks=pytest.mark.cuda)])
def test_tricubic_vectorized_device_neutral(device):
    if device == "cuda" and not torch.cuda.is_available():
        pytest.skip("CUDA not available")
    ...
```

### 4.3 Torch.compile Compatibility

The vectorized implementation should be torch.compile-friendly:

1. **No Python loops over batch dimensions:** Loop only over fixed small constants (e.g., 4 polynomial terms)
2. **No dynamic control flow based on tensor values:** Use `torch.where` for conditional logic
3. **No list comprehensions that create variable-length tensors:** Use `torch.stack` with fixed-length lists
4. **No in-place operations on graph-tracked tensors:** Use out-of-place ops (`.clone()` if needed)

**Known Issues:**

- **CUDA graphs + reshape views:** Per `docs/fix_plan.md` PERF-PYTORCH-004 Attempt #17, tensor views created by `.reshape()` inside compiled code can trigger "accessing tensor output of CUDAGraphs that has been overwritten" errors. If this occurs, use `.contiguous().clone()` instead of `.reshape()`.

**Compile Test Plan (Phase E):**
```python
@torch.compile(mode="reduce-overhead")
def compiled_get_structure_factor(crystal, h, k, l):
    return crystal.get_structure_factor(h, k, l)

def test_tricubic_vectorized_compile():
    """Verify torch.compile works with vectorized tricubic."""
    crystal = Crystal(...)
    h, k, l = torch.randn(100, device="cpu"), torch.randn(100), torch.randn(100)

    # Warm-up compile
    _ = compiled_get_structure_factor(crystal, h, k, l)

    # Measure speedup
    t0 = time.time()
    eager_result = crystal.get_structure_factor(h, k, l)
    eager_time = time.time() - t0

    t0 = time.time()
    compiled_result = compiled_get_structure_factor(crystal, h, k, l)
    compiled_time = time.time() - t0

    assert torch.allclose(eager_result, compiled_result, rtol=1e-5)
    print(f"Speedup: {eager_time / compiled_time:.2f}x")
```

---

## 5. Failure Modes & Mitigation

### 5.1 Out-of-Bounds Neighborhoods

**Scenario:** Query point near the edge of the HKL grid; some neighbors fall outside `[h_min, h_max]`.

**Current Behavior (scalar):** Emit one warning, set `self.interpolate = False`, return `default_F`.

**Vectorized Behavior (Phase C):**

1. **Detect OOB indices:** Check if any neighborhood indices fall outside bounds
2. **Emit warning once:** Use a flag to ensure warning prints only once
3. **Mask invalid points:** Create a boolean mask `(B,)` indicating which query points have valid neighborhoods
4. **Apply fallback:** For invalid points, use `default_F`; for valid points, proceed with interpolation

**Implementation Strategy:**
```python
# After computing h_grid, k_grid, l_grid (B, 4 each)
h_valid = (h_grid >= h_min) & (h_grid <= h_max)  # (B, 4)
k_valid = (k_grid >= k_min) & (k_grid <= k_max)  # (B, 4)
l_valid = (l_grid >= l_min) & (l_grid <= l_max)  # (B, 4)

# All 4 neighbors must be valid for each query point
valid_mask = h_valid.all(dim=-1) & k_valid.all(dim=-1) & l_valid.all(dim=-1)  # (B,)

if not valid_mask.all():
    if not self._interpolation_warning_shown:
        num_invalid = (~valid_mask).sum().item()
        print(f"WARNING: {num_invalid} query points have out-of-range neighborhoods")
        print("WARNING: using default_F for these points; disabling interpolation for remainder")
        self._interpolation_warning_shown = True
    self.interpolate = False

# Apply mask: gather only for valid points, use default_F for invalid
F_cell = torch.where(valid_mask, interpolated_values, default_F)
```

### 5.2 Memory Pressure (Large Batches)

**Scenario:** 1024×1024 detector with oversample=2 → B ≈ 4M → `sub_Fhkl` shape `(4M, 4, 4, 4)` ≈ 1 GB.

**Mitigation Options:**

1. **Mini-batching (if needed):** Split `B` into chunks (e.g., process 256k points at a time). Defer to Phase D if benchmarks show OOM issues.
2. **Lazy evaluation:** If only a subset of pixels need interpolation (e.g., ROI), filter before building neighborhoods.
3. **Mixed precision:** Use float16 for intermediate calculations (but verify numerical stability).

**Decision:** Monitor memory usage in Phase E benchmarks. If >80% GPU memory consumed, implement mini-batching in Phase D.

### 5.3 Numerical Stability (Division by Zero)

**Scenario:** Lagrange denominators `(xa[i] - xa[j])` could be zero if grid is degenerate.

**Mitigation:** Clamp denominators to a small epsilon (1e-10) to avoid NaNs:
```python
denom_i = (xa[:, i] - xa[:, j]).clamp_min(1e-10)
```

**Verification:** Add a test with nearly-degenerate grids and assert no NaNs/Infs in output.

---

## 6. Validation Strategy (Phase E Prerequisites)

### 6.1 Parity Tests

**AT-STR-002 (Structure Factors):** Run existing acceptance test after vectorization:
```bash
env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_str_002.py -v
```
**Expected:** Same correlation/RMSE as baseline (scalar interpolation).

**Golden Data:** Use C-code reference (`nanoBragg.c`) with identical parameters to generate comparison images:
```bash
nb-compare --resample --outdir reports/2025-10-vectorization/phase_e/nb_compare \
    -- -default_F 100 -cell 70 80 90 75 85 95 -lambda 1.0 -distance 100 -detpixels 512 -N 2
```

### 6.2 Gradient Tests

**Unit-level:** Verify `polint_vectorized`, `polin2_vectorized`, `polin3_vectorized` pass gradcheck.

**Integration-level:** Verify end-to-end gradients through `Simulator.run()` with interpolation enabled.

### 6.3 Performance Benchmarks

**Baseline vs. Vectorized:**
- Reuse `scripts/benchmarks/tricubic_baseline.py` with a `--mode vectorized` flag
- Measure CPU and CUDA warm/cold timings for 256², 512², 1024² detectors
- Target: ≥10× speedup for batched case vs. 100 scalar calls

**Expected Improvements:**
- CPU: Amortize overhead across batch; expect 5–10× improvement
- CUDA: Enable kernel fusion; expect 10–50× improvement (depends on memory bandwidth)

### 6.4 Regression Coverage

**New Unit Tests (Phase D):**
- `tests/test_tricubic_vectorized.py::test_polint_vectorized_matches_scalar`
- `tests/test_tricubic_vectorized.py::test_polin2_vectorized_matches_scalar`
- `tests/test_tricubic_vectorized.py::test_polin3_vectorized_vs_c_reference`
- `tests/test_tricubic_vectorized.py::test_batched_neighborhood_gather`
- `tests/test_tricubic_vectorized.py::test_oob_fallback_vectorized`

**Integration Tests (Phase E):**
- Existing `tests/test_at_str_002.py` (run with vectorized code)
- Add `tests/test_at_str_002.py::test_vectorized_vs_scalar_equivalence` (compare both paths)

---

## 7. Implementation Roadmap Summary

### Phase C: Neighborhood Gather (Plan Tasks C1–C3)

**Inputs:** `h, k, l` with arbitrary leading dims
**Outputs:** `sub_Fhkl` shape `(B, 4, 4, 4)`, coordinate arrays `(B, 4)` each

**Key Steps:**
1. Flatten inputs to `(B,)`
2. Compute `h_flr = torch.floor(h).to(dtype=torch.long)`
3. Build `h_grid = h_flr.unsqueeze(-1) + offsets` → `(B, 4)`
4. Use advanced indexing `hkl_data[h_grid[:, :, None, None], ...]` → `(B, 4, 4, 4)`
5. Detect OOB with masks; apply fallback logic

**Exit Criteria:**
- Unit test: `test_batched_neighborhood_gather` passes
- No Python loops over `B` dimension
- Device-neutral (runs on CPU and CUDA)

### Phase D: Polynomial Evaluation (Plan Tasks D1–D3)

**Inputs:** `sub_Fhkl (B, 4, 4, 4)`, query points `h, k, l (B,)`, coords `(B, 4)` each
**Outputs:** `F_cell (B,)` interpolated values

**Key Steps:**
1. Implement `polint_vectorized` using Lagrange basis
2. Implement `polin2_vectorized` stacking 4× `polint_vectorized`
3. Implement `polin3_vectorized` stacking 4× `polin2_vectorized`
4. Replace scalar helpers in `crystal.py` with vectorized versions
5. Add gradient tests

**Exit Criteria:**
- Unit tests: `test_polint_vectorized_matches_scalar`, etc. pass
- Gradient test: `test_tricubic_gradient` passes with `torch.autograd.gradcheck`
- Torch.compile compatibility: no graph breaks or CUDA errors

### Phase E: Validation (Plan Tasks E1–E3)

**Artifacts:**
- `phase_e/pytest.log` (regression tests)
- `phase_e/perf_results.json` (CPU/CUDA benchmarks)
- `phase_e/nb_compare/metrics.json` (C-code parity)
- `phase_e/summary.md` (consolidated results)

**Success Criteria:**
- AT-STR-002 passes with correlation ≥ 0.999
- Gradients flow correctly (gradcheck passes)
- CPU/CUDA speedup ≥ 10× vs. scalar baseline
- No memory regressions (GPU usage < 80%)

---

## 8. Symbols & Notation Glossary

| Symbol | Meaning | Units/Type |
|--------|---------|------------|
| `B` | Batch dimension (flattened from `S × F × ...`) | Integer |
| `S`, `F` | Slow/fast detector pixel indices | Integer |
| `h`, `k`, `l` | Miller indices (fractional) | Float (Å⁻¹ in reciprocal space) |
| `h_flr` | Floor of Miller index | Integer |
| `sub_Fhkl` | 4×4×4 neighborhood of structure factors | Float (electrons) |
| `F_cell` | Interpolated structure factor | Float (electrons) |
| `offsets` | Neighborhood offset array `[-1, 0, 1, 2]` | Integer |
| `xa`, `ya` | Coordinate and value arrays for `polint` | Float |
| `L` | Lagrange basis function | Dimensionless |
| `default_F` | Fallback structure factor | Float (electrons) |

---

## 9. Dependencies & Caching Strategy

### 9.1 HKL Data Device Management

**Current Issue:** `self.hkl_data` is allocated on the device where it was loaded (typically CPU). If a query comes in on CUDA, advanced indexing will fail or silently transfer data.

**Proposed Solution:**

1. **At Crystal initialization:** Store `hkl_data` on CPU (large arrays)
2. **At first interpolation call:** Detect device from input tensors; move `hkl_data` to that device if needed
3. **Cache the moved tensor:** Store a reference to avoid repeated transfers

```python
def _ensure_hkl_on_device(self, device):
    if self.hkl_data is not None:
        if self.hkl_data.device != device:
            self.hkl_data = self.hkl_data.to(device=device)
```

**Trade-off:** Increases memory if both CPU and CUDA runs occur (duplicate `hkl_data`). Acceptable for typical workflows where device is fixed per run.

### 9.2 Precomputed Weights (Future Optimization)

For grids with constant spacing (e.g., integer HKL indices), Lagrange weights are constant. Phase D could cache a `(4, 4, 4, 4)` weight tensor:

```python
self._tricubic_weights = self._compute_tricubic_weights()  # Called once at init

def _compute_tricubic_weights(self):
    """Precompute Lagrange weights for integer-spaced grid."""
    # offsets = [-1, 0, 1, 2]
    # For each interpolation point x ∈ [0, 1], compute Lagrange basis
    # (deferred to Phase D or later)
    ...
```

**Decision:** Defer unless Phase E benchmarks show significant overhead in polynomial evaluation (unlikely given batch sizes).

---

## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Memory OOM for large detectors | Medium | High (crashes) | Implement mini-batching in Phase D if needed |
| CUDA graph errors with reshape views | Low (already addressed in PERF-004) | Medium (runtime error) | Use `.contiguous().clone()` per fix plan |
| Numerical drift from C-code | Low (Lagrange formula is exact) | Medium (parity failure) | Extensive parity tests in Phase E |
| Gradient check failure | Low (all ops differentiable) | High (breaks optimization) | Unit-level gradcheck in Phase D before integration |
| Torch.compile graph breaks | Medium (nested control flow) | Low (perf only) | Smoke tests in Phase E; fallback to eager if needed |
| Device mismatch errors | Medium (HKL data on CPU, query on CUDA) | Medium (runtime error) | Explicit device harmonization at method entry |

---

## 11. Open Questions & Future Work

### 11.1 Deferred to Future Phases

1. **Absorption Vectorization (Phase F):** Similar shape design for `_apply_detector_absorption` with `(T, S, F)` tensors
2. **Weight Matrix Precomputation:** If polynomial evaluation becomes a bottleneck
3. **Mixed Precision Support:** Use float16 for intermediate calculations (verify numerics)
4. **JIT Compilation Tuning:** Investigate `torch.jit.script` as alternative to `torch.compile`

### 11.2 Cross-References for Phase C/D Implementation

**Files to modify:**
- `src/nanobrag_torch/models/crystal.py` lines 313–409 (`_tricubic_interpolation`)
- `src/nanobrag_torch/utils/physics.py` lines 315–445 (add vectorized helpers)
- `tests/test_tricubic_vectorized.py` (new file)

**Specs to validate:**
- `specs/spec-a-core.md` §4.3 (Interpolation behavior)
- `specs/spec-a-parallel.md` AT-STR-002 (Structure factor parity)

**Architecture alignment:**
- `docs/architecture/pytorch_design.md` §2.4 (Vectorization strategy)
- `docs/development/pytorch_runtime_checklist.md` (Device/dtype rules)

---

## 12. Appendix: Sample Broadcast Calculation

**Example:** 3×3 detector (B=9), compute neighborhoods

```python
import torch

# Input Miller indices (S=3, F=3)
h = torch.tensor([[1.2, 2.5, 3.8],
                  [0.5, 1.9, 2.3],
                  [3.1, 4.0, 5.2]])
k = torch.tensor([[0.3, 1.1, 2.7],
                  [1.5, 2.0, 3.9],
                  [0.8, 1.6, 2.4]])
l = torch.zeros_like(h)

# Flatten to (B,)
h_flat = h.flatten()  # [1.2, 2.5, 3.8, 0.5, 1.9, 2.3, 3.1, 4.0, 5.2]
k_flat = k.flatten()
l_flat = l.flatten()
B = h_flat.shape[0]  # 9

# Compute floor indices
h_flr = torch.floor(h_flat).to(dtype=torch.long)  # [1, 2, 3, 0, 1, 2, 3, 4, 5]

# Build offset array
offsets = torch.arange(-1, 3, dtype=torch.long)  # [-1, 0, 1, 2]

# Broadcast to (B, 4)
h_grid = h_flr.unsqueeze(-1) + offsets  # shape (9, 4)
# h_grid[0] = [0, 1, 2, 3]  (for h=1.2)
# h_grid[1] = [1, 2, 3, 4]  (for h=2.5)
# ...

# Simulate HKL data lookup (mock 10×10×10 grid)
hkl_data = torch.rand(10, 10, 10)

# Advanced indexing to build (B, 4, 4, 4) neighborhoods
k_grid = torch.floor(k_flat).to(dtype=torch.long).unsqueeze(-1) + offsets
l_grid = torch.floor(l_flat).to(dtype=torch.long).unsqueeze(-1) + offsets

sub_Fhkl = hkl_data[h_grid[:, :, None, None],
                    k_grid[:, None, :, None],
                    l_grid[:, None, None, :]]  # (9, 4, 4, 4)

print(f"sub_Fhkl shape: {sub_Fhkl.shape}")  # torch.Size([9, 4, 4, 4])
```

---

## Document Metadata

- **Author:** Ralph (nanoBragg PyTorch development loop)
- **Reviewed By:** Galph (supervisor)
- **Status:** DRAFT (awaiting Phase C implementation)
- **Next Actions:** Execute Phase C tasks (C1–C3) to implement batched neighborhood gather; update fix_plan.md with this memo's path and findings
- **Artifact Path:** `reports/2025-10-vectorization/phase_b/design_notes.md`

---

**End of Design Notes**
