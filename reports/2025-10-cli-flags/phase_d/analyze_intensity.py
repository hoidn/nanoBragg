#!/usr/bin/env python3
"""
Phase D3 Intensity Gap Analysis
Compares C and PyTorch float images to diagnose the 257.7× intensity scaling discrepancy.
"""
import numpy as np
import json
from pathlib import Path

# Load float images
c_path = Path("../phase_c/parity/c_img.bin")
torch_path = Path("../phase_c/parity/torch_img.bin")

print("Loading float images...")
c_img = np.fromfile(c_path, dtype=np.float32)
torch_img = np.fromfile(torch_path, dtype=np.float32)

print(f"C image size: {len(c_img)} floats ({c_path.stat().st_size} bytes)")
print(f"PyTorch image size: {len(torch_img)} floats ({torch_path.stat().st_size} bytes)")

# Expected shape: 2463 × 2527 = 6,224,001 pixels
expected_size = 2463 * 2527
if len(c_img) == expected_size:
    shape = (2527, 2463)  # slow, fast
    c_img = c_img.reshape(shape)
    torch_img = torch_img.reshape(shape)
    print(f"Reshaped to {shape} (slow, fast)")
else:
    print(f"WARNING: Expected {expected_size} pixels, got {len(c_img)}")

# Compute statistics
stats = {
    "c": {
        "max": float(np.max(c_img)),
        "min": float(np.min(c_img)),
        "mean": float(np.mean(c_img)),
        "std": float(np.std(c_img)),
        "sum": float(np.sum(c_img)),
        "l2_norm": float(np.linalg.norm(c_img))
    },
    "pytorch": {
        "max": float(np.max(torch_img)),
        "min": float(np.min(torch_img)),
        "mean": float(np.mean(torch_img)),
        "std": float(np.std(torch_img)),
        "sum": float(np.sum(torch_img)),
        "l2_norm": float(np.linalg.norm(torch_img))
    },
    "ratios": {
        "max_ratio": float(np.max(torch_img) / np.max(c_img)),
        "mean_ratio": float(np.mean(torch_img) / np.mean(c_img)),
        "sum_ratio": float(np.sum(torch_img) / np.sum(c_img)),
        "l2_ratio": float(np.linalg.norm(torch_img) / np.linalg.norm(c_img))
    },
    "correlation": float(np.corrcoef(c_img.flatten(), torch_img.flatten())[0, 1])
}

# Print results
print("\n" + "="*80)
print("INTENSITY GAP ANALYSIS")
print("="*80)
print("\nC Implementation:")
print(f"  Max:      {stats['c']['max']:.6e}")
print(f"  Min:      {stats['c']['min']:.6e}")
print(f"  Mean:     {stats['c']['mean']:.6e}")
print(f"  Std Dev:  {stats['c']['std']:.6e}")
print(f"  Sum:      {stats['c']['sum']:.6e}")
print(f"  L2 Norm:  {stats['c']['l2_norm']:.6e}")

print("\nPyTorch Implementation:")
print(f"  Max:      {stats['pytorch']['max']:.6e}")
print(f"  Min:      {stats['pytorch']['min']:.6e}")
print(f"  Mean:     {stats['pytorch']['mean']:.6e}")
print(f"  Std Dev:  {stats['pytorch']['std']:.6e}")
print(f"  Sum:      {stats['pytorch']['sum']:.6e}")
print(f"  L2 Norm:  {stats['pytorch']['l2_norm']:.6e}")

print("\nRatios (PyTorch / C):")
print(f"  Max ratio:   {stats['ratios']['max_ratio']:.6f}×")
print(f"  Mean ratio:  {stats['ratios']['mean_ratio']:.6f}×")
print(f"  Sum ratio:   {stats['ratios']['sum_ratio']:.6f}×")
print(f"  L2 ratio:    {stats['ratios']['l2_ratio']:.6f}×")
print(f"  Correlation: {stats['correlation']:.8f}")

# Check against known parameters
print("\n" + "="*80)
print("HYPOTHESIS: Missing Normalization Factor?")
print("="*80)
print("\nKnown parameters from C log:")
print("  phi_steps = 10")
print("  sources = 1")
print("  mosaic_domains = 1")
print("  oversample = 1×1 = 1")
print(f"\nObserved ratio: {stats['ratios']['max_ratio']:.2f}×")
print(f"Expected steps divisor (sources × phi × mosaic × oversample²): 1 × 10 × 1 × 1 = 10")
print(f"Ratio/10 = {stats['ratios']['max_ratio']/10:.2f}× (remaining unexplained factor)")

# Check for other patterns
print("\nOther potential factors:")
print(f"  Ratio ≈ oversample⁴? {stats['ratios']['max_ratio']:.2f} vs 1 (no)")
print(f"  Ratio ≈ pixel_count factor? {stats['ratios']['max_ratio']:.2f} vs 1 (no)")
print(f"  Ratio ≈ 256 = 2⁸? {stats['ratios']['max_ratio']:.2f} vs 256 (close!)")

# Save JSON
output_path = Path("intensity_gap_stats.json")
with open(output_path, 'w') as f:
    json.dump(stats, f, indent=2)
print(f"\n✓ Saved statistics to {output_path}")

print("\n" + "="*80)
print("ROI Peak Analysis (10×10 window around C peak)")
print("="*80)

# Find C peak location
c_max_idx = np.unravel_index(np.argmax(c_img), c_img.shape)
print(f"C peak at pixel (slow={c_max_idx[0]}, fast={c_max_idx[1]}): {c_img[c_max_idx]:.6e}")

# Extract 10×10 ROI around C peak
roi_size = 10
s_start = max(0, c_max_idx[0] - roi_size//2)
s_end = min(shape[0], c_max_idx[0] + roi_size//2)
f_start = max(0, c_max_idx[1] - roi_size//2)
f_end = min(shape[1], c_max_idx[1] + roi_size//2)

c_roi = c_img[s_start:s_end, f_start:f_end]
torch_roi = torch_img[s_start:s_end, f_start:f_end]

print(f"ROI: slow[{s_start}:{s_end}], fast[{f_start}:{f_end}]")
print(f"  C ROI max:      {np.max(c_roi):.6e}")
print(f"  PyTorch ROI max: {np.max(torch_roi):.6e}")
print(f"  ROI max ratio:  {np.max(torch_roi)/np.max(c_roi):.6f}×")
print(f"  ROI mean ratio: {np.mean(torch_roi)/np.mean(c_roi):.6f}×")

# Per-pixel residual histogram
residuals = torch_roi.flatten() - c_roi.flatten()
print(f"\nROI residuals:")
print(f"  Mean Δ:  {np.mean(residuals):.6e}")
print(f"  Std Δ:   {np.std(residuals):.6e}")
print(f"  Max |Δ|: {np.max(np.abs(residuals)):.6e}")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print(f"The intensity gap is approximately {stats['ratios']['max_ratio']:.1f}×.")
print("This is suspiciously close to 256 = 2⁸.")
print("Potential causes:")
print("  1. Missing phi_steps normalization in PyTorch (factor of 10)")
print("  2. Additional oversample² factor not being applied (though oversample=1)")
print("  3. Byte-order or dtype conversion artifact (256 = 2⁸)")
print("  4. Different fluence/r_e²/solid-angle normalization")
print("  5. Missing ADC offset in C but applied in PyTorch")
print("\nNeed to:")
print("  - Compare simulator normalization code (steps divisor)")
print("  - Check fluence/r_e² scaling factors")
print("  - Review solid angle calculation")
print("  - Trace one pixel through both implementations")
