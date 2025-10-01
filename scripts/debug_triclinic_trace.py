#!/usr/bin/env python
"""Generate detailed trace for triclinic simulation to match C-code output."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from pathlib import Path
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.config import CrystalConfig, DetectorConfig

def trace_triclinic_pixel():
    """Generate detailed trace for pixel (372, 289) in triclinic simulation."""
    
    # Match exact parameters from C trace
    device = torch.device("cpu")
    dtype = torch.float64
    
    print("=== PYTHON TRICLINIC TRACE ===")
    
    # Triclinic crystal configuration matching C-code
    triclinic_config = CrystalConfig(
        cell_a=70.0,
        cell_b=80.0,
        cell_c=90.0,
        cell_alpha=75.0391,
        cell_beta=85.0136,
        cell_gamma=95.0081,
        N_cells=[5, 5, 5],
        misset_deg=(-89.968546, -31.328953, 177.753396),
    )
    
    crystal = Crystal(config=triclinic_config, device=device, dtype=dtype)
    
    # Detector configuration matching C-code
    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=512,
        fpixels=512,
        beam_center_s=256.5,
        beam_center_f=256.5,
    )
    
    detector = Detector(config=detector_config, device=device, dtype=dtype)
    
    # Print crystal vectors to match C trace
    print("TRACE: After crystal initialization:")
    print(f"TRACE:   a = {crystal.a.tolist()} |a| = {torch.norm(crystal.a).item():.6g}")
    print(f"TRACE:   b = {crystal.b.tolist()} |b| = {torch.norm(crystal.b).item():.6g}")
    print(f"TRACE:   c = {crystal.c.tolist()} |c| = {torch.norm(crystal.c).item():.6g}")
    print(f"TRACE:   a_star = {crystal.a_star.tolist()} |a_star| = {torch.norm(crystal.a_star).item():.6g}")
    print(f"TRACE:   b_star = {crystal.b_star.tolist()} |b_star| = {torch.norm(crystal.b_star).item():.6g}")
    print(f"TRACE:   c_star = {crystal.c_star.tolist()} |c_star| = {torch.norm(crystal.c_star).item():.6g}")
    
    # Create simulator
    crystal_rot_config = CrystalConfig(
        phi_start_deg=torch.tensor(0.0, device=device, dtype=dtype),
        osc_range_deg=torch.tensor(0.0, device=device, dtype=dtype),
        mosaic_spread_deg=torch.tensor(0.0, device=device, dtype=dtype),
        mosaic_domains=1,
    )
    
    simulator = Simulator(
        crystal,
        detector,
        crystal_config=crystal_rot_config,
        device=device,
        dtype=dtype,
    )
    
    # Set wavelength to match C-code
    simulator.wavelength = 1.0
    
    # Target pixel coordinates from C trace
    target_spixel = 372
    target_fpixel = 289
    
    print(f"TRACE: Tracing pixel ({target_spixel}, {target_fpixel})")
    
    # Manually calculate the same values that the C code traces
    # Get detector pixel positions
    slow_indices = torch.arange(detector.spixels, device=device, dtype=dtype)
    fast_indices = torch.arange(detector.fpixels, device=device, dtype=dtype)
    slow_grid, fast_grid = torch.meshgrid(slow_indices, fast_indices, indexing="ij")
    
    # Extract target pixel position
    s_idx = target_spixel
    f_idx = target_fpixel
    
    # Calculate pixel position in meters (matching C code)
    # Get detector geometry vectors (ALREADY IN METERS - no conversion needed!)
    pix0_vec = detector.pix0_vector  # Already in meters
    fdet_vec = detector.fdet_vec     # Unit vector (dimensionless)
    sdet_vec = detector.sdet_vec     # Unit vector (dimensionless)

    pixel_size_m = detector.pixel_size  # Already in meters
    
    # Calculate pixel position in meters
    # pixel_pos = pix0_vector + f_idx * pixel_size * fdet_vec + s_idx * pixel_size * sdet_vec
    pixel_pos_vec = pix0_vec + f_idx * pixel_size_m * fdet_vec + s_idx * pixel_size_m * sdet_vec
    
    # Extract components (C code uses different axis convention)
    pixel_pos_distance = pixel_pos_vec[0].item()  # Distance along beam (x-axis)
    pixel_pos_s = pixel_pos_vec[1].item()         # Slow axis (y-axis)
    pixel_pos_f = pixel_pos_vec[2].item()         # Fast axis (z-axis)
    
    print(f"TRACE_PY: pixel_pos_meters {pixel_pos_distance:.15g} {pixel_pos_s:.15g} {pixel_pos_f:.15g}")
    
    # Calculate diffracted beam direction (unit vector)
    pixel_pos_vec = torch.tensor([pixel_pos_distance, pixel_pos_s, pixel_pos_f], device=device, dtype=dtype)
    airpath = torch.norm(pixel_pos_vec)
    diffracted = pixel_pos_vec / airpath
    
    print(f"TRACE_PY: diffracted_vec {diffracted[0].item():.15g} {diffracted[1].item():.15g} {diffracted[2].item():.15g}")
    
    # Calculate scattering vector
    # Incident beam is along +x: incident = [1, 0, 0]
    incident = torch.tensor([1.0, 0.0, 0.0], device=device, dtype=dtype)
    lambda_A = 1.0  # Angstroms (from simulator.wavelength)
    lambda_m = lambda_A * 1e-10  # Convert to meters

    # Scattering vector in m^-1
    scattering_m_inv = (diffracted - incident) / lambda_m

    # Convert to Angstrom^-1 for output
    scattering_A_inv = scattering_m_inv * 1e-10

    print(f"TRACE_PY: scattering_vec_A_inv {scattering_A_inv[0].item():.15g} {scattering_A_inv[1].item():.15g} {scattering_A_inv[2].item():.15g}")
    
    # Calculate Miller indices using rotated real-space vectors
    # Get the rotated vectors (no phi/mosaic rotation for this case)
    (rot_a, rot_b, rot_c), (rot_a_star, rot_b_star, rot_c_star) = crystal.get_rotated_real_vectors(crystal_rot_config)
    
    # For our single pixel and single domain/phi case, extract the vectors
    # Shape should be (1, 1, 3) for (N_phi, N_mos, 3)
    a_vec = rot_a[0, 0]  # First phi, first mosaic domain
    b_vec = rot_b[0, 0]
    c_vec = rot_c[0, 0]
    
    # Calculate fractional Miller indices: h = S·a, etc.
    # scattering_A_inv is already in Angstrom^-1
    h_frac = torch.dot(scattering_A_inv, a_vec)
    k_frac = torch.dot(scattering_A_inv, b_vec) 
    l_frac = torch.dot(scattering_A_inv, c_vec)
    
    print(f"TRACE_PY: hkl_frac {h_frac.item():.15g} {k_frac.item():.15g} {l_frac.item():.15g}")
    
    # Calculate integer Miller indices
    h0 = torch.round(h_frac).int()
    k0 = torch.round(k_frac).int()
    l0 = torch.round(l_frac).int()
    
    print(f"TRACE_PY: hkl_int {h0.item()} {k0.item()} {l0.item()}")
    
    # Calculate F_cell (structure factor)
    F_cell = crystal.get_structure_factor(h0.float(), k0.float(), l0.float())
    print(f"TRACE_PY: F_cell {F_cell.item():.15g}")
    
    # Calculate F_latt using fractional parts
    from nanobrag_torch.utils.physics import sincg
    F_latt_a = sincg(torch.pi * (h_frac - h0.float()), crystal.N_cells_a)
    F_latt_b = sincg(torch.pi * (k_frac - k0.float()), crystal.N_cells_b)
    F_latt_c = sincg(torch.pi * (l_frac - l0.float()), crystal.N_cells_c)
    F_latt = F_latt_a * F_latt_b * F_latt_c
    
    print(f"TRACE_PY: F_latt_components {F_latt_a.item():.15g} {F_latt_b.item():.15g} {F_latt_c.item():.15g}")
    print(f"TRACE_PY: F_latt {F_latt.item():.15g}")
    
    # Calculate total structure factor and intensity
    F_total = F_cell * F_latt
    intensity = F_total * F_total  # |F|^2
    
    print(f"TRACE_PY: F_total {F_total.item():.15g}")
    print(f"TRACE_PY: intensity_raw {intensity.item():.15g}")
    
    # Apply physical scaling factors like the C code does
    # Solid angle correction
    close_distance_m = detector.distance  # Already in meters
    pixel_size_m_omega = detector.pixel_size  # Already in meters
    
    omega_pixel = (pixel_size_m_omega * pixel_size_m_omega) / (airpath.item() * airpath.item()) * close_distance_m / airpath.item()
    
    print(f"TRACE_PY: omega_pixel {omega_pixel:.15g}")
    
    # Apply full scaling (this is approximate - would need all C constants)
    r_e_sqr = 7.94079248018965e-30  # Thomson cross section
    fluence = 1.25932015286227086e29  # From C trace
    
    # This is a simplified version - the C code has more complex scaling
    physical_intensity = intensity.item() * omega_pixel * r_e_sqr * fluence
    
    print(f"TRACE_PY: physical_intensity {physical_intensity:.15g}")
    
    print("\n=== COMPARISON SUMMARY ===")
    print("Check these values against the C trace:")
    print(f"  Pixel position (meters): {pixel_pos_distance:.15g} {pixel_pos_s:.15g} {pixel_pos_f:.15g}")
    print(f"  Diffracted vector: {diffracted[0].item():.15g} {diffracted[1].item():.15g} {diffracted[2].item():.15g}")  
    print(f"  Scattering vector: {scattering_A_inv[0].item():.15g} {scattering_A_inv[1].item():.15g} {scattering_A_inv[2].item():.15g}")
    print(f"  Miller indices (frac): {h_frac.item():.15g} {k_frac.item():.15g} {l_frac.item():.15g}")
    print(f"  Miller indices (int): {h0.item()} {k0.item()} {l0.item()}")
    print(f"  F_latt: {F_latt.item():.15g}")
    print(f"  Final intensity: {physical_intensity:.15g}")

if __name__ == "__main__":
    trace_triclinic_pixel()