#!/usr/bin/env python
"""Debug script to check Miller index calculation for specific pixels."""

import os
import torch

# Set up environment
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Import PyTorch implementation
from nanobrag_torch.config import (
    CrystalConfig, BeamConfig, DetectorConfig,
    DetectorConvention, DetectorPivot
)
from nanobrag_torch.models import Crystal, Detector


def check_miller_indices():
    """Check what Miller indices are calculated for specific pixels."""

    # Create configuration matching the test
    crystal_config = CrystalConfig(
        cell_a=70.0,
        cell_b=80.0,
        cell_c=90.0,
        cell_alpha=85.0,
        cell_beta=95.0,
        cell_gamma=105.0,
        N_cells=(1, 1, 1),
        default_F=100.0
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

    # Get pixel coordinates for a few test pixels
    test_pixels = [
        (0, 0),      # Corner
        (128, 128),  # Center
        (129, 129),  # Just off-center
        (100, 100),  # Arbitrary
        (150, 150),  # Another arbitrary
    ]

    print("=" * 60)
    print("MILLER INDEX CALCULATION FOR SPECIFIC PIXELS")
    print("=" * 60)

    # Get all pixel coordinates
    pixel_coords_meters = detector.get_pixel_coords()
    pixel_coords_angstroms = pixel_coords_meters * 1e10

    # Incident beam (MOSFLM: along +X)
    incident_beam_unit = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)

    for slow, fast in test_pixels:
        print(f"\nPixel ({slow}, {fast}):")

        # Get pixel position
        pixel_pos = pixel_coords_angstroms[slow, fast]
        print(f"  Position (Å): {pixel_pos.numpy()}")

        # Calculate diffracted beam unit vector
        pixel_distance = torch.norm(pixel_pos)
        diffracted_unit = pixel_pos / pixel_distance
        print(f"  Diffracted unit vector: {diffracted_unit.numpy()}")

        # Calculate scattering vector
        scattering_vector = (diffracted_unit - incident_beam_unit) / beam_config.wavelength_A
        print(f"  Scattering vector S: {scattering_vector.numpy()}")
        print(f"  |S| = {torch.norm(scattering_vector).item():.6f}")

        # Calculate Miller indices using real-space vectors
        h = torch.dot(scattering_vector, crystal.a)
        k = torch.dot(scattering_vector, crystal.b)
        l = torch.dot(scattering_vector, crystal.c)

        print(f"  Miller indices (h,k,l): ({h:.4f}, {k:.4f}, {l:.4f})")

        # Round to nearest integer
        h0 = torch.round(h)
        k0 = torch.round(k)
        l0 = torch.round(l)
        print(f"  Nearest integers: ({h0:.0f}, {k0:.0f}, {l0:.0f})")

        # Check structure factor
        F = crystal.get_structure_factor(h0, k0, l0)
        print(f"  Structure factor F: {F:.1f}")

    # Now check what's happening with the HKL grid
    print("\n" + "=" * 60)
    print("HKL GRID INFORMATION")
    print("=" * 60)

    if crystal.hkl_data is not None:
        h_range = crystal.hkl_data['h_range']
        k_range = crystal.hkl_data['k_range']
        l_range = crystal.hkl_data['l_range']
        print(f"HKL grid loaded:")
        print(f"  h: {h_range[0]} to {h_range[1]}")
        print(f"  k: {k_range[0]} to {k_range[1]}")
        print(f"  l: {l_range[0]} to {l_range[1]}")

        # Count non-zero entries
        grid = crystal.hkl_data['grid']
        non_zero = torch.sum(grid != 0)
        total = grid.numel()
        print(f"  Non-zero entries: {non_zero} / {total}")
    else:
        print("No HKL data loaded - using default_F everywhere")
        print(f"default_F = {crystal_config.default_F}")

    # Check if interpolation is enabled
    print(f"\nInterpolation enabled: {crystal.interpolation_enabled}")


if __name__ == "__main__":
    check_miller_indices()