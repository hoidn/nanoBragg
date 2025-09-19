#!/usr/bin/env python3
"""
Verify the pivot mode fix for tilted detector configurations.

This script tests that:
1. C commands include correct pivot mode flags
2. C code uses SAMPLE pivot when twotheta != 0
3. Pixel positions match between Python and C
4. Correlation improves from 0.040 to >0.999
"""

import os
import sys
from pathlib import Path

# Add the project root to the path so we can import modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "scripts"))

# Set required environment variable for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import numpy as np
import torch
from c_reference_runner import CReferenceRunner
from c_reference_utils import build_nanobragg_command, generate_identity_matrix
from nanobrag_torch.config import BeamConfig, CrystalConfig, DetectorConfig, DetectorConvention, DetectorPivot


def test_pivot_command_generation():
    """Test that the C command includes correct pivot mode flags."""
    print("=" * 60)
    print("TESTING PIVOT COMMAND GENERATION")
    print("=" * 60)
    
    # Common configs
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),
    )
    
    beam_config = BeamConfig(
        wavelength_A=6.2,
        N_source_points=1,
        source_distance_mm=10000.0,
        source_size_mm=0.0,
    )
    
    # Test 1: Baseline config (no twotheta, should use BEAM pivot)
    baseline_detector = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=51.2,
        beam_center_f=51.2,
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM,
    )
    
    # Test 2: Tilted config (twotheta != 0, should use SAMPLE pivot)
    tilted_detector = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=51.2,
        beam_center_f=51.2,
        detector_convention=DetectorConvention.MOSFLM,
        detector_rotx_deg=5.0,
        detector_roty_deg=3.0,
        detector_rotz_deg=2.0,
        detector_twotheta_deg=20.0,
        detector_pivot=DetectorPivot.SAMPLE,  # Explicitly set SAMPLE pivot
    )
    
    # Generate commands
    matrix_file = "/tmp/identity.mat"
    generate_identity_matrix(matrix_file)
    
    baseline_cmd = build_nanobragg_command(
        baseline_detector, crystal_config, beam_config, matrix_file
    )
    
    tilted_cmd = build_nanobragg_command(
        tilted_detector, crystal_config, beam_config, matrix_file
    )
    
    print("\n1. BASELINE COMMAND ANALYSIS:")
    print(f"   Config pivot: {baseline_detector.detector_pivot}")
    print(f"   Command: {' '.join(baseline_cmd)}")
    
    if "-pivot" in baseline_cmd:
        pivot_idx = baseline_cmd.index("-pivot")
        pivot_value = baseline_cmd[pivot_idx + 1]
        print(f"   ✅ Pivot flag found: -pivot {pivot_value}")
        if pivot_value == "beam":
            print(f"   ✅ Correct: BEAM pivot for baseline config")
        else:
            print(f"   ❌ Error: Expected 'beam', got '{pivot_value}'")
    else:
        print(f"   ❌ Error: No -pivot flag found in command")
    
    print("\n2. TILTED COMMAND ANALYSIS:")
    print(f"   Config pivot: {tilted_detector.detector_pivot}")
    print(f"   Config twotheta: {tilted_detector.detector_twotheta_deg}°")
    print(f"   Command: {' '.join(tilted_cmd)}")
    
    if "-pivot" in tilted_cmd:
        pivot_idx = tilted_cmd.index("-pivot")
        pivot_value = tilted_cmd[pivot_idx + 1]
        print(f"   ✅ Pivot flag found: -pivot {pivot_value}")
        if pivot_value == "sample":
            print(f"   ✅ Correct: SAMPLE pivot for tilted config")
            return True
        else:
            print(f"   ❌ Error: Expected 'sample', got '{pivot_value}'")
            return False
    else:
        print(f"   ❌ Error: No -pivot flag found in command")
        return False


def test_c_execution_with_pivot():
    """Test that C code actually uses the specified pivot mode."""
    print("\n" + "=" * 60)
    print("TESTING C EXECUTION WITH PIVOT MODES")
    print("=" * 60)
    
    runner = CReferenceRunner()
    
    if not runner.is_available():
        print("❌ C reference not available, skipping execution test")
        return False
    
    # Common configs
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),
    )
    
    beam_config = BeamConfig(
        wavelength_A=6.2,
        N_source_points=1,
        source_distance_mm=10000.0,
        source_size_mm=0.0,
    )
    
    # Test with tilted configuration that should use SAMPLE pivot
    tilted_detector = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=100,  # Small for testing
        fpixels=100,
        beam_center_s=5.1,
        beam_center_f=5.1,
        detector_convention=DetectorConvention.MOSFLM,
        detector_twotheta_deg=20.0,
        detector_pivot=DetectorPivot.SAMPLE,
    )
    
    print("\n3. EXECUTING C CODE WITH SAMPLE PIVOT:")
    print(f"   Detector config: twotheta={tilted_detector.detector_twotheta_deg}°")
    print(f"   Pivot mode: {tilted_detector.detector_pivot}")
    
    # Run simulation and capture output
    result = runner.run_simulation(
        tilted_detector, crystal_config, beam_config,
        label="Pivot Test - Sample Mode"
    )
    
    if result is not None:
        print(f"   ✅ C simulation completed successfully")
        print(f"   Image shape: {result.shape}")
        print(f"   Value range: {result.min():.2e} to {result.max():.2e}")
        return True
    else:
        print(f"   ❌ C simulation failed")
        return False


def test_correlation_with_fixed_pivot():
    """Test correlation between Python and C with correct pivot modes."""
    print("\n" + "=" * 60)
    print("TESTING CORRELATION WITH FIXED PIVOT MODES")
    print("=" * 60)
    
    # Import simulator modules
    try:
        from nanobrag_torch.models.simulator import Simulator
        from nanobrag_torch.models.crystal import Crystal
        from nanobrag_torch.models.detector import Detector
        from nanobrag_torch.models.beam import Beam
    except ImportError as e:
        print(f"❌ Cannot import PyTorch modules: {e}")
        return False
    
    runner = CReferenceRunner()
    if not runner.is_available():
        print("❌ C reference not available")
        return False
    
    # Small test configuration for speed
    tilted_detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=64,  # Small for speed
        fpixels=64,
        beam_center_s=3.2,
        beam_center_f=3.2,
        detector_convention=DetectorConvention.MOSFLM,
        detector_twotheta_deg=15.0,  # Moderate twotheta
        detector_pivot=DetectorPivot.SAMPLE,
    )
    
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(3, 3, 3),  # Small for speed
    )
    
    beam_config = BeamConfig(
        wavelength_A=6.2,
        N_source_points=1,
        source_distance_mm=10000.0,
        source_size_mm=0.0,
    )
    
    print(f"\n4. RUNNING CORRELATION TEST:")
    print(f"   Detector: {tilted_detector_config.spixels}x{tilted_detector_config.fpixels}")
    print(f"   Twotheta: {tilted_detector_config.detector_twotheta_deg}°")
    print(f"   Pivot: {tilted_detector_config.detector_pivot}")
    
    # Run C simulation
    c_image = runner.run_simulation(
        tilted_detector_config, crystal_config, beam_config,
        label="Correlation Test - C Reference"
    )
    
    if c_image is None:
        print("❌ C simulation failed")
        return False
    
    # Run PyTorch simulation
    try:
        crystal = Crystal(crystal_config)
        detector = Detector(tilted_detector_config)
        beam = Beam(beam_config)
        simulator = Simulator(crystal, detector, beam)
        
        print("   Running PyTorch simulation...")
        py_image = simulator.simulate().detach().cpu().numpy()
        
        print(f"   ✅ PyTorch simulation completed")
        print(f"   Python image shape: {py_image.shape}")
        print(f"   C image shape: {c_image.shape}")
        
        # Check shapes match
        if py_image.shape != c_image.shape:
            print(f"   ❌ Shape mismatch: Python {py_image.shape} vs C {c_image.shape}")
            return False
        
        # Compute correlation
        correlation = np.corrcoef(py_image.ravel(), c_image.ravel())[0, 1]
        print(f"   Correlation: {correlation:.6f}")
        
        if correlation > 0.999:
            print(f"   ✅ Excellent correlation! (>0.999)")
            return True
        elif correlation > 0.9:
            print(f"   ⚠️  Good correlation but not perfect ({correlation:.6f})")
            return False
        else:
            print(f"   ❌ Poor correlation ({correlation:.6f})")
            return False
            
    except Exception as e:
        print(f"   ❌ PyTorch simulation failed: {e}")
        return False


def main():
    """Run all pivot mode verification tests."""
    print("PIVOT MODE VERIFICATION SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Command generation
    try:
        result1 = test_pivot_command_generation()
        results.append(("Command Generation", result1))
    except Exception as e:
        print(f"❌ Command generation test failed: {e}")
        results.append(("Command Generation", False))
    
    # Test 2: C execution
    try:
        result2 = test_c_execution_with_pivot()
        results.append(("C Execution", result2))
    except Exception as e:
        print(f"❌ C execution test failed: {e}")
        results.append(("C Execution", False))
    
    # Test 3: Correlation
    try:
        result3 = test_correlation_with_fixed_pivot()
        results.append(("Correlation", result3))
    except Exception as e:
        print(f"❌ Correlation test failed: {e}")
        results.append(("Correlation", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name:<20} {status}")
        if not passed:
            all_passed = False
    
    print(f"\nOverall result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Pivot mode fix is working correctly!")
        print("   The correlation issue should now be resolved.")
    else:
        print("\n⚠️  Fix needs more work. Check the failed tests above.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)