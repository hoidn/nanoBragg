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

## 2. Configuration Parity

**CRITICAL REQUIREMENT:** Before implementing any test that compares against C-code output, you **MUST** ensure exact configuration parity. All golden test cases must be generated with commands that are verifiably equivalent to the PyTorch test configurations.

**Authoritative Reference:** See the **[C-CLI to PyTorch Configuration Map](./c_to_pytorch_config_map.md)** for:
- Complete parameter mappings
- Implicit conventions (pivot modes, beam adjustments, rotation axes)
- Common configuration bugs and prevention strategies

Configuration mismatches are the most common source of test failures. Always verify:
- Pivot mode (BEAM vs SAMPLE) based on parameter implications
- Convention-specific adjustments (e.g., MOSFLM's 0.5 pixel offset)
- Default rotation axes for each convention
- Proper unit conversions at boundaries
 - Explicit convention selection: tests and harnesses MUST pass `-convention` (or equivalent API flag) to avoid implicit CUSTOM switching when vector parameters are present

## 2.1 Ground Truth: Parallel Trace-Driven Validation

The foundation of our testing strategy is a "Golden Suite" of test data. Crucially, final-output comparison is insufficient for effective debugging. Our strategy is therefore centered on **Parallel Trace-Driven Validation**.

For each test case, the Golden Suite must contain three components:
1. **Golden Output Image:** The final .bin file from the C code.
2. **Golden C-Code Trace Log:** A detailed, step-by-step log of intermediate variables from the C code for a specific on-peak pixel.
3. **PyTorch Trace Log:** An identical, step-by-step log from the PyTorch implementation for the same pixel.

This allows for direct, line-by-line comparison of the entire physics calculation, making it possible to pinpoint the exact line of code where a divergence occurs.

### 2.2 Instrumenting the C Code

The `nanoBragg.c` source in `golden_suite_generator/` must be instrumented with a `-dump_pixel <slow> <fast>` command-line flag. When run with this flag, the program must write a detailed log file (`<test_case_name>_C_trace.log`) containing key intermediate variables (e.g., `scattering_vector`, `h`, `k`, `l`, `F_cell`, `F_latt`, `omega_pixel`, `polar`) for the specified pixel. This provides the ground truth for component-level testing.

### 2.3 Golden Test Cases

The following test cases will be defined, and all three artifacts (image, C trace, PyTorch trace) will be generated and stored in `tests/golden_data/`.

| Test Case Name | Description | Purpose |
| :--- | :--- | :--- |
| `simple_cubic` | A 100Å cubic cell, single wavelength, no mosaicity, no oscillation. | The "hello world" test for basic geometry and spot calculation. |
| `triclinic_P1` | A low-symmetry triclinic cell with misset orientation. | To stress-test the reciprocal space and geometry calculations. |
| `simple_cubic_mosaic` | The `simple_cubic` case with mosaic spread. | To test the mosaic domain implementation. |
| `cubic_tilted_detector` | Cubic cell with rotated and tilted detector. | To test general detector geometry implementation. |

### 2.4 Canonical Generation Commands

**⚠️ CRITICAL:** The following commands are the **single source of truth** for reproducing the golden data. All parallel verification MUST use these exact parameters. These commands must be run from within the `golden_suite_generator/` directory.

#### 2.4.1 `simple_cubic`
**Purpose:** Basic validation of geometry and physics calculations.

**Canonical Command:**
```bash
./nanoBragg -hkl P1.hkl -matrix A.mat \
  -lambda 6.2 \
  -N 5 \
  -default_F 100 \
  -distance 100 \
  -detsize 102.4 \
  -pixel 0.1 \
  -floatfile ../tests/golden_data/simple_cubic.bin \
  -intfile ../tests/golden_data/simple_cubic.img
```

**Key Parameters:**
- Crystal: 100Å cubic cell, 5×5×5 unit cells
- Detector: 100mm distance, 1024×1024 pixels (via `-detsize 102.4`)
- Beam: λ=6.2Å, uniform F=100

#### 2.4.2 `triclinic_P1`
**Purpose:** Validates general triclinic geometry and misset rotations.

**Canonical Command:**
```bash
./nanoBragg -misset -89.968546 -31.328953 177.753396 \
  -cell 70 80 90 75 85 95 \
  -default_F 100 \
  -N 5 \
  -lambda 1.0 \
  -detpixels 512 \
  -floatfile tests/golden_data/triclinic_P1/image.bin
```

**Key Parameters:**
- Crystal: Triclinic (70,80,90,75°,85°,95°), 5×5×5 unit cells
- Detector: 100mm distance, 512×512 pixels (via `-detpixels 512`)
- Pivot: BEAM mode ("pivoting detector around direct beam spot")

**⚠️ CRITICAL DIFFERENCE:** Uses `-detpixels 512` NOT `-detsize`!

#### 2.4.3 `simple_cubic_mosaic`
**Purpose:** Validates mosaicity implementation.

**Canonical Command:**
```bash
./nanoBragg -hkl P1.hkl -matrix A.mat \
  -lambda 6.2 \
  -N 5 \
  -default_F 100 \
  -distance 100 \
  -detsize 100 \
  -pixel 0.1 \
  -mosaic_spread 1.0 \
  -mosaic_domains 10 \
  -floatfile ../tests/golden_data/simple_cubic_mosaic.bin \
  -intfile ../tests/golden_data/simple_cubic_mosaic.img
```

**Key Parameters:**
- Same as simple_cubic but with 1.0° mosaic spread, 10 domains
- Detector: 1000×1000 pixels (via `-detsize 100`)

#### 2.3.4 `cubic_tilted_detector`
**Purpose:** Validates general detector geometry with rotations.

**Canonical Command:**
```bash
./nanoBragg -lambda 6.2 \
  -N 5 \
  -cell 100 100 100 90 90 90 \
  -default_F 100 \
  -distance 100 \
  -detsize 102.4 \
  -detpixels 1024 \
  -Xbeam 61.2 -Ybeam 61.2 \
  -detector_rotx 5 -detector_roty 3 -detector_rotz 2 \
  -twotheta 15 \
  -oversample 1 \
  -floatfile tests/golden_data/cubic_tilted_detector/image.bin
```

**Key Parameters:**
- Detector rotations: rotx=5°, roty=3°, rotz=2°, twotheta=15°
- Beam center offset: (61.2, 61.2) mm
- Pivot: SAMPLE mode with explicit beam center

## 2.5 Parallel Validation Matrix (AT ↔ tests ↔ env/commands)

This matrix maps each Acceptance Test in the AT‑PARALLEL suite to its concrete test file(s), required environment variables, and canonical commands to execute them. Use this section to run the exact parity checks that gate C↔PyTorch equivalence.

General environment for live C parity tests:

- `KMP_DUPLICATE_LIB_OK=TRUE` (avoid MKL conflicts on some systems)
- `NB_RUN_PARALLEL=1` (enables live C↔PyTorch tests)
- `NB_C_BIN=./golden_suite_generator/nanoBragg` (path to C reference binary)
  - Fallback: if `golden_suite_generator/nanoBragg` does not exist in this repo, use `NB_C_BIN=./nanoBragg` (root‑level C binary)

Quick invocation patterns (authoritative harness = pytest):

- Shared parity matrix: `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py`
- Single parity case (example): `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py -k "AT-PARALLEL-002"`
- PyTorch-only invariance (when applicable): `pytest -v tests/test_at_parallel_0XX.py`
- Golden-data parity (no C binary required): `pytest -v tests/test_at_parallel_012.py`

Reference mapping:

- AT‑PARALLEL‑001 — Beam Center Scaling
  - Parity harness: `tests/test_parity_matrix.py -k "AT-PARALLEL-001"`
  - Env: `NB_RUN_PARALLEL=1`, `NB_C_BIN` set (parity)
  - Command (canonical): `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py -k "AT-PARALLEL-001"`
  - Supplemental PyTorch-only regression: `pytest -v tests/test_at_parallel_001.py`
  - Notes: Verifies detector-size scaling and MOSFLM +0.5 offset parity.

- AT‑PARALLEL‑002 — Pixel Size Independence
  - Parity harness: `tests/test_parity_matrix.py -k "AT-PARALLEL-002"`
  - Env: `NB_RUN_PARALLEL=1`, `NB_C_BIN` set (parity)
  - Command (canonical): `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py -k "AT-PARALLEL-002"`
  - Supplemental PyTorch-only regression: `pytest -v tests/test_at_parallel_002.py`
  - Notes: Enforces correlation ≥0.9999 across pixel sizes under MOSFLM convention.

- AT‑PARALLEL‑004 — MOSFLM 0.5 Pixel Offset
  - Parity harness: `tests/test_parity_matrix.py -k "AT-PARALLEL-004"`
  - Env: `NB_RUN_PARALLEL=1`, `NB_C_BIN` set (parity)
  - Command (canonical): `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py -k "AT-PARALLEL-004"`
  - Supplemental PyTorch-only regression: `pytest -v tests/test_at_parallel_004.py`
  - Notes: Verifies MOSFLM +0.5 pixel offset vs. XDS convention with correlation >0.99.

- AT‑PARALLEL‑006 — Single Reflection Position
  - Parity harness: `tests/test_parity_matrix.py -k "AT-PARALLEL-006"`
  - Env: `NB_RUN_PARALLEL=1`, `NB_C_BIN` set (parity)
  - Command (canonical): `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py -k "AT-PARALLEL-006"`
  - Supplemental checks: `pytest -v tests/test_at_parallel_006.py`
  - Notes: Enforces parity across distance/wavelength sweeps.

- AT‑PARALLEL‑007 — Peak Position with Rotations
  - Parity harness: `tests/test_parity_matrix.py -k "AT-PARALLEL-007"`
  - Env: `NB_RUN_PARALLEL=1`, `NB_C_BIN` set (parity)
  - Command (canonical): `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py -k "AT-PARALLEL-007"`
  - Supplemental checks: `pytest -v tests/test_at_parallel_007.py`
  - Notes: Validates rotated detector parity with correlation ≥0.9995 and consistent intensity sums.

- AT‑PARALLEL‑003/005/008/009/010/013/014/015/016/017/018/021/022/023/024/025/026/028/029
  - Test files: `tests/test_at_parallel_0XX.py`
  - Env: varies; most invariance tests run without C; rotation/combined/tilted cases may include live parity variants (see file headers)

- AT‑PARALLEL‑011 — Polarization Factor Verification (C↔PyTorch live parity)
  - Test file: `tests/test_at_parallel_011.py`
  - Env: `NB_RUN_PARALLEL=1`, `NB_C_BIN` set
  - Command: `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_at_parallel_011.py`

- AT‑PARALLEL‑012 — Reference Pattern Correlation (golden data)
  - Test file: `tests/test_at_parallel_012.py`
  - Env: none (uses `tests/golden_data/*`)
  - Command: `pytest -v tests/test_at_parallel_012.py`

- AT‑PARALLEL‑020 — Comprehensive Integration (C↔PyTorch live parity)
  - Test file: `tests/test_at_parallel_020.py`
  - Env: `NB_RUN_PARALLEL=1`, `NB_C_BIN` set
  - Command: `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_at_parallel_020.py`

- AT‑PARALLEL‑022 — Combined Detector+Crystal Rotation Equivalence (C↔PyTorch live parity)
  - Test file: `tests/test_at_parallel_022.py`
  - Env: `NB_RUN_PARALLEL=1`, `NB_C_BIN` set
  - Command: `KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_at_parallel_022.py`

- Parity case definitions: `tests/parity_cases.yaml` is the machine-readable companion to this matrix. It enumerates canonical commands, sweeps, thresholds, and options for the shared parity runner (`tests/test_parity_matrix.py`). Every parity-threshold AT SHALL appear in both the matrix and the YAML file.

### 2.5.1 Trace Recipe (per AT)

For equivalence debugging (AT‑PARALLEL failures, correlation below thresholds, structured diffs), generate aligned traces:

- Pixel selection: choose a strong on‑peak pixel close to the beam center or a specified coordinate in the test; record the exact `(s,f)` indices used.
- PyTorch trace: emit a structured log containing, at minimum, `pix0_vector`, basis vectors, `R` (distance), solid angle (both point‑pixel and obliquity‑corrected), close_distance and obliquity factor, `k_in`, `k_out`, `S`, Miller indices (float and rounded), `F`, lattice factors (`F_latt_a/b/c`, product), `F^2`, `F_latt^2`, `omega/solid_angle`, pixel area, fluence and final intensity.
- C trace: run the C binary with identical parameters and print the same variables for the same pixel. If needed, add temporary printf instrumentation; keep units consistent with the PyTorch trace (meters, steradians, Å where noted).
- Dtype/device: debug in float64 on CPU for determinism unless the AT explicitly requires GPU.
- Artifacts: save as `reports/debug/<DATE>/AT-<ID>/{c_trace.log, py_trace.log, metrics.json, diff_heatmap.png}` and cite paths in the plan.

### 2.5.2 Matrix Gate (hard preflight)

Before any parity run in a debugging loop:

- Resolve the AT in this matrix to the exact pytest node(s) and required environment.
- Verify `NB_C_BIN` exists and is executable; if the project uses a root‑level `./nanoBragg`, set `NB_C_BIN=./nanoBragg`.
- Prohibition: Do not run PyTorch‑only tests first for equivalence loops. The first command MUST be the canonical C‑parity pytest invocation mapped here. PyTorch‑only checks are allowed only as secondary, supportive diagnostics.
- If an AT mapping is missing or incomplete, add a minimal entry here (test file, env, canonical command) and append a TODO in `docs/fix_plan.md` referencing the addition.
 - Friction rule: If the same parity steps (env export, pytest node, trace generation) are repeated across two loops, factor them into a minimal helper (e.g., a one‑liner shell alias or small script) and reference it in this matrix. Record the addition briefly in `docs/fix_plan.md` Attempts History. Do not bypass pytest; helpers should only wrap the mapped canonical commands.

### 2.5.3 Normative Parity Coverage (SHALL)

- Every acceptance test in `specs/spec-a-parallel.md` with a C↔Py numerical threshold MUST have:
  - A human-readable entry in this matrix (test path, environment, canonical command), and
  - A corresponding machine-readable case in `tests/parity_cases.yaml` powering `tests/test_parity_matrix.py`.
- Missing coverage in either location is blocking. The fix plan cannot mark the AT done until the mapping exists or an explicit harness entry (with pass/fail logic) is added.
- Documentation updates MUST keep the matrix and YAML file in sync with the canonical command line (arguments, sweeps, thresholds).

### 2.5.4 Artifact-Backed Closure (SHALL)

- Success claims for parity-threshold ATs MUST cite artifacts from a mapped parity path meeting thresholds:
  - Metrics: correlation, MSE, RMSE, max |Δ|, C_sum, Py_sum, sum_ratio (optional SSIM when helpful).
  - Storage: under `reports/<date>-AT-<ID>/metrics.json` (or equivalent) plus supporting visuals (diff heatmaps/overlays) when failures occur.
  - fix_plan Attempts History MUST reference these paths (look for `Metrics:` / `Artifacts:` entries).
- No artifacts → no closure; reopen the fix plan item instead.

### 2.5.5 Environment Canonicalization Preflight (SHALL)

- Resolve `NB_C_BIN` before running parity commands. Preferred order: environment value → `./golden_suite_generator/nanoBragg` → `./nanoBragg`. Abort if none exist.
- Invoke PyTorch parity via `sys.executable` to ensure the active virtual environment executes the run.
- Treat missing binaries/interpreters as blocking errors (fail fast rather than skipping parity).

### 2.5.6 CI Meta-Check (Docs-as-Data)

- CI MUST lint for:
  - Spec → matrix → YAML coverage for all parity-threshold ATs.
  - Existence of mapped commands/binaries referenced in the YAML.
  - Presence of artifact paths when fix_plan marks parity items complete.
- CI SHOULD fail when any invariant above is violated; parity documentation is normative.

## 2.6 CI Gates (Parity & Traces)

To prevent drift, CI should enforce the following fast gates on CPU:

- Detector geometry visual parity: run `scripts/verify_detector_geometry.py` and fail if any reported correlation drops below the documented thresholds (e.g., ≥0.999 for baseline/tilted unless otherwise specified). Save PNG and metrics JSON as artifacts.
- Trace parity check: generate one C trace and one PyTorch trace for the canonical pixel (`tests/golden_data/simple_cubic_pixel_trace.log` spec) and assert no first‑difference at the named checkpoints (e.g., pix0_vector, basis vectors, q, h,k,l, omega_pixel). Attach c_trace.log/py_trace.log on failure.

Optional visual parity harness (sanity check):

- Script: `scripts/comparison/run_parallel_visual.py`
- Env: `NB_C_BIN` should point to C binary
- Run: `python scripts/comparison/run_parallel_visual.py`
- Output: PNGs and `metrics.json` under `parallel_test_visuals/AT-PARALLEL-XXX/`

When the visual harness and the AT tests disagree, treat the AT tests as the primary gate (authoritative) and use parallel trace‑driven debugging (Section 2.1) to identify the first divergence. Scripts are supportive tools; conformance is determined by the pytest suite.

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

**Primary Validation Tool:** The main script for running end-to-end parallel validation against the C-code reference is `scripts/verify_detector_geometry.py`. This script automates the execution of both the PyTorch and C implementations, generates comparison plots, and computes quantitative correlation metrics. It relies on `scripts/c_reference_runner.py` to manage the C-code execution.

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
