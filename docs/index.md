# Project Documentation Index

Welcome to the central index for all `nanoBragg-PyTorch` project documentation. This guide provides a map to the key technical specifications, development processes, and historical records that define the project.

---

## 🏛️ Permanent Documentation

These are the core, living documents that guide the project.

### Core Project Guides
* **[Index of Findings](./findings.md)** - Consolidated record of verified bugs, conventions, and parity gaps for quick recall.
### PyTorch Guardrails
* **[PyTorch Runtime Checklist](./development/pytorch_runtime_checklist.md)** – quick do/don’t list for vectorization and device placement. Always review before editing simulator code.
* **[PyTorch Design](./architecture/pytorch_design.md#vectorization-strategy)** – detailed explanation of the required broadcast shapes and batched flows.
* **[Testing Strategy §1.4](./development/testing_strategy.md#14-pytorch-device--dtype-discipline)** – required CPU/GPU smoke tests and compile checks.

* **[CLAUDE.md](../CLAUDE.md)** - The primary instruction set for the AI agent.
* **[README.md](../README.md)** - The main project entry point.
* **[README_PYTORCH.md](../README_PYTORCH.md)** - Comprehensive user guide for the PyTorch implementation, including CLI usage, parallel comparison tools, and visualization.
* **[PROJECT_STATUS.md](../PROJECT_STATUS.md)** - Tracks the current active development initiative.
* **[loop.sh](../loop.sh)** - Supervisory automation harness for Claude loops; treat as a protected asset (do **not** delete during hygiene passes).
* **[supervisor.sh](../supervisor.sh)** - Supervisor (galph) runner. Supports `--sync-via-git` for cross-machine turn taking; treat as a protected asset.
* **[input.md](../input.md)** - Supervisor→Engineer steering memo. Rewritten and committed each supervisor run; treat as a protected asset.

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
* **[Debugging Guide](./debugging/debugging.md)** - General debugging workflows and strategies.
* **[Documentation Sync SOP (Template)](../prompts/doc_sync_sop.md)** - Repeatable process to find/fix doc drift and keep SOPs aligned with tests.
* **[Detector Fix Phase 2 Session](./development/detector_fix_phase2_session.md)** - Detailed debugging session log.
* **[Detector Geometry Debugging](./debugging/detector_geometry_debugging.md)** - Specific detector geometry debugging guide.
* **[Detector Rotation Debugging Session](./development/detector_rotation_debugging_session.md)** - Rotation-specific debugging session.
* **[Implementation Plan](./development/implementation_plan.md)** - Phased development roadmap.
* **[Lessons in Differentiability](./development/lessons_in_differentiability.md)** - Key learnings about maintaining gradient flow.
* **[Project Status](./development/PROJECT_STATUS.md)** - Current development status (duplicate link).
* **[Testing Strategy](./development/testing_strategy.md)** - Three-tier validation approach.
* **[Validation Scripts](../scripts/validation/README.md)** - Reusable parity/validation helpers referenced by prompts and supervisor input; prefer these over ad‑hoc snippets when available.

### Debugging Resources (`docs/debugging/`)
* **[Detector Geometry Checklist](./debugging/detector_geometry_checklist.md)** - ⚠️ **MANDATORY** checklist before debugging detector issues.

### User Guides (`docs/user/`)
* **[CLI Quickstart](./user/cli_quickstart.md)** - Installing and running the PyTorch CLI.
* **[Known Limitations](./user/known_limitations.md)** - Current limitations and workarounds, including triclinic misset issues.
* **[Migration Guide](./user/migration_guide.md)** - Guide for migrating from C to PyTorch version.
* **[Performance Guide](./user/performance.md)** - Performance optimization and benchmarking.
* **[Rotation Usage](./user/rotation_usage.md)** - How to use rotation features correctly.

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
