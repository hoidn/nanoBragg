#!/usr/bin/env python3
"""
Single Pixel Trace Debugging Script for nanoBragg PyTorch Implementation

This script calculates the diffraction intensity for a single, specific detector pixel
and prints a detailed, step-by-step log of all intermediate variables. This log will
serve as a "golden trace" for future debugging.

Target Pixel: (slow=250, fast=350)
This pixel is chosen because it is near a Bragg peak in the simple_cubic case.
"""

import os
import sys
import torch
import numpy as np

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.utils.geometry import dot_product, unitize, magnitude

# Constants
TARGET_S_PIXEL = 250
TARGET_F_PIXEL = 350
OUTPUT_LOG_PATH = "tests/golden_data/simple_cubic_pixel_trace.log"

def log_variable(name, tensor, log_file):
    """Helper function to log variable name and tensor value."""
    if torch.is_tensor(tensor):
        if tensor.numel() == 1:
            log_file.write(f"{name}: {tensor.item():.12e}\n")
        else:
            log_file.write(f"{name}: {tensor.detach().numpy()}\n")
    else:
        log_file.write(f"{name}: {tensor}\n")
    log_file.flush()

def main():
    """Main function to perform single pixel trace calculation."""
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(OUTPUT_LOG_PATH), exist_ok=True)
    
    # Initialize components with float64 precision
    detector = Detector(device=torch.device("cpu"), dtype=torch.float64)
    crystal = Crystal(device=torch.device("cpu"), dtype=torch.float64)
    
    # Load structure factors for simple cubic
    hkl_file = "simple_cubic.hkl"
    if os.path.exists(hkl_file):
        crystal.load_hkl(hkl_file)
    
    # Simulation parameters (from simple_cubic test case)
    wavelength = 1.0  # Angstroms
    
    with open(OUTPUT_LOG_PATH, 'w') as log_file:
        log_file.write("="*80 + "\n")
        log_file.write("Single Pixel Trace Debugging Log\n")
        log_file.write("nanoBragg PyTorch Implementation\n")
        log_file.write("="*80 + "\n\n")
        
        log_file.write(f"Target Pixel: (slow={TARGET_S_PIXEL}, fast={TARGET_F_PIXEL})\n")
        log_file.write(f"Test Case: simple_cubic\n")
        log_file.write(f"Wavelength: {wavelength} Angstroms\n")
        log_file.write(f"Precision: {detector.dtype}\n\n")
        
        # Step 1: Log wavelength
        log_variable("Wavelength (Å)", torch.tensor(wavelength), log_file)
        
        # Step 2: Get pixel coordinates
        pixel_coords_full = detector.get_pixel_coords()
        log_file.write(f"\nPixel coordinates tensor shape: {pixel_coords_full.shape}\n")
        
        # Step 3: Extract target pixel coordinate
        pixel_coord_target = pixel_coords_full[TARGET_S_PIXEL, TARGET_F_PIXEL]
        log_variable("Pixel Coordinate (Å)", pixel_coord_target, log_file)
        
        # Step 4: Use pixel coordinates already in Angstroms and calculate diffracted beam direction (unit vector)
        # Detector.get_pixel_coords() already returns coordinates in Angstroms
        pixel_coord_angstroms = pixel_coord_target
        log_variable("Pixel Coordinate (Å)", pixel_coord_angstroms, log_file)
        
        # diffracted_beam = pixel_coord / |pixel_coord|
        diffracted_beam, pixel_distance = unitize(pixel_coord_angstroms)
        log_variable("Diffracted Beam (unit vector)", diffracted_beam, log_file)
        log_variable("Pixel Distance (Å)", pixel_distance, log_file)
        
        # Step 5: Define incident beam direction (unit vector)
        # For parallel beam along +X axis: [1, 0, 0]
        incident_beam = torch.tensor([1.0, 0.0, 0.0], dtype=detector.dtype)
        log_variable("Incident Beam (unit vector)", incident_beam, log_file)
        
        # Step 6: Calculate scattering vector q
        # q = (2π/λ) * (diffracted - incident)
        two_pi_by_lambda = 2.0 * torch.pi / wavelength
        k_in = two_pi_by_lambda * incident_beam
        k_out = two_pi_by_lambda * diffracted_beam
        q = k_out - k_in
        log_variable("Wave Vector k (Å⁻¹)", torch.tensor(two_pi_by_lambda), log_file)
        log_variable("Scattering Vector q (Å⁻¹)", q, log_file)
        
        # Step 7: Calculate fractional Miller indices
        # h = q · a*, k = q · b*, l = q · c*
        h_frac = dot_product(q, crystal.a_star)
        k_frac = dot_product(q, crystal.b_star)
        l_frac = dot_product(q, crystal.c_star)
        hkl_frac = torch.stack([h_frac, k_frac, l_frac])
        log_variable("Fractional Miller Index h,k,l", hkl_frac, log_file)
        
        # Step 8: Calculate nearest integer Miller indices
        h0 = torch.round(h_frac).int()
        k0 = torch.round(k_frac).int()
        l0 = torch.round(l_frac).int()
        hkl_int = torch.stack([h0.float(), k0.float(), l0.float()])
        log_variable("Nearest Integer h₀,k₀,l₀", hkl_int, log_file)
        
        # Step 9: Look up structure factor F_cell
        F_cell = crystal.get_structure_factor(h0, k0, l0)
        log_variable("F_cell", F_cell, log_file)
        
        # Step 10: Calculate lattice factor F_latt using sincg functions
        # F_latt = F_cell * sincg(h-h0, Na) * sincg(k-k0, Nb) * sincg(l-l0, Nc)
        from nanobrag_torch.utils.physics import sincg
        
        dh = h_frac - h0.float()
        dk = k_frac - k0.float()
        dl = l_frac - l0.float()
        
        sincg_h = sincg(dh, crystal.N_cells_a)
        sincg_k = sincg(dk, crystal.N_cells_b)
        sincg_l = sincg(dl, crystal.N_cells_c)
        
        log_variable("Δh (h - h₀)", dh, log_file)
        log_variable("Δk (k - k₀)", dk, log_file)
        log_variable("Δl (l - l₀)", dl, log_file)
        log_variable("sincg(Δh, Na)", sincg_h, log_file)
        log_variable("sincg(Δk, Nb)", sincg_k, log_file)
        log_variable("sincg(Δl, Nc)", sincg_l, log_file)
        
        F_latt = F_cell * sincg_h * sincg_k * sincg_l
        log_variable("F_latt", F_latt, log_file)
        
        # Step 11: Calculate raw intensity
        # I = |F_latt|²
        raw_intensity = torch.abs(F_latt) ** 2
        log_variable("Raw Intensity", raw_intensity, log_file)
        
        # Step 12: Apply physical scaling factors
        # Physical constants (from nanoBragg.c ~line 240)
        r_e_sqr = 7.94e-26  # classical electron radius squared (cm²)
        fluence = 125932015286227086360700780544.0  # photons per square meter (C default)
        polarization = 1.0  # unpolarized beam
        
        # Solid angle correction
        airpath = pixel_distance
        close_distance = detector.distance
        pixel_size = detector.pixel_size
        omega_pixel = (pixel_size * pixel_size) / (airpath * airpath) * close_distance / airpath
        log_variable("Solid Angle (steradians)", omega_pixel, log_file)
        
        # Convert r_e_sqr from cm² to Å²
        r_e_sqr_angstrom = r_e_sqr * (1e8 * 1e8)
        log_variable("r_e_sqr (Å²)", torch.tensor(r_e_sqr_angstrom), log_file)
        
        # Convert fluence from photons/m² to photons/Å²
        fluence_angstrom = fluence / (1e10 * 1e10)
        log_variable("fluence (photons/Å²)", torch.tensor(fluence_angstrom), log_file)
        
        # Final physical intensity with consistent units
        physical_intensity = raw_intensity * omega_pixel * r_e_sqr_angstrom * fluence_angstrom * polarization
        log_variable("Final Physical Intensity", physical_intensity, log_file)
        
        # Additional debugging information
        log_file.write(f"\n" + "="*80 + "\n")
        log_file.write("Additional Debugging Information\n")
        log_file.write("="*80 + "\n")
        
        # Crystal parameters
        log_file.write(f"Crystal unit cell: {crystal.cell_a} x {crystal.cell_b} x {crystal.cell_c} Å\n")
        log_file.write(f"Crystal size: {crystal.N_cells_a} x {crystal.N_cells_b} x {crystal.N_cells_c} cells\n")
        log_variable("a_star", crystal.a_star, log_file)
        log_variable("b_star", crystal.b_star, log_file)
        log_variable("c_star", crystal.c_star, log_file)
        
        # Detector parameters
        log_file.write(f"Detector distance: {detector.distance} Å\n")
        log_file.write(f"Pixel size: {detector.pixel_size} Å\n")
        log_file.write(f"Detector size: {detector.spixels} x {detector.fpixels} pixels\n")
        log_file.write(f"Beam center: ({detector.beam_center_s}, {detector.beam_center_f}) pixels\n")
        log_variable("Fast detector axis", detector.fdet_vec, log_file)
        log_variable("Slow detector axis", detector.sdet_vec, log_file)
        log_variable("Normal detector axis", detector.odet_vec, log_file)
        
        log_file.write(f"\nTrace completed successfully.\n")

if __name__ == "__main__":
    main()