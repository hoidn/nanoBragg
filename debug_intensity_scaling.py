#!/usr/bin/env python3
"""
Debug script to trace intensity scaling issue.
"""

import os
import torch
import numpy as np

# Set the environment variable to prevent MKL conflicts
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from src.nanobrag_torch.config import (
    DetectorConfig, CrystalConfig, BeamConfig, DetectorConvention
)
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.simulator import Simulator


def debug_intensity_components():
    """Debug individual components of intensity calculation."""
    print("=== DEBUGGING INTENSITY SCALING ===")

    # Use the same configuration as the failing test
    pixel_size = 0.1  # mm
    beam_center_mm = 128 * pixel_size  # 12.8mm

    detector_config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        distance_mm=100.0,
        pixel_size_mm=pixel_size,
        spixels=256,
        fpixels=256,
        beam_center_s=beam_center_mm,
        beam_center_f=beam_center_mm,
    )

    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),  # Larger crystal for more reflections
        default_F=100.0
    )

    beam_config = BeamConfig(
        wavelength_A=6.2,
        fluence=1e12
    )

    # Create components
    detector = Detector(detector_config)
    crystal = Crystal(crystal_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)

    print(f"\n=== SIMULATION PARAMETERS ===")
    print(f"Wavelength: {simulator.wavelength} Å")
    print(f"Fluence: {simulator.fluence} photons/m²")
    print(f"r_e_sqr: {simulator.r_e_sqr} m²")
    print(f"Default F: {crystal_config.default_F}")
    print(f"N_cells: ({crystal.N_cells_a}, {crystal.N_cells_b}, {crystal.N_cells_c})")

    # Check crystal lattice vectors
    print(f"\n=== CRYSTAL VECTORS ===")
    print(f"a vector: {crystal.a}")
    print(f"b vector: {crystal.b}")
    print(f"c vector: {crystal.c}")
    print(f"a* vector: {crystal.a_star}")
    print(f"b* vector: {crystal.b_star}")
    print(f"c* vector: {crystal.c_star}")

    # Test a few specific pixel calculations
    print(f"\n=== PIXEL CALCULATION TEST ===")

    # Get pixel coordinates for center pixel
    pixel_coords_meters = detector.get_pixel_coords()
    pixel_coords_angstroms = pixel_coords_meters * 1e10

    center_s, center_f = 128, 128
    center_coord = pixel_coords_angstroms[center_s, center_f]
    print(f"Center pixel coord (Å): {center_coord}")

    # Calculate scattering vector for center pixel
    pixel_magnitude = torch.sqrt(torch.sum(center_coord * center_coord))
    diffracted_beam_unit = center_coord / pixel_magnitude
    incident_beam_unit = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
    scattering_vector = (diffracted_beam_unit - incident_beam_unit) / simulator.wavelength

    print(f"Pixel magnitude: {pixel_magnitude}")
    print(f"Diffracted beam unit: {diffracted_beam_unit}")
    print(f"Scattering vector: {scattering_vector}")

    # Calculate Miller indices
    h = torch.dot(scattering_vector, crystal.a)
    k = torch.dot(scattering_vector, crystal.b)
    l = torch.dot(scattering_vector, crystal.c)

    print(f"Miller indices (h,k,l): ({h:.6f}, {k:.6f}, {l:.6f})")

    # Find nearest integer indices
    h0 = torch.round(h)
    k0 = torch.round(k)
    l0 = torch.round(l)

    print(f"Nearest integer indices: ({h0}, {k0}, {l0})")

    # Get structure factor
    F_cell = crystal.get_structure_factor(h0.unsqueeze(0), k0.unsqueeze(0), l0.unsqueeze(0))
    print(f"F_cell: {F_cell}")

    # Calculate lattice factor (SQUARE shape)
    from src.nanobrag_torch.utils.physics import sincg

    h_frac = h - h0
    k_frac = k - k0
    l_frac = l - l0

    print(f"Fractional parts: ({h_frac:.6f}, {k_frac:.6f}, {l_frac:.6f})")

    F_latt_a = sincg(torch.pi * h_frac, crystal.N_cells_a)
    F_latt_b = sincg(torch.pi * k_frac, crystal.N_cells_b)
    F_latt_c = sincg(torch.pi * l_frac, crystal.N_cells_c)
    F_latt = F_latt_a * F_latt_b * F_latt_c

    print(f"F_latt components: ({F_latt_a:.6f}, {F_latt_b:.6f}, {F_latt_c:.6f})")
    print(f"F_latt total: {F_latt}")

    # Calculate total structure factor and intensity
    F_total = F_cell * F_latt
    intensity = F_total * F_total

    print(f"F_total: {F_total}")
    print(f"Raw intensity: {intensity}")

    # Calculate physical scaling factors
    airpath = pixel_magnitude * 1e-10  # Å to meters
    close_distance_m = detector.distance  # Already in meters
    pixel_size_m = detector.pixel_size  # Already in meters

    omega_pixel = (
        (pixel_size_m * pixel_size_m)
        / (airpath * airpath)
        * close_distance_m
        / airpath
    )

    print(f"\n=== PHYSICAL SCALING ===")
    print(f"Airpath (m): {airpath}")
    print(f"Close distance (m): {close_distance_m}")
    print(f"Pixel size (m): {pixel_size_m}")
    print(f"Omega: {omega_pixel}")

    # Final intensity
    final_intensity = (
        intensity
        * omega_pixel
        * simulator.r_e_sqr
        * simulator.fluence
    )

    print(f"Final intensity: {final_intensity}")

    # Compare with actual simulation result
    image = simulator.run()
    actual_center = image[center_s, center_f]
    print(f"Actual simulation result at center: {actual_center}")
    print(f"Ratio (manual/actual): {final_intensity / actual_center if actual_center != 0 else 'inf'}")


if __name__ == "__main__":
    debug_intensity_components()