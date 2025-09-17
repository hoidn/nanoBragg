#!/usr/bin/env python3
"""
Calculate the exact ratio from the C code trace output
"""

import math

def main():
    print("EXACT RATIO CALCULATION FROM C CODE TRACE")
    print("=" * 50)
    
    # From the C trace output:
    input_distance = 0.1  # meters (100mm)
    final_distance = 0.0974964  # meters from trace output
    
    # Calculate the ratio
    ratio = input_distance / final_distance
    print(f"Input distance:  {input_distance:.6f} m ({input_distance*1000:.1f} mm)")
    print(f"Final distance:  {final_distance:.6f} m ({final_distance*1000:.1f} mm)")  
    print(f"Ratio:           {ratio:.6f}")
    print(f"Distance change: {(final_distance-input_distance)*1000:.1f} mm")
    
    # The key insight: ratio = cos(effective_tilt_angle)
    # From the odet_vector after rotations in the trace:
    # odet_after_rotz = 0.973034724475264 -0.224642766741965 -0.0523359562429438
    # beam_vector = [1, 0, 0]  
    # ratio = dot_product([1,0,0], [0.973034724475264, -0.224642766741965, -0.0523359562429438])
    #       = 0.973034724475264
    
    theoretical_ratio = 0.973034724475264  # From the trace odet_vector[1]
    theoretical_final_distance = input_distance / theoretical_ratio
    
    print(f"\nFrom C trace odet_vector[1]: {theoretical_ratio:.6f}")
    print(f"Theoretical final distance:  {theoretical_final_distance:.6f} m ({theoretical_final_distance*1000:.1f} mm)")
    print(f"Theoretical distance change: {(theoretical_final_distance-input_distance)*1000:.1f} mm")
    
    # This matches! The ~2.5mm difference is because the line I found shows 0.0974964
    # Let me recalculate with the exact value
    exact_ratio = input_distance / 0.0974964
    print(f"\nExact ratio from trace:      {exact_ratio:.6f}")
    print(f"Exact distance change:       {(1/exact_ratio - 1)*100:.1f} mm (for 100mm input)")
    
    # For the tilted detector test case with larger rotations this difference scales!
    print("\n" + "=" * 50)
    print("SCALING FOR TILTED TEST CASE")
    print("=" * 50)
    
    # The test case has rotx=5°, roty=3°, rotz=2°, twotheta=15°
    # Let's calculate the effective angle
    
    # From the actual C output, let me find the odet_vector components
    # From trace: odet_after_rotz = 0.973034724475264 -0.224642766741965 -0.0523359562429438
    odet_x = 0.973034724475264
    ratio_actual = odet_x
    
    print(f"Actual ratio from C trace: {ratio_actual:.6f}")
    print(f"This corresponds to effective tilt angle: {math.degrees(math.acos(ratio_actual)):.1f}°")
    
    # Distance increase for any input distance
    distance_factor = 1.0 / ratio_actual
    print(f"Distance multiplication factor: {distance_factor:.6f}")
    print(f"For 100mm: becomes {100 * distance_factor:.1f}mm (+{100*(distance_factor-1):.1f}mm)")
    
    print(f"\n*** This explains the ~2.8mm systematic offset! ***")
    print(f"The PyTorch implementation doesn't apply this distance correction.")

if __name__ == "__main__":
    main()