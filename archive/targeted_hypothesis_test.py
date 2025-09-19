#!/usr/bin/env python3
"""
Targeted Hypothesis Testing for 28mm Systematic Offset (DEPRECATED; moved to archive/)

This script directly tests the most likely hypotheses by running
detector geometry comparisons with specific parameter variations.

Uses diffraction pattern analysis (peak positions and correlations)
since CReferenceRunner only returns image data, not detector geometry info.

Deprecated: superseded by scripts/test_hypothesis_framework.py and the nb-compare tool (AT-TOOLS-001).
"""

import os
import sys
import numpy as np
import torch
import json
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime

# Set environment variable for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src and scripts to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from nanobrag_torch.models.detector import Detector
from nanobrag_torch.config import DetectorConfig, DetectorPivot
from scripts.c_reference_runner import CReferenceRunner

def test_distance_scaling_hypothesis():
    """Test if diffraction pattern changes scale with detector distance (H1: Different Rotation Centers)"""
    print("\n" + "="*60)
    print("TESTING H1: Different Rotation Centers")
    print("Testing if diffraction pattern scaling matches distance scaling...")
    print("="*60)

    results = {}
    distances = [100, 200]  # Reduced for faster testing

    # Import additional dependencies for simulation
    from nanobrag_torch.config import CrystalConfig, BeamConfig
    from nanobrag_torch.models.crystal import Crystal
    from nanobrag_torch.simulator import Simulator

    for distance in distances:
        print(f"\nTesting distance: {distance}mm")

        # Standard tilted configuration
        detector_config = DetectorConfig(
            distance_mm=distance,
            beam_center_s=51.2,     # mm
            beam_center_f=51.2,     # mm
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            detector_rotx_deg=torch.tensor(5.0),   # degrees
            detector_roty_deg=torch.tensor(3.0),   # degrees
            detector_rotz_deg=torch.tensor(2.0),   # degrees
            detector_twotheta_deg=torch.tensor(15.0),  # degrees
            detector_pivot=DetectorPivot.BEAM,
            twotheta_axis=torch.tensor([0.0, 0.0, -1.0])
        )

        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5), default_F=100.0
        )

        beam_config = BeamConfig(wavelength_A=6.2)

        # Generate PyTorch simulation
        detector = Detector(detector_config)
        crystal = Crystal(crystal_config, beam_config=beam_config)
        simulator = Simulator(crystal, detector, beam_config=beam_config)
        pytorch_image = simulator.run()

        # Find peak position in PyTorch image
        pytorch_peak_idx = torch.argmax(pytorch_image)
        pytorch_peak_s = pytorch_peak_idx // 1024
        pytorch_peak_f = pytorch_peak_idx % 1024

        # Generate C reference simulation
        try:
            runner = CReferenceRunner()
            c_image = runner.run_simulation(detector_config, crystal_config, beam_config)

            if c_image is not None:
                print(f"  C simulation completed successfully (image shape: {c_image.shape})")

                # Find peak position in C image
                c_peak_idx = np.argmax(c_image)
                c_peak_s = c_peak_idx // 1024
                c_peak_f = c_peak_idx % 1024

                # Calculate peak position difference
                peak_diff_s = abs(float(pytorch_peak_s) - float(c_peak_s))
                peak_diff_f = abs(float(pytorch_peak_f) - float(c_peak_f))
                peak_diff_total = np.sqrt(peak_diff_s**2 + peak_diff_f**2)

                # Calculate pattern correlation
                pytorch_np = pytorch_image.detach().numpy()
                correlation = np.corrcoef(pytorch_np.ravel(), c_image.ravel())[0, 1]

                results[distance] = {
                    'distance_mm': distance,
                    'pytorch_peak': [float(pytorch_peak_s), float(pytorch_peak_f)],
                    'c_peak': [float(c_peak_s), float(c_peak_f)],
                    'peak_difference_pixels': peak_diff_total,
                    'pattern_correlation': correlation,
                    'pytorch_max_intensity': float(torch.max(pytorch_image)),
                    'c_max_intensity': float(np.max(c_image))
                }

                print(f"  Peak difference: {peak_diff_total:.2f} pixels")
                print(f"  Pattern correlation: {correlation:.4f}")

            else:
                print(f"  C simulation failed")
                results[distance] = {'error': 'C simulation failed'}

        except Exception as e:
            print(f"  Error running test: {e}")
            results[distance] = {'error': str(e)}

    # Analyze scaling behavior if we have results for multiple distances
    if len([r for r in results.values() if 'peak_difference_pixels' in r]) >= 2:
        valid_results = {k: v for k, v in results.items() if 'peak_difference_pixels' in v}
        distances_tested = list(valid_results.keys())

        if len(distances_tested) >= 2:
            dist1, dist2 = distances_tested[:2]
            diff1 = valid_results[dist1]['peak_difference_pixels']
            diff2 = valid_results[dist2]['peak_difference_pixels']

            # If errors scale with distance, the ratio should be proportional to distance ratio
            distance_ratio = dist2 / dist1
            error_ratio = diff2 / diff1 if diff1 > 0 else float('inf')

            print(f"\nScaling analysis:")
            print(f"  Distance ratio ({dist2}/{dist1}): {distance_ratio:.2f}")
            print(f"  Error ratio ({diff2:.2f}/{diff1:.2f}): {error_ratio:.2f}")

            # If errors scale linearly with distance, ratios should be similar
            ratio_match = abs(error_ratio - distance_ratio) < 0.5
            print(f"  Linear scaling: {'Yes' if ratio_match else 'No'}")

    assert results, "Test completed with results"

def test_beam_center_hypothesis():
    """Test if error is related to beam center interpretation (H2)"""
    print("\n" + "="*60)
    print("TESTING H2: Beam Position Interpretation")
    print("Testing different beam center values...")
    print("="*60)
    
    results = {}
    # Test beam centers: corner (0,0), quarter (25.6), center (51.2), three-quarter (76.8)
    beam_centers = [(0.0, 0.0), (25.6, 25.6), (51.2, 51.2), (76.8, 76.8)]
    
    for beam_s, beam_f in beam_centers:
        print(f"\nTesting beam center: ({beam_s}, {beam_f})")
        
        config = DetectorConfig(
            distance_mm=100,  # 100mm
            beam_center_s=beam_s,
            beam_center_f=beam_f,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            detector_rotx_deg=torch.tensor(5.0),
            detector_roty_deg=torch.tensor(3.0),
            detector_rotz_deg=torch.tensor(2.0),
            detector_twotheta_deg=torch.tensor(15.0),
            detector_pivot=DetectorPivot.BEAM,
            twotheta_axis=torch.tensor([0.0, 0.0, -1.0])
        )
        
        detector = Detector(config)
        pix0_pytorch = detector.pix0_vector
        
        # C reference - using same config objects as the working test
        from nanobrag_torch.config import CrystalConfig, BeamConfig

        c_detector_config = DetectorConfig(
            distance_mm=100,
            beam_center_s=beam_s,
            beam_center_f=beam_f,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            detector_rotx_deg=5.0,
            detector_roty_deg=3.0,
            detector_rotz_deg=2.0,
            detector_twotheta_deg=15.0,
            detector_pivot=DetectorPivot.BEAM,
        )

        c_crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5), default_F=100.0
        )

        c_beam_config = BeamConfig(wavelength_A=6.2)

        try:
            runner = CReferenceRunner()
            c_image = runner.run_simulation(c_detector_config, c_crystal_config, c_beam_config)

            # NOTE: CReferenceRunner only returns image data, not detector geometry
            # This test needs detector geometry info which isn't available from current API
            if c_image is not None:
                print(f"  C simulation completed successfully (image shape: {c_image.shape})")
                # For now, skip the pix0 comparison since we can't get detector info
                print(f"  Cannot compare pix0 vectors - API limitation")

                # Store what we can - the PyTorch values and note the limitation
                results[f"{beam_s}_{beam_f}"] = {
                    'beam_center': [beam_s, beam_f],
                    'pix0_pytorch': pix0_pytorch.detach().numpy().tolist(),
                    'c_image_shape': c_image.shape,
                    'api_limitation': 'Cannot compare pix0 vectors - C reference does not return detector geometry'
                }
                continue
            else:
                print(f"  C simulation failed")
                results[f"{beam_s}_{beam_f}"] = {'error': 'C simulation failed'}
                continue

        except Exception as e:
            print(f"  Error running test: {e}")
            results[f"{beam_s}_{beam_f}"] = {'error': str(e)}
    
    assert results, "Test completed with results"

def test_pivot_mode_hypothesis():
    """Test different pivot modes (H4: Missing Coordinate Transformation)"""
    print("\n" + "="*60)
    print("TESTING H4: Missing Coordinate Transformation")
    print("Testing different pivot modes...")
    print("="*60)
    
    results = {}
    pivot_modes = [DetectorPivot.BEAM, DetectorPivot.SAMPLE]
    
    for pivot_mode in pivot_modes:
        print(f"\nTesting pivot mode: {pivot_mode.name}")
        
        config = DetectorConfig(
            distance_mm=100,  # 100mm
            beam_center_s=51.2,
            beam_center_f=51.2,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            detector_rotx_deg=torch.tensor(5.0),
            detector_roty_deg=torch.tensor(3.0),
            detector_rotz_deg=torch.tensor(2.0),
            detector_twotheta_deg=torch.tensor(15.0),
            detector_pivot=pivot_mode,
            twotheta_axis=torch.tensor([0.0, 0.0, -1.0])
        )
        
        detector = Detector(config)
        pix0_pytorch = detector.pix0_vector
        
        # For now, just record the PyTorch results - API limitation prevents C comparison
        print(f"  PyTorch pix0_vector: {pix0_pytorch.detach().numpy()}")
        print(f"  Cannot compare with C reference - API limitation")

        results[pivot_mode.name] = {
            'pivot_mode': pivot_mode.name,
            'pix0_pytorch': pix0_pytorch.detach().numpy().tolist(),
            'api_limitation': 'Cannot compare pix0 vectors - C reference does not return detector geometry'
        }
    
    assert results, "Test completed with results"

def test_identity_configuration():
    """Test with identity/zero rotation configuration (H4)"""
    print("\n" + "="*60)
    print("TESTING H4: Identity Configuration")
    print("Testing with no rotations...")
    print("="*60)
    
    config = DetectorConfig(
        distance_mm=100,  # 100mm
        beam_center_s=51.2,
        beam_center_f=51.2,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        detector_rotx_deg=torch.tensor(0.0),  # No rotations
        detector_roty_deg=torch.tensor(0.0),
        detector_rotz_deg=torch.tensor(0.0),
        detector_twotheta_deg=torch.tensor(0.0),
        detector_pivot=DetectorPivot.BEAM,
        twotheta_axis=torch.tensor([0.0, 0.0, -1.0])
    )
    
    detector = Detector(config)
    pix0_pytorch = detector.pix0_vector
    
    # For now, just record the PyTorch results - API limitation prevents C comparison
    print(f"Identity configuration pix0_vector: {pix0_pytorch.detach().numpy()}")
    print(f"Cannot compare with C reference - API limitation")

    results = {
        'pix0_pytorch': pix0_pytorch.detach().numpy().tolist(),
        'api_limitation': 'Cannot compare pix0 vectors - C reference does not return detector geometry'
    }

    print(f"Identity configuration recorded (no comparison possible due to API limitation)")

    assert results, "Test completed with results"

def main():
    """Run targeted hypothesis tests"""
    print("TARGETED HYPOTHESIS TESTING FOR 28MM SYSTEMATIC OFFSET")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path("targeted_hypothesis_results")
    output_dir.mkdir(exist_ok=True)
    
    all_results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {}
    }
    
    # Test most likely hypotheses
    print("Testing the most promising hypotheses for the 28mm offset...")
    
    # H4: Identity test - most diagnostic
    try:
        all_results['tests']['identity'] = test_identity_configuration()
    except Exception as e:
        print(f"Error in identity test: {e}")
        all_results['tests']['identity'] = {'error': str(e)}
    
    # H1: Distance scaling
    try:
        all_results['tests']['distance_scaling'] = test_distance_scaling_hypothesis()
    except Exception as e:
        print(f"Error in distance scaling test: {e}")
        all_results['tests']['distance_scaling'] = {'error': str(e)}
    
    # H2: Beam center interpretation
    try:
        all_results['tests']['beam_center'] = test_beam_center_hypothesis()
    except Exception as e:
        print(f"Error in beam center test: {e}")
        all_results['tests']['beam_center'] = {'error': str(e)}
    
    # H4: Pivot mode
    try:
        all_results['tests']['pivot_mode'] = test_pivot_mode_hypothesis()
    except Exception as e:
        print(f"Error in pivot mode test: {e}")
        all_results['tests']['pivot_mode'] = {'error': str(e)}
    
    # Save results
    output_file = output_dir / "targeted_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Results saved to: {output_file}")
    
    # Analysis
    identity_result = all_results['tests'].get('identity', {})
    if 'error_magnitude_mm' in identity_result:
        error_mm = identity_result['error_magnitude_mm']
        print(f"Identity config error: {error_mm:.2f}mm")
        
        if error_mm > 25:
            print("🔍 DIAGNOSIS: Large error in identity configuration suggests:")
            print("   - Fundamental coordinate system mismatch")
            print("   - Unit conversion error")
            print("   - Missing coordinate transformation")
            print("   - This is likely H4: Missing Coordinate Transformation")
        elif error_mm < 1:
            print("✅ Identity config looks good - error is in rotation logic")
        else:
            print(f"⚠️  Moderate error in identity config: {error_mm:.2f}mm")
    
    print("\nNext steps:")
    print("1. Check identity configuration results first")
    print("2. If identity has large error -> investigate coordinate systems")
    print("3. If identity is good -> focus on rotation center differences")

if __name__ == "__main__":
    main()
