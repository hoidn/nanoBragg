#!/usr/bin/env python
"""
Generate PyTorch trace for pixel (128,128) @ 0.4mm pixel size.
Match C trace output format exactly for comparison.
"""
import os
import sys
sys.path.insert(0, '/home/ollie/Documents/nanoBragg')
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
from src.nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig, DetectorConvention
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.utils.physics import sincg

# Configuration: AT-PARALLEL-002 @ 0.4mm
detector_config = DetectorConfig(
    detector_convention=DetectorConvention.MOSFLM,
    distance_mm=100.0,
    pixel_size_mm=0.4,
    spixels=256,
    fpixels=256,
    beam_center_s=25.6,  # mm - MOSFLM adds +0.5px internally
    beam_center_f=25.6,  # mm
)

crystal_config = CrystalConfig(
    cell_a=100.0, cell_b=100.0, cell_c=100.0,
    cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
    N_cells=(5, 5, 5),
    default_F=100.0
)

beam_config = BeamConfig(
    wavelength_A=6.2
)

detector = Detector(detector_config)
crystal = Crystal(crystal_config)

# Trace pixel (128, 128) - slow=128, fast=128
s, f = 128, 128

print("PYTORCH_TRACE: Configuration")
print(f"PYTORCH_TRACE: pixel_size_mm={detector_config.pixel_size_mm}")
print(f"PYTORCH_TRACE: detpixels={detector_config.spixels}")
print(f"PYTORCH_TRACE: distance_mm={detector_config.distance_mm}")
print(f"PYTORCH_TRACE: beam_center_mm=({detector_config.beam_center_s}, {detector_config.beam_center_f})")
print(f"PYTORCH_TRACE: wavelength_A={beam_config.wavelength_A}")
print(f"PYTORCH_TRACE: N_cells={crystal_config.N_cells}")
print(f"PYTORCH_TRACE: default_F={crystal_config.default_F}")
print(f"PYTORCH_TRACE: trace_pixel=(s={s}, f={f})")
print()

# Get pixel coordinates
pixel_coords = detector.get_pixel_coords()
pixel_coord = pixel_coords[s, f]

print("PYTORCH_TRACE: Pixel Geometry")
print(f"PYTORCH_TRACE: pixel_pos_meters={pixel_coord.tolist()}")

R = torch.norm(pixel_coord)
print(f"PYTORCH_TRACE: R_distance_meters={R.item():.15e}")

# Solid angle
solid_angle = detector.get_solid_angle(pixel_coord.unsqueeze(0).unsqueeze(0))[0, 0]
print(f"PYTORCH_TRACE: omega_pixel_sr={solid_angle.item():.15e}")

close_distance = detector.close_distance.item()
obliquity = close_distance / R.item()
print(f"PYTORCH_TRACE: close_distance_meters={close_distance:.15e}")
print(f"PYTORCH_TRACE: obliquity_factor={obliquity:.15e}")
print()

# Scattering vectors
wavelength_m = beam_config.wavelength_A * 1e-10
k_in = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64) / wavelength_m
diffracted_unit = pixel_coord / R
k_out = diffracted_unit / wavelength_m
S_vector = (k_out - k_in) * 1e-10  # Convert to 1/Angstrom

print("PYTORCH_TRACE: Scattering")
print(f"PYTORCH_TRACE: diffracted_vec={diffracted_unit.tolist()}")
print(f"PYTORCH_TRACE: incident_vec=[1.0, 0.0, 0.0]")
print(f"PYTORCH_TRACE: lambda_meters={wavelength_m:.15e}")
print(f"PYTORCH_TRACE: scattering_vec_A_inv={S_vector.tolist()}")
print()

# Miller indices
(a_vec, b_vec, c_vec), (a_star, b_star, c_star) = crystal.get_rotated_real_vectors(crystal_config)
a_vec = a_vec.squeeze()
b_vec = b_vec.squeeze()
c_vec = c_vec.squeeze()

h = torch.dot(S_vector, a_vec)
k = torch.dot(S_vector, b_vec)
l = torch.dot(S_vector, c_vec)

h_int = torch.round(h).int().item()
k_int = torch.round(k).int().item()
l_int = torch.round(l).int().item()

print("PYTORCH_TRACE: Miller Indices")
print(f"PYTORCH_TRACE: hkl_frac=[{h.item():.15e}, {k.item():.15e}, {l.item():.15e}]")
print(f"PYTORCH_TRACE: hkl_rounded=[{h_int}, {k_int}, {l_int}]")
print()

# Lattice factors
h_frac = h - h_int
k_frac = k - k_int
l_frac = l - l_int

N_a, N_b, N_c = crystal_config.N_cells

F_latt_a = sincg(torch.pi * h_frac, torch.tensor(N_a, dtype=torch.float64))
F_latt_b = sincg(torch.pi * k_frac, torch.tensor(N_b, dtype=torch.float64))
F_latt_c = sincg(torch.pi * l_frac, torch.tensor(N_c, dtype=torch.float64))
F_latt = F_latt_a * F_latt_b * F_latt_c

print("PYTORCH_TRACE: Shape Factors")
print(f"PYTORCH_TRACE: F_latt_a={F_latt_a.item():.15e}")
print(f"PYTORCH_TRACE: F_latt_b={F_latt_b.item():.15e}")
print(f"PYTORCH_TRACE: F_latt_c={F_latt_c.item():.15e}")
print(f"PYTORCH_TRACE: F_latt={F_latt.item():.15e}")
print()

# Structure factor
F_cell = crystal_config.default_F
print(f"PYTORCH_TRACE: F_cell={F_cell:.15e}")
print()

# Intensity before scaling (physics only)
I_before_scaling = (F_cell ** 2) * (F_latt ** 2)
print("PYTORCH_TRACE: Physics Intensity")
print(f"PYTORCH_TRACE: I_before_scaling={I_before_scaling.item():.15e}")
print()

# Constants and scaling
r_e_m = 2.81794092e-15  # classical electron radius in meters
r_e_sqr = r_e_m ** 2
print(f"PYTORCH_TRACE: r_e_sqr={r_e_sqr:.15e}")

# Fluence: C code uses a default fluence calculation
# From C trace: fluence = 1.25932015286227e+29 photons/m^2
# Check if this matches our calculation
# C code: fluence = flux * exposure / (beamsize_x * beamsize_y)
# Default: flux=1e12, exposure=1, beamsize defaults give this fluence

# Try to match C's fluence calculation
# C defaults (from nanoBragg.c): flux=1e12, exposure=1, beamsize_x=beamsize_y=0 (special case)
# When beamsize=0, C uses: fluence = flux (no area normalization)
# But wait, C trace shows fluence=1.259e+29, which is > 1e12
# This suggests C is converting units somewhere

# From C code comments: fluence is in photons/m^2
# Default flux is 1e12 photons/s, exposure is 1s
# So raw fluence = 1e12 photons
# But C divides by beamsize area if beamsize > 0
# When beamsize=0, it seems to use a different calculation

# Let me check what PyTorch Simulator uses
from src.nanobrag_torch.simulator import Simulator
simulator = Simulator(crystal, detector, crystal_config, beam_config)

# The simulator computes fluence internally
# Let's check the defaults
print(f"PYTORCH_TRACE: beam_config.fluence (user)={beam_config.fluence}")
print(f"PYTORCH_TRACE: beam_config.flux={beam_config.flux}")
print(f"PYTORCH_TRACE: beam_config.exposure={beam_config.exposure}")
print(f"PYTORCH_TRACE: beam_config.beamsize_mm={beam_config.beamsize_mm}")
print()

# Compute fluence like C code does
if beam_config.fluence is not None:
    fluence = beam_config.fluence
else:
    # Default calculation
    if beam_config.flux > 0 and beam_config.exposure > 0:
        flux = beam_config.flux
        exposure = beam_config.exposure
        beamsize = beam_config.beamsize_mm
        if beamsize > 0:
            fluence = (flux * exposure) / (beamsize ** 2 * 1e-6)  # Convert mm² to m²
        else:
            # C uses a default beam area when beamsize=0
            # From C: default is 100µm x 100µm = 1e-8 m²
            fluence = (flux * exposure) / 1e-8
    else:
        fluence = 1e12  # fallback

print(f"PYTORCH_TRACE: fluence (computed)={fluence:.15e}")
print()

# Steps (for normalization)
# C code: steps = sources * phi_steps * mos_doms * oversample^2
# Our case: 1 source, 1 phi_step, 1 mos_dom, oversample=1
steps = 1
print(f"PYTORCH_TRACE: steps={steps}")
print()

# Final intensity (full scaling)
# C formula: I_pixel_final = r_e_sqr * fluence * I_before_scaling * omega / steps
I_pixel_final = r_e_sqr * fluence * I_before_scaling.item() * solid_angle.item() / steps
print("PYTORCH_TRACE: Final Intensity")
print(f"PYTORCH_TRACE: I_pixel_final={I_pixel_final:.15e}")
print()

# Run full simulation and check pixel value
image = simulator.run()
actual_value = image[s, f].item()
print("PYTORCH_TRACE: Simulation Result")
print(f"PYTORCH_TRACE: floatimage[{s},{f}]={actual_value:.15e}")
print()

# Compare to C trace
c_I_pixel_final = 141.897172586441
c_floatimage = 141.897171020508
py_floatimage = actual_value

ratio = py_floatimage / c_floatimage
error_pct = (ratio - 1.0) * 100

print("=== COMPARISON TO C TRACE ===")
print(f"C I_pixel_final: {c_I_pixel_final:.12f}")
print(f"C floatimage:    {c_floatimage:.12f}")
print(f"Py floatimage:   {py_floatimage:.12f}")
print(f"Ratio (Py/C):    {ratio:.12f}")
print(f"Error:           {error_pct:+.6f}%")
print()

if abs(ratio - 1.0) > 0.001:
    print("⚠️  DIVERGENCE DETECTED: PyTorch value differs by >0.1%")
    print("Checking intermediate values for first divergence...")
    print()

    # Check each component
    print("Component-by-component comparison:")
    print(f"  omega: C={1.330100955665e-05:.15e}, Py={solid_angle.item():.15e}")
    print(f"  close_distance: C={0.1:.15e}, Py={close_distance:.15e}")
    print(f"  R: C={0.106351868812917:.15e}, Py={R.item():.15e}")
    print(f"  F_latt: C={33.6515931996904:.15e}, Py={F_latt.item():.15e}")
    print(f"  F_cell: C={100:.15e}, Py={F_cell:.15e}")
    print(f"  I_before_scaling: C={11324297.2487745:.15e}, Py={I_before_scaling.item():.15e}")
    print(f"  r_e_sqr: C={7.94079248018965e-30:.15e}, Py={r_e_sqr:.15e}")
    print(f"  fluence: C={1.25932015286227e+29:.15e}, Py={fluence:.15e}")
    print(f"  steps: C={1}, Py={steps}")