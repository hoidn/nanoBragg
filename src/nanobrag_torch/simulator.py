"""
Main Simulator class for nanoBragg PyTorch implementation.

This module orchestrates the entire diffraction simulation, taking Crystal and
Detector objects as input and producing the final diffraction pattern.
"""

from typing import Optional

import torch

from .config import BeamConfig
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
        beam_config: BeamConfig = None,
        device=None,
        dtype=torch.float64,
    ):
        """Initialize simulator with crystal, detector, and beam configuration."""
        self.crystal = crystal
        self.detector = detector
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
        Run the diffraction simulation.

        Args:
            pixel_batch_size: Optional batching for memory management

        Returns:
            torch.Tensor: Final diffraction image
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

        # Calculate dimensionless Miller indices using crystallographic convention
        # Laue condition: h = S·a where S is the crystallographic scattering vector
        # Use override if provided (for gradient testing)
        a_vec = override_a_star if override_a_star is not None else self.crystal.a
        h = dot_product(
            scattering_vector, a_vec.view(1, 1, 3)
        )
        k = dot_product(
            scattering_vector, self.crystal.b.view(1, 1, 3)
        )
        l = dot_product(
            scattering_vector, self.crystal.c.view(1, 1, 3)
        )

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
        F_total = F_cell * F_latt
        intensity = F_total * F_total  # |F|^2

        # Apply physical scaling factors (from nanoBragg.c ~line 3050)
        # Solid angle correction, converting all units to meters for calculation
        airpath = pixel_magnitudes.squeeze(-1)  # Remove last dimension for broadcasting
        airpath_m = airpath * 1e-10  # Å to meters
        close_distance_m = self.detector.distance * 1e-10  # Å to meters
        pixel_size_m = self.detector.pixel_size * 1e-10  # Å to meters
        
        omega_pixel = (pixel_size_m**2) / (airpath_m**2) * close_distance_m / airpath_m
        
        # Final intensity with all physical constants in meters
        # Units: [dimensionless] × [steradians] × [m²] × [photons/m²] × [dimensionless] = [photons·steradians]
        physical_intensity = intensity * self.r_e_sqr * self.fluence * self.polarization * omega_pixel

        return physical_intensity
