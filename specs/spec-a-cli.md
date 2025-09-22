# nanoBragg Spec A — CLI Binding

This shard documents the command-line interface, header precedence, and CLI-focused acceptance tests. It should be read alongside [spec-a-core.md](spec-a-core.md) for the simulation engine requirements and [spec-a-parallel.md](spec-a-parallel.md) for conformance profiles.

CLI Interface (Normative)

All options recognized by this code version are enumerated below. Values with units are converted
immediately as specified in Units & Conversions. Unsupported flags are not recognized even if
present in header comments.

- Input files:
    - -hkl <file>: Text file of “h k l F” (integers h,k,l; real F). Required unless Fdump.bin exists
or -default_F used.
    - -mat <file>: 3×3 MOSFLM-style A matrix (reciprocal cell vectors scaled by 1/λ). Required
unless -cell used.
    - -cell a b c alpha beta gamma: Direct cell in Å and degrees; alternative to -mat.
    - -img <file>: Read SMV header; may set fpixels, spixels, pixel size (mm), distance (mm), close
distance (mm), wavelength (Å), beam centers (mm), ORGX/ORGY (pixels), φ start (deg), oscillation
range (deg), 2θ (deg). Image data is read but not used.
    - -mask <file>: Read SMV mask; uses same headers to initialize geometry as -img. Zero-valued
mask pixels are skipped during rendering.
    - -sourcefile <file>: Multi-column text file with up to five columns per source: X, Y, Z,
weight, λ. Missing columns default to values described in “Sources & divergence” below.
- HKL caching:
    - On reading -hkl, the program writes a binary dump Fdump.bin to speed subsequent runs.
    - If -hkl is not provided, it attempts to read Fdump.bin. If neither is available and -default_F
is zero, the program prints usage and exits.
- Structure factors:
    - -default_F <F>: F for any HKL falling outside the loaded HKL grid (also used to prefill).
Default 0.
- Detector pixel geometry:
    - -pixel <mm>: Pixel size (mm). Default 0.1 mm.
    - -detpixels <N>: Square detector pixel count: sets both fpixels and spixels to N.
    - -detpixels_f <N>, -detpixels_x <N>: Fast-axis pixels.
    - -detpixels_s <N>, -detpixels_y <N>: Slow-axis pixels.
    - -detsize <mm>: Square detector side (mm): sets both fast and slow sizes.
    - -detsize_f <mm>, -detsize_s <mm>: Sides in mm.
    - -distance <mm>: Sample-to-detector center distance (mm). Sets pivot to BEAM.
    - -close_distance <mm>: Minimum distance from sample to detector plane along its normal (mm).
Sets pivot to SAMPLE.
    - -point_pixel: Use 1/R^2 solid-angle only (no obliquity).
- Detector orientation:
    - -detector_rotx <deg>, -detector_roty <deg>, -detector_rotz <deg>: Detector rotations about lab
axes (radians internally).
    - -twotheta <deg>: Detector rotation about twotheta_axis.
    - -twotheta_axis x y z: Axis (unit vector) for -twotheta.
    - -curved_det: Treat detector pixels as lying on a sphere so all pixels are equidistant from
sample. Switch only; no argument used.
- Detector absorption:
    - -detector_abs <µm>|inf|0: Attenuation depth (µm); “inf” or 0 disable absorption (μ=0,
thickness=0).
    - -detector_thick <µm>: Sensor thickness (µm).
    - -detector_thicksteps <int> or -thicksteps <int>: Discretization layers through the thickness.
- Beam/conventions:
    - -mosflm, -xds, -adxv, -denzo, -dials: Predefined detector/beam conventions (see Geometry
& conventions).
    - -pivot beam|sample: Override pivot; otherwise set by convention or certain flags as noted.
    - -fdet_vector x y z, -sdet_vector x y z, -odet_vector x y z, -beam_vector x y z, -polar_vector
x y z, -spindle_axis x y z, -twotheta_axis x y z: Custom unit vectors; sets convention to CUSTOM.
    - -pix0_vector x y z: Detector origin offset vector (meters) from sample to the first (min fast,
min slow) pixel prior to rotations; sets convention to CUSTOM.
    - -Xbeam <mm>, -Ybeam <mm>: Projected direct-beam position on detector (mm); sets pivot to BEAM.
    - -Xclose <mm>, -Yclose <mm>: Near point (mm) on detector when pivoting about sample; sets pivot
to SAMPLE.
    - -ORGX <pixels>, -ORGY <pixels>: XDS-style beam center; sets pivot to SAMPLE.
- Beam spectrum/divergence:
    - -lambda <Å>, -wave <Å>: Central wavelength (Å).
    - -energy <eV>: Central energy (eV); converted to λ.
    - -dispersion <percent>: Spectral width; fraction internally.
    - -dispsteps <int>: Number of wavelength steps across the dispersion range.
    - -divergence <mrad>: Sets both horizontal and vertical angular ranges (radians internally).
    - -hdivrange <mrad>, -vdivrange <mrad>: Angular ranges (radians internally).
    - -hdivstep <mrad>, -vdivstep <mrad>: Angular step sizes (radians internally).
    - -hdivsteps <int>, -vdivsteps <int>, -divsteps <int>: Step counts for divergence (if only
-divsteps is given, it sets both).
- Polarization:
    - -polar <value>: Kahn polarization factor (dimensionless). Default printed value “polarization”
is used.
    - -nopolar: Disable polarization correction (factor forced to 1).
- Crystal size/shape and mosaicity:
    - -Na <int>, -Nb <int>, -Nc <int>, -N <int>: Number of unit cells along a,b,c. Any values ≤1 are
clamped to 1 later (zero is not preserved).
    - -samplesize <mm> or -xtalsize <mm>: Set crystal full widths in x=y=z (mm); alternative:
-sample_thick|_x, -sample_width|_y|-width, -sample_height|_z|-height, and -xtal_thick|_x,
-xtal_width|_y|-width, -xtal_height|_z|-height for each dimension.
    - -square_xtal (default), -round_xtal, -gauss_xtal, -binary_spots/-tophat_spots: Spot shapes.
See “Lattice factors”.
    - -fudge <value>: Shape parameter scaling (dimensionless).
    - -mosaic, -mosaici, or -mosaic_spr <deg>: Isotropic mosaic spread (degrees).
    - -mosaic_dom <int>: Number of mosaic domains.
- Sampling:
    - -phi <deg>: Starting spindle rotation angle.
    - -osc <deg>: Oscillation range.
    - -phistep <deg>: Step size.
    - -phisteps <int>: Number of steps.
    - -dmin <Å>: Minimum d-spacing cutoff. Subpaths with computed d < dmin are skipped.
    - -oversample <int>: Sub-pixel sampling per axis (square grid).
    - -oversample_thick: Recompute absorption per subpixel (see “Normalization” caveat).
    - -oversample_polar: Recompute polarization per subpixel (see “Normalization” caveat).
    - -oversample_omega: Recompute solid angle per subpixel (see “Normalization” caveat).
    - -roi xmin xmax ymin ymax: Pixel index limits (inclusive test; zero-based internal loops).
- Background:
    - -water <µm>: Effective cubic dimension (µm) used for a simple uniform “water” background term
(see exact formula in “Background & noise”).
- Source intensity:
    - -fluence <photons/m^2>, or use:
    - -flux &lt;photons/s&gt;, -exposure &lt;s&gt;, -beamsize &lt;mm&gt;: Determines fluence = flux·exposure / beamsize^2. Also clips sample_y and sample_z to beamsize if beamsize is positive and smaller—warning is printed.
- Output:
    - -floatfile|-floatimage <file>: Raw floats (pixels).
    - -intfile|-intimage <file>: SMV unsigned short (scaled).
    - -scale <value>: Scale for SMV (if ≤0, auto-scale to max ≈ 55000).
    - -adc <counts>: Additive offset for SMV and noise outputs (default 40).
    - -pgmfile|-pgmimage <file>: PGM output; scaled by -pgmscale or auto.
    - -pgmscale <value>: Relative scale for PGM.
    - -noisefile|-noiseimage <file>: SMV with Poisson noise (enabled when provided).
    - -nopgm: Disable PGM output.
- Interpolation:
    - -interpolate: Enable tricubic interpolation of F(hkl) between Bragg peaks.
    - -nointerpolate: Disable interpolation.
- Misc:
    - -printout: Verbose pixel prints (for debugging).
    - -printout_pixel f s: Limit prints to specified pixel.
    - -trace_pixel s f: Instrument trace for a pixel.
    - -noprogress / -progress: Toggle progress meter.
    - -seed <int>: Noise RNG seed (negative used internally), defaults to negative time.
    - -mosaic_seed <int>, -misset_seed <int>: Seeds for mosaic domain rotations and random misset.
    - -misset 10 20 30: Apply misset angles (deg). -misset random: Use a random orientation.
    - -stol <file>, -4stol <file>, -Q <file>, -stolout <file>: Auxiliary S(Q) support is read but
not used further in this version.

Unsupported flags in examples:

- -dispstep (example shows this; not recognized). The supported control is -dispsteps (count).
- -hdiv and -vdiv (examples show these; not recognized). Supported are -hdivrange and -vdivrange.

Precedence and overrides (Normative)

- If both -img and -mask headers are read, the last one read wins for shared header-initialized
quantities.
- Setting beam/detector conventions sets both the basis vectors and the default pivot. Explicit
-pivot overrides this.
- -Xbeam/-Ybeam force pivot to BEAM; -Xclose/-Yclose and -ORGX/-ORGY force pivot to SAMPLE.
- Custom basis vectors or -pix0_vector set convention to CUSTOM and use provided vectors where
specified.
- If both -flux/-exposure/-beamsize and -fluence are provided, fluence is recomputed to be
consistent with flux/exposure/beamsize whenever flux != 0 and exposure > 0 and beamsize ≥ 0;
exposure > 0 also recomputes flux to be consistent with the chosen fluence and beamsize.
- -N and -Na/-Nb/-Nc are clamped later to ≥1 (zero-valued sizes are not preserved, contrary to
header comments).
- If -hkl is missing and Fdump.bin is missing and -default_F is zero → exit with usage.

CLI Binding (Profile: Reference CLI) — Acceptance Tests (Normative)

References: ../docs/architecture/c_parameter_dictionary.md, ../docs/development/c_to_pytorch_config_map.md, ../docs/development/testing_strategy.md
Why: c_parameter_dictionary is the authoritative C flag→variable map; config_map captures implicit rules and parity pitfalls; testing_strategy outlines CLI acceptance patterns and end-to-end checks.

These tests apply only to implementations claiming the Reference CLI Binding Profile. They verify the presence and behavior of a CLI wrapper that maps flags to engine parameters and writes outputs/headers per this spec. Small detectors and tight ROIs are used to keep runtimes low.

- AT-CLI-001 CLI presence and help
  - Setup: Invoke nanoBragg with -h (or --help).
  - Expectation: Prints usage including at least: -hkl, -mat, -cell, -pixel, -detpixels, -distance, -lambda|-energy, -floatfile, -intfile, -noisefile, -pgmfile, -scale, -adc, -mosflm/-xds/-adxv/-denzo/-dials, -roi. Exit code indicates success.

- AT-CLI-002 Minimal render and headers
  - Setup: Run with small geometry (e.g., -detpixels 32 -pixel 0.1 -distance 100), a trivial HKL file (or -default_F), and specify -floatfile and -intfile outputs.
  - Expectation: Both files are created. SMV header contains required keys with units: SIZE1/2, PIXEL_SIZE(mm), DISTANCE(mm), WAVELENGTH(Å), BEAM_CENTER_X/Y(mm), ADXV/MOSFLM/DENZO centers, DIALS_ORIGIN(mm,mm,mm), XDS_ORGX/ORGY(pixels), CLOSE_DISTANCE(mm), PHI/OSC_START/OSC_RANGE(deg), TWOTHETA(deg), DETECTOR_SN, BEAMLINE. Data ordering is fast-major (index = slow*fpixels + fast).

- AT-CLI-003 Conventions and pivot behavior
  - Setup: Two runs: one with -mosflm, one with -xds; same detector, pixel, distance; small ROI.
  - Expectation: MOSFLM run uses pivot=BEAM; XDS run uses pivot=SAMPLE by default. ORGX/ORGY and ADXV/MOSFLM/DENZO center keys reflect the mapping rules defined in Geometry & Conventions. Providing -pivot sample|beam overrides the default pivot and leads to consistent origins/beam centers per the spec relations.

- AT-CLI-004 Header precedence and mask behavior
  - Setup: Provide -img and -mask files with conflicting header geometry values; ensure mask contains zeros in a small block; render a small ROI.
  - Expectation: The last file read among -img/-mask determines shared header-initialized quantities. Pixels where the mask value is 0 are skipped (remain zero in outputs) and excluded from statistics.

- AT-CLI-005 ROI bounding
  - Setup: Render with -roi xmin xmax ymin ymax strictly inside the detector.
  - Expectation: Only pixels within the ROI rectangle have non-zero values in the float/int/noise outputs; pixels outside remain zero.

- AT-CLI-006 Output scaling and PGM
  - Setup: Produce -intfile with and without -scale (and no noise). Also produce -pgmfile with and without -pgmscale.
  - Expectation: Without -scale, autoscale maps max float pixel to approximately 55,000 counts (within rounding). With -scale set, integer pixel = floor(min(65535, float*scale + adc)). PGM is P5 with header, a comment line “# pixels scaled by <pgm_scale>”, 255, then fast-major bytes equal to min(255, floor(float*pgm_scale)).

- AT-CLI-007 Noise determinism
  - Setup: Produce -noisefile twice with the same -seed and same inputs over a small ROI.
  - Expectation: Integer noise images are identical; overload counts match. Changing -seed changes the noise image.

- AT-CLI-008 dmin filtering
  - Setup: Two runs on a small ROI: one without -dmin and one with a moderately strict -dmin (Å) that removes high-angle contributions for that ROI.
  - Expectation: The -dmin run produces a strictly lower or equal total intensity sum over the ROI compared to the run without -dmin; differences are localized toward higher-angle pixels.

- AT-CLI-009 Error handling and usage
  - Setup: Invoke nanoBragg without -hkl and without an Fdump.bin and with -default_F=0.
  - Expectation: Program prints usage/help indicating required inputs and exits with a non-zero status.
