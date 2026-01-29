#!/usr/bin/env python3
"""
Probabilistic Mosaic Benchmark: Monte Carlo vs Analytic Convergence

Compares refinement of mosaic_spread_deg using:
  - Baseline: Simulator with mosaic_domains=5 (fast but noisy MC)
  - Challenger: ProbabilisticSimulator (analytic, smooth gradients)
  - Ground truth: Simulator with mosaic_domains=50

Generates:
  - demo_outputs/probabilistic_vs_mc_loss.png (convergence plot)
  - demo_outputs/probabilistic_vs_mc_summary.json (machine-readable results)

Reference: docs/strategy/mainstrategy.md §4, docs/plans/2026-01-29-probabilistic-simulator-implementation.md Task 3
"""

import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["NANOBRAGG_DISABLE_COMPILE"] = "1"

import argparse
import json
import sys
import time
from pathlib import Path

import torch

from nanobrag_torch.config import BeamConfig, CrystalConfig, DetectorConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.simulators.probabilistic import ProbabilisticSimulator

# ---------------------------------------------------------------------------
# Constants derived from refinement_demo_diffuse.py
# ---------------------------------------------------------------------------
TRUE_MOSAIC_SPREAD_DEG = 2.0
INIT_MOSAIC_SPREAD_DEG = 0.5

FIXED_PARAMS = dict(
    cell_a=100.0,
    cell_b=100.0,
    cell_c=100.0,
    cell_alpha=90.0,
    cell_beta=90.0,
    cell_gamma=90.0,
    N_cells=(3, 3, 3),
    default_F=100.0,
    mosaic_seed=42,
)

DETECTOR_CONFIG = DetectorConfig(
    fpixels=64,
    spixels=64,
    pixel_size_mm=0.1,
    distance_mm=100.0,
)

BEAM_CONFIG = BeamConfig(
    wavelength_A=1.0,
    fluence=1e28,
)


def build_configs(device, dtype, mosaic_domains, mosaic_spread_deg):
    """Build Crystal, Detector, and configs for a given domain count/spread."""
    crystal_cfg = CrystalConfig(
        **FIXED_PARAMS,
        mosaic_spread_deg=mosaic_spread_deg,
        mosaic_domains=mosaic_domains,
        misset_deg=(0.0, 0.0, 0.0),
    )
    crystal = Crystal(config=crystal_cfg, device=device, dtype=dtype)
    detector = Detector(config=DETECTOR_CONFIG, device=device, dtype=dtype)
    return crystal, detector, crystal_cfg


def generate_ground_truth(device, dtype):
    """Generate high-fidelity ground truth with many MC domains."""
    print("[ground_truth] Generating with mosaic_domains=50 ...")
    crystal, detector, cfg = build_configs(
        device, dtype, mosaic_domains=50, mosaic_spread_deg=TRUE_MOSAIC_SPREAD_DEG
    )
    sim = Simulator(
        crystal=crystal, detector=detector,
        crystal_config=cfg, beam_config=BEAM_CONFIG,
        device=device, dtype=dtype,
    )
    gt = sim.run().detach()
    print(f"[ground_truth] shape={gt.shape}, sum={gt.sum().item():.3e}, max={gt.max().item():.3e}")
    return gt


def run_refinement(label, sim_class, device, dtype, gt_image, iterations,
                   mosaic_domains, optimizer_kwargs):
    """Run refinement loop, return loss_history and per_iter_times."""
    spread_param = torch.tensor(
        INIT_MOSAIC_SPREAD_DEG, dtype=dtype, requires_grad=True
    )
    optimizer = torch.optim.Adam([spread_param], **optimizer_kwargs)

    loss_history = []
    iter_times = []

    for i in range(iterations):
        t0 = time.perf_counter()

        optimizer.zero_grad()

        cfg = CrystalConfig(
            **FIXED_PARAMS,
            mosaic_spread_deg=spread_param,
            mosaic_domains=mosaic_domains,
            misset_deg=(0.0, 0.0, 0.0),
        )
        crystal = Crystal(config=cfg, device=device, dtype=dtype)
        detector = Detector(config=DETECTOR_CONFIG, device=device, dtype=dtype)
        sim = sim_class(
            crystal=crystal, detector=detector,
            crystal_config=cfg, beam_config=BEAM_CONFIG,
            device=device, dtype=dtype,
        )
        pred = sim.run()
        loss = torch.nn.functional.mse_loss(pred, gt_image)
        loss.backward()
        optimizer.step()

        with torch.no_grad():
            spread_param.clamp_(min=0.01, max=10.0)

        dt = time.perf_counter() - t0
        loss_val = loss.item()
        loss_history.append(loss_val)
        iter_times.append(dt)

        if i % 20 == 0 or i == iterations - 1:
            print(f"[{label}][{i:3d}] loss={loss_val:.4e}  spread={spread_param.item():.4f}  time={dt:.3f}s")

    return loss_history, iter_times, spread_param.item()


def make_plot(baseline_losses, prob_losses, baseline_times, prob_times, outpath):
    """Generate convergence comparison plot."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.semilogy(baseline_losses, label=f"MC baseline (domains=5), avg {sum(baseline_times)/len(baseline_times):.2f}s/iter", alpha=0.8)
    ax.semilogy(prob_losses, label=f"Probabilistic (analytic), avg {sum(prob_times)/len(prob_times):.2f}s/iter", alpha=0.8)

    ax.set_xlabel("Iteration")
    ax.set_ylabel("MSE Loss (log)")
    ax.set_title("Probabilistic vs Monte Carlo Mosaic Refinement")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    # Annotate final losses
    ax.annotate(f"final={baseline_losses[-1]:.2e}", xy=(len(baseline_losses)-1, baseline_losses[-1]),
                fontsize=8, color="C0")
    ax.annotate(f"final={prob_losses[-1]:.2e}", xy=(len(prob_losses)-1, prob_losses[-1]),
                fontsize=8, color="C1")

    speedup = (sum(baseline_times) / len(baseline_times)) / max(sum(prob_times) / len(prob_times), 1e-9)
    ax.text(0.02, 0.02, f"Speedup: {speedup:.1f}x", transform=ax.transAxes,
            fontsize=10, verticalalignment="bottom",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))

    fig.tight_layout()
    fig.savefig(str(outpath), dpi=150)
    plt.close(fig)
    print(f"Plot saved: {outpath}")


def main():
    parser = argparse.ArgumentParser(description="Probabilistic vs MC benchmark")
    parser.add_argument("--iterations", type=int, default=150)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--outdir", default=None)
    parser.add_argument("--plot-only", action="store_true",
                        help="Load existing JSON and regenerate plot without rerunning")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    outdir = Path(args.outdir) if args.outdir else repo_root / "demo_outputs"
    outdir.mkdir(parents=True, exist_ok=True)

    json_path = outdir / "probabilistic_vs_mc_summary.json"
    png_path = outdir / "probabilistic_vs_mc_loss.png"

    if args.plot_only:
        if not json_path.exists():
            print(f"ERROR: {json_path} not found. Run without --plot-only first.")
            return 1
        data = json.loads(json_path.read_text())
        make_plot(
            data["baseline"]["loss"], data["probabilistic"]["loss"],
            data["baseline"]["per_iteration_seconds"], data["probabilistic"]["per_iteration_seconds"],
            png_path,
        )
        return 0

    device = torch.device(args.device)
    dtype = torch.float32

    torch.manual_seed(7)

    print("=" * 60)
    print("PROBABILISTIC vs MONTE CARLO BENCHMARK")
    print(f"  device={device}, iterations={args.iterations}")
    print(f"  ground truth mosaic_spread={TRUE_MOSAIC_SPREAD_DEG} deg")
    print(f"  init mosaic_spread={INIT_MOSAIC_SPREAD_DEG} deg")
    print("=" * 60)

    gt_image = generate_ground_truth(device, dtype)

    # --- Baseline MC refinement ---
    print(f"\n{'='*60}")
    print("BASELINE: Simulator (MC, domains=5)")
    print(f"{'='*60}")
    torch.manual_seed(7)
    bl_losses, bl_times, bl_final_spread = run_refinement(
        label="baseline", sim_class=Simulator,
        device=device, dtype=dtype, gt_image=gt_image,
        iterations=args.iterations, mosaic_domains=5,
        optimizer_kwargs=dict(lr=0.02),
    )

    # --- Probabilistic refinement ---
    print(f"\n{'='*60}")
    print("CHALLENGER: ProbabilisticSimulator (analytic)")
    print(f"{'='*60}")
    torch.manual_seed(7)
    pr_losses, pr_times, pr_final_spread = run_refinement(
        label="probabilistic", sim_class=ProbabilisticSimulator,
        device=device, dtype=dtype, gt_image=gt_image,
        iterations=args.iterations, mosaic_domains=1,
        optimizer_kwargs=dict(lr=0.02),
    )

    # --- Summary ---
    bl_avg = sum(bl_times) / len(bl_times)
    pr_avg = sum(pr_times) / len(pr_times)
    speedup = bl_avg / max(pr_avg, 1e-9)

    summary = {
        "ground_truth": {"mosaic_spread_deg": TRUE_MOSAIC_SPREAD_DEG, "domains": 50},
        "baseline": {
            "label": "Simulator (MC, domains=5)",
            "loss": bl_losses,
            "per_iteration_seconds": bl_times,
            "total_seconds": sum(bl_times),
            "final_spread_deg": bl_final_spread,
        },
        "probabilistic": {
            "label": "ProbabilisticSimulator (analytic)",
            "loss": pr_losses,
            "per_iteration_seconds": pr_times,
            "total_seconds": sum(pr_times),
            "final_spread_deg": pr_final_spread,
        },
        "config": {
            "iterations": args.iterations,
            "device": str(device),
            "init_spread_deg": INIT_MOSAIC_SPREAD_DEG,
            "true_spread_deg": TRUE_MOSAIC_SPREAD_DEG,
            "detector": "64x64, 0.1mm pixel, 100mm distance",
            "optimizer": "Adam lr=0.02",
        },
        "speedup": round(speedup, 2),
    }

    json_path.write_text(json.dumps(summary, indent=2))
    print(f"\nSummary JSON: {json_path}")

    make_plot(bl_losses, pr_losses, bl_times, pr_times, png_path)

    print(f"\n{'='*60}")
    print("RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"  Baseline final loss:       {bl_losses[-1]:.4e}")
    print(f"  Probabilistic final loss:  {pr_losses[-1]:.4e}")
    print(f"  Baseline avg iter time:    {bl_avg:.3f}s")
    print(f"  Probabilistic avg iter:    {pr_avg:.3f}s")
    print(f"  Speedup:                   {speedup:.1f}x")
    print(f"  Baseline final spread:     {bl_final_spread:.4f} deg (true: {TRUE_MOSAIC_SPREAD_DEG})")
    print(f"  Probabilistic final spread:{pr_final_spread:.4f} deg (true: {TRUE_MOSAIC_SPREAD_DEG})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
