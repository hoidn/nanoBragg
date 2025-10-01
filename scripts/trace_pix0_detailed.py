#!/usr/bin/env python3
"""
Ultra-detailed pix0_vector calculation tracer for Phase 4.1 diagnostic deep dive.

This script shows every single step of the pix0 calculation with all intermediate
values to identify the exact divergence point between C and Python implementations.
"""

import os
import sys
import torch
import numpy as np
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set environment variables
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.models.detector import Detector
from nanobrag_torch.config import DetectorConfig, DetectorPivot, DetectorConvention
from nanobrag_torch.utils.units import degrees_to_radians
import math


def trace_scalar(tag: str, val: float, prefix: str = "PIX0_PY"):
    """Print a scalar with maximum precision."""
    if isinstance(val, torch.Tensor):
        val = val.item()
    print(f"{prefix}:{tag}={val:.15g}")


def trace_vec(tag: str, vec: torch.Tensor, prefix: str = "PIX0_PY"):
    """Print a vector with maximum precision."""
    if vec.dim() == 0:
        print(f"{prefix}:{tag}={vec.item():.15g}")
    else:
        values = " ".join(f"{v:.15g}" for v in vec.cpu().numpy())
        print(f"{prefix}:{tag}=[{values}]")


def trace_mat(tag: str, mat: torch.Tensor, prefix: str = "PIX0_PY"):
    """Print a 3x3 matrix with maximum precision."""
    m = mat.cpu().numpy()
    for i in range(3):
        row = " ".join(f"{m[i,j]:.15g}" for j in range(3))
        print(f"{prefix}:{tag}_row{i}=[{row}]")


def create_rotation_matrix_x(angle_rad: float) -> torch.Tensor:
    """Create X-axis rotation matrix with detailed trace."""
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    trace_scalar("rot_x_angle_rad", angle_rad)
    trace_scalar("rot_x_cos", cos_a)
    trace_scalar("rot_x_sin", sin_a)
    
    matrix = torch.tensor([
        [1.0, 0.0, 0.0],
        [0.0, cos_a, -sin_a],
        [0.0, sin_a, cos_a]
    ], dtype=torch.float64)
    
    trace_mat("rot_x_matrix", matrix)
    return matrix


def create_rotation_matrix_y(angle_rad: float) -> torch.Tensor:
    """Create Y-axis rotation matrix with detailed trace."""
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    trace_scalar("rot_y_angle_rad", angle_rad)
    trace_scalar("rot_y_cos", cos_a)
    trace_scalar("rot_y_sin", sin_a)
    
    matrix = torch.tensor([
        [cos_a, 0.0, sin_a],
        [0.0, 1.0, 0.0],
        [-sin_a, 0.0, cos_a]
    ], dtype=torch.float64)
    
    trace_mat("rot_y_matrix", matrix)
    return matrix


def create_rotation_matrix_z(angle_rad: float) -> torch.Tensor:
    """Create Z-axis rotation matrix with detailed trace."""
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    trace_scalar("rot_z_angle_rad", angle_rad)
    trace_scalar("rot_z_cos", cos_a)
    trace_scalar("rot_z_sin", sin_a)
    
    matrix = torch.tensor([
        [cos_a, -sin_a, 0.0],
        [sin_a, cos_a, 0.0],
        [0.0, 0.0, 1.0]
    ], dtype=torch.float64)
    
    trace_mat("rot_z_matrix", matrix)
    return matrix


def create_twotheta_rotation_matrix(angle_rad: float, axis: torch.Tensor) -> torch.Tensor:
    """Create two-theta rotation matrix around arbitrary axis with detailed trace."""
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    trace_scalar("twotheta_angle_rad", angle_rad)
    trace_scalar("twotheta_cos", cos_a)
    trace_scalar("twotheta_sin", sin_a)
    trace_vec("twotheta_axis", axis)
    
    # Normalize axis
    axis_norm = torch.norm(axis)
    trace_scalar("twotheta_axis_norm", axis_norm)
    
    if axis_norm < 1e-10:
        return torch.eye(3, dtype=torch.float64)
    
    u = axis / axis_norm
    trace_vec("twotheta_axis_normalized", u)
    
    # Rodrigues' rotation formula
    ux, uy, uz = u[0], u[1], u[2]
    trace_scalar("twotheta_ux", ux)
    trace_scalar("twotheta_uy", uy)
    trace_scalar("twotheta_uz", uz)
    
    # Cross-product matrix
    K = torch.tensor([
        [0.0, -uz, uy],
        [uz, 0.0, -ux],
        [-uy, ux, 0.0]
    ], dtype=torch.float64)
    trace_mat("twotheta_cross_product_matrix", K)
    
    # Identity matrix
    I = torch.eye(3, dtype=torch.float64)
    
    # Outer product u ⊗ u
    outer = torch.outer(u, u)
    trace_mat("twotheta_outer_product", outer)
    
    # Rodrigues formula: R = I + sin(θ)K + (1-cos(θ))K²
    K_squared = torch.mm(K, K)
    trace_mat("twotheta_K_squared", K_squared)
    
    matrix = I + sin_a * K + (1 - cos_a) * K_squared
    trace_mat("twotheta_matrix", matrix)
    
    return matrix


def trace_pix0_calculation_step_by_step():
    """Trace the complete pix0_vector calculation with every intermediate step."""
    print("=" * 80)
    print("ULTRA-DETAILED PIX0_VECTOR CALCULATION TRACE")
    print("=" * 80)
    
    # Configuration matching the C trace output (BEAM pivot mode)
    config = DetectorConfig(
        distance_mm=100.0,
        beam_center_s=51.3,  # From C trace: no explicit beam center means use detector center
        beam_center_f=51.3,  # From C trace: no explicit beam center means use detector center  
        detector_rotx_deg=5.0,
        detector_roty_deg=3.0,
        detector_rotz_deg=2.0,
        detector_twotheta_deg=20.0,
        detector_pivot=DetectorPivot.BEAM,  # C trace shows BEAM pivot mode
        detector_convention=DetectorConvention.MOSFLM,
        pixel_size_mm=0.1,
        fpixels=1024,
        spixels=1024,
    )
    
    print("\nCONFIGURATION:")
    trace_scalar("distance_mm", config.distance_mm)
    trace_scalar("beam_center_s", config.beam_center_s)
    trace_scalar("beam_center_f", config.beam_center_f)
    trace_scalar("pixel_size_mm", config.pixel_size_mm)
    trace_scalar("detector_rotx_deg", config.detector_rotx_deg)
    trace_scalar("detector_roty_deg", config.detector_roty_deg)
    trace_scalar("detector_rotz_deg", config.detector_rotz_deg)
    trace_scalar("detector_twotheta_deg", config.detector_twotheta_deg)
    print(f"PIX0_PY:detector_pivot={config.detector_pivot.value}")
    print(f"PIX0_PY:detector_convention={config.detector_convention.value}")
    
    # Convert angles to radians
    print("\nANGLE CONVERSION:")
    rotx_rad = degrees_to_radians(config.detector_rotx_deg)
    roty_rad = degrees_to_radians(config.detector_roty_deg) 
    rotz_rad = degrees_to_radians(config.detector_rotz_deg)
    twotheta_rad = degrees_to_radians(config.detector_twotheta_deg)
    
    trace_scalar("rotx_rad", rotx_rad)
    trace_scalar("roty_rad", roty_rad)
    trace_scalar("rotz_rad", rotz_rad)
    trace_scalar("twotheta_rad", twotheta_rad)
    
    # Initial basis vectors (MOSFLM convention)
    print("\nINITIAL BASIS VECTORS (MOSFLM):")
    fdet_init = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    sdet_init = torch.tensor([0.0, -1.0, 0.0], dtype=torch.float64)
    odet_init = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
    
    trace_vec("fdet_initial", fdet_init)
    trace_vec("sdet_initial", sdet_init)
    trace_vec("odet_initial", odet_init)
    
    # Check pivot mode and calculate accordingly
    if config.detector_pivot == DetectorPivot.BEAM:
        print("\nPIX0 CALCULATION (BEAM PIVOT - AFTER ROTATIONS):")
        
        # First apply rotations to basis vectors
        print("\nROTATION MATRIX CONSTRUCTION:")
        
        # X rotation
        print("\nX-AXIS ROTATION:")
        Rx = create_rotation_matrix_x(rotx_rad)
        
        # Y rotation  
        print("\nY-AXIS ROTATION:")
        Ry = create_rotation_matrix_y(roty_rad)
        
        # Z rotation
        print("\nZ-AXIS ROTATION:")
        Rz = create_rotation_matrix_z(rotz_rad)
        
        # Combined rotation matrix (order: rotx -> roty -> rotz)
        print("\nCOMBINED ROTATION MATRIX CONSTRUCTION:")
        
        # Step 1: Rx
        R1 = Rx
        trace_mat("R1_Rx", R1)
        
        # Step 2: Ry @ Rx
        R2 = torch.mm(Ry, R1)
        trace_mat("R2_Ry_Rx", R2)
        
        # Step 3: Rz @ Ry @ Rx
        R3 = torch.mm(Rz, R2)
        trace_mat("R3_Rz_Ry_Rx", R3)
        
        # Apply rotations to basis vectors
        print("\nROTATED BASIS VECTORS:")
        fdet_rotated = torch.mv(R3, fdet_init)
        sdet_rotated = torch.mv(R3, sdet_init)
        odet_rotated = torch.mv(R3, odet_init)
        
        trace_vec("fdet_after_xyz_rotations", fdet_rotated)
        trace_vec("sdet_after_xyz_rotations", sdet_rotated)
        trace_vec("odet_after_xyz_rotations", odet_rotated)
        
        # Two-theta rotation (around Y axis for MOSFLM)
        print("\nTWO-THETA ROTATION:")
        twotheta_axis = torch.tensor([0.0, 1.0, 0.0], dtype=torch.float64)  # Y-axis for MOSFLM
        R_twotheta = create_twotheta_rotation_matrix(twotheta_rad, twotheta_axis)
        
        # Apply twotheta rotation
        fdet_final = torch.mv(R_twotheta, fdet_rotated)
        sdet_final = torch.mv(R_twotheta, sdet_rotated)
        odet_final = torch.mv(R_twotheta, odet_rotated)
        
        trace_vec("fdet_after_twotheta", fdet_final)
        trace_vec("sdet_after_twotheta", sdet_final)
        trace_vec("odet_after_twotheta", odet_final)
        
        # Now calculate pix0_vector using BEAM pivot formula with rotated vectors
        print("\nBEAM PIVOT PIX0 CALCULATION:")
        
        # MOSFLM beam center calculation (add 0.5 for pixel center)
        # CRITICAL: MOSFLM convention swaps axes: F<->s(Y), S<->f(X)
        Fbeam = (config.beam_center_s + 0.5) * config.pixel_size_mm / 1000.0
        Sbeam = (config.beam_center_f + 0.5) * config.pixel_size_mm / 1000.0
        distance_m = config.distance_mm / 1000.0
        beam_vector = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)  # MOSFLM beam direction
        
        trace_scalar("beam_center_s_plus_half", config.beam_center_s + 0.5)
        trace_scalar("beam_center_f_plus_half", config.beam_center_f + 0.5)
        trace_scalar("Fbeam_m", Fbeam)
        trace_scalar("Sbeam_m", Sbeam)
        trace_scalar("distance_m", distance_m)
        trace_vec("beam_vector", beam_vector)
        
        # Calculate each component
        fdet_component = -Fbeam * fdet_final
        sdet_component = -Sbeam * sdet_final
        beam_component = distance_m * beam_vector
        
        trace_vec("fdet_component", fdet_component)
        trace_vec("sdet_component", sdet_component)
        trace_vec("beam_component", beam_component)
        
        # Sum components for final pix0
        pix0_final = fdet_component + sdet_component + beam_component
        trace_vec("pix0_final_beam_pivot", pix0_final)
        
        # Store results for comparison
        pix0_rotated = pix0_final
        fdet_rotated = fdet_final
        sdet_rotated = sdet_final
        odet_rotated = odet_final
        
    else:
        # SAMPLE pivot mode: calculate pix0 BEFORE rotations, then rotate it
        print("\nPIX0 CALCULATION (SAMPLE PIVOT - BEFORE ROTATIONS):")
        
        # MOSFLM beam center calculation (add 0.5 for pixel center)
        Fclose = (config.beam_center_f + 0.5) * config.pixel_size_mm / 1000.0
        Sclose = (config.beam_center_s + 0.5) * config.pixel_size_mm / 1000.0
        distance_m = config.distance_mm / 1000.0
        
        trace_scalar("beam_center_f_plus_half", config.beam_center_f + 0.5)
        trace_scalar("beam_center_s_plus_half", config.beam_center_s + 0.5)
        trace_scalar("Fclose_m", Fclose)
        trace_scalar("Sclose_m", Sclose)
        trace_scalar("distance_m", distance_m)
        
        # Calculate each component
        fdet_component = -Fclose * fdet_init
        sdet_component = -Sclose * sdet_init
        odet_component = distance_m * odet_init
        
        trace_vec("fdet_component", fdet_component)
        trace_vec("sdet_component", sdet_component)
        trace_vec("odet_component", odet_component)
        
        # Sum components
        pix0_unrotated = fdet_component + sdet_component + odet_component
        trace_vec("pix0_unrotated", pix0_unrotated)
        
        # Apply rotation matrices step by step
        print("\nROTATION MATRIX CONSTRUCTION:")
        
        # X rotation
        print("\nX-AXIS ROTATION:")
        Rx = create_rotation_matrix_x(rotx_rad)
        
        # Y rotation  
        print("\nY-AXIS ROTATION:")
        Ry = create_rotation_matrix_y(roty_rad)
        
        # Z rotation
        print("\nZ-AXIS ROTATION:")
        Rz = create_rotation_matrix_z(rotz_rad)
        
        # Two-theta rotation (around Y axis for MOSFLM)
        print("\nTWO-THETA ROTATION:")
        twotheta_axis = torch.tensor([0.0, 1.0, 0.0], dtype=torch.float64)  # Y-axis for MOSFLM
        R_twotheta = create_twotheta_rotation_matrix(twotheta_rad, twotheta_axis)
        
        # Combined rotation matrix (order: rotx -> roty -> rotz -> twotheta)
        print("\nCOMBINED ROTATION MATRIX CONSTRUCTION:")
        
        # Step 1: Rx
        R1 = Rx
        trace_mat("R1_Rx", R1)
        
        # Step 2: Ry @ Rx
        R2 = torch.mm(Ry, R1)
        trace_mat("R2_Ry_Rx", R2)
        
        # Step 3: Rz @ Ry @ Rx
        R3 = torch.mm(Rz, R2)
        trace_mat("R3_Rz_Ry_Rx", R3)
        
        # Step 4: R_twotheta @ Rz @ Ry @ Rx
        R_combined = torch.mm(R_twotheta, R3)
        trace_mat("R_combined_final", R_combined)
        
        # Apply combined rotation to pix0
        print("\nAPPLYING ROTATION TO PIX0:")
        pix0_rotated = torch.mv(R_combined, pix0_unrotated)
        trace_vec("pix0_rotated_final", pix0_rotated)
        
        # Also calculate rotated basis vectors for verification
        print("\nROTATED BASIS VECTORS:")
        fdet_rotated = torch.mv(R_combined, fdet_init)
        sdet_rotated = torch.mv(R_combined, sdet_init)
        odet_rotated = torch.mv(R_combined, odet_init)
    
    trace_vec("fdet_rotated", fdet_rotated)
    trace_vec("sdet_rotated", sdet_rotated)
    trace_vec("odet_rotated", odet_rotated)
    
    # Verify orthonormality
    print("\nORTHONORMALITY VERIFICATION:")
    fdet_norm = torch.norm(fdet_rotated)
    sdet_norm = torch.norm(sdet_rotated)
    odet_norm = torch.norm(odet_rotated)
    
    trace_scalar("fdet_norm", fdet_norm)
    trace_scalar("sdet_norm", sdet_norm)
    trace_scalar("odet_norm", odet_norm)
    
    fdet_dot_sdet = torch.dot(fdet_rotated, sdet_rotated)
    fdet_dot_odet = torch.dot(fdet_rotated, odet_rotated)
    sdet_dot_odet = torch.dot(sdet_rotated, odet_rotated)
    
    trace_scalar("fdet_dot_sdet", fdet_dot_sdet)
    trace_scalar("fdet_dot_odet", fdet_dot_odet)
    trace_scalar("sdet_dot_odet", sdet_dot_odet)
    
    # Compare with Detector class implementation
    print("\nCOMPARISON WITH DETECTOR CLASS:")
    detector = Detector(config)
    
    trace_vec("detector_fdet_vec", detector.fdet_vec)
    trace_vec("detector_sdet_vec", detector.sdet_vec) 
    trace_vec("detector_odet_vec", detector.odet_vec)
    trace_vec("detector_pix0_vector", detector.pix0_vector)
    
    # Calculate differences
    print("\nDIFFERENCE ANALYSIS:")
    fdet_diff = fdet_rotated - detector.fdet_vec
    sdet_diff = sdet_rotated - detector.sdet_vec
    odet_diff = odet_rotated - detector.odet_vec
    pix0_diff = pix0_rotated - detector.pix0_vector
    
    trace_vec("fdet_difference", fdet_diff)
    trace_vec("sdet_difference", sdet_diff)
    trace_vec("odet_difference", odet_diff)
    trace_vec("pix0_difference", pix0_diff)
    
    trace_scalar("fdet_diff_norm", torch.norm(fdet_diff))
    trace_scalar("sdet_diff_norm", torch.norm(sdet_diff))
    trace_scalar("odet_diff_norm", torch.norm(odet_diff))
    trace_scalar("pix0_diff_norm", torch.norm(pix0_diff))
    
    print("\n" + "=" * 80)
    print("PIX0 DETAILED TRACE COMPLETE")
    print("=" * 80)
    print("\nKey values to compare with C implementation:")
    print(f"  pix0_vector: [{pix0_rotated[0]:.15g}, {pix0_rotated[1]:.15g}, {pix0_rotated[2]:.15g}]")
    print(f"  Expected C:  [0.09523, 0.05882, -0.05170] (from problem statement)")
    
    return pix0_rotated


def main():
    """Run the ultra-detailed pix0 calculation trace."""
    pix0_result = trace_pix0_calculation_step_by_step()


if __name__ == "__main__":
    main()