# Probabilistic Simulator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship a drop-in `ProbabilisticSimulator` plus benchmark artifacts that demonstrate the analytic mosaic model described in `docs/strategy/mainstrategy.md`.

**Architecture:** Implement a subclass of `Simulator` that reuses the existing vectorized detector/geometry stack, swaps in a probabilistic physics kernel per `docs/plans/2026-01-29-probabilistic-simulator-design.md`, and exposes a benchmark script that compares Monte Carlo vs analytic convergence.

**Tech Stack:** PyTorch (CPU+CUDA), Matplotlib, NumPy, nanoBragg CLI-style configs, pytest.

---

### Task 1: Add Probabilistic Simulator Tests (expected to fail first)

**Files:**
- Create: `tests/test_probabilistic_simulator.py`
- Modify: none (test-only task)
- Test Command: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_probabilistic_simulator.py`

**Step 1: Write failing regression + gradcheck tests**

```python
# tests/test_probabilistic_simulator.py
import torch
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.config import BeamConfig, CrystalConfig, DetectorConfig

@pytest.mark.cuda
@pytest.mark.parametrize("device", [torch.device("cpu"), torch.device("cuda")])
def test_probabilistic_matches_monte_carlo(device):
    # TODO: instantiate ProbabilisticSimulator once available
    raise NotImplementedError
```

Include two tests:
1. **`test_probabilistic_matches_high_domain_limit`** — run baseline `Simulator` with `mosaic_domains=64` and the future `ProbabilisticSimulator` with the same config (except it will ignore domains) on a tiny 8×8 detector ROI; assert max relative error < 5%.
2. **`test_probabilistic_gradcheck`** — wrap a single-pixel forward pass (use `DetectorConfig(spixels=1, fpixels=1)`) and call `torch.autograd.gradcheck` on `mosaic_spread_deg` using double precision; `ProbabilisticSimulator` should keep gradients intact.

Use deterministic seeds for Monte Carlo (`mosaic_seed=7`). Reference `docs/strategy/mainstrategy.md §3A` for the “drop-in” contract inside comments so the intent is locked into the test.

**Step 2: Run the targeted test module to verify it fails**

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_probabilistic_simulator.py`
Expected: ImportError or `NotImplementedError` that confirms the simulator class doesn’t exist yet.

**Step 3: Commit test scaffold (optional)**

```bash
git add tests/test_probabilistic_simulator.py
git commit -m "test: add probabilistic simulator regression harness"  # optional checkpoint
```

---

### Task 2: Implement ProbabilisticSimulator Kernel

**Files:**
- Create: `src/nanobrag_torch/simulators/probabilistic.py`
- Modify: `src/nanobrag_torch/__init__.py`, `src/nanobrag_torch/simulator.py`, `pyproject.toml` (entry point), `tests/test_probabilistic_simulator.py`
- Test Command: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_probabilistic_simulator.py`

**Step 1: Create module + class skeleton**

Define `ProbabilisticSimulator(Simulator)` with docstring referencing `docs/plans/2026-01-29-probabilistic-simulator-design.md` and `docs/strategy/mainstrategy.md §3`. Add attributes:
- `_analytic_mosaic_spread_rad`
- `_stash_mosaic_state()` / `_restore_mosaic_state()` helpers for stash-and-patch run logic (set `mosaic_spread_deg=0`, `mosaic_domains=1`).
- Override `_compute_physics_for_position` to call new kernel.

Export the class via `src/nanobrag_torch/__init__.py` so `from nanobrag_torch.simulators import ProbabilisticSimulator` works.

**Step 2: Implement probabilistic kernel**

Inside `src/nanobrag_torch/simulators/probabilistic.py`, add a pure function `compute_probabilistic_physics_for_position(...)` mirroring the baseline kernel signature. Implementation specifics:
- Accept `mosaic_spread_rad` tensor and `eps=1e-12`.
- Compute scattering vector `s` exactly as baseline (reuse `compute_physics_for_position` helper or copy logic if factoring is easier).
- Convert to fractional Miller indices (h, k, l) using rotated vectors already supplied by `Simulator.run`.
- Compute integer HKL for structure-factor lookup, reuse `crystal_get_structure_factor` callback.
- Lattice factor uses existing `sincg` / `sinc3` utilities (import from `nanobrag_torch.utils.physics`).
- Compute `dQ = dh * a_star + dk * b_star + dl * c_star` where `dh = h - h0` etc, all tensors kept differentiable.
- `sigma = q_norm * torch.tan(mosaic_spread_rad.clamp_min(1e-8)) + eps` with `q_norm = torch.norm(scattering_vector, dim=-1)`.
- Analytic envelope `gaussian = torch.exp(-torch.sum(dQ * dQ, dim=-1) / (2.0 * sigma * sigma))`.
- Return `(intensity_with_gaussian, intensity_pre_polar)` to preserve tracing behavior from base kernel.
- Device/dtype neutral: infer from `pixel_coords_angstroms`.

**Step 3: Override run() to stash/patche mosaic config**

Implement `ProbabilisticSimulator.run(...)` to:
1. Capture `orig_spread`, `orig_domains`, `orig_seed` from `self.crystal.config`.
2. If `self._analytic_mosaic_spread_rad` is unset, convert degrees→radians once and store as tensor on device.
3. Temporarily set `config.mosaic_spread_deg = 0.0` and `config.mosaic_domains = 1` before calling `super().run(...)`.
4. Pass `mosaic_spread` into `_compute_physics_for_position` via instance property (e.g., set `self._analytic_spread_tensor`).
5. Ensure `finally` restores the original config to avoid side effects on repeated runs.

**Step 4: Wire kernel invocation**

Override `_compute_physics_for_position` to call the probabilistic kernel with the stored spread tensor. Keep API parity with baseline, still returning `(post_polar, pre_polar)` and reusing polarization logic from parent by calling a helper for polarization + scaling. Guard against `None` spread (raise `RuntimeError` if stash patch not set to catch misuse).

**Step 5: Update tests for passing behavior**

Fill in `tests/test_probabilistic_simulator.py` to:
- Instantiate the new simulator via `from nanobrag_torch.simulators.probabilistic import ProbabilisticSimulator` (or package export if added).
- Monte Carlo baseline: set `mosaic_domains=64`, `phi_steps=1`, small detector ROI (use `DetectorConfig` ROI fields) for speed.
- Use `torch.testing.assert_close` with `rtol=5e-2`, `atol=1e-3` on normalized intensity.
- For gradcheck, convert configs to double precision and call `gradcheck` on `lambda spread: simulator.run().sum()` style closure. Set `torch.backends.cuda.matmul.allow_tf32 = False` for determinism.

**Step 6: Run focused pytest target**

Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_probabilistic_simulator.py`
Expected: PASS on CPU; run again with `CUDA_VISIBLE_DEVICES=0` to validate GPU path if available.

**Step 7: Commit implementation**

```bash
git add src/nanobrag_torch/__init__.py src/nanobrag_torch/simulator.py src/nanobrag_torch/simulators/probabilistic.py tests/test_probabilistic_simulator.py
git commit -m "feat: add probabilistic simulator kernel"
```

---

### Task 3: Benchmark Script + Plot

**Files:**
- Create: `scripts/benchmark_probabilistic.py`
- Modify: `docs/strategy/mainstrategy.md` (reference artifact path) and `README_PYTORCH.md` (add usage snippet), `demo_outputs/.gitignore` (ensure JSON/PNG tracked)
- Artifacts: `demo_outputs/probabilistic_vs_mc_loss.png`, `demo_outputs/probabilistic_vs_mc_summary.json`
- Test Command: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmark_probabilistic.py --iterations 200`

**Step 1: Implement benchmark CLI**

Script requirements:
- Set `os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"` and `os.environ["NANOBRAGG_DISABLE_COMPILE"] = "1"` at top.
- CLI args: `--iterations`, `--device`, `--outdir`, `--plot-only` (optional to skip reruns).
- Workflow per strategy §4: generate ground-truth Monte Carlo image (`Simulator` w/ `mosaic_domains=50`), baseline Monte Carlo refinement (`mosaic_domains=5`), analytic refinement (`ProbabilisticSimulator`).
- Use `scripts/refinement_demo_diffuse.py` constants as starting point (reuse `refinement_demo_diffuse.FIXED_PARAMS`).
- Each refinement loop: track loss per iteration (MSE between simulated and GT), record wall-clock via `time.perf_counter()` around forward+backward+optimizer step.
- Define helper builders:
  - `build_configs(device, dtype, mosaic_domains, mosaic_spread_deg)` that returns `Crystal`, `Detector`, configs, and `BeamConfig` derived from the diffuse demo constants so both simulators share identical geometry.
  - `run_refinement(simulator, spread_param, iterations, optimizer_kwargs, label)` that performs a gradient descent loop, returns `loss_history` and `per_iter_times`.
- Deterministic seeding: call `torch.manual_seed(7)` and fix any `torch.Generator` used for random numbers so MC baseline stays repeatable (aligns with plan Task 1 seeds).
- Parameterization:
  - Optimize only `mosaic_spread_deg` for both simulators (misset locked to demo defaults) to isolate the probabilistic benefit.
  - Use identical optimizer hyperparameters (e.g., Adam LR=0.02) and initialize spread to `0.5°` for both baselines to make curves comparable.
- Device/dtype neutrality: accept `--device` argument (`cpu` default) and cast configs + tensors accordingly; keep dtype float32 for runtime parity, but allow overriding via CLI flag in the future.
- Add structured logging (e.g., `print(f"[baseline][{i}] loss=... time=...")`) so the supervisor can skim convergence from terminal output.

**Step 2: Plot + summary outputs**

- Use Matplotlib to plot loss vs iteration for baseline vs analytic plus ground truth reference; label curves clearly, include speedup annotation.
- Annotate plot with:
  - Average iteration time for each curve (e.g., `1.21s/iter` vs `0.24s/iter`)
  - Final loss values so PI reviewers can read off the convergence win visually.
- Save summary JSON containing:
  ```json
  {
    "ground_truth": {"mosaic_spread_deg": 2.0, "domains": 50},
    "baseline": {
      "label": "Simulator (MC, domains=5)",
      "loss": [...],
      "per_iteration_seconds": [...],
      "total_seconds": 12.3
    },
    "probabilistic": {
      "label": "ProbabilisticSimulator",
      "loss": [...],
      "per_iteration_seconds": [...],
      "total_seconds": 2.8
    },
    "config": {...}
  }
  ```
  Include the exact CLI arguments used so runs are reproducible.
- Ensure script creates `demo_outputs/` if missing and writes to `demo_outputs/probabilistic_vs_mc_loss.png` + JSON by default or to `--outdir` if provided. Support `--plot-only` by loading an existing JSON file and regenerating the PNG without rerunning the refinement loops.

**Step 3: Document benchmark hook**

- Update `README_PYTORCH.md` (Performance section) with a “Probabilistic Mosaic Benchmark” subsection that includes:
  - One-paragraph summary of what the script demonstrates.
  - Exact command (`KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmark_probabilistic.py --iterations 150 --device cpu`) and the expected artifacts (`demo_outputs/probabilistic_vs_mc_loss.png` and `.json`).
  - Interpreting the plot (probabilistic curve smoother, faster, reaches lower loss).
- Update `docs/strategy/mainstrategy.md` §4 bullet to reference the specific script/outputs now that they exist and cite the measured speedup ratio from Step 4 so strategy evidence is concrete.

**Step 4: Run benchmark for evidence**

Command: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmark_probabilistic.py --iterations 150 --device cpu`
Expected: script prints per-iteration stats, produces PNG/JSON in `demo_outputs/`. Capture runtime + final losses for supervisor report.
- Copy the resulting PNG, JSON, and console log into `plans/active/strat-prob-002/reports/<timestamp>/` so future reviewers can audit the exact evidence bundle without rerunning the script.
- Record the measured speedup (baseline mean iter time ÷ probabilistic mean iter time) in both the report and `docs/strategy/mainstrategy.md`.

**Step 5: Commit benchmark + docs**

```bash
git add scripts/benchmark_probabilistic.py demo_outputs/.gitignore README_PYTORCH.md docs/strategy/mainstrategy.md
git commit -m "feat: add probabilistic benchmark and docs"
```

---

### Task 4: (Optional) Integration Smoke Test

If time permits, run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_perf_005.py::TestTorchCompile::test_simulator_compile` to make sure the new subclass doesn’t break compile guards. Not part of acceptance but recommended before merging.
