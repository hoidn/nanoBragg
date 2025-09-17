#!/usr/bin/env python3
"""
Detailed Python trace script to compare with C implementation
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.simulator import Simulator
from src.nanobrag_torch.config import (
    DetectorConfig, CrystalConfig, BeamConfig,
    DetectorConvention, DetectorPivot
)

print("=== PYTHON DETAILED TRACE ===")

# Configuration matching C test
detector_config = DetectorConfig(
    distance_mm=100.0,
    pixel_size_mm=0.1,
    spixels=1024,
    fpixels=1024,
    beam_center_s=51.2,  # Match C exactly
    beam_center_f=51.2,  # Match C exactly  
    detector_rotx_deg=5.0,
    detector_roty_deg=3.0,
    detector_rotz_deg=2.0,
    detector_twotheta_deg=15.0,
    detector_convention=DetectorConvention.MOSFLM,
    detector_pivot=DetectorPivot.BEAM
)

crystal_config = CrystalConfig(
    cell_a=100.0,
    cell_b=100.0,
    cell_c=100.0,
    cell_alpha=90.0,
    cell_beta=90.0,
    cell_gamma=90.0,
    N_cells=(5, 5, 5)
)

beam_config = BeamConfig(
    wavelength_A=6.2
)

print("TRACE_PY:=== Configuration ===")
print(f"TRACE_PY:detector_convention=MOSFLM")
print(f"TRACE_PY:distance_mm={detector_config.distance_mm}")
print(f"TRACE_PY:pixel_size_mm={detector_config.pixel_size_mm}")
print(f"TRACE_PY:beam_center_s={detector_config.beam_center_s}")
print(f"TRACE_PY:beam_center_f={detector_config.beam_center_f}")
print(f"TRACE_PY:detector_rotx_deg={detector_config.detector_rotx_deg}")
print(f"TRACE_PY:detector_roty_deg={detector_config.detector_roty_deg}")
print(f"TRACE_PY:detector_rotz_deg={detector_config.detector_rotz_deg}")
print(f"TRACE_PY:detector_twotheta_deg={detector_config.detector_twotheta_deg}")
print(f"TRACE_PY:convention={detector_config.detector_convention}")
print(f"TRACE_PY:pivot={detector_config.detector_pivot}")

# Convert to radians for comparison with C
rotx_rad = np.deg2rad(detector_config.detector_rotx_deg)
roty_rad = np.deg2rad(detector_config.detector_roty_deg)
rotz_rad = np.deg2rad(detector_config.detector_rotz_deg)
twotheta_rad = np.deg2rad(detector_config.detector_twotheta_deg)

print(f"TRACE_PY:angles_rad=rotx:{rotx_rad:.16g} roty:{roty_rad:.16g} rotz:{rotz_rad:.16g} twotheta:{twotheta_rad:.16g}")

# Beam center conversion (matching C MOSFLM convention)
beam_center_x_m = detector_config.beam_center_s * 1e-3  # mm to m
beam_center_y_m = detector_config.beam_center_f * 1e-3  # mm to m
print(f"TRACE_PY:beam_center_m=X:{beam_center_x_m:.3g} Y:{beam_center_y_m:.3g} pixel_mm:{detector_config.pixel_size_mm}")

# Create detector
detector = Detector(detector_config)

# Trace internal conversion
print(f"TRACE_PY:distance_m={detector.distance}")
print(f"TRACE_PY:pixel_size_m={detector.pixel_size}")
print(f"TRACE_PY:beam_center_s_pixels={detector.beam_center_s.item()}")
print(f"TRACE_PY:beam_center_f_pixels={detector.beam_center_f.item()}")

# Initial vectors (before rotations)
print(f"TRACE_PY:initial_fdet=0 0 1")
print(f"TRACE_PY:initial_sdet=0 -1 0") 
print(f"TRACE_PY:initial_odet=1 0 0")

# Get rotation matrices
rotx_rad_tensor = torch.tensor(rotx_rad)
roty_rad_tensor = torch.tensor(roty_rad)  
rotz_rad_tensor = torch.tensor(rotz_rad)

# Rotation matrices (same order as C)
def rotation_matrix_x(angle):
    cos_angle = torch.cos(angle)
    sin_angle = torch.sin(angle)
    return torch.tensor([
        [1., 0., 0.],
        [0., cos_angle, -sin_angle],
        [0., sin_angle, cos_angle]
    ], dtype=torch.float64)

def rotation_matrix_y(angle):
    cos_angle = torch.cos(angle)
    sin_angle = torch.sin(angle)
    return torch.tensor([
        [cos_angle, 0., sin_angle],
        [0., 1., 0.],
        [-sin_angle, 0., cos_angle]
    ], dtype=torch.float64)

def rotation_matrix_z(angle):
    cos_angle = torch.cos(angle)
    sin_angle = torch.sin(angle)
    return torch.tensor([
        [cos_angle, -sin_angle, 0.],
        [sin_angle, cos_angle, 0.],
        [0., 0., 1.]
    ], dtype=torch.float64)

Rx = rotation_matrix_x(rotx_rad_tensor)
Ry = rotation_matrix_y(roty_rad_tensor)
Rz = rotation_matrix_z(rotz_rad_tensor)

print("TRACE_PY:Rx=[{:.15g} {:.15g} {:.15g}; {:.15g} {:.15g} {:.15g}; {:.15g} {:.15g} {:.15g}]".format(
    Rx[0,0].item(), Rx[0,1].item(), Rx[0,2].item(),
    Rx[1,0].item(), Rx[1,1].item(), Rx[1,2].item(),
    Rx[2,0].item(), Rx[2,1].item(), Rx[2,2].item()))

print("TRACE_PY:Ry=[{:.15g} {:.15g} {:.15g}; {:.15g} {:.15g} {:.15g}; {:.15g} {:.15g} {:.15g}]".format(
    Ry[0,0].item(), Ry[0,1].item(), Ry[0,2].item(),
    Ry[1,0].item(), Ry[1,1].item(), Ry[1,2].item(),
    Ry[2,0].item(), Ry[2,1].item(), Ry[2,2].item()))

print("TRACE_PY:Rz=[{:.15g} {:.15g} {:.15g}; {:.15g} {:.15g} {:.15g}; {:.15g} {:.15g} {:.15g}]".format(
    Rz[0,0].item(), Rz[0,1].item(), Rz[0,2].item(),
    Rz[1,0].item(), Rz[1,1].item(), Rz[1,2].item(),
    Rz[2,0].item(), Rz[2,1].item(), Rz[2,2].item()))

# Combined rotation (X*Y*Z order, matching C)
R_total = torch.matmul(torch.matmul(Rx, Ry), Rz)
print("TRACE_PY:R_total=[{:.15g} {:.15g} {:.15g}; {:.15g} {:.15g} {:.15g}; {:.15g} {:.15g} {:.15g}]".format(
    R_total[0,0].item(), R_total[0,1].item(), R_total[0,2].item(),
    R_total[1,0].item(), R_total[1,1].item(), R_total[1,2].item(),
    R_total[2,0].item(), R_total[2,1].item(), R_total[2,2].item()))

# Trace basis vectors
print(f"TRACE_PY:fdet_vec={detector.fdet_vec.numpy()}")
print(f"TRACE_PY:sdet_vec={detector.sdet_vec.numpy()}")
print(f"TRACE_PY:odet_vec={detector.odet_vec.numpy()}")

print(f"TRACE_PY:fdet_after_rotz={detector.fdet_vec.numpy()}")
print(f"TRACE_PY:sdet_after_rotz={detector.sdet_vec.numpy()}")
print(f"TRACE_PY:odet_after_rotz={detector.odet_vec.numpy()}")

print(f"TRACE_PY:twotheta_axis=0 0 -1")
print(f"TRACE_PY:fdet_after_twotheta={detector.fdet_vec.numpy()}")
print(f"TRACE_PY:sdet_after_twotheta={detector.sdet_vec.numpy()}")
print(f"TRACE_PY:odet_after_twotheta={detector.odet_vec.numpy()}")

# Convention mapping
print(f"TRACE_PY:convention_mapping=Fbeam←Ybeam_mm(+0.5px),Sbeam←Xbeam_mm(+0.5px),beam_vec=[1 0 0]")

# Beam center in meters (MOSFLM convention: add 0.5 pixel)
Fbeam_m = (detector_config.beam_center_f + 0.5) * detector_config.pixel_size_mm * 1e-3
Sbeam_m = (detector_config.beam_center_s + 0.5) * detector_config.pixel_size_mm * 1e-3
print(f"TRACE_PY:Fbeam_m={Fbeam_m:.6g}")
print(f"TRACE_PY:Sbeam_m={Sbeam_m:.6g}")
print(f"TRACE_PY:distance_m={detector.distance:.6g}")

# Calculate terms for pix0_vector
# Matching C calculation exactly
distance_m = detector.distance
fdet_vec = detector.fdet_vec.numpy()
sdet_vec = detector.sdet_vec.numpy()

term_fast = -Fbeam_m * fdet_vec
term_slow = Sbeam_m * sdet_vec  
term_beam = np.array([distance_m, 0, 0])

print(f"TRACE_PY:term_fast={term_fast}")
print(f"TRACE_PY:term_slow={term_slow}")
print(f"TRACE_PY:term_beam={term_beam}")

pix0_calculated = term_beam + term_fast + term_slow
print(f"TRACE_PY:pix0_vector_calculated={pix0_calculated}")

# Trace pix0_vector
print(f"TRACE_PY:pix0_vector={detector.pix0_vector.numpy()}")

# Create crystal
crystal = Crystal(crystal_config)
print(f"TRACE_PY:cell_a={crystal.cell_a}")
print(f"TRACE_PY:cell_b={crystal.cell_b}")
print(f"TRACE_PY:cell_c={crystal.cell_c}")

# Trace reciprocal vectors
print(f"TRACE_PY:a_star={crystal.a_star.numpy()}")
print(f"TRACE_PY:b_star={crystal.b_star.numpy()}")
print(f"TRACE_PY:c_star={crystal.c_star.numpy()}")

# Get pixel coordinates for specific pixels (simplified)
coords = detector.get_pixel_coords()
test_pixels = [(0,0), (512,512), (1023,1023)]
for s,f in test_pixels:
    pos = coords[s,f].numpy()
    print(f"TRACE_PY:pixel({s},{f})_position={pos}")

print("TRACE_PY:=== End Python trace ===")