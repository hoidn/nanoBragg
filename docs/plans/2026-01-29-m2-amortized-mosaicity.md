# M2 Amortized Mosaicity Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver Strategy §7 Milestone M2 by teaching the Duck multi-image demo to learn per-image mosaic spread via an amortized encoder whose gradients grow with dataset size.

**Architecture:** Extend the deterministic Duck dataset with per-image mosaic ground truth, add a lightweight CNN encoder that maps photon-count tiles + orientation context to posterior parameters, plug the encoder into an amortized variant of `MultiImageTrainer` that instantiates conditioned mosaic posteriors per image, and expose the workflow through `scripts/demo_recover_duck.py` with diagnostics + documentation updates.

**Tech Stack:** PyTorch (Conv2d/BatchNorm/Adam), existing `VariationalMosaicSimulator`, pytest, matplotlib, JSON logging, docs in Markdown.

---

### Task 1: Duck dataset spec + per-image mosaic ground truth

**Files:**
- Create: `docs/specs/duck_multi_image_dataset.md`
- Modify: `docs/index.md`
- Modify: `scripts/generate_duck_multi_image.py`
- Modify: `src/nanobrag_torch/io/duck_dataset.py`
- Modify: `tests/test_duck_dataset.py`
- Artifact: refreshed `demo_inputs/duck_multi_image/{metadata.json,counts/*.pt}`

**Step 1: Write the failing test**

```python
# tests/test_duck_dataset.py
from nanobrag_torch.io.duck_dataset import DuckDataset

def test_duck_dataset_includes_mosaic_ground_truth(tmp_path):
    dataset_dir = tmp_path / "duck_multi_image"
    (dataset_dir / "counts").mkdir(parents=True)
    (dataset_dir / "metadata.json").write_text("""
    {"n_images": 1, "spixels": 64, "fpixels": 64,
     "orientations": [[[1,0,0],[0,1,0],[0,0,1]]],
     "per_image": [{"mosaic_spread_deg": 1.5}],
     "crystal_config": {}, "beam_config": {},
     "observation_meta": {"scale": 7.2}}
    """)
    torch.save(torch.ones(64, 64), dataset_dir / "counts" / "img_00.pt")
    sample = DuckDataset(dataset_dir)[0]
    assert sample.mosaic_spread_deg == pytest.approx(1.5)
    assert DuckDataset(dataset_dir).observation_meta["scale"] == pytest.approx(7.2)
```

**Step 2: Run the test to verify it fails**

Run: `pytest tests/test_duck_dataset.py::test_duck_dataset_includes_mosaic_ground_truth -v`
Expected: FAIL because `DuckSample` lacks the `mosaic_spread_deg` attribute and metadata lacks `per_image` handling.

**Step 3: Implement the minimal code + regenerate dataset**

- Update `scripts/generate_duck_multi_image.py` to:
  - Sample per-image mosaic spreads (e.g., `rng.normal(loc=2.0, scale=0.3)` clamped to `[0.5, 3.0]`).
  - Record `per_image[i]["mosaic_spread_deg"]` and copy `meta["scale"]` plus `mean_counts`.
- Expand `DuckSample` dataclass with `mosaic_spread_deg: float` and return it inside `__getitem__`.
- Add helper `DuckDataset.mosaic_truth` returning list of degrees for later diagnostics.
- Re-run dataset generation:
  - `python scripts/generate_duck_multi_image.py --outdir demo_inputs/duck_multi_image --images 20 --observation-mean 25`
  - Verify console logs show per-image misset + mosaic spreads; stage refreshed files under `demo_inputs/duck_multi_image/`.

**Step 4: Document the contract**

- Author `docs/specs/duck_multi_image_dataset.md` describing layout, metadata schema (top-level keys + `per_image` entries), and guarantees about mosaic spread sampling + normalization.
- Update `docs/index.md` “Project Documentation” list to link the new spec.

**Step 5: Re-run tests**

Run: `pytest tests/test_duck_dataset.py -v`
Expected: PASS, including the new mosaic truth test.

**Step 6: Commit**

```bash
git add docs/specs/duck_multi_image_dataset.md docs/index.md \
        scripts/generate_duck_multi_image.py src/nanobrag_torch/io/duck_dataset.py \
        tests/test_duck_dataset.py demo_inputs/duck_multi_image
git commit -m "feat: enrich Duck dataset with per-image mosaic truth"
```

---

### Task 2: Amortized mosaic encoder module

**Files:**
- Create: `src/nanobrag_torch/vi/amortized_encoder.py`
- Modify: `src/nanobrag_torch/vi/__init__.py`
- Modify: `tests/test_vi_mosaic.py`

**Step 1: Write the failing test**

```python
# tests/test_vi_mosaic.py
from nanobrag_torch.vi.amortized_encoder import DuckMosaicEncoder

def test_amortized_encoder_outputs_mu_rho(tmp_path):
    encoder = DuckMosaicEncoder(in_channels=1,
                                orientation_features=3,
                                hidden=32)
    counts = torch.randn(4, 1, 64, 64)
    orientations = torch.zeros(4, 3)
    mu, rho = encoder(counts, orientations)
    assert mu.shape == (4,)
    assert rho.shape == (4,)
    loss = (mu + rho).sum()
    loss.backward()
    for param in encoder.parameters():
        assert param.grad is not None
```

**Step 2: Run the test to verify it fails**

Run: `pytest tests/test_vi_mosaic.py::test_amortized_encoder_outputs_mu_rho -v`
Expected: FAIL because the encoder module does not exist.

**Step 3: Implement the encoder**

- Create `DuckMosaicEncoder` with:
  - Three `Conv2d` layers (1→8→16→32) + `BatchNorm2d` + `ReLU` (device/dtype neutral).
  - Global average pooling followed by concatenation of orientation features (Euler XYZ derived from dataset orientation matrix, computed once in trainer and fed as `(batch,3)` tensor).
  - Two linear heads outputting `(mu, rho)` in log-space; clamp rho via `softplus` in trainer.
  - `forward(counts, orient_features)` returns `(mu, rho)` shaped `(batch,)` and `(batch,)`.
- Export the encoder in `vi/__init__.py`.

**Step 4: Re-run the test**

Run: `pytest tests/test_vi_mosaic.py::test_amortized_encoder_outputs_mu_rho -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/nanobrag_torch/vi/amortized_encoder.py src/nanobrag_torch/vi/__init__.py \
        tests/test_vi_mosaic.py
git commit -m "feat: add Duck mosaic amortized encoder"
```

---

### Task 3: Amortized multi-image trainer + conditioned posterior plumbing

**Files:**
- Modify: `src/nanobrag_torch/vi/multi_image_trainer.py`
- Modify: `src/nanobrag_torch/vi/mosaic_posterior.py`
- Modify: `tests/test_vi_mosaic.py`

**Step 1: Write the failing trainer test**

```python
# tests/test_vi_mosaic.py
from nanobrag_torch.vi.multi_image_trainer import MultiImageTrainer
from nanobrag_torch.vi.amortized_encoder import DuckMosaicEncoder

def test_amortized_trainer_recovers_per_image_spread(duck_dataset_path):
    dataset = DuckDataset(duck_dataset_path)
    trainer = MultiImageTrainer.from_dataset(
        dataset,
        amortized_encoder=DuckMosaicEncoder(),
        amortized=True,
        posterior_cfg={"k_samples": 2},
    )
    stats = trainer.step(iterations=5)
    assert "per_image_sigma_deg" in stats
    assert len(stats["per_image_sigma_deg"]) == len(dataset)
    assert max(stats["per_image_sigma_deg"]) != pytest.approx(min(stats["per_image_sigma_deg"]))
```

**Step 2: Run the test**

Run: `pytest tests/test_vi_mosaic.py::test_amortized_trainer_recovers_per_image_spread -v`
Expected: FAIL because trainer lacks amortized mode and conditioned posteriors.

**Step 3: Implement conditioned posterior plumbing**

- Add `ConditionedMosaicPosterior` helper in `mosaic_posterior.py` that accepts tensors `mu`, `rho`, `prior_mu`, `prior_log_sigma` and implements `.sample`, `.kl_divergence`, `.log_prob_sigma`, `.log_prior_sigma` without `nn.Parameter`s (values derived from encoder outputs and retain gradients).
- Extend `MultiImageTrainer` with:
  - Optional `amortized_encoder` argument stored as module on correct device/dtype.
  - Utility to convert each orientation matrix into Euler angles once.
  - New method `_build_conditioned_posterior(mu, rho)` returning a `ConditionedMosaicPosterior` (softplus rho for std, clamp mu range).
  - `step()` detection: if `self.amortized_encoder` is set, batch counts into `(batch,1,H,W)`, call encoder once per iteration, and per image create simulator with conditioned posterior before calling `poisson_elbo`.
  - Collect diagnostics: per-image predicted sigma in degrees, KL + log-likelihood contributions, gradient norms of encoder parameters (use `torch.nn.utils.clip_grad_norm_` or manual loop).

**Step 4: Re-run amortized tests**

- `pytest tests/test_vi_mosaic.py::test_amortized_trainer_recovers_per_image_spread -v`
- `pytest tests/test_vi_mosaic.py::test_multi_image_trainer_batches_duck -v`
Expected: PASS for both shared and amortized modes.

**Step 5: Commit**

```bash
git add src/nanobrag_torch/vi/multi_image_trainer.py src/nanobrag_torch/vi/mosaic_posterior.py \
        tests/test_vi_mosaic.py
git commit -m "feat: add amortized multi-image trainer and conditioned posterior"
```

---

### Task 4: CLI integration, diagnostics, and documentation

**Files:**
- Modify: `scripts/demo_recover_duck.py`
- Modify: `docs/strategy/mainstrategy.md`
- Modify: `docs/development/testing_strategy.md`
- Modify: `docs/fix_plan.md`
- Modify: `docs/index.md` (strategy references if needed)
- Modify: `tests/test_vi_mosaic.py` (CLI smoke)
- Artifact: `plans/active/strat-m2-001/reports/<ts>/amortized_demo/{loss.png,summary.json,gradients.json}`

**Step 1: Write the failing CLI test**

```python
# tests/test_vi_mosaic.py
import json, subprocess, tempfile

def test_demo_recover_duck_cli_amortized():
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = ["python", "scripts/demo_recover_duck.py",
               "--dataset", "demo_inputs/duck_multi_image",
               "--outdir", tmpdir,
               "--mode", "amortized",
               "--iterations", "5",
               "--device", "cpu",
               "--log-gradients"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0
        summary = json.loads(Path(tmpdir)/"duck_summary.json".read_text())
        assert "amortized" in summary["trainer_mode"]
        assert "gradient_norms" in summary
```

**Step 2: Run the test**

Run: `pytest tests/test_vi_mosaic.py::test_demo_recover_duck_cli_amortized -v`
Expected: FAIL because CLI lacks the new flag.

**Step 3: Implement CLI + diagnostics**

- Update `scripts/demo_recover_duck.py` to accept `--mode {shared,amortized}`, `--log-gradients`, and `--dataset-size-sweep`.
- When `mode=amortized`, instantiate the trainer with the encoder, run iterations, collect per-image sigma vs ground truth (from dataset metadata) and gradient norms vs dataset size, write to `duck_summary.json`, and emit `duck_amortized_loss.png` with two curves (loss, sigma error).
- Support dataset-size sweep (e.g., rerun with 10 vs 20 images) when `--dataset-size-sweep` is provided; log gradient norm deltas.

**Step 4: Update docs**

- `docs/strategy/mainstrategy.md §7` — add paragraph describing M2 amortized encoder, success metrics (sigma recovery ≥1.5°, gradient norms increasing with dataset size), and reference artifact path.
- `docs/development/testing_strategy.md` — document new pytest selectors + CLI command for amortized mode, plus expected outputs.
- `docs/fix_plan.md` — mark Tasks 1–3 complete and replace STRAT-M2-001 next actions with the amortized encoder steps + artifact references.
- Ensure `docs/index.md` references the new spec (if not already linked).

**Step 5: Capture artifacts**

Run:
```bash
python scripts/demo_recover_duck.py \
    --dataset demo_inputs/duck_multi_image \
    --outdir plans/active/strat-m2-001/reports/$(date -u +%Y-%m-%dT%H%M%SZ)/amortized_demo \
    --mode amortized --iterations 50 --device cpu --log-gradients \
    --dataset-size-sweep 10 20
```
Expected: directory with `duck_loss.png`, `duck_summary.json`, `gradient_stats.json`, console log referencing gradient growth.
Copy summary artifacts into `demo_outputs/duck_amortized/` for docs.

**Step 6: Run the focused test suite**

Run: `pytest tests/test_vi_mosaic.py -k "duck_dataset or amortized" -v`
Expected: PASS.

**Step 7: Commit**

```bash
git add scripts/demo_recover_duck.py docs/strategy/mainstrategy.md \
        docs/development/testing_strategy.md docs/fix_plan.md docs/index.md \
        tests/test_vi_mosaic.py demo_outputs/duck_amortized \
        plans/active/strat-m2-001/reports/*/amortized_demo
git commit -m "feat: add amortized Duck demo and documentation"
```

---

Plan complete and saved to `docs/plans/2026-01-29-m2-amortized-mosaicity.md`. Two execution options:

1. **Subagent-Driven (this session)** — dispatch one agent per task with check-ins between tasks.
2. **Parallel Session** — open a fresh session/worktree and run superpowers:executing-plans with checkpoints per task.

Which approach?
