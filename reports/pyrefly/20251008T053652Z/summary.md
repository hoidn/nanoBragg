# Pyrefly Static Analysis Summary — Phase B

**Scan Date:** 2025-10-08T05:46:01Z
**Commit:** 8ca885f95dfca23d8a3e3867af3f5aefff7f40a3
**Branch:** feature/spec-based-2
**Tool:** pyrefly 0.35.0
**Python:** 3.13.7
**Mode:** Evidence-only baseline scan (no fixes applied)

## Overview

Pyrefly found **78 errors** across **8 files** in the `src/` directory. Exit code: **1** (violations detected). The scan was executed per `prompts/pyrefly.md` SOP Phase B.

**Artifacts:**
- Full log: `reports/pyrefly/20251008T053652Z/pyrefly.log`
- Environment: `reports/pyrefly/20251008T053652Z/env.json`
- Commands: `reports/pyrefly/20251008T053652Z/commands.txt`

## Findings by Severity

### Blocker Issues (Breaking Type Safety / Likely Runtime Errors)

These violations indicate serious type mismatches that could cause runtime failures or violate differentiability contracts:

#### 1. **Unsupported Operations (29 errors)** — Rule: `unsupported-operation`

Most critical cluster involves tensor power operations (`**`) which appear to be false positives from pyrefly not recognizing torch.Tensor's `__pow__` implementation:

**Power operations (likely false positives, verify with runtime):**
- `src/nanobrag_torch/io/mask.py:250:20` — `dist_s**2` (4 errors total for dist_s**2 + dist_f**2)
- `src/nanobrag_torch/simulator.py:1658:48` — `pixel_coords_meters**2` (2 errors)
- `src/nanobrag_torch/simulator.py:1814:23` — `masked_pixels ** 2` (2 errors)

**Division by None (actual bugs):**
- `src/nanobrag_torch/models/detector.py:86:32` — `config.beam_center_s / config.pixel_size_mm` (beam_center_s can be None)
- `src/nanobrag_torch/models/detector.py:87:32` — `config.beam_center_f / config.pixel_size_mm` (beam_center_f can be None)
- `src/nanobrag_torch/models/detector.py:262:29` — `beam_s_mm / self.config.pixel_size_mm` (beam_s_mm can be None)
- `src/nanobrag_torch/models/detector.py:263:29` — `beam_f_mm / self.config.pixel_size_mm` (beam_f_mm can be None)
- `src/nanobrag_torch/models/detector.py:275:26` — `beam_f_mm / 1000.0` (beam_f_mm can be None)
- `src/nanobrag_torch/models/detector.py:276:26` — `beam_s_mm / 1000.0` (beam_s_mm can be None)
- `src/nanobrag_torch/models/detector.py:510:26` — `self.config.beam_center_f / 1000.0` (beam_center_f can be None)
- `src/nanobrag_torch/models/detector.py:511:26` — `self.config.beam_center_s / 1000.0` (beam_center_s can be None)
- `src/nanobrag_torch/models/detector.py:514:25` — `self.config.beam_center_f / 1000.0` (beam_center_f can be None)
- `src/nanobrag_torch/models/detector.py:515:25` — `self.config.beam_center_s / 1000.0` (beam_center_s can be None)

**Multiplication/Addition with None (actual bugs):**
- `src/nanobrag_torch/simulator.py:1650:31` — `self.detector.config.detector_abs_um * 1e-6` (detector_abs_um can be None)
- `src/nanobrag_torch/simulator.py:585:31` — `roi_ymax+1` (roi_ymax can be None)
- `src/nanobrag_torch/simulator.py:587:34` — `roi_xmax+1` (roi_xmax can be None)
- `src/nanobrag_torch/simulator.py:1133:22` — `roi_ymax+1` (roi_ymax can be None)
- `src/nanobrag_torch/simulator.py:1135:25` — `roi_xmax+1` (roi_xmax can be None)

**Unary negation on None:**
- `src/nanobrag_torch/simulator.py:922:41` — `-source_directions` (source_directions can be None)
- `src/nanobrag_torch/simulator.py:1010:41` — `-source_directions` (source_directions can be None)

**Subscripting None:**
- `src/nanobrag_torch/simulator.py:1273:55,77,99` — `pix0[0/1/2]` (3 errors, pix0 can be None)
- `src/nanobrag_torch/simulator.py:1353:34` — `pixel_coords_meters[target_slow, target_fast]` (pixel_coords_meters can be None)

#### 2. **Bad Argument Types (26 errors)** — Rule: `bad-argument-type`

**Tensor vs scalar mismatches (design decision needed):**
- `src/nanobrag_torch/__main__.py:983:38` — `wavelength_m` (Tensor | float) → `read_sourcefile` expects float
- `src/nanobrag_torch/__main__.py:1028:42` — `wavelength_m` (Tensor | float) → `generate_sources_from_divergence_dispersion` expects float
- `src/nanobrag_torch/__main__.py:1175:31` — `detector_config.pixel_size_mm` (Tensor | float) → `write_smv` expects float (8 total smv.write_smv calls with Tensor|float arguments)
- `src/nanobrag_torch/simulator.py:678-680` — `N_cells_{a,b,c}` (Tensor) → `compute_physics_for_position` expects int (3 errors)
- `src/nanobrag_torch/simulator.py:685:25` — `self.kahn_factor` (Tensor) → `compute_physics_for_position` expects float
- `src/nanobrag_torch/simulator.py:250-252` — `Na/Nb/Nc` (int) → `sincg` expects Tensor (3 errors)
- `src/nanobrag_torch/simulator.py:362,388` — `kahn_factor` (float) → polarization_factor expects Tensor (2 errors)

**None vs required type:**
- `src/nanobrag_torch/simulator.py:365,391` — `polarization_axis` (Tensor | None) → polarization_factor expects Tensor (2 errors)
- `src/nanobrag_torch/simulator.py:539:39` — `self.beam_config.source_directions` (None) → `.to()` requires Tensor
- `src/nanobrag_torch/simulator.py:547:33,557:55` — `len(self.beam_config.source_directions)` (None not Sized, 2 errors)
- `src/nanobrag_torch/models/detector.py:767:17` — `self.pix0_vector` (Tensor | None) → `torch.allclose` requires Tensor

#### 3. **Missing Attributes (7 errors)** — Rule: `missing-attribute`

**NoneType attribute access (actual bugs):**
- `src/nanobrag_torch/models/detector.py:144:36` — `self.pix0_vector.clone()` (pix0_vector can be None)
- `src/nanobrag_torch/models/detector.py:787:40` — `self.pix0_vector.clone()` (pix0_vector can be None)
- `src/nanobrag_torch/models/detector.py:812:25` — `self.pix0_vector.unsqueeze(0)` (pix0_vector can be None)
- `src/nanobrag_torch/simulator.py:539:39` — `self.beam_config.source_directions.to(...)` (source_directions can be None)

**bool vs Tensor (actual bugs):**
- `src/nanobrag_torch/simulator.py:314:26` — `dmin_mask.unsqueeze(-1)` (dmin_mask is bool, not Tensor)
- `src/nanobrag_torch/simulator.py:316:26` — `dmin_mask.unsqueeze(-1)` (dmin_mask is bool, not Tensor)

**Missing interpolation_enabled attribute:**
- `src/nanobrag_torch/__main__.py:1093:13` — `crystal.interpolation_enabled = ...` (Crystal has no such attribute)

### High Priority (Design Violations)

#### 4. **Read-Only Property Assignment (8 errors)** — Rule: `read-only`

These violate PyTorch's @property pattern for `device` attributes:

- `src/nanobrag_torch/models/crystal.py:55:13,57:13,127:13` — `self.device = ...` (3 errors in Crystal)
- `src/nanobrag_torch/models/detector.py:46:13,48:13,216:13` — `self.device = ...` (3 errors in Detector)
- `src/nanobrag_torch/simulator.py:490:13,492:13` — `self.device = ...` (2 errors in Simulator)

**Note:** These might be intentional pattern violations; verify against differentiability requirements (CLAUDE.md rule 10).

#### 5. **Bad Assignments (4 errors)** — Rule: `bad-assignment`

- `src/nanobrag_torch/__main__.py:863:45` — `tuple[@_, ...]` not assignable to `misset_deg: tuple[float, float, float]`
- `src/nanobrag_torch/io/hkl.py:51:9` — `float | int` not assignable to `int` (cycle-breaking inconsistency)
- `src/nanobrag_torch/models/crystal.py:722:13` — `Tensor | float` not assignable to `float` (cycle-breaking inconsistency)
- `src/nanobrag_torch/simulator.py:512:44` — `Tensor` not assignable to attribute with type `Never`

### Medium Priority (Return Type Violations)

#### 6. **Bad Returns (3 errors)** — Rule: `bad-return`

- `src/nanobrag_torch/simulator.py:425:12` — Returns `tuple[Tensor | Unknown, Tensor | None]` but declared return type is `Tensor`
- `src/nanobrag_torch/io/mosflm.py:156:12` — Returns `tuple[floating[Any], ..., Any]` but declared as `tuple[float, ..., float]`
- `src/nanobrag_torch/utils/auto_selection.py:28:6` — Missing explicit return on some paths (function declared to return `SamplingParams`)

### Low Priority (Function Definition)

#### 7. **Bad Function Definitions (1 error)** — Rule: `bad-function-definition`

- `src/nanobrag_torch/simulator.py:35:104` — Default `None` not assignable to parameter `crystal_get_structure_factor` with type `Callable[[Tensor, Tensor, Tensor], Tensor]`

## Findings by File

### src/nanobrag_torch/simulator.py (36 errors)

**Primary issues:**
- Unsupported operations on potential None values (roi_ymax/xmax, source_directions, pixel_coords_meters)
- Bad argument types (Tensor vs int/float in physics calculations)
- Read-only device assignments (2 errors)
- Return type mismatch (intensity tuple)
- Missing return path (bad-function-definition)

**Recommendation:** Triage into:
1. None-safety violations (add assertions/guards at entry points)
2. Tensor/scalar type contract enforcement (decide on strict scalar I/O vs tensor-native)
3. Device property refactor (align with CLAUDE.md rule on @property pattern)

### src/nanobrag_torch/models/detector.py (17 errors)

**Primary issues:**
- Division by None (beam_center_s/f can be None, 10 errors)
- Read-only device assignments (3 errors)
- NoneType attribute access on pix0_vector (3 errors)
- Bad argument to torch.allclose (1 error)

**Recommendation:** Add explicit None checks for beam_center_s/f before arithmetic operations; verify pix0_vector initialization contract.

### src/nanobrag_torch/__main__.py (14 errors)

**Primary issues:**
- Bad argument types passing Tensor | float to functions expecting scalar float (smv.write_smv, sourcefile readers)
- Tuple type mismatch on misset_deg assignment
- Missing Crystal.interpolation_enabled attribute

**Recommendation:** Decide boundary enforcement strategy: either add `.item()` calls at I/O boundaries (breaking gradients) or refactor called functions to accept Tensor | float.

### src/nanobrag_torch/io/mask.py (4 errors)

**Primary issues:**
- Tensor `**` operations flagged as unsupported (likely false positive)

**Recommendation:** Verify runtime behavior; if tests pass, mark as deferred/known-false-positive.

### src/nanobrag_torch/models/crystal.py (4 errors)

**Primary issues:**
- Read-only device assignments (3 errors)
- Bad assignment (Tensor | float → float in cycle-breaking context)

**Recommendation:** Same as Detector — align device property pattern with arch.

### Other Files (3 errors total)

- `src/nanobrag_torch/io/hkl.py:51` — float | int → int inconsistency
- `src/nanobrag_torch/io/mosflm.py:156` — Return type precision mismatch (floating[Any] vs float)
- `src/nanobrag_torch/utils/auto_selection.py:28` — Missing return path

## Deferred Items (Potential False Positives)

**Tensor `**` operations (mask.py, simulator.py):** Pyrefly may not recognize torch.Tensor's `__pow__` method. Verify with:
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -k "mask" -v
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -k "solid_angle" -v  # exercises pixel_coords_meters**2
```

If tests pass without `AttributeError` or `TypeError`, annotate these as known pyrefly limitations and defer.

## Next Steps (Phase C Triage)

1. **Immediate Blockers (delegate to Ralph):**
   - None-safety violations in detector.py (beam_center arithmetic) and simulator.py (roi operations, source_directions, pix0)
   - Missing Crystal.interpolation_enabled attribute (CLI breakage)
   - Return type mismatch in simulator.py:425 (likely affects test assertions)

2. **Design Decisions (galph):**
   - Tensor vs scalar boundary enforcement strategy (affects 26 bad-argument-type errors)
   - Device property refactor approach (read-only violations — @property vs manual setters)

3. **Test Coverage Validation:**
   - Run collect-only to identify which pytest nodes exercise the flagged code paths:
     ```bash
     pytest --collect-only -q tests/test_models.py tests/test_simulator.py tests/test_at_*.py
     ```

4. **Artifact Handoff:**
   - Update `docs/fix_plan.md` STATIC-PYREFLY-001 Attempt #2 with this summary
   - Prepare `input.md` Do Now for Ralph with top 2-3 blocker fixes and reproduction commands

## Command Reference

**Reproduce this scan:**
```bash
pyrefly check src | tee reports/pyrefly/20251008T053652Z/pyrefly.log
```

**Exit code:** 1 (violations detected)

**Re-run after fixes:**
```bash
mkdir -p reports/pyrefly/$(date -u +%Y%m%dT%H%M%SZ)
pyrefly check src | tee reports/pyrefly/$(date -u +%Y%m%dT%H%M%SZ)/pyrefly.log
# Compare against baseline using diff or custom script
```

---

**End of Summary** — Phase B Complete
**Next Phase:** C (Triage & Prioritisation) per `plans/active/static-pyrefly.md`
