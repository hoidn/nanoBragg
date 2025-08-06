# nanoBragg PyTorch Architecture Hub

**This is the central navigation point for all architecture and design documentation.**

## Start Here

1. **[Global Project Conventions](./conventions.md)** - Units, coordinate systems, and universal rules
2. **[C-Code Overview](./c_code_overview.md)** - Understanding the reference implementation
3. **[PyTorch Design](./pytorch_design.md)** - Overall system architecture and vectorization strategy

## Component Specifications

These documents are the **authoritative specifications** for each major component. They override global conventions where explicitly stated.

### Core Components
- **[Detector](./detector.md)** ⚠️ - **CRITICAL: Uses hybrid unit system (meters internally)**
  - Pixel coordinate generation
  - Rotation sequences and pivot modes
  - Convention-dependent geometry
  
- **[Crystal](./crystal.md)** *(Phase 2)* - Crystal lattice and orientation
  - Unit cell parameters
  - Misset rotations
  - Reciprocal space calculations

- **[Simulator](./simulator.md)** *(Phase 3)* - Main simulation engine
  - Integration of all components
  - Physics calculations
  - Intensity accumulation

### Utility Modules
- **[Geometry Utilities](./geometry_utils.md)** - Vector operations and rotations
- **[Physics Utilities](./physics_utils.md)** - Scattering calculations and corrections

## Critical Implementation Notes

### ⚠️ Unit System Exceptions
While the global rule states "all calculations use Angstroms," the following exceptions apply:
- **Detector geometry**: Uses meters internally (see [Detector spec](./detector.md#61-critical-hybrid-unit-system))
- **User interfaces**: Accept millimeters for distances, degrees for angles

### ⚠️ Non-Standard Physics Conventions
- **Miller indices**: Calculated using real-space vectors, not reciprocal (see [C-Code Overview](./c_code_overview.md#71-critical-non-standard-miller-index-calculation))
- **F_latt calculation**: Uses fractional indices `(h-h0)` (see [C-Code Overview](./c_code_overview.md#72-critical-f_latt-calculation))

## Development Workflow

1. **Before implementing any component**:
   - Read the global conventions
   - Read the specific component contract
   - Check for any non-standard behaviors
   
2. **During implementation**:
   - Follow the parallel trace validation strategy
   - Verify units at component boundaries
   - Test against canonical golden data

3. **After implementation**:
   - Update component documentation with lessons learned
   - Add any newly discovered conventions
   - Create regression tests for edge cases

## Quick Reference

### Where to Find Key Information

| Topic | Primary Document | Key Section |
|-------|-----------------|-------------|
| Unit conversions | [Global Conventions](./conventions.md) | Section 2 |
| Detector pivot modes | [Detector](./detector.md) | Section 8.1 |
| Miller index calculation | [C-Code Overview](./c_code_overview.md) | Section 7.1 |
| Golden test commands | [Testing Strategy](../development/testing_strategy.md) | Section 2.2 |
| Debugging methodology | [Detector Debugging Case Study](../development/detector_geometry_debugging.md) | Full document |

## Navigation

- **Up**: [Main docs](../README.md)
- **Testing**: [Development docs](../development/)
- **C-Code Analysis**: [Function reference](./c_function_reference.md), [Parameter dictionary](./c_parameter_dictionary.md)