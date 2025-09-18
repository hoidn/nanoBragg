#!/usr/bin/env python
"""Analyze why correlation isn't perfect 1.0"""

import numpy as np
import matplotlib.pyplot as plt

# Load the binary files
with open('c_output.bin', 'rb') as f:
    c_data = np.frombuffer(f.read(), dtype=np.float32)
    c_image = c_data.reshape(64, 64)

with open('pytorch_output.bin', 'rb') as f:
    pytorch_data = np.frombuffer(f.read(), dtype=np.float32)
    pytorch_image = pytorch_data.reshape(64, 64)

# Compute difference
diff = pytorch_image - c_image

print("=== Analyzing Differences ===")
print(f"\nBasic Statistics:")
print(f"C image range: [{c_image.min():.6f}, {c_image.max():.6f}]")
print(f"PyTorch range: [{pytorch_image.min():.6f}, {pytorch_image.max():.6f}]")
print(f"Difference range: [{diff.min():.6f}, {diff.max():.6f}]")
print(f"Mean absolute difference: {np.abs(diff).mean():.6f}")
print(f"Max absolute difference: {np.abs(diff).max():.6f}")
print(f"Relative error (max): {(np.abs(diff).max() / c_image.max() * 100):.2f}%")

# Check if differences are systematic or random
print(f"\n=== Pattern Analysis ===")
print(f"Mean difference: {diff.mean():.6e} (should be ~0 if random)")
print(f"Std of difference: {diff.std():.6f}")

# Check where the largest differences occur
max_diff_idx = np.unravel_index(np.argmax(np.abs(diff)), diff.shape)
print(f"\nLargest difference at pixel {max_diff_idx}:")
print(f"  C value: {c_image[max_diff_idx]:.6f}")
print(f"  PyTorch value: {pytorch_image[max_diff_idx]:.6f}")
print(f"  Difference: {diff[max_diff_idx]:.6f}")

# Look at differences by intensity level
print(f"\n=== Differences by Intensity Level ===")
# Create bins based on C intensity
bins = [0, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
for i in range(len(bins)-1):
    mask = (c_image >= bins[i]) & (c_image < bins[i+1])
    if mask.any():
        mean_diff = diff[mask].mean()
        std_diff = diff[mask].std()
        max_diff = np.abs(diff[mask]).max()
        print(f"Intensity [{bins[i]:.1f}, {bins[i+1]:.1f}): mean diff={mean_diff:.6f}, std={std_diff:.6f}, max={max_diff:.6f}")

# Check for noise - compare multiple pixels with same expected value
print(f"\n=== Checking for Random Noise ===")
# Background pixels (should all be similar)
background_mask = c_image < 0.1
if background_mask.any():
    c_bg_values = c_image[background_mask]
    pytorch_bg_values = pytorch_image[background_mask]
    print(f"Background pixels (intensity < 0.1):")
    print(f"  C std: {c_bg_values.std():.6f}")
    print(f"  PyTorch std: {pytorch_bg_values.std():.6f}")
    print(f"  Unique C values: {len(np.unique(c_bg_values))}")
    print(f"  Unique PyTorch values: {len(np.unique(pytorch_bg_values))}")

# Check specific pixel values to see if they're identical
print(f"\n=== Sample Pixel Values ===")
print("Comparing 10 random pixels:")
np.random.seed(42)
for _ in range(10):
    i, j = np.random.randint(0, 64, 2)
    print(f"  [{i:2d},{j:2d}]: C={c_image[i,j]:.8f}, PyTorch={pytorch_image[i,j]:.8f}, diff={diff[i,j]:.8f}")

# Check if it's a numerical precision issue
print(f"\n=== Numerical Precision Analysis ===")
# Count how many values are exactly equal
exact_matches = (c_image == pytorch_image)
print(f"Pixels with exact match: {exact_matches.sum()} / {c_image.size} ({exact_matches.sum()/c_image.size*100:.1f}%)")

# Count how many are within float32 epsilon
epsilon = np.finfo(np.float32).eps
close_matches = np.abs(diff) < epsilon * np.maximum(np.abs(c_image), np.abs(pytorch_image))
print(f"Pixels within machine epsilon: {close_matches.sum()} / {c_image.size} ({close_matches.sum()/c_image.size*100:.1f}%)")

# Count within various tolerances
for tol in [1e-6, 1e-5, 1e-4, 1e-3, 1e-2]:
    within_tol = np.abs(diff) < tol
    print(f"Pixels within {tol:.0e}: {within_tol.sum()} / {c_image.size} ({within_tol.sum()/c_image.size*100:.1f}%)")

# Create a histogram of differences
plt.figure(figsize=(12, 4))

plt.subplot(1, 3, 1)
plt.hist(diff.flatten(), bins=50, edgecolor='black')
plt.xlabel('Difference (PyTorch - C)')
plt.ylabel('Count')
plt.title('Distribution of Differences')
plt.axvline(0, color='red', linestyle='--', alpha=0.5)

plt.subplot(1, 3, 2)
plt.hist(np.log10(np.abs(diff.flatten()) + 1e-10), bins=50, edgecolor='black')
plt.xlabel('log10(|Difference|)')
plt.ylabel('Count')
plt.title('Log Distribution of Absolute Differences')

plt.subplot(1, 3, 3)
relative_error = np.abs(diff) / (np.abs(c_image) + 1e-10)
plt.hist(np.log10(relative_error.flatten() + 1e-10), bins=50, edgecolor='black')
plt.xlabel('log10(Relative Error)')
plt.ylabel('Count')
plt.title('Log Distribution of Relative Errors')

plt.tight_layout()
plt.savefig('tmp/difference_analysis.png', dpi=150)
print(f"\nSaved difference analysis plots to tmp/difference_analysis.png")