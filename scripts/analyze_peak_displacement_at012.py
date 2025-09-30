"""
Analyze peak displacement patterns in AT-PARALLEL-012.
Computes centroid shifts and looks for systematic patterns.
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.ndimage import maximum_filter, center_of_mass
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from datetime import datetime

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


def find_peaks_with_centroids(image, n_peaks=50, percentile=99.0, window=5):
    """Find peaks and compute their centroids."""
    threshold = np.percentile(image, percentile)
    local_max = maximum_filter(image, size=3) == image
    peaks = np.where((local_max) & (image > threshold))

    if len(peaks[0]) == 0:
        return np.array([]).reshape(0, 2), np.array([]), np.array([]).reshape(0, 2)

    intensities = image[peaks]
    peak_coords = np.column_stack([peaks[0], peaks[1]])

    sorted_indices = np.argsort(intensities)[::-1][:n_peaks]
    peak_coords = peak_coords[sorted_indices]
    intensities = intensities[sorted_indices]

    # Compute centroids
    centroids = []
    for peak in peak_coords:
        s, f = peak
        # Extract window around peak
        s_min = max(0, s - window // 2)
        s_max = min(image.shape[0], s + window // 2 + 1)
        f_min = max(0, f - window // 2)
        f_max = min(image.shape[1], f + window // 2 + 1)

        window_data = image[s_min:s_max, f_min:f_max]

        if window_data.sum() > 0:
            # Compute centroid relative to window
            com = center_of_mass(window_data)
            # Convert to global coordinates
            centroid_s = s_min + com[0]
            centroid_f = f_min + com[1]
            centroids.append([centroid_s, centroid_f])
        else:
            centroids.append([float(s), float(f)])

    return peak_coords, intensities, np.array(centroids)


def match_peaks_with_offsets(golden_peaks, pytorch_peaks):
    """Match peaks and compute displacement vectors."""
    if len(golden_peaks) == 0 or len(pytorch_peaks) == 0:
        return [], []

    # Compute pairwise distances
    distances = cdist(golden_peaks, pytorch_peaks, metric='euclidean')

    # Apply Hungarian algorithm
    row_ind, col_ind = linear_sum_assignment(distances)

    # Compute displacement vectors
    matched_distances = distances[row_ind, col_ind]
    displacements = []
    matched_pairs = []

    for i, (g_idx, p_idx) in enumerate(zip(row_ind, col_ind)):
        if matched_distances[i] <= 5.0:  # Only consider matches within 5 pixels
            g_pos = golden_peaks[g_idx]
            p_pos = pytorch_peaks[p_idx]
            displacement = p_pos - g_pos  # (ds, df)
            displacements.append(displacement)
            matched_pairs.append((g_idx, p_idx))

    return np.array(displacements), matched_pairs


def main():
    # Load images
    output_dir = Path("reports") / "2025-09-29-AT-PARALLEL-012"
    golden_image = np.load(output_dir / "triclinic_golden.npy")
    pytorch_image = np.load(output_dir / "triclinic_pytorch.npy")

    print("=== Peak Displacement Analysis for AT-PARALLEL-012 ===")
    print()

    # Find peaks with centroids
    g_peaks, g_intensities, g_centroids = find_peaks_with_centroids(golden_image, n_peaks=50, percentile=99.0)
    p_peaks, p_intensities, p_centroids = find_peaks_with_centroids(pytorch_image, n_peaks=50, percentile=99.0)

    print(f"Golden peaks found: {len(g_peaks)}")
    print(f"PyTorch peaks found: {len(p_peaks)}")
    print()

    # Match peaks using centroids
    displacements, matched_pairs = match_peaks_with_offsets(g_centroids, p_centroids)

    print(f"Matched peak pairs (≤5px): {len(displacements)}")

    if len(displacements) == 0:
        print("No matched peaks found!")
        return

    print()

    # Analyze displacement statistics
    ds = displacements[:, 0]  # slow direction
    df = displacements[:, 1]  # fast direction
    magnitudes = np.sqrt(ds**2 + df**2)

    print("=== Displacement Statistics ===")
    print(f"Mean displacement: ({np.mean(ds):.4f}, {np.mean(df):.4f}) px")
    print(f"Std displacement:  ({np.std(ds):.4f}, {np.std(df):.4f}) px")
    print(f"Max displacement:  {np.max(magnitudes):.4f} px")
    print(f"Median displacement: {np.median(magnitudes):.4f} px")
    print()

    # Check for systematic patterns
    # 1. Radial pattern: displacement vs distance from center
    center = np.array([256.0, 256.0])
    for g_idx, p_idx in matched_pairs:
        g_pos = g_centroids[g_idx]
        p_pos = p_centroids[p_idx]

    g_matched_centroids = g_centroids[[pair[0] for pair in matched_pairs]]
    distances_from_center = np.sqrt(np.sum((g_matched_centroids - center)**2, axis=1))

    # 2. Directional pattern: displacement direction vs position
    angles = np.arctan2(df, ds) * 180 / np.pi  # displacement angle in degrees

    print("=== Pattern Analysis ===")
    print(f"Radial distances from center: min={np.min(distances_from_center):.1f}, max={np.max(distances_from_center):.1f} px")
    print(f"Displacement angles: min={np.min(angles):.1f}°, max={np.max(angles):.1f}°")
    print()

    # Compute correlation between distance and displacement magnitude
    from scipy.stats import pearsonr
    corr_radial, _ = pearsonr(distances_from_center, magnitudes)
    print(f"Correlation (distance vs magnitude): {corr_radial:.4f}")

    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(16, 16))

    # 1. Displacement vector field
    ax = axes[0, 0]
    ax.imshow(np.log1p(golden_image), cmap='gray', origin='lower', alpha=0.3)
    for i, (g_idx, p_idx) in enumerate(matched_pairs):
        g_pos = g_centroids[g_idx]
        p_pos = p_centroids[p_idx]
        ax.arrow(g_pos[1], g_pos[0], p_pos[1] - g_pos[1], p_pos[0] - g_pos[0],
                 head_width=3, head_length=3, fc='red', ec='red', alpha=0.7, width=0.5)
    ax.set_title('Displacement Vectors (Golden → PyTorch)', fontsize=14)
    ax.set_xlabel('Fast (px)')
    ax.set_ylabel('Slow (px)')

    # 2. Displacement magnitude vs distance from center
    ax = axes[0, 1]
    ax.scatter(distances_from_center, magnitudes, alpha=0.7)
    ax.set_xlabel('Distance from center (px)')
    ax.set_ylabel('Displacement magnitude (px)')
    ax.set_title(f'Radial Pattern (corr={corr_radial:.4f})', fontsize=14)
    ax.grid(True, alpha=0.3)

    # 3. Histogram of displacement magnitudes
    ax = axes[1, 0]
    ax.hist(magnitudes, bins=20, edgecolor='black', alpha=0.7)
    ax.axvline(np.median(magnitudes), color='red', linestyle='--', label=f'Median: {np.median(magnitudes):.3f} px')
    ax.axvline(0.5, color='green', linestyle='--', label='Spec threshold: 0.5 px')
    ax.set_xlabel('Displacement magnitude (px)')
    ax.set_ylabel('Count')
    ax.set_title('Displacement Magnitude Distribution', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 4. Displacement components
    ax = axes[1, 1]
    ax.scatter(df, ds, alpha=0.7)
    ax.axhline(0, color='black', linestyle='--', alpha=0.3)
    ax.axvline(0, color='black', linestyle='--', alpha=0.3)
    ax.set_xlabel('Fast displacement (px)')
    ax.set_ylabel('Slow displacement (px)')
    ax.set_title('Displacement Components', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.axis('equal')

    plt.tight_layout()
    out_file = output_dir / "peak_displacement_analysis.png"
    plt.savefig(out_file, dpi=150, bbox_inches='tight')
    print(f"Visualization saved to: {out_file}")

    # Check if there's a systematic offset
    mean_ds = np.mean(ds)
    mean_df = np.mean(df)
    if abs(mean_ds) > 0.1 or abs(mean_df) > 0.1:
        print()
        print(f"⚠️  Systematic offset detected: ({mean_ds:.4f}, {mean_df:.4f}) px")
        print("This suggests a global coordinate system or indexing issue.")
    else:
        print()
        print("✅ No significant systematic offset detected.")

    if np.median(magnitudes) > 0.5:
        print(f"❌ Median displacement {np.median(magnitudes):.3f} > 0.5 px spec threshold")
        print("This explains the low peak match rate (30/50).")
    else:
        print(f"✅ Median displacement {np.median(magnitudes):.3f} ≤ 0.5 px spec threshold")


if __name__ == "__main__":
    main()