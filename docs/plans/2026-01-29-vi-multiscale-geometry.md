# VI Multiscale Geometry Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expand the VI benchmark/diagnostics tooling with reproducible geometry presets and sweeps so we can test whether smaller cells + shorter wavelengths (per `docs/strategy/mainstrategy.md §9`) restore VI σ ≥ 1.5° on the canonical benchmark.

**Architecture:** Mirror the `BenchmarkScenario` pattern from `scripts/benchmark_probabilistic_presets.py`, expose preset selection through both VI CLI entry points, and add a geometry-sweep helper that records ELBO metrics/gradients for each configuration. Run the sweep + canonical benchmark, archiving artifacts under `plans/active/strat-vi-001/reports/<ts>/geometry_*` and updating `docs/findings.md` + `docs/strategy/mainstrategy.md` accordingly.

**Tech Stack:** Python 3.11, PyTorch 2.x, CLI scripts (`scripts/benchmark_vi_mosaic.py`, `scripts/analysis/vi_poisson_diagnostics.py`), tests in `tests/test_vi_mosaic.py`, JSON/Markdown artifacts, `matplotlib` for plots.

---

### Task 1: Geometry preset scaffolding (module + CLI wiring)

**Files:**
- Create: `scripts/vi_geometry_presets.py`
- Modify: `scripts/benchmark_vi_mosaic.py`
- Modify: `scripts/analysis/vi_poisson_diagnostics.py`
- Modify: `tests/test_vi_mosaic.py`

**Step 1: Write failing unit test**

Add to `tests/test_vi_mosaic.py`:

```python
def test_vi_benchmark_geometry_preset_overrides_defaults(tmp_path):
    from scripts.benchmark_vi_mosaic import run_benchmark
    summary = run_benchmark(
        iterations=2,
        k_samples=1,
        output_dir=None,
        geometry_preset="hi_res_small_cell",
    )
    assert summary["config"]["cell_edge_A"] == pytest.approx(60.0)
    assert summary["config"]["fpixels"] == 96
```

**Step 2: Run the targeted test**

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_benchmark_geometry_preset_overrides_defaults -v`
Expected: FAIL (unknown kwarg / preset).

**Step 3: Implement preset module**

- Create `scripts/vi_geometry_presets.py` with a `@dataclass VIGeometryPreset` mirroring `BenchmarkScenario`. Define:
  - `default = VIGeometryPreset(cell_edge_A=100.0, wavelength_A=1.0, distance_mm=100.0, pixel_size_mm=0.1, fpixels=64, spixels=64)`
  - `hi_res_small_cell = VIGeometryPreset(cell_edge_A=60.0, wavelength_A=0.7, distance_mm=80.0, pixel_size_mm=0.075, fpixels=96, spixels=96)`
  - `hi_res_micro = VIGeometryPreset(cell_edge_A=40.0, wavelength_A=0.45, distance_mm=60.0, pixel_size_mm=0.05, fpixels=128, spixels=128)`
- Export `PRESETS` dict + `resolve_geometry(args, overrides)` helper so downstream code can merge explicit CLI overrides on top of preset values. Document reference to `docs/strategy/mainstrategy.md §9` (multi-scale crystals) in module docstring.

**Step 4: Wire presets into benchmark CLI**

- In `scripts/benchmark_vi_mosaic.py`, import the new helper and add `parser.add_argument("--geometry-preset", choices=PRESETS.keys(), default="default")` plus explicit `--cell-edge`, `--wavelength`, etc. precedence comment.
- Update `run_benchmark()` signature to accept `geometry_preset: str | None = None`. Inside `main()`, resolve geometry via helper:

```python
preset = resolve_geometry(args, explicit_overrides={
    "cell_edge_A": args.cell_edge if parser_was_provided else None,
    ...
})
```

- Store the final geometry inside `summary["config"]` and include `summary["geometry_preset"] = preset.name`.
- Ensure both CLI + programmatic calls can pass either `geometry_preset="hi_res_small_cell"` or explicit numeric overrides (explicit numbers win over presets per `docs/plans/2026-01-29-probabilistic-benchmark-realignment.md`).

**Step 5: Update diagnostics CLI**

- In `scripts/analysis/vi_poisson_diagnostics.py`, add the same `--geometry-preset` flag and propagate resolved geometry to `run_diagnostics()` / `_run_vi_refinement()` so diagnostics run under the requested preset. Include geometry metadata in each record (e.g., `record["geometry"] = {...}`).

**Step 6: Re-run targeted tests**

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_benchmark_geometry_preset_overrides_defaults -v`
Expected: PASS.

**Step 7: Commit scaffolding**

```bash
git add scripts/vi_geometry_presets.py scripts/benchmark_vi_mosaic.py \
        scripts/analysis/vi_poisson_diagnostics.py tests/test_vi_mosaic.py
git commit -m "feat: add VI geometry presets and CLI wiring"
```

---

### Task 2: Geometry sweep helper + test coverage

**Files:**
- Modify: `scripts/analysis/vi_poisson_diagnostics.py`
- Modify: `tests/test_vi_mosaic.py`
- Artifacts: `plans/active/strat-vi-001/reports/<ts>/geometry_dev/`

**Step 1: Add failing geometry-sweep test**

Append to `tests/test_vi_mosaic.py`:

```python
def test_vi_geometry_sweep_returns_all_presets(tmp_path):
    from scripts.analysis.vi_poisson_diagnostics import run_geometry_sweep
    records = run_geometry_sweep(
        presets=["default", "hi_res_small_cell"],
        iterations=3,
        outdir=tmp_path,
        k_samples=1,
        observation_mean=5.0,
    )
    assert {r["geometry_preset"] for r in records} == {"default", "hi_res_small_cell"}
    for rec in records:
        assert "sigma_max_deg" in rec
        assert rec["prior_spread_deg"] > 0
```

**Step 2: Run the new test**

`KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_vi_geometry_sweep_returns_all_presets -v`
Expected: FAIL (helper missing).

**Step 3: Implement geometry sweep**

- Inside `scripts/analysis/vi_poisson_diagnostics.py`, add `run_geometry_sweep(...)` that:
  - Accepts `presets`, `iterations`, `k_samples`, `observation_mean`, `prior_*` knobs, and `outdir`.
  - Resolves each preset via the helper, calls `run_diagnostics()` with `capture_stride=1`, and stores results under `<outdir>/<preset>/diagnostics.json` + `summary.md`.
  - Consolidates per-preset stats (σ trajectory max, gradient ratios, observation stats) into `geometry_sweep.json` and Markdown table.
- Add CLI flags `--geometry-grid default,hi_res_small_cell,hi_res_micro` and `--geometry-grid-outdir PATH`. When set, skip the single-run outputs and call `run_geometry_sweep()`.

**Step 4: Extend diagnostics snapshot test**

- Update `tests/test_vi_mosaic.py::test_vi_diagnostics_snapshot` to assert that `record["geometry"]["cell_edge_A"]` exists.

**Step 5: Run focused pytest selection**

`KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k "geometry_sweep or vi_diagnostics_snapshot" -v`
Expected: PASS.

**Step 6: Capture dev artifact (optional but encouraged)**

```
ts=$(date -u +%Y-%m-%dT%H%M%SZ)
out=plans/active/strat-vi-001/reports/${ts}/geometry_dev
mkdir -p "$out"
KMP_DUPLICATE_LIB_OK=TRUE python scripts/analysis/vi_poisson_diagnostics.py \
  --iterations 5 --k-samples 2 --geometry-grid default,hi_res_small_cell \
  --geometry-grid-outdir "$out"
```

**Step 7: Commit sweep helper**

```bash
git add scripts/analysis/vi_poisson_diagnostics.py tests/test_vi_mosaic.py \
        plans/active/strat-vi-001/reports/${ts}/geometry_dev
git commit -m "feat: add VI geometry sweep helper"
```

---

### Task 3: Execute multiscale sweep + canonical benchmark, update docs

**Artifacts:** `plans/active/strat-vi-001/reports/<ts>/geometry_sweep/`, `/geometry_benchmark/`
**Docs:** `docs/findings.md`, `docs/strategy/mainstrategy.md`, `docs/fix_plan.md`, `input.md`

**Step 1: Prepare artifact directories**

```
ts=$(date -u +%Y-%m-%dT%H%M%SZ)
SWEEP=plans/active/strat-vi-001/reports/${ts}/geometry_sweep
BENCH=plans/active/strat-vi-001/reports/${ts}/geometry_benchmark
mkdir -p "$SWEEP" "$BENCH"
```

**Step 2: Run geometry sweep diagnostics**

```
KMP_DUPLICATE_LIB_OK=TRUE python scripts/analysis/vi_poisson_diagnostics.py \
  --iterations 40 --capture-stride 1 --k-samples 4 \
  --observation-mean 25 --observation-normalization mean --observation-seed 321 \
  --prior-spread-start 2.0 --prior-spread-end 0.5 --prior-warmup-steps 20 \
  --prior-log-sigma 0.2 --geometry-grid default,hi_res_small_cell,hi_res_micro \
  --geometry-grid-outdir "$SWEEP"
```

Document σ_max, gradient ratios, and any NaN/overflow incidents in `$SWEEP/summary.md`.

**Step 3: Select best preset + run canonical benchmark**

- Inspect `$SWEEP/summary.md`; choose the preset with highest σ or gradient ratio.
- Run the 150-iteration benchmark with matching geometry:

```
KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 python scripts/benchmark_vi_mosaic.py \
  --iterations 150 --k-samples 4 --observation-mean 25 --observation-normalization mean \
  --observation-seed 321 --kl-weight-start 0.2 --kl-weight-end 1.0 --kl-warmup-steps 120 \
  --prior-spread-start 2.0 --prior-spread-end 0.5 --prior-warmup-steps 120 \
  --prior-log-sigma 0.2 --geometry-preset <best_preset> --outdir "$BENCH"
```

- Summarise VI σ trajectory vs MC/analytic in `$BENCH/summary.md`.

**Step 4: Update docs + findings**

- Append results to `docs/findings.md` under FND-VI-2026-01, referencing `$SWEEP` and `$BENCH` artifact paths.
- Update `docs/strategy/mainstrategy.md §9` with a brief paragraph on multiscale geometry outcomes.
- Refresh `docs/fix_plan.md` (STRAT-VI-001) to state Task 24 follow-up complete + note whether multiscale geometry succeeded or failed, plus next mitigation (e.g., normalizing flow posterior).
- Rewrite `input.md` per supervisor template with new focus/mapped tests referencing this plan.

**Step 5: Tests + lint**

Run canonical smoke + geometry tests:

```
KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k "geometry or benchmark_script_smoke" -v
```

**Step 6: Commit artifacts + docs**

```bash
git add "$SWEEP" "$BENCH" docs/findings.md docs/strategy/mainstrategy.md docs/fix_plan.md input.md
git commit -m "chore: document VI multiscale geometry sweep"
```

---

Plan complete and saved to `docs/plans/2026-01-29-vi-multiscale-geometry.md`.

Two execution options:
1. **Subagent-Driven (this session)** — launch `superpowers:subagent-driven-development` and run each task with check-ins.
2. **Parallel Session** — new terminal/worktree executing the plan via `superpowers:executing-plans`.

Which approach should we take?
