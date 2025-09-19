#!/usr/bin/env python3
"""
Analyze the mismatch between PyTorch and C implementations for tilted detector case.

This script loads the correlation metrics and performs detailed analysis to understand
why the tilted detector case shows negative correlation while straight detector works.
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import torch
import fabio
from scipy import ndimage
from skimage import feature

# Ensure MKL compatibility
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


def load_correlation_metrics(report_dir="reports/detector_verification"):
    """Load the saved correlation metrics."""
    metrics_path = Path(report_dir) / "correlation_metrics.json"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Correlation metrics not found at {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)


def load_images(test_case, report_dir="reports/detector_verification"):
    """Load PyTorch and C reference images for a test case."""
    # For this analysis, we need to re-run the simulation to get the images
    # Import what we need
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from src.nanobrag_torch.simulator import Simulator
    from src.nanobrag_torch.models.crystal import Crystal
    from src.nanobrag_torch.models.detector import Detector
    from src.nanobrag_torch.models.beam import Beam
    from src.nanobrag_torch.config import SimulationConfig
    
    # Configure for the test case
    if test_case == "simple_cubic_tilted":
        # Tilted detector configuration
        detector_config = {
            'distance': 100.0,  # mm
            'pixel_size': 0.1,  # mm
            'size': (1024, 1024),
            'beam_center': (512.5, 512.5),
            'detector_rotx': 5.0,  # 5 degree tilt
            'detector_roty': 0.0,
            'detector_rotz': 0.0,
            'detector_twotheta': 0.0,
            'convention': 'MOSFLM',
            'pivot': 'BEAM'
        }
    else:
        # Straight detector configuration
        detector_config = {
            'distance': 100.0,  # mm
            'pixel_size': 0.1,  # mm
            'size': (1024, 1024),
            'beam_center': (512.5, 512.5),
            'detector_rotx': 0.0,
            'detector_roty': 0.0,
            'detector_rotz': 0.0,
            'detector_twotheta': 0.0,
            'convention': 'MOSFLM',
            'pivot': 'BEAM'
        }
    
    # Create models
    crystal = Crystal(
        unit_cell=(100.0, 100.0, 100.0, 90.0, 90.0, 90.0),
        space_group_symbol='P1',
        phi_start=0.0,
        phi_end=0.0,
        mosaic_domains=1,
        mosaic_spread=0.0,
        misset=(0.0, 0.0, 0.0)
    )
    
    detector = Detector(**detector_config)
    
    beam = Beam(
        wavelength=6.2,  # Angstroms
        flux=1e12,
        beam_size=(0.1, 0.1),  # mm
        divergence=(0.0, 0.0),  # mrad
        polarization=1.0
    )
    
    # Load structure factors
    hkl_path = Path("tests/golden_data/simple_cubic.hkl")
    
    # Create simulator
    config = SimulationConfig(
        oversample=1,
        crystal_size=(5, 5, 5),  # cells
        default_F=100.0,
        fluence=1e15,
        water_path_mm=0.0,
        air_path_mm=0.0,
        add_noise=False
    )
    
    simulator = Simulator(
        crystal=crystal,
        detector=detector,
        beam=beam,
        config=config
    )
    
    # Load structure factors and simulate
    simulator.load_structure_factors(str(hkl_path))
    torch_image = simulator.simulate().cpu().numpy()
    
    # Load C reference image
    c_output_path = Path("tests/golden_data") / f"{test_case}_intimage.img"
    if c_output_path.exists():
        c_image = fabio.open(str(c_output_path)).data.astype(np.float32)
    else:
        print(f"Warning: C reference image not found for {test_case}")
        c_image = None
    
    return torch_image, c_image


def find_bright_spots(image, n_spots=20, threshold_percentile=99.5):
    """Find the brightest spots in an image."""
    # Apply threshold
    threshold = np.percentile(image, threshold_percentile)
    
    # Find local maxima
    # Use a larger neighborhood for tilted case to avoid noise
    local_maxima = feature.peak_local_max(
        image,
        min_distance=10,
        threshold_abs=threshold,
        num_peaks=n_spots,
        exclude_border=True
    )
    
    # Sort by intensity
    if len(local_maxima) > 0:
        intensities = [image[y, x] for y, x in local_maxima]
        sorted_indices = np.argsort(intensities)[::-1]
        local_maxima = local_maxima[sorted_indices]
    
    return local_maxima


def match_spots(spots1, spots2, max_distance=50):
    """Match corresponding spots between two images."""
    matches = []
    
    for i, spot1 in enumerate(spots1):
        distances = np.sqrt(np.sum((spots2 - spot1)**2, axis=1))
        min_idx = np.argmin(distances)
        min_dist = distances[min_idx]
        
        if min_dist < max_distance:
            matches.append((i, min_idx, min_dist))
    
    return matches


def analyze_spot_transformation(spots1, spots2, matches):
    """Analyze the transformation between matched spots."""
    if not matches:
        return None
    
    # Extract matched pairs
    pairs1 = np.array([spots1[i] for i, j, _ in matches])
    pairs2 = np.array([spots2[j] for i, j, _ in matches])
    
    # Calculate offsets
    offsets = pairs2 - pairs1
    mean_offset = np.mean(offsets, axis=0)
    std_offset = np.std(offsets, axis=0)
    
    # Check for rotation by looking at angle changes
    if len(matches) >= 2:
        # Calculate vectors between spot pairs
        vec1 = pairs1[1:] - pairs1[0]
        vec2 = pairs2[1:] - pairs2[0]
        
        # Calculate angles
        angles1 = np.arctan2(vec1[:, 1], vec1[:, 0])
        angles2 = np.arctan2(vec2[:, 1], vec2[:, 0])
        angle_diffs = angles2 - angles1
        
        # Wrap angles to [-pi, pi]
        angle_diffs = np.arctan2(np.sin(angle_diffs), np.cos(angle_diffs))
        mean_rotation = np.mean(angle_diffs)
    else:
        mean_rotation = 0
    
    return {
        'mean_offset': mean_offset,
        'std_offset': std_offset,
        'mean_rotation_rad': mean_rotation,
        'mean_rotation_deg': np.degrees(mean_rotation),
        'n_matches': len(matches)
    }


def plot_diagnostic_comparison(torch_image, c_image, torch_spots, c_spots, matches, 
                             transformation, test_case, output_dir):
    """Create diagnostic plots comparing PyTorch and C implementations."""
    fig = plt.figure(figsize=(20, 15))
    
    # Common colormap and normalization
    vmin = min(torch_image.min(), c_image.min() if c_image is not None else torch_image.min())
    vmax = max(torch_image.max(), c_image.max() if c_image is not None else torch_image.max())
    
    # 1. PyTorch image with spots
    ax1 = plt.subplot(2, 3, 1)
    im1 = ax1.imshow(torch_image, cmap='viridis', vmin=vmin, vmax=vmax, origin='lower')
    if len(torch_spots) > 0:
        ax1.scatter(torch_spots[:, 1], torch_spots[:, 0], c='red', s=100, marker='x', linewidth=2)
        for i, (y, x) in enumerate(torch_spots[:5]):  # Label first 5
            ax1.annotate(f'{i}', (x, y), color='white', fontsize=8, ha='center', va='bottom')
    ax1.set_title(f'PyTorch Implementation\nMax: {torch_image.max():.2f}')
    ax1.set_xlabel('Fast axis (pixels)')
    ax1.set_ylabel('Slow axis (pixels)')
    plt.colorbar(im1, ax=ax1)
    
    if c_image is not None:
        # 2. C reference image with spots
        ax2 = plt.subplot(2, 3, 2)
        im2 = ax2.imshow(c_image, cmap='viridis', vmin=vmin, vmax=vmax, origin='lower')
        if len(c_spots) > 0:
            ax2.scatter(c_spots[:, 1], c_spots[:, 0], c='red', s=100, marker='x', linewidth=2)
            for i, (y, x) in enumerate(c_spots[:5]):  # Label first 5
                ax2.annotate(f'{i}', (x, y), color='white', fontsize=8, ha='center', va='bottom')
        ax2.set_title(f'C Reference\nMax: {c_image.max():.2f}')
        ax2.set_xlabel('Fast axis (pixels)')
        ax2.set_ylabel('Slow axis (pixels)')
        plt.colorbar(im2, ax=ax2)
        
        # 3. Difference map
        ax3 = plt.subplot(2, 3, 3)
        diff = torch_image - c_image
        im3 = ax3.imshow(diff, cmap='RdBu_r', center=0, origin='lower')
        ax3.set_title(f'Difference (PyTorch - C)\nRMS: {np.sqrt(np.mean(diff**2)):.2f}')
        ax3.set_xlabel('Fast axis (pixels)')
        ax3.set_ylabel('Slow axis (pixels)')
        plt.colorbar(im3, ax=ax3)
        
        # 4. Log scale comparison
        ax4 = plt.subplot(2, 3, 4)
        torch_log = np.log10(np.maximum(torch_image, 1e-10))
        ax4.imshow(torch_log, cmap='viridis', origin='lower')
        ax4.set_title('PyTorch (log scale)')
        ax4.set_xlabel('Fast axis (pixels)')
        ax4.set_ylabel('Slow axis (pixels)')
        
        ax5 = plt.subplot(2, 3, 5)
        c_log = np.log10(np.maximum(c_image, 1e-10))
        ax5.imshow(c_log, cmap='viridis', origin='lower')
        ax5.set_title('C Reference (log scale)')
        ax5.set_xlabel('Fast axis (pixels)')
        ax5.set_ylabel('Slow axis (pixels)')
        
        # 5. Spot correspondence plot
        ax6 = plt.subplot(2, 3, 6)
        if matches and transformation:
            # Plot matched spots
            for i, j, dist in matches:
                ax6.plot([torch_spots[i, 1], c_spots[j, 1]], 
                        [torch_spots[i, 0], c_spots[j, 0]], 
                        'b-', alpha=0.5)
                ax6.scatter(torch_spots[i, 1], torch_spots[i, 0], 
                           c='red', s=50, marker='o', label='PyTorch' if i == 0 else '')
                ax6.scatter(c_spots[j, 1], c_spots[j, 0], 
                           c='blue', s=50, marker='s', label='C' if i == 0 else '')
            
            ax6.set_xlim(0, torch_image.shape[1])
            ax6.set_ylim(0, torch_image.shape[0])
            ax6.invert_yaxis()
            ax6.set_aspect('equal')
            ax6.legend()
            ax6.set_title(f'Spot Correspondences\nMean offset: ({transformation["mean_offset"][1]:.1f}, {transformation["mean_offset"][0]:.1f})\nRotation: {transformation["mean_rotation_deg"]:.1f}°')
            ax6.set_xlabel('Fast axis (pixels)')
            ax6.set_ylabel('Slow axis (pixels)')
        else:
            ax6.text(0.5, 0.5, 'No matched spots found', 
                    transform=ax6.transAxes, ha='center', va='center')
            ax6.set_title('Spot Correspondences')
    
    plt.suptitle(f'Diagnostic Analysis: {test_case}', fontsize=16)
    plt.tight_layout()
    plt.savefig(Path(output_dir) / f'{test_case}_diagnostic_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()


def analyze_intensity_distribution(torch_image, c_image, test_case, output_dir):
    """Analyze and compare intensity distributions."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Flatten images
    torch_flat = torch_image.flatten()
    c_flat = c_image.flatten() if c_image is not None else None
    
    # 1. Histogram comparison
    ax = axes[0, 0]
    ax.hist(torch_flat[torch_flat > 0], bins=50, alpha=0.5, label='PyTorch', density=True)
    if c_flat is not None:
        ax.hist(c_flat[c_flat > 0], bins=50, alpha=0.5, label='C', density=True)
    ax.set_xlabel('Intensity')
    ax.set_ylabel('Density')
    ax.set_title('Intensity Distribution (non-zero pixels)')
    ax.legend()
    ax.set_yscale('log')
    
    # 2. Log-scale histogram
    ax = axes[0, 1]
    torch_log = np.log10(np.maximum(torch_flat, 1e-10))
    ax.hist(torch_log[torch_flat > 0], bins=50, alpha=0.5, label='PyTorch', density=True)
    if c_flat is not None:
        c_log = np.log10(np.maximum(c_flat, 1e-10))
        ax.hist(c_log[c_flat > 0], bins=50, alpha=0.5, label='C', density=True)
    ax.set_xlabel('log10(Intensity)')
    ax.set_ylabel('Density')
    ax.set_title('Log Intensity Distribution')
    ax.legend()
    
    # 3. Scatter plot (if C reference available)
    ax = axes[1, 0]
    if c_image is not None:
        # Sample points to avoid overplotting
        mask = (torch_flat > 0) | (c_flat > 0)
        indices = np.where(mask)[0]
        if len(indices) > 10000:
            indices = np.random.choice(indices, 10000, replace=False)
        
        ax.scatter(c_flat[indices], torch_flat[indices], alpha=0.1, s=1)
        ax.plot([0, max(c_flat.max(), torch_flat.max())], 
                [0, max(c_flat.max(), torch_flat.max())], 
                'r--', label='y=x')
        ax.set_xlabel('C Intensity')
        ax.set_ylabel('PyTorch Intensity')
        ax.set_title('Intensity Correlation')
        ax.legend()
        ax.set_xscale('log')
        ax.set_yscale('log')
    else:
        ax.text(0.5, 0.5, 'No C reference available', 
                transform=ax.transAxes, ha='center', va='center')
    
    # 4. Radial profile
    ax = axes[1, 1]
    center = np.array(torch_image.shape) // 2
    y, x = np.ogrid[:torch_image.shape[0], :torch_image.shape[1]]
    r = np.sqrt((x - center[1])**2 + (y - center[0])**2).astype(int)
    
    # Compute radial average
    max_r = min(center)
    torch_radial = ndimage.mean(torch_image, labels=r, index=np.arange(0, max_r))
    ax.plot(torch_radial, label='PyTorch', linewidth=2)
    
    if c_image is not None:
        c_radial = ndimage.mean(c_image, labels=r, index=np.arange(0, max_r))
        ax.plot(c_radial, label='C', linewidth=2)
    
    ax.set_xlabel('Radius (pixels)')
    ax.set_ylabel('Mean Intensity')
    ax.set_title('Radial Intensity Profile')
    ax.legend()
    ax.set_yscale('log')
    
    plt.suptitle(f'Intensity Distribution Analysis: {test_case}', fontsize=14)
    plt.tight_layout()
    plt.savefig(Path(output_dir) / f'{test_case}_intensity_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()


def main():
    # Setup output directory
    output_dir = Path("reports/detector_verification/tilted_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load correlation metrics
    print("Loading correlation metrics...")
    metrics = load_correlation_metrics()
    
    # Print summary
    print("\nCorrelation Summary:")
    print(f"  Baseline (straight detector): {metrics['baseline']['correlation']:.4f}")
    print(f"  Tilted detector: {metrics['tilted']['correlation']:.4f}")
    
    # Analyze tilted case
    test_case = "simple_cubic_tilted"
    print(f"\nAnalyzing {test_case}...")
    
    # Load images
    try:
        torch_image, c_image = load_images(test_case)
        print(f"  PyTorch image shape: {torch_image.shape}")
        print(f"  PyTorch intensity range: [{torch_image.min():.2f}, {torch_image.max():.2f}]")
        
        if c_image is not None:
            print(f"  C image shape: {c_image.shape}")
            print(f"  C intensity range: [{c_image.min():.2f}, {c_image.max():.2f}]")
            
            # Find bright spots
            print("\nFinding bright spots...")
            torch_spots = find_bright_spots(torch_image, n_spots=20)
            c_spots = find_bright_spots(c_image, n_spots=20)
            
            print(f"  Found {len(torch_spots)} spots in PyTorch image")
            print(f"  Found {len(c_spots)} spots in C image")
            
            # Match spots
            if len(torch_spots) > 0 and len(c_spots) > 0:
                matches = match_spots(torch_spots, c_spots, max_distance=100)
                print(f"  Matched {len(matches)} spot pairs")
                
                # Analyze transformation
                transformation = analyze_spot_transformation(torch_spots, c_spots, matches)
                if transformation:
                    print(f"\nTransformation analysis:")
                    print(f"  Mean offset: ({transformation['mean_offset'][1]:.1f}, {transformation['mean_offset'][0]:.1f}) pixels")
                    print(f"  Std offset: ({transformation['std_offset'][1]:.1f}, {transformation['std_offset'][0]:.1f}) pixels")
                    print(f"  Mean rotation: {transformation['mean_rotation_deg']:.1f}°")
            else:
                matches = []
                transformation = None
            
            # Create diagnostic plots
            print("\nCreating diagnostic plots...")
            plot_diagnostic_comparison(torch_image, c_image, torch_spots, c_spots, 
                                     matches, transformation, test_case, output_dir)
            
            # Analyze intensity distributions
            analyze_intensity_distribution(torch_image, c_image, test_case, output_dir)
            
            # Save analysis results
            analysis_results = {
                'test_case': test_case,
                'correlation': metrics['tilted']['correlation'],
                'torch_spots': len(torch_spots),
                'c_spots': len(c_spots),
                'matched_spots': len(matches) if matches else 0,
                'transformation': transformation
            }
            
            with open(output_dir / f'{test_case}_analysis.json', 'w') as f:
                json.dump(analysis_results, f, indent=2)
            
            print(f"\nAnalysis complete. Results saved to {output_dir}")
            
            # Also analyze straight case for comparison
            print(f"\nAnalyzing simple_cubic_straight for comparison...")
            test_case = "simple_cubic_straight"
            torch_image, c_image = load_images(test_case)
            
            if c_image is not None:
                torch_spots = find_bright_spots(torch_image, n_spots=20)
                c_spots = find_bright_spots(c_image, n_spots=20)
                matches = match_spots(torch_spots, c_spots, max_distance=100) if len(torch_spots) > 0 and len(c_spots) > 0 else []
                transformation = analyze_spot_transformation(torch_spots, c_spots, matches) if matches else None
                
                plot_diagnostic_comparison(torch_image, c_image, torch_spots, c_spots, 
                                         matches, transformation, test_case, output_dir)
                analyze_intensity_distribution(torch_image, c_image, test_case, output_dir)
            
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()