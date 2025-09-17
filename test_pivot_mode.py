#!/usr/bin/env python3
"""
Test the critical discovery: C code automatically switches to SAMPLE pivot when twotheta is used.
"""

import os
import sys
from pathlib import Path

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

def test_pivot_mode(pivot_mode, twotheta_deg, label):
    """Test a specific pivot mode with twotheta."""
    print(f"\n🔬 Testing pivot={pivot_mode.name}, twotheta={twotheta_deg}° ({label})")
    
    # Test configuration 
    test_detector_config = DetectorConfig(
        distance_mm=100.0,
        beam_center_s=51.2,
        beam_center_f=51.2,
        detector_rotx_deg=0.0,
        detector_roty_deg=0.0,
        detector_rotz_deg=0.0,
        detector_twotheta_deg=twotheta_deg,
        detector_pivot=pivot_mode,
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
        label=f"pivot_{label}"
    )
    
    # Compute correlation
    correlation = np.corrcoef(pytorch_image.flat, c_image.flat)[0, 1]
    
    print(f"📊 PyTorch vs C correlation: {correlation:.6f}")
    
    status = "✅ EXCELLENT" if correlation > 0.999 else "✅ Good" if correlation > 0.99 else "❌ Poor"
    print(f"   Status: {status}")
    
    return correlation

def main():
    print("CRITICAL PIVOT MODE TEST")
    print("=" * 40)
    print("Testing hypothesis: C code auto-switches to SAMPLE pivot when twotheta is used")
    
    results = []
    
    # Test the BEAM pivot (what we've been using incorrectly)
    corr_beam = test_pivot_mode(DetectorPivot.BEAM, 15.0, "BEAM_15deg")
    results.append(("BEAM pivot", corr_beam))
    
    # Test the SAMPLE pivot (what C code actually uses!)
    corr_sample = test_pivot_mode(DetectorPivot.SAMPLE, 15.0, "SAMPLE_15deg") 
    results.append(("SAMPLE pivot", corr_sample))
    
    # Also test with combined rotations using SAMPLE pivot
    print(f"\n🔬 Testing FULL combined case with SAMPLE pivot")
    test_detector_config = DetectorConfig(
        distance_mm=100.0,
        beam_center_s=51.2,
        beam_center_f=51.2,
        detector_rotx_deg=5.0,
        detector_roty_deg=3.0,
        detector_rotz_deg=2.0,
        detector_twotheta_deg=15.0,
        detector_pivot=DetectorPivot.SAMPLE,  # THE CRITICAL FIX!
        detector_convention=DetectorConvention.MOSFLM,
    )
    
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
    
    # Run simulation
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
        label="SAMPLE_combined"
    )
    
    corr_combined = np.corrcoef(pytorch_image.flat, c_image.flat)[0, 1]
    results.append(("SAMPLE combined", corr_combined))
    
    print(f"📊 Combined PyTorch vs C correlation: {corr_combined:.6f}")
    status = "✅ EXCELLENT" if corr_combined > 0.999 else "✅ Good" if corr_combined > 0.99 else "❌ Poor"
    print(f"   Status: {status}")
    
    print("\n" + "=" * 40)
    print("FINAL RESULTS:")
    print("=" * 40)
    for label, corr in results:
        if corr > 0.999:
            status = "🎯 PERFECT!"
        elif corr > 0.99:
            status = "✅ Good"
        else:
            status = "❌ Poor"
        print(f"{label:15s}: {corr:8.6f} {status}")
    
    # Determine if we found the fix
    best_label, best_corr = max(results, key=lambda x: x[1])
    if best_corr > 0.999:
        print(f"\n🎉 ROOT CAUSE FOUND AND FIXED!")
        print(f"🎯 Solution: Use SAMPLE pivot mode when twotheta > 0")
        print(f"🎯 Best result: {best_label} = {best_corr:.6f}")
    else:
        print(f"\n🔍 Still debugging needed...")
        print(f"🎯 Best so far: {best_label} = {best_corr:.6f}")

if __name__ == "__main__":
    main()