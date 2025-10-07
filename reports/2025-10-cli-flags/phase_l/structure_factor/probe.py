#!/usr/bin/env python
"""
Structure-Factor Coverage Probe for Supervisor Pixel
CLI-FLAGS-003 Phase L3a Evidence Gathering

Purpose:
    Verify whether the supervisor pixel (-7,-1,-14) exists in scaled.hkl or Fdump.bin
    and determine the structure factor value PyTorch retrieves for this reflection.

Usage:
    KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/structure_factor/probe.py \
        --pixel 685 1039 \
        --hkl scaled.hkl \
        --fdump golden_suite_generator/Fdump.bin \
        --fdump tmp/Fdump.bin \
        --dtype float64 \
        --device cpu

Outputs:
    - probe.log: Structured log with HKL grid coverage, amplitude queries, and metadata
    - analysis.md: Summary comparing PyTorch retrieval against C reference (F_cell=190.27)
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime
import platform

import torch

# Ensure repo install is in place per project hygiene rules
try:
    from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention, DetectorPivot
    from nanobrag_torch.models.crystal import Crystal
    from nanobrag_torch.models.detector import Detector
    from nanobrag_torch.io.hkl import read_hkl_file, read_fdump
    from nanobrag_torch.io.mosflm import read_mosflm_matrix, reciprocal_to_real_cell
except ImportError as e:
    print(f"ERROR: Failed to import nanobrag_torch modules. Ensure editable install: pip install -e .", file=sys.stderr)
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)


def create_parser():
    parser = argparse.ArgumentParser(description="Structure-factor probe for Phase L3a")
    parser.add_argument('--pixel', nargs=2, type=int, required=True,
                        metavar=('SLOW', 'FAST'),
                        help='Supervisor pixel coordinates (slow, fast)')
    parser.add_argument('--hkl', type=str, required=True,
                        help='Path to HKL file')
    parser.add_argument('--fdump', action='append', default=[],
                        help='Path to Fdump binary (can specify multiple)')
    parser.add_argument('--dtype', type=str, default='float64',
                        choices=['float32', 'float64'],
                        help='PyTorch dtype for numerical precision')
    parser.add_argument('--device', type=str, default='cpu',
                        choices=['cpu', 'cuda'],
                        help='Device for tensor operations')
    return parser


def get_supervisor_params(dtype, device):
    """
    Extract canonical configuration from the scaling audit harness.

    Source: reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:60-103
    """
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
            'beam_center_s': 213.907080,
            'beam_center_f': 217.742295,
            'detector_rotx_deg': 0.0,
            'detector_roty_deg': 0.0,
            'detector_rotz_deg': 0.0,
            'detector_twotheta_deg': 0.0,
            'detector_convention': DetectorConvention.CUSTOM,
            'detector_pivot': DetectorPivot.SAMPLE,
            'oversample': 1,
            'custom_fdet_vector': (0.999982, -0.005998, -0.000118),
            'custom_sdet_vector': (-0.005998, -0.999970, -0.004913),
            'custom_odet_vector': (-0.000088, 0.004914, -0.999988),
            'custom_beam_vector': (0.00051387949, 0.0, -0.99999986),
            'pix0_override_m': (-0.216336293, 0.215205512, -0.230200866)
        },
        'beam': {
            'wavelength_A': 0.9768,
            'polarization_factor': 0.0,
            'flux': 1e18,
            'exposure': 1.0,
            'beamsize_mm': 1.0
        }
    }


def main():
    parser = create_parser()
    args = parser.parse_args()

    # Resolve paths and parameters
    pixel_slow, pixel_fast = args.pixel
    hkl_path = Path(args.hkl)
    fdump_paths = [Path(p) for p in args.fdump]
    dtype = torch.float32 if args.dtype == 'float32' else torch.float64
    device = torch.device(args.device)

    # Create output directory
    out_dir = Path(__file__).parent
    log_path = out_dir / 'probe.log'

    # Start logging
    log_lines = []
    def log(msg):
        print(msg)
        log_lines.append(msg)

    log("="*80)
    log("Structure-Factor Coverage Probe")
    log("CLI-FLAGS-003 Phase L3a Evidence")
    log("="*80)
    log("")

    # Record environment
    git_sha = None
    try:
        import subprocess
        git_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                         stderr=subprocess.DEVNULL).decode().strip()
    except:
        git_sha = "unknown"

    log(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    log(f"Git SHA: {git_sha}")
    log(f"Torch version: {torch.__version__}")
    log(f"Platform: {platform.platform()}")
    log(f"Device: {device}")
    log(f"Dtype: {dtype}")
    log("")

    # Load supervisor configuration
    log("Loading supervisor command configuration...")
    params = get_supervisor_params(dtype, device)

    # Load MOSFLM matrix
    mat_path = Path('A.mat')
    if not mat_path.exists():
        log(f"ERROR: A.mat not found in {Path.cwd()}")
        sys.exit(1)

    a_star, b_star, c_star = read_mosflm_matrix(str(mat_path), params['beam']['wavelength_A'])
    cell_params = reciprocal_to_real_cell(a_star, b_star, c_star)
    cell_a, cell_b, cell_c, cell_alpha, cell_beta, cell_gamma = cell_params

    # Build crystal config
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
        **params['crystal']
    )

    log("Crystal config initialized")
    log("")

    # Query target Miller index from C trace
    # Source: reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:143-164
    target_hkl = (-7, -1, -14)
    c_reference_F = 190.27

    log(f"Target Miller index: h={target_hkl[0]}, k={target_hkl[1]}, l={target_hkl[2]}")
    log(f"C reference F_cell: {c_reference_F}")
    log("")

    # Test HKL file
    log("="*80)
    log(f"Source 1: HKL file ({hkl_path})")
    log("="*80)

    if not hkl_path.exists():
        log(f"SKIP: File not found")
    else:
        try:
            F_grid, metadata = read_hkl_file(str(hkl_path), default_F=0.0, device=device, dtype=dtype)

            h_min, h_max = metadata['h_min'], metadata['h_max']
            k_min, k_max = metadata['k_min'], metadata['k_max']
            l_min, l_max = metadata['l_min'], metadata['l_max']

            log(f"Grid shape: {F_grid.shape}")
            log(f"H range: [{h_min}, {h_max}]")
            log(f"K range: [{k_min}, {k_max}]")
            log(f"L range: [{l_min}, {l_max}]")

            # Check if target is in range
            h, k, l = target_hkl
            in_range = (h_min <= h <= h_max and
                       k_min <= k <= k_max and
                       l_min <= l <= l_max)

            log(f"Target in range: {in_range}")

            if in_range:
                # Create temporary crystal instance and attach HKL data
                crystal = Crystal(crystal_config)
                crystal.hkl_data = F_grid
                crystal.hkl_metadata = metadata

                # Query structure factor
                h_t = torch.tensor([h], dtype=dtype, device=device)
                k_t = torch.tensor([k], dtype=dtype, device=device)
                l_t = torch.tensor([l], dtype=dtype, device=device)

                F_result = crystal.get_structure_factor(h_t, k_t, l_t)
                F_value = F_result[0].item()

                log(f"Retrieved F_cell: {F_value}")
                log(f"Delta from C: {F_value - c_reference_F}")
            else:
                log("Target reflection is OUT OF RANGE")

        except Exception as e:
            log(f"ERROR reading HKL: {e}")

        log("")

    # Test Fdump files
    for i, fdump_path in enumerate(fdump_paths, 1):
        log("="*80)
        log(f"Source {i+1}: Fdump binary ({fdump_path})")
        log("="*80)

        if not fdump_path.exists():
            log(f"SKIP: File not found")
        else:
            try:
                F_grid, metadata = read_fdump(str(fdump_path), device=device, dtype=dtype)

                h_min, h_max = metadata['h_min'], metadata['h_max']
                k_min, k_max = metadata['k_min'], metadata['k_max']
                l_min, l_max = metadata['l_min'], metadata['l_max']

                log(f"Grid shape: {F_grid.shape}")
                log(f"H range: [{h_min}, {h_max}]")
                log(f"K range: [{k_min}, {k_max}]")
                log(f"L range: [{l_min}, {l_max}]")

                # Check if target is in range
                h, k, l = target_hkl
                in_range = (h_min <= h <= h_max and
                           k_min <= k <= k_max and
                           l_min <= l <= l_max)

                log(f"Target in range: {in_range}")

                if in_range:
                    # Create temporary crystal instance and attach Fdump data
                    crystal = Crystal(crystal_config)
                    crystal.hkl_data = F_grid
                    crystal.hkl_metadata = metadata

                    # Query structure factor
                    h_t = torch.tensor([h], dtype=dtype, device=device)
                    k_t = torch.tensor([k], dtype=dtype, device=device)
                    l_t = torch.tensor([l], dtype=dtype, device=device)

                    F_result = crystal.get_structure_factor(h_t, k_t, l_t)
                    F_value = F_result[0].item()

                    log(f"Retrieved F_cell: {F_value}")
                    log(f"Delta from C: {F_value - c_reference_F}")
                else:
                    log("Target reflection is OUT OF RANGE")

            except Exception as e:
                log(f"ERROR reading Fdump: {e}")

            log("")

    # Save log
    log("="*80)
    log("Probe complete")
    log("="*80)

    with open(log_path, 'w') as f:
        f.write('\n'.join(log_lines))

    print(f"\nLog saved to: {log_path}")

    # Generate analysis stub
    analysis_path = out_dir / 'analysis.md'
    analysis_content = f"""# Structure-Factor Coverage Analysis

**Date:** {datetime.utcnow().isoformat()}Z
**Task:** CLI-FLAGS-003 Phase L3a
**Goal:** Verify structure-factor source for supervisor pixel

## Target Reflection

- **Miller index:** h={target_hkl[0]}, k={target_hkl[1]}, l={target_hkl[2]}
- **C reference F_cell:** {c_reference_F}
- **Source:** `reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:143-164`

## Data Sources Tested

See `probe.log` for detailed output from:
- `scaled.hkl` (HKL text file)
- Fdump binaries (if provided via --fdump)

## Findings

[Review probe.log output and fill in conclusions here]

### HKL File Coverage

- Grid ranges: [see log]
- Target in range: [yes/no]
- Retrieved F_cell: [value]
- Delta from C: [value]

### Fdump Coverage

[Repeat for each Fdump tested]

## Hypothesis

[Based on the coverage analysis, explain where C derives F_cell=190.27]

## Next Actions (Phase L3b)

[Recommendations for HKL/Fdump ingestion strategy]
"""

    with open(analysis_path, 'w') as f:
        f.write(analysis_content)

    print(f"Analysis template saved to: {analysis_path}")
    print("\nNext step: Review probe.log and complete analysis.md with findings")


if __name__ == '__main__':
    main()
