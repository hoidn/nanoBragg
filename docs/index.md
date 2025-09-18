# Project Documentation Index

Welcome to the central index for all `nanoBragg-PyTorch` project documentation. This guide provides a map to the key technical specifications, development processes, and historical records that define the project.

---

## 🏛️ Permanent Documentation

These are the core, living documents that guide the project.

### Core Project Guides
* **[CLAUDE.md](../CLAUDE.md)** - The primary instruction set for the AI agent.
* **[README.md](../README.md)** - The main project entry point.
* **[PROJECT_STATUS.md](../PROJECT_STATUS.md)** - Tracks the current active development initiative.

### Architecture & Design (`docs/architecture/`)
* **[Architecture Hub](./architecture/README.md)** - The central navigation point for all architectural documentation.
* **[C Code Overview](./architecture/c_code_overview.md)** - Original C codebase structure and design patterns.
* **[C Function Reference](./architecture/c_function_reference.md)** - Function-by-function porting guide.
* **[C Parameter Dictionary](./architecture/c_parameter_dictionary.md)** - Complete mapping of C command-line parameters.
* **[Conventions](./architecture/conventions.md)** - Coding and design conventions.
* **[Detector Component](./architecture/detector.md)** - Detailed detector component specification with hybrid unit system.
* **[Parameter Trace Analysis](./architecture/parameter_trace_analysis.md)** - End-to-end parameter flow for gradient interpretation.
* **[PyTorch Design](./architecture/pytorch_design.md)** - Core PyTorch implementation architecture.
* **[Undocumented Conventions](./architecture/undocumented_conventions.md)** - Living document of implicit C-code behaviors.

### Development Process (`docs/development/`)
* **[C to PyTorch Config Map](./development/c_to_pytorch_config_map.md)** - Critical configuration mapping between C and PyTorch.
* **[Contributing Guidelines](./development/CONTRIBUTING.md)** - How to contribute to the project.
* **[Debugging Guide](./development/debugging.md)** - General debugging workflows and strategies.
* **[Detector Fix Phase 2 Session](./development/detector_fix_phase2_session.md)** - Detailed debugging session log.
* **[Detector Geometry Debugging](./development/detector_geometry_debugging.md)** - Specific detector geometry debugging guide.
* **[Detector Rotation Debugging Session](./development/detector_rotation_debugging_session.md)** - Rotation-specific debugging session.
* **[Implementation Plan](./development/implementation_plan.md)** - Phased development roadmap.
* **[Lessons in Differentiability](./development/lessons_in_differentiability.md)** - Key learnings about maintaining gradient flow.
* **[Project Status](./development/PROJECT_STATUS.md)** - Current development status (duplicate link).
* **[Testing Strategy](./development/testing_strategy.md)** - Three-tier validation approach.

### Debugging Resources (`docs/debugging/`)
* **[Detector Geometry Checklist](./debugging/detector_geometry_checklist.md)** - ⚠️ **MANDATORY** checklist before debugging detector issues.

### User Guides (`docs/user/`)
* **[Migration Guide](./user/migration_guide.md)** - Guide for migrating from C to PyTorch version.
* **[Performance Guide](./user/performance.md)** - Performance optimization and benchmarking.
* **[Rotation Usage](./user/rotation_usage.md)** - How to use rotation features correctly.
* **[CLI Quickstart](./user/cli_quickstart.md)** - Installing and running the PyTorch CLI.

### Development Checklists (`docs/development/checklists/`)
* **[Checklist 1](./development/checklists/checklist1.md)** - Development checklist.

---

## 🗄️ Archival Documentation

This collection provides the historical context of the project's development.

* **[Historical Debugging Sessions](../history/)** - Detailed logs of past debugging sessions and their resolutions.
* **[Initiatives & Feature Plans](../initiatives/)** - Plans, checklists, and findings for major development efforts.
* **[Reports & Analysis](../reports/)** - Milestone summaries, performance reports, and investigation findings.

---

## 🔍 Quick Navigation

### By Priority
1. **[Detector Geometry Debugging Checklist](./debugging/detector_geometry_checklist.md)** - Start here for detector issues
2. **[C to PyTorch Config Map](./development/c_to_pytorch_config_map.md)** - Essential for configuration parity
3. **[Undocumented Conventions](./architecture/undocumented_conventions.md)** - Critical implicit behaviors

### By Task
- **Debugging detector issues?** → [Detector Geometry Checklist](./debugging/detector_geometry_checklist.md)
- **Porting C code?** → [C Function Reference](./architecture/c_function_reference.md)
- **Understanding architecture?** → [Architecture Hub](./architecture/README.md)
- **Setting up development?** → [Implementation Plan](./development/implementation_plan.md)

---

*Last updated: Generated on demand by `/update-docs` command*
