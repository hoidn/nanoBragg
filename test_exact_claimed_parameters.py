#!/usr/bin/env python3
"""
Test the EXACT parameters that were reported to achieve 0.993 correlation.
"""

import os
import sys
from pathlib import Path
import torch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variable
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.config import (
    BeamConfig,
    CrystalConfig,
    DetectorConfig,
    DetectorConvention,
    DetectorPivot,
)
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

# Import C reference components
sys.path.append("scripts")
from c_reference_runner import CReferenceRunner
import numpy as np
import json

def test_exact_claimed_fix():
    """Test with the EXACT parameters claimed to achieve 0.993 correlation."""
    print(f"\n🔬 Testing EXACT claimed parameters that achieved 0.993")
    print("   rotx=5, roty=3, rotz=2, twotheta=15, beam=(51.2, 51.2)")
    
    # Exact configuration that was claimed to work
    test_detector_config = DetectorConfig(
        distance_mm=100.0,
        beam_center_s=51.2,  # EXACT value from reported command
        beam_center_f=51.2,  # EXACT value from reported command
        detector_rotx_deg=5.0,   # EXACT value from reported command
        detector_roty_deg=3.0,   # EXACT value from reported command
        detector_rotz_deg=2.0,   # EXACT value from reported command
        detector_twotheta_deg=15.0, # EXACT value from reported command
        detector_pivot=DetectorPivot.BEAM,
        detector_convention=DetectorConvention.MOSFLM,
    )
    
    # Standard crystal config
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0,
        phi_start_deg=0.0,
        osc_range_deg=0.0,
        mosaic_spread_deg=0.0,
    )
    
    # Standard beam config  
    beam_config = BeamConfig(wavelength_A=6.2)
    
    # Create PyTorch simulation
    crystal = Crystal(crystal_config)
    detector = Detector(test_detector_config)
    simulator = Simulator(crystal, detector, crystal_config)
    pytorch_image = simulator.run()
    
    print(f"✅ PyTorch simulation completed")
    
    # Run C reference with identical parameters
    c_runner = CReferenceRunner()
    c_image = c_runner.run_simulation(
        detector_config=test_detector_config,
        crystal_config=crystal_config,
        beam_config=beam_config,
    )
    
    if c_image is not None:
        print(f"✅ C reference simulation completed")
        
        # Convert pytorch image for comparison
        pytorch_np = pytorch_image.cpu().numpy()
        
        # Compute correlation with masking
        mask = (pytorch_np > 1e-10) | (c_image > 1e-10)
        if mask.sum() > 0:
            correlation = np.corrcoef(
                pytorch_np.flatten()[mask.flatten()],
                c_image.flatten()[mask.flatten()]
            )[0, 1]
            
            print(f"📊 PyTorch vs C correlation: {correlation:.6f}")
            status = "✅ Good" if correlation > 0.99 else "❌ Poor"
            print(f"   Status: {status}")
            
            return correlation
        else:
            print("❌ No valid pixels for correlation")
            return 0.0
    else:
        print("❌ C reference execution failed")
        return 0.0

if __name__ == "__main__":
    correlation = test_exact_claimed_fix()
    print(f"\n{'='*60}")
    print(f"FINAL RESULT: {correlation:.6f}")
    if correlation > 0.99:
        print("✅ SUCCESS: High correlation achieved!")
    else:
        print("❌ FAILURE: Still getting poor correlation")
    print(f"{'='*60}")