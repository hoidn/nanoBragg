# Variational Mosaicity Simulator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan.

**Goal:** Replace the analytic mosaicity model with a variational inference (VI) simulator that
samples mosaic rotations via reparameterization and optimizes a per-crystal posterior over
mosaic spread, then deprecate the analytic approach after validation.

**Architecture:** Add a VI posterior module, a new `VariationalMosaicSimulator` that samples K
rotations per forward pass, and a Poisson ELBO training/benchmark script. Preserve the existing
`Simulator` API and keep analytic `ProbabilisticSimulator` available until VI validation passes.

**Tech Stack:** PyTorch (autograd, Generator), pytest, existing nanoBragg torch simulator stack.

---

### Task 1: Add VI posterior module (reparameterized sigma + KL)

**Files:**
- Create: `src/nanobrag_torch/vi/mosaic_posterior.py`
- Test: `tests/test_vi_mosaic.py`

**Step 1: Write the failing test**

```python
# tests/test_vi_mosaic.py

def test_mosaic_posterior_shapes_and_kl():
    posterior = MosaicPosterior(device="cpu", dtype=torch.float64)
    sigma, kl = posterior.sample_sigma(batch_size=4)
    assert sigma.shape == (4,)
    assert torch.isfinite(kl).all()
```

**Step 2: Run test to verify it fails**

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_mosaic_posterior_shapes_and_kl -v`
Expected: FAIL with `NameError: MosaicPosterior is not defined`.

**Step 3: Write minimal implementation**

```python
# src/nanobrag_torch/vi/mosaic_posterior.py

class MosaicPosterior:
    def __init__(self, device, dtype, prior_mu=0.0, prior_sigma=0.5):
        self.mu = torch.nn.Parameter(torch.tensor(0.0, device=device, dtype=dtype))
        self.rho = torch.nn.Parameter(torch.tensor(-2.0, device=device, dtype=dtype))
        self.prior_mu = prior_mu
        self.prior_sigma = prior_sigma

    def sample_sigma(self, batch_size):
        eps = torch.randn(batch_size, device=self.mu.device, dtype=self.mu.dtype)
        sigma = torch.exp(self.mu + torch.nn.functional.softplus(self.rho) * eps)
        kl = self._kl_log_normal(sigma)
        return sigma, kl
```

**Step 4: Run test to verify it passes**

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_mosaic_posterior_shapes_and_kl -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/nanobrag_torch/vi/mosaic_posterior.py tests/test_vi_mosaic.py
git commit -m "feat: add variational mosaic posterior"
```

---

### Task 2: Add VI kernel + simulator (K rotation samples)

**Files:**
- Create: `src/nanobrag_torch/simulators/variational_mosaic.py`
- Modify: `src/nanobrag_torch/simulators/__init__.py`
- Test: `tests/test_vi_mosaic.py`

**Step 1: Write the failing tests**

Extend `tests/test_vi_mosaic.py` with a `TestVariationalMosaicSimulator` suite that keeps detectors tiny (≤4×4) for sub‑second runtime:

```python
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.simulators.variational_mosaic import VariationalMosaicSimulator

class TestVariationalMosaicSimulator:
    def _make_setup(self, *, mosaic_spread_deg=0.5):
        # reuse the _make_tiny_setup helper from tests/test_probabilistic_simulator.py

    def test_k1_matches_deterministic_baseline(self):
        vi = VariationalMosaicSimulator(..., mosaic_posterior=posterior)
        base = Simulator(...)
        img_base = base.run()
        img_vi = vi.run(k_samples=1, mosaic_posterior=posterior, seed=13)
        assert torch.allclose(img_vi, img_base, atol=1e-6, rtol=1e-5)

    def test_multi_sample_average_matches_manual_mean(self):
        seed = 17
        expected_sigmas = posterior.sample(k=2, generator=_make_generator(seed))
        manual = torch.stack([_run_with_sigma(s) for s in expected_sigmas]).mean(0)
        img_vi = vi.run(k_samples=2, mosaic_posterior=posterior, seed=seed)
        assert torch.allclose(img_vi, manual, atol=1e-6, rtol=1e-5)

    def test_requires_positive_k_samples(self):
        vi = VariationalMosaicSimulator(...)
        with pytest.raises(ValueError):
            vi.run(k_samples=0)
```

Add helper utilities inside the test file to avoid duplication: `_make_generator(seed)` returning a CPU generator and `_run_with_sigma` that patches the crystal config and calls the baseline simulator.

**Step 2: Run tests to verify they fail**

Run:
```
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::TestVariationalMosaicSimulator::test_k1_matches_deterministic_baseline -v
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::TestVariationalMosaicSimulator::test_multi_sample_average_matches_manual_mean -v
```
Expected: Both fail because `VariationalMosaicSimulator` does not exist.

**Step 3: Write the implementation**

Create `src/nanobrag_torch/simulators/variational_mosaic.py` with `VariationalMosaicSimulator(Simulator)`:

- Accept an optional `MosaicPosterior` in `__init__`; default to `MosaicPosterior(device=self.device, dtype=self.dtype)`.
- Override `run(..., k_samples=None, mosaic_posterior=None, generator=None, seed=None, reduce="mean", return_samples=False)`; keep base kwargs identical to `Simulator.run` for drop‑in parity.
- Validate `k_samples >= 1` and resolve the posterior argument.
- When `seed` is provided, allocate `gen = torch.Generator(device=self.device)` and call `gen.manual_seed(seed)`; otherwise honor a passed `generator`.
- Sample `sigma_rad = posterior.sample(k_samples, generator=gen)` and convert to degrees via `torch.rad2deg` without detaching.
- For each sample, temporarily patch `self.crystal.config.mosaic_spread_deg` (store original value, use `try/finally`), call `super().run(...)`, and collect the image tensor.
- Stack per‑sample images on dim 0 and reduce via `torch.mean` (or `.sum` when `reduce="sum"`). When `return_samples=True`, also return the sampled sigmas for the ELBO helper.
- Export the class from `src/nanobrag_torch/simulators/__init__.py` and ensure all tensors stay on the caller’s device/dtype with no `.item()` usage.

**Step 4: Run tests to verify they pass**

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::TestVariationalMosaicSimulator -v`
Expected: PASS (the MosaicPosterior suite continues to pass).

**Step 5: Commit**

```bash
git add src/nanobrag_torch/simulators/variational_mosaic.py \
        src/nanobrag_torch/simulators/__init__.py \
        tests/test_vi_mosaic.py
git commit -m "feat: add variational mosaic simulator"
```

---

### Task 3: Add Poisson ELBO training helper + gradcheck

**Files:**
- Create: `src/nanobrag_torch/vi/poisson_elbo.py`
- Test: `tests/test_vi_mosaic.py`

**Step 1: Write the failing tests**

- Extend `tests/test_vi_mosaic.py` with `from nanobrag_torch.vi.poisson_elbo import poisson_elbo` and a helper such as `_make_vi_fixture(device, dtype)` that returns `(sim, posterior, observed)` using `_make_tiny_setup(spixels=4, fpixels=4)` and `observed = sim.run(k_samples=1, seed=11)`.
- Add the `TestPoissonELBO` suite:

```python
class TestPoissonELBO:
    def test_seeded_runs_repeat(self):
        sim, posterior, observed = _make_vi_fixture(device="cpu", dtype=torch.float64)
        loss1 = poisson_elbo(sim, observed_counts=observed, k_samples=3, seed=5)
        loss2 = poisson_elbo(sim, observed_counts=observed, k_samples=3, seed=5)
        assert torch.allclose(loss1, loss2)

    def test_gradients_flow(self):
        sim, posterior, observed = _make_vi_fixture(device="cpu", dtype=torch.float32)
        loss = poisson_elbo(sim, observed_counts=observed, k_samples=2, seed=9)
        loss.backward()
        assert posterior.mu.grad is not None
        assert posterior.rho.grad is not None

    def test_gradcheck_mu_rho(self):
        sim, posterior, observed = _make_vi_fixture(device="cpu", dtype=torch.float64)

        def elbo_with_params(mu, rho):
            posterior.mu = torch.nn.Parameter(mu)
            posterior.rho = torch.nn.Parameter(rho)
            gen = torch.Generator(device="cpu"); gen.manual_seed(123)
            return poisson_elbo(sim, observed, k_samples=2, generator=gen)

        mu = posterior.mu.detach().requires_grad_()
        rho = posterior.rho.detach().requires_grad_()
        torch.autograd.gradcheck(elbo_with_params, (mu, rho), eps=1e-6, atol=1e-4, rtol=1e-4)
```

- Keep tensors small so gradcheck finishes quickly and document that `NANOBRAGG_DISABLE_COMPILE=1` is required for grad tests.

**Step 2: Run tests to verify they fail**

```
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::TestPoissonELBO::test_seeded_runs_repeat -v
NANOBRAGG_DISABLE_COMPILE=1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::TestPoissonELBO::test_gradcheck_mu_rho -v
```

Expected: ImportError/AttributeError because `poisson_elbo` does not exist.

**Step 3: Write minimal implementation**

Create `src/nanobrag_torch/vi/poisson_elbo.py` with:

```python
from __future__ import annotations

import torch

def poisson_elbo(
    simulator,
    observed_counts: torch.Tensor,
    *,
    k_samples: int = 4,
    reduce: str = "mean",
    generator: torch.Generator | None = None,
    seed: int | None = None,
    pixel_batch_size: int | None = None,
    stochastic_pixel_count: int | None = None,
    clamp_eps: float = 1e-12,
    return_components: bool = False,
    **kwargs,
):
    posterior = simulator.mosaic_posterior
    if generator is None and seed is not None:
        generator = torch.Generator(device=simulator.device)
        generator.manual_seed(seed)
    simulated = simulator.run(
        k_samples=k_samples,
        generator=generator,
        reduce=reduce,
        pixel_batch_size=pixel_batch_size,
        stochastic_pixel_count=stochastic_pixel_count,
        **kwargs,
    )
    if isinstance(simulated, tuple):
        simulated = simulated[0]
    observed = observed_counts.to(device=simulator.device, dtype=simulator.dtype)
    sim_clamped = simulated.clamp_min(clamp_eps)
    log_lik = (observed * sim_clamped.log() - simulated).sum()
    kl = posterior.kl_divergence()
    loss = -(log_lik - kl)
    if return_components:
        return loss, {"log_likelihood": log_lik, "kl": kl, "simulated": simulated}
    return loss
```

- Export `poisson_elbo` from `src/nanobrag_torch/vi/__init__.py`.
- Docstring must cite `docs/plans/2026-01-29-vi-mosaic-design.md §Model Definition` and explain it computes the negative Poisson ELBO (likelihood minus KL).

**Step 4: Run tests to verify they pass**

```
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::TestPoissonELBO::test_seeded_runs_repeat -v
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::TestPoissonELBO::test_gradients_flow -v
NANOBRAGG_DISABLE_COMPILE=1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::TestPoissonELBO::test_gradcheck_mu_rho -v
```

**Step 5: Commit**

```bash
git add src/nanobrag_torch/vi/poisson_elbo.py src/nanobrag_torch/vi/__init__.py tests/test_vi_mosaic.py
git commit -m "feat: add Poisson ELBO helper"
```

---

### Task 4: Add VI benchmark script and update strategy docs

**Files:**
- Create: `scripts/benchmark_vi_mosaic.py`
- Modify: `docs/strategy/mainstrategy.md`
- Modify: `docs/development/testing_strategy.md`

**Step 1: Write the failing test (script smoke)**

```python
# tests/test_vi_mosaic.py

def test_benchmark_script_smoke(tmp_path):
    result = run_benchmark(output_dir=tmp_path)
    assert (tmp_path / "vi_vs_mc_loss.png").exists()
```

**Step 2: Run test to verify it fails**

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_benchmark_script_smoke -v`
Expected: FAIL because script does not exist.

**Step 3: Write minimal implementation**

```python
# scripts/benchmark_vi_mosaic.py
# Generate MC, analytic, and VI loss curves; write PNG + JSON summary.
```

**Step 4: Run test to verify it passes**

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_benchmark_script_smoke -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/benchmark_vi_mosaic.py docs/strategy/mainstrategy.md docs/development/testing_strategy.md tests/test_vi_mosaic.py
git commit -m "docs: add VI mosaic benchmark and strategy updates"
```

---

### Task 5: Deprecate analytic probabilistic simulator (post-validation)

**Files:**
- Modify: `src/nanobrag_torch/simulators/probabilistic.py`
- Modify: `README_PYTORCH.md`
- Modify: `docs/plans/2026-01-29-probabilistic-simulator-design.md`

**Step 1: Write the failing test**

```python
# tests/test_vi_mosaic.py

def test_probabilistic_simulator_deprecated_warning():
    with pytest.warns(DeprecationWarning):
        ProbabilisticSimulator(...)
```

**Step 2: Run test to verify it fails**

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_probabilistic_simulator_deprecated_warning -v`
Expected: FAIL because no warning is raised.

**Step 3: Write minimal implementation**

```python
# src/nanobrag_torch/simulators/probabilistic.py
import warnings
warnings.warn("ProbabilisticSimulator is deprecated; use VariationalMosaicSimulator", DeprecationWarning)
```

**Step 4: Run test to verify it passes**

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_probabilistic_simulator_deprecated_warning -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/nanobrag_torch/simulators/probabilistic.py README_PYTORCH.md docs/plans/2026-01-29-probabilistic-simulator-design.md tests/test_vi_mosaic.py
git commit -m "docs: deprecate analytic mosaic simulator after VI"
```

---

### Task 6: Capture canonical VI benchmark artifacts

**Files:**
- Modify: `demo_outputs/vi_vs_mc_loss.png`
- Modify: `demo_outputs/vi_vs_mc_summary.json`
- Create: `plans/active/strat-vi-001/reports/2026-01-29T080653Z/benchmark_vi_mosaic.log`
- Create: `plans/active/strat-vi-001/reports/2026-01-29T080653Z/vi_vs_mc_loss.png`
- Create: `plans/active/strat-vi-001/reports/2026-01-29T080653Z/vi_vs_mc_summary.json`
- Create: `plans/active/strat-vi-001/reports/2026-01-29T080653Z/benchmark_summary.md`

**Step 1: Prep artifact directory**

```bash
mkdir -p plans/active/strat-vi-001/reports/2026-01-29T080653Z
```

Expected: directory exists with no error output.

**Step 2: Run the canonical benchmark command and tee output**

```bash
KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  python scripts/benchmark_vi_mosaic.py --iterations 150 --outdir demo_outputs \
  2>&1 | tee plans/active/strat-vi-001/reports/2026-01-29T080653Z/benchmark_vi_mosaic.log
```

Expected: command exits 0, `demo_outputs/vi_vs_mc_loss.png` and `demo_outputs/vi_vs_mc_summary.json` are regenerated, log records MC/analytic/VI stats.

**Step 3: Archive PNG/JSON under the plan artifacts root**

```bash
cp demo_outputs/vi_vs_mc_loss.png \
   plans/active/strat-vi-001/reports/2026-01-29T080653Z/vi_vs_mc_loss.png
cp demo_outputs/vi_vs_mc_summary.json \
   plans/active/strat-vi-001/reports/2026-01-29T080653Z/vi_vs_mc_summary.json
```

Expected: copies appear under the timestamped directory (use `ls` to confirm).

**Step 4: Summarize convergence metrics**

```bash
python - <<'PY' > plans/active/strat-vi-001/reports/2026-01-29T080653Z/benchmark_summary.md
import json, pathlib
summary = json.loads(pathlib.Path('demo_outputs/vi_vs_mc_summary.json').read_text())
def _final(entry):
    loss = entry['loss'][-1]
    spread = entry.get('final_spread_deg')
    secs = entry['per_iteration_seconds']
    return loss, spread, sum(secs)/len(secs)
mc_loss, mc_spread, mc_dt = _final(summary['mc_baseline'])
an_loss, an_spread, an_dt = _final(summary['analytic'])
vi_loss, vi_spread, vi_dt = _final(summary['vi'])
lines = [
    '# VI Benchmark Summary',
    '',
    '*Artifacts:* demo_outputs/vi_vs_mc_loss.png, demo_outputs/vi_vs_mc_summary.json',
    '',
    f"MC baseline → loss={mc_loss:.3e}, spread={mc_spread:.3f}°, avg_iter={mc_dt:.4f}s",
    f"Analytic → loss={an_loss:.3e}, spread={an_spread:.3f}°, avg_iter={an_dt:.4f}s",
    f"VI → loss={vi_loss:.3e}, spread={vi_spread:.3f}°, avg_iter={vi_dt:.4f}s",
]
pathlib.Path('plans/active/strat-vi-001/reports/2026-01-29T080653Z/benchmark_summary.md').write_text('\n'.join(lines) + '\n')
PY
```

Expected: markdown file captures losses, spreads, and per-iteration timings pulled from the JSON.

**Step 5: Commit artifacts**

```bash
git add demo_outputs/vi_vs_mc_loss.png demo_outputs/vi_vs_mc_summary.json \
        plans/active/strat-vi-001/reports/2026-01-29T080653Z/
git commit -m "docs: archive canonical VI benchmark artifacts"
```
