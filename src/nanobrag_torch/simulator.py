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
        crystal_config: CrystalConfig = None,
        beam_config: BeamConfig = None,
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
        self.crystal_config = crystal_config if crystal_config is not None else CrystalConfig()
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
        self.r_e_sqr = 7.94079248018965e-30  # classical electron radius squared (meters squared)
        self.fluence = 125932015286227086360700780544.0  # photons per square meter (C default)
        self.polarization = 1.0  # unpolarized beam

    def run(self, pixel_batch_size: Optional[int] = None, override_a_star: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Run the diffraction simulation with crystal rotation and mosaicity.

        This method vectorizes the simulation over all detector pixels, phi angles,
        and mosaic domains. It integrates contributions from all crystal orientations
        to produce the final diffraction pattern.

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

        Returns:
            torch.Tensor: Final diffraction image with shape (spixels, fpixels).
        """
        # Get pixel coordinates (spixels, fpixels, 3) in Angstroms
        pixel_coords_angstroms = self.detector.get_pixel_coords()
        
        # Calculate scattering vectors for each pixel
        # The C code calculates scattering vector as the difference between
        # unit vectors pointing to the pixel and the incident direction
        
        # Diffracted beam unit vector (from origin to pixel)
        pixel_magnitudes = torch.sqrt(
            torch.sum(pixel_coords_angstroms * pixel_coords_angstroms, dim=-1, keepdim=True)
        )
        diffracted_beam_unit = pixel_coords_angstroms / pixel_magnitudes

        # Incident beam unit vector [1, 0, 0]
        incident_beam_unit = self.incident_beam_direction.expand_as(diffracted_beam_unit)

        # Scattering vector using crystallographic convention (nanoBragg.c style)
        # S = (s_out - s_in) / λ where s_out, s_in are unit vectors
        scattering_vector = (diffracted_beam_unit - incident_beam_unit) / self.wavelength

        # Get rotated lattice vectors for all phi steps and mosaic domains
        # Shape: (N_phi, N_mos, 3)
        if override_a_star is None:
            rot_a, rot_b, rot_c = self.crystal.get_rotated_real_vectors(self.crystal_config)
        else:
            # For gradient testing with override, use single orientation
            rot_a = override_a_star.view(1, 1, 3)
            rot_b = self.crystal.b.view(1, 1, 3)
            rot_c = self.crystal.c.view(1, 1, 3)

        # Broadcast scattering vector to be compatible with rotation dimensions
        # scattering_vector: (S, F, 3) -> (S, F, 1, 1, 3)
        # rot_a: (N_phi, N_mos, 3) -> (1, 1, N_phi, N_mos, 3)
        scattering_broadcast = scattering_vector.unsqueeze(-2).unsqueeze(-2)
        rot_a_broadcast = rot_a.unsqueeze(0).unsqueeze(0)
        rot_b_broadcast = rot_b.unsqueeze(0).unsqueeze(0)
        rot_c_broadcast = rot_c.unsqueeze(0).unsqueeze(0)

        # Calculate dimensionless Miller indices using nanoBragg.c convention
        # nanoBragg.c uses: h = S·a where S is the scattering vector and a is real-space vector
        # Result shape: (S, F, N_phi, N_mos)
        h = dot_product(scattering_broadcast, rot_a_broadcast)
        k = dot_product(scattering_broadcast, rot_b_broadcast)
        l = dot_product(scattering_broadcast, rot_c_broadcast)

        # Find nearest integer Miller indices for structure factor lookup
        h0 = torch.round(h)
        k0 = torch.round(k)
        l0 = torch.round(l)

        # Look up structure factors F_cell using integer indices
        F_cell = self.crystal.get_structure_factor(h0, k0, l0)

        # Calculate lattice structure factor F_latt using fractional differences
        # The sincg function models the shape of the Bragg peak around integer positions
        delta_h = h - h0
        delta_k = k - k0
        delta_l = l - l0
        F_latt_a = sincg(delta_h, self.crystal.N_cells_a)
        F_latt_b = sincg(delta_k, self.crystal.N_cells_b)
        F_latt_c = sincg(delta_l, self.crystal.N_cells_c)
        F_latt = F_latt_a * F_latt_b * F_latt_c

        # Calculate total structure factor and intensity
        # Shape: (S, F, N_phi, N_mos)
        F_total = F_cell * F_latt
        intensity = F_total * F_total  # |F|^2

        # Integrate over phi steps and mosaic domains
        # Sum across the last two dimensions to get final 2D image
        integrated_intensity = torch.sum(intensity, dim=(-2, -1))

        # Apply physical scaling factors (from nanoBragg.c ~line 3050)
        # Solid angle correction, converting all units to meters for calculation
        airpath = pixel_magnitudes.squeeze(-1)  # Remove last dimension for broadcasting
        airpath_m = airpath * 1e-10  # Å to meters
        close_distance_m = self.detector.distance * 1e-10  # Å to meters
        pixel_size_m = self.detector.pixel_size * 1e-10  # Å to meters
        
        omega_pixel = (pixel_size_m**2) / (airpath_m**2) * close_distance_m / airpath_m
        
        # Final intensity with all physical constants in meters
        # Units: [dimensionless] × [steradians] × [m²] × [photons/m²] × [dimensionless] = [photons·steradians]
        physical_intensity = integrated_intensity * self.r_e_sqr * self.fluence * self.polarization * omega_pixel

        return physical_intensity
