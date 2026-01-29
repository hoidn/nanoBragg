# Probabilistic Benchmark Realignment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rework the probabilistic benchmark so it exposes tunable geometry overrides, gradient diagnostics, and a high-resolution scenario that demonstrates the analytic kernel's convergence and >4× speedup targets from `docs/strategy/mainstrategy.md` §4.

**Architecture:** Extend `scripts/benchmark_probabilistic.py` with structured scenario configs, CLI overrides, and optional instrumentation hooks instead of one-off constants. Introduce helper utilities so new behavior is covered by targeted tests and reproducible CLI runs, then rerun the benchmark under a high-resolution preset that surfaces non-zero mosaic gradients. Documentation and artifacts must advertise the new scenario and measured win.

**Tech Stack:** Python 3.11, PyTorch, pytest, Matplotlib, JSON/PNG artifacts.

---

### Task 1: Geometry overrides + gradient diagnostics

**Files:**
- Modify: `scripts/benchmark_probabilistic.py`
- Create: `tests/scripts/test_benchmark_probabilistic_cli.py`

**Step 1: Factor scenario config helper**

```python
# scripts/benchmark_probabilistic.py
@dataclass
class BenchmarkScenario:
    cell_edge_A: float
    wavelength_A: float
    distance_mm: float
    pixel_size_mm: float
    fpixels: int
    spixels: int

    def apply(self, detector_cfg: DetectorConfig) -> DetectorConfig:
        ...  # ensures overrides stay scoped
```

Move the current `FIXED_PARAMS`, `DETECTOR_CONFIG`, `BEAM_CONFIG` into a `DEFAULT_SCENARIO` instance plus helper functions `make_crystal_config(spread, domains, scenario)` and `make_detector_config(scenario)` so tests can import and reuse them.

**Step 2: Add CLI overrides + --scenario option**

Add parser arguments:
- `--cell-edge`, `--wavelength`, `--distance`, `--pixel-size`
- `--fpixels`, `--spixels`
- `--scenario {default,hi_res_a,hi_res_b}` (validated against a module-level dict)

Resolve precedence: explicit CLI overrides beat `--scenario`, and `--scenario` overrides the baked-in default when no explicit flag is provided. Update `build_configs` to accept a `BenchmarkScenario` object created from the parsed options.

**Step 3: Implement gradient diagnostics**

Add `--diagnose-gradients` flag. Inside `run_refinement`, before `optimizer.step()`, capture `grad = spread_param.grad.detach().clone()` and append to a list. When the flag is set, print `np.mean(np.abs(grads))` per backend along with the current iteration log, and insert that vector into the JSON summary (e.g., `"spread_gradients": [...]`). Ensure the gradients stay on CPU regardless of device via `.item()` only after detaching (spread_param itself should stay differentiable). Update the plot annotation to mention whether gradient ever dips below `1e-6` when diagnosis runs.

**Step 4: Add pytest coverage for CLI parsing**

Create `tests/scripts/test_benchmark_probabilistic_cli.py` that imports `scripts.benchmark_probabilistic` as a module (without executing the CLI). Tests:
- `test_scenario_override_defaults()` ensures `resolve_scenario(args)` produces expected values when only `--scenario hi_res_a` is set.
- `test_cli_flag_precedence()` instantiates argparse Namespace with both `--scenario` and explicit `--distance`, verifying explicit values win.
- `test_diagnose_inserts_gradients_key(tmp_path)` writes a 1-iteration JSON via calling `main()` with patched args and asserts the JSON contains the gradient array when `--diagnose-gradients` and `--plot-only` interplay happen.

Use `pytest -k benchmark_probabilistic_cli -v` as the verification command.

**Step 5: Commit**

```bash
git add scripts/benchmark_probabilistic.py tests/scripts/test_benchmark_probabilistic_cli.py
git commit -m "feat: benchmark overrides + gradient diagnostics"
```

---

### Task 2: High-resolution presets + sweep helper

**Files:**
- Modify: `scripts/benchmark_probabilistic.py`
- Create: `scripts/benchmark_probabilistic_presets.py`
- Modify: `docs/plans/2026-01-29-probabilistic-simulator-implementation.md` (Task 3 section references)

**Step 1: Define preset catalog**

Create `scripts/benchmark_probabilistic_presets.py` that exposes:

```python
PRESETS = {
    "default": BenchmarkScenario(...),
    "hi_res_a": BenchmarkScenario(cell_edge_A=40.0, wavelength_A=0.65, distance_mm=80.0, pixel_size_mm=0.075, fpixels=96, spixels=96),
    "hi_res_b": BenchmarkScenario(cell_edge_A=30.0, wavelength_A=0.5, distance_mm=60.0, pixel_size_mm=0.05, fpixels=128, spixels=128),
}
```

Keep the presets in a dedicated module so they can be imported by both the CLI and any future notebooks. Document the physics rationale (smaller cell => larger reciprocal spacing, shorter wavelength => pushes reflections to higher |q| where the Gaussian envelope varies).

**Step 2: Wire presets into CLI + add --sweep-json**

Back in `scripts/benchmark_probabilistic.py`, import `PRESETS`. Update argument parsing so `--scenario` picks from `PRESETS.keys()`, and add `--sweep-json` that accepts a path to a JSON file shaped like `[{"scenario": "hi_res_a", "iterations": 60}, ...]`. When provided, iterate through entries, running a truncated refinement (<=60 iters) per scenario, collecting:
- `final_loss`
- `final_spread`
- `mean_iteration_time`
- `mean_abs_gradient`

Persist the sweep results to `<outdir>/probabilistic_vs_mc_sweep.json`.

**Step 3: CLI dry-run + pytest hook**

Add a `--dry-run` option that only prints the parsed scenario and exits (used by tests to avoid long sims). Extend the pytest module to spawn the CLI with `--dry-run --scenario hi_res_a --cell-edge 35` using `subprocess.run` and assert stdout shows the resolved values.

**Step 4: Update implementation plan references**

In `docs/plans/2026-01-29-probabilistic-simulator-implementation.md` Task 3, append a bullet referencing the new presets and sweep output so future readers know how to regenerate the improved benchmark.

**Step 5: Commit**

```bash
git add scripts/benchmark_probabilistic.py scripts/benchmark_probabilistic_presets.py docs/plans/2026-01-29-probabilistic-simulator-implementation.md tests/scripts/test_benchmark_probabilistic_cli.py
git commit -m "feat: benchmark presets + sweep"
```

---

### Task 3: Evidence run + documentation refresh

**Files:**
- Modify: `docs/strategy/mainstrategy.md`
- Modify: `README_PYTORCH.md`
- Modify: `docs/fix_plan.md`
- Update artifacts: `demo_outputs/probabilistic_vs_mc_loss.png`, `demo_outputs/probabilistic_vs_mc_summary.json`, `demo_outputs/probabilistic_vs_mc_sweep.json`, `plans/active/strat-prob-002/reports/<timestamp>/`

**Step 1: Run diagnostic sweeps**

Commands:

```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmark_probabilistic.py \
  --iterations 40 --device cpu --scenario hi_res_a --diagnose-gradients \
  --sweep-json scripts/presets/hi_res_probe.json

KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmark_probabilistic.py \
  --iterations 100 --device cpu --scenario hi_res_b --diagnose-gradients
```

Expectations:
- The hi_res_a sweep JSON shows mean absolute gradient ≥ 1e-3 and speedup ≥ 4×.
- The hi_res_b full run yields a monotonic analytic curve plus PNG/JSON artifacts under `demo_outputs/`.

Copy the updated PNG/JSON plus console logs into a new timestamped folder under `plans/active/strat-prob-002/reports/`.

**Step 2: Update docs with new evidence**

In `docs/strategy/mainstrategy.md` §4, replace the previous CPU measurements with the new hi-res metrics (include gradient magnitude observation). In `README_PYTORCH.md` Performance section, describe the new CLI knobs and mention how to pass `--scenario hi_res_b --diagnose-gradients` to reproduce the published plot. Reference the sweep JSON for the ≥4× speedup claim.

**Step 3: Fix plan + findings**

Edit `docs/fix_plan.md` so STRAT-PROB-002 next actions reference the hi-res scenario handoff rather than the original 64×64 geometry. If the Model Mismatch risk remains for low-resolution cubes, log a new finding (e.g., `FND-PROB-2026-01` in `docs/findings.md`) summarizing the diagnostic results and linking to the sweep artifact.

**Step 4: Commit evidence + docs**

```bash
git add demo_outputs/ docs/strategy/mainstrategy.md README_PYTORCH.md docs/fix_plan.md docs/findings.md plans/active/strat-prob-002/reports/<timestamp>/
git commit -m "docs: probabilistic benchmark hi-res evidence"
```

---

### Task 4: Input + regression guardrail

**Files:**
- Modify: `input.md`
- Modify: `plans/active/strat-prob-002/README.md` (note the new presets and sweep log path)
- Update: `plans/active/strat-prob-002/reports/<timestamp>/summary.md`

**Step 1: Refresh supervisor handoff**

Re-write `input.md` (per supervisor workflow) to target the hi-res benchmark task, referencing the new CLI commands and mapped tests from Task 1. Include `pytest -k benchmark_probabilistic_cli -v` plus the benchmark CLI command in the mapped tests list.

**Step 2: Summaries + README adjustments**

Add a subsection to `plans/active/strat-prob-002/README.md` enumerating the preset scenarios and the most recent report directory. Update `summary.md` for this loop with the hi-res evidence pointer.

**Step 3: Commit handoff docs**

```bash
git add input.md plans/active/strat-prob-002/README.md plans/active/strat-prob-002/reports/<timestamp>/summary.md
git commit -m "supervisor: handoff for hi-res probabilistic benchmark"
```

---

**Execution Handoff:** Plan complete and saved to `docs/plans/2026-01-29-probabilistic-benchmark-realignment.md`. Two execution options:

1. **Subagent-Driven (this session)** — dispatch fresh subagents per task with `superpowers:subagent-driven-development` for rapid checkpointed execution.
2. **Parallel Session (separate)** — start a new session/worktree, load this plan, and run it end-to-end using `superpowers:executing-plans`.

Please choose the approach before implementation begins.
