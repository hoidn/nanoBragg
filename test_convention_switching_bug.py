#!/usr/bin/env python3
"""
Test the CUSTOM vs MOSFLM convention switching bug.
The hypothesis: DetectorConfig auto-sets twotheta_axis=[0,0,-1] which may trigger CUSTOM convention.
"""

import os
import sys
import torch
from pathlib import Path

# Set environment variable
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src to path  
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig, DetectorConvention, DetectorPivot
from scripts.c_reference_utils import build_nanobragg_command

def test_convention_switching():
    """Test how different twotheta_axis settings affect C command generation."""
    
    print("Testing CUSTOM vs MOSFLM Convention Switching")
    print("=" * 60)
    print()
    
    # Create base crystal and beam configs
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
    )
    
    beam_config = BeamConfig(wavelength_A=6.2)
    
    test_cases = [
        {
            "name": "Baseline - No rotations, twotheta_axis=None (explicit)",
            "detector_config": DetectorConfig(
                distance_mm=100.0, pixel_size_mm=0.1, spixels=1024, fpixels=1024,
                beam_center_s=51.25, beam_center_f=51.25,
                detector_convention=DetectorConvention.MOSFLM,
                detector_pivot=DetectorPivot.BEAM,
                # Explicitly leave twotheta_axis as None - don't let __post_init__ set it
            )
        },
        {
            "name": "Tilted - With rotations, twotheta_axis=None (explicit)", 
            "detector_config": DetectorConfig(
                distance_mm=100.0, pixel_size_mm=0.1, spixels=1024, fpixels=1024,
                beam_center_s=51.25, beam_center_f=51.25,
                detector_convention=DetectorConvention.MOSFLM,
                detector_rotx_deg=5.0, detector_roty_deg=3.0, detector_rotz_deg=2.0,
                detector_twotheta_deg=15.0, detector_pivot=DetectorPivot.SAMPLE,
                # Explicitly leave twotheta_axis as None - don't let __post_init__ set it
            )
        },
    ]
    
    for test_case in test_cases:
        print(f"🔬 {test_case['name']}")
        detector_config = test_case['detector_config']
        
        # Check what __post_init__ set for twotheta_axis
        print(f"   twotheta_axis after __post_init__: {detector_config.twotheta_axis}")
        
        # Generate C command
        try:
            cmd = build_nanobragg_command(
                detector_config=detector_config,
                crystal_config=crystal_config,
                beam_config=beam_config,
            )
            
            # Check if -twotheta_axis appears in command
            has_twotheta_axis_param = "-twotheta_axis" in cmd
            print(f"   Command includes -twotheta_axis: {has_twotheta_axis_param}")
            
            if has_twotheta_axis_param:
                # Extract the axis values
                idx = cmd.index("-twotheta_axis")
                axis_values = [cmd[idx+1], cmd[idx+2], cmd[idx+3]]
                print(f"   Axis values sent to C: [{axis_values[0]}, {axis_values[1]}, {axis_values[2]}]")
                print(f"   ⚠️  This will trigger CUSTOM convention (no +0.5 pixel offset)!")
            else:
                print(f"   ✅ No -twotheta_axis sent → C uses MOSFLM convention (+0.5 pixel offset)")
            
            # Show key parameters sent to C
            relevant_params = []
            for i, arg in enumerate(cmd):
                if arg in ["-Xbeam", "-Ybeam", "-twotheta", "-detector_rotx", "-detector_roty", "-detector_rotz", "-pivot"]:
                    if i + 1 < len(cmd):
                        relevant_params.append(f"{arg} {cmd[i+1]}")
                elif arg == "-twotheta_axis" and i + 3 < len(cmd):
                    relevant_params.append(f"{arg} {cmd[i+1]} {cmd[i+2]} {cmd[i+3]}")
            
            print(f"   Key C parameters: {', '.join(relevant_params)}")
            
        except Exception as e:
            print(f"   ❌ Error generating command: {e}")
        
        print()

def test_manual_axis_override():
    """Test manually overriding twotheta_axis to None."""
    
    print("Testing Manual twotheta_axis Override")
    print("=" * 40)
    print()
    
    # Create detector config that would normally auto-set twotheta_axis
    detector_config = DetectorConfig(
        distance_mm=100.0, pixel_size_mm=0.1, spixels=1024, fpixels=1024,
        beam_center_s=51.25, beam_center_f=51.25,
        detector_convention=DetectorConvention.MOSFLM,
        detector_rotx_deg=5.0, detector_roty_deg=3.0, detector_rotz_deg=2.0,
        detector_twotheta_deg=15.0, detector_pivot=DetectorPivot.SAMPLE,
    )
    
    print(f"Original twotheta_axis: {detector_config.twotheta_axis}")
    
    # Manually override to None to prevent CUSTOM convention
    detector_config.twotheta_axis = None
    print(f"After manual override: {detector_config.twotheta_axis}")
    
    # Generate command
    crystal_config = CrystalConfig(cell_a=100.0, cell_b=100.0, cell_c=100.0, cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0)
    beam_config = BeamConfig(wavelength_A=6.2)
    
    cmd = build_nanobragg_command(
        detector_config=detector_config,
        crystal_config=crystal_config,
        beam_config=beam_config,
    )
    
    has_twotheta_axis_param = "-twotheta_axis" in cmd
    print(f"Command includes -twotheta_axis: {has_twotheta_axis_param}")
    
    if not has_twotheta_axis_param:
        print("✅ Success! No -twotheta_axis sent, C will use MOSFLM convention")
    else:
        print("❌ Still sending -twotheta_axis, will trigger CUSTOM convention")

def main():
    test_convention_switching()
    test_manual_axis_override()

if __name__ == "__main__":
    main()