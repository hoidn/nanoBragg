#!/usr/bin/env python3
"""Debug script to isolate NaN gradients in the full simulation pipeline."""

import os
import torch
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

def test_simulation_components():
    """Test each component of the simulation to isolate NaN source."""
    print("=== Testing Full Simulation Components ===")

    device = torch.device('cpu')
    dtype = torch.float64

    # Create tensor parameter with gradient
    cell_a = torch.tensor(100.0, dtype=dtype, requires_grad=True)

    config = CrystalConfig(
        cell_a=cell_a,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        mosaic_spread_deg=0.0,
        mosaic_domains=1,
        N_cells=(5, 5, 5),
    )

    crystal = Crystal(config=config, device=device, dtype=dtype)
    detector = Detector(device=device, dtype=dtype)
    simulator = Simulator(crystal, detector, crystal_config=config, device=device, dtype=dtype)

    print("\n1. Testing pixel coordinate calculation...")
    pixel_coords_meters = detector.get_pixel_coords()
    pixel_coords_angstroms = pixel_coords_meters * 1e10
    print(f"   Pixel coords contains NaN: {torch.isnan(pixel_coords_angstroms).any()}")

    print("\n2. Testing scattering vector calculation...")
    pixel_squared_sum = torch.sum(pixel_coords_angstroms * pixel_coords_angstroms, dim=-1, keepdim=True)
    pixel_squared_sum = torch.clamp(pixel_squared_sum, min=0.0)
    pixel_magnitudes = torch.sqrt(pixel_squared_sum)
    diffracted_beam_unit = pixel_coords_angstroms / pixel_magnitudes

    incident_beam_direction = torch.tensor([1.0, 0.0, 0.0], device=device, dtype=dtype)
    incident_beam_unit = incident_beam_direction.expand_as(diffracted_beam_unit)
    wavelength = 6.2  # From beam config

    scattering_vector = (diffracted_beam_unit - incident_beam_unit) / wavelength
    print(f"   Scattering vector contains NaN: {torch.isnan(scattering_vector).any()}")

    print("\n3. Testing lattice vector rotation...")
    (rot_a, rot_b, rot_c), (rot_a_star, rot_b_star, rot_c_star) = crystal.get_rotated_real_vectors(config)
    print(f"   Rotated a contains NaN: {torch.isnan(rot_a).any()}")

    print("\n4. Testing Miller index calculation...")
    # Broadcast for vectorized calculation
    scattering_broadcast = scattering_vector.unsqueeze(-2).unsqueeze(-2)
    rot_a_broadcast = rot_a.unsqueeze(0).unsqueeze(0)
    rot_b_broadcast = rot_b.unsqueeze(0).unsqueeze(0)
    rot_c_broadcast = rot_c.unsqueeze(0).unsqueeze(0)

    # Use manual dot product to avoid potential issues in utils.geometry
    h = torch.sum(scattering_broadcast * rot_a_broadcast, dim=-1)
    k = torch.sum(scattering_broadcast * rot_b_broadcast, dim=-1)
    l = torch.sum(scattering_broadcast * rot_c_broadcast, dim=-1)

    print(f"   h contains NaN: {torch.isnan(h).any()}")
    print(f"   k contains NaN: {torch.isnan(k).any()}")
    print(f"   l contains NaN: {torch.isnan(l).any()}")

    print("\n5. Testing structure factor lookup...")
    h0 = torch.round(h)
    k0 = torch.round(k)
    l0 = torch.round(l)

    F_cell = crystal.get_structure_factor(h0, k0, l0)
    print(f"   F_cell contains NaN: {torch.isnan(F_cell).any()}")
    print(f"   F_cell shape: {F_cell.shape}")
    print(f"   F_cell sample values: {F_cell[500:510, 500:510, 0, 0]}")

    print("\n6. Testing lattice structure factor (SQUARE shape)...")
    Na = crystal.N_cells_a
    Nb = crystal.N_cells_b
    Nc = crystal.N_cells_c

    # Import the sincg function to test directly
    from nanobrag_torch.utils.physics import sincg

    # Test sincg function with fractional Miller indices
    h_frac = h - h0
    k_frac = k - k0
    l_frac = l - l0

    print(f"   h_frac contains NaN: {torch.isnan(h_frac).any()}")
    print(f"   k_frac contains NaN: {torch.isnan(k_frac).any()}")
    print(f"   l_frac contains NaN: {torch.isnan(l_frac).any()}")

    # Test sincg function
    F_latt_a = sincg(torch.pi * h_frac, Na)
    F_latt_b = sincg(torch.pi * k_frac, Nb)
    F_latt_c = sincg(torch.pi * l_frac, Nc)

    print(f"   F_latt_a contains NaN: {torch.isnan(F_latt_a).any()}")
    print(f"   F_latt_b contains NaN: {torch.isnan(F_latt_b).any()}")
    print(f"   F_latt_c contains NaN: {torch.isnan(F_latt_c).any()}")

    F_latt = F_latt_a * F_latt_b * F_latt_c
    print(f"   F_latt contains NaN: {torch.isnan(F_latt).any()}")

    print("\n7. Testing intensity calculation...")
    F_total = F_cell * F_latt
    intensity = F_total * F_total
    print(f"   intensity contains NaN: {torch.isnan(intensity).any()}")

    print("\n8. Testing integration...")
    integrated_intensity = torch.sum(intensity, dim=(-2, -1))
    print(f"   integrated_intensity contains NaN: {torch.isnan(integrated_intensity).any()}")

    print("\n9. Testing normalization...")
    phi_steps = config.phi_steps
    mosaic_domains = config.mosaic_domains
    steps = phi_steps * mosaic_domains
    normalized_intensity = integrated_intensity / steps
    print(f"   normalized_intensity contains NaN: {torch.isnan(normalized_intensity).any()}")

    print("\n10. Testing physical scaling...")
    airpath = pixel_magnitudes.squeeze(-1)
    airpath_m = airpath * 1e-10
    close_distance_m = detector.distance
    pixel_size_m = detector.pixel_size

    omega_pixel = (
        (pixel_size_m * pixel_size_m)
        / (airpath_m * airpath_m)
        * close_distance_m
        / airpath_m
    )
    print(f"   omega_pixel contains NaN: {torch.isnan(omega_pixel).any()}")

    final_with_omega = normalized_intensity * omega_pixel
    print(f"   final_with_omega contains NaN: {torch.isnan(final_with_omega).any()}")

    # Physical constants
    r_e_sqr = 7.94079248018965e-30
    fluence = 1e12  # Default from BeamConfig

    physical_intensity = final_with_omega * r_e_sqr * fluence
    print(f"   physical_intensity contains NaN: {torch.isnan(physical_intensity).any()}")

    print("\n11. Testing backward pass on final result...")
    try:
        cell_a.grad = None
        loss = physical_intensity.sum()
        print(f"   Final loss: {loss}")
        print(f"   Final loss contains NaN: {torch.isnan(loss).any()}")

        loss.backward()
        print(f"   cell_a.grad: {cell_a.grad}")
        print(f"   cell_a.grad contains NaN: {torch.isnan(cell_a.grad).any() if cell_a.grad is not None else 'None'}")

    except Exception as e:
        print(f"   Error in backward pass: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simulation_components()