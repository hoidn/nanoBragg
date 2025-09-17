#!/usr/bin/env python3
"""
Detailed comparison of pix0_vector calculation between PyTorch and C.
Focus on the exact rotation sequence and intermediate steps.
"""

import os
import sys
import torch
import numpy as np
from pathlib import Path
import subprocess
import tempfile

# Set environment variable
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.utils.geometry import angles_to_rotation_matrix, rotate_axis
from scripts.c_reference_utils import build_nanobragg_command

def trace_pytorch_pix0_calculation():
    """Step-by-step pix0_vector calculation in PyTorch."""
    
    print("PYTORCH PIX0_VECTOR CALCULATION")
    print("=" * 50)
    
    # Configuration that produces 39mm offset
    detector_config = DetectorConfig(
        distance_mm=100.0, pixel_size_mm=0.1, spixels=1024, fpixels=1024,
        beam_center_s=51.25, beam_center_f=51.25,
        detector_convention=DetectorConvention.MOSFLM,
        detector_rotx_deg=5.0, detector_roty_deg=3.0, detector_rotz_deg=2.0,
        detector_twotheta_deg=15.0, detector_pivot=DetectorPivot.SAMPLE,
    )
    
    print(f"Input parameters:")
    print(f"  rotx={detector_config.detector_rotx_deg}°, roty={detector_config.detector_roty_deg}°, rotz={detector_config.detector_rotz_deg}°")
    print(f"  twotheta={detector_config.detector_twotheta_deg}°, pivot={detector_config.detector_pivot}")
    print(f"  beam_center=({detector_config.beam_center_s}, {detector_config.beam_center_f}) mm")
    print(f"  distance={detector_config.distance_mm} mm, pixel_size={detector_config.pixel_size_mm} mm")
    
    # Manual calculation following detector.py logic
    device = torch.device('cpu')
    dtype = torch.float64
    
    # Step 1: Initial basis vectors (MOSFLM convention)
    print(f"\n1. Initial basis vectors (MOSFLM convention):")
    fdet_initial = torch.tensor([0.0, 0.0, 1.0], device=device, dtype=dtype)
    sdet_initial = torch.tensor([0.0, -1.0, 0.0], device=device, dtype=dtype)
    odet_initial = torch.tensor([1.0, 0.0, 0.0], device=device, dtype=dtype)
    print(f"  fdet_initial: {fdet_initial.numpy()}")
    print(f"  sdet_initial: {sdet_initial.numpy()}")
    print(f"  odet_initial: {odet_initial.numpy()}")
    
    # Step 2: Rotation matrix for detector rotations (rotx, roty, rotz)
    rotx_rad = torch.tensor(np.radians(detector_config.detector_rotx_deg), dtype=dtype)
    roty_rad = torch.tensor(np.radians(detector_config.detector_roty_deg), dtype=dtype)
    rotz_rad = torch.tensor(np.radians(detector_config.detector_rotz_deg), dtype=dtype)
    
    print(f"\n2. Detector rotations (in radians):")
    print(f"  rotx: {rotx_rad.item():.6f} rad ({detector_config.detector_rotx_deg}°)")
    print(f"  roty: {roty_rad.item():.6f} rad ({detector_config.detector_roty_deg}°)")
    print(f"  rotz: {rotz_rad.item():.6f} rad ({detector_config.detector_rotz_deg}°)")
    
    R_det = angles_to_rotation_matrix(rotx_rad, roty_rad, rotz_rad)
    print(f"  Combined rotation matrix R_det:")
    print(f"    {R_det[0].numpy()}")
    print(f"    {R_det[1].numpy()}")
    print(f"    {R_det[2].numpy()}")
    
    # Step 3: Apply detector rotations
    print(f"\n3. After detector rotations:")
    fdet_rotated = torch.mv(R_det, fdet_initial)
    sdet_rotated = torch.mv(R_det, sdet_initial)
    odet_rotated = torch.mv(R_det, odet_initial)
    print(f"  fdet_rotated: {fdet_rotated.numpy()}")
    print(f"  sdet_rotated: {sdet_rotated.numpy()}")
    print(f"  odet_rotated: {odet_rotated.numpy()}")
    
    # Step 4: Two-theta rotation
    twotheta_rad = torch.tensor(np.radians(detector_config.detector_twotheta_deg), dtype=dtype)
    twotheta_axis = detector_config.twotheta_axis  # Should be [0,0,-1] for MOSFLM
    
    print(f"\n4. Two-theta rotation:")
    print(f"  twotheta: {twotheta_rad.item():.6f} rad ({detector_config.detector_twotheta_deg}°)")
    print(f"  twotheta_axis: {twotheta_axis.numpy()}")
    
    if abs(twotheta_rad) > 1e-6:
        # Convert to same dtype for consistency
        twotheta_axis = twotheta_axis.to(dtype=dtype)
        fdet_final = rotate_axis(fdet_rotated, twotheta_axis, twotheta_rad)
        sdet_final = rotate_axis(sdet_rotated, twotheta_axis, twotheta_rad)
        odet_final = rotate_axis(odet_rotated, twotheta_axis, twotheta_rad)
    else:
        fdet_final = fdet_rotated
        sdet_final = sdet_rotated
        odet_final = odet_rotated
    
    print(f"  After twotheta rotation:")
    print(f"    fdet_final: {fdet_final.numpy()}")
    print(f"    sdet_final: {sdet_final.numpy()}")
    print(f"    odet_final: {odet_final.numpy()}")
    
    # Step 5: Calculate beam center (MOSFLM convention with +0.5 pixel offset)
    beam_center_s_pixels = detector_config.beam_center_s / detector_config.pixel_size_mm
    beam_center_f_pixels = detector_config.beam_center_f / detector_config.pixel_size_mm
    
    print(f"\n5. Beam center calculation:")
    print(f"  beam_center (mm): ({detector_config.beam_center_s}, {detector_config.beam_center_f})")
    print(f"  beam_center (pixels): ({beam_center_s_pixels}, {beam_center_f_pixels})")
    
    # MOSFLM adds +0.5 pixel offset
    sbeam_pixels = beam_center_s_pixels + 0.5
    fbeam_pixels = beam_center_f_pixels + 0.5
    print(f"  With +0.5 offset: ({sbeam_pixels}, {fbeam_pixels}) pixels")
    
    # Convert to meters
    pixel_size_m = detector_config.pixel_size_mm / 1000.0
    sbeam_m = sbeam_pixels * pixel_size_m
    fbeam_m = fbeam_pixels * pixel_size_m
    print(f"  In meters: ({sbeam_m:.6f}, {fbeam_m:.6f})")
    
    # Step 6: Calculate pix0_vector
    distance_m = detector_config.distance_mm / 1000.0
    
    print(f"\n6. pix0_vector calculation:")
    print(f"  distance: {distance_m:.3f} m")
    
    pix0_vector = distance_m * odet_final - sbeam_m * sdet_final - fbeam_m * fdet_final
    
    print(f"  pix0_vector = {distance_m:.3f} * odet_final - {sbeam_m:.6f} * sdet_final - {fbeam_m:.6f} * fdet_final")
    print(f"  pix0_vector = {pix0_vector.numpy()}")
    
    # Cross-check with Detector class
    print(f"\n7. Cross-check with Detector class:")
    detector = Detector(detector_config)
    detector_pix0 = detector.pix0_vector.detach().numpy()
    print(f"  Detector.pix0_vector: {detector_pix0}")
    
    match = np.allclose(pix0_vector.numpy(), detector_pix0, atol=1e-10)
    print(f"  Manual calc matches Detector class: {match}")
    
    return pix0_vector.numpy()

def run_c_calculation():
    """Run C calculation and extract pix0_vector."""
    
    print("\n" + "=" * 70)
    print("C REFERENCE PIX0_VECTOR CALCULATION")  
    print("=" * 70)
    
    # Same configuration as PyTorch
    detector_config = DetectorConfig(
        distance_mm=100.0, pixel_size_mm=0.1, spixels=1024, fpixels=1024,
        beam_center_s=51.25, beam_center_f=51.25,
        detector_convention=DetectorConvention.MOSFLM,
        detector_rotx_deg=5.0, detector_roty_deg=3.0, detector_rotz_deg=2.0,
        detector_twotheta_deg=15.0, detector_pivot=DetectorPivot.SAMPLE,
    )
    
    crystal_config = CrystalConfig(cell_a=100.0, cell_b=100.0, cell_c=100.0, cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0)
    beam_config = BeamConfig(wavelength_A=6.2)
    
    # Generate C command
    cmd = build_nanobragg_command(
        detector_config=detector_config,
        crystal_config=crystal_config, 
        beam_config=beam_config,
        executable_path="golden_suite_generator/nanoBragg_trace"
    )
    
    print(f"C command: {' '.join(cmd)}")
    
    # Create identity matrix file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mat', delete=False) as f:
        f.write("1.0 0.0 0.0\n")
        f.write("0.0 1.0 0.0\n")
        f.write("0.0 0.0 1.0\n")
        matrix_file = f.name
    
    # Add matrix to command
    cmd.extend(["-matrix", matrix_file])
    
    try:
        # Run the command and capture output
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".", timeout=30)
        
        if result.returncode != 0:
            print(f"❌ C command failed: {result.stderr}")
            return None
        
        # Parse output for pix0_vector
        lines = result.stderr.split('\n')  # C trace output goes to stderr
        pix0_line = None
        
        for line in lines:
            if 'pix0_vector' in line or 'PIX0' in line:
                print(f"Found line: {line}")
                pix0_line = line
                # Try to extract numbers
                
        if not pix0_line:
            print("❌ Could not find pix0_vector in C output")
            print("Last 20 lines of stderr:")
            for line in lines[-20:]:
                if line.strip():
                    print(f"  {line}")
            return None
            
    except subprocess.TimeoutExpired:
        print("❌ C command timed out")
        return None
    except Exception as e:
        print(f"❌ Error running C command: {e}")
        return None
    finally:
        # Clean up matrix file
        if 'matrix_file' in locals():
            os.unlink(matrix_file)
    
    return None

def main():
    """Main comparison function."""
    
    print("DETAILED PIX0_VECTOR CALCULATION COMPARISON")
    print("=" * 80)
    print()
    
    # Get PyTorch calculation
    pytorch_pix0 = trace_pytorch_pix0_calculation()
    
    # Get C calculation (for reference - may not work without proper instrumentation)
    c_pix0 = run_c_calculation()
    
    # Known values from PHASE_6_FINAL_REPORT.md
    print(f"\n" + "=" * 70)
    print("COMPARISON WITH KNOWN VALUES FROM REPORT")
    print("=" * 70)
    
    known_pytorch = np.array([0.109814, 0.022698, -0.051758])  # From report
    known_c = np.array([0.095234, 0.058827, -0.051702])       # From report
    
    print(f"Current PyTorch: [{pytorch_pix0[0]:.6f}, {pytorch_pix0[1]:.6f}, {pytorch_pix0[2]:.6f}]")
    print(f"Report PyTorch:  [{known_pytorch[0]:.6f}, {known_pytorch[1]:.6f}, {known_pytorch[2]:.6f}]")
    print(f"Report C:        [{known_c[0]:.6f}, {known_c[1]:.6f}, {known_c[2]:.6f}]")
    
    pytorch_matches_report = np.allclose(pytorch_pix0, known_pytorch, atol=1e-5)
    print(f"Current matches report PyTorch: {pytorch_matches_report}")
    
    diff_from_c = pytorch_pix0 - known_c
    diff_magnitude_mm = np.linalg.norm(diff_from_c) * 1000
    print(f"Difference from C: [{diff_from_c[0]:.6f}, {diff_from_c[1]:.6f}, {diff_from_c[2]:.6f}] m")
    print(f"Difference magnitude: {diff_magnitude_mm:.1f} mm")

if __name__ == "__main__":
    main()