#!/usr/bin/env python3
"""
Test multiple rotation configurations to identify patterns.
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot

# Test configurations
test_configs = [
    # Identity (baseline - should work)
    {"name": "Identity", "rotx": 0, "roty": 0, "rotz": 0, "twotheta": 0},
    
    # Single axis rotations
    {"name": "X-only", "rotx": 5, "roty": 0, "rotz": 0, "twotheta": 0},
    {"name": "Y-only", "rotx": 0, "roty": 5, "rotz": 0, "twotheta": 0},
    {"name": "Z-only", "rotx": 0, "roty": 0, "rotz": 5, "twotheta": 0},
    {"name": "TwoTheta-only", "rotx": 0, "roty": 0, "rotz": 0, "twotheta": 15},
    
    # Original problematic case
    {"name": "Problematic", "rotx": 5, "roty": 3, "rotz": 2, "twotheta": 15},
]

print("ROTATION CONFIGURATION ANALYSIS")
print("=" * 60)

for test in test_configs:
    config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=51.2,
        beam_center_f=51.2,
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM,
        detector_rotx_deg=test["rotx"],
        detector_roty_deg=test["roty"],
        detector_rotz_deg=test["rotz"],
        detector_twotheta_deg=test["twotheta"],
    )
    
    detector = Detector(config=config)
    
    # Check if using default path vs calculated path
    is_default = detector._is_default_config()
    
    # Calculate deviation from identity vectors
    identity_fdet = torch.tensor([0.0, 0.0, 1.0])
    identity_sdet = torch.tensor([0.0, -1.0, 0.0])
    identity_odet = torch.tensor([1.0, 0.0, 0.0])
    
    fdet_dev = torch.norm(detector.fdet_vec - identity_fdet).item()
    sdet_dev = torch.norm(detector.sdet_vec - identity_sdet).item()
    odet_dev = torch.norm(detector.odet_vec - identity_odet).item()
    
    total_dev = fdet_dev + sdet_dev + odet_dev
    
    print(f"\n{test['name']:<15}: rotx={test['rotx']:2d}° roty={test['roty']:2d}° rotz={test['rotz']:2d}° twotheta={test['twotheta']:2d}°")
    print(f"{'':15}  Default path: {is_default}")
    print(f"{'':15}  Total deviation: {total_dev:.6f}")
    print(f"{'':15}  Basis deviations: F={fdet_dev:.4f}, S={sdet_dev:.4f}, O={odet_dev:.4f}")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("- Identity should use default path and have zero deviation")
print("- Single rotations should show which transformations are problematic") 
print("- Default path bypasses rotation calculations entirely")
print("- Non-zero deviations indicate rotation matrix applications")