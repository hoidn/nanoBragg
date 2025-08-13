#!/usr/bin/env python3
"""Test if golden data matches our raw intensity before physical scaling."""

import torch
import numpy as np
import sys
import os

sys.path.insert(0, "src")

from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


def main():
    print("=== Testing Raw Intensity Hypothesis ===")

    # Create components
    device = torch.device("cpu")
    dtype = torch.float64

    crystal = Crystal(device=device, dtype=dtype)
    detector = Detector(device=device, dtype=dtype)

    # I need to modify the simulator to return raw intensity
    # Let me create a custom version temporarily

    # Get pixel coordinates
    pixel_coords_angstroms = detector.get_pixel_coords()

    # Calculate scattering vectors (copy from simulator.py)
    pixel_magnitudes = torch.sqrt(
        torch.sum(pixel_coords_angstroms * pixel_coords_angstroms, dim=-1, keepdim=True)
    )
    diffracted_beam_unit = pixel_coords_angstroms / pixel_magnitudes

    incident_beam_direction = torch.tensor([1.0, 0.0, 0.0], device=device, dtype=dtype)
    incident_beam_unit = incident_beam_direction.expand_as(diffracted_beam_unit)

    wavelength = 1.0
    two_pi_by_lambda = 2.0 * torch.pi / wavelength
    k_in = two_pi_by_lambda * incident_beam_unit
    k_out = two_pi_by_lambda * diffracted_beam_unit
    scattering_vector = k_out - k_in

    # Calculate Miller indices
    from nanobrag_torch.utils.geometry import dot_product

    h = dot_product(scattering_vector, crystal.a_star.view(1, 1, 3))
    k = dot_product(scattering_vector, crystal.b_star.view(1, 1, 3))
    l = dot_product(scattering_vector, crystal.c_star.view(1, 1, 3))

    h0 = torch.round(h)
    k0 = torch.round(k)
    l0 = torch.round(l)

    F_cell = crystal.get_structure_factor(h0, k0, l0)

    # Calculate lattice structure factor
    from nanobrag_torch.utils.physics import sincg

    delta_h = h - h0
    delta_k = k - k0
    delta_l = l - l0
    F_latt_a = sincg(delta_h, crystal.N_cells_a)
    F_latt_b = sincg(delta_k, crystal.N_cells_b)
    F_latt_c = sincg(delta_l, crystal.N_cells_c)
    F_latt = F_latt_a * F_latt_b * F_latt_c

    # Raw intensity (before physical scaling)
    F_total = F_cell * F_latt
    raw_intensity = F_total * F_total

    # Load golden data
    golden_float_data = torch.from_numpy(
        np.fromfile("tests/golden_data/simple_cubic.bin", dtype=np.float32).reshape(
            500, 500
        )
    ).to(dtype=torch.float64)

    print(
        f"Raw intensity: max={torch.max(raw_intensity):.2e}, mean={torch.mean(raw_intensity):.2e}"
    )
    print(
        f"Golden data:   max={torch.max(golden_float_data):.2e}, mean={torch.mean(golden_float_data):.2e}"
    )

    # Check ratio
    ratio = torch.max(raw_intensity) / torch.max(golden_float_data)
    print(f"Ratio: {ratio:.2e}")

    # Test if scaling by some factor makes them match
    for scale in [1e-9, 1e-10, 1e-11, 1e-12, 1e-13, 1e-14, 1e-15]:
        scaled = raw_intensity * scale
        if torch.allclose(scaled, golden_float_data, rtol=1e-5, atol=1e-15):
            print(f"MATCH FOUND with scale factor: {scale}")
            return

    print("No simple scaling factor found")


if __name__ == "__main__":
    main()
