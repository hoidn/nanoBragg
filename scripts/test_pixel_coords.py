#!/usr/bin/env python
"""Test pixel coordinate calculation for both cubic and triclinic crystals."""

import os
import torch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.config import (
    DetectorConfig, CrystalConfig, BeamConfig,
    DetectorConvention, DetectorPivot
)
from nanobrag_torch.models import Crystal, Detector
from nanobrag_torch.simulator import Simulator

def test_pixel_coordinates():
    """Check that pixel coordinates are calculated correctly."""

    # Common detector configuration
    detector_config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM,
        distance_mm=150.0,
        pixel_size_mm=0.1,
        spixels=256,
        fpixels=256
    )

    # Create detector once
    detector = Detector(detector_config)

    # Get pixel coordinates (should be same regardless of crystal)
    pixel_coords = detector.get_pixel_coords()  # (3, spixels, fpixels) in Angstroms

    print("Detector configuration:")
    print(f"  Distance: {detector.distance:.3f} m = {detector.distance * 1e10:.1f} Å")
    print(f"  Pixel size: {detector.pixel_size:.6f} m = {detector.pixel_size * 1e10:.1f} Å")
    print(f"  Detector: {detector.spixels}x{detector.fpixels} pixels")

    print("\nPixel coordinate checks:")
    print(f"  Shape: {pixel_coords.shape}")
    print(f"  Dtype: {pixel_coords.dtype}")

    # Check center pixel (should be near beam center)
    center_s = detector.spixels // 2
    center_f = detector.fpixels // 2
    # Note: shape is (spixels, fpixels, 3) not (3, spixels, fpixels)
    center_coord = pixel_coords[center_s, center_f, :]
    print(f"\nCenter pixel ({center_s}, {center_f}):")
    print(f"  Position (Å): [{center_coord[0]:.3f}, {center_coord[1]:.3f}, {center_coord[2]:.3f}]")
    print(f"  Distance from origin: {torch.norm(center_coord):.3f} Å")

    # Check corner pixels
    corners = [
        (0, 0, "Top-left"),
        (0, detector.fpixels-1, "Top-right"),
        (detector.spixels-1, 0, "Bottom-left"),
        (detector.spixels-1, detector.fpixels-1, "Bottom-right")
    ]

    print("\nCorner pixels:")
    for s, f, label in corners:
        coord = pixel_coords[s, f, :]
        print(f"  {label} ({s}, {f}): [{coord[0]:.3f}, {coord[1]:.3f}, {coord[2]:.3f}] Å")

    # Check for near-zero values (the bug)
    min_coord = torch.min(torch.abs(pixel_coords))
    max_coord = torch.max(torch.abs(pixel_coords))
    print(f"\nCoordinate ranges:")
    print(f"  Min absolute value: {min_coord:.12f} Å")
    print(f"  Max absolute value: {max_coord:.12f} Å")

    if max_coord < 1.0:
        print("\n⚠️  ERROR: Pixel coordinates are near-zero! This is the bug!")
        print("    Expected coordinates should be ~1,500,000 Å (150mm distance)")

        # Debug detector internals
        print("\nDetector internals:")
        print(f"  pix0_vector: {detector.pix0_vector}")
        print(f"  fdet_vec: {detector.fdet_vec}")
        print(f"  sdet_vec: {detector.sdet_vec}")
        print(f"  odet_vec: {detector.odet_vec}")
    else:
        print("\n✓ Pixel coordinates look reasonable")

    return pixel_coords

def test_with_simulator():
    """Test pixel coordinates when used in simulator."""

    # Test both cubic and triclinic
    configs = [
        ("Cubic", CrystalConfig(
            cell_a=80.0, cell_b=80.0, cell_c=80.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5), default_F=100.0
        )),
        ("Triclinic", CrystalConfig(
            cell_a=70.0, cell_b=80.0, cell_c=90.0,
            cell_alpha=85.0, cell_beta=95.0, cell_gamma=105.0,
            N_cells=(5, 5, 5), default_F=100.0
        ))
    ]

    detector_config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM,
        distance_mm=150.0,
        pixel_size_mm=0.1,
        spixels=256,
        fpixels=256
    )

    beam_config = BeamConfig(wavelength_A=1.5)

    for label, crystal_config in configs:
        print(f"\n{'='*60}")
        print(f"Testing with {label} crystal")
        print('='*60)

        crystal = Crystal(crystal_config, beam_config)
        detector = Detector(detector_config)

        # Check if detector is being modified differently for different crystals
        pixel_coords = detector.get_pixel_coords()
        center_coord = pixel_coords[128, 128, :]

        print(f"Center pixel position: [{center_coord[0]:.3f}, {center_coord[1]:.3f}, {center_coord[2]:.3f}] Å")
        print(f"Distance from origin: {torch.norm(center_coord):.3f} Å")

        # Run simulation and check
        sim = Simulator(crystal, detector, crystal_config, beam_config)

        # Check if simulator modified detector
        pixel_coords_after = detector.get_pixel_coords()
        center_coord_after = pixel_coords_after[128, 128, :]

        if not torch.allclose(center_coord, center_coord_after):
            print("⚠️  WARNING: Detector coordinates changed after creating Simulator!")
            print(f"  Before: {center_coord}")
            print(f"  After: {center_coord_after}")

if __name__ == "__main__":
    print("Testing pixel coordinate calculation")
    print("="*60)

    coords = test_pixel_coordinates()
    test_with_simulator()