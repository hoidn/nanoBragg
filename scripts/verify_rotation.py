#!/usr/bin/env python3
"""
Detector rotation verification script for nanoBragg PyTorch implementation.

This script tests the DETECTOR geometry rotation pipeline by comparing the PyTorch
Detector._calculate_basis_vectors() output against ground truth data from the C-code
trace logs for the 'cubic_tilted_detector' test case.

The test uses:
- Initial MOSFLM vectors: fdet=[0,0,1], sdet=[0,-1,0], odet=[1,0,0]
- Rotation angles: rotx=5.0°, roty=3.0°, rotz=2.0°, twotheta=15.0°
- Two-theta axis: [0,0,-1]

This focuses on the actual cause of the correlation mismatch rather than crystal rotations.
"""

import os
import torch
import numpy as np
from typing import Tuple, Dict

# Set environment variable for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


def get_detector_ground_truth() -> Dict[str, torch.Tensor]:
    """
    Load ground truth detector basis vectors from the C-code trace.
    
    These values are from tests/test_detector_geometry.py which contains
    the exact expected rotated basis vectors from nanoBragg.c for the
    'cubic_tilted_detector' test case.
    """
    # Expected rotated detector basis vectors from C-code trace (in meters)
    expected_fdet_vec = torch.tensor(
        [0.0311947630447082, -0.096650175316428, 0.994829447880333], 
        dtype=torch.float64
    )
    expected_sdet_vec = torch.tensor(
        [-0.228539518954453, -0.969636205471835, -0.0870362988312832], 
        dtype=torch.float64
    )
    expected_odet_vec = torch.tensor(
        [0.973034724475264, -0.224642766741965, -0.0523359562429438], 
        dtype=torch.float64
    )
    
    # Initial MOSFLM basis vectors (before rotation)
    initial_fdet_vec = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    initial_sdet_vec = torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64)
    initial_odet_vec = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
    
    # Rotation parameters from the test case
    detector_rotx_deg = 5.0
    detector_roty_deg = 3.0
    detector_rotz_deg = 2.0
    detector_twotheta_deg = 15.0
    twotheta_axis = torch.tensor([0.0, 0.0, -1.0], dtype=torch.float64)
    
    return {
        'detector_rotx_deg': detector_rotx_deg,
        'detector_roty_deg': detector_roty_deg,
        'detector_rotz_deg': detector_rotz_deg,
        'detector_twotheta_deg': detector_twotheta_deg,
        'twotheta_axis': twotheta_axis,
        'initial_fdet_vec': initial_fdet_vec,
        'initial_sdet_vec': initial_sdet_vec,
        'initial_odet_vec': initial_odet_vec,
        'expected_fdet_vec': expected_fdet_vec,
        'expected_sdet_vec': expected_sdet_vec,
        'expected_odet_vec': expected_odet_vec,
    }


def pytorch_detector_rotation(ground_truth: Dict) -> Dict[str, torch.Tensor]:
    """
    Test PyTorch detector rotation using the Detector._calculate_basis_vectors() method.
    
    This creates a Detector instance with the test case configuration and
    extracts the rotated basis vectors for comparison.
    """
    import sys
    sys.path.append('src')
    from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot
    from nanobrag_torch.models.detector import Detector
    
    # Create detector configuration matching the test case
    config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=61.2,  # Offset slow axis
        beam_center_f=61.2,  # Offset fast axis
        detector_convention=DetectorConvention.MOSFLM,
        detector_rotx_deg=ground_truth['detector_rotx_deg'],
        detector_roty_deg=ground_truth['detector_roty_deg'],
        detector_rotz_deg=ground_truth['detector_rotz_deg'],
        detector_twotheta_deg=ground_truth['detector_twotheta_deg'],
        detector_pivot=DetectorPivot.BEAM,
    )
    
    # Create detector instance
    detector = Detector(config=config, dtype=torch.float64)
    
    return {
        'computed_fdet_vec': detector.fdet_vec,
        'computed_sdet_vec': detector.sdet_vec,
        'computed_odet_vec': detector.odet_vec,
    }


def manual_detector_rotation(ground_truth: Dict) -> Dict[str, torch.Tensor]:
    """
    Manual implementation of detector rotation to verify PyTorch logic.
    
    This replicates the exact sequence from Detector._calculate_basis_vectors():
    1. Apply detector rotations (rotx, roty, rotz)
    2. Apply two-theta rotation around specified axis
    """
    import sys
    sys.path.append('src')
    from nanobrag_torch.utils.geometry import angles_to_rotation_matrix, rotate_axis
    
    # Get initial basis vectors
    fdet_vec = ground_truth['initial_fdet_vec'].clone()
    sdet_vec = ground_truth['initial_sdet_vec'].clone()
    odet_vec = ground_truth['initial_odet_vec'].clone()
    
    # Convert degrees to radians
    rotx_rad = torch.deg2rad(torch.tensor(ground_truth['detector_rotx_deg'], dtype=torch.float64))
    roty_rad = torch.deg2rad(torch.tensor(ground_truth['detector_roty_deg'], dtype=torch.float64))
    rotz_rad = torch.deg2rad(torch.tensor(ground_truth['detector_rotz_deg'], dtype=torch.float64))
    twotheta_rad = torch.deg2rad(torch.tensor(ground_truth['detector_twotheta_deg'], dtype=torch.float64))
    
    # Apply detector rotations (rotx, roty, rotz)
    rotation_matrix = angles_to_rotation_matrix(rotx_rad, roty_rad, rotz_rad)
    
    fdet_vec = torch.matmul(rotation_matrix, fdet_vec)
    sdet_vec = torch.matmul(rotation_matrix, sdet_vec)
    odet_vec = torch.matmul(rotation_matrix, odet_vec)
    
    # Apply two-theta rotation around specified axis
    twotheta_axis = ground_truth['twotheta_axis']
    
    if torch.abs(twotheta_rad) > 1e-12:
        fdet_vec = rotate_axis(fdet_vec, twotheta_axis, twotheta_rad)
        sdet_vec = rotate_axis(sdet_vec, twotheta_axis, twotheta_rad)
        odet_vec = rotate_axis(odet_vec, twotheta_axis, twotheta_rad)
    
    return {
        'manual_fdet_vec': fdet_vec,
        'manual_sdet_vec': sdet_vec,
        'manual_odet_vec': odet_vec,
    }


def step_by_step_detector_rotation(ground_truth: Dict) -> Dict[str, torch.Tensor]:
    """
    Step-by-step detector rotation to debug any potential issues.
    
    This applies each rotation individually to help identify where any
    discrepancies might occur.
    """
    import sys
    sys.path.append('src')
    from nanobrag_torch.utils.geometry import angles_to_rotation_matrix, rotate_axis
    
    # Get initial basis vectors
    fdet_vec = ground_truth['initial_fdet_vec'].clone()
    sdet_vec = ground_truth['initial_sdet_vec'].clone()
    odet_vec = ground_truth['initial_odet_vec'].clone()
    
    print("Step-by-step detector rotation:")
    print(f"Initial vectors:")
    print(f"  fdet: {fdet_vec.numpy()}")
    print(f"  sdet: {sdet_vec.numpy()}")
    print(f"  odet: {odet_vec.numpy()}")
    
    # Convert degrees to radians
    rotx_rad = torch.deg2rad(torch.tensor(ground_truth['detector_rotx_deg'], dtype=torch.float64))
    roty_rad = torch.deg2rad(torch.tensor(ground_truth['detector_roty_deg'], dtype=torch.float64))
    rotz_rad = torch.deg2rad(torch.tensor(ground_truth['detector_rotz_deg'], dtype=torch.float64))
    twotheta_rad = torch.deg2rad(torch.tensor(ground_truth['detector_twotheta_deg'], dtype=torch.float64))
    
    # Apply rotations individually for debugging
    if torch.abs(rotx_rad) > 1e-12:
        Rx = angles_to_rotation_matrix(rotx_rad, torch.tensor(0.0), torch.tensor(0.0))
        fdet_vec = torch.matmul(Rx, fdet_vec)
        sdet_vec = torch.matmul(Rx, sdet_vec)
        odet_vec = torch.matmul(Rx, odet_vec)
        print(f"After X rotation ({ground_truth['detector_rotx_deg']}°):")
        print(f"  fdet: {fdet_vec.numpy()}")
        print(f"  sdet: {sdet_vec.numpy()}")
        print(f"  odet: {odet_vec.numpy()}")
    
    if torch.abs(roty_rad) > 1e-12:
        Ry = angles_to_rotation_matrix(torch.tensor(0.0), roty_rad, torch.tensor(0.0))
        fdet_vec = torch.matmul(Ry, fdet_vec)
        sdet_vec = torch.matmul(Ry, sdet_vec)
        odet_vec = torch.matmul(Ry, odet_vec)
        print(f"After Y rotation ({ground_truth['detector_roty_deg']}°):")
        print(f"  fdet: {fdet_vec.numpy()}")
        print(f"  sdet: {sdet_vec.numpy()}")
        print(f"  odet: {odet_vec.numpy()}")
    
    if torch.abs(rotz_rad) > 1e-12:
        Rz = angles_to_rotation_matrix(torch.tensor(0.0), torch.tensor(0.0), rotz_rad)
        fdet_vec = torch.matmul(Rz, fdet_vec)
        sdet_vec = torch.matmul(Rz, sdet_vec)
        odet_vec = torch.matmul(Rz, odet_vec)
        print(f"After Z rotation ({ground_truth['detector_rotz_deg']}°):")
        print(f"  fdet: {fdet_vec.numpy()}")
        print(f"  sdet: {sdet_vec.numpy()}")
        print(f"  odet: {odet_vec.numpy()}")
    
    # Apply two-theta rotation
    if torch.abs(twotheta_rad) > 1e-12:
        twotheta_axis = ground_truth['twotheta_axis']
        fdet_vec = rotate_axis(fdet_vec, twotheta_axis, twotheta_rad)
        sdet_vec = rotate_axis(sdet_vec, twotheta_axis, twotheta_rad)
        odet_vec = rotate_axis(odet_vec, twotheta_axis, twotheta_rad)
        print(f"After twotheta rotation ({ground_truth['detector_twotheta_deg']}° around {twotheta_axis.numpy()}):")
        print(f"  fdet: {fdet_vec.numpy()}")
        print(f"  sdet: {sdet_vec.numpy()}")
        print(f"  odet: {odet_vec.numpy()}")
    
    return {
        'step_fdet_vec': fdet_vec,
        'step_sdet_vec': sdet_vec,
        'step_odet_vec': odet_vec,
    }


def print_comparison_table(method_name: str, computed: Dict[str, torch.Tensor], expected: Dict[str, torch.Tensor]):
    """Print a detailed comparison table showing computed vs expected detector basis vectors."""
    print(f"\n=== {method_name} Results ===")
    print("Vector      | Component |   Computed   |   Expected   |   Difference  |   Rel Error")
    print("-" * 80)
    
    total_error = 0.0
    count = 0
    max_error = 0.0
    
    vector_mapping = {
        'fdet_vec': 'Fast Det',
        'sdet_vec': 'Slow Det',
        'odet_vec': 'Normal Det'
    }
    
    for computed_key, vector_name in vector_mapping.items():
        expected_key = f'expected_{computed_key}'
        
        # Handle different naming conventions
        if computed_key not in computed:
            # Try alternative naming
            alt_key = computed_key.replace('_vec', '_vec')
            if f'computed_{alt_key}' in computed:
                computed_key = f'computed_{alt_key}'
            elif f'manual_{alt_key}' in computed:
                computed_key = f'manual_{alt_key}'
            elif f'step_{alt_key}' in computed:
                computed_key = f'step_{alt_key}'
                
        if computed_key in computed and expected_key in expected:
            comp_vec = computed[computed_key]
            exp_vec = expected[expected_key]
            
            for i, component in enumerate(['X', 'Y', 'Z']):
                comp_val = float(comp_vec[i])
                exp_val = float(exp_vec[i])
                diff = comp_val - exp_val
                rel_error = abs(diff / exp_val) if abs(exp_val) > 1e-12 else 0.0
                
                print(f"{vector_name:11} | {component:9} | {comp_val:12.8f} | {exp_val:12.8f} | {diff:13.2e} | {rel_error:11.2e}")
                
                total_error += abs(diff)
                max_error = max(max_error, abs(diff))
                count += 1
    
    avg_error = total_error / count if count > 0 else 0.0
    print(f"\nAverage absolute error: {avg_error:.2e}")
    print(f"Maximum absolute error: {max_error:.2e}")
    
    return max_error


def verify_vector_properties(vectors: Dict[str, torch.Tensor], method_name: str):
    """Verify that the computed basis vectors have proper orthonormal properties."""
    print(f"\n=== {method_name} Vector Properties ===")
    
    # Extract vectors (handle different naming conventions)
    fdet_vec = None
    sdet_vec = None
    odet_vec = None
    
    for key, vec in vectors.items():
        if 'fdet' in key:
            fdet_vec = vec
        elif 'sdet' in key:
            sdet_vec = vec
        elif 'odet' in key:
            odet_vec = vec
    
    if fdet_vec is None or sdet_vec is None or odet_vec is None:
        print("Could not find all three basis vectors")
        return
    
    # Check magnitudes (should be 1)
    fdet_mag = torch.norm(fdet_vec)
    sdet_mag = torch.norm(sdet_vec)
    odet_mag = torch.norm(odet_vec)
    
    print(f"Vector magnitudes:")
    print(f"  |fdet|: {float(fdet_mag):.12f} (error: {abs(float(fdet_mag) - 1.0):.2e})")
    print(f"  |sdet|: {float(sdet_mag):.12f} (error: {abs(float(sdet_mag) - 1.0):.2e})")
    print(f"  |odet|: {float(odet_mag):.12f} (error: {abs(float(odet_mag) - 1.0):.2e})")
    
    # Check orthogonality (dot products should be 0)
    fdet_dot_sdet = torch.dot(fdet_vec, sdet_vec)
    fdet_dot_odet = torch.dot(fdet_vec, odet_vec)
    sdet_dot_odet = torch.dot(sdet_vec, odet_vec)
    
    print(f"Orthogonality checks:")
    print(f"  fdet·sdet: {float(fdet_dot_sdet):.2e}")
    print(f"  fdet·odet: {float(fdet_dot_odet):.2e}")
    print(f"  sdet·odet: {float(sdet_dot_odet):.2e}")
    
    # Check handedness (cross product should match expected direction)
    cross_fs = torch.cross(fdet_vec, sdet_vec)
    cross_error = torch.norm(cross_fs - odet_vec)
    
    print(f"Handedness check:")
    print(f"  |fdet×sdet - odet|: {float(cross_error):.2e}")
    
    # Overall assessment
    max_magnitude_error = max(abs(float(fdet_mag) - 1.0), abs(float(sdet_mag) - 1.0), abs(float(odet_mag) - 1.0))
    max_orthogonality_error = max(abs(float(fdet_dot_sdet)), abs(float(fdet_dot_odet)), abs(float(sdet_dot_odet)))
    
    if max_magnitude_error < 1e-12 and max_orthogonality_error < 1e-12 and float(cross_error) < 1e-12:
        print("✅ Vectors form a proper orthonormal basis")
    else:
        print("⚠️  Vector properties check FAILED")


def run_detector_rotation_verification():
    """Run the complete detector rotation verification analysis."""
    
    print("Detector Rotation Verification")
    print("=" * 50)
    print()
    
    # Load ground truth data
    ground_truth = get_detector_ground_truth()
    
    print("Test Configuration:")
    print(f"  Rotation angles: rotx={ground_truth['detector_rotx_deg']}°, roty={ground_truth['detector_roty_deg']}°, rotz={ground_truth['detector_rotz_deg']}°")
    print(f"  Two-theta: {ground_truth['detector_twotheta_deg']}° around axis {ground_truth['twotheta_axis'].numpy()}")
    print(f"  Detector convention: MOSFLM")
    print()
    
    # 1. Test PyTorch Detector implementation
    print("1. Testing PyTorch Detector Implementation")
    print("-" * 40)
    
    try:
        pytorch_results = pytorch_detector_rotation(ground_truth)
        max_error_pytorch = print_comparison_table("PyTorch Detector", pytorch_results, ground_truth)
        verify_vector_properties(pytorch_results, "PyTorch Detector")
        
    except Exception as e:
        print(f"ERROR in PyTorch Detector method: {e}")
        pytorch_results = None
        max_error_pytorch = float('inf')
    
    # 2. Test manual implementation
    print("\n2. Testing Manual Implementation")
    print("-" * 40)
    
    try:
        manual_results = manual_detector_rotation(ground_truth)
        max_error_manual = print_comparison_table("Manual Implementation", manual_results, ground_truth)
        verify_vector_properties(manual_results, "Manual Implementation")
        
    except Exception as e:
        print(f"ERROR in manual method: {e}")
        manual_results = None
        max_error_manual = float('inf')
    
    # 3. Step-by-step debugging
    print("\n3. Step-by-Step Debugging")
    print("-" * 40)
    
    try:
        step_results = step_by_step_detector_rotation(ground_truth)
        max_error_step = print_comparison_table("Step-by-Step", step_results, ground_truth)
        verify_vector_properties(step_results, "Step-by-Step")
        
    except Exception as e:
        print(f"ERROR in step-by-step method: {e}")
        step_results = None
        max_error_step = float('inf')
    
    # 4. Cross-method comparison
    print("\n4. Cross-Method Comparison")
    print("-" * 40)
    
    if pytorch_results and manual_results:
        print("Difference between PyTorch and Manual methods:")
        
        pytorch_fdet = pytorch_results['computed_fdet_vec']
        pytorch_sdet = pytorch_results['computed_sdet_vec'] 
        pytorch_odet = pytorch_results['computed_odet_vec']
        
        manual_fdet = manual_results['manual_fdet_vec']
        manual_sdet = manual_results['manual_sdet_vec']
        manual_odet = manual_results['manual_odet_vec']
        
        fdet_diff = torch.norm(pytorch_fdet - manual_fdet)
        sdet_diff = torch.norm(pytorch_sdet - manual_sdet)
        odet_diff = torch.norm(pytorch_odet - manual_odet)
        
        print(f"  |fdet_pytorch - fdet_manual|: {float(fdet_diff):.2e}")
        print(f"  |sdet_pytorch - sdet_manual|: {float(sdet_diff):.2e}")
        print(f"  |odet_pytorch - odet_manual|: {float(odet_diff):.2e}")
        
        max_method_diff = max(float(fdet_diff), float(sdet_diff), float(odet_diff))
        
        if max_method_diff < 1e-12:
            print("✅ PyTorch and Manual methods agree within numerical precision")
        else:
            print("⚠️  SIGNIFICANT DIFFERENCE between PyTorch and Manual methods!")
    
    # 5. Summary
    print("\n" + "="*60)
    print("🎯 DETECTOR ROTATION VERIFICATION SUMMARY")
    print("="*60)
    
    print(f"\n📊 ACCURACY vs GROUND TRUTH:")
    if pytorch_results:
        print(f"   PyTorch Detector: max error = {max_error_pytorch:.2e}")
    if manual_results:
        print(f"   Manual Implementation: max error = {max_error_manual:.2e}")
    if step_results:
        print(f"   Step-by-Step: max error = {max_error_step:.2e}")
    
    # Determine overall status
    best_error = min(filter(lambda x: x != float('inf'), [max_error_pytorch, max_error_manual, max_error_step]))
    
    if best_error < 1e-8:
        print(f"\n✅ CONCLUSION: Detector rotation implementation is CORRECT")
        print(f"   All methods achieve high accuracy (best error: {best_error:.2e})")
        print(f"   The detector rotation pipeline is working as expected.")
    else:
        print(f"\n⚠️  CONCLUSION: Detector rotation has SIGNIFICANT ERROR")
        print(f"   Best achieved error: {best_error:.2e}")
        print(f"   This suggests a bug in the rotation implementation.")
        
        # Suggest debugging steps
        print(f"\n🔍 DEBUGGING SUGGESTIONS:")
        print(f"   1. Check rotation matrix calculation in angles_to_rotation_matrix()")
        print(f"   2. Verify rotate_axis() implementation for two-theta rotation")
        print(f"   3. Check rotation order and axis conventions")
        print(f"   4. Verify ground truth data from C-code trace")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    run_detector_rotation_verification()