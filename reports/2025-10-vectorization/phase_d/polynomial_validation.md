# Phase D1: Polynomial Validation Worksheet
# Tricubic Interpolation Vectorization

**Document Version:** 1.0
**Date:** 2025-10-07
**Git SHA:** (to be recorded after D2 implementation)
**Initiative:** VECTOR-TRICUBIC-001 (PERF-PYTORCH-004 backlog)
**Plan Reference:** `plans/active/vectorization.md` Phase D (tasks D1–D4)
**Design Reference:** `reports/2025-10-vectorization/phase_b/design_notes.md` Section 3
**Implementation Context:** `reports/2025-10-vectorization/phase_c/implementation_notes.md`

---

## Executive Summary

This worksheet defines the **tensor-shape contracts**, **C-code reference mappings**, and **validation strategy** for vectorizing the polynomial interpolation helpers (`polint`, `polin2`, `polin3`) that power tricubic structure factor interpolation. Phase C established batched neighborhood gathering producing `(B, 4, 4, 4)` subcubes; Phase D will enable these subcubes to be consumed without Python loops, unlocking GPU parallelism and torch.compile fusion.

**Key Deliverable:** A complete specification for implementing batched polynomial evaluation with clear input/output shapes, C-code mapping per CLAUDE Rule #11, gradient preservation guarantees, and device neutrality requirements. This worksheet serves as the binding contract between design (Phase B), infrastructure (Phase C), and implementation (Phase D2).

---

## 1. Context & Dependencies

### 1.1 Phase Handoff

**From Phase C (Completed):**
- Batched neighborhood gather produces `sub_Fhkl: (B, 4, 4, 4)` structure factor neighborhoods
- Coordinate arrays `h_indices, k_indices, l_indices: (B, 4)` ready for polynomial evaluation
- Shape assertions validate `(B, 4, 4, 4)` neighborhoods and device consistency
- Test harness `tests/test_tricubic_vectorized.py` validates gather infrastructure on CPU + CUDA
- **Blocker:** Batched path falls back to nearest-neighbor because polynomial helpers expect scalars

**To Phase D (This Worksheet):**
- Define exact tensor shapes for vectorized `polint`/`polin2`/`polin3`
- Map C-code Lagrange formulas to PyTorch batched operations
- Specify gradient validation strategy (gradcheck tolerances, float64 requirement)
- Plan device coverage (CPU + CUDA smoke tests, environment flags)
- Enumerate tap points for instrumentation if parity drifts
- Document masking strategy for out-of-bounds neighborhoods
- Record performance baseline expectations for Phase E comparison

**To Phase E (Validation):**
- Acceptance test selectors (`test_at_str_002.py::test_tricubic_interpolation_enabled`)
- Benchmark commands (`scripts/benchmarks/tricubic_baseline.py --mode vectorized`)
- Parity harness invocation (`nb-compare` with ROI for focal-plane correlation)
- Expected speedup metrics (≥10× vs. scalar baseline per Phase B design notes)

### 1.2 References

**Architecture & Design:**
- `specs/spec-a-core.md` §4.3 — Tricubic interpolation behavior specification
- `specs/spec-a-parallel.md` AT-STR-002 — Structure factor parity acceptance test
- `docs/architecture/pytorch_design.md` §§2.2–2.4 — Vectorization strategy, broadcast shapes
- `docs/development/pytorch_runtime_checklist.md` — Device/dtype neutrality guardrails
- `arch.md` Section 15 — Differentiability guidelines (no `.item()`, no `torch.linspace` with tensor endpoints)

**C-Code Implementation (Ground Truth):**
- `golden_suite_generator/nanoBragg.c` lines 4150–4158 — `polint` (1D Lagrange interpolation)
- `golden_suite_generator/nanoBragg.c` lines 4162–4171 — `polin2` (2D nested interpolation)
- `golden_suite_generator/nanoBragg.c` lines 4174–4187 — `polin3` (3D tricubic interpolation)

**Existing PyTorch Implementation (Scalar-Only):**
- `src/nanobrag_torch/utils/physics.py` lines 315–445 — Current `polint`/`polin2`/`polin3` helpers
- `src/nanobrag_torch/models/crystal.py` lines 355–464 — `_tricubic_interpolation` caller

**Phase B/C Artifacts:**
- `reports/2025-10-vectorization/phase_b/design_notes.md` §3 — Detailed C-code semantics mapping
- `reports/2025-10-vectorization/phase_c/implementation_notes.md` — Gather implementation + test results
- `reports/2025-10-vectorization/phase_c/gradient_smoke.log` — Current regression harness evidence

**Testing Infrastructure:**
- `tests/test_tricubic_vectorized.py` — Gather tests (CPU + CUDA device parametrisation)
- `tests/test_at_str_002.py` — Acceptance tests for interpolation correctness
- `reports/2025-10-vectorization/phase_d/collect.log` — pytest collection proof (5 tests)

---

## 2. Tensor Shape Design

### 2.1 Input Shapes (from Phase C Gather)

The vectorized polynomial helpers will consume the outputs of Phase C neighborhood gathering:

| Tensor | Shape | Description | Device/Dtype |
|--------|-------|-------------|--------------|
| `sub_Fhkl` | `(B, 4, 4, 4)` | Structure factor neighborhoods (64 values per query point) | Same as input Miller indices |
| `h_indices` | `(B, 4)` | h-coordinates: `[h_flr-1, h_flr, h_flr+1, h_flr+2]` for each query | Same as input |
| `k_indices` | `(B, 4)` | k-coordinates: `[k_flr-1, k_flr, k_flr+1, k_flr+2]` | Same as input |
| `l_indices` | `(B, 4)` | l-coordinates: `[l_flr-1, l_flr, l_flr+1, l_flr+2]` | Same as input |
| `h`, `k`, `l` | `(B,)` | Query points (fractional Miller indices) | Same as input |

**Critical Constraint:** All tensors must be on the **same device** and use compatible **dtypes** (typically float32 for performance, float64 for gradient validation). Phase C assertions enforce this.

### 2.2 Output Shape

| Tensor | Shape | Description | Constraints |
|--------|-------|-------------|-------------|
| `F_cell` | `(B,)` | Interpolated structure factors | `requires_grad` preserved from inputs |

**Reshape Contract:** The caller (`_tricubic_interpolation`) will reshape `F_cell` from `(B,)` back to the original input shape before returning.

### 2.3 Intermediate Shapes (Nested Interpolation)

Following the C-code nesting structure:

#### polint (1D Lagrange Interpolation)

```
Input:
  xa: (B, 4)  — x-coordinates
  ya: (B, 4)  — y-values
  x:  (B,)    — query points

Output:
  y:  (B,)    — interpolated values
```

#### polin2 (2D Interpolation via 4× polint)

```
Input:
  x1a: (B, 4)    — first dimension coordinates
  x2a: (B, 4)    — second dimension coordinates
  ya:  (B, 4, 4) — values at grid points
  x1:  (B,)      — query point (first dim)
  x2:  (B,)      — query point (second dim)

Intermediate:
  ymtmp: (B, 4)  — results of interpolating along x2 for each of 4 rows

Output:
  y: (B,)        — interpolated values
```

#### polin3 (3D Tricubic Interpolation via 4× polin2)

```
Input:
  x1a: (B, 4)       — h-coordinates
  x2a: (B, 4)       — k-coordinates
  x3a: (B, 4)       — l-coordinates
  ya:  (B, 4, 4, 4) — structure factors at grid points
  x1:  (B,)         — h query points
  x2:  (B,)         — k query points
  x3:  (B,)         — l query points

Intermediate:
  ymtmp: (B, 4)     — results of 4× polin2 calls (one per h-slice)

Output:
  y: (B,)           — interpolated F values
```

### 2.4 Worked Example: Mapping Detector Grid → Batch → Output

**Scenario:** 512×512 detector, no oversample, single phi/mosaic step

**Input Miller Indices:**
```
h, k, l: (512, 512)  — detector grid shape
```

**Phase C Flattening:**
```
B = 512 × 512 = 262,144
h_flat, k_flat, l_flat: (262144,)
```

**Phase C Gather Outputs:**
```
sub_Fhkl: (262144, 4, 4, 4)   — 64 neighbors per pixel
h_indices: (262144, 4)         — h-coordinates for interpolation
k_indices: (262144, 4)
l_indices: (262144, 4)
```

**Phase D polin3 Evaluation:**
```
F_cell_flat: (262144,)  — one interpolated F per pixel
```

**Caller Reshape:**
```
F_cell = F_cell_flat.reshape(512, 512)  — restore detector grid shape
```

**Memory Footprint:**
- `sub_Fhkl`: 262,144 × 64 × 4 bytes (float32) = ~67 MB
- `h/k/l_indices`: 3 × 262,144 × 4 × 4 bytes = ~12.6 MB
- `F_cell`: 262,144 × 4 bytes = ~1 MB
- **Total intermediate:** ~80 MB (well within GPU/CPU limits)

---

## 3. C-Code Reference Implementation (CLAUDE Rule #11)

### 3.1 polint (1D Lagrange Interpolation)

**C-Code Implementation Reference (from nanoBragg.c, lines 4150-4158):**

```c
void polint(double *xa, double *ya, double x, double *y)
{
        double x0,x1,x2,x3;
        x0 = (x-xa[1])*(x-xa[2])*(x-xa[3])*ya[0]/((xa[0]-xa[1])*(xa[0]-xa[2])*(xa[0]-xa[3]));
        x1 = (x-xa[0])*(x-xa[2])*(x-xa[3])*ya[1]/((xa[1]-xa[0])*(xa[1]-xa[2])*(xa[1]-xa[3]));
        x2 = (x-xa[0])*(x-xa[1])*(x-xa[3])*ya[2]/((xa[2]-xa[0])*(xa[2]-xa[1])*(xa[2]-xa[3]));
        x3 = (x-xa[0])*(x-xa[1])*(x-xa[2])*ya[3]/((xa[3]-xa[0])*(xa[3]-xa[1])*(xa[3]-xa[2]));
        *y = x0+x1+x2+x3;
}
```

**Lagrange Formula:**
For 4-point interpolation, the Lagrange basis function for point `i` is:
```
Lᵢ(x) = ∏_{j≠i} (x - xⱼ) / (xᵢ - xⱼ)
```

The interpolated value is:
```
y = Σᵢ₌₀³ yᵢ × Lᵢ(x)
```

**Vectorization Strategy:**

For each query point in the batch, compute all 4 Lagrange basis functions in parallel using broadcasting:

```python
def polint_vectorized(xa: torch.Tensor, ya: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
    """
    Vectorized 1D 4-point Lagrange interpolation.

    C-Code Implementation Reference (from nanoBragg.c, lines 4150-4158):
    ```c
    void polint(double *xa, double *ya, double x, double *y)
    {
            double x0,x1,x2,x3;
            x0 = (x-xa[1])*(x-xa[2])*(x-xa[3])*ya[0]/((xa[0]-xa[1])*(xa[0]-xa[2])*(xa[0]-xa[3]));
            x1 = (x-xa[0])*(x-xa[2])*(x-xa[3])*ya[1]/((xa[1]-xa[0])*(xa[1]-xa[2])*(xa[1]-xa[3]));
            x2 = (x-xa[0])*(x-xa[1])*(x-xa[3])*ya[2]/((xa[2]-xa[0])*(xa[2]-xa[1])*(xa[2]-xa[3]));
            x3 = (x-xa[0])*(x-xa[1])*(x-xa[2])*ya[3]/((xa[3]-xa[0])*(xa[3]-xa[1])*(xa[3]-xa[2]));
            *y = x0+x1+x2+x3;
    }
    ```

    Args:
        xa: (B, 4) x-coordinates
        ya: (B, 4) y-values
        x:  (B,) query points

    Returns:
        (B,) interpolated values
    """
    # Compute Lagrange basis functions for each i ∈ [0, 3]
    # For i=0: numerator = (x - xa[1]) * (x - xa[2]) * (x - xa[3])
    #          denominator = (xa[0] - xa[1]) * (xa[0] - xa[2]) * (xa[0] - xa[3])
    # Repeat for i=1,2,3

    # Implementation follows C-code term-by-term expansion
```

**IMPORTANT:** The docstring template MUST be included in the D2 implementation exactly as shown above, per CLAUDE Rule #11.

### 3.2 polin2 (2D Nested Interpolation)

**C-Code Implementation Reference (from nanoBragg.c, lines 4162-4171):**

```c
void polin2(double *x1a, double *x2a, double **ya, double x1, double x2, double *y)
{
        void polint(double *xa, double *ya, double x, double *y);
        int j;
        double ymtmp[4];
        for (j=1;j<=4;j++) {
                polint(x2a,ya[j-1],x2,&ymtmp[j-1]);
        }
        polint(x1a,ymtmp,x1,y);
}
```

**Vectorization Strategy:**

Process all 4 rows in parallel using `torch.stack`:

```python
def polin2_vectorized(x1a: torch.Tensor, x2a: torch.Tensor, ya: torch.Tensor,
                      x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
    """
    Vectorized 2D polynomial interpolation.

    C-Code Implementation Reference (from nanoBragg.c, lines 4162-4171):
    ```c
    void polin2(double *x1a, double *x2a, double **ya, double x1, double x2, double *y)
    {
            void polint(double *xa, double *ya, double x, double *y);
            int j;
            double ymtmp[4];
            for (j=1;j<=4;j++) {
                    polint(x2a,ya[j-1],x2,&ymtmp[j-1]);
            }
            polint(x1a,ymtmp,x1,y);
    }
    ```

    Args:
        x1a: (B, 4)    first dimension coordinates
        x2a: (B, 4)    second dimension coordinates
        ya:  (B, 4, 4) values at grid points
        x1:  (B,)      query point (first dim)
        x2:  (B,)      query point (second dim)

    Returns:
        (B,) interpolated values
    """
    # Interpolate along x2 for each of the 4 rows
    # Stack results into ymtmp: (B, 4)
    # Final polint along x1 dimension
```

### 3.3 polin3 (3D Tricubic Interpolation)

**C-Code Implementation Reference (from nanoBragg.c, lines 4174-4187):**

```c
void polin3(double *x1a, double *x2a, double *x3a, double ***ya, double x1,
        double x2, double x3, double *y)
{
        void polint(double *xa, double ya[], double x, double *y);
        void polin2(double *x1a, double *x2a, double **ya, double x1,double x2, double *y);
        void polin1(double *x1a, double *ya, double x1, double *y);
        int j;
        double ymtmp[4];

        for (j=1;j<=4;j++) {
            polin2(x2a,x3a,&ya[j-1][0],x2,x3,&ymtmp[j-1]);
        }
        polint(x1a,ymtmp,x1,y);
}
```

**Vectorization Strategy:**

Stack 4 polin2 results (one per h-slice) and apply final polint:

```python
def polin3_vectorized(x1a: torch.Tensor, x2a: torch.Tensor, x3a: torch.Tensor,
                      ya: torch.Tensor, x1: torch.Tensor, x2: torch.Tensor, x3: torch.Tensor) -> torch.Tensor:
    """
    Vectorized 3D tricubic interpolation.

    C-Code Implementation Reference (from nanoBragg.c, lines 4174-4187):
    ```c
    void polin3(double *x1a, double *x2a, double *x3a, double ***ya, double x1,
            double x2, double x3, double *y)
    {
            void polint(double *xa, double ya[], double x, double *y);
            void polin2(double *x1a, double *x2a, double **ya, double x1,double x2, double *y);
            void polin1(double *x1a, double *ya, double x1, double *y);
            int j;
            double ymtmp[4];

            for (j=1;j<=4;j++) {
                polin2(x2a,x3a,&ya[j-1][0],x2,x3,&ymtmp[j-1]);
            }
            polint(x1a,ymtmp,x1,y);
    }
    ```

    Args:
        x1a: (B, 4)       h-coordinates
        x2a: (B, 4)       k-coordinates
        x3a: (B, 4)       l-coordinates
        ya:  (B, 4, 4, 4) structure factors at grid points
        x1:  (B,)         h query points
        x2:  (B,)         k query points
        x3:  (B,)         l query points

    Returns:
        (B,) interpolated F values
    """
    # Interpolate 4 2D slices (one per h index)
    # Stack results into ymtmp: (B, 4)
    # Final polint along h dimension
```

---

## 4. Gradient Validation Strategy

### 4.1 Differentiability Requirements

Per `arch.md` Section 15 and `docs/development/pytorch_runtime_checklist.md`, vectorized polynomial helpers MUST:

1. **Preserve Computation Graph:** All operations use tensor arithmetic; no `.item()`, `.numpy()`, or `.detach()` calls
2. **Avoid Non-Differentiable Functions:** No `torch.linspace` with tensor endpoints (known PyTorch limitation)
3. **Handle Division Safely:** Clamp denominators to avoid NaN/Inf from near-zero values
4. **Maintain `requires_grad`:** Output tensors inherit gradient tracking from inputs

### 4.2 Gradient Test Plan

**Unit-Level Tests (D3):**

Test each vectorized helper independently with `torch.autograd.gradcheck`:

```python
def test_polint_vectorized_gradients():
    """Verify gradients flow through vectorized 1D interpolation."""
    xa = torch.tensor([[0.0, 1.0, 2.0, 3.0]], requires_grad=False, dtype=torch.float64)
    ya = torch.tensor([[1.0, 2.0, 4.0, 8.0]], requires_grad=True, dtype=torch.float64)
    x = torch.tensor([1.5], requires_grad=True, dtype=torch.float64)

    # Gradcheck w.r.t. x
    assert torch.autograd.gradcheck(
        lambda x_: polint_vectorized(xa, ya, x_),
        x,
        eps=1e-6,
        atol=1e-4
    )

    # Gradcheck w.r.t. ya
    assert torch.autograd.gradcheck(
        lambda ya_: polint_vectorized(xa, ya_, x),
        ya,
        eps=1e-6,
        atol=1e-4
    )
```

**Expected Tolerances (float64):**
- `eps=1e-6` — finite difference step size
- `atol=1e-4` — absolute tolerance for numerical vs. analytical gradients
- `rtol=1e-3` — relative tolerance (default)

**Integration-Level Test (D3):**

Verify end-to-end gradients through `_tricubic_interpolation`:

```python
def test_tricubic_vectorized_end_to_end_gradients():
    """Verify gradients flow through batched tricubic path."""
    cell_a = torch.tensor(100.0, requires_grad=True, dtype=torch.float64)
    config = CrystalConfig(cell_a=cell_a, ...)
    crystal = Crystal(config)

    # Batched input
    h = torch.tensor([1.5, 2.3, 3.1], dtype=torch.float64)
    k = torch.tensor([0.5, 1.2, 2.8], dtype=torch.float64)
    l = torch.tensor([0.0, 0.5, 1.0], dtype=torch.float64)

    F_cell = crystal.get_structure_factor(h, k, l)
    loss = F_cell.sum()
    loss.backward()

    assert cell_a.grad is not None, "Gradient should flow to cell parameter"
    assert not torch.isnan(cell_a.grad).any(), "Gradients must not be NaN"
```

### 4.3 Gradient Failure Modes & Mitigation

| Failure Mode | Symptom | Mitigation |
|--------------|---------|------------|
| Division by zero in Lagrange denominators | `grad = NaN` | Clamp denominators: `denom.clamp_min(1e-10)` |
| Detached intermediate tensors | `grad = None` | Audit all operations; ensure no `.item()` calls |
| `torch.linspace` with tensor coords | `grad = None` for endpoints | Use manual arithmetic: `xa[:, i]` indexing |
| In-place operations on tracked tensors | Runtime error | Use out-of-place ops: `+` not `+=` |

---

## 5. Device & Dtype Neutrality Plan

### 5.1 Device Handling

Per Core Rule #16 (PyTorch Device & Dtype Neutrality):

**Requirements:**
1. Accept tensors on any device (CPU, CUDA)
2. All intermediate tensors must live on the **same device** as inputs
3. No hard-coded `.cpu()` or `.cuda()` calls
4. Infer device from input tensors

**Implementation Pattern:**

```python
def polint_vectorized(xa, ya, x):
    device = xa.device  # Infer from input
    dtype = xa.dtype

    # All intermediate tensors inherit device/dtype
    # No explicit .to(device=...) calls needed if using tensor ops
```

**Phase C Infrastructure:**
- Offsets array: Created with `device=self.device` (line 373 in crystal.py)
- Coordinate grids: Inherit device from flattened Miller indices
- Neighborhoods: Gathered via advanced indexing (preserves device)

**Prohibition:** Do NOT call `.to(device="cpu")` or `.to(device="cuda")` inside polynomial helpers.

### 5.2 Dtype Handling

**Default Precision:** float32 (performance-optimized, per `arch.md` Section 14)

**Gradient Testing Precision:** float64 (required for `torch.autograd.gradcheck` numerical stability)

**Test Strategy:**

```python
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_polint_vectorized_dtype_neutral(dtype):
    """Verify polint works with different dtypes."""
    xa = torch.tensor([[0.0, 1.0, 2.0, 3.0]], dtype=dtype)
    ya = torch.tensor([[1.0, 2.0, 4.0, 8.0]], dtype=dtype)
    x = torch.tensor([1.5], dtype=dtype)

    result = polint_vectorized(xa, ya, x)
    assert result.dtype == dtype
    assert not torch.isnan(result).any()
```

### 5.3 CPU + CUDA Smoke Tests

**Requirement:** Run polynomial tests on both CPU and CUDA before marking Phase D complete.

**Parametrised Test Pattern:**

```python
@pytest.mark.parametrize("device", [
    "cpu",
    pytest.param("cuda", marks=pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available"))
])
def test_polin3_vectorized_device_neutral(device):
    """Verify polin3 works on CPU and CUDA."""
    ya = torch.rand(10, 4, 4, 4, device=device)
    x1a = torch.arange(4, device=device, dtype=torch.float32)
    # ... rest of test
```

**Commands (Phase D4):**

```bash
# CPU test
env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py -k "poly" -v

# CUDA test (when available)
env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py -k "poly and cuda" -v
```

**Artifact Storage:**
- `reports/2025-10-vectorization/phase_d/pytest_cpu.log`
- `reports/2025-10-vectorization/phase_d/pytest_cuda.log`

---

## 6. Masking Strategy for Out-of-Bounds Neighborhoods

### 6.1 Current Behavior (Phase C)

Phase C detects OOB neighborhoods **before** gathering:

```python
if not valid_mask.all():
    if not self._interpolation_warning_shown:
        num_invalid = (~valid_mask).sum().item()
        print(f"WARNING: {num_invalid} query points have out-of-range neighborhoods")
        print("WARNING: using default_F for these points; disabling interpolation for remainder")
        self._interpolation_warning_shown = True
    self.interpolate = False
```

**Consequence:** Once any OOB point is detected, interpolation is **globally disabled** for the rest of the run.

### 6.2 Phase D Masking Requirements

**Goal:** Preserve existing OOB semantics while enabling batched polynomial evaluation.

**Strategy:**

1. **OOB Detection:** Already handled by Phase C (before polynomial call)
2. **Polynomial Input:** Only valid neighborhoods reach `polin3_vectorized`
3. **Fallback Path:** Invalid points use `default_F` (applied in caller)

**No Additional Masking Needed in Polynomial Helpers:** The helpers assume all input neighborhoods are valid. The caller (`_tricubic_interpolation`) applies the mask via `torch.where`:

```python
if valid_mask.all():
    # All points valid → call polin3_vectorized
    F_cell = polin3_vectorized(h_indices, k_indices, l_indices, sub_Fhkl, h_flat, k_flat, l_flat)
else:
    # Mixed valid/invalid → apply mask
    F_cell_valid = polin3_vectorized(h_indices[valid_mask], ...)
    F_cell = torch.where(valid_mask, F_cell_valid_padded, default_F)
```

**Alternative (Simpler):** Since Phase C already disables interpolation globally on first OOB, the batched path may never encounter mixed masks. Verify this in Phase D2 implementation.

### 6.3 NaN Handling

**Potential Issue:** Lagrange denominators `(xa[i] - xa[j])` could be zero if grid is degenerate.

**Mitigation:**

```python
# In polint_vectorized
denom_i = (xa[:, i] - xa[:, j]).clamp_min(1e-10)  # Prevent division by zero
```

**Test Case (Phase D3):**

```python
def test_polint_vectorized_handles_near_degenerate_grids():
    """Verify no NaNs with nearly-equal grid points."""
    xa = torch.tensor([[0.0, 0.0 + 1e-12, 1.0, 2.0]])  # Near-duplicate point
    ya = torch.tensor([[1.0, 2.0, 3.0, 4.0]])
    x = torch.tensor([0.5])

    result = polint_vectorized(xa, ya, x)
    assert not torch.isnan(result).any()
    assert not torch.isinf(result).any()
```

---

## 7. Instrumentation & Tap Points

### 7.1 Purpose

If parity drifts between C-code and PyTorch batched polynomials, we need **tap points** to log intermediate values for comparison.

### 7.2 Proposed Tap Points

**polint (1D):**
- Input: `xa[0], ya[0], x` (first query point in batch)
- Lagrange basis weights: `basis[0, :]` (4 values)
- Output: `y[0]`

**polin2 (2D):**
- Input: `ya[0, :, :]` (first 4×4 slice)
- Intermediate: `ymtmp[0, :]` (4 values after x2 interpolation)
- Output: `y[0]`

**polin3 (3D):**
- Input: `ya[0, :, :, :]` (first 4×4×4 neighborhood)
- Intermediate: `ymtmp[0, :]` (4 values after x2/x3 interpolation)
- Output: `y[0]`

### 7.3 Instrumentation Example

```python
def polin3_vectorized(...):
    # ... implementation ...

    # TAP POINT (conditional, disabled by default)
    if os.environ.get("NANOBRAG_DEBUG_POLIN3") == "1":
        print(f"TRACE_PY: polin3 input ya[0, 0, 0, :] = {ya[0, 0, 0, :].tolist()}")
        print(f"TRACE_PY: polin3 ymtmp[0, :] = {ymtmp[0, :].tolist()}")
        print(f"TRACE_PY: polin3 output y[0] = {y[0].item()}")

    return y
```

**C-Code Equivalent:**

```c
// In nanoBragg.c polin3
if (getenv("NANOBRAG_DEBUG_POLIN3")) {
    printf("TRACE_C: polin3 input ya[0][0][0] = %.15g\n", ya[0][0][0]);
    // ... more taps
}
```

**Activation (Phase E debugging):**

```bash
export NANOBRAG_DEBUG_POLIN3=1
pytest tests/test_at_str_002.py -v
```

### 7.4 Tap Point Storage

If tap logging grows complex, store schemas in:
```
reports/2025-10-vectorization/phase_d/tap_points.md
```

**Decision:** Defer tap point implementation to Phase E (parity debugging) unless D3 unit tests reveal discrepancies.

---

## 8. Performance Baseline & Expected Metrics

### 8.1 Current Baseline (Phase A)

**From `reports/2025-10-vectorization/phase_a/tricubic_baseline.md`:**
- CPU: ~1.4 ms/call (100 scalar calls in benchmark)
- CUDA: ~5.5 ms/call (100 scalar calls in benchmark)

**Total for 100 calls:**
- CPU: 140 ms
- CUDA: 550 ms

**Bottleneck:** External Python loop over query points; each call has fixed overhead.

### 8.2 Expected Post-Vectorization Performance (Phase E Target)

**Assumption:** Batched polynomial evaluation amortizes overhead across B points.

**Target Speedup:**
- **CPU:** 5–10× improvement (14–28 ms for 100 batched points vs. 140 ms for 100 scalar calls)
- **CUDA:** 10–50× improvement (11–55 ms vs. 550 ms) — depends on kernel fusion via torch.compile

**Measurement Command (Phase E):**

```bash
python scripts/benchmarks/tricubic_baseline.py \
    --mode vectorized \
    --outdir reports/2025-10-vectorization/phase_e/perf \
    --device cpu cuda
```

**Expected Artifacts:**
- `phase_e/perf/tricubic_baseline_results.json` — Before/after timing comparison
- `phase_e/perf_summary.md` — Speedup analysis and bottleneck identification

### 8.3 Torch.compile Compatibility

**Goal:** Ensure vectorized polynomial helpers are compile-friendly (no graph breaks).

**Test (Phase E):**

```python
@torch.compile(mode="reduce-overhead")
def compiled_polin3(x1a, x2a, x3a, ya, x1, x2, x3):
    return polin3_vectorized(x1a, x2a, x3a, ya, x1, x2, x3)

def test_polin3_compiles_without_graph_breaks():
    """Verify torch.compile works with vectorized polin3."""
    ya = torch.rand(100, 4, 4, 4, device="cpu")
    # ... setup inputs ...

    # Warm-up compile
    _ = compiled_polin3(x1a, x2a, x3a, ya, x1, x2, x3)

    # Verify no exceptions during compiled execution
    result = compiled_polin3(x1a, x2a, x3a, ya, x1, x2, x3)
    assert result.shape == (100,)
```

**Known Issue:** Per `docs/fix_plan.md` PERF-PYTORCH-004 Attempt #17, CUDA graphs + `.reshape()` can trigger "accessing tensor output of CUDAGraphs that has been overwritten" errors. If this occurs, use `.contiguous().clone()` instead.

---

## 9. Test Coverage Plan (Phase D3)

### 9.1 Unit Tests (New)

**File:** `tests/test_tricubic_vectorized.py` (extend existing TestTricubicGather class)

**New Test Class:** `TestTricubicPolynomials`

| Test Name | Purpose | Coverage |
|-----------|---------|----------|
| `test_polint_vectorized_matches_scalar` | Verify batched polint produces same results as scalar loop | Scalar equivalence, B=1 and B>1 |
| `test_polint_vectorized_gradients` | Verify gradcheck passes for polint | Gradient flow w.r.t. x and ya |
| `test_polin2_vectorized_matches_scalar` | Verify batched polin2 vs. scalar | 2D interpolation correctness |
| `test_polin2_vectorized_gradients` | Verify gradcheck passes for polin2 | Gradient flow end-to-end |
| `test_polin3_vectorized_vs_c_reference` | Verify polin3 matches C-code output | Parity with golden C values |
| `test_polin3_vectorized_gradients` | Verify gradcheck passes for polin3 | Gradient flow for tricubic |
| `test_polynomial_device_neutrality[cpu]` | Verify CPU execution | Device consistency |
| `test_polynomial_device_neutrality[cuda]` | Verify CUDA execution | Device consistency |
| `test_polynomial_dtype_preservation` | Verify float32/float64 handling | Dtype compatibility |
| `test_polynomial_handles_near_degenerate` | Verify NaN handling for edge cases | Numerical stability |

**Total New Tests:** 10 (in addition to existing 5 gather tests)

### 9.2 Integration Tests (Regression)

**Existing Tests (Must Still Pass):**
- `tests/test_at_str_002.py::test_tricubic_interpolation_enabled`
- `tests/test_at_str_002.py::test_tricubic_out_of_bounds_fallback`
- `tests/test_at_str_002.py::test_auto_enable_interpolation`

**Expected Behavior Change:**
- Phase C: Batched inputs → fall back to nearest-neighbor (warning)
- Phase D: Batched inputs → use `polin3_vectorized` (no warning)

### 9.3 Acceptance Tests (Phase E)

**File:** `tests/test_at_str_002.py`

**Command:**

```bash
env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_str_002.py -v
```

**Expected:** All tests pass with correlation ≥ 0.999 (same as scalar path).

---

## 10. Open Questions & Decisions for Supervisor Sign-Off

### 10.1 Resolved in This Worksheet

✅ **Tensor shapes:** Fully specified for all helpers (polint/polin2/polin3)
✅ **C-code mapping:** CLAUDE Rule #11 templates ready for docstrings
✅ **Gradient strategy:** gradcheck plan with float64 + tolerances defined
✅ **Device coverage:** CPU + CUDA parametrised tests planned
✅ **Masking:** OOB handling delegated to Phase C caller (no polynomial changes)
✅ **Tap points:** Conditional logging strategy defined for Phase E debugging

### 10.2 Open Questions for Supervisor Review

1. **Mini-Batching:** Should Phase D implement chunking for B>1M, or defer to Phase E if OOM occurs?
   - **Recommendation:** Defer. Test with 2048² detector (B=4M) in Phase E first.

2. **Precomputed Weights:** Should we cache Lagrange weight matrices for integer-spaced grids?
   - **Recommendation:** Defer to Phase F. Nested loop approach easier to verify first.

3. **Torch.compile Mode:** Use `"reduce-overhead"`, `"max-autotune"`, or skip compile in Phase D?
   - **Recommendation:** Test with `"reduce-overhead"` in Phase E; skip in D2 implementation.

4. **Complex HKL Interpolation:** C-code supports complex structure factors; PyTorch path currently real-only.
   - **Recommendation:** Out of scope for Phase D; add TODO for future work.

5. **Alternative Interpolation Schemes:** Spec mentions cubic splines; C-code uses Lagrange. Unify?
   - **Recommendation:** Out of scope. Lagrange is spec'd and C-code ground truth.

---

## 11. Exit Criteria for Phase D1 (This Worksheet)

**Phase D1 Complete When:**
- [x] This worksheet (`polynomial_validation.md`) authored with all required sections
- [x] Tensor shapes documented with worked examples
- [x] C-code references quoted exactly (lines 4150–4187) per CLAUDE Rule #11
- [x] Gradient validation strategy specified (gradcheck commands, tolerances)
- [x] Device coverage plan defined (CPU + CUDA smoke tests)
- [x] Tap point schema outlined for future debugging
- [x] Performance baseline expectations recorded from Phase A
- [x] Test coverage plan enumerated (10 new unit tests + regression)
- [x] `pytest --collect-only -q tests/test_tricubic_vectorized.py` output captured in `reports/2025-10-vectorization/phase_d/collect.log`
- [x] Worksheet reviewed by supervisor (galph) — **PENDING**

**Next Phase D2:** Implement `polint_vectorized`, `polin2_vectorized`, `polin3_vectorized` in `utils/physics.py` following this worksheet's specifications.

---

## 12. Configuration Knobs & Environment Flags

### 12.1 Environment Variables

**Required for All Tests:**
- `KMP_DUPLICATE_LIB_OK=TRUE` — Prevent MKL library conflicts

**Optional for Debugging:**
- `NANOBRAG_DEBUG_POLIN3=1` — Enable tap point logging
- `TORCH_COMPILE_DEBUG=1` — Debug torch.compile graph breaks

**Future Performance Tuning:**
- `TORCH_COMPILE_MODE=reduce-overhead` — torch.compile strategy
- `OMP_NUM_THREADS=8` — CPU parallelism for NumPy/PyTorch

### 12.2 Runtime Configuration

**Dtype Override (Phase E):**

```python
# Force float64 for gradient validation
F_cell = crystal.get_structure_factor(h.to(dtype=torch.float64), ...)
```

**Device Override (Phase E):**

```python
# Force CUDA execution
F_cell = crystal.get_structure_factor(h.to(device="cuda"), ...)
```

**Torch.compile Caching:**

Per `docs/fix_plan.md` PERF-PYTORCH-004, compiled kernels are cached in `~/.cache/torch/inductor/`. Phase E should document cache behavior.

---

## 13. Coordination with Other Plans

### 13.1 PERF-PYTORCH-004 (Performance Initiative)

**Dependency:** Phase D vectorization unblocks PERF-004 Phase C benchmarking tasks.

**Hand-off:** Once Phase E validates speedup, PERF-004 can proceed with:
- C5: Weighted-source parity memo
- C8/C9: Pixel-grid and rotated-vector cost probes
- D5/D6/D7: Caching work

**Artifact Link:** `reports/benchmarks/20250930-165726-compile-cache/analysis.md` identifies `polin3` as hotspot.

### 13.2 CLI-FLAGS-003 (CLI Parity)

**Dependency:** CLI dtype flag (`-dtype float64`) should work with vectorized tricubic.

**Verification (Phase E):** Run acceptance tests with `-dtype float64` flag and ensure no regressions.

### 13.3 AT-TIER2-GRADCHECK (Gradient Tests)

**Dependency:** Phase D gradient tests contribute to AT-TIER2 coverage.

**Hand-off:** Once Phase D3 completes, update `docs/fix_plan.md` AT-TIER2 Attempts History with polynomial gradcheck evidence.

---

## 14. Documentation Updates (Phase D4 & Phase G)

### 14.1 Phase D4 (Implementation Loop)

**Update After D2 Implementation:**
- `src/nanobrag_torch/utils/physics.py` — Add vectorized polynomial helpers with C-code docstrings
- `src/nanobrag_torch/models/crystal.py` — Update `_tricubic_interpolation` to use batched helpers
- `tests/test_tricubic_vectorized.py` — Add `TestTricubicPolynomials` class with 10 new tests

**Capture Artifacts:**
- `reports/2025-10-vectorization/phase_d/pytest_cpu.log` — Full test run on CPU
- `reports/2025-10-vectorization/phase_d/pytest_cuda.log` — Full test run on CUDA (if available)
- `reports/2025-10-vectorization/phase_d/implementation_notes.md` — Summary of D2 changes (like Phase C)

### 14.2 Phase G (Documentation Handoff)

**Update After Phase E Validation:**
- `docs/development/pytorch_runtime_checklist.md` — Add tricubic vectorization lessons learned
- `docs/architecture/pytorch_design.md` — Document polynomial broadcasting patterns
- `arch.md` — Update ADR-11 (Full Tensor Vectorization) to include tricubic interpolation
- `CLAUDE.md` — Add one-line note about vectorization requirement for future structure factor work

---

## 15. Summary & Hand-off to Phase D2

**This Worksheet Provides:**
- ✅ Complete tensor-shape specification for polint/polin2/polin3
- ✅ Exact C-code references (lines 4150–4187) ready for docstring insertion
- ✅ Gradient validation plan with gradcheck commands and tolerances
- ✅ Device coverage strategy (CPU + CUDA smoke tests)
- ✅ Tap point inventory for future parity debugging
- ✅ Performance baseline from Phase A and expected Phase E targets
- ✅ Test coverage plan (10 new unit tests + regression)
- ✅ Masking/NaN handling strategies
- ✅ Open questions documented for supervisor triage

**Phase D2 Implementation Checklist:**
1. Copy C-code docstring templates from Section 3 into new helpers
2. Implement `polint_vectorized` following shape spec in Section 2.3
3. Implement `polin2_vectorized` stacking 4× polint results
4. Implement `polin3_vectorized` stacking 4× polin2 results
5. Update `crystal.py` to call vectorized helpers for B>1
6. Add 10 unit tests from Section 9.1 to `test_tricubic_vectorized.py`
7. Run CPU + CUDA smoke tests and capture logs
8. Update fix_plan.md Attempts History with metrics + artifact paths

**Blocking Conditions for Phase D2 Start:**
- ✅ Phase C gather infrastructure complete (verified in Phase C3)
- ✅ Worksheet reviewed by supervisor (galph) — **PENDING**
- ⬜ No missing C-code references or undefined tensor shapes (self-audit complete)

**Next Loop (D2):** Implement batched polynomial helpers in `utils/physics.py` and integrate into `crystal.py`, following this worksheet as the binding specification.

---

## Document Metadata

- **Author:** Ralph (nanoBragg PyTorch development loop)
- **Reviewed By:** Galph (supervisor) — **PENDING**
- **Status:** DRAFT (Phase D1 deliverable; awaiting supervisor approval for D2 start)
- **Artifact Path:** `reports/2025-10-vectorization/phase_d/polynomial_validation.md`
- **Collection Log:** `reports/2025-10-vectorization/phase_d/collect.log` (5 tests collected)
- **Next Actions:**
  1. Supervisor reviews worksheet for completeness and technical accuracy
  2. If approved, proceed to Phase D2 implementation
  3. If changes needed, update worksheet and re-submit

---

**End of Phase D1 Polynomial Validation Worksheet**
