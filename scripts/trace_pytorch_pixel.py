#!/usr/bin/env python3
"""
PyTorch pixel trace for CLI-FLAGS-003 Phase K3g3 debugging.

Generates a detailed trace of all intermediate calculations for a single pixel
to match the C code TRACE_C output format for line-by-line comparison.

Usage:
    python scripts/trace_pytorch_pixel.py --spixel 236 --fpixel 398
"""
import os
import sys
import argparse
import torch

# Set required environment variable
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig


def trace_pixel(spixel: int, fpixel: int, output_file: str):
    """Generate complete trace for a single pixel."""

    # Use float64 for maximum precision in trace
    dtype = torch.float64
    device = torch.device('cpu')

    print(f"=== PyTorch Pixel Trace (s={spixel}, f={fpixel}) ===", file=sys.stderr)
    print(f"Device: {device}, dtype: {dtype}", file=sys.stderr)

    # Configuration matching the test case
    crystal_config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(10, 10, 10),
        default_F=300.0,
    )

    from nanobrag_torch.config import DetectorConvention

    detector_config = DetectorConfig(
        spixels=512,
        fpixels=512,
        pixel_size_mm=0.1,
        distance_mm=100.0,
        beam_center_s=25.6,  # 512 * 0.1 / 2
        beam_center_f=25.6,  # 512 * 0.1 / 2
        detector_convention=DetectorConvention.MOSFLM,
    )

    # Initialize components
    crystal = Crystal(crystal_config, device=device, dtype=dtype)
    detector = Detector(detector_config, device=device, dtype=dtype)

    # Beam parameters (not using BeamConfig object)
    wavelength_A = 1.0

    # Open output file
    with open(output_file, 'w') as f:
        # ===== CRYSTAL LATTICE COMPUTATION =====
        f.write("=== CRYSTAL LATTICE COMPUTATION ===\n")

        # Get cell tensors
        tensors = crystal.compute_cell_tensors()

        # Base reciprocal vectors
        a_star = tensors['a_star']
        b_star = tensors['b_star']
        c_star = tensors['c_star']

        f.write(f"TRACE_PY: Initial reciprocal vectors (Å^-1):\n")
        f.write(f"TRACE_PY:   a_star = [{a_star[0].item():.15g}, {a_star[1].item():.15g}, {a_star[2].item():.15g}]\n")
        f.write(f"TRACE_PY:   b_star = [{b_star[0].item():.15g}, {b_star[1].item():.15g}, {b_star[2].item():.15g}]\n")
        f.write(f"TRACE_PY:   c_star = [{c_star[0].item():.15g}, {c_star[1].item():.15g}, {c_star[2].item():.15g}]\n")

        # Cell volume
        V_cell = tensors['V']

        # Reciprocal cell volume
        b_star_cross_c_star = torch.cross(b_star, c_star)
        V_star = torch.dot(a_star, b_star_cross_c_star)

        f.write(f"TRACE_PY: V_star = {V_star.item():.15g} Å^-3\n")
        f.write(f"TRACE_PY: V_cell = {V_cell.item():.15g} Å^3\n")

        # Real-space vectors
        a = tensors['a']
        b = tensors['b']
        c = tensors['c']

        f.write(f"TRACE_PY: Real-space vectors (Å):\n")
        f.write(f"TRACE_PY:   a = [{a[0].item():.15g}, {a[1].item():.15g}, {a[2].item():.15g}] |a| = {torch.norm(a).item():.15g}\n")
        f.write(f"TRACE_PY:   b = [{b[0].item():.15g}, {b[1].item():.15g}, {b[2].item():.15g}] |b| = {torch.norm(b).item():.15g}\n")
        f.write(f"TRACE_PY:   c = [{c[0].item():.15g}, {c[1].item():.15g}, {c[2].item():.15g}] |c| = {torch.norm(c).item():.15g}\n")

        # Convert to meters (C code convention)
        a_m = a * 1e-10
        b_m = b * 1e-10
        c_m = c * 1e-10

        f.write(f"TRACE_PY: Real-space vectors (meters):\n")
        f.write(f"TRACE_PY:   a_m = [{a_m[0].item():.15g}, {a_m[1].item():.15g}, {a_m[2].item():.15g}] |a_m| = {torch.norm(a_m).item():.15g}\n")
        f.write(f"TRACE_PY:   b_m = [{b_m[0].item():.15g}, {b_m[1].item():.15g}, {b_m[2].item():.15g}] |b_m| = {torch.norm(b_m).item():.15g}\n")
        f.write(f"TRACE_PY:   c_m = [{c_m[0].item():.15g}, {c_m[1].item():.15g}, {c_m[2].item():.15g}] |c_m| = {torch.norm(c_m).item():.15g}\n")

        # ===== DETECTOR GEOMETRY =====
        f.write("\n=== DETECTOR GEOMETRY ===\n")

        # Get detector basis
        det_tensors = detector.compute_detector_basis()
        fdet_vec = det_tensors['fdet']
        sdet_vec = det_tensors['sdet']
        odet_vec = det_tensors['odet']
        pix0_vector = det_tensors['pix0_vector']

        f.write(f"TRACE_PY: Detector basis vectors:\n")
        f.write(f"TRACE_PY:   fdet = [{fdet_vec[0].item():.15g}, {fdet_vec[1].item():.15g}, {fdet_vec[2].item():.15g}]\n")
        f.write(f"TRACE_PY:   sdet = [{sdet_vec[0].item():.15g}, {sdet_vec[1].item():.15g}, {sdet_vec[2].item():.15g}]\n")
        f.write(f"TRACE_PY:   odet = [{odet_vec[0].item():.15g}, {odet_vec[1].item():.15g}, {odet_vec[2].item():.15g}]\n")
        f.write(f"TRACE_PY: pix0_vector = [{pix0_vector[0].item():.15g}, {pix0_vector[1].item():.15g}, {pix0_vector[2].item():.15g}]\n")

        # ===== PIXEL POSITION =====
        f.write(f"\n=== PIXEL POSITION (s={spixel}, f={fpixel}) ===\n")

        # Compute pixel position
        pixel_size_m = detector_config.pixel_size_mm * 1e-3

        # C code uses integer pixel indices (not pixel centers)
        # pixel_pos = pix0_vector + fpixel * fdet_vec * pixel_size + spixel * sdet_vec * pixel_size
        pixel_pos = (
            pix0_vector
            + fpixel * fdet_vec * pixel_size_m
            + spixel * sdet_vec * pixel_size_m
        )

        f.write(f"TRACE_PY: pixel_pos_meters = [{pixel_pos[0].item():.15g}, {pixel_pos[1].item():.15g}, {pixel_pos[2].item():.15g}]\n")

        # Distance to pixel
        R_distance = torch.norm(pixel_pos)
        f.write(f"TRACE_PY: R_distance_meters = {R_distance.item():.15g}\n")

        # Diffracted beam direction (unit vector)
        diffracted = pixel_pos / R_distance
        f.write(f"TRACE_PY: diffracted_vec = [{diffracted[0].item():.15g}, {diffracted[1].item():.15g}, {diffracted[2].item():.15g}]\n")

        # ===== BEAM AND SCATTERING =====
        f.write("\n=== BEAM AND SCATTERING ===\n")

        # Incident beam (along +X in MOSFLM)
        incident = torch.tensor([1.0, 0.0, 0.0], device=device, dtype=dtype)
        f.write(f"TRACE_PY: incident_vec = [{incident[0].item():.15g}, {incident[1].item():.15g}, {incident[2].item():.15g}]\n")

        # Wavelength
        wavelength_m = wavelength_A * 1e-10
        f.write(f"TRACE_PY: lambda_meters = {wavelength_m:.15g}\n")
        f.write(f"TRACE_PY: lambda_angstroms = {wavelength_A:.15g}\n")

        # Scattering vector S = (k_out - k_in) / lambda (in Å^-1)
        # Units: diffracted and incident are unitless, wavelength_m in meters
        # Convert to Å^-1: multiply by 1e10
        scattering_A_inv = (diffracted - incident) / wavelength_m * 1e-10

        f.write(f"TRACE_PY: scattering_vec_A_inv = [{scattering_A_inv[0].item():.15g}, {scattering_A_inv[1].item():.15g}, {scattering_A_inv[2].item():.15g}]\n")

        # ===== MILLER INDICES =====
        f.write("\n=== MILLER INDICES ===\n")

        # h = a · S, k = b · S, l = c · S (using real-space vectors in Å and S in Å^-1)
        # No phi rotation (phi=0), no mosaic (single domain)
        h_frac = torch.dot(a, scattering_A_inv)
        k_frac = torch.dot(b, scattering_A_inv)
        l_frac = torch.dot(c, scattering_A_inv)

        f.write(f"TRACE_PY: hkl_frac = [{h_frac.item():.15g}, {k_frac.item():.15g}, {l_frac.item():.15g}]\n")

        # Round to nearest integer
        h0 = torch.ceil(h_frac - 0.5).int()
        k0 = torch.ceil(k_frac - 0.5).int()
        l0 = torch.ceil(l_frac - 0.5).int()

        f.write(f"TRACE_PY: hkl_rounded = [{h0.item()}, {k0.item()}, {l0.item()}]\n")

        # ===== LATTICE FACTOR (SQUARE SHAPE) =====
        f.write("\n=== LATTICE FACTOR (SQUARE SHAPE) ===\n")

        Na = crystal_config.N_cells[0]
        Nb = crystal_config.N_cells[1]
        Nc = crystal_config.N_cells[2]

        f.write(f"TRACE_PY: N_cells = ({Na}, {Nb}, {Nc})\n")

        # CRITICAL: Use h, k, l (NOT h-h0, k-k0, l-l0) per CLI-FLAGS-003 Phase K2 fix
        # F_latt_a = sincg(π·h, Na) = sin(π·h·Na) / (Na·sin(π·h))
        def sincg_trace(arg, N):
            """Compute sincg with trace output."""
            # sincg(x, N) = sin(N*x) / (N * sin(x))
            numerator = torch.sin(N * arg)
            denominator = N * torch.sin(arg)
            # Avoid division by zero
            result = torch.where(
                torch.abs(denominator) > 1e-15,
                numerator / denominator,
                torch.ones_like(arg)  # lim_{x->0} sin(Nx)/(N*sin(x)) = 1
            )
            return result

        import math
        F_latt_a = sincg_trace(math.pi * h_frac, Na)
        F_latt_b = sincg_trace(math.pi * k_frac, Nb)
        F_latt_c = sincg_trace(math.pi * l_frac, Nc)
        F_latt = F_latt_a * F_latt_b * F_latt_c

        f.write(f"TRACE_PY: F_latt_a = sincg(π·{h_frac.item():.15g}, {Na}) = {F_latt_a.item():.15g}\n")
        f.write(f"TRACE_PY: F_latt_b = sincg(π·{k_frac.item():.15g}, {Nb}) = {F_latt_b.item():.15g}\n")
        f.write(f"TRACE_PY: F_latt_c = sincg(π·{l_frac.item():.15g}, {Nc}) = {F_latt_c.item():.15g}\n")
        f.write(f"TRACE_PY: F_latt = {F_latt.item():.15g}\n")

        # ===== STRUCTURE FACTOR =====
        f.write("\n=== STRUCTURE FACTOR ===\n")

        F_cell = crystal_config.default_F
        f.write(f"TRACE_PY: F_cell = {F_cell:.15g}\n")

        # ===== INTENSITY BEFORE SCALING =====
        f.write("\n=== INTENSITY BEFORE SCALING ===\n")

        I_before_scaling = F_cell**2 * F_latt**2
        f.write(f"TRACE_PY: I_before_scaling = {I_before_scaling.item():.15g}\n")

        # ===== SCALING FACTORS =====
        f.write("\n=== SCALING FACTORS ===\n")

        # Classical electron radius
        r_e_m = 2.81794117756025e-15
        r_e_sqr = r_e_m**2
        f.write(f"TRACE_PY: r_e_meters = {r_e_m:.15g}\n")
        f.write(f"TRACE_PY: r_e_sqr = {r_e_sqr:.15g}\n")

        # Solid angle
        close_distance = detector_config.distance_mm * 1e-3  # meters
        obliquity_factor = close_distance / R_distance.item()
        omega_pixel = (pixel_size_m**2 / R_distance.item()**2) * obliquity_factor
        f.write(f"TRACE_PY: close_distance_meters = {close_distance:.15g}\n")
        f.write(f"TRACE_PY: obliquity_factor = {obliquity_factor:.15g}\n")
        f.write(f"TRACE_PY: omega_pixel_sr = {omega_pixel:.15g}\n")

        # Fluence (from C code default)
        # fluence = flux * exposure_time / beam_area
        # C code uses: fluence = 1e20 (default), but we need to compute from flux
        # For now, match the C trace value
        fluence_photons_per_m2 = 1.25932015286227e+29
        f.write(f"TRACE_PY: fluence_photons_per_m2 = {fluence_photons_per_m2:.15g}\n")

        # Polarization factor
        cos_2theta = diffracted[0].item()  # dot(diffracted, incident) for incident=[1,0,0]
        polar = (1.0 + cos_2theta**2) / 2.0
        f.write(f"TRACE_PY: cos_2theta = {cos_2theta:.15g}\n")
        f.write(f"TRACE_PY: polar = {polar:.15g}\n")

        # Final intensity
        I_pixel_final = I_before_scaling.item() * r_e_sqr * fluence_photons_per_m2 * omega_pixel * polar
        f.write(f"TRACE_PY: I_pixel_final = {I_pixel_final:.15g}\n")

    print(f"PyTorch trace saved to: {output_file}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Generate PyTorch pixel trace")
    parser.add_argument('--spixel', type=int, required=True, help="Slow pixel index")
    parser.add_argument('--fpixel', type=int, required=True, help="Fast pixel index")
    parser.add_argument('--output', type=str, default=None, help="Output file (default: auto-generated)")

    args = parser.parse_args()

    if args.output is None:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        args.output = f"reports/2025-10-cli-flags/phase_k/f_latt_fix/post_fix/py_trace_{timestamp}.log"

    trace_pixel(args.spixel, args.fpixel, args.output)


if __name__ == '__main__':
    main()
