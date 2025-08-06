# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🛑 Core Implementation Rules (IMPORTANT)

**YOU MUST ADHERE TO THESE RULES TO AVOID COMMON BUGS:**

1.  **Consistent Unit System:** All internal physics calculations **MUST** use a single, consistent unit system. The project standard is **Angstroms (Å)** for length and **electron-volts (eV)** for energy.
    -   **Action:** Convert all input parameters (e.g., from mm, meters) to this internal system immediately upon ingestion in the configuration or model layers.
    -   **Verification:** When debugging, the first step is to check the units of all inputs to a calculation.

2.  **Crystallographic Convention:** All calculations of Miller indices (h,k,l) from a scattering vector S **MUST** use the dot product with the **real-space lattice vectors** (a, b, c). This is a non-standard convention specific to the nanoBragg.c codebase that must be replicated exactly. **Formula:** h = dot(S, a).

3.  **Differentiability is Paramount:** The PyTorch computation graph **MUST** remain connected for all differentiable parameters.
    -   **Action:** Do not manually overwrite derived tensors (like `a_star`). Instead, implement them as differentiable functions or `@property` methods that re-calculate from the base parameters (e.g., `cell_a`).
    -   **Verification:** Before merging any new feature with differentiable parameters, it **MUST** have a passing `torch.autograd.gradcheck` test.

4.  **Coordinate System & Image Orientation:** This project uses a `(slow, fast)` pixel indexing convention, consistent with `matplotlib.imshow(origin='lower')` and `fabio`.
    -   **Action:** Ensure all `torch.meshgrid` calls use `indexing="ij"` to produce `(slow, fast)` grids.
    -   **Verification:** When comparing to external images (like the Golden Suite), always confirm the axis orientation. A 90-degree rotation in the diff image is a classic sign of an axis swap.

5.  **Parallel Trace Debugging is Mandatory:** All debugging of physics discrepancies **MUST** begin with a parallel trace comparison.
    -   **Action:** Generate a step-by-step log from the instrumented C code and an identical log from the PyTorch script (`scripts/debug_pixel_trace.py`). Compare these two files to find the first line where they numerically diverge. **Before comparing, consult the component contract in `docs/architecture/` to verify the expected units of all variables in the trace log.**
    -   **Reference:** See `docs/development/testing_strategy.md` for the strategy and `docs/development/debugging.md` for the detailed workflow.

6.  **PyTorch Environment Variable:** All PyTorch code execution **MUST** set the environment variable `KMP_DUPLICATE_LIB_OK=TRUE` to prevent MKL library conflicts.
    -   **Action:** Either set `os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'` in Python before importing torch, or prefix command-line calls with `KMP_DUPLICATE_LIB_OK=TRUE`.
    -   **Reason:** Prevents "Error #15: Initializing libiomp5.dylib, but found libiomp5.dylib already initialized" crashes when multiple libraries (PyTorch, NumPy) load MKL runtime.
    -   **Verification:** All Python scripts and tests that import torch must include this environment variable setting.

7.  **Differentiable Programming Principles:** All PyTorch code **MUST** maintain computational graph connectivity for gradient flow.
    -   **Action:** Avoid functions that explicitly detach tensors from the computation graph within a differentiable code path.
    -   **Forbidden:** Using `.item()`, `.numpy()`, or `.detach()` on a tensor that requires a gradient, as this will sever the gradient path.
    -   **Correct:** Pass tensors directly through the computation pipeline. Use Python-level control flow (like `isinstance`) to handle different input types gracefully, but ensure the core operations are performed on tensors.
    -   **Known Limitation:** Be aware that some PyTorch functions, like `torch.linspace`, do not propagate gradients to their `start` and `end` arguments. In such cases, a manual, differentiable implementation using basic tensor operations (e.g., `torch.arange`) is required.
    -   **Verification:** All differentiable parameters must have passing `torch.autograd.gradcheck` tests.

8.  **Preserve C-Code References Until Feature-Complete:** C-code quotes in docstrings serve as a roadmap for unimplemented features. They **MUST NOT** be removed until the corresponding feature is fully implemented, tested, and validated.
    -   **Action:** When implementing a feature described by a C-code quote, leave the quote in place. Once the feature is complete and all its tests (including integration and gradient tests) are passing, the quote may be updated or removed if it no longer adds value beyond the implemented code.
    -   **Example:** A docstring for an unimplemented function should retain its C-code reference. A docstring for a partially implemented function (e.g., `phi` rotation is done but `misset` is not) should retain the C-code reference for the unimplemented part, clearly marked as "Future Work".
    -   **Verification:** Before removing any C-code reference, confirm that the functionality it describes is covered by a passing test in the test suite.

9.  **Never Use `.item()` on Differentiable Tensors:** The `.item()` method **MUST NOT** be used on any tensor that needs to remain differentiable.
    -   **Action:** Pass tensors directly to configuration objects and functions instead of extracting scalar values.
    -   **Forbidden:** `config = Config(param=tensor.item())` - This permanently severs the computation graph.
    -   **Correct:** `config = Config(param=tensor)` - Preserves gradient flow.
    -   **Verification:** Any use of `.item()` must be followed by verification that the tensor is not needed for gradient computation.

9.  **Avoid `torch.linspace` for Gradient-Critical Code:** `torch.linspace` does not preserve gradients from tensor endpoints.
    -   **Action:** Use manual tensor arithmetic for differentiable range generation: `start + step_size * torch.arange(...)`.
    -   **Forbidden:** `torch.linspace(start_tensor, end_tensor, steps)` where `start_tensor` or `end_tensor` require gradients.
    -   **Correct:** `start_tensor + (end_tensor - start_tensor) * torch.arange(steps) / (steps - 1)`.
    -   **Verification:** Check that generated ranges preserve `requires_grad=True` when input tensors require gradients.

10. **Boundary Enforcement for Type Safety:** Use clean architectural boundaries to handle tensor/scalar conversions.
    -   **Action:** Core methods assume tensor inputs; type conversions happen at call sites.
    -   **Forbidden:** `isinstance(param, torch.Tensor)` checks inside core computational methods.
    -   **Correct:** `config = Config(param=torch.tensor(value))` at boundaries, `def core_method(tensor_param)` in implementation.
    -   **Verification:** Core methods should not contain type checking logic; all parameters should be tensors with consistent device/dtype.

11. **C-Code Reference Template (MANDATORY FOR ALL PORTED FUNCTIONS):**
    -   **Action:** When implementing ANY function that ports logic from nanoBragg.c, you MUST:
        1. FIRST create the function stub with the docstring template below
        2. THEN fill in the C-code reference BEFORE writing any implementation
        3. ONLY THEN proceed with the Python implementation
    -   **Template:**
        ```python
        def function_name(self, ...):
            """
            Brief description of function purpose.
            
            C-Code Implementation Reference (from nanoBragg.c, lines XXXX-YYYY):
            ```c
            [PASTE EXACT C-CODE HERE - DO NOT PARAPHRASE]
            ```
            
            Args:
                ...
            Returns:
                ...
            """
            # Implementation goes here
        ```
    -   **Forbidden:** Writing the implementation before adding the C-code reference
    -   **Verification:** Before marking any implementation task complete, verify C-code reference exists
    -   **Rationale:** This is not just for human readability; it is a critical part of our trace-driven validation strategy. It provides a direct, in-code link between the new implementation and its ground-truth reference, which is essential for debugging and verification. Failure to include this reference is considered an implementation error.

12. **Critical Data Flow Convention: The Misset Rotation Pipeline**

    **This rule is non-negotiable and describes a non-standard data flow that MUST be replicated exactly.** The static misset orientation is integrated into the lattice vector calculation in a specific sequence.

    The correct, end-to-end data flow is:
    1.  Calculate the **base** real (`a,b,c`) and reciprocal (`a*,b*,c*`) vectors from the six unit cell parameters in a canonical orientation.
    2.  Apply the static misset rotation matrix to **only the reciprocal vectors** (`a*,b*,c*`).
    3.  **Crucially, recalculate the real-space vectors (`a,b,c`) from the newly rotated reciprocal vectors** using the standard crystallographic relationship (e.g., `a = (b* x c*) * V`).
    4.  These recalculated, misset-aware real-space vectors are then passed to the dynamic rotation pipeline (`get_rotated_real_vectors`) and are ultimately used in the simulator's Miller index calculation (`h = S·a`).

    **Rationale:** This specific sequence is how `nanoBragg.c` ensures the static orientation is correctly propagated. Any deviation will cause the simulation to fail validation against the golden test cases.

13. **Reciprocal Vector Recalculation for Self-Consistency**

    **The C-code performs a circular recalculation that MUST be replicated for exact metric duality.** After building initial reciprocal vectors and calculating real vectors from them, the C-code recalculates the reciprocal vectors using the standard formula.

    The complete sequence is:
    1. Build initial reciprocal vectors using the default orientation convention
    2. Calculate real vectors from reciprocal: `a = (b* × c*) × V`
    3. **Recalculate reciprocal vectors from real**: `a* = (b × c) / V_actual`
    4. **Use actual volume**: `V_actual = a · (b × c)` instead of the formula volume

    **Critical:** The volume from the actual vectors differs slightly (~0.6% for triclinic cells) from the formula volume. Using V_actual ensures perfect metric duality (a·a* = 1 exactly).

    **Verification:** The `test_metric_duality` test must pass with `rtol=1e-12`.

14. **Mandatory Component Contracts:** For any non-trivial component port (e.g., `Detector`, `Crystal`), the first step of the implementation phase **MUST** be to author (or consult, if it exists) a complete technical specification in `docs/architecture/[component_name].md`. This contract is the authoritative source for all conventions, units, and logic flows. Implementation must not begin until this document is complete.

15. **Detector Geometry Conventions:** The Detector component follows specific conventions that **MUST** be preserved:
    -   **Coordinate System:** Lab frame with beam along +X axis, right-handed system, sample at origin
    -   **Pixel Indexing:** `(slow, fast)` order using `torch.meshgrid(..., indexing="ij")`
    -   **Pixel Reference:** Integer indices refer to pixel **leading edge/corner**, not center
    -   **Rotation Order:** detector_rotx → detector_roty → detector_rotz → detector_twotheta
    -   **Convention Dependency:** MOSFLM vs XDS affects initial basis vectors and twotheta axis
    -   **Unit Handling:** User config in mm/degrees, internal calculations in Angstroms/radians
    -   **Pivot Modes:** BEAM pivot (around beam spot) vs SAMPLE pivot (around sample position)
    -   **Verification:** All detector tests must pass, including basis vector orthonormality and gradient flow

## Crystallographic Conventions

This project adheres to the `|G| = 1/d` convention, where `G = h*a* + k*b* + l*c*`. This is equivalent to the `|Q| = 2π/d` convention where `Q = 2πG`. All tests and calculations must be consistent with this standard.

**Default Orientation Matrix**: The project uses the nanoBragg.c convention for constructing the default orientation of reciprocal lattice vectors from cell parameters:
- a* is placed purely along the x-axis
- b* is placed in the x-y plane  
- c* fills out 3D space

This specific orientation must be maintained for consistency with the C-code implementation.

## Golden Test Case Specification (`simple_cubic`)

**The exact `nanoBragg.c` commands used to generate all golden reference data are centrally documented in `tests/golden_data/README.md`. That file is the single source of truth for reproducing the test suite.**

The following parameters for the `simple_cubic` case are provided for quick reference and context. These are the ground truth for the baseline validation milestone.

* **Detector Size:** `1024 x 1024` pixels
* **Pixel Size:** `0.1` mm
* **Detector Distance:** `100` mm
* **Beam Center:** `(512.5, 512.5)` pixels (derived from detector size and beam position)
* **Wavelength (`lambda`):** `6.2` Å
* **Crystal Cell:** `100 x 100 x 100` Å, `90, 90, 90` degrees
* **Crystal Size (`-N`):** `5 x 5 x 5` cells
* **Default Structure Factor (`-default_F`):** `100`

## Repository Overview

This repository contains **nanoBragg**, a C-based diffraction simulator for nanocrystals, along with comprehensive documentation for a planned PyTorch port. The codebase consists of:

- **Core C simulators**: `nanoBragg.c` (main diffraction simulator), `nonBragg.c` (amorphous scattering), `noisify.c` (noise addition)
- **PyTorch port documentation**: Complete architectural design and implementation plan in `./docs/`
- **Auxiliary tools**: Shell scripts for data conversion and matrix generation

## Build Commands

### C Code Compilation
```bash
# Standard build
gcc -O3 -o nanoBragg nanoBragg.c -lm -fopenmp

# Build other simulators
gcc -O3 -o nonBragg nonBragg.c -lm
gcc -O3 -o noisify noisify.c -lm
```

### No Testing Framework
The repository currently uses manual validation through example runs and visual inspection. No automated test suite exists for the C code.

## Core Architecture

### C Implementation Structure
- **Single-file architecture**: All core logic in `nanoBragg.c` (~49k lines)
- **Procedural design**: Sequential execution through main() function
- **Three-phase execution**:
  1. **Setup Phase**: Parse arguments, load files, initialize geometry
  2. **Simulation Loop**: Nested loops over pixels, sources, mosaic domains, phi steps
  3. **Output Phase**: Apply scaling, add noise, write image files

### Key Data Flow
1. **Input**: Structure factors (HKL file), crystal orientation (matrix file), beam/detector parameters
2. **Core calculation**: For each detector pixel, sum contributions from all source points, mosaic domains, and phi steps
3. **Output**: SMV-format diffraction images with optional noise

### OpenMP Parallelization
- Single `#pragma omp parallel for` directive on outer pixel loop
- Shared read-only data (geometry, structure factors)
- Private per-thread variables for calculations
- Reduction clauses for global statistics

## PyTorch Port Design

The `./docs/` directory contains a complete architectural design for a PyTorch reimplementation:

### Key Design Principles
- **Vectorization over loops**: Replace nested C loops with broadcasting tensor operations
- **Object-oriented structure**: `Crystal`, `Detector`, `Simulator` classes
- **Differentiable parameters**: Enable gradient-based optimization. **(See Core Implementation Rules above)**
- **GPU acceleration**: Leverage PyTorch's CUDA backend
- **Consistent Units**: All internal calculations use Angstroms. **(See Core Implementation Rules above)**

### Critical Documentation Files
**Architecture & Design:**
- `docs/architecture/pytorch_design.md`: Core system architecture, vectorization strategy, class design, memory management
- `docs/development/implementation_plan.md`: Phased development roadmap with specific tasks and deliverables
- `docs/development/testing_strategy.md`: Three-tier validation approach (translation correctness, gradient correctness, scientific validation)

**C Code Analysis:**
- `docs/architecture/c_code_overview.md`: Original C codebase structure, execution flow, and design patterns
- `docs/architecture/c_function_reference.md`: Complete function-by-function reference with porting guidance
- `docs/architecture/c_parameter_dictionary.md`: All command-line parameters mapped to internal C variables

**Advanced Topics:**
- `docs/architecture/parameter_trace_analysis.md`: End-to-end parameter flow analysis for gradient interpretation
- `docs/development/processes.xml`: Standard Operating Procedures for development workflow

### Testing Strategy (PyTorch Port)
1. **Tier 1**: Numerical equivalence with instrumented C code ("Golden Suite")
2. **Tier 2**: Gradient correctness via `torch.autograd.gradcheck`
3. **Tier 3**: Scientific validation against physical principles

## Common Usage Patterns

### Basic Simulation
```bash
# Generate structure factors from PDB
getcif.com 3pcq
refmac5 hklin 3pcq.mtz xyzin 3pcq.pdb hklout refmacout.mtz xyzout refmacout.pdb
mtz_to_P1hkl.com refmacout.mtz FC_ALL_LS

# Create orientation matrix
./UBtoA.awk << EOF | tee A.mat
CELL 281 281 165.2 90 90 120 
WAVE 6.2
RANDOM
EOF

# Run simulation
./nanoBragg -hkl P1.hkl -matrix A.mat -lambda 6.2 -N 10
```

### SAXS Simulation
```bash
# Single unit cell with interpolation
./nanoBragg -mat bigcell.mat -hkl P1.hkl -lambda 1 -N 1 -distance 1000 -detsize 100 -pixel 0.1
```

## File I/O Conventions

### Input Files
- **HKL files**: Plain text format `h k l F` (one reflection per line)
- **Matrix files**: MOSFLM-style orientation matrices (9 values for reciprocal vectors)
- **STOL files**: Structure factor vs sin(θ)/λ for amorphous materials

### Output Files
- **floatimage.bin**: Raw 4-byte float intensities
- **intimage.img**: SMV-format noiseless image
- **noiseimage.img**: SMV-format with Poisson noise
- **image.pgm**: 8-bit grayscale for visualization

## Development Workflow

### Standard Operating Procedures
**IMPORTANT**: For all non-trivial development tasks, consult `docs/development/processes.xml` which contains comprehensive Standard Operating Procedures (SOPs) for:
- Task planning and decomposition
- Test-driven development
- Bug fixing and verification
- Documentation updates
- Large-scale refactoring

The SOPs emphasize:
- **Checklist-driven approach**: Use TodoWrite/TodoRead tools for task management
- **Plan before acting**: Create detailed plans before implementation
- **Verify then commit**: Always run tests before committing changes
- **Subagent scaling**: Use specialized subagents for complex or parallelizable tasks

### For C Code Changes
1. Modify source files directly
2. Recompile with appropriate flags
3. Test with known examples from README
4. Validate output visually with ADXV or similar

### For PyTorch Port Development
**Primary References:**
- `docs/development/implementation_plan.md`: Detailed phase-by-phase development plan
- `docs/architecture/pytorch_design.md`: System architecture and vectorization approach
- `docs/development/testing_strategy.md`: Comprehensive validation methodology

**Implementation Order:**
1. **Phase 1**: Implement utility functions (`utils/geometry.py`, `utils/physics.py`)
2. **Phase 2**: Build core data models (`Crystal`, `Detector` classes) 
3. **Phase 3**: Implement `Simulator` class and main executable
4. **Phase 4**: Add differentiable capabilities and validation

**Key Implementation Guidelines:**
- Use `docs/architecture/c_function_reference.md` for porting individual C functions
- Reference `docs/architecture/c_parameter_dictionary.md` for parameter mapping
- Consult `docs/architecture/parameter_trace_analysis.md` for understanding gradient flow
- Follow testing strategy in `docs/development/testing_strategy.md` for validation

## Memory and Performance Considerations

### C Implementation
- Memory usage scales with detector size and simulation complexity
- CPU parallelization via OpenMP (typically 4-16 cores)
- Large structure factor tables cached in memory

### PyTorch Port
- Memory-intensive vectorization strategy with batching fallback
- GPU acceleration for tensor operations
- Configurable precision (float32/float64) and batching for memory management

## ⚡ Common Commands & Workflow

To improve efficiency, use these standard commands for common tasks.

- **List all available tests:**
  `pytest --collect-only`
- **Run the full test suite:**
  `make test`
- **Run a specific test function:**
  `# Format: pytest -v <file_path>::<ClassName>::<test_function_name>`
  `pytest -v tests/test_suite.py::TestTier1TranslationCorrectness::test_simple_cubic_reproduction`
- **Run the pixel trace debug script:**
  `KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py`
- **Install the package in editable mode:**
  `pip install -e .`

## Domain-Specific Context

This is scientific simulation software for **X-ray crystallography** and **small-angle scattering (SAXS)**. Key physical concepts:
- **Bragg diffraction**: Constructive interference from crystal lattice
- **Structure factors**: Fourier transform of electron density
- **Mosaicity**: Crystal imperfection modeling
- **Ewald sphere**: Geometric construction for diffraction condition

The software is used in structural biology, materials science, and synchrotron/X-ray free-electron laser facilities.