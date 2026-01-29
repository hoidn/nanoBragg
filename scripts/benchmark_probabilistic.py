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

from benchmark_probabilistic_presets import PRESETS, BenchmarkScenario

# ---------------------------------------------------------------------------
# Constants derived from refinement_demo_diffuse.py
# ---------------------------------------------------------------------------
TRUE_MOSAIC_SPREAD_DEG = 2.0
INIT_MOSAIC_SPREAD_DEG = 0.5

CELL_ANGLES = (90.0, 90.0, 90.0)
N_CELLS = (3, 3, 3)
DEFAULT_F = 100.0
MOSAIC_SEED = 42


def make_detector_config(scenario: BenchmarkScenario) -> DetectorConfig:
    """Build DetectorConfig from scenario."""
    return DetectorConfig(
        fpixels=scenario.fpixels,
        spixels=scenario.spixels,
        pixel_size_mm=scenario.pixel_size_mm,
        distance_mm=scenario.distance_mm,
    )


def make_beam_config(scenario: BenchmarkScenario) -> BeamConfig:
    """Build BeamConfig from scenario."""
    return BeamConfig(
        wavelength_A=scenario.wavelength_A,
        fluence=1e28,
    )


def resolve_scenario(args) -> BenchmarkScenario:
    """Resolve BenchmarkScenario from CLI args with precedence: explicit flags > --scenario > default."""
    base = PRESETS.get(args.scenario, PRESETS["default"]) if args.scenario else PRESETS["default"]

    return BenchmarkScenario(
        cell_edge_A=args.cell_edge if args.cell_edge is not None else base.cell_edge_A,
        wavelength_A=args.wavelength if args.wavelength is not None else base.wavelength_A,
        distance_mm=args.distance if args.distance is not None else base.distance_mm,
        pixel_size_mm=args.pixel_size if args.pixel_size is not None else base.pixel_size_mm,
        fpixels=args.fpixels if args.fpixels is not None else base.fpixels,
        spixels=args.spixels if args.spixels is not None else base.spixels,
    )


def build_configs(scenario: BenchmarkScenario, device, dtype, mosaic_domains, mosaic_spread_deg):
    """Build Crystal, Detector, and configs for a given domain count/spread."""
    crystal_cfg = CrystalConfig(
        cell_a=scenario.cell_edge_A,
        cell_b=scenario.cell_edge_A,
        cell_c=scenario.cell_edge_A,
        cell_alpha=CELL_ANGLES[0],
        cell_beta=CELL_ANGLES[1],
        cell_gamma=CELL_ANGLES[2],
        N_cells=N_CELLS,
        default_F=DEFAULT_F,
        mosaic_seed=MOSAIC_SEED,
        mosaic_spread_deg=mosaic_spread_deg,
        mosaic_domains=mosaic_domains,
        misset_deg=(0.0, 0.0, 0.0),
    )
    detector_cfg = make_detector_config(scenario)
    beam_cfg = make_beam_config(scenario)

    crystal = Crystal(config=crystal_cfg, device=device, dtype=dtype)
    detector = Detector(config=detector_cfg, device=device, dtype=dtype)
    return crystal, detector, crystal_cfg, beam_cfg


def generate_ground_truth(scenario: BenchmarkScenario, device, dtype):
    """Generate high-fidelity ground truth with many MC domains."""
    print("[ground_truth] Generating with mosaic_domains=50 ...")
    crystal, detector, cfg, beam_cfg = build_configs(
        scenario, device, dtype, mosaic_domains=50, mosaic_spread_deg=TRUE_MOSAIC_SPREAD_DEG
    )
    sim = Simulator(
        crystal=crystal, detector=detector,
        crystal_config=cfg, beam_config=beam_cfg,
        device=device, dtype=dtype,
    )
    gt = sim.run().detach()
    print(f"[ground_truth] shape={gt.shape}, sum={gt.sum().item():.3e}, max={gt.max().item():.3e}")
    return gt


def run_refinement(label, sim_class, scenario, device, dtype, gt_image, iterations,
                   mosaic_domains, optimizer_kwargs, diagnose_gradients=False):
    """Run refinement loop, return loss_history, per_iter_times, final_spread, and gradients."""
    spread_param = torch.tensor(
        INIT_MOSAIC_SPREAD_DEG, dtype=dtype, requires_grad=True
    )
    optimizer = torch.optim.Adam([spread_param], **optimizer_kwargs)

    loss_history = []
    iter_times = []
    gradients = []

    for i in range(iterations):
        t0 = time.perf_counter()

        optimizer.zero_grad()

        cfg = CrystalConfig(
            cell_a=scenario.cell_edge_A,
            cell_b=scenario.cell_edge_A,
            cell_c=scenario.cell_edge_A,
            cell_alpha=CELL_ANGLES[0],
            cell_beta=CELL_ANGLES[1],
            cell_gamma=CELL_ANGLES[2],
            N_cells=N_CELLS,
            default_F=DEFAULT_F,
            mosaic_seed=MOSAIC_SEED,
            mosaic_spread_deg=spread_param,  # type: ignore[arg-type]
            mosaic_domains=mosaic_domains,
            misset_deg=(0.0, 0.0, 0.0),
        )
        detector_cfg = make_detector_config(scenario)
        beam_cfg = make_beam_config(scenario)

        crystal = Crystal(config=cfg, device=device, dtype=dtype)
        detector = Detector(config=detector_cfg, device=device, dtype=dtype)
        sim = sim_class(
            crystal=crystal, detector=detector,
            crystal_config=cfg, beam_config=beam_cfg,
            device=device, dtype=dtype,
        )
        pred = sim.run()
        loss = torch.nn.functional.mse_loss(pred, gt_image)
        loss.backward()

        if diagnose_gradients and spread_param.grad is not None:
            gradients.append(spread_param.grad.abs().item())

        optimizer.step()

        with torch.no_grad():
            spread_param.clamp_(min=0.01, max=10.0)

        dt = time.perf_counter() - t0
        loss_val = loss.item()
        loss_history.append(loss_val)
        iter_times.append(dt)

        if i % 20 == 0 or i == iterations - 1:
            print(f"[{label}][{i:3d}] loss={loss_val:.4e}  spread={spread_param.item():.4f}  time={dt:.3f}s")

    return loss_history, iter_times, spread_param.item(), gradients


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


def run_sweep(sweep_json, scenario, device, dtype, outdir):
    """Run parameter sweep from JSON specification."""
    sweep_data = json.loads(Path(sweep_json).read_text())
    results = []

    for entry in sweep_data:
        entry_scenario_name = entry.get("scenario", "default")
        entry_iterations = entry.get("iterations", 50)

        current_scenario = PRESETS.get(entry_scenario_name, scenario)
        print(f"\n[SWEEP] Running scenario={entry_scenario_name}, iterations={entry_iterations}")

        gt_image = generate_ground_truth(current_scenario, device, dtype)

        torch.manual_seed(7)
        _, bl_times, bl_spread, bl_grads = run_refinement(
            label="sweep_baseline", sim_class=Simulator,
            scenario=current_scenario, device=device, dtype=dtype, gt_image=gt_image,
            iterations=entry_iterations, mosaic_domains=5,
            optimizer_kwargs=dict(lr=0.02), diagnose_gradients=True,
        )

        torch.manual_seed(7)
        pr_losses, pr_times, pr_spread, pr_grads = run_refinement(
            label="sweep_prob", sim_class=ProbabilisticSimulator,
            scenario=current_scenario, device=device, dtype=dtype, gt_image=gt_image,
            iterations=entry_iterations, mosaic_domains=1,
            optimizer_kwargs=dict(lr=0.02), diagnose_gradients=True,
        )

        results.append({
            "scenario": entry_scenario_name,
            "iterations": entry_iterations,
            "baseline": {
                "final_loss": bl_times[-1] if bl_times else None,
                "final_spread": bl_spread,
                "mean_iteration_time": sum(bl_times) / len(bl_times) if bl_times else 0,
                "mean_abs_gradient": sum(bl_grads) / len(bl_grads) if bl_grads else 0,
            },
            "probabilistic": {
                "final_loss": pr_losses[-1] if pr_losses else None,
                "final_spread": pr_spread,
                "mean_iteration_time": sum(pr_times) / len(pr_times) if pr_times else 0,
                "mean_abs_gradient": sum(pr_grads) / len(pr_grads) if pr_grads else 0,
            },
        })

    sweep_out = Path(outdir) / "probabilistic_vs_mc_sweep.json"
    sweep_out.write_text(json.dumps(results, indent=2))
    print(f"\n[SWEEP] Results saved: {sweep_out}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Probabilistic vs MC benchmark")
    parser.add_argument("--iterations", type=int, default=150)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--outdir", default=None)
    parser.add_argument("--plot-only", action="store_true",
                        help="Load existing JSON and regenerate plot without rerunning")

    # Scenario selection
    parser.add_argument("--scenario", choices=list(PRESETS.keys()), default=None,
                        help="Use a named scenario preset")
    parser.add_argument("--cell-edge", type=float, default=None,
                        help="Override cell edge length (Angstroms)")
    parser.add_argument("--wavelength", type=float, default=None,
                        help="Override wavelength (Angstroms)")
    parser.add_argument("--distance", type=float, default=None,
                        help="Override detector distance (mm)")
    parser.add_argument("--pixel-size", type=float, default=None,
                        help="Override pixel size (mm)")
    parser.add_argument("--fpixels", type=int, default=None,
                        help="Override fast-axis pixel count")
    parser.add_argument("--spixels", type=int, default=None,
                        help="Override slow-axis pixel count")

    # Diagnostics
    parser.add_argument("--diagnose-gradients", action="store_true",
                        help="Capture and report gradient magnitudes")
    parser.add_argument("--sweep-json", type=str, default=None,
                        help="Path to JSON file with sweep specification")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print resolved scenario and exit")

    args = parser.parse_args()

    scenario = resolve_scenario(args)

    if args.dry_run:
        print(json.dumps({
            "scenario": args.scenario or "default",
            "resolved": {
                "cell_edge_A": scenario.cell_edge_A,
                "wavelength_A": scenario.wavelength_A,
                "distance_mm": scenario.distance_mm,
                "pixel_size_mm": scenario.pixel_size_mm,
                "fpixels": scenario.fpixels,
                "spixels": scenario.spixels,
            }
        }, indent=2))
        return 0

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

    if args.sweep_json:
        device = torch.device(args.device)
        dtype = torch.float32
        torch.manual_seed(7)
        return run_sweep(args.sweep_json, scenario, device, dtype, outdir)

    device = torch.device(args.device)
    dtype = torch.float32

    torch.manual_seed(7)

    print("=" * 60)
    print("PROBABILISTIC vs MONTE CARLO BENCHMARK")
    print(f"  device={device}, iterations={args.iterations}")
    print(f"  scenario: {args.scenario or 'default'}")
    print(f"  geometry: {scenario.fpixels}x{scenario.spixels} @ {scenario.pixel_size_mm}mm, {scenario.distance_mm}mm distance")
    print(f"  beam: wavelength={scenario.wavelength_A}A, cell_edge={scenario.cell_edge_A}A")
    print(f"  ground truth mosaic_spread={TRUE_MOSAIC_SPREAD_DEG} deg")
    print(f"  init mosaic_spread={INIT_MOSAIC_SPREAD_DEG} deg")
    print("=" * 60)

    gt_image = generate_ground_truth(scenario, device, dtype)

    # --- Baseline MC refinement ---
    print(f"\n{'='*60}")
    print("BASELINE: Simulator (MC, domains=5)")
    print(f"{'='*60}")
    torch.manual_seed(7)
    bl_losses, bl_times, bl_final_spread, bl_grads = run_refinement(
        label="baseline", sim_class=Simulator,
        scenario=scenario, device=device, dtype=dtype, gt_image=gt_image,
        iterations=args.iterations, mosaic_domains=5,
        optimizer_kwargs=dict(lr=0.02), diagnose_gradients=args.diagnose_gradients,
    )

    # --- Probabilistic refinement ---
    print(f"\n{'='*60}")
    print("CHALLENGER: ProbabilisticSimulator (analytic)")
    print(f"{'='*60}")
    torch.manual_seed(7)
    pr_losses, pr_times, pr_final_spread, pr_grads = run_refinement(
        label="probabilistic", sim_class=ProbabilisticSimulator,
        scenario=scenario, device=device, dtype=dtype, gt_image=gt_image,
        iterations=args.iterations, mosaic_domains=1,
        optimizer_kwargs=dict(lr=0.02), diagnose_gradients=args.diagnose_gradients,
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
            "scenario": args.scenario or "default",
            "geometry": {
                "cell_edge_A": scenario.cell_edge_A,
                "wavelength_A": scenario.wavelength_A,
                "distance_mm": scenario.distance_mm,
                "pixel_size_mm": scenario.pixel_size_mm,
                "fpixels": scenario.fpixels,
                "spixels": scenario.spixels,
            },
            "init_spread_deg": INIT_MOSAIC_SPREAD_DEG,
            "true_spread_deg": TRUE_MOSAIC_SPREAD_DEG,
            "optimizer": "Adam lr=0.02",
        },
        "speedup": round(speedup, 2),
    }

    if args.diagnose_gradients:
        summary["baseline"]["spread_gradients"] = bl_grads
        summary["probabilistic"]["spread_gradients"] = pr_grads

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

    if args.diagnose_gradients:
        bl_mean_grad = sum(bl_grads) / len(bl_grads) if bl_grads else 0
        pr_mean_grad = sum(pr_grads) / len(pr_grads) if pr_grads else 0
        print(f"  Baseline mean |grad|:      {bl_mean_grad:.4e}")
        print(f"  Probabilistic mean |grad|: {pr_mean_grad:.4e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
