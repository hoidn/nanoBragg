# VI Prior Schedule & Multi-Geometry Diagnostics Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an informative prior schedule for the VI mosaic posterior, expose it through the diagnostics/benchmark CLIs, and run multi-geometry experiments to see whether prior shaping or higher-resolution detectors recover σ ≥ 1.5°.

**Architecture:** Introduce a `LinearPriorSchedule` helper and `MosaicPosterior.set_prior()` hook so diagnostics and benchmarks can update the prior mean/log-σ every iteration. Extend both CLIs with `--prior-*` knobs, propagate metadata into diagnostics outputs, and capture new artifacts for 32×32, 64×64, and 128×128 detectors.

**Tech Stack:** Python 3.11, PyTorch 2.x, `nanobrag_torch.vi` modules, pytest, CLI tooling (`scripts/analysis/vi_poisson_diagnostics.py`, `scripts/benchmark_vi_mosaic.py`).

---

### Task 1: Prior schedule helper + posterior hook

**Files:**
- Create: `src/nanobrag_torch/vi/prior_schedule.py`
- Modify: `src/nanobrag_torch/vi/mosaic_posterior.py`
- Modify: `tests/test_vi_mosaic.py`

**Step 1: Write failing tests**

```python
class TestLinearPriorSchedule:
    def test_interpolates_spread(self):
        sched = LinearPriorSchedule(start_deg=2.0, end_deg=0.5, warmup_steps=10)
        assert math.isclose(sched.spread_deg(step=0), 2.0)
        assert math.isclose(sched.spread_deg(step=5), 1.25, rel_tol=1e-6)
        assert math.isclose(sched.spread_deg(step=10), 0.5)


def test_mosaic_posterior_set_prior_updates_buffers():
    post = MosaicPosterior(init_spread_deg=0.5, dtype=torch.float64)
    post.set_prior(spread_deg=2.0, log_sigma=0.25)
    assert torch.isclose(post.prior_mu, torch.log(torch.tensor(2.0 * math.pi / 180.0)))
    assert torch.isclose(post.prior_log_sigma, torch.tensor(0.25))
```

**Step 2: Run tests to confirm failure**

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k "LinearPriorSchedule or set_prior" -v`
Expected: FAIL (missing helper + setter).

**Step 3: Implement prior helper + setter**

- Create `src/nanobrag_torch/vi/prior_schedule.py` with a `@dataclass LinearPriorSchedule` exposing `spread_deg(step, total_iters=None)` and `log_sigma(step, total_iters=None)`.
- Import it in `src/nanobrag_torch/vi/__init__.py` if needed.
- Add `set_prior(self, *, spread_deg: float | None = None, log_sigma: float | None = None)` to `MosaicPosterior` that updates `prior_mu`/`prior_log_sigma` buffers (degrees→radians for `spread_deg`).
- Document the helper in the module docstring referencing `docs/plans/2026-01-29-vi-prior-geometry.md` §Task 1.

**Step 4: Re-run targeted tests**

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k "LinearPriorSchedule or set_prior" -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/nanobrag_torch/vi/prior_schedule.py src/nanobrag_torch/vi/mosaic_posterior.py \
        tests/test_vi_mosaic.py
git commit -m "feat: add VI prior schedule helper and setter"
```

---

### Task 2: Wire prior schedule through diagnostics & benchmark CLIs

**Files:**
- Modify: `scripts/analysis/vi_poisson_diagnostics.py`
- Modify: `scripts/benchmark_vi_mosaic.py`
- Modify: `src/nanobrag_torch/vi/poisson_elbo.py` (add diagnostic fields if needed)
- Modify: `tests/test_vi_mosaic.py`

**Step 1: Add failing integration test**

```python
def test_vi_diagnostics_records_prior_schedule(tmp_path):
    records = run_diagnostics(
        iterations=4,
        capture_stride=1,
        k_samples=2,
        fpixels=16,
        spixels=16,
        output_dir=None,
        prior_spread_start=2.0,
        prior_spread_end=0.5,
        prior_warmup_steps=3,
        prior_log_sigma=0.2,
    )
    assert records[0]["prior_spread_deg"] == pytest.approx(2.0, abs=1e-6)
    assert records[-1]["prior_spread_deg"] == pytest.approx(0.5, abs=1e-3)
```

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_diagnostics_records_prior_schedule -v`
Expected: FAIL (kwargs missing / records lack keys).

**Step 2: Extend CLIs with prior knobs**

- Update `run_diagnostics` signature + argparse options to accept `prior_spread_start`, `prior_spread_end`, `prior_log_sigma`, `prior_warmup_steps` (defaults to existing behavior: start=end=1.0, warmup=0).
- Instantiate `LinearPriorSchedule` and, inside the training loop, call `posterior.set_prior(spread_deg=schedule.spread_deg(i, iterations), log_sigma=schedule.log_sigma(i))`.
- Store current prior values in `diag` or record dict (`rec["prior_spread_deg"]`, `rec["prior_log_sigma"]`).
- Mirror the same arguments in `run_benchmark`/CLI so the VI path uses the schedule; propagate metadata into `vi_vs_mc_summary.json` under `vi["prior"]`.
- When writing Markdown summaries, add a column for prior spread/log-σ.

**Step 3: Update ELBO diagnostics dataclass if necessary**

- If convenient, add optional `prior_spread_deg`/`prior_log_sigma` fields to `ELBODiagnostics` so tooling can keep everything together.

**Step 4: Update tests**

- Extend smoke tests (`test_benchmark_script_smoke`) to run with `--prior-spread-start 2.0 --prior-spread-end 0.5 --prior-warmup-steps 5`.
- Ensure new records survive JSON serialisation.

**Step 5: Run targeted pytest suite**

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k "prior schedule or diagnostics_records_prior_schedule or benchmark_script_smoke" -v`
Expected: PASS.

**Step 6: Commit**

```bash
git add scripts/analysis/vi_poisson_diagnostics.py scripts/benchmark_vi_mosaic.py \
        src/nanobrag_torch/vi/poisson_elbo.py tests/test_vi_mosaic.py
git commit -m "feat: expose VI prior schedule through diagnostics and benchmark"
```

---

### Task 3: Prior schedule sweeps across detector sizes

**Artifacts:** `plans/active/strat-vi-001/reports/<ts>/prior_schedule/{32x32,64x64,128x128}/`

**Step 1: Prepare artifact directories**

```bash
TS=$(date -u +%Y-%m-%dT%H%M%SZ)
BASE=plans/active/strat-vi-001/reports/${TS}/prior_schedule
mkdir -p "$BASE/32x32" "$BASE/64x64" "$BASE/128x128"
```

**Step 2: Run 32×32 diagnostic sweep**

```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/analysis/vi_poisson_diagnostics.py \
  --iterations 25 --capture-stride 1 --k-samples 4 \
  --fpixels 32 --spixels 32 --observation-mean 25 --observation-normalization mean \
  --observation-seed 321 --prior-spread-start 2.0 --prior-spread-end 0.5 \
  --prior-warmup-steps 20 --prior-log-sigma 0.2 --outdir "$BASE/32x32"
```

Record in `$BASE/32x32/summary.md` whether σ surpasses 1.0° or gradient ratios change.

**Step 3: Repeat for 64×64 and 128×128**

Same command with `--fpixels --spixels` = 64/64 and 128/128, writing to corresponding directories. Capture diagnostic plots (JSON + Markdown) and note any σ improvement. If runs diverge, log failure in summary.

**Step 4: Update docs**

- Append observations to `docs/findings.md` (FND-VI-2026-01) referencing new artifact paths.
- Update `docs/strategy/mainstrategy.md §9` summarizing whether prior schedule or higher resolutions improved σ.

**Step 5: Commit artifacts + docs**

```bash
git add "$BASE" docs/findings.md docs/strategy/mainstrategy.md
git commit -m "chore: record VI prior schedule diagnostics across detector sizes"
```

---

### Task 4: Canonical benchmark with best prior/geometry

**Artifacts:** `plans/active/strat-vi-001/reports/<ts>/prior_benchmark/`

**Step 1: Select best configuration**

- Inspect summaries from Task 3. Choose the detector size + prior schedule that delivered the highest σ after 25 iterations.
- Document selection rationale in `$BASE/summary.md`.

**Step 2: Run 150-iteration benchmark**

```bash
TS_BENCH=$(date -u +%Y-%m-%dT%H%M%SZ)
OUT=plans/active/strat-vi-001/reports/${TS_BENCH}/prior_benchmark
mkdir -p "$OUT"
KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 python scripts/benchmark_vi_mosaic.py \
  --iterations 150 --k-samples 4 --fpixels <SIZE> --spixels <SIZE> \
  --observation-mean 25 --observation-normalization mean --observation-seed 321 \
  --kl-weight-start 0.2 --kl-weight-end 1.0 --kl-warmup-steps 120 \
  --prior-spread-start 2.0 --prior-spread-end 0.5 --prior-warmup-steps 120 \
  --prior-log-sigma 0.2 --outdir "$OUT"
```

Replace `<SIZE>` with the chosen detector resolution; adjust prior knobs if Task 3 identified better values.

**Step 3: Analyze outcome**

- Summarize σ trajectories for MC, analytic, and VI in `$OUT/summary.md`.
- If VI still collapses (<1.2°), clearly state failure and recommend next mitigation (e.g., multi-scale crystal geometry or flow posterior).
- If VI ≥1.5°, document success criteria and update fix plan exit status.

**Step 4: Update documentation + fix plan**

- Update `docs/findings.md` and `docs/strategy/mainstrategy.md §9` with benchmark results (success or failure).
- Update `docs/fix_plan.md` (STRAT-VI-001) to reflect Task 22 progress, referencing new artifacts and noting next steps.
- Refresh `input.md` with new instructions + mapped tests (`test_vi_mosaic.py::test_benchmark_script_smoke`, etc.).

**Step 5: Regression tests + commit**

```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k "prior or benchmark" -v
git add docs/findings.md docs/strategy/mainstrategy.md docs/fix_plan.md input.md "$OUT"
git commit -m "feat: evaluate VI prior schedule on canonical benchmark"
```

---

Plan complete and saved to `docs/plans/2026-01-29-vi-prior-geometry.md`.

Two execution options:

1. **Subagent-Driven (this session)** — launch `superpowers:subagent-driven-development`, run each task with check-ins.
2. **Parallel Session** — new terminal/worktree using `superpowers:executing-plans` to execute tasks sequentially.

Which approach should we take?
