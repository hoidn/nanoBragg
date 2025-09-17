Overview (Normative)

- Purpose: Simulate far-field diffraction from a finite 3D crystal lattice onto a planar detector,
including beam divergence and spectral dispersion, mosaic spread, sample rotation, detector
absorption, polarization, and pixel solid-angle/obliquity.
- Scope: Far-field only (no near-field propagation). No symmetry enforcement; structure factors are
taken as-is (P1).
- Constants:
    - Classical electron radius squared r_e^2 = 7.94079248018965e-30 m^2.
    - Avogadro constant N_A = 6.02214179e23 mol^-1.
- Outputs:
    - Float image (raw intensity per pixel; photons/steradian scaled to photons/pixel).
    - Noiseless SMV image (scaled to 16-bit with ADC offset).
    - Optional PGM (8-bit preview).
    - Optional Poisson-noise SMV image (photon counting).

Units & Conversions (Normative)

- General rules:
    - Lengths: Inputs in Å (for cell lengths, wavelength), mm (detector geometry), µm (sensor
thickness), convert internally to meters (m) where used in geometry and physics.
    - Angles: Degrees for CLI/user headers, converted to radians. Divergences in mrad converted
to radians.
    - Spectral dispersion: Percent converted to fraction.
    - Energy: eV to wavelength via λ[Å] = 12398.42 / E[eV]; converted to meters (×1e-10).
    - Pixels: Detector SIZE1 (fast), SIZE2 (slow). Pixel indexing: linear index imgidx = spixel *
fpixels + fpixel, where spixel is slow-axis index and fpixel is fast-axis index.
- Quantities (input → internal):
    - -cell a b c α β γ: a,b,c Å → m by ×1e-10; α,β,γ deg → rad by ×π/180.
    - -mat (MOSFLM A*): reciprocal vectors include 1/λ; corrected by multiplying by (1e-10/λ[m]) to
remove wavelength.
    - -lambda/-wave λ[Å] → λ[m] = λ[Å] × 1e-10.
    - -energy E[eV] → λ[m] = (12398.42/E) × 1e-10.
    - -distance d[mm] → distance[m] = d/1000.
    - -close_distance d[mm] → close_distance[m] = d/1000.
    - -detsize[_f|_s] L[mm] → detsize[m] = L/1000.
    - -pixel p[mm] → pixel_size[m] = p/1000.
    - -detector_thick t[µm] → t[m] = t × 1e-6. -detector_abs u[µm] sets µ = 1/(u×1e-6) or both zero
if “inf”/0.
    - -detector_rotx/y/z, -twotheta: deg → rad.
    - -hdivrange/-vdivrange δ[mrad] → radians = δ/1000. -divergence sets both ranges to same value.
    - -hdivstep/-vdivstep: stepsize in mrad → rad by /1000.
    - -dispersion [%] → fraction by /100. -dispsteps count. Internal step size dispstep auto-derived
(see Sampling).
    - -Xbeam/-Ybeam x[mm] → Xbeam,Ybeam [m] = x/1000.
    - -ORGX/-ORGY: in pixel units (dimensionless).
    - Sample sizes (-xtalsize, -xtal_*, -sample_*): mm → m by /1000.
    - -beamsize [mm] → m by /1000.
    - -water [µm] → m by ×1e-6.

CLI Interface (Normative)

- Crystal and structure factors:
    - -mat file: MOSFLM A* 3×3 in 3 lines; removes wavelength factor.
    - -cell a b c α β γ: Å and degrees; enables user-defined cell.
    - -misset x y z: mis-setting rotations in deg applied to reciprocal vectors; alternatively
-misset random (randomized; see Randomness).
    - -hkl file: text with lines h k l F (real values allowed; non-integers warned).
    - -default_F F0: default structure factor amplitude for unspecified HKL when filling grid from
-hkl.
- Crystal size:
    - -Na N, -Nb N, -Nc N: unit cells along a,b,c. -N N sets all three. Values ≤1 coerced to 1.0
after unit cell determined.
    - -xtalsize L: cubic crystal of edge L (mm) ⇒ sets all sample dimensions. -xtal_x|_y|_z,
-samplesize, -sample_x|_y|_z are synonyms by axis (mm).
- Beam and spectrum:
    - -lambda λ_Å or -wave λ_Å; -energy E_eV.
    - -dispersion frac_percent and -dispsteps N. No direct -dispstep support (see Unsupported).
    - Divergence:
        - -divergence δ_mrad sets horizontal and vertical ranges equal.
        - -hdivrange δ_mrad, -vdivrange δ_mrad; -hdivstep δ_mrad, -vdivstep δ_mrad; -hdivsteps N,
-vdivsteps N, -divsteps N (sets both).
        - -round_div (default) uses elliptical cut; -square_div includes full grid.
- Detector geometry and conventions:
    - Size: -distance d_mm, -detsize L_mm (sets both axes), -detsize_f, -detsize_s, -detpixels N
(sets both), -detpixels_f|_x, -detpixels_s|_y, -pixel p_mm.
    - Absorption: -detector_abs u_um (attenuation length µm; inf or 0 disables absorption),
-detector_thick t_um, -detector_thicksteps N (alias -thicksteps).
    - Beam center and axes:
        - -Xbeam/-Ybeam (mm, MOSFLM-like inputs).
        - -mosflm, -denzo, -adxv, -xds, -dials, -custom set base conventions and pivots (see
Geometry & Conventions).
        - -ORGX/-ORGY (XDS origin; pixels).
        - -twotheta deg, -detector_rotx deg, -detector_roty deg, -detector_rotz deg.
        - Optional manual axes: -fdet_vector x y z, -sdet_vector x y z, -odet_vector x y z,
-beam_vector x y z, -polar_vector x y z, -spindle_axis x y z, -twotheta_axis x y z, -pix0_vector x y
z. Selecting any sets convention to CUSTOM.
        - Pivot override: -pivot sample|beam. Also -distance forces BEAM; -close_distance forces
SAMPLE.
- Sampling & regions:
    - -phi deg, -osc deg, -phistep deg, -phisteps N.
    - -oversample N, -oversample_thick, -oversample_polar, -oversample_omega.
    - -roi xmin xmax ymin ymax (pixel indices inclusive bounds) to restrict rendering region.
    - -dmin Å resolution cutoff (converted to meters).
- Polarization:
    - -polar Kahn_factor to enable polarization correction (default 1.0), or -nopolar to disable (no
polarization correction).
- Intensities and noise:
    - -fluence photons_per_m2 or -flux photons_per_s with -beamsize mm and -exposure s (fluence
computed as flux*exposure/beamsize^2).
    - -water µm of water-equivalent background thickness.
    - -coherent parsed but no effect (incoherent addition is always used).
- I/O:
    - Inputs: -img header.img reads SMV header and seeds detector params; -mask mask.img reads mask:
0-valued pixels are skipped.
    - Outputs:
        - -floatfile file (floatimage.bin default).
        - -intfile file (intimage.img default), -scale s to set integer scaling.
        - -noisefile file (noiseimage.img default), -nonoise disables noise file generation.
        - -pgmfile file (image.pgm default), -pgmscale to set PGM scaling; -nopgm disables.
- Misc:
    - -stol file, -4stol file, -Q file: reads sinθ/λ vs F for amorphous background support (reading
implemented; not used for background intensity in this version).
    - -stolout file: accepted; not written by this version.
    - -printout and -printout_pixel f s: print per-pixel diagnostics; -trace_pixel s f prints deeper
debug for that pixel.
    - -progress (default) or -noprogress progress meter.
    - -seed N (noise), -mosaic_seed N (mosaic orientations), -misset_seed N (misset when
randomized).

Precedence and overrides:

- Header ingestion (-img, -mask): overrides detector pixel dimensions, pixel size, distance,
twotheta, beam center, ORGX/ORGY, and wavelength where provided.
- Convention selection sets base axes and default beam centers depending on pivot; manual axis flags
override and force CUSTOM convention.
- -distance vs -close_distance choose pivot; subsequent orientation applies accordingly.
- If -hkl not provided, attempts to read Fdump.bin; if neither present and -default_F is 0, exits
with error.
- -dispsteps, -hdiv*, -vdiv*, -phisteps, -detector_thicksteps: auto-selected if not or partially
specified (see Sampling).

Unsupported examples (Normative):

- Flags shown in the file’s comment examples but not recognized:
    - -dispstep (unsupported; use -dispsteps to set count; step size auto-derived).
    - -hdiv and -vdiv (unsupported; use -hdivrange and -vdivrange).
- Example -N 0 does not produce a single unit cell; values ≤1 are coerced to 1.

Geometry & Conventions (Normative)

- Basis vectors (initial defaults per convention; all normalized):
    - MOSFLM/DENZO:
        - Beam direction: +X.
        - Detector normal: +X; fast axis: +Z; slow axis: −Y.
        - Twotheta axis: −Z; polarization axis: +Z; spindle axis: +Z.
        - Beam center mapping to fast/slow: Fbeam = Ybeam + 0.5*pixel_size, Sbeam = Xbeam +
0.5*pixel_size.
        - Pivot: BEAM.
    - ADXV:
        - Beam direction: +Z.
        - Detector normal: +Z; fast axis: +X; slow axis: −Y.
        - Twotheta axis: −X; polarization axis: +X; spindle axis: +X.
        - Fbeam = Xbeam, Sbeam = detsize_s - Ybeam. Pivot: BEAM.
    - XDS:
        - Beam direction: +Z.
        - Detector normal: +Z; fast axis: +X; slow axis: +Y.
        - Twotheta axis: +X; polarization axis: +X; spindle axis: +X.
        - Fbeam = Xbeam, Sbeam = Ybeam. Pivot: SAMPLE.
    - DIALS:
        - Beam direction: +Z.
        - Detector normal: +Z; fast axis: +X; slow axis: +Y.
        - Twotheta axis: +Y; polarization axis: +Y; spindle axis: +Y.
        - Fbeam = Xbeam, Sbeam = Ybeam. Pivot: SAMPLE.
    - CUSTOM:
        - Uses provided axes; if origin unknown, uses near-point defaults; pivot unchanged unless
overridden.
- Detector pivot (BEAM vs SAMPLE) and origin:
    - Let f, s, o be unit vectors of fast, slow, normal axes; b beam direction unit vector; Fbeam,
Sbeam desired beam center projection in meters; distance the detector center distance.
    - BEAM pivot: The detector origin vector pix0 (from sample to the origin of its local coordinate
system) is set to:
        - pix0 = -Fbeam * f + -Sbeam * s + distance * b.
    - SAMPLE pivot: First, compute pix0 from near-point (Fclose, Sclose, close_distance):
        - pix0 = -Fclose * f + -Sclose * s + close_distance * o.
        - Then apply detector rotations and twotheta about twotheta_axis.
    - After orientation, compute:
        - Near-point in fast/slow: Fclose = -pix0·f, Sclose = -pix0·s.
        - Orthogonal distance: close_distance = pix0·o.
        - Beam-center coordinates after orientation:
            - Compute the vector from detector origin to beam hit: Δ = (close_distance/ratio) * b
- pix0, where ratio = b · R(o) (R applies preliminary rotations to the normal). Then Fbeam = Δ·f,
Sbeam = Δ·s, and distance = close_distance/ratio.
        - XDS origin (pixels): ORGX = Fclose/pixel_size + 0.5, ORGY = Sclose/pixel_size + 0.5.
        - DIALS origin (mm frame): DIALS_ORIGIN = (1000*pix0·[0,0,1], 1000*pix0·[0,1,0],
1000*pix0·[-1,0,0]).
- Rotation order:
    - Detector axes are first rotated by extrinsic rotations detector_rotx, detector_roty,
detector_rotz (about +X, +Y, +Z of lab frame, in that order), then by twotheta about twotheta_axis.
    - Spindle rotation phi is applied to real-space cell vectors about spindle_axis.
    - Mosaic rotations are applied after spindle rotation via a unitary 3×3 rotation.

Unit Cell & Orientation (Normative)

- From -mat (MOSFLM A* 3×3):
    - Read three rows; remove wavelength by scaling each reciprocal vector by 1e-10/λ[m]; update
magnitudes accordingly.
    - Apply missetting rotation if provided: rotations in radians about X, then Y, then Z to the
reciprocal vectors.
- From -cell:
    - Given a,b,c (Å) and α,β,γ (rad), compute real-space volume:
        - Let aavg=(α+β+γ)/2; skew = sin(aavg)*sin(aavg-α)*sin(aavg-β)*sin(aavg-γ). V_cell = 2 a b c
sqrt(|skew|) (Å^3; coerced to positive).
    - Reciprocal lengths: a* = b c sin(α) / V_cell (Å^-1), similar for b*, c*.
    - Reciprocal angles from direct-space angles and vice versa; trigonometric terms are clamped to
[-1,1] if necessary.
    - Default cartesian reciprocal basis constructed to match the angles; direct-space cell then
computed from crosses: a = (b*×c*) / V*, etc. Convert real-space vectors to meters by ×1e-10. Save
reference orientation (a0,b0,c0).
- Sample size and counts:
    - If -xtal/-sample sizes provided, Na = ceil(sample_x/|a|), etc., coerced to ≥1. Crystal
dimensions in meters: xtalsize_a = |a|*Na, etc.
    - Recommended oversampling: reciprocal_pixel = λ * distance / pixel_size; oversample =
ceil(3*max(xtalsize)/reciprocal_pixel) if not given.
- If neither -mat nor -cell provided and no -img header to seed, error.

Sources, Divergence, Dispersion (Normative)

- -sourcefile format: rows of up to five numbers X Y Z I λ[m]. Missing values default to:
    - Direction (X,Y,Z) = -source_distance * beam_direction, intensity 1, wavelength λ0. Directions
re-normalized; intensities used as weights.
- Otherwise, synthetic sources are generated:
    - Divergence grid:
        - Horizontal angles hdiv = hdivstep * i - hdivrange/2, i ∈ [0,hdivsteps). Similar for
vertical vdiv.
        - If round_div (default), includes only points satisfying an elliptical cut:
            - ((hdiv^2 - (hdivstep^2/4)*(1 - hdivsteps%2))/hdivrange^2 + (vdiv^2 - (vdivstep^2/4)*(1
- vdivsteps%2))/vdivrange^2) * 4 ≤ 1.1.
        - At each (hdiv,vdiv), construct direction by rotating the beam direction: rotate about
polarization axis by vdiv, then about vert = beam×polarization by hdiv, and normalize.
    - Dispersion grid:
        - dispsteps wavelengths: λ = λ0 * (1 + dispstep * j - dispersion/2), j ∈ [0, dispsteps).
Step size dispstep auto-derived (see below).
    - Each (divergence, dispersion) point defines one source with equal weight 1/sources.
- Auto-selection logic:
    - For each of horizontal divergence, vertical divergence, dispersion, phi, and detector
thickness, the code resolves any missing combination of count, range, and stepsize with the
following pattern:
        - If no count specified: set count to 1 and range to 0 unless a step was given; if step
only, set range=step and count=2. If range only, set step=range and count=2. If range and step, set
count=ceil(range/step).
        - If count specified: if range unspecified, choose default range (1.0 for angles; 0.5e-6 for
thickness) and derive step; if step unspecified, derive step as range/(count-1), ensuring at least 2
steps for a range.
    - Dispersion-specific: ranges are in fraction (e.g., 0.01 for 1%). If only dispersion given and
no counts/step, sets step=dispersion and count=2 (endpoints).
- Result: sources = (#divergence points) × dispsteps. Mosaic domains are generated separately (see
Randomness), and steps = sources * mosaic_domains * phisteps * oversample^2.

Sampling & Accumulation (Normative)

- Nested loops (conceptual order for each pixel):
    - Detector thickness layers: thick_tic = 0..(thicksteps-1)
    - Subpixels: subS = 0..(oversample-1), subF = 0..(oversample-1)
    - Sources: all generated source directions and wavelengths
    - Phi steps: phi_tic = 0..(phisteps-1) with phi = phi0 + phi_step*phi_tic
    - Mosaic domains: mos_tic = 0..(mosaic_domains-1) with per-domain rotation
- Normalization:
    - Accumulated amplitude-squared contributions per pixel (including background) are linearly
summed into I across all nested loops.
    - After loops, per-pixel intensity contribution test = r_e^2 * fluence * I / steps. Pixel-level
corrections (capture fraction, polarization factor, solid angle) are applied either per subpixel (if
oversample flags are set) or once after summation (if not).
- Region of Interest:
    - If a pixel lies outside the ROI, it is skipped entirely (including statistics and outputs). If
a mask is provided, mask value 0 also skips the pixel.

Physics & Intensities (Normative)

- Pixel 3D position (meters):
    - Subpixel centers:
        - Fdet = subpixel_size * (fpixel * oversample + subF) + subpixel_size/2
        - Sdet = subpixel_size * (spixel * oversample + subS) + subpixel_size/2
        - Odet = 0 (planar detector; for curved detector, see below).
    - Position vector from sample to subpixel:
        - Planar: pos = Fdet*f + Sdet*s + Odet*o + pix0.
        - Curved (if enabled): Start with pos = distance * beam_direction; rotate pos about s by
angle pos·Y/distance and about f by pos·Z/distance, to maintain constant radial distance.
- Unit vectors and path:
    - Diffracted direction: s_out = unit(pos); path length airpath = |pos|.
    - Incident direction (from source): source direction array stores (−beam_direction) unit
vectors; s_in is the negative of stored source direction vector (normalized).
    - Scattering vector: q = (s_out − s_in) / λ[m] (units m^-1); stol = 0.5 * |q| (sinθ/λ).
- Resolution cutoff:
    - If dmin > 0 and stol > 0 and dmin > 1/(2*stol), skip contribution.
- Pixel solid angle:
    - Ω_pixel = (pixel_size^2 / airpath^2) * (close_distance / airpath). If -point_pixel, use 1/
airpath^2 (omit obliquity).
    - If -oversample_omega, Ω_pixel is applied within the subpixel loops; otherwise applied once per
pixel after loops.
- Detector absorption (per-layer capture fraction):
    - parallax = s_out · o (cosine of incidence relative to detector normal).
    - For layer index n with thickness step Δt, attenuation coefficient µ:
        - Capture fraction for that layer: exp(-n * Δt * µ / parallax) − exp(-(n+1) * Δt * µ /
parallax).
    - If -oversample_thick, multiply intensity within loops; otherwise multiply once per pixel after
loops by the last-calculated capture_fraction.
- Polarization (Kahn model):
    - If enabled (-polar K, default K=1.0), compute:
        - cos(2θ) = s_in · s_out; sin^2(2θ) = 1 − cos^2(2θ).
        - Select polarization plane using axis (from -polar_vector): compute B_in = unit(axis ×
s_in) and E_in = unit(s_in × B_in).
        - Project diffracted onto E/B: E_out = s_out · E_in, B_out = s_out · B_in.
        - Define ψ = −atan2(B_out, E_out).
        - Polarization factor: P = 0.5 * (1 + cos^2(2θ) − K * cos(2ψ) * sin^2(2θ)).
    - If -oversample_polar, multiply by P within loops; otherwise multiply once at end by last-
calculated P.
- Crystal orientation and Miller indices:
    - Apply phi rotation to a0,b0,c0 about spindle axis to obtain ap,bp,cp.
    - Apply mosaic rotation (per domain) to get a,b,c.
    - Compute fractional indices (dimensionless): h = a · q, k = b · q, l = c · q.
    - Nearest integer indices for lookup: h0 = ceil(h−0.5), etc.
- Lattice transform (finite crystal shape factor):
    - SQUARE (parallelpiped):
        - Factor is product of grating responses along each axis (when count > 1): multiply by
sin(Na*π h) / sin(π h) (and similarly for k,l), skipping axes where N≤1.
    - ROUND:
        - Define radius squared in hkl space: ρ^2 = Na^2(h−h0)^2 + Nb^2(k−k0)^2 + Nc^2(l−l0)^2.
        - Factor: Na*Nb*Nc*0.723601254558268 * sinc3(π*sqrt(ρ^2 * fudge)).
        - Here sinc3(x) = 3*(sin x/x − cos x)/x^2 with sinc3(0)=1.
    - GAUSS:
        - Define reciprocal-space squared radius:
            - r*^2 = | (h−h0)*a* + (k−k0)*b* + (l−l0)*c* |^2 * Na^2 Nb^2 Nc^2.
        - Factor: Na*Nb*Nc*exp( −(r*^2 / 0.63 * fudge) ).
    - TOPHAT:
        - Using same r*^2: Factor: Na*Nb*Nc * [ r*^2 * fudge < 0.3969 ] (indicator function).
- Structure factors:
    - Interpolation default: auto-selected based on crystal size:
        - If Na≤2 or Nb≤2 or Nc≤2, enable tricubic interpolation (interpolate=1); otherwise disable
(interpolate=0). CLI -interpolate or -nointerpolate override defaults.
    - Tricubic interpolation:
        - Neighborhood: h0_flr=floor(h), etc.; uses 4 nearest integers [h0_flr−1, h0_flr, h0_flr+1,
h0_flr+2] in each dimension and 3-pass interpolation (cubic Lagrange).
        - If neighborhood would be out-of-grid (relative to min/max HKL bounds), set
F_cell=default_F and permanently disable interpolation for the remainder of the run (fallback to
nearest neighbor).
    - Nearest neighbor:
        - If integer indices are in-bounds, use F(h0,k0,l0); otherwise use default_F (often 0).
- Per-subpixel contribution accumulation:
    - Initialize per-pixel I to background I_bg (see Background).
    - For each nested-loop combination:
        - Compute stol cutoff; then lattice factor F_latt and unit-cell F_cell.
        - Increment: I += F_cell^2 * F_latt^2.
        - If oversampling flags are set, multiply by capture_fraction, polarization, and Ω_pixel
before adding.
    - After loops:
        - test = r_e^2 * fluence * I / steps.
        - If oversampling flags not set, multiply test by capture_fraction, polarization, and
Ω_pixel.
        - Add to float image at this pixel.
- Final scaling to integer image:
    - Determine intfile_scale:
        - If not given and max_I>0, set to 55000 / max_I; otherwise 1.0.
    - For each ROI pixel: val = float_pixel * intfile_scale + adc_offset (default adc_offset =
40.0); clip to [0,65535] and round to nearest integer.

Background & Noise (Normative)

- Water-equivalent uniform background:
    - If water_size > 0, background amplitude F_bg = 2.57 electrons; I_bg = F_bg^2 * r_e^2 * fluence
* water_size^3 * 1e6 * N_A / 18.0. I_bg is added once per pixel before diffraction accumulation.
    - Reading of .stol files (sinθ/λ vs F) is implemented with margin values added at extremes, but
these values are not used to compute background intensity in this version.
- Noise image (Poisson):
    - If -noisefile enabled (default), simulate Poisson counts per pixel:
        - counts = Poisson(mean = float_pixel). Sum counts and track overloads (>65535 after adding
adc_offset).
        - Final stored value per pixel: counts + adc_offset, clipped to [0,65535].
- Seeds:
    - Poisson RNG seed default: negative current time; can be overridden by -seed (negated integer).
    - Mosaic random seed via -mosaic_seed (negated integer).
    - Misset random seed -misset_seed used when -misset random is specified.

Statistics (Normative)

- After full image accumulation over ROI:
    - Mean avg = sum(pixel) / N.
    - RMS rms = sqrt( sum(pixel^2) / (N−1) ).
    - RMSD rmsd = sqrt( sum( (pixel−avg)^2 ) / (N−1) ).
    - Max intensity and its (Fdet,Sdet) position are tracked.
    - Detector solid angle coverage printed as sum(Ω_pixel) / steps.

File I/O (Normative)

- HKL input (-hkl):
    - Text file with lines: h k l F (space separated). First pass counts entries and tracks min/max
h,k,l (non-integers warned). Second pass reads with h,k,l as integers; populates 3D array F(h−hmin,
k−kmin, l−lmin). If -default_F is non-zero, the array is pre-filled with that before setting
provided values.
- Structure-factor cache Fdump.bin:
    - Written if -hkl loaded: header line with 6 integers h_min h_max k_min k_max l_min l_max
followed by a form-feed character. Then raw 64‑bit doubles in nested order: for h0 = 0..h_range, k0
= 0..k_range, a contiguous block of l_range+1 doubles for l0. Read back accordingly.
- SMV outputs (-intfile noiseless and -noisefile noisy):
    - Header format:
        - First line {… keys terminated by }\f; header is padded with spaces to 512 bytes.
        - Keys and units:
            - HEADER_BYTES=512; DIM=2; BYTE_ORDER=big_endian|little_endian; TYPE=unsigned_short;
            - SIZE1=fpixels; SIZE2=spixels; PIXEL_SIZE=mm; DISTANCE=mm;
            - WAVELENGTH=Å;
            - BEAM_CENTER_X=mm; BEAM_CENTER_Y=mm;
            - ADXV_CENTER_X=mm; ADXV_CENTER_Y=mm; (ADXV_CENTER_Y = (detsize_s − Sbeam)×1000)
            - MOSFLM_CENTER_X=mm; MOSFLM_CENTER_Y=mm; (MOSFLM: Sbeam−0.5*pixel_size,
Fbeam−0.5*pixel_size)
            - DENZO_X_BEAM=mm; DENZO_Y_BEAM=mm; (no half-pixel offsets)
            - DIALS_ORIGIN=mm,mm,mm (triple of millimeters along lab Z,Y,−X basis).
            - XDS_ORGX, XDS_ORGY (pixels).
            - CLOSE_DISTANCE=mm;
            - PHI=deg; OSC_START=deg; OSC_RANGE=deg;
            - TWOTHETA=deg;
            - DETECTOR_SN=000; BEAMLINE=fake;
    - Payload: fpixels*spixels unsigned 16‑bit integers written in row-major slow-fast order (slow
major).
- Float image (-floatfile):
    - Raw 32‑bit floats, fpixels*spixels entries, in the same slow-fast order as above. No header.
- PGM (-pgmfile, P5):
    - Header:
        - P5
        - <fpixels> <spixels>
        - # pixels scaled by <pgm_scale>
        - 255
    - Payload: fpixels*spixels 8‑bit unsigned values, scaled by pgm_scale (default chosen as
intfile_scale or 250/(5*rmsd) whichever is smaller), clipped to [0,255].
- Mask/IMG ingestion:
    - Both read as ADSC SMV-like: header keys parsed from the header block starting with {. If
HEADER_BYTES != 512, the header is read entirely and parsed.
    - Keys used if present: SIZE1, SIZE2, PIXEL_SIZE (mm), DISTANCE (mm), CLOSE_DISTANCE (mm),
WAVELENGTH (Å), BEAM_CENTER_X (mm), BEAM_CENTER_Y (mm), ORGX, ORGY, PHI (deg), OSC_RANGE (deg),
TWOTHETA (deg).
    - Pixel array (unsigned short) is read into memory; for -mask, pixels with value 0 are skipped
during simulation.
    - Note: -mask flips Ybeam by Ybeam = detsize_s − (BEAM_CENTER_Y/1000). -img uses Ybeam =
BEAM_CENTER_Y/1000 (no flip).

Randomness (Normative)

- Random number generator:
    - Uniform RNG with a standard linear congruential with shuffle table.
    - -seed sets the seed for Poisson sampling (negated integer).
- Poisson deviate:
    - Drawn for each pixel’s simulated photon count in the noise image from a Poisson distribution
with mean equal to the float image value.
- Mosaic rotations:
    - For mosaic_domains > 0 and mosaic_spread > 0 (radians), each domain’s rotation is sampled
uniformly over a spherical cap of angular radius mosaic_spread using three independent uniform
deviates on [−1,1] mapped to a rotation angle rot = mosaic_spread * (1−r3^2)^(1/3) and a unit axis v
constructed from two deviates on a unit circle. First domain is an identity rotation.
- Misset randomization:
    - If -misset random, a flag is set to randomize misset; this version sets a marker but does
not apply a randomized misset rotation beyond conventional misset rotation unless explicit angles
are provided.

Error Handling & Warnings (Normative)

- Errors:
    - Missing inputs: If neither -hkl nor Fdump.bin exists and -default_F==0.0, or if neither -mat
nor -cell is provided, exit.
    - HKL bounds invalid: if computed ranges are negative, exit.
- Warnings:
    - Non-integer h,k,l values in HKL; impossible reciprocal lengths/volumes; oddball angles (values
outside valid trigonometric domain are clamped).
    - detector_thick > 0 with unset µ: sets µ = 1/detector_thick.
    - Oversampling recommendation when reciprocal pixel size is much smaller than crystal width.
    - Mosaicity auto-selection messages and when mosaic spread is non-zero with only one domain;
defaults coerced to ≥1 domain as described.
    - Divergence grid points outside round-div ellipse are excluded.

Scenarios To Analyze (Informative)

- Example 1:
    - ./nanoBragg -mat auto.mat -hkl P1.hkl -distance 2500
    - Unsupported flags: none.
    - Resolved:
        - distance = 2.5 m.
        - Default: dispersion/divergence off (sources=1), phisteps=1, mosaic_domains=1.
        - Detector convention defaults to MOSFLM; beam center defaults to image center with half-
pixel offsets; axes as in MOSFLM; pivot BEAM.
        - steps = oversample^2 with oversample auto-selected from cell size and geometry.
    - Pixel walkthrough:
        - pos = Fdet f + Sdet s + pix0; s_out = unit(pos); q = (s_out − s_in)/λ.
        - h,k,l from a,b,c dot q; F_latt from SQUARE default grating (unless -round_xtal/others).
        - Interpolate F_cell (tricubic) if auto-enabled; else nearest-neighbor.
        - I += F_cell^2 F_latt^2.
        - After loops: test = r_e^2 * fluence * I / steps * capture_fraction * P * Ω_pixel. Add to
float image. Then scale/offset to SMV integers.
- Example 2:
    - ./nanoBragg -mat A.mat -hkl P1.hkl -lambda 1 -dispersion 0.1 -dispstep 3 -distance 100
-detsize 100 -pixel 0.1 -hdiv 0.28 -hdivstep 0.02 -vdiv 0.28 -vdivstep 0.02 -fluence 1e24 -N 0
-water 0
    - Unsupported flags: -dispstep (use -dispsteps), -hdiv (use -hdivrange), -vdiv (use -vdivrange).
    - Resolved behavior with supported subset:
        - λ=1 Å → 1e-10 m; dispersion=0.001 (10%?), note: 0.1% vs 10% depends on intent; CLI
-dispersion 0.1 = 0.1%? Code interprets percent: 0.1% means 0.001. File comments show “percent”; 0.1
→ 0.001.
        - Without -dispsteps, auto picks dispsteps=2 at endpoints.
        - Without -hdivrange/-vdivrange, divergence remains off (hdivsteps=vdivsteps=1).
        - distance=0.1 m; detsize=100 mm → 0.1×0.1 m; pixel=0.0001 m; Na=Nb=Nc from -N 0 are coerced
to 1 (not 0 as the comment suggests). water=0 disables background.
- Example 3:
    - ./nanoBragg -cell 74 74 36 90 90 90 -misset 10 20 30 -hkl P1.hkl -lambda 1 -dispersion 0.1
-dispstep 3 -distance 100 -detsize 100 -pixel 0.1 -hdiv 0.28 -hdivstep 0.02 -vdiv 0.28 -vdivstep
0.02 -fluence 1e24 -N 0 -water 0
    - Unsupported flags as in Example 2.
    - Resolved differences:
        - User cell used; real/reciprocal vectors computed; misset rotations applied (X then Y then
Z about lab axes).
        - All else as above; divergence off if not given as ranges; dispersion endpoints with
dispsteps=2.

Glossary (Informative)

- beam_direction b: unit vector of incident beam in lab frame.
- f,s,o: unit vectors of detector fast, slow, and normal axes in lab frame.
- pix0: detector origin vector from sample, after rotations/pivot; defines the coordinate frame
origin for pixel mapping.
- Fdet,Sdet: subpixel offsets along fast/slow axes (m).
- pos: position vector of a subpixel in lab frame (m).
- s_in, s_out: unit incident and diffracted beam vectors.
- q: scattering vector (m^-1).
- a,b,c: real-space cell vectors (m). a*,b*,c*: reciprocal-space vectors (Å^-1).
- h,k,l: fractional Miller indices (dimensionless). h0,k0,l0: nearest integers.
- F_cell: structure factor amplitude for unit cell at (h,k,l).
- F_latt: lattice shape factor (dimensionless).
- P: polarization factor (dimensionless).
- Ω_pixel: pixel solid angle/obliquity factor (sr → dimensionless factor).
- µ: detector attenuation coefficient (m^-1). parallax: cosine of diffracted ray component along
detector normal.
- I_bg: uniform background intensity contribution (photons per steradian-equivalent before pixel
corrections).

Scope & Non‑Goals (Informative)

- Far-field model only; no Fresnel/near-field propagation.
- No point-spread or MTF modeling beyond pixel obliquity factor.
- No space-group symmetry enforcement or Friedel symmetry; HKL treated as P1.
- No detector readout nonlinearity modeling beyond ADC offset and clipping.

Acceptance Criteria (Normative)

- All units and conversions are explicitly identified; Å↔m, mm↔m, µm↔m, deg↔rad, mrad↔rad,
percent↔fraction, eV→Å→m.
- Every CLI option parsed in this version is documented with units, defaults, and behavior;
unsupported flags in examples are identified.
- Geometry equations and mappings are included: pixel→3D mapping, incident/diffracted vectors, q,
stol, solid-angle, parallax absorption, polarization.
- Lattice factor and interpolation equations and neighborhoods are specified; fallback and disabling
behavior when out-of-range occurs is captured.
- Fluence/flux/exposure/beamsize relation is documented along with sample clipping.
- File formats are precisely specified (headers, payloads, padding, ordering, numeric types).
- Sampling structure and normalization by steps is explicitly defined.
- Randomness, seeds, and distributions used are documented.

Quality Bar Checklist (Informative)

- Units table and conversions complete and consistent.
- All implemented CLI options covered; mismatches against examples flagged.
- Major formulas captured with exact ASCII math.
- File formats (HKL, Fdump, SMV, float, PGM) fully described.
- Sampling loops, oversampling flags, and normalization clearly specified.

Notes on Minor Behaviors (Informative)

- -coherent is parsed but has no effect in this version; intensities are combined incoherently.
- .stol reading is implemented but not used for pixel background in this version; -water uses a
fixed F_bg model instead.
- If interpolation encounters an out-of-range neighborhood once, interpolation is disabled for the
remainder of the run (nearest-neighbor then used thereafter).

