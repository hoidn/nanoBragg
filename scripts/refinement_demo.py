#!/usr/bin/env python3
"""
Refinement Demo: Mosaic Spread + Orientation Recovery

Demonstrates gradient-based parameter recovery using nanoBragg PyTorch.
This script generates synthetic diffraction data with known parameters,
then recovers those parameters via gradient descent optimization.

Reference: plans/active/refinement-demo.md

Usage:
    python scripts/refinement_demo.py [options]

Options:
    --iterations N    Number of optimization iterations (default: 250)
    --fallback        Use single-parameter (mosaic-only) mode for debugging
    --plot            Generate static visualization (PNG)
    --gif             Generate animated GIF showing refinement progression
    --frame-interval  Save frame every N iterations for GIF (default: 5)
    --fps N           Frames per second for GIF (default: 8)

Examples:
    # Basic run with static plot
    python scripts/refinement_demo.py --plot

    # Full visualization with GIF animation
    python scripts/refinement_demo.py --plot --gif --iterations 150

    # Quick test with fewer iterations
    python scripts/refinement_demo.py --iterations 50 --fallback --plot
"""

import os
from pathlib import Path

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["NANOBRAGG_DISABLE_COMPILE"] = "1"

import argparse
import sys

# Output directory for visualization artifacts
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
OUTPUT_DIR = REPO_ROOT / "demo_outputs"

import torch

from nanobrag_torch.config import BeamConfig, CrystalConfig, DetectorConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

# ============================================================================
# CONFIGURATION
# ============================================================================

# Ground truth parameters to recover
TRUE_MOSAIC_SPREAD = 0.6  # degrees
TRUE_MISSET = (12.0, 8.0, -5.0)  # degrees - tilted orientation for realistic pattern

# Initial guess offset from truth (what we try to recover FROM)
INIT_MISSET_OFFSET = (-2.0, -1.5, 1.5)  # Start a few degrees away from truth

# Fixed parameters (not refined)
# Using orthorhombic cell with misset for non-grid diffraction pattern
# Orthorhombic is easier to optimize than triclinic but still looks realistic
FIXED_PARAMS = dict(
    cell_a=80.0,
    cell_b=95.0,
    cell_c=110.0,
    cell_alpha=90.0,
    cell_beta=90.0,
    cell_gamma=90.0,
    N_cells=(8, 8, 8),
    default_F=100.0,
    mosaic_domains=5,
    mosaic_seed=42,  # CRITICAL: deterministic sampling for gradients
)

# Detector configuration
# Note: 64x64 is tuned for the current learning rates
# For higher resolution visualization, also adjust LRs in run_refinement()
DETECTOR_CONFIG = DetectorConfig(
    fpixels=64,  # Fast axis pixels
    spixels=64,  # Slow axis pixels
    pixel_size_mm=0.1,
    distance_mm=100.0,
)

# Beam configuration
BEAM_CONFIG = BeamConfig(
    wavelength_A=1.0,
    fluence=1e28,
)


def generate_experimental_data(
    device: torch.device,
    dtype: torch.dtype,
    use_fallback: bool = False,
) -> torch.Tensor:
    """Generate synthetic diffraction pattern with ground truth parameters.

    Args:
        device: Torch device for computation
        dtype: Torch dtype for computation
        use_fallback: If True, use identity misset (single-parameter mode)

    Returns:
        Detached tensor containing the "experimental" image
    """
    misset = (0.0, 0.0, 0.0) if use_fallback else TRUE_MISSET

    true_config = CrystalConfig(
        **FIXED_PARAMS,
        mosaic_spread_deg=TRUE_MOSAIC_SPREAD,
        misset_deg=misset,
    )

    crystal = Crystal(config=true_config, device=device, dtype=dtype)
    detector = Detector(config=DETECTOR_CONFIG, device=device, dtype=dtype)
    simulator = Simulator(
        crystal=crystal,
        detector=detector,
        crystal_config=true_config,
        beam_config=BEAM_CONFIG,
        device=device,
        dtype=dtype,
    )

    # Run forward simulation and detach from graph
    experimental_image = simulator.run().detach()

    print("Generated experimental data:")
    print(f"  Shape: {experimental_image.shape}")
    print(f"  Sum: {experimental_image.sum().item():.2e}")
    print(f"  Max: {experimental_image.max().item():.2e}")
    print(f"  True mosaic_spread: {TRUE_MOSAIC_SPREAD}°")
    print(f"  True misset: {misset}")

    return experimental_image


def run_refinement(
    experimental_image: torch.Tensor,
    device: torch.device,
    dtype: torch.dtype,
    n_iterations: int = 100,
    use_fallback: bool = False,
    save_frames: bool = False,
    frame_interval: int = 5,
) -> dict:
    """Run gradient-based refinement to recover parameters.

    Args:
        experimental_image: Target diffraction pattern
        device: Torch device for computation
        dtype: Torch dtype for computation
        n_iterations: Number of optimization iterations
        use_fallback: If True, only refine mosaic spread (not misset)
        save_frames: If True, save predicted images for GIF animation
        frame_interval: Save a frame every N iterations (default: 5)

    Returns:
        Tuple of (history dict, final predicted image, optional frames list)
    """
    # Initialize parameters with wrong values
    init_mosaic = torch.tensor(0.2, dtype=dtype, requires_grad=True)

    if use_fallback:
        # Single-parameter mode: only refine mosaic spread
        params = [init_mosaic]
        init_misset_x = torch.tensor(0.0, dtype=dtype)
        init_misset_y = torch.tensor(0.0, dtype=dtype)
        init_misset_z = torch.tensor(0.0, dtype=dtype)
        # Higher LR for single parameter
        optimizer = torch.optim.Adam(params, lr=0.05)
    else:
        # Full mode: refine mosaic spread and misset angles
        # Start offset from truth (not at zero) to avoid symmetry issues
        init_misset_x = torch.tensor(TRUE_MISSET[0] + INIT_MISSET_OFFSET[0], dtype=dtype, requires_grad=True)
        init_misset_y = torch.tensor(TRUE_MISSET[1] + INIT_MISSET_OFFSET[1], dtype=dtype, requires_grad=True)
        init_misset_z = torch.tensor(TRUE_MISSET[2] + INIT_MISSET_OFFSET[2], dtype=dtype, requires_grad=True)
        # Use separate parameter groups with different learning rates
        # Triclinic cell has more complex loss landscape - use moderate LRs
        optimizer = torch.optim.Adam([
            {"params": [init_mosaic], "lr": 0.01},  # Conservative for mosaic
            {"params": [init_misset_x, init_misset_y, init_misset_z], "lr": 0.05},
        ])

    # History tracking
    history = {
        "iteration": [],
        "loss": [],
        "mosaic_spread": [],
        "misset_x": [],
        "misset_y": [],
        "misset_z": [],
    }

    # Frame storage for GIF animation
    frames = [] if save_frames else None

    print(f"\nInitial parameters:")
    print(f"  mosaic_spread: {init_mosaic.item():.3f}° (true: {TRUE_MOSAIC_SPREAD}°)")
    if not use_fallback:
        print(
            f"  misset: ({init_misset_x.item():.2f}, {init_misset_y.item():.2f}, "
            f"{init_misset_z.item():.2f})° (true: {TRUE_MISSET})"
        )

    # Pre-create detector (doesn't change during refinement)
    detector = Detector(config=DETECTOR_CONFIG, device=device, dtype=dtype)

    # Learning rate scheduler - reduce LR when loss plateaus
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=15, min_lr=1e-4
    )

    print(f"\n{'='*60}")
    print(f"Starting refinement: {n_iterations} iterations")
    print(f"{'='*60}")

    for iteration in range(n_iterations):
        optimizer.zero_grad()

        # Build config with current (differentiable) parameters
        if use_fallback:
            misset_tuple = (0.0, 0.0, 0.0)
        else:
            misset_tuple = (init_misset_x, init_misset_y, init_misset_z)

        current_config = CrystalConfig(
            **FIXED_PARAMS,
            mosaic_spread_deg=init_mosaic,
            misset_deg=misset_tuple,
        )

        # Forward simulation
        crystal = Crystal(config=current_config, device=device, dtype=dtype)
        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            crystal_config=current_config,
            beam_config=BEAM_CONFIG,
            device=device,
            dtype=dtype,
        )
        predicted_image = simulator.run()

        # MSE loss against experimental data
        loss = torch.nn.functional.mse_loss(predicted_image, experimental_image)

        # Backward pass
        loss.backward()

        # Check for gradient issues
        if init_mosaic.grad is None:
            print(f"WARNING: No gradient for mosaic_spread at iteration {iteration}")
        elif not torch.isfinite(init_mosaic.grad):
            print(
                f"WARNING: Non-finite gradient for mosaic_spread at iteration {iteration}"
            )

        # Optimizer step
        optimizer.step()

        # Update learning rate scheduler
        scheduler.step(loss)

        # Enforce physical constraints
        with torch.no_grad():
            init_mosaic.clamp_(min=0.01, max=5.0)  # Mosaic spread must be positive

        # Record history
        history["iteration"].append(iteration)
        history["loss"].append(loss.item())
        history["mosaic_spread"].append(init_mosaic.item())
        history["misset_x"].append(init_misset_x.item())
        history["misset_y"].append(init_misset_y.item())
        history["misset_z"].append(init_misset_z.item())

        # Save frame for GIF animation
        if save_frames and (iteration % frame_interval == 0 or iteration == n_iterations - 1):
            frames.append({
                "iteration": iteration,
                "predicted": predicted_image.detach().cpu().clone(),
                "loss": loss.item(),
                "mosaic": init_mosaic.item(),
                "misset": (init_misset_x.item(), init_misset_y.item(), init_misset_z.item()),
            })

        # Progress reporting
        if iteration % 10 == 0 or iteration == n_iterations - 1:
            msg = f"Iter {iteration:3d}: loss={loss.item():.4e}, mosaic={init_mosaic.item():.3f}°"
            if not use_fallback:
                msg += (
                    f", misset=({init_misset_x.item():+.2f}, "
                    f"{init_misset_y.item():+.2f}, {init_misset_z.item():+.2f})°"
                )
            print(msg)

    # Return history, final predicted image, and optional frames
    return history, predicted_image, frames


def print_results(history: dict, use_fallback: bool = False) -> dict:
    """Print refinement results and compute success metrics.

    Args:
        history: Dictionary containing optimization history
        use_fallback: If True, only mosaic spread was refined

    Returns:
        Dictionary with success metrics
    """
    true_misset = (0.0, 0.0, 0.0) if use_fallback else TRUE_MISSET

    print(f"\n{'='*60}")
    print("REFINEMENT RESULTS")
    print(f"{'='*60}")

    print(
        f"\n{'Parameter':<18} | {'True':>8} | {'Initial':>8} | {'Refined':>8} | {'Error':>8}"
    )
    print("-" * 60)

    mosaic_error = abs(history["mosaic_spread"][-1] - TRUE_MOSAIC_SPREAD)
    init_mosaic_val = history["mosaic_spread"][0]
    print(
        f"{'mosaic_spread (°)':<18} | {TRUE_MOSAIC_SPREAD:>8.3f} | {init_mosaic_val:>8.3f} | "
        f"{history['mosaic_spread'][-1]:>8.3f} | {mosaic_error:>8.3f}"
    )

    misset_errors = []
    if not use_fallback:
        init_misset = (history["misset_x"][0], history["misset_y"][0], history["misset_z"][0])
        for i, (name, true_val) in enumerate(
            [("misset_x", true_misset[0]), ("misset_y", true_misset[1]), ("misset_z", true_misset[2])]
        ):
            refined = history[name][-1]
            error = abs(refined - true_val)
            misset_errors.append(error)
            print(
                f"{name + ' (°)':<18} | {true_val:>8.2f} | {init_misset[i]:>8.2f} | "
                f"{refined:>8.2f} | {error:>8.2f}"
            )

    print(f"\nConvergence:")
    print(f"  Initial loss: {history['loss'][0]:.4e}")
    print(f"  Final loss:   {history['loss'][-1]:.4e}")
    reduction = history["loss"][0] / max(history["loss"][-1], 1e-20)
    print(f"  Reduction:    {reduction:.1f}x")

    # Compute success metrics
    metrics = {
        "loss_reduction": reduction,
        "mosaic_error": mosaic_error,
        "max_misset_error": max(misset_errors) if misset_errors else 0.0,
        "final_loss": history["loss"][-1],
    }

    # Check success criteria
    print(f"\n{'='*60}")
    print("SUCCESS CRITERIA")
    print(f"{'='*60}")

    success = True

    # Criterion 1: Loss decreases by at least 10x
    if reduction >= 10.0:
        print(f"✓ Loss reduction >= 10x: {reduction:.1f}x")
    else:
        print(f"✗ Loss reduction >= 10x: {reduction:.1f}x (FAILED)")
        success = False

    # Criterion 2: Mosaic spread within ±0.1°
    if mosaic_error <= 0.1:
        print(f"✓ Mosaic spread error <= 0.1°: {mosaic_error:.3f}°")
    else:
        print(f"✗ Mosaic spread error <= 0.1°: {mosaic_error:.3f}° (FAILED)")
        success = False

    # Criterion 3: Misset angles within ±1° (if applicable)
    if not use_fallback:
        max_misset_err = max(misset_errors)
        if max_misset_err <= 1.0:
            print(f"✓ Max misset error <= 1°: {max_misset_err:.2f}°")
        else:
            print(f"✗ Max misset error <= 1°: {max_misset_err:.2f}° (FAILED)")
            success = False

    # Criterion 4: No NaN/Inf
    if all(
        val == val and abs(val) != float("inf")  # NaN check and Inf check
        for val in history["loss"]
    ):
        print("✓ No NaN/Inf in loss")
    else:
        print("✗ No NaN/Inf in loss (FAILED)")
        success = False

    print(f"\n{'='*60}")
    if success:
        print("ALL SUCCESS CRITERIA MET")
    else:
        print("SOME CRITERIA FAILED")
    print(f"{'='*60}")

    metrics["success"] = success
    return metrics


def plot_results(
    history: dict,
    experimental_image: torch.Tensor,
    final_image: torch.Tensor,
    use_fallback: bool = False,
    output_path: str = "refinement_demo.png",
) -> None:
    """Generate visualization of refinement results.

    Args:
        history: Dictionary containing optimization history
        experimental_image: Ground truth diffraction pattern
        final_image: Final refined diffraction pattern
        use_fallback: If True, only mosaic spread was refined
        output_path: Path to save the output figure
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("WARNING: matplotlib not available, skipping visualization")
        return

    true_misset = (0.0, 0.0, 0.0) if use_fallback else TRUE_MISSET

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # Row 1: Images
    im0 = axes[0, 0].imshow(
        experimental_image.numpy(), cmap="viridis", origin="lower"
    )
    axes[0, 0].set_title("Experimental (Ground Truth)")
    plt.colorbar(im0, ax=axes[0, 0], fraction=0.046)

    im1 = axes[0, 1].imshow(
        final_image.detach().numpy(), cmap="viridis", origin="lower"
    )
    axes[0, 1].set_title("Refined")
    plt.colorbar(im1, ax=axes[0, 1], fraction=0.046)

    # Difference image
    diff = (final_image.detach() - experimental_image).numpy()
    im2 = axes[0, 2].imshow(diff, cmap="RdBu_r", origin="lower")
    axes[0, 2].set_title("Difference (Refined - Truth)")
    plt.colorbar(im2, ax=axes[0, 2], fraction=0.046)

    # Row 2: Convergence curves
    axes[1, 0].semilogy(history["loss"])
    axes[1, 0].set_xlabel("Iteration")
    axes[1, 0].set_ylabel("MSE Loss")
    axes[1, 0].set_title("Loss Convergence")
    axes[1, 0].grid(True, alpha=0.3)

    axes[1, 1].plot(history["mosaic_spread"], label="Refined", linewidth=2)
    axes[1, 1].axhline(
        TRUE_MOSAIC_SPREAD, color="r", linestyle="--", label="Truth", linewidth=2
    )
    axes[1, 1].set_xlabel("Iteration")
    axes[1, 1].set_ylabel("Mosaic Spread (°)")
    axes[1, 1].set_title("Mosaic Spread Recovery")
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    if not use_fallback:
        axes[1, 2].plot(history["misset_x"], label="misset_x", linewidth=2)
        axes[1, 2].plot(history["misset_y"], label="misset_y", linewidth=2)
        axes[1, 2].plot(history["misset_z"], label="misset_z", linewidth=2)
        axes[1, 2].axhline(true_misset[0], color="C0", linestyle="--", alpha=0.5)
        axes[1, 2].axhline(true_misset[1], color="C1", linestyle="--", alpha=0.5)
        axes[1, 2].axhline(true_misset[2], color="C2", linestyle="--", alpha=0.5)
        axes[1, 2].set_xlabel("Iteration")
        axes[1, 2].set_ylabel("Misset Angles (°)")
        axes[1, 2].set_title("Misset Recovery")
        axes[1, 2].legend()
        axes[1, 2].grid(True, alpha=0.3)
    else:
        axes[1, 2].text(
            0.5, 0.5, "Misset not refined\n(fallback mode)",
            ha="center", va="center", fontsize=14,
            transform=axes[1, 2].transAxes
        )
        axes[1, 2].set_title("Misset (N/A in fallback mode)")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\nVisualization saved to: {output_path}")
    plt.close()


def create_refinement_gif(
    frames: list,
    experimental_image: torch.Tensor,
    output_path: str = "refinement_animation.gif",
    fps: int = 8,
    use_fallback: bool = False,
) -> None:
    """Create animated GIF showing refinement progression.

    Args:
        frames: List of frame dictionaries from run_refinement
        experimental_image: Ground truth diffraction pattern
        output_path: Path to save the output GIF
        fps: Frames per second for animation
        use_fallback: If True, only mosaic spread was refined
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation, PillowWriter
        import numpy as np
    except ImportError:
        print("WARNING: matplotlib not available, skipping GIF creation")
        return

    if not frames:
        print("WARNING: No frames to animate")
        return

    true_misset = (0.0, 0.0, 0.0) if use_fallback else TRUE_MISSET
    exp_np = experimental_image.numpy()

    # Compute global intensity range for consistent colormap
    all_intensities = [exp_np] + [f["predicted"].numpy() for f in frames]
    vmin = min(arr.min() for arr in all_intensities)
    vmax = max(arr.max() for arr in all_intensities)

    # Create figure with 3 panels: Experiment | Model | Difference
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.suptitle("Refinement Progress", fontsize=14, fontweight="bold")

    # Static: Experimental image
    im_exp = axes[0].imshow(exp_np, cmap="viridis", origin="lower", vmin=vmin, vmax=vmax)
    axes[0].set_title("Experiment (Target)")
    axes[0].set_xlabel("Fast axis (pixels)")
    axes[0].set_ylabel("Slow axis (pixels)")
    plt.colorbar(im_exp, ax=axes[0], fraction=0.046, label="Intensity")

    # Dynamic: Model prediction
    im_model = axes[1].imshow(
        frames[0]["predicted"].numpy(), cmap="viridis", origin="lower", vmin=vmin, vmax=vmax
    )
    axes[1].set_title("Model (Predicted)")
    axes[1].set_xlabel("Fast axis (pixels)")
    plt.colorbar(im_model, ax=axes[1], fraction=0.046, label="Intensity")

    # Dynamic: Difference (Experiment - Model)
    diff_data = exp_np - frames[0]["predicted"].numpy()
    # Compute symmetric colormap range for difference images
    all_diffs = [exp_np - f["predicted"].numpy() for f in frames]
    diff_max = max(max(abs(d.min()), abs(d.max())) for d in all_diffs)
    im_diff = axes[2].imshow(
        diff_data, cmap="RdBu_r", origin="lower", vmin=-diff_max, vmax=diff_max
    )
    axes[2].set_title("Residual (Exp - Model)")
    axes[2].set_xlabel("Fast axis (pixels)")
    plt.colorbar(im_diff, ax=axes[2], fraction=0.046, label="Δ Intensity")

    # Text annotation for parameters
    param_text = fig.text(
        0.02, 0.02, "", fontsize=10, family="monospace",
        verticalalignment="bottom", bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8)
    )

    def update(frame_idx):
        frame = frames[frame_idx]
        pred_np = frame["predicted"].numpy()
        diff_np = exp_np - pred_np

        # Update model image
        im_model.set_data(pred_np)
        axes[1].set_title(f"Model (Iter {frame['iteration']})")

        # Update difference image
        im_diff.set_data(diff_np)

        # Update parameter text
        if use_fallback:
            text = (
                f"Iteration: {frame['iteration']}\n"
                f"Loss: {frame['loss']:.3e}\n"
                f"Mosaic: {frame['mosaic']:.3f}° (true: {TRUE_MOSAIC_SPREAD}°)"
            )
        else:
            text = (
                f"Iteration: {frame['iteration']}\n"
                f"Loss: {frame['loss']:.3e}\n"
                f"Mosaic: {frame['mosaic']:.3f}° (true: {TRUE_MOSAIC_SPREAD}°)\n"
                f"Misset X: {frame['misset'][0]:+.2f}° (true: {true_misset[0]:+.1f}°)\n"
                f"Misset Y: {frame['misset'][1]:+.2f}° (true: {true_misset[1]:+.1f}°)\n"
                f"Misset Z: {frame['misset'][2]:+.2f}° (true: {true_misset[2]:+.1f}°)"
            )
        param_text.set_text(text)

        return [im_model, im_diff, param_text]

    plt.tight_layout(rect=[0, 0.08, 1, 0.95])

    # Create animation
    anim = FuncAnimation(
        fig, update, frames=len(frames), interval=1000 // fps, blit=False
    )

    # Save as GIF
    print(f"Creating GIF with {len(frames)} frames at {fps} fps...")
    writer = PillowWriter(fps=fps)
    anim.save(output_path, writer=writer)
    print(f"Animation saved to: {output_path}")
    plt.close()


def main():
    """Main entry point for refinement demo."""
    parser = argparse.ArgumentParser(
        description="Refinement Demo: Gradient-based parameter recovery"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=250,
        help="Number of optimization iterations (default: 250)",
    )
    parser.add_argument(
        "--fallback",
        action="store_true",
        help="Use single-parameter (mosaic-only) mode",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate visualization plots (requires matplotlib)",
    )
    parser.add_argument(
        "--gif",
        action="store_true",
        help="Generate animated GIF of refinement progression",
    )
    parser.add_argument(
        "--frame-interval",
        type=int,
        default=5,
        help="Save a frame every N iterations for GIF (default: 5)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=8,
        help="Frames per second for GIF animation (default: 8)",
    )
    args = parser.parse_args()

    # Setup
    device = torch.device("cpu")
    dtype = torch.float64
    torch.manual_seed(42)

    print("=" * 60)
    print("NANOBRAG PYTORCH REFINEMENT DEMO")
    print("=" * 60)
    print(f"\nDevice: {device}")
    print(f"Dtype: {dtype}")
    print(f"Mode: {'fallback (mosaic-only)' if args.fallback else 'full (mosaic + misset)'}")
    print(f"Iterations: {args.iterations}")

    # Phase 1: Generate experimental data
    print(f"\n{'='*60}")
    print("PHASE 1: Generate Experimental Data")
    print(f"{'='*60}")
    experimental_image = generate_experimental_data(
        device, dtype, use_fallback=args.fallback
    )

    # Phase 2: Run refinement
    print(f"\n{'='*60}")
    print("PHASE 2: Run Gradient-Based Refinement")
    print(f"{'='*60}")
    history, final_image, frames = run_refinement(
        experimental_image,
        device,
        dtype,
        n_iterations=args.iterations,
        use_fallback=args.fallback,
        save_frames=args.gif,
        frame_interval=args.frame_interval,
    )

    # Phase 3: Print results
    metrics = print_results(history, use_fallback=args.fallback)

    # Phase 4: Optional visualization
    if args.plot or args.gif:
        print(f"\n{'='*60}")
        print("PHASE 4: Visualization")
        print(f"{'='*60}")
        OUTPUT_DIR.mkdir(exist_ok=True)

        if args.plot:
            output_path = OUTPUT_DIR / "refinement_demo.png"
            plot_results(
                history,
                experimental_image,
                final_image,
                use_fallback=args.fallback,
                output_path=str(output_path),
            )

        if args.gif and frames:
            gif_path = OUTPUT_DIR / "refinement_animation.gif"
            create_refinement_gif(
                frames,
                experimental_image,
                output_path=str(gif_path),
                fps=args.fps,
                use_fallback=args.fallback,
            )

    # Return exit code based on success
    return 0 if metrics["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
