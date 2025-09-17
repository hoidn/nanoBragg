#!/usr/bin/env python3
"""
Test gradient flow preservation in the detector.
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot

print("GRADIENT FLOW VERIFICATION")
print("=" * 50)

# Test configuration with differentiable parameters
distance_tensor = torch.tensor(100.0, requires_grad=True, dtype=torch.float64)
rotx_tensor = torch.tensor(5.0, requires_grad=True, dtype=torch.float64)
roty_tensor = torch.tensor(3.0, requires_grad=True, dtype=torch.float64)
rotz_tensor = torch.tensor(2.0, requires_grad=True, dtype=torch.float64)
twotheta_tensor = torch.tensor(15.0, requires_grad=True, dtype=torch.float64)

config = DetectorConfig(
    distance_mm=distance_tensor,
    pixel_size_mm=0.1,
    spixels=1024,
    fpixels=1024,
    beam_center_s=51.2,
    beam_center_f=51.2,
    detector_convention=DetectorConvention.MOSFLM,
    detector_pivot=DetectorPivot.BEAM,
    detector_rotx_deg=rotx_tensor,
    detector_roty_deg=roty_tensor,
    detector_rotz_deg=rotz_tensor,
    detector_twotheta_deg=twotheta_tensor,
)

try:
    detector = Detector(config=config)
    print("✓ Detector created successfully with tensor parameters")
    
    # Test pixel coordinates computation
    positions = detector.get_pixel_coords()
    print(f"✓ Pixel positions computed: shape {positions.shape}")
    
    # Test gradient flow by computing a loss on pixel positions
    # Use a small subset for efficiency
    subset = positions[500:520, 500:520]  # 20x20 subset around center
    loss = subset.sum()
    
    print(f"✓ Loss computed: {loss.item():.6f}")
    print(f"✓ Loss requires_grad: {loss.requires_grad}")
    
    # Backward pass
    loss.backward()
    
    # Check gradients
    params = {
        'distance_mm': distance_tensor,
        'detector_rotx_deg': rotx_tensor,
        'detector_roty_deg': roty_tensor,
        'detector_rotz_deg': rotz_tensor,
        'detector_twotheta_deg': twotheta_tensor,
    }
    
    print("\nGRADIENT CHECK:")
    all_gradients_exist = True
    for name, param in params.items():
        if param.grad is not None:
            grad_norm = torch.norm(param.grad).item()
            print(f"  {name:<20}: grad_norm = {grad_norm:.8f} ✓")
        else:
            print(f"  {name:<20}: NO GRADIENT ✗")
            all_gradients_exist = False
    
    if all_gradients_exist:
        print("\n🎉 SUCCESS: All differentiable parameters have gradients!")
        print("✓ Gradient flow is preserved through detector geometry calculations")
    else:
        print("\n⚠️  WARNING: Some parameters missing gradients")
        
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()