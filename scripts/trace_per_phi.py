#!/usr/bin/env python3
"""
CLI-FLAGS-003 Phase K3e: Per-φ Miller Index Parity

This script captures Miller index + lattice factor traces for each φ step
(φ_tic=0…9) to diagnose the φ-grid mismatch between C and PyTorch.

Context: PyTorch reports k≈1.9997 (φ=0°) while C reports k≈1.9928 (φ=0.09°),
causing a 21.6% F_latt_b inflation. This per-φ dump will isolate the first φ
where Δk exceeds tolerance.

Usage:
    PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/trace_per_phi.py \\
        --outdir reports/2025-10-cli-flags/phase_k/f_latt_fix/per_phi/

Output:
    - per_phi_pytorch.json: Full per-φ trace data (PyTorch)
    - per_phi_summary.md: Comparison summary with first divergence
    - (C trace expected from instrumented nanoBragg.c separately)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Critical: MKL conflict prevention
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src to path for imports
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / 'src'))

import torch
import numpy as np
from nanobrag_torch.io.mosflm import read_mosflm_matrix, reciprocal_to_real_cell
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig
from nanobrag_torch.utils.physics import sincg


def trace_pixel_per_phi(
    pixel_s, pixel_f,
    crystal, detector, beam_config,
    phi_steps=10, phi_start_deg=0.0, osc_range_deg=0.1,
    device='cpu', dtype=torch.float64
):
    """
    Generate per-φ trace of Miller indices and lattice factors for a single pixel.

    Args:
        pixel_s, pixel_f: Target pixel coordinates
        crystal: Crystal instance
        detector: Detector instance
        beam_config: BeamConfig instance
        phi_steps: Number of φ steps (default 10)
        phi_start_deg: Starting φ angle in degrees (default 0.0)
        osc_range_deg: Oscillation range in degrees (default 0.1)
        device: Torch device
        dtype: Torch dtype

    Returns:
        List of dicts, one per φ tick, containing:
            - phi_tic: φ step index (0…9)
            - phi_deg: φ angle in degrees
            - h_frac, k_frac, l_frac: Fractional Miller indices
            - h, k, l: Rounded Miller indices
            - F_latt_a, F_latt_b, F_latt_c: Lattice shape factors
            - F_latt: Product of shape factors
    """

    # Get pixel position (reuse production code per CLAUDE.md tracing discipline)
    pixel_coords_m = detector.get_pixel_coords()
    pixel_pos_m = pixel_coords_m[pixel_s, pixel_f, :]
    pixel_pos_A = pixel_pos_m * 1e10  # Convert meters → Angstroms

    # Scattering geometry (fixed for this pixel)
    distance_vec_A = pixel_pos_A - detector.pix0_vector * 1e10
    R = torch.norm(distance_vec_A)
    diffracted = distance_vec_A / R

    # Incident beam (MOSFLM convention: +X)
    k_in = torch.tensor([1.0, 0.0, 0.0], device=device, dtype=dtype)

    # Scattering vector S = (d - i) / λ
    wavelength_A = beam_config.wavelength_A
    S = (diffracted - k_in) / wavelength_A

    # Lattice parameters
    Na, Nb, Nc = crystal.config.N_cells

    # Spindle axis (from supervisor command: -spindle_axis -1 0 0)
    spindle_axis = torch.tensor([-1.0, 0.0, 0.0], device=device, dtype=dtype)
    spindle_axis = spindle_axis / torch.norm(spindle_axis)  # Ensure unit

    results = []

    for phi_tic in range(phi_steps):
        # Compute φ for this step (matching C loop behavior)
        # C-code: for (phi_tic=0; phi_tic<phisteps; phi_tic++) { phi = phi0 + osc*phi_tic; }
        phi_frac = phi_tic / max(1, phi_steps - 1) if phi_steps > 1 else 0.0
        phi_deg = phi_start_deg + osc_range_deg * phi_frac
        phi_rad = torch.deg2rad(torch.tensor(phi_deg, device=device, dtype=dtype))

        # Rotation matrix around spindle axis
        # Rodrigues formula: R = I + sin(θ)K + (1-cos(θ))K²
        # where K is the skew-symmetric cross-product matrix of the spindle axis
        c = torch.cos(phi_rad)
        s = torch.sin(phi_rad)
        ux, uy, uz = spindle_axis[0], spindle_axis[1], spindle_axis[2]

        rot_matrix = torch.tensor([
            [c + ux**2*(1-c),     ux*uy*(1-c) - uz*s,  ux*uz*(1-c) + uy*s],
            [uy*ux*(1-c) + uz*s,  c + uy**2*(1-c),     uy*uz*(1-c) - ux*s],
            [uz*ux*(1-c) - uy*s,  uz*uy*(1-c) + ux*s,  c + uz**2*(1-c)]
        ], device=device, dtype=dtype)

        # Get base real-space vectors (with MOSFLM orientation + misset, no phi yet)
        a_base = crystal.a
        b_base = crystal.b
        c_base = crystal.c

        # Apply phi rotation
        a_rot = torch.matmul(rot_matrix, a_base)
        b_rot = torch.matmul(rot_matrix, b_base)
        c_rot = torch.matmul(rot_matrix, c_base)

        # Miller indices (fractional)
        h_frac = torch.dot(S, a_rot).item()
        k_frac = torch.dot(S, b_rot).item()
        l_frac = torch.dot(S, c_rot).item()

        # Rounded Miller indices (C convention: ceil(x - 0.5))
        h = torch.ceil(torch.tensor(h_frac) - 0.5).item()
        k = torch.ceil(torch.tensor(k_frac) - 0.5).item()
        l = torch.ceil(torch.tensor(l_frac) - 0.5).item()

        # Lattice shape factors (SQUARE model, matching current Simulator)
        F_latt_a = sincg(
            torch.pi * torch.tensor(h_frac, device=device, dtype=dtype),
            torch.tensor(Na, device=device, dtype=dtype)
        ).item()
        F_latt_b = sincg(
            torch.pi * torch.tensor(k_frac, device=device, dtype=dtype),
            torch.tensor(Nb, device=device, dtype=dtype)
        ).item()
        F_latt_c = sincg(
            torch.pi * torch.tensor(l_frac, device=device, dtype=dtype),
            torch.tensor(Nc, device=device, dtype=dtype)
        ).item()
        F_latt = F_latt_a * F_latt_b * F_latt_c

        results.append({
            'phi_tic': phi_tic,
            'phi_deg': float(phi_deg),
            'h_frac': float(h_frac),
            'k_frac': float(k_frac),
            'l_frac': float(l_frac),
            'h': int(h),
            'k': int(k),
            'l': int(l),
            'F_latt_a': float(F_latt_a),
            'F_latt_b': float(F_latt_b),
            'F_latt_c': float(F_latt_c),
            'F_latt': float(F_latt),
        })

    return results


def main():
    parser = argparse.ArgumentParser(
        description='CLI-FLAGS-003 Phase K3e: Per-φ Miller index parity'
    )
    parser.add_argument(
        '--outdir',
        type=Path,
        default=Path('reports/2025-10-cli-flags/phase_k/f_latt_fix/per_phi'),
        help='Output directory for per-φ traces'
    )
    parser.add_argument(
        '--pixel-s',
        type=int,
        default=133,
        help='Slow pixel coordinate (default: 133, from Phase K traces)'
    )
    parser.add_argument(
        '--pixel-f',
        type=int,
        default=134,
        help='Fast pixel coordinate (default: 134, from Phase K traces)'
    )
    args = parser.parse_args()

    # Use float64 for deterministic debugging
    dtype = torch.float64
    device = 'cpu'

    print("="*80)
    print("CLI-FLAGS-003 Phase K3e: Per-φ Miller Index Parity")
    print("="*80)
    print()
    print(f"Configuration:")
    print(f"  Output directory: {args.outdir}")
    print(f"  Target pixel: ({args.pixel_s}, {args.pixel_f})")
    print(f"  Dtype: {dtype}")
    print(f"  Device: {device}")
    print()

    # Supervisor command parameters
    mat_file = repo_root / "A.mat"
    wavelength_A = 0.976800

    # Load MOSFLM orientation matrix
    a_star, b_star, c_star = read_mosflm_matrix(str(mat_file), wavelength_A)
    cell_params = reciprocal_to_real_cell(a_star, b_star, c_star)

    # Crystal configuration (supervisor command)
    crystal_config = CrystalConfig(
        cell_a=cell_params[0],
        cell_b=cell_params[1],
        cell_c=cell_params[2],
        cell_alpha=cell_params[3],
        cell_beta=cell_params[4],
        cell_gamma=cell_params[5],
        N_cells=(36, 47, 29),
        default_F=0.0,
        mosflm_a_star=a_star,
        mosflm_b_star=b_star,
        mosflm_c_star=c_star,
        phi_start_deg=0.0,
        osc_range_deg=0.1,
        phi_steps=10,
    )

    # Detector configuration (from supervisor command via pix0_vector override)
    # NOTE: These beam_center values are derived from the pix0_vector calculation
    # to match the supervisor command geometry
    detector_config = DetectorConfig(
        distance_mm=231.274660,
        pixel_size_mm=0.172,
        spixels=2527,
        fpixels=2463,
        beam_center_s=213.907080,  # mm (Xbeam in MOSFLM)
        beam_center_f=217.742295,  # mm (Ybeam in MOSFLM)
        oversample=1,
    )

    # Beam configuration
    beam_config = BeamConfig(
        wavelength_A=wavelength_A,
        polarization_factor=0.0,  # C default when -polar not provided
        flux=1e18,
        exposure=1.0,
        beamsize_mm=1.0,
    )

    # Instantiate components
    crystal = Crystal(crystal_config, device=device, dtype=dtype)
    detector = Detector(detector_config, device=device, dtype=dtype)

    print(f"Tracing pixel ({args.pixel_s}, {args.pixel_f}) across φ steps...")
    print()

    # Generate per-φ trace
    per_phi_data = trace_pixel_per_phi(
        args.pixel_s, args.pixel_f,
        crystal, detector, beam_config,
        phi_steps=10,
        phi_start_deg=0.0,
        osc_range_deg=0.1,
        device=device,
        dtype=dtype
    )

    # Create output directory
    args.outdir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')

    # Write JSON output
    json_file = args.outdir / f'per_phi_pytorch_{timestamp}.json'
    with open(json_file, 'w') as f:
        json.dump({
            'metadata': {
                'timestamp': timestamp,
                'pixel_s': args.pixel_s,
                'pixel_f': args.pixel_f,
                'phi_steps': 10,
                'phi_start_deg': 0.0,
                'osc_range_deg': 0.1,
                'dtype': str(dtype),
                'device': device,
            },
            'traces': per_phi_data,
        }, f, indent=2)

    print(f"✅ PyTorch trace saved to: {json_file}")
    print()

    # Display summary table
    print("-"*80)
    print("Per-φ Trace Summary (PyTorch)")
    print("-"*80)
    print()
    print(f"{'φ_tic':<7} {'φ (deg)':<10} {'h_frac':<12} {'k_frac':<12} {'l_frac':<12} {'F_latt_b':<12} {'F_latt':<14}")
    print("-"*80)
    for entry in per_phi_data:
        print(f"{entry['phi_tic']:<7} {entry['phi_deg']:<10.6f} "
              f"{entry['h_frac']:<12.6f} {entry['k_frac']:<12.6f} {entry['l_frac']:<12.6f} "
              f"{entry['F_latt_b']:<12.6f} {entry['F_latt']:<14.6e}")
    print()

    # Write summary markdown
    summary_file = args.outdir / f'per_phi_summary_{timestamp}.md'
    with open(summary_file, 'w') as f:
        f.write(f"# CLI-FLAGS-003 Phase K3e: Per-φ Parity Summary\n\n")
        f.write(f"**Generated:** {timestamp}  \n")
        f.write(f"**Target Pixel:** ({args.pixel_s}, {args.pixel_f})  \n")
        f.write(f"**Configuration:** φ ∈ [0°, 0.1°], 10 steps  \n\n")

        f.write("## PyTorch Trace\n\n")
        f.write("| φ_tic | φ (deg) | h_frac | k_frac | l_frac | F_latt_b | F_latt |\n")
        f.write("|-------|---------|--------|--------|--------|----------|--------|\n")
        for entry in per_phi_data:
            f.write(f"| {entry['phi_tic']} | {entry['phi_deg']:.6f} | "
                   f"{entry['h_frac']:.6f} | {entry['k_frac']:.6f} | {entry['l_frac']:.6f} | "
                   f"{entry['F_latt_b']:.6f} | {entry['F_latt']:.6e} |\n")

        f.write("\n## Next Actions\n\n")
        f.write("1. Instrument C code to emit matching per-φ trace\n")
        f.write("2. Run comparison to identify first φ where Δk > 5e-4\n")
        f.write("3. Proceed to Phase K3f φ sampling fix\n")

    print(f"✅ Summary markdown saved to: {summary_file}")
    print()
    print("="*80)
    print("Next Steps:")
    print("="*80)
    print()
    print("1. Instrument C code (golden_suite_generator/nanoBragg.c) to log:")
    print("   TRACE_C_PHI φ_tic=<idx> phi_deg=<angle> k=<val> F_latt_b=<val>")
    print()
    print("2. Rebuild: make -C golden_suite_generator")
    print()
    print("3. Run C with supervisor command, capture stdout → per_phi_c.log")
    print()
    print("4. Compare C vs PyTorch traces to find first divergence")
    print()

if __name__ == '__main__':
    main()
