#!/usr/bin/env python3
"""
Systematic analysis script to diagnose the correlation mismatch between PyTorch and C implementations
for tilted detector geometry.

This script investigates why the tilted detector case shows -0.019 correlation while
baseline shows 0.9988 correlation.
"""

import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import torch
from scipy.signal import correlate2d

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nanobrag_torch.config import BeamConfig, CrystalConfig, DetectorConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator

# Set environment variable for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

def load_binary_image(file_path, shape=(1024, 1024)):
    """Load binary image data."""
    return np.fromfile(file_path, dtype=np.float32).reshape(shape)

def calculate_detailed_metrics(pytorch_img, c_img):
    """Calculate comprehensive comparison metrics."""
    # Flatten for correlation
    py_flat = pytorch_img.flatten()
    c_flat = c_img.flatten()
    
    # Basic metrics
    correlation = np.corrcoef(py_flat, c_flat)[0, 1]
    
    # Center of mass
    y_indices, x_indices = np.indices(pytorch_img.shape)
    
    py_total = np.sum(pytorch_img)
    c_total = np.sum(c_img)
    
    py_com = (
        np.sum(y_indices * pytorch_img) / py_total,
        np.sum(x_indices * pytorch_img) / py_total
    )
    
    c_com = (
        np.sum(y_indices * c_img) / c_total,
        np.sum(x_indices * c_img) / c_total
    )
    
    # Brightest pixel locations
    py_max_idx = np.unravel_index(np.argmax(pytorch_img), pytorch_img.shape)
    c_max_idx = np.unravel_index(np.argmax(c_img), c_img.shape)
    
    # Pattern analysis
    difference = pytorch_img - c_img
    abs_difference = np.abs(difference)
    
    return {
        'correlation': correlation,
        'pytorch_total': py_total,
        'c_total': c_total,
        'intensity_ratio': py_total / c_total if c_total > 0 else float('inf'),
        'pytorch_com': py_com,
        'c_com': c_com,
        'com_offset': (py_com[0] - c_com[0], py_com[1] - c_com[1]),
        'pytorch_max_pixel': py_max_idx,
        'c_max_pixel': c_max_idx,
        'max_pixel_offset': (py_max_idx[0] - c_max_idx[0], py_max_idx[1] - c_max_idx[1]),
        'rms_absolute': np.sqrt(np.mean(difference**2)),
        'max_abs_difference': np.max(abs_difference),
        'mean_abs_difference': np.mean(abs_difference),
    }

def analyze_spatial_patterns(pytorch_img, c_img):
    """Analyze spatial patterns to detect systematic transformations."""
    
    # Check for rotation by comparing quadrant sums
    h, w = pytorch_img.shape
    mid_h, mid_w = h // 2, w // 2
    
    # Quadrant analysis
    quadrants_py = {
        'TL': np.sum(pytorch_img[:mid_h, :mid_w]),
        'TR': np.sum(pytorch_img[:mid_h, mid_w:]),
        'BL': np.sum(pytorch_img[mid_h:, :mid_w]),
        'BR': np.sum(pytorch_img[mid_h:, mid_w:])
    }
    
    quadrants_c = {
        'TL': np.sum(c_img[:mid_h, :mid_w]),
        'TR': np.sum(c_img[:mid_h, mid_w:]),
        'BL': np.sum(c_img[mid_h:, :mid_w]),
        'BR': np.sum(c_img[mid_h:, mid_w:])
    }
    
    # Check cross-correlation at different offsets
    
    # Limited cross-correlation for performance
    subset_size = 256
    start_h, start_w = (h - subset_size) // 2, (w - subset_size) // 2
    
    py_subset = pytorch_img[start_h:start_h+subset_size, start_w:start_w+subset_size]
    c_subset = c_img[start_h:start_h+subset_size, start_w:start_w+subset_size]
    
    # Cross-correlation
    xcorr = correlate2d(py_subset, c_subset, mode='same')
    xcorr_max_idx = np.unravel_index(np.argmax(xcorr), xcorr.shape)
    center = (subset_size // 2, subset_size // 2)
    offset = (xcorr_max_idx[0] - center[0], xcorr_max_idx[1] - center[1])
    
    return {
        'quadrants_pytorch': quadrants_py,
        'quadrants_c': quadrants_c,
        'best_cross_corr_offset': offset,
        'max_cross_corr_value': np.max(xcorr)
    }

def check_coordinate_conventions(detector_config):
    """Check if coordinate system conventions might be causing issues."""
    
    # Create detector and get pixel coordinates
    detector = Detector(detector_config)
    
    # Get all pixel coordinates
    all_coords = detector.get_pixel_coords()  # Shape: (spixels, fpixels, 3)
    
    # Get pixel coordinates for corners and center
    test_pixels = [
        (0, 0),      # Top-left
        (0, 1023),   # Top-right  
        (1023, 0),   # Bottom-left
        (1023, 1023), # Bottom-right
        (512, 512)   # Center
    ]
    
    pixel_info = {}
    for s, f in test_pixels:
        coords = all_coords[s, f]  # Extract specific pixel coordinates
        pixel_info[f'({s},{f})'] = {
            'lab_coords': coords.tolist()
        }
    
    return pixel_info

def create_diagnostic_plots(pytorch_img, c_img, metrics, spatial_analysis, save_dir):
    """Create comprehensive diagnostic plots."""
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle(f'Correlation Mismatch Diagnostic Analysis\nCorrelation: {metrics["correlation"]:.6f}', fontsize=16)
    
    # Raw images
    vmax = max(np.max(pytorch_img), np.max(c_img))
    im1 = axes[0,0].imshow(pytorch_img, vmax=vmax, origin='lower')
    axes[0,0].set_title('PyTorch Image')
    axes[0,0].plot(metrics['pytorch_com'][1], metrics['pytorch_com'][0], 'r+', markersize=10, label='COM')
    axes[0,0].plot(metrics['pytorch_max_pixel'][1], metrics['pytorch_max_pixel'][0], 'rx', markersize=8, label='Max')
    axes[0,0].legend()
    plt.colorbar(im1, ax=axes[0,0])
    
    im2 = axes[0,1].imshow(c_img, vmax=vmax, origin='lower')
    axes[0,1].set_title('C Code Image')
    axes[0,1].plot(metrics['c_com'][1], metrics['c_com'][0], 'r+', markersize=10, label='COM')
    axes[0,1].plot(metrics['c_max_pixel'][1], metrics['c_max_pixel'][0], 'rx', markersize=8, label='Max')
    axes[0,1].legend()
    plt.colorbar(im2, ax=axes[0,1])
    
    # Difference map
    difference = pytorch_img - c_img
    im3 = axes[0,2].imshow(difference, cmap='RdBu_r', origin='lower')
    axes[0,2].set_title('Difference (PyTorch - C)')
    plt.colorbar(im3, ax=axes[0,2])
    
    # Profile comparisons
    center_row = pytorch_img.shape[0] // 2
    center_col = pytorch_img.shape[1] // 2
    
    axes[1,0].plot(pytorch_img[center_row, :], 'b-', label='PyTorch', alpha=0.7)
    axes[1,0].plot(c_img[center_row, :], 'r-', label='C Code', alpha=0.7)
    axes[1,0].set_title(f'Horizontal Profile (row {center_row})')
    axes[1,0].legend()
    axes[1,0].set_xlabel('Pixel')
    axes[1,0].set_ylabel('Intensity')
    
    axes[1,1].plot(pytorch_img[:, center_col], 'b-', label='PyTorch', alpha=0.7)
    axes[1,1].plot(c_img[:, center_col], 'r-', label='C Code', alpha=0.7)
    axes[1,1].set_title(f'Vertical Profile (col {center_col})')
    axes[1,1].legend()
    axes[1,1].set_xlabel('Pixel')
    axes[1,1].set_ylabel('Intensity')
    
    # Scatter plot
    flat_py = pytorch_img.flatten()[::100]  # Sample for performance
    flat_c = c_img.flatten()[::100]
    axes[1,2].scatter(flat_c, flat_py, alpha=0.5, s=1)
    axes[1,2].plot([0, np.max(flat_c)], [0, np.max(flat_c)], 'r--', alpha=0.5)
    axes[1,2].set_xlabel('C Code Intensity')
    axes[1,2].set_ylabel('PyTorch Intensity')
    axes[1,2].set_title(f'Intensity Correlation\nr = {metrics["correlation"]:.6f}')
    
    plt.tight_layout()
    plt.savefig(save_dir / 'correlation_mismatch_analysis.png', dpi=150, bbox_inches='tight')
    plt.show()

def investigate_simulation_components(crystal_config, detector_config):
    """Test individual simulation components for correctness."""
    
    print("\n=== SIMULATION COMPONENT ANALYSIS ===")
    
    # Test crystal orientation and lattice vectors
    crystal = Crystal(crystal_config)
    print(f"Crystal lattice vectors:")
    print(f"  a: {crystal.a}")
    print(f"  b: {crystal.b}")  
    print(f"  c: {crystal.c}")
    
    # Test detector geometry
    detector = Detector(detector_config)
    print(f"\nDetector geometry initialized successfully")
    
    # Test center pixel calculation
    all_coords = detector.get_pixel_coords()
    center_coords = all_coords[512, 512]
    
    print(f"Center pixel (512, 512) lab coordinates: {center_coords}")
    
    return {
        'lattice_vectors': [crystal.a.tolist(), crystal.b.tolist(), crystal.c.tolist()],
        'center_pixel_test': {
            'lab_coords': center_coords.tolist()
        }
    }

def main():
    """Main diagnostic function."""
    
    print("=== CORRELATION MISMATCH DIAGNOSTIC ANALYSIS ===\n")
    
    # Setup paths
    repo_root = Path(__file__).parent.parent
    reports_dir = repo_root / "reports" / "detector_verification"
    golden_dir = repo_root / "tests" / "golden_data" / "cubic_tilted_detector"
    
    # Load existing correlation metrics
    print("1. Loading existing correlation metrics...")
    with open(reports_dir / "correlation_metrics.json", 'r') as f:
        correlation_data = json.load(f)
    
    print(f"   Baseline correlation: {correlation_data['baseline']['correlation']:.6f}")
    print(f"   Tilted correlation: {correlation_data['tilted']['correlation']:.6f}")
    print(f"   Issue confirmed: {correlation_data['tilted']['correlation']:.6f} << 0")
    
    # Load images for tilted case
    print("\n2. Loading tilted detector images...")
    
    # Check if we have PyTorch output available from previous runs
    pytorch_image_file = reports_dir / "pytorch_tilted_output.bin"
    c_image_file = golden_dir / "image.bin"
    
    if not pytorch_image_file.exists():
        print("   PyTorch image not found. Generating fresh simulation...")
        
        # Load configuration for tilted case
        with open(golden_dir / "params.json", 'r') as f:
            params = json.load(f)
        
        # Create configuration components
        crystal_config = CrystalConfig(
            cell_a=params["unit_cell"]["a"],
            cell_b=params["unit_cell"]["b"], 
            cell_c=params["unit_cell"]["c"],
            cell_alpha=params["unit_cell"]["alpha"],
            cell_beta=params["unit_cell"]["beta"],
            cell_gamma=params["unit_cell"]["gamma"],
            N_cells=(params["crystal_size_cells"], params["crystal_size_cells"], params["crystal_size_cells"]),
            default_F=100.0
        )
        
        detector_config = DetectorConfig(
            distance_mm=params["detector_distance_mm"],
            pixel_size_mm=params["detector_size_mm"] / params["detector_pixels"],
            spixels=params["detector_pixels"],
            fpixels=params["detector_pixels"],
            beam_center_s=params["beam_center_mm"]["x"],
            beam_center_f=params["beam_center_mm"]["y"],
            detector_rotx_deg=params["detector_rotations_deg"]["x"],
            detector_roty_deg=params["detector_rotations_deg"]["y"],
            detector_rotz_deg=params["detector_rotations_deg"]["z"],
            detector_twotheta_deg=params["twotheta_deg"],
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM
        )
        
        beam_config = BeamConfig(
            wavelength_A=params["wavelength_A"]
        )
        
        # Create model instances
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        
        # Run simulation
        simulator = Simulator(crystal, detector, crystal_config, beam_config)
        pytorch_image = simulator.run()
        
        # Save for reuse
        pytorch_image.numpy().astype(np.float32).tofile(pytorch_image_file)
        print(f"   Saved PyTorch output to {pytorch_image_file}")
        
    else:
        print("   Loading existing PyTorch output...")
        pytorch_image = torch.from_numpy(load_binary_image(pytorch_image_file))
        
        # Load configuration for component testing
        with open(golden_dir / "params.json", 'r') as f:
            params = json.load(f)
        
        crystal_config = CrystalConfig(
            cell_a=params["unit_cell"]["a"],
            cell_b=params["unit_cell"]["b"], 
            cell_c=params["unit_cell"]["c"],
            cell_alpha=params["unit_cell"]["alpha"],
            cell_beta=params["unit_cell"]["beta"],
            cell_gamma=params["unit_cell"]["gamma"],
            N_cells=(params["crystal_size_cells"], params["crystal_size_cells"], params["crystal_size_cells"]),
            default_F=100.0
        )
        
        detector_config = DetectorConfig(
            distance_mm=params["detector_distance_mm"],
            pixel_size_mm=params["detector_size_mm"] / params["detector_pixels"],
            spixels=params["detector_pixels"],
            fpixels=params["detector_pixels"],
            beam_center_s=params["beam_center_mm"]["x"],
            beam_center_f=params["beam_center_mm"]["y"],
            detector_rotx_deg=params["detector_rotations_deg"]["x"],
            detector_roty_deg=params["detector_rotations_deg"]["y"],
            detector_rotz_deg=params["detector_rotations_deg"]["z"],
            detector_twotheta_deg=params["twotheta_deg"],
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM
        )
        
        beam_config = BeamConfig(
            wavelength_A=params["wavelength_A"]
        )
    
    # Load C reference image
    print("   Loading C reference image...")
    c_image = load_binary_image(c_image_file)
    
    # Convert to numpy for analysis
    pytorch_img_np = pytorch_image.numpy()
    
    print(f"   PyTorch image shape: {pytorch_img_np.shape}, total intensity: {np.sum(pytorch_img_np):.1f}")
    print(f"   C image shape: {c_image.shape}, total intensity: {np.sum(c_image):.1f}")
    
    # Calculate detailed metrics
    print("\n3. Calculating detailed comparison metrics...")
    metrics = calculate_detailed_metrics(pytorch_img_np, c_image)
    
    print(f"   Correlation: {metrics['correlation']:.6f}")
    print(f"   Intensity ratio (PyTorch/C): {metrics['intensity_ratio']:.6f}")
    print(f"   Center of mass offset: Δs={metrics['com_offset'][0]:.1f}, Δf={metrics['com_offset'][1]:.1f} pixels")
    print(f"   Max pixel offset: Δs={metrics['max_pixel_offset'][0]}, Δf={metrics['max_pixel_offset'][1]} pixels")
    print(f"   RMS absolute difference: {metrics['rms_absolute']:.1f}")
    
    # Spatial pattern analysis
    print("\n4. Analyzing spatial patterns...")
    spatial_analysis = analyze_spatial_patterns(pytorch_img_np, c_image)
    
    print(f"   Best cross-correlation offset: {spatial_analysis['best_cross_corr_offset']}")
    print("   Quadrant intensity comparison:")
    for quad in ['TL', 'TR', 'BL', 'BR']:
        py_val = spatial_analysis['quadrants_pytorch'][quad]
        c_val = spatial_analysis['quadrants_c'][quad]
        ratio = py_val / c_val if c_val > 0 else float('inf')
        print(f"     {quad}: PyTorch={py_val:.1f}, C={c_val:.1f}, ratio={ratio:.3f}")
    
    # Check coordinate conventions
    print("\n5. Checking coordinate system conventions...")
    pixel_info = check_coordinate_conventions(detector_config)
    
    print("   Key pixel coordinates (lab frame):")
    for pixel, info in pixel_info.items():
        print(f"     {pixel}: {info['lab_coords']}")
    
    # Test simulation components
    component_info = investigate_simulation_components(crystal_config, detector_config)
    
    # Create diagnostic plots
    print("\n6. Creating diagnostic plots...")
    save_dir = reports_dir / "tilted_analysis"
    save_dir.mkdir(exist_ok=True)
    
    create_diagnostic_plots(pytorch_img_np, c_image, metrics, spatial_analysis, save_dir)
    
    # Convert numpy types to native Python types for JSON serialization
    def convert_for_json(obj):
        if isinstance(obj, (np.floating, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.integer, np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, torch.Tensor):
            return obj.detach().cpu().numpy().tolist()
        elif isinstance(obj, dict):
            return {k: convert_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [convert_for_json(item) for item in obj]
        return obj
    
    # Save detailed analysis
    analysis_results = {
        'correlation_metrics': convert_for_json(metrics),
        'spatial_analysis': convert_for_json(spatial_analysis),
        'pixel_coordinates': convert_for_json(pixel_info),
        'component_analysis': convert_for_json(component_info),
        'summary': {
            'correlation': float(metrics['correlation']),
            'likely_issues': [],
            'recommendations': []
        }
    }
    
    # Diagnostic analysis
    if abs(metrics['correlation']) < 0.1:
        analysis_results['summary']['likely_issues'].append('Severe correlation mismatch suggests systematic transformation difference')
    
    if abs(metrics['com_offset'][0]) > 50 or abs(metrics['com_offset'][1]) > 50:
        analysis_results['summary']['likely_issues'].append(f"Large center-of-mass offset: {metrics['com_offset']}")
    
    if abs(metrics['intensity_ratio'] - 1.0) > 0.1:
        analysis_results['summary']['likely_issues'].append(f"Intensity scaling mismatch: {metrics['intensity_ratio']:.3f}")
    
    # Recommendations
    if metrics['correlation'] < -0.5:
        analysis_results['summary']['recommendations'].append('Negative correlation suggests coordinate system flip or reflection')
    
    analysis_results['summary']['recommendations'].extend([
        'Check scattering vector calculation in simulator',
        'Verify Miller index computation',
        'Examine structure factor interpolation',
        'Investigate intensity accumulation logic'
    ])
    
    # Save results
    with open(save_dir / "detailed_analysis.json", 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    print(f"\n   Diagnostic plots saved to: {save_dir}/correlation_mismatch_analysis.png")
    print(f"   Detailed analysis saved to: {save_dir}/detailed_analysis.json")
    
    # Summary
    print("\n=== DIAGNOSTIC SUMMARY ===")
    print(f"Correlation: {metrics['correlation']:.6f} (TARGET: > 0.99)")
    print("Status: SEVERE MISMATCH - Investigation required")
    print("\nLikely issues identified:")
    for issue in analysis_results['summary']['likely_issues']:
        print(f"  - {issue}")
    print("\nRecommended next steps:")
    for rec in analysis_results['summary']['recommendations']:
        print(f"  - {rec}")

if __name__ == "__main__":
    main()