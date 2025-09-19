#!/usr/bin/env python3
"""
Temporary debug script to compare AT-PARALLEL-021 (working) vs AT-PARALLEL-023 (failing).
"""

import os
import sys
import tempfile
import subprocess
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.nanobrag_torch.config import (
    BeamConfig, CrystalConfig, DetectorConfig, DetectorConvention
)
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.simulator import Simulator

# Set environment variable for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

C_BINARY = Path(__file__).parent / "nanoBragg"

def run_c_simulation(params, output_file):
    """Run C simulation with given parameters."""
    cmd = [str(C_BINARY)]
    for key, value in params.items():
        cmd.append(key)
        if value is not None:
            if isinstance(value, (list, tuple)):
                cmd.extend([str(v) for v in value])
            else:
                cmd.append(str(value))

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"C binary failed: {result.stderr}")

    # Load binary data
    with open(output_file, 'rb') as f:
        data = np.fromfile(f, dtype=np.float32)
    return data.reshape(256, 256)

def run_pytorch_simulation(beam_config, crystal_config, detector_config):
    """Run PyTorch simulation."""
    crystal = Crystal(crystal_config)
    detector = Detector(detector_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)
    image = simulator.run()
    return image.cpu().numpy()

def main():
    print("=== Debugging AT-PARALLEL-021 vs AT-PARALLEL-023 ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Common parameters
        cell_params = [100.0, 100.0, 100.0, 90.0, 90.0, 90.0]
        detector_size = 256
        pixel_size = 0.1
        distance = 100.0
        wavelength = 6.2

        print("\n1. Testing AT-PARALLEL-021 style (phi rotation)...")

        # AT-PARALLEL-021 style: phi rotation, ROI
        roi = [100, 156, 100, 156]
        c_output_021 = str(tmpdir / "c_021.bin")

        c_params_021 = {
            "-cell": cell_params,
            "-lambda": wavelength,
            "-N": 5,
            "-default_F": 100,
            "-distance": distance,
            "-detpixels": detector_size,
            "-pixel": pixel_size,
            "-phi": 0,
            "-osc": 90,
            "-phisteps": 1,
            "-roi": roi,
            "-fluence": 1e12,
            "-mosflm": None,
            "-floatfile": c_output_021,
            "-seed": 42,
        }

        c_img_021 = run_c_simulation(c_params_021, c_output_021)

        # PyTorch equivalent
        beam_config_021 = BeamConfig(wavelength_A=wavelength, fluence=1e12)
        crystal_config_021 = CrystalConfig(
            cell_a=cell_params[0], cell_b=cell_params[1], cell_c=cell_params[2],
            cell_alpha=cell_params[3], cell_beta=cell_params[4], cell_gamma=cell_params[5],
            N_cells=(5, 5, 5), default_F=100.0,
            phi_start_deg=0, osc_range_deg=90, phi_steps=1,
        )
        detector_config_021 = DetectorConfig(
            distance_mm=distance, pixel_size_mm=pixel_size,
            spixels=detector_size, fpixels=detector_size,
            roi_xmin=roi[0], roi_xmax=roi[1], roi_ymin=roi[2], roi_ymax=roi[3],
        )

        pytorch_img_021 = run_pytorch_simulation(beam_config_021, crystal_config_021, detector_config_021)

        # Extract ROI for comparison
        c_roi_021 = c_img_021[roi[2]:roi[3], roi[0]:roi[1]]
        pytorch_roi_021 = pytorch_img_021

        print(f"  C 021: mean={np.mean(c_roi_021):.6f}, max={np.max(c_roi_021):.6f}")
        print(f"  PyTorch 021: mean={np.mean(pytorch_roi_021):.6f}, max={np.max(pytorch_roi_021):.6f}")

        # Check if 021 passes
        try:
            np.testing.assert_allclose(pytorch_roi_021, c_roi_021, rtol=1e-5, atol=1e-6)
            print("  ✅ AT-PARALLEL-021 style PASSES")
        except AssertionError as e:
            print(f"  ❌ AT-PARALLEL-021 style FAILS: {str(e).split('Max')[0]}...")

        print("\n2. Testing AT-PARALLEL-023 style (misset angles)...")

        # AT-PARALLEL-023 style: misset angles, full detector
        c_output_023 = str(tmpdir / "c_023.bin")

        c_params_023 = {
            "-cell": cell_params,
            "-lambda": wavelength,
            "-N": 5,
            "-default_F": 100,
            "-distance": distance,
            "-detpixels": detector_size,
            "-pixel": pixel_size,
            "-phi": 0,
            "-osc": 0,
            "-seed": 42,
            "-mosflm": None,
            "-floatfile": c_output_023,
            "-misset": [0.0, 0.0, 0.0],
        }

        c_img_023 = run_c_simulation(c_params_023, c_output_023)

        # PyTorch equivalent
        beam_config_023 = BeamConfig(wavelength_A=wavelength)  # Default fluence
        crystal_config_023 = CrystalConfig(
            cell_a=cell_params[0], cell_b=cell_params[1], cell_c=cell_params[2],
            cell_alpha=cell_params[3], cell_beta=cell_params[4], cell_gamma=cell_params[5],
            N_cells=(5, 5, 5), default_F=100.0,
            phi_start_deg=0, osc_range_deg=0, phi_steps=1,
            misset_deg=(0.0, 0.0, 0.0),
        )
        detector_config_023 = DetectorConfig(
            distance_mm=distance, pixel_size_mm=pixel_size,
            spixels=detector_size, fpixels=detector_size,
            detector_convention=DetectorConvention.MOSFLM,
        )

        pytorch_img_023 = run_pytorch_simulation(beam_config_023, crystal_config_023, detector_config_023)

        print(f"  C 023: mean={np.mean(c_img_023):.6f}, max={np.max(c_img_023):.6f}")
        print(f"  PyTorch 023: mean={np.mean(pytorch_img_023):.6f}, max={np.max(pytorch_img_023):.6f}")

        # Check if 023 passes
        try:
            np.testing.assert_allclose(pytorch_img_023, c_img_023, rtol=1e-5, atol=1e-6)
            print("  ✅ AT-PARALLEL-023 style PASSES")
        except AssertionError as e:
            print(f"  ❌ AT-PARALLEL-023 style FAILS: {str(e).split('Max')[0]}...")

        print("\n3. Comparison Analysis:")
        print(f"  021 uses phi rotation (osc=90°), 023 uses misset rotation (misset=0°)")
        print(f"  021 uses ROI ({roi}), 023 uses full detector")
        print(f"  021 uses fluence=1e12, 023 uses default fluence")

        # Check if the main difference is just ROI vs full detector
        print(f"\n4. Testing 021 vs 023 on same ROI region...")
        c_roi_023 = c_img_023[roi[2]:roi[3], roi[0]:roi[1]]
        pytorch_roi_023 = pytorch_img_023[roi[2]:roi[3], roi[0]:roi[1]]

        print(f"  C 023 ROI: mean={np.mean(c_roi_023):.6f}, max={np.max(c_roi_023):.6f}")
        print(f"  PyTorch 023 ROI: mean={np.mean(pytorch_roi_023):.6f}, max={np.max(pytorch_roi_023):.6f}")

        # Compare the ROI regions
        try:
            np.testing.assert_allclose(pytorch_roi_023, c_roi_023, rtol=1e-5, atol=1e-6)
            print("  ✅ AT-PARALLEL-023 ROI PASSES")
        except AssertionError as e:
            print(f"  ❌ AT-PARALLEL-023 ROI FAILS: {str(e).split('Max')[0]}...")

if __name__ == "__main__":
    main()