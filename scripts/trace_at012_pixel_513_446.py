#!/usr/bin/env python3
"""Generate detailed PyTorch trace for simple_cubic pixel (513, 446) matching C trace format."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
import torch
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorPivot
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector, DetectorConvention

def main():
    # Target pixel (513, 446) - from analysis showing C=92.72, Py=100.29
    target_s = 513
    target_f = 446

    print(f"=== PyTorch Trace for Pixel ({target_s}, {target_f}) ===\n")

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

    # === DETECTOR GEOMETRY ===
    print("TRACE_PY:detector_convention=MOSFLM")
    print("TRACE_PY:angles_rad=rotx:0 roty:0 rotz:0 twotheta:0")
    # Convert beam center from pixels to meters (C code uses Xbeam/Ybeam in meters, but MOSFLM swaps them)
    # In MOSFLM: Fbeam ← Ybeam, Sbeam ← Xbeam
    beam_center_s_m = detector.beam_center_s * detector.pixel_size
    beam_center_f_m = detector.beam_center_f * detector.pixel_size
    print(f"TRACE_PY:beam_center_m=X:{beam_center_s_m:.15g} Y:{beam_center_f_m:.15g} pixel_mm:{detector_config.pixel_size_mm}")
    print(f"TRACE_PY:initial_fdet={detector.fdet_vec[0]:.15g} {detector.fdet_vec[1]:.15g} {detector.fdet_vec[2]:.15g}")
    print(f"TRACE_PY:initial_sdet={detector.sdet_vec[0]:.15g} {detector.sdet_vec[1]:.15g} {detector.sdet_vec[2]:.15g}")
    print(f"TRACE_PY:pix0_vector={detector.pix0_vector[0]:.15g} {detector.pix0_vector[1]:.15g} {detector.pix0_vector[2]:.15g}")

    # Get pixel position
    pixel_coords = detector.get_pixel_coords()  # (spixels, fpixels, 3)
    pix_vec = pixel_coords[target_s, target_f, :]
    print(f"TRACE_PY: pixel_pos_meters {pix_vec[0]:.15g} {pix_vec[1]:.15g} {pix_vec[2]:.15g}")

    # Compute R (airpath distance)
    R = torch.norm(pix_vec)
    print(f"TRACE_PY: R_distance_meters {R:.15g}")

    # Compute omega (solid angle)
    pixel_size_m = detector_config.pixel_size_mm * 1e-3
    close_distance_m = detector_config.distance_mm * 1e-3
    omega_pixel = (pixel_size_m**2 * close_distance_m) / R**3
    print(f"TRACE_PY: omega_pixel_sr {omega_pixel:.15g}")
    print(f"TRACE_PY: close_distance_meters {close_distance_m:.15g}")
    print(f"TRACE_PY: obliquity_factor {close_distance_m/R:.15g}")

    # Diffracted direction (unit vector)
    diffracted = pix_vec / R
    print(f"TRACE_PY: diffracted_vec {diffracted[0]:.15g} {diffracted[1]:.15g} {diffracted[2]:.15g}")

    # Incident direction
    incident = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
    print(f"TRACE_PY: incident_vec {incident[0]:.15g} {incident[1]:.15g} {incident[2]:.15g}")

    # Wavelength
    lambda_m = beam_config.wavelength_A * 1e-10
    print(f"TRACE_PY: lambda_meters {lambda_m:.15g}")

    # Scattering vector S = (diffracted - incident) / λ (in 1/Angstrom)
    S_vec = (diffracted - incident) / lambda_m
    print(f"TRACE_PY: scattering_vec_A_inv {S_vec[0]:.15g} {S_vec[1]:.15g} {S_vec[2]:.15g}")

    # === CRYSTAL LATTICE ===
    # Get rotated lattice vectors (real and reciprocal)
    # Returns shape (N_phi, N_mos, 3) - for simple case with no rotation, this is (1, 1, 3)
    (rot_a, rot_b, rot_c), (rot_a_star, rot_b_star, rot_c_star) = crystal.get_rotated_real_vectors(crystal_config)

    # Extract the single phi/mosaic configuration (phi=0, mos=0)
    rot_a = rot_a[0, 0, :]  # Now shape (3,)
    rot_b = rot_b[0, 0, :]
    rot_c = rot_c[0, 0, :]

    # Convert to meters for Miller index calculation (matching C code)
    rot_a_m = rot_a * 1e-10
    rot_b_m = rot_b * 1e-10
    rot_c_m = rot_c * 1e-10

    # Compute Miller indices h,k,l = S · lattice_vectors
    h_float = torch.dot(S_vec, rot_a_m)
    k_float = torch.dot(S_vec, rot_b_m)
    l_float = torch.dot(S_vec, rot_c_m)
    print(f"TRACE_PY: hkl_frac {h_float:.15g} {k_float:.15g} {l_float:.15g}")

    # Round to nearest integer
    h_int = int(torch.ceil(h_float - 0.5).item())
    k_int = int(torch.ceil(k_float - 0.5).item())
    l_int = int(torch.ceil(l_float - 0.5).item())
    print(f"TRACE_PY: hkl_rounded {h_int} {k_int} {l_int}")

    # === LATTICE SHAPE FACTOR (F_latt) ===
    # Using sinc function: sinc(x) = sin(π*x)/(π*x)
    # F_latt = sinc(h*Na) * sinc(k*Nb) * sinc(l*Nc)
    Na, Nb, Nc = crystal_config.N_cells

    def sincg(x, N):
        """Generalized sinc function matching C code."""
        if N <= 1:
            return torch.tensor(1.0, dtype=torch.float64)
        sin_Nx = torch.sin(N * x)
        sin_x = torch.sin(x)
        # Handle x ≈ 0
        if torch.abs(sin_x) < 1e-10:
            return torch.tensor(float(N), dtype=torch.float64)
        return sin_Nx / sin_x

    import math
    F_latt_a = sincg(math.pi * h_float, Na)
    F_latt_b = sincg(math.pi * k_float, Nb)
    F_latt_c = sincg(math.pi * l_float, Nc)
    F_latt = F_latt_a * F_latt_b * F_latt_c

    print(f"TRACE_PY: F_latt_a {F_latt_a:.15g}")
    print(f"TRACE_PY: F_latt_b {F_latt_b:.15g}")
    print(f"TRACE_PY: F_latt_c {F_latt_c:.15g}")
    print(f"TRACE_PY: F_latt {F_latt:.15g}")

    # === STRUCTURE FACTOR ===
    F_cell = crystal_config.default_F
    print(f"TRACE_PY: F_cell {F_cell}")

    # === INTENSITY CALCULATION ===
    # I = F_cell² * F_latt²
    I_before_scaling = F_cell**2 * F_latt**2
    print(f"TRACE_PY: I_before_scaling {I_before_scaling:.15g}")

    # Physical constants (from nanoBragg.c ~line 240)
    r_e_sqr = 7.94079248018965e-30  # classical electron radius squared (meters squared)
    print(f"TRACE_PY: r_e_sqr {r_e_sqr:.15g}")

    fluence = beam_config.fluence
    print(f"TRACE_PY: fluence {fluence:.15g}")

    steps = 1  # No oversampling in simple case
    print(f"TRACE_PY: steps {steps}")
    print(f"TRACE_PY: oversample_thick 0")
    print(f"TRACE_PY: oversample_polar 0")
    print(f"TRACE_PY: oversample_omega 0")

    capture_fraction = 1.0
    print(f"TRACE_PY: capture_fraction {capture_fraction}")

    # Polarization factor (unpolarized case)
    cos_2theta = torch.dot(incident, diffracted)
    polar = 0.5 * (1.0 + cos_2theta**2)
    print(f"TRACE_PY: polar {polar:.15g}")
    print(f"TRACE_PY: omega_pixel {omega_pixel:.15g}")

    # Final intensity
    I_pixel_final = r_e_sqr * fluence * I_before_scaling / steps * capture_fraction * polar * omega_pixel
    print(f"TRACE_PY: I_pixel_final {I_pixel_final:.15g}")

    # Accumulated (no multiple sources/mosaic domains in this case)
    print(f"TRACE_PY: floatimage_accumulated {I_pixel_final:.15g}")

    # Save to file
    output_dir = Path(__file__).parent.parent / "reports" / "2025-09-30-AT-PARALLEL-012"
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "py_trace_pixel_513_446.log", 'w') as f:
        # Write all the trace lines
        f.write(f"TRACE_PY:detector_convention=MOSFLM\n")
        f.write(f"TRACE_PY:angles_rad=rotx:0 roty:0 rotz:0 twotheta:0\n")
        f.write(f"TRACE_PY:beam_center_m=X:{beam_center_s_m:.15g} Y:{beam_center_f_m:.15g} pixel_mm:{detector_config.pixel_size_mm}\n")
        f.write(f"TRACE_PY:initial_fdet={detector.fdet_vec[0]:.15g} {detector.fdet_vec[1]:.15g} {detector.fdet_vec[2]:.15g}\n")
        f.write(f"TRACE_PY:initial_sdet={detector.sdet_vec[0]:.15g} {detector.sdet_vec[1]:.15g} {detector.sdet_vec[2]:.15g}\n")
        f.write(f"TRACE_PY:pix0_vector={detector.pix0_vector[0]:.15g} {detector.pix0_vector[1]:.15g} {detector.pix0_vector[2]:.15g}\n")
        f.write(f"TRACE_PY: pixel_pos_meters {pix_vec[0]:.15g} {pix_vec[1]:.15g} {pix_vec[2]:.15g}\n")
        f.write(f"TRACE_PY: R_distance_meters {R:.15g}\n")
        f.write(f"TRACE_PY: omega_pixel_sr {omega_pixel:.15g}\n")
        f.write(f"TRACE_PY: close_distance_meters {close_distance_m:.15g}\n")
        f.write(f"TRACE_PY: obliquity_factor {close_distance_m/R:.15g}\n")
        f.write(f"TRACE_PY: diffracted_vec {diffracted[0]:.15g} {diffracted[1]:.15g} {diffracted[2]:.15g}\n")
        f.write(f"TRACE_PY: incident_vec {incident[0]:.15g} {incident[1]:.15g} {incident[2]:.15g}\n")
        f.write(f"TRACE_PY: lambda_meters {lambda_m:.15g}\n")
        f.write(f"TRACE_PY: scattering_vec_A_inv {S_vec[0]:.15g} {S_vec[1]:.15g} {S_vec[2]:.15g}\n")
        f.write(f"TRACE_PY: hkl_frac {h_float:.15g} {k_float:.15g} {l_float:.15g}\n")
        f.write(f"TRACE_PY: hkl_rounded {h_int} {k_int} {l_int}\n")
        f.write(f"TRACE_PY: F_latt_a {F_latt_a:.15g}\n")
        f.write(f"TRACE_PY: F_latt_b {F_latt_b:.15g}\n")
        f.write(f"TRACE_PY: F_latt_c {F_latt_c:.15g}\n")
        f.write(f"TRACE_PY: F_latt {F_latt:.15g}\n")
        f.write(f"TRACE_PY: F_cell {F_cell}\n")
        f.write(f"TRACE_PY: I_before_scaling {I_before_scaling:.15g}\n")
        f.write(f"TRACE_PY: r_e_sqr {r_e_sqr:.15g}\n")
        f.write(f"TRACE_PY: fluence {fluence:.15g}\n")
        f.write(f"TRACE_PY: steps {steps}\n")
        f.write(f"TRACE_PY: oversample_thick 0\n")
        f.write(f"TRACE_PY: oversample_polar 0\n")
        f.write(f"TRACE_PY: oversample_omega 0\n")
        f.write(f"TRACE_PY: capture_fraction {capture_fraction}\n")
        f.write(f"TRACE_PY: polar {polar:.15g}\n")
        f.write(f"TRACE_PY: omega_pixel {omega_pixel:.15g}\n")
        f.write(f"TRACE_PY: I_pixel_final {I_pixel_final:.15g}\n")
        f.write(f"TRACE_PY: floatimage_accumulated {I_pixel_final:.15g}\n")

    print(f"\n=== Trace saved to: {output_dir / 'py_trace_pixel_513_446.log'} ===")

if __name__ == "__main__":
    main()