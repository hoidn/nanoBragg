#!/usr/bin/env python3
"""
Generate PyTorch pixel trace for parity debugging.

Emits TRACE_PY lines matching the C trace schema for direct line-by-line comparison.
Designed for Phase C2 of VECTOR-PARITY-001 vectorization parity regression diagnosis.

Usage:
    python scripts/debug_pixel_trace.py --pixel 2048 2048 --tag ROI_center --out-dir reports/phase_c/traces
    python scripts/debug_pixel_trace.py --pixel 1792 2048 --tag ROI_boundary --out-dir reports/phase_c/traces
    python scripts/debug_pixel_trace.py --pixel 4095 2048 --tag far_edge --out-dir reports/phase_c/traces
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
import argparse
import torch
import numpy as np
from pathlib import Path
import json
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention, DetectorPivot


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate PyTorch pixel trace for parity debugging",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--pixel', nargs=2, type=int, required=True, metavar=('SLOW', 'FAST'),
        help='Pixel coordinates (slow, fast) to trace'
    )
    parser.add_argument(
        '--tag', type=str, default='pixel', metavar='NAME',
        help='Tag for output filename (default: pixel)'
    )
    parser.add_argument(
        '--out-dir', type=str, default='reports/trace_output', metavar='PATH',
        help='Output directory for trace logs (default: reports/trace_output)'
    )
    parser.add_argument(
        '--dtype', type=str, default='float64', choices=['float32', 'float64'],
        help='PyTorch dtype for trace (default: float64 for determinism)'
    )
    parser.add_argument(
        '--device', type=str, default='cpu', choices=['cpu', 'cuda'],
        help='Device for trace (default: cpu for determinism)'
    )

    return parser.parse_args()


def emit_trace(prefix, key, *values):
    """
    Emit a single TRACE_PY line matching C trace schema.

    Args:
        prefix: "TRACE_PY" for PyTorch traces
        key: Variable name (e.g., "pix0_vector_meters")
        values: Numeric values to print (printed with %.15e precision for floats)
    """
    formatted_values = []
    for v in values:
        if isinstance(v, (torch.Tensor, np.ndarray)):
            # Extract scalar or vector elements
            if hasattr(v, 'numel') and v.numel() == 1:
                formatted_values.append(f"{v.item():.15e}")
            elif len(v.shape) == 0:  # Scalar tensor
                formatted_values.append(f"{v.item():.15e}")
            else:
                # Vector: print each element
                for elem in v.flatten():
                    formatted_values.append(f"{elem.item():.15e}")
        elif isinstance(v, (int, bool)):
            formatted_values.append(str(int(v)))
        elif isinstance(v, float):
            formatted_values.append(f"{v:.15e}")
        elif isinstance(v, str):
            formatted_values.append(v)
        else:
            formatted_values.append(str(v))

    print(f"{prefix}: {key} {' '.join(formatted_values)}")


def main():
    """Main trace generation routine."""
    args = parse_args()

    # Extract pixel coordinates
    target_s, target_f = args.pixel

    # Setup output directory
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Setup device and dtype
    dtype = torch.float64 if args.dtype == 'float64' else torch.float32
    device = torch.device(args.device)

    # Configuration matching the 4096² parity case from Phase C1
    # Command: -default_F 100 -cell 100 100 100 90 90 90 -lambda 0.5 -distance 500 -pixel 0.05 -detpixels 4096 -N 5 -convention MOSFLM -oversample 1

    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0,
        phi_start_deg=0.0,
        osc_range_deg=0.0,
        phi_steps=1,
        mosaic_spread_deg=0.0,
        mosaic_domains=1
    )

    detector_config = DetectorConfig(
        spixels=4096,
        fpixels=4096,
        pixel_size_mm=0.05,
        distance_mm=500.0,
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM,
        detector_rotx_deg=0.0,
        detector_roty_deg=0.0,
        detector_rotz_deg=0.0,
        detector_twotheta_deg=0.0
    )

    beam_config = BeamConfig(
        wavelength_A=0.5,
        polarization_factor=0.0,  # Unpolarized
        flux=0.0,  # Default: no flux specified (keeps default fluence 1.259e+29)
        exposure=1.0,
        beamsize_mm=0.1
    )

    # Create components
    crystal = Crystal(crystal_config, dtype=dtype, device=device)
    detector = Detector(detector_config, dtype=dtype, device=device)
    simulator = Simulator(crystal, detector, crystal_config, beam_config, dtype=dtype, device=device)

    # Start trace output
    print(f"=== PyTorch Pixel Trace for ({target_s}, {target_f}) ===")
    print(f"Configuration: 4096×4096, pixel=0.05mm, distance=500mm, λ=0.5Å, MOSFLM convention")
    print(f"Device: {device}, dtype: {dtype}")
    print()

    # Resolve twotheta_axis from config (it defaults based on convention)
    if detector_config.twotheta_axis is None:
        # MOSFLM default: [0, 0, -1]
        twotheta_axis_tensor = torch.tensor([0.0, 0.0, -1.0], dtype=dtype, device=device)
    else:
        twotheta_axis_tensor = detector_config.twotheta_axis.to(device=device, dtype=dtype)
    twotheta_axis = twotheta_axis_tensor.cpu().numpy()

    # Emit detector geometry traces
    # First emit rotation matrices and initial basis vectors
    emit_trace("TRACE_PY", "fdet_after_rotz", detector.fdet_vec.cpu().numpy())
    emit_trace("TRACE_PY", "sdet_after_rotz", detector.sdet_vec.cpu().numpy())
    emit_trace("TRACE_PY", "odet_after_rotz", detector.odet_vec.cpu().numpy())
    emit_trace("TRACE_PY", "twotheta_axis", twotheta_axis)

    # After twotheta rotation (zero in this case)
    emit_trace("TRACE_PY", "fdet_after_twotheta", detector.fdet_vec.cpu().numpy())
    emit_trace("TRACE_PY", "sdet_after_twotheta", detector.sdet_vec.cpu().numpy())
    emit_trace("TRACE_PY", "odet_after_twotheta", detector.odet_vec.cpu().numpy())

    # Convention
    emit_trace("TRACE_PY", "detector_convention", "MOSFLM")

    # Angles (all zero in this config)
    emit_trace("TRACE_PY", "angles_rad", f"rotx:{detector_config.detector_rotx_deg * np.pi / 180:.15e}",
               f"roty:{detector_config.detector_roty_deg * np.pi / 180:.15e}",
               f"rotz:{detector_config.detector_rotz_deg * np.pi / 180:.15e}",
               f"twotheta:{detector_config.detector_twotheta_deg * np.pi / 180:.15e}")

    # Beam center (stored in pixels, convert to meters)
    pixel_size_m = detector_config.pixel_size_mm / 1000.0
    beam_center_f_m = (detector.beam_center_f * pixel_size_m).item()
    beam_center_s_m = (detector.beam_center_s * pixel_size_m).item()
    emit_trace("TRACE_PY", "beam_center_m", f"X:{beam_center_f_m:.15e}", f"Y:{beam_center_s_m:.15e}",
               f"pixel_mm:{detector_config.pixel_size_mm}")

    # Initial basis vectors (before rotations - for MOSFLM these are the same since no rotations)
    emit_trace("TRACE_PY", "initial_fdet", detector.fdet_vec.cpu().numpy())
    emit_trace("TRACE_PY", "initial_sdet", detector.sdet_vec.cpu().numpy())
    emit_trace("TRACE_PY", "initial_odet", detector.odet_vec.cpu().numpy())

    # Rotation matrices (identity for this case)
    # Emit as "[a b c; d e f; g h i]" format
    emit_trace("TRACE_PY", "Rx", "[1 0 0; 0 1 0; 0 0 1]")
    emit_trace("TRACE_PY", "Ry", "[1 0 0; 0 1 0; 0 0 1]")
    emit_trace("TRACE_PY", "Rz", "[1 0 0; 0 1 0; 0 0 1]")
    emit_trace("TRACE_PY", "R_total", "[1 0 0; 0 1 0; 0 0 1]")

    # Re-emit after rotations (same as before for zero rotations)
    emit_trace("TRACE_PY", "fdet_after_rotz", detector.fdet_vec.cpu().numpy())
    emit_trace("TRACE_PY", "sdet_after_rotz", detector.sdet_vec.cpu().numpy())
    emit_trace("TRACE_PY", "odet_after_rotz", detector.odet_vec.cpu().numpy())
    emit_trace("TRACE_PY", "twotheta_axis", twotheta_axis)
    emit_trace("TRACE_PY", "fdet_after_twotheta", detector.fdet_vec.cpu().numpy())
    emit_trace("TRACE_PY", "sdet_after_twotheta", detector.sdet_vec.cpu().numpy())
    emit_trace("TRACE_PY", "odet_after_twotheta", detector.odet_vec.cpu().numpy())

    # Convention mapping
    emit_trace("TRACE_PY", "convention_mapping", "Fbeam←Ybeam_mm(+0.5px),Sbeam←Xbeam_mm(+0.5px),beam_vec=[1 0 0]")

    # Fbeam and Sbeam
    emit_trace("TRACE_PY", "Fbeam_m", beam_center_f_m)
    emit_trace("TRACE_PY", "Sbeam_m", beam_center_s_m)
    emit_trace("TRACE_PY", "distance_m", detector_config.distance_mm / 1000.0)

    # pix0 calculation terms (pixel_size_m already defined above)
    distance_m = detector_config.distance_mm / 1000.0

    # Beam direction for MOSFLM: [1, 0, 0]
    beam_direction = torch.tensor([1.0, 0.0, 0.0], dtype=dtype, device=device)

    term_fast = -beam_center_f_m * detector.fdet_vec
    term_slow = -beam_center_s_m * detector.sdet_vec
    term_beam = distance_m * beam_direction

    emit_trace("TRACE_PY", "term_fast", term_fast.cpu().numpy())
    emit_trace("TRACE_PY", "term_slow", term_slow.cpu().numpy())
    emit_trace("TRACE_PY", "term_beam", term_beam.cpu().numpy())

    # pix0_vector
    pix0_vector = detector.pix0_vector
    emit_trace("TRACE_PY", "pix0_vector", pix0_vector.cpu().numpy())

    # Now compute target pixel position
    # Get pixel coordinates (meters)
    # Note: get_pixel_coords() returns all pixel coordinates, no arguments needed
    pixel_coords_m = detector.get_pixel_coords()
    target_coords = pixel_coords_m[target_s, target_f]

    emit_trace("TRACE_PY", "pix0_vector_meters", pix0_vector.cpu().numpy())
    emit_trace("TRACE_PY", "fdet_vec", detector.fdet_vec.cpu().numpy())
    emit_trace("TRACE_PY", "sdet_vec", detector.sdet_vec.cpu().numpy())
    emit_trace("TRACE_PY", "pixel_pos_meters", target_coords.cpu().numpy())

    # Airpath and solid angle
    R = torch.norm(target_coords)
    emit_trace("TRACE_PY", "R_distance_meters", R)

    # Solid angle (omega)
    close_distance_m = detector.close_distance
    omega = (pixel_size_m ** 2 * close_distance_m) / (R ** 3)
    emit_trace("TRACE_PY", "omega_pixel_sr", omega)
    emit_trace("TRACE_PY", "close_distance_meters", close_distance_m)

    # Obliquity factor
    obliquity_factor = close_distance_m / R
    emit_trace("TRACE_PY", "obliquity_factor", obliquity_factor)

    # Diffracted direction
    diffracted_vec = target_coords / R
    emit_trace("TRACE_PY", "diffracted_vec", diffracted_vec.cpu().numpy())

    # Incident beam direction (MOSFLM: [1, 0, 0]) - already defined as beam_direction
    incident_vec = beam_direction
    emit_trace("TRACE_PY", "incident_vec", incident_vec.cpu().numpy())

    # Wavelength
    lambda_m = beam_config.wavelength_A * 1e-10
    lambda_A = beam_config.wavelength_A
    emit_trace("TRACE_PY", "lambda_meters", lambda_m)
    emit_trace("TRACE_PY", "lambda_angstroms", lambda_A)

    # Scattering vector: S = (d - i) / λ [in m⁻¹] per spec-a-core.md line 446
    # Note: Variable name "scattering_vec_A_inv" is historical from C code but actually contains m⁻¹ values
    S_per_m = (diffracted_vec - incident_vec) / lambda_m
    emit_trace("TRACE_PY", "scattering_vec_A_inv", S_per_m.cpu().numpy())

    # Get rotated lattice vectors (phi=0, no mosaic)
    # The method returns (N_phi, N_mos, 3) tensors, extract first element for phi=0, mos=0
    (rot_a_all, rot_b_all, rot_c_all), (rot_a_star_all, rot_b_star_all, rot_c_star_all) = crystal.get_rotated_real_vectors(crystal_config)

    # Extract phi=0, mosaic=0 vectors
    rot_a = rot_a_all[0, 0]  # Shape: (3,)
    rot_b = rot_b_all[0, 0]
    rot_c = rot_c_all[0, 0]
    rot_a_star = rot_a_star_all[0, 0]
    rot_b_star = rot_b_star_all[0, 0]
    rot_c_star = rot_c_star_all[0, 0]

    # Crystal stores vectors in Angstroms, but we need to verify units
    # Real vectors are in Angstroms, reciprocal in 1/Angstrom (from C code)
    # The crystal.a, b, c are already in Angstroms per the implementation
    rot_a_A = rot_a  # Already in Angstroms
    rot_b_A = rot_b
    rot_c_A = rot_c
    rot_a_star_per_A = rot_a_star  # Already in 1/Angstrom
    rot_b_star_per_A = rot_b_star
    rot_c_star_per_A = rot_c_star

    emit_trace("TRACE_PY", "rot_a_angstroms", rot_a_A.cpu().numpy())
    emit_trace("TRACE_PY", "rot_b_angstroms", rot_b_A.cpu().numpy())
    emit_trace("TRACE_PY", "rot_c_angstroms", rot_c_A.cpu().numpy())
    emit_trace("TRACE_PY", "rot_a_star_A_inv", rot_a_star_per_A.cpu().numpy())
    emit_trace("TRACE_PY", "rot_b_star_A_inv", rot_b_star_per_A.cpu().numpy())
    emit_trace("TRACE_PY", "rot_c_star_A_inv", rot_c_star_per_A.cpu().numpy())

    # Miller indices (fractional)
    # h = S · a, k = S · b, l = S · c
    # Crystal class stores vectors in ANGSTROMS (both real and reciprocal)
    # We need to convert to meters for the dot product with S_per_m (which is in 1/m)
    rot_a_m = rot_a * 1e-10  # Angstroms to meters
    rot_b_m = rot_b * 1e-10
    rot_c_m = rot_c * 1e-10

    h_frac = torch.dot(S_per_m.flatten(), rot_a_m.flatten())
    k_frac = torch.dot(S_per_m.flatten(), rot_b_m.flatten())
    l_frac = torch.dot(S_per_m.flatten(), rot_c_m.flatten())

    emit_trace("TRACE_PY", "hkl_frac", h_frac, k_frac, l_frac)

    # Miller indices (rounded)
    h_int = torch.round(h_frac).to(torch.long)
    k_int = torch.round(k_frac).to(torch.long)
    l_int = torch.round(l_frac).to(torch.long)
    emit_trace("TRACE_PY", "hkl_rounded", h_int, k_int, l_int)

    # Lattice factors (SQUARE shape)
    Na, Nb, Nc = crystal_config.N_cells

    # Import the production sincg function to ensure trace matches simulator
    from nanobrag_torch.utils.physics import sincg

    # C-Code Reference (from nanoBragg.c, lines 15026-15029):
    # ```c
    # double sincg(double x,double N) {
    #     if(x==0.0) return N;
    #     return sin(x*N)/sin(x);
    # }
    # ```
    # Formula: sincg(π·h, Na) = sin(Na·π·h) / sin(π·h)
    # This is NOT the same as sincg(π·h) / sincg(π·h/Na)!

    F_latt_a = sincg(torch.pi * h_frac, torch.tensor(Na, dtype=dtype, device=device))
    F_latt_b = sincg(torch.pi * k_frac, torch.tensor(Nb, dtype=dtype, device=device))
    F_latt_c = sincg(torch.pi * l_frac, torch.tensor(Nc, dtype=dtype, device=device))

    emit_trace("TRACE_PY", "F_latt_a", F_latt_a)
    emit_trace("TRACE_PY", "F_latt_b", F_latt_b)
    emit_trace("TRACE_PY", "F_latt_c", F_latt_c)

    F_latt = F_latt_a * F_latt_b * F_latt_c
    emit_trace("TRACE_PY", "F_latt", F_latt)

    # Structure factor (default_F for this case, no HKL file)
    F_cell = crystal_config.default_F
    emit_trace("TRACE_PY", "F_cell", F_cell)

    # Intensity before scaling
    I_before_scaling = (F_cell ** 2) * (F_latt ** 2)
    emit_trace("TRACE_PY", "I_before_scaling", I_before_scaling)

    # Scaling parameters
    r_e = 2.8179403227e-15  # Classical electron radius [m]
    r_e_sqr = r_e ** 2
    emit_trace("TRACE_PY", "r_e_meters", r_e)
    emit_trace("TRACE_PY", "r_e_sqr", r_e_sqr)

    # Fluence from BeamConfig (already computed per spec-a-core.md line 517)
    # Do NOT recompute; BeamConfig.__post_init__ applies the spec formula
    # and handles edge cases (flux=0, beamsize clipping, etc.)
    fluence = beam_config.fluence
    emit_trace("TRACE_PY", "fluence_photons_per_m2", fluence)

    # Steps (sources × phi × mosaic × oversample²)
    steps = 1 * crystal_config.phi_steps * crystal_config.mosaic_domains * 1  # oversample=1
    emit_trace("TRACE_PY", "steps", steps)

    # Oversample flags (all zero for this config)
    emit_trace("TRACE_PY", "oversample_thick", 0)
    emit_trace("TRACE_PY", "oversample_polar", 0)
    emit_trace("TRACE_PY", "oversample_omega", 0)

    # Capture fraction (assume 1.0 for no detector absorption modeled)
    capture_fraction = 1.0
    emit_trace("TRACE_PY", "capture_fraction", capture_fraction)

    # Polarization factor
    # For unpolarized (Kahn=0): 0.5 * (1 + cos²(2θ))
    cos_2theta = torch.dot(incident_vec.flatten(), diffracted_vec.flatten())
    polar = 0.5 * (1 + cos_2theta ** 2)
    emit_trace("TRACE_PY", "polar", polar)
    emit_trace("TRACE_PY", "omega_pixel", omega)
    emit_trace("TRACE_PY", "cos_2theta", cos_2theta)

    # Final intensity
    # I_pixel = r_e² * fluence * I_before_scaling / steps * capture * polar * omega
    I_pixel_final = r_e_sqr * fluence * I_before_scaling / steps * capture_fraction * polar * omega
    emit_trace("TRACE_PY", "I_pixel_final", I_pixel_final)

    # Accumulated floatimage (for single pixel this equals I_pixel_final)
    emit_trace("TRACE_PY", "floatimage_accumulated", I_pixel_final)

    print()
    print(f"=== Trace Complete ===")
    print(f"Target pixel: ({target_s}, {target_f})")
    print(f"Final intensity: {I_pixel_final:.15e}")

    # Save trace to file
    out_file = out_dir / f"pixel_{target_s}_{target_f}.log"

    # Re-run trace emission to file
    import io
    import contextlib

    trace_buffer = io.StringIO()
    with contextlib.redirect_stdout(trace_buffer):
        # Re-emit all traces (this is a bit repetitive but ensures file matches stdout)
        emit_trace("TRACE_PY", "fdet_after_rotz", detector.fdet_vec.cpu().numpy())
        emit_trace("TRACE_PY", "sdet_after_rotz", detector.sdet_vec.cpu().numpy())
        emit_trace("TRACE_PY", "odet_after_rotz", detector.odet_vec.cpu().numpy())
        emit_trace("TRACE_PY", "twotheta_axis", twotheta_axis)
        emit_trace("TRACE_PY", "fdet_after_twotheta", detector.fdet_vec.cpu().numpy())
        emit_trace("TRACE_PY", "sdet_after_twotheta", detector.sdet_vec.cpu().numpy())
        emit_trace("TRACE_PY", "odet_after_twotheta", detector.odet_vec.cpu().numpy())
        emit_trace("TRACE_PY", "detector_convention", "MOSFLM")
        emit_trace("TRACE_PY", "angles_rad", f"rotx:{detector_config.detector_rotx_deg * np.pi / 180:.15e}",
                   f"roty:{detector_config.detector_roty_deg * np.pi / 180:.15e}",
                   f"rotz:{detector_config.detector_rotz_deg * np.pi / 180:.15e}",
                   f"twotheta:{detector_config.detector_twotheta_deg * np.pi / 180:.15e}")
        emit_trace("TRACE_PY", "beam_center_m", f"X:{beam_center_f_m:.15e}", f"Y:{beam_center_s_m:.15e}",
                   f"pixel_mm:{detector_config.pixel_size_mm}")
        emit_trace("TRACE_PY", "initial_fdet", detector.fdet_vec.cpu().numpy())
        emit_trace("TRACE_PY", "initial_sdet", detector.sdet_vec.cpu().numpy())
        emit_trace("TRACE_PY", "initial_odet", detector.odet_vec.cpu().numpy())
        emit_trace("TRACE_PY", "Rx", "[1 0 0; 0 1 0; 0 0 1]")
        emit_trace("TRACE_PY", "Ry", "[1 0 0; 0 1 0; 0 0 1]")
        emit_trace("TRACE_PY", "Rz", "[1 0 0; 0 1 0; 0 0 1]")
        emit_trace("TRACE_PY", "R_total", "[1 0 0; 0 1 0; 0 0 1]")
        emit_trace("TRACE_PY", "fdet_after_rotz", detector.fdet_vec.cpu().numpy())
        emit_trace("TRACE_PY", "sdet_after_rotz", detector.sdet_vec.cpu().numpy())
        emit_trace("TRACE_PY", "odet_after_rotz", detector.odet_vec.cpu().numpy())
        emit_trace("TRACE_PY", "twotheta_axis", twotheta_axis)
        emit_trace("TRACE_PY", "fdet_after_twotheta", detector.fdet_vec.cpu().numpy())
        emit_trace("TRACE_PY", "sdet_after_twotheta", detector.sdet_vec.cpu().numpy())
        emit_trace("TRACE_PY", "odet_after_twotheta", detector.odet_vec.cpu().numpy())
        emit_trace("TRACE_PY", "convention_mapping", "Fbeam←Ybeam_mm(+0.5px),Sbeam←Xbeam_mm(+0.5px),beam_vec=[1 0 0]")
        emit_trace("TRACE_PY", "Fbeam_m", beam_center_f_m)
        emit_trace("TRACE_PY", "Sbeam_m", beam_center_s_m)
        emit_trace("TRACE_PY", "distance_m", detector_config.distance_mm / 1000.0)
        emit_trace("TRACE_PY", "term_fast", term_fast.cpu().numpy())
        emit_trace("TRACE_PY", "term_slow", term_slow.cpu().numpy())
        emit_trace("TRACE_PY", "term_beam", term_beam.cpu().numpy())
        emit_trace("TRACE_PY", "pix0_vector", pix0_vector.cpu().numpy())
        emit_trace("TRACE_PY", "pix0_vector_meters", pix0_vector.cpu().numpy())
        emit_trace("TRACE_PY", "fdet_vec", detector.fdet_vec.cpu().numpy())
        emit_trace("TRACE_PY", "sdet_vec", detector.sdet_vec.cpu().numpy())
        emit_trace("TRACE_PY", "pixel_pos_meters", target_coords.cpu().numpy())
        emit_trace("TRACE_PY", "R_distance_meters", R)
        emit_trace("TRACE_PY", "omega_pixel_sr", omega)
        emit_trace("TRACE_PY", "close_distance_meters", close_distance_m)
        emit_trace("TRACE_PY", "obliquity_factor", obliquity_factor)
        emit_trace("TRACE_PY", "diffracted_vec", diffracted_vec.cpu().numpy())
        emit_trace("TRACE_PY", "incident_vec", incident_vec.cpu().numpy())
        emit_trace("TRACE_PY", "lambda_meters", lambda_m)
        emit_trace("TRACE_PY", "lambda_angstroms", lambda_A)
        emit_trace("TRACE_PY", "scattering_vec_A_inv", S_per_m.cpu().numpy())
        emit_trace("TRACE_PY", "rot_a_angstroms", rot_a_A.cpu().numpy())
        emit_trace("TRACE_PY", "rot_b_angstroms", rot_b_A.cpu().numpy())
        emit_trace("TRACE_PY", "rot_c_angstroms", rot_c_A.cpu().numpy())
        emit_trace("TRACE_PY", "rot_a_star_A_inv", rot_a_star_per_A.cpu().numpy())
        emit_trace("TRACE_PY", "rot_b_star_A_inv", rot_b_star_per_A.cpu().numpy())
        emit_trace("TRACE_PY", "rot_c_star_A_inv", rot_c_star_per_A.cpu().numpy())
        emit_trace("TRACE_PY", "hkl_frac", h_frac, k_frac, l_frac)
        emit_trace("TRACE_PY", "hkl_rounded", h_int, k_int, l_int)
        emit_trace("TRACE_PY", "F_latt_a", F_latt_a)
        emit_trace("TRACE_PY", "F_latt_b", F_latt_b)
        emit_trace("TRACE_PY", "F_latt_c", F_latt_c)
        emit_trace("TRACE_PY", "F_latt", F_latt)
        emit_trace("TRACE_PY", "F_cell", F_cell)
        emit_trace("TRACE_PY", "I_before_scaling", I_before_scaling)
        emit_trace("TRACE_PY", "r_e_meters", r_e)
        emit_trace("TRACE_PY", "r_e_sqr", r_e_sqr)
        emit_trace("TRACE_PY", "fluence_photons_per_m2", fluence)
        emit_trace("TRACE_PY", "steps", steps)
        emit_trace("TRACE_PY", "oversample_thick", 0)
        emit_trace("TRACE_PY", "oversample_polar", 0)
        emit_trace("TRACE_PY", "oversample_omega", 0)
        emit_trace("TRACE_PY", "capture_fraction", capture_fraction)
        emit_trace("TRACE_PY", "polar", polar)
        emit_trace("TRACE_PY", "omega_pixel", omega)
        emit_trace("TRACE_PY", "cos_2theta", cos_2theta)
        emit_trace("TRACE_PY", "I_pixel_final", I_pixel_final)
        emit_trace("TRACE_PY", "floatimage_accumulated", I_pixel_final)

    # Write to file
    with open(out_file, 'w') as f:
        f.write(trace_buffer.getvalue())

    print(f"Trace written to: {out_file}")

    # Save metadata
    metadata = {
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "pixel_slow": target_s,
        "pixel_fast": target_f,
        "tag": args.tag,
        "device": str(device),
        "dtype": str(dtype),
        "configuration": {
            "detpixels": 4096,
            "pixel_mm": 0.05,
            "distance_mm": 500.0,
            "wavelength_A": 0.5,
            "cell": "100 100 100 90 90 90",
            "N_cells": "5 5 5",
            "default_F": 100.0,
            "convention": "MOSFLM"
        },
        "final_intensity": float(I_pixel_final.item() if isinstance(I_pixel_final, torch.Tensor) else I_pixel_final)
    }

    metadata_file = out_dir / f"pixel_{target_s}_{target_f}_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"Metadata written to: {metadata_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
