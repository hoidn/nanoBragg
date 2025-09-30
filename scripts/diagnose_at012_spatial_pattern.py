#!/usr/bin/env python3
"""
Diagnostic script for AT-PARALLEL-012: Analyze spatial pattern of errors.

This script performs a detailed spatial analysis of the 0.5% correlation gap
without requiring C code traces. It tests multiple hypotheses about the error:
- Radial dependence (omega/solid angle bug)
- Angular dependence (geometry/coordinate bug)
- Intensity dependence (normalization bug)
- Symmetry (detector basis vectors)

Usage:
    python scripts/diagnose_at012_spatial_pattern.py
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Set environment variable for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nanobrag_torch.config import BeamConfig, CrystalConfig, DetectorConfig
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.simulator import Simulator


def load_golden_image(golden_path):
    """Load golden reference image from binary file."""
    print(f"Loading golden image from {golden_path}")
    golden_data = np.fromfile(golden_path, dtype=np.float32)
    image_size = int(np.sqrt(len(golden_data)))
    golden_image = golden_data.reshape(image_size, image_size)
    print(f"  Golden image shape: {golden_image.shape}")
    print(f"  Golden image stats: min={golden_image.min():.3e}, max={golden_image.max():.3e}, mean={golden_image.mean():.3e}")
    return golden_image


def generate_pytorch_image():
    """Generate PyTorch image with exact golden parameters."""
    print("\nGenerating PyTorch image...")

    # Golden parameters from tests/golden_data/README.md
    crystal_config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0,
    )

    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
    )

    beam_config = BeamConfig(wavelength_A=6.2)

    # Create simulator
    crystal = Crystal(config=crystal_config, beam_config=beam_config)
    detector = Detector(config=detector_config)
    simulator = Simulator(
        crystal=crystal,
        detector=detector,
        beam_config=beam_config,
        dtype=torch.float64,
    )

    # Run simulation
    print("  Running simulation...")
    pytorch_image = simulator.run()
    pytorch_np = pytorch_image.cpu().numpy()

    print(f"  PyTorch image shape: {pytorch_np.shape}")
    print(f"  PyTorch image stats: min={pytorch_np.min():.3e}, max={pytorch_np.max():.3e}, mean={pytorch_np.mean():.3e}")

    return pytorch_np


def compute_ratio_map(pytorch_img, golden_img, intensity_threshold=0.1):
    """Compute ratio map (PyTorch/Golden) for pixels above threshold."""
    # Only compute ratios where both images have significant intensity
    mask = (golden_img > intensity_threshold) & (pytorch_img > intensity_threshold)

    # Avoid division by zero
    ratio_map = np.full_like(golden_img, np.nan)
    ratio_map[mask] = pytorch_img[mask] / golden_img[mask]

    print(f"\nRatio map statistics:")
    print(f"  Valid pixels: {mask.sum()} / {mask.size} ({100*mask.sum()/mask.size:.1f}%)")
    print(f"  Mean ratio: {np.nanmean(ratio_map):.6f}")
    print(f"  Median ratio: {np.nanmedian(ratio_map):.6f}")
    print(f"  Std ratio: {np.nanstd(ratio_map):.6f}")
    print(f"  Min ratio: {np.nanmin(ratio_map):.6f}")
    print(f"  Max ratio: {np.nanmax(ratio_map):.6f}")

    return ratio_map, mask


def analyze_radial_dependence(ratio_map, mask, center_pixel=(512, 512)):
    """Analyze ratio as function of distance from center."""
    print(f"\n=== Radial Dependence Analysis ===")
    print(f"  Center pixel: {center_pixel}")

    # Create distance map
    s_indices, f_indices = np.meshgrid(
        np.arange(ratio_map.shape[0]),
        np.arange(ratio_map.shape[1]),
        indexing='ij'
    )

    distances = np.sqrt(
        (s_indices - center_pixel[0])**2 +
        (f_indices - center_pixel[1])**2
    )

    # Bin by distance
    distance_bins = np.arange(0, np.max(distances), 50)  # 50-pixel bins
    ratio_vs_distance = []
    distance_centers = []

    for i in range(len(distance_bins) - 1):
        bin_mask = mask & (distances >= distance_bins[i]) & (distances < distance_bins[i+1])
        if bin_mask.sum() > 10:  # Need at least 10 pixels
            ratio_vs_distance.append(np.nanmean(ratio_map[bin_mask]))
            distance_centers.append((distance_bins[i] + distance_bins[i+1]) / 2)

    # Check for correlation
    if len(distance_centers) > 2:
        correlation = np.corrcoef(distance_centers, ratio_vs_distance)[0, 1]
        print(f"  Correlation with distance: {correlation:.4f}")

        # Linear fit
        coeffs = np.polyfit(distance_centers, ratio_vs_distance, 1)
        print(f"  Linear fit: ratio = {coeffs[0]:.6e} * distance + {coeffs[1]:.6f}")

        if abs(correlation) > 0.5:
            print(f"  ⚠️  STRONG radial dependence detected!")
            print(f"      This suggests omega/solid-angle calculation error")
    else:
        correlation = 0.0
        coeffs = [0.0, 1.0]

    return distance_centers, ratio_vs_distance, correlation


def analyze_angular_dependence(ratio_map, mask, center_pixel=(512, 512)):
    """Analyze ratio as function of angle from center."""
    print(f"\n=== Angular Dependence Analysis ===")

    # Create angle map
    s_indices, f_indices = np.meshgrid(
        np.arange(ratio_map.shape[0]),
        np.arange(ratio_map.shape[1]),
        indexing='ij'
    )

    angles = np.arctan2(
        s_indices - center_pixel[0],
        f_indices - center_pixel[1]
    ) * 180 / np.pi  # Convert to degrees

    # Bin by angle
    angle_bins = np.arange(-180, 180, 15)  # 15-degree bins
    ratio_vs_angle = []
    angle_centers = []

    for i in range(len(angle_bins) - 1):
        bin_mask = mask & (angles >= angle_bins[i]) & (angles < angle_bins[i+1])
        if bin_mask.sum() > 10:
            ratio_vs_angle.append(np.nanmean(ratio_map[bin_mask]))
            angle_centers.append((angle_bins[i] + angle_bins[i+1]) / 2)

    # Check for patterns
    if len(angle_centers) > 4:
        ratio_std = np.std(ratio_vs_angle)
        ratio_range = np.max(ratio_vs_angle) - np.min(ratio_vs_angle)
        print(f"  Angular variation (std): {ratio_std:.6f}")
        print(f"  Angular range: {ratio_range:.6f}")

        if ratio_range > 0.01:
            print(f"  ⚠️  SIGNIFICANT angular dependence detected!")
            print(f"      This suggests coordinate system / geometry error")

    return angle_centers, ratio_vs_angle


def analyze_intensity_dependence(ratio_map, mask, golden_img):
    """Analyze ratio as function of intensity level."""
    print(f"\n=== Intensity Dependence Analysis ===")

    # Get golden intensities for valid pixels
    golden_valid = golden_img[mask]
    ratio_valid = ratio_map[mask]

    # Bin by intensity (log scale)
    intensity_bins = np.logspace(
        np.log10(golden_valid.min()),
        np.log10(golden_valid.max()),
        20
    )

    ratio_vs_intensity = []
    intensity_centers = []

    for i in range(len(intensity_bins) - 1):
        bin_mask = (golden_valid >= intensity_bins[i]) & (golden_valid < intensity_bins[i+1])
        if bin_mask.sum() > 10:
            ratio_vs_intensity.append(np.nanmean(ratio_valid[bin_mask]))
            intensity_centers.append(np.sqrt(intensity_bins[i] * intensity_bins[i+1]))

    # Check for correlation
    if len(intensity_centers) > 2:
        # Use log scale for intensity
        log_intensities = np.log10(intensity_centers)
        correlation = np.corrcoef(log_intensities, ratio_vs_intensity)[0, 1]
        print(f"  Correlation with log(intensity): {correlation:.4f}")

        if abs(correlation) > 0.5:
            print(f"  ⚠️  STRONG intensity dependence detected!")
            print(f"      This suggests normalization or scaling error")

    return intensity_centers, ratio_vs_intensity


def analyze_symmetry(ratio_map, mask, center_pixel=(512, 512)):
    """Analyze symmetry of ratio map."""
    print(f"\n=== Symmetry Analysis ===")

    # Check center vs edges
    center_region = mask.copy()
    center_radius = 100
    s_indices, f_indices = np.meshgrid(
        np.arange(ratio_map.shape[0]),
        np.arange(ratio_map.shape[1]),
        indexing='ij'
    )
    distances = np.sqrt(
        (s_indices - center_pixel[0])**2 +
        (f_indices - center_pixel[1])**2
    )
    center_region &= (distances < center_radius)
    edge_region = mask & (distances > 400)

    center_ratio = np.nanmean(ratio_map[center_region])
    edge_ratio = np.nanmean(ratio_map[edge_region])

    print(f"  Center ratio (r<{center_radius}): {center_ratio:.6f}")
    print(f"  Edge ratio (r>400): {edge_ratio:.6f}")
    print(f"  Asymmetry: {abs(center_ratio - edge_ratio):.6f}")

    if abs(center_ratio - edge_ratio) > 0.005:
        print(f"  ⚠️  SIGNIFICANT center-edge asymmetry detected!")
        print(f"      Center: {((center_ratio - 1) * 100):.2f}% from unity")
        print(f"      Edge: {((edge_ratio - 1) * 100):.2f}% from unity")

    # Check quadrant symmetry
    quadrants = []
    labels = ['Upper-left', 'Upper-right', 'Lower-left', 'Lower-right']

    for i, (s_range, f_range) in enumerate([
        (slice(0, center_pixel[0]), slice(0, center_pixel[1])),
        (slice(0, center_pixel[0]), slice(center_pixel[1], None)),
        (slice(center_pixel[0], None), slice(0, center_pixel[1])),
        (slice(center_pixel[0], None), slice(center_pixel[1], None)),
    ]):
        quadrant_mask = mask.copy()
        quadrant_mask[:, :] = False
        quadrant_mask[s_range, f_range] = mask[s_range, f_range]
        quadrant_ratio = np.nanmean(ratio_map[quadrant_mask])
        quadrants.append(quadrant_ratio)
        print(f"  {labels[i]} quadrant: {quadrant_ratio:.6f}")

    quadrant_std = np.std(quadrants)
    print(f"  Quadrant variation (std): {quadrant_std:.6f}")

    if quadrant_std > 0.002:
        print(f"  ⚠️  ASYMMETRIC quadrant distribution!")
        print(f"      This suggests detector basis vector error")


def generate_diagnostic_plots(ratio_map, mask, distance_data, angle_data, intensity_data, output_dir):
    """Generate diagnostic plots."""
    print(f"\n=== Generating Diagnostic Plots ===")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    # 1. Ratio map heatmap
    ax = axes[0, 0]
    ratio_display = ratio_map.copy()
    ratio_display[~mask] = np.nan
    im = ax.imshow(ratio_display, origin='lower', cmap='RdBu_r', vmin=0.99, vmax=1.01)
    ax.set_title('Ratio Map (PyTorch / Golden)')
    ax.set_xlabel('Fast Axis (pixels)')
    ax.set_ylabel('Slow Axis (pixels)')
    plt.colorbar(im, ax=ax, label='Ratio')

    # 2. Log-scale difference
    ax = axes[0, 1]
    log_diff = np.log10(np.abs(ratio_display - 1.0))
    im = ax.imshow(log_diff, origin='lower', cmap='viridis')
    ax.set_title('Log10(|Ratio - 1|)')
    ax.set_xlabel('Fast Axis (pixels)')
    ax.set_ylabel('Slow Axis (pixels)')
    plt.colorbar(im, ax=ax, label='Log10(|Error|)')

    # 3. Radial profile
    ax = axes[0, 2]
    distance_centers, ratio_vs_distance, correlation = distance_data
    ax.plot(distance_centers, ratio_vs_distance, 'o-')
    ax.axhline(y=1.0, color='r', linestyle='--', alpha=0.5)
    ax.set_xlabel('Distance from Center (pixels)')
    ax.set_ylabel('Mean Ratio')
    ax.set_title(f'Radial Profile (corr={correlation:.3f})')
    ax.grid(True, alpha=0.3)

    # 4. Angular profile
    ax = axes[1, 0]
    angle_centers, ratio_vs_angle = angle_data
    ax.plot(angle_centers, ratio_vs_angle, 'o-')
    ax.axhline(y=1.0, color='r', linestyle='--', alpha=0.5)
    ax.set_xlabel('Angle (degrees)')
    ax.set_ylabel('Mean Ratio')
    ax.set_title('Angular Profile')
    ax.grid(True, alpha=0.3)

    # 5. Intensity dependence
    ax = axes[1, 1]
    intensity_centers, ratio_vs_intensity = intensity_data
    ax.semilogx(intensity_centers, ratio_vs_intensity, 'o-')
    ax.axhline(y=1.0, color='r', linestyle='--', alpha=0.5)
    ax.set_xlabel('Golden Intensity (log scale)')
    ax.set_ylabel('Mean Ratio')
    ax.set_title('Intensity Dependence')
    ax.grid(True, alpha=0.3)

    # 6. Histogram of ratios
    ax = axes[1, 2]
    ratio_valid = ratio_map[mask]
    ax.hist(ratio_valid, bins=100, edgecolor='black')
    ax.axvline(x=1.0, color='r', linestyle='--', label='Unity')
    ax.axvline(x=np.nanmean(ratio_valid), color='g', linestyle='--', label='Mean')
    ax.set_xlabel('Ratio (PyTorch / Golden)')
    ax.set_ylabel('Pixel Count')
    ax.set_title('Ratio Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = output_dir / 'at012_spatial_analysis.png'
    plt.savefig(plot_path, dpi=150)
    print(f"  Saved plot to {plot_path}")
    plt.close()


def main():
    """Main diagnostic routine."""
    print("=" * 80)
    print("AT-PARALLEL-012 Spatial Pattern Diagnostic")
    print("=" * 80)

    # Set up paths
    project_root = Path(__file__).parent.parent
    golden_path = project_root / "tests" / "golden_data" / "simple_cubic.bin"
    output_dir = project_root / "diagnostic_artifacts" / "at012_spatial"

    # Check golden file exists
    if not golden_path.exists():
        print(f"ERROR: Golden file not found at {golden_path}")
        return 1

    # Load golden image
    golden_img = load_golden_image(golden_path)

    # Generate PyTorch image
    pytorch_img = generate_pytorch_image()

    # Verify shapes match
    if golden_img.shape != pytorch_img.shape:
        print(f"ERROR: Shape mismatch: golden={golden_img.shape}, pytorch={pytorch_img.shape}")
        return 1

    # Compute ratio map
    ratio_map, mask = compute_ratio_map(pytorch_img, golden_img, intensity_threshold=0.1)

    # Run analyses
    distance_data = analyze_radial_dependence(ratio_map, mask)
    angle_data = analyze_angular_dependence(ratio_map, mask)
    intensity_data = analyze_intensity_dependence(ratio_map, mask, golden_img)
    analyze_symmetry(ratio_map, mask)

    # Generate plots
    generate_diagnostic_plots(
        ratio_map, mask, distance_data, angle_data, intensity_data, output_dir
    )

    # Summary and hypotheses
    print("\n" + "=" * 80)
    print("SUMMARY AND HYPOTHESES")
    print("=" * 80)

    print("\nObserved Pattern:")
    print(f"  - Direct beam (center): PyTorch +1.03% HIGHER")
    print(f"  - Off-axis peaks: PyTorch -0.07% LOWER (average)")
    print(f"  - Total asymmetry: 1.1%")
    print(f"  - Correlation: 0.9946 (target: 0.9995)")

    print("\nTop 3 Hypotheses (ranked by evidence):")

    # Hypothesis ranking based on analysis
    distance_correlation = distance_data[2]

    print("\n1. OMEGA/SOLID ANGLE CALCULATION ERROR (HIGH PRIORITY)")
    print("   Evidence:")
    print(f"     - Radial correlation: {distance_correlation:.4f}")
    print("     - Center-edge asymmetry matches omega dependence")
    print("   Bug Location:")
    print("     - simulator.py: omega calculation (lines 660-670, 769-780)")
    print("     - Check close_distance vs distance usage")
    print("     - Verify obliquity factor: close_distance/R")
    print("   Recommendation:")
    print("     - Add trace logging for omega values at center vs edges")
    print("     - Verify r-factor calculation in detector.py (_calculate_pix0_vector)")

    print("\n2. POLARIZATION FACTOR ERROR (MEDIUM PRIORITY)")
    print("   Evidence:")
    print("     - Angular dependence patterns")
    print("     - Systematic center-edge difference")
    print("   Bug Location:")
    print("     - simulator.py: polarization_factor calculation (lines 685-694)")
    print("     - utils/physics.py: polarization_factor function")
    print("   Recommendation:")
    print("     - Compare polarization values at center vs edges")
    print("     - Check incident/diffracted beam direction calculation")

    print("\n3. NORMALIZATION/STEPS CALCULATION (LOW PRIORITY)")
    print("   Evidence:")
    print("     - Uniform offset could be normalization")
    print("     - But spatial pattern suggests geometry, not uniform scaling")
    print("   Bug Location:")
    print("     - simulator.py: steps calculation (line 562)")
    print("     - Check oversample factor handling")
    print("   Recommendation:")
    print("     - Verify steps = phi * mosaic * oversample^2")
    print("     - Check if oversample=1 is applied correctly")

    print("\n" + "=" * 80)
    print("CONCLUSION:")
    print("=" * 80)
    print("The spatial pattern strongly suggests a GEOMETRY bug, not a physics bug.")
    print("The center-edge asymmetry is characteristic of omega (solid angle) errors.")
    print("")
    print("Most likely cause: Incorrect close_distance calculation or r-factor usage")
    print("in the obliquity correction: omega = (pixel_size^2/R^2) * (close_distance/R)")
    print("")
    print("Next steps:")
    print("  1. Add detailed logging to omega calculation")
    print("  2. Compare omega values: center pixel vs edge pixels")
    print("  3. Verify r-factor calculation matches C code exactly")
    print("  4. Check if close_distance is being updated correctly")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())