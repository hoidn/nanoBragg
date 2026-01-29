# VI ELBO Decomposition & Recovery Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Instrument, diagnose, and rebalance the VI Poisson ELBO so we can explain the σ collapse (FND-VI-2026-01) and iterate on fixes (observation scaling, posterior parameterization, alternative objectives) until the canonical benchmark (`docs/strategy/mainstrategy.md §9`) passes the ≥1.5° criterion.

**Architecture:** Extend `poisson_elbo` diagnostics with component-wise gradient tracking, add CLI sweep tooling for observation-count experiments, introduce a non-centered posterior option inside `MosaicPosterior`, and prototype an IWAE-style ELBO so we can compare objectives without rewriting the simulator. All new knobs must flow through `scripts/analysis/vi_poisson_diagnostics.py`, `scripts/benchmark_vi_mosaic.py`, and the JSON/Markdown artifacts consumed by `docs/findings.md`.

**Tech Stack:** PyTorch (autograd, torch.autograd.grad), Python CLI tooling, pytest (`tests/test_vi_mosaic.py`), Matplotlib logging, Markdown docs.

---

### Task 1: Component gradient diagnostics (log-likelihood vs KL)

**Files:**
- Modify: `src/nanobrag_torch/vi/poisson_elbo.py`
- Modify: `tests/test_vi_mosaic.py`
- Modify: `scripts/analysis/vi_poisson_diagnostics.py`
- Modify: `scripts/benchmark_vi_mosaic.py`

**Step 1: Write failing tests**

```python
# tests/test_vi_mosaic.py
def test_poisson_elbo_reports_component_gradients():
    sim, posterior, observed = _make_vi_fixture(device="cpu", dtype=torch.float64)
    loss, diag = poisson_elbo(
        sim,
        observed_counts=observed,
        k_samples=2,
        seed=7,
        return_components=True,
        capture_component_grads=True,
    )
    assert diag.mu_grad_norm_log_lik > 0
    assert diag.kl_grad_norm_mu > 0
    assert diag.mu_grad_norm_total == diag.mu_grad_norm
```

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_poisson_elbo_reports_component_gradients -v`  
Expected: FAIL (`capture_component_grads` arg missing).

**Step 2: Implement component gradient capture**

- Extend `ELBODiagnostics` with new float fields: `mu_grad_norm_log_lik`, `mu_grad_norm_kl`, `rho_grad_norm_log_lik`, `rho_grad_norm_kl`, plus ratio helpers (`likelihood_vs_kl_grad_ratio_mu`, etc.).
- Add `capture_component_grads: bool = False` kwarg to `poisson_elbo`. When `True`, call `torch.autograd.grad` twice (with `retain_graph=True`): once on `log_lik`, once on `kl`. Detach/store absolute norms for μ and ρ before computing `loss`.
- Expose helper `populate_component_grad_norms(diag, posterior)` that fills the *total* grad norms after `loss.backward()`; reuse inside diagnostics to keep existing call-sites simple.

**Step 3: Thread diagnostics through tooling**

- Update `scripts/analysis/vi_poisson_diagnostics.py` to pass `capture_component_grads=True` and include the new fields in JSON + Markdown tables. Add CLI flag `--diagnostics-stride` (default 1) so canonical runs can log every iteration instead of every 10th step; propagate to `_run_vi_refinement` inside `scripts/benchmark_vi_mosaic.py`.
- Update `scripts/benchmark_vi_mosaic.py` so `--diagnostics-log` includes component grad columns.

**Step 4: Update tests + docs**

- Extend `tests/test_vi_mosaic.py::test_vi_diagnostics_snapshot` to ensure the JSON entry includes `mu_grad_norm_log_lik` and `mu_grad_norm_kl`.
- Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k \"poisson_elbo_reports_component_gradients or test_vi_diagnostics_snapshot\" -v`

**Step 5: Commit**

```bash
git add src/nanobrag_torch/vi/poisson_elbo.py tests/test_vi_mosaic.py \
        scripts/analysis/vi_poisson_diagnostics.py scripts/benchmark_vi_mosaic.py
git commit -m "feat: log VI component gradient norms per iteration"
```

---

### Task 2: Observation-count sweep harness

**Files:**
- Modify: `scripts/analysis/vi_poisson_diagnostics.py`
- Modify: `tests/test_vi_mosaic.py`
- Update artifacts: `plans/active/strat-vi-001/reports/<ts>/observation_sweep/`
- Docs: `docs/findings.md`, `docs/strategy/mainstrategy.md` (once sweep evidence exists)

**Step 1: Add failing test scaffolding**

```python
def test_vi_observation_sweep_runs_multiple_means(tmp_path):
    from scripts.analysis.vi_poisson_diagnostics import run_observation_sweep
    records = run_observation_sweep(
        observation_means=[25.0, 100.0],
        iterations=5,
        outdir=tmp_path,
        k_samples=2,
    )
    assert len(records) == 2
    assert {r["observation_target_mean"] for r in records} == {25.0, 100.0}
```

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_observation_sweep_runs_multiple_means -v`  
Expected: FAIL (helper missing).

**Step 2: Implement sweep helper + CLI**

- Add `run_observation_sweep(...)` to `scripts/analysis/vi_poisson_diagnostics.py` that loops over `observation_means`, calls `run_diagnostics` with `capture_stride=1`, and writes per-mean JSON/Markdown plus a combined `observation_sweep.json` + table summarising `log_likelihood`, `kl`, gradient ratios, and σ trajectories.
- Extend CLI with `--observation-mean-grid 25,100,300,1000` and `--observation-grid-outdir`. When set, skip the single-run output and produce the sweep artifacts under `plans/active/strat-vi-001/reports/<ts>/observation_sweep/`.
- Ensure metadata (mean_counts, scale, seed) is stored for each sweep entry.

**Step 3: Update tests**

- Write snapshot-style assertion that the combined JSON contains monotonically increasing `observation_mean_counts`.
- Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_observation_sweep_runs_multiple_means -v`

**Step 4: Capture evidence + documentation**

- Command template:  
  `ts=$(date -u +%Y-%m-%dT%H%M%SZ); outdir=plans/active/strat-vi-001/reports/${ts}/observation_sweep; KMP_DUPLICATE_LIB_OK=TRUE python scripts/analysis/vi_poisson_diagnostics.py --iterations 25 --k-samples 4 --observation-mean-grid 25,100,300,1000 --observation-grid-outdir "$outdir"`  
  Archive the resulting JSON/MD, update `docs/findings.md` (FND-VI-2026-01) with sweep conclusions, and reference them from `docs/strategy/mainstrategy.md §9`.

**Step 5: Commit**

```bash
git add scripts/analysis/vi_poisson_diagnostics.py tests/test_vi_mosaic.py \
        plans/active/strat-vi-001/reports/${ts} docs/findings.md docs/strategy/mainstrategy.md
git commit -m "feat: add VI observation-count sweep diagnostics"
```

---

### Task 3: Non-centered posterior parameterization experiment

**Files:**
- Modify: `src/nanobrag_torch/vi/mosaic_posterior.py`
- Modify: `src/nanobrag_torch/vi/__init__.py`
- Modify: `scripts/benchmark_vi_mosaic.py`
- Modify: `scripts/analysis/vi_poisson_diagnostics.py`
- Modify: `tests/test_vi_mosaic.py`
- Docs: `docs/plans/2026-01-29-vi-mosaic-design.md` (add variational family note)

**Step 1: Write failing tests**

```python
class TestMosaicPosteriorParameterizations:
    def test_noncentered_sampling_positive(self):
        posterior = MosaicPosterior(
            init_spread_deg=0.5,
            parameterization="noncentered",
            dtype=torch.float64,
            device=torch.device("cpu"),
        )
        samples = posterior.sample(k=16, generator=torch.Generator().manual_seed(11))
        assert torch.all(samples > 0)
        assert torch.std(samples) > 0.0
```

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::TestMosaicPosteriorParameterizations::test_noncentered_sampling_positive -v`  
Expected: FAIL (parameterization kwarg missing).

**Step 2: Implement non-centered logic**

- Add `parameterization: Literal["log_normal","noncentered"] = "log_normal"` to `MosaicPosterior.__init__`.
- For the new mode, store `base_sigma = torch.tensor(init_rad)` and `posterior_scale = softplus(rho)` but generate samples via `sigma = torch.nn.functional.softplus(base_sigma + posterior_scale * eps)` (keeps gradients linear w.r.t. μ). Keep KL computation in log-space by transforming samples with `torch.log`.
- Provide `log_prob_sigma()` helper returning `log q(sigma)` for use by Task 4.

**Step 3: Wire into simulators and CLI**

- Update `VariationalMosaicSimulator` (and its import) to accept `posterior_parameterization` and propagate to `MosaicPosterior`.
- Add CLI flags `--posterior-parameterization` to both diagnostics + benchmark scripts so experiments can toggle modes; store parameterization info in JSON.

**Step 4: Tests + gradcheck**

- Extend `tests/test_vi_mosaic.py::TestVariationalMosaicSimulator` to instantiate both parameterizations and verify gradients still flow (run gradcheck on non-centered mode).
- Run targeted suite:  
  `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k \"MosaicPosteriorParameterizations or VariationalMosaicSimulator\" -v`

**Step 5: Commit**

```bash
git add src/nanobrag_torch/vi/mosaic_posterior.py src/nanobrag_torch/vi/__init__.py \
        scripts/benchmark_vi_mosaic.py scripts/analysis/vi_poisson_diagnostics.py \
        tests/test_vi_mosaic.py docs/plans/2026-01-29-vi-mosaic-design.md
git commit -m \"feat: add non-centered posterior option for VI mosaic\"
```

---

### Task 4: Alternative ELBO (IWAE-style) prototype

**Files:**
- Modify: `src/nanobrag_torch/vi/poisson_elbo.py`
- Modify: `src/nanobrag_torch/vi/mosaic_posterior.py` (log-density helpers)
- Modify: `tests/test_vi_mosaic.py`
- Modify: `scripts/analysis/vi_poisson_diagnostics.py`
- Modify: `scripts/benchmark_vi_mosaic.py`
- Docs: `docs/strategy/mainstrategy.md`, `docs/findings.md`

**Step 1: Add failing tests**

```python
def test_poisson_elbo_iwae_matches_standard_when_k1():
    sim, posterior, observed = _make_vi_fixture(device="cpu", dtype=torch.float64)
    loss_std = poisson_elbo(sim, observed_counts=observed, k_samples=1)
    loss_iwae = poisson_elbo(
        sim,
        observed_counts=observed,
        k_samples=1,
        objective=\"iwae\",
    )
    assert torch.allclose(loss_iwae, loss_std, atol=1e-6, rtol=1e-6)
```

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_poisson_elbo_iwae_matches_standard_when_k1 -v`  
Expected: FAIL (objective arg missing).

**Step 2: Implement IWAE objective**

- Extend `poisson_elbo` signature with `objective: Literal["standard","iwae"] = "standard"`. When `iwae`, retain per-sample log-likelihoods (`log_lik_samples`), compute `log_q` via new `posterior.log_prob(samples)` and `log_p` via `posterior.log_prior(samples)`. Evaluate `log_weights = log_lik_samples + log_p - log_q`, then `loss = -torch.logsumexp(log_weights, dim=0) + math.log(k_samples)`. Preserve KL logging by storing analytic KL in diagnostics for comparison.

**Step 3: Surface CLI controls**

- Add `--elbo-objective` to diagnostics + benchmark (default `standard`, options `iwae`), store objective choice plus per-sample stats in JSON, and plot annotation in Markdown.

**Step 4: Regression tests**

- Add `test_poisson_elbo_iwae_requires_multiple_samples` to confirm `objective="iwae"` warns when `k_samples < 2`.
- Extend CLI smoke tests to call `run_benchmark(..., elbo_objective="iwae")` and ensure the summary JSON includes `"vi": {"objective": "iwae"}`.

**Step 5: Evidence + docs**

- Run a short IWAE diagnostic sweep (≤25 iters) and archive under `plans/active/strat-vi-001/reports/<ts>/iwae/`.
- Update `docs/findings.md` (FND-VI-2026-01) with IWAE vs standard comparison, and summarize trade-offs in `docs/strategy/mainstrategy.md §9`.

**Step 6: Commit**

```bash
git add src/nanobrag_torch/vi/poisson_elbo.py src/nanobrag_torch/vi/mosaic_posterior.py \
        scripts/analysis/vi_poisson_diagnostics.py scripts/benchmark_vi_mosaic.py \
        tests/test_vi_mosaic.py docs/findings.md docs/strategy/mainstrategy.md
git commit -m \"feat: add IWAE objective option for VI Poisson ELBO\"
```

---

### Execution Handoff

Plan complete and saved to `docs/plans/2026-01-29-vi-elbo-decomposition.md`.

Execution options:

1. **Subagent-Driven (this session):** Launch `superpowers:subagent-driven-development`, execute each task with interim reviews.
2. **Parallel Session:** Create a fresh session/worktree, load `superpowers:executing-plans`, and run the plan in batches with checkpoints.

Which do you prefer?

