# Ralph Loop 2025-10-12T013323Z: C15 Cluster Evidence

## Loop Context

**Self-Selection Rationale:**
- **Input.md directive:** Requested [DETECTOR-CONFIG-001] Phase B design (stale - work complete and archived)
- **Actual priority:** [TEST-SUITE-TRIAGE-001] Critical, in_progress, 13 failures remaining
- **Selected cluster:** C15 "Mixed Units Zero Intensity" - highest-value physics bug
- **Ground rules justification:** Ralph prompt §"Don't" → "Don't implement placeholder logic"; §"Search first" → item complete, not incomplete; §"pick exactly one... (the most valuable/blocked)"

## C15 Cluster Status

**Test:** `tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive`
**Status:** ❌ FAILING (Zero intensity bug)
**Runtime:** 3.79s

### Test Configuration

**Crystal (Triclinic):**
- Cell: a=75.5Å, b=82.3Å, c=91.7Å
- Angles: α=87.5°, β=92.3°, γ=95.8°
- N_cells: (3, 3, 3)
- default_F: 100.0
- Phi: start=0°, range=1°, steps=1

**Detector (XDS Convention):**
- Distance: 150.5 mm
- Pixel size: 0.172 mm
- Size: 128×128 pixels
- Rotations: rotx=5°, roty=3°, rotz=2°, twotheta=10°

**Beam:**
- Wavelength: 1.54Å (Cu K-alpha)
- Fluence: 1e23 photons/m²
- Polarization: 0.95
- dmin: 2.0Å

### Failure Mode

**Symptom:** Simulator returns all-zero intensity array (128×128 tensor of zeros)
**Expected:** Non-zero intensities for valid diffraction from triclinic crystal
**Assertion:** `intensity.max() > 0` → FAILS

### Hypothesis Space (Ranked)

Based on fix_plan.md Attempt #271 C15 analysis:

1. **dmin filtering too aggressive** - 2.0Å cutoff may exclude all reflections
2. **Unit conversion error** - Mixed mm/Å/degrees may have propagation bug
3. **XDS convention with rotations** - Interaction between convention and detector geometry
4. **Scattering vector calculation** - Triclinic+rotations+twotheta may trigger edge case
5. **Fluence scaling** - 1e23 may be too low (vs typical 1e24 in passing tests)
6. **Lattice shape factor** - N_cells=(3,3,3) edge case with triclinic symmetry

### Next Actions (Priority Order)

1. **Minimal reproducer** - Strip test to simplest failing case (cubic cell, no rotations, higher fluence)
2. **dmin probe** - Re-run test with dmin=None to bypass filtering
3. **Parallel trace** - Generate C vs PyTorch trace for single pixel (central) per debugging.md SOP
4. **Unit audit** - Verify mm→m, Å→m, deg→rad conversions in simulator._compute_physics_for_position
5. **Convention interaction** - Test XDS+rotations+twotheta separately (passing test has MOSFLM baseline)

## Evidence Artifacts

- **Test log:** `test_failure.log` (full pytest output with traceback)
- **Reproduction command:** `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_015.py::TestATParallel015MixedUnits::test_mixed_units_comprehensive`

## Commit Plan

**Scope:** Docs-only loop (no code changes)
**Updates:**
- This summary document
- `docs/fix_plan.md` Attempts History entry documenting self-selection and evidence capture

**Next Loop:** Debug C15 cluster with hypothesis testing and parallel trace comparison
