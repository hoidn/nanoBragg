# VI Canonical Benchmark Refresh Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Re-run the canonical 150-iteration VI benchmark using the adaptive Poisson observation scaling so we can capture artifacts proving whether σ recovers ≥1.5° and update docs/findings/fix-plan accordingly.

**Architecture:** Use the existing `scripts/benchmark_vi_mosaic.py` pipeline with the new `--observation-mean/--observation-normalization` knobs, log Poisson metadata, and archive PNG/JSON/stats inside `plans/active/strat-vi-001/reports/<ts>/` plus `demo_outputs/`. Tie evidence back into `docs/findings.md` + `docs/strategy/mainstrategy.md` while keeping STRAT-VI-001 status accurate.

**Tech Stack:** Python CLI (PyTorch, numpy), Bash tooling, pytest (`tests/test_vi_mosaic.py`), Markdown docs.

---

### Task 1: Prepare artifacts and run canonical benchmark

**Files / Dirs:**
- `scripts/benchmark_vi_mosaic.py`
- `plans/active/strat-vi-001/reports/<ts>/benchmark/`

**Step 1: Create timestamped artifact root**
```bash
ts=$(date -u +%Y-%m-%dT%H%M%SZ)
export VI_BENCH_ROOT="plans/active/strat-vi-001/reports/${ts}"
mkdir -p "$VI_BENCH_ROOT/benchmark"
```
Expected: `$VI_BENCH_ROOT` now exists; record `ts` for later doc edits.

**Step 2: Capture raw observation stats before sampling**
```bash
python - <<'PY'
from pathlib import Path
import torch
from scripts import benchmark_vi_mosaic as bm

_, meta = bm._generate_ground_truth(
    cell_edge_A=bm.DEFAULT_CELL_EDGE_A,
    wavelength_A=bm.DEFAULT_WAVELENGTH_A,
    distance_mm=bm.DEFAULT_DISTANCE_MM,
    pixel_size_mm=bm.DEFAULT_PIXEL_SIZE_MM,
    fpixels=bm.DEFAULT_FPIXELS,
    spixels=bm.DEFAULT_SPIXELS,
    device=torch.device('cpu'),
    dtype=torch.float32,
    observation_mean=25.0,
    observation_normalization="mean",
    observation_seed=321,
)
Path("$VI_BENCH_ROOT/observation_scale_stats.txt").write_text(
    "\n".join([
        f"raw_mean={meta['raw_mean']:.6e}",
        f"raw_max={meta['raw_max']:.6e}",
        f"scale={meta['scale']:.6e}",
        f"target_mean_counts={meta['target_mean_counts']:.3f}",
    ])
)
PY
```
Expected: `observation_scale_stats.txt` records the adaptive scaling stats; keep for auditability.

**Step 3: Run canonical benchmark**
```bash
KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  python scripts/benchmark_vi_mosaic.py \
    --iterations 150 \
    --observation-mean 25.0 \
    --observation-normalization mean \
    --observation-seed 321 \
    --kl-weight-start 0.2 \
    --kl-weight-end 1.0 \
    --kl-warmup-steps 120 \
    --diagnostics-log "$VI_BENCH_ROOT/benchmark/vi_diagnostics.json" \
    --outdir "$VI_BENCH_ROOT/benchmark"
```
Expected: command finishes without error (≈20–25 min CPU). Outputs `vi_vs_mc_loss.png`, `vi_vs_mc_summary.json` under the benchmark directory.

---

### Task 2: Archive outputs and compute metrics

**Files / Dirs:**
- `demo_outputs/vi_vs_mc_loss.png`
- `demo_outputs/vi_vs_mc_summary.json`
- `$VI_BENCH_ROOT/vi_vs_mc_loss.png`
- `$VI_BENCH_ROOT/vi_vs_mc_summary.json`
- `$VI_BENCH_ROOT/vi_observation_stats.json`
- `$VI_BENCH_ROOT/benchmark_fluence_summary.md`

**Step 1: Extract observation + sigma stats**
```bash
python - <<'PY'
import json, pathlib
summary = json.loads(pathlib.Path("$VI_BENCH_ROOT/benchmark/vi_vs_mc_summary.json").read_text())
obs = summary["observations"]
stats = {
    "vi_final_sigma_deg": summary["vi"]["final_spread_deg"],
    "vi_loss_first": summary["vi"]["loss"][0],
    "vi_loss_last": summary["vi"]["loss"][-1],
    "mc_final_sigma_deg": summary["mc_baseline"]["final_spread_deg"],
    "mc_loss_first": summary["mc_baseline"]["loss"][0],
    "mc_loss_last": summary["mc_baseline"]["loss"][-1],
    "analytic_final_sigma_deg": summary["analytic"]["final_spread_deg"],
    "observation_mean_counts": obs["mean_counts"],
    "observation_max_counts": obs["max_counts"],
    "observation_scale": obs["scale"],
    "observation_scale_mode": obs["scale_mode"],
    "target_mean_counts": obs["target_mean_counts"],
    "observation_seed": obs["seed"],
}
pathlib.Path("$VI_BENCH_ROOT/vi_observation_stats.json").write_text(json.dumps(stats, indent=2))
print(json.dumps(stats, indent=2))
PY
```
Expected: JSON shows whether `sigma_final_deg >= 1.5`. Keep the emitted stats file for docs.

**Step 2: Copy artifacts into demo outputs + root**
```bash
cp "$VI_BENCH_ROOT/benchmark/vi_vs_mc_loss.png" demo_outputs/vi_vs_mc_loss.png
cp "$VI_BENCH_ROOT/benchmark/vi_vs_mc_summary.json" demo_outputs/vi_vs_mc_summary.json
cp "$VI_BENCH_ROOT/benchmark/vi_vs_mc_loss.png" "$VI_BENCH_ROOT/vi_vs_mc_loss.png"
cp "$VI_BENCH_ROOT/benchmark/vi_vs_mc_summary.json" "$VI_BENCH_ROOT/vi_vs_mc_summary.json"
```
Also ensure `vi_observation_stats.json`, `observation_scale_stats.txt`, and `benchmark/vi_diagnostics.json` remain inside `$VI_BENCH_ROOT`.

**Step 3: Write benchmark summary markdown**
```bash
cat > "$VI_BENCH_ROOT/benchmark_fluence_summary.md" <<'MD'
# Canonical VI benchmark with adaptive Poisson scaling

- Command: `python scripts/benchmark_vi_mosaic.py --iterations 150 --observation-mean 25.0 --observation-normalization mean --observation-seed 321 --kl-weight-start 0.2 --kl-weight-end 1.0 --kl-warmup-steps 120`
- Artifacts: `vi_vs_mc_loss.png`, `vi_vs_mc_summary.json`, `vi_observation_stats.json`, `benchmark/vi_diagnostics.json`
- Key metrics:
  - VI σ final (deg): <fill from vi_observation_stats.json> (target 2.0°)
  - MC σ final (deg): <fill>
  - VI loss first / last: <fill>
  - MC loss first / last: <fill>
  - Observation stats: mean=<fill>, max=<fill>, scale_mode=<fill>, scale=<fill>
- Notes: Document whether σ reached ≥1.5° by iter 150 and list the next diagnostic if not.
MD
```
Fill in `<fill>` placeholders with numbers from `vi_observation_stats.json`.

---

### Task 3: Refresh documentation + fix plan

**Files:**
- `docs/findings.md`
- `docs/strategy/mainstrategy.md`
- `docs/fix_plan.md`
- `$VI_BENCH_ROOT/summary.md`

**Step 1: Findings update**
- Append a new paragraph under FND-VI-2026-01 describing the adaptive scaling benchmark outcome, referencing `$VI_BENCH_ROOT` and quoting the σ result.

**Step 2: Strategy doc**
- In `docs/strategy/mainstrategy.md §9`, document the new benchmark command (observation knobs, typical runtime) and summarize whether σ met the ≥1.5° criterion.

**Step 3: Fix plan metadata**
- Under STRAT-VI-001, mark Task 9 complete (if artifacts captured) and update `next_action` based on σ result (e.g., “analyze log-likelihood curvature” if still low). Update supervisor state/dwell line accordingly.

**Step 4: Artifact summary**
- Create or append `$VI_BENCH_ROOT/summary.md` with a concise note linking to `benchmark_fluence_summary.md`, the σ outcome, and any follow-up recommendation.

---

### Task 4: Regression tests + lint

**Files:**
- `tests/test_vi_mosaic.py`

**Step 1: Run targeted smoke tests**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_benchmark_script_smoke -v
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_diagnostics_snapshot -v
```
Expected: both PASS, confirming CLI metadata stayed stable.

**Step 2: Commit artifacts + docs**
```bash
git add demo_outputs/vi_vs_mc_loss.png demo_outputs/vi_vs_mc_summary.json \
       "$VI_BENCH_ROOT" docs/findings.md docs/strategy/mainstrategy.md docs/fix_plan.md

git commit -m "chore: archive VI benchmark with adaptive Poisson scaling" -m "sigma=<value>"
```
Replace `<value>` with the observed final σ rounded to 3 decimals.
