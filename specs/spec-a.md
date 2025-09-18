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
- Interpolated amorphous background from -stol files is read but not used to alter pixel intensities
in this version.

Acceptance Tests (Normative)

Structure Factors & Fdump

1. HKL two-pass bounds and grid
   - Given an HKL file containing at least three entries with distinct h,k,l (e.g., −1 0 0 F1, 0 0 0 F0, 1 0 0 F2), the loader SHALL:
     - First pass: compute h_min, h_max, k_min, k_max, l_min, l_max matching the extrema in the file; warn on any non-integer h,k,l values.
     - Second pass: allocate a 3D grid of size (h_range+1)×(k_range+1)×(l_range+1) and populate the exact indices with their F values.
     - If ranges are invalid (any range < 0), the program SHALL exit with an error.
2. default_F behavior
   - When -default_F > 0 and an HKL file is provided, the grid SHALL be prefilled to default_F before loading, and any HKL not present in the file remains default_F. When -default_F == 0, unspecified entries remain 0.
   - During rendering, for a nearest-neighbor lookup outside the HKL bounds, the structure factor amplitude used SHALL be default_F (or 0 if default_F==0).
3. Interpolation enabling and out-of-range handling
   - Auto-selection: If any of Na, Nb, Nc ≤ 2, tricubic interpolation SHALL be enabled by default; otherwise it SHALL be disabled. CLI flags -interpolate and -nointerpolate override this.
   - If, while interpolating, any 4×4×4 neighborhood would be out of bounds for the current (h,k,l), the implementation SHALL set F_cell to default_F for that evaluation AND permanently disable interpolation for the remainder of the run (subsequent evaluations use nearest-neighbor rules).
4. Binary cache (Fdump.bin)
   - After successfully loading an HKL file, the program SHALL write a cache file containing: a header line with six integers (h_min h_max k_min k_max l_min l_max) followed by a form feed, then contiguous pages of doubles for each k-slab across h, each containing (l_range+1) values.
   - On a subsequent run without -hkl, if Fdump.bin is readable, the program SHALL load the exact same grid extents and values as produced from the original HKL input.

Beam Model & Geometry

5. Convention initialization
   - Selecting each convention SHALL initialize beam and detector axes and pivots as follows:
     - MOSFLM and DENZO: beam +X, detector normal +X, fast +Z, slow −Y, pivot BEAM; MOSFLM maps Fbeam = Ybeam + 0.5·pixel, Sbeam = Xbeam + 0.5·pixel; DENZO uses Fbeam = Ybeam, Sbeam = Xbeam.
     - ADXV: beam +Z, detector normal +Z, fast +X, slow −Y, pivot BEAM; Fbeam = Xbeam, Sbeam = detsize_s − Ybeam.
     - XDS: beam +Z, detector normal +Z, fast +X, slow +Y, pivot SAMPLE; Fbeam = Xbeam, Sbeam = Ybeam.
     - DIALS: beam +Z, detector normal +Z, fast +X, slow +Y, pivot SAMPLE; Fbeam = Xbeam, Sbeam = Ybeam.
     - CUSTOM: Using user-specified axes (any of fast/slow/normal/beam/polar/spindle/twotheta/pix0) SHALL set convention to CUSTOM without modifying pivot unless -pivot is provided.
6. Pivot semantics and detector origin
   - BEAM pivot: With distance d and Fbeam/Sbeam in meters, the detector origin vector (from sample to detector local origin) SHALL be set to −Fbeam·f − Sbeam·s + d·b prior to subsequent rotations; after orientation, the reported direct-beam center in the detector frame SHALL agree with the beam-center mapping for the active convention.
   - SAMPLE pivot: With near-point Fclose/Sclose and close_distance in meters, the origin vector SHALL be set to −Fclose·f − Sclose·s + close_distance·o and then rotated; after orientation, Fclose = −origin·f, Sclose = −origin·s, close_distance = origin·o.
7. Rotations and two-theta
   - Detector axis rotations SHALL be applied in order: rotx about +X, then roty about +Y, then rotz about +Z, then a rotation of all three axes (and origin) about twotheta_axis by the specified two-theta angle.
   - The reported TWOTHETA value in outputs SHALL equal the user-specified value (deg).
8. Pixel mapping and solid angle
   - For each subpixel center (Fdet,Sdet), the 3D position vector SHALL be pos = origin + Fdet·f + Sdet·s (+ Odet·o for thickness layers). The diffracted unit vector is unit(pos), and the pixel solid-angle factor SHALL be:
     - Ω = (pixel_size^2 / |pos|^2)·(close_distance/|pos|) by default; if -point_pixel is set, Ω = 1/|pos|^2.
9. Polarization factor toggles
   - If -nopolar is set, the polarization factor applied SHALL be 1 for all contributions.
   - If -polar K is provided, the Kahn model SHALL be used with that K to compute the factor; with -oversample_polar it SHALL be applied per subpixel, otherwise once per pixel using the last computed value.

CLI, Config, and State Initialization

10. Header ingestion and precedence
    - When -img and/or -mask are provided, recognized header fields (pixel counts, pixel size, distance, close_distance, wavelength, beam center, ORGX/ORGY, φ start, oscillation, two-theta) SHALL initialize corresponding parameters; when both -img and -mask are provided, the last one read SHALL win for shared keys.
    - For -mask headers, BEAM_CENTER_Y SHALL be interpreted with a flip along the slow axis (Ybeam = detsize_s − value_mm/1000); for -img headers, BEAM_CENTER_Y SHALL be used directly (Ybeam = value_mm/1000).
11. Pivot choice
    - Providing -distance (without -close_distance) SHALL set pivot to BEAM. Providing -close_distance SHALL set pivot to SAMPLE. The -pivot flag SHALL override either.
12. Auto-selection of step counts
    - For each of horizontal divergence, vertical divergence, spectral dispersion, phi, and detector thickness sampling, missing combinations of count/range/step SHALL be resolved per the rules in “Sources, Divergence & Dispersion” and “Sampling & Accumulation”, resulting in:
      - No parameters → count=1, range=0, step=0.
      - Only step → range=step, count=2.
      - Only range → step=range, count=2.
      - Only count → range set to a finite default (angles: 1.0 rad; thickness: 0.5e-6 m) and step derived as range/(count−1) with count coerced to ≥2 for nonzero range.
13. Fluence and clipping
    - If -flux, -exposure, and -beamsize are provided, fluence SHALL be set to flux·exposure / beamsize^2. If beamsize > 0 and beamsize < sample_y or sample_z, the implementation SHALL clip those sample dimensions to beamsize and emit a warning.
14. ROI and mask behavior
    - Pixels outside the specified ROI (−roi xmin xmax ymin ymax) SHALL be skipped for simulation and excluded from statistics and outputs. Pixels with mask value 0 from -mask SHALL be skipped similarly.
15. Random seeds
    - Default seeds SHALL be: noise seed = negative wall-clock time; mosaic_seed = −12345678; misset_seed = noise seed. CLI -seed, -mosaic_seed, and -misset_seed SHALL override these.
16. Outputs and scaling
    - If -intfile is written and -scale ≤ 0 or not provided, the scaling factor SHALL be set to 55000 / max_float_pixel when max > 0, else 1.0; the ADC offset SHALL be added (default 40.0), values SHALL be clipped to [0,65535], and rounded to nearest.
    - If -nonoise is set, a noise image SHALL NOT be written even if -noisefile is specified; otherwise, the noise image SHALL be generated by Poisson (or Gaussian approximation for large means) about the float image, then offset, clipped, and written with the same header conventions.

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

Acceptance Tests (Normative)

- Geometry & Conventions
  - AT-GEO-001 MOSFLM beam-center mapping and 0.5-pixel offsets
    - Setup: detector_convention=MOSFLM; pixel_size=0.1 mm; distance=100.0 mm; beam_center_X=beam_center_Y=51.2 mm; pivot=BEAM; no rotations; twotheta=0.
    - Expectation: Using f=[0,0,1], s=[0,-1,0], o=[1,0,0], Fbeam=Sbeam=(51.2+0.05) mm. The detector origin SHALL be pix0_vector = [0.1, 0.05125, -0.05125] meters (±1e-9 m tolerance).
  - AT-GEO-002 Pivot defaults and overrides
    - Setup A: Provide -distance only (no -close_distance), MOSFLM.
    - Expectation: pivot SHALL be BEAM.
    - Setup B: Provide -close_distance only.
    - Expectation: pivot SHALL be SAMPLE.
    - Setup C: Provide -pivot sample when -distance is also set.
    - Expectation: pivot SHALL be SAMPLE (explicit override wins).
  - AT-GEO-003 r-factor distance update and beam-center preservation
    - Setup: Non-zero detector rotations + twotheta; set close_distance explicitly; compute pre-rotation basis then rotate per spec.
    - Expectation: r = b·o_after_rotations; distance SHALL be updated to distance = close_distance / r and direct-beam Fbeam/Sbeam computed from R = close_distance/r·b − D0 SHALL equal the user’s beam center (within tolerance), for both BEAM and SAMPLE pivots.
  - AT-GEO-004 Two-theta axis defaults by convention
    - Setup: For each convention: MOSFLM→axis=[0,0,-1], XDS→[1,0,0], DIALS→[0,1,0]. Apply a small twotheta.
    - Expectation: The applied rotation axis SHALL match the convention default unless overridden. The reported TWOTHETA value SHALL equal the user-specified value (deg).
  - AT-GEO-005 Curved detector mapping
    - Setup: Enable -curved_det; choose several off-center pixels.
    - Expectation: The curved mapping SHALL yield |pos| equal for all pixels at a given Fdet,Sdet angular offset (spherical arc mapping), and differ from planar mapping in a way consistent with the spec’s small-angle rotations about s and f by Sdet/distance and Fdet/distance respectively.
  - AT-GEO-006 Point-pixel solid angle
    - Setup: Pick an off-center pixel with finite close_distance and R.
    - Expectation: With -point_pixel, Ω SHALL equal 1/R^2. Without it, Ω SHALL equal (pixel_size^2/R^2)·(close_distance/R).

- Sampling, Normalization, Absorption
  - AT-SAM-001 Steps normalization
    - Setup: sources=1; mosaic_domains=1; oversample=1; phisteps=2 with identical physics across steps (e.g., zero mosaic and symmetric phi so F_cell and F_latt identical); disable thickness/polar/omega oversample toggles.
    - Expectation: Final per-pixel scale SHALL divide by steps=2 so intensity matches the single-step case (within numeric tolerance).
  - AT-SAM-002 Oversample_* last-value semantics
    - Setup: oversample=2; construct a pixel where ω or polarization varies across subpixels (e.g., off-center pixel); leave -oversample_omega and -oversample_polar unset; disable absorption.
    - Expectation: Final scale SHALL multiply by the last-computed ω and polarization values (not their averages). Enabling -oversample_omega or -oversample_polar SHALL switch to per-subpixel multiplicative application (no “last-value” behavior).
  - AT-ABS-001 Detector absorption layering
    - Setup: thickness>0; thicksteps>1; finite μ from -detector_abs; choose a pixel with parallax ρ=d·o ≠ 0; disable oversample_thick.
    - Expectation: Per-layer capture fractions SHALL follow exp(−t·Δz·μ/ρ) − exp(−(t+1)·Δz·μ/ρ), summing (t=0..steps−1) to 1−exp(−thickness·μ/ρ). With -oversample_thick unset, the final S SHALL be multiplied by the last layer’s capture fraction; with -oversample_thick set, the running sum SHALL be multiplied by each layer’s capture fraction as terms accumulate.
  - AT-SAM-003 dmin culling
    - Setup: Choose a pixel/source such that stol=0.5·|q| yields dmin < 0.5/stol; set dmin positive.
    - Expectation: The contribution for that subpath SHALL be skipped.

- Structure Factors & Interpolation
  - AT-STR-001 Nearest-neighbor lookup when interpolation off
    - Setup: Load a small HKL grid with known F values; set -nointerpolate; query pixels yielding integer (h0,k0,l0) both in-range and out-of-range.
    - Expectation: In-range uses grid values; out-of-range uses default_F.
  - AT-STR-002 Tricubic interpolation and fallback
    - Setup: Enable -interpolate; choose fractional h,k,l within a grid with complete 4×4×4 neighborhoods.
    - Expectation: F_cell SHALL be tricubically interpolated between neighbors. If a required 4-neighborhood is out of bounds at any evaluation, implementation SHALL print a one-time warning, use default_F for that evaluation, and permanently disable interpolation for the rest of the run.
  - AT-STR-003 Lattice shape models
    - Setup: Compare SQUARE (sincg) vs ROUND (sinc3) vs GAUSS vs TOPHAT using identical crystal sizes and a reflection near a peak.
    - Expectation: Implementations SHALL produce F_latt per the formulas: SQUARE=Π sincg(π·Δ), ROUND=Na·Nb·Nc·0.723601254558268·sinc3(π·sqrt(fudge·hrad^2)), GAUSS and TOPHAT as specified; ROUND scales and cutoff behavior SHALL match the spec.

- Polarization
  - AT-POL-001 Kahn model and toggles
    - Setup: Define incident i, diffracted d, polarization axis p and Kahn factor K in (0,1); compute a pixel with non-zero 2θ and ψ.
    - Expectation: With -polar K, polarization factor per pixel SHALL equal 0.5·(1 + cos^2(2θ) − K·cos(2ψ)·sin^2(2θ)). With -nopolar, factor SHALL be 1. With -oversample_polar unset, the final pixel scale SHALL use the last computed polarization value; with -oversample_polar set, apply per subpixel to the running sum.

- Background & Noise
  - AT-BKG-001 Water background term
    - Setup: -water set to a finite µm; otherwise zero contributions (e.g., default_F=0); compute one pixel.
    - Expectation: Initial accumulator I SHALL equal I_bg = (F_bg^2)·r_e^2·fluence·(water_size^3)·1e6·Avogadro/18 before adding any Bragg terms.
  - AT-NOISE-001 Noise image generation and seeds
    - Setup: Write -noisefile; set -seed; choose pixels with means <12, between 12 and 1e6, and >1e6.
    - Expectation: For <12, use exact Poisson; for large means up to 1e6, use rejection sampling; for >1e6, use Gaussian approximation N(mean, variance=mean). Output reproducibility SHALL follow -seed; additive ADC and clipping SHALL be applied; overload count SHALL be reported.

- File I/O & Headers
  - AT-IO-001 SMV header and data ordering
    - Setup: Write -intfile and -noisefile; big_endian vs little_endian as appropriate.
    - Expectation: Header SHALL include all required keys exactly as listed (HEADER_BYTES, DIM, BYTE_ORDER, TYPE, SIZE1/2, PIXEL_SIZE, DISTANCE, WAVELENGTH, BEAM_CENTER_X/Y, ADXV/MOSFLM/DENZO centers, DIALS_ORIGIN, XDS_ORGX/ORGY, CLOSE_DISTANCE, PHI/OSC_START/OSC_RANGE, TWOTHETA, DETECTOR_SN, BEAMLINE), closed with }\f and padded to 512 bytes; data SHALL be fast-major (row-wise) with pixel index = slow*fpixels + fast.
  - AT-IO-002 PGM writer
    - Setup: Write -pgmfile with and without -pgmscale.
    - Expectation: File SHALL be P5 with width, height, one comment line “# pixels scaled by <pgm_scale>”, 255, followed by width*height bytes with values = floor(min(255, float_pixel * pgm_scale)).
  - AT-IO-003 Fdump caching
    - Setup: Provide -hkl; verify Fdump.bin is written; re-run without -hkl.
    - Expectation: Implementation SHALL read HKLs from Fdump.bin; header and data layout SHALL match spec; behavior when -default_F prefills missing points SHALL be preserved.

- Sources, Divergence & Dispersion
  - AT-SRC-001 Sourcefile and weighting
    - Setup: -sourcefile with two sources having distinct weights and λ; disable other sampling.
    - Expectation: steps = 2; intensity contributions SHALL sum with per-source λ and weight, then divide by steps.
  - AT-SRC-002 Auto-selection of count/range/step
    - Setup: Provide only step (or only range, or only count) for divergence/dispersion; also thickness sampling.
    - Expectation: The missing quantities SHALL resolve to count/range/step per the rules in the spec, with angles default range=1.0 rad and thickness default range=0.5e-6 m when only count is provided.

- Precedence, Header Ingestion, ROI & Mask
  - AT-PRE-001 Header precedence (-img vs -mask)
    - Setup: Provide both -img and -mask; overlapping header keys differ.
    - Expectation: The last file read SHALL win for shared keys; for -mask ingestion, BEAM_CENTER_Y SHALL be interpreted as detsize_s − value_mm.
  - AT-PRE-002 Pivot and origin overrides
    - Setup: Use -Xbeam/-Ybeam vs -Xclose/-Yclose vs -ORGX/-ORGY and -pivot.
    - Expectation: -Xbeam/-Ybeam SHALL force pivot=BEAM; -Xclose/-Yclose and -ORGX/-ORGY SHALL force pivot=SAMPLE; -pivot SHALL override both.
  - AT-ROI-001 ROI and mask behavior
    - Setup: Provide -roi limiting to a sub-rectangle and a -mask with zeros in a subset.
    - Expectation: Pixels outside ROI or with mask value 0 SHALL be skipped in rendering and excluded from statistics.

- Fluence, Flux, Exposure, Beamsize
  - AT-FLU-001 Fluence calculation and sample clipping
    - Setup: Provide -flux, -exposure, -beamsize, and also -fluence; set beamsize smaller than sample_y/z.
    - Expectation: fluence SHALL be recomputed as flux·exposure/beamsize^2 whenever flux != 0 and exposure > 0 and beamsize ≥ 0; exposure > 0 SHALL recompute flux consistently; when beamsize > 0 and smaller than sample_y or sample_z, those sample dimensions SHALL be clipped to beamsize and a warning printed.

- Statistics
  - AT-STA-001 Float-image statistics
    - Setup: Render a small ROI with known pattern; no scaling to int/noise.
    - Expectation: Reported max value and its last-set subpixel coordinates; mean, RMS, and RMSD computed over unmasked ROI pixels as per definitions in the spec.

CLI Binding (Profile: Reference CLI) — Acceptance Tests (Normative)

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

Parallel Validation Tests (Profile: C-PyTorch Equivalence) — Acceptance Tests (Normative)

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
  - Setup: Cubic crystal, apply detector rotations rotx=5°, roty=3°, rotz=2°, twotheta=10°
  - Expectation: Peak shifts SHALL be 10-100 pixels; Relative peak positions preserved ±5%; Total intensity conserved ±10%

- AT-PARALLEL-008 Multi-Peak Pattern Registration
  - Setup: Triclinic cell (70,80,90,75,85,95)°, generate pattern with 20+ visible reflections
  - Expectation: >95% of bright peaks SHALL align ±1 pixel between C and PyTorch; Intensity ratio RMS error <10%; Pattern correlation >0.98

- AT-PARALLEL-009 Intensity Normalization
  - Setup: Vary crystal size N=1,2,3,5,10; structure factor F=50,100,200,500; wavelength=1.0,1.5,2.0,3.0Å
  - Expectation: Intensity SHALL scale as N³ (R²>0.99); Intensity SHALL scale as F² (R²>0.99); C/PyTorch intensity ratio SHALL be constant ±10%
  - Failure mode: 79x intensity difference between implementations

- AT-PARALLEL-010 Solid Angle Corrections
  - Setup: Vary detector distance 50,100,200,400mm; detector tilt 0°,10°,20°,30°
  - Expectation: Intensity SHALL follow 1/r² law ±5%; Tilt corrections SHALL preserve total flux ±10%

- AT-PARALLEL-011 Polarization Factor Verification
  - Setup: Test reflections at different scattering angles, compare polarized vs unpolarized
  - Expectation: Polarization factor SHALL match P=(1+cos²(2θ))/2 ±1%; Angular dependence R²>0.95 vs theory

- AT-PARALLEL-012 Reference Pattern Correlation
  - Setup: Generate patterns with proven C configurations, test cubic, tetragonal, orthorhombic, triclinic cells
  - Expectation: Simple cubic correlation SHALL be >0.999; Complex triclinic correlation SHALL be >0.995; Peak positions SHALL align ±0.5 pixels
  - Failure mode: Correlation 0.048 indicates fundamental geometry error

- AT-PARALLEL-013 Cross-Platform Consistency
  - Setup: Run same calculation on different machines/architectures
  - Expectation: Results SHALL be numerically identical for fixed seeds; Peak positions SHALL not vary; Intensities SHALL match to machine precision

- AT-PARALLEL-014 Noise Robustness Test
  - Setup: Add Poisson noise with different seeds, compare statistics
  - Expectation: Mean intensity SHALL be preserved ±1%; Peak positions SHALL not shift with noise; Noise statistics SHALL match Poisson distribution

- AT-PARALLEL-015 Mixed Unit Input Handling
  - Setup: Test various unit combinations: distance in mm, wavelength in Å, angles in degrees
  - Expectation: Unit conversions SHALL be applied consistently; Results SHALL be independent of input units used; No unit confusion errors

- AT-PARALLEL-016 Extreme Scale Testing
  - Setup: Test nano-crystals (N=1) to large crystals (N=100), wavelengths 0.1-10Å, distances 10mm-10m
  - Expectation: Physics SHALL remain valid at all scales; No numerical overflow/underflow; Graceful handling of extreme parameters

- AT-PARALLEL-017 Grazing Incidence Geometry
  - Setup: Large detector tilts >45°, twotheta>60°, oblique incidence
  - Expectation: Geometry calculations SHALL remain stable; Solid angle corrections SHALL be applied correctly; No singularities in rotation matrices

- AT-PARALLEL-018 Crystal Boundary Conditions
  - Setup: Crystal at singular orientations, aligned axes, zero-angle cases
  - Expectation: No division by zero errors; Degenerate cases SHALL be handled gracefully; Results SHALL be continuous near boundaries

- AT-PARALLEL-019 High-Resolution Data
  - Setup: Small d-spacings <1Å, large detector 4096x4096, fine sampling
  - Expectation: Memory usage SHALL scale linearly; Performance SHALL degrade gracefully; Precision SHALL be maintained for fine features

- AT-PARALLEL-020 Comprehensive Integration Test
  - Setup: Complete simulation with all features: triclinic cell, mosaic spread, phi rotation, detector tilts, absorption, polarization
  - Expectation: Full pipeline SHALL execute without errors; All corrections SHALL be applied consistently; Final correlation between C and PyTorch SHALL be >0.95

Quality Bar Checklist (Informative)

- All major formulas and conversions are explicit and match the implementation.
- CLI options and synonyms reflect exactly what this code parses today.
- Output formats and headers match exactly what is written.
- Sampling structure, normalization, and edge-case behavior (e.g., out-of-range interpolation, last-
value multiplicative factors, clamping Na/Nb/Nc ≥ 1) are fully specified.

Conformance Profiles (Normative)

- Core Engine Profile
  - Covers physics, geometry, sampling, interpolation, background/noise, statistics, and I/O semantics independent of transport. Implementations conforming to this profile SHALL satisfy all normative sections and acceptance tests in this document except those explicitly scoped to the CLI binding.

- Reference CLI Binding Profile
  - Scope: Implementations claiming CLI compatibility SHALL expose a command-line interface that maps flags, defaults, units, precedence, and outputs as defined below. Unknown flags SHOULD produce a clear error with usage guidance. Synonyms listed MUST be supported equivalently.

- C-PyTorch Equivalence Profile
  - Scope: Implementations claiming equivalence with the C reference implementation SHALL pass all AT-PARALLEL-* tests with specified tolerances. This profile ensures that alternative implementations produce outputs functionally equivalent to the original nanoBragg.c.
  - Requirements: Must conform to Core Engine Profile and pass all 20 AT-PARALLEL tests.
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
