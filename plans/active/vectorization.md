## Vectorization Refactoring Plan for `nanobrag-torch`

### 1. Objective

This plan outlines the strategy to refactor two performance-critical, non-vectorized components in the `nanobrag-torch` simulator: **detector absorption** and **Fhkl tricubic interpolation**. The goal is to replace the current Python-level loops with fully vectorized PyTorch tensor operations to significantly improve performance, especially on GPUs, and to enable the practical use of tricubic interpolation for full-frame simulations.

### 2. Task 1: Vectorize Detector Absorption (`_apply_detector_absorption`)

**Current State:** The implementation in `src/nanobrag_torch/simulator.py` uses a Python `for` loop to iterate over `thicksteps` when `oversample_thick=True`. This is a major performance bottleneck as it executes expensive `torch.exp()` operations sequentially for every pixel on the detector.

**Proposed Solution:** Eliminate the Python loop by creating a new tensor dimension for the thickness layers. This will allow the capture fraction for all layers and all pixels to be computed in a single, parallelized operation.

#### 2.1. Implementation Steps

The refactoring will be applied to the `_apply_detector_absorption` method in `src/nanobrag_torch/simulator.py`.

1.  **Create a Layer Index Tensor:**
    Instead of a Python loop `for t in range(thicksteps):`, create a 1D tensor representing the layer indices.
    ```python
    t_indices = torch.arange(thicksteps, device=intensity.device, dtype=intensity.dtype)
    ```

2.  **Expand Tensors for Broadcasting:**
    To perform the calculation in parallel, expand the dimensions of the `t_indices` and `parallax` tensors to make them broadcast-compatible.
    *   `t_indices` (shape `(T,)`) becomes `t_expanded` (shape `(T, 1, 1)`).
    *   `parallax` (shape `(S, F)`) becomes `parallax_expanded` (shape `(1, S, F)`).
    *   `intensity` (shape `(S, F)`) becomes `intensity_expanded` (shape `(1, S, F)`).
    ```python
    t_expanded = t_indices.reshape(-1, 1, 1)
    parallax_expanded = parallax.unsqueeze(0)
    intensity_expanded = intensity.unsqueeze(0)
    ```

3.  **Vectorize Capture Fraction Calculation:**
    Compute the capture fractions for all layers and pixels in a single operation. The formula is `exp(−t·Δz·μ/ρ) − exp(−(t+1)·Δz·μ/ρ)`.
    ```python
    exp_start_all = torch.exp(-t_expanded * delta_z * mu / parallax_expanded)
    exp_end_all = torch.exp(-(t_expanded + 1) * delta_z * mu / parallax_expanded)
    capture_fractions = exp_start_all - exp_end_all  # Resulting shape: (T, S, F)
    ```

4.  **Apply Fractions and Sum:**
    Multiply the expanded intensity tensor by the capture fractions and sum along the thickness dimension (`dim=0`) to get the final result.
    ```python
    # Multiply intensity by capture fractions for each layer
    # (1, S, F) * (T, S, F) -> (T, S, F)
    layered_intensity = intensity_expanded * capture_fractions

    # Sum over the thickness dimension to get the final result
    # (T, S, F) -> (S, F)
    result = torch.sum(layered_intensity, dim=0)
    ```

#### 2.2. Verification & Acceptance Criteria

*   **Numerical Equivalence:** The vectorized implementation must produce results that are numerically identical (`torch.allclose` with `atol=1e-12`) to the original loop-based implementation. A unit test will be created to verify this.
*   **Performance Gain:** A benchmark test will be created to measure the execution time. The vectorized version is expected to be **orders of magnitude faster**, especially for `thicksteps > 1` on a GPU.

---

### 3. Task 2: Vectorize Fhkl Tricubic Interpolation (`polin3`)

**Current State:** The functions `polin3`, `polin2`, and `polint` in `src/nanobrag_torch/utils/physics.py` are direct ports of the scalar C code. They use nested Python loops and are incompatible with the vectorized inputs from the main simulator, making `F_hkl` refinement on full images impossible.

**Proposed Solution:** Refactor the interpolation functions from the bottom up (`polint` -> `polin2` -> `polin3`) to handle batched inputs corresponding to all pixels on the detector. The most critical part is to first gather the 4x4x4 neighborhoods for all pixels in a single, vectorized operation.

#### 3.1. Implementation Steps

This is a multi-phase refactoring task.

**Phase 1: Vectorized Neighborhood Gathering** (in `Crystal._tricubic_interpolation`)

1.  **Input:** The function receives `h, k, l` tensors of shape `(S, F)`.
2.  **Calculate Indices:** Compute `h_flr`, `k_flr`, `l_flr` using `torch.floor()`.
3.  **Create Offset Tensor:** `offsets = torch.arange(-1, 3, device=self.device, dtype=torch.long)` -> `[-1, 0, 1, 2]`.
4.  **Construct Index Grids:** Use broadcasting to create the full integer indices for all neighborhoods.
    ```python
    # Shapes: (S, F, 4)
    h_indices = h_flr.unsqueeze(-1) + offsets
    k_indices = k_flr.unsqueeze(-1) + offsets
    l_indices = l_flr.unsqueeze(-1) + offsets
    ```
5.  **Gather `F_hkl` Data:** Use advanced indexing to gather the `F_hkl` values for all neighborhoods at once. This is the most critical step.
    ```python
    # h_indices[:, :, :, None, None] -> (S, F, 4, 1, 1)
    # k_indices[:, :, None, :, None] -> (S, F, 1, 4, 1)
    # l_indices[:, :, None, None, :] -> (S, F, 1, 1, 4)
    # These broadcast to index a (S, F, 4, 4, 4) tensor from hkl_data
    sub_Fhkl = self.hkl_data[
        h_indices[:, :, :, None, None],
        k_indices[:, :, None, :, None],
        l_indices[:, :, None, None, :]
    ] # Resulting shape: (S, F, 4, 4, 4)
    ```

**Phase 2: Vectorize `polint`** (in `utils/physics.py`)

1.  **Update Signature:** Modify `polint` to accept batched inputs.
    *   `xa`: shape `(..., 4)`
    *   `ya`: shape `(..., 4)`
    *   `x`: shape `(...)`
2.  **Vectorize Lagrange Formula:** Rewrite the scalar formula using tensor slicing and broadcasting.
    ```python
    def polint_vectorized(xa, ya, x):
        x = x.unsqueeze(-1) # Shape: (..., 1)
        # Slices of xa and ya will have shape (..., 1)
        x0 = (x - xa[..., 1:2]) * (x - xa[..., 2:3]) * (x - xa[..., 3:4]) * ya[..., 0:1] / \
             ((xa[..., 0:1] - xa[..., 1:2]) * (xa[..., 0:1] - xa[..., 2:3]) * (xa[..., 0:1] - xa[..., 3:4]))
        # ... repeat for x1, x2, x3 ...
        return x0 + x1 + x2 + x3
    ```

**Phase 3: Vectorize `polin2` and `polin3`** (in `utils/physics.py`)

1.  **Update Signatures:** Modify `polin2` and `polin3` to accept batched inputs.
2.  **Replace Loops with Slicing:** Replace the Python `for` loops with tensor slicing and calls to the newly vectorized `polint` and `polin2`.
    *   **Vectorized `polin2`:**
        ```python
        def polin2_vectorized(x1a, x2a, ya, x1, x2):
            # ya shape: (..., 4, 4)
            ymtmp = torch.zeros_like(ya[..., 0]) # Shape: (..., 4)
            # Replace loop with vectorized calls
            for j in range(4):
                ymtmp[..., j] = polint_vectorized(x2a, ya[..., j, :], x2)
            return polint_vectorized(x1a, ymtmp, x1)
        ```
        (Note: The small `for j in range(4)` loop can remain for clarity, as it doesn't scale with the number of pixels).
    *   **Vectorized `polin3`:** The logic is identical to `polin2` but with an extra dimension, calling the new `polin2_vectorized`.

#### 3.2. Verification & Acceptance Criteria

*   **Numerical Equivalence:** Create a unit test that compares the output of the new vectorized `polin3` against a reference implementation that manually iterates over each pixel and calls the original scalar `polin3`. The results must be identical (`torch.allclose`).
*   **Performance Gain:** Benchmark the vectorized implementation on a full-size detector image (e.g., 1024x1024). The execution time should be reduced from minutes/hours (for a hypothetical looped version) to **under a second** on a modern GPU.

