# Project Documentation Index

Welcome to the central index for all `nanoBragg-PyTorch` project documentation. This guide provides a map to the key technical specifications, development processes, and historical records that define the project.

The documentation is organized into two main categories:

* **🏛️ Permanent Documentation:** Living documents that define the current state, architecture, and processes of the project. **These are essential for all contributors.**
* **🗄️ Archival Documentation:** A historical record of plans, debugging sessions, and reports. Valuable for understanding project evolution and the context behind design decisions.

---

## 🚀 Audience-Based Entry Points

To get started quickly, find your role below and follow the recommended reading path.

### For New Developers
*Start here to understand the project's foundations.*
1. **[Architecture Hub](./architecture/README.md)**: The central navigation point for all technical specifications.
2. **[C-CLI to PyTorch Configuration Map](./development/c_to_pytorch_config_map.md)**: ⚠️ **CRITICAL** - Understand how C and PyTorch configurations align to prevent common bugs.
3. **[Testing Strategy](./development/testing_strategy.md)**: Learn how to validate your work against the C reference.
4. **[Global Conventions](./architecture/conventions.md)**: The universal rules for units, coordinate systems, etc.

### For Current Contributors
*Quick links for day-to-day development.*
1. **[PROJECT_STATUS.md](../PROJECT_STATUS.md)**: Check the current active initiative and progress.
2. **[Detector Geometry Debugging Checklist](./debugging/detector_geometry_checklist.md)**: ⚠️ **MANDATORY** before tackling any detector correlation issues.
3. **[Undocumented C Conventions](./architecture/undocumented_conventions.md)**: A living log of implicit C-code behaviors.

### For Debugging & Historical Context
*Understand why things are the way they are.*
1. **[Historical Debugging Session Map](../history/debugging_session_relationship_map.md)**: A visual timeline and guide to all past debugging efforts.
2. **[The 8-Phase Detector Debugging Saga](../history/2025-01-09_detector-geometry-8-phase-debug.md)**: A masterclass in systematic, parallel-trace debugging.

---

## 🏛️ Permanent Documentation

These are the core, living documents that guide the project.

### Core Project Guides
* **[CLAUDE.md](../CLAUDE.md)** - The primary instruction set for the AI agent, containing critical implementation rules.
* **[README.md](../README.md)** - The main project entry point and high-level overview.
* **[PROJECT_STATUS.md](../PROJECT_STATUS.md)** - Tracks the current active development initiative.

### Architecture & Design (`docs/architecture/`)
* **[Architecture Hub](./architecture/README.md)** - The central navigation point for all architecture and design documentation.
* **[Global Project Conventions](./architecture/conventions.md)** - Defines the universal unit system, coordinate frames, and indexing rules.
* **[PyTorch Design](./architecture/pytorch_design.md)** - Outlines the core software architecture, vectorization strategy, and class design for the PyTorch port.
* **[Detector Specification](./architecture/detector.md)** - ⚠️ **CRITICAL** - Authoritative specification for the Detector, including its essential hybrid unit system (meters internally).
* **[Undocumented C Conventions](./architecture/undocumented_conventions.md)** - A living document capturing implicit C-code behaviors discovered during debugging.
* **[C-Code Overview](./architecture/c_code_overview.md)** - High-level explanation of the reference C implementation's structure and non-standard physics conventions.
* **[C Parameter Dictionary](./architecture/c_parameter_dictionary.md)** - A definitive reference for all command-line parameters accepted by `nanoBragg.c`.

### Development Process (`docs/development/`)
* **[C-CLI to PyTorch Configuration Map](./development/c_to_pytorch_config_map.md)** - ⚠️ **CRITICAL** - The authoritative source for configuration parity between `nanoBragg.c` and PyTorch.
* **[Testing Strategy](./development/testing_strategy.md)** - Defines the three-tier testing approach and the canonical commands for generating golden data.
* **[Debugging Guidelines](./development/debugging.md)** - The official methodology for debugging, centered on the mandatory parallel trace comparison rule.
* **[Detector Geometry Debugging Checklist](./debugging/detector_geometry_checklist.md)** - ⚠️ **MANDATORY** - A time-saving checklist of common pitfalls and solutions for detector correlation issues.
* **[Lessons in Differentiability](./development/lessons_in_differentiability.md)** - A valuable case study and guide to avoiding common PyTorch gradient pitfalls.
* **[CONTRIBUTING.md](./development/CONTRIBUTING.md)** - Standard guide for setting up the development environment and contributing.

### User Guides (`docs/user/`)
* **[Rotation Usage Guide](./user/rotation_usage.md)** - How to use the crystal rotation and mosaicity features.
* **[Performance Guide](./user/performance.md)** - Performance analysis and recommendations for users.
* **[Migration Guide](./user/migration_guide.md)** - Guide for transitioning to new features like dynamic geometry.

---

## 🗄️ Archival Documentation

This collection provides the historical context of the project's development. It is not required for daily work but is invaluable for understanding the rationale behind current design choices.

### Historical Debugging Sessions (`history/`)
* **[Debugging Session Relationship Map](../history/debugging_session_relationship_map.md)** - **Best entry point for the archive.** A visual timeline and detailed index of all major debugging sessions related to detector geometry.
* **[Example Session: 8-Phase Investigation](../history/2025-01-09_detector-geometry-8-phase-debug.md)** - A comprehensive log of a ~10-hour systematic debugging effort that precisely localized a critical bug.

### Initiative & Feature Plans (`initiatives/` and `plans/`)
* **[Initiatives Directory](../initiatives/)**: Contains detailed plans, checklists, and findings for major development efforts, such as the `detector-correlation-fix` and `parallel-trace-validation` initiatives.
* **[Plans Directory](../plans/)**: Contains older or feature-specific plans, such as for implementing `cellparams` and `rotation`.

### Reports & Analysis (`reports/`)
* **[Reports Directory](../reports/)**: Contains analysis reports, performance benchmarks, milestone summaries, and summaries of outstanding issues. Examples include `milestone1_summary.md` and `TILTED_DETECTOR_ROOT_CAUSE_ANALYSIS.md`.