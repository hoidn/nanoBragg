#!/usr/bin/env python3
"""
Compare peak locations between C and PyTorch outputs.
"""
import numpy as np
from pathlib import Path

# Load images
c_img = np.fromfile("../phase_c/parity/c_img.bin", dtype=np.float32).reshape(2527, 2463)
torch_img = np.fromfile("../phase_c/parity/torch_img.bin", dtype=np.float32).reshape(2527, 2463)

# Find peaks
c_peak_idx = np.unravel_index(np.argmax(c_img), c_img.shape)
torch_peak_idx = np.unravel_index(np.argmax(torch_img), torch_img.shape)

print("="*80)
print("PEAK LOCATION COMPARISON")
print("="*80)
print(f"\nC peak:")
print(f"  Location: (slow={c_peak_idx[0]}, fast={c_peak_idx[1]})")
print(f"  Intensity: {c_img[c_peak_idx]:.6e}")

print(f"\nPyTorch peak:")
print(f"  Location: (slow={torch_peak_idx[0]}, fast={torch_peak_idx[1]})")
print(f"  Intensity: {torch_img[torch_peak_idx]:.6e}")

print(f"\nPeak displacement:")
print(f"  Δ slow: {torch_peak_idx[0] - c_peak_idx[0]} pixels")
print(f"  Δ fast: {torch_peak_idx[1] - c_peak_idx[1]} pixels")
print(f"  Distance: {np.sqrt((torch_peak_idx[0]-c_peak_idx[0])**2 + (torch_peak_idx[1]-c_peak_idx[1])**2):.1f} pixels")

# Check what PyTorch has at C peak location
torch_at_c_peak = torch_img[c_peak_idx]
c_at_torch_peak = c_img[torch_peak_idx]

print(f"\nCross-check:")
print(f"  PyTorch intensity at C peak location: {torch_at_c_peak:.6e}")
print(f"  C intensity at PyTorch peak location: {c_at_torch_peak:.6e}")

# Count non-zero pixels
c_nonzero = np.count_nonzero(c_img)
torch_nonzero = np.count_nonzero(torch_img)
print(f"\nNon-zero pixels:")
print(f"  C: {c_nonzero:,} ({100*c_nonzero/c_img.size:.2f}%)")
print(f"  PyTorch: {torch_nonzero:,} ({100*torch_nonzero/torch_img.size:.2f}%)")

# Look at top 10 peaks
print(f"\nTop 10 C peaks:")
c_flat = c_img.flatten()
c_top10_idx = np.argsort(c_flat)[-10:][::-1]
for rank, idx in enumerate(c_top10_idx, 1):
    s, f = np.unravel_index(idx, c_img.shape)
    print(f"  #{rank}: ({s:4d}, {f:4d}) = {c_flat[idx]:.3e}")

print(f"\nTop 10 PyTorch peaks:")
torch_flat = torch_img.flatten()
torch_top10_idx = np.argsort(torch_flat)[-10:][::-1]
for rank, idx in enumerate(torch_top10_idx, 1):
    s, f = np.unravel_index(idx, torch_img.shape)
    print(f"  #{rank}: ({s:4d}, {f:4d}) = {torch_flat[idx]:.3e}")
