# Global Project Conventions

**Status:** Authoritative Specification

This document is the single source of truth for conventions that apply across the entire nanoBragg-PyTorch codebase. All components MUST adhere to these rules.

---

## 1. Unit System

- **Internal Calculation Standard:** All internal PyTorch calculations **MUST** use:
  - **Length:** Angstroms (Å)
  - **Angles:** Radians
- **Configuration Interface:** User-facing parameters in configuration classes (e.g., `DetectorConfig`) **MUST** be specified in:
  - **Length:** Millimeters (mm)
  - **Angles:** Degrees
- **Golden Trace Interface (for Testing):** The instrumented C-code trace logs have their own unit conventions that **MUST** be handled during testing:
  - `DETECTOR_PIX0_VECTOR`: **Meters (m)**. Tests must convert this to Angstroms (`* 1e10`) before comparison.
  - *Add other trace-specific units here as they are discovered.*

---

## 2. Coordinate Systems & Indexing

- **Lab Frame:** Right-handed system.
  - **Origin:** Sample position `(0,0,0)`.
  - **Primary Axis:** Beam travels along the `+X` axis (MOSFLM convention).
- **Pixel Indexing:**
  - **Order:** `(slow, fast)`. This corresponds to `(row, column)` in a 2D tensor.
  - **Reference Point:** Integer indices `(s, f)` refer to the **leading edge/corner** of the pixel area. This is a critical C-code compatibility requirement.
  - **`torch.meshgrid`:** All calls to `torch.meshgrid` **MUST** use `indexing="ij"` to conform to this convention.

---

## 3. Project Glossary

- **Beam Center:** A 2D coordinate `(s, f)` in pixels representing the intersection of the direct beam with the detector plane.
- **Pixel Origin:** The 3D coordinate corresponding to the integer index `(s, f)`. Per the convention above, this refers to the *leading edge* of the pixel.