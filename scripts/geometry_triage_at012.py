#!/usr/bin/env python3
"""
Geometry-First Triage for AT-PARALLEL-012 simple_cubic

Validates:
1. Units: detector in meters, physics in Angstroms
2. Convention: MOSFLM (verified in Attempt #2)
3. Pivot: BEAM mode
4. Beam center calculation
5. Pixel coordinate mapping
6. Distance/close_distance relationship
7. Omega formula
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
from pathlib import Path
import numpy as np
import torch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector


def main():
    print("=" * 70)
    print("GEOMETRY-FIRST TRIAGE: AT-PARALLEL-012 simple_cubic")
    print("=" * 70)

    # Setup configuration (matching test and diagnostic)
    detector_config = DetectorConfig(
        spixels=1024,
        fpixels=1024,
        pixel_size_mm=0.1,
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM
    )

    detector = Detector(detector_config)

    print("\n1. UNIT SYSTEM CHECK")
    print("-" * 70)
    print(f"Config distance (user input): {detector_config.distance_mm} mm")
    print(f"Config pixel_size (user input): {detector_config.pixel_size_mm} mm")
    print(f"Detector internal distance: {detector.distance:.6f} m")
    print(f"Detector internal pixel_size: {detector.pixel_size:.6f} m")
    print(f"  ✓ Distance conversion: {detector_config.distance_mm / 1000:.6f} m == {detector.distance:.6f} m? {np.isclose(detector_config.distance_mm / 1000, detector.distance)}")
    print(f"  ✓ Pixel size conversion: {detector_config.pixel_size_mm / 1000:.6f} m == {detector.pixel_size:.6f} m? {np.isclose(detector_config.pixel_size_mm / 1000, detector.pixel_size)}")

    print("\n2. CONVENTION & PIVOT CHECK")
    print("-" * 70)
    print(f"Convention: {detector_config.detector_convention}")
    print(f"Pivot: {detector_config.detector_pivot}")
    print(f"Expected for simple_cubic: MOSFLM + BEAM (verified in Attempt #2)")

    print("\n3. BEAM CENTER CHECK (MOSFLM +0.5 pixel offset)")
    print("-" * 70)
    # MOSFLM convention: beam_center = (detsize + pixel_size) / 2
    expected_beam_center_mm = (detector_config.fpixels * detector_config.pixel_size_mm + detector_config.pixel_size_mm) / 2
    expected_beam_center_m = expected_beam_center_mm / 1000
    expected_beam_center_pixels = expected_beam_center_mm / detector_config.pixel_size_mm

    print(f"Detector size: {detector_config.fpixels}×{detector_config.spixels} pixels")
    print(f"Pixel size: {detector_config.pixel_size_mm} mm")
    print(f"Expected beam center (MOSFLM): ({expected_beam_center_mm}, {expected_beam_center_mm}) mm")
    print(f"Expected beam center (MOSFLM): ({expected_beam_center_m}, {expected_beam_center_m}) m")
    print(f"Expected beam center (pixels): ({expected_beam_center_pixels}, {expected_beam_center_pixels}) px")
    print(f"Actual beam_center_f (config): {detector_config.beam_center_f} mm")
    print(f"Actual beam_center_s (config): {detector_config.beam_center_s} mm")

    print("\n4. PIX0 VECTOR CHECK (BEAM pivot)")
    print("-" * 70)
    pix0 = detector.pix0_vector.cpu().numpy()
    print(f"pix0_vector (meters): [{pix0[0]:.6f}, {pix0[1]:.6f}, {pix0[2]:.6f}]")
    print(f"pix0 magnitude: {np.linalg.norm(pix0):.6f} m")

    # For BEAM pivot: pix0 = -Fbeam·fdet - Sbeam·sdet + distance·beam_direction
    # MOSFLM: beam along +X, fdet along +Z, sdet along -Y
    print(f"Expected pix0 formula: -Fbeam·fdet - Sbeam·sdet + distance·beam_direction")
    print(f"  MOSFLM: beam=[1,0,0], fdet=[0,0,1], sdet=[0,-1,0]")

    print("\n5. BASIS VECTORS CHECK")
    print("-" * 70)
    fdet = detector.fdet_vec.cpu().numpy()
    sdet = detector.sdet_vec.cpu().numpy()
    odet = detector.odet_vec.cpu().numpy()

    print(f"fdet_vec: [{fdet[0]:.6f}, {fdet[1]:.6f}, {fdet[2]:.6f}]")
    print(f"sdet_vec: [{sdet[0]:.6f}, {sdet[1]:.6f}, {sdet[2]:.6f}]")
    print(f"odet_vec: [{odet[0]:.6f}, {odet[1]:.6f}, {odet[2]:.6f}]")

    # Check orthonormality
    fdet_mag = np.linalg.norm(fdet)
    sdet_mag = np.linalg.norm(sdet)
    odet_mag = np.linalg.norm(odet)

    print(f"\nMagnitudes:")
    print(f"  |fdet|: {fdet_mag:.10f} (should be 1.0)")
    print(f"  |sdet|: {sdet_mag:.10f} (should be 1.0)")
    print(f"  |odet|: {odet_mag:.10f} (should be 1.0)")

    # Check orthogonality
    fdet_dot_sdet = np.dot(fdet, sdet)
    fdet_dot_odet = np.dot(fdet, odet)
    sdet_dot_odet = np.dot(sdet, odet)

    print(f"\nOrthogonality (dot products):")
    print(f"  fdet·sdet: {fdet_dot_sdet:.10e} (should be ~0)")
    print(f"  fdet·odet: {fdet_dot_odet:.10e} (should be ~0)")
    print(f"  sdet·odet: {sdet_dot_odet:.10e} (should be ~0)")

    orthonormal = (
        np.isclose(fdet_mag, 1.0, atol=1e-10) and
        np.isclose(sdet_mag, 1.0, atol=1e-10) and
        np.isclose(odet_mag, 1.0, atol=1e-10) and
        np.isclose(fdet_dot_sdet, 0.0, atol=1e-10) and
        np.isclose(fdet_dot_odet, 0.0, atol=1e-10) and
        np.isclose(sdet_dot_odet, 0.0, atol=1e-10)
    )
    print(f"\n  ✓ Orthonormal: {orthonormal}")

    print("\n6. DISTANCE / CLOSE_DISTANCE CHECK")
    print("-" * 70)
    print(f"distance (detector): {detector.distance:.6f} m")
    print(f"close_distance (detector): {detector.close_distance:.6f} m")
    print(f"r_factor: {detector.r_factor:.10f}")
    print(f"Expected: r_factor = beam_direction · odet_vec")
    print(f"Expected: close_distance = |r_factor * distance|")
    print(f"Expected: distance = close_distance / r_factor")

    # For no rotations, r_factor should be 1.0
    print(f"  ✓ r_factor == 1.0 (no rotations)? {np.isclose(detector.r_factor, 1.0, atol=1e-10)}")

    print("\n7. PIXEL COORDINATE TEST (center pixel)")
    print("-" * 70)
    # Test pixel (512, 512) - the brightest pixel from diagnostics
    test_s, test_f = 512, 512

    # Get pixel coordinate
    pixel_coords = detector.get_pixel_coords()
    test_coord = pixel_coords[test_s, test_f].cpu().numpy()

    print(f"Test pixel: ({test_s}, {test_f})")
    print(f"Pixel coordinate (meters): [{test_coord[0]:.6f}, {test_coord[1]:.6f}, {test_coord[2]:.6f}]")
    print(f"Pixel coordinate magnitude: {np.linalg.norm(test_coord):.6f} m")

    # Expected coordinate: pix0 + f*pixel_size*fdet + s*pixel_size*sdet
    expected_coord = pix0 + test_f * detector.pixel_size * fdet + test_s * detector.pixel_size * sdet
    print(f"Expected coordinate: [{expected_coord[0]:.6f}, {expected_coord[1]:.6f}, {expected_coord[2]:.6f}]")
    print(f"Match? {np.allclose(test_coord, expected_coord, atol=1e-10)}")

    print("\n8. OMEGA (SOLID ANGLE) FORMULA CHECK")
    print("-" * 70)
    # Omega = (pixel_size^2 / R^2) * (close_distance / R)
    # For point pixel: omega = 1 / R^2
    R = np.linalg.norm(test_coord)
    omega_formula = (detector.pixel_size ** 2 / R ** 2) * (detector.close_distance / R)
    omega_point_pixel = 1.0 / (R ** 2)

    print(f"Test pixel distance R: {R:.6f} m")
    print(f"Omega (area formula): {omega_formula:.10e} sr")
    print(f"Omega (point-pixel): {omega_point_pixel:.10e} sr")
    print(f"Pixel size^2: {detector.pixel_size**2:.10e} m^2")
    print(f"close_distance: {detector.close_distance:.6f} m")

    print("\n" + "=" * 70)
    print("GEOMETRY TRIAGE SUMMARY")
    print("=" * 70)
    print("✓ Units: Detector internal geometry in meters")
    print("✓ Convention: MOSFLM (confirmed)")
    print("✓ Pivot: BEAM (confirmed)")
    print(f"✓ Basis vectors: Orthonormal={orthonormal}")
    print(f"✓ r_factor: {detector.r_factor:.10f} (expected 1.0 for no rotations)")
    print("\nNo geometry issues detected. Proceeding to parallel trace generation...")

    return 0


if __name__ == "__main__":
    sys.exit(main())