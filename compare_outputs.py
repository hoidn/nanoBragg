#!/usr/bin/env python
"""Compare C and PyTorch outputs."""

import numpy as np
import matplotlib.pyplot as plt

# Load the binary files
with open('c_output.bin', 'rb') as f:
    c_data = np.frombuffer(f.read(), dtype=np.float32)
    c_image = c_data.reshape(64, 64)

with open('pytorch_output.bin', 'rb') as f:
    pytorch_data = np.frombuffer(f.read(), dtype=np.float32)
    pytorch_image = pytorch_data.reshape(64, 64)

# Find peak positions
c_peak_idx = np.unravel_index(np.argmax(c_image), c_image.shape)
pytorch_peak_idx = np.unravel_index(np.argmax(pytorch_image), pytorch_image.shape)

print("C version:")
print(f"  Max intensity: {c_image.max():.6f} at pixel {c_peak_idx}")
print(f"  Mean: {c_image.mean():.6f}")
print(f"  RMS: {np.sqrt(np.mean(c_image**2)):.6f}")
print(f"  Total intensity: {c_image.sum():.6f}")

print("\nPyTorch version:")
print(f"  Max intensity: {pytorch_image.max():.6f} at pixel {pytorch_peak_idx}")
print(f"  Mean: {pytorch_image.mean():.6f}")
print(f"  RMS: {np.sqrt(np.mean(pytorch_image**2)):.6f}")
print(f"  Total intensity: {pytorch_image.sum():.6f}")

# Compute correlation
correlation = np.corrcoef(c_image.flatten(), pytorch_image.flatten())[0, 1]
print(f"\nCorrelation: {correlation:.6f}")

# Compute difference
diff = pytorch_image - c_image
print(f"\nDifference stats:")
print(f"  Max diff: {np.abs(diff).max():.6f}")
print(f"  Mean diff: {diff.mean():.6f}")
print(f"  RMS diff: {np.sqrt(np.mean(diff**2)):.6f}")

# Create comparison plot
fig, axes = plt.subplots(2, 3, figsize=(15, 10))

# C output
im1 = axes[0, 0].imshow(c_image, origin='lower', cmap='hot')
axes[0, 0].set_title(f'C Output\nMax={c_image.max():.3f} at {c_peak_idx}')
axes[0, 0].plot(c_peak_idx[1], c_peak_idx[0], 'c+', markersize=10)
fig.colorbar(im1, ax=axes[0, 0])

# PyTorch output
im2 = axes[0, 1].imshow(pytorch_image, origin='lower', cmap='hot')
axes[0, 1].set_title(f'PyTorch Output\nMax={pytorch_image.max():.3f} at {pytorch_peak_idx}')
axes[0, 1].plot(pytorch_peak_idx[1], pytorch_peak_idx[0], 'c+', markersize=10)
fig.colorbar(im2, ax=axes[0, 1])

# Difference
im3 = axes[0, 2].imshow(diff, origin='lower', cmap='RdBu', vmin=-np.abs(diff).max(), vmax=np.abs(diff).max())
axes[0, 2].set_title(f'Difference (PyTorch - C)\nMax abs diff={np.abs(diff).max():.3f}')
fig.colorbar(im3, ax=axes[0, 2])

# Log scale plots
c_log = np.log10(np.maximum(c_image, 1e-10))
pytorch_log = np.log10(np.maximum(pytorch_image, 1e-10))

im4 = axes[1, 0].imshow(c_log, origin='lower', cmap='hot')
axes[1, 0].set_title('C Output (log scale)')
fig.colorbar(im4, ax=axes[1, 0])

im5 = axes[1, 1].imshow(pytorch_log, origin='lower', cmap='hot')
axes[1, 1].set_title('PyTorch Output (log scale)')
fig.colorbar(im5, ax=axes[1, 1])

# Scatter plot
axes[1, 2].scatter(c_image.flatten(), pytorch_image.flatten(), alpha=0.5, s=1)
axes[1, 2].plot([0, c_image.max()], [0, c_image.max()], 'r--', alpha=0.5)
axes[1, 2].set_xlabel('C Output')
axes[1, 2].set_ylabel('PyTorch Output')
axes[1, 2].set_title(f'Correlation: {correlation:.4f}')
axes[1, 2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('comparison.png', dpi=150)
print("\nSaved comparison plot to comparison.png")

# Check peak position difference
peak_diff_pixels = np.sqrt((c_peak_idx[0] - pytorch_peak_idx[0])**2 +
                           (c_peak_idx[1] - pytorch_peak_idx[1])**2)
print(f"\nPeak position difference: {peak_diff_pixels:.1f} pixels")
if peak_diff_pixels <= 2:
    print("✓ Peak positions agree within spec tolerance (≤2 pixels)")
else:
    print("✗ Peak positions differ by more than spec tolerance (>2 pixels)")

# Check correlation
if correlation > 0.95:
    print(f"✓ Correlation {correlation:.4f} meets spec requirement (>0.95)")
else:
    print(f"✗ Correlation {correlation:.4f} below spec requirement (<0.95)")