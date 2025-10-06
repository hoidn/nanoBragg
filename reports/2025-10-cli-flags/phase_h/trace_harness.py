#!/usr/bin/env python3
"""
PyTorch trace harness for CLI-FLAGS-003 Phase H1.
Generates TRACE_PY output matching C trace format.
Phase H1: Clean trace without manual beam overrides - Detector.apply_custom_vectors() handles beam_vector from CLI.
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

# Phase H6b: Patch Detector to emit TRACE_PY lines
_original_detector_init = Detector.__init__

def traced_detector_init(self, config=None, device=None, dtype=torch.float32):
    """Wrapped Detector.__init__ that emits TRACE_PY lines after geometry setup."""
    # Call original __init__ which sets up all geometry
    _original_detector_init(self, config, device, dtype)

    # Now emit TRACE_PY lines matching C trace format
    print(f"TRACE_PY:detector_convention={self.config.detector_convention.name}")

    # Angles (in radians)
    rotx_rad = self.config.detector_rotx_deg * 3.141592653589793 / 180.0
    roty_rad = self.config.detector_roty_deg * 3.141592653589793 / 180.0
    rotz_rad = self.config.detector_rotz_deg * 3.141592653589793 / 180.0
    twotheta_rad = self.config.detector_twotheta_deg * 3.141592653589793 / 180.0
    print(f"TRACE_PY:angles_rad=rotx:{rotx_rad:.15g} roty:{roty_rad:.15g} rotz:{rotz_rad:.15g} twotheta:{twotheta_rad:.15g}")

    # Beam center in meters (Xclose/Yclose)
    Xclose_m = self.config.beam_center_f / 1000.0 if self.config.beam_center_f is not None else 0.0
    Yclose_m = self.config.beam_center_s / 1000.0 if self.config.beam_center_s is not None else 0.0
    pixel_mm = self.config.pixel_size_mm
    print(f"TRACE_PY:beam_center_m=Xclose:{Xclose_m:.15g} Yclose:{Yclose_m:.15g} pixel_mm:{pixel_mm:.15g}")

    # Initial detector vectors (for CUSTOM these are the custom vectors)
    if self.config.custom_fdet_vector:
        fdet_init = self.config.custom_fdet_vector
        print(f"TRACE_PY:initial_fdet={fdet_init[0]:.15g} {fdet_init[1]:.15g} {fdet_init[2]:.15g}")
    if self.config.custom_sdet_vector:
        sdet_init = self.config.custom_sdet_vector
        print(f"TRACE_PY:initial_sdet={sdet_init[0]:.15g} {sdet_init[1]:.15g} {sdet_init[2]:.15g}")
    if self.config.custom_odet_vector:
        odet_init = self.config.custom_odet_vector
        print(f"TRACE_PY:initial_odet={odet_init[0]:.15g} {odet_init[1]:.15g} {odet_init[2]:.15g}")

    # Fclose/Sclose
    Fclose_m = self.config.beam_center_f / 1000.0
    Sclose_m = self.config.beam_center_s / 1000.0
    print(f"TRACE_PY:Fclose_m={Fclose_m:.15g}")
    print(f"TRACE_PY:Sclose_m={Sclose_m:.15g}")

    # close_distance, r-factor, distance
    close_distance_m = self.close_distance.item() if isinstance(self.close_distance, torch.Tensor) else self.close_distance
    print(f"TRACE_PY:close_distance_m={close_distance_m:.15g}")

    ratio = self.r_factor.item() if isinstance(self.r_factor, torch.Tensor) else self.r_factor
    print(f"TRACE_PY:ratio={ratio:.15g}")

    distance_m = self.distance_corrected.item() if isinstance(self.distance_corrected, torch.Tensor) else self.distance_corrected
    print(f"TRACE_PY:distance_m={distance_m:.15g}")

    # For CUSTOM convention with custom vectors, always compute term_* regardless of pivot
    # These show the intermediate calculation steps
    if self.config.custom_fdet_vector:
        fdet_vec = torch.tensor(self.config.custom_fdet_vector, dtype=torch.float64)
        sdet_vec = torch.tensor(self.config.custom_sdet_vector, dtype=torch.float64)
        odet_vec = torch.tensor(self.config.custom_odet_vector, dtype=torch.float64)

        term_fast = -Fclose_m * fdet_vec
        term_slow = -Sclose_m * sdet_vec
        term_close = close_distance_m * odet_vec

        print(f"TRACE_PY:term_fast_before_rot={term_fast[0].item():.15g} {term_fast[1].item():.15g} {term_fast[2].item():.15g}")
        print(f"TRACE_PY:term_slow_before_rot={term_slow[0].item():.15g} {term_slow[1].item():.15g} {term_slow[2].item():.15g}")
        print(f"TRACE_PY:term_close_before_rot={term_close[0].item():.15g} {term_close[1].item():.15g} {term_close[2].item():.15g}")

    # pix0 vector
    pix0 = self.pix0_vector
    pix0_vals = [pix0[i].item() if isinstance(pix0, torch.Tensor) else pix0[i] for i in range(3)]
    print(f"TRACE_PY:pix0_before_rotation={pix0_vals[0]:.15g} {pix0_vals[1]:.15g} {pix0_vals[2]:.15g}")
    print(f"TRACE_PY:pix0_after_rotz={pix0_vals[0]:.15g} {pix0_vals[1]:.15g} {pix0_vals[2]:.15g}")
    print(f"TRACE_PY:pix0_after_twotheta={pix0_vals[0]:.15g} {pix0_vals[1]:.15g} {pix0_vals[2]:.15g}")

    # Detector basis vectors (after rotations)
    fdet = self.fdet_vec
    sdet = self.sdet_vec
    odet = self.odet_vec
    fdet_vals = [fdet[i].item() if isinstance(fdet, torch.Tensor) else fdet[i] for i in range(3)]
    sdet_vals = [sdet[i].item() if isinstance(sdet, torch.Tensor) else sdet[i] for i in range(3)]
    odet_vals = [odet[i].item() if isinstance(odet, torch.Tensor) else odet[i] for i in range(3)]

    print(f"TRACE_PY:fdet_after_rotz={fdet_vals[0]:.15g} {fdet_vals[1]:.15g} {fdet_vals[2]:.15g}")
    print(f"TRACE_PY:sdet_after_rotz={sdet_vals[0]:.15g} {sdet_vals[1]:.15g} {sdet_vals[2]:.15g}")
    print(f"TRACE_PY:odet_after_rotz={odet_vals[0]:.15g} {odet_vals[1]:.15g} {odet_vals[2]:.15g}")

    # twotheta_axis
    if hasattr(self.config, 'twotheta_axis') and self.config.twotheta_axis is not None:
        twotheta_axis = self.config.twotheta_axis
    else:
        twotheta_axis = (0, 1, 0)
    print(f"TRACE_PY:twotheta_axis={twotheta_axis[0]:.15g} {twotheta_axis[1]:.15g} {twotheta_axis[2]:.15g}")

    print(f"TRACE_PY:fdet_after_twotheta={fdet_vals[0]:.15g} {fdet_vals[1]:.15g} {fdet_vals[2]:.15g}")
    print(f"TRACE_PY:sdet_after_twotheta={sdet_vals[0]:.15g} {sdet_vals[1]:.15g} {sdet_vals[2]:.15g}")
    print(f"TRACE_PY:odet_after_twotheta={odet_vals[0]:.15g} {odet_vals[1]:.15g} {odet_vals[2]:.15g}")

# Install the patched version
Detector.__init__ = traced_detector_init

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

    # Phase H6b: Do NOT force detector_pivot=BEAM
    # Let the pivot be determined by the CLI precedence rules
    # (custom vectors imply SAMPLE pivot regardless of -distance)
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
        custom_beam_vector=tuple(beam_vector),  # Phase H1: Pass beam_vector to Detector
        oversample=oversample
        # Phase H6b: Omit detector_pivot to let DetectorConfig choose SAMPLE
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

    # Phase H6b: Detector creation will now emit TRACE_PY lines via patched __init__
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

    # Phase H1: No manual incident beam override
    # Detector.apply_custom_vectors() now consumes beam_vector from custom_beam_direction during init
    # This allows end-to-end CLI→Detector flow without manual patches

    # Run simulation (trace will be printed to stdout)
    print(f"# Tracing pixel (slow={target_pixel[0]}, fast={target_pixel[1]})", file=sys.stderr)
    image = simulator.run()
    print(f"# Trace complete", file=sys.stderr)

if __name__ == '__main__':
    main()
