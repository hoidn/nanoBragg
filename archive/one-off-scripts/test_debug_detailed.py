#!/usr/bin/env python3
"""Detailed debug of simulator calculations."""

import torch
import sys
import os
sys.path.insert(0, 'src')

from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.utils.geometry import dot_product

def main():
    print("=== Detailed Simulator Debug ===")
    
    device = torch.device("cpu")
    dtype = torch.float64
    
    crystal = Crystal(device=device, dtype=dtype)
    detector = Detector(device=device, dtype=dtype)
    
    # Create small detector for easy debugging
    detector.spixels = 3
    detector.fpixels = 3
    detector.invalidate_cache()
    
    wavelength = 1.0
    incident_beam_direction = torch.tensor([1.0, 0.0, 0.0], device=device, dtype=dtype)
    
    # Get pixel coordinates
    pixel_coords_angstroms = detector.get_pixel_coords()
    print(f"Pixel coordinates shape: {pixel_coords_angstroms.shape}")
    print(f"Sample coordinates:\n{pixel_coords_angstroms}")
    
    # Calculate diffracted beam unit vectors
    pixel_magnitudes = torch.sqrt(torch.sum(pixel_coords_angstroms * pixel_coords_angstroms, dim=-1, keepdim=True))
    diffracted_beam_unit = pixel_coords_angstroms / pixel_magnitudes
    print(f"Diffracted beam unit vectors:\n{diffracted_beam_unit}")
    
    # Incident beam unit vector
    incident_beam_unit = incident_beam_direction.expand_as(diffracted_beam_unit)
    print(f"Incident beam unit vector:\n{incident_beam_unit}")
    
    # Scattering vector
    scattering_vector = (diffracted_beam_unit - incident_beam_unit) / wavelength
    print(f"Scattering vector:\n{scattering_vector}")
    
    # Miller indices
    h = dot_product(scattering_vector, crystal.a_star.view(1, 1, 3))
    k = dot_product(scattering_vector, crystal.b_star.view(1, 1, 3))
    l = dot_product(scattering_vector, crystal.c_star.view(1, 1, 3))
    
    print(f"Miller indices h:\n{h}")
    print(f"Miller indices k:\n{k}")
    print(f"Miller indices l:\n{l}")
    
    # Integer indices
    h0 = torch.round(h)
    k0 = torch.round(k)
    l0 = torch.round(l)
    
    print(f"Nearest integer h0:\n{h0}")
    print(f"Nearest integer k0:\n{k0}")
    print(f"Nearest integer l0:\n{l0}")
    
    # Fractional differences
    delta_h = h - h0
    delta_k = k - k0  
    delta_l = l - l0
    
    print(f"Delta h:\n{delta_h}")
    print(f"Delta k:\n{delta_k}")
    print(f"Delta l:\n{delta_l}")

if __name__ == "__main__":
    main()