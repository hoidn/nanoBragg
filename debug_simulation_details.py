#!/usr/bin/env python
"""Debug script to understand why the simulation produces zero intensity."""

import os
import torch
import numpy as np
import tempfile

# Set up environment
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Import PyTorch implementation
from nanobrag_torch.config import (
    CrystalConfig, BeamConfig, DetectorConfig,
    DetectorConvention, DetectorPivot, CrystalShape
)
from nanobrag_torch.models import Crystal, Detector
from nanobrag_torch.io.hkl import read_hkl_file


def debug_simulation():
    """Debug why simulation produces zero intensity."""

    # Try different crystal configurations
    configs = [
        {
            "name": "N=1, shape=SQUARE",
            "N_cells": (1, 1, 1),
            "shape": CrystalShape.SQUARE,
            "fudge": 1.0
        },
        {
            "name": "N=5, shape=SQUARE",
            "N_cells": (5, 5, 5),
            "shape": CrystalShape.SQUARE,
            "fudge": 1.0
        },
        {
            "name": "N=1, shape=GAUSS",
            "N_cells": (1, 1, 1),
            "shape": CrystalShape.GAUSS,
            "fudge": 1.0
        },
        {
            "name": "N=5, shape=GAUSS",
            "N_cells": (5, 5, 5),
            "shape": CrystalShape.GAUSS,
            "fudge": 1.0
        },
    ]

    for config in configs:
        print(f"\n{'=' * 60}")
        print(f"Testing: {config['name']}")
        print(f"{'=' * 60}")

        crystal_config = CrystalConfig(
            cell_a=70.0,
            cell_b=80.0,
            cell_c=90.0,
            cell_alpha=85.0,
            cell_beta=95.0,
            cell_gamma=105.0,
            N_cells=config["N_cells"],
            shape=config["shape"],
            fudge=config["fudge"],
            default_F=100.0  # Use default_F to simplify
        )

        detector_config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM,
            distance_mm=150.0,
            pixel_size_mm=0.1,
            spixels=256,
            fpixels=256
        )

        beam_config = BeamConfig(
            wavelength_A=1.5
        )

        # Create objects
        crystal = Crystal(crystal_config, beam_config)
        detector = Detector(detector_config)

        # Test a specific pixel near the beam center
        test_pixel = (128, 128)  # Center pixel

        # Get pixel coordinates
        pixel_coords_meters = detector.get_pixel_coords()
        pixel_coords_angstroms = pixel_coords_meters * 1e10

        # Get position for test pixel
        pixel_pos = pixel_coords_angstroms[test_pixel[0], test_pixel[1]]

        # Calculate scattering vector
        pixel_dist = torch.norm(pixel_pos)
        diffracted_unit = pixel_pos / pixel_dist
        incident_unit = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)

        scattering_vector = (diffracted_unit - incident_unit) / beam_config.wavelength_A

        # Calculate Miller indices
        h = torch.dot(scattering_vector, crystal.a)
        k = torch.dot(scattering_vector, crystal.b)
        l = torch.dot(scattering_vector, crystal.c)

        print(f"Test pixel {test_pixel}:")
        print(f"  Miller indices: h={h:.4f}, k={k:.4f}, l={l:.4f}")
        print(f"  Rounded: h0={torch.round(h):.0f}, k0={torch.round(k):.0f}, l0={torch.round(l):.0f}")

        # Check structure factor
        h0 = torch.round(h)
        k0 = torch.round(k)
        l0 = torch.round(l)
        F_cell = crystal.get_structure_factor(h0, k0, l0)
        print(f"  F_cell: {F_cell:.2f}")

        # Calculate F_latt for SQUARE shape (simplest case)
        if config["shape"] == CrystalShape.SQUARE:
            # F_latt = Na·Nb·Nc for integer indices
            Na, Nb, Nc = config["N_cells"]
            F_latt = Na * Nb * Nc
            print(f"  F_latt (SQUARE): {F_latt}")

        # Calculate F_latt for GAUSS shape
        elif config["shape"] == CrystalShape.GAUSS:
            h_frac = h - h0
            k_frac = k - k0
            l_frac = l - l0

            # Calculate reciprocal space distance
            delta_r_star = (h_frac * crystal.a_star +
                          k_frac * crystal.b_star +
                          l_frac * crystal.c_star)
            rad_star_sqr = torch.sum(delta_r_star * delta_r_star)

            Na, Nb, Nc = config["N_cells"]
            rad_star_sqr_scaled = rad_star_sqr * Na * Na * Nb * Nb * Nc * Nc

            F_latt = Na * Nb * Nc * torch.exp(-(rad_star_sqr_scaled / 0.63) * config["fudge"])
            print(f"  h_frac={h_frac:.4f}, k_frac={k_frac:.4f}, l_frac={l_frac:.4f}")
            print(f"  rad_star_sqr: {rad_star_sqr:.6f}")
            print(f"  rad_star_sqr_scaled: {rad_star_sqr_scaled:.6f}")
            print(f"  F_latt (GAUSS): {F_latt:.6f}")

        # Total intensity
        F_total = F_cell * F_latt
        intensity = F_total * F_total
        print(f"  F_total: {F_total:.6f}")
        print(f"  Intensity: {intensity:.6f}")

    print(f"\n{'=' * 60}")
    print("OBSERVATIONS:")
    print("1. For N=1, F_latt = 1 for SQUARE (good)")
    print("2. For GAUSS, check if exponential term is reasonable")
    print("3. Higher N should give stronger intensity")


if __name__ == "__main__":
    debug_simulation()