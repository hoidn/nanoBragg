#!/usr/bin/env python3
"""
Test different pivot modes to understand the Y-component discrepancy.
"""

import os
import sys
import torch
import numpy as np
import subprocess
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set PyTorch environment for MKL compatibility
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot, BeamConfig, CrystalConfig
from nanobrag_torch.models.detector import Detector
from c_reference_utils import build_nanobragg_command, generate_identity_matrix

def run_c_with_pivot(pivot_mode, twotheta_deg=15.0):
    """Run C code with specific pivot mode"""
    
    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=61.2,
        beam_center_f=61.2,
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=pivot_mode,
        detector_rotx_deg=0.0,
        detector_roty_deg=0.0,
        detector_rotz_deg=0.0,
        detector_twotheta_deg=twotheta_deg,
    )
    
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),
    )
    
    beam_config = BeamConfig(
        wavelength_A=6.2, N_source_points=1,
        source_distance_mm=10000.0, source_size_mm=0.0,
    )
    
    # Generate temp matrix file
    matrix_file = "temp_identity.mat"
    generate_identity_matrix(matrix_file)
    
    # Build command
    cmd = build_nanobragg_command(
        detector_config, crystal_config, beam_config, 
        matrix_file=matrix_file,
        executable_path="golden_suite_generator/nanoBragg"
    )
    
    print(f"C Command: {' '.join(cmd)}")
    
    # Execute C code
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    Path(matrix_file).unlink(missing_ok=True)
    
    if result.returncode != 0:
        print(f"❌ C execution failed for pivot={pivot_mode}")
        return None, None
    
    # Extract pix0_vector
    all_output = (result.stdout or '') + '\n' + (result.stderr or '')
    c_pix0 = None
    
    for line in all_output.split('\n'):
        if 'DETECTOR_PIX0_VECTOR' in line and not 'before' in line.lower():
            parts = line.split()
            if len(parts) >= 4:
                try:
                    x = float(parts[1])
                    y = float(parts[2]) 
                    z = float(parts[3])
                    c_pix0 = np.array([x, y, z])
                    break
                except (ValueError, IndexError):
                    continue
    
    # Get PyTorch result for comparison
    detector = Detector(detector_config)
    py_pix0 = detector.pix0_vector.detach().numpy()
    
    return c_pix0, py_pix0

def test_pivot_modes():
    """Test both BEAM and SAMPLE pivot modes"""
    
    print("=== TESTING PIVOT MODES ===")
    print("Comparing BEAM vs SAMPLE pivot with twotheta=15°")
    
    # Test SAMPLE pivot (what we've been using)
    print(f"\n--- SAMPLE PIVOT ---")
    c_sample, py_sample = run_c_with_pivot(DetectorPivot.SAMPLE, 15.0)
    
    if c_sample is not None and py_sample is not None:
        print(f"C pix0_vector (SAMPLE):       {c_sample}")
        print(f"PyTorch pix0_vector (SAMPLE): {py_sample}")
        
        diff_sample = (py_sample - c_sample) * 1000
        print(f"Y error (SAMPLE):           {diff_sample[1]:.1f} mm")
    
    # Test BEAM pivot
    print(f"\n--- BEAM PIVOT ---")
    c_beam, py_beam = run_c_with_pivot(DetectorPivot.BEAM, 15.0)
    
    if c_beam is not None and py_beam is not None:
        print(f"C pix0_vector (BEAM):         {c_beam}")
        print(f"PyTorch pix0_vector (BEAM):   {py_beam}")
        
        diff_beam = (py_beam - c_beam) * 1000
        print(f"Y error (BEAM):             {diff_beam[1]:.1f} mm")
        
        if abs(diff_beam[1]) < abs(diff_sample[1]):
            print(f"✅ BEAM pivot has smaller Y error!")

if __name__ == "__main__":
    test_pivot_modes()
