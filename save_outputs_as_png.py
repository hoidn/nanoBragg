#!/usr/bin/env python
"""Save C and PyTorch outputs as PNG images."""

import numpy as np
import matplotlib.pyplot as plt

# Load the binary files
with open('c_output.bin', 'rb') as f:
    c_data = np.frombuffer(f.read(), dtype=np.float32)
    c_image = c_data.reshape(64, 64)

with open('pytorch_output.bin', 'rb') as f:
    pytorch_data = np.frombuffer(f.read(), dtype=np.float32)
    pytorch_image = pytorch_data.reshape(64, 64)

# Save C output
plt.figure(figsize=(8, 8))
plt.imshow(c_image, origin='lower', cmap='hot')
plt.colorbar(label='Intensity')
plt.title(f'C Output (Max={c_image.max():.3f})')
c_peak = np.unravel_index(np.argmax(c_image), c_image.shape)
plt.plot(c_peak[1], c_peak[0], 'c+', markersize=15, markeredgewidth=2)
plt.xlabel('Fast axis (pixels)')
plt.ylabel('Slow axis (pixels)')
plt.tight_layout()
plt.savefig('tmp/c_output.png', dpi=150)
plt.close()

# Save PyTorch output
plt.figure(figsize=(8, 8))
plt.imshow(pytorch_image, origin='lower', cmap='hot')
plt.colorbar(label='Intensity')
plt.title(f'PyTorch Output (Max={pytorch_image.max():.3f})')
pytorch_peak = np.unravel_index(np.argmax(pytorch_image), pytorch_image.shape)
plt.plot(pytorch_peak[1], pytorch_peak[0], 'c+', markersize=15, markeredgewidth=2)
plt.xlabel('Fast axis (pixels)')
plt.ylabel('Slow axis (pixels)')
plt.tight_layout()
plt.savefig('tmp/pytorch_output.png', dpi=150)
plt.close()

# Save difference map
diff = pytorch_image - c_image
plt.figure(figsize=(8, 8))
plt.imshow(diff, origin='lower', cmap='RdBu', vmin=-np.abs(diff).max(), vmax=np.abs(diff).max())
plt.colorbar(label='Intensity difference')
plt.title(f'Difference (PyTorch - C)\nMax abs diff={np.abs(diff).max():.3f}')
plt.xlabel('Fast axis (pixels)')
plt.ylabel('Slow axis (pixels)')
plt.tight_layout()
plt.savefig('tmp/difference.png', dpi=150)
plt.close()

print("Saved images to tmp/:")
print("  - c_output.png")
print("  - pytorch_output.png")
print("  - difference.png")
print("  - comparison.png (already there)")
print(f"\nCorrelation between C and PyTorch: {np.corrcoef(c_image.flatten(), pytorch_image.flatten())[0, 1]:.4f}")