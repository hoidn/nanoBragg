Overview (Normative)

- Purpose: Simulates far-field diffraction from a perfect-lattice nanocrystal on a pixelated area
detector. No near-field propagation or detector PSF beyond pixel solid-angle/obliquity is modeled.
No symmetry is imposed; reflection indexing is P1 only (no Friedel pairing).
- Scope: Renders pixel intensities from a set of sources (beam divergence and spectral dispersion),
crystal orientation (including rotation oscillation and mosaic domains), and detector geometry.
Outputs: raw float image, SMV-format integer image (with and without Poisson noise), and optional
PGM.
- Key constants:
    - Classical electron radius squared r_e^2 = 7.94079248018965e-30 m^2.
    - Avogadro’s number = 6.02214179e23 mol^-1.

Units & Conversions (Normative)

- Length:
    - Å input → meters: multiply by 1e-10.
    - mm input → meters: divide by 1000.
    - µm input → meters: multiply by 1e-6.
- Angles:
    - Degrees → radians: multiply by π/180.
    - mrad → radians: divide by 1000.
- Wavelength:
    - Angstrom input -lambda → meters: λ = (Å)·1e-10.
    - Energy input -energy (eV) → meters: λ = (12398.42 / E_eV)·1e-10.
- Dispersion:
    - -dispersion percent → fraction: divide by 100.
- Beam polarization:
    - Kahn factor is dimensionless in [0, 1].
- Detector absorption:
    - -detector_abs (attenuation depth) in µm → m^-1: μ = 1 / (depth_µm·1e-6).
- Flux/fluence/exposure/beamsize:
    - Flux in photons/s.
    - Exposure in seconds.
    - Beamsize input in mm → meters: divide by 1000.
    - Fluence in photons/m^2. If flux, exposure, and beamsize are set, fluence = flux·exposure /
beamsize^2.
- Reciprocal measures:
    - Scattering vector q in m^-1.
    - stols (sinθ/λ) = 0.5·|q|.
- Output file header units:
    - SMV header PIXEL_SIZE and DISTANCE in mm; WAVELENGTH in Å; beam centers in mm; XDS origin
in pixels.

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
-sample_thick|_x, -sample_width|_y| -width, -sample_heigh|_z| -heigh, and -xtal_thick|_x,
-xtal_width|_y| -width, -xtal_heigh|_z| -heigh for each dimension.
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
    - -flux <photons/s>, -exposure <s>, -beamsize <mm>: Determines fluence = flux·exposure /
beamsize^2. Also clips sample_y and sample_z to beamsize if beamsize is positive and smaller—warning
is printed.
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

Geometry & Conventions (Normative)

- Detector basis: Three orthonormal unit vectors:
    - Fast axis vector f (increasing fast pixel index).
    - Slow axis vector s (increasing slow pixel index).
    - Detector normal vector o (increasing distance from sample).
    - If o is not provided or not unit length, it is generated as o = unit(f × s).
- Beam and polarization:
    - Incident beam unit vector b points from sample toward the source direction (used in geometry
and for q).
    - Polarization unit vector p is the incident E-vector direction.
    - “Vertical” axis v = unit(b × p).
    - Spindle axis u is the rotation axis for φ.
- Conventions (initialization prior to applying detector rotations and 2θ):
    - ADXV:
        - Beam b = [0 0 1]; f = [1 0 0]; s = [0 -1 0]; o = [0 0 1]; 2θ-axis = [-1 0 0]; p = [1 0 0];
u = [1 0 0].
        - Default beam center Xbeam = (detsize_f + pixel)/2, Ybeam = (detsize_s - pixel)/2.
        - Initial beam spot for Fbeam/Sbeam: Fbeam = Xbeam, Sbeam = detsize_s − Ybeam. Pivot = BEAM.
    - MOSFLM:
        - Beam b = [1 0 0]; f = [0 0 1]; s = [0 -1 0]; o = [1 0 0]; 2θ-axis = [0 0 -1]; p = [0 0 1];
u = [0 0 1].
        - Default Xbeam = (detsize_s + pixel)/2, Ybeam = (detsize_f + pixel)/2.
        - Fbeam = Ybeam + 0.5·pixel; Sbeam = Xbeam + 0.5·pixel. Pivot = BEAM.
    - DENZO: Same as MOSFLM bases, Fbeam = Ybeam, Sbeam = Xbeam. Pivot = BEAM.
    - XDS:
        - Beam b = [0 0 1]; f = [1 0 0]; s = [0 1 0]; o = [0 0 1]; 2θ-axis = [1 0 0]; p = [1 0 0]; u
= [1 0 0].
        - Defaults Xbeam = Xclose, Ybeam = Yclose. Fbeam = Xbeam; Sbeam = Ybeam. Pivot = SAMPLE.
    - DIALS:
        - Beam b = [0 0 1]; f = [1 0 0]; s = [0 1 0]; o = [0 0 1]; 2θ-axis = [0 1 0]; p = [0 1 0]; u
= [0 1 0].
        - Defaults Xbeam = Xclose, Ybeam = Yclose. Fbeam = Xbeam; Sbeam = Ybeam. Pivot = SAMPLE.
    - CUSTOM: Uses provided vectors; default Xbeam,Ybeam = Xclose,Yclose; Fbeam = Xbeam; Sbeam
= Ybeam.
- Beam center relations:
    - Fbeam/Sbeam (fast/slow coordinates in meters) are computed from Xbeam/Ybeam (mm converted to
m) per convention (note MOSFLM and DENZO introduce ±0.5 pixel shifts as shown above).
- Detector rotations and pivot:
    - Apply small-angle rotations to f, s, o: first around lab X/Y/Z by the provided angles, then a
rotation of all three around twotheta_axis by 2θ.
    - The scalar ratio r = b·o_after_rotations is computed. If close_distance is unspecified, it is
set to |r·distance|. Then distance is set to distance = close_distance / r.
    - If pivot = SAMPLE:
        - Define the detector origin vector from sample to the detector plane intersection of the
fast/slow near-point:
          D0 = −Fclose·f − Sclose·s + close_distance·o, then rotate D0 by the detector rotations
as above.
    - If pivot = BEAM:
        - Define the detector origin vector from sample to the chosen beam-center pixel:
          D0 = −Fbeam·f − Sbeam·s + distance·b (after rotations).
    - Point of closest approach on the detector plane: Fclose = −D0·f, Sclose = −D0·s,
close_distance = D0·o.
    - Direct-beam position after rotations:
        - Let R = close_distance/r·b − D0, then Fbeam = f·R, Sbeam = s·R; update distance =
close_distance / r.
- Origins in different conventions:
    - XDS origin (pixels): ORGX = Fclose/pixel + 0.5; ORGY = Sclose/pixel + 0.5.
    - DIALS origin (mm): computed by taking dot products with the fixed lab axes [0,0,1], [0,1,0],
and [−1,0,0] respectively on D0, then scaling by 1000.

Unit Cell & Orientation (Normative)

- From MOSFLM A matrix:
    - Read three reciprocal vectors in units of Å^-1·(1/λ_Å). They are scaled by (1e-10 / λ_m) to
remove λ from A, converting to Å^-1.
- From direct cell (Å, deg):
    - Compute V_cell from angles using:
        - aavg = (α+β+γ)/2, skew = sin(aavg)·sin(aavg−α)·sin(aavg−β)·sin(aavg−γ).
        - V_cell = 2·a·b·c·sqrt(|skew|).
    - Reciprocal lengths (Å^-1): |a*| = b·c·sin(α)/V_cell, cyclic permutations for b*, c*.
    - Construct reciprocal basis vectors from angles (standard triclinic relations).
- Misset:
    - -misset random: a random rotation is generated over a spherical cap of 90° (uniform over
SO(3)); the resulting Euler-equivalent angles are reported.
    - -misset α β γ (deg): these are applied to the reciprocal vectors (in order: X, Y, Z axes;
right-handed rotations).
- Direct–reciprocal relations:
    - V_star = a*·(b* × c*), V_cell = 1 / V_star.
    - Real-space basis: a = V_cell·(b* × c*), etc.
    - Recompute reciprocal basis from real-space via V_star scaling and cross products.
- Angle derivations:
    - Direct-space cosines: cos α = (b·c)/(|b||c|), etc., sines by ratios using V_cell/Vectors;
angles from atan2(sin, cos) with clamping to [-1,1].
    - Reciprocal-space angles similarly.
- Unit conversion to meters:
    - After cell construction, a, b, c (Å) are scaled by 1e-10 to meters for all subsequent dot
products with q.
- Crystal size:
    - If sample dimensions are provided (m), they are converted to cell counts: Na = ceil(sample_x/|
a|), etc. Each of Na, Nb, Nc is then clamped to ≥1. Crystal full widths: |a|·Na, |b|·Nb, |c|·Nc
(meters).

Sources, Divergence & Dispersion (Normative)

- Sources from file:
    - Each line: X, Y, Z (position vector in meters), weight (dimensionless), λ (meters). Missing
fields default to:
        - Position along −source_distance·b (source_distance default 10 m).
        - Weight = 1.0.
        - λ = λ0.
    - Positions are normalized to unit direction vectors (X,Y,Z overwrites become unit direction).
The weight column is read but ignored (equal weighting results).
- Generated sources (when no file provided):
    - Horizontal/vertical divergence grids are defined by ranges and either steps or step sizes.
Elliptical trimming: with round_div on, grid points outside the ellipse (normalized squared radius >
about 0.25 adjusted for even/odd grids) are skipped.
    - Each divergence point starts from vector −source_distance·b, rotated about p by vertical angle
and about v by horizontal angle; then normalized to a unit direction.
    - For each divergence direction, wavelength is sampled with dispsteps values across [λ0·(1 −
dispersion/2), λ0·(1 + dispersion/2)] with equal spacing dispstep determined by auto-selection (see
below).
    - Total number of sources = (#accepted divergence points) × dispsteps. Each source is
effectively equally weighted by normalization at the end (division by steps).
- Auto-selection rules:
    - For each of {horizontal divergence, vertical divergence, spectral dispersion} and detector
thickness:
        - If step count ≤ 0:
            - If range < 0 and step size ≤ 0: use 1 step, zero range (i.e., no spread).
            - If range < 0 and step size > 0: set range = step size, steps = 2.
            - If range ≥ 0 and step size ≤ 0: step size = range, steps = 2.
            - If range ≥ 0 and step size > 0: steps = ceil(range / step size).
        - If step count > 0:
            - If range < 0 and step size ≤ 0: set a nominal range and step size = range / steps.
            - If range < 0 and step size > 0: range = step size, steps = 2.
            - If range ≥ 0 and step size ≤ 0: step size = range / max(steps − 1, 1).
    - Mosaic domains:
        - If domains ≤ 0:
            - If mosaic spread < 0: domains = 1, spread = 0.
            - If spread == 0: domains = 1.
            - If spread > 0 and domains not set: domains = 10 (with one domain forced to identity).
        - If domains set > 0 and spread < 0: force domains = 1, spread = 0.

Sampling & Accumulation (Normative)

- Loop order per pixel within ROI and unmasked:
    - For each detector thickness layer index t = 0..thicksteps-1:
        - Odet = t·(thickness/steps) (meters).
        - For subpixel grid (oversample × oversample):
            - Compute detector-plane coordinates (meters): Fdet and Sdet at subpixel centers.
            - Detector point in lab frame: P = D0 + Fdet·f + Sdet·s + Odet·o. If curved detector is
enabled, an alternative spherical mapping is used: start at distance along b and rotate about s and
f by small angles Sdet/distance and Fdet/distance respectively.
            - Diffracted unit vector d = unit(P); airpath R = ||P||.
            - Solid angle per subpixel:
                - ω = pixel^2 / R^2 · (close_distance / R).
                - If point-pixel mode: ω = 1 / R^2.
            - Absorption per thickness layer (if enabled):
                - Parallax factor: ρ = d·o.
                - Capture fraction for this layer: exp(−t·Δz·μ/ρ) − exp(−(t+1)·Δz·μ/ρ), where Δz =
thickness/steps.
            - For each source:
                - Incident unit vector i = −source_dir (unitized); wavelength λ from source.
                - q = (d − i) / λ (m^-1). stol = 0.5·||q||.
                - If dmin > 0 and stol > 0 and dmin > 0.5/stol: skip this subpath.
                - Polarization factor (if enabled; Kahn model):
                    - cos(2θ) = i·d; sin^2(2θ) = 1 − cos^2(2θ).
                    - Construct B_in = unit(p × i), E_in = unit(i × B_in). Project d into this EB
plane: E_out = d·E_in, B_out = d·B_in. ψ = −atan2(B_out, E_out).
                    - Polarization factor = 0.5·(1 + cos^2(2θ) − K·cos(2ψ)·sin^2(2θ)), where K is
the Kahn factor from -polar.
                - Crystal orientation:
                    - φ step: φ = φ0 + (step index)*phistep; rotate the reference cell (a0,b0,c0)
about u by φ to get (ap,bp,cp).
                    - Mosaic: for each domain, apply the domain’s rotation to (ap,bp,cp) to get
(a,b,c).
                - Fractional Miller indices: h = a·q, k = b·q, l = c·q (dimensionless).
                - Nearest integer triplet: (h0, k0, l0) = round to nearest via ceil(x − 0.5).
                - Lattice factor F_latt:
                    - SQUARE (grating): F_latt = sincg(π·h, Na) · sincg(π·k, Nb) · sincg(π·l, Nc),
where
                        - sincg(x,N) = N if x = 0; otherwise sin(N·x)/sin(x).
                    - ROUND (sinc3 sphere): hrad^2 = (h−h0)^2·Na^2 + (k−k0)^2·Nb^2 + (l−l0)^2·Nc^2.
                        - F_latt = Na·Nb·Nc·0.723601254558268 · sinc3(π·sqrt(fudge·hrad^2)), where
                            - sinc3(x) = 3·[(sin x)/x − cos x]/x^2 (with sinc3(0)=1).
                    - GAUSS (in reciprocal space): Let Δr*^2 = ||(h−h0)·a* + (k−k0)·b* + (l−l0)·c*||
^2 · Na^2·Nb^2·Nc^2,
                        - F_latt = Na·Nb·Nc·exp(−(Δr*^2 / 0.63)·fudge).
                    - TOPHAT: F_latt = Na·Nb·Nc if (Δr*^2 · fudge < 0.3969); else 0.
                - Structure factor F_cell:
                    - If interpolation is on:
                        - Use 4×4×4 tricubic neighborhood at indices floor(h)±{1,0,1,2} (same for
k,l). If the 4-neighborhood would go out of bounds of the loaded HKL ranges, a one-time warning is
printed, the default_F is used for the current reflection, and interpolation is permanently disabled
for the rest of the run.
                    - If interpolation is off:
                        - Nearest-neighbor lookup of F_cell at (h0, k0, l0) if in-range; else F_cell
= default_F.
                - Intensity accumulation (additive term):
                    - I_term = (F_cell^2)·(F_latt^2).
                    - Accumulator I (per pixel) starts at I_bg (background, see below) and adds
I_term for every inner-loop combination.
                    - Normalization caveat:
                        - If -oversample_thick is set, after each addition the entire current
accumulator I is multiplied by the layer’s capture fraction (rather than multiplying I_term).
Similarly for -oversample_polar (multiply by polarization factor) and -oversample_omega (multiply by
ω). This means the multiplicative factors apply to the running sum, not per-term, and thus depend on
loop order and number of additions.
- Final per-pixel scaling:
    - Define steps = (number of sources) · (number of mosaic domains) · (phisteps) · (oversample^2).
    - After all loops (including all thickness layers and subpixels), compute:
        - S = r_e^2 · fluence · I / steps.
        - If -oversample_thick is NOT set, multiply S by the last computed capture fraction (from
the last subpixel and last layer). If -oversample_polar is NOT set, multiply S by the last computed
polarization factor. If -oversample_omega is NOT set, multiply S by the last computed ω. These “last
value” applications are not averages; they depend on the final loop state for that pixel.
    - Accumulate S into the float image.

Interpolation & Fallbacks (Normative)

- Interpolation mode defaults:
    - If -interpolate provided: on.
    - If -nointerpolate provided: off.
    - Otherwise auto: If any of Na, Nb, Nc ≤ 2, interpolation is enabled; else disabled.
- Out-of-range while interpolating:
    - If the required 4×4×4 neighborhood is not fully available within the HKL grid, the program:
        - Emits a one-time warning.
        - Uses default_F for that evaluation.
        - Permanently disables interpolation for the remainder of the run.

Background & Noise (Normative)

- Constant background per pixel (added before accumulation):
    - F_bg = 2.57 (dimensionless, “water” forward scattering amplitude).
    - I_bg = (F_bg^2) · r_e^2 · fluence · (water_size^3) · 1e6 · Avogadro / water_MW.
    - water_size is -water in µm converted to meters; water_MW = 18 g/mol.
    - Note: This formula is exactly as implemented; units do not match a physical volume
consistently (the 1e6 factor multiplies the cubic meter term).
- Poisson noise (if enabled by -noisefile):
    - For each pixel, draw from a Poisson distribution with mean = float image value (before scaling
and ADC) to produce an integer noise image. If mean > 1e6, a Gaussian approximation is used: N(mean,
variance=mean).
    - After sampling, add adc_offset, clamp to [0, 65535], count overloads.
- Noise RNG seeding:
    - Default seed is negative wall-clock time; can be overridden via -seed. Negative seeds are used
internally for initialization.

Polarization (Normative)

- Computed as described in Sampling. If -nopolar is set, the polarization factor is set to 1 for the
pixel (no effect). If -polar is provided, its value is used as Kahn factor K in [0,1].

Statistics (Normative)

- After rendering:
    - max_I: maximum float image pixel value and its fast/slow subpixel coordinates at which it was
last set.
    - mean = sum(pixel)/N; RMS = sqrt(sum(pixel^2)/(N − 1)).
    - RMSD from mean: computed as sqrt(sum((pixel − mean)^2)/(N − 1)).
    - N counts only pixels inside the ROI and unmasked.
    - These statistics are for the float image, not the SMV-scaled or noise images.

File I/O (Normative)

- HKL text input:
    - Two-pass read:
        - First pass: count lines of four values (h, k, l, F), track min/max of h,k,l (warn if non-
integers encountered).
        - Second pass: allocate a 3D grid [h_min..h_max]×[k_min..k_max]×[l_min..l_max] of doubles
and fill with F. Unspecified grid points retain their initial default_F if set and initialization
path was taken.
- HKL binary dump Fdump.bin:
    - Header: six integers h_min h_max k_min k_max l_min l_max followed by newline and form feed
character.
    - Data: For each h in 0..(h_range), for each k in 0..(k_range), write an array of (l_range+1)
doubles in native endianness. Read order matches write order.
- SMV outputs (-intfile and -noisefile):
    - File structure: ASCII header followed by binary data.
    - Header keys exactly as written:
        - {, newlines, key/value pairs terminated by ;, then closing }\f, padded with spaces to 512
bytes before data.
        - Required keys:
            - HEADER_BYTES=512;, DIM=2;, BYTE_ORDER=big_endian|little_endian;, TYPE=unsigned_short;
            - SIZE1=<fpixels>;, SIZE2=<spixels>;
            - PIXEL_SIZE=<mm>;, DISTANCE=<mm>;, WAVELENGTH=<Å>;
            - BEAM_CENTER_X=<mm>;, BEAM_CENTER_Y=<mm>;
            - ADXV_CENTER_X=<mm>;, ADXV_CENTER_Y=<mm>;
            - MOSFLM_CENTER_X=<mm>;, MOSFLM_CENTER_Y=<mm>;
            - DENZO_X_BEAM=<mm>;, DENZO_Y_BEAM=<mm>;
            - DIALS_ORIGIN=<mm>,<mm>,<mm>
            - XDS_ORGX=<pixels>;, XDS_ORGY=<pixels>;
            - CLOSE_DISTANCE=<mm>;
            - PHI=<deg>;, OSC_START=<deg>;, OSC_RANGE=<deg>;
            - TWOTHETA=<deg>;, DETECTOR_SN=000;, BEAMLINE=fake;
    - Data: unsigned short, fast-major (row-wise) ordering: pixel index = slow*fpixels + fast.
- Raw float image (-floatfile):
    - Binary file of pixels 4-byte floats in the same fast-major order. No header.
- PGM (-pgmfile):
    - P5 format:
        - P5, newline, <width> <height>, newline, comment line: # pixels scaled by <pgm_scale>,
newline, 255, newline, followed by width*height bytes (fast-major).
    - Values: min(255, float_pixel * pgm_scale) floored to integer.
- SMV header ingestion:
    - The following keys, if present in -img/-mask headers, are applied (last file read wins):
        - SIZE1, SIZE2: per-axis pixel counts.
        - PIXEL_SIZE (mm), DISTANCE(mm), CLOSE_DISTANCE(mm), WAVELENGTH(Å), BEAM_CENTER_X/Y (mm),
ORGX/ORGY (pixels), PHI (deg), OSC_RANGE (deg), TWOTHETA (deg).
    - Note: On reading -mask, Y beam center is interpreted as detsize_s − (value in mm); for -img it
is taken directly.

Randomness (Normative)

- RNG model: Uniform deviates on (0,1) via a linear congruential generator with shuffling (Numerical
Recipes pattern).
- Used for:
    - Poisson deviates:
        - Exact for means < 12.
        - Rejection sampling for larger means up to 1e6.
        - Gaussian approximation for means > 1e6: mean + sqrt(mean)*N(0,1).
    - Mosaic domain rotations: random unit vectors and rotation angles within the spherical cap
defined by -mosaic spread (deg).
    - Random misset: uniform over the sphere (90° cap).
- Seeds:
    - Noise seed: default negative time; controlled by -seed.
    - Mosaic seed: default -12345678; controlled by -mosaic_seed.
    - Misset seed: default equal to -seed; controlled by -misset_seed.

Error Handling & Warnings (Normative)

- Missing inputs: Without -hkl and a readable Fdump.bin, and -default_F = 0 → program prints usage
and exits.
- If -mat absent and -cell incomplete → usage printed and exit.
- Warnings printed for:
    - Non-integer h,k,l in HKL input.
    - “Oddball” cell angles outside [-1,1] tolerance (values are clamped for angle computation).
    - Auto-generated detector normal if not unit.
    - Potential sample clipping if beamsize < sample_y or sample_z.
    - When mosaic spread > 0 but mosaic_domains initially not set → default to 10 domains (warning
printed).
    - Interpolation out-of-range → disables interpolation for remainder of run (one-time warning).

Scenarios to Analyze (Informative)

- Example 1:
    - ./nanoBragg -mat auto.mat -hkl P1.hkl -distance 2500
    - Supported as-is. Internals:
        - Distance = 2.5 m. Pixel defaults: 0.1 mm; detector size defaults 102.4 mm per side (unless
overridden by headers).
        - Conventions default to MOSFLM unless overridden; pivot defaults to BEAM; Xbeam/Ybeam auto-
selected per convention if not provided.
        - Sources: 1 (no divergence/dispersion set). Mosaic: 1 domain, 0 spread (auto). φ: 1 step (0
range). Oversample: auto from crystal size and λ/distance/pixel; else set to recommended value ≥1.
        - Steps = oversample^2.
        - Geometry:
            - Load A matrix; rescale by 1/λ to Å^-1; derive real-space cell; convert to meters.
            - Set detector basis and origin per MOSFLM, apply rotations if provided, compute D0,
Fclose/Sclose/close_distance, Fbeam/Sbeam, XDS/DIALS origins.
        - Pixel walk:
            - For a chosen pixel, compute P = D0 + Fdet·f + Sdet·s (+ Odet·o), d = unit(P), q = (d −
b)/λ. Find nearest (h0,k0,l0), F_latt for shape, F_cell (nearest or interpolated). Accumulate I_term
and scale to S with r_e^2·fluence/steps and multiplicative factors as described.
- Example 2:
    - ./nanoBragg -mat A.mat -hkl P1.hkl -lambda 1 -dispersion 0.1 -dispstep 3 -distance 100
-detsize 100 -pixel 0.1 -hdiv 0.28 -hdivstep 0.02 -vdiv 0.28 -vdivstep 0.02 -fluence 1e24 -N 0
-water 0
    - Unsupported flags: -dispstep (use -dispsteps <int>), -hdiv (use -hdivrange), -vdiv (use
-vdivrange).
    - After replacing unsupported flags with supported ones:
        - λ = 1 Å = 1e-10 m. Dispersion = 0.1 (10%); choose -dispsteps 3 if that was intended.
        - Distance = 0.1 m; detsize = 0.1 m; pixel = 0.1 mm; fluence = 1e24 photons/m^2.
        - With -hdivrange 0.28 mrad, -hdivstep 0.02 mrad, -vdivrange 0.28 mrad, -vdivstep 0.02
mrad, auto-selection yields horizontal steps = ceil(0.28/0.02)=14, similarly vertical = 14, then
elliptical trimming reduces the count (only those within the ellipse kept).
        - -N 0 results in Na=Nb=Nc=1 (clamped to ≥1).
        - -water 0 disables the background term (I_bg still set but becomes 0 since size=0).
        - Steps = (#accepted divergence points) × dispsteps × mosaic_domains × phisteps ×
oversample^2. With default mosaic (spread 0) and φ defaults, this reduces to (ellipse points × 3
× oversample^2).
- Example 3:
    - ./nanoBragg -cell 74 74 36 90 90 90 -misset 10 20 30 -hkl P1.hkl -lambda 1 -dispersion 0.1
-dispstep 3 -distance 100 -detsize 100 -pixel 0.1 -hdiv 0.28 -hdivstep 0.02 -vdiv 0.28 -vdivstep
0.02 -fluence 1e24 -N 0 -water 0
    - Same unsupported flags as Example 2; apply same replacements. Geometry follows from direct
cell (scaled to meters) and misset angles applied to reciprocal space then converted back to real
space.

Glossary (Informative)

- Detector fast/slow axes f/s: unit vectors along increasing pixel indices in fast/slow directions.
- Detector normal o: unit vector normal to detector plane, pointing from sample to detector.
- Detector origin D0: vector from sample to the plane coordinate corresponding to near-point or beam
center depending on pivot.
- Beam b: unit vector from sample along the incident beam direction.
- Polarization p: unit E-vector direction of the incident beam.
- Vertical v: unit vector perpendicular to both beam and polarization: v = unit(b × p).
- Spindle u: unit rotation axis for φ.
- Xbeam/Ybeam: direct beam position on detector in mm units (for header reporting).
- Fbeam/Sbeam: beam position in fast/slow metric coordinates (meters) used to construct D0 when
pivoting about the beam.
- ORGX/ORGY: XDS beam center in pixels.
- DIALS origin: detector origin in mm projected onto lab axes as implemented.
- a,b,c: real-space unit cell vectors (meters) after all rotations.
- a*,b*,c*: reciprocal-space cell vectors (Å^-1).
- q: scattering vector in m^-1: (d − i)/λ.
- stol: 0.5·|q| in m^-1; used only for d_min cut.
- F_cell: structure factor amplitude (arbitrary units) from HKL input (no symmetry).
- F_latt: lattice transform factor (dimensionless) from chosen shape.
- I: accumulator for intensity before applying r_e^2 and fluence.
- ω: pixel solid angle factor (steradian approximation).
- μ: detector attenuation coefficient (m^-1).

Scope & Non‑Goals (Informative)

- Far-field diffraction only; no near-field wave optics or detector PSF beyond pixel obliquity.
- No space-group symmetry applied; no partiality model beyond lattice Fourier transforms.
- No detector nonlinearity modeling; no dark current or read noise (only Poisson photon noise).
- Source weights read from file are ignored; equal weighting via division by steps is always used.
- Interpolated amorphous background from -stol files is read but not used to alter pixel intensities
in this version.

Acceptance Criteria (Normative)

- Units and conversions listed for all input quantities and internal transformations.
- Every CLI option parsed by this version is documented with units, defaults, and semantics;
unsupported example options are called out with supported equivalents.
- Equations are provided for:
    - Detector point mapping: P = D0 + Fdet·f + Sdet·s + Odet·o (or spherical alternative if
enabled).
    - d, i, q, stol, d_min culling.
    - Pixel solid angle and point-pixel option.
    - Detector absorption per layer vs parallax: exp differences.
    - Polarization (Kahn model) with ψ definition.
    - Lattice transforms for SQUARE, ROUND, GAUSS, TOPHAT (including fudge and radii definitions).
    - Tricubic interpolation neighborhood and fallback to nearest/default_F.
    - Fluence, flux, exposure, beamsize: fluence = flux·exposure / beamsize^2; sample clipping
warnings.
    - Background I_bg formula.
    - Steps normalization and noted caveats for the oversample_* multiplicative application.
- File formats documented exactly as written/read, including SMV header keys, units, 512-byte
padding, and data ordering.

Quality Bar Checklist (Informative)

- All major formulas and conversions are explicit and match the implementation.
- CLI options and synonyms reflect exactly what this code parses today.
- Output formats and headers match exactly what is written.
- Sampling structure, normalization, and edge-case behavior (e.g., out-of-range interpolation, last-
value multiplicative factors, clamping Na/Nb/Nc ≥ 1) are fully specified.
