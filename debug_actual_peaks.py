#!/usr/bin/env python
"""Debug script to find actual peak positions in the triclinic simulation."""

import os
import torch
import numpy as np
import tempfile

# Set up environment
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Import PyTorch implementation
from nanobrag_torch.config import (
    CrystalConfig, BeamConfig, DetectorConfig,
    DetectorConvention, DetectorPivot
)
from nanobrag_torch.models import Crystal, Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.io.hkl import read_hkl_file


def find_peaks():
    """Find actual peak positions in the simulation."""

    # Create configuration matching the test
    crystal_config = CrystalConfig(
        cell_a=70.0,
        cell_b=80.0,
        cell_c=90.0,
        cell_alpha=85.0,
        cell_beta=95.0,
        cell_gamma=105.0,
        N_cells=(1, 1, 1),
        default_F=0.0  # Only explicit reflections
    )

    detector_config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM,
        distance_mm=150.0,
        pixel_size_mm=0.1,
        spixels=256,
        fpixels=256
    )

    beam_config = BeamConfig(
        wavelength_A=1.5
    )

    # Create crystal
    crystal = Crystal(crystal_config, beam_config)

    # Create HKL grid with specific reflections
    with tempfile.NamedTemporaryFile(mode='w', suffix='.hkl', delete=False) as f:
        # Write limited set of reflections for clarity
        reflections = [
            (1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
            (1, 1, 0),
            (1, 0, 1),
            (0, 1, 1),
            (-1, 0, 0),
            (0, -1, 0),
            (0, 0, -1),
        ]
        for h, k, l in reflections:
            f.write(f"{h} {k} {l} 100\n")
        hkl_file = f.name

    # Load HKL file
    crystal.hkl_data = read_hkl_file(hkl_file, default_F=0.0)
    os.unlink(hkl_file)

    # Create detector
    detector = Detector(detector_config)

    print("=" * 60)
    print("SIMULATION PARAMETERS")
    print("=" * 60)
    print(f"Crystal: a={crystal_config.cell_a}, b={crystal_config.cell_b}, c={crystal_config.cell_c}")
    print(f"         α={crystal_config.cell_alpha}°, β={crystal_config.cell_beta}°, γ={crystal_config.cell_gamma}°")
    print(f"Detector: {detector_config.spixels}x{detector_config.fpixels}, distance={detector_config.distance_mm}mm")
    print(f"Wavelength: {beam_config.wavelength_A} Å")
    print(f"HKL reflections loaded: {len(reflections)}")

    # Run simulation
    simulator = Simulator(crystal, detector, crystal_config, beam_config)
    image = simulator.run()

    print("\n" + "=" * 60)
    print("IMAGE STATISTICS")
    print("=" * 60)
    print(f"Min intensity: {torch.min(image):.6f}")
    print(f"Max intensity: {torch.max(image):.6f}")
    print(f"Mean intensity: {torch.mean(image):.6f}")
    print(f"Non-zero pixels: {torch.sum(image > 0)}")

    # Find peaks
    threshold = 0.01 * torch.max(image)
    peak_mask = image > threshold
    peak_indices = torch.nonzero(peak_mask)

    print(f"\nFound {len(peak_indices)} pixels above threshold {threshold:.6f}")

    if len(peak_indices) > 0:
        print("\n" + "=" * 60)
        print("PEAK POSITIONS")
        print("=" * 60)
        print("Top 10 peaks:")

        # Get intensities at peak positions
        peak_intensities = [image[idx[0], idx[1]].item() for idx in peak_indices]

        # Sort by intensity
        sorted_indices = np.argsort(peak_intensities)[::-1]

        for i in range(min(10, len(sorted_indices))):
            idx = sorted_indices[i]
            slow, fast = peak_indices[idx]
            intensity = peak_intensities[idx]
            print(f"  ({slow:3d}, {fast:3d}): intensity = {intensity:.6f}")

    # Check what's happening at expected positions
    print("\n" + "=" * 60)
    print("EXPECTED POSITIONS CHECK")
    print("=" * 60)

    expected_positions = [
        (129, 129, "(1,0,0) expected"),
        (124, 129, "(0,1,0) expected"),
        (129, 133, "(0,0,1) expected"),
    ]

    for slow, fast, label in expected_positions:
        if 0 <= slow < 256 and 0 <= fast < 256:
            intensity = image[slow, fast].item()
            print(f"Position ({slow}, {fast}) {label}: intensity = {intensity:.6f}")

            # Check 3x3 neighborhood
            slow_min = max(0, slow - 1)
            slow_max = min(256, slow + 2)
            fast_min = max(0, fast - 1)
            fast_max = min(256, fast + 2)

            neighborhood = image[slow_min:slow_max, fast_min:fast_max]
            max_neighbor = torch.max(neighborhood).item()
            print(f"  Max in 3x3 neighborhood: {max_neighbor:.6f}")


if __name__ == "__main__":
    find_peaks()