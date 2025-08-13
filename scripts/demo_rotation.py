#!/usr/bin/env python3
"""
Rotation and Mosaicity Demonstration Script for nanoBragg PyTorch

This script showcases the rotation capabilities of the PyTorch nanoBragg implementation,
generating a series of images that demonstrate:
1. No rotation (baseline)
2. Phi rotation series
3. Mosaicity effects (no mosaic vs increasing mosaic spread)

The script saves output images with descriptive names for analysis.
"""

import os
import torch
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Set environment variable for PyTorch
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Add src to path to import nanobrag_torch
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.config import CrystalConfig


def save_image_with_metadata(image, filepath, metadata=None):
    """Save image with matplotlib and add metadata to filename."""
    # Convert to numpy for visualization
    if isinstance(image, torch.Tensor):
        image_np = image.detach().cpu().numpy()
    else:
        image_np = image

    plt.figure(figsize=(8, 8))
    plt.imshow(image_np, origin="lower", cmap="viridis")
    plt.colorbar(label="Intensity")

    # Add metadata to title if provided
    if metadata:
        title_parts = []
        for key, value in metadata.items():
            if isinstance(value, float):
                title_parts.append(f"{key}={value:.1f}")
            else:
                title_parts.append(f"{key}={value}")
        plt.title(", ".join(title_parts))

    plt.xlabel("Fast (pixels)")
    plt.ylabel("Slow (pixels)")
    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Saved: {filepath}")


def demo_no_rotation():
    """Demonstrate baseline case with no rotation."""
    print("\n=== Demo 1: No Rotation (Baseline) ===")

    # Set seed for reproducibility
    torch.manual_seed(42)

    # Create components
    device = torch.device("cpu")
    dtype = torch.float64

    crystal = Crystal(device=device, dtype=dtype)
    detector = Detector(device=device, dtype=dtype)

    # No rotation configuration
    config = CrystalConfig(
        phi_start_deg=0.0,
        phi_steps=1,
        osc_range_deg=0.0,
        mosaic_spread_deg=0.0,  # No mosaicity
        mosaic_domains=1,
    )

    simulator = Simulator(
        crystal, detector, crystal_config=config, device=device, dtype=dtype
    )

    # Generate image
    image = simulator.run()

    # Find brightest spot info
    max_intensity = torch.max(image)
    max_pos = torch.unravel_index(torch.argmax(image), image.shape)

    print(f"Max intensity: {max_intensity:.2f}")
    print(f"Brightest spot at: ({max_pos[0]}, {max_pos[1]})")

    # Save image
    output_dir = Path("demo_outputs")
    output_dir.mkdir(exist_ok=True)

    metadata = {"phi": 0.0, "mosaic": 0.0, "max_int": float(max_intensity)}

    save_image_with_metadata(
        image, output_dir / "01_no_rotation_baseline.png", metadata
    )

    return image


def demo_phi_rotation_series():
    """Demonstrate phi rotation series showing crystal orientation changes."""
    print("\n=== Demo 2: Phi Rotation Series ===")

    # Set seed for reproducibility
    torch.manual_seed(42)

    device = torch.device("cpu")
    dtype = torch.float64

    crystal = Crystal(device=device, dtype=dtype)
    detector = Detector(device=device, dtype=dtype)

    output_dir = Path("demo_outputs")

    # Generate images at different phi angles
    phi_angles = [0, 30, 60, 90, 120, 150]

    for i, phi in enumerate(phi_angles):
        print(f"Generating phi={phi}° image...")

        config = CrystalConfig(
            phi_start_deg=float(phi),
            phi_steps=1,
            osc_range_deg=0.0,
            mosaic_spread_deg=0.1,  # Small mosaic for realistic appearance
            mosaic_domains=5,
        )

        simulator = Simulator(
            crystal, detector, crystal_config=config, device=device, dtype=dtype
        )
        image = simulator.run()

        # Find brightest spot info
        max_intensity = torch.max(image)
        max_pos = torch.unravel_index(torch.argmax(image), image.shape)

        print(
            f"  Phi {phi}°: max_intensity={max_intensity:.2f}, pos=({max_pos[0]}, {max_pos[1]})"
        )

        # Save image
        metadata = {"phi": phi, "mosaic": 0.1, "max_int": float(max_intensity)}

        save_image_with_metadata(
            image, output_dir / f"02_phi_rotation_{i:02d}_{phi:03d}deg.png", metadata
        )


def demo_mosaicity_effects():
    """Demonstrate mosaicity effects showing spot broadening."""
    print("\n=== Demo 3: Mosaicity Effects ===")

    # Set seed for reproducibility
    torch.manual_seed(42)

    device = torch.device("cpu")
    dtype = torch.float64

    crystal = Crystal(device=device, dtype=dtype)
    detector = Detector(device=device, dtype=dtype)

    output_dir = Path("demo_outputs")

    # Test different mosaic spread values
    mosaic_spreads = [0.0, 0.5, 1.0, 2.0, 5.0]

    for i, mosaic_spread in enumerate(mosaic_spreads):
        print(f"Generating mosaic_spread={mosaic_spread}° image...")

        config = CrystalConfig(
            phi_start_deg=0.0,
            phi_steps=1,
            osc_range_deg=0.0,
            mosaic_spread_deg=mosaic_spread,
            mosaic_domains=max(1, int(mosaic_spread * 10)),  # Scale domains with spread
        )

        simulator = Simulator(
            crystal, detector, crystal_config=config, device=device, dtype=dtype
        )
        image = simulator.run()

        # Analyze spot characteristics
        max_intensity = torch.max(image)
        max_pos = torch.unravel_index(torch.argmax(image), image.shape)

        # Simple spot width analysis (FWHM approximation)
        center_y, center_x = max_pos
        try:
            # Get profiles through brightest spot
            h_profile = image[center_y, :]
            v_profile = image[:, center_x]

            # Find approximate FWHM
            half_max = max_intensity / 2
            h_indices = torch.where(h_profile >= half_max)[0]
            v_indices = torch.where(v_profile >= half_max)[0]

            h_width = len(h_indices) if len(h_indices) > 0 else 1
            v_width = len(v_indices) if len(v_indices) > 0 else 1
            avg_width = (h_width + v_width) / 2

        except Exception:
            avg_width = 1

        print(
            f"  Mosaic {mosaic_spread}°: max_intensity={max_intensity:.2f}, avg_width={avg_width:.1f} pixels"
        )

        # Save image
        metadata = {
            "phi": 0.0,
            "mosaic": mosaic_spread,
            "max_int": float(max_intensity),
            "width": float(avg_width),
        }

        save_image_with_metadata(
            image,
            output_dir / f"03_mosaicity_{i:02d}_spread_{mosaic_spread:03.1f}deg.png",
            metadata,
        )


def create_summary_report():
    """Create a summary report of the demonstration."""
    print("\n=== Creating Summary Report ===")

    output_dir = Path("demo_outputs")
    report_file = output_dir / "demo_summary.txt"

    with open(report_file, "w") as f:
        f.write("nanoBragg PyTorch Rotation and Mosaicity Demonstration Summary\n")
        f.write("=" * 60 + "\n\n")

        f.write(
            "This demonstration showcases the rotation capabilities implemented in Phase 2\n"
        )
        f.write("and validated in Phase 3 of the PyTorch nanoBragg development.\n\n")

        f.write("Generated Images:\n")
        f.write("-" * 20 + "\n")
        f.write(
            "01_no_rotation_baseline.png         - Baseline case (phi=0°, mosaic=0°)\n"
        )
        f.write(
            "02_phi_rotation_*_*deg.png          - Phi rotation series (0° to 150°)\n"
        )
        f.write(
            "03_mosaicity_*_spread_*deg.png      - Mosaicity effects (0° to 5° spread)\n\n"
        )

        f.write("Key Observations:\n")
        f.write("-" * 20 + "\n")
        f.write(
            "1. Phi rotation changes spot positions as crystal orientation changes\n"
        )
        f.write("2. Mosaicity broadens spots due to crystal imperfection simulation\n")
        f.write("3. Higher mosaic spread produces more diffuse, broader spots\n")
        f.write("4. All effects are differentiable for gradient-based optimization\n\n")

        f.write("Implementation Details:\n")
        f.write("-" * 20 + "\n")
        f.write("- Crystal rotation via spindle axis (rotation_axis.py)\n")
        f.write("- Mosaic domain generation using Gaussian distribution\n")
        f.write("- Vectorized operations for efficient GPU computation\n")
        f.write("- Maintains differentiability throughout the computation graph\n\n")

        f.write("Next Steps:\n")
        f.write("-" * 20 + "\n")
        f.write("- Use these capabilities for structure refinement\n")
        f.write(
            "- Implement oscillation (phi stepping) for data collection simulation\n"
        )
        f.write("- Add beam divergence and spectral dispersion effects\n")

    print(f"Summary report saved: {report_file}")


def main():
    """Main demonstration function."""
    print("nanoBragg PyTorch Rotation and Mosaicity Demonstration")
    print("=" * 55)

    try:
        # Run demonstrations
        baseline_image = demo_no_rotation()
        demo_phi_rotation_series()
        demo_mosaicity_effects()

        # Create summary
        create_summary_report()

        print("\n✅ All demonstrations completed successfully!")
        print("Check the 'demo_outputs/' directory for generated images and summary.")

    except Exception as e:
        print(f"\n❌ Demonstration failed with error: {e}")
        print("This may be expected if the PyTorch implementation is not yet complete.")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
