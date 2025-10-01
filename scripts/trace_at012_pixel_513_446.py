#!/usr/bin/env python3
"""
PyTorch Trace for AT-PARALLEL-012 simple_cubic

Generate detailed trace for pixel (513, 446) - identified as strong off-center peak
This matches C trace instrumentation for parallel comparison.

Variables logged (matching C trace):
- pix0_vector
- fdet_vec, sdet_vec, odet_vec (basis vectors)
- pixel_coords (position in meters)
- R (airpath distance)
- omega (solid angle)
- close_distance, obliquity_factor
- incident vector (k_in)
- diffracted vector (k_out)
- scattering vector (S)
- Miller indices (h, k, l - float and rounded)
- F_cell (structure factor)
- F_latt (lattice shape factor components)
- polarization factor
- absorption (capture_fraction)
- final intensity
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
from pathlib import Path
import numpy as np
import torch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


def main():
    # Target pixel - strong off-center peak
    target_s, target_f = 513, 446

    print("=" * 80)
    print(f"PYTORCH TRACE: AT-PARALLEL-012 simple_cubic pixel ({target_s}, {target_f})")
    print("=" * 80)

    # Setup configuration (matching test)
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

    # Instantiate models
    crystal = Crystal(crystal_config)
    detector = Detector(detector_config)

    print("\n1. DETECTOR GEOMETRY")
    print("-" * 80)
    pix0 = detector.pix0_vector.cpu().numpy()
    fdet = detector.fdet_vec.cpu().numpy()
    sdet = detector.sdet_vec.cpu().numpy()
    odet = detector.odet_vec.cpu().numpy()

    print(f"pix0_vector [m]: [{pix0[0]:.10e}, {pix0[1]:.10e}, {pix0[2]:.10e}]")
    print(f"fdet_vec: [{fdet[0]:.10e}, {fdet[1]:.10e}, {fdet[2]:.10e}]")
    print(f"sdet_vec: [{sdet[0]:.10e}, {sdet[1]:.10e}, {sdet[2]:.10e}]")
    print(f"odet_vec: [{odet[0]:.10e}, {odet[1]:.10e}, {odet[2]:.10e}]")
    print(f"distance [m]: {detector.distance:.10e}")
    print(f"close_distance [m]: {detector.close_distance:.10e}")
    print(f"pixel_size [m]: {detector.pixel_size:.10e}")
    print(f"r_factor: {detector.r_factor:.10e}")

    print(f"\n2. PIXEL COORDINATE")
    print("-" * 80)
    pixel_coords = detector.get_pixel_coords()
    pixel_coord = pixel_coords[target_s, target_f].cpu().numpy()

    print(f"Pixel: ({target_s}, {target_f})")
    print(f"Pixel coordinate [m]: [{pixel_coord[0]:.10e}, {pixel_coord[1]:.10e}, {pixel_coord[2]:.10e}]")

    # Convert to Angstroms for physics
    pixel_coord_ang = pixel_coord * 1e10
    print(f"Pixel coordinate [Å]: [{pixel_coord_ang[0]:.10e}, {pixel_coord_ang[1]:.10e}, {pixel_coord_ang[2]:.10e}]")

    # Distance
    R_m = np.linalg.norm(pixel_coord)
    R_ang = R_m * 1e10
    print(f"R (airpath) [m]: {R_m:.10e}")
    print(f"R (airpath) [Å]: {R_ang:.10e}")

    # Unit diffracted vector
    diffracted_unit = pixel_coord / R_m
    print(f"diffracted (unit): [{diffracted_unit[0]:.10e}, {diffracted_unit[1]:.10e}, {diffracted_unit[2]:.10e}]")

    print(f"\n3. SOLID ANGLE (OMEGA)")
    print("-" * 80)
    omega = (detector.pixel_size ** 2 / R_m ** 2) * (detector.close_distance / R_m)
    print(f"omega (area formula): {omega:.10e} sr")
    print(f"omega (point-pixel): {1.0 / (R_m ** 2):.10e} sr")

    # Obliquity factor
    obliquity = np.dot(diffracted_unit, odet)
    print(f"obliquity_factor (d·o): {obliquity:.10e}")

    print(f"\n4. INCIDENT BEAM & SCATTERING VECTOR")
    print("-" * 80)
    # MOSFLM: beam along +X
    incident_direction = np.array([1.0, 0.0, 0.0])
    print(f"incident_direction: [{incident_direction[0]:.10e}, {incident_direction[1]:.10e}, {incident_direction[2]:.10e}]")

    wavelength_ang = beam_config.wavelength_A
    print(f"wavelength [Å]: {wavelength_ang:.10e}")

    # Scattering vector: S = (diffracted - incident) / λ
    scattering_vector = (diffracted_unit - incident_direction) / wavelength_ang
    S_mag = np.linalg.norm(scattering_vector)

    print(f"Scattering vector S [Å⁻¹]: [{scattering_vector[0]:.10e}, {scattering_vector[1]:.10e}, {scattering_vector[2]:.10e}]")
    print(f"|S|: {S_mag:.10e} Å⁻¹")
    print(f"stol (sin(θ)/λ): {S_mag / 2:.10e}")

    print(f"\n5. MILLER INDICES")
    print("-" * 80)
    # Get real-space vectors (no phi rotation for simple cubic at phi=0)
    real_vecs = crystal.get_real_vectors()
    a_vec = real_vecs[0].cpu().numpy()
    b_vec = real_vecs[1].cpu().numpy()
    c_vec = real_vecs[2].cpu().numpy()

    print(f"a_vec [Å]: [{a_vec[0]:.10e}, {a_vec[1]:.10e}, {a_vec[2]:.10e}]")
    print(f"b_vec [Å]: [{b_vec[0]:.10e}, {b_vec[1]:.10e}, {b_vec[2]:.10e}]")
    print(f"c_vec [Å]: [{c_vec[0]:.10e}, {c_vec[1]:.10e}, {c_vec[2]:.10e}]")

    # Miller indices: h = S · a, k = S · b, l = S · c
    h_float = np.dot(scattering_vector, a_vec)
    k_float = np.dot(scattering_vector, b_vec)
    l_float = np.dot(scattering_vector, c_vec)

    print(f"h (float): {h_float:.10e}")
    print(f"k (float): {k_float:.10e}")
    print(f"l (float): {l_float:.10e}")

    # Nearest integer (ceil(x - 0.5))
    h_int = int(np.ceil(h_float - 0.5))
    k_int = int(np.ceil(k_float - 0.5))
    l_int = int(np.ceil(l_float - 0.5))

    print(f"h (int): {h_int}")
    print(f"k (int): {k_int}")
    print(f"l (int): {l_int}")

    # Fractional parts
    h_frac = h_float - h_int
    k_frac = k_float - k_int
    l_frac = l_float - l_int

    print(f"Fractional parts: h={h_frac:.10e}, k={k_frac:.10e}, l={l_frac:.10e}")

    print(f"\n6. STRUCTURE FACTOR")
    print("-" * 80)
    # For simple cubic with default_F=100, all F_cell should be 100
    print(f"default_F: {crystal_config.default_F:.10e}")
    print(f"F_cell (expected): {crystal_config.default_F:.10e}")

    print(f"\n7. LATTICE SHAPE FACTOR (SQUARE)")
    print("-" * 80)
    # F_latt = sincg(π·h_frac, Na) · sincg(π·k_frac, Nb) · sincg(π·l_frac, Nc)
    Na, Nb, Nc = crystal_config.N_cells

    def sincg(x, N):
        """Generalized sinc: sin(N*x) / sin(x), with special case for x≈0"""
        if abs(x) < 1e-10:
            return float(N)
        return np.sin(N * x) / np.sin(x)

    F_latt_a = sincg(np.pi * h_frac, Na)
    F_latt_b = sincg(np.pi * k_frac, Nb)
    F_latt_c = sincg(np.pi * l_frac, Nc)
    F_latt = F_latt_a * F_latt_b * F_latt_c

    print(f"Na, Nb, Nc: {Na}, {Nb}, {Nc}")
    print(f"F_latt_a (sincg(π·{h_frac:.6f}, {Na})): {F_latt_a:.10e}")
    print(f"F_latt_b (sincg(π·{k_frac:.6f}, {Nb})): {F_latt_b:.10e}")
    print(f"F_latt_c (sincg(π·{l_frac:.6f}, {Nc})): {F_latt_c:.10e}")
    print(f"F_latt (product): {F_latt:.10e}")

    print(f"\n8. POLARIZATION FACTOR")
    print("-" * 80)
    # Kahn polarization factor
    kahn_factor = beam_config.polarization_factor
    print(f"Kahn factor: {kahn_factor:.10e}")

    # Polarization axis (default +Y for MOSFLM)
    polarization_axis = np.array([0.0, 1.0, 0.0])
    print(f"Polarization axis: [{polarization_axis[0]:.10e}, {polarization_axis[1]:.10e}, {polarization_axis[2]:.10e}]")

    # Calculate polarization factor (from utils/physics.py)
    # polar = 0.5 * (1 + cos²(2θ) - K·cos(2ψ)·sin²(2θ))
    cos_2theta = np.dot(incident_direction, diffracted_unit)
    sin_2theta_sq = 1.0 - cos_2theta ** 2

    # Project incident onto plane perpendicular to scattering
    incident_perp = incident_direction - cos_2theta * diffracted_unit
    incident_perp_mag = np.linalg.norm(incident_perp)

    if incident_perp_mag > 1e-10:
        incident_perp_unit = incident_perp / incident_perp_mag
        cos_2psi = np.dot(polarization_axis, incident_perp_unit)
    else:
        cos_2psi = 0.0

    polar = 0.5 * (1.0 + cos_2theta ** 2 - kahn_factor * cos_2psi * sin_2theta_sq)

    print(f"cos(2θ): {cos_2theta:.10e}")
    print(f"sin²(2θ): {sin_2theta_sq:.10e}")
    print(f"cos(2ψ): {cos_2psi:.10e}")
    print(f"polarization_factor: {polar:.10e}")

    print(f"\n9. ABSORPTION (DETECTOR CAPTURE)")
    print("-" * 80)
    # Check if detector has absorption parameters
    if hasattr(detector_config, 'detector_thick_um') and detector_config.detector_thick_um > 0:
        print(f"detector_thick_um: {detector_config.detector_thick_um}")
        print(f"detector_abs_um: {detector_config.detector_abs_um}")
        print(f"detector_thicksteps: {detector_config.detector_thicksteps}")
        # Would need to calculate parallax and layer fractions here
    else:
        capture_fraction = 1.0
        print(f"No detector absorption (capture_fraction = 1.0)")

    print(f"\n10. FINAL INTENSITY CALCULATION")
    print("-" * 80)

    # Classic electron radius
    r_e_cm = 2.8179403227e-13
    r_e_ang = r_e_cm * 1e8
    r_e_sq = r_e_ang ** 2
    print(f"r_e² [Å²]: {r_e_sq:.10e}")

    # Fluence (default from BeamConfig)
    fluence = beam_config.fluence
    print(f"fluence [photons/Å²]: {fluence:.10e}")

    # Steps (for single source, single phi, no mosaic, oversample=1)
    n_sources = 1
    n_phi = 1
    n_mosaic = 1
    oversample_sq = 1  # auto-selected 1-fold oversampling
    steps = n_sources * n_phi * n_mosaic * oversample_sq
    print(f"steps (normalization): {steps}")

    # Intensity before final scaling
    I_before_scaling = (crystal_config.default_F ** 2) * (F_latt ** 2)
    print(f"I_before_scaling (F²·F_latt²): {I_before_scaling:.10e}")

    # Final intensity
    I_final = r_e_sq * fluence * I_before_scaling * omega * polar / steps
    print(f"I_final: {I_final:.10e}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Pixel: ({target_s}, {target_f})")
    print(f"Miller indices: h={h_int}, k={k_int}, l={l_int}")
    print(f"F_latt: {F_latt:.6e}")
    print(f"Polarization: {polar:.6e}")
    print(f"Omega: {omega:.6e} sr")
    print(f"Final intensity: {I_final:.6e}")

    # Now run full simulation and check actual value
    print("\n" + "=" * 80)
    print("VERIFICATION (Full Simulation)")
    print("=" * 80)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)
    full_image = simulator.run().cpu().numpy()
    actual_intensity = full_image[target_s, target_f]
    print(f"Simulated intensity at ({target_s}, {target_f}): {actual_intensity:.6e}")
    print(f"Trace prediction: {I_final:.6e}")
    print(f"Match: {np.isclose(actual_intensity, I_final, rtol=1e-3)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
