#!/usr/bin/env python3
"""
Test if PyTorch can match MOSFLM C reference exactly.
"""

import os
import torch
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.detector import Detector

def test_mosflm_match():
    """Test if PyTorch matches MOSFLM C reference for pix0_vector."""
    
    print("=== Testing PyTorch vs MOSFLM C Reference ===\n")
    
    # Expected MOSFLM C reference result
    c_mosflm_pix0 = np.array([0.112087366299472, 0.0653100408232811, -0.0556023303792543])
    
    # Create detector config that should match MOSFLM behavior
    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=61.2,
        beam_center_f=61.2,
        detector_rotx_deg=5.0,
        detector_roty_deg=3.0,
        detector_rotz_deg=2.0,
        detector_twotheta_deg=15.0,
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.SAMPLE,
        twotheta_axis=None  # Should trigger MOSFLM convention
    )
    
    print(f"Config twotheta_axis after init: {detector_config.twotheta_axis}")
    
    # Create PyTorch detector
    detector = Detector(detector_config)
    pytorch_pix0 = detector.pix0_vector.detach().numpy()
    
    print(f"C MOSFLM pix0_vector:     {c_mosflm_pix0}")
    print(f"PyTorch pix0_vector:      {pytorch_pix0}")
    
    diff = pytorch_pix0 - c_mosflm_pix0
    diff_magnitude = np.linalg.norm(diff)
    
    print(f"Difference:               {diff}")
    print(f"Difference magnitude:     {diff_magnitude:.6e} m")
    
    # Check if custom convention detection is working
    is_custom = detector._is_custom_convention()
    print(f"Is custom convention:     {is_custom}")
    
    if diff_magnitude < 1e-12:
        print("✅ SUCCESS: PyTorch matches MOSFLM C reference exactly!")
    elif diff_magnitude < 1e-3:
        print("⚠️  CLOSE: PyTorch is close but not exact match")
    else:
        print("❌ FAILURE: PyTorch does not match MOSFLM C reference")


if __name__ == "__main__":
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    test_mosflm_match()