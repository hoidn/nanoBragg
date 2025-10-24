#!/usr/bin/env python
"""
Generate PyTorch trace for pixel (368, 262) in AT-PARALLEL-012 (triclinic).
This script traces the full simulation pipeline to find divergence from C code.
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
import torch
import numpy as np

# Add src to path
sys.path.insert(0, '/home/ollie/Documents/nanoBragg/src')

from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.config import BeamConfig, CrystalConfig, DetectorConfig, DetectorConvention
from nanobrag_torch.simulator import Simulator

def trace_pixel(detector, crystal, beam_config, pixel_coords):
    """
    Detailed trace for a single pixel matching C code trace points.

    Args:
        detector: Detector instance
        crystal: Crystal instance
        beam_config: BeamConfig instance
        pixel_coords: (slow, fast) tuple for target pixel
    """
    slow_idx, fast_idx = pixel_coords

    # Get pixel positions in lab frame (meters)
    pixel_positions = detector.get_pixel_coords()
    pixel_pos = pixel_positions[slow_idx, fast_idx].numpy()

    print(f"TRACE_PY: pixel_pos_meters {pixel_pos[0]:.15e} {pixel_pos[1]:.15e} {pixel_pos[2]:.15e}")

    # Calculate distances
    R_distance = np.linalg.norm(pixel_pos)
    print(f"TRACE_PY: R_distance_meters {R_distance:.15e}")

    # Get omega (solid angle) for this pixel
    omega_pixel = detector.get_solid_angle()[slow_idx, fast_idx].item()
    print(f"TRACE_PY: omega_pixel_sr {omega_pixel:.15e}")

    # Close distance (detector distance from sample)
    close_distance = detector.distance  # In meters
    print(f"TRACE_PY: close_distance_meters {close_distance:.15e}")

    # Obliquity factor
    obliquity_factor = close_distance / R_distance
    print(f"TRACE_PY: obliquity_factor {obliquity_factor:.15e}")

    # Diffracted beam unit vector
    diffracted = pixel_pos / R_distance
    print(f"TRACE_PY: diffracted_vec {diffracted[0]:.15e} {diffracted[1]:.15e} {diffracted[2]:.15e}")

    # Incident beam unit vector (along +X axis)
    incident = np.array([1.0, 0.0, 0.0])
    print(f"TRACE_PY: incident_vec {incident[0]:.15e} {incident[1]:.15e} {incident[2]:.15e}")

    # Lambda in meters
    lambda_m = beam_config.wavelength_A * 1e-10
    print(f"TRACE_PY: lambda_meters {lambda_m:.15e}")

    # Scattering vector in 1/Angstrom
    scattering_vec = (diffracted - incident) / lambda_m  # 1/m
    scattering_vec_A_inv = scattering_vec * 1e-10  # Convert to 1/Angstrom
    print(f"TRACE_PY: scattering_vec_A_inv {scattering_vec_A_inv[0]:.15e} {scattering_vec_A_inv[1]:.15e} {scattering_vec_A_inv[2]:.15e}")

    # Get reciprocal vectors from crystal (in 1/Angstrom) using properties
    a_recip = crystal.a_star.numpy()
    b_recip = crystal.b_star.numpy()
    c_recip = crystal.c_star.numpy()

    # Calculate Miller indices (continuous)
    h_float = np.dot(a_recip, scattering_vec_A_inv)
    k_float = np.dot(b_recip, scattering_vec_A_inv)
    l_float = np.dot(c_recip, scattering_vec_A_inv)

    print(f"TRACE_PY: hkl_frac {h_float:.15e} {k_float:.15e} {l_float:.15e}")

    # Round to nearest integer
    h_int = int(np.ceil(h_float - 0.5))
    k_int = int(np.ceil(k_float - 0.5))
    l_int = int(np.ceil(l_float - 0.5))

    print(f"TRACE_PY: hkl_rounded {h_int} {k_int} {l_int}")

    # Calculate F_latt components (lattice shape factor)
    N_a, N_b, N_c = crystal.config.N_cells

    def sincg(x, N):
        """Sinc function matching C code: sin(N*x) / sin(x)"""
        if abs(x) < 1e-10:
            return N
        return np.sin(N * x) / np.sin(x)

    F_latt_a = sincg(np.pi * h_float, N_a) if N_a > 1 else 1.0
    F_latt_b = sincg(np.pi * k_float, N_b) if N_b > 1 else 1.0
    F_latt_c = sincg(np.pi * l_float, N_c) if N_c > 1 else 1.0
    F_latt = F_latt_a * F_latt_b * F_latt_c

    print(f"TRACE_PY: F_latt_a {F_latt_a:.15e}")
    print(f"TRACE_PY: F_latt_b {F_latt_b:.15e}")
    print(f"TRACE_PY: F_latt_c {F_latt_c:.15e}")
    print(f"TRACE_PY: F_latt {F_latt:.15e}")

    # F_cell (structure factor - using default_F)
    F_cell = crystal.config.default_F
    print(f"TRACE_PY: F_cell {F_cell:.15e}")

    # Polarization factor (Kahn factor for unpolarized beam)
    # polar = 1 - sin^2(2theta) * cos^2(azimuth) for unpolarized
    # For polarization_factor = 0.0, use Kahn formula
    polar_vector = np.array([0.0, 0.0, 1.0])  # Z-axis

    # Calculate polarization using Kahn formula
    # P = (1 - (s_out · polar_axis)^2) where s_out is normalized scattering direction
    scattering_norm = (diffracted - incident)
    scattering_norm_mag = np.linalg.norm(scattering_norm)
    s_out = scattering_norm / scattering_norm_mag

    dot_polar = np.dot(s_out, polar_vector)
    polar = 1.0 - dot_polar * dot_polar

    print(f"TRACE_PY: polarization_factor {polar:.15e}")

    # Accumulate intensity (simplified - just one subpixel for comparison)
    I_contribution = F_cell**2 * F_latt**2

    # For full simulation with 2x2 subpixels (oversample=2):
    # This matches C code which does 4 subpixel samples
    I_total = I_contribution * 4  # 4 subpixel samples

    print(f"TRACE_PY: I_before_scaling {I_total:.15e}")

    # Final scaling
    r_e_sqr = 7.94079248018965e-30  # Classical electron radius squared (m^2)
    fluence = beam_config.fluence
    steps = 4  # phi_steps * mos_domains = 1 * 1 = 1, but oversample = 2, so 2*2 = 4

    print(f"TRACE_PY: r_e_sqr {r_e_sqr:.15e}")
    print(f"TRACE_PY: fluence {fluence:.15e}")
    print(f"TRACE_PY: steps {steps}")

    # Final pixel value
    pixel_value = r_e_sqr * fluence * I_total * polar * omega_pixel / steps

    print(f"TRACE_PY: I_pixel_final {pixel_value:.15e}")

def main():
    # AT-PARALLEL-012 triclinic parameters
    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=512,
        fpixels=512,
        beam_center_s=256 + 0.05,  # MOSFLM convention: +0.5px offset
        beam_center_f=256 + 0.05,
        detector_convention=DetectorConvention.MOSFLM
    )

    crystal_config = CrystalConfig(
        cell_a=70.0, cell_b=80.0, cell_c=90.0,
        cell_alpha=75.0, cell_beta=85.0, cell_gamma=95.0,
        misset_deg=(-89.968546, -31.328953, 177.753396),
        N_cells=(5, 5, 5),
        default_F=100.0,
        mosaic_seed=1
    )

    beam_config = BeamConfig(
        wavelength_A=1.0,
        fluence=1.25932015286227e+29,  # From C trace
        polarization_factor=0.0,  # Kahn factor (0.0 = unpolarized)
        nopolar=False
    )

    # Create components
    detector = Detector(detector_config)
    crystal = Crystal(crystal_config)

    print("=== PyTorch Trace for Pixel (368, 262) - AT-PARALLEL-012 ===", file=sys.stderr)
    print(f"Detector: {detector_config.distance_mm}mm, {detector_config.pixel_size_mm}mm/px, ({detector_config.spixels}x{detector_config.fpixels})", file=sys.stderr)
    print(f"Crystal: triclinic {crystal_config.cell_a}x{crystal_config.cell_b}x{crystal_config.cell_c} Å", file=sys.stderr)
    print(f"         α={crystal_config.cell_alpha}° β={crystal_config.cell_beta}° γ={crystal_config.cell_gamma}°", file=sys.stderr)
    print(f"         misset=({crystal_config.misset_deg[0]:.3f}, {crystal_config.misset_deg[1]:.3f}, {crystal_config.misset_deg[2]:.3f})°", file=sys.stderr)
    print(f"Beam: λ={beam_config.wavelength_A}Å, fluence={beam_config.fluence:.6e}", file=sys.stderr)
    print("", file=sys.stderr)

    # Trace specific pixel (slow=368, fast=262)
    trace_pixel(detector, crystal, beam_config, (368, 262))

    # For comparison, run full simulation
    simulator = Simulator(
        crystal=crystal,
        detector=detector,
        beam_config=beam_config
    )

    image = simulator.run()
    pixel_value_full = image[368, 262].item()

    print(f"\nFull simulation pixel value: {pixel_value_full:.15e}", file=sys.stderr)
    print(f"C reference value: 1.382164387435720e+02", file=sys.stderr)
    print(f"Ratio (Py/C): {pixel_value_full / 138.216438743572:.12f}", file=sys.stderr)

if __name__ == '__main__':
    main()