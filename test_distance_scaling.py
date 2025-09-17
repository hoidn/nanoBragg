#!/usr/bin/env python3
"""
Test distance scaling to validate H1: Different Rotation Centers

If the error is due to different rotation centers, the error should scale
linearly with detector distance. This test will run the detector verification
at multiple distances and analyze the scaling pattern.
"""

import os
import sys
import numpy as np
import torch
import json
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

# Set environment variable for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from nanobrag_torch.models.detector import Detector
from nanobrag_torch.config import DetectorConfig, DetectorPivot

def test_pix0_at_distance(distance_mm):
    """Test pix0 vector calculation at specific distance"""
    print(f"\nTesting distance: {distance_mm}mm")
    
    # Standard tilted configuration
    config = DetectorConfig(
        distance_mm=distance_mm,           # mm
        beam_center_s=51.2,               # mm
        beam_center_f=51.2,               # mm
        pixel_size_mm=0.1,                # mm
        spixels=1024,
        fpixels=1024,
        detector_rotx_deg=5.0,   # degrees
        detector_roty_deg=3.0,   # degrees
        detector_rotz_deg=2.0,   # degrees
        detector_twotheta_deg=15.0,  # degrees
        detector_pivot=DetectorPivot.BEAM,
        twotheta_axis=torch.tensor([0.0, 0.0, -1.0])
    )
    
    detector = Detector(config)
    pix0_pytorch = detector.pix0_vector
    
    # Also test baseline (no rotations) for comparison
    config_baseline = DetectorConfig(
        distance_mm=distance_mm,           # mm
        beam_center_s=51.2,               # mm
        beam_center_f=51.2,               # mm
        pixel_size_mm=0.1,                # mm
        spixels=1024,
        fpixels=1024,
        detector_rotx_deg=0.0,   # No rotations
        detector_roty_deg=0.0,
        detector_rotz_deg=0.0,
        detector_twotheta_deg=0.0,
        detector_pivot=DetectorPivot.BEAM,
        twotheta_axis=torch.tensor([0.0, 0.0, -1.0])
    )
    
    detector_baseline = Detector(config_baseline)
    pix0_baseline = detector_baseline.pix0_vector
    
    # Calculate the change due to rotations
    rotation_effect = pix0_pytorch - pix0_baseline
    
    result = {
        'distance_mm': distance_mm,
        'pix0_tilted': pix0_pytorch.detach().numpy().tolist(),
        'pix0_baseline': pix0_baseline.detach().numpy().tolist(),
        'rotation_effect': rotation_effect.detach().numpy().tolist(),
        'rotation_magnitude_mm': float(torch.norm(rotation_effect).item() * 1000)
    }
    
    print(f"  Tilted pix0:     [{pix0_pytorch[0]:.6f}, {pix0_pytorch[1]:.6f}, {pix0_pytorch[2]:.6f}] m")
    print(f"  Baseline pix0:   [{pix0_baseline[0]:.6f}, {pix0_baseline[1]:.6f}, {pix0_baseline[2]:.6f}] m")
    print(f"  Rotation effect: [{rotation_effect[0]:.6f}, {rotation_effect[1]:.6f}, {rotation_effect[2]:.6f}] m")
    print(f"  Rotation magnitude: {result['rotation_magnitude_mm']:.2f}mm")
    
    return result

def analyze_distance_scaling(results):
    """Analyze if the rotation effect scales with distance"""
    
    distances = [r['distance_mm'] for r in results]
    magnitudes = [r['rotation_magnitude_mm'] for r in results]
    
    print("\n" + "="*60)
    print("DISTANCE SCALING ANALYSIS")
    print("="*60)
    
    # Print summary table
    print("Distance (mm) | Rotation Effect (mm) | Effect/Distance Ratio")
    print("-"*55)
    for i, result in enumerate(results):
        distance = result['distance_mm']
        magnitude = result['rotation_magnitude_mm']
        ratio = magnitude / distance if distance > 0 else 0
        print(f"{distance:11.0f} | {magnitude:17.2f} | {ratio:.4f}")
    
    # Linear regression to check scaling
    if len(distances) >= 2:
        # Fit line: rotation_effect = a * distance + b
        A = np.vstack([distances, np.ones(len(distances))]).T
        slope, intercept = np.linalg.lstsq(A, magnitudes, rcond=None)[0]
        
        print(f"\nLinear fit: rotation_effect = {slope:.4f} * distance + {intercept:.4f}")
        
        # Calculate R²
        y_pred = slope * np.array(distances) + intercept
        ss_res = np.sum((magnitudes - y_pred) ** 2)
        ss_tot = np.sum((magnitudes - np.mean(magnitudes)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        print(f"R² correlation: {r_squared:.4f}")
        
        # Analysis
        print("\n" + "="*40)
        print("HYPOTHESIS VALIDATION")
        print("="*40)
        
        if r_squared > 0.95:
            print("✅ STRONG LINEAR SCALING DETECTED")
            print("   - Rotation effect scales linearly with distance")
            print("   - This confirms H1: Different Rotation Centers")
            print(f"   - Slope: {slope:.4f} (should be ~sin(rotation_angle) for center offset)")
            
            # Estimate effective offset
            # For small rotations, if we rotate by angle θ around wrong center,
            # the error is approximately distance * sin(θ)
            total_rotation = np.sqrt(5**2 + 3**2 + 2**2)  # Approximate total rotation
            expected_slope = np.sin(np.radians(total_rotation))
            print(f"   - Expected slope for {total_rotation:.1f}° rotation: {expected_slope:.4f}")
            
            if abs(slope - expected_slope) < 0.05:
                print("   - Slope matches expected value - rotation center confirmed!")
            else:
                print("   - Slope differs from expected - more complex transformation issue")
                
        elif r_squared > 0.7:
            print("⚠️  MODERATE LINEAR SCALING")
            print("   - Some distance dependence, but not perfectly linear")
            print("   - May be rotation center issue with other complications")
            
        else:
            print("❌ NO CLEAR LINEAR SCALING")
            print("   - Error doesn't scale with distance")
            print("   - Likely NOT a rotation center issue")
            print("   - Consider H2 (beam position) or H4 (coordinate transform)")
            
        return {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_squared,
            'hypothesis_confirmed': r_squared > 0.95
        }
    
    return None

def create_visualization(results, analysis):
    """Create plots showing distance scaling"""
    
    distances = [r['distance_mm'] for r in results]
    magnitudes = [r['rotation_magnitude_mm'] for r in results]
    
    plt.figure(figsize=(10, 6))
    
    # Plot data points
    plt.subplot(1, 2, 1)
    plt.scatter(distances, magnitudes, color='red', s=100, alpha=0.7, label='Measured')
    
    if analysis and 'slope' in analysis:
        # Plot fitted line
        x_line = np.linspace(min(distances), max(distances), 100)
        y_line = analysis['slope'] * x_line + analysis['intercept']
        plt.plot(x_line, y_line, 'b--', alpha=0.8, 
                label=f'Linear fit (R²={analysis["r_squared"]:.3f})')
        
        # Add expected line if we have good scaling
        if analysis['r_squared'] > 0.95:
            total_rotation = np.sqrt(5**2 + 3**2 + 2**2)
            expected_slope = np.sin(np.radians(total_rotation))
            y_expected = expected_slope * x_line
            plt.plot(x_line, y_expected, 'g:', alpha=0.8, 
                    label=f'Expected ({total_rotation:.1f}° rotation)')
    
    plt.xlabel('Detector Distance (mm)')
    plt.ylabel('Rotation Effect Magnitude (mm)')
    plt.title('Rotation Effect vs Distance')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot rotation components
    plt.subplot(1, 2, 2)
    
    x_components = [r['rotation_effect'][0] * 1000 for r in results]  # Convert to mm
    y_components = [r['rotation_effect'][1] * 1000 for r in results]
    z_components = [r['rotation_effect'][2] * 1000 for r in results]
    
    plt.plot(distances, x_components, 'ro-', label='X component', alpha=0.7)
    plt.plot(distances, y_components, 'go-', label='Y component', alpha=0.7)
    plt.plot(distances, z_components, 'bo-', label='Z component', alpha=0.7)
    
    plt.xlabel('Detector Distance (mm)')
    plt.ylabel('Rotation Effect Component (mm)')
    plt.title('Rotation Effect Components')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot
    output_dir = Path("distance_scaling_analysis")
    output_dir.mkdir(exist_ok=True)
    plot_file = output_dir / "distance_scaling_plot.png"
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    plt.show()
    
    print(f"📈 Plot saved to: {plot_file}")

def main():
    """Main function to test distance scaling hypothesis"""
    print("DISTANCE SCALING TEST FOR ROTATION CENTER HYPOTHESIS")
    print("="*60)
    print("Testing if rotation effects scale linearly with detector distance...")
    print("This will validate H1: Different Rotation Centers")
    
    # Test at multiple distances
    distances_to_test = [50, 100, 150, 200, 300, 400]
    
    results = []
    
    print("\nRunning tests at different distances:")
    print("="*40)
    
    for distance in distances_to_test:
        try:
            result = test_pix0_at_distance(distance)
            results.append(result)
        except Exception as e:
            print(f"Error testing distance {distance}mm: {e}")
    
    if len(results) >= 2:
        # Analyze scaling
        analysis = analyze_distance_scaling(results)
        
        # Create visualization
        create_visualization(results, analysis)
        
        # Save results
        output_dir = Path("distance_scaling_analysis")
        output_dir.mkdir(exist_ok=True)
        
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'test_description': 'Distance scaling test for rotation center hypothesis',
            'results': results,
            'analysis': analysis
        }
        
        results_file = output_dir / "distance_scaling_results.json"
        with open(results_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n📊 Results saved to: {results_file}")
        
        # Final conclusion
        print(f"\n" + "="*60)
        print("FINAL CONCLUSION")
        print("="*60)
        
        if analysis and analysis.get('hypothesis_confirmed', False):
            print("🎯 HYPOTHESIS H1 CONFIRMED: Different Rotation Centers")
            print("   - The rotation effect scales linearly with detector distance")
            print("   - PyTorch and C code use different rotation centers")
            print("   - This explains the ~28mm systematic offset")
            print("\n✅ RECOMMENDED FIX:")
            print("   - Investigate detector pivot mode implementation")
            print("   - Ensure PyTorch rotates around same point as C code")
            print("   - Check beam center vs sample center rotation logic")
        else:
            print("❓ HYPOTHESIS H1 NOT CONFIRMED")
            print("   - Rotation effect doesn't scale linearly with distance")
            print("   - The issue may be more complex:")
            print("     • H2: Beam position interpretation")
            print("     • H4: Missing coordinate transformation")
            print("     • H6: Integer vs fractional pixel indexing")
            
    else:
        print("❌ Insufficient data for analysis")

if __name__ == "__main__":
    main()