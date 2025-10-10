#!/usr/bin/env python3
"""
Generate PyTorch pixel trace for parity debugging.

Emits TRACE_PY lines matching the C trace schema for direct line-by-line comparison.
Designed for Phase C2 of VECTOR-PARITY-001 vectorization parity regression diagnosis.

Features (Phase E extensions):
  - Oversample support: --oversample N (subpixel sampling grid)
  - Tap collection: --taps f_cell (structured metrics for debugging)
  - JSON output: --json (write tap metrics to structured JSON files)

Usage:
    # Basic trace (legacy, oversample=1)
    python scripts/debug_pixel_trace.py --pixel 2048 2048 --tag ROI_center --out-dir reports/phase_c/traces

    # Tap 4 (F_cell statistics) with oversample=2
    python scripts/debug_pixel_trace.py --pixel 0 0 --tag edge --oversample 2 --taps f_cell --json --out-dir reports/phase_e/py_taps
    python scripts/debug_pixel_trace.py --pixel 2048 2048 --tag centre --oversample 2 --taps f_cell --json --out-dir reports/phase_e/py_taps

    # Multiple taps (future extension)
    python scripts/debug_pixel_trace.py --pixel 0 0 --oversample 2 --taps f_cell,omega --json --out-dir reports/taps
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
    parser.add_argument(
        '--oversample', type=int, default=1, metavar='N',
        help='Subpixel sampling grid size (default: 1, no oversampling)'
    )
    parser.add_argument(
        '--taps', type=str, default=None, metavar='TAP[,TAP...]',
        help='Comma-separated tap selectors (e.g., f_cell,omega). If unspecified, only legacy TRACE output.'
    )
    parser.add_argument(
        '--json', action='store_true',
        help='Write tap metrics to JSON files alongside trace logs'
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


def collect_f_cell_tap(crystal, crystal_config, S_per_m_all, oversample, dtype, device):
    """
    Collect Tap 4 (F_cell statistics) metrics for all subpixels.

    Args:
        crystal: Crystal instance
        crystal_config: CrystalConfig instance
        S_per_m_all: Scattering vectors for all subpixels, shape (oversample, oversample, 3)
        oversample: Subpixel grid size
        dtype: torch dtype
        device: torch device

    Returns:
        dict: Tap 4 metrics matching schema from tap_points.md
    """
    # Get rotated lattice vectors for all phi/mosaic combinations
    (rot_a_all, rot_b_all, rot_c_all), (rot_a_star_all, rot_b_star_all, rot_c_star_all) = \
        crystal.get_rotated_real_vectors(crystal_config)

    # Extract phi=0, mosaic=0 vectors (shape: 3)
    rot_a = rot_a_all[0, 0] * 1e-10  # Å → meters
    rot_b = rot_b_all[0, 0] * 1e-10
    rot_c = rot_c_all[0, 0] * 1e-10

    # Accumulate statistics across all subpixels
    total_lookups = 0
    out_of_bounds_count = 0
    zero_f_count = 0
    f_cell_sum = 0.0

    # HKL bounds (initialize to extremes)
    h_min, h_max = float('inf'), float('-inf')
    k_min, k_max = float('inf'), float('-inf')
    l_min, l_max = float('inf'), float('-inf')

    # Loop over subpixels to collect F_cell statistics
    for sub_s in range(oversample):
        for sub_f in range(oversample):
            # Get scattering vector for this subpixel
            S_per_m = S_per_m_all[sub_s, sub_f]

            # Compute fractional Miller indices
            h_frac = torch.dot(S_per_m.flatten(), rot_a.flatten())
            k_frac = torch.dot(S_per_m.flatten(), rot_b.flatten())
            l_frac = torch.dot(S_per_m.flatten(), rot_c.flatten())

            # Round to nearest integer
            h0 = int(torch.round(h_frac).item())
            k0 = int(torch.round(k_frac).item())
            l0 = int(torch.round(l_frac).item())

            # Update HKL bounds
            h_min = min(h_min, h0)
            h_max = max(h_max, h0)
            k_min = min(k_min, k0)
            k_max = max(k_max, k0)
            l_min = min(l_min, l0)
            l_max = max(l_max, l0)

            total_lookups += 1

            # Check if HKL is in bounds (if HKL data exists)
            if hasattr(crystal, 'hkl_data') and crystal.hkl_data is not None:
                # Get HKL grid bounds from crystal
                h_range = crystal.hkl_data.get('h_range', (h0, h0))
                k_range = crystal.hkl_data.get('k_range', (k0, k0))
                l_range = crystal.hkl_data.get('l_range', (l0, l0))

                in_bounds = (h_range[0] <= h0 <= h_range[1] and
                            k_range[0] <= k0 <= k_range[1] and
                            l_range[0] <= l0 <= l_range[1])

                if not in_bounds:
                    out_of_bounds_count += 1
                    # Out-of-bounds returns default_F
                    f_cell = crystal_config.default_F
                else:
                    # Would query HKL grid here in production
                    # For now, use default_F (since test case has no HKL file)
                    f_cell = crystal_config.default_F
            else:
                # No HKL data: all lookups return default_F
                f_cell = crystal_config.default_F
                # Consider this as "in bounds" since we have no grid to violate

            # Count zero F values
            if abs(f_cell) < 1e-10:
                zero_f_count += 1

            f_cell_sum += f_cell

    # Compute mean F_cell
    mean_f_cell = f_cell_sum / total_lookups if total_lookups > 0 else 0.0

    return {
        'total_lookups': total_lookups,
        'out_of_bounds_count': out_of_bounds_count,
        'zero_f_count': zero_f_count,
        'mean_f_cell': mean_f_cell,
        'hkl_bounds': {
            'h_min': int(h_min) if h_min != float('inf') else 0,
            'h_max': int(h_max) if h_max != float('-inf') else 0,
            'k_min': int(k_min) if k_min != float('inf') else 0,
            'k_max': int(k_max) if k_max != float('-inf') else 0,
            'l_min': int(l_min) if l_min != float('inf') else 0,
            'l_max': int(l_max) if l_max != float('-inf') else 0,
        }
    }


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

    # Parse tap selectors
    enabled_taps = set()
    if args.taps:
        enabled_taps = set(tap.strip() for tap in args.taps.split(','))

    # Configuration matching the 4096² parity case from Phase C1
    # Command: -default_F 100 -cell 100 100 100 90 90 90 -lambda 0.5 -distance 500 -pixel 0.05 -detpixels 4096 -N 5 -convention MOSFLM
    # Now supports --oversample argument (default 1)

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

    # ========== TAP COLLECTION (Phase E Instrumentation) ==========
    tap_metrics = {}

    if 'f_cell' in enabled_taps and args.oversample > 1:
        print()
        print(f"=== Collecting Tap 4 (F_cell statistics) for oversample={args.oversample} ===")

        # Compute subpixel scattering vectors (oversample × oversample grid)
        # Generate subpixel offsets from -0.5 to +0.5 of pixel width
        oversample = args.oversample
        subpixel_offsets = torch.linspace(-0.5, 0.5, oversample, dtype=dtype, device=device)

        # Create meshgrid for subpixel positions (slow, fast)
        sub_s_grid, sub_f_grid = torch.meshgrid(subpixel_offsets, subpixel_offsets, indexing='ij')

        # Compute positions for all subpixels
        # target_coords is the pixel corner; add subpixel offsets scaled by pixel size
        S_per_m_all = torch.zeros((oversample, oversample, 3), dtype=dtype, device=device)

        for sub_s_idx in range(oversample):
            for sub_f_idx in range(oversample):
                # Subpixel position offset in meters
                subpix_offset_s = sub_s_grid[sub_s_idx, sub_f_idx] * pixel_size_m
                subpix_offset_f = sub_f_grid[sub_s_idx, sub_f_idx] * pixel_size_m

                # Compute subpixel position in lab frame
                subpixel_pos = target_coords + subpix_offset_s * detector.sdet_vec + subpix_offset_f * detector.fdet_vec

                # Compute diffracted direction for this subpixel
                R_sub = torch.norm(subpixel_pos)
                diffracted_sub = subpixel_pos / R_sub

                # Compute scattering vector for this subpixel
                S_per_m_all[sub_s_idx, sub_f_idx] = (diffracted_sub - incident_vec) / lambda_m

        # Collect F_cell statistics using production helpers
        f_cell_tap = collect_f_cell_tap(crystal, crystal_config, S_per_m_all, oversample, dtype, device)

        tap_metrics['f_cell_stats'] = {
            'tap_id': 'f_cell_stats',
            'pixel_coords': [target_s, target_f],
            'oversample': oversample,
            'values': f_cell_tap
        }

        # Print summary to stdout
        print(f"  Total HKL lookups: {f_cell_tap['total_lookups']}")
        print(f"  Out-of-bounds count: {f_cell_tap['out_of_bounds_count']}")
        print(f"  Zero F count: {f_cell_tap['zero_f_count']}")
        print(f"  Mean F_cell: {f_cell_tap['mean_f_cell']:.6f}")
        print(f"  HKL bounds: h=[{f_cell_tap['hkl_bounds']['h_min']},{f_cell_tap['hkl_bounds']['h_max']}] "
              f"k=[{f_cell_tap['hkl_bounds']['k_min']},{f_cell_tap['hkl_bounds']['k_max']}] "
              f"l=[{f_cell_tap['hkl_bounds']['l_min']},{f_cell_tap['hkl_bounds']['l_max']}]")

    print()
    print(f"=== Trace Complete ===")
    print(f"Target pixel: ({target_s}, {target_f})")
    print(f"Final intensity: {I_pixel_final:.15e}")
    if tap_metrics:
        print(f"Collected taps: {', '.join(tap_metrics.keys())}")

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

    # Write tap metrics to JSON if requested
    if args.json and tap_metrics:
        for tap_id, tap_data in tap_metrics.items():
            # Add timestamp to tap data
            tap_data['timestamp_utc'] = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

            tap_json_file = out_dir / f"pixel_{target_s}_{target_f}_{tap_id}.json"
            with open(tap_json_file, 'w') as f:
                json.dump(tap_data, f, indent=2)

            print(f"Tap JSON written to: {tap_json_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
