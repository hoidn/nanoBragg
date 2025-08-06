# Project Status

## 📍 Current Active Initiative

**Name:** General Detector Geometry
**Path:** `plans/active/general-detector-geometry/`
**Branch:** `feature/general-detector-geometry` (baseline: feature/crystal-orientation-misset)
**Started:** 2025-08-05
**Current Phase:** Phase 3: Golden Test Case Generation (Phase 2 Complete ✅)
**Progress:** ████████░░░░░░░░ 40%
**Next Milestone:** Generate cubic_tilted_detector golden test case with nanoBragg.c
**R&D Plan:** `plans/active/general-detector-geometry/plan.md`
**Implementation Plan:** `plans/active/general-detector-geometry/implementation.md`

## 📋 Previous Initiative

**Name:** Crystal Orientation Misset
**Path:** `plans/active/crystal-orientation-misset/`
**Branch:** `feature/crystal-orientation-misset` (baseline: feature/general-triclinic-cell-params)
**Started:** 2025-01-20
**Current Phase:** Phase 2: Crystal Integration & Trace Validation ✅ (Completed)
**Progress:** ████████░░░░░░░░ 50%
**Next Milestone:** Simulator integration with phi and misset rotations working together
**R&D Plan:** `plans/active/crystal-orientation-misset/plan.md`
**Implementation Plan:** `plans/active/crystal-orientation-misset/implementation.md`

## 🎯 Current Initiative Objective

Replace the static detector with a fully configurable, general-purpose model that derives its geometry from user-provided parameters. This will enable simulation of realistic experimental setups with varying detector distances, positions, and orientations, making it possible to compare simulations against real-world experimental data.

## 📊 Key Success Metrics

- cubic_tilted_detector test achieves ≥0.990 Pearson correlation with golden image
- All detector geometry parameters (distance, beam center, rotations, twotheta) pass gradient checks
- No regression in existing tests (simple_cubic must continue to pass)
- Detector basis vectors match C-code trace values with atol=1e-9
- Complete geometric transformation pipeline: detector rotations → twotheta → positioning in 3D space