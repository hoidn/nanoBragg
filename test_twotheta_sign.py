#!/usr/bin/env python3
"""
Test fixing the twotheta rotation angle sign.
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

def test_twotheta_sign(twotheta_deg, label):
    """Test a specific twotheta angle (positive or negative)."""
    print(f"\n🔬 Testing twotheta = {twotheta_deg}° ({label})")
    
    # Test configuration 
    test_detector_config = DetectorConfig(
        distance_mm=100.0,
        beam_center_s=51.2,
        beam_center_f=51.2,
        detector_rotx_deg=0.0,
        detector_roty_deg=0.0,
        detector_rotz_deg=0.0,
        detector_twotheta_deg=twotheta_deg,
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
    c_image = runner.run_simulation(
        test_detector_config, crystal_config, beam_config, 
        label=f"twotheta_{label}"
    )
    
    # Compute correlation
    correlation = np.corrcoef(pytorch_image.flat, c_image.flat)[0, 1]
    
    print(f"📊 PyTorch vs C correlation: {correlation:.6f}")
    
    status = "✅ Good" if correlation > 0.99 else "❌ Poor"
    print(f"   Status: {status}")
    
    return correlation

def main():
    print("Twotheta Angle Sign Test")
    print("=" * 30)
    
    # Test both angle signs and magnitudes
    results = []
    
    # Current failing case
    corr_pos_15 = test_twotheta_sign(15.0, "plus_15")
    results.append(("plus_15", corr_pos_15))
    
    # Try negative angle
    corr_neg_15 = test_twotheta_sign(-15.0, "minus_15")
    results.append(("minus_15", corr_neg_15))
    
    # Try smaller angles to see if magnitude matters
    corr_pos_5 = test_twotheta_sign(5.0, "plus_5")
    results.append(("plus_5", corr_pos_5))
    
    corr_neg_5 = test_twotheta_sign(-5.0, "minus_5")
    results.append(("minus_5", corr_neg_5))
    
    print("\n" + "=" * 30)
    print("SUMMARY:")
    print("=" * 30)
    for label, corr in results:
        status = "✅ Good" if corr > 0.99 else "❌ Poor"  
        print(f"{label:10s}: {corr:8.6f} {status}")
    
    # Find the best angle
    best_label, best_corr = max(results, key=lambda x: x[1])
    print(f"\n🎯 Best angle: {best_label} with correlation {best_corr:.6f}")

if __name__ == "__main__":
    main()