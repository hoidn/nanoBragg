#!/usr/bin/env python3
"""
Trace pixel (512, 512) through the entire nanoBragg pipeline to identify divergence from C code.

This script generates detailed traces matching the C implementation format for debugging
the detector geometry correlation issue (0.040 vs target >0.999 for tilted configurations).
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
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.config import (
    DetectorConfig, CrystalConfig, DetectorPivot, DetectorConvention
)
from nanobrag_torch.utils.units import degrees_to_radians


def trace_vec(tag: str, vec: torch.Tensor, prefix: str = "TRACE_PY"):
    """Print a vector in the same format as C trace."""
    if vec.dim() == 0:
        print(f"{prefix}:{tag}={vec.item():.15g}")
    else:
        values = " ".join(f"{v:.15g}" for v in vec.cpu().numpy())
        print(f"{prefix}:{tag}={values}")


def trace_scalar(tag: str, val: float, prefix: str = "TRACE_PY"):
    """Print a scalar in the same format as C trace."""
    if isinstance(val, torch.Tensor):
        val = val.item()
    print(f"{prefix}:{tag}={val:.15g}")


def trace_mat(tag: str, mat: torch.Tensor, prefix: str = "TRACE_PY"):
    """Print a matrix in the same format as C trace."""
    m = mat.cpu().numpy()
    vals = []
    for i in range(3):
        for j in range(3):
            vals.append(f"{m[i,j]:.15g}")
    mat_str = "[" + " ".join(vals[:3]) + "; " + " ".join(vals[3:6]) + "; " + " ".join(vals[6:]) + "]"
    print(f"{prefix}:{tag}={mat_str}")


def main():
    # Configuration matching the tilted detector case from fixplan
    detector_config = DetectorConfig(
        distance_mm=100.0,
        beam_center_s=51.2,  # This maps to Xbeam in C (MOSFLM convention)
        beam_center_f=51.2,  # This maps to Ybeam in C (MOSFLM convention)
        detector_rotx_deg=5.0,
        detector_roty_deg=3.0,
        detector_rotz_deg=2.0,
        detector_twotheta_deg=20.0,
        detector_pivot=DetectorPivot.SAMPLE,  # Automatically set when twotheta != 0
        detector_convention=DetectorConvention.MOSFLM,
        pixel_size_mm=0.1,
        fpixels=1024,
        spixels=1024,
    )
    
    crystal_config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        default_F=100.0,
    )
    
    # Target pixel to trace
    target_s = 512
    target_f = 512
    
    print("=" * 80)
    print("PARALLEL TRACE: Pixel (512, 512) through nanoBragg pipeline")
    print("=" * 80)
    
    # Print configuration
    print("\nCONFIGURATION:")
    print(f"TRACE_PY:detector_convention={detector_config.detector_convention.value}")
    print(f"TRACE_PY:detector_pivot={detector_config.detector_pivot.value}")
    trace_scalar("distance_mm", detector_config.distance_mm)
    trace_scalar("beam_center_s", detector_config.beam_center_s)
    trace_scalar("beam_center_f", detector_config.beam_center_f)
    trace_scalar("pixel_size_mm", detector_config.pixel_size_mm)
    
    # Print rotation angles
    print("\nROTATION ANGLES (degrees):")
    trace_scalar("detector_rotx_deg", detector_config.detector_rotx_deg)
    trace_scalar("detector_roty_deg", detector_config.detector_roty_deg)
    trace_scalar("detector_rotz_deg", detector_config.detector_rotz_deg)
    trace_scalar("detector_twotheta_deg", detector_config.detector_twotheta_deg)
    
    # Convert to radians for internal use
    rotx_rad = degrees_to_radians(detector_config.detector_rotx_deg)
    roty_rad = degrees_to_radians(detector_config.detector_roty_deg)
    rotz_rad = degrees_to_radians(detector_config.detector_rotz_deg)
    twotheta_rad = degrees_to_radians(detector_config.detector_twotheta_deg)
    
    print("\nROTATION ANGLES (radians):")
    trace_scalar("detector_rotx_rad", rotx_rad)
    trace_scalar("detector_roty_rad", roty_rad)
    trace_scalar("detector_rotz_rad", rotz_rad)
    trace_scalar("detector_twotheta_rad", twotheta_rad)
    
    # Create detector
    print("\n" + "=" * 40)
    print("DETECTOR GEOMETRY CALCULATION")
    print("=" * 40)
    
    detector = Detector(detector_config)
    
    # Trace initial basis vectors (before rotation)
    print("\nINITIAL BASIS VECTORS (MOSFLM convention):")
    if detector_config.detector_convention == DetectorConvention.MOSFLM:
        initial_fdet = torch.tensor([0.0, 0.0, 1.0])
        initial_sdet = torch.tensor([0.0, -1.0, 0.0])
        initial_odet = torch.tensor([1.0, 0.0, 0.0])
    else:
        initial_fdet = torch.tensor([1.0, 0.0, 0.0])
        initial_sdet = torch.tensor([0.0, 1.0, 0.0])
        initial_odet = torch.tensor([0.0, 0.0, 1.0])
    
    trace_vec("initial_fdet", initial_fdet)
    trace_vec("initial_sdet", initial_sdet)
    trace_vec("initial_odet", initial_odet)
    
    # Trace rotated basis vectors
    print("\nROTATED BASIS VECTORS:")
    trace_vec("fdet_vec", detector.fdet_vec)
    trace_vec("sdet_vec", detector.sdet_vec)
    trace_vec("odet_vec", detector.odet_vec)
    
    # Trace pix0_vector calculation
    print("\nPIX0_VECTOR CALCULATION:")
    if detector_config.detector_pivot == DetectorPivot.SAMPLE:
        print("TRACE_PY:pivot_mode=SAMPLE (calculate pix0 BEFORE rotations, then rotate)")
        # Show the unrotated pix0 calculation
        Fclose = (detector_config.beam_center_f + 0.5) * detector_config.pixel_size_mm / 1000.0
        Sclose = (detector_config.beam_center_s + 0.5) * detector_config.pixel_size_mm / 1000.0
        trace_scalar("Fclose_m", Fclose)
        trace_scalar("Sclose_m", Sclose)
        trace_scalar("distance_m", detector_config.distance_mm / 1000.0)
        
        # Calculate unrotated pix0
        pix0_unrotated = (
            -Fclose * initial_fdet
            - Sclose * initial_sdet
            + (detector_config.distance_mm / 1000.0) * initial_odet
        )
        trace_vec("pix0_unrotated", pix0_unrotated)
    else:
        print("TRACE_PY:pivot_mode=BEAM (calculate pix0 AFTER rotations)")
        Fbeam = (detector_config.beam_center_f + 0.5) * detector_config.pixel_size_mm / 1000.0
        Sbeam = (detector_config.beam_center_s + 0.5) * detector_config.pixel_size_mm / 1000.0
        trace_scalar("Fbeam_m", Fbeam)
        trace_scalar("Sbeam_m", Sbeam)
    
    trace_vec("pix0_vector", detector.pix0_vector)
    
    # Calculate pixel (512, 512) position
    print(f"\nPIXEL ({target_s}, {target_f}) POSITION:")
    
    # Get all pixel coordinates
    pixel_coords = detector.get_pixel_coords()  # Shape: (spixels, fpixels, 3)
    
    # Extract target pixel coordinate
    pixel_pos_meters = pixel_coords[target_s, target_f]
    trace_vec("pixel_pos_meters", pixel_pos_meters)
    
    # Convert to Angstroms for physics calculations
    pixel_pos_angstroms = pixel_pos_meters * 1e10
    trace_vec("pixel_pos_angstroms", pixel_pos_angstroms)
    
    # Calculate scattering vector for this pixel
    print("\nSCATTERING VECTOR CALCULATION:")
    
    # Wavelength (hardcoded for test case)
    wavelength_A = 6.2
    trace_scalar("wavelength_A", wavelength_A)
    
    # Incident beam vector (along +X in MOSFLM)
    k_incident = torch.tensor([1.0, 0.0, 0.0]) * (2 * np.pi / wavelength_A)
    trace_vec("k_incident", k_incident)
    
    # Scattered beam vector (from origin to pixel)
    pixel_distance = torch.norm(pixel_pos_angstroms)
    k_scattered = (pixel_pos_angstroms / pixel_distance) * (2 * np.pi / wavelength_A)
    trace_vec("k_scattered", k_scattered)
    
    # Scattering vector S = k_scattered - k_incident
    S_vector = k_scattered - k_incident
    trace_vec("S_vector", S_vector)
    
    # Create crystal and calculate Miller indices
    print("\n" + "=" * 40)
    print("CRYSTAL LATTICE CALCULATION")
    print("=" * 40)
    
    crystal = Crystal(crystal_config)
    
    # Trace real-space lattice vectors
    print("\nREAL-SPACE LATTICE VECTORS (Angstroms):")
    trace_vec("a_vec", crystal.a)
    trace_vec("b_vec", crystal.b)
    trace_vec("c_vec", crystal.c)
    
    # Trace reciprocal lattice vectors
    print("\nRECIPROCAL LATTICE VECTORS (1/Angstroms):")
    trace_vec("a_star", crystal.a_star)
    trace_vec("b_star", crystal.b_star)
    trace_vec("c_star", crystal.c_star)
    
    # Calculate Miller indices using non-standard convention
    print("\nMILLER INDEX CALCULATION (h = S·a convention):")
    h = torch.dot(S_vector, crystal.a)
    k = torch.dot(S_vector, crystal.b)
    l = torch.dot(S_vector, crystal.c)
    
    trace_scalar("h_index", h)
    trace_scalar("k_index", k)
    trace_scalar("l_index", l)
    
    # Round to nearest integer
    h_int = torch.round(h)
    k_int = torch.round(k)
    l_int = torch.round(l)
    
    trace_scalar("h_rounded", h_int)
    trace_scalar("k_rounded", k_int)
    trace_scalar("l_rounded", l_int)
    
    # Calculate structure factor (simplified)
    print("\nSTRUCTURE FACTOR:")
    F_hkl = crystal_config.default_F  # Simplified - using default
    trace_scalar("F_hkl", F_hkl)
    
    # Calculate intensity (simplified)
    print("\nINTENSITY CALCULATION:")
    intensity = F_hkl * F_hkl  # |F|^2
    trace_scalar("intensity", intensity)
    
    print("\n" + "=" * 80)
    print("TRACE COMPLETE")
    print("=" * 80)
    print("\nTo compare with C trace, run:")
    print("  1. Add matching trace statements to nanoBragg.c")
    print("  2. Run: ./nanoBragg [params] -trace_pixel 512 512 2>&1 | grep TRACE_C > c_trace.log")
    print("  3. Run: python trace_pixel_512_512.py > py_trace.log")
    print("  4. Compare: diff c_trace.log py_trace.log")


if __name__ == "__main__":
    main()