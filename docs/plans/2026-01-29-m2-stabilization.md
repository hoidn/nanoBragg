# Duck Amortized Stabilization Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add gradient-clipping and multi-phase curriculum tooling for the Duck amortized demo so we can run stabilized 500-iteration / 50/100-image studies and document whether these mitigations move σ beyond the 0.5° ceiling.

**Architecture:** Extend `MultiImageTrainer` with optional gradient clipping hooks, surface the knobs through `scripts/demo_recover_duck.py`, and add a new curriculum runner that applies staged learning-rate / KL schedules on a single trainer instance while logging per-phase metrics. Capture two evidence bundles (500-iter clip run + curriculum sweep) and thread the results into strategy/fix-plan docs.

**Tech Stack:** PyTorch (optimizer + gradient utilities), CLI scripts under `scripts/`, pytest (`tests/test_vi_mosaic.py`), matplotlib for artifact plots.

---

### Task 1: MultiImageTrainer Gradient Clipping

**Files:**
- Modify: `src/nanobrag_torch/vi/multi_image_trainer.py`
- Modify: `tests/test_vi_mosaic.py` (amortized block near `test_multi_image_trainer_amortized_mode`)

**Step 1: Write failing test**

Add `test_multi_image_trainer_enforces_grad_clip` that:

```python
def test_multi_image_trainer_enforces_grad_clip(duck_dataset_small):
    trainer = MultiImageTrainer.from_dataset(
        duck_dataset_small,
        config=MultiImageTrainerConfig(
            lr=0.05,
            clip_grad_norm=0.1,
            k_samples=1,
            dtype=torch.float32,
        ),
        amortized=True,
        amortized_encoder=DuckMosaicEncoder(),
        log_gradients=True,
    )
    stats = trainer.step(iterations=1)
    assert max(stats["gradient_norms"]) <= 0.11
```

Expose a `duck_dataset_small` fixture (reuse the existing DuckDataset fixture but slice to 2 images to keep runtime low) if needed.

**Step 2: Run failing test**

```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_multi_image_trainer_enforces_grad_clip -k amortized -v
```

Expect failure because clipped norms are not yet bounded.

**Step 3: Implement gradient clipping**

- Extend `MultiImageTrainerConfig` with `clip_grad_norm: float | None = None` and optional `clip_scope: Literal["all","encoder","posterior"] = "all"`.
- Add helper `_iter_trainable_params(scope)` that yields the tensors to clip (encoder params when amortized, per-image posteriors/log-scales in joint mode, shared posterior otherwise).
- After `total_loss.backward()` but before `self.optimizer.step()`, call `torch.nn.utils.clip_grad_norm_` on the selected params when `clip_grad_norm` is set. Capture the returned norm; if `scope == "encoder"`, only pass encoder params.
- When `self.log_gradients` is `True`, append `min(returned_norm, self.config.clip_grad_norm)` so recorded metrics reflect the clipped magnitude.
- Guard for cases where no params require clipping (skip call).

**Step 4: Re-run targeted tests**

```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k "grad_clip or amortized" -v
```

Expect new test to pass along with existing amortized suite.

**Step 5: Commit**

```bash
git add src/nanobrag_torch/vi/multi_image_trainer.py tests/test_vi_mosaic.py
git commit -m "feat: add amortized grad clipping support"
```

---

### Task 2: CLI + Docs Wiring for Gradient Clipping

**Files:**
- Modify: `scripts/demo_recover_duck.py`
- Modify: `docs/development/testing_strategy.md` §6.2
- Modify: `docs/strategy/mainstrategy.md` §7 (CLI command tables)
- Modify: `tests/test_vi_mosaic.py::test_demo_recover_duck_cli_amortized`

**Step 1: Extend CLI**

- Add `--clip-grad-norm` (float, default None) and `--clip-scope {all,encoder,posterior}` arguments.
- Thread both knobs into `MultiImageTrainerConfig` construction.
- Include the clip metadata inside `duck_summary.json` under `config.clip_grad_norm` and `config.clip_scope`.

**Step 2: Update CLI test**

- Modify `test_demo_recover_duck_cli_amortized` to invoke the script via `subprocess.run` (or helper) with `--clip-grad-norm 0.5 --clip-scope encoder`.
- Assert the emitted JSON reflects the clip values and that the command exits 0.

**Step 3: Update testing strategy**

- Document the new CLI flags in `docs/development/testing_strategy.md §6.2` (canonical amortized command) and note when to enable clipping (e.g., “Set `--clip-grad-norm 0.5` before 300+ iteration runs to avoid NaNs”).
- Mention mapped pytest selectors covering the clip path.

**Step 4: Refresh strategy doc references**

- Add a sentence in `docs/strategy/mainstrategy.md §7` (M2 section) describing the new stabilization knobs and referencing the plan’s evidence bundle.

**Step 5: Run CLI smoke test**

```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/demo_recover_duck.py --mode amortized --iterations 1 --clip-grad-norm 0.5 --clip-scope encoder --dataset demo_inputs/duck_multi_image --outdir /tmp/duck_clip_smoke
```

**Step 6: Commit**

```bash
git add scripts/demo_recover_duck.py docs/development/testing_strategy.md docs/strategy/mainstrategy.md tests/test_vi_mosaic.py
git commit -m "feat: expose grad clipping knobs in Duck CLI"
```

---

### Task 3: Curriculum Runner + Tests

**Files:**
- Create: `scripts/analysis/run_duck_curriculum.py`
- Modify: `src/nanobrag_torch/vi/multi_image_trainer.py` (helper `set_learning_rate` + ability to update `kl_weight` at runtime)
- Modify: `tests/test_vi_mosaic.py` (add `test_curriculum_runner_two_phase_smoke`)
- Add fixture JSON under `tests/fixtures/curriculum_two_phase.json`

**Step 1: Implement runtime setters**

- Add `MultiImageTrainer.set_learning_rate(lr: float)` that updates `self.config.lr` and each optimizer param group.
- Allow `trainer.step()` to read the latest `self.config.kl_weight` each call so per-phase updates take effect.

**Step 2: Author curriculum script**

- New CLI: `python scripts/analysis/run_duck_curriculum.py --dataset demo_inputs/duck_multi_image --phases tests/fixtures/curriculum_two_phase.json --outdir plans/active/strat-m2-002/reports/<ts>/curriculum`
- JSON schema: `[{"iterations": 50, "lr": 0.01, "kl_weight": 0.2, "clip_grad_norm": 0.5}, ...]`.
- Script responsibilities:
  1. Build one `MultiImageTrainer` (amortized mode).
  2. Loop over phases, calling new setters before `trainer.step(iterations=phase.iterations)`.
  3. Append phase summaries (loss delta, σ delta, gradient norms when available) to a `curriculum_summary.json` and emit per-phase plots (loss/sigma vs cumulative iteration).

**Step 3: Add fixture JSON**

- Place `tests/fixtures/curriculum_two_phase.json` with two short phases (1 iteration each) for test use.

**Step 4: Write curriculum smoke test**

- New pytest function runs the script with the fixture (use `subprocess.run([...], check=True)` plus `tmp_path` outdir) and asserts `curriculum_summary.json` exists with `len(phases) == 2` and cumulative iterations recorded.

**Step 5: Run targeted tests**

```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k curriculum -v
```

**Step 6: Commit**

```bash
git add scripts/analysis/run_duck_curriculum.py src/nanobrag_torch/vi/multi_image_trainer.py tests/test_vi_mosaic.py tests/fixtures/curriculum_two_phase.json
git commit -m "feat: add Duck curriculum runner"
```

---

### Task 4: Stabilized Evidence + Documentation

**Files:**
- Artifacts: `plans/active/strat-m2-002/reports/<ts>/grad_clip_500/`, `.../curriculum_sweep/`
- Modify: `docs/strategy/mainstrategy.md` §7 tables
- Modify: `docs/findings.md` (append details to FND-M2-2026-01)
- Modify: `docs/fix_plan.md` (STRAT-M2-002 block + FSM line)
- Update: `demo_outputs/duck_amortized_grad_clip/`, `demo_outputs/duck_amortized_curriculum/`

**Step 1: Run gradient-clipped 500-iter study**

```bash
export ARTIFACT_ROOT=plans/active/strat-m2-002/reports/$(date -u +%Y-%m-%dT%H%M%SZ)/grad_clip_500
mkdir -p "$ARTIFACT_ROOT"
KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  python scripts/demo_recover_duck.py \
    --mode amortized --iterations 500 --lr 0.003 \
    --clip-grad-norm 0.5 --clip-scope encoder \
    --k-samples 4 --dataset demo_inputs/duck_multi_image \
    --outdir "$ARTIFACT_ROOT" --log-gradients
```

Mirror PNG/JSON into `demo_outputs/duck_amortized_grad_clip/`.

**Step 2: Run curriculum sweep**

```bash
export CURR_ROOT=plans/active/strat-m2-002/reports/$(date -u +%Y-%m-%dT%H%M%SZ)/curriculum_sweep
KMP_DUPLICATE_LIB_OK=TRUE python scripts/analysis/run_duck_curriculum.py \
  --dataset demo_inputs/duck_multi_image \
  --phases configs/m2_curriculum_phases.json \
  --outdir "$CURR_ROOT"
```

Include a second JSON file that scales to 50/100-image datasets so we can compare sigma trajectories; place results plus summary CSV into `CURR_ROOT`.

**Step 3: Update docs**

- `docs/strategy/mainstrategy.md`: extend the M2 table with two new rows (“longrun_20_clip”, “curriculum_20→50→100”), citing artifact paths and noting whether σ moved.
- `docs/findings.md`: update FND-M2-2026-01 with a section summarizing why gradient clipping + curriculum still failed (or highlight any improvement if observed).
- `docs/fix_plan.md`: add STRAT-M2-002 status, artifact root, and FSM supervisor line referencing the new plan.

**Step 4: Tests + verification**

```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k "amortized or curriculum" -v
```

**Step 5: Stage artifacts + docs**

```bash
git add plans/active/strat-m2-002/reports/* demo_outputs/duck_amortized_grad_clip demo_outputs/duck_amortized_curriculum \
  docs/strategy/mainstrategy.md docs/findings.md docs/fix_plan.md
```

**Step 6: Commit**

```bash
git commit -m "feat: document Duck amortized stabilization experiments"
```

---

Plan complete and saved to `docs/plans/2026-01-29-m2-stabilization.md`. Two execution options:

1. **Subagent-Driven (this session)** — dispatch per task with superpowers:subagent-driven-development and review after each.
2. **Parallel Session** — open a fresh session/worktree, load this plan, and run superpowers:executing-plans with checkpoints after every task.

Which approach?
