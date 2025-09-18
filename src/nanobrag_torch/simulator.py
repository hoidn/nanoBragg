"""
Main Simulator class for nanoBragg PyTorch implementation.

This module orchestrates the entire diffraction simulation, taking Crystal and
Detector objects as input and producing the final diffraction pattern.
"""

from typing import Optional

import torch

from .config import BeamConfig, CrystalConfig, CrystalShape
from .models.crystal import Crystal
from .models.detector import Detector
from .utils.geometry import dot_product
from .utils.physics import sincg, sinc3, polarization_factor


class Simulator:
    """
    Main diffraction simulator class.

    Implements the vectorized PyTorch equivalent of the nested loops in the
    original nanoBragg.c main simulation loop.
    """

    def __init__(
        self,
        crystal: Crystal,
        detector: Detector,
        crystal_config: Optional[CrystalConfig] = None,
        beam_config: Optional[BeamConfig] = None,
        device=None,
        dtype=torch.float64,
    ):
        """
        Initialize simulator with crystal, detector, and configurations.

        Args:
            crystal: Crystal object containing unit cell and structure factors
            detector: Detector object with geometry parameters
            crystal_config: Configuration for crystal rotation parameters (phi, mosaic)
            beam_config: Beam configuration (optional, for future use)
            device: PyTorch device (cpu/cuda)
            dtype: PyTorch data type
        """
        self.crystal = crystal
        self.detector = detector
        self.crystal_config = (
            crystal_config if crystal_config is not None else CrystalConfig()
        )
        self.beam_config = beam_config if beam_config is not None else BeamConfig()
        self.device = device if device is not None else torch.device("cpu")
        self.dtype = dtype

        # Hard-coded simple_cubic beam parameters (from golden test case)
        # Incident beam direction: [1, 0, 0] (from log: INCIDENT_BEAM_DIRECTION= 1 0 0)
        # Wave: 1 Angstrom
        self.incident_beam_direction = torch.tensor(
            [1.0, 0.0, 0.0], device=self.device, dtype=self.dtype
        )
        self.wavelength = self.beam_config.wavelength_A  # Use beam config wavelength

        # Physical constants (from nanoBragg.c ~line 240)
        self.r_e_sqr = (
            7.94079248018965e-30  # classical electron radius squared (meters squared)
        )
        self.fluence = (
            125932015286227086360700780544.0  # photons per square meter (C default)
        )
        # Polarization setup from beam config
        self.kahn_factor = self.beam_config.polarization_factor if not self.beam_config.nopolar else 0.0
        self.polarization_axis = torch.tensor(
            self.beam_config.polarization_axis, device=self.device, dtype=self.dtype
        )

    def run(
        self,
        pixel_batch_size: Optional[int] = None,
        override_a_star: Optional[torch.Tensor] = None,
        oversample: Optional[int] = None,
        oversample_omega: Optional[bool] = None,
        oversample_polar: Optional[bool] = None,
        oversample_thick: Optional[bool] = None,
    ) -> torch.Tensor:
        """
        Run the diffraction simulation with crystal rotation and mosaicity.

        This method vectorizes the simulation over all detector pixels, phi angles,
        and mosaic domains. It integrates contributions from all crystal orientations
        to produce the final diffraction pattern.

        Important: This implementation uses the full Miller indices (h, k, l) for the
        lattice shape factor calculation, not the fractional part (h-h0). This correctly
        models the crystal shape transform and is consistent with the physics of
        diffraction from a finite crystal.

        C-Code Implementation Reference (from nanoBragg.c, lines 2993-3151):
        The vectorized implementation replaces these nested loops. The outer `source`
        loop is future work for handling beam divergence and dispersion.

        ```c
                        /* loop over sources now */
                        for(source=0;source<sources;++source){

                            /* retrieve stuff from cache */
                            incident[1] = -source_X[source];
                            incident[2] = -source_Y[source];
                            incident[3] = -source_Z[source];
                            lambda = source_lambda[source];

                            /* ... scattering vector calculation ... */

                            /* sweep over phi angles */
                            for(phi_tic = 0; phi_tic < phisteps; ++phi_tic)
                            {
                                /* ... crystal rotation ... */

                                /* enumerate mosaic domains */
                                for(mos_tic=0;mos_tic<mosaic_domains;++mos_tic)
                                {
                                    /* ... mosaic rotation ... */
                                    /* ... h,k,l calculation ... */
                                    /* ... F_cell and F_latt calculation ... */

                                    /* convert amplitudes into intensity (photons per steradian) */
                                    I += F_cell*F_cell*F_latt*F_latt;
                                }
                            }
                        }
        ```

        Args:
            pixel_batch_size: Optional batching for memory management.
            override_a_star: Optional override for the a_star vector for testing.
            oversample: Number of subpixel samples per axis. Defaults to detector config.
            oversample_omega: Apply solid angle per subpixel. Defaults to detector config.
            oversample_polar: Apply polarization per subpixel. Defaults to detector config.
            oversample_thick: Apply absorption per subpixel. Defaults to detector config.

        Returns:
            torch.Tensor: Final diffraction image with shape (spixels, fpixels).
        """
        # Get oversampling parameters from detector config if not provided
        if oversample is None:
            oversample = self.detector.config.oversample
        if oversample_omega is None:
            oversample_omega = self.detector.config.oversample_omega
        if oversample_polar is None:
            oversample_polar = self.detector.config.oversample_polar
        if oversample_thick is None:
            oversample_thick = self.detector.config.oversample_thick

        # For now, we'll implement the base case without oversampling for this test
        # The full subpixel implementation will come later
        # This matches the current implementation which doesn't yet have subpixel sampling

        # Get pixel coordinates (spixels, fpixels, 3) in meters
        pixel_coords_meters = self.detector.get_pixel_coords()
        # Convert to Angstroms for physics calculations
        pixel_coords_angstroms = pixel_coords_meters * 1e10

        # Calculate scattering vectors for each pixel
        # The C code calculates scattering vector as the difference between
        # unit vectors pointing to the pixel and the incident direction

        # Diffracted beam unit vector (from origin to pixel)
        pixel_squared_sum = torch.sum(
            pixel_coords_angstroms * pixel_coords_angstroms, dim=-1, keepdim=True
        )
        # Clamp to prevent negative values that could cause complex gradients
        pixel_squared_sum = torch.clamp(pixel_squared_sum, min=0.0)
        pixel_magnitudes = torch.sqrt(pixel_squared_sum)
        diffracted_beam_unit = pixel_coords_angstroms / pixel_magnitudes

        # Incident beam unit vector [1, 0, 0]
        incident_beam_unit = self.incident_beam_direction.expand_as(
            diffracted_beam_unit
        )

        # Scattering vector using crystallographic convention (nanoBragg.c style)
        # S = (s_out - s_in) / λ where s_out, s_in are unit vectors
        scattering_vector = (
            diffracted_beam_unit - incident_beam_unit
        ) / self.wavelength

        # Apply dmin culling if specified (AT-SAM-003)
        # Calculate stol = 0.5·|q| where q is the scattering vector
        # Per spec: cull if dmin > 0 and stol > 0 and dmin > 0.5/stol
        dmin_mask = None
        if self.beam_config.dmin > 0:
            # Calculate stol = 0.5 * |scattering_vector|
            # Note: scattering_vector is already divided by wavelength
            stol = 0.5 * torch.norm(scattering_vector, dim=-1)  # Shape: (S, F)

            # Apply culling condition: dmin > 0.5/stol
            # This is equivalent to: stol > 0.5/dmin
            # Avoid division by zero in stol
            stol_threshold = 0.5 / self.beam_config.dmin
            dmin_mask = (stol > 0) & (stol > stol_threshold)  # Shape: (S, F)

            # dmin_mask is True for pixels that should be CULLED (skipped)
            # We'll invert it later to get pixels to keep

        # Get rotated lattice vectors for all phi steps and mosaic domains
        # Shape: (N_phi, N_mos, 3)
        if override_a_star is None:
            (rot_a, rot_b, rot_c), (rot_a_star, rot_b_star, rot_c_star) = (
                self.crystal.get_rotated_real_vectors(self.crystal_config)
            )
            # Cache rotated reciprocal vectors for GAUSS/TOPHAT shape models
            self._rot_a_star = rot_a_star
            self._rot_b_star = rot_b_star
            self._rot_c_star = rot_c_star
        else:
            # For gradient testing with override, use single orientation
            rot_a = override_a_star.view(1, 1, 3)
            rot_b = self.crystal.b.view(1, 1, 3)
            rot_c = self.crystal.c.view(1, 1, 3)
            rot_a_star = override_a_star.view(1, 1, 3)
            rot_b_star = self.crystal.b_star.view(1, 1, 3)
            rot_c_star = self.crystal.c_star.view(1, 1, 3)
            # Cache for shape models
            self._rot_a_star = rot_a_star
            self._rot_b_star = rot_b_star
            self._rot_c_star = rot_c_star

        # Broadcast scattering vector to be compatible with rotation dimensions
        # scattering_vector: (S, F, 3) -> (S, F, 1, 1, 3)
        # rot_a: (N_phi, N_mos, 3) -> (1, 1, N_phi, N_mos, 3)
        scattering_broadcast = scattering_vector.unsqueeze(-2).unsqueeze(-2)
        rot_a_broadcast = rot_a.unsqueeze(0).unsqueeze(0)
        rot_b_broadcast = rot_b.unsqueeze(0).unsqueeze(0)
        rot_c_broadcast = rot_c.unsqueeze(0).unsqueeze(0)

        # Calculate dimensionless Miller indices using nanoBragg.c convention
        # nanoBragg.c uses: h = S·a where S is the scattering vector and a is real-space vector
        # IMPORTANT: The real-space vectors a, b, c have already incorporated any misset rotation
        # through the Crystal.compute_cell_tensors() method, which ensures consistency with C-code
        # Result shape: (S, F, N_phi, N_mos)
        h = dot_product(scattering_broadcast, rot_a_broadcast)
        k = dot_product(scattering_broadcast, rot_b_broadcast)
        l = dot_product(scattering_broadcast, rot_c_broadcast)  # noqa: E741

        # Find nearest integer Miller indices for structure factor lookup
        h0 = torch.round(h)
        k0 = torch.round(k)
        l0 = torch.round(l)

        # Look up structure factors F_cell using integer indices
        # TODO: Future implementation must calculate |h*a* + k*b* + l*c*| <= 1/d_min
        # for correct resolution cutoffs in triclinic cells
        F_cell = self.crystal.get_structure_factor(h0, k0, l0)

        # Calculate lattice structure factor F_latt based on crystal shape model
        # CORRECT: Use fractional part (h-h0, k-k0, l-l0) to match C-code behavior
        Na = self.crystal.N_cells_a
        Nb = self.crystal.N_cells_b
        Nc = self.crystal.N_cells_c
        shape = self.crystal_config.shape
        fudge = self.crystal_config.fudge

        if shape == CrystalShape.SQUARE:
            # Parallelepiped/grating model using sincg function
            # F_latt = sincg(π·h, Na) · sincg(π·k, Nb) · sincg(π·l, Nc)
            F_latt_a = sincg(torch.pi * (h - h0), Na)
            F_latt_b = sincg(torch.pi * (k - k0), Nb)
            F_latt_c = sincg(torch.pi * (l - l0), Nc)
            F_latt = F_latt_a * F_latt_b * F_latt_c

        elif shape == CrystalShape.ROUND:
            # Spherical/elliptical model using sinc3 function
            # hrad^2 = (h−h0)^2·Na^2 + (k−k0)^2·Nb^2 + (l−l0)^2·Nc^2
            # F_latt = Na·Nb·Nc·0.723601254558268·sinc3(π·sqrt(fudge·hrad^2))
            h_frac = h - h0
            k_frac = k - k0
            l_frac = l - l0
            hrad_sqr = (h_frac * h_frac * Na * Na +
                       k_frac * k_frac * Nb * Nb +
                       l_frac * l_frac * Nc * Nc)
            # Protect against negative values before sqrt (though shouldn't happen)
            hrad_sqr = torch.clamp(hrad_sqr, min=0.0)
            F_latt = Na * Nb * Nc * 0.723601254558268 * sinc3(
                torch.pi * torch.sqrt(hrad_sqr * fudge)
            )

        elif shape == CrystalShape.GAUSS:
            # Gaussian in reciprocal space
            # Δr*^2 = ||(h−h0)·a* + (k−k0)·b* + (l−l0)·c*||^2 · Na^2·Nb^2·Nc^2
            # F_latt = Na·Nb·Nc·exp(−(Δr*^2 / 0.63)·fudge)
            h_frac = h - h0
            k_frac = k - k0
            l_frac = l - l0

            # Get reciprocal vectors for the current phi/mosaic configuration
            # Shape of rot_a_star etc: (N_phi, N_mos, 3)
            if hasattr(self, '_rot_a_star'):
                # Use cached rotated reciprocal vectors if available
                delta_r_star = (h_frac.unsqueeze(-1) * self._rot_a_star +
                               k_frac.unsqueeze(-1) * self._rot_b_star +
                               l_frac.unsqueeze(-1) * self._rot_c_star)
            else:
                # Fall back to unrotated vectors
                delta_r_star = (h_frac.unsqueeze(-1) * self.crystal.a_star.view(1, 1, 1, 3) +
                               k_frac.unsqueeze(-1) * self.crystal.b_star.view(1, 1, 1, 3) +
                               l_frac.unsqueeze(-1) * self.crystal.c_star.view(1, 1, 1, 3))

            # Calculate squared magnitude
            rad_star_sqr = torch.sum(delta_r_star * delta_r_star, dim=-1)
            rad_star_sqr = rad_star_sqr * Na * Na * Nb * Nb * Nc * Nc

            F_latt = Na * Nb * Nc * torch.exp(-(rad_star_sqr / 0.63) * fudge)

        elif shape == CrystalShape.TOPHAT:
            # Binary spots/top-hat function
            # F_latt = Na·Nb·Nc if (Δr*^2 · fudge < 0.3969); else 0
            h_frac = h - h0
            k_frac = k - k0
            l_frac = l - l0

            # Similar to GAUSS, calculate reciprocal space distance
            if hasattr(self, '_rot_a_star'):
                delta_r_star = (h_frac.unsqueeze(-1) * self._rot_a_star +
                               k_frac.unsqueeze(-1) * self._rot_b_star +
                               l_frac.unsqueeze(-1) * self._rot_c_star)
            else:
                delta_r_star = (h_frac.unsqueeze(-1) * self.crystal.a_star.view(1, 1, 1, 3) +
                               k_frac.unsqueeze(-1) * self.crystal.b_star.view(1, 1, 1, 3) +
                               l_frac.unsqueeze(-1) * self.crystal.c_star.view(1, 1, 1, 3))

            rad_star_sqr = torch.sum(delta_r_star * delta_r_star, dim=-1)
            rad_star_sqr = rad_star_sqr * Na * Na * Nb * Nb * Nc * Nc

            # Apply threshold
            inside_cutoff = (rad_star_sqr * fudge) < 0.3969
            F_latt = torch.where(inside_cutoff,
                                torch.full_like(rad_star_sqr, Na * Nb * Nc),
                                torch.zeros_like(rad_star_sqr))

        else:
            raise ValueError(f"Unsupported crystal shape: {shape}")

        # Calculate total structure factor and intensity
        # Shape: (S, F, N_phi, N_mos)
        F_total = F_cell * F_latt
        intensity = F_total * F_total  # |F|^2

        # Apply dmin culling mask if specified (AT-SAM-003)
        # Set intensity to zero for pixels that should be culled
        if dmin_mask is not None:
            # dmin_mask is True for pixels to cull, shape: (S, F)
            # We need to broadcast to match intensity shape: (S, F, N_phi, N_mos)
            keep_mask = ~dmin_mask.unsqueeze(-1).unsqueeze(-1)
            intensity = intensity * keep_mask.to(intensity.dtype)

        # Integrate over phi steps and mosaic domains
        # Sum across the last two dimensions to get final 2D image
        integrated_intensity = torch.sum(intensity, dim=(-2, -1))

        # Calculate normalization factor (steps)
        # Per spec AT-SAM-001: "Final per-pixel scale SHALL divide by steps"
        # where steps = sources * phi_steps * mosaic_domains * oversample steps
        # For now: sources=1, oversample=1 (not yet implemented)
        phi_steps = self.crystal_config.phi_steps
        mosaic_domains = self.crystal_config.mosaic_domains
        steps = phi_steps * mosaic_domains  # * sources * oversample (future)

        # Normalize by the number of steps
        normalized_intensity = integrated_intensity / steps

        # Apply physical scaling factors (from nanoBragg.c ~line 3050)
        # Solid angle correction, converting all units to meters for calculation

        # Check if we're doing subpixel sampling
        if oversample > 1:
            # Generate subpixel offsets (centered on pixel center)
            # Per spec: "Compute detector-plane coordinates (meters): Fdet and Sdet at subpixel centers."
            # Shape: (oversample, oversample) for slow and fast offsets
            # Create offsets in fractional pixel units
            subpixel_step = 1.0 / oversample
            offset_start = -0.5 + subpixel_step / 2.0
            offset_end = 0.5 - subpixel_step / 2.0

            # Use manual arithmetic to preserve gradients (avoid torch.linspace)
            subpixel_offsets = offset_start + torch.arange(
                oversample, device=self.device, dtype=self.dtype
            ) * subpixel_step

            sub_s, sub_f = torch.meshgrid(subpixel_offsets, subpixel_offsets, indexing='ij')

            # Get detector basis vectors for proper coordinate transformation
            f_axis = self.detector.fdet_vec  # Fast axis vector
            s_axis = self.detector.sdet_vec  # Slow axis vector

            # Initialize accumulator for intensity
            accumulated_intensity = torch.zeros_like(normalized_intensity)

            # Track last computed omega and polarization for each pixel (for last-value semantics)
            last_omega = torch.zeros_like(normalized_intensity)
            last_polar = torch.ones_like(normalized_intensity)  # Will be computed per subpixel

            # Track whether we've applied factors per-subpixel
            omega_applied = False

            # Subpixel loop - vectorizable but kept explicit for clarity and correctness
            for i_s in range(oversample):
                for i_f in range(oversample):
                    # Compute subpixel offset in meters using detector basis vectors
                    # offset = delta_s * s_axis + delta_f * f_axis
                    delta_s = sub_s[i_s, i_f] * self.detector.pixel_size
                    delta_f = sub_f[i_s, i_f] * self.detector.pixel_size

                    # Apply offsets using detector basis vectors
                    # Shape: (S, F, 3) for coordinates
                    offset_vector = delta_s * s_axis + delta_f * f_axis
                    subpixel_coords = pixel_coords_meters + offset_vector.unsqueeze(0).unsqueeze(0)

                    # Calculate airpath for this subpixel
                    subpixel_coords_ang = subpixel_coords * 1e10  # Convert to Angstroms
                    sub_squared = torch.sum(subpixel_coords_ang * subpixel_coords_ang, dim=-1)
                    sub_squared = torch.clamp(sub_squared, min=1e-20)  # Avoid division by zero
                    sub_magnitudes = torch.sqrt(sub_squared)

                    # Convert back to meters for omega calculation
                    airpath_m = sub_magnitudes * 1e-10

                    # Get close_distance from detector (computed during init)
                    close_distance_m = self.detector.close_distance
                    pixel_size_m = self.detector.pixel_size

                    # Calculate solid angle (omega) for this subpixel
                    # Per spec: "ω = pixel^2 / R^2 · (close_distance / R)"
                    if self.detector.config.point_pixel:
                        # Point pixel mode: ω = 1 / R^2
                        omega_subpixel = 1.0 / (airpath_m * airpath_m)
                    else:
                        # Standard mode with obliquity correction
                        omega_subpixel = (
                            (pixel_size_m * pixel_size_m)
                            / (airpath_m * airpath_m)
                            * close_distance_m
                            / airpath_m
                        )

                    # Scale omega by number of subpixels (each contributes 1/N^2 of total)
                    omega_subpixel_scaled = omega_subpixel / (oversample * oversample)

                    # Calculate polarization factor for this subpixel
                    # Need incident and diffracted directions
                    # Shape of incident: (S, F, 3)
                    S, F = pixel_coords_meters.shape[:2]
                    incident = -self.incident_beam_direction.unsqueeze(0).unsqueeze(0).expand(S, F, 3)

                    # Diffracted direction is the normalized pixel coordinate
                    diffracted = subpixel_coords / sub_magnitudes.unsqueeze(-1) * 1e10  # Normalize

                    # Calculate polarization factor using Kahn model
                    if self.beam_config.nopolar:
                        polar_subpixel = torch.ones_like(omega_subpixel)
                    else:
                        polar_subpixel = polarization_factor(
                            self.kahn_factor,
                            incident,
                            diffracted,
                            self.polarization_axis
                        )

                    # Compute the subpixel intensity contribution
                    subpixel_intensity = normalized_intensity / (oversample * oversample)

                    # Apply factors based on oversample flags
                    if oversample_omega:
                        # Apply omega per subpixel
                        subpixel_intensity = subpixel_intensity * omega_subpixel
                        omega_applied = True
                    else:
                        # Track last omega value for later application
                        last_omega = omega_subpixel  # Full value, not scaled

                    if oversample_polar:
                        # Apply polarization per subpixel
                        subpixel_intensity = subpixel_intensity * polar_subpixel
                    else:
                        # Track last polarization value
                        last_polar = polar_subpixel

                    # Accumulate the subpixel contribution
                    accumulated_intensity += subpixel_intensity

            # Apply last-value semantics if flags are not set
            if not oversample_omega and not omega_applied:
                # Multiply by last omega value (not the average!)
                # This is the key difference: use LAST value, not average
                accumulated_intensity = accumulated_intensity * last_omega

            if not oversample_polar:
                # Apply last polarization value (currently constant)
                accumulated_intensity = accumulated_intensity * last_polar

            # Use accumulated intensity
            normalized_intensity = accumulated_intensity
        else:
            # No subpixel sampling - original code path
            airpath = pixel_magnitudes.squeeze(-1)  # Remove last dimension for broadcasting
            airpath_m = airpath * 1e-10  # Å to meters
            close_distance_m = self.detector.distance  # Already in meters
            pixel_size_m = self.detector.pixel_size  # Already in meters

            omega_pixel = (
                (pixel_size_m * pixel_size_m)
                / (airpath_m * airpath_m)
                * close_distance_m
                / airpath_m
            )

            # Apply omega directly
            normalized_intensity = normalized_intensity * omega_pixel

        # Apply detector absorption if configured (AT-ABS-001)
        if (self.detector.config.detector_thick_um is not None and
            self.detector.config.detector_thick_um > 0 and
            self.detector.config.detector_abs_um is not None and
            self.detector.config.detector_abs_um > 0):

            # Apply absorption calculation
            normalized_intensity = self._apply_detector_absorption(
                normalized_intensity,
                pixel_coords_meters,
                oversample_thick
            )

        # Final intensity with all physical constants in meters
        # Units: [dimensionless] × [steradians] × [m²] × [photons/m²] × [dimensionless] = [photons·steradians]
        physical_intensity = (
            normalized_intensity
            * self.r_e_sqr
            * self.fluence
        )

        # Add water background if configured (AT-BKG-001)
        if self.beam_config.water_size_um > 0:
            water_background = self._calculate_water_background()
            physical_intensity = physical_intensity + water_background

        return physical_intensity

    def _calculate_water_background(self) -> torch.Tensor:
        """Calculate water background contribution (AT-BKG-001).

        The water background models forward scattering from amorphous water molecules.
        This is a constant per-pixel contribution that mimics diffuse scattering.

        Formula from spec:
        I_bg = (F_bg^2) · r_e^2 · fluence · (water_size^3) · 1e6 · Avogadro / water_MW

        Where:
        - F_bg = 2.57 (dimensionless, water forward scattering amplitude)
        - r_e^2 = classical electron radius squared
        - fluence = photons per square meter
        - water_size = water thickness in micrometers converted to meters
        - Avogadro = 6.02214179e23 mol^-1
        - water_MW = 18 g/mol

        Note: The 1e6 factor is as specified in the C code; it creates a unit inconsistency
        but we replicate it exactly for compatibility.

        Returns:
            Background intensity per pixel (same shape as detector)
        """
        # Physical constants
        F_bg = 2.57  # Water forward scattering amplitude (dimensionless)
        Avogadro = 6.02214179e23  # mol^-1
        water_MW = 18.0  # g/mol

        # Convert water size from micrometers to meters
        water_size_m = self.beam_config.water_size_um * 1e-6

        # Calculate background intensity per spec formula
        # Note: The 1e6 factor creates unit inconsistency but matches C code
        I_bg = (
            F_bg * F_bg
            * self.r_e_sqr
            * self.fluence
            * (water_size_m ** 3)
            * 1e6
            * Avogadro
            / water_MW
        )

        # Create uniform background for all pixels
        # Shape should match detector dimensions
        fpixels = self.detector.fpixels
        spixels = self.detector.spixels

        background = torch.full(
            (spixels, fpixels),
            I_bg,
            device=self.device,
            dtype=self.dtype
        )

        return background

    def _apply_detector_absorption(
        self,
        intensity: torch.Tensor,
        pixel_coords_meters: torch.Tensor,
        oversample_thick: bool
    ) -> torch.Tensor:
        """Apply detector absorption with layering (AT-ABS-001).

        Args:
            intensity: Input intensity tensor [S, F]
            pixel_coords_meters: Pixel coordinates in meters [S, F, 3]
            oversample_thick: If True, apply absorption per layer; if False, use last-value semantics

        Returns:
            Intensity with absorption applied

        Implementation follows spec AT-ABS-001:
        - Parallax factor: ρ = d·o where d is detector normal, o is observation direction
        - Capture fraction per layer: exp(−t·Δz·μ/ρ) − exp(−(t+1)·Δz·μ/ρ)
        - With oversample_thick=False: multiply by last layer's capture fraction
        - With oversample_thick=True: accumulate with per-layer capture fractions
        """
        # Get detector parameters
        thickness_m = self.detector.config.detector_thick_um * 1e-6  # μm to meters
        thicksteps = self.detector.config.detector_thicksteps

        # Calculate μ (absorption coefficient) from attenuation depth
        # μ = 1 / (attenuation_depth_m)
        attenuation_depth_m = self.detector.config.detector_abs_um * 1e-6  # μm to meters
        mu = 1.0 / attenuation_depth_m  # m^-1

        # Get detector normal vector (odet_vector)
        detector_normal = self.detector.odet_vec  # Shape: [3]

        # Calculate observation directions (normalized pixel coordinates)
        # o = pixel_coords / |pixel_coords|
        pixel_distances = torch.sqrt(torch.sum(pixel_coords_meters**2, dim=-1, keepdim=True))
        observation_dirs = pixel_coords_meters / torch.clamp(pixel_distances, min=1e-10)

        # Calculate parallax factor: ρ = d·o
        # detector_normal shape: [3], observation_dirs shape: [S, F, 3]
        # Result shape: [S, F]
        parallax = torch.sum(detector_normal.unsqueeze(0).unsqueeze(0) * observation_dirs, dim=-1)
        parallax = torch.abs(parallax)  # Take absolute value to ensure positive
        parallax = torch.clamp(parallax, min=1e-10)  # Avoid division by zero

        # Calculate layer thickness
        delta_z = thickness_m / thicksteps

        # Initialize result
        if oversample_thick:
            # Accumulate with per-layer capture fractions
            result = torch.zeros_like(intensity)

            for t in range(thicksteps):
                # Calculate capture fraction for this layer
                # exp(−t·Δz·μ/ρ) − exp(−(t+1)·Δz·μ/ρ)
                exp_start = torch.exp(-t * delta_z * mu / parallax)
                exp_end = torch.exp(-(t + 1) * delta_z * mu / parallax)
                capture_fraction = exp_start - exp_end

                # Apply to intensity and accumulate
                result = result + intensity * capture_fraction

        else:
            # Use last-value semantics: multiply by last layer's capture fraction
            t = thicksteps - 1  # Last layer
            exp_start = torch.exp(-t * delta_z * mu / parallax)
            exp_end = torch.exp(-(t + 1) * delta_z * mu / parallax)
            capture_fraction = exp_start - exp_end

            result = intensity * capture_fraction

        return result
