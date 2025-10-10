#!/usr/bin/env python3
"""
Minimal reproducer for dtype cache mismatch in Detector.get_pixel_coords()

This script demonstrates the float32/float64 RuntimeError that occurs when
a Detector is created with default float32 caches but then used with float64 configs.

Error Location: src/nanobrag_torch/models/detector.py:767
Error Message: RuntimeError: Float did not match Double

Root Cause: torch.allclose() attempts to compare float32 cached basis vectors
against float64 current basis vectors without dtype coercion.
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
from nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator

def test_dtype_cache_mismatch():
    """Reproduce dtype mismatch in detector cache."""
    print("=" * 80)
    print("Minimal Reproducer: Detector Dtype Cache Mismatch")
    print("=" * 80)
    print()

    # Create detector config (defaults to float32)
    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=64,
        fpixels=64,
        oversample=1
    )

    print("Step 1: Create Detector with default dtype (float32)")
    detector_float32 = Detector(detector_config)  # defaults to float32
    print(f"  detector.dtype = {detector_float32.dtype}")
    print(f"  detector.fdet_vec.dtype = {detector_float32.fdet_vec.dtype}")
    print()

    print("Step 2: Call get_pixel_coords() to populate cache (float32)")
    coords_float32 = detector_float32.get_pixel_coords()
    print(f"  coords.dtype = {coords_float32.dtype}")
    print(f"  Cache populated with float32 basis vectors")
    print()

    print("Step 3: Create new Detector instance with float64 dtype")
    detector_float64 = Detector(detector_config, dtype=torch.float64)
    print(f"  detector.dtype = {detector_float64.dtype}")
    print(f"  detector.fdet_vec.dtype = {detector_float64.dtype}")
    print()

    print("Step 4: Attempt to call get_pixel_coords() (this will fail)")
    try:
        coords_float64 = detector_float64.get_pixel_coords()
        print(f"  SUCCESS: coords.dtype = {coords_float64.dtype}")
    except RuntimeError as e:
        print(f"  FAILURE: RuntimeError: {e}")
        print()
        print("Analysis:")
        print("  - Cached basis vectors are float32 (from first call)")
        print("  - Current basis vectors are float64 (from new dtype)")
        print("  - torch.allclose() cannot compare different dtypes")
        print("  - detector.py:767 needs dtype coercion before comparison")

    print()
    print("=" * 80)

def test_simulator_dtype_mismatch():
    """Reproduce dtype mismatch when creating Simulator with float64."""
    print()
    print("=" * 80)
    print("Simulator Integration: Dtype Mismatch During Initialization")
    print("=" * 80)
    print()

    # Crystal and beam configs
    crystal_config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0,
        phi_start_deg=0.0,
        mosaic_spread_deg=0.0
    )

    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=64,
        fpixels=64
    )

    beam_config = BeamConfig(wavelength_A=1.0)

    print("Creating Crystal and Detector with float64 dtype...")
    crystal = Crystal(crystal_config, beam_config, dtype=torch.float64)
    detector = Detector(detector_config, dtype=torch.float64)

    print(f"  crystal.dtype = {crystal.dtype}")
    print(f"  detector.dtype = {detector.dtype}")
    print()

    print("Attempting to create Simulator (triggers detector.get_pixel_coords())...")
    try:
        simulator = Simulator(crystal, detector, crystal_config, beam_config)
        print(f"  SUCCESS: Simulator created")
    except RuntimeError as e:
        print(f"  FAILURE: RuntimeError: {e}")
        print()
        print("Stack trace location: simulator.py:569 -> detector.get_pixel_coords()")

    print()
    print("=" * 80)

if __name__ == "__main__":
    test_dtype_cache_mismatch()
    test_simulator_dtype_mismatch()
