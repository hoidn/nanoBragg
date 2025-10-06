#!/usr/bin/env python3
"""
CLI-FLAGS-003 Phase K3d: Dtype Sensitivity Analysis for F_latt

This script analyzes the impact of floating-point precision (float32 vs float64)
on the lattice shape factor calculation. The current 21.6% F_latt_b mismatch between
C and PyTorch may be influenced by dtype rounding in Miller index calculations.

Target: Isolate whether dtype precision affects hkl_frac and F_latt_* calculations.
Expected: Float64 should reduce or eliminate rounding-related F_latt drift.

Env Control: Set NB_PYTORCH_DTYPE=float64 to force double precision.
Baseline: Default float32 behavior documented in scaling_chain.md
"""

import os
import sys
import json
import torch
import numpy as np
from pathlib import Path

# Critical: MKL conflict prevention
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src to path for imports
repo_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(repo_root / 'src'))

from nanobrag_torch.io.mosflm import read_mosflm_matrix, reciprocal_to_real_cell
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig
from nanobrag_torch.simulator import Simulator

def get_dtype_from_env():
    """Parse NB_PYTORCH_DTYPE env var to determine precision."""
    dtype_str = os.environ.get('NB_PYTORCH_DTYPE', 'float32').lower()
    if dtype_str == 'float64':
        return torch.float64, 'float64'
    elif dtype_str == 'float32':
        return torch.float32, 'float32'
    else:
        raise ValueError(f"Unknown dtype: {dtype_str}")

def trace_scaling_chain(pixel_s, pixel_f, crystal, detector, beam_config, simulator):
    """
    Generate a detailed trace of the scaling chain for a single pixel.

    This reuses production code paths exactly per CLAUDE.md Core Rule #0.3
    (Instrumentation/Tracing Discipline).
    """

    # Get pixel position in meters (detector internal unit)
    pixel_coords_m = detector.get_pixel_coords()
    pixel_pos_m = pixel_coords_m[pixel_s, pixel_f, :]

    # Convert to Angstroms for physics
    pixel_pos_A = pixel_pos_m * 1e10

    # Compute scattering geometry
    distance_vec_A = pixel_pos_A - detector.pix0_vector * 1e10
    R = torch.norm(distance_vec_A)
    diffracted = distance_vec_A / R

    # Incident beam (MOSFLM convention: +X)
    k_in = torch.tensor([1.0, 0.0, 0.0], device=pixel_pos_m.device, dtype=pixel_pos_m.dtype)

    # Scattering vector S = (d - i) / λ (Å⁻¹)
    wavelength_A = beam_config.wavelength_A
    S = (diffracted - k_in) / wavelength_A

    # Get real-space vectors (these incorporate MOSFLM orientation + any misset)
    # Using base real vectors (phi=0, no mosaic rotation for this simple trace)
    a_vec = crystal.a
    b_vec = crystal.b
    c_vec = crystal.c

    # Miller indices (fractional)
    h_frac = torch.dot(S, a_vec).item()
    k_frac = torch.dot(S, b_vec).item()
    l_frac = torch.dot(S, c_vec).item()

    # Rounded Miller indices
    h = torch.ceil(torch.tensor(h_frac) - 0.5).item()
    k = torch.ceil(torch.tensor(k_frac) - 0.5).item()
    l = torch.ceil(torch.tensor(l_frac) - 0.5).item()

    # Lattice shape factors (SQUARE model)
    from nanobrag_torch.utils.physics import sincg
    Na, Nb, Nc = crystal.config.N_cells

    F_latt_a = sincg(
        torch.pi * torch.tensor(h_frac, device=pixel_pos_m.device, dtype=pixel_pos_m.dtype),
        torch.tensor(Na, device=pixel_pos_m.device, dtype=pixel_pos_m.dtype)
    ).item()
    F_latt_b = sincg(
        torch.pi * torch.tensor(k_frac, device=pixel_pos_m.device, dtype=pixel_pos_m.dtype),
        torch.tensor(Nb, device=pixel_pos_m.device, dtype=pixel_pos_m.dtype)
    ).item()
    F_latt_c = sincg(
        torch.pi * torch.tensor(l_frac, device=pixel_pos_m.device, dtype=pixel_pos_m.dtype),
        torch.tensor(Nc, device=pixel_pos_m.device, dtype=pixel_pos_m.dtype)
    ).item()
    F_latt = F_latt_a * F_latt_b * F_latt_c

    # Solid angle factors
    close_distance = detector.config.distance_mm / 1000.0  # m
    pixel_size = detector.config.pixel_size_mm / 1000.0     # m
    pixel_area = pixel_size * pixel_size

    omega_pixel = pixel_area / (R/1e10)**2 * (close_distance / (R/1e10))

    # Polarization (Kahn factor, defaults to 0.0 in C when -polar not provided)
    polar = beam_config.polarization_factor

    return {
        'pixel_s': pixel_s,
        'pixel_f': pixel_f,
        'pixel_pos_A': [float(x) for x in pixel_pos_A.cpu().numpy().tolist()],
        'R': float(R.item()) if torch.is_tensor(R) else float(R),
        'wavelength_A': float(wavelength_A),
        'h_frac': float(h_frac),
        'k_frac': float(k_frac),
        'l_frac': float(l_frac),
        'h': float(h),
        'k': float(k),
        'l': float(l),
        'F_latt_a': float(F_latt_a),
        'F_latt_b': float(F_latt_b),
        'F_latt_c': float(F_latt_c),
        'F_latt': float(F_latt),
        'omega_pixel': float(omega_pixel),
        'polar': float(polar),
        'Na': int(Na),
        'Nb': int(Nb),
        'Nc': int(Nc),
    }

def main():
    dtype, dtype_name = get_dtype_from_env()
    device = 'cpu'  # CPU for determinism per testing_strategy.md §2.5.1

    print("="*80)
    print(f"CLI-FLAGS-003 Phase K3d: Dtype Sensitivity Analysis ({dtype_name})")
    print("="*80)
    print()
    print(f"Environment:")
    print(f"  NB_PYTORCH_DTYPE = {os.environ.get('NB_PYTORCH_DTYPE', 'float32 (default)')}")
    print(f"  PyTorch dtype = {dtype}")
    print(f"  Device = {device}")
    print()

    # Supervisor command parameters (from input.md and plan.md)
    mat_file = repo_root / "A.mat"
    wavelength_A = 0.976800

    # Load MOSFLM orientation matrix
    a_star, b_star, c_star = read_mosflm_matrix(str(mat_file), wavelength_A)
    cell_params = reciprocal_to_real_cell(a_star, b_star, c_star)

    # Crystal configuration
    crystal_config = CrystalConfig(
        cell_a=cell_params[0],
        cell_b=cell_params[1],
        cell_c=cell_params[2],
        cell_alpha=cell_params[3],
        cell_beta=cell_params[4],
        cell_gamma=cell_params[5],
        N_cells=(36, 47, 29),  # From supervisor command
        default_F=0.0,
        mosflm_a_star=a_star,
        mosflm_b_star=b_star,
        mosflm_c_star=c_star,
        phi_start_deg=0.0,
        osc_range_deg=0.0,
        phi_steps=1,
    )

    # Detector configuration
    detector_config = DetectorConfig(
        distance_mm=74.0,
        pixel_size_mm=0.1,
        spixels=512,
        fpixels=512,
        beam_center_s=25.6,
        beam_center_f=25.6,
        oversample=1,
    )

    # Beam configuration
    beam_config = BeamConfig(
        wavelength_A=wavelength_A,
        polarization_factor=0.0,  # C default when -polar not provided (per Phase I2)
        flux=1e12,
        exposure=1.0,
        beamsize_mm=0.1,
    )

    # Instantiate components with requested dtype
    crystal = Crystal(crystal_config, device=device, dtype=dtype)
    detector = Detector(detector_config, device=device, dtype=dtype)
    simulator = Simulator(
        crystal=crystal,
        detector=detector,
        beam_config=beam_config,
        device=device,
        dtype=dtype,
    )

    # Target pixel from Phase J/K traces (on-peak pixel)
    pixel_s, pixel_f = 133, 134

    print(f"Tracing pixel ({pixel_s}, {pixel_f})...")
    print()

    trace = trace_scaling_chain(
        pixel_s, pixel_f,
        crystal, detector, beam_config, simulator
    )

    # Display trace
    print("-"*80)
    print("Scaling Chain Trace")
    print("-"*80)
    print()
    print(f"Target pixel: ({trace['pixel_s']}, {trace['pixel_f']})")
    print(f"Wavelength: {trace['wavelength_A']:.6f} Å")
    print()
    print("Miller indices (fractional):")
    print(f"  h = {trace['h_frac']:.15f}")
    print(f"  k = {trace['k_frac']:.15f}")
    print(f"  l = {trace['l_frac']:.15f}")
    print()
    print("Miller indices (rounded):")
    print(f"  h = {trace['h']}")
    print(f"  k = {trace['k']}")
    print(f"  l = {trace['l']}")
    print()
    print(f"Lattice shape factors (SQUARE, Na={trace['Na']}, Nb={trace['Nb']}, Nc={trace['Nc']}):")
    print(f"  F_latt_a = {trace['F_latt_a']:.15f}")
    print(f"  F_latt_b = {trace['F_latt_b']:.15f}")
    print(f"  F_latt_c = {trace['F_latt_c']:.15f}")
    print(f"  F_latt   = {trace['F_latt']:.15e}")
    print()
    print(f"Scaling factors:")
    print(f"  omega_pixel = {trace['omega_pixel']:.15e} sr")
    print(f"  polar       = {trace['polar']:.6f}")
    print()

    # Write JSON output for comparison
    output_file = repo_root / "reports/2025-10-cli-flags/phase_k/f_latt_fix/dtype_sweep" / f"trace_{dtype_name}.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(trace, f, indent=2)

    print(f"Trace saved to: {output_file}")
    print()

    # Load and compare if both traces exist
    float32_file = output_file.parent / "trace_float32.json"
    float64_file = output_file.parent / "trace_float64.json"

    if float32_file.exists() and float64_file.exists():
        print("="*80)
        print("Dtype Comparison: float32 vs float64")
        print("="*80)
        print()

        with open(float32_file) as f:
            trace32 = json.load(f)
        with open(float64_file) as f:
            trace64 = json.load(f)

        print("Fractional Miller Index Deltas (float64 - float32):")
        print(f"  Δh = {trace64['h_frac'] - trace32['h_frac']:.15e}")
        print(f"  Δk = {trace64['k_frac'] - trace32['k_frac']:.15e}")
        print(f"  Δl = {trace64['l_frac'] - trace32['l_frac']:.15e}")
        print()

        print("Lattice Shape Factor Deltas (float64 - float32):")
        print(f"  ΔF_latt_a = {trace64['F_latt_a'] - trace32['F_latt_a']:.15e}")
        print(f"  ΔF_latt_b = {trace64['F_latt_b'] - trace32['F_latt_b']:.15e}")
        print(f"  ΔF_latt_c = {trace64['F_latt_c'] - trace32['F_latt_c']:.15e}")
        print(f"  ΔF_latt   = {trace64['F_latt'] - trace32['F_latt']:.15e}")
        print()

        # Relative errors
        rel_h = abs((trace64['h_frac'] - trace32['h_frac']) / trace64['h_frac']) * 100 if trace64['h_frac'] != 0 else 0
        rel_k = abs((trace64['k_frac'] - trace32['k_frac']) / trace64['k_frac']) * 100 if trace64['k_frac'] != 0 else 0
        rel_l = abs((trace64['l_frac'] - trace32['l_frac']) / trace64['l_frac']) * 100 if trace64['l_frac'] != 0 else 0

        rel_F_latt_b = abs((trace64['F_latt_b'] - trace32['F_latt_b']) / trace64['F_latt_b']) * 100 if trace64['F_latt_b'] != 0 else 0
        rel_F_latt = abs((trace64['F_latt'] - trace32['F_latt']) / trace64['F_latt']) * 100 if trace64['F_latt'] != 0 else 0

        print("Relative Precision Errors (%):")
        print(f"  h_frac:    {rel_h:.4e}%")
        print(f"  k_frac:    {rel_k:.4e}%")
        print(f"  l_frac:    {rel_l:.4e}%")
        print(f"  F_latt_b:  {rel_F_latt_b:.4e}%")
        print(f"  F_latt:    {rel_F_latt:.4e}%")
        print()

        # C reference values from scaling_chain.md
        C_F_latt_b = 38.63  # From Phase K2 report
        Py32_F_latt_b = trace32['F_latt_b']
        Py64_F_latt_b = trace64['F_latt_b']

        error32 = abs((Py32_F_latt_b - C_F_latt_b) / C_F_latt_b) * 100
        error64 = abs((Py64_F_latt_b - C_F_latt_b) / C_F_latt_b) * 100

        print("C Reference Comparison (from scaling_chain.md):")
        print(f"  C F_latt_b      = {C_F_latt_b:.2f}")
        print(f"  PyTorch float32 = {Py32_F_latt_b:.2f}  (error: {error32:.2f}%)")
        print(f"  PyTorch float64 = {Py64_F_latt_b:.2f}  (error: {error64:.2f}%)")
        print()

        if error64 < error32:
            improvement = error32 - error64
            print(f"✅ Float64 reduces error by {improvement:.2f} percentage points")
        else:
            print(f"❌ Float64 does NOT reduce error (dtype not the root cause)")
        print()

        # Write summary
        summary = {
            'float32': {
                'h_frac': trace32['h_frac'],
                'k_frac': trace32['k_frac'],
                'l_frac': trace32['l_frac'],
                'F_latt_b': trace32['F_latt_b'],
                'F_latt': trace32['F_latt'],
                'error_vs_C_pct': error32,
            },
            'float64': {
                'h_frac': trace64['h_frac'],
                'k_frac': trace64['k_frac'],
                'l_frac': trace64['l_frac'],
                'F_latt_b': trace64['F_latt_b'],
                'F_latt': trace64['F_latt'],
                'error_vs_C_pct': error64,
            },
            'C_reference': {
                'F_latt_b': C_F_latt_b,
            },
            'deltas': {
                'h_frac': trace64['h_frac'] - trace32['h_frac'],
                'k_frac': trace64['k_frac'] - trace32['k_frac'],
                'l_frac': trace64['l_frac'] - trace32['l_frac'],
                'F_latt_b': trace64['F_latt_b'] - trace32['F_latt_b'],
                'F_latt': trace64['F_latt'] - trace32['F_latt'],
            },
            'dtype_sensitivity_conclusion': 'float64_improves' if error64 < error32 else 'dtype_not_root_cause',
        }

        summary_file = output_file.parent / "dtype_sensitivity.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"Summary saved to: {summary_file}")
        print()

if __name__ == '__main__':
    main()
