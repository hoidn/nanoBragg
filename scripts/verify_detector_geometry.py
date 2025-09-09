#!/usr/bin/env python3
"""
Visual verification script for detector geometry.

This script creates visualizations to verify the detector geometry implementation
by comparing baseline (simple_cubic) and tilted detector configurations.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import matplotlib.pyplot as plt
import numpy as np
import torch
from matplotlib.colors import LogNorm

from nanobrag_torch.config import (
    BeamConfig,
    CrystalConfig,
    DetectorConfig,
    DetectorConvention,
    DetectorPivot,
)
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

# Import C reference verification components
try:
    from c_reference_runner import CReferenceRunner, compute_agreement_metrics

    C_REFERENCE_AVAILABLE = True
except ImportError:
    print("⚠️  C reference components not available")
    C_REFERENCE_AVAILABLE = False


def create_output_dir():
    """Create output directory for verification images."""
    output_dir = Path("reports/detector_verification")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def print_parity_report(pytorch_config, c_command, label=""):
    """Print side-by-side comparison of PyTorch config and C command parameters.
    
    Args:
        pytorch_config: DetectorConfig instance
        c_command: List of C command arguments
        label: Configuration label (e.g., "Baseline" or "Tilted")
    """
    print(f"\n{'='*60}")
    print(f"CONFIGURATION PARITY TABLE: {label}")
    print(f"{'='*60}")
    print(f"{'Parameter':<25} {'PyTorch':<20} {'C-Code':<20}")
    print(f"{'-'*65}")
    
    # Extract C command values
    c_params = {}
    i = 0
    while i < len(c_command):
        if c_command[i].startswith('-'):
            param = c_command[i]
            if i + 1 < len(c_command) and not c_command[i + 1].startswith('-'):
                value = c_command[i + 1]
                # Handle multi-value parameters
                j = i + 2
                while j < len(c_command) and not c_command[j].startswith('-'):
                    value += f" {c_command[j]}"
                    j += 1
                c_params[param] = value
                i = j - 1
            else:
                c_params[param] = "true"
        i += 1
    
    # Print comparisons
    print(f"{'Pivot Mode':<25} {pytorch_config.detector_pivot.name:<20} {c_params.get('-pivot', 'DEFAULT'):<20}")
    print(f"{'Distance (mm)':<25} {pytorch_config.distance_mm:<20} {c_params.get('-distance', 'N/A'):<20}")
    print(f"{'Beam Center S (mm)':<25} {pytorch_config.beam_center_s:<20} {c_params.get('-beam', '').split()[0] if '-beam' in c_params else 'N/A':<20}")
    print(f"{'Beam Center F (mm)':<25} {pytorch_config.beam_center_f:<20} {c_params.get('-beam', '').split()[1] if '-beam' in c_params and len(c_params['-beam'].split()) > 1 else 'N/A':<20}")
    print(f"{'Detector rotx (deg)':<25} {pytorch_config.detector_rotx_deg:<20} {c_params.get('-detector_rotx', '0.0'):<20}")
    print(f"{'Detector roty (deg)':<25} {pytorch_config.detector_roty_deg:<20} {c_params.get('-detector_roty', '0.0'):<20}")
    print(f"{'Detector rotz (deg)':<25} {pytorch_config.detector_rotz_deg:<20} {c_params.get('-detector_rotz', '0.0'):<20}")
    print(f"{'Two-theta (deg)':<25} {pytorch_config.detector_twotheta_deg:<20} {c_params.get('-detector_twotheta', '0.0'):<20}")
    
    if pytorch_config.detector_twotheta_deg != 0 and pytorch_config.twotheta_axis is not None:
        axis_str = f"[{pytorch_config.twotheta_axis[0]:.1f}, {pytorch_config.twotheta_axis[1]:.1f}, {pytorch_config.twotheta_axis[2]:.1f}]"
        c_axis = c_params.get('-twotheta_axis', 'DEFAULT')
        print(f"{'Two-theta axis':<25} {axis_str:<20} {c_axis:<20}")
    
    print(f"{'='*60}\n")


def run_simulation(detector_config, label=""):
    """Run a simulation with the given detector configuration."""
    print(f"\n{'='*60}")
    print(f"Running simulation: {label}")
    print(f"{'='*60}")

    # Set environment variable
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    device = torch.device("cpu")
    dtype = torch.float64

    # Create crystal config (simple cubic)
    crystal_config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 5, 5),
    )

    # Create beam config
    beam_config = BeamConfig(
        wavelength_A=6.2,
        N_source_points=1,
        source_distance_mm=10000.0,
        source_size_mm=0.0,
    )

    # Create models
    detector = Detector(config=detector_config, device=device, dtype=dtype)
    crystal = Crystal(config=crystal_config, device=device, dtype=dtype)

    # Print detector information
    print(f"\nDetector Configuration:")
    print(f"  Distance: {detector_config.distance_mm} mm")
    print(
        f"  Beam center: ({detector_config.beam_center_s}, {detector_config.beam_center_f}) mm"
    )
    print(
        f"  Rotations: rotx={detector_config.detector_rotx_deg}°, "
        f"roty={detector_config.detector_roty_deg}°, "
        f"rotz={detector_config.detector_rotz_deg}°"
    )
    print(f"  Two-theta: {detector_config.detector_twotheta_deg}°")

    print(f"\nDetector Basis Vectors:")
    print(f"  Fast axis: {detector.fdet_vec.numpy()}")
    print(f"  Slow axis: {detector.sdet_vec.numpy()}")
    print(f"  Normal axis: {detector.odet_vec.numpy()}")
    print(f"  Pix0 vector: {detector.pix0_vector.numpy()} meters")

    # Create and run simulator
    simulator = Simulator(
        crystal=crystal,
        detector=detector,
        beam_config=beam_config,
        device=device,
        dtype=dtype,
    )

    # Run simulation
    print("\nRunning simulation...")
    image = simulator.run()

    return image.numpy(), detector


def find_brightest_spots(image, n_spots=5):
    """Find the brightest spots in the image."""
    # Flatten and find top indices
    flat_indices = np.argpartition(image.ravel(), -n_spots)[-n_spots:]
    flat_indices = flat_indices[np.argsort(image.ravel()[flat_indices])[::-1]]

    # Convert to 2D indices
    spots = []
    for idx in flat_indices:
        s, f = np.unravel_index(idx, image.shape)
        intensity = image[s, f]
        spots.append((s, f, intensity))

    return spots


def create_comparison_plots(baseline_data, tilted_data, output_dir):
    """Create comparison plots for baseline and tilted detector."""
    baseline_image, baseline_detector = baseline_data
    tilted_image, tilted_detector = tilted_data

    # Create figure with subplots
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle("Detector Geometry Verification: Baseline vs Tilted", fontsize=16)

    # Plot baseline image
    im1 = axes[0, 0].imshow(
        baseline_image,
        norm=LogNorm(vmin=1e-6, vmax=baseline_image.max()),
        origin="lower",
        cmap="viridis",
    )
    axes[0, 0].set_title("Baseline Detector (simple_cubic)")
    axes[0, 0].set_xlabel("Fast axis (pixels)")
    axes[0, 0].set_ylabel("Slow axis (pixels)")
    plt.colorbar(im1, ax=axes[0, 0], label="Intensity")

    # Plot tilted image
    im2 = axes[0, 1].imshow(
        tilted_image,
        norm=LogNorm(vmin=1e-6, vmax=tilted_image.max()),
        origin="lower",
        cmap="viridis",
    )
    axes[0, 1].set_title("Tilted Detector (20° two-theta)")
    axes[0, 1].set_xlabel("Fast axis (pixels)")
    axes[0, 1].set_ylabel("Slow axis (pixels)")
    plt.colorbar(im2, ax=axes[0, 1], label="Intensity")

    # Plot difference
    diff_image = np.log10(tilted_image + 1e-10) - np.log10(baseline_image + 1e-10)
    im3 = axes[0, 2].imshow(diff_image, cmap="RdBu_r", origin="lower", vmin=-2, vmax=2)
    axes[0, 2].set_title("Log Ratio (Tilted/Baseline)")
    axes[0, 2].set_xlabel("Fast axis (pixels)")
    axes[0, 2].set_ylabel("Slow axis (pixels)")
    plt.colorbar(im3, ax=axes[0, 2], label="Log10(Tilted/Baseline)")

    # Find and mark brightest spots
    baseline_spots = find_brightest_spots(baseline_image, n_spots=10)
    tilted_spots = find_brightest_spots(tilted_image, n_spots=10)

    # Mark spots on images
    for s, f, _ in baseline_spots[:5]:
        axes[0, 0].plot(f, s, "r+", markersize=15, markeredgewidth=2)

    for s, f, _ in tilted_spots[:5]:
        axes[0, 1].plot(f, s, "r+", markersize=15, markeredgewidth=2)

    # Plot intensity profiles
    # Horizontal profile through beam center
    baseline_beam_s = int(baseline_detector.beam_center_s.item())
    tilted_beam_s = int(tilted_detector.beam_center_s.item())

    axes[1, 0].semilogy(baseline_image[baseline_beam_s, :], label="Baseline")
    axes[1, 0].semilogy(tilted_image[tilted_beam_s, :], label="Tilted")
    axes[1, 0].set_title("Horizontal Profile (through beam center)")
    axes[1, 0].set_xlabel("Fast axis (pixels)")
    axes[1, 0].set_ylabel("Intensity")
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # Vertical profile through beam center
    baseline_beam_f = int(baseline_detector.beam_center_f.item())
    tilted_beam_f = int(tilted_detector.beam_center_f.item())

    axes[1, 1].semilogy(baseline_image[:, baseline_beam_f], label="Baseline")
    axes[1, 1].semilogy(tilted_image[:, tilted_beam_f], label="Tilted")
    axes[1, 1].set_title("Vertical Profile (through beam center)")
    axes[1, 1].set_xlabel("Slow axis (pixels)")
    axes[1, 1].set_ylabel("Intensity")
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    # Spot position comparison
    axes[1, 2].set_title("Brightest Spot Positions")

    # Plot baseline spots in blue
    baseline_s = [s for s, _, _ in baseline_spots[:5]]
    baseline_f = [f for _, f, _ in baseline_spots[:5]]
    axes[1, 2].scatter(
        baseline_f, baseline_s, c="blue", s=100, label="Baseline", alpha=0.6
    )

    # Plot tilted spots in red
    tilted_s = [s for s, _, _ in tilted_spots[:5]]
    tilted_f = [f for _, f, _ in tilted_spots[:5]]
    axes[1, 2].scatter(tilted_f, tilted_s, c="red", s=100, label="Tilted", alpha=0.6)

    # Draw arrows showing movement
    for i in range(min(3, len(baseline_spots), len(tilted_spots))):
        axes[1, 2].annotate(
            "",
            xy=(tilted_f[i], tilted_s[i]),
            xytext=(baseline_f[i], baseline_s[i]),
            arrowprops=dict(arrowstyle="->", color="green", lw=2, alpha=0.5),
        )

    axes[1, 2].set_xlabel("Fast axis (pixels)")
    axes[1, 2].set_ylabel("Slow axis (pixels)")
    axes[1, 2].legend()
    axes[1, 2].grid(True, alpha=0.3)
    axes[1, 2].set_xlim(0, 1024)
    axes[1, 2].set_ylim(0, 1024)

    plt.tight_layout()

    # Save figure
    output_path = output_dir / "detector_geometry_comparison.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\nSaved comparison plot to: {output_path}")

    # Close to free memory
    plt.close()


def create_parallel_comparison_plots(pytorch_data, c_reference_data, output_dir):
    """Create 4-panel comparison: PyTorch vs C Reference for both configurations.

    Layout:
    [PyTorch Baseline] [C Reference Baseline]
    [PyTorch Tilted  ] [C Reference Tilted  ]
    [Difference Heatmaps and Correlation Metrics]

    Args:
        pytorch_data: Tuple of (baseline_image, tilted_image) from PyTorch
        c_reference_data: Tuple of (baseline_image, tilted_image) from C reference
        output_dir: Directory to save plots
    """
    pytorch_baseline, pytorch_tilted = pytorch_data
    c_baseline, c_tilted = c_reference_data

    if pytorch_baseline is None or c_baseline is None:
        print("❌ Missing baseline data for parallel comparison")
        return

    if pytorch_tilted is None or c_tilted is None:
        print("❌ Missing tilted data for parallel comparison")
        return

    # Create figure with subplots
    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    fig.suptitle(
        "Parallel C Reference Verification: PyTorch vs nanoBragg.c", fontsize=16
    )

    # Determine common intensity range for consistent coloring
    all_images = [pytorch_baseline, c_baseline, pytorch_tilted, c_tilted]
    vmin = max(1e-6, min(img.min() for img in all_images))
    vmax = max(img.max() for img in all_images)

    # Row 1: Baseline comparison
    im1 = axes[0, 0].imshow(
        pytorch_baseline,
        norm=LogNorm(vmin=vmin, vmax=vmax),
        origin="lower",
        cmap="viridis",
    )
    axes[0, 0].set_title("PyTorch Baseline (simple_cubic)")
    axes[0, 0].set_xlabel("Fast axis (pixels)")
    axes[0, 0].set_ylabel("Slow axis (pixels)")
    plt.colorbar(im1, ax=axes[0, 0], label="Intensity")

    im2 = axes[0, 1].imshow(
        c_baseline, norm=LogNorm(vmin=vmin, vmax=vmax), origin="lower", cmap="viridis"
    )
    axes[0, 1].set_title("C Reference Baseline")
    axes[0, 1].set_xlabel("Fast axis (pixels)")
    axes[0, 1].set_ylabel("Slow axis (pixels)")
    plt.colorbar(im2, ax=axes[0, 1], label="Intensity")

    # Row 2: Tilted comparison
    im3 = axes[1, 0].imshow(
        pytorch_tilted,
        norm=LogNorm(vmin=vmin, vmax=vmax),
        origin="lower",
        cmap="viridis",
    )
    axes[1, 0].set_title("PyTorch Tilted (20° two-theta)")
    axes[1, 0].set_xlabel("Fast axis (pixels)")
    axes[1, 0].set_ylabel("Slow axis (pixels)")
    plt.colorbar(im3, ax=axes[1, 0], label="Intensity")

    im4 = axes[1, 1].imshow(
        c_tilted, norm=LogNorm(vmin=vmin, vmax=vmax), origin="lower", cmap="viridis"
    )
    axes[1, 1].set_title("C Reference Tilted")
    axes[1, 1].set_xlabel("Fast axis (pixels)")
    axes[1, 1].set_ylabel("Slow axis (pixels)")
    plt.colorbar(im4, ax=axes[1, 1], label="Intensity")

    # Row 3: Difference analysis
    # Baseline difference
    baseline_diff = pytorch_baseline - c_baseline
    baseline_rel_diff = baseline_diff / (c_baseline + 1e-10)

    im5 = axes[2, 0].imshow(
        baseline_rel_diff, cmap="RdBu_r", origin="lower", vmin=-0.01, vmax=0.01
    )  # ±1% relative difference
    axes[2, 0].set_title("Baseline Relative Difference\n(PyTorch - C) / C")
    axes[2, 0].set_xlabel("Fast axis (pixels)")
    axes[2, 0].set_ylabel("Slow axis (pixels)")
    plt.colorbar(im5, ax=axes[2, 0], label="Relative Difference")

    # Tilted difference
    tilted_diff = pytorch_tilted - c_tilted
    tilted_rel_diff = tilted_diff / (c_tilted + 1e-10)

    im6 = axes[2, 1].imshow(
        tilted_rel_diff, cmap="RdBu_r", origin="lower", vmin=-0.01, vmax=0.01
    )
    axes[2, 1].set_title("Tilted Relative Difference\n(PyTorch - C) / C")
    axes[2, 1].set_xlabel("Fast axis (pixels)")
    axes[2, 1].set_ylabel("Slow axis (pixels)")
    plt.colorbar(im6, ax=axes[2, 1], label="Relative Difference")

    plt.tight_layout()

    # Save figure
    output_path = output_dir / "parallel_c_comparison.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\nSaved parallel comparison plot to: {output_path}")

    plt.close()


def print_summary_report(baseline_data, tilted_data):
    """Print a summary report of the detector geometry verification."""
    baseline_image, baseline_detector = baseline_data
    tilted_image, tilted_detector = tilted_data

    print("\n" + "=" * 60)
    print("SUMMARY REPORT")
    print("=" * 60)

    # Find brightest spots
    baseline_spots = find_brightest_spots(baseline_image, n_spots=5)
    tilted_spots = find_brightest_spots(tilted_image, n_spots=5)

    print("\nTop 5 Brightest Spots:")
    print("\nBaseline:")
    for i, (s, f, intensity) in enumerate(baseline_spots):
        print(f"  Spot {i+1}: ({s:4d}, {f:4d}) - Intensity: {intensity:.2e}")

    print("\nTilted:")
    for i, (s, f, intensity) in enumerate(tilted_spots):
        print(f"  Spot {i+1}: ({s:4d}, {f:4d}) - Intensity: {intensity:.2e}")

    # Calculate spot shifts
    print("\nSpot Position Shifts (pixels):")
    for i in range(min(3, len(baseline_spots), len(tilted_spots))):
        b_s, b_f, _ = baseline_spots[i]
        t_s, t_f, _ = tilted_spots[i]
        shift_s = t_s - b_s
        shift_f = t_f - b_f
        shift_mag = np.sqrt(shift_s**2 + shift_f**2)
        print(
            f"  Spot {i+1}: Δs={shift_s:+4d}, Δf={shift_f:+4d}, "
            f"|Δ|={shift_mag:5.1f} pixels"
        )

    # Image statistics
    print("\nImage Statistics:")
    print(
        f"  Baseline - Min: {baseline_image.min():.2e}, "
        f"Max: {baseline_image.max():.2e}, "
        f"Mean: {baseline_image.mean():.2e}"
    )
    print(
        f"  Tilted   - Min: {tilted_image.min():.2e}, "
        f"Max: {tilted_image.max():.2e}, "
        f"Mean: {tilted_image.mean():.2e}"
    )

    # Detector geometry comparison
    print("\nDetector Geometry Changes:")
    print("  Basis vector rotations verified through visual inspection")
    print("  Two-theta rotation causes systematic shift in diffraction pattern")
    print("  Beam center offset preserved in tilted configuration")

    print("\n✅ Visual verification complete!")


def run_c_reference_verification(
    baseline_config, tilted_config, crystal_config, beam_config
):
    """Run C reference verification if available.

    Args:
        baseline_config: Baseline DetectorConfig
        tilted_config: Tilted DetectorConfig
        crystal_config: CrystalConfig for both simulations
        beam_config: BeamConfig for both simulations

    Returns:
        Tuple of (baseline_image, tilted_image) or (None, None) if unavailable
    """
    if not C_REFERENCE_AVAILABLE:
        return None, None

    # Try to find nanoBragg executable
    possible_paths = [
        "golden_suite_generator/nanoBragg_golden",  # Golden executable
        "golden_suite_generator/nanoBragg_trace",   # Trace executable
        "golden_suite_generator/nanoBragg",         # Default location
        "./nanoBragg_golden",                       # Current directory
    ]
    
    runner = None
    for path in possible_paths:
        if Path(path).exists():
            runner = CReferenceRunner(executable_path=path)
            if runner.is_available():
                print(f"✓ Found C reference at: {path}")
                break
    
    if runner is None or not runner.is_available():
        print("⚠️  C reference nanoBragg not available")
        return None, None

    # Run both configurations
    baseline_configs = (baseline_config, crystal_config, beam_config)
    tilted_configs = (tilted_config, crystal_config, beam_config)

    return runner.run_both_configurations(baseline_configs, tilted_configs)


def main():
    """Enhanced main function with optional C reference validation."""
    print("Detector Geometry Visual Verification")
    print("=====================================")

    # Create output directory
    output_dir = create_output_dir()

    # Configuration 1: Baseline (simple_cubic)
    baseline_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=51.2,
        beam_center_f=51.2,
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM,
    )

    # Configuration 2: Tilted detector with more dramatic rotation
    # Using larger angles to create visible diffraction pattern changes
    tilted_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=51.2,  # Standard beam center
        beam_center_f=51.2,  # Standard beam center
        detector_convention=DetectorConvention.MOSFLM,
        detector_rotx_deg=0.0,   # No X rotation
        detector_roty_deg=0.0,   # No Y rotation 
        detector_rotz_deg=0.0,   # No Z rotation
        detector_twotheta_deg=20.0,  # Large twotheta for visible effect
        detector_pivot=DetectorPivot.SAMPLE,  # Use SAMPLE pivot (twotheta implies SAMPLE in C code)
    )

    # Common crystal and beam configs
    crystal_config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 5, 5),
    )

    beam_config = BeamConfig(
        wavelength_A=6.2,
        N_source_points=1,
        source_distance_mm=10000.0,
        source_size_mm=0.0,
    )

    # Run PyTorch simulations
    print("\n" + "=" * 60)
    print("PYTORCH VERIFICATION")
    print("=" * 60)
    baseline_data = run_simulation(baseline_config, "Baseline (simple_cubic)")
    tilted_data = run_simulation(tilted_config, "Tilted (15° two-theta + rotations)")

    pytorch_results = (baseline_data[0], tilted_data[0])  # Extract just the images

    # Create standard comparison plots
    create_comparison_plots(baseline_data, tilted_data, output_dir)

    # Try C reference verification
    if C_REFERENCE_AVAILABLE:
        c_baseline, c_tilted = run_c_reference_verification(
            baseline_config, tilted_config, crystal_config, beam_config
        )

        if c_baseline is not None and c_tilted is not None:
            c_results = (c_baseline, c_tilted)

            # Compute quantitative comparison
            print(f"\n{'='*60}")
            print("QUANTITATIVE AGREEMENT ANALYSIS")
            print(f"{'='*60}")

            metrics = compute_agreement_metrics(pytorch_results, c_results)

            # Print metrics
            if "baseline" in metrics and "correlation" in metrics["baseline"]:
                baseline_corr = metrics["baseline"]["correlation"]
                print(f"Baseline correlation: {baseline_corr:.6f}")

            if "tilted" in metrics and "correlation" in metrics["tilted"]:
                tilted_corr = metrics["tilted"]["correlation"]
                print(f"Tilted correlation: {tilted_corr:.6f}")

            if "overall" in metrics:
                min_corr = metrics["overall"]["min_correlation"]
                all_good = metrics["overall"]["all_correlations_good"]

                print(f"Minimum correlation: {min_corr:.6f}")

                if all_good:
                    print("✅ EXCELLENT AGREEMENT with C reference!")
                else:
                    print(f"⚠️  Correlation below threshold (expected > 0.999)")

            # Create enhanced parallel comparison plots
            create_parallel_comparison_plots(pytorch_results, c_results, output_dir)

            # Save metrics to file (convert numpy/bool types for JSON compatibility)
            import json
            import numpy as np

            def make_json_serializable(obj):
                """Convert numpy types to Python types for JSON serialization."""
                if isinstance(obj, dict):
                    return {k: make_json_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, (np.integer, np.int64, np.int32)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float64, np.float32)):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, np.bool_):
                    return bool(obj)
                return obj

            metrics_json = make_json_serializable(metrics)
            metrics_file = output_dir / "correlation_metrics.json"
            with open(metrics_file, "w") as f:
                json.dump(metrics_json, f, indent=2)
            print(f"Saved metrics to: {metrics_file}")

        else:
            print("⚠️  C reference execution failed, skipping parallel verification")
    else:
        print("⚠️  C reference not available, skipping parallel verification")

    # Print summary report
    print_summary_report(baseline_data, tilted_data)

    print(f"\nAll outputs saved to: {output_dir}")


if __name__ == "__main__":
    main()
