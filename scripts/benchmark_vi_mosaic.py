#!/usr/bin/env python3
"""
VI Mosaic Benchmark: Monte Carlo vs Analytic vs Variational Inference.

Compares refinement of mosaic_spread_deg using:
  - MC baseline: Simulator with mosaic_domains=5
  - Analytic: ProbabilisticSimulator (Gaussian envelope)
  - VI: VariationalMosaicSimulator with Poisson ELBO

Generates:
  - vi_vs_mc_loss.png (convergence plot)
  - vi_vs_mc_summary.json (machine-readable results)

Reference: docs/strategy/mainstrategy.md §8,
           docs/plans/2026-01-29-vi-mosaic-implementation-plan.md Task 4
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
from nanobrag_torch.simulators.variational_mosaic import VariationalMosaicSimulator
from nanobrag_torch.vi.mosaic_posterior import MosaicPosterior

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TRUE_MOSAIC_SPREAD_DEG = 2.0
INIT_MOSAIC_SPREAD_DEG = 0.5

CELL_ANGLES = (90.0, 90.0, 90.0)
N_CELLS = (3, 3, 3)
DEFAULT_F = 100.0
MOSAIC_SEED = 42

DEFAULT_FPIXELS = 64
DEFAULT_SPIXELS = 64
DEFAULT_PIXEL_SIZE_MM = 0.1
DEFAULT_DISTANCE_MM = 100.0
DEFAULT_WAVELENGTH_A = 1.0
DEFAULT_CELL_EDGE_A = 100.0


def _build_configs(*, cell_edge_A, wavelength_A, distance_mm, pixel_size_mm,
                   fpixels, spixels, mosaic_spread_deg, mosaic_domains,
                   mosaic_seed, device, dtype):
    """Build Crystal, Detector, and config objects."""
    crystal_cfg = CrystalConfig(
        cell_a=cell_edge_A, cell_b=cell_edge_A, cell_c=cell_edge_A,
        cell_alpha=CELL_ANGLES[0], cell_beta=CELL_ANGLES[1], cell_gamma=CELL_ANGLES[2],
        N_cells=N_CELLS, default_F=DEFAULT_F,
        mosaic_seed=mosaic_seed,
        mosaic_spread_deg=mosaic_spread_deg,
        mosaic_domains=mosaic_domains,
        misset_deg=(0.0, 0.0, 0.0),
    )
    detector_cfg = DetectorConfig(
        fpixels=fpixels, spixels=spixels,
        pixel_size_mm=pixel_size_mm, distance_mm=distance_mm,
    )
    beam_cfg = BeamConfig(wavelength_A=wavelength_A, fluence=1e28)
    crystal = Crystal(config=crystal_cfg, device=device, dtype=dtype)
    detector = Detector(config=detector_cfg, device=device, dtype=dtype)
    return crystal, detector, crystal_cfg, beam_cfg


def _generate_ground_truth(*, cell_edge_A, wavelength_A, distance_mm,
                           pixel_size_mm, fpixels, spixels, device, dtype):
    """Generate high-fidelity ground truth with 50 MC domains."""
    crystal, detector, cfg, beam_cfg = _build_configs(
        cell_edge_A=cell_edge_A, wavelength_A=wavelength_A,
        distance_mm=distance_mm, pixel_size_mm=pixel_size_mm,
        fpixels=fpixels, spixels=spixels,
        mosaic_spread_deg=TRUE_MOSAIC_SPREAD_DEG,
        mosaic_domains=50, mosaic_seed=MOSAIC_SEED,
        device=device, dtype=dtype,
    )
    sim = Simulator(
        crystal=crystal, detector=detector,
        crystal_config=cfg, beam_config=beam_cfg,
        device=device, dtype=dtype,
    )
    result = sim.run()
    if isinstance(result, tuple):
        result = result[0]
    return result.detach()


def _run_mc_refinement(*, iterations, cell_edge_A, wavelength_A, distance_mm,
                       pixel_size_mm, fpixels, spixels, gt_image,
                       device, dtype):
    """Refine mosaic spread with MC baseline (domains=5)."""
    spread_param = torch.tensor(INIT_MOSAIC_SPREAD_DEG, dtype=dtype, requires_grad=True)
    optimizer = torch.optim.Adam([spread_param], lr=0.02)
    losses, times = [], []

    for i in range(iterations):
        t0 = time.perf_counter()
        optimizer.zero_grad()
        crystal, detector, cfg, beam_cfg = _build_configs(
            cell_edge_A=cell_edge_A, wavelength_A=wavelength_A,
            distance_mm=distance_mm, pixel_size_mm=pixel_size_mm,
            fpixels=fpixels, spixels=spixels,
            mosaic_spread_deg=spread_param, mosaic_domains=5,
            mosaic_seed=MOSAIC_SEED, device=device, dtype=dtype,
        )
        sim = Simulator(
            crystal=crystal, detector=detector,
            crystal_config=cfg, beam_config=beam_cfg,
            device=device, dtype=dtype,
        )
        pred = sim.run()
        if isinstance(pred, tuple):
            pred = pred[0]
        loss = torch.nn.functional.mse_loss(pred, gt_image)
        loss.backward()
        optimizer.step()
        with torch.no_grad():
            spread_param.clamp_(min=0.01, max=10.0)
        dt = time.perf_counter() - t0
        losses.append(loss.item())
        times.append(dt)
        if i % 20 == 0 or i == iterations - 1:
            print(f"[MC][{i:3d}] loss={loss.item():.4e} spread={spread_param.item():.4f} dt={dt:.3f}s")

    return losses, times, spread_param.item()


def _run_analytic_refinement(*, iterations, cell_edge_A, wavelength_A,
                             distance_mm, pixel_size_mm, fpixels, spixels,
                             gt_image, device, dtype):
    """Refine mosaic spread with ProbabilisticSimulator (analytic)."""
    spread_param = torch.tensor(INIT_MOSAIC_SPREAD_DEG, dtype=dtype, requires_grad=True)
    optimizer = torch.optim.Adam([spread_param], lr=0.02)
    losses, times = [], []

    for i in range(iterations):
        t0 = time.perf_counter()
        optimizer.zero_grad()
        crystal, detector, cfg, beam_cfg = _build_configs(
            cell_edge_A=cell_edge_A, wavelength_A=wavelength_A,
            distance_mm=distance_mm, pixel_size_mm=pixel_size_mm,
            fpixels=fpixels, spixels=spixels,
            mosaic_spread_deg=spread_param, mosaic_domains=1,
            mosaic_seed=MOSAIC_SEED, device=device, dtype=dtype,
        )
        sim = ProbabilisticSimulator(
            crystal=crystal, detector=detector,
            crystal_config=cfg, beam_config=beam_cfg,
            device=device, dtype=dtype,
        )
        pred = sim.run()
        if isinstance(pred, tuple):
            pred = pred[0]
        loss = torch.nn.functional.mse_loss(pred, gt_image)
        loss.backward()
        optimizer.step()
        with torch.no_grad():
            spread_param.clamp_(min=0.01, max=10.0)
        dt = time.perf_counter() - t0
        losses.append(loss.item())
        times.append(dt)
        if i % 20 == 0 or i == iterations - 1:
            print(f"[Analytic][{i:3d}] loss={loss.item():.4e} spread={spread_param.item():.4f} dt={dt:.3f}s")

    return losses, times, spread_param.item()


def _run_vi_refinement(*, iterations, k_samples, cell_edge_A, wavelength_A,
                       distance_mm, pixel_size_mm, fpixels, spixels,
                       gt_image, device, dtype, diagnostics_log=None,
                       diagnostics_stride=10,
                       kl_weight_start=1.0, kl_weight_end=1.0,
                       kl_warmup_steps=0):
    """Refine mosaic spread with VI (Poisson ELBO)."""
    from nanobrag_torch.vi.poisson_elbo import poisson_elbo, populate_grad_norms

    posterior = MosaicPosterior(
        init_spread_deg=INIT_MOSAIC_SPREAD_DEG, dtype=dtype, device=device,
    )
    crystal, detector, cfg, beam_cfg = _build_configs(
        cell_edge_A=cell_edge_A, wavelength_A=wavelength_A,
        distance_mm=distance_mm, pixel_size_mm=pixel_size_mm,
        fpixels=fpixels, spixels=spixels,
        mosaic_spread_deg=INIT_MOSAIC_SPREAD_DEG, mosaic_domains=1,
        mosaic_seed=None, device=device, dtype=dtype,
    )
    sim = VariationalMosaicSimulator(
        crystal=crystal, detector=detector,
        crystal_config=cfg, beam_config=beam_cfg,
        mosaic_posterior=posterior,
        device=device, dtype=dtype,
    )
    optimizer = torch.optim.Adam(
        [posterior.mu, posterior.rho], lr=0.02,
    )

    from nanobrag_torch.vi.kl_schedule import LinearKLWeightSchedule
    kl_sched = LinearKLWeightSchedule(
        start=kl_weight_start, end=kl_weight_end, warmup_steps=kl_warmup_steps,
    )

    losses, times = [], []
    diag_records = []
    for i in range(iterations):
        t0 = time.perf_counter()
        optimizer.zero_grad()
        beta = kl_sched.weight(step=i, total_iters=iterations)
        capture = diagnostics_log is not None and (i % diagnostics_stride == 0 or i == iterations - 1)
        result = poisson_elbo(
            sim, observed_counts=gt_image, k_samples=k_samples, seed=42 + i,
            kl_weight=beta, return_components=capture,
        )
        if capture:
            loss, diag = result
            loss.backward()
            populate_grad_norms(diag, posterior)
            rec = diag.to_dict()
            rec["iteration"] = i
            diag_records.append(rec)
        else:
            loss = result
            loss.backward()
        optimizer.step()
        dt = time.perf_counter() - t0
        losses.append(loss.item())
        times.append(dt)
        if i % 20 == 0 or i == iterations - 1:
            sigma_deg = posterior.sample(k=1).item() * (180.0 / 3.141592653589793)
            print(f"[VI][{i:3d}] loss={loss.item():.4e} sigma_deg~{sigma_deg:.4f} dt={dt:.3f}s")

    if diagnostics_log is not None and diag_records:
        Path(diagnostics_log).parent.mkdir(parents=True, exist_ok=True)
        Path(diagnostics_log).write_text(json.dumps(diag_records, indent=2))
        print(f"VI diagnostics log: {diagnostics_log}")

    final_sigma = posterior.sample(k=1).item() * (180.0 / 3.141592653589793)
    return losses, times, final_sigma


def _make_plot(mc_losses, analytic_losses, vi_losses, outpath):
    """Generate convergence comparison plot."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.semilogy(mc_losses, label="MC baseline (domains=5)", alpha=0.8)
    ax.semilogy(analytic_losses, label="Analytic (ProbabilisticSimulator)", alpha=0.8)
    ax.semilogy(vi_losses, label="VI (VariationalMosaicSimulator)", alpha=0.8)
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Loss (log)")
    ax.set_title("MC vs Analytic vs VI Mosaic Refinement")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(str(outpath), dpi=150)
    plt.close(fig)
    print(f"Plot saved: {outpath}")


def run_benchmark(
    *,
    iterations: int = 30,
    k_samples: int = 4,
    device: str = "cpu",
    output_dir=None,
    fpixels: int = DEFAULT_FPIXELS,
    spixels: int = DEFAULT_SPIXELS,
    cell_edge_A: float = DEFAULT_CELL_EDGE_A,
    wavelength_A: float = DEFAULT_WAVELENGTH_A,
    distance_mm: float = DEFAULT_DISTANCE_MM,
    pixel_size_mm: float = DEFAULT_PIXEL_SIZE_MM,
    diagnostics_log: str | None = None,
    diagnostics_stride: int = 10,
    kl_weight_start: float = 1.0,
    kl_weight_end: float = 1.0,
    kl_warmup_steps: int = 0,
) -> dict:
    """Run the full MC vs Analytic vs VI benchmark.

    Returns a summary dict. When output_dir is set, writes JSON and PNG artifacts.

    This is the reusable entry point consumed by both CLI and smoke tests.
    """
    dev = torch.device(device)
    dtype = torch.float32

    torch.manual_seed(7)

    geo_kwargs = dict(
        cell_edge_A=cell_edge_A, wavelength_A=wavelength_A,
        distance_mm=distance_mm, pixel_size_mm=pixel_size_mm,
        fpixels=fpixels, spixels=spixels,
    )

    gt_image = _generate_ground_truth(device=dev, dtype=dtype, **geo_kwargs)

    torch.manual_seed(7)
    mc_losses, mc_times, mc_spread = _run_mc_refinement(
        iterations=iterations, gt_image=gt_image, device=dev, dtype=dtype, **geo_kwargs,
    )

    torch.manual_seed(7)
    an_losses, an_times, an_spread = _run_analytic_refinement(
        iterations=iterations, gt_image=gt_image, device=dev, dtype=dtype, **geo_kwargs,
    )

    torch.manual_seed(7)
    vi_losses, vi_times, vi_spread = _run_vi_refinement(
        iterations=iterations, k_samples=k_samples,
        gt_image=gt_image, device=dev, dtype=dtype,
        diagnostics_log=diagnostics_log,
        diagnostics_stride=diagnostics_stride,
        kl_weight_start=kl_weight_start,
        kl_weight_end=kl_weight_end,
        kl_warmup_steps=kl_warmup_steps,
        **geo_kwargs,
    )

    summary = {
        "ground_truth": {"mosaic_spread_deg": TRUE_MOSAIC_SPREAD_DEG, "domains": 50},
        "mc_baseline": {
            "loss": mc_losses, "per_iteration_seconds": mc_times,
            "final_spread_deg": mc_spread,
        },
        "analytic": {
            "loss": an_losses, "per_iteration_seconds": an_times,
            "final_spread_deg": an_spread,
        },
        "vi": {
            "loss": vi_losses, "per_iteration_seconds": vi_times,
            "final_spread_deg": vi_spread, "k_samples": k_samples,
            "kl_weight": {
                "start": kl_weight_start, "end": kl_weight_end,
                "warmup_steps": kl_warmup_steps,
            },
        },
        "config": {
            "iterations": iterations, "device": device,
            "init_spread_deg": INIT_MOSAIC_SPREAD_DEG,
            "true_spread_deg": TRUE_MOSAIC_SPREAD_DEG,
            **geo_kwargs,
        },
    }

    if output_dir is not None:
        outdir = Path(output_dir)
        outdir.mkdir(parents=True, exist_ok=True)
        json_path = outdir / "vi_vs_mc_summary.json"
        json_path.write_text(json.dumps(summary, indent=2))
        print(f"Summary JSON: {json_path}")
        png_path = outdir / "vi_vs_mc_loss.png"
        _make_plot(mc_losses, an_losses, vi_losses, png_path)

    return summary


def main():
    parser = argparse.ArgumentParser(description="MC vs Analytic vs VI mosaic benchmark")
    parser.add_argument("--iterations", type=int, default=150)
    parser.add_argument("--k-samples", type=int, default=4)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--outdir", default=None)
    parser.add_argument("--fpixels", type=int, default=DEFAULT_FPIXELS)
    parser.add_argument("--spixels", type=int, default=DEFAULT_SPIXELS)
    parser.add_argument("--cell-edge", type=float, default=DEFAULT_CELL_EDGE_A)
    parser.add_argument("--wavelength", type=float, default=DEFAULT_WAVELENGTH_A)
    parser.add_argument("--distance", type=float, default=DEFAULT_DISTANCE_MM)
    parser.add_argument("--pixel-size", type=float, default=DEFAULT_PIXEL_SIZE_MM)
    parser.add_argument("--diagnostics-log", default=None,
                        help="Path to write VI diagnostics JSON (captures every --diagnostics-stride iters)")
    parser.add_argument("--diagnostics-stride", type=int, default=10)
    parser.add_argument("--kl-weight-start", type=float, default=1.0)
    parser.add_argument("--kl-weight-end", type=float, default=1.0)
    parser.add_argument("--kl-warmup-steps", type=int, default=0)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    outdir = Path(args.outdir) if args.outdir else repo_root / "demo_outputs"

    run_benchmark(
        iterations=args.iterations,
        k_samples=args.k_samples,
        device=args.device,
        output_dir=str(outdir),
        fpixels=args.fpixels,
        spixels=args.spixels,
        cell_edge_A=args.cell_edge,
        wavelength_A=args.wavelength,
        distance_mm=args.distance,
        pixel_size_mm=args.pixel_size,
        diagnostics_log=args.diagnostics_log,
        diagnostics_stride=args.diagnostics_stride,
        kl_weight_start=args.kl_weight_start,
        kl_weight_end=args.kl_weight_end,
        kl_warmup_steps=args.kl_warmup_steps,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
