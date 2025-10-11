# C15 Cluster: Mixed Units Zero Intensity

**STAMP:** 20251011T193829Z
**Phase:** M3 (post-Phase M2 validation)
**Cluster ID:** C15
**Category:** Mixed Units Zero Intensity
**Status:** → Phase M3 (implementation bug, needs callchain investigation)

---

## Executive Summary

**Classification:** Implementation Bug (edge case, zero signal produced)

Comprehensive mixed-units test (`test_at_parallel_015.py::test_mixed_units_comprehensive`) produces zero intensity output when combining unit conversions across detector geometry (mm), crystal cell (Å), and wavelength (Å). Unit conversion helpers appear correct in isolation, but the integration produces no diffraction signal.

**Impact:** Specific combination of unit scales causes simulation to produce empty image. This suggests either:
1. Unit conversion boundary condition (e.g., underflow/overflow)
2. Geometry calculation error with mixed-scale inputs
3. Culling logic incorrectly rejecting all reflections

**Priority:** P2.2 (High — edge case, but core functionality affected)

---

## Failure Summary

**Total Failures:** 1

### Affected Test

**Test:** `test_at_parallel_015.py::TestATParallel015::test_mixed_units_comprehensive`

**Purpose:** Validates that simulator correctly handles inputs specified in mixed units (detector in mm, crystal/wavelength in Å, as per hybrid unit system in ADR-01).

**Failure Mode:** Output image contains all zeros; no diffraction spots present. Expected: Non-zero intensity matching C-code reference.

**Observed Behavior:**
- Simulation runs without errors or warnings
- Image dimensions correct
- All pixel values = 0.0 (no signal)
- No culling warnings or geometry errors logged

---

## Reproduction Commands

### Minimal Targeted Reproduction
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_015.py::TestATParallel015::test_mixed_units_comprehensive
```

**Expected:** FAILED (zero intensity, assertion error on max(image) > threshold)

### With Trace Debugging (Recommended Next Step)
```bash
env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py \
    --cell 100 100 100 90 90 90 \
    --lambda 1.0 \
    --distance 100 \
    --detpixels 128 \
    --pixel_size 0.1 \
    --default_F 100 \
    --trace_pixel 64 64 \
    --compare_c
```

**Goal:** Generate step-by-step C vs PyTorch trace to identify first divergence point in unit-sensitive calculations.

---

## Technical Details

### Suspected Code Paths

**High Probability:**
1. **Scattering vector calculation** (`simulator.py`, q-vector computation)
   - Requires Å→m conversion for physics
   - Detector coords in meters, wavelength in Å
   - Incorrect conversion factor could zero out q-vectors

2. **dmin culling** (`simulator.py`, resolution limit check)
   - Uses stol (sinθ/λ) with mixed units
   - Off-by-orders-of-magnitude error could reject all reflections

3. **Solid angle calculation** (`simulator.py`, Ω factor)
   - Depends on detector distance and pixel size (meters)
   - Incorrect unit conversion could produce zero Ω

4. **Structure factor lookup** (`crystal.py`, F_cell interpolation)
   - Uses reciprocal space coordinates (Å⁻¹)
   - Out-of-bounds access returns default_F or zero

**Medium Probability:**
5. **Lattice shape factors** (`utils/physics.py`, sincg/sinc3 functions)
   - Uses Miller indices (h,k,l) — dimensionless, unlikely culprit
   - But could be affected by upstream q-vector errors

**Low Probability:**
6. **Unit conversion helpers** (`utils/units.py`)
   - Previously validated in isolation
   - Unlikely to be wrong, but worth re-checking

### Spec Reference

**arch.md §ADR-01 (Hybrid Unit System):**
> "Detector geometry (distance, pixel size, pix0_vector, pixel coordinates) uses meters internally to match C semantics and avoid Å-scale precision issues. Physics computations (q, stol, shape factors) operate in Angstroms. Conversion at the interface: pixel coords [m] × 1e10 → [Å]."

**Key Conversion Points:**
- Detector distance: CLI in mm → config in mm → detector in meters → physics interface multiplies by 1e10 for Å
- Pixel size: CLI in mm → config in mm → detector in meters → physics interface multiplies by 1e10 for Å
- Wavelength: CLI in Å → config in Å → physics uses directly (no conversion)
- Cell parameters: CLI in Å → config in Å → crystal uses directly (no conversion)

**Hypothesis:** The "physics interface" conversion (pixel coords × 1e10) may be missing or applied incorrectly in one code path.

---

## Debugging Strategy (Callchain Investigation)

### Phase 1: Reproduce with Trace
Generate parallel traces (C and PyTorch) for minimal mixed-units case:
```bash
# C trace (instrumented binary)
NB_C_BIN=./golden_suite_generator/nanoBragg ./golden_suite_generator/nanoBragg \
    -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100 -detpixels 128 \
    -pixel 0.1 -default_F 100 -floatfile c_output.bin 2>&1 | grep "TRACE_C:" > c_trace.log

# PyTorch trace
python scripts/debug_pixel_trace.py --cell 100 100 100 90 90 90 --lambda 1.0 \
    --distance 100 --detpixels 128 --pixel_size 0.1 --default_F 100 \
    --trace_pixel 64 64 > py_trace.log
```

**Deliverable:** `c_trace.log` and `py_trace.log` with line-by-line variable dumps.

### Phase 2: Identify First Divergence
Compare traces using `scripts/compare_traces.py` (or manual diff):
```bash
diff -y c_trace.log py_trace.log | less
```

**Key Variables to Check:**
- `pixel_coords` (should be in meters in Detector, Å in physics)
- `q_vector` (Å⁻¹)
- `stol` (Å⁻¹, = 0.5 * |q|)
- `dmin` threshold (Å)
- `h, k, l` (Miller indices, dimensionless)
- `F_latt` (lattice shape factor)
- `F_cell` (structure factor)
- `I_pixel` (final intensity)

**Goal:** Find first line where C and PyTorch diverge numerically.

### Phase 3: Fix and Validate
Once divergence point identified:
1. Fix incorrect unit conversion or formula
2. Re-run trace to confirm convergence
3. Re-run `test_mixed_units_comprehensive` to confirm pass
4. Run C-vs-PyTorch parity check (correlation ≥0.999)

---

## Test Coverage

### Existing Test (Failing)
- `test_at_parallel_015.py::test_mixed_units_comprehensive` — Mixed-units integration test

### Additional Tests Needed (Post-Fix)
1. **Detector-in-mm smoke test** — Verify basic simulation with detector in mm, cell in Å
2. **Unit conversion boundary test** — Very small/large values (test for underflow/overflow)
3. **Parity matrix expansion** — Add mixed-units row to AT-PARALLEL suite

---

## Hypotheses (Ranked by Likelihood)

### H1: Missing Å→m Conversion (HIGH)
**Theory:** Pixel coordinates from Detector (meters) not multiplied by 1e10 when passed to physics functions expecting Ångströms.

**Evidence:** Zero intensity suggests q-vectors or distances are off by orders of magnitude.

**Test:** Insert assertion in simulator.py checking `q_vector` magnitude is reasonable (~1 Å⁻¹ for typical diffraction).

**Fix Location:** `simulator.py`, `get_pixel_coords()` call site or physics interface.

### H2: dmin Culling Error (HIGH)
**Theory:** dmin threshold incorrectly converted or compared, causing all reflections to be culled.

**Evidence:** No warnings logged, but zero intensity consistent with "nothing passes culling".

**Test:** Temporarily disable dmin culling (`dmin=0` or comment out check), see if signal appears.

**Fix Location:** `simulator.py`, dmin culling logic (if-statement comparing stol vs threshold).

### H3: Solid Angle Zero (MEDIUM)
**Theory:** Ω calculation produces zero due to unit mismatch (e.g., `R` in wrong units).

**Evidence:** Ω=0 would zero out all intensities mathematically.

**Test:** Add debug print for `Ω` values in simulator; check if non-zero.

**Fix Location:** `simulator.py`, solid angle calculation (Ω = pixel²/R² * ...).

### H4: Reciprocal Space OOB (LOW)
**Theory:** All (h,k,l) indices fall outside structure factor grid, returning zeros.

**Evidence:** Would require massive unit error (unlikely to pass other tests).

**Test:** Check if `get_structure_factor()` returns default_F or 0 for all pixels.

**Fix Location:** `crystal.py`, structure factor lookup or grid bounds.

---

## Exit Criteria

- [ ] Parallel trace generated (C vs PyTorch) for mixed-units case
- [ ] First divergence point identified with specific variable and line number
- [ ] Root cause diagnosed (unit conversion error, culling bug, etc.)
- [ ] Fix implemented and unit-tested
- [ ] `test_at_parallel_015.py::test_mixed_units_comprehensive` PASSES
- [ ] C-code parity validated (correlation ≥0.999)
- [ ] Architecture documentation updated if ADR-01 requires clarification
- [ ] Additional test coverage added to prevent regression

---

## Code Locations

**Primary Suspects:**
- `src/nanobrag_torch/simulator.py` (q-vector calculation, dmin culling, Ω calculation)
- `src/nanobrag_torch/models/detector.py` (`get_pixel_coords()` return units)
- `src/nanobrag_torch/utils/units.py` (conversion helpers)

**Secondary:**
- `src/nanobrag_torch/models/crystal.py` (structure factor lookup)
- `src/nanobrag_torch/utils/physics.py` (lattice shape factors)

**Testing:**
- `tests/test_at_parallel_015.py` (failing test)
- `tests/test_units.py` (unit conversion validation)
- `scripts/debug_pixel_trace.py` (trace generation tool)

**Documentation:**
- `docs/architecture/README.md` (Trace Instrumentation Rule)
- `docs/debugging/debugging.md` (Parallel trace-driven debugging SOP)
- `arch.md` (ADR-01 Hybrid Unit System)

---

## Spec/Arch References

- **arch.md §ADR-01:** Hybrid Unit System (Detector in meters, physics in Angstroms)
- **specs/spec-a-core.md §3:** Units & Geometry (normative unit definitions)
- **docs/architecture/README.md §⚠️:** Trace Instrumentation Rule (reuse production helpers in traces)
- **docs/debugging/debugging.md §3:** Parallel Trace-Driven Debugging (mandatory SOP for physics discrepancies)

---

## Related Fix Plan Items

- **[UNIT-CONV-001]:** In progress; this cluster is the primary blocker
- **[VECTOR-PARITY-001]:** Mixed-units case may fall under Tap 5.3 scope (deferred pending this resolution)

---

## Artifacts Expected

- **Parallel Trace:** `reports/2026-01-test-suite-triage/phase_m3/20251011T193829Z/mixed_units/{c_trace.log, py_trace.log, divergence_analysis.md}`
- **Hypothesis Testing:** Per-hypothesis test results (H1, H2, H3, H4) in `hypothesis_results.md`
- **Implementation PR:** Code fix with line-by-line explanation of unit conversion correction
- **Passing Validation:** `pytest -v tests/test_at_parallel_015.py` → 100% pass
- **Parity Check:** C vs PyTorch correlation ≥0.999 for mixed-units case
- **Documentation Updates:** arch.md ADR-01 clarifications if needed

---

**Status:** → Phase M3 (blocked on callchain investigation). Requires trace-driven debugging per debugging.md SOP before implementation can proceed.

**Phase M3 Classification:** Implementation bug requiring diagnostic phase (trace generation + hypothesis testing) followed by targeted fix. Estimated effort: 4-6 hours (trace generation: 1-2h, diagnosis: 2-3h, fix + validation: 1-2h).

**Next Owner:** Assign to [VECTOR-PARITY-001] callchain specialist or ralph with explicit directive to follow parallel trace SOP from debugging.md §3.
