#!/usr/bin/env python3
"""Generate PyTorch trace for simple_cubic at pixel (513, 446) - a strong peak."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
import numpy as np
import torch
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorPivot
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector, DetectorConvention
from nanobrag_torch.simulator import Simulator

def main():
    # Target pixel (513, 446) - from analysis showing C=92.72, Py=100.29
    target_s = 513
    target_f = 446

    print(f"=== Generating PyTorch Trace for Pixel ({target_s}, {target_f}) ===\n")

    # Setup PyTorch configuration (matching test)
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

    # Build models
    crystal = Crystal(crystal_config)
    detector = Detector(detector_config)

    # Get detector geometry for this pixel
    pixel_coords = detector.get_pixel_coords()  # (spixels, fpixels, 3)
    pix_vec = pixel_coords[target_s, target_f, :]
    print(f"pix0_vector (meters): {detector.pix0_vector}")
    print(f"fdet_vec: {detector.fdet_vec}")
    print(f"sdet_vec: {detector.sdet_vec}")
    print(f"pixel_coords[{target_s},{target_f}]: {pix_vec}")

    # Get beam/sample geometry
    print(f"\nIncident beam direction: {[1.0, 0.0, 0.0]}")
    print(f"Wavelength: {beam_config.wavelength_A} Å")

    # Get diffracted direction
    diffracted = pix_vec / torch.norm(pix_vec)
    print(f"Diffracted direction (unit): {diffracted}")

    # Scattering vector S = k_out - k_in where k = 2π/λ
    incident = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
    k_magnitude = 2 * np.pi / beam_config.wavelength_A  # 1/Å
    k_in = incident * k_magnitude
    k_out = diffracted * k_magnitude
    S = k_out - k_in  # 1/Å (converting diffracted from m to dimensionless unit vector)
    print(f"\nk_in (2π/λ): {k_in}")
    print(f"k_out (2π/λ): {k_out}")
    print(f"Scattering vector S (1/Å): {S}")

    # Get rotated lattice vectors - returns ((a,b,c), (a*,b*,c*))
    real_vecs, recip_vecs = crystal.get_rotated_real_vectors(crystal_config)
    rot_a, rot_b, rot_c = real_vecs
    rot_a_star, rot_b_star, rot_c_star = recip_vecs

    # Squeeze batch dimensions for dot products
    rot_a = rot_a.squeeze()
    rot_b = rot_b.squeeze()
    rot_c = rot_c.squeeze()
    rot_a_star = rot_a_star.squeeze()
    rot_b_star = rot_b_star.squeeze()
    rot_c_star = rot_c_star.squeeze()

    print(f"\nRotated real vectors (Å):")
    print(f"  a: {rot_a}")
    print(f"  b: {rot_b}")
    print(f"  c: {rot_c}")

    print(f"\nRotated reciprocal vectors (1/Å):")
    print(f"  a*: {rot_a_star}")
    print(f"  b*: {rot_b_star}")
    print(f"  c*: {rot_c_star}")

    # Compute Miller indices (h,k,l) via S · lattice_vectors
    # Use real space vectors per project convention (|G| = 1/d)
    # S is already in 1/Å
    h_float = torch.dot(S, rot_a)
    k_float = torch.dot(S, rot_b)
    l_float = torch.dot(S, rot_c)

    h_int = torch.round(h_float).long()
    k_int = torch.round(k_float).long()
    l_int = torch.round(l_float).long()

    print(f"\nMiller indices (float): h={h_float:.6f}, k={k_float:.6f}, l={l_float:.6f}")
    print(f"Miller indices (int): h={h_int}, k={k_int}, l={l_int}")

    # Get structure factor (using default_F)
    F_cell = crystal_config.default_F
    print(f"\nStructure factor F_cell: {F_cell}")

    # Lattice shape factor F_latt (for N=5x5x5)
    # This is computed in the simulator but we can show the formula
    print(f"\nLattice shape factor F_latt: computed from sinc3({h_float}, {k_float}, {l_float}, Na=5, Nb=5, Nc=5)")

    # Get physical constants
    r_e = 2.8179403262e-15  # meters (classical electron radius)
    print(f"\nClassical electron radius r_e: {r_e:.6e} m")

    # Omega (solid angle)
    R = torch.norm(pix_vec)
    pixel_size_m = detector_config.pixel_size_mm * 1e-3
    close_distance_m = detector_config.distance_mm * 1e-3
    omega = (pixel_size_m**2 * close_distance_m) / R**3
    print(f"\nR (airpath): {R:.6f} m")
    print(f"close_distance: {close_distance_m:.6f} m")
    print(f"pixel_size: {pixel_size_m:.6f} m")
    print(f"omega: {omega:.6e} sr")

    # Fluence (default from beam_config)
    fluence = beam_config.fluence
    print(f"\nFluence: {fluence:.6e} photons/m^2")

    # Polarization factor (unpolarized case, kahn_factor=0.0 default)
    # P = 0.5 * (1 + cos²(2θ))
    cos_2theta = torch.dot(incident, diffracted)
    polar = 0.5 * (1.0 + cos_2theta**2)
    print(f"\ncos(2θ): {cos_2theta:.6f}")
    print(f"Polarization factor: {polar:.6f}")

    print(f"\n=== Trace Complete ===")
    print(f"This trace should be compared line-by-line with C trace for pixel ({target_s}, {target_f})")

    # Save trace
    output_dir = Path(__file__).parent.parent / "reports" / "2025-09-30-AT-PARALLEL-012"
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "py_trace_pixel_513_446.log", 'w') as f:
        f.write(f"=== PyTorch Trace for Pixel ({target_s}, {target_f}) ===\n\n")
        f.write(f"Detector Geometry:\n")
        f.write(f"  pix0_vector: {detector.pix0_vector.tolist()}\n")
        f.write(f"  fdet_vec: {detector.fdet_vec.tolist()}\n")
        f.write(f"  sdet_vec: {detector.sdet_vec.tolist()}\n")
        f.write(f"  pixel_coords[{target_s},{target_f}]: {pix_vec.tolist()}\n")
        f.write(f"\nBeam:\n")
        f.write(f"  incident: [1.0, 0.0, 0.0]\n")
        f.write(f"  wavelength: {beam_config.wavelength_A} Å\n")
        f.write(f"\nScattering:\n")
        f.write(f"  diffracted: {diffracted.tolist()}\n")
        f.write(f"  S (1/Å): {S.tolist()}\n")
        f.write(f"\nLattice (real):\n")
        f.write(f"  rot_a: {rot_a.tolist()}\n")
        f.write(f"  rot_b: {rot_b.tolist()}\n")
        f.write(f"  rot_c: {rot_c.tolist()}\n")
        f.write(f"\nLattice (reciprocal):\n")
        f.write(f"  rot_a_star: {rot_a_star.tolist()}\n")
        f.write(f"  rot_b_star: {rot_b_star.tolist()}\n")
        f.write(f"  rot_c_star: {rot_c_star.tolist()}\n")
        f.write(f"\nMiller:\n")
        f.write(f"  h_float: {h_float:.6f}\n")
        f.write(f"  k_float: {k_float:.6f}\n")
        f.write(f"  l_float: {l_float:.6f}\n")
        f.write(f"  h_int: {h_int}\n")
        f.write(f"  k_int: {k_int}\n")
        f.write(f"  l_int: {l_int}\n")
        f.write(f"\nIntensity:\n")
        f.write(f"  F_cell: {F_cell}\n")
        f.write(f"  r_e: {r_e:.6e} m\n")
        f.write(f"  R: {R:.6f} m\n")
        f.write(f"  close_distance: {close_distance_m:.6f} m\n")
        f.write(f"  omega: {omega:.6e} sr\n")
        f.write(f"  fluence: {fluence:.6e} photons/m^2\n")
        f.write(f"  cos_2theta: {cos_2theta:.6f}\n")
        f.write(f"  polar: {polar:.6f}\n")

    print(f"\nTrace saved to: {output_dir / 'py_trace_pixel_513_446.log'}")

if __name__ == "__main__":
    main()