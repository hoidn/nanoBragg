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

**Step 1: Write the failing test**

```python
# tests/test_vi_mosaic.py

def test_vi_mosaic_k1_matches_fixed_rotation():
    sim = VariationalMosaicSimulator(...)
    img = sim.run(..., k_samples=1, seed=123)
    assert img.shape == (64, 64)
```

**Step 2: Run test to verify it fails**

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_mosaic_k1_matches_fixed_rotation -v`
Expected: FAIL with `ImportError` or missing class.

**Step 3: Write minimal implementation**

```python
# src/nanobrag_torch/simulators/variational_mosaic.py

class VariationalMosaicSimulator(Simulator):
    def run(..., k_samples=4, mosaic_posterior=None, seed=None):
        # build geometry once
        # sample K rotations from mosaic_posterior
        # compute physics per sample and average
        return image
```

**Step 4: Run test to verify it passes**

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_mosaic_k1_matches_fixed_rotation -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/nanobrag_torch/simulators/variational_mosaic.py src/nanobrag_torch/simulators/__init__.py tests/test_vi_mosaic.py
git commit -m "feat: add variational mosaic simulator"
```

---

### Task 3: Add Poisson ELBO training helper + gradcheck

**Files:**
- Create: `src/nanobrag_torch/vi/poisson_elbo.py`
- Test: `tests/test_vi_mosaic.py`

**Step 1: Write the failing test**

```python
# tests/test_vi_mosaic.py

def test_vi_mosaic_gradcheck():
    posterior = MosaicPosterior(device="cpu", dtype=torch.float64)
    loss = poisson_elbo(simulator, posterior, observed)
    loss.backward()
    assert torch.isfinite(posterior.mu.grad).all()
```

**Step 2: Run test to verify it fails**

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_mosaic_gradcheck -v`
Expected: FAIL with missing `poisson_elbo`.

**Step 3: Write minimal implementation**

```python
# src/nanobrag_torch/vi/poisson_elbo.py

def poisson_elbo(simulator, posterior, observed, k_samples=4):
    sim_intensity = simulator.run(..., k_samples=k_samples, mosaic_posterior=posterior)
    log_lik = (observed * torch.log(sim_intensity.clamp_min(1e-12)) - sim_intensity).sum()
    _, kl = posterior.sample_sigma(batch_size=1)
    return -(log_lik - kl)
```

**Step 4: Run test to verify it passes**

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_mosaic_gradcheck -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/nanobrag_torch/vi/poisson_elbo.py tests/test_vi_mosaic.py
git commit -m "feat: add poisson ELBO for VI mosaic"
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
