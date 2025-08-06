# nanoBragg PyTorch Testing Strategy

**Version:** 1.1  
**Date:** 2024-07-25  
**Owner:** [Your Name/Team]

## 1. Introduction & Philosophy

This document outlines the comprehensive testing strategy for the PyTorch implementation of nanoBragg. The primary goal is to ensure that the new application is a correct, verifiable, and trustworthy scientific tool.

Our testing philosophy is a three-tiered hybrid approach, designed to build confidence layer by layer:

1. **Tier 1: Translation Correctness:** We first prove that the PyTorch code is a faithful, numerically precise reimplementation of the original C code's physical model. The C code is treated as the "ground truth" specification.
2. **Tier 2: Gradient Correctness:** We then prove that the new differentiable capabilities are mathematically sound.
3. **Tier 3: Scientific Validation:** Finally, we validate the model against objective physical principles.

All tests will be implemented using the PyTest framework.

## 2. Ground Truth: Parallel Trace-Driven Validation

The foundation of our testing strategy is a "Golden Suite" of test data. Crucially, final-output comparison is insufficient for effective debugging. Our strategy is therefore centered on **Parallel Trace-Driven Validation**.

For each test case, the Golden Suite must contain three components:
1. **Golden Output Image:** The final .bin file from the C code.
2. **Golden C-Code Trace Log:** A detailed, step-by-step log of intermediate variables from the C code for a specific on-peak pixel.
3. **PyTorch Trace Log:** An identical, step-by-step log from the PyTorch implementation for the same pixel.

This allows for direct, line-by-line comparison of the entire physics calculation, making it possible to pinpoint the exact line of code where a divergence occurs.

### 2.1 Instrumenting the C Code

The `nanoBragg.c` source in `golden_suite_generator/` must be instrumented with a `-dump_pixel <slow> <fast>` command-line flag. When run with this flag, the program must write a detailed log file (`<test_case_name>_C_trace.log`) containing key intermediate variables (e.g., `scattering_vector`, `h`, `k`, `l`, `F_cell`, `F_latt`, `omega_pixel`, `polar`) for the specified pixel. This provides the ground truth for component-level testing.

### 2.2 Golden Test Cases

The following test cases will be defined, and all three artifacts (image, C trace, PyTorch trace) will be generated and stored in `tests/golden_data/`.

| Test Case Name | Description | Purpose |
| :--- | :--- | :--- |
| `simple_cubic` | A 100Å cubic cell, single wavelength, no mosaicity, no oscillation. | The "hello world" test for basic geometry and spot calculation. |
| `triclinic_complex` | A low-symmetry triclinic cell. | To stress-test the reciprocal space and geometry calculations. |
| `with_mosaicity` | The `simple_cubic` case with a 0.5-degree mosaic spread. | To test the mosaic domain implementation. |

## 3. Tier 1: Translation Correctness Testing

**Goal:** To prove the PyTorch code is a faithful port of the C code.

### 3.1 The Foundational Test: Parallel Trace Validation

All debugging of physics discrepancies **must** begin with a parallel trace comparison. Comparing only the final output images is insufficient and can be misleading. The line-by-line comparison of intermediate variables between the C-code trace and the PyTorch trace is the only deterministic method for locating the source of an error and is the mandatory first step before attempting to debug with any other method.

### 3.2 Unit Tests (`tests/test_utils.py`)

**Target:** Functions in `utils/geometry.py` and `utils/physics.py`.  
**Methodology:** For each function, create a PyTest test using hard-coded inputs. The expected output will be taken directly from the Golden C-Code Trace Log.

### 3.3 Component Tests (`tests/test_models.py`)

**Target:** The `Detector` and `Crystal` classes.  
**Methodology:** The primary component test is the **Parallel Trace Comparison**.

- `test_trace_equivalence`: A test that runs `scripts/debug_pixel_trace.py` to generate a new PyTorch trace and compares it numerically, line-by-line, against the corresponding Golden C-Code Trace Log. This single test validates the entire chain of component calculations.

### 3.4 Integration Tests (`tests/test_simulator.py`)

**Target:** The end-to-end `Simulator.run()` method.  
**Methodology:** For each test case, create a test that compares the final PyTorch image tensor against the golden `.bin` file using `torch.allclose`. This test should only be expected to pass after the Parallel Trace Comparison test passes.

## 4. Tier 2: Gradient Correctness Testing

**Goal:** To prove that the automatic differentiation capabilities are mathematically correct.

### 4.1 Gradient Checks (`tests/test_gradients.py`)

*   **Target:** All parameters intended for refinement.
*   **Methodology:** We will use PyTorch's built-in numerical gradient checker, `torch.autograd.gradcheck`. For each parameter, a test will be created that:
    1.  Sets up a minimal, fast-to-run simulation scenario.
    2.  Defines a function that takes the parameter tensor as input and returns a scalar loss.
    3.  Calls `gradcheck` on this function and its input.
*   **Requirement:** The following parameters (at a minimum) must pass `gradcheck`:
    *   **Crystal:** `cell_a`, `cell_gamma`, `misset_rot_x`
    *   **Detector:** `distance_mm`, `Fbeam_mm`
    *   **Beam:** `lambda_A`
    *   **Model:** `mosaic_spread_rad`, `fluence`

### 4.2 Multi-Tier Gradient Testing

**Comprehensive gradient testing requires multiple levels of verification:**

#### 4.2.1 Unit-Level Gradient Tests
- **Target:** Individual components like `get_rotated_real_vectors`
- **Purpose:** Verify gradients flow correctly through isolated functions
- **Example:**
  ```python
  def test_rotation_gradients():
      phi_start = torch.tensor(10.0, requires_grad=True, dtype=torch.float64)
      config = CrystalConfig(phi_start_deg=phi_start)
      rotated_vectors = crystal.get_rotated_real_vectors(config)
      assert rotated_vectors[0].requires_grad
      assert torch.autograd.gradcheck(lambda x: crystal.get_rotated_real_vectors(
          CrystalConfig(phi_start_deg=x))[0].sum(), phi_start)
  ```

#### 4.2.2 Integration-Level Gradient Tests
- **Target:** End-to-end `Simulator.run()` method
- **Purpose:** Verify gradients flow through complete simulation chain
- **Critical:** All configuration parameters must be tensors to preserve gradient flow

#### 4.2.3 Gradient Stability Tests
- **Target:** Parameter ranges and edge cases
- **Purpose:** Verify gradients remain stable across realistic parameter variations
- **Example:**
  ```python
  def test_gradient_stability():
      for phi_val in [0.0, 45.0, 90.0, 180.0]:
          phi_start = torch.tensor(phi_val, requires_grad=True, dtype=torch.float64)
          config = CrystalConfig(phi_start_deg=phi_start)
          result = simulator.run_with_config(config)
          assert result.requires_grad
  ```

#### 4.2.4 Gradient Flow Debugging
- **Purpose:** Systematic approach to diagnose gradient breaks
- **Methodology:**
  1. **Isolation:** Create minimal test case with `requires_grad=True`
  2. **Tracing:** Check `requires_grad` at each computation step
  3. **Break Point Identification:** Find where gradients are lost
  4. **Common Causes:**
     - `.item()` calls on differentiable tensors (detaches from computation graph)
     - `torch.linspace` with tensor endpoints (known PyTorch limitation)
     - Manual tensor overwriting instead of functional computation
     - Using `.detach()` or `.numpy()` on tensors that need gradients

## 5. Tier 3: Scientific Validation Testing

**Goal:** To validate the model against objective physical principles, independent of the original C code.

### 5.1 First Principles Tests (`tests/test_validation.py`)

*   **Target:** The fundamental geometry and physics of the simulation.
*   **Methodology:**
    *   **`test_bragg_spot_position`:**
        1.  Configure a simple case: cubic cell, beam along Z, detector on XY plane, no rotations.
        2.  Analytically calculate the exact (x,y) position of a low-index reflection (e.g., (1,0,0)) using the Bragg equation and simple trigonometry.
        3.  Run the simulation.
        4.  Find the coordinates of the brightest pixel in the output image using `torch.argmax`.
        5.  Assert that the simulated spot position is within one pixel of the analytically calculated position.
    *   **`test_polarization_limits`:**
        1.  Configure a reflection to be at exactly 90 degrees 2-theta.
        2.  Run the simulation with polarization set to horizontal. Assert the spot intensity is near maximum.
        3.  Run again with polarization set to vertical. Assert the spot intensity is near zero.