#!/usr/bin/env python3
"""
Verify basis vector conventions between PyTorch and C implementations.

This script checks initial basis vector definitions, orthogonality,
and handedness for different detector conventions.
"""

import os
import sys
from pathlib import Path
import numpy as np
import torch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

# Set environment variable for MKL
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.detector import Detector


def verify_basis_vectors():
    """Compare basis vectors for different conventions and configurations."""
    
    print("=" * 60)
    print("BASIS VECTOR CONVENTION VERIFICATION")
    print("=" * 60)
    
    # Test configurations
    configs = {
        "MOSFLM_BEAM": {
            "convention": DetectorConvention.MOSFLM,
            "pivot": DetectorPivot.BEAM,
            "distance_mm": 100.0,
            "beam_center_s": 51.2,
            "beam_center_f": 51.2,
            "pixel_size_mm": 0.1,
        },
        "MOSFLM_SAMPLE": {
            "convention": DetectorConvention.MOSFLM,
            "pivot": DetectorPivot.SAMPLE,
            "distance_mm": 100.0,
            "beam_center_s": 51.2,
            "beam_center_f": 51.2,
            "pixel_size_mm": 0.1,
        },
        "XDS_BEAM": {
            "convention": DetectorConvention.XDS,
            "pivot": DetectorPivot.BEAM,
            "distance_mm": 100.0,
            "beam_center_s": 51.2,
            "beam_center_f": 51.2,
            "pixel_size_mm": 0.1,
        }
    }
    
    results = {}
    
    for config_name, config_params in configs.items():
        print(f"\n{'=' * 40}")
        print(f"Configuration: {config_name}")
        print("-" * 40)
        
        # Create detector config
        config = DetectorConfig(
            detector_convention=config_params["convention"],
            detector_pivot=config_params["pivot"],
            distance_mm=config_params["distance_mm"],
            beam_center_s=config_params["beam_center_s"],
            beam_center_f=config_params["beam_center_f"],
            pixel_size_mm=config_params["pixel_size_mm"],
            detector_rotx_deg=0.0,  # No rotation initially
            detector_roty_deg=0.0,
            detector_rotz_deg=0.0,
            detector_twotheta_deg=0.0,
        )
        
        # Create detector
        detector = Detector(config)
        
        # Extract basis vectors
        fdet = detector.fdet_vec.numpy()
        sdet = detector.sdet_vec.numpy()
        
        # Calculate derived properties
        dot_product = np.dot(fdet, sdet)
        cross_product = np.cross(fdet, sdet)
        fdet_magnitude = np.linalg.norm(fdet)
        sdet_magnitude = np.linalg.norm(sdet)
        
        print(f"\nBasis vectors:")
        print(f"  fdet (fast): {fdet}")
        print(f"  sdet (slow): {sdet}")
        
        print(f"\nMagnitudes:")
        print(f"  |fdet| = {fdet_magnitude:.6f} (should be 1.0)")
        print(f"  |sdet| = {sdet_magnitude:.6f} (should be 1.0)")
        
        print(f"\nOrthogonality:")
        print(f"  fdet·sdet = {dot_product:.2e} (should be 0)")
        
        print(f"\nCross product:")
        print(f"  fdet×sdet = {cross_product}")
        print(f"  |fdet×sdet| = {np.linalg.norm(cross_product):.6f}")
        
        # Check handedness
        if config_params["convention"] == DetectorConvention.MOSFLM:
            expected_beam_dir = np.array([1.0, 0.0, 0.0])
            alignment = np.dot(cross_product, expected_beam_dir)
            print(f"\nHandedness check (MOSFLM):")
            print(f"  Expected beam direction: {expected_beam_dir}")
            print(f"  Alignment with beam: {alignment:.6f} (should be ~1.0)")
        
        # Store results
        results[config_name] = {
            "fdet": fdet,
            "sdet": sdet,
            "orthogonal": abs(dot_product) < 1e-10,
            "normalized": abs(fdet_magnitude - 1.0) < 1e-10 and abs(sdet_magnitude - 1.0) < 1e-10,
            "cross_product": cross_product
        }
    
    # Test with rotations
    print("\n" + "=" * 60)
    print("BASIS VECTORS WITH ROTATIONS")
    print("-" * 60)
    
    # Create detector with rotations
    config_rotated = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.SAMPLE,
        distance_mm=100.0,
        beam_center_s=51.2,
        beam_center_f=51.2,
        pixel_size_mm=0.1,
        detector_rotx_deg=5.0,
        detector_roty_deg=3.0,
        detector_rotz_deg=2.0,
        detector_twotheta_deg=20.0,
    )
    
    detector_rotated = Detector(config_rotated)
    
    fdet_rot = detector_rotated.fdet_vec.numpy()
    sdet_rot = detector_rotated.sdet_vec.numpy()
    
    print(f"\nRotation parameters:")
    print(f"  rotx: 5°, roty: 3°, rotz: 2°, twotheta: 20°")
    
    print(f"\nRotated basis vectors:")
    print(f"  fdet: {fdet_rot}")
    print(f"  sdet: {sdet_rot}")
    
    # Verify properties are preserved
    dot_rot = np.dot(fdet_rot, sdet_rot)
    mag_f_rot = np.linalg.norm(fdet_rot)
    mag_s_rot = np.linalg.norm(sdet_rot)
    
    print(f"\nProperties after rotation:")
    print(f"  |fdet| = {mag_f_rot:.6f} (should be 1.0)")
    print(f"  |sdet| = {mag_s_rot:.6f} (should be 1.0)")
    print(f"  fdet·sdet = {dot_rot:.2e} (should be 0)")
    
    # Compare pix0_vector calculation
    print("\n" + "=" * 60)
    print("PIX0_VECTOR CALCULATION")
    print("-" * 60)
    
    pix0 = detector_rotated.pix0_vector.numpy()
    print(f"\npix0_vector (SAMPLE pivot, rotated): {pix0}")
    print(f"|pix0_vector| = {np.linalg.norm(pix0):.6f} meters")
    
    # Calculate expected distance from origin
    expected_distance = config_rotated.distance_mm / 1000.0  # Convert to meters
    actual_distance = np.linalg.norm(pix0)
    
    print(f"\nDistance verification:")
    print(f"  Expected detector distance: {expected_distance:.6f} m")
    print(f"  Actual |pix0_vector|: {actual_distance:.6f} m")
    print(f"  Difference: {abs(actual_distance - expected_distance):.2e} m")
    
    # Save results
    output_dir = Path(__file__).parent.parent / "results" / "rotation_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "basis_vector_verification.txt", "w") as f:
        f.write("Basis Vector Verification Results\n\n")
        
        for config_name, result in results.items():
            f.write(f"{config_name}:\n")
            f.write(f"  Orthogonal: {result['orthogonal']}\n")
            f.write(f"  Normalized: {result['normalized']}\n")
            f.write(f"  Cross product: {result['cross_product']}\n\n")
    
    print(f"\nResults saved to: {output_dir / 'basis_vector_verification.txt'}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("-" * 60)
    
    all_orthogonal = all(r["orthogonal"] for r in results.values())
    all_normalized = all(r["normalized"] for r in results.values())
    
    if all_orthogonal and all_normalized:
        print("✅ All basis vectors are orthonormal")
    else:
        print("❌ Basis vector issues detected:")
        if not all_orthogonal:
            print("   - Some vectors are not orthogonal")
        if not all_normalized:
            print("   - Some vectors are not unit length")
    
    if abs(dot_rot) < 1e-10 and abs(mag_f_rot - 1.0) < 1e-10:
        print("✅ Orthonormality preserved under rotation")
    else:
        print("❌ Rotation affects orthonormality")


if __name__ == "__main__":
    verify_basis_vectors()