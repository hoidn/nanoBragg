#!/usr/bin/env python3
"""
Detailed trace script for AT-PARALLEL-012 simple_cubic test.

This script identifies the strongest peak in the golden data and generates
a detailed PyTorch trace to identify the 0.5% discrepancy (correlation 0.9946 vs target 0.9995).

Usage:
    KMP_DUPLICATE_LIB_OK=TRUE python scripts/trace_at012_simple_cubic.py
"""

import os
import struct
import sys
from pathlib import Path

import numpy as np
import torch

# Set environment variable for MKL library conflicts
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nanobrag_torch.config import (
    DetectorConfig,
    DetectorConvention,
    DetectorPivot,
    CrystalConfig,
    BeamConfig,
)
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator


def load_golden_float_image(filename: str, shape: tuple) -> np.ndarray:
    """Load a binary float image from golden data."""
    with open(filename, 'rb') as f:
        data = f.read()
        n_floats = len(data) // 4
        assert n_floats == shape[0] * shape[1], f"Expected {shape[0]*shape[1]} floats, got {n_floats}"
        floats = struct.unpack(f'{n_floats}f', data)
        return np.array(floats).reshape(shape)


def main():
    # Load golden data
    golden_file = Path(__file__).parent.parent / "tests" / "golden_data" / "simple_cubic.bin"
    print(f"Loading golden data from: {golden_file}")
    golden_image = load_golden_float_image(str(golden_file), (1024, 1024))

    # Find strongest peak (use argmax for single strongest pixel)
    peak_idx = np.argmax(golden_image)
    peak_s = peak_idx // 1024
    peak_f = peak_idx % 1024
    peak_intensity_golden = golden_image[peak_s, peak_f]

    print(f"\n{'='*80}")
    print(f"STRONGEST PEAK IDENTIFICATION")
    print(f"{'='*80}")
    print(f"Peak location (slow, fast): ({peak_s}, {peak_f})")
    print(f"Peak intensity (golden):    {peak_intensity_golden:.12e}")
    print(f"{'='*80}\n")

    # Setup PyTorch configuration matching test
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0
    )

    detector_config = DetectorConfig(
        spixels=1024,
        fpixels=1024,
        pixel_size_mm=0.1,
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM
    )

    beam_config = BeamConfig(
        wavelength_A=6.2
    )

    # Create simulator
    print("Initializing PyTorch simulator...")
    crystal = Crystal(crystal_config)
    detector = Detector(detector_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)

    # Run full simulation to get PyTorch image
    print("Running full PyTorch simulation...")
    pytorch_image = simulator.run().cpu().numpy()
    peak_intensity_pytorch = pytorch_image[peak_s, peak_f]

    print(f"\n{'='*80}")
    print(f"INTENSITY COMPARISON AT PEAK")
    print(f"{'='*80}")
    print(f"Golden intensity:  {peak_intensity_golden:.12e}")
    print(f"PyTorch intensity: {peak_intensity_pytorch:.12e}")
    print(f"Ratio (Py/C):      {peak_intensity_pytorch/peak_intensity_golden:.12f}")
    print(f"Difference:        {abs(peak_intensity_pytorch - peak_intensity_golden):.12e}")
    print(f"Relative error:    {abs(peak_intensity_pytorch - peak_intensity_golden)/peak_intensity_golden*100:.6f}%")
    print(f"{'='*80}\n")

    # Get detailed trace for this pixel
    print(f"\n{'='*80}")
    print(f"DETAILED PYTORCH TRACE FOR PIXEL ({peak_s}, {peak_f})")
    print(f"{'='*80}\n")

    # Get detector geometry for this pixel
    pixel_coords_meters = detector.get_pixel_coords()
    pix_coord = pixel_coords_meters[peak_s, peak_f]
    print(f"DETECTOR GEOMETRY:")
    print(f"  pix0_vector (m):     [{detector.pix0_vector[0]:.15e}, {detector.pix0_vector[1]:.15e}, {detector.pix0_vector[2]:.15e}]")
    print(f"  fdet_vec:            [{detector.fdet_vec[0]:.15e}, {detector.fdet_vec[1]:.15e}, {detector.fdet_vec[2]:.15e}]")
    print(f"  sdet_vec:            [{detector.sdet_vec[0]:.15e}, {detector.sdet_vec[1]:.15e}, {detector.sdet_vec[2]:.15e}]")
    print(f"  odet_vec:            [{detector.odet_vec[0]:.15e}, {detector.odet_vec[1]:.15e}, {detector.odet_vec[2]:.15e}]")
    print(f"  beam_center_s (pix): {detector.beam_center_s:.15e}")
    print(f"  beam_center_f (pix): {detector.beam_center_f:.15e}")
    print(f"  pixel_size (m):      {detector.pixel_size:.15e}")
    print(f"  distance (m):        {detector.distance:.15e}")
    print(f"  close_distance (m):  {detector.close_distance:.15e}")
    print(f"\nPIXEL COORDINATES:")
    print(f"  Pixel ({peak_s}, {peak_f}) position (m): [{pix_coord[0]:.15e}, {pix_coord[1]:.15e}, {pix_coord[2]:.15e}]")
    pix_coord_ang = pix_coord * 1e10
    print(f"  Pixel position (Å):                      [{pix_coord_ang[0]:.6f}, {pix_coord_ang[1]:.6f}, {pix_coord_ang[2]:.6f}]")

    # Calculate airpath and omega
    airpath_m = torch.sqrt(torch.sum(pix_coord * pix_coord))
    print(f"  Airpath (m):                             {airpath_m:.15e}")

    if detector.config.point_pixel:
        omega_pixel = 1.0 / (airpath_m * airpath_m)
    else:
        omega_pixel = (detector.pixel_size * detector.pixel_size) / (airpath_m * airpath_m) * detector.close_distance / airpath_m
    print(f"  Omega (sr):                              {omega_pixel:.15e}")
    print(f"  Obliquity factor:                        {detector.close_distance/airpath_m:.15e}")

    # Get crystal vectors
    print(f"\nCRYSTAL LATTICE VECTORS:")
    print(f"  a (Å):     [{crystal.a[0]:.15e}, {crystal.a[1]:.15e}, {crystal.a[2]:.15e}]")
    print(f"  b (Å):     [{crystal.b[0]:.15e}, {crystal.b[1]:.15e}, {crystal.b[2]:.15e}]")
    print(f"  c (Å):     [{crystal.c[0]:.15e}, {crystal.c[1]:.15e}, {crystal.c[2]:.15e}]")
    print(f"  a* (Å⁻¹):  [{crystal.a_star[0]:.15e}, {crystal.a_star[1]:.15e}, {crystal.a_star[2]:.15e}]")
    print(f"  b* (Å⁻¹):  [{crystal.b_star[0]:.15e}, {crystal.b_star[1]:.15e}, {crystal.b_star[2]:.15e}]")
    print(f"  c* (Å⁻¹):  [{crystal.c_star[0]:.15e}, {crystal.c_star[1]:.15e}, {crystal.c_star[2]:.15e}]")
    print(f"  Volume (Å³): {crystal.V:.15e}")

    # Calculate scattering vector
    print(f"\nSCATTERING VECTOR CALCULATION:")
    pixel_mag_ang = torch.sqrt(torch.sum(pix_coord_ang * pix_coord_ang))
    diffracted_unit = pix_coord_ang / pixel_mag_ang
    incident_unit = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)  # MOSFLM beam direction
    wavelength = 6.2  # Angstroms
    scattering_vec = (diffracted_unit - incident_unit) / wavelength

    print(f"  Diffracted unit vector: [{diffracted_unit[0]:.15e}, {diffracted_unit[1]:.15e}, {diffracted_unit[2]:.15e}]")
    print(f"  Incident unit vector:   [{incident_unit[0]:.15e}, {incident_unit[1]:.15e}, {incident_unit[2]:.15e}]")
    print(f"  Scattering vector (Å⁻¹): [{scattering_vec[0]:.15e}, {scattering_vec[1]:.15e}, {scattering_vec[2]:.15e}]")
    print(f"  |S| (Å⁻¹):              {torch.norm(scattering_vec):.15e}")

    # Calculate Miller indices using real-space vectors (correct crystallographic convention)
    print(f"\nMILLER INDEX CALCULATION (using real-space vectors):")
    h = torch.dot(scattering_vec, crystal.a)
    k = torch.dot(scattering_vec, crystal.b)
    l = torch.dot(scattering_vec, crystal.c)
    h0 = round(h.item())
    k0 = round(k.item())
    l0 = round(l.item())

    print(f"  h (fractional):  {h:.15e}")
    print(f"  k (fractional):  {k:.15e}")
    print(f"  l (fractional):  {l:.15e}")
    print(f"  h0 (rounded):    {h0}")
    print(f"  k0 (rounded):    {k0}")
    print(f"  l0 (rounded):    {l0}")

    # Calculate F_cell
    F_cell = crystal.get_structure_factor(
        torch.tensor([[h0]], dtype=torch.float64),
        torch.tensor([[k0]], dtype=torch.float64),
        torch.tensor([[l0]], dtype=torch.float64)
    ).item()
    print(f"  F_cell:          {F_cell:.15e}")

    # Calculate F_latt components (SQUARE shape)
    print(f"\nLATTICE STRUCTURE FACTOR (SQUARE shape):")
    from nanobrag_torch.utils.physics import sincg
    Na = crystal.N_cells_a
    Nb = crystal.N_cells_b
    Nc = crystal.N_cells_c

    F_latt_a = sincg(torch.pi * (h - h0), Na).item()
    F_latt_b = sincg(torch.pi * (k - k0), Nb).item()
    F_latt_c = sincg(torch.pi * (l - l0), Nc).item()
    F_latt = F_latt_a * F_latt_b * F_latt_c

    print(f"  N_cells: ({Na}, {Nb}, {Nc})")
    print(f"  F_latt_a: {F_latt_a:.15e}")
    print(f"  F_latt_b: {F_latt_b:.15e}")
    print(f"  F_latt_c: {F_latt_c:.15e}")
    print(f"  F_latt:   {F_latt:.15e}")

    # Calculate intensity before scaling
    print(f"\nINTENSITY CALCULATION:")
    I_before_steps = (F_cell * F_latt) ** 2
    print(f"  I_before_steps = (F_cell × F_latt)²: {I_before_steps:.15e}")

    # Normalization factors
    phi_steps = 1
    mosaic_domains = 1
    oversample = 1
    steps = phi_steps * mosaic_domains * oversample * oversample
    print(f"  steps (phi × mosaic × oversample²): {steps}")

    I_normalized = I_before_steps / steps
    print(f"  I_normalized = I / steps: {I_normalized:.15e}")

    # Apply omega
    I_with_omega = I_normalized * omega_pixel
    print(f"  I_with_omega = I × ω: {I_with_omega:.15e}")

    # Polarization factor (approximate - need full calculation)
    from nanobrag_torch.utils.physics import polarization_factor
    kahn_factor = beam_config.polarization_factor
    polarization_axis = torch.tensor(beam_config.polarization_axis, dtype=torch.float64)

    incident_3d = incident_unit.unsqueeze(0)
    diffracted_3d = diffracted_unit.unsqueeze(0)
    polar_factor = polarization_factor(kahn_factor, incident_3d, diffracted_3d, polarization_axis).item()
    print(f"  Polarization factor: {polar_factor:.15e}")

    I_with_polar = I_with_omega * polar_factor
    print(f"  I_with_polar = I × ω × polar: {I_with_polar:.15e}")

    # Apply physical constants
    r_e_sqr = 7.94079248018965e-30
    fluence = beam_config.fluence
    I_final = I_with_polar * r_e_sqr * fluence

    print(f"  r_e² (m²):           {r_e_sqr:.15e}")
    print(f"  fluence (photons/m²): {fluence:.15e}")
    print(f"  I_final = I × r_e² × fluence: {I_final:.15e}")

    # Compare with actual PyTorch result
    print(f"\n{'='*80}")
    print(f"FINAL COMPARISON")
    print(f"{'='*80}")
    print(f"  Calculated intensity: {I_final:.15e}")
    print(f"  PyTorch intensity:    {peak_intensity_pytorch:.15e}")
    print(f"  Golden intensity:     {peak_intensity_golden:.15e}")
    print(f"  Calc vs PyTorch ratio: {I_final/peak_intensity_pytorch:.12f}")
    print(f"  Calc vs Golden ratio:  {I_final/peak_intensity_golden:.12f}")
    print(f"{'='*80}\n")

    # Summary statistics for full image
    print(f"\n{'='*80}")
    print(f"FULL IMAGE STATISTICS")
    print(f"{'='*80}")
    from scipy.stats import pearsonr
    corr, _ = pearsonr(golden_image.flatten(), pytorch_image.flatten())

    print(f"Correlation coefficient: {corr:.12f}")
    print(f"Target correlation:      0.9995")
    print(f"Shortfall:               {(0.9995 - corr)*100:.6f}%")

    # Compute RMSE
    rmse = np.sqrt(np.mean((golden_image - pytorch_image)**2))
    max_diff = np.max(np.abs(golden_image - pytorch_image))
    mean_golden = np.mean(golden_image)

    print(f"\nRMSE:                    {rmse:.12e}")
    print(f"Max absolute difference: {max_diff:.12e}")
    print(f"Mean golden intensity:   {mean_golden:.12e}")
    print(f"RMSE / mean:             {rmse/mean_golden*100:.6f}%")
    print(f"{'='*80}\n")

    # HYPOTHESIS GENERATION
    print(f"\n{'='*80}")
    print(f"HYPOTHESIS FOR 0.5% DISCREPANCY")
    print(f"{'='*80}")

    # Check if it's a systematic scale factor
    scale_factor = peak_intensity_golden / peak_intensity_pytorch
    print(f"\nScale factor (Golden/PyTorch) at peak: {scale_factor:.12f}")

    # Check a few more bright pixels
    bright_threshold = np.percentile(golden_image, 99.9)
    bright_mask = golden_image > bright_threshold
    bright_golden = golden_image[bright_mask]
    bright_pytorch = pytorch_image[bright_mask]
    bright_ratios = bright_golden / bright_pytorch

    print(f"\nBright pixel statistics (top 0.1%):")
    print(f"  Number of bright pixels: {len(bright_golden)}")
    print(f"  Mean ratio (Golden/PyTorch): {np.mean(bright_ratios):.12f}")
    print(f"  Std dev of ratio:            {np.std(bright_ratios):.12f}")
    print(f"  Min ratio:                   {np.min(bright_ratios):.12f}")
    print(f"  Max ratio:                   {np.max(bright_ratios):.12f}")

    # Possible causes
    print(f"\nPOSSIBLE CAUSES:")
    causes = [
        ("1. Systematic scale factor error",
         f"All pixels scaled by {scale_factor:.6f} suggests a constant multiplicative error"),
        ("2. Solid angle calculation (omega)",
         f"Check obliquity factor and close_distance calculation"),
        ("3. Polarization factor",
         f"Verify kahn_factor and polarization axis orientation"),
        ("4. Physical constants (r_e², fluence)",
         f"Verify exact values match C code constants"),
        ("5. Pixel coordinate calculation",
         f"Check pix0_vector and detector basis vector calculations"),
        ("6. MOSFLM convention +0.5 pixel offset",
         f"Verify beam_center offset is correctly applied"),
    ]

    for i, (cause, detail) in enumerate(causes, 1):
        print(f"\n  {cause}")
        print(f"    → {detail}")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()