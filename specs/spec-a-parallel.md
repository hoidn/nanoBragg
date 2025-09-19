# nanoBragg Spec A — Conformance & Parallel Tests

This shard enumerates the CLI profile acceptance tests, parallel validation suite, developer tooling expectations, and conformance profiles. Review [spec-a-core.md](spec-a-core.md) for base requirements and [spec-a-cli.md](spec-a-cli.md) for CLI semantics referenced here.

Parallel Validation Tests (Profile: C-PyTorch Equivalence) — Acceptance Tests (Normative)

References: ../docs/development/testing_strategy.md (parallel trace-driven validation), ../docs/debugging/debugging.md (trace SOP), ../docs/debugging/detector_geometry_checklist.md (detector geometry triage), ../docs/architecture/undocumented_conventions.md (hidden C behaviors)
Why: testing_strategy and debugging.md define the parallel trace methodology; the detector checklist accelerates geometry debugging; undocumented_conventions flags hidden C behaviors that often break equivalence.

These tests verify that PyTorch implementation produces outputs equivalent to the C reference implementation. They apply to implementations claiming the C-PyTorch Equivalence Profile. These are black-box behavioral tests comparing outputs without examining internal implementation details.

- AT-PARALLEL-001 Beam Center Scales with Detector Size
  - Setup: Test detector sizes 64x64, 128x128, 256x256, 512x512, 1024x1024 pixels with 0.1mm pixel size, cubic crystal 100Å N=3, λ=6.2Å
  - Expectation: Beam center (mm) SHALL equal detector_pixels/2 × pixel_size_mm; Peak SHALL appear at detector center ±2 pixels; Correlation between C and PyTorch >0.95
  - Failure mode: Fixed beam center at 51.2mm regardless of detector size

- AT-PARALLEL-002 Pixel Size Independence
  - Setup: Fixed 256x256 detector, vary pixel sizes 0.05, 0.1, 0.2, 0.4mm, beam center at 25.6mm
  - Expectation: Beam center in pixels SHALL equal 25.6mm / pixel_size_mm ±0.1 pixels; Peak positions SHALL scale inversely with pixel size; Pattern correlation >0.95

- AT-PARALLEL-003 Detector Offset Preservation
  - Setup: Test beam centers (20,20), (30,40), (45,25), (60,60)mm with 256x256, 512x512, 1024x1024 detectors
  - Expectation: Peak SHALL appear at beam_center_mm / pixel_size_mm ±1 pixel; Offset ratios preserved ±2%

- AT-PARALLEL-004 MOSFLM 0.5 Pixel Offset
  - Setup: MOSFLM vs XDS convention comparison, 256x256 detector, beam center 25.6mm
  - Expectation: MOSFLM SHALL add +0.5 pixel offset; Peak position difference SHALL be 0.4-0.6 pixels between conventions; Pattern correlation >0.99 when aligned

- AT-PARALLEL-005 Beam Center Parameter Mapping
  - Setup: Test -Xbeam/-Ybeam vs -ORGX/-ORGY vs -Xclose/-Yclose parameter equivalence
  - Expectation: Equivalent configurations SHALL produce same beam centers ±0.5 pixels; Pivot mode SHALL be set consistently

- AT-PARALLEL-006 Single Reflection Position
  - Setup: Cubic crystal 100Å, single (1,0,0) reflection, vary distance (50,100,200mm) and wavelength (1.0,1.5,2.0Å)
  - Expectation: Peak position SHALL match Bragg angle calculation θ=arcsin(λ/(2d)) ±0.5 pixels; Distance scaling ratio ±2%; Wavelength scaling follows Bragg's law ±1%

- AT-PARALLEL-007 Peak Position with Rotations
  - Setup: 100,100,100,90,90,90 cell; -default_F 100; detector 256×256, -pixel 0.1, -distance 100; MOSFLM; auto beam center; -phi 0 -osc 0; -mosaic 0; divergence=0; dispersion=0; -oversample 1; full-frame ROI; -pivot beam; -detector_rotx 5 -detector_roty 3 -detector_rotz 2 -twotheta 10.
  - Procedure: Run C and PyTorch with identical flags. Detect local maxima above the 99.5th percentile; select top N=25 peaks. Register C↔PyTorch peaks via Hungarian matching with 1.0‑pixel gating.
  - Pass: Image correlation ≥ 0.98; ≥ 95% matched peaks within ≤ 1.0 pixel; total float-image sums ratio in [0.9, 1.1].

- AT-PARALLEL-008 Multi-Peak Pattern Registration
  - Setup: Triclinic 70,80,90,75,85,95 cell; -default_F 100; N=5; detector 512×512, -pixel 0.1, -distance 100; MOSFLM; -phi 0 -osc 0; -mosaic 0; divergence=0; dispersion=0; -oversample 1; full-frame ROI.
  - Procedure: Find local maxima; take top N=100 peaks above the 99th percentile, using non‑max suppression radius=3 px. Match C↔PyTorch with Hungarian algorithm, 1.0‑pixel gating.
  - Pass: ≥ 95% matched within ≤ 1.0 pixel; RMS error of intensity ratios across matched peaks < 10%; image correlation ≥ 0.98.

- AT-PARALLEL-009 Intensity Normalization
  - Setup: Cell 100,100,100,90,90,90; detector 256×256, -pixel 0.1, -distance 100; MOSFLM; -phi 0 -osc 0; -mosaic 0; -oversample 1; point_pixel OFF.
  - Procedure:
    - N‑sweep: N ∈ {1,2,3,5,10} with -default_F 100 fixed (Na=Nb=Nc=N).
    - F‑sweep: F ∈ {50,100,200,500} with N=5 fixed.
    - For each run, compute I_max from a 21×21 window centered on the strongest peak.
    - Fit log(I_max) vs log(N) and log(I_max) vs log(F).
  - Pass: slope_N ≈ 6.0 ± 0.3 with R² ≥ 0.99; slope_F ≈ 2.0 ± 0.05 with R² ≥ 0.99; for each point the C/PyTorch I_max ratio mean within ±10% of 1.0.

- AT-PARALLEL-010 Solid Angle Corrections
  - Setup: Cell 100,100,100; N=5; -default_F 100; -phi 0 -osc 0; -mosaic 0; divergence=0; dispersion=0; -oversample 1. Distances R ∈ {50,100,200,400} mm; tilts ∈ {0°,10°,20°,30°}.
  - Modes: (A) point_pixel ON; (B) point_pixel OFF (with obliquity).
  - Procedure: For each R (and tilt in B) run C and PyTorch; compute total float‑image sum over the full detector.
  - Pass: (A) sum ∝ 1/R² within ±5%; (B) sum ∝ close_distance/R³ within ±10% (check pairwise ratios). In all cases C↔PyTorch correlation ≥ 0.98.

- AT-PARALLEL-011 Polarization Factor Verification
  - Setup: Cell 100,100,100; N=5; detector 256×256, -pixel 0.1, -distance 100; MOSFLM; -phi 0; -mosaic 0; -oversample 1; point_pixel OFF; polarization_axis aligned per convention.
  - A) Unpolarized (kahn_factor=0): Compute theoretical P = 0.5·(1+cos²(2θ)) from incident/diffracted unit vectors; compare pixelwise to implementation P.
  - B) Polarized (kahn_factor=0.95): Compute Kahn model P using the same vectors/axis; compare pixelwise to implementation P.
  - Pass: For A and B, R² ≥ 0.95 vs theory and mean absolute relative error ≤ 1% (A) and ≤ 2% (B). C↔PyTorch image correlation ≥ 0.98 for identical axes/seeds.

- AT-PARALLEL-012 Reference Pattern Correlation
  - Setup: Use the canonical C commands in tests/golden_data/README.md to generate fixtures: simple_cubic (1024×1024), triclinic_P1 (512×512, explicit misset), and cubic_tilted_detector (rotations + 2θ). Run PyTorch with identical flags.
  - Pass: simple_cubic correlation ≥ 0.999 and top N=50 peaks ≤ 0.5 px; triclinic_P1 correlation ≥ 0.995 and top N=50 peaks ≤ 0.5 px; tilted correlation ≥ 0.98 and top N=50 peaks ≤ 1.0 px.
  - High-resolution variant: Setup: λ=0.5Å; detector 4096×4096, pixel 0.05mm, distance 500mm; cell 100,100,100; N=5; compare on a 512×512 ROI centered on the beam. Pass: No NaNs/Infs; C vs PyTorch correlation ≥ 0.95 on the ROI; top N=50 peaks in ROI ≤ 1.0 px.

- AT-PARALLEL-013 Cross-Platform Consistency
  - Constraints: CPU, float64, deterministic Torch mode; identical seeds; no GPU.
  - Setup: Use triclinic_P1 case from AT‑PARALLEL‑012.
  - Pass: PyTorch vs PyTorch (machine A vs B) allclose with rtol ≤ 1e−7, atol ≤ 1e−12 and correlation ≥ 0.999. C vs PyTorch allclose with rtol ≤ 1e−5, atol ≤ 1e−6 and correlation ≥ 0.995.

  - AT-PARALLEL-014 Noise Robustness Test
  - Setup: Create a float image with moderate intensities (e.g., simple_cubic scaled to mean ≈ 1e3). Generate SMV integer images with Poisson noise for two seeds (e.g., 123 and 456) using the same scale/ADC.
  - Metrics: mean(intimage) within ±1% of scale·mean(float)+ADC per seed; for top N=20 float-image peaks, median centroid shift ≤ 0.5 px and 90th percentile ≤ 1.0 px in noisy images; overload counts across seeds within ±10%.
  - Pass: All metrics satisfied for both seeds.

- AT-PARALLEL-015 Mixed Unit Input Handling
  - Setup: Test various unit combinations: distance in mm, wavelength in Å, angles in degrees
  - Expectation: Unit conversions SHALL be applied consistently; Results SHALL be independent of input units used; No unit confusion errors

- AT-PARALLEL-016 Extreme Scale Testing
  - Setup: Representative extremes (C and PyTorch): (1) Tiny: N=1, λ=0.1Å, distance=10mm, 128×128, pixel 0.05mm; (2) Large cell: 300,300,300,90,90,90; N=10; λ=6Å; 1024×1024; pixel 0.1mm; (3) Long distance: distance=10m; 256×256; pixel 0.2mm. Common: φ=0; mosaic=0; divergence/dispersion=0; oversample=1.
  - Pass: No NaNs/Infs; no exceptions; C vs PyTorch correlation ≥ 0.95; top N=25 peaks ≤ 2 px.

- AT-PARALLEL-017 Grazing Incidence Geometry
  - Setup: Large detector tilts >45°, twotheta>60°, oblique incidence
  - Expectation: Geometry calculations SHALL remain stable; Solid angle corrections SHALL be applied correctly; No singularities in rotation matrices

- AT-PARALLEL-018 Crystal Boundary Conditions
  - Setup: Crystal at singular orientations, aligned axes, zero-angle cases
  - Expectation: No division by zero errors; Degenerate cases SHALL be handled gracefully; Results SHALL be continuous near boundaries

 

- AT-PARALLEL-020 Comprehensive Integration Test
  - Setup: Triclinic 70,80,90,75,85,95; N=5; -mosaic 0.5; -mosaic_dom 5; -phi 0 -osc 90 -phisteps 9; -detector_rotx 5 -detector_roty 3 -detector_rotz 2; -twotheta 10; absorption enabled (e.g., -detector_abs 500 -detector_thick 450 -thicksteps 5); polarization K=0.95; detector 512×512, pixel 0.1mm, distance 100mm; -oversample 1; fixed seeds.
  - Pass: Runs without errors; C vs PyTorch correlation ≥ 0.95; top N=50 peaks ≤ 1.0 px; total sum ratio in [0.9, 1.1].

  - AT-PARALLEL-021 Crystal Phi Rotation Equivalence
  - Setup: Use cubic cell (100,100,100,90,90,90) with -phi 0, -osc 90, -phisteps 1 (midpoint ≈ 45°) and a second case with -phisteps 9 (-phistep 10) covering the same 90° range; fixed seeds; small detector (e.g., -detpixels 256 -pixel 0.1) and tight ROI centered on beam.
  - Expectation: For identical inputs, C and PyTorch float images SHALL match within numeric tolerances (rtol ≤ 1e-5, atol ≤ 1e-6); dominant peak positions SHALL rotate consistently with φ (midpoint ≈ 45° for single-step case); multi-step case (phisteps>1) SHALL match after normalization by steps; image correlation >0.99 and peak position error ≤0.5 pixels.

  - AT-PARALLEL-022 Combined Detector+Crystal Rotation Equivalence
  - Setup: Apply non-zero detector rotations (e.g., -detector_rotx 5 -detector_roty 3 -detector_rotz 2 -twotheta 10) together with crystal φ rotation cases from AT-PARALLEL-021; fixed seeds; same small detector/ROI settings.
  - Expectation: C and PyTorch float images SHALL agree within tolerances (rtol ≤ 1e-5, atol ≤ 1e-6); peak trajectories reflect both detector and crystal rotations; total intensity conservation within ±10% across the compared images; correlation >0.98 and peak alignment within ≤1 pixel after accounting for expected rotational shifts.

  - AT-PARALLEL-023 Misset Angles Equivalence (Explicit α β γ)
  - Setup: φ=0, osc=0; cells: triclinic (70,80,90,75,85,95) and cubic (100,100,100,90,90,90); run with explicit float -misset triplets in degrees: (0.0,0.0,0.0), (10.5,0.0,0.0), (0.0,10.25,0.0), (0.0,0.0,9.75), (15.0,20.5,30.25). Detector 256×256, -pixel 0.1, fixed -default_F and seeds. Use identical flags for C and PyTorch.
  - Expectation: Right‑handed XYZ rotations applied to reciprocal vectors once at init; real vectors recomputed. For each case, C vs PyTorch float images allclose (rtol ≤ 1e−5, atol ≤ 1e−6), correlation ≥ 0.99; top N=25 peaks within ≤ 0.5 px.

  - AT-PARALLEL-024 Random Misset Reproducibility and Equivalence
  - Setup: Implementations SHALL support -misset random and -misset_seed. Prefer a C‑compatible RNG (e.g., LCG) for identical angle sampling. Case: cubic 100,100,100; N=5; λ=1.0; detector 256×256, pixel 0.1mm, distance 100mm; φ=0; osc=0; mosaic=0; -oversample 1. Test two seeds S∈{12345,54321}.
  - Expectation: Determinism: PyTorch same‑seed runs are identical (rtol ≤ 1e−12, atol ≤ 1e−15). Cross‑impl equivalence: For each seed, C vs PyTorch allclose (rtol ≤ 1e−5, atol ≤ 1e−6), correlation ≥ 0.99. Seed effect: Different seeds produce correlation ≤ 0.7 within the same implementation. SHOULD: if sampled angles are reported, they match within 1e−12 rad after unit conversions.

  - AT-PARALLEL-025 Maximum Intensity Position Alignment
  - Setup: Cell 100,100,100,90,90,90; -lambda 1.0; -N 1; -default_F 100; detector 64×64, -pixel 0.1, -distance 100; MOSFLM convention; no rotations, no mosaic, no divergence/dispersion.
  - Expectation: The pixel coordinates of maximum intensity SHALL match between C and PyTorch implementations within 0.5 pixels. Specifically: |argmax(C_image) - argmax(PyTorch_image)| < 0.5 for both row and column indices. This test detects any systematic coordinate shift including MOSFLM +0.5 pixel offsets, axis swaps, or origin differences.

  - AT-PARALLEL-026 Absolute Peak Position for Triclinic Crystal
  - Setup: Triclinic cell 70,80,90,85,95,105; -lambda 1.5; -N 1; -default_F 100; detector 256×256, -pixel 0.1, -distance 150; MOSFLM convention; identity orientation matrix.
  - Expectation: The brightest Bragg peak SHALL appear at the same absolute pixel position (±1.0 pixel) in both C and PyTorch implementations. This validates the entire crystallographic chain for non-orthogonal unit cells.

Quality Bar Checklist (Informative)

- All major formulas and conversions are explicit and match the implementation.
- CLI options and synonyms reflect exactly what this code parses today.
- Output formats and headers match exactly what is written.
- Sampling structure, normalization, and edge-case behavior (e.g., out-of-range interpolation, last-
value multiplicative factors, clamping Na/Nb/Nc ≥ 1) are fully specified.

Developer Tools — Acceptance Tests (Optional)

- AT-TOOLS-001 Dual-Runner Comparison Script
  - Purpose: Run the C and PyTorch implementations with identical arguments; capture runtimes; compute comparison metrics; save preview images and a reproducible artifact bundle.
  - Scope: Optional developer tooling. This AT is normative for the script’s behavior and outputs, but it does NOT gate Core Engine or C–PyTorch Equivalence conformance and is not counted in AT-PARALLEL totals.
  - Invocation:
    - Script name SHOULD be exposed as a console entry `nb-compare` (preferred) or available at `scripts/nb_compare.py`.
    - Usage: `nb-compare [--outdir DIR] [--roi xmin xmax ymin ymax] [--threshold T] [--resample] [--png-scale PCTL] [--save-diff] [--c-bin PATH] [--py-bin PATH] -- ARGS...`
    - ARGS... are forwarded unchanged to both runners (C and PyTorch).
    - Binary resolution: C runner from `--c-bin` or `NB_C_BIN` env (default `./nanoBragg` in CWD); PyTorch runner from `--py-bin` or `NB_PY_BIN` env (default `nanoBragg` on PATH or `python -m nanobrag_torch`).
  - Behavior:
    - Preflight: verify both runners are executable; ensure any float outputs are captured even if caller did not pass `-floatfile` by adding separate temp paths per runner; preserve and log original stdout/stderr.
    - Runtime capture: run C first then PyTorch using identical ARGS; measure wall time using a monotonic clock; print `C runtime: X.XXX s` and `Py runtime: Y.YYY s`.
    - Load float outputs for metrics. If shapes differ: without `--resample` exit with error code 4; with `--resample`, resize PyTorch image to C’s shape via nearest-neighbor and note this in the summary.
    - ROI: if provided, compute metrics on the ROI, otherwise on the full frame.
  - Metrics (on float images after ROI/resample as applicable):
    - Pearson correlation coefficient (flattened ROI), MSE, RMSE, max absolute difference, total sums (C_sum, Py_sum) and their ratio.
    - Optional SSIM MAY be included.
    - Prints a one-line summary and a small table to stdout.
  - Outputs (unique artifact directory):
    - Directory: `comparisons/YYYYMMDD-HHMMSS-<short-hash>` where `<short-hash>` is a hash of canonicalized ARGS.
    - Files: `c_stdout.txt`, `c_stderr.txt`, `py_stdout.txt`, `py_stderr.txt`, `c_float.bin`, `py_float.bin` (copied or symlinked), optional `diff.bin`; `c.png`, `py.png` (8‑bit previews), optional `diff.png` heatmap if `--save-diff`.
    - `summary.json` with fields: args, binaries used, ROI, resample flag, `runtime_c_ms`, `runtime_py_ms`, `correlation`, `mse`, `rmse`, `max_abs_diff`, `sum_c`, `sum_py`, `sum_ratio`, `png_scale_method` and percentile.
  - PNG previews (for visualization only, not for metrics):
    - Default scaling: linear 0 to the union 99.5th percentile of the two images (over the ROI), clipped and mapped to [0,255] uint8. `--png-scale` overrides percentile; log scaling MAY be offered but MUST be noted in `summary.json`.
  - Exit codes:
    - 0: success; metrics computed; artifacts saved.
    - 1: usage error; 2: runner failure (non‑zero exit); 3: correlation < `--threshold` (if provided); 4: dimension mismatch without `--resample`; 5: I/O or parse error.
  - Examples:
    - `nb-compare --threshold 0.98 --roi 100 356 100 356 -- -default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -detpixels 256 -distance 100`
    - `NB_C_BIN=./nanoBragg NB_PY_BIN=nanoBragg nb-compare -- -default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -detpixels 256 -distance 100`
  - Notes:
    - Runtimes are informational and MUST NOT be used for conformance gating; they depend on hardware and environment. Metrics operate on float images (pre‑noise/ADC) regardless of any integer/noise outputs requested via ARGS.

Conformance Profiles (Normative)

- Core Engine Profile
  - Covers physics, geometry, sampling, interpolation, background/noise, statistics, and I/O semantics independent of transport. Implementations conforming to this profile SHALL satisfy all normative sections and acceptance tests in this document except those explicitly scoped to the CLI binding.

- Reference CLI Binding Profile
  - Scope: Implementations claiming CLI compatibility SHALL expose a command-line interface that maps flags, defaults, units, precedence, and outputs as defined below. Unknown flags SHOULD produce a clear error with usage guidance. Synonyms listed MUST be supported equivalently.

- C-PyTorch Equivalence Profile
  - Scope: Implementations claiming equivalence with the C reference implementation SHALL pass all AT-PARALLEL-* tests with specified tolerances. This profile ensures that alternative implementations produce outputs functionally equivalent to the original nanoBragg.c.
  - Requirements: Must conform to Core Engine Profile and pass all 23 AT-PARALLEL tests.
  - Key tolerances: Pattern correlation >0.95 for general cases, >0.999 for simple cubic; Peak position accuracy ±2 pixels; Intensity scaling within 2x; Beam center calculation must scale with detector size.
  - Units & conversions:
    - Å→m = ×1e−10; mm→m = ÷1000; µm→m = ×1e−6; deg→rad = ×π/180; mrad→rad = ÷1000.
    - Wavelength: -lambda|-wave Å→m; -energy eV→m via λ = (12398.42/E)·1e−10.
    - Dispersion percent→fraction by ÷100.
    - Fluence derivation: fluence = flux·exposure / beamsize^2 when flux ≠ 0 and exposure > 0 and beamsize ≥ 0; exposure > 0 recomputes flux to be consistent with chosen fluence and beamsize.
  - Inputs & files:
    - -hkl <file>: P1 “h k l F” text; required unless Fdump.bin exists or -default_F > 0.
    - -mat <file>: MOSFLM A-matrix (reciprocal vectors scaled by 1/λ), rescaled internally by (1e−10/λ).
    - -cell a b c α β γ: Direct cell in Å, deg; alternative to -mat.
    - -img/-mask <file>: Apply recognized SMV header keys; -mask zeros are skipped when rendering.
    - -sourcefile <file>: Per-source columns X Y Z weight λ; missing values default as in Sources.
  - Detector geometry:
    - -pixel <mm>; -detpixels <N> (square) or -detpixels_f|-detpixels_x <N>, -detpixels_s|-detpixels_y <N>.
    - -detsize <mm> (square) or -detsize_f/-detsize_s <mm>.
    - -distance <mm> (sets pivot=BEAM); -close_distance <mm> (sets pivot=SAMPLE).
    - -detector_rotx/-roty/-rotz <deg>; -twotheta <deg> with -twotheta_axis x y z.
    - -point_pixel; -curved_det (flag; no argument).
    - -Xbeam/-Ybeam <mm> force pivot=BEAM; -Xclose/-Yclose <mm> and -ORGX/-ORGY <pixels> force pivot=SAMPLE; -pivot beam|sample overrides.
    - Derived: ORGX = Fclose/pixel + 0.5; ORGY = Sclose/pixel + 0.5. DIALS origin from dot products of pix0 with lab axes [0,0,1], [0,1,0], [−1,0,0] in mm.
  - Beam/detector conventions:
    - -mosflm, -adxv, -denzo, -xds, -dials set basis vectors, beam/polarization vectors, spindle and 2θ axes, and default pivot as in Geometry & Conventions. Providing any of -fdet_vector, -sdet_vector, -odet_vector, -beam_vector, -polar_vector, -spindle_axis, -twotheta_axis, -pix0_vector selects CUSTOM.
  - Absorption & thickness:
    - -detector_abs <µm>|inf|0; -detector_thick <µm>; -detector_thicksteps|-thicksteps <int>.
    - If only a layer count is provided (no total thickness or per-layer step), a finite default total thickness (e.g., 0.5 µm) SHALL be assumed and the per-layer step derived; thickness modeling SHALL be active in this case.
  - Sampling:
    - -phi <deg>, -osc <deg>, -phistep <deg>, -phisteps <int>; -dmin <Å>.
    - -oversample <int>; -oversample_thick, -oversample_polar, -oversample_omega apply per-subpixel normalization to the running sum.
    - -roi xmin xmax ymin ymax (inclusive; zero-based internally).
  - Sources, divergence & dispersion:
    - -lambda|-wave <Å> or -energy <eV>; -fluence <photons/m^2> or -flux/-exposure/-beamsize to derive fluence; sample_y/z clipped to beamsize if beamsize > 0 and smaller (with warning).
    - Divergence: -divergence <mrad> sets both ranges; -hdivrange/-vdivrange <mrad>; -hdivstep/-vdivstep <mrad>; -hdivsteps/-vdivsteps <int>; -divsteps sets both counts. Auto-resolution rules: if only count is given, default angular range=1.0 rad and derive step; if only step is given, set range=step and counts=2; if range+count, derive step; enforce counts ≥ 2 for nonzero ranges. -round_div (default) culls to ellipse; -square_div disables culling.
    - Dispersion: -dispersion <percent>, -dispsteps <int>; auto-resolution rules analogous to divergence.
    - -sourcefile weighting: Each source’s contribution MUST be multiplied by its weight before division by steps.
  - Crystal size/shape/mosaic:
    - -Na/-Nb/-Nc <int>, -N <int> (clamped to ≥1 when converting from sizes); -samplesize|-xtalsize <mm> or per-axis variants.
    - -square_xtal (default), -round_xtal, -gauss_xtal, -binary_spots|-tophat_spots; -fudge <value>.
    - -mosaic|-mosaici|-mosaic_spr <deg>; -mosaic_dom <int>; -misset random or -misset α β γ (deg) with seeds.
  - Interpolation:
    - -interpolate enables tricubic; -nointerpolate disables. Auto default: enable if any of Na/Nb/Nc ≤ 2; else disable. If 4×4×4 neighborhood is out of range, a one-time warning is printed; default_F is used for that evaluation; interpolation MAY be disabled thereafter by the engine.
  - Background & noise:
    - -water <µm> background term; -noisefile|-noiseimage enables Poisson noise; -nonoise disables; -seed controls RNG. Poisson exact for small means, rejection up to 1e6, Gaussian approximation beyond.
  - Outputs:
    - -floatfile|-floatimage (4-byte floats, fast-major); -intfile|-intimage (SMV unsigned short). -scale, -adc, -pgmfile|-pgmimage, -pgmscale, -nopgm as in File I/O. SMV headers MUST include the listed keys and data ordering MUST be slow*fpixels + fast.
  - Precedence & overrides:
    - Last of -img/-mask wins for shared header keys; -mask interprets BEAM_CENTER_Y as detsize_s − value, -img uses value directly. Convention selection sets default vectors and pivot; custom vectors set CUSTOM. -Xbeam/-Ybeam force pivot=BEAM; -Xclose/-Yclose/-ORGX/-ORGY force pivot=SAMPLE; -pivot overrides. Missing -hkl and Fdump.bin and -default_F=0 SHALL produce a usage error.
  - Normalization & steps:
    - steps = sources × mosaic_domains × phisteps × oversample^2. Per-subpath: add F_cell^2 · F_latt^2 into I (starting at I_bg), applying per-subpixel capture/polar/ω if respective oversample flags are set. Final scaling per pixel S = r_e^2 · fluence · I / steps, then apply any factor whose oversample flag is NOT set using the last computed values.
  - Error handling & reporting:
    - Usage/help MUST enumerate flags and synonyms with units and defaults. Missing required inputs or inconsistent parameters MUST produce clear errors.
