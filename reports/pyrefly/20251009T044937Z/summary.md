# Pyrefly Static Analysis Triage — Phase C

**Triage Date:** 2025-12-22
**Baseline Scan:** 2025-10-08T05:46:01Z (`reports/pyrefly/20251008T053652Z/`)
**Commit:** 8ca885f95dfca23d8a3e3867af3f5aefff7f40a3
**Branch:** feature/spec-based-2
**Total Violations:** 78 errors across 8 files
**Triaged By:** galph/ralph supervisor loop #209

## Triage Summary

This document classifies the 78 pyrefly violations from the Phase B baseline scan into actionable severity buckets with owner assignments and pytest selectors for validation.

### Severity Buckets

| Severity | Count | Description | Action Plan |
|----------|-------|-------------|-------------|
| **BLOCKER** | 22 | None-safety violations causing runtime crashes | Fix immediately (Phase D delegation) |
| **HIGH** | 26 | Type contract violations (Tensor vs scalar) | Design decision required before fixes |
| **MEDIUM** | 16 | Property/return type violations | Refactor with test coverage |
| **DEFER** | 14 | Likely false positives (tensor `**` operations) | Validate runtime, mark as known limitation |

---

## BLOCKER Issues (22 errors) — Immediate Action Required

### BL-1: None Arithmetic in Detector Geometry (10 errors)
**File:** `src/nanobrag_torch/models/detector.py`
**Rule:** `unsupported-operation`
**Root Cause:** `beam_center_s` and `beam_center_f` can be None when not explicitly set via CLI
**Impact:** Runtime TypeError when computing beam center from None values

**Affected Lines:**
- L86:32 — `config.beam_center_s / config.pixel_size_mm`
- L87:32 — `config.beam_center_f / config.pixel_size_mm`
- L262:29 — `beam_s_mm / self.config.pixel_size_mm`
- L263:29 — `beam_f_mm / self.config.pixel_size_mm`
- L275:26 — `beam_f_mm / 1000.0`
- L276:26 — `beam_s_mm / 1000.0`
- L510:26 — `self.config.beam_center_f / 1000.0`
- L511:26 — `self.config.beam_center_s / 1000.0`
- L514:25 — `self.config.beam_center_f / 1000.0`
- L515:25 — `self.config.beam_center_s / 1000.0`

**Fix Strategy:**
Add explicit None checks at entry points (likely in `__init__` or property getters). Convention-specific defaults should be computed if values are None.

**Owner:** ralph (detector geometry module)
**Pytest Selector:** `pytest --collect-only -q tests/test_models.py::TestDetector -k "beam_center or pix0"`
**Validation Command:**
```bash
# After fix, verify these tests still pass
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_models.py::TestDetector -k "beam_center"
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_001.py  # Beam center scaling
```

---

### BL-2: ROI Bounds None Arithmetic (4 errors)
**File:** `src/nanobrag_torch/simulator.py`
**Rule:** `unsupported-operation`
**Root Cause:** `roi_ymax` and `roi_xmax` can be None when ROI not specified
**Impact:** Runtime TypeError when constructing ROI slices

**Affected Lines:**
- L585:31 — `roi_ymax+1`
- L587:34 — `roi_xmax+1`
- L1133:22 — `roi_ymax+1`
- L1135:25 — `roi_xmax+1`

**Fix Strategy:**
Guard ROI slice construction with `if roi_ymax is not None:` checks or set defaults during config initialization.

**Owner:** ralph (simulator core)
**Pytest Selector:** `pytest --collect-only -q tests/test_simulator.py -k "roi"`
**Validation Command:**
```bash
# After fix, verify ROI tests pass
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_simulator.py -k "roi"
# Also check full-frame tests (roi=None case)
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_012.py
```

---

### BL-3: Source Directions None Operations (2 errors)
**File:** `src/nanobrag_torch/simulator.py`
**Rule:** `unsupported-operation`
**Root Cause:** `source_directions` can be None when no divergence/dispersion specified
**Impact:** Runtime TypeError on unary negation

**Affected Lines:**
- L922:41 — `-source_directions`
- L1010:41 — `-source_directions`

**Fix Strategy:**
Add guard: `if source_directions is not None: k_in = -source_directions else: k_in = default_beam_direction`

**Owner:** ralph (beam/source module)
**Pytest Selector:** `pytest --collect-only -q tests/ -k "source or divergence"`
**Validation Command:**
```bash
# After fix, test single-source and multi-source cases
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_006.py  # Single reflection
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/ -k "divergence" -v
```

---

### BL-4: pix0_vector None Subscripting (4 errors)
**File:** `src/nanobrag_torch/simulator.py`, `src/nanobrag_torch/models/detector.py`
**Rule:** `unsupported-operation`, `missing-attribute`
**Root Cause:** `pix0_vector` can be None before detector geometry computed
**Impact:** Runtime TypeError/AttributeError

**Affected Lines:**
- simulator.py L1273:55,77,99 — `pix0[0/1/2]` subscript
- simulator.py L1353:34 — `pixel_coords_meters[target_slow, target_fast]`
- detector.py L144:36 — `self.pix0_vector.clone()`
- detector.py L787:40 — `self.pix0_vector.clone()`
- detector.py L812:25 — `self.pix0_vector.unsqueeze(0)`

**Fix Strategy:**
Ensure `pix0_vector` and `pixel_coords_meters` are always computed before use. Add assertions at call sites or move initialization earlier.

**Owner:** ralph (detector geometry)
**Pytest Selector:** `pytest --collect-only -q tests/test_models.py::TestDetector -k "pix0 or pixel_coords"`
**Validation Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_models.py::TestDetector::test_detector_pixel_coords
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_007.py  # Peak position with rotations
```

---

### BL-5: Missing Crystal.interpolation_enabled Attribute (1 error)
**File:** `src/nanobrag_torch/__main__.py`
**Rule:** `missing-attribute`
**Root Cause:** CLI tries to set `crystal.interpolation_enabled` but Crystal class doesn't have this attribute
**Impact:** Runtime AttributeError during CLI execution

**Affected Lines:**
- L1093:13 — `crystal.interpolation_enabled = ...`

**Fix Strategy:**
Add `interpolation_enabled` property to Crystal class or remove the assignment and rely on config-based initialization.

**Owner:** ralph (crystal model + CLI)
**Pytest Selector:** `pytest --collect-only -q tests/test_models.py::TestCrystal -k "interpolation"`
**Validation Command:**
```bash
# After fix, verify CLI runs without AttributeError
KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -default_F 1 -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100 -detpixels 128 -floatfile /tmp/test.bin
# Check interpolation tests
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/ -k "interpolation or tricubic"
```

---

### BL-6: Missing Return Path (1 error)
**File:** `src/nanobrag_torch/utils/auto_selection.py`
**Rule:** `bad-return`
**Root Cause:** Function declared to return `SamplingParams` but has code paths that don't return
**Impact:** Runtime returns None unexpectedly

**Affected Lines:**
- L28:6 — Missing explicit return on some paths

**Fix Strategy:**
Add explicit return or raise NotImplementedError on unhandled branches.

**Owner:** ralph (utils)
**Pytest Selector:** `pytest --collect-only -q tests/ -k "auto_selection or sampling"`
**Validation Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/ -k "sampling" -v
```

---

## HIGH Priority Issues (26 errors) — Design Decision Required

### H-1: Tensor vs Scalar Type Boundaries (26 errors)
**Files:** `src/nanobrag_torch/__main__.py`, `src/nanobrag_torch/simulator.py`
**Rule:** `bad-argument-type`
**Root Cause:** Mixing Tensor | float types at I/O boundaries
**Impact:** Type contract violations; potential gradient breaks if `.item()` added naively

**Categories:**

#### H-1a: CLI → I/O Functions (Tensor | float → float expected) — 10 errors
**Affected:**
- `__main__.py:983` — `wavelength_m` → `read_sourcefile`
- `__main__.py:1028` — `wavelength_m` → `generate_sources_from_divergence_dispersion`
- `__main__.py:1175-1185` — 8× `detector_config.{pixel_size_mm,distance_mm,...}` → `write_smv`

**Design Choice:**
1. **Option A (Break Gradients):** Add `.item()` at I/O boundaries → violates CLAUDE.md rule 9
2. **Option B (Preserve Gradients):** Refactor I/O functions to accept `Tensor | float` → preferred per arch.md §15

**Owner:** galph (design decision) → ralph (implementation)
**Pytest Selector:** `pytest --collect-only -q tests/ -k "smv or sourcefile"`
**Validation Command:**
```bash
# After decision, verify gradient tests still pass
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_gradients.py -k "wavelength or distance"
# And I/O tests
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/ -k "smv" -v
```

#### H-1b: Simulator → Physics Kernels (Tensor vs int/float) — 9 errors
**Affected:**
- `simulator.py:678-680` — `N_cells_{a,b,c}` (Tensor) → `compute_physics_for_position` expects int
- `simulator.py:685` — `kahn_factor` (Tensor) → expects float
- `simulator.py:250-252` — `Na/Nb/Nc` (int) → `sincg` expects Tensor
- `simulator.py:362,388` — `kahn_factor` (float) → `polarization_factor` expects Tensor
- `simulator.py:365,391` — `polarization_axis` (Tensor | None) → expects Tensor

**Design Choice:**
Physics kernels should be tensor-native (accept Tensor, broadcast internally). Convert scalars to tensors at call sites.

**Owner:** ralph (physics kernels)
**Pytest Selector:** `pytest --collect-only -q tests/test_utils.py -k "sincg or polarization"`
**Validation Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_utils.py::test_sincg
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/ -k "polarization" -v
```

#### H-1c: Detector Validation (None vs Tensor) — 7 errors
**Affected:**
- `simulator.py:539:39` — `source_directions.to(...)` when source_directions is None
- `simulator.py:547,557` — `len(source_directions)` when None
- `detector.py:767` — `torch.allclose(self.pix0_vector, ...)` when pix0_vector is None

**Fix Strategy:**
Add explicit None guards before operations requiring Tensor.

**Owner:** ralph (detector + simulator validation)
**Pytest Selector:** Same as BL-4 above

---

## MEDIUM Priority Issues (16 errors) — Refactor with Coverage

### M-1: Read-Only Device Property Violations (8 errors)
**Files:** `src/nanobrag_torch/models/crystal.py`, `detector.py`, `simulator.py`
**Rule:** `read-only`
**Root Cause:** Assigning to `self.device` when it's defined as @property
**Impact:** Violates PyTorch @property pattern; potential gradient breaks

**Affected Lines:**
- crystal.py L55,57,127 (3 errors)
- detector.py L46,48,216 (3 errors)
- simulator.py L490,492 (2 errors)

**Fix Strategy:**
Follow CLAUDE.md rule 10: Use @property for derived quantities. Remove direct assignments and compute device from config tensors.

**Owner:** ralph (models refactor)
**Pytest Selector:** `pytest --collect-only -q tests/test_models.py`
**Validation Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_models.py::TestCrystal::test_device_handling
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_models.py::TestDetector::test_device_handling
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_gradients.py  # Ensure gradients still flow
```

---

### M-2: Return Type Mismatches (3 errors)
**Files:** `src/nanobrag_torch/simulator.py`, `io/mosflm.py`
**Rule:** `bad-return`
**Impact:** Type contract violations in function signatures

**Affected:**
- simulator.py:425 — Returns tuple but declared as Tensor
- mosflm.py:156 — Returns floating[Any] but declared as float
- auto_selection.py:28 — Missing return (covered in BL-6)

**Fix Strategy:**
Align return type annotations with actual returned values.

**Owner:** ralph (type annotations)
**Pytest Selector:** `pytest --collect-only -q tests/ -k "mosflm or intensity"`
**Validation Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/ -k "mosflm" -v
```

---

### M-3: Bad Assignments (4 errors)
**Files:** `__main__.py`, `io/hkl.py`, `models/crystal.py`, `simulator.py`
**Rule:** `bad-assignment`
**Impact:** Type narrowing inconsistencies

**Affected:**
- `__main__.py:863` — tuple[@_, ...] → tuple[float, float, float]
- `hkl.py:51` — float | int → int
- `crystal.py:722` — Tensor | float → float
- `simulator.py:512` — Tensor → Never type

**Fix Strategy:**
Add explicit type narrowing or adjust annotations to match runtime behavior.

**Owner:** ralph (type cleanup)
**Pytest Selector:** `pytest --collect-only -q tests/test_io.py tests/test_models.py`
**Validation Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_io.py::test_hkl_loading
```

---

### M-4: Bad Function Definition (1 error)
**File:** `src/nanobrag_torch/simulator.py`
**Rule:** `bad-function-definition`
**Root Cause:** Default `None` not assignable to parameter expecting Callable

**Affected Lines:**
- L35:104 — `crystal_get_structure_factor` parameter default

**Fix Strategy:**
Use `Optional[Callable[...]]` annotation or provide non-None default.

**Owner:** ralph (simulator API)
**Pytest Selector:** `pytest --collect-only -q tests/test_simulator.py`
**Validation Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_simulator.py
```

---

## DEFER Bucket (14 errors) — Likely False Positives

### D-1: Tensor Power Operations (14 errors)
**Files:** `io/mask.py`, `simulator.py`
**Rule:** `unsupported-operation`
**Root Cause:** Pyrefly doesn't recognize `torch.Tensor.__pow__` method
**Impact:** None (runtime works correctly)

**Affected:**
- mask.py:250 — `dist_s**2`, `dist_f**2` (4 errors)
- simulator.py:1658 — `pixel_coords_meters**2` (2 errors)
- simulator.py:1814 — `masked_pixels ** 2` (2 errors)
- Similar patterns (6 more)

**Validation:**
```bash
# Verify runtime behavior is correct
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/ -k "mask" -v
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/ -k "solid_angle" -v
```

**Decision:** If tests pass without TypeError/AttributeError, mark as **known pyrefly limitation** and document in fix_plan. Do not fix.

**Owner:** n/a (documentation only)
**Artifact:** This triage summary serves as documentation

---

## Owner Assignment Summary

| Owner | Error Count | Priority | Modules |
|-------|-------------|----------|---------|
| ralph | 48 | BLOCKER+HIGH+MEDIUM | detector, simulator, crystal, CLI, I/O |
| galph | 26 | HIGH (design decision) | Type boundary strategy |
| n/a | 14 | DEFER | False positives (document only) |

---

## Delegation Plan for Phase D

### Ralph Backlog (Prioritized)

**Round 1: BLOCKERS (22 errors) — Estimated 2-3 loops**
1. BL-1: Detector None arithmetic (10 errors) — `detector.py` lines 86,87,262,263,275,276,510,511,514,515
2. BL-2: ROI bounds (4 errors) — `simulator.py` lines 585,587,1133,1135
3. BL-4: pix0_vector None (4 errors) — `detector.py` + `simulator.py`
4. BL-3: Source directions (2 errors) — `simulator.py` lines 922,1010
5. BL-5: Missing interpolation_enabled (1 error) — `__main__.py` line 1093
6. BL-6: Missing return path (1 error) — `auto_selection.py` line 28

**Round 2: HIGH (after galph design decision) — Estimated 3-4 loops**
7. H-1a: I/O boundary types (10 errors) — Pending design choice
8. H-1b: Physics kernel types (9 errors) — Make kernels tensor-native
9. H-1c: Validation guards (7 errors) — Add None checks

**Round 3: MEDIUM — Estimated 2 loops**
10. M-1: Device property refactor (8 errors) — All models
11. M-2: Return type fixes (3 errors)
12. M-3: Assignment type narrowing (4 errors)
13. M-4: Function definition (1 error)

### Galph Design Decision (HIGH priority, blocks H-1a)

**Question:** How should we handle Tensor | float at I/O boundaries?

**Options:**
- **A (Breaks Gradients):** Add `.item()` calls at I/O — violates arch.md §15 differentiability
- **B (Preserves Gradients):** Refactor I/O to accept `Tensor | float` — aligned with PyTorch best practices

**Recommendation:** Choose Option B. Update `io/smv.py`, `io/source.py` to accept `Tensor | float` and use `.item()` only at the final serialization step (when gradient flow no longer matters).

**Pytest Validation:**
```bash
# After decision, verify gradient flow preserved
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_gradients.py
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/ -k "smv" -v
```

---

## Pytest Selector Validation

All selectors validated with `--collect-only`:

```bash
# Blocker tests
pytest --collect-only -q tests/test_models.py::TestDetector -k "beam_center or pix0"
pytest --collect-only -q tests/test_simulator.py -k "roi"
pytest --collect-only -q tests/ -k "source or divergence"
pytest --collect-only -q tests/ -k "interpolation or tricubic"
pytest --collect-only -q tests/ -k "sampling"

# High priority tests
pytest --collect-only -q tests/ -k "smv or sourcefile"
pytest --collect-only -q tests/test_utils.py -k "sincg or polarization"

# Medium priority tests
pytest --collect-only -q tests/test_models.py
pytest --collect-only -q tests/ -k "mosflm"
pytest --collect-only -q tests/test_io.py
pytest --collect-only -q tests/test_simulator.py

# Defer validation
pytest --collect-only -q tests/ -k "mask"
pytest --collect-only -q tests/ -k "solid_angle"
```

---

## Artifact Structure

```
reports/pyrefly/20251009T044937Z/
├── summary.md              (this file)
├── commands.txt            (pytest validation commands)
└── env.json                (environment snapshot — to be added)
```

---

## Next Actions (Phase D)

1. **Galph:** Decide on H-1a type boundary strategy and document in input.md for next Ralph loop
2. **Ralph:** Start with BL-1 (detector None arithmetic) — highest error count, clearest fix
3. **Both:** After Round 1 blockers fixed, re-run pyrefly and compare delta against this baseline
4. **Documentation:** Update docs/fix_plan.md Attempt #4 with this triage summary reference

---

**End of Triage** — Phase C Complete
**Baseline:** `reports/pyrefly/20251008T053652Z/`
**Triage Artifacts:** `reports/pyrefly/20251009T044937Z/`
**Next Phase:** D (Delegation & Follow-up Hooks) per `plans/active/static-pyrefly.md`
