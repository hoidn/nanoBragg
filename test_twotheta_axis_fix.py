#!/usr/bin/env python3
"""
Test fixing the twotheta axis sign to match C code.
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

def test_twotheta_axis(axis_vector, label):
    """Test a specific twotheta axis configuration."""
    print(f"\n🔬 Testing twotheta with axis {axis_vector} ({label})")
    
    # Test configuration (twotheta only, with specified axis)
    test_detector_config = DetectorConfig(
        distance_mm=100.0,
        beam_center_s=51.2,
        beam_center_f=51.2,
        detector_rotx_deg=0.0,
        detector_roty_deg=0.0,
        detector_rotz_deg=0.0,
        detector_twotheta_deg=15.0,
        twotheta_axis=torch.tensor(axis_vector, dtype=torch.float64),
        detector_pivot=DetectorPivot.BEAM,
        detector_convention=DetectorConvention.MOSFLM,
    )
    
    # Crystal and beam configuration
    crystal_config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        default_F=100.0,
        mosaic_domains=5,
        mosaic_spread_deg=0.1,
    )
    
    beam_config = BeamConfig(
        wavelength_A=6.2,
        source_distance_mm=1000.0,
        source_size_mm=0.1,
    )
    
    # Create models and run PyTorch simulation
    detector = Detector(test_detector_config)
    crystal = Crystal(crystal_config)
    simulator = Simulator(
        detector=detector,
        crystal=crystal,
        beam_config=beam_config,
    )
    
    pytorch_result = simulator.run()
    pytorch_image = pytorch_result.detach().cpu().numpy()
    
    # Run C reference
    runner = CReferenceRunner()
    
    # Test configuration 
    c_image = runner.run_simulation(
        test_detector_config, crystal_config, beam_config, 
        label=f"twotheta_axis_{label}"
    )
    
    # Compute correlation
    correlation = np.corrcoef(pytorch_image.flat, c_image.flat)[0, 1]
    
    print(f"📊 PyTorch vs C correlation: {correlation:.6f}")
    
    status = "✅ Good" if correlation > 0.99 else "❌ Poor"
    print(f"   Status: {status}")
    
    return correlation

def main():
    print("Twotheta Axis Sign Test")
    print("=" * 30)
    
    # Test both axis directions
    results = []
    
    # Current implementation (negative Z)
    corr_neg_z = test_twotheta_axis([0.0, 0.0, -1.0], "negative_Z")
    results.append(("negative_Z", corr_neg_z))
    
    # C code default (positive Z)
    corr_pos_z = test_twotheta_axis([0.0, 0.0, 1.0], "positive_Z") 
    results.append(("positive_Z", corr_pos_z))
    
    # Also test X and Y axes for completeness
    corr_pos_y = test_twotheta_axis([0.0, 1.0, 0.0], "positive_Y")
    results.append(("positive_Y", corr_pos_y))
    
    corr_neg_y = test_twotheta_axis([0.0, -1.0, 0.0], "negative_Y")
    results.append(("negative_Y", corr_neg_y))
    
    print("\n" + "=" * 30)
    print("SUMMARY:")
    print("=" * 30)
    for label, corr in results:
        status = "✅ Good" if corr > 0.99 else "❌ Poor"  
        print(f"{label:12s}: {corr:8.6f} {status}")
    
    # Find the best axis
    best_label, best_corr = max(results, key=lambda x: x[1])
    print(f"\n🎯 Best axis: {best_label} with correlation {best_corr:.6f}")

if __name__ == "__main__":
    main()