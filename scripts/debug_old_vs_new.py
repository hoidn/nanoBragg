#!/usr/bin/env python3
"""Compare old and new pixel coordinate calculations."""

import os
import torch

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Parameters from default config
device = torch.device("cpu")
dtype = torch.float64
spixels = 1024
fpixels = 1024
beam_center_s = torch.tensor(512.0, device=device, dtype=dtype)  # in pixels
beam_center_f = torch.tensor(512.0, device=device, dtype=dtype)  # in pixels
pixel_size = torch.tensor(1000.0, device=device, dtype=dtype)  # in Angstroms
distance = torch.tensor(1000000.0, device=device, dtype=dtype)  # in Angstroms

# Basis vectors
fdet_vec = torch.tensor([0.0, 0.0, 1.0], device=device, dtype=dtype)
sdet_vec = torch.tensor([0.0, -1.0, 0.0], device=device, dtype=dtype)
odet_vec = torch.tensor([1.0, 0.0, 0.0], device=device, dtype=dtype)

# OLD METHOD (from original get_pixel_coords):
print("OLD METHOD:")
s_coords = torch.arange(spixels, device=device, dtype=dtype)
f_coords = torch.arange(fpixels, device=device, dtype=dtype)

# Convert to Angstroms relative to beam center
s_angstroms_old = (s_coords - beam_center_s) * pixel_size
f_angstroms_old = (f_coords - beam_center_f) * pixel_size

# For pixel (0,0)
print(f"Pixel (0,0) s offset: {s_angstroms_old[0]}")
print(f"Pixel (0,0) f offset: {f_angstroms_old[0]}")

# For pixel (512,512) - should be at beam center
print(f"Pixel (512,512) s offset: {s_angstroms_old[512]}")
print(f"Pixel (512,512) f offset: {f_angstroms_old[512]}")

detector_origin = distance * odet_vec
pixel_00_old = detector_origin + s_angstroms_old[0] * sdet_vec + f_angstroms_old[0] * fdet_vec
pixel_512_old = detector_origin + s_angstroms_old[512] * sdet_vec + f_angstroms_old[512] * fdet_vec

print(f"OLD: Pixel (0,0) position: {pixel_00_old}")
print(f"OLD: Pixel (512,512) position: {pixel_512_old}")

# NEW METHOD (using pix0_vector):
print("\nNEW METHOD:")
# Calculate pix0_vector
s_offset = (0.5 - beam_center_s) * pixel_size
f_offset = (0.5 - beam_center_f) * pixel_size
pix0_vector = detector_origin + s_offset * sdet_vec + f_offset * fdet_vec

print(f"pix0_vector: {pix0_vector}")

# For pixel (0,0)
pixel_00_new = pix0_vector + 0 * pixel_size * sdet_vec + 0 * pixel_size * fdet_vec
print(f"NEW: Pixel (0,0) position: {pixel_00_new}")

# For pixel (512,512)
pixel_512_new = pix0_vector + 512 * pixel_size * sdet_vec + 512 * pixel_size * fdet_vec
print(f"NEW: Pixel (512,512) position: {pixel_512_new}")

print("\nDIFFERENCES:")
print(f"Pixel (0,0) difference: {pixel_00_new - pixel_00_old}")
print(f"Pixel (512,512) difference: {pixel_512_new - pixel_512_old}")

# The issue is that the beam center calculation is different
print("\nANALYSIS:")
print("OLD: pixel position = origin + (index - beam_center) * pixel_size * basis")
print("NEW: pixel position = pix0 + index * pixel_size * basis")
print("     where pix0 = origin + (0.5 - beam_center) * pixel_size * basis")
print("")
print("The NEW method assumes pixels are centered at integer indices,")
print("while the OLD method assumes pixels edges are at integer indices.")