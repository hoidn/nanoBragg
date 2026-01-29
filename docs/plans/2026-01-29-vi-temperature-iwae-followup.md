# VI Temperature × IWAE Follow-up Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend the new likelihood-temperature knob by (a) sweeping hotter temperatures (up to 8×) and (b) combining temperature with the IWAE objective to see if either intervention lifts σ beyond 1° on short diagnostics.

**Architecture:** Reuse the existing Poisson ELBO plumbing (`src/nanobrag_torch/vi/poisson_elbo.py`) and diagnostics harness (`scripts/analysis/vi_poisson_diagnostics.py`) defined in `docs/plans/2026-01-29-vi-mosaic-design.md §Variational Family` and `docs/plans/2026-01-29-vi-poisson-likelihood-rescaling.md §Adaptive Scaling Definition`. The experiments are configuration-only: no new kernel math, just different CLI invocations plus documentation of the results.

**Tech Stack:** Python 3.11, PyTorch 2.x (autograd), diagnostics CLI (`scripts/analysis/vi_poisson_diagnostics.py`), Markdown/JSON logging, pytest for smoke checks.

---

### Task 1: Run extended temperature sweep (T = {1, 2, 4, 8})

**Files / Artifacts:**
- Artifacts: `plans/active/strat-vi-001/reports/<ts>/temperature_sweep_hot/`
- Existing helper: `scripts/analysis/vi_poisson_diagnostics.py::run_likelihood_temperature_sweep`
- Docs to update later: `docs/findings.md`, `docs/strategy/mainstrategy.md`, `docs/fix_plan.md`

**Step 1: Prepare artifact directory**
```bash
TS=$(date -u +%Y-%m-%dT%H%M%SZ)
OUT=plans/active/strat-vi-001/reports/${TS}/temperature_sweep_hot
mkdir -p "$OUT"
```
Expected: `$OUT` exists for logs/plots.

**Step 2: Run hotter temperature sweep (standard objective)**
```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/analysis/vi_poisson_diagnostics.py \
  --iterations 25 --k-samples 4 --observation-mean 25.0 \
  --observation-normalization mean --observation-seed 321 \
  --temperature-sweep "1.0,2.0,4.0,8.0" \
  --temperature-sweep-outdir "$OUT"
```
Expected: Subfolders `T_1.0`, `T_2.0`, `T_4.0`, `T_8.0`, plus combined `temperature_sweep.json` and `temperature_sweep_summary.md`. Confirm σ_mean, gradient ratios, and log-likelihood entries appear for each temperature.

**Step 3: Check for divergence / NaNs**
- Inspect `$OUT/temperature_sweep_summary.md` and ensure `σ_mean` remains finite.
- If `T=8` causes NaNs or diverging gradients, note the failure in the summary; no rerun needed.

**Step 4: Smoke tests**
- Run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_temperature_sweep_runs_multiple_temperatures -v`
Expected: PASS (verifies helper integrity after CLI usage).

---

### Task 2: IWAE + temperature combination sweep

**Files / Artifacts:**
- Continue using `$OUT` but create IWAE-specific subdir: `$OUT/iwae`
- Scripts: `scripts/analysis/vi_poisson_diagnostics.py` (IWAE flags)

**Step 1: Run IWAE sweep with hotter temperatures**
```bash
mkdir -p "$OUT/iwae"
KMP_DUPLICATE_LIB_OK=TRUE python scripts/analysis/vi_poisson_diagnostics.py \
  --iterations 25 --k-samples 8 --observation-mean 25.0 \
  --observation-normalization mean --observation-seed 321 \
  --elbo-objective iwae --temperature-sweep "1.0,2.0,4.0,8.0" \
  --temperature-sweep-outdir "$OUT/iwae"
```
Expected: Combined JSON/Markdown plus per-temperature folders inside `$OUT/iwae`. Each run should record `objective="iwae"`, per-sample log-weight stats, and σ trajectories.

**Step 2: Identify best-performing configuration**
- Parse `$OUT/iwae/temperature_sweep.json` to find the maximum `sigma_mean_deg` across temperatures.
- Record best temp, σ, and gradient ratios in `$OUT/iwae/summary.md`.

**Step 3: Conditional canonical benchmark (only if σ_mean ≥ 1.2°)**
- If any IWAE+temperature entry yields σ ≥ 1.2° within 25 iterations, run the full 150-iteration benchmark using that temperature/objective combo:
```bash
BEST_T=???  # fill from Step 2
BENCH_ROOT=plans/active/strat-vi-001/reports/${TS}/iwae_temp_benchmark
mkdir -p "$BENCH_ROOT"
KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  python scripts/benchmark_vi_mosaic.py \
  --iterations 150 --observation-mean 25.0 --observation-normalization mean \
  --observation-seed 321 --kl-weight-start 0.2 --kl-weight-end 1.0 \
  --kl-warmup-steps 120 --k-samples 8 \
  --elbo-objective iwae --likelihood-temperature "$BEST_T" \
  --outdir "$BENCH_ROOT"
```
- Archive `vi_vs_mc_loss.png`, `vi_vs_mc_summary.json`, and diagnostics under `$BENCH_ROOT`.
- If no IWAE+temperature run crosses σ ≥ 1.2°, SKIP this step and note “benchmark not triggered” in the summary.

**Step 4: Smoke tests**
- Run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_benchmark_script_smoke -v`.
- Expected: PASS.

---

### Task 3: Summaries + documentation updates

**Files:**
- Modify: `docs/findings.md` (FND-VI-2026-01)
- Modify: `docs/strategy/mainstrategy.md §9`
- Modify: `docs/fix_plan.md` (STRAT-VI-001 section)
- Update: `input.md`
- Artifacts: `$OUT/summary.md`, `$OUT/iwae/summary.md`, optional `$BENCH_ROOT/summary.md`

**Step 1: Draft artifact summaries**
- Create `$OUT/summary.md` describing the extended sweep (σ trends, gradient ratios, divergence notes).
- Create `$OUT/iwae/summary.md` summarizing IWAE results and whether the benchmark was triggered.
- If Task 2 Step 3 ran, add `$BENCH_ROOT/summary.md` with key σ/loss metrics.

**Step 2: Update findings + strategy**
- Append a paragraph to `docs/findings.md` FND-VI-2026-01 covering both sweeps, linking to `$OUT` and `$OUT/iwae` (and `$BENCH_ROOT` if present).
- In `docs/strategy/mainstrategy.md §9`, describe the experiment outcomes and explicitly state whether hotter temperatures or IWAE+temperature changed σ recovery.

**Step 3: Refresh fix plan + supervisor FSM**
- In `docs/fix_plan.md`, add a new Task entry under STRAT-VI-001 referencing this plan, mark Task 18 as complete, and set `next_action` based on the new evidence (e.g., “evaluate posterior prior schedule” if still collapsed).
- Append the latest supervisor state line (`focus=STRAT-VI-001 state=ready_for_implementation dwell=0 artifacts=... next_action=...`).

**Step 4: Write new `input.md`**
- Point to this plan, specify artifact paths, mapped tests (`test_vi_temperature_sweep_runs_multiple_temperatures`, `test_benchmark_script_smoke`), and summarize desired outcome for the engineer.

**Step 5: Regression test sweep**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k "temperature or benchmark_script_smoke" -v
```
Expected: PASS.

**Step 6: Commit**
```bash
git add docs/findings.md docs/strategy/mainstrategy.md docs/fix_plan.md input.md \
        docs/plans/2026-01-29-vi-temperature-iwae-followup.md \
        plans/active/strat-vi-001/reports/${TS}/ \
        ${BENCH_ROOT:-}
# Include demo_outputs/* if benchmark artifacts update shared plots.
git commit -m "feat: investigate hotter VI likelihood temperatures and IWAE combo"
```

---

Plan complete and saved to `docs/plans/2026-01-29-vi-temperature-iwae-followup.md`.
Two execution options:
1. **Subagent-Driven (this session)** — launch `superpowers:subagent-driven-development` and iterate task-by-task with supervisor checkpoints.
2. **Parallel Session** — open a new worktree/session, load `superpowers:executing-plans`, and run the plan sequentially.
