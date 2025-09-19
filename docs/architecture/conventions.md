# Global Project Conventions

Status: Consolidated. Canonical definitions live in `specs/spec-a.md` (normative) and `arch.md` (ADR-backed). This file keeps only project-wide clarifications that aid PyTorch tensorization.

## 1) Units — See Spec/Arch

- Canonical units, conversions, and detector hybrid exceptions are defined in:
  - `specs/spec-a.md` (Units & Conversions; Geometry & Conventions)
  - `arch.md` (Sections on hybrid unit system and Geometry Model)
- This document does not restate those rules. When in doubt, defer to the spec/arch.

## 2) Coordinate Systems & Indexing (PyTorch specifics)

- Lab frame: right-handed; origin at sample. Primary beam axis per convention (see spec).
- Pixel indexing in tensors:
  - Order: `(slow, fast)` equals `(row, column)`.
  - Reference point: integer indices `(s,f)` refer to the leading edge/corner of the pixel area (matches C indexing expectations).
  - Always use `torch.meshgrid(indexing="ij")` to preserve `(slow,fast)` ordering.

## 3) Project Glossary (selected)

- Beam Center: `(s,f)` in pixels where the direct beam hits the detector.
- Pixel Origin: 3D coordinate corresponding to integer index `(s,f)`; by convention, refers to the pixel’s leading edge.
