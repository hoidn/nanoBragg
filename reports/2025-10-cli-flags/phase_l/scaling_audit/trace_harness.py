#!/usr/bin/env python
"""
Phase L2b PyTorch Scaling Trace Harness

Captures the PyTorch side of the scaling chain comparison for supervisor command.
Mirrors the C trace fields from reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log.

Date: 2025-10-17
Engineer: Ralph (loop i=62, evidence-only mode)
Plan Reference: plans/active/cli-noise-pix0/plan.md Phase L2b
"""

import argparse
import json
import sys
import platform
import os
import torch
from pathlib import Path
from datetime import datetime

# Set KMP env before torch import (defensive re-check)
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Ensure editable install is used
if 'nanobrag_torch' not in sys.modules:
    # PYTHONPATH=src should be set externally per input.md How-To Step 3
    pass

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.io.mosflm import read_mosflm_matrix, reciprocal_to_real_cell
from nanobrag_torch.io.hkl import read_hkl_file


def create_parser():
    """CLI for trace harness per input.md Step 2."""
    parser = argparse.ArgumentParser(description="PyTorch scaling trace harness")
    parser.add_argument('--pixel', type=int, nargs=2, required=True, metavar=('SLOW', 'FAST'),
                        help='Pixel coordinates to trace (slow, fast)')
    parser.add_argument('--out', type=str, required=True,
                        help='Output trace filename (e.g., trace_py_scaling.log)')
    parser.add_argument('--config', type=str, choices=['supervisor'], required=True,
                        help='Config preset to use (supervisor = CLI-FLAGS-003 supervisor command)')
    parser.add_argument('--device', type=str, default='cpu',
                        help='Device (cpu or cuda)')
    parser.add_argument('--dtype', type=str, default='float32', choices=['float32', 'float64'],
                        help='Tensor dtype (default float32)')
    parser.add_argument('--phi-mode', type=str, default='spec', choices=['spec', 'c-parity'],
                        help='Phi carryover mode: spec=compliant (default), c-parity=emulate C bug')
    parser.add_argument('--emit-rot-stars', action='store_true',
                        help='Emit per-phi real-space vectors (ap/bp/cp) via TRACE_PY_ROTSTAR lines')
    return parser


def get_supervisor_params(dtype, device):
    """
    Return supervisor command parameter dict (not yet instantiated as config objects).

    Per input.md Step 3.
    """
    # Supervisor command parameters (from phase_i/supervisor_command/README.md:33-75)
    return {
        'crystal': {
            'misset_deg': (0.0, 0.0, 0.0),
            'phi_start_deg': 0.0,
            'osc_range_deg': 0.1,
            'phi_steps': 10,
            'spindle_axis': torch.tensor([-1.0, 0.0, 0.0], dtype=dtype, device=device),
            'mosaic_spread_deg': 0.0,
            'mosaic_domains': 1,
            'mosaic_seed': -12345678,
            'N_cells': (36, 47, 29),
            'default_F': 0.0  # Using HKL file
        },
        'detector': {
            'distance_mm': 231.274660,
            'pixel_size_mm': 0.172,
            'spixels': 2527,
            'fpixels': 2463,
            'beam_center_s': 213.907080,  # Ybeam in mm
            'beam_center_f': 217.742295,  # Xbeam in mm
            'detector_rotx_deg': 0.0,
            'detector_roty_deg': 0.0,
            'detector_rotz_deg': 0.0,
            'detector_twotheta_deg': 0.0,
            'detector_convention': DetectorConvention.CUSTOM,
            'detector_pivot': DetectorPivot.SAMPLE,
            'oversample': 1,
            # Custom detector vectors (per supervisor command)
            'custom_fdet_vector': (0.999982, -0.005998, -0.000118),
            'custom_sdet_vector': (-0.005998, -0.999970, -0.004913),
            'custom_odet_vector': (-0.000088, 0.004914, -0.999988),
            'custom_beam_vector': (0.00051387949, 0.0, -0.99999986),
            # Custom pix0 override (mm→m conversion)
            'pix0_override_m': (-0.216336293, 0.215205512, -0.230200866)
        },
        'beam': {
            'wavelength_A': 0.9768,
            'polarization_factor': 0.0,  # Kahn factor = 0.0 per c_stdout line 132
            'flux': 1e18,
            'exposure': 1.0,
            'beamsize_mm': 1.0
        }
    }



def main():
    parser = create_parser()
    args = parser.parse_args()

    # Resolve dtype and device (Step 3)
    dtype = torch.float32 if args.dtype == 'float32' else torch.float64
    device = torch.device(args.device)

    # Log environment (Step 9 per input.md)
    env_info = {
        'python_version': sys.version,
        'torch_version': torch.__version__,
        'platform': platform.platform(),
        'cuda_available': torch.cuda.is_available(),
        'device': str(device),
        'dtype': args.dtype,
        'git_sha': os.popen('git rev-parse HEAD').read().strip(),
        'timestamp_iso': datetime.utcnow().isoformat() + 'Z'
    }

    env_path = Path('reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_env.json')
    with open(env_path, 'w') as f:
        json.dump(env_info, f, indent=2)

    # Load configuration parameters (Step 3)
    if args.config == 'supervisor':
        params = get_supervisor_params(dtype, device)
    else:
        raise ValueError(f"Unknown config: {args.config}")

    # Load MOSFLM matrix (Step 3)
    mat_path = Path('A.mat')
    if not mat_path.exists():
        raise FileNotFoundError(f"A.mat not found in current directory: {Path.cwd()}")

    # Note: wavelength is already in params['beam']['wavelength_A']
    a_star, b_star, c_star = read_mosflm_matrix(str(mat_path), params['beam']['wavelength_A'])

    # Extract cell parameters from reciprocal vectors
    cell_params = reciprocal_to_real_cell(a_star, b_star, c_star)
    cell_a, cell_b, cell_c, cell_alpha, cell_beta, cell_gamma = cell_params

    # Build crystal config with cell params and MOSFLM vectors
    # Each MOSFLM reciprocal vector must be assigned to its own config field
    # (not packed into a single list) so Crystal uses the specified orientation
    # Apply phi carryover mode per input.md Phase M1 (2025-10-07)
    crystal_config = CrystalConfig(
        cell_a=cell_a,
        cell_b=cell_b,
        cell_c=cell_c,
        cell_alpha=cell_alpha,
        cell_beta=cell_beta,
        cell_gamma=cell_gamma,
        mosflm_a_star=torch.tensor(a_star, dtype=dtype, device=device),
        mosflm_b_star=torch.tensor(b_star, dtype=dtype, device=device),
        mosflm_c_star=torch.tensor(c_star, dtype=dtype, device=device),
        phi_carryover_mode=args.phi_mode,  # Phase M1: route supervisor override
        **params['crystal']
    )

    # Build detector and beam configs
    detector_config = DetectorConfig(**params['detector'])
    beam_config = BeamConfig(**params['beam'])

    # Load HKL file (Step 3)
    hkl_path = Path('scaled.hkl')
    if not hkl_path.exists():
        raise FileNotFoundError(f"scaled.hkl not found in current directory: {Path.cwd()}")

    # Read HKL grid (returns tensor + metadata dict)
    F_grid_tensor, hkl_metadata = read_hkl_file(str(hkl_path), default_F=0.0, device=device, dtype=dtype)

    # Extract metadata for crystal configuration
    h_min = hkl_metadata['h_min']
    h_max = hkl_metadata['h_max']
    k_min = hkl_metadata['k_min']
    k_max = hkl_metadata['k_max']
    l_min = hkl_metadata['l_min']
    l_max = hkl_metadata['l_max']
    h_range = h_max - h_min + 1
    k_range = k_max - k_min + 1
    l_range = l_max - l_min + 1

    # Snapshot config (Step 4 per input.md)
    config_snapshot = {
        'crystal': {
            'N_cells': crystal_config.N_cells,
            'phi_start_deg': crystal_config.phi_start_deg,
            'osc_range_deg': crystal_config.osc_range_deg,
            'phi_steps': crystal_config.phi_steps,
            'mosaic_spread_deg': crystal_config.mosaic_spread_deg,
            'mosaic_domains': crystal_config.mosaic_domains,
            'spindle_axis': crystal_config.spindle_axis.tolist(),
            'phi_carryover_mode': crystal_config.phi_carryover_mode
        },
        'detector': {
            'distance_mm': detector_config.distance_mm,
            'pixel_size_mm': detector_config.pixel_size_mm,
            'spixels': detector_config.spixels,
            'fpixels': detector_config.fpixels,
            'beam_center_s': detector_config.beam_center_s,
            'beam_center_f': detector_config.beam_center_f,
            'convention': str(detector_config.detector_convention),
            'pivot': str(detector_config.detector_pivot),
            'oversample': detector_config.oversample
        },
        'beam': {
            'wavelength_A': beam_config.wavelength_A,
            'polarization_factor': beam_config.polarization_factor,
            'flux': beam_config.flux,
            'exposure': beam_config.exposure,
            'beamsize_mm': beam_config.beamsize_mm
        },
        'hkl': {
            'path': str(hkl_path),
            'h_range': (h_min, h_min + h_range),
            'k_range': (k_min, k_min + k_range),
            'l_range': (l_min, l_min + l_range)
        }
    }

    config_path = Path('reports/2025-10-cli-flags/phase_l/scaling_audit/config_snapshot.json')
    with open(config_path, 'w') as f:
        json.dump(config_snapshot, f, indent=2)

    # Instantiate components (Step 5 per input.md, honour -nonoise)
    detector = Detector(detector_config, dtype=dtype, device=device)
    crystal = Crystal(crystal_config, dtype=dtype, device=device)

    # Attach HKL grid and metadata to Crystal (Phase L2b fix)
    # Crystal.get_structure_factor consults hkl_data and hkl_metadata, not ad-hoc attributes
    crystal.hkl_data = F_grid_tensor
    crystal.hkl_metadata = hkl_metadata

    # Run simulator with debug_config to capture live TRACE_PY output (Step 5)
    # Per Attempt #67 (2025-10-06): Simulator with debug_config={'trace_pixel': [s, f]}
    # automatically emits TRACE_PY lines to stdout containing real computed values
    # Phase M2 (2025-12-06): Add emit_rot_stars flag to enable TRACE_PY_ROTSTAR output
    slow, fast = args.pixel
    debug_config = {
        'trace_pixel': [slow, fast],
        'emit_rot_stars': args.emit_rot_stars
    }

    simulator = Simulator(
        crystal, detector,
        beam_config=beam_config,
        dtype=dtype, device=device,
        debug_config=debug_config
    )

    # Capture stdout during simulation run (Step 6 per input.md)
    # Use contextlib.redirect_stdout to capture TRACE_PY output
    import io
    from contextlib import redirect_stdout

    stdout_capture = io.StringIO()
    with redirect_stdout(stdout_capture):
        intensities = simulator.run()

    # Extract TRACE_PY lines from captured output (Step 7)
    trace_lines = []
    trace_py_phi_lines = []
    for line in stdout_capture.getvalue().splitlines():
        if line.startswith('TRACE_PY_PHI'):
            trace_py_phi_lines.append(line)
        elif line.startswith('TRACE_PY'):  # Includes TRACE_PY:, TRACE_PY_TRICUBIC, etc.
            trace_lines.append(line)

    if not trace_lines:
        raise RuntimeError("No TRACE_PY output captured. Simulator may not have emitted trace for pixel.")

    # Write main trace to file (Step 8)
    trace_path = Path(args.out)
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    with open(trace_path, 'w') as f:
        f.write('\n'.join(trace_lines))
        f.write('\n')

    # Write per-φ trace lines if captured
    if trace_py_phi_lines:
        phi_trace_name = args.out.replace('.log', '_per_phi.log')
        phi_trace_path = Path('reports/2025-10-cli-flags/phase_l/per_phi') / phi_trace_name
        phi_trace_path.parent.mkdir(parents=True, exist_ok=True)

        with open(phi_trace_path, 'w') as f:
            f.write('\n'.join(trace_py_phi_lines))
            f.write('\n')

        # Parse per-φ lines into structured JSON
        per_phi_data = []
        for line in trace_py_phi_lines:
            # Parse: TRACE_PY_PHI phi_tic=0 phi_deg=0 k_frac=-3.857... F_latt_b=1.779... F_latt=-0.0625...
            parts = line.split()
            if len(parts) >= 6:
                entry = {}
                for part in parts[1:]:  # Skip "TRACE_PY_PHI" prefix
                    if '=' in part:
                        key, value = part.split('=', 1)
                        # Convert to appropriate type
                        if key in ['phi_tic']:
                            entry[key] = int(value)
                        else:
                            entry[key] = float(value)
                per_phi_data.append(entry)

        # Write structured JSON
        json_name = args.out.replace('.log', '_per_phi.json')
        json_path = Path('reports/2025-10-cli-flags/phase_l/per_phi') / json_name

        timestamp = datetime.utcnow().isoformat() + 'Z'
        json_output = {
            'timestamp': timestamp,
            'pixel': {'slow': slow, 'fast': fast},
            'config': args.config,
            'device': str(device),
            'dtype': args.dtype,
            'per_phi_entries': per_phi_data
        }

        with open(json_path, 'w') as f:
            json.dump(json_output, f, indent=2)

        print(f"Per-φ trace written to {phi_trace_path}")
        print(f"Per-φ JSON written to {json_path}")
        print(f"Captured {len(trace_py_phi_lines)} TRACE_PY_PHI lines")

    # Extract final intensity for verification
    pixel_intensity = intensities[slow, fast].item()

    print(f"Main trace written to {trace_path}")
    print(f"Environment snapshot: {env_path}")
    print(f"Config snapshot: {config_path}")
    print(f"Captured {len(trace_lines)} TRACE_PY lines")
    print(f"\nPixel ({slow}, {fast}) final intensity: {pixel_intensity:.15g}")


if __name__ == '__main__':
    main()
