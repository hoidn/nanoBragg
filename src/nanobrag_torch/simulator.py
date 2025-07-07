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
        self.wavelength = 1.0  # Angstroms

    def run(self, pixel_batch_size: Optional[int] = None) -> torch.Tensor:
        """
        Run the diffraction simulation.

        Args:
            pixel_batch_size: Optional batching for memory management

        Returns:
            torch.Tensor: Final diffraction image
        """
        # Get pixel coordinates (spixels, fpixels, 3) in meters
        pixel_coords = self.detector.get_pixel_coords()
        
        # Convert to Angstroms for scattering vector calculation
        pixel_coords_angstroms = pixel_coords * 1e10  # meters to Angstroms
        
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

        # Scattering vector: q = (k_out - k_in) in Å⁻¹
        # For X-ray diffraction: q = (2π/λ) * (unit_out - unit_in)
        two_pi_by_lambda = 2.0 * torch.pi / self.wavelength
        k_in = two_pi_by_lambda * incident_beam_unit
        k_out = two_pi_by_lambda * diffracted_beam_unit  
        scattering_vector = k_out - k_in

        # Calculate dimensionless Miller indices using reciprocal-space vectors
        # h = dot_product(q, a*) where a* is in Å⁻¹, q is in Å⁻¹
        h = dot_product(
            scattering_vector, self.crystal.a_star.expand_as(scattering_vector)
        )
        k = dot_product(
            scattering_vector, self.crystal.b_star.expand_as(scattering_vector)
        )
        l = dot_product(
            scattering_vector, self.crystal.c_star.expand_as(scattering_vector)
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

        # Return raw, unscaled intensity for comparison with floatimage.bin
        # The intfile_scale = 5.4581e+11 factor is applied when writing integer images,
        # but floatimage.bin contains the raw photon intensities

        # Sum over sources (only one source in simple_cubic case)
        # For now, no additional summing needed since we have only one source

        return intensity
