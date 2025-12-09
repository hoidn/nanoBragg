# nanoBragg PyTorch Architecture Design (Addendum)

## 1.1 Tricubic Interpolation & Detector Absorption Vectorization

The core simulator physics loops have been fully vectorized to eliminate Python-level iteration and enable efficient GPU acceleration. This section documents the batched tensor flows for two critical computational paths: structure factor interpolation and detector absorption.

### 1.1.1 Tricubic Interpolation Pipeline

**Objective:** Sample structure factors at arbitrary fractional Miller indices using 4×4×4 neighborhood interpolation without Python loops.

**Implementation:** `src/nanobrag_torch/models/crystal.py` (`_tricubic_interpolation`, commit 12742e5) and `src/nanobrag_torch/utils/physics.py` (`polint_vectorized`, `polin2_vectorized`, `polin3_vectorized`, commit f796861).

**C-Code Reference:** `nanoBragg.c` lines 2604-3278 (polin3/polin2/polint implementations).

**Tensor Flow:**

1. **Batched Neighborhood Gather** (Phase C)
   - Input: Fractional Miller indices `(h, k, l)` with shape `(B,)` where `B = sources × phi_steps × mosaic_domains × oversample²`
   - Compute 64 neighbor indices: `(h0-1:h0+2, k0-1:k0+2, l0-1:l0+2)` via broadcasting
   - Output: `neighbor_F` tensor with shape `(B, 4, 4, 4)` containing structure factors for all 64 neighbors
   - Out-of-bounds handling: Single-pass bounds check; fallback to `default_F` for invalid queries

2. **Batched Polynomial Evaluation** (Phase D)
   - 1D interpolation (`polint_vectorized`): Processes `(B, 4)` → `(B,)` via vectorized Neville's algorithm
   - 2D interpolation (`polin2_vectorized`): Chains four 1D passes then aggregates
   - 3D interpolation (`polin3_vectorized`): Chains sixteen 1D passes, then four 2D passes, then final 1D
   - All operations preserve `requires_grad=True` for differentiability
   - Shape: `(B, 4, 4, 4)` → `(B,)` structure factors via pure tensor arithmetic

**Evidence:**
- **Correctness:** `tests/test_tricubic_vectorized.py` (19 tests, CPU + CUDA parametrization)
- **Performance:** Phase E microbenchmarks show ≤1.2% delta vs baseline (`reports/2025-10-vectorization/phase_e/perf/20251009T034421Z/`)
- **Parity:** AT-STR-002 acceptance tests pass with correlation >0.999

**CUDA Status:** CPU validation complete. CUDA execution blocked by pre-existing device-placement defect (tracked in `docs/fix_plan.md` Attempt #14; see PERF-PYTORCH-004).

### 1.1.2 Detector Absorption Vectorization

**Objective:** Process detector thickness layers in parallel to compute depth-dependent capture fractions.

**Implementation:** `src/nanobrag_torch/simulator.py` lines 1764-1787 (validated Phase F; already vectorized).

**C-Code Reference:** `nanoBragg.c` lines 2975-2983 (detector absorption loop).

**Tensor Flow:**

1. **Parallax Calculation**
   - Compute observation direction `obs_dir = pixel_pos / |pixel_pos|` for all pixels
   - Parallax factor: `ρ = detector_normal · obs_dir` (shape: `(S, F)`)
   - Broadcast to `(thicksteps, S, F)` for layer-wise computation

2. **Layer Capture Fractions**
   - Formula: `capture[t] = exp(−t·Δz·μ/ρ) − exp(−(t+1)·Δz·μ/ρ)` where `μ = 1/attenuation_depth`
   - Single vectorized operation processes all layers simultaneously
   - Shape: `(thicksteps, S, F)` capture fraction tensor

3. **Integration with Main Loop**
   - Batched over `(thicksteps, sources, phi_steps, mosaic_domains, oversample², S, F)`
   - Device/dtype neutral via `.device` property from input tensors
   - Preserves gradient flow (no `.item()` or detached operations)

**Evidence:**
- **Correctness:** `tests/test_at_abs_001.py` extended to 16 parametrized tests (8/8 CPU passing; CUDA blocked)
- **Performance:** Phase F3 CPU benchmarks show 0.0% regression vs baseline (`reports/2025-10-vectorization/phase_f/perf/20251009T050859Z/`)
- **Physics:** Capture fractions sum to `1 − exp(−thickness·μ/ρ)` within 1e-6 tolerance

**CUDA Status:** CPU validation complete with zero performance regression. CUDA benchmarks deferred pending device-placement fix (see `docs/fix_plan.md` Attempt #14 and Phase F summary for rerun commands).

### 1.1.3 Broadcast Shape Reference

All vectorized paths follow the canonical broadcast pattern from `arch.md` §8:

- **Pixel grid:** `(S, F)` for slow/fast detector dimensions
- **Subpixel sampling:** `(oversample², S, F)` when `oversample > 1`
- **Thickness layers:** `(thicksteps, S, F)` for detector absorption
- **Full batch:** `(sources, phi_steps, mosaic_domains, oversample², thicksteps, S, F)` in the general case

Extensions must preserve these shapes; adding a new sampling dimension requires expanding the broadcast pattern, not introducing Python loops.

### 1.1.4 Follow-Up Work

**CUDA Performance & Validation:** Once the device-placement defect is resolved (PERF-PYTORCH-004):
1. Rerun `tests/test_tricubic_vectorized.py` on CUDA (expect 19/19 passing)
2. Rerun `tests/test_at_abs_001.py -k cuda` (expect 8/8 passing)
3. Execute CUDA benchmarks per `reports/2025-10-vectorization/phase_f/summary.md` Appendix
4. Append metrics to Phase E/F artifacts and update `docs/fix_plan.md` with CUDA evidence

**References:**
- **Plans:** `plans/active/vectorization.md` (Phases C-F complete)
- **Artifacts:** `reports/2025-10-vectorization/` (phase_c through phase_f evidence bundles)
- **C-Code:** `nanoBragg.c:2604-3278` (tricubic), `nanoBragg.c:2975-2983` (absorption)

### 1.1.5 Source Weighting & Integration (C-Parity Confirmed)

**Objective:** Ensure equal weighting across all sources per normative spec, matching C reference behavior.

**Implementation:** `src/nanobrag_torch/simulator.py` lines 399-423 (guard) and steps normalization at line 1892.

**C-Code Reference:** `nanoBragg.c` lines 2570-2720 (source ingestion and steps calculation).

**Normative Spec:** `specs/spec-a-core.md:151-153` explicitly states that source weight and wavelength columns are read but ignored; CLI `-lambda` is authoritative and equal weighting applies via division by source count.

**Parity Validation:**
- **Phase H Reassessment:** `reports/2025-11-source-weights/phase_h/20251010T002324Z/parity_reassessment.md` supersedes legacy divergence classification; C code inspection (lines 2570-2720) confirms weights stored in `source_I[]` are never used as multiplicative factors, and `steps = sources * mosaic_domains * phisteps * oversample^2` divides by count, not weight sum.
- **Parity Thresholds:** Correlation ≥0.999, |sum_ratio−1| ≤5e-3 (observed: 0.9999886, 0.0038 across seven consecutive validation runs)
- **Evidence:** `tests/test_cli_scaling.py::TestSourceWeightsDivergence` (7 tests passing, xfail removed in Phase H2)

**Data Flow:**
1. Source weights are parsed from sourcefile but never multiplied into intensity contributions
2. All sources contribute equally to pixel accumulation
3. Final normalization: `I_scaled = r_e^2 * fluence * I / steps` where `steps = source_count * ...`
4. Weight column serves documentary purpose only (may encode flux metadata for external tools)

**Known C Defect (Decoupled):** Comment lines in sourcefiles are incorrectly parsed as zero-weight sources, inflating count in C binary. Tracked separately in `[C-SOURCEFILE-001]` and does not affect weight handling semantics.

**Acceptance:** AT-SRC-001 (sourcefile and weighting) validates equal contribution via correlation checks.

## 1.2 Differentiability vs Performance

Principle: Differentiability is required; over-hardening is not. Prefer the minimal change that passes gradcheck and preserves vectorization.

- Minimal Differentiability Contract
  - Return analytic limits at removable singularities only when the raw op produces NaN/Inf or unacceptable relative error in tests.
  - Keep the nominal fast path branch-free (or mask-based) and fully vectorized.
  - Avoid speculative guards and extra branches unless backed by (a) a reproduced gradient failure or (b) a measured numerical/perf improvement.

- Branching Budget (Hot Helpers)
  - Per-element branching inside hot helpers (e.g., `sincg`, `sinc3`, polarization) must be justified with numbers (gradcheck evidence or microbenchmark delta).

- Mask vs Guard
  - Masks gate analytic limits; a single epsilon guard may backstop tiny denominators. If the mask tolerance renders guards redundant, prefer the mask alone.

- Precision Guidance
  - Default dev dtype: float64; default prod dtype: float32. Tolerances must state dtype assumptions and be tested in both where relevant.

- Acceptance Criteria for Helper Changes
  - Show a before/after gradcheck result (float64 required, float32 if relevant).
  - Include a microbenchmark (≥1e6 evaluations) comparing old/new helper.
  - Confirm vectorization preserved (no data-dependent Python control flow).

### 1.2.1 Stochastic Operations in Differentiable Paths

Stochastic tensor operations (e.g., mosaic rotation sampling) require special
handling for gradient correctness:

**Problem**: `torch.autograd.gradcheck` evaluates the function multiple times
with perturbed inputs. If the function uses unseeded randomness, each evaluation
sees different random values, making numerical gradient estimation meaningless.

**Solution**: Deterministic seeding + reparameterization

1. **Freeze the randomness**: Create a `torch.Generator` seeded from config
   (e.g., `config.mosaic_seed`). Pass this generator to all stochastic ops.

2. **Reparameterize for gradients**: Factor stochastic values as:
   ```python
   actual_value = frozen_base_noise * differentiable_scale
   ```
   where `frozen_base_noise` is sampled with the seeded generator (no gradient),
   and `differentiable_scale` is the parameter that should receive gradients.

3. **Test both properties**:
   - **Gradient correctness**: `gradcheck` passes with non-zero stochastic params
   - **Seed reproducibility**: Same seed produces identical results

**Example**: Mosaic rotation generation (MOSAIC-GRADIENT-001)
```python
gen = torch.Generator(device=device)
gen.manual_seed(config.mosaic_seed & 0x7FFFFFFF)  # Handle negative seeds

base_angles = torch.randn(n_domains, generator=gen)  # frozen
actual_angles = base_angles * mosaic_spread_rad       # gradient flows here
```

**Evidence**: `tests/test_gradients.py::TestMosaicGradients`

## 1.3 Stage-A Parameterized Experiment Model (High-Level API)

Stage-A optimization introduces learnable geometry and beam parameterization on
top of the existing config-driven models.  The core physics and vectorization
remain in `Crystal`, `Detector`, and `Simulator`; Stage-A wraps them in a thin
composition layer:

- **Implementation:** `src/nanobrag_torch/models/experiment.py`
- **Spec:** `docs/architecture/parameterized_experiment.md`

### 1.3.1 Components

- `CrystalStageAParams`
  - Owns raw crystal Stage-A DOFs (log-length deltas, bounded angle/misset
    deltas).
  - Builds a derived `CrystalConfig` with tensor-valued `cell_*` and
    `misset_deg`, consumed by `Crystal` via the existing `compute_cell_tensors`
    pipeline (including misset and reciprocal/real duality rules).

- `DetectorStageAParams`
  - Owns raw detector Stage-A DOFs (log-distance delta, small-angle tilts,
    beam-center shifts in pixel units).
  - Builds a derived `DetectorConfig` that feeds the existing detector geometry
    and pivot logic.

- `BeamStageAParams`
  - Owns a log-fluence delta around the base `BeamConfig.fluence`.
  - Builds a derived `BeamConfig` with tensor-valued `fluence`, used by
    `Simulator` in the final scaling.

- `ExperimentModel`
  - High-level `nn.Module` that composes the above parameter blocks with
    `Crystal`, `Detector`, and `Simulator`.
  - Constructor:

    ```python
    ExperimentModel(
        crystal_config: CrystalConfig,
        detector_config: DetectorConfig,
        beam_config: BeamConfig,
        device=None,
        dtype=torch.float32,
        param_init: str = "frozen"  # or "stage_a"
    )
    ```

  - `forward()`:
    - Builds derived configs via the parameter blocks.
    - Instantiates `Crystal`, `Detector`, and `Simulator` on the requested
      device/dtype.
    - Returns the float image from `Simulator.run()`.

### 1.3.2 Param Initialization Modes

- `param_init="frozen"`
  - All raw fields registered as buffers (no `nn.Parameter` objects).
  - `experiment.parameters()` is empty.
  - Output is numerically equivalent to the legacy config-driven path (within
    acceptance tolerances) for given configs.

- `param_init="stage_a"`
  - Stage-A DOFs registered as `nn.Parameter` objects.
  - `experiment.parameters()` exposes exactly the Stage-A parameter tensors,
    suitable for optimizers (Adam/LBFGS).

### 1.3.3 Optimizer Usage (Summary)

For Stage-A refinement, the standard pattern is:

```python
experiment = ExperimentModel(
    crystal_config=crystal_cfg,
    detector_config=detector_cfg,
    beam_config=beam_cfg,
    param_init="stage_a",
    device="cuda",
    dtype=torch.float32,
)

optimizer = torch.optim.Adam(experiment.parameters(), lr=1e-2)
for _ in range(num_steps):
    optimizer.zero_grad()
    pred = experiment()
    loss = ((pred - target_image) ** 2).mean()
    loss.backward()
    optimizer.step()
```

All vectorization, device/dtype neutrality, and differentiability guarantees
from earlier sections apply unchanged; the ExperimentModel is a thin wrapper
that only materializes new configs from the raw parameters.
