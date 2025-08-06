### **Agent Implementation Checklist: Phase 1 - Prerequisite Setup & Golden Data Generation**

**Overall Goal for this Phase:** To prepare the configuration, testing infrastructure, and ground-truth data required for the core implementation.

**Instructions for Agent:**
1.  Copy this checklist into your working memory.
2.  Update the `State` for each item as you progress: `[ ]` (Open) -> `[P]` (In Progress) -> `[D]` (Done).
3.  Follow the `How/Why & API Guidance` column carefully for implementation details.

---

| ID | Task Description | State | How/Why & API Guidance |
| :--- | :--- | :--- | :--- |
| **Section 0: Preparation & Context Priming** |
| 0.A | **Review Key Documents** | `[ ]` | **Why:** To load the necessary context and technical specifications before coding. <br> **Docs:** `plans/geometry/plan_geometry.md`, `plans/geometry/implementation_geometry.md`. |
| 0.B | **Identify Target Files for Modification** | `[ ]` | **Why:** To have a clear list of files that will be touched during this phase. <br> **Files:** `src/nanobrag_torch/config.py` (Modify), `tests/test_crystal_geometry.py` (Create), `CLAUDE.md` (Modify), `tests/golden_data/triclinic_P1/` (Create directory and contents). |
| **Section 1: Update Configuration** |
| 1.A | **Expand `CrystalConfig`** | `[ ]` | **Why:** To support general triclinic cell definitions and reproducible mosaic generation. <br> **How:** Add the fields below to the `CrystalConfig` dataclass. <br> **File:** `src/nanobrag_torch/config.py`. <br> **Fields to add:** <br> - `cell_a: float = 100.0` <br> - `cell_b: float = 100.0` <br> - `cell_c: float = 100.0` <br> - `cell_alpha: float = 90.0` <br> - `cell_beta: float = 90.0` <br> - `cell_gamma: float = 90.0` <br> - `mosaic_seed: Optional[int] = None` |
| **Section 2: Golden Data Generation** |
| 2.A | **Create `triclinic_P1` Directory** | `[ ]` | **Why:** To organize all artifacts for the new golden test case. <br> **Command:** `mkdir -p tests/golden_data/triclinic_P1` |
| 2.B | **Generate `triclinic_P1` Golden Image** | `[ ]` | **Why:** To create the ground-truth diffraction pattern for the new test case. <br> **How:** Run the C `nanoBragg` executable with a known triclinic cell. <br> **Command:** `./nanoBragg -cell 70 80 90 75 85 95 -hkl P1.hkl -default_F 100 -N 5 -lambda 1.0 -detpixels 512 -floatfile tests/golden_data/triclinic_P1/image.bin` |
| 2.C | **Generate `triclinic_P1` Trace Log** | `[ ]` | **Why:** To create the ground-truth log of intermediate calculations for debugging and validation. <br> **How:** Run the instrumented C `nanoBragg` executable with the `-dump_pixel` and `-dump_geometry` flags. <br> **Command:** `./nanoBragg -cell 70 80 90 75 85 95 -hkl P1.hkl -default_F 100 -N 5 -lambda 1.0 -detpixels 512 -dump_pixel 256 256 -dump_geometry > tests/golden_data/triclinic_P1/trace.log` |
| 2.D | **Create `params.json`** | `[ ]` | **Why:** To document the exact conditions used to generate the golden data, ensuring reproducibility. <br> **How:** Create a new JSON file with the generation parameters. <br> **File:** `tests/golden_data/triclinic_P1/params.json`. <br> **Content:** `{ "c_code_commit_hash": "<git rev-parse HEAD>", "compiler_version": "<gcc --version>", "command": "./nanoBragg ...", "cell": [70, 80, 90, 75, 85, 95], "lambda": 1.0, "N_cells": 5, "detpixels": 512 }` |
| 2.E | **Create `regenerate_golden.sh`** | `[ ]` | **Why:** To provide a single, executable script for regenerating all golden artifacts for this test case. <br> **File:** `tests/golden_data/triclinic_P1/regenerate_golden.sh`. <br> **Content:** A shell script containing the commands from tasks 2.B and 2.C. |
| **Section 3: Testing Infrastructure** |
| 3.A | **Create New Test File** | `[ ]` | **Why:** To create a dedicated location for the new geometry-related tests. <br> **How:** Create an empty file `tests/test_crystal_geometry.py` with a basic class structure. <br> **Content:** `import pytest\nclass TestCrystalGeometry:\n    def test_placeholder(self):\n        pass` |
| **Section 4: Documentation** |
| 4.A | **Update `CLAUDE.md`** | `[ ]` | **Why:** To formally document the crystallographic conventions used in the project, preventing future ambiguity. <br> **How:** Add a new section titled "Crystallographic Conventions" to `CLAUDE.md`. <br> **Content:** "This project adheres to the `|G| = 1/d` convention, where `G = h*a* + k*b* + l*c*`. This is equivalent to the `|Q| = 2π/d` convention where `Q = 2πG`. All tests and calculations must be consistent with this standard." |
| **Section 5: Finalization** |
| 5.A | **Code Formatting & Linting** | `[ ]` | **Why:** To maintain code quality. <br> **How:** Run `black .` and `ruff . --fix` on all modified files. |
| 5.B | **Commit Phase 1 Work** | `[ ]` | **Why:** To checkpoint the completion of the setup phase. <br> **Commit Message:** `feat(geometry): Phase 1 - Add config and golden data for triclinic cell` |

---

**Success Test (Acceptance Gate):**
*   The `triclinic_P1` artifacts are produced in `tests/golden_data/triclinic_P1/`.
*   The `trace.log` includes numeric values for `a,b,c,a*,b*,c*,V` with ≥15 significant digits.
*   `CLAUDE.md` is updated with the `|G|=1/d` convention.
*   `src/nanobrag_torch/config.py` contains the updated `CrystalConfig`.
