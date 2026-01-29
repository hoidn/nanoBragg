# CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

IMPORTANT INSTRUCTIONS 
When using subagents:
1. - Create detailed, self-contained prompts for each agent. 
- Include a list of all relevant files the agent will need to understand the context of the tas
- Include specific instructions on what to accomplish
- Define clear output expectations
- Remember agents are stateless and need complete context
2. If appropriate, spawn parallel subagents, ensuring all agents launch in a single parallel batch
3. Collect & Summarize Results
- Gather outputs from all completed agents
- Synthesize findings into cohesive response
<example>
<subagent you might want to use>
name: debugger
description: Debugging specialist for errors, test failures, and unexpected behavior. Use proactively when encountering any issues.
model: sonnet
</subagent you might want to use>
this agent needs context on the spec, architecture, development practices,
and project documentation relevant to the failing tests / feature / behavior / component(s)
</example
IMPORTANT

### Protected Assets Rule
- **Never delete or rename files referenced in `docs/index.md`.** Treat that index as the canonical allowlist of required artifacts (e.g., `loop.sh`). If removal or relocation is unavoidable, update `docs/index.md` in the same change and clearly document the rationale in the commit message and relevant plan entry.
- Before any repository hygiene or cleanup sweep, refresh `docs/index.md` and verify that none of the targeted files appear there.

## 🚀 Current Initiative: None

## ⚙️ PyTorch Runtime Guardrails

- **Vectorization is mandatory:** Any simulator change must preserve the batched tensor flows described in `docs/architecture/pytorch_design.md` (no re-introduced Python loops when a batched helper exists).
- **Device/dtype neutrality:** Do not introduce `.cpu()`/`.cuda()` or per-call `.to()` shims inside compiled paths; ensure tensors live on the caller’s device/dtype up front and run CPU + CUDA smoke checks when available.
- **Quick reference:** See `docs/development/pytorch_runtime_checklist.md` (create/update as part of this change) for the actionable checklist before and after every PyTorch edit.

---

**For a complete overview of the project's documentation, start with the [Project Documentation Index](./docs/index.md).**

Key starting points include:
- **[Architecture Hub](./docs/architecture/README.md)** for all technical specifications.
- **[Testing Strategy](./docs/development/testing_strategy.md)** for validation procedures.

## 📋 Quick Reference: Comparison Tool

The `nb-compare` tool compares C and PyTorch implementations side-by-side:

```bash
# Basic comparison
nb-compare -- -default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100 -detpixels 256

# With custom binaries and ROI
nb-compare --c-bin ./golden_suite_generator/nanoBragg --roi 100 156 100 156 -- [args...]

# With resampling for shape mismatch and custom output
nb-compare --resample --outdir my_comparison --threshold 0.98 -- [args...]
```

Outputs comparison metrics (correlation, RMSE, peak alignment) and PNG previews to `comparison_artifacts/`.

## 📋 Quick Reference: nanoBragg C Commands

For exact golden-data commands, see [`tests/golden_data/README.md`](./tests/golden_data/README.md). Use the NB_C_BIN env var to select the C binary:

```bash
# Recommended: instrumented binary under golden_suite_generator/
export NB_C_BIN=./golden_suite_generator/nanoBragg
# Alternative (frozen binary at repo root):
# export NB_C_BIN=./nanoBragg

# Simple cubic test case
"$NB_C_BIN" -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 1024 -floatfile output.bin

# Tilted detector with MOSFLM convention
"$NB_C_BIN" -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 1024 -Xbeam 61.2 -Ybeam 61.2 \
  -detector_rotx 5 -detector_roty 3 -detector_rotz 2 -twotheta 15 \
  -floatfile output.bin
```

For all parameters, see [`docs/architecture/c_parameter_dictionary.md`](./docs/architecture/c_parameter_dictionary.md).

## 🛑 Core Implementation Rules (IMPORTANT)

**YOU MUST ADHERE TO THESE RULES TO AVOID COMMON BUGS:**

0.  **🚨 DETECTOR DEBUGGING PREREQUISITE:** Before debugging ANY detector geometry correlation issue, you **MUST** read the [Detector Geometry Debugging Checklist](./docs/debugging/detector_geometry_checklist.md). This document will save you 4-8 hours by identifying common issues:
    - Unit system confusion (Detector uses meters internally, not Angstroms)
    - MOSFLM convention axis swap and +0.5 pixel offset
    - Undocumented CUSTOM convention switching
    - Known C code logging bugs
    - **Failure to read this checklist will result in DAYS of unnecessary debugging!**

0.  **Configuration Parity is Mandatory:** Before writing any test or implementation that involves C-code validation, you **MUST** consult the [C-CLI to PyTorch Configuration Map](./docs/development/c_to_pytorch_config_map.md). This document is the single source of truth for all parameter mappings and implicit C-code conventions. Failure to ensure 1:1 configuration parity is the most common source of bugs, particularly with:
    - Implicit pivot mode logic (e.g., `-twotheta` implies SAMPLE pivot)
    - Convention-dependent beam center calculations (MOSFLM adds 0.5 pixel adjustment)
    - Rotation axis defaults (MOSFLM uses Y-axis, XDS uses X-axis for twotheta)
    - Unit conversions (mm→m, degrees→radians)

0.  **Instrumentation / Tracing Discipline:** Never re-derive physics or duplicate algorithms in trace/debug code. Instrumentation must reuse the production helpers or cached intermediates so traces reflect the exact values the main path computed (see [Architecture Hub](./docs/architecture/README.md#⚠️-trace-instrumentation-rule)). Parallel "trace-only" implementations inevitably drift and make parity debugging unreliable.

1.  **Units (canonical in spec/arch):** Use the conversions and detector hybrid exception exactly as defined in `specs/spec-a.md` (Units & Geometry) and summarized in `arch.md` and `docs/architecture/detector.md`.

2.  **Crystallographic Convention (by design):** Compute h,k,l via real‑space dot (see `specs/spec-a.md` Physics for the authoritative statement).

3.  **Differentiability:** Follow `arch.md` Differentiability Guidelines (no `.item()` on grad tensors, avoid `torch.linspace` with tensor endpoints, derive via functions/properties) and require `torch.autograd.gradcheck` for parameters.

4.  **Coordinate System & Image Orientation:** This project uses a `(slow, fast)` pixel indexing convention, consistent with `matplotlib.imshow(origin='lower')` and `fabio`.
    -   **Action:** Ensure all `torch.meshgrid` calls use `indexing="ij"` to produce `(slow, fast)` grids.
    -   **Verification:** When comparing to external images (like the Golden Suite), always confirm the axis orientation. A 90-degree rotation in the diff image is a classic sign of an axis swap.

5.  **Parallel Trace Debugging is Mandatory:** All debugging of physics discrepancies **MUST** begin with a parallel trace comparison.
    -   **Action:** Generate a step-by-step log from the instrumented C code and an identical log from the PyTorch script (`scripts/debug_pixel_trace.py`). Compare these two files to find the first line where they numerically diverge. **Before comparing, consult the component contract in `docs/architecture/` to verify the expected units of all variables in the trace log.**
    -   **Reference:** See `docs/development/testing_strategy.md` for the strategy and `docs/debugging/debugging.md` for the detailed workflow.
    -   **Key Scripts:** The primary script for end-to-end validation is `scripts/verify_detector_geometry.py`. It uses helper modules `scripts/c_reference_runner.py` to execute the C code and `scripts/smv_parser.py` to read the output images. For single-pixel, step-by-step debugging, use `scripts/debug_pixel_trace.py`.

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

16. **PyTorch Device & Dtype Neutrality:** Implementation MUST work for CPU and GPU tensors and for all supported dtypes without silent device transfers.
    -   **Action:** Accept tensors on whatever device/dtype the caller provides; use helper utilities (`to()`/`type_as()`) to coerce internal temporaries to the dominant device/dtype instead of hard-coding `.cpu()`/`.cuda()` or allocating new CPU tensors mid-pipeline.
    -   **Verification:** Add (or update) smoke tests that exercise both CPU and CUDA execution whenever a code path touches tensor math; at minimum, run the authoritative command once with `device=cpu` and once with `device=cuda` (when available) before marking work complete. Treat any Dynamo/compile warnings about mixed devices as failures to resolve immediately.
    -   **Forbidden:** Leaving datasets, constants, or configuration tensors on default CPU while multiplying by GPU intermediates; relying on implicit device promotion; assuming float64/CPU execution in production paths.
    -   **Scope:** This applies across the project and to any future PyTorch work you undertake—make code device/dtype agnostic by default.

17. **Tooling & Benchmark Placement:** Benchmark, profiling, and diagnostic scripts SHALL live under structured tooling directories (`scripts/benchmarks/`, `scripts/profiling/`, etc.) and follow the repo's CLI/env conventions.
    -   **Action:** When creating or modifying benchmarking utilities, place them under `scripts/…`, require `KMP_DUPLICATE_LIB_OK=TRUE`, resolve binaries via the documented precedence, and record authoritative commands in `docs/development/testing_strategy.md` (or the relevant tooling index).
    -   **Forbidden:** Dropping standalone benchmarking files in the repo root or bypassing the editable-install expectation with ad-hoc `sys.path` tweaks.
    -   **Verification:** Update `docs/fix_plan.md` (Suite/Tooling section) with reproduction commands and results every time a benchmark uncovers an issue; ensure CI/docs reference the canonical script location.

18. **Stochastic Operations Must Use Seeded Generators:** Any use of `torch.rand`, `torch.randn`, or similar stochastic functions in code that may be differentiated **MUST** use a `torch.Generator` with deterministic seeding.
    -   **Action:** Create generator with `gen = torch.Generator(device=device)`, seed it from the appropriate config parameter (e.g., `config.mosaic_seed`), and pass `generator=gen` to stochastic ops.
    -   **Forbidden:** `torch.randn(...)` without `generator=` argument in any code path that may be differentiated.
    -   **Rationale:** Unseeded RNG produces different values per forward call, breaking `torch.autograd.gradcheck` which compares analytical gradients (from one forward pass) against numerical gradients (from multiple forwards with perturbed inputs). Without deterministic seeding, numerical gradients measure sensitivity to random noise, not to the intended parameter.
    -   **Reparameterization Pattern:** For parameters that scale stochastic values (e.g., `mosaic_spread_deg`), use: `actual_value = frozen_base_noise * scale_param`. The frozen noise has no gradient; the scale parameter carries gradients.
    -   **Verification:** Any function using stochastic operations must have a passing `torch.autograd.gradcheck` test with non-zero stochastic parameters.
    -   **Reference:** MOSAIC-GRADIENT-001, `tests/test_gradients.py::TestMosaicGradients`

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

### Binaries and Instrumentation (IMPORTANT)
- Treat the root `./nanoBragg` as a frozen reference binary; do not rebuild it for tracing.
- Build and recompile any instrumented C binary under `golden_suite_generator/` (e.g., `./golden_suite_generator/nanoBragg`).
- Always invoke the C runner via `NB_C_BIN`:
  - Recommended: `export NB_C_BIN=./golden_suite_generator/nanoBragg`
  - Alternative: `export NB_C_BIN=./nanoBragg`
- Tooling (e.g., comparison scripts) SHOULD resolve the C runner in this order:
  1) `--c-bin` arg if provided
  2) `NB_C_BIN` env var
  3) `./golden_suite_generator/nanoBragg` if present
  4) `./nanoBragg`
  5) Otherwise, error with guidance

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
"$NB_C_BIN" -hkl P1.hkl -matrix A.mat -lambda 6.2 -N 10
```

### SAXS Simulation
```bash
# Single unit cell with interpolation
"$NB_C_BIN" -mat bigcell.mat -hkl P1.hkl -lambda 1 -N 1 -distance 1000 -detsize 100 -pixel 0.1
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
- **Default precision: float32** (configurable via explicit dtype override; use float64 for gradient checks)
- Batching support for memory management

## ⚡ Common Commands & Workflow

To improve efficiency, use these standard commands for common tasks.

### Testing Commands
- **List all available tests:**
  `pytest --collect-only`
- **Run the full test suite:**
  `env KMP_DUPLICATE_LIB_OK=TRUE pytest -v` (run from the repository root)
- **Run acceptance tests:**
  `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_*.py -v`
- **Run parallel validation tests (C-PyTorch equivalence):**
  `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_parallel_*.py -v`
- **Run a specific test function:**
  `# Format: pytest -v <file_path>::<ClassName>::<test_function_name>`
  `pytest -v tests/test_suite.py::TestTier1TranslationCorrectness::test_simple_cubic_reproduction`
- **Install the package in editable mode:**
  `pip install -e .`

### Debugging Commands
- **Run the pixel trace debug script:**
  `KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py`
- **Generate C trace for debugging:**
  ```bash
  # 1. Add printf statements to nanoBragg.c for variables of interest
  # 2. Recompile: make -C golden_suite_generator
  # 3. Run with test parameters:
  ./golden_suite_generator/nanoBragg [parameters] 2>&1 | grep "TRACE_C:" > c_trace.log
  ```
- **Compare golden reference data:**
  See [`tests/golden_data/README.md`](./tests/golden_data/README.md) for exact commands
- **Lint parity coverage documentation:**
  `python scripts/lint_parity_coverage.py`
  Validates spec → matrix → YAML consistency and identifies missing coverage

## Domain-Specific Context

This is scientific simulation software for **X-ray crystallography** and **small-angle scattering (SAXS)**. Key physical concepts:
- **Bragg diffraction**: Constructive interference from crystal lattice
- **Structure factors**: Fourier transform of electron density
- **Mosaicity**: Crystal imperfection modeling
- **Ewald sphere**: Geometric construction for diffraction condition

The software is used in structural biology, materials science, and synchrotron/X-ray free-electron laser facilities.
