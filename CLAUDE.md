# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains **nanoBragg**, a C-based diffraction simulator for nanocrystals, along with comprehensive documentation for a planned PyTorch port. The codebase consists of:

- **Core C simulators**: `nanoBragg.c` (main diffraction simulator), `nonBragg.c` (amorphous scattering), `noisify.c` (noise addition)
- **PyTorch port documentation**: Complete architectural design and implementation plan in `./torch/`
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

The `./torch/` directory contains a complete architectural design for a PyTorch reimplementation:

### Key Design Principles
- **Vectorization over loops**: Replace nested C loops with broadcasting tensor operations
- **Object-oriented structure**: `Crystal`, `Detector`, `Simulator` classes
- **Differentiable parameters**: Enable gradient-based optimization
- **GPU acceleration**: Leverage PyTorch's CUDA backend

### Critical Documentation Files
**Architecture & Design:**
- `PyTorch_Architecture_Design.md`: Core system architecture, vectorization strategy, class design, memory management
- `Implementation_Plan.md`: Phased development roadmap with specific tasks and deliverables
- `Testing_Strategy.md`: Three-tier validation approach (translation correctness, gradient correctness, scientific validation)

**C Code Analysis:**
- `C_Architecture_Overview.md`: Original C codebase structure, execution flow, and design patterns
- `C_Function_Reference.md`: Complete function-by-function reference with porting guidance
- `C_Parameter_Dictionary.md`: All command-line parameters mapped to internal C variables

**Advanced Topics:**
- `Parameter_Trace_Analysis.md`: End-to-end parameter flow analysis for gradient interpretation
- `processes.md`: Standard Operating Procedures for development workflow

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
**IMPORTANT**: For all non-trivial development tasks, consult `torch/processes.md` which contains comprehensive Standard Operating Procedures (SOPs) for:
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
- `torch/Implementation_Plan.md`: Detailed phase-by-phase development plan
- `torch/PyTorch_Architecture_Design.md`: System architecture and vectorization approach
- `torch/Testing_Strategy.md`: Comprehensive validation methodology

**Implementation Order:**
1. **Phase 1**: Implement utility functions (`utils/geometry.py`, `utils/physics.py`)
2. **Phase 2**: Build core data models (`Crystal`, `Detector` classes) 
3. **Phase 3**: Implement `Simulator` class and main executable
4. **Phase 4**: Add differentiable capabilities and validation

**Key Implementation Guidelines:**
- Use `torch/C_Function_Reference.md` for porting individual C functions
- Reference `torch/C_Parameter_Dictionary.md` for parameter mapping
- Consult `torch/Parameter_Trace_Analysis.md` for understanding gradient flow
- Follow testing strategy in `torch/Testing_Strategy.md` for validation

## Memory and Performance Considerations

### C Implementation
- Memory usage scales with detector size and simulation complexity
- CPU parallelization via OpenMP (typically 4-16 cores)
- Large structure factor tables cached in memory

### PyTorch Port
- Memory-intensive vectorization strategy with batching fallback
- GPU acceleration for tensor operations
- Configurable precision (float32/float64) and batching for memory management

## Domain-Specific Context

This is scientific simulation software for **X-ray crystallography** and **small-angle scattering (SAXS)**. Key physical concepts:
- **Bragg diffraction**: Constructive interference from crystal lattice
- **Structure factors**: Fourier transform of electron density
- **Mosaicity**: Crystal imperfection modeling
- **Ewald sphere**: Geometric construction for diffraction condition

The software is used in structural biology, materials science, and synchrotron/X-ray free-electron laser facilities.