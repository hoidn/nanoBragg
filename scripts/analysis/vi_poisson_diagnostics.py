#!/usr/bin/env python3
"""
VI Poisson ELBO diagnostics harness for spread-collapse analysis.

Runs a short VI refinement (≤25 iterations by default), captures per-iteration
diagnostics via ``poisson_elbo(return_components=True)``, and emits:
  - JSON time-series of log-likelihood, KL, sigma stats, gradient norms
  - Markdown summary

Reference: docs/plans/2026-01-29-vi-mosaic-implementation-plan.md Task 7 Step 2
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
from nanobrag_torch.simulators.variational_mosaic import VariationalMosaicSimulator
from nanobrag_torch.vi.mosaic_posterior import MosaicPosterior
from nanobrag_torch.vi.poisson_elbo import poisson_elbo, populate_grad_norms

TRUE_SPREAD_DEG = 2.0
INIT_SPREAD_DEG = 0.5


def run_diagnostics(
    *,
    iterations: int = 25,
    capture_stride: int = 1,
    k_samples: int = 4,
    fpixels: int = 32,
    spixels: int = 32,
    device: str = "cpu",
    output_dir: str | None = None,
    kl_weight_start: float = 1.0,
    kl_weight_end: float = 1.0,
    kl_warmup_steps: int = 0,
) -> list[dict]:
    """Run short VI refinement and capture diagnostics."""
    dev = torch.device(device)
    dtype = torch.float32

    crystal_cfg = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(3, 3, 3), default_F=100.0,
        mosaic_seed=42, mosaic_spread_deg=TRUE_SPREAD_DEG, mosaic_domains=5,
        misset_deg=(0.0, 0.0, 0.0),
    )
    det_cfg = DetectorConfig(fpixels=fpixels, spixels=spixels, pixel_size_mm=0.1, distance_mm=100.0)
    beam_cfg = BeamConfig(wavelength_A=1.0, fluence=1e28)
    crystal_gt = Crystal(crystal_cfg, device=dev, dtype=dtype)
    detector_gt = Detector(det_cfg, device=dev, dtype=dtype)
    sim_gt = Simulator(crystal=crystal_gt, detector=detector_gt, crystal_config=crystal_cfg, beam_config=beam_cfg, device=dev, dtype=dtype)
    with torch.no_grad():
        gt_image = sim_gt.run()
    if isinstance(gt_image, tuple):
        gt_image = gt_image[0]

    # VI setup
    crystal_cfg_vi = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(3, 3, 3), default_F=100.0,
        mosaic_seed=None, mosaic_spread_deg=INIT_SPREAD_DEG, mosaic_domains=1,
        misset_deg=(0.0, 0.0, 0.0),
    )
    crystal_vi = Crystal(crystal_cfg_vi, device=dev, dtype=dtype)
    detector_vi = Detector(det_cfg, device=dev, dtype=dtype)
    posterior = MosaicPosterior(init_spread_deg=INIT_SPREAD_DEG, dtype=dtype, device=dev)
    sim_vi = VariationalMosaicSimulator(
        crystal=crystal_vi, detector=detector_vi,
        crystal_config=crystal_cfg_vi, beam_config=beam_cfg,
        mosaic_posterior=posterior, device=dev, dtype=dtype,
    )
    optimizer = torch.optim.Adam([posterior.mu, posterior.rho], lr=0.02)

    from nanobrag_torch.vi.kl_schedule import LinearKLWeightSchedule
    kl_sched = LinearKLWeightSchedule(
        start=kl_weight_start, end=kl_weight_end, warmup_steps=kl_warmup_steps,
    )

    records = []
    for i in range(iterations):
        t0 = time.perf_counter()
        optimizer.zero_grad()
        beta = kl_sched.weight(step=i, total_iters=iterations)
        loss, diag = poisson_elbo(
            sim_vi, observed_counts=gt_image, k_samples=k_samples,
            seed=42 + i, kl_weight=beta, return_components=True,
        )
        loss.backward()
        populate_grad_norms(diag, posterior)
        optimizer.step()
        dt = time.perf_counter() - t0

        if i % capture_stride == 0 or i == iterations - 1:
            rec = diag.to_dict()
            rec["iteration"] = i
            rec["wall_seconds"] = dt
            rec["kl_weight"] = beta
            records.append(rec)
            print(f"[diag][{i:3d}] loss={diag.loss:.4e} ll={diag.log_likelihood:.4e} "
                  f"kl={diag.kl:.4e} sigma_mean={diag.sigma_mean_deg:.4f}° "
                  f"|∇mu|={diag.mu_grad_norm:.4e} |∇rho|={diag.rho_grad_norm:.4e}")

    if output_dir:
        outdir = Path(output_dir)
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "vi_diagnostics.json").write_text(json.dumps(records, indent=2))
        # Markdown summary
        lines = [
            "# VI Poisson Diagnostics Summary",
            "",
            f"Iterations: {iterations}, k_samples: {k_samples}, "
            f"detector: {spixels}×{fpixels}",
            "",
            "| Iter | Loss | LogLik | KL | σ_mean° | |∇μ| | |∇ρ| |",
            "|------|------|--------|-----|---------|------|------|",
        ]
        for r in records:
            lines.append(
                f"| {r['iteration']} | {r['loss']:.3e} | {r['log_likelihood']:.3e} | "
                f"{r['kl']:.3e} | {r['sigma_mean_deg']:.3f} | "
                f"{r['mu_grad_norm']:.3e} | {r['rho_grad_norm']:.3e} |"
            )
        (outdir / "vi_diagnostics_summary.md").write_text("\n".join(lines) + "\n")
        print(f"Artifacts written to {outdir}")

    return records


def main():
    parser = argparse.ArgumentParser(description="VI Poisson ELBO diagnostics")
    parser.add_argument("--iterations", type=int, default=25)
    parser.add_argument("--capture-stride", type=int, default=1)
    parser.add_argument("--k-samples", type=int, default=4)
    parser.add_argument("--fpixels", type=int, default=32)
    parser.add_argument("--spixels", type=int, default=32)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--outdir", default=None)
    parser.add_argument("--kl-weight-start", type=float, default=1.0)
    parser.add_argument("--kl-weight-end", type=float, default=1.0)
    parser.add_argument("--kl-warmup-steps", type=int, default=0)
    args = parser.parse_args()

    outdir = args.outdir
    if outdir is None:
        outdir = str(Path(__file__).resolve().parent.parent.parent / "demo_outputs" / "vi_diagnostics")

    run_diagnostics(
        iterations=args.iterations,
        capture_stride=args.capture_stride,
        k_samples=args.k_samples,
        fpixels=args.fpixels,
        spixels=args.spixels,
        device=args.device,
        output_dir=outdir,
        kl_weight_start=args.kl_weight_start,
        kl_weight_end=args.kl_weight_end,
        kl_warmup_steps=args.kl_warmup_steps,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
