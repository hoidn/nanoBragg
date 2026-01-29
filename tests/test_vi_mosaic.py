"""Tests for the variational mosaic posterior module.

Design reference: docs/plans/2026-01-29-vi-mosaic-design.md §Testing
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import math
import torch
import pytest

from nanobrag_torch.vi.mosaic_posterior import MosaicPosterior


class TestMosaicPosteriorShapesAndKL:
    """Verify shapes, positivity, KL, and gradient flow of MosaicPosterior."""

    @pytest.fixture
    def posterior(self):
        return MosaicPosterior(
            init_spread_deg=0.5,
            prior_spread_deg=1.0,
            prior_log_sigma=1.0,
            dtype=torch.float64,
        )

    def test_sample_shape_single(self, posterior):
        samples = posterior.sample(k=1)
        assert samples.shape == (1,)

    def test_sample_shape_multi(self, posterior):
        samples = posterior.sample(k=8)
        assert samples.shape == (8,)

    def test_samples_positive(self, posterior):
        samples = posterior.sample(k=100)
        assert (samples > 0).all(), "Mosaic spread samples must be positive (exp transform)"

    def test_kl_nonnegative(self, posterior):
        kl = posterior.kl_divergence()
        assert kl.item() >= -1e-7, f"KL divergence should be non-negative, got {kl.item()}"

    def test_kl_zero_when_equal_to_prior(self):
        """KL(q||p) = 0 when q matches the prior exactly."""
        prior_deg = 1.0
        p = MosaicPosterior(
            init_spread_deg=prior_deg,
            prior_spread_deg=prior_deg,
            prior_log_sigma=1.0,
            dtype=torch.float64,
        )
        # Set rho so softplus(rho) = prior_log_sigma = 1.0
        # softplus(x) = log(1 + exp(x)); we want log(1+exp(x))=1 => x = log(e-1) ≈ 0.5413
        with torch.no_grad():
            p.rho.fill_(math.log(math.e - 1.0))
        kl = p.kl_divergence()
        assert abs(kl.item()) < 1e-10, f"KL should be ~0 when q==p, got {kl.item()}"

    def test_forward_returns_tuple(self, posterior):
        samples, kl = posterior(k=4)
        assert samples.shape == (4,)
        assert kl.dim() == 0  # scalar

    def test_gradients_flow_through_sample(self, posterior):
        """Reparameterized samples must carry gradients to mu and rho."""
        gen = torch.Generator(device="cpu")
        gen.manual_seed(42)
        samples = posterior.sample(k=4, generator=gen)
        loss = samples.sum()
        loss.backward()
        assert posterior.mu.grad is not None and posterior.mu.grad.abs() > 0
        assert posterior.rho.grad is not None and posterior.rho.grad.abs() > 0

    def test_gradients_flow_through_kl(self, posterior):
        """KL must carry gradients to mu and rho."""
        kl = posterior.kl_divergence()
        kl.backward()
        assert posterior.mu.grad is not None
        assert posterior.rho.grad is not None

    def test_deterministic_with_generator(self, posterior):
        """Seeded generator produces identical samples."""
        gen1 = torch.Generator(device="cpu")
        gen1.manual_seed(123)
        s1 = posterior.sample(k=5, generator=gen1)

        gen2 = torch.Generator(device="cpu")
        gen2.manual_seed(123)
        s2 = posterior.sample(k=5, generator=gen2)

        assert torch.allclose(s1, s2), "Seeded samples should be deterministic"

    def test_posterior_std_positive(self, posterior):
        """softplus(rho) is always positive."""
        assert posterior.posterior_std.item() > 0


# ---------------------------------------------------------------------------
# TestVariationalMosaicSimulator
# ---------------------------------------------------------------------------
from nanobrag_torch.config import BeamConfig, CrystalConfig, DetectorConfig, CrystalShape
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.simulators.variational_mosaic import VariationalMosaicSimulator


def _make_tiny_setup(device="cpu", dtype=torch.float32, mosaic_spread_deg=0.5,
                     mosaic_domains=1, mosaic_seed=7, spixels=4, fpixels=4):
    """Build a minimal crystal + detector for fast VI tests."""
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0,
        mosaic_spread_deg=mosaic_spread_deg,
        mosaic_domains=mosaic_domains,
        mosaic_seed=mosaic_seed,
        shape=CrystalShape.SQUARE,
    )
    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=spixels,
        fpixels=fpixels,
    )
    beam_config = BeamConfig(
        wavelength_A=6.2,
        fluence=1.25932015286227086360700780544e28,
        nopolar=True,
    )
    crystal = Crystal(crystal_config, device=device, dtype=dtype)
    detector = Detector(detector_config, device=device, dtype=dtype)
    return crystal, detector, crystal_config, detector_config, beam_config


def _make_generator(seed, device="cpu"):
    gen = torch.Generator(device=device)
    gen.manual_seed(seed)
    return gen


class TestVariationalMosaicSimulator:
    """Tests for the K-sample variational mosaic simulator.

    Plan ref: docs/plans/2026-01-29-vi-mosaic-implementation-plan.md Task 2
    """

    def test_k1_matches_deterministic_baseline(self):
        """With k=1, VI simulator should produce the same image as the base
        simulator run with the same mosaic spread value."""
        device = "cpu"
        dtype = torch.float32
        seed = 13

        # Get what sigma the posterior will sample with this seed
        posterior = MosaicPosterior(
            init_spread_deg=0.5, dtype=dtype, device=device,
        )
        gen = _make_generator(seed, device)
        sigma_rad = posterior.sample(k=1, generator=gen)
        sigma_deg = (sigma_rad[0] * (180.0 / torch.pi)).item()

        # Run base simulator with that exact spread
        crystal_b, detector_b, cc_b, dc_b, bc_b = _make_tiny_setup(
            device=device, dtype=dtype,
            mosaic_spread_deg=sigma_deg, mosaic_domains=1, mosaic_seed=None,
        )
        sim_base = Simulator(
            crystal=crystal_b, detector=detector_b,
            crystal_config=cc_b, beam_config=bc_b,
            device=torch.device(device), dtype=dtype,
        )
        img_base = sim_base.run()

        # Run VI simulator with k=1 and same seed
        crystal_vi, detector_vi, cc_vi, dc_vi, bc_vi = _make_tiny_setup(
            device=device, dtype=dtype,
            mosaic_spread_deg=0.5, mosaic_domains=1,
        )
        posterior_vi = MosaicPosterior(
            init_spread_deg=0.5, dtype=dtype, device=device,
        )
        sim_vi = VariationalMosaicSimulator(
            crystal=crystal_vi, detector=detector_vi,
            crystal_config=cc_vi, beam_config=bc_vi,
            mosaic_posterior=posterior_vi,
            device=torch.device(device), dtype=dtype,
        )
        img_vi = sim_vi.run(k_samples=1, seed=seed)

        assert torch.allclose(img_vi, img_base, atol=1e-6, rtol=1e-5), (
            f"k=1 VI image should match baseline. "
            f"Max diff: {(img_vi - img_base).abs().max().item()}"
        )

    def test_multi_sample_average_matches_manual_mean(self):
        """K=2 VI output should equal manual average of two single-sigma runs."""
        device = "cpu"
        dtype = torch.float32
        seed = 17

        posterior = MosaicPosterior(
            init_spread_deg=0.5, dtype=dtype, device=device,
        )
        # Get the two sigma values this seed will produce
        gen = _make_generator(seed, device)
        sigmas_rad = posterior.sample(k=2, generator=gen)

        # Manually run base simulator for each sigma
        manual_images = []
        for i in range(2):
            s_deg = (sigmas_rad[i] * (180.0 / torch.pi)).item()
            crystal, detector, cc, dc, bc = _make_tiny_setup(
                device=device, dtype=dtype,
                mosaic_spread_deg=s_deg, mosaic_domains=1, mosaic_seed=None,
            )
            sim = Simulator(
                crystal=crystal, detector=detector,
                crystal_config=cc, beam_config=bc,
                device=torch.device(device), dtype=dtype,
            )
            manual_images.append(sim.run())

        manual_mean = torch.stack(manual_images, dim=0).mean(dim=0)

        # Run VI simulator with k=2
        crystal_vi, detector_vi, cc_vi, dc_vi, bc_vi = _make_tiny_setup(
            device=device, dtype=dtype,
            mosaic_spread_deg=0.5, mosaic_domains=1,
        )
        posterior_vi = MosaicPosterior(
            init_spread_deg=0.5, dtype=dtype, device=device,
        )
        sim_vi = VariationalMosaicSimulator(
            crystal=crystal_vi, detector=detector_vi,
            crystal_config=cc_vi, beam_config=bc_vi,
            mosaic_posterior=posterior_vi,
            device=torch.device(device), dtype=dtype,
        )
        img_vi = sim_vi.run(k_samples=2, seed=seed)

        assert torch.allclose(img_vi, manual_mean, atol=1e-6, rtol=1e-5), (
            f"k=2 VI image should match manual mean. "
            f"Max diff: {(img_vi - manual_mean).abs().max().item()}"
        )

    def test_requires_positive_k_samples(self):
        """k_samples=0 should raise ValueError."""
        device = "cpu"
        dtype = torch.float32
        crystal, detector, cc, dc, bc = _make_tiny_setup(
            device=device, dtype=dtype,
        )
        sim_vi = VariationalMosaicSimulator(
            crystal=crystal, detector=detector,
            crystal_config=cc, beam_config=bc,
            device=torch.device(device), dtype=dtype,
        )
        with pytest.raises(ValueError):
            sim_vi.run(k_samples=0)


# ---------------------------------------------------------------------------
# TestPoissonELBO
# ---------------------------------------------------------------------------
from nanobrag_torch.vi.poisson_elbo import poisson_elbo, ELBODiagnostics, populate_grad_norms


def _make_vi_fixture(device="cpu", dtype=torch.float64):
    """Build a VariationalMosaicSimulator + observed counts for ELBO tests."""
    crystal, detector, cc, dc, bc = _make_tiny_setup(
        device=device, dtype=dtype, spixels=4, fpixels=4,
        mosaic_spread_deg=0.5, mosaic_domains=1, mosaic_seed=None,
    )
    posterior = MosaicPosterior(
        init_spread_deg=0.5, dtype=dtype, device=device,
    )
    sim = VariationalMosaicSimulator(
        crystal=crystal, detector=detector,
        crystal_config=cc, beam_config=bc,
        mosaic_posterior=posterior,
        device=torch.device(device), dtype=dtype,
    )
    # Generate "observed" counts from the simulator itself (seed=11)
    with torch.no_grad():
        observed = sim.run(k_samples=1, seed=11)
    return sim, posterior, observed


class TestPoissonELBO:
    """Tests for the Poisson ELBO training helper.

    Plan ref: docs/plans/2026-01-29-vi-mosaic-implementation-plan.md Task 3
    """

    def test_kl_weight_scales_loss(self):
        """kl_weight < 1 reduces loss by down-weighting KL term."""
        sim, posterior, observed = _make_vi_fixture(device="cpu", dtype=torch.float64)
        loss_default, diag_default = poisson_elbo(
            sim, observed_counts=observed, k_samples=2, seed=3, return_components=True,
        )
        sim.mosaic_posterior.zero_grad()
        loss_beta, diag_beta = poisson_elbo(
            sim, observed_counts=observed, k_samples=2, seed=3,
            kl_weight=0.25, return_components=True,
        )
        # Loss should equal -(log_lik - 0.25 * kl)
        expected = -(diag_beta.log_likelihood - 0.25 * diag_beta.kl)
        assert torch.allclose(loss_beta, torch.tensor(expected, dtype=loss_beta.dtype), atol=1e-6)
        # With smaller KL weight, loss should be lower (KL penalty reduced)
        assert loss_beta < loss_default
        # kl_weight should be recorded in diagnostics
        assert diag_beta.kl_weight == 0.25
        assert diag_default.kl_weight == 1.0

    def test_seeded_runs_repeat(self):
        """Same seed should produce identical ELBO values."""
        sim, posterior, observed = _make_vi_fixture(device="cpu", dtype=torch.float64)
        loss1 = poisson_elbo(sim, observed_counts=observed, k_samples=3, seed=5)
        # Reset posterior grads between calls
        sim.mosaic_posterior.zero_grad()
        loss2 = poisson_elbo(sim, observed_counts=observed, k_samples=3, seed=5)
        assert torch.allclose(loss1, loss2), (
            f"Seeded ELBO should be deterministic. Got {loss1.item()} vs {loss2.item()}"
        )

    def test_gradients_flow(self):
        """ELBO loss must carry gradients to posterior mu and rho."""
        sim, posterior, observed = _make_vi_fixture(device="cpu", dtype=torch.float32)
        loss = poisson_elbo(sim, observed_counts=observed, k_samples=2, seed=9)
        loss.backward()
        assert posterior.mu.grad is not None, "mu.grad is None"
        assert posterior.rho.grad is not None, "rho.grad is None"

    def test_gradcheck_mu_rho(self):
        """Analytical and numerical gradients must agree for mu and rho."""
        sim, posterior, observed = _make_vi_fixture(device="cpu", dtype=torch.float64)

        def elbo_with_params(mu, rho):
            # Bypass nn.Module.__setattr__ which rejects non-Parameter tensors
            posterior._parameters["mu"] = mu
            posterior._parameters["rho"] = rho
            gen = torch.Generator(device="cpu")
            gen.manual_seed(123)
            return poisson_elbo(sim, observed, k_samples=2, generator=gen)

        mu = posterior.mu.detach().clone().requires_grad_()
        rho = posterior.rho.detach().clone().requires_grad_()
        torch.autograd.gradcheck(
            elbo_with_params, (mu, rho), eps=1e-6, atol=1e-4, rtol=1e-4
        )


# ---------------------------------------------------------------------------
# Benchmark script smoke test
# ---------------------------------------------------------------------------
import sys
from pathlib import Path

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


def test_vi_diagnostics_beta_schedule(tmp_path):
    """Diagnostics harness with KL annealing records correct beta values."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "analysis"))
    from vi_poisson_diagnostics import run_diagnostics

    outdir = tmp_path / "diag"
    records = run_diagnostics(
        iterations=4, capture_stride=1, k_samples=2,
        fpixels=8, spixels=8, output_dir=str(outdir),
        kl_weight_start=0.2, kl_weight_end=1.0, kl_warmup_steps=2,
    )
    betas = [r["kl_weight"] for r in records]
    assert betas[0] == pytest.approx(0.2)
    assert betas[-1] == pytest.approx(1.0)


def test_kl_schedule_hits_start_mid_end():
    """LinearKLWeightSchedule ramps from start to end over warmup_steps."""
    from nanobrag_torch.vi.kl_schedule import LinearKLWeightSchedule

    sched = LinearKLWeightSchedule(start=0.1, end=1.0, warmup_steps=50)
    assert math.isclose(sched.weight(step=0, total_iters=100), 0.1)
    assert math.isclose(sched.weight(step=25, total_iters=100), 0.55, rel_tol=1e-5)
    assert math.isclose(sched.weight(step=60, total_iters=100), 1.0)


def test_probabilistic_simulator_deprecated_warning():
    """ProbabilisticSimulator must emit a DeprecationWarning on construction.

    Plan ref: docs/plans/2026-01-29-vi-mosaic-implementation-plan.md Task 5
    """
    from nanobrag_torch.simulators.probabilistic import ProbabilisticSimulator

    crystal, detector, cc, dc, bc = _make_tiny_setup(device="cpu", dtype=torch.float32)
    with pytest.warns(DeprecationWarning, match="ProbabilisticSimulator is deprecated"):
        ProbabilisticSimulator(
            crystal=crystal,
            detector=detector,
            crystal_config=cc,
            beam_config=bc,
            device=torch.device("cpu"),
            dtype=torch.float32,
        )


def test_benchmark_script_smoke(tmp_path):
    """Smoke test: run_benchmark produces expected artifacts.

    Plan ref: docs/plans/2026-01-29-vi-mosaic-implementation-plan.md Task 4
    """
    from benchmark_vi_mosaic import run_benchmark

    result = run_benchmark(
        iterations=2,
        k_samples=2,
        device="cpu",
        output_dir=str(tmp_path),
        fpixels=4,
        spixels=4,
    )
    assert (tmp_path / "vi_vs_mc_loss.png").exists(), "Missing PNG artifact"
    assert (tmp_path / "vi_vs_mc_summary.json").exists(), "Missing JSON artifact"
    assert "mc_baseline" in result
    assert "analytic" in result
    assert "vi" in result


# ---------------------------------------------------------------------------
# Diagnostics snapshot test (Task 7 Step 3)
# ---------------------------------------------------------------------------
import json as _json


def test_return_components_diagnostics():
    """return_components=True yields ELBODiagnostics with finite scalars and
    an attached simulated tensor.

    Plan ref: docs/plans/2026-01-29-vi-mosaic-implementation-plan.md Task 7 Step 1
    """
    sim, posterior, observed = _make_vi_fixture(device="cpu", dtype=torch.float64)
    loss, diag = poisson_elbo(
        sim, observed_counts=observed, k_samples=2, seed=7, return_components=True,
    )
    assert isinstance(diag, ELBODiagnostics)
    assert math.isfinite(diag.log_likelihood)
    assert math.isfinite(diag.kl)
    assert math.isfinite(diag.loss)
    assert diag.sigma_mean_deg > 0
    assert diag.sigma_std_deg >= 0
    # simulated tensor should be graph-attached
    assert diag.simulated is not None
    assert diag.simulated.requires_grad or loss.requires_grad

    # After backward, populate_grad_norms should fill in grad norms
    loss.backward()
    populate_grad_norms(diag, posterior)
    assert math.isfinite(diag.mu_grad_norm)
    assert math.isfinite(diag.rho_grad_norm)

    # Serialisable dict should not contain the tensor
    d = diag.to_dict()
    assert "simulated" not in d
    assert "log_likelihood" in d


def test_vi_diagnostics_snapshot(tmp_path):
    """5-iteration CPU smoke test: diagnostics JSON with finite gradient norms
    when sigma_deg is clamped below the ground truth.

    Plan ref: docs/plans/2026-01-29-vi-mosaic-implementation-plan.md Task 7 Step 3
    """
    device = "cpu"
    dtype = torch.float32

    # Build tiny setup with ground truth spread = 2.0°
    crystal_gt, det_gt, cc_gt, dc_gt, bc_gt = _make_tiny_setup(
        device=device, dtype=dtype, spixels=32, fpixels=32,
        mosaic_spread_deg=2.0, mosaic_domains=5, mosaic_seed=42,
    )
    sim_gt = Simulator(
        crystal=crystal_gt, detector=det_gt,
        crystal_config=cc_gt, beam_config=bc_gt,
        device=torch.device(device), dtype=dtype,
    )
    with torch.no_grad():
        gt_image = sim_gt.run()
    if isinstance(gt_image, tuple):
        gt_image = gt_image[0]

    # VI setup with init spread clamped below truth (0.5° < 2.0°)
    crystal, detector, cc, dc, bc = _make_tiny_setup(
        device=device, dtype=dtype, spixels=32, fpixels=32,
        mosaic_spread_deg=0.5, mosaic_domains=1, mosaic_seed=None,
    )
    posterior = MosaicPosterior(init_spread_deg=0.5, dtype=dtype, device=device)
    sim_vi = VariationalMosaicSimulator(
        crystal=crystal, detector=detector,
        crystal_config=cc, beam_config=bc,
        mosaic_posterior=posterior,
        device=torch.device(device), dtype=dtype,
    )
    optimizer = torch.optim.Adam([posterior.mu, posterior.rho], lr=0.02)

    records = []
    for i in range(5):
        optimizer.zero_grad()
        loss, diag = poisson_elbo(
            sim_vi, observed_counts=gt_image, k_samples=2, seed=42 + i,
            return_components=True,
        )
        loss.backward()
        populate_grad_norms(diag, posterior)
        optimizer.step()
        records.append(diag.to_dict())

    # Write JSON artifact
    out_json = tmp_path / "vi_diagnostics.json"
    out_json.write_text(_json.dumps(records, indent=2))

    # Verify gradient norms are finite (non-NaN)
    for rec in records:
        assert math.isfinite(rec["mu_grad_norm"]), f"mu_grad_norm not finite: {rec}"
        assert math.isfinite(rec["rho_grad_norm"]), f"rho_grad_norm not finite: {rec}"
