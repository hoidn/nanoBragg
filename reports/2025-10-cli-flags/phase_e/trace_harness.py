#!/usr/bin/env python3
"""
PyTorch trace harness for CLI-FLAGS-003 Phase E2.
Generates TRACE_PY output matching C trace format.
"""

import os
import sys
import torch
from pathlib import Path

# Set environment variable for MKL conflicts
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'src'))

from nanobrag_torch.config import (
    DetectorConfig, CrystalConfig, BeamConfig,
    DetectorConvention, DetectorPivot, CrystalShape
)
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.io.hkl import read_hkl_file
from nanobrag_torch.io.mosflm import read_mosflm_matrix, reciprocal_to_real_cell

def main():
    """Run trace for specific pixel matching C command."""

    # Paths
    repo_root = Path(__file__).parent.parent.parent.parent
    mat_file = repo_root / "A.mat"
    hkl_file = repo_root / "scaled.hkl"

    # Parameters from C command
    wavelength_A = 0.976800
    oversample = 1
    pix0_vector_mm = [-216.336293, 215.205512, -230.200866]
    flux = 1e18
    exposure = 1.0
    beamsize = 1.0
    spindle_axis = [-1.0, 0.0, 0.0]
    Xbeam = 217.742295
    Ybeam = 213.907080
    distance = 231.274660
    pixel_size = 0.172
    detpixels = (2463, 2527)  # (spixels, fpixels)
    odet_vector = [-0.000088, 0.004914, -0.999988]
    sdet_vector = [-0.005998, -0.999970, -0.004913]
    fdet_vector = [0.999982, -0.005998, -0.000118]
    beam_vector = [0.00051387949, 0.0, -0.99999986]
    N_cells = (36, 47, 29)
    osc = 0.1
    phi = 0.0
    phisteps = 10

    # Target pixel (slow, fast)
    target_pixel = (1039, 685)

    # Load crystal cell from matrix
    a_star, b_star, c_star = read_mosflm_matrix(str(mat_file), wavelength_A)
    cell_params = reciprocal_to_real_cell(a_star, b_star, c_star)

    # Load HKL data
    hkl_data = read_hkl_file(str(hkl_file), default_F=0.0)

    # Calculate fluence from flux/exposure/beamsize
    # fluence = flux * exposure / (beamsize_m^2)
    beamsize_m = beamsize / 1000.0  # mm to m
    fluence = flux * exposure / (beamsize_m * beamsize_m)

    # Create crystal config
    crystal_config = CrystalConfig(
        cell_a=cell_params[0],
        cell_b=cell_params[1],
        cell_c=cell_params[2],
        cell_alpha=cell_params[3],
        cell_beta=cell_params[4],
        cell_gamma=cell_params[5],
        N_cells=N_cells,
        default_F=0.0,
        phi_start_deg=phi,
        osc_range_deg=osc,
        phi_steps=phisteps,
        mosaic_spread_deg=0.0,
        mosaic_domains=1,
        spindle_axis=tuple(spindle_axis),
        # Phase G: Pass MOSFLM orientation
        mosflm_a_star=a_star,
        mosflm_b_star=b_star,
        mosflm_c_star=c_star
    )

    # Create detector config with CUSTOM convention
    # Convert pix0_vector from mm to meters
    pix0_vector_m = [x / 1000.0 for x in pix0_vector_mm]

    detector_config = DetectorConfig(
        spixels=detpixels[0],
        fpixels=detpixels[1],
        pixel_size_mm=pixel_size,
        distance_mm=distance,
        detector_convention=DetectorConvention.CUSTOM,
        beam_center_s=Ybeam,  # Ybeam maps to slow axis
        beam_center_f=Xbeam,  # Xbeam maps to fast axis
        pix0_override_m=tuple(pix0_vector_m),
        custom_fdet_vector=tuple(fdet_vector),
        custom_sdet_vector=tuple(sdet_vector),
        custom_odet_vector=tuple(odet_vector),
        oversample=oversample,
        detector_pivot=DetectorPivot.BEAM  # -distance was specified
    )

    # Create beam config
    # Note: beam_vector is stored separately and set in simulator based on convention
    beam_config = BeamConfig(
        wavelength_A=wavelength_A,
        fluence=fluence,
        polarization_axis=(0.0, 1.0, 0.0),  # Default from C code
        polarization_factor=1.0,
        nopolar=False
    )

    # Create models
    crystal = Crystal(crystal_config, device='cpu', dtype=torch.float64)
    crystal.load_hkl(str(hkl_file), write_cache=False)
    detector = Detector(detector_config, device='cpu', dtype=torch.float64)

    # Create simulator with trace enabled
    debug_config = {
        'trace_pixel': target_pixel  # [slow, fast]
    }

    simulator = Simulator(
        crystal=crystal,
        detector=detector,
        crystal_config=crystal_config,
        beam_config=beam_config,
        device='cpu',
        dtype=torch.float64,
        debug_config=debug_config
    )

    # Override incident beam direction for CUSTOM convention with explicit beam_vector
    simulator.incident_beam_direction = torch.tensor(
        beam_vector, device=simulator.device, dtype=simulator.dtype
    )

    # Run simulation (trace will be printed to stdout)
    print(f"# Tracing pixel (slow={target_pixel[0]}, fast={target_pixel[1]})", file=sys.stderr)
    image = simulator.run()
    print(f"# Trace complete", file=sys.stderr)

if __name__ == '__main__':
    main()
