#!/usr/bin/env python3
"""
Custom debugging script for the failing test_at_parallel_025.py::test_maximum_intensity_simple_case

This script reproduces the exact test configuration and compares C vs PyTorch pixel traces
at the locations where maximum intensity is found:
- C max at [34, 34] with value 55,040
- PyTorch max at [33, 33] with value 0.010

Parameters:
- wavelength: 1.0 Å
- cell: 100x100x100 Å, 90°x90°x90°
- N_cells: (1, 1, 1)
- default_F: 100.0
- detector: 64x64 pixels, 0.1mm pixel size, 100mm distance
- detector convention: MOSFLM
"""

import os
import sys
import torch
import numpy as np
import tempfile
from pathlib import Path

# Set required environment variables
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src and scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.utils.geometry import dot_product, unitize

def debug_pytorch_pixel(s_pixel, f_pixel, simulator):
    """Debug a single pixel computation in PyTorch."""
    print(f"\n🔍 PYTORCH TRACE for pixel ({s_pixel}, {f_pixel})")

    # Get pixel coordinates in meters, then convert to Angstroms
    pixel_coords_meters = simulator.detector.get_pixel_coords()
    pixel_coord_meters = pixel_coords_meters[s_pixel, f_pixel]  # Shape: (3,)
    pixel_coord_angstroms = pixel_coord_meters * 1e10

    print(f"TRACE_PY: pixel_coord_meters {pixel_coord_meters[0]:.15g} {pixel_coord_meters[1]:.15g} {pixel_coord_meters[2]:.15g}")
    print(f"TRACE_PY: pixel_coord_angstroms {pixel_coord_angstroms[0]:.15g} {pixel_coord_angstroms[1]:.15g} {pixel_coord_angstroms[2]:.15g}")

    # Calculate diffracted beam unit vector
    pixel_distance = torch.sqrt(torch.sum(pixel_coord_angstroms * pixel_coord_angstroms))
    diffracted_beam_unit = pixel_coord_angstroms / pixel_distance

    print(f"TRACE_PY: pixel_distance_angstroms {pixel_distance:.15g}")
    print(f"TRACE_PY: diffracted_beam_unit {diffracted_beam_unit[0]:.15g} {diffracted_beam_unit[1]:.15g} {diffracted_beam_unit[2]:.15g}")

    # Incident beam direction (MOSFLM convention: +X axis)
    incident_beam_unit = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)

    # Scattering vector
    wavelength = simulator.wavelength
    scattering_vector = (diffracted_beam_unit - incident_beam_unit) / wavelength

    print(f"TRACE_PY: wavelength {wavelength:.15g}")
    print(f"TRACE_PY: incident_beam {incident_beam_unit[0]:.15g} {incident_beam_unit[1]:.15g} {incident_beam_unit[2]:.15g}")
    print(f"TRACE_PY: scattering_vector {scattering_vector[0]:.15g} {scattering_vector[1]:.15g} {scattering_vector[2]:.15g}")

    # Miller indices using real-space vectors
    h = dot_product(scattering_vector, simulator.crystal.a)
    k = dot_product(scattering_vector, simulator.crystal.b)
    l = dot_product(scattering_vector, simulator.crystal.c)

    print(f"TRACE_PY: crystal_a {simulator.crystal.a[0]:.15g} {simulator.crystal.a[1]:.15g} {simulator.crystal.a[2]:.15g}")
    print(f"TRACE_PY: crystal_b {simulator.crystal.b[0]:.15g} {simulator.crystal.b[1]:.15g} {simulator.crystal.b[2]:.15g}")
    print(f"TRACE_PY: crystal_c {simulator.crystal.c[0]:.15g} {simulator.crystal.c[1]:.15g} {simulator.crystal.c[2]:.15g}")
    print(f"TRACE_PY: hkl_frac {h:.15g} {k:.15g} {l:.15g}")

    # Nearest integer indices
    h0 = torch.round(h)
    k0 = torch.round(k)
    l0 = torch.round(l)

    print(f"TRACE_PY: hkl_int {h0:.15g} {k0:.15g} {l0:.15g}")

    # Structure factor
    F_cell = simulator.crystal.get_structure_factor(h0.int(), k0.int(), l0.int())
    print(f"TRACE_PY: F_cell {F_cell:.15g}")

    # Lattice structure factor (using fractional part)
    from nanobrag_torch.utils.physics import sincg

    Na = simulator.crystal.N_cells_a
    Nb = simulator.crystal.N_cells_b
    Nc = simulator.crystal.N_cells_c

    dh = h - h0
    dk = k - k0
    dl = l - l0

    print(f"TRACE_PY: crystal_size {Na} {Nb} {Nc}")
    print(f"TRACE_PY: hkl_frac_delta {dh:.15g} {dk:.15g} {dl:.15g}")

    sincg_h = sincg(torch.pi * dh, Na)
    sincg_k = sincg(torch.pi * dk, Nb)
    sincg_l = sincg(torch.pi * dl, Nc)

    print(f"TRACE_PY: sincg_values {sincg_h:.15g} {sincg_k:.15g} {sincg_l:.15g}")

    F_latt = sincg_h * sincg_k * sincg_l
    print(f"TRACE_PY: F_latt {F_latt:.15g}")

    # Total structure factor and raw intensity
    F_total = F_cell * F_latt
    raw_intensity = F_total * F_total

    print(f"TRACE_PY: F_total {F_total:.15g}")
    print(f"TRACE_PY: raw_intensity {raw_intensity:.15g}")

    # Physical scaling
    r_e_sqr = simulator.r_e_sqr  # meters^2
    fluence = simulator.fluence   # photons/m^2

    # Solid angle calculation
    airpath_m = pixel_distance.item() * 1e-10  # Angstroms to meters
    close_distance_m = simulator.detector.distance  # meters
    pixel_size_m = simulator.detector.pixel_size    # meters

    omega_pixel = (pixel_size_m * pixel_size_m) / (airpath_m * airpath_m) * close_distance_m / airpath_m

    print(f"TRACE_PY: r_e_sqr_m2 {r_e_sqr:.15g}")
    print(f"TRACE_PY: fluence_per_m2 {fluence:.15g}")
    print(f"TRACE_PY: airpath_m {airpath_m:.15g}")
    print(f"TRACE_PY: close_distance_m {close_distance_m:.15g}")
    print(f"TRACE_PY: pixel_size_m {pixel_size_m:.15g}")
    print(f"TRACE_PY: omega_steradians {omega_pixel:.15g}")

    # Final physical intensity
    physical_intensity = raw_intensity * omega_pixel * r_e_sqr * fluence

    print(f"TRACE_PY: final_intensity {physical_intensity:.15g}")

    return physical_intensity.item()

def main():
    """Main debugging function."""
    print("🔬 Starting debug of failing test_at_parallel_025.py")
    print("Configuration: λ=1.0Å, cubic 100Å cell, N=1, 64×64 detector")

    # Exact configuration from failing test
    crystal_config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(1, 1, 1),
        default_F=100.0
    )

    detector_config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=64,
        fpixels=64
    )

    beam_config = BeamConfig(
        wavelength_A=1.0
    )

    # Create PyTorch objects
    crystal = Crystal(crystal_config, beam_config)
    detector = Detector(detector_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)

    print(f"\n📊 Configuration Summary:")
    print(f"Crystal cell: {crystal_config.cell_a}×{crystal_config.cell_b}×{crystal_config.cell_c} Å")
    print(f"Crystal angles: {crystal_config.cell_alpha}×{crystal_config.cell_beta}×{crystal_config.cell_gamma}°")
    print(f"Crystal N_cells: {crystal_config.N_cells}")
    print(f"Default F: {crystal_config.default_F}")
    print(f"Wavelength: {beam_config.wavelength_A} Å")
    print(f"Detector: {detector_config.spixels}×{detector_config.fpixels} pixels")
    print(f"Pixel size: {detector_config.pixel_size_mm} mm")
    print(f"Distance: {detector_config.distance_mm} mm")
    print(f"Convention: {detector_config.detector_convention}")

    # Debug key pixels where maxima were found
    # C max: [34, 34], PyTorch max: [33, 33]

    print("\n" + "="*60)
    print("DEBUGGING C MAXIMUM POSITION [34, 34]")
    print("="*60)
    py_intensity_c_pos = debug_pytorch_pixel(34, 34, simulator)

    print("\n" + "="*60)
    print("DEBUGGING PYTORCH MAXIMUM POSITION [33, 33]")
    print("="*60)
    py_intensity_py_pos = debug_pytorch_pixel(33, 33, simulator)

    # Run full simulation to get actual PyTorch image
    print("\n🏃 Running full PyTorch simulation...")
    pytorch_image = simulator.run()

    print(f"\nPyTorch image statistics:")
    print(f"Shape: {pytorch_image.shape}")
    print(f"Max value: {pytorch_image.max():.6e}")
    print(f"Min value: {pytorch_image.min():.6e}")
    print(f"Value at [34,34]: {pytorch_image[34, 34]:.6e}")
    print(f"Value at [33,33]: {pytorch_image[33, 33]:.6e}")

    # Find actual maximum
    max_val = torch.max(pytorch_image)
    max_positions = (pytorch_image == max_val).nonzero()
    if len(max_positions) > 0:
        max_pos = max_positions[-1]  # Last occurrence
        print(f"Actual PyTorch max: {max_val:.6e} at [{max_pos[0].item()}, {max_pos[1].item()}]")

    print(f"\n📈 Intensity comparison:")
    print(f"Single-pixel PyTorch calc at [34,34]: {py_intensity_c_pos:.6e}")
    print(f"Single-pixel PyTorch calc at [33,33]: {py_intensity_py_pos:.6e}")
    print(f"Full simulation at [34,34]: {pytorch_image[34, 34]:.6e}")
    print(f"Full simulation at [33,33]: {pytorch_image[33, 33]:.6e}")
    print(f"Expected C value at [34,34]: ~55040")

    scale_factor = 55040 / py_intensity_c_pos if py_intensity_c_pos > 0 else float('inf')
    print(f"Scale factor needed: {scale_factor:.2e}")

if __name__ == "__main__":
    main()