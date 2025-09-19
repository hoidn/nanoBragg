#!/usr/bin/env python3
"""
Debug script to investigate zero correlation issue in parallel tests.
"""

import os
import torch
import numpy as np

# Set the environment variable to prevent MKL conflicts
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from src.nanobrag_torch.config import (
    DetectorConfig, CrystalConfig, BeamConfig, DetectorConvention
)
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.simulator import Simulator


def debug_simulation():
    """Debug a simple simulation to see what's going wrong."""
    print("=== DEBUGGING ZERO CORRELATION ISSUE ===")

    # Use the same configuration as the failing test
    pixel_size = 0.1  # mm
    beam_center_mm = 128 * pixel_size  # 12.8mm

    detector_config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        distance_mm=100.0,
        pixel_size_mm=pixel_size,
        spixels=256,
        fpixels=256,
        beam_center_s=beam_center_mm,
        beam_center_f=beam_center_mm,
    )

    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),  # Larger crystal for more reflections
        default_F=100.0
    )

    beam_config = BeamConfig(
        wavelength_A=6.2,
        fluence=1e12
    )

    print(f"Detector config: {detector_config}")
    print(f"Crystal config: {crystal_config}")
    print(f"Beam config: {beam_config}")

    try:
        # Create components
        print("\n=== CREATING COMPONENTS ===")
        detector = Detector(detector_config)
        print(f"Detector created successfully")
        print(f"  beam_center_s: {detector.beam_center_s}")
        print(f"  beam_center_f: {detector.beam_center_f}")
        print(f"  distance: {detector.distance}")
        print(f"  pixel_size: {detector.pixel_size}")

        crystal = Crystal(crystal_config)
        print(f"Crystal created successfully")
        print(f"  cell dimensions: {crystal.cell_a}, {crystal.cell_b}, {crystal.cell_c}")
        print(f"  N_cells: {crystal.N_cells_a}, {crystal.N_cells_b}, {crystal.N_cells_c}")

        simulator = Simulator(crystal, detector, crystal_config, beam_config)
        print(f"Simulator created successfully")
        print(f"  wavelength: {simulator.wavelength}")
        print(f"  fluence: {simulator.fluence}")

        # Run simulation
        print("\n=== RUNNING SIMULATION ===")
        image = simulator.run()
        print(f"Simulation completed")
        print(f"Image shape: {image.shape}")
        print(f"Image dtype: {image.dtype}")
        print(f"Image device: {image.device}")

        # Check for problematic values
        print("\n=== ANALYZING RESULTS ===")
        print(f"Image min: {image.min()}")
        print(f"Image max: {image.max()}")
        print(f"Image mean: {image.mean()}")
        print(f"Image sum: {image.sum()}")

        # Check for NaN/inf
        nan_count = torch.isnan(image).sum()
        inf_count = torch.isinf(image).sum()
        print(f"NaN count: {nan_count}")
        print(f"Inf count: {inf_count}")

        # Find non-zero pixels
        nonzero_count = (image > 1e-10).sum()
        print(f"Non-zero pixels (>1e-10): {nonzero_count}")

        if nonzero_count > 0:
            # Find peak position
            max_idx = torch.argmax(image)
            peak_s = max_idx // 256
            peak_f = max_idx % 256
            print(f"Peak position: ({peak_s}, {peak_f})")
            print(f"Peak value: {image[peak_s, peak_f]}")

            # Show a small region around peak
            s_start = max(0, peak_s - 2)
            s_end = min(256, peak_s + 3)
            f_start = max(0, peak_f - 2)
            f_end = min(256, peak_f + 3)

            print(f"Region around peak ({s_start}:{s_end}, {f_start}:{f_end}):")
            region = image[s_start:s_end, f_start:f_end]
            print(region)
        else:
            print("No significant intensity found!")

            # Sample a few pixels to check intermediate values
            print("\nChecking a few pixel positions...")
            test_positions = [(128, 128), (100, 100), (150, 150), (50, 50)]
            for s, f in test_positions:
                if s < image.shape[0] and f < image.shape[1]:
                    print(f"  ({s}, {f}): {image[s, f]}")

        return image

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    debug_simulation()