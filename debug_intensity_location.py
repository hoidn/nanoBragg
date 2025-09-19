#!/usr/bin/env python3
"""
Debug where the maximum intensity actually appears in both images.
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import numpy as np
import tempfile
from pathlib import Path

# Add scripts directory to path
import sys
sys.path.append('scripts')
from c_reference_runner import CReferenceRunner
from src.nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.simulator import Simulator
import torch

with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)

    # Simple configuration
    crystal_config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(1, 1, 1),
        default_F=100.0
    )

    detector_config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=64,
        fpixels=64
    )

    beam_config = BeamConfig(
        wavelength_A=1.0
    )

    # Run C simulation
    runner = CReferenceRunner(work_dir=str(tmpdir))
    c_image = runner.run_simulation(
        detector_config,
        crystal_config,
        beam_config,
        label="Debug"
    )

    # Run PyTorch simulation
    crystal = Crystal(crystal_config, beam_config)
    detector = Detector(detector_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)
    pytorch_image = simulator.run()

    print("\n=== IMAGE STATISTICS ===")
    print(f"C image shape: {c_image.shape}")
    print(f"C image range: [{c_image.min():.3f}, {c_image.max():.3f}]")
    print(f"C image mean: {c_image.mean():.3f}")
    print(f"C image non-zero pixels: {np.sum(c_image > 0)}")

    print(f"\nPyTorch image shape: {pytorch_image.shape}")
    print(f"PyTorch image range: [{pytorch_image.min():.3f}, {pytorch_image.max():.3f}]")
    print(f"PyTorch image mean: {pytorch_image.mean():.3f}")
    print(f"PyTorch image non-zero pixels: {torch.sum(pytorch_image > 0).item()}")

    # Find maximums
    c_max_idx = np.unravel_index(np.argmax(c_image), c_image.shape)
    pt_max_idx = np.unravel_index(torch.argmax(pytorch_image).item(), pytorch_image.shape)

    print(f"\n=== MAXIMUM LOCATIONS ===")
    print(f"C max at: {c_max_idx} with value {c_image[c_max_idx]:.3f}")
    print(f"PyTorch max at: {pt_max_idx} with value {pytorch_image[pt_max_idx]:.3f}")

    # Check a 5x5 region around expected center
    print(f"\n=== 5x5 REGION AROUND CENTER (31-35, 31-35) ===")
    print("C image:")
    for s in range(31, 36):
        row = []
        for f in range(31, 36):
            if s < c_image.shape[0] and f < c_image.shape[1]:
                val = c_image[s, f]
                if val > 0:
                    row.append(f"{val:8.1f}")
                else:
                    row.append("       0")
            else:
                row.append("     OOB")
        print(f"  Row {s}: " + " ".join(row))

    print("\nPyTorch image:")
    for s in range(31, 36):
        row = []
        for f in range(31, 36):
            if s < pytorch_image.shape[0] and f < pytorch_image.shape[1]:
                val = pytorch_image[s, f].item()
                if val > 1e-6:
                    row.append(f"{val:8.6f}")
                else:
                    row.append("       0")
            else:
                row.append("     OOB")
        print(f"  Row {s}: " + " ".join(row))

    # Check if images are shifted versions of each other
    print("\n=== CHECKING FOR SYSTEMATIC SHIFT ===")
    # Try shifting PyTorch image by (1, 1) and check correlation
    if pytorch_image.shape == c_image.shape:
        # Normalize images for comparison
        c_norm = (c_image - c_image.mean()) / (c_image.std() + 1e-10)
        pt_np = pytorch_image.numpy()
        pt_norm = (pt_np - pt_np.mean()) / (pt_np.std() + 1e-10)

        # Original correlation
        orig_corr = np.corrcoef(c_norm.flatten(), pt_norm.flatten())[0, 1]
        print(f"Original correlation: {orig_corr:.4f}")

        # Try shifting by (1, 1)
        pt_shifted = np.zeros_like(pt_norm)
        pt_shifted[:-1, :-1] = pt_norm[1:, 1:]
        shift_corr = np.corrcoef(c_norm.flatten(), pt_shifted.flatten())[0, 1]
        print(f"Correlation after shifting PyTorch by (+1, +1): {shift_corr:.4f}")

        # Try shifting by (-1, -1)
        pt_shifted2 = np.zeros_like(pt_norm)
        pt_shifted2[1:, 1:] = pt_norm[:-1, :-1]
        shift_corr2 = np.corrcoef(c_norm.flatten(), pt_shifted2.flatten())[0, 1]
        print(f"Correlation after shifting PyTorch by (-1, -1): {shift_corr2:.4f}")