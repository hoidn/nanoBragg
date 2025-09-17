#!/usr/bin/env python3
"""
Simple correlation test to identify the 28mm offset issue

This script runs the existing verify_detector_geometry script and extracts
the correlation values to analyze the detector geometry mismatch.
"""

import os
import json
import subprocess
from pathlib import Path

# Set environment variable for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

def run_verification_and_extract_correlation():
    """Run detector verification and extract correlation metrics"""
    print("Running detector geometry verification...")
    
    try:
        # Run the verification script
        result = subprocess.run(
            ["python", "scripts/verify_detector_geometry.py"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent)
        )
        
        if result.returncode != 0:
            print(f"Verification script failed with return code {result.returncode}")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return None
        
        # Check if correlation metrics file was created
        metrics_file = Path("reports/detector_verification/correlation_metrics.json")
        if metrics_file.exists():
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
            
            print("✅ Successfully extracted correlation metrics")
            return metrics
        else:
            print("❌ No correlation metrics file found")
            print("Script output:", result.stdout[-500:])  # Last 500 chars
            return None
            
    except Exception as e:
        print(f"Error running verification: {e}")
        return None

def analyze_correlation_issue(metrics):
    """Analyze the correlation results to identify the issue"""
    if not metrics:
        print("No metrics to analyze")
        return
    
    print("\n" + "="*60)
    print("CORRELATION ANALYSIS")
    print("="*60)
    
    # Extract key metrics
    baseline_correlation = metrics.get('baseline', {}).get('correlation', 0)
    tilted_correlation = metrics.get('tilted', {}).get('correlation', 0)
    
    print(f"Baseline correlation: {baseline_correlation:.6f}")
    print(f"Tilted correlation:   {tilted_correlation:.6f}")
    
    correlation_drop = baseline_correlation - tilted_correlation
    print(f"Correlation drop:     {correlation_drop:.6f}")
    
    # Check if we have spot shift data
    if 'spot_shifts' in metrics:
        shifts = metrics['spot_shifts']
        print(f"\nSpot position shifts:")
        for i, shift in enumerate(shifts[:3], 1):  # First 3 spots
            delta_s = shift.get('delta_s', 0)
            delta_f = shift.get('delta_f', 0)
            magnitude = shift.get('magnitude', 0)
            print(f"  Spot {i}: Δs={delta_s:+3.0f}, Δf={delta_f:+3.0f}, |Δ|={magnitude:.1f} pixels")
    
    # Diagnostic analysis
    print(f"\n" + "="*40)
    print("DIAGNOSTIC ANALYSIS")
    print("="*40)
    
    if baseline_correlation > 0.99:
        print("✅ Baseline (no rotations) looks excellent")
        print("   - Coordinate system basics are correct")
        print("   - Unit conversions are working")
    else:
        print("⚠️  Baseline correlation is sub-optimal")
        print("   - May indicate fundamental coordinate issue")
    
    if tilted_correlation < 0.5:
        print("❌ Tilted configuration has severe mismatch")
        print("   - Large systematic error in rotation logic")
        print("   - Likely ~28mm offset due to:")
        
        if correlation_drop > 0.6:
            print("     HYPOTHESIS: Different rotation centers (H1)")
            print("     - C code rotates around beam center")
            print("     - PyTorch may rotate around sample/detector center")
            print("     - Error scales with detector distance and rotation angle")
            
    elif tilted_correlation < 0.9:
        print("⚠️  Tilted configuration has moderate mismatch")
        print("   - Rotation logic partially working")
        print("   - May be unit conversion or sign error")
    else:
        print("✅ Tilted configuration looks good")
    
    # Specific recommendations
    print(f"\n" + "="*40)
    print("RECOMMENDED NEXT STEPS")
    print("="*40)
    
    if tilted_correlation < 0.5:
        print("1. 🔍 INVESTIGATE ROTATION CENTERS:")
        print("   - Compare pix0 vectors between C and PyTorch")
        print("   - Check if PyTorch rotates around wrong point")
        print("   - Verify pivot mode implementation")
        
        print("2. 🧮 VERIFY COORDINATE TRANSFORMATIONS:")
        print("   - Check rotation matrix application order")
        print("   - Verify right-hand rule consistency")
        print("   - Check if basis vectors are orthonormal after rotations")
        
        print("3. 📐 TEST DISTANCE SCALING:")
        print("   - Run same tilted config at different distances")
        print("   - If error scales linearly -> rotation center issue")
        print("   - If error constant -> transformation/unit issue")

def main():
    """Main function to run correlation test and analysis"""
    print("SIMPLE CORRELATION TEST FOR 28MM DETECTOR OFFSET")
    print("="*60)
    
    # Run verification and get correlation data
    metrics = run_verification_and_extract_correlation()
    
    if metrics:
        # Analyze the correlation issue
        analyze_correlation_issue(metrics)
        
        # Save analysis for reference
        output_dir = Path("correlation_analysis")
        output_dir.mkdir(exist_ok=True)
        
        analysis_file = output_dir / "correlation_analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"\n📊 Full metrics saved to: {analysis_file}")
        print("📈 Visual plots available in: reports/detector_verification/")
        
    else:
        print("❌ Unable to extract correlation metrics")
        print("   Check that verify_detector_geometry.py is working correctly")

if __name__ == "__main__":
    main()