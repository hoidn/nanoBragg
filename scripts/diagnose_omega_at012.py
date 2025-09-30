#!/usr/bin/env python3
"""
Diagnostic script for AT-PARALLEL-012 omega calculation investigation.

This script creates the exact configuration from test_at_parallel_012 and
exposes all omega-related parameters, calculating omega for test pixels to
identify the source of the +7.07% center / +3.18% edge radial intensity pattern.

Expected omega formula (from spec):
    omega = (pixel_size² / R²) × (close_distance / R)
          = (pixel_size² × close_distance) / R³

Usage:
    python scripts/diagnose_omega_at012.py
"""

import os
import sys
import torch

# Set KMP_DUPLICATE_LIB_OK to prevent MKL conflicts
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.config import (
    DetectorConfig,
    DetectorConvention,
    DetectorPivot,
    CrystalConfig,
    BeamConfig,
)
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator


def diagnose_omega():
    """Diagnose omega calculation for AT-PARALLEL-012."""

    print("=" * 80)
    print("AT-PARALLEL-012 OMEGA DIAGNOSTICS")
    print("=" * 80)
    print()

    # Setup identical configuration to test_at_parallel_012
    print("Setting up test configuration (simple_cubic):")
    print("  Detector: 1024×1024 pixels, 0.1mm/pixel, 100mm distance")
    print("  Wavelength: 6.2 Å")
    print("  Convention: MOSFLM (default)")
    print("  Pivot: BEAM")
    print()

    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0
    )

    detector_config = DetectorConfig(
        spixels=1024,
        fpixels=1024,
        pixel_size_mm=0.1,
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM
    )

    beam_config = BeamConfig(
        wavelength_A=6.2
    )

    # Create detector and simulator
    detector = Detector(detector_config)
    crystal = Crystal(crystal_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)

    # Print all omega-related parameters
    print("=" * 80)
    print("DETECTOR PARAMETERS")
    print("=" * 80)
    print()

    print("Distance parameters:")
    print(f"  detector.config.distance_mm:       {detector.config.distance_mm} mm")
    print(f"  detector.distance (internal):      {detector.distance} m = {detector.distance * 1000} mm")

    if hasattr(detector, 'distance_corrected'):
        dist_corr_mm = detector.distance_corrected * 1000 if detector.distance_corrected is not None else None
        print(f"  detector.distance_corrected:       {detector.distance_corrected} m = {dist_corr_mm} mm")

    if hasattr(detector.config, 'close_distance_mm') and detector.config.close_distance_mm is not None:
        print(f"  detector.config.close_distance_mm: {detector.config.close_distance_mm} mm")

    print(f"  detector.close_distance:           {detector.close_distance} m = {detector.close_distance * 1000} mm")

    if hasattr(detector, 'r_factor'):
        print(f"  detector.r_factor:                 {detector.r_factor}")

    print()

    print("Pixel parameters:")
    print(f"  detector.config.pixel_size_mm:     {detector.config.pixel_size_mm} mm")
    print(f"  detector.pixel_size (internal):    {detector.pixel_size} m = {detector.pixel_size * 1000} mm")
    print(f"  detector.config.point_pixel:       {detector.config.point_pixel}")
    print()

    print("Beam center parameters:")
    print(f"  detector.config.beam_center_s:     {detector.config.beam_center_s} mm")
    print(f"  detector.config.beam_center_f:     {detector.config.beam_center_f} mm")
    print(f"  detector.beam_center_s (pixels):   {detector.beam_center_s.item():.6f}")
    print(f"  detector.beam_center_f (pixels):   {detector.beam_center_f.item():.6f}")
    print()

    print("Basis vectors:")
    print(f"  detector.fdet_vec: {detector.fdet_vec.cpu().numpy()}")
    print(f"  detector.sdet_vec: {detector.sdet_vec.cpu().numpy()}")
    print(f"  detector.odet_vec: {detector.odet_vec.cpu().numpy()}")
    print()

    print("pix0_vector (position of pixel 0,0):")
    print(f"  {detector.pix0_vector.cpu().numpy()} meters")
    print(f"  {(detector.pix0_vector * 1e10).cpu().numpy()} Angstroms")
    print()

    # Test pixels for omega calculation
    test_pixels = [
        (512, 512, "Center"),
        (512, 700, "Mid-edge"),
        (512, 900, "Near-edge"),
    ]

    print("=" * 80)
    print("OMEGA CALCULATION FOR TEST PIXELS")
    print("=" * 80)
    print()

    # Get pixel coordinates
    pixel_coords_meters = detector.get_pixel_coords()

    for slow, fast, label in test_pixels:
        print(f"Pixel ({slow}, {fast}) [{label}]:")
        print("-" * 60)

        # Get pixel position in meters
        pos_m = pixel_coords_meters[slow, fast]
        print(f"  Position (meters):    ({pos_m[0].item():.15e}, {pos_m[1].item():.15e}, {pos_m[2].item():.15e})")

        # Convert to Angstroms for display
        pos_ang = pos_m * 1e10
        print(f"  Position (Angstroms): ({pos_ang[0].item():.6f}, {pos_ang[1].item():.6f}, {pos_ang[2].item():.6f})")

        # Calculate R (airpath distance in meters)
        R_m = torch.sqrt(torch.sum(pos_m * pos_m)).item()
        print(f"  R (airpath distance): {R_m:.15e} meters = {R_m * 1000:.6f} mm")

        # Get omega calculation parameters
        pixel_size_m = detector.pixel_size
        close_distance_m = detector.close_distance

        # Calculate omega using the formula from simulator.py lines 662-670
        if detector.config.point_pixel:
            omega = 1.0 / (R_m * R_m)
            print(f"  Mode: point_pixel")
            print(f"  Formula: omega = 1 / R²")
        else:
            omega = (pixel_size_m * pixel_size_m) / (R_m * R_m) * (close_distance_m / R_m)
            print(f"  Mode: standard (with obliquity)")
            print(f"  Formula: omega = (pixel_size² / R²) × (close_distance / R)")

        print()
        print(f"  Calculation breakdown:")
        print(f"    pixel_size²:           {pixel_size_m * pixel_size_m:.15e} m²")
        print(f"    close_distance:        {close_distance_m:.15e} m")
        print(f"    R²:                    {R_m * R_m:.15e} m²")
        print(f"    R³:                    {R_m * R_m * R_m:.15e} m³")
        print(f"    pixel_size² / R²:      {(pixel_size_m * pixel_size_m) / (R_m * R_m):.15e}")
        print(f"    close_distance / R:    {close_distance_m / R_m:.15e}")
        print(f"    omega (final):         {omega:.15e} sr")
        print()

        # Compare with expected C code behavior
        # C code expected formula (from nanoBragg.c):
        # omega = pixel_size² / airpath² × close_distance / airpath
        # where airpath is in meters
        print(f"  C-code expected calculation:")
        print(f"    Expected omega = (0.0001² × 0.1) / {R_m:.6f}³")
        expected_omega = (pixel_size_m * pixel_size_m * close_distance_m) / (R_m * R_m * R_m)
        print(f"    Expected omega = {expected_omega:.15e} sr")
        print(f"    Ratio (computed/expected): {omega / expected_omega:.15e}")
        print()

    # Calculate omega ratio for center vs edge to see if it matches the intensity pattern
    print("=" * 80)
    print("OMEGA RADIAL DEPENDENCE ANALYSIS")
    print("=" * 80)
    print()

    # Center pixel
    pos_center = pixel_coords_meters[512, 512]
    R_center = torch.sqrt(torch.sum(pos_center * pos_center)).item()
    omega_center = (pixel_size_m * pixel_size_m) / (R_center * R_center) * (close_distance_m / R_center)

    # Edge pixel
    pos_edge = pixel_coords_meters[512, 900]
    R_edge = torch.sqrt(torch.sum(pos_edge * pos_edge)).item()
    omega_edge = (pixel_size_m * pixel_size_m) / (R_edge * R_edge) * (close_distance_m / R_edge)

    print(f"Center pixel (512, 512):")
    print(f"  R = {R_center:.6f} m")
    print(f"  omega = {omega_center:.15e} sr")
    print()

    print(f"Edge pixel (512, 900):")
    print(f"  R = {R_edge:.6f} m")
    print(f"  omega = {omega_edge:.15e} sr")
    print()

    print(f"Ratio (omega_center / omega_edge): {omega_center / omega_edge:.6f}")
    print()

    # Compare with observed intensity pattern
    print("Observed intensity pattern from AT-PARALLEL-012:")
    print("  Center pixels: +7.07% higher than expected")
    print("  Edge pixels:   +3.18% higher than expected")
    print("  Ratio:         1.0707 / 1.0318 = 1.0377")
    print()

    print("Expected behavior:")
    print("  If omega calculation is correct, intensity should scale uniformly")
    print("  Radial intensity variation suggests:")
    print("    - Incorrect close_distance value, OR")
    print("    - Missing obliquity correction, OR")
    print("    - Wrong coordinate system (using Angstroms instead of meters), OR")
    print("    - Detector basis vector error")
    print()

    # Check for common issues
    print("=" * 80)
    print("DIAGNOSTIC CHECKS")
    print("=" * 80)
    print()

    # Check 1: Are we using meters everywhere?
    print("Check 1: Unit consistency")
    print(f"  pixel_size in meters: {pixel_size_m:.15e} (should be 0.0001)")
    print(f"  close_distance in meters: {close_distance_m:.15e} (should be 0.1)")
    print(f"  R_center in meters: {R_center:.15e} (should be ~0.100xxx)")
    if abs(pixel_size_m - 0.0001) > 1e-10:
        print("  ⚠️  WARNING: pixel_size is not 0.0001 meters!")
    if abs(close_distance_m - 0.1) > 1e-6:
        print("  ⚠️  WARNING: close_distance is not 0.1 meters!")
    print()

    # Check 2: Is r_factor being calculated correctly?
    print("Check 2: r_factor calculation")
    if hasattr(detector, 'r_factor'):
        print(f"  r_factor: {detector.r_factor.item():.15e}")
        print(f"  Expected: ~1.0 for unrotated detector")
        if abs(detector.r_factor.item() - 1.0) > 1e-6:
            print("  ⚠️  WARNING: r_factor is not 1.0 for unrotated detector!")
    else:
        print("  ⚠️  WARNING: r_factor not calculated!")
    print()

    # Check 3: Is distance_corrected being used correctly?
    print("Check 3: Distance correction")
    if hasattr(detector, 'distance_corrected'):
        if detector.distance_corrected is not None:
            print(f"  distance_corrected: {detector.distance_corrected.item():.15e} m")
            print(f"  Expected: 0.1 m for unrotated detector")
            if abs(detector.distance_corrected.item() - 0.1) > 1e-6:
                print("  ⚠️  WARNING: distance_corrected is not 0.1 meters!")
        else:
            print("  distance_corrected: None")
    else:
        print("  ⚠️  WARNING: distance_corrected not set!")
    print()

    # Check 4: pix0_vector correctness
    print("Check 4: pix0_vector position")
    print(f"  pix0_vector: {detector.pix0_vector.cpu().numpy()}")
    print(f"  Expected: approximately [-0.0512, 0.0512, 0.1] for MOSFLM BEAM pivot")
    expected_pix0 = torch.tensor([-0.05125, 0.05125, 0.1], dtype=detector.pix0_vector.dtype)
    diff = torch.abs(detector.pix0_vector.cpu() - expected_pix0)
    print(f"  Difference from expected: {diff.cpu().numpy()}")
    if torch.any(diff > 1e-3):
        print("  ⚠️  WARNING: pix0_vector differs significantly from expected!")
    print()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("If omega calculation is correct, the radial intensity pattern suggests:")
    print("  1. Check if C code uses different close_distance formula")
    print("  2. Check if C code applies additional normalization factor")
    print("  3. Check if pixel coordinate calculation has systematic error")
    print("  4. Compare trace output from C code for same test pixels")
    print()
    print("Next steps:")
    print("  1. Generate C trace for pixels (512,512), (512,700), (512,900)")
    print("  2. Compare omega values line-by-line with this output")
    print("  3. Look for first divergence point in calculation chain")
    print()


if __name__ == "__main__":
    diagnose_omega()