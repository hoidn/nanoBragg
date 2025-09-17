#!/usr/bin/env python3
"""
Debug the baseline detector geometry issue.
Since even no-rotation case has 7.8% correlation, the issue is fundamental.
"""

import os
import sys
import torch
import numpy as np
from pathlib import Path

# Set environment variable
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.detector import Detector

def debug_baseline_detector():
    """Debug baseline detector geometry with NO rotations."""
    
    print("BASELINE DETECTOR GEOMETRY DEBUG")
    print("=" * 50)
    print("Testing detector geometry with ZERO rotations")
    print()
    
    # Baseline configuration - NO rotations at all
    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=51.25,
        beam_center_f=51.25,
        detector_convention=DetectorConvention.MOSFLM,
        detector_rotx_deg=0.0,    # NO ROTATION
        detector_roty_deg=0.0,    # NO ROTATION  
        detector_rotz_deg=0.0,    # NO ROTATION
        detector_twotheta_deg=0.0,  # NO TWOTHETA
        detector_pivot=DetectorPivot.BEAM,
    )
    
    print(f"Configuration:")
    print(f"  All rotations: 0°")
    print(f"  Beam center: ({detector_config.beam_center_s}, {detector_config.beam_center_f}) mm") 
    print(f"  Distance: {detector_config.distance_mm} mm")
    print(f"  Pixel size: {detector_config.pixel_size_mm} mm")
    print(f"  Convention: {detector_config.detector_convention}")
    print()
    
    # Create detector
    detector = Detector(detector_config)
    
    # Expected values for baseline MOSFLM
    print("Expected vs Actual Values:")
    print("-" * 30)
    
    # Basis vectors should be identity for no rotations (MOSFLM convention)
    dtype = detector.fdet_vec.dtype  # Match detector dtype
    expected_fdet = torch.tensor([0.0, 0.0, 1.0], dtype=dtype)  # Fast = +Z
    expected_sdet = torch.tensor([0.0, -1.0, 0.0], dtype=dtype)  # Slow = -Y  
    expected_odet = torch.tensor([1.0, 0.0, 0.0], dtype=dtype)   # Normal = +X
    
    print(f"fdet_vec:")
    print(f"  Expected: {expected_fdet.numpy()}")
    print(f"  Actual:   {detector.fdet_vec.detach().numpy()}")
    print(f"  Match:    {torch.allclose(detector.fdet_vec, expected_fdet, atol=1e-10)}")
    print()
    
    print(f"sdet_vec:")
    print(f"  Expected: {expected_sdet.numpy()}")  
    print(f"  Actual:   {detector.sdet_vec.detach().numpy()}")
    print(f"  Match:    {torch.allclose(detector.sdet_vec, expected_sdet, atol=1e-10)}")
    print()
    
    print(f"odet_vec:")
    print(f"  Expected: {expected_odet.numpy()}")
    print(f"  Actual:   {detector.odet_vec.detach().numpy()}")
    print(f"  Match:    {torch.allclose(detector.odet_vec, expected_odet, atol=1e-10)}")
    print()
    
    # Beam center calculation (MOSFLM adds +0.5 pixel)
    beam_center_s_pixels = detector_config.beam_center_s / detector_config.pixel_size_mm  # 512.5
    beam_center_f_pixels = detector_config.beam_center_f / detector_config.pixel_size_mm  # 512.5
    
    # Add MOSFLM +0.5 offset
    sbeam_pixels = beam_center_s_pixels + 0.5  # 513.0
    fbeam_pixels = beam_center_f_pixels + 0.5  # 513.0
    
    # Convert to meters
    pixel_size_m = detector_config.pixel_size_mm / 1000.0  # 0.0001 m
    expected_sbeam_m = sbeam_pixels * pixel_size_m  # 0.0513 m
    expected_fbeam_m = fbeam_pixels * pixel_size_m  # 0.0513 m
    
    print(f"Beam center calculation:")
    print(f"  Input (mm): ({detector_config.beam_center_s}, {detector_config.beam_center_f})")
    print(f"  Pixels: ({beam_center_s_pixels}, {beam_center_f_pixels})")
    print(f"  +0.5 offset: ({sbeam_pixels}, {fbeam_pixels})")  
    print(f"  Meters: ({expected_sbeam_m:.6f}, {expected_fbeam_m:.6f})")
    print()
    
    # pix0_vector calculation
    distance_m = detector_config.distance_mm / 1000.0  # 0.1 m
    
    # Expected: pix0 = distance * odet - sbeam * sdet - fbeam * fdet
    expected_pix0 = (distance_m * expected_odet - 
                     expected_sbeam_m * expected_sdet - 
                     expected_fbeam_m * expected_fdet)
    
    print(f"pix0_vector calculation:")
    print(f"  Formula: distance * odet - sbeam * sdet - fbeam * fdet")
    print(f"  = {distance_m:.3f} * {expected_odet.numpy()} - {expected_sbeam_m:.6f} * {expected_sdet.numpy()} - {expected_fbeam_m:.6f} * {expected_fdet.numpy()}")
    print(f"  Expected: {expected_pix0.numpy()}")
    print(f"  Actual:   {detector.pix0_vector.detach().numpy()}")
    print(f"  Match:    {torch.allclose(detector.pix0_vector, expected_pix0, atol=1e-10)}")
    
    diff = detector.pix0_vector.detach().numpy() - expected_pix0.numpy()
    print(f"  Difference: {diff}")
    print(f"  |Difference|: {np.linalg.norm(diff) * 1000:.1f} mm")
    print()
    
    # Test a simple pixel coordinate
    print("Test pixel coordinate calculation:")
    print("-" * 40)
    
    # Test center pixel (512, 512) - should be at beam center
    s_idx, f_idx = 512, 512
    
    # Expected position relative to pix0  
    s_offset = s_idx * pixel_size_m  # 0.0512 m
    f_offset = f_idx * pixel_size_m  # 0.0512 m
    
    expected_pixel_pos = expected_pix0 + s_offset * expected_sdet + f_offset * expected_fdet
    
    print(f"Center pixel (512, 512):")
    print(f"  s_offset: {s_offset:.6f} m")  
    print(f"  f_offset: {f_offset:.6f} m")
    print(f"  Expected position: {expected_pixel_pos.numpy()}")
    
    # Calculate with detector method
    pixel_pos = detector.get_pixel_positions(torch.tensor([[s_idx, f_idx]]))
    print(f"  Detector position: {pixel_pos[0].detach().numpy()}")
    print(f"  Match: {torch.allclose(pixel_pos[0], expected_pixel_pos, atol=1e-10)}")
    
    pos_diff = pixel_pos[0].detach().numpy() - expected_pixel_pos.numpy()
    print(f"  Difference: {pos_diff}")
    print(f"  |Difference|: {np.linalg.norm(pos_diff) * 1000:.1f} mm")

def main():
    debug_baseline_detector()

if __name__ == "__main__":
    main()