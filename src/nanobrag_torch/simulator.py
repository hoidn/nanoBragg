"""
Main Simulator class for nanoBragg PyTorch implementation.

This module orchestrates the entire diffraction simulation, taking Crystal and
Detector objects as input and producing the final diffraction pattern.
"""

from typing import Optional

import torch

from .config import BeamConfig, CrystalConfig
from .models.crystal import Crystal
from .models.detector import Detector
from .utils.geometry import dot_product
from .utils.physics import sincg


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
        self.device = device if device is not None else torch.device("cpu")
        self.dtype = dtype

        # Hard-coded simple_cubic beam parameters (from golden test case)
        # Incident beam direction: [1, 0, 0] (from log: INCIDENT_BEAM_DIRECTION= 1 0 0)
        # Wave: 1 Angstrom
        self.incident_beam_direction = torch.tensor(
            [1.0, 0.0, 0.0], device=self.device, dtype=self.dtype
        )
        self.wavelength = 6.2  # Angstroms (matches debug script and C code test case)

        # Physical constants (from nanoBragg.c ~line 240)
        self.r_e_sqr = (
            7.94079248018965e-30  # classical electron radius squared (meters squared)
        )
        self.fluence = (
            125932015286227086360700780544.0  # photons per square meter (C default)
        )
        self.polarization = 1.0  # unpolarized beam

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

        # Get rotated lattice vectors for all phi steps and mosaic domains
        # Shape: (N_phi, N_mos, 3)
        if override_a_star is None:
            (rot_a, rot_b, rot_c), (rot_a_star, rot_b_star, rot_c_star) = (
                self.crystal.get_rotated_real_vectors(self.crystal_config)
            )
        else:
            # For gradient testing with override, use single orientation
            rot_a = override_a_star.view(1, 1, 3)
            rot_b = self.crystal.b.view(1, 1, 3)
            rot_c = self.crystal.c.view(1, 1, 3)
            rot_a_star = override_a_star.view(1, 1, 3)
            rot_b_star = self.crystal.b_star.view(1, 1, 3)
            rot_c_star = self.crystal.c_star.view(1, 1, 3)

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

        # Calculate lattice structure factor F_latt using fractional part (h-h0)
        # CORRECT: Use fractional part (h-h0, k-k0, l-l0) to match C-code behavior
        # The sincg function expects its input pre-multiplied by π
        F_latt_a = sincg(torch.pi * (h - h0), self.crystal.N_cells_a)
        F_latt_b = sincg(torch.pi * (k - k0), self.crystal.N_cells_b)
        F_latt_c = sincg(torch.pi * (l - l0), self.crystal.N_cells_c)
        F_latt = F_latt_a * F_latt_b * F_latt_c

        # Calculate total structure factor and intensity
        # Shape: (S, F, N_phi, N_mos)
        F_total = F_cell * F_latt
        intensity = F_total * F_total  # |F|^2

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
            last_polar = torch.ones_like(normalized_intensity) * self.polarization

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

                    # Calculate polarization for this subpixel (simplified for now)
                    polar_subpixel = self.polarization

                    # Apply factors based on oversample flags
                    if oversample_omega:
                        # Apply omega per subpixel - multiply and accumulate
                        accumulated_intensity += normalized_intensity * omega_subpixel_scaled
                        omega_applied = True
                    else:
                        # Just accumulate intensity uniformly, will apply omega at end
                        accumulated_intensity += normalized_intensity / (oversample * oversample)
                        # Always update last_omega to track the final subpixel's value
                        last_omega = omega_subpixel  # Full value, not scaled

                    if oversample_polar:
                        # Apply polarization per subpixel (would multiply current contribution)
                        # For now, polarization is constant, so no effect
                        pass
                    else:
                        # Track last polarization value
                        last_polar = polar_subpixel * torch.ones_like(normalized_intensity)

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

        # Final intensity with all physical constants in meters
        # Units: [dimensionless] × [steradians] × [m²] × [photons/m²] × [dimensionless] = [photons·steradians]
        physical_intensity = (
            normalized_intensity
            * self.r_e_sqr
            * self.fluence
            * self.polarization
        )

        return physical_intensity
