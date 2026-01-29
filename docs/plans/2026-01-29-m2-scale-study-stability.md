# STRAT-M2-001 Scale-Study Stability Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Stabilize the amortized Duck scale-study runs (500-iter baseline, 50-image, 100-image) and capture analyzable metrics so we can decide whether σ recovery improves with dataset size.

**Architecture:** Reuse the existing amortized Duck CLI plus dataset folders, but switch to conservative learning rates, capture richer metrics/gradient logs, and automate post-processing via a summarizer script before updating docs/fix-plan with the new evidence.

**Tech Stack:** Python + PyTorch CLI, matplotlib (already used by demo), pytest selectors under `tests/test_vi_mosaic.py`, lightweight analysis script + pytest for summaries.

---

### Task 1: Stabilize 500-iteration baseline (20 images)

**Files / Artifacts:**
- Modify: `docs/plans/2026-01-29-m2-amortized-scale-study.md` (update LR guidance)
- Artifact dir: `plans/active/strat-m2-001/reports/<ts>/scale_study/amortized_longrun_20/`
- Mirror: `demo_outputs/duck_amortized_longrun_20/`
- Tests: `tests/test_vi_mosaic.py::test_demo_recover_duck_cli_amortized`

**Step 1: Refresh plan LR guidance**
- Edit `docs/plans/2026-01-29-m2-amortized-scale-study.md` Task 2 LR bullet so it states `--lr 0.003` plus a note "fallback to 0.001 if gradients still explode".

**Step 2: Reserve artifact directories**
```bash
export LONGRUN_ROOT=plans/active/strat-m2-001/reports/$(date -u +%Y-%m-%dT%H%M%SZ)/scale_study/amortized_longrun_20
mkdir -p "$LONGRUN_ROOT" demo_outputs/duck_amortized_longrun_20
```

**Step 3: Run stabilized 500-iter baseline**
```bash
KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  python scripts/demo_recover_duck.py \
    --dataset demo_inputs/duck_multi_image \
    --outdir "$LONGRUN_ROOT" \
    --iterations 500 \
    --mode amortized \
    --k-samples 4 \
    --lr 0.003 \
    --kl-weight 1.0 \
    --observation-mean 25.0 \
    --log-gradients \
    --device cpu | tee "$LONGRUN_ROOT/run.log"
```
- If loss or gradients become `nan`, immediately rerun with `--lr 0.0015`. If that still diverges, drop to `0.001` and document in run.log header.

**Step 4: Copy demo artifacts and capture metrics**
```bash
cp "$LONGRUN_ROOT/duck_loss.png" demo_outputs/duck_amortized_longrun_20/
cp "$LONGRUN_ROOT/duck_summary.json" demo_outputs/duck_amortized_longrun_20/
python - <<'PY'
import json, math, pathlib
root = pathlib.Path(\"$LONGRUN_ROOT\")
data = json.loads((root / \"duck_summary.json\").read_text())
grads = data.get(\"gradient_norms\", [])
def safe_min(seq):
    return min((x for x in seq if x is not None and not math.isnan(x)), default=None)
def safe_max(seq):
    return max((x for x in seq if x is not None and not math.isnan(x)), default=None)
metrics = {
    \"initial_loss\": data[\"results\"][\"initial_loss\"],
    \"final_loss\": data[\"results\"].get(\"final_loss\"),
    \"initial_sigma_deg\": data[\"results\"][\"initial_sigma_deg\"],
    \"final_sigma_deg\": data[\"results\"].get(\"final_sigma_deg\"),
    \"sigma_min_deg\": safe_min(data.get(\"per_image_sigma_deg\", [])),
    \"sigma_max_deg\": safe_max(data.get(\"per_image_sigma_deg\", [])),
    \"gradient_norm_mean\": sum(grads)/len(grads) if grads else None,
    \"iterations\": data[\"config\"][\"iterations\"],
    \"diverged\": bool(any(math.isnan(x) for x in grads))
}
(root / \"metrics_snapshot_longrun.json\").write_text(json.dumps(metrics, indent=2))
PY
```

**Step 5: Run targeted test & stage artifacts**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_demo_recover_duck_cli_amortized -v
git add "$LONGRUN_ROOT" demo_outputs/duck_amortized_longrun_20 docs/plans/2026-01-29-m2-amortized-scale-study.md
```

---

### Task 2: Execute 50-image & 100-image runs (300 iterations)

**Files / Artifacts:**
- Artifact dirs: `plans/active/strat-m2-001/reports/<ts>/scale_study/amortized_scale_50/` and `/amortized_scale_100/`
- Mirrors: `demo_outputs/duck_amortized_scale_50/`, `demo_outputs/duck_amortized_scale_100/`
- Tests: `pytest tests/test_vi_mosaic.py -k amortized`

**Step 1: Reserve artifact directories**
```bash
export SCALE50_ROOT=plans/active/strat-m2-001/reports/$(date -u +%Y-%m-%dT%H%M%SZ)/scale_study/amortized_scale_50
mkdir -p "$SCALE50_ROOT" demo_outputs/duck_amortized_scale_50
sleep 1
export SCALE100_ROOT=plans/active/strat-m2-001/reports/$(date -u +%Y-%m-%dT%H%M%SZ)/scale_study/amortized_scale_100
mkdir -p "$SCALE100_ROOT" demo_outputs/duck_amortized_scale_100
```

**Step 2: Run 50-image training (300 iters @ lr=0.004)**
```bash
KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  python scripts/demo_recover_duck.py \
    --dataset demo_inputs/duck_multi_image_n50 \
    --outdir "$SCALE50_ROOT" \
    --iterations 300 \
    --mode amortized \
    --k-samples 4 \
    --lr 0.004 \
    --kl-weight 1.0 \
    --observation-mean 25.0 \
    --log-gradients \
    --device cpu | tee "$SCALE50_ROOT/run.log"
```
- If gradients exceed `1e8` or loss spikes, rerun with `--lr 0.003` and append note to run.log.

**Step 3: Run 100-image training (300 iters @ lr=0.003)**
```bash
KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  python scripts/demo_recover_duck.py \
    --dataset demo_inputs/duck_multi_image_n100 \
    --outdir "$SCALE100_ROOT" \
    --iterations 300 \
    --mode amortized \
    --k-samples 4 \
    --lr 0.003 \
    --kl-weight 1.0 \
    --observation-mean 25.0 \
    --log-gradients \
    --device cpu | tee "$SCALE100_ROOT/run.log"
```
- Fallback: rerun with `--lr 0.002` if gradients explode.

**Step 4: Mirror artifacts + metrics snapshots**
- Repeat the Step 4 Python snippet from Task 1 for both `$SCALE50_ROOT` and `$SCALE100_ROOT`, writing `metrics_snapshot_50.json` and `metrics_snapshot_100.json`.
- Copy `duck_loss.png` / `duck_summary.json` into the matching `demo_outputs/` dirs.

**Step 5: Run amortized test sweep & stage artifacts**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k amortized -v
git add "$SCALE50_ROOT" "$SCALE100_ROOT" \
        demo_outputs/duck_amortized_scale_50 demo_outputs/duck_amortized_scale_100
```

---

### Task 3: Add amortized metrics summarizer

**Files:**
- Create: `scripts/analysis/summarize_duck_amortized.py`
- Create: `tests/test_analysis_duck_summary.py`
- Create: `tests/fixtures/duck_summary_sample.json`

**Step 1: Write failing test**
```python
# tests/test_analysis_duck_summary.py
from scripts.analysis.summarize_duck_amortized import summarize_runs
from pathlib import Path

def test_summarize_runs_extracts_metrics(tmp_path):
    sample = tmp_path / "sample.json"
    sample.write_text(Path("tests/fixtures/duck_summary_sample.json").read_text())
    row = summarize_runs([sample])[0]
    assert row["label"] == sample.parent.name
    assert row["iterations"] == 3
    assert row["sigma_min_deg"] == 0.25
    assert row["gradient_norm_mean"] == 42.0
```

**Step 2: Run test to confirm failure**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_analysis_duck_summary.py::test_summarize_runs_extracts_metrics -v
```

**Step 3: Implement summarizer script**
```python
# scripts/analysis/summarize_duck_amortized.py
import argparse, csv, json, pathlib, statistics, sys
from typing import Iterable, List, Dict

def summarize_runs(summary_paths: Iterable[pathlib.Path]) -> List[Dict[str, float]]:
    rows = []
    for path in summary_paths:
        data = json.loads(path.read_text())
        grads = data.get("gradient_norms", [])
        row = {
            "label": path.parent.name,
            "iterations": data["config"]["iterations"],
            "initial_sigma_deg": data["results"].get("initial_sigma_deg"),
            "final_sigma_deg": data["results"].get("final_sigma_deg"),
            "sigma_min_deg": min(data.get("per_image_sigma_deg", []), default=None),
            "sigma_max_deg": max(data.get("per_image_sigma_deg", []), default=None),
            "gradient_norm_mean": statistics.fmean(grads) if grads else None,
            "final_loss": data["results"].get("final_loss"),
        }
        rows.append(row)
    return rows

def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize Duck amortized runs")
    parser.add_argument("summary", nargs="+", type=pathlib.Path,
                        help="Paths to duck_summary.json files")
    parser.add_argument("--out", type=pathlib.Path,
                        help="Optional CSV output (stdout default)")
    args = parser.parse_args()
    rows = summarize_runs(args.summary)
    if not rows:
        return 0
    out_file = args.out.open("w", newline="") if args.out else sys.stdout
    writer = csv.DictWriter(out_file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    if args.out:
        out_file.close()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 4: Add sample fixture**
```json
// tests/fixtures/duck_summary_sample.json
{
  "config": {"iterations": 3},
  "results": {
    "initial_sigma_deg": 0.5,
    "final_sigma_deg": 0.4,
    "final_loss": -123.4
  },
  "per_image_sigma_deg": [0.25, 0.45, 0.5],
  "gradient_norms": [21.0, 63.0]
}
```

**Step 5: Re-run tests & stage files**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_analysis_duck_summary.py::test_summarize_runs_extracts_metrics -v
git add scripts/analysis/summarize_duck_amortized.py \
        tests/test_analysis_duck_summary.py tests/fixtures/duck_summary_sample.json
```

---

### Task 4: Update documentation + ledger

**Files:**
- Modify: `docs/strategy/mainstrategy.md` (§7 M2 section)
- Modify: `docs/development/testing_strategy.md` (§6.2)
- Modify: `docs/fix_plan.md`
- Modify: `docs/findings.md` (add `FND-M2-2026-01` if σ<1.5° even with 100 images)
- Update: `input.md` with new mapped tests + artifact dirs

**Step 1: Summarize runs for documentation**
```bash
python scripts/analysis/summarize_duck_amortized.py \
  "$LONGRUN_ROOT/duck_summary.json" \
  "$SCALE50_ROOT/duck_summary.json" \
  "$SCALE100_ROOT/duck_summary.json" \
  --out plans/active/strat-m2-001/reports/$(date -u +%Y-%m-%dT%H%M%SZ)/scale_study/summary.csv
```
- Reference the CSV + per-run metrics in documentation.

**Step 2: Update strategy/testing docs**
- `docs/strategy/mainstrategy.md`: replace the “Next Action” paragraph with the new 500/50/100 results (loss deltas, σ min/max, gradient norms, artifact directories).
- `docs/development/testing_strategy.md`: add the new scale-study commands, dataset paths, and mention the summarizer script under §6.2.

**Step 3: Update fix plan + findings**
- `docs/fix_plan.md`: mark Tasks 1–4 complete, log artifact directories, and append new supervisor state entry referencing this plan and summary CSV.
- `docs/findings.md`: if σ still <1.5° on all runs, add `FND-M2-2026-01` describing the limitation, referencing all three artifact directories and summary CSV.

**Step 4: Refresh input.md & stage docs**
```bash
git add docs/strategy/mainstrategy.md docs/development/testing_strategy.md \
        docs/fix_plan.md docs/findings.md plans/active/strat-m2-001/reports/*/scale_study/summary.csv input.md
```

**Step 5: Final verification + commit**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k "amortized or analysis" -v
pytest tests/test_analysis_duck_summary.py -v
git status -sb
git commit -m "feat: add amortized scale-study evidence"
```

Plan complete and saved to `docs/plans/2026-01-29-m2-scale-study-stability.md`. Two execution options:

1. **Subagent-Driven (this session)** — dispatch a new subagent per task using `superpowers:subagent-driven-development`, review after each task.
2. **Parallel Session** — open a new worktree/session and run `superpowers:executing-plans` to execute Tasks 1–4 with checkpoints.

Which approach?
