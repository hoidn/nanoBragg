# Phase C Trace Plan — VECTOR-PARITY-001
**Initiative:** Restore 4096² parity (≥0.999 correlation) for vectorization profiling unblock
**Phase:** C — Divergence Localisation
**Date:** 2025-10-10
**Status:** STAGING

---

## Question & Initiative Context

### Primary Trace Question
**Where does PyTorch first diverge from C-code for pixels with perfect ROI parity but catastrophic full-frame failure?**

The 4096² benchmark shows:
- Central ROI (512×512 @ indices 1792:2304): **perfect parity** (corr≈1.0, sum_ratio≈0.999987) ✅
- Full frame (4096²): **catastrophic failure** (corr≈0.063, sum_ratio≈225×) ❌

This paradox suggests:
1. **Core physics (geometry, scaling, lattice factors) agrees** where Bragg signal concentrates
2. **Edge/background handling diverges** where C intensity ≈0 but PyTorch intensity inflates 225×

### Hypothesis Prioritisation
Based on Phase B ROI evidence (`reports/2026-01-vectorization-parity/phase_b/20251010T035732Z/roi_scope.md`):

**H1: Edge overexposure / halo accumulation (HIGH PRIORITY)**
- **Observation:** PyTorch sum ≈225× C sum suggests accumulation in low-signal regions
- **Suspected subsystems:** Steps normalisation, solid angle calculation at detector edges, oversample handling
- **Trace focus:** Compare `steps`, `omega_pixel`, `solid_angle`, final intensity for edge pixels vs ROI pixels

**H2: Missing normalization factor (MEDIUM PRIORITY)**
- **Observation:** 225× inflation suggests missing 1/N division (e.g., sources, oversample², thicksteps)
- **Suspected subsystems:** Source weighting, oversample integration, thickness layer summation
- **Trace focus:** Count actual sources/phi/mosaic/oversample values; verify `steps` calculation matches spec §4–5

**H3: Boundary condition artifacts (LOW PRIORITY unless H1/H2 cleared)**
- **Observation:** Full-frame correlation tools may include zero-padding or edge masking differences
- **Suspected subsystems:** Image I/O, boundary pixel handling in simulator
- **Trace focus:** Inspect pixels at detector corners (0,0), (4095,4095), (0,4095), (4095,0)

### Spec/Arch Anchors
- **Canonical equations:** `specs/spec-a-core.md` §4 (Sampling & Sources), §5 (Scaling & Intensity Aggregation)
- **Implementation contract:** `arch.md` §8 (Physics Model & Scaling), §15 (Differentiability — no silent normalization changes)
- **Runtime checklist:** `docs/development/pytorch_runtime_checklist.md` #4 (Source weighting: equal-weight contract)
- **Parallel trace SOP:** `docs/debugging/debugging.md` §2 (Workflow SOP-4.1), Trace Schema (variable names, units, precision)

---

## Target ROI & Pixel Selection

### ROI Strategy
Use **three pixel classes** to map divergence geography:

| Class | Indices (slow, fast) | Purpose | Expected Behavior |
|-------|---------------------|---------|-------------------|
| **ROI Center** | (2048, 2048) | Validate known-good path | Perfect C↔Py match (corr≈1.0) |
| **ROI Edge** | (1792, 2048) or (2304, 2048) | Transition zone | Should still agree if H1 applies only to far edges |
| **Frame Edge** | (4095, 2048) or (2048, 4095) | Divergence locus | Where intensity inflation manifests |

**Rationale:**
Phase B4a confirmed central ROI meets spec thresholds. By sampling ROI→edge→far-edge, we can identify the **first pixel coordinate** where C vs Py intensities diverge beyond tolerance.

**Selected Pixels (concrete coordinates):**
1. **ROI center:** `(slow=2048, fast=2048)` — on-peak (if Bragg signal present), baseline trace
2. **ROI boundary:** `(slow=1792, fast=2048)` — first row outside ROI, test edge sensitivity
3. **Far edge:** `(slow=4000, fast=2048)` — near detector limit, probe inflation hypothesis

### Acceptance Criteria (per pixel)
- **Perfect match:** |Py intensity − C intensity| / C intensity ≤ 0.001 (0.1% relative error)
- **Trace alignment:** All tap points (pix0_vector, basis, q, hkl, F, omega, steps) agree to ≥12 significant digits
- **First Divergence identification:** Document the **first variable name** where C vs Py differ beyond float64 precision

---

## Instrumentation Scope

### C Trace Edits (golden_suite_generator/nanoBragg.c)

**Target variables (trace print statements):**

```c
// Add at end of pixel loop (after intensity calculation, before image write)
if (spixel == <SELECTED_SLOW> && fpixel == <SELECTED_FAST>) {
    fprintf(stderr, "TRACE_C: pixel_idx (%d, %d)\n", spixel, fpixel);
    fprintf(stderr, "TRACE_C: pix0_vector %.15e %.15e %.15e [m]\n",
            pix0_vector[1], pix0_vector[2], pix0_vector[3]);
    fprintf(stderr, "TRACE_C: pixel_pos %.15e %.15e %.15e [m]\n",
            pixel_X, pixel_Y, pixel_Z);
    fprintf(stderr, "TRACE_C: diffracted_vec %.15e %.15e %.15e\n",
            diffracted[1], diffracted[2], diffracted[3]);
    fprintf(stderr, "TRACE_C: scattering_vec_A_inv %.15e %.15e %.15e\n",
            scattering[1], scattering[2], scattering[3]);
    fprintf(stderr, "TRACE_C: hkl_frac %.15e %.15e %.15e\n", h, k, l);
    fprintf(stderr, "TRACE_C: F_cell %.15e\n", F_cell);
    fprintf(stderr, "TRACE_C: F_latt %.15e\n", F_latt);
    fprintf(stderr, "TRACE_C: omega_pixel %.15e [sr]\n", omega_pixel);
    fprintf(stderr, "TRACE_C: polar %.15e\n", polar);
    fprintf(stderr, "TRACE_C: steps %d\n", steps);
    fprintf(stderr, "TRACE_C: I_term %.15e\n", I);
    fprintf(stderr, "TRACE_C: final_intensity %.15e\n", floatimage[spixel*fpixels + fpixel]);
}
```

**Recompile command:**
```bash
cd golden_suite_generator
make clean && make
# Verify binary exists: ls -lh nanoBragg
```

**Environment setup:**
```bash
export NB_C_BIN=./golden_suite_generator/nanoBragg
```

### PyTorch Trace Hooks (scripts/debug_pixel_trace.py or new dedicated script)

**Proposed script:** `scripts/debug_4096_trace.py` (minimal, focused on 3-pixel sweep)

**Key trace points (align with C variable names per `docs/debugging/debugging.md` Trace Schema):**
- `pix0_vector` [m] — detector origin after pivot/rotation
- `pixel_pos_meters` [m] — target pixel 3D position
- `diffracted_vec` — unit vector from sample to pixel
- `scattering_vec_A_inv` [Å⁻¹] — q = (d − i)/λ
- `hkl_frac` — Miller indices (float, before rounding)
- `F_cell`, `F_latt` — structure factor and lattice shape factor
- `omega_pixel` [sr] — solid angle (compare obliquity-corrected vs point-pixel)
- `polar` — polarization factor
- `steps` — total sampling steps (sources × phi × mosaic × oversample²)
- `I_term` — accumulated intensity before scaling
- `final_intensity` — pixel value in output image

**Device/dtype discipline:**
- Trace in `dtype=torch.float64` on `device="cpu"` for determinism and precision (matches C double precision)
- Verify tensors do not silently migrate to GPU mid-trace
- Use `KMP_DUPLICATE_LIB_OK=TRUE` environment variable

**Template invocation:**
```python
# Pseudo-code for scripts/debug_4096_trace.py
for pixel in [(2048, 2048), (1792, 2048), (4000, 2048)]:
    slow, fast = pixel
    # ... run simulator with trace hooks enabled at (slow, fast) ...
    print(f"TRACE_PY: pixel_idx ({slow}, {fast})")
    print(f"TRACE_PY: pix0_vector {pix0[0]:.15e} {pix0[1]:.15e} {pix0[2]:.15e} [m]")
    # ... (match C trace format exactly) ...
```

---

## Tap Points & Owners

### Tap Point Checklist (C→Py variable flow)

| Subsystem | Tap Point Variable | C Source Line (approx) | PyTorch Module/Function | Units | Notes |
|-----------|-------------------|----------------------|------------------------|-------|-------|
| **Detector Geometry** | `pix0_vector` | nanoBragg.c ~L2500 | `models/detector.py::get_pix0_vector()` | meters | Detector origin; verify pivot mode (BEAM vs SAMPLE) |
| | `fdet_vector`, `sdet_vector`, `odet_vector` | ~L2400 | `models/detector.py::get_rotated_basis_vectors()` | unit vectors | Rotated detector basis after twotheta |
| | `pixel_pos` (X,Y,Z) | ~L3200 | `models/detector.py::get_pixel_coords()` | meters | 3D position of target pixel center |
| **Scattering Vector** | `diffracted` | ~L3300 | `simulator.py::_compute_physics_for_position()` | unit vector | d = unit(pixel_pos) |
| | `scattering` (S or q) | ~L3350 | `utils/physics.py` or inline | Å⁻¹ | q = (d − i)/λ; verify wavelength conversion |
| **Miller Indices** | `h`, `k`, `l` (float) | ~L3450 | `simulator.py` via `crystal.get_rotated_real_vectors()` | dimensionless | h = S·a; check misset/phi rotation application |
| **Structure Factor** | `F_cell` | ~L3550 | `models/crystal.py::get_structure_factor()` | electrons | Interpolation vs nearest vs default_F fallback |
| **Lattice Factor** | `F_latt` | ~L3600 | `utils/physics.py::sincg()` or shape model | dimensionless | SQUARE/ROUND/GAUSS/TOPHAT; verify N_cells usage |
| **Solid Angle** | `omega_pixel` | ~L3700 | `simulator.py::_compute_solid_angle()` | steradians | Obliquity correction: Ω = (pixel²/R²) × (close_distance/R) × (o·d) |
| **Polarization** | `polar` | ~L3750 | `utils/physics.py::polarization_factor()` | [0,1] | Kahn model; verify 2θ and ψ calculation |
| **Normalization** | `steps` | ~L2100 | `simulator.py::run()` | count | steps = sources × phi × mosaic × oversample²; **CRITICAL for H2** |
| **Intensity Aggregation** | `I` (accumulated) | ~L3800 | `simulator.py` loop | intensity units | Sum over sources/phi/mosaic/oversample before scaling |
| **Final Scaling** | `floatimage[idx]` | ~L4000 | `simulator.py::run()` return | intensity | I_final = r_e² × fluence × I / steps; apply last-value Ω/polar if oversample_* off |

**Owner assignment:**
- **Geometry/solid angle taps:** Review `docs/architecture/detector.md` contract (meters, obliquity formula)
- **Miller/structure taps:** Cross-check `docs/architecture/crystal.md` and `specs/spec-a-core.md` §3 (reciprocal space)
- **Normalization taps:** Validate against `specs/spec-a-core.md` §4–5 (sampling equations) and `arch.md` §8 (steps formula)

---

## Expected Outputs & Storage

### Artifact Structure
```
reports/2026-01-vectorization-parity/phase_c/20251010T040739Z/
├── trace_plan.md          # This document
├── c_traces/
│   ├── pixel_2048_2048.log    # C trace for ROI center
│   ├── pixel_1792_2048.log    # C trace for ROI boundary
│   └── pixel_4000_2048.log    # C trace for far edge
├── py_traces/
│   ├── pixel_2048_2048.log    # PyTorch trace for ROI center
│   ├── pixel_1792_2048.log    # PyTorch trace for ROI boundary
│   └── pixel_4000_2048.log    # PyTorch trace for far edge
├── diffs/
│   ├── diff_2048_2048.txt     # Line-by-line C vs Py diff
│   ├── diff_1792_2048.txt
│   └── diff_4000_2048.txt
├── first_divergence.md    # Summary: first mismatched variable per pixel, magnitude, hypothesis
├── commands.txt           # Exact C and PyTorch invocation commands used
└── env.json               # Environment metadata (git SHA, Python/PyTorch versions, device/dtype)
```

### Trace Execution Commands (Canonical)

**C trace generation:**
```bash
# For each selected pixel (slow, fast):
export NB_C_BIN=./golden_suite_generator/nanoBragg
$NB_C_BIN \
  -default_F 100 \
  -cell 100 100 100 90 90 90 \
  -lambda 6.2 \
  -distance 100 \
  -detpixels 4096 \
  -N 5 \
  -convention MOSFLM \
  -floatfile /tmp/c_trace_test.bin \
  2>&1 | grep "TRACE_C:" > reports/2026-01-vectorization-parity/phase_c/20251010T040739Z/c_traces/pixel_${slow}_${fast}.log
```

**PyTorch trace generation:**
```bash
# Run debug script (to be authored in Phase C1)
KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_4096_trace.py \
  --pixels "2048,2048" "1792,2048" "4000,2048" \
  --outdir reports/2026-01-vectorization-parity/phase_c/20251010T040739Z/py_traces/ \
  --device cpu \
  --dtype float64
```

**Diff comparison:**
```bash
# For each pixel pair:
diff -u \
  reports/2026-01-vectorization-parity/phase_c/20251010T040739Z/c_traces/pixel_2048_2048.log \
  reports/2026-01-vectorization-parity/phase_c/20251010T040739Z/py_traces/pixel_2048_2048.log \
  > reports/2026-01-vectorization-parity/phase_c/20251010T040739Z/diffs/diff_2048_2048.txt
```

### Acceptance Criteria (Phase C Exit)
- [ ] C and PyTorch traces exist for all 3 selected pixels
- [ ] `first_divergence.md` documents **first mismatched variable** for each pixel class
- [ ] Magnitude of divergence quantified (absolute and relative error)
- [ ] Hypothesis H1/H2/H3 prioritisation updated based on findings
- [ ] `docs/fix_plan.md` Attempt #N (supervisor loop) logged with:
  - Artifacts paths
  - First Divergence summary (variable name, subsystem, pixel class)
  - Next Actions (debugging/fix/verification steps for Phase D/E)

---

## Open Questions / Risks

### Questions Requiring Supervisor Confirmation
1. **Pixel selection approval:** Are (2048,2048), (1792,2048), (4000,2048) the optimal choices, or should corner pixels (e.g., 4095,4095) be prioritised?
2. **Trace script authoring:** Should we extend `scripts/debug_pixel_trace.py` or create standalone `scripts/debug_4096_trace.py`?
3. **Instrumentation depth:** Do we need per-source/per-phi/per-mosaic traces (full loop unroll), or is final-aggregated trace sufficient for first divergence?
4. **ROI sweep deferral:** Should Phase C proceed immediately, or should we first run the optional 1024² ROI sweep to map correlation geography more finely?

### Known Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|-----------|
| **C trace overflow** | Stderr buffer fills; trace incomplete | Redirect to file directly: `2> c_trace.log` instead of `2>&1 | grep` |
| **PyTorch device migration** | Silent CPU→GPU transfer breaks determinism | Add assertions: `assert tensor.device.type == "cpu"` before trace print |
| **Trace format drift** | C and Py variable names/units mismatch | Review `docs/debugging/debugging.md` Trace Schema before editing print statements |
| **Diff noise from float precision** | 1e-15 differences obscure real divergence | Filter diffs to only show lines with Δ > 1e-10 (tunable threshold) |
| **Large trace files** | Multi-MB logs committed to git | Store under `reports/` (gitignored for >1MB files); reference paths in plan only |

### TODOs Before Phase C1 Execution
- [ ] Confirm pixel coordinates with supervisor (or document selection rationale in this plan)
- [ ] Rebuild `golden_suite_generator/nanoBragg` with trace instrumentation
- [ ] Verify `NB_C_BIN` points to instrumented binary (not frozen root-level `./nanoBragg`)
- [ ] Author or adapt `scripts/debug_4096_trace.py` following Trace Schema
- [ ] Run `pytest --collect-only -q` after any script edits to ensure repo health
- [ ] Document any deviations from this plan in `first_divergence.md` or fix_plan Attempt notes

---

## References & Dependencies

### Normative Documents (Spec/Arch)
- `specs/spec-a-core.md` §§4–5 — Sampling, sources, scaling equations
- `arch.md` §§2, 8, 15 — Broadcast shapes, physics model, differentiability
- `docs/architecture/pytorch_design.md` §1.1 & §1.1.5 — Vectorization flows, equal-weight source contract
- `docs/debugging/debugging.md` §2 — Parallel trace SOP-4.1, Trace Schema (names/units/precision)

### Evidence Trail (Phase A/B Artifacts)
- **Good baseline:** `reports/benchmarks/20251009-161714/` (corr≈0.999998, git SHA missing)
- **Phase A matrix:** `reports/2026-01-vectorization-parity/phase_a/20251010T023622Z/artifact_matrix.md`
- **Phase B full-frame failure:** `reports/2026-01-vectorization-parity/phase_b/20251010T030852Z/nb_compare_full/summary.json` (corr≈0.063, sum_ratio≈225)
- **Phase B ROI success:** `reports/2026-01-vectorization-parity/phase_b/20251010T035732Z/roi_compare/summary.json` (corr≈1.0, sum_ratio≈0.999987)
- **ROI scope analysis:** `reports/2026-01-vectorization-parity/phase_b/20251010T035732Z/roi_compare/roi_scope.md`

### Tooling & Commands
- C binary resolution: `NB_C_BIN` precedence (env → `./golden_suite_generator/nanoBragg` → `./nanoBragg`)
- PyTorch invocation: `KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch` or debug scripts
- Parity harness: `nb-compare` (`scripts/comparison/nb_compare.py`)
- Testing strategy: `docs/development/testing_strategy.md` §§1.4–2, §2.5 (parity matrix)

### Plan & Fix Plan
- **Active plan:** `plans/active/vectorization-parity-regression.md` Phase C1–C3 checklist
- **Fix plan entry:** `docs/fix_plan.md` `[VECTOR-PARITY-001]` Attempts History, Next Actions

---

**Plan Status:** STAGED — awaiting supervisor approval to proceed with C/PyTorch instrumentation (Phase C1).
**Next Steps:** Review this plan; confirm pixel selection and trace script approach; execute Phase C1 (C trace capture) then C2 (PyTorch trace capture) then C3 (diff & hypothesise).
