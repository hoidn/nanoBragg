#!/usr/bin/env python3
"""
Test remaining hypotheses after ruling out H1 (rotation centers)

Based on distance scaling results, we now focus on:
- H4: Missing Coordinate Transformation (most likely)
- H2: Beam Position Interpretation 
- H6: Integer vs Fractional Pixel indexing

This script tests these systematically.
"""

import os
import sys
import numpy as np
import torch
import json
from pathlib import Path
from datetime import datetime

# Set environment variable for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from nanobrag_torch.models.detector import Detector
from nanobrag_torch.config import DetectorConfig, DetectorPivot

def test_identity_configuration():
    """Test H4: Identity configuration should have minimal error"""
    print("\n" + "="*60)
    print("TESTING H4: Identity Configuration (No Rotations)")
    print("="*60)
    print("If there's a missing coordinate transformation, even identity")
    print("config might show systematic error.")
    
    # Identity configuration - no rotations at all
    config_identity = DetectorConfig(
        distance_mm=100.0,
        beam_center_s=51.2,
        beam_center_f=51.2,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        detector_rotx_deg=0.0,
        detector_roty_deg=0.0,
        detector_rotz_deg=0.0,
        detector_twotheta_deg=0.0,
        detector_pivot=DetectorPivot.BEAM,
        twotheta_axis=torch.tensor([0.0, 0.0, -1.0])
    )
    
    detector = Detector(config_identity)
    pix0_pytorch = detector.pix0_vector
    
    # Expected pix0 for identity config (analytical calculation)
    # For MOSFLM with beam center (51.2, 51.2):
    # pix0 should be [-Fbeam, -Sbeam, +distance] where Fbeam = Sbeam = (51.2 + 0.5) * 0.1mm
    expected_fbeam = (51.2 + 0.5) * 0.1e-3  # MOSFLM adds 0.5 pixel offset, convert to meters  
    expected_sbeam = (51.2 + 0.5) * 0.1e-3
    expected_distance = 100.0e-3  # convert to meters
    
    # Identity config should give: pix0 = [-Fbeam, -Sbeam, +distance]
    expected_pix0 = torch.tensor([-expected_fbeam, -expected_sbeam, expected_distance])
    
    error_vector = pix0_pytorch - expected_pix0
    error_magnitude_mm = torch.norm(error_vector).item() * 1000
    
    print(f"PyTorch pix0:  [{pix0_pytorch[0]:.6f}, {pix0_pytorch[1]:.6f}, {pix0_pytorch[2]:.6f}] m")
    print(f"Expected pix0: [{expected_pix0[0]:.6f}, {expected_pix0[1]:.6f}, {expected_pix0[2]:.6f}] m")
    print(f"Error vector:  [{error_vector[0]:.6f}, {error_vector[1]:.6f}, {error_vector[2]:.6f}] m")
    print(f"Error magnitude: {error_magnitude_mm:.2f}mm")
    
    if error_magnitude_mm < 0.1:
        print("✅ Identity config looks correct - error is in rotation logic")
        hypothesis_4_confirmed = False
    elif error_magnitude_mm > 10:
        print("🔴 Large error in identity config - fundamental coordinate issue")
        hypothesis_4_confirmed = True
    else:
        print("🟡 Moderate error in identity config - needs investigation")
        hypothesis_4_confirmed = False
        
    return {
        'pix0_pytorch': pix0_pytorch.detach().numpy().tolist(),
        'pix0_expected': expected_pix0.numpy().tolist(),
        'error_vector': error_vector.detach().numpy().tolist(),
        'error_magnitude_mm': error_magnitude_mm,
        'hypothesis_4_confirmed': hypothesis_4_confirmed
    }

def test_beam_center_variations():
    """Test H2: Beam center interpretation differences"""
    print("\n" + "="*60)  
    print("TESTING H2: Beam Center Interpretation")
    print("="*60)
    print("Testing if error varies with beam center position...")
    
    results = {}
    beam_centers = [
        (0.0, 0.0),      # Corner
        (25.6, 25.6),    # Quarter  
        (51.2, 51.2),    # Center (standard)
        (76.8, 76.8),    # Three-quarter
        (102.4, 102.4),  # Edge
    ]
    
    base_error = None
    
    for beam_s, beam_f in beam_centers:
        print(f"\nTesting beam center: ({beam_s}, {beam_f})")
        
        # Standard tilted configuration with varying beam center
        config = DetectorConfig(
            distance_mm=100.0,
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
            twotheta_axis=torch.tensor([0.0, 0.0, -1.0])
        )
        
        detector = Detector(config)
        pix0_tilted = detector.pix0_vector
        
        # Compare to baseline (no rotations) at same beam center
        config_baseline = DetectorConfig(
            distance_mm=100.0,
            beam_center_s=beam_s,
            beam_center_f=beam_f,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            detector_rotx_deg=0.0,
            detector_roty_deg=0.0,  
            detector_rotz_deg=0.0,
            detector_twotheta_deg=0.0,
            detector_pivot=DetectorPivot.BEAM,
            twotheta_axis=torch.tensor([0.0, 0.0, -1.0])
        )
        
        detector_baseline = Detector(config_baseline)
        pix0_baseline = detector_baseline.pix0_vector
        
        # Calculate rotation effect
        rotation_effect = pix0_tilted - pix0_baseline
        error_magnitude_mm = torch.norm(rotation_effect).item() * 1000
        
        print(f"  Rotation effect magnitude: {error_magnitude_mm:.2f}mm")
        
        if base_error is None:
            base_error = error_magnitude_mm
            
        results[f"{beam_s}_{beam_f}"] = {
            'beam_center': [beam_s, beam_f],
            'pix0_tilted': pix0_tilted.detach().numpy().tolist(),
            'pix0_baseline': pix0_baseline.detach().numpy().tolist(),
            'rotation_effect': rotation_effect.detach().numpy().tolist(),
            'error_magnitude_mm': error_magnitude_mm
        }
    
    # Analyze variation in error across beam centers
    error_magnitudes = [r['error_magnitude_mm'] for r in results.values()]
    error_std = np.std(error_magnitudes)
    error_mean = np.mean(error_magnitudes)
    
    print(f"\nError statistics across beam centers:")
    print(f"  Mean error: {error_mean:.2f}mm")
    print(f"  Std dev:    {error_std:.2f}mm")
    print(f"  Range:      {min(error_magnitudes):.2f} - {max(error_magnitudes):.2f}mm")
    
    if error_std < 0.5:
        print("✅ Error is consistent across beam centers - NOT a beam center issue")
        hypothesis_2_confirmed = False
    else:
        print("🔴 Error varies with beam center - beam center interpretation issue")
        hypothesis_2_confirmed = True
        
    return {
        'results': results,
        'error_statistics': {
            'mean': error_mean,
            'std': error_std,
            'min': min(error_magnitudes),
            'max': max(error_magnitudes)
        },
        'hypothesis_2_confirmed': hypothesis_2_confirmed
    }

def test_individual_rotations():
    """Test H4: Individual rotation axes to isolate the error"""
    print("\n" + "="*60)
    print("TESTING H4: Individual Rotation Axes")
    print("="*60)
    print("Testing each rotation axis individually to isolate the error...")
    
    results = {}
    rotation_tests = [
        ("rotx_only", 5.0, 0.0, 0.0, 0.0),
        ("roty_only", 0.0, 3.0, 0.0, 0.0),
        ("rotz_only", 0.0, 0.0, 2.0, 0.0),
        ("twotheta_only", 0.0, 0.0, 0.0, 15.0),
        ("all_rotations", 5.0, 3.0, 2.0, 15.0),
    ]
    
    for test_name, rotx, roty, rotz, twotheta in rotation_tests:
        print(f"\nTesting {test_name}: rotx={rotx}°, roty={roty}°, rotz={rotz}°, twotheta={twotheta}°")
        
        config = DetectorConfig(
            distance_mm=100.0,
            beam_center_s=51.2,
            beam_center_f=51.2,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            detector_rotx_deg=rotx,
            detector_roty_deg=roty,
            detector_rotz_deg=rotz,
            detector_twotheta_deg=twotheta,
            detector_pivot=DetectorPivot.BEAM,
            twotheta_axis=torch.tensor([0.0, 0.0, -1.0])
        )
        
        detector = Detector(config)
        pix0_rotated = detector.pix0_vector
        
        # Compare to identity
        config_identity = DetectorConfig(
            distance_mm=100.0,
            beam_center_s=51.2,
            beam_center_f=51.2,
            pixel_size_mm=0.1,
            spixels=1024,
            fpixels=1024,
            detector_rotx_deg=0.0,
            detector_roty_deg=0.0,
            detector_rotz_deg=0.0,
            detector_twotheta_deg=0.0,
            detector_pivot=DetectorPivot.BEAM,
            twotheta_axis=torch.tensor([0.0, 0.0, -1.0])
        )
        
        detector_identity = Detector(config_identity)
        pix0_identity = detector_identity.pix0_vector
        
        rotation_effect = pix0_rotated - pix0_identity
        error_magnitude_mm = torch.norm(rotation_effect).item() * 1000
        
        print(f"  Error magnitude: {error_magnitude_mm:.2f}mm")
        print(f"  Error vector: [{rotation_effect[0]*1000:.2f}, {rotation_effect[1]*1000:.2f}, {rotation_effect[2]*1000:.2f}] mm")
        
        results[test_name] = {
            'rotations': [rotx, roty, rotz, twotheta],
            'pix0_rotated': pix0_rotated.detach().numpy().tolist(),
            'pix0_identity': pix0_identity.detach().numpy().tolist(),
            'rotation_effect': rotation_effect.detach().numpy().tolist(),
            'error_magnitude_mm': error_magnitude_mm
        }
    
    # Analyze which rotations contribute most to error
    individual_errors = {
        'rotx': results['rotx_only']['error_magnitude_mm'],
        'roty': results['roty_only']['error_magnitude_mm'], 
        'rotz': results['rotz_only']['error_magnitude_mm'],
        'twotheta': results['twotheta_only']['error_magnitude_mm'],
    }
    
    max_contributor = max(individual_errors, key=individual_errors.get)
    max_error = individual_errors[max_contributor]
    
    print(f"\nLargest individual contributor: {max_contributor} ({max_error:.2f}mm)")
    print(f"All rotations combined: {results['all_rotations']['error_magnitude_mm']:.2f}mm")
    
    return {
        'results': results,
        'individual_errors': individual_errors,
        'max_contributor': max_contributor,
        'max_error': max_error
    }

def main():
    """Run remaining hypothesis tests"""
    print("TESTING REMAINING HYPOTHESES FOR 28MM OFFSET")
    print("="*60)
    print("H1 (rotation centers) has been RULED OUT by distance scaling test.")
    print("Now testing H4, H2, and rotation isolation...")
    
    output_dir = Path("remaining_hypotheses_results")
    output_dir.mkdir(exist_ok=True)
    
    all_results = {
        'timestamp': datetime.now().isoformat(),
        'summary': 'Testing remaining hypotheses after ruling out H1'
    }
    
    # Test identity configuration
    print("\n" + "🔍 PHASE 1: Identity Configuration Test")
    try:
        identity_results = test_identity_configuration()
        all_results['identity_test'] = identity_results
    except Exception as e:
        print(f"Error in identity test: {e}")
        all_results['identity_test'] = {'error': str(e)}
    
    # Test beam center variations
    print("\n" + "🔍 PHASE 2: Beam Center Variation Test")
    try:
        beam_center_results = test_beam_center_variations()
        all_results['beam_center_test'] = beam_center_results
    except Exception as e:
        print(f"Error in beam center test: {e}")
        all_results['beam_center_test'] = {'error': str(e)}
    
    # Test individual rotations
    print("\n" + "🔍 PHASE 3: Individual Rotation Test")
    try:
        rotation_results = test_individual_rotations()
        all_results['rotation_test'] = rotation_results
    except Exception as e:
        print(f"Error in rotation test: {e}")
        all_results['rotation_test'] = {'error': str(e)}
    
    # Save results
    results_file = output_dir / "remaining_hypotheses_results.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=lambda x: float(x) if hasattr(x, 'item') else x)
    
    # Final analysis
    print("\n" + "="*60)
    print("FINAL DIAGNOSIS")
    print("="*60)
    
    if 'identity_test' in all_results:
        identity_error = all_results['identity_test'].get('error_magnitude_mm', 0)
        if identity_error > 10:
            print("🔴 MAJOR FINDING: Large error in identity configuration!")
            print("   This indicates a fundamental coordinate system issue (H4)")
        elif identity_error < 0.1:
            print("✅ Identity config is accurate - rotation logic is the problem")
        else:
            print("🟡 Moderate identity error - needs deeper investigation")
    
    if 'beam_center_test' in all_results:
        beam_confirmed = all_results['beam_center_test'].get('hypothesis_2_confirmed', False)
        if beam_confirmed:
            print("🔴 BEAM CENTER ISSUE CONFIRMED: Error varies with beam position")
        else:
            print("✅ Beam center interpretation appears consistent")
    
    if 'rotation_test' in all_results:
        max_contributor = all_results['rotation_test'].get('max_contributor', 'unknown')
        max_error = all_results['rotation_test'].get('max_error', 0)
        print(f"📊 Largest rotation contributor: {max_contributor} ({max_error:.2f}mm)")
    
    print(f"\n📊 Results saved to: {results_file}")
    print("\n🎯 Next steps: Focus debugging on the identified problematic rotation axis/transformation")

if __name__ == "__main__":
    main()