#!/usr/bin/env python
"""
Minimal refinement demo: optimize crystal cell parameter against a target pattern.

This script demonstrates the core differentiable refinement workflow in ~100 lines.
Run: KMP_DUPLICATE_LIB_OK=TRUE python scripts/refinement_minimal.py

Optionally load geometry from SMV file:
    python scripts/refinement_minimal.py --smv path/to/image.img
"""

import argparse
import os
import sys
os.environ.setdefault("NANOBRAGG_DISABLE_COMPILE", "1")

import torch
import matplotlib.pyplot as plt

from nanobrag_torch.simulator import Simulator
from nanobrag_torch.config import (
    CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention
)
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector


class SuppressOutput:
    """Context manager to suppress stdout."""
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        return self
    def __exit__(self, *args):
        sys.stdout.close()
        sys.stdout = self._stdout


def load_detector_from_smv(smv_path, device, dtype):
    """Load detector geometry from SMV file header."""
    from nanobrag_torch.io.smv import read_smv
    _, header = read_smv(smv_path)
    config = DetectorConfig(
        distance_mm=float(header.get('DISTANCE', 100.0)),
        pixel_size_mm=float(header.get('PIXEL_SIZE', 0.1)),
        spixels=int(header.get('SIZE2', 256)),
        fpixels=int(header.get('SIZE1', 256)),
        detector_convention=DetectorConvention.MOSFLM
    )
    return Detector(config, device=device, dtype=dtype)


def main():
    parser = argparse.ArgumentParser(description="Minimal cell refinement demo")
    parser.add_argument("--smv", help="Load detector geometry from SMV file")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.float32
    print(f"Device: {device}")

    # Ground truth and initial parameters
    TRUE_CELL_A, INIT_CELL_A = 100.0, 95.0

    # Setup detector (from file or defaults)
    if args.smv:
        print(f"Loading geometry from: {args.smv}")
        detector = load_detector_from_smv(args.smv, device, dtype)
    else:
        detector_config = DetectorConfig(
            distance_mm=100.0, pixel_size_mm=0.1, spixels=256, fpixels=256,
            detector_convention=DetectorConvention.MOSFLM
        )
        detector = Detector(detector_config, device=device, dtype=dtype)

    beam_config = BeamConfig(wavelength_A=1.5)
    crystal_config = CrystalConfig(
        cell_a=TRUE_CELL_A, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5), default_F=100.0
    )

    # Create target with true parameters
    crystal = Crystal(crystal_config, device=device, dtype=dtype)
    with SuppressOutput():
        simulator = Simulator(crystal=crystal, detector=detector, beam_config=beam_config)
        with torch.no_grad():
            target = simulator.run()
    print(f"Target: {target.shape}, max={target.max():.2e}")

    # Initialize refinement: create cell_a as learnable parameter
    cell_a = torch.tensor(INIT_CELL_A, device=device, dtype=dtype, requires_grad=True)

    # Update crystal in-place (efficient - no reallocation needed)
    crystal.cell_a = cell_a

    optimizer = torch.optim.Adam([cell_a], lr=0.5)
    history = []

    print(f"\nRefining cell_a: {INIT_CELL_A:.2f} → {TRUE_CELL_A:.2f} Å")
    print("-" * 40)

    # Refinement loop - crystal.cell_a updates in-place via gradient descent
    for step in range(30):
        optimizer.zero_grad()

        with SuppressOutput():
            simulator = Simulator(crystal=crystal, detector=detector, beam_config=beam_config)
            pattern = simulator.run()

        loss = torch.mean((pattern - target) ** 2)
        loss.backward()
        optimizer.step()

        history.append((cell_a.item(), loss.item()))
        if step % 5 == 0:
            print(f"Step {step:2d}: cell_a={cell_a.item():.3f} Å, loss={loss.item():.2e}")

    print("-" * 40)
    print(f"Final: cell_a={cell_a.item():.3f} Å (error: {abs(cell_a.item()-TRUE_CELL_A):.3f} Å)")

    # Plot convergence
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    steps = range(len(history))
    ax1.plot(steps, [h[0] for h in history], 'b-o', markersize=3)
    ax1.axhline(TRUE_CELL_A, color='g', linestyle='--', label=f'True: {TRUE_CELL_A}')
    ax1.set_xlabel('Step'); ax1.set_ylabel('cell_a (Å)'); ax1.legend()

    ax2.semilogy(steps, [h[1] for h in history], 'r-o', markersize=3)
    ax2.set_xlabel('Step'); ax2.set_ylabel('MSE Loss')

    plt.tight_layout()
    plt.savefig('refinement_result.png', dpi=150)
    print("Saved: refinement_result.png")


if __name__ == "__main__":
    main()
