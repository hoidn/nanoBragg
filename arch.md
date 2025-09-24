# nanoBragg PyTorch — Implementation Architecture

Document version: 1.0 (aligned with specs/spec-a.md)
Target spec: specs/spec-a.md (single-file normative spec)
Implementation target: Python (>=3.11) + PyTorch (float64 default). Type blocks may use TypeScript-style for clarity; implement with Python dataclasses and torch tensors.

## Running The CLI

- Install (recommended):
  - `pip install -e .` from repo root (provides `nanoBragg` console script).
- Run (installed):
  - `nanoBragg -hkl P1.hkl -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100 -floatfile out.bin`
- Run (without install):
  - `PYTHONPATH=src python -m nanobrag_torch -hkl P1.hkl -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100 -floatfile out.bin`
- Minimal quick test (no HKL):
  - `nanoBragg -default_F 1 -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100 -detpixels 128 -pgmfile test.pgm`

Notes
- Entry point: `src/nanobrag_torch/__main__.py` (module runner `python -m nanobrag_torch`).
- Required inputs: provide `-hkl` (or existing `Fdump.bin`) or set `-default_F > 0`, and either `-mat` (MOSFLM A*) or `-cell`.
- Useful speedups: use `-roi xmin xmax ymin ymax` for small windows; reduce `-detpixels` during tests.
- SMV/PGM outputs: `-intfile` (with optional `-scale`, `-adc`), `-noisefile` (Poisson), `-pgmfile` (8‑bit preview).


## Spec vs Architecture Precedence

- Normative contract: The specs/spec-a.md file defines the external contract (CLI flags, units, geometry/physics equations, file formats, and Acceptance Tests). It takes precedence for externally visible behavior.
- Implementation guidance: This arch.md documents ADRs, module layout, and concrete decisions used to realize the spec with PyTorch. It is subordinate to the spec.
- Conflict resolution: If arch.md and specs/spec-a.md disagree, implement to the spec and open a PR to realign arch.md.
- Underspecification: When the spec is silent, follow the ADRs here. If experience shows the spec needs additions, propose a spec change in specs/spec-b.md and update acceptance tests accordingly.

## 1) Goals & Non‑Goals

- Goals
  - Render far-field diffraction from perfect-lattice nanocrystals per spec, matching nanoBragg C semantics.
  - Honor detector/beam conventions (MOSFLM, XDS; ADXV/DENZO/DIALS to be added) including pivots and two-theta.
  - Vectorize core loops in PyTorch (pixels × phi × mosaic × sources × subpixels) with GPU support.
  - Maintain differentiability (end-to-end gradients) for cell and geometry parameters — **critical for optimization capabilities** (see Section 15).
  - Support spec’d I/O: raw float image, SMV with/without noise, optional PGM, HKL read + Fdump cache.
  - Deterministic/reproducible runs via explicit seeds per RNG domains.

- Non-goals (from spec Overview and scope)
  - No near-field propagation and no detector PSF beyond pixel solid-angle/obliquity.
  - No symmetry (P1 only, no Friedel pairing).
  - Out-of-scope flags in examples (e.g., -dispstep, -hdiv/-vdiv) remain unsupported.

## 2) Workspace & Runtime Layout

- Source:
  - `src/nanobrag_torch/`
    - `config.py` — dataclasses for Crystal/Detector/Beam configs
    - `models/`
      - `detector.py` — detector geometry, conventions, pix0, pixel coordinates (meters)
      - `crystal.py` — cell tensors, misset, phi/mosaic rotations, HKL access
    - `simulator.py` — vectorized physics loop, scaling, solid angle
    - `utils/` — geometry (rotations, dot/cross), physics kernels, unit conversions
  - `scripts/` — debug and comparison scripts (C vs PyTorch traces)
  - `specs/` — spec-a.md (normative); tests appended under Acceptance Tests
  - `tests/` — project tests (Python-level, when present)

- Run-time artifacts (as spec evolves)
  - `Fdump.bin` — binary HKL cache
  - `*.img` — SMV images (int and noise)
  - `*.pgm` — optional preview image
  - `*.bin` — raw float image

## 2a) Architectural Decisions (ADRs)

- ADR-01 Hybrid Unit System (Detector in meters)
  - Detector geometry (distance, pixel size, pix0_vector, pixel coordinates) uses meters internally to match C semantics and avoid Å-scale precision issues.
  - Physics computations (q, stol, shape factors) operate in Angstroms.
  - Conversion at the interface: pixel coords [m] × 1e10 → [Å].
  - Alignment with spec: specs/spec-a.md states q is expressed in m⁻¹ in the spec; this implementation uses Å for physics while keeping geometry in meters, with explicit conversions at the interface.

- ADR-02 Rotation Order and Conventions
  - Basis initialization per convention (MOSFLM, XDS). Apply rotations in order: rotx → roty → rotz → rotate around `twotheta_axis` by `detector_twotheta`.
  - Pivots: BEAM and SAMPLE formulas per spec.

- ADR-03 Beam-center Mapping (MOSFLM) and +0.5 pixel Offsets
  - MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (after mm→pixels). CUSTOM (when active): spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs.

- ADR-04 Pixel Coordinate Caching
  - Cache `get_pixel_coords()` outputs keyed implicitly by geometry version. Invalidate cache on geometry change (basis vector or pix0 change).

- ADR-05 Deterministic Sampling & Seeds
  - Distinct RNG domains: noise, mosaic, misset. Spec requires fixed defaults and -seed overrides. Implement the spec's LCG+shuffle PRNG for determinism; torch.Generator may be used only if it reproduces the exact bitstream.

- ADR-08 Differentiability Preservation [CRITICAL]
  - All operations on differentiable parameters must maintain computation graph connectivity. See Section 15 for comprehensive guidelines.
  - Use @property methods for derived tensors, never overwrite with `.item()` or detached values.
  - Implement boundary enforcement: type conversions at call sites, tensor assumptions in core methods.

- ADR-06 Interpolation Fallback [IMPLEMENTED]
  - Tricubic interpolation is enabled/disabled per spec. On out-of-range neighborhood, emit one-time warning, use default_F for that eval, and disable interpolation for the remainder of the run.
  - Implementation complete: `polint`/`polin2`/`polin3` in `utils/physics.py`, `_tricubic_interpolation` in `models/crystal.py`
  - Auto-enables for crystals with any dimension ≤ 2 cells

- ADR-07 Oversample_* "Last-value" Semantics
  - When oversample_thick/polar/omega are NOT set, apply final capture/polarization/Ω once using the last computed value (loop-order dependent), matching the spec's caveat.

- ADR-09 Detector Absorption Implementation [IMPLEMENTED]
  - Absorption parameters stored in DetectorConfig: `detector_abs_um` (attenuation depth), `detector_thick_um` (thickness), `detector_thicksteps` (layers)
  - Parallax factor ρ = d·o computed per-pixel using detector normal and observation direction
  - Layer capture fractions: exp(−t·Δz·μ/ρ) − exp(−(t+1)·Δz·μ/ρ) where μ = 1/attenuation_depth

- ADR-10 Convention-Aware Incident Beam Direction [IMPLEMENTED]
  - Simulator incident beam direction must match detector convention for consistency (AT-PARALLEL-004)
  - MOSFLM convention: beam along [1,0,0] (+X axis)
  - XDS/DIALS conventions: beam along [0,0,1] (+Z axis)
  - Default to MOSFLM direction when no detector provided (for backward compatibility)

- ADR-11 Full Tensor Vectorization [IMPLEMENTED 2025-09-24]
  - Eliminated all Python loops in core computation path for >10x performance gain
  - Subpixel sampling: Process all oversample×oversample subpixels as batch dimension (S, F, oversample²)
  - Thickness layers: Process all detector layers in parallel using broadcasting (thicksteps, S, F)
  - Maintains exact numerical equivalence with loop-based implementation
  - Enables efficient GPU acceleration through pure tensor operations

- ADR-12 Golden Data Generation Strategy [2025-09-24]
  - Golden reference data for tests should use self-contained commands without external file dependencies
  - Use `-cell` parameters directly instead of requiring P1.hkl/A.mat files
  - Accept minor numerical tolerance differences (≤0.001 correlation) between C and PyTorch implementations
  - Document exact generation commands in tests/golden_data/README.md for reproducibility

## 3) High‑Level System Architecture

- CLI & Config Layer [IMPLEMENTED]
  - `__main__.py` - Entry point with argparse, maps CLI flags to engine parameters per spec
  - Parses spec-defined flags and image/mask headers, resolves precedence, and instantiates config dataclasses

- Geometry Engine
  - Detector: conventions, rotations, pix0 computation, meters→Å conversion, solid angle factors.
  - Crystal: triclinic cell tensors, misset, phi, mosaic rotations; reciprocal/real-space duality.

- Physics Engine
  - Computes scattering vectors; dmin culling; structure factor lookup/interpolation; lattice shape factors (SQUARE/ROUND/GAUSS/TOPHAT); polarization; absorption; background; steps normalization; final scaling.

- I/O Engine [IMPLEMENTED]
  - HKL text & Fdump read/write; SMV/PGM writers; noise image; statistics reporter.

- Observability & Validation
  - Deterministic traces (debug scripts), acceptance-test-driven behavior.

## 4) Module Structure [IMPLEMENTED]

```
nanobrag_torch/
  config.py                # DetectorConfig, CrystalConfig, BeamConfig (+ enums)
  simulator.py             # Vectorized physics core (pixels × phi × mosaic)
  __main__.py             # CLI entry point with full argparse implementation
  models/
    detector.py            # Basis vectors, pivots, twotheta, pix0, pixel coords
    crystal.py             # Cell tensors, misset, phi/mosaic rotations, HKL I/O
  utils/
    geometry.py            # dot/cross, rotations (axis/matrix)
    physics.py             # sincg, sinc3, polarization_factor [ALL IMPLEMENTED]
    units.py               # mm↔Å/m, deg↔rad, etc.
    c_random.py           # C-compatible RNG for reproducibility
  io/
    hkl.py                # HKL file reading and Fdump.bin caching
    smv.py                # SMV format reader/writer with header parsing
    pgm.py                # PGM image writer
    mask.py               # Mask file reading and application
    source.py             # Source file parsing for beam divergence
    mosflm.py             # MOSFLM matrix file support
```

## 5) Data Models (TypeScript-style; implement via dataclasses)

```ts
enum DetectorConvention { MOSFLM, XDS, ADXV, DENZO, DIALS, CUSTOM }
enum DetectorPivot { BEAM, SAMPLE }

interface CrystalConfig {
  cell_a: number; cell_b: number; cell_c: number;          // Å
  cell_alpha: number; cell_beta: number; cell_gamma: number;// deg
  misset_deg: [number, number, number];                    // deg (XYZ)
  phi_start_deg: number; osc_range_deg: number; phi_steps: number;
  spindle_axis: [number, number, number];                  // unit vector
  mosaic_spread_deg: number; mosaic_domains: number; mosaic_seed?: number;
  N_cells: [number, number, number];                       // Na,Nb,Nc (≥1)
  default_F: number;                                       // fallback F
}

interface DetectorConfig {
  distance_mm: number; pixel_size_mm: number;
  spixels: number; fpixels: number;
  beam_center_s: number; beam_center_f: number;            // mm
  detector_rotx_deg: number; detector_roty_deg: number; detector_rotz_deg: number;
  detector_twotheta_deg: number; twotheta_axis?: [number, number, number];
  detector_convention: DetectorConvention; detector_pivot: DetectorPivot;
  oversample: number;                                      // subpixel grid per axis
}

interface BeamConfig {
  wavelength_A: number;                                    // Å
  polarization_factor: number;                             // Kahn K (0..1)
  flux?: number; exposure?: number; beamsize?: number;     // for fluence calc
}
```

## 6) Execution Flow (pseudocode)

1. Parse CLI and headers [IMPLEMENTED], resolve precedence; build CrystalConfig, DetectorConfig, BeamConfig.
2. Instantiate Detector (meters) and Crystal (Å). Optionally load HKL or Fdump.
3. Compute `pix0_vector` per pivot and convention; compute basis rotations; cache pixel coords in meters, convert to Å for physics.
4. Build sampling sets: phi (phi_steps), mosaic (mosaic_domains), sources (divergence/dispersion), subpixels (oversample^2), thickness steps.
5. For each pixel/subpixel/thickness/source/phi/mosaic:
   - pos = D0 + Fdet·f + Sdet·s (+ Odet·o if thick); d = unit(pos); R=|pos|; Ω = pixel^2/R^2·(close_distance/R) or 1/R^2 if point-pixel.
   - i = −source_dir; λ from source; q = (d−i)/λ; stol=0.5·|q|; cull if dmin>0 and stol>0 and dmin>0.5/stol.
   - Rotate (a,b,c) by phi about spindle; apply mosaic rotation; compute h=a·q, k=b·q, l=c·q.
   - h0,k0,l0 = ceil(x−0.5) (nearest int); F_latt via selected lattice model.
   - F_cell via tricubic (if enabled and in-bounds) else nearest or default_F per spec fallback.
   - Polarization per Kahn model unless -nopolar.
   - Accumulate I_term = (F_cell^2)·(F_latt^2) with oversample_* caveats (last-value vs per-term multiply).
6. Final scaling per pixel: S = r_e^2 · fluence · I / steps; if oversample_* toggles are off, multiply S once by the last computed capture/polarization/Ω per spec. Add background I_bg if enabled. Write outputs.

## 7) Geometry Model & Conventions

- Basis vectors and defaults (initial, before rotations):
  - ADXV:   f=[1,0,0], s=[0,−1,0], o=[0,0,1],  beam=[0,0,1], default twotheta_axis=[−1,0,0]; pivot=BEAM. Default beam centers: Xbeam=(detsize_f+pixel)/2, Ybeam=(detsize_s−pixel)/2; mapping Fbeam=Xbeam, Sbeam=detsize_s−Ybeam.
  - MOSFLM: f=[0,0,1], s=[0,−1,0], o=[1,0,0],  beam=[1,0,0], default twotheta_axis=[0,0,−1]; pivot=BEAM. Beam-center mapping: Fbeam=Ybeam+0.5·pixel; Sbeam=Xbeam+0.5·pixel.
  - DENZO:  f=[0,0,1], s=[0,−1,0], o=[1,0,0],  beam=[1,0,0], default twotheta_axis=[0,0,−1]; pivot=BEAM. Beam-center mapping: Fbeam=Ybeam; Sbeam=Xbeam.
  - XDS:    f=[1,0,0], s=[0,1,0],  o=[0,0,1],  beam=[0,0,1], default twotheta_axis=[1,0,0];  pivot=SAMPLE. Beam-center mapping: Fbeam=Xbeam; Sbeam=Ybeam (defaults Xbeam=Xclose, Ybeam=Yclose).
  - DIALS:  f=[1,0,0], s=[0,1,0],  o=[0,0,1],  beam=[0,0,1], default twotheta_axis=[0,1,0];  pivot=SAMPLE. Beam-center mapping: Fbeam=Xbeam; Sbeam=Ybeam.
- Rotations: apply XYZ small-angle rotations to f/s/o, then rotate around twotheta_axis by two-theta.
- r-factor update: r = b·o_after; if close_distance unspecified: close_distance = |r·distance|; then set distance = close_distance / r. Direct-beam Fbeam/Sbeam recomputed from R = close_distance/r·b − D0.
- Pivots:
  - SAMPLE: D0 = −Fclose·f − Sclose·s + close_distance·o, then rotate D0 (pix0) with detector rotations and two-theta.
  - BEAM: D0 = −Fbeam·f − Sbeam·s + distance·beam (after rotations); preserves beam center.
  - CLI forcing and precedence (per spec-a):
    - Providing `-distance` (without `-close_distance`) forces BEAM pivot; providing `-close_distance` forces SAMPLE pivot.
    - Providing beam-center style inputs forces pivot: `-Xbeam`/`-Ybeam` → BEAM; `-Xclose`/`-Yclose` or `-ORGX`/`-ORGY` → SAMPLE.
    - Explicit `-pivot` overrides either.
- Beam center mapping:
  - ADXV:   Fbeam = Xbeam; Sbeam = detsize_s − Ybeam.
  - MOSFLM: Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel (mm→pixels→meters).
  - DENZO:  Fbeam = Ybeam; Sbeam = Xbeam.
  - XDS/DIALS: Fbeam = Xbeam; Sbeam = Ybeam.
  - CUSTOM: spec is silent; ADR decision is to not apply implicit +0.5 offsets unless provided by user inputs.
- Curved detector [IMPLEMENTED]: spherical mapping via small-angle rotations Sdet/distance and Fdet/distance.

## 8) Physics Model & Scaling

- Scattering vector and stol: i = −source_dir (unit), d=unit(pos), q=(d−i)/λ [m−1 in spec; Angstroms in implementation], stol=0.5·|q|.
- Lattice shape models:
  - SQUARE: F_latt = sincg(π·h,Na) · sincg(π·k,Nb) · sincg(π·l,Nc).
  - ROUND:  F_latt = Na·Nb·Nc·0.723601254558268 · sinc3(π·sqrt(fudge·hrad^2)).
  - GAUSS/TOPHAT: per spec formulas using Δr*^2 and cutoff.
- Structure factors: tricubic 4×4×4 interpolation with fallback; nearest-neighbor otherwise; default_F out-of-range.
- Polarization (Kahn): factor = 0.5·(1 + cos^2(2θ) − K·cos(2ψ)·sin^2(2θ)), ψ from EB-plane projection.
- Absorption & parallax: per-layer capture fraction = exp(−t·Δz·μ/ρ) − exp(−(t+1)·Δz·μ/ρ), ρ=d·o.
- Solid angle: Ω = pixel^2/R^2 · (close_distance/R); point-pixel: Ω = 1/R^2.
- Background: I_bg = (F_bg^2)·r_e^2·fluence·(water_size^3)·1e6·Avogadro/18.
- Steps normalization: steps = sources·mosaic_domains·phisteps·oversample^2; S = r_e^2·fluence·I/steps; apply last-value factors if oversample_* toggles are off.

## 9) HKL Data & Interpolation

- Text HKL read: two-pass min/max then grid allocations; non-integer warnings; unspecified points initialized to default_F when requested.
- Binary Fdump: header of six ints, form-feed separator, then (h_range+1)×(k_range+1)×(l_range+1) doubles in native endianness (fastest-varying l).
- Interpolation: enable/disable via flags; auto-enable if any of Na/Nb/Nc ≤ 2 (per spec defaults) unless user forces off.

## 10) I/O — Headers & Image Files [IMPLEMENTED]

- SMV integer images:
  - Header keys exactly as spec; close with `}\f`; pad to 512 bytes; data unsigned short, slow-major ordering (fast index contiguous; pixel index = slow*fpixels + fast).
  - Scale factor: if ≤0 or missing, set to 55000/max(float) else 1.0; add ADC offset (default 40), clip [0,65535].
- Noise images:
  - Poisson (exact <12, rejection up to 1e6, Gaussian approx >1e6), then ADC and clipping; overload count tracked.
- PGM:
  - P5 with comment line `# pixels scaled by <pgm_scale>`; values floor(min(255, float_pixel * pgm_scale)).
- Header ingestion from -img/-mask: recognized keys applied; last file read wins; for -mask, Y beam center interpreted as detsize_s − value_mm.

## 11) RNG & Seeds [IMPLEMENTED]

- Domains and defaults:
  - noise_seed = negative wall-clock time (spec default), override via -seed.
  - mosaic_seed = −12345678 (spec default) unless set.
  - misset_seed = noise_seed unless set.
- PRNG: Implement the spec’s linear congruential generator with shuffle table for all RNG domains to guarantee deterministic, cross-device reproducibility. Torch generators may be used for performance only if they reproduce the identical bitstream; otherwise, use the custom PRNG directly.

## 12) Testing Strategy (maps to spec Acceptance Tests)

- Unit tests
  - geometry: basis vectors per convention, pix0, r-factor distance update, Ω calculation, point-pixel.
  - crystal: triclinic tensors, misset rotation, phi/mosaic rotations.
  - physics: sincg numerical stability, polarization factor, absorption layers, steps normalization.
  - io: SMV header serialization, Fdump read/write, PGM writer.

- Integration tests
  - Acceptance Tests from specs/spec-a.md (“Acceptance Tests (Normative)”), including AT-GEO-001..AT-STA-001.
  - C-vs-PyTorch trace parity for selected pixels (debug scripts).

## 13) Implementation Plan (incremental)

1) Geometry correctness
  - Fix MOSFLM BEAM-pivot beam-center mapping; add r-factor distance update; align default pivots per spec.
2) Steps normalization & Ω last-value caveat
  - Implement steps division; wire oversample_* toggles with last-value behavior.
3) Absorption & thickness
  - Implement per-layer capture fractions and -oversample_thick semantics.
4) Polarization
  - Implement Kahn model; -nopolar and -oversample_polar behaviors.
5) Structure factors & interpolation
  - Wire HKL grid into `get_structure_factor`; implement tricubic with fallback.
6) I/O engine
  - SMV/PGM/Raw writers; Fdump cache; header ingestion; stats.
7) Sources/divergence/dispersion & dmin
  - Add multi-source sampling and auto count/range/step resolution; implement dmin culling.

## 14) Implementation‑Defined Defaults (explicit)

- dtype: float64 tensors for numerical stability, with `.to(dtype=...)` promoted when needed.
- device: CPU default; opt-in CUDA via `.to(device)`.
- Tolerances: geometry comparisons use atol ~1e-15 for cached basis checks; acceptance checks use explicit tolerances per test.
- When spec and C disagree subtly on rounding, use spec’s rounding: nearest integer via `ceil(x − 0.5)`.

## 15) Differentiability Guidelines (Critical for PyTorch Implementation)

### Core Principles

The PyTorch implementation **MUST** maintain end-to-end differentiability to enable gradient-based optimization. This is a fundamental architectural requirement that affects every design decision.

### Mandatory Rules

1. **Never Use `.item()` on Differentiable Tensors**
   - **Forbidden:** `config = Config(param=tensor.item())` — permanently severs computation graph
   - **Correct:** `config = Config(param=tensor)` — preserves gradient flow
   - **Rationale:** `.item()` extracts a Python scalar, completely detaching from autograd

2. **Avoid `torch.linspace` for Gradient-Critical Code**
   - **Problem:** `torch.linspace` doesn't preserve gradients from tensor endpoints
   - **Forbidden:** `torch.linspace(start_tensor, end_tensor, steps)` where tensors require gradients
   - **Correct:** `start_tensor + (end_tensor - start_tensor) * torch.arange(steps) / (steps - 1)`
   - **Alternative:** Use manual tensor arithmetic for all range generation needing gradients

3. **Implement Derived Properties as Functions**
   - **Forbidden:** Overwriting class attributes with computed values (e.g., `self.a_star = calculate_reciprocal()`)
   - **Correct:** Use `@property` decorators that recalculate from base parameters each access
   - **Example:** Crystal reciprocal vectors must be computed from cell parameters on-demand

4. **Boundary Enforcement for Type Safety**
   - **Pattern:** Core methods assume tensor inputs; handle type conversions at call sites only
   - **Forbidden:** `isinstance(param, torch.Tensor)` checks inside computational methods
   - **Correct:** Convert scalars to tensors at API boundaries, maintain tensors throughout core
   - **Benefit:** Clean architecture while preserving gradient flow

5. **Avoid Gradient-Breaking Operations**
   - **Forbidden in gradient paths:**
     - `.detach()` — explicitly breaks gradient connection
     - `.numpy()` — converts to NumPy array, losing autograd
     - `.cpu()` without maintaining graph — can break device consistency
   - **Allowed:** These operations are safe in non-differentiable contexts (logging, visualization)

### Testing Requirements

**Every differentiable parameter MUST have:**
1. **Unit-level gradient test:** Verify gradients flow through isolated functions
2. **Integration gradient test:** Verify end-to-end gradient flow through complete simulation
3. **Stability test:** Verify gradients remain stable across parameter variations
4. **Use `torch.autograd.gradcheck`:** With `dtype=torch.float64` for numerical precision

### Common Pitfalls and Solutions

| Pitfall | Symptom | Solution |
|---------|---------|----------|
| Using `.item()` in config | Gradients are None | Pass tensors directly |
| `torch.linspace` with tensor bounds | No gradient on start/end | Manual arithmetic |
| Overwriting derived attributes | Stale gradients | Use @property methods |
| Type checks in core methods | Complex branching | Boundary enforcement |
| In-place operations | Runtime errors | Use out-of-place ops |

### Architecture Implications

- **Config objects:** Must accept both scalars and tensors, preserving tensor types
- **Model classes:** Use @property for all derived geometric/crystallographic quantities
- **Simulator:** Maintain tensor operations throughout; batch operations for efficiency
- **Utils:** Implement gradient-safe versions of standard operations (ranges, interpolation)

### Debugging Gradient Issues

1. **Check requires_grad:** Verify input tensors have `requires_grad=True`
2. **Print computation graph:** Use `torchviz` or `tensorboard` to visualize graph
3. **Isolate breaks:** Binary search through operations to find where gradients stop
4. **Use retain_graph:** For debugging multiple backward passes
5. **Check autograd.grad:** Manually compute gradients for specific tensors

### Reference Documentation

For comprehensive details and examples:
- **Lessons learned:** `docs/development/lessons_in_differentiability.md` — real debugging cases and solutions
- **Design principles:** `docs/architecture/pytorch_design.md` — architectural patterns for differentiability
- **Testing strategy:** `docs/development/testing_strategy.md` — Tier 2 gradient correctness methodology
- **Parameter trace:** `docs/architecture/parameter_trace_analysis.md` — understanding gradient flow paths

### Verification Checklist

- [ ] All `.item()` calls verified as non-differentiable paths
- [ ] No `torch.linspace` with gradient-requiring endpoints
- [ ] All derived properties use @property or functional patterns
- [ ] Type conversions happen only at boundaries
- [ ] `torch.autograd.gradcheck` passes for all parameters
- [ ] Integration tests verify end-to-end gradient flow

**Remember:** Breaking differentiability breaks the fundamental value proposition of the PyTorch port — the ability to optimize physical parameters via gradient descent.

## 16) Developer Notes

- Maintain strict separation between geometry (meters) and physics (Å). Convert once at the interface.
- **Preserve differentiability at all costs:** Follow Section 15 guidelines religiously. This is non-negotiable for optimization capabilities.
- Cache only pure-geometry outputs; invalidate on config changes; keep unit tests focused and vectorized.
- Keep acceptance tests in specs/spec-b.md up-to-date with behavior; use them as the primary source of truth.
- **Before implementing any differentiable feature:** Review `docs/development/lessons_in_differentiability.md` to avoid known pitfalls.
- **Use @property pattern:** For all derived quantities (reciprocal vectors, rotated bases, etc.) to maintain gradient flow.
- **Test gradients early and often:** Don't wait until integration; verify gradients at the unit level first.
- **SAMPLE vs BEAM pivot tolerances:** BEAM pivot preserves beam center exactly (1e-6 tolerance), SAMPLE pivot has geometric constraints leading to ~3.5e-2 tolerance with large rotations. This matches C-code behavior.
