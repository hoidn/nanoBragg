# nanoBragg PyTorch Implementation Plan

**Version:** 1.0  
**Date:** 2023-10-27  
**Project Lead:** [Your Name/Team]

## 1. Introduction

This document outlines the phased implementation plan for translating `nanoBragg.c` into a new PyTorch-based application. The plan is structured to build the application from the ground up, starting with foundational utilities and progressively assembling them into the final, complete simulator.

Each phase represents a logical grouping of tasks and serves as a major milestone. A phase is not considered complete until all its associated code is implemented and all corresponding tests (as defined in `Testing_Strategy.md`) are passing.

**Prerequisites:**
*   The `C_Architecture_Overview.md`, `C_Parameter_Dictionary.md`, and `C_Function_Reference.md` documents are complete and have been reviewed.
*   The `PyTorch_Architecture_Design.md` and `Testing_Strategy.md` documents are complete and have been approved.
*   The "Golden C Code" test suite (instrumented C code, golden output images, and debug logs) has been generated.

## 1.1. Prerequisite - Developer Environment Setup

To support a consistent and maintainable development process, a `CONTRIBUTING.md` file and a `requirements.txt` file will be created as the first task. These will provide clear instructions for new developers on how to:
1.  Create a Python virtual environment.
2.  Install all necessary dependencies (e.g., `torch`, `pytest`, `fabio`).
3.  Run the complete test suite to verify their setup.
4.  Adhere to code formatting standards (e.g., `black`, `isort`).

## 3. Development Phases & Tasks

### Phase 1: Foundation & Utilities

**Goal:** Create the low-level, reusable building blocks for geometry and physics calculations. This phase is critical as all subsequent components will depend on it.

*   **Task 1.1: Implement Geometry Utilities (`utils/geometry.py`)**
    *   **Description:** Create vectorized PyTorch functions for all core 3D vector operations.
    *   **Functions to Implement:** `dot_product`, `cross_product`, `unitize`, `rotate_axis`, `rotate_umat`, etc.
    *   **Reference:** `C_Function_Reference.md` for the original C function logic.
    *   **Definition of Done:** All functions are implemented and pass their corresponding unit tests as defined in `Testing_Strategy.md` (Tier 1).

*   **Task 1.2: Implement Physics Utilities (`utils/physics.py`)**
    *   **Description:** Create vectorized PyTorch functions for the physical models.
    *   **Functions to Implement:** `sincg`, `sinc3`, `polarization_factor`.
    *   **Note:** The random number generators from the C code (`poidev`, `gaussdev`) will be replaced by their native PyTorch equivalents (`torch.poisson`, `torch.randn`) and do not need to be re-implemented here.
    *   **Definition of Done:** All functions are implemented and pass their corresponding unit tests.

### Phase 2: Core Data Models

**Goal:** Structure the simulation's state and parameters into logical, object-oriented classes.

*   **Task 2.1: Define Configuration Dataclasses (`config.py`)**
    *   **Description:** Create the `CrystalConfig`, `DetectorConfig`, and `BeamConfig` Python `dataclasses`.
    *   **Reference:** `C_Parameter_Dictionary.md` for the complete list of parameters, their types, and default values.
    *   **Definition of Done:** All parameters from the dictionary are represented in the dataclasses. Code is reviewed for correctness.

*   **Task 2.2: Implement the `Detector` Class (`models/detector.py`)**
    *   **Description:** Implement the `Detector` class, which takes a `DetectorConfig` object. It should calculate and cache its basis vectors (`fdet_vec`, etc.) and implement the `get_pixel_coords()` method to generate the tensor of all pixel coordinates.
    *   **Reference:** `PyTorch_Architecture_Design.md` and the geometry setup logic in the C `main` function.
    *   **Definition of Done:** The class is implemented and passes its component-level tests (verifying its calculated geometry against the golden C debug logs).

*   **Task 2.3: Implement the `Crystal` Class (`models/crystal.py`)**
    *   **Description:** Implement the `Crystal` class, which takes a `CrystalConfig` object. It should calculate its base reciprocal vectors and include methods for loading HKL data and applying rotations.
    *   **Reference:** `PyTorch_Architecture_Design.md` and the crystal setup logic in the C `main` function.
    *   **Definition of Done:** The class is implemented and passes its component-level tests (verifying its calculated vectors against the golden C debug logs).

### Phase 3: The Simulator & Application

**Goal:** Assemble the components into a working simulator and create the user-facing entry point.

*   **Task 3.1: Implement the `Simulator` Class (`simulator.py`)**
    *   **Description:** This is the most complex task. Implement the `Simulator` class and its `run()` method, focusing on the vectorization strategy outlined in the architecture design. This involves preparing inputs, expanding dimensions for broadcasting, performing the vectorized physics calculations, and summing the results.
    *   **Reference:** `PyTorch_Architecture_Design.md` and the main simulation loop in `nanoBragg.c`.
    *   **Definition of Done:** The `run()` method is implemented. Initial "smoke tests" (running without crashing) are successful. Full correctness will be verified in the next step.

*   **Task 3.2: Integration Testing**
    *   **Description:** Write and pass the full integration tests for the `Simulator`. This involves running the complete simulation for each case in the "Golden Test Suite" and comparing the final output image to the golden C-generated image.
    *   **Reference:** `Testing_Strategy.md` (Tier 1).
    *   **Definition of Done:** The PyTorch simulator produces numerically identical (within tolerance) images to the C code for all test cases.

*   **Task 3.3: Implement the Main Executable (`main.py`)**
    *   **Description:** Create the final user-facing script. This includes setting up `argparse` to parse all command-line arguments, instantiating the config dataclasses, creating and running the `Simulator`, and saving the output image.
    *   **Definition of Done:** The script can be run from the command line and successfully produces a diffraction image.

### Phase 4: Advanced Features & Validation

**Goal:** Implement and test the new differentiable capabilities and perform final scientific validation.

*   **Task 4.1: Implement Differentiable Parameters**
    *   **Description:** Refactor the configuration and model classes to ensure that key physical parameters can be passed as `torch.Tensor` objects with `requires_grad=True`.
    *   **Definition of Done:** The `Simulator` can run with learnable tensors as input without error.

*   **Task 4.2: Gradient Testing**
    *   **Description:** Write and pass the gradient tests for all designated learnable parameters using `torch.autograd.gradcheck`.
    *   **Reference:** `Testing_Strategy.md` (Tier 2).
    *   **Definition of Done:** The analytical gradients computed by PyTorch match the numerical finite-difference gradients for all tested parameters.

*   **Task 4.3: Scientific Validation**
    *   **Description:** Perform the final sanity checks to ensure the model is physically reasonable.
    *   **Reference:** `Testing_Strategy.md` (Tier 3).
    *   **Tasks:**
        *   Implement and pass the "First Principles" tests.
        *   (Optional) Implement and pass the "Cross-Validation" test.
    *   **Definition of Done:** The model's output is confirmed to be physically correct in idealized scenarios.

## 4. Reproducibility & RNG Policy

To ensure deterministic and reproducible results, all stochastic kernels will accept an optional `torch.Generator` instance. Tests will pin a fixed seed (e.g., `seed=0`) to ensure bit-wise reproducibility. The `Simulator` class will accept an optional `seed` integer to initialize this generator.

## 5. Continuous Integration (CI)

A CI pipeline will be established using GitHub Actions to automate testing. The workflow will be defined in `.github/workflows/test.yaml` and will run `pytest -q --durations=10` on every push and pull request.