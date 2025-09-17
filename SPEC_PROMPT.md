# Authoritative Technical Spec for nanoBragg.c (Prompt)

## Role
- You are a senior computational physics engineer and C code auditor.
- Your job is to read and understand the provided `nanoBragg.c` source and produce an authoritative, self‑contained technical specification that exactly reflects what this code does today. Avoid speculation.
- Maintain an implementation‑agnostic perspective: describe observable behavior, math, units, data formats, and interfaces without mentioning programming language constructs, internal function names, macros, or threading/parallel frameworks.

## Inputs You Have
- The full text of `nanoBragg.c`.
- The example CLI invocations listed under “Scenarios to Analyze”.
- If any example flag name does not exist in this `nanoBragg.c`, treat it as unsupported in this code version, and call this out explicitly.

## Primary Deliverable
- A rigorous, self‑contained spec that:
  - Describes every physical and mathematical calculation implemented.
  - Enumerates every CLI flag and synonym recognized by this code version, with types, defaults, allowed ranges, and units.
  - Traces all unit conversions explicitly and consistently.
  - Documents all input and output file formats exactly as implemented (including binary layout and headers).
  - Captures auto‑selection logic, precedence rules, pivot/convention handling, and edge‑case behavior.
  - Includes implementation‑faithful equations and pseudocode where appropriate.
  - Flags any mismatches between examples and this code’s supported flags.

## Absolute Requirements
- Faithfulness: Base all behavior on this exact `nanoBragg.c`. If something is ambiguous, describe the observable algorithmic behavior and equations rather than guessing new behavior. Do not reference internal code identifiers (function or variable names).
- Implementation‑agnostic: Do not mention language/runtime details (e.g., OpenMP, thread counts, specific function names, macros, or debug/trace prints). Focus on functional behavior, inputs/outputs, math, and units.
- Units: For every quantity, state units on input, internal representation units, and output units; list each conversion step (e.g., Å→m, mm→m, deg→rad, mrad→rad, µm→m, percent→fraction, eV→λ).
- Exhaustiveness: Cover the full data flow from CLI and optional SMV header ingestion through geometry setup, sampling loops, intensity accumulation, scaling, statistics, and file outputs.
- Determinism and randomness: Describe all random number usage, seeds, distributions, and thresholds.
- Conventions: Precisely document detector/beam conventions (ADXV, MOSFLM, XDS, DIALS, DENZO, CUSTOM), pivoting (BEAM vs SAMPLE), rotation orders, and how beam centers/origins are computed per convention.
- Sampling & weighting: Explicitly detail loops and multiplicative/additive factors across sources, divergence/dispersion, phi steps, mosaic domains, subpixels, and detector thickness layers, including the final normalization by the total “steps”.
- Equations: Provide the exact formulas as implemented for:
  - Pixel position to 3D mapping via detector basis and origin.
  - Diffracted and incident unit vectors, scattering vector q, |q| to sinθ/λ mapping.
  - Pixel solid angle (and point‑pixel option).
  - Detector absorption and capture fraction vs. parallax.
  - Polarization factor (Kahn model) with ψ definition and vector projections.
  - Lattice factors for SQUARE (grating), ROUND (sinc3), GAUSS, TOPHAT, including fudge and radius definitions in reciprocal/real space.
  - Tricubic interpolation neighborhood and fallbacks; nearest‑neighbor indexing rules (ceil/floor) and bounds checks.
  - Fluence, flux, exposure, beamsize relations and sample clipping logic.
  - Water background term and constants.
  - Statistics (max, mean, RMS, RMSD).
- Files & formats: Precisely specify:
  - HKL text input (h k l F), scanning and bounds, default_F behavior.
  - Binary dump `Fdump.bin` layout.
  - SMV outputs: exact header keys written, units (mm vs m), endianness detection, header padding to 512 bytes, payload type and ordering.
  - Float image binary (`floatfile`): element type, count, and ordering.
  - PGM output (P5) header and data; note the scale applied.
  - Mask and IMG header ingestion and which parameters they override.
- Edge cases: Document behavior for zero/negative or missing values, auto‑selection defaults (steps, ranges), clipping, dmin cutoff, detector thickness = 0, mosaic_domains/spread combinations, polarization toggles, interpolation off, round_div vs square_div, curved detector on/off.
  

## Document Structure
- Overview
  - Purpose and high‑level description of the simulation scope (far‑field only, no near‑field).
  - Key constants (`r_e^2`, Avogadro) and their units.
- Units & Conversions
  - A table listing every parameter with its input units, internal units, conversion formula, and where applied in code.
  - Conversions: Å↔m, mm↔m, µm↔m, deg↔rad, mrad↔rad, percent↔fraction, eV→λ.
- CLI Interface
  - Comprehensive table of all recognized flags in this code version, including:
    - All synonyms as parsed (e.g., `-mat`, `-hkl`, `-cell`, `-misset`, `-Na`/`-Nb`/`-Nc`/`-N`, detector flags, etc.).
    - Type, default, valid ranges, units.
    - Exactly which simulation quantities they control, how those quantities participate in subsequent computations, and precedence/override rules.
  - Precedence and overrides (e.g., `-img`/`-mask` header values, pivot choice from convention, defaults).
  - Unsupported example flags: Explicitly list any flags present in the examples but not recognized by this code (e.g., `-pix0_vector_mm` or `-matrix` if absent), and explain the closest supported equivalent if any.
- Geometry & Conventions
  - Detector basis vectors `fdet`, `sdet`, `odet` and their normalization.
  - Beam, polarization, spindle vectors; vertical vector construction.
  - Pivot modes (BEAM vs SAMPLE): exact formulas for the detector origin vector (from sample to detector plane) and for preserving beam center or sample near‑point.
  - Rotation order and application points: `detector_rotx/y/z` then `twotheta_axis`; how `ratio` and `close_distance` are computed and used; final `Fbeam`/`Sbeam`, `ORGX`/`ORGY`, `dials_origin`.
  - Conventions (ADXV, MOSFLM, XDS, DIALS, DENZO, CUSTOM): initial bases, beam centers, and mapping between conventions (including the MOSFLM +0.5 px shifts present in code).
- Unit Cell & Orientation
  - From `-mat` (MOSFLM A): wavelength scaling removal (`1e-10/λ`) and subsequent magnitude updates.
  - From `-cell` and `-misset`: direct and reciprocal vectors, volumes, angles; misset rotation application.
  - Cross products used to derive real↔reciprocal spaces; formulas for `V_cell`, `V_star` and angles (and clamping).
- Sources, Divergence, Dispersion
  - Auto‑selection logic for steps and ranges across `hdiv`/`vdiv`/`disp`; `round_div` elliptical cut.
  - Source direction generation via rotations around polarization/vertical axes; normalization; weighting.
  - Flux/fluence/exposure/beamsize relation and sample clipping warnings; final fluence determination.
- Sampling & Accumulation
  - Complete nested loop order and normalization:
    - detector thickness layers → subpixels (`oversample^2`) → sources → phi steps → mosaic domains.
  - Oversample options for thick/polar/omega and when factors are applied per subpixel vs post‑loop.
  - `dmin` cutoff logic.
- Physics & Intensities
  - Pixel center construction: 3D position formula from `Fdet`/`Sdet`/`Odet` and `pix0_vector`; curved detector alternative.
  - Unitization and `airpath`; pixel solid angle formula; `point_pixel` behavior.
  - Parallax and `capture_fraction` formula across layers.
  - Incident/diffracted vectors; scattering vector `q` and `stol = 0.5*|q|`.
  - Polarization factor formula with definitions of ψ, `E_in`/`B_in` construction, and Kahn factor.
  - `h,k,l` computation as dot products with real‑space vectors; nearest integer indices; bounds conditions.
  - Lattice factor formulas for SQUARE, ROUND (sinc3), GAUSS, TOPHAT including `Na`/`Nb`/`Nc` roles, `fudge`, and radius definitions in the correct space.
  - Structure factor interpolation (tricubic, 4×4×4 neighborhood) vs nearest‑neighbor vs `default_F`, with precise out‑of‑range detection.
  - Final per‑pixel intensity: scaling by `r_e^2`, fluence, `capture_fraction`, polarization, solid angle, and division by total steps.
- Background & Noise
  - Water background `I_bg` expression and units.
  - Poisson noise generation rules (thresholds for switching to Gaussian approx) and ADC offset; overload clipping.
- Statistics
  - Computation of max, mean, RMS, RMSD (post processing over ROI).
- File I/O
  - HKL input format and scanning logic (two‑pass count then fill).
  - `Fdump.bin` binary layout: header values then contiguous 3D array page order.
  - SMV outputs (int/noise images):
    - Header fields and units (mm), beam center variants (ADXV/MOSFLM/DENZO), XDS `ORGX`/`ORGY`, `DIALS_ORIGIN`, etc.
    - Byte order detection and header padding to 512 bytes.
    - Data layout: unsigned short per pixel in fast‑major order; scaling rules.
  - Float image (`floatfile`): number of 4‑byte floats and ordering.
 - PGM (P5): header lines and body; `pgm_scale` usage.
  - Mask and IMG header ingestion: which fields are read and how they set `fpixels`/`spixels`/`pixel_size`/`distance`/beam centers, etc.
- Randomness
  - Describe seeding behavior and the probability distributions used (Poisson, Gaussian, Lorentzian, triangular, exponential) and where applied, without naming internal functions.
  
- Error Handling & Warnings
  - Exact conditions that print warnings or exit; required flags; compatibility constraints (e.g., need `-mat` or `-cell`; HKL vs `default_F`).
- Scenarios to Analyze
  - For each provided example CLI:
    - Identify any unsupported flags in this code version and specify the supported equivalent (if any).
    - Resolve all inputs to consistent internal units (table).
    - Derive the number of sources, steps, oversampling, and mosaic domains actually used.
    - Provide the resolved detector geometry (basis vectors and detector origin vector) and beam center(s) per convention.
    - Walk one representative pixel through all calculations to exemplify the chain (position → q → hkl → `F_latt`, `F_cell` → intensity factors → final pixel value scaling).
- Glossary
  - Define all symbols and vectors (by concept/quantity name) with units.

## Style & Output Rules
- Organize with clear section headers and short, focused paragraphs or bullet lists.
- Use inline code style for flag names and defined quantities (e.g., `-hkl`, `incident_beam_direction`). Avoid internal code identifiers.
- Express equations in plain ASCII math (e.g., `I += F_cell^2 * F_latt^2`).
- Be concise but complete; avoid redundant exposition.
- Do not invent behavior not present in the code. If something seems inconsistent, document what the code actually does, and note the inconsistency.

## Normative vs Informative
- Mark sections that define external behavior, math, units, I/O formats, and conformance constraints as “Normative”.
- Mark examples, worked walkthroughs, background explanations, and non-essential guidance as “Informative”.
- The “Acceptance Criteria” and “Quality Bar Checklist” are normative.

## Scope & Non‑Goals (Informative)
- State the scope: far‑field diffraction only; no near‑field propagation or PSF modeling beyond pixel solid angle/obliquity.
- Clarify non‑goals or out‑of‑scope features (e.g., symmetry enforcement, partiality models not present, detector readout non-linearities unless explicitly modeled).

## Acceptance Criteria (Normative)
- Units table includes every quantity used in math; all conversions are explicit and consistent.
- Every CLI option parsed by this code version is documented with units and semantics; unsupported flags in examples are explicitly flagged.
- All major formulas (geometry, intensity, lattice, polarization, absorption, solid angle, interpolation) are included and correct as implemented.
- File formats exactly match read/write behavior, including header keys, units, padding, ordering, and numeric types.
- Sampling structure and normalization by total steps are explicit and correct.
- Randomness usage, seeding, and distributions are described where used.
- Edge‑case behaviors (zero/negative values, toggles, auto‑selection defaults) are documented.

## Quality Bar Checklist (Informative)
- Units table includes every quantity used in math.
- All conversions are explicit and consistent.
- Every CLI option parsed in code is documented; examples calling unsupported flags are flagged.
- All major formulas (geometry, intensity, lattice, polarization, absorption, solid angle, interpolation) are included and correct.
- All file formats exactly match what the code writes/reads.
- Sampling and normalization by total steps is explicit.

---

Now produce the spec.
