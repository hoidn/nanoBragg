# Parameterized Experiment Model (Stage‑A)

This document specifies the learnable geometry and beam parameterization
introduced by plan `STAGEA-PARAM-001`.  The goal is to expose an
optimizer‑friendly API for Stage‑A refinement while preserving the existing
config‑driven interfaces and C‑parity guarantees when parameterization is
disabled.

The implementation described here corresponds to:

- `src/nanobrag_torch/models/experiment.py`
- `src/nanobrag_torch/models/crystal.py`
- `src/nanobrag_torch/models/detector.py`
- `src/nanobrag_torch/config.py`

## 1. Objectives

- Provide differentiable tensors for the primary Stage‑A degrees of freedom:
  crystal cell + orientation, coarse detector geometry, and beam fluence.
- Keep the existing `Crystal`, `Detector`, `BeamConfig`, and `Simulator` APIs
  unchanged for all legacy call sites.
- Ensure that when parameters are initialized in a “frozen” mode, the
  parameterized path reproduces the legacy config‑driven path within the
  numerical tolerances used by the acceptance tests.

All mappings in this document respect:

- Core units and geometry rules in `specs/spec-a-core.md`.
- Vectorization and device/dtype neutrality in
  `docs/architecture/pytorch_design.md`.
- Detector conventions and pivot rules in `docs/architecture/detector.md`.

## 2. Raw Parameterization

The Stage‑A parameterization is implemented as thin `nn.Module` wrappers that
own raw parameters and map them back to `CrystalConfig`, `DetectorConfig`, and
`BeamConfig` instances.  The physics remains in the existing models and
simulator.

### 2.1 Crystal (Stage‑A)

Class: `CrystalStageAParams` in
`src/nanobrag_torch/models/experiment.py`.

Inputs:

- `base_config: CrystalConfig`
- `device`, `dtype`
- Mode selector `param_init="frozen" | "stage_a"`

Raw parameters (`param_init="stage_a"`):

- Log‑length deltas (unconstrained):
  - `δ_log_a`, `δ_log_b`, `δ_log_c` (shape `()`)
- Bounded angle deltas (degrees):
  - `Δα_raw`, `Δβ_raw`, `Δγ_raw` (shape `()`)
  - `Δmisset_raw = (Δmx_raw, Δmy_raw, Δmz_raw)` (shape `(3,)`)

Base values (buffers):

- `a0`, `b0`, `c0` from `base_config.cell_*` (Å)
- `α0`, `β0`, `γ0` from `base_config.cell_*` (deg)
- `m0 = (m0x, m0y, m0z)` from `base_config.misset_deg` (deg)

Mappings:

- Cell lengths (always positive, log‑parameterized):

  ```python
  a = a0 * torch.exp(δ_log_a)
  b = b0 * torch.exp(δ_log_b)
  c = c0 * torch.exp(δ_log_c)
  ```

- Cell angles (bounded deltas, Stage‑A search window):

  ```python
  max_angle_delta = 10.0  # degrees
  α = α0 + max_angle_delta * torch.tanh(Δα_raw)
  β = β0 + max_angle_delta * torch.tanh(Δβ_raw)
  γ = γ0 + max_angle_delta * torch.tanh(Δγ_raw)
  ```

- Static misset angles (bounded deltas, applied as XYZ Euler rotations within
  the existing misset pipeline in `Crystal.compute_cell_tensors`):

  ```python
  max_misset_delta = 10.0  # degrees
  Δmisset = max_misset_delta * torch.tanh(Δmisset_raw)
  misset_deg = m0 + Δmisset
  ```

The Stage‑A crystal wrapper constructs a derived `CrystalConfig` by copying the
base config and overwriting:

- `cell_a`, `cell_b`, `cell_c`
- `cell_alpha`, `cell_beta`, `cell_gamma`
- `misset_deg`

These fields are stored as tensors on the requested `device`/`dtype` and are
consumed by `Crystal` via the existing `torch.as_tensor` logic, preserving the
misset pipeline and reciprocal/real‑space duality rules.

### 2.2 Detector (Stage‑A)

Class: `DetectorStageAParams` in
`src/nanobrag_torch/models/experiment.py`.

Inputs:

- `base_config: DetectorConfig`
- `device`, `dtype`
- Mode selector `param_init="frozen" | "stage_a"`

Raw parameters (`param_init="stage_a"`):

- Log‑distance delta:
  - `δ_log_distance_mm` (shape `()`)
- Bounded small‑angle tilts:
  - `Δrotx_raw`, `Δroty_raw`, `Δrotz_raw`, `Δtwotheta_raw` (shape `()`)
- Optional beam‑center pixel deltas (Stage‑A coarse centering):
  - `Δbeam_s_raw`, `Δbeam_f_raw` (shape `()`)

Base values (buffers):

- `d0_mm = base_config.distance_mm`
- `r0 = (rotx0, roty0, rotz0, twotheta0)` from the base config (deg)
- `beam0_s_mm`, `beam0_f_mm` from the base config after
  `DetectorConfig.__post_init__` (deg and mm).

Mappings:

- Distance (mm, positive):

  ```python
  distance_mm = d0_mm * torch.exp(δ_log_distance_mm)
  ```

- Tilt angles (degrees, bounded deltas):

  ```python
  max_tilt_delta = 5.0  # degrees
  rotx = rotx0 + max_tilt_delta * torch.tanh(Δrotx_raw)
  roty = roty0 + max_tilt_delta * torch.tanh(Δroty_raw)
  rotz = rotz0 + max_tilt_delta * torch.tanh(Δrotz_raw)
  twotheta = twotheta0 + max_tilt_delta * torch.tanh(Δtwotheta_raw)
  ```

- Beam‑center mm offsets (expressed in the same mm space as the config, so the
  detector’s MOSFLM/XDS beam‑center mapping still applies):

  ```python
  max_beam_shift_mm = base_config.pixel_size_mm * 5.0
  beam_center_s = beam0_s_mm + max_beam_shift_mm * torch.tanh(Δbeam_s_raw)
  beam_center_f = beam0_f_mm + max_beam_shift_mm * torch.tanh(Δbeam_f_raw)
  ```

The derived `DetectorConfig` copies the base config and overwrites:

- `distance_mm`
- `detector_rotx_deg`, `detector_roty_deg`, `detector_rotz_deg`,
  `detector_twotheta_deg`
- `beam_center_s`, `beam_center_f`

Pivot mode, detector convention, and all other fields are inherited from the
base config, so the existing detector geometry pipeline
(`Detector.__init__`, `_apply_mosflm_beam_convention`, `get_pixel_coords`,
etc.) remains authoritative.

### 2.3 Beam (Stage‑A)

Class: `BeamStageAParams` in
`src/nanobrag_torch/models/experiment.py`.

Inputs:

- `base_config: BeamConfig`
- `device`, `dtype`
- Mode selector `param_init="frozen" | "stage_a"`

Raw parameters (`param_init="stage_a"`):

- Log‑fluence delta:
  - `δ_log_fluence` (shape `()`)

Base value (buffer):

- `ϕ0 = base_config.fluence` (photons/m²)

Mapping:

```python
fluence = ϕ0 * torch.exp(δ_log_fluence)
```

All other beam fields (wavelength, multi‑source directions, polarization) are
currently inherited directly from `BeamConfig`.  Additional Stage‑A DOFs for
simple spectral or direction parameters may be added in a later phase using the
same pattern.

## 3. Experiment Composition API

Class: `ExperimentModel` in
`src/nanobrag_torch/models/experiment.py`.

### 3.1 Construction

Canonical constructor:

```python
from nanobrag_torch.models.experiment import ExperimentModel
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig

experiment = ExperimentModel(
    crystal_config=CrystalConfig(...),
    detector_config=DetectorConfig(...),
    beam_config=BeamConfig(...),
    param_init="frozen",  # or "stage_a"
    device="cpu",
    dtype=torch.float32,
)
```

- When `param_init="frozen"`:
  - All raw fields are registered as buffers (no `nn.Parameter` objects).
  - `experiment.parameters()` is empty; existing config‑driven workflows are
    unchanged when the experiment wrapper is not used.
- When `param_init="stage_a"`:
  - Crystal, detector, and beam Stage‑A DOFs are registered as
    `nn.Parameter`s.
  - `experiment.parameters()` returns exactly the Stage‑A parameter tensors,
    suitable for optimizers such as Adam or LBFGS.

### 3.2 Forward Path

`ExperimentModel` composes the existing core components without re‑implementing
physics:

1. Build derived configs from raw parameters:

   ```python
   crystal_cfg = crystal_params.build_config()
   detector_cfg = detector_params.build_config()
   beam_cfg = beam_params.build_config()
   ```

2. Instantiate the legacy models:

   ```python
   crystal = Crystal(crystal_cfg, beam_config=beam_cfg, device=device, dtype=dtype)
   detector = Detector(detector_cfg, device=device, dtype=dtype)
   simulator = Simulator(crystal, detector, beam_config=beam_cfg, device=device, dtype=dtype)
   ```

3. Run the simulation:

   ```python
   float_image = simulator.run(**sim_kwargs)
   ```

The `forward()` method returns the float image tensor with shape
`(spixels, fpixels)` and preserves the canonical broadcast shapes and sampling
rules from `pytorch_design.md`.

### 3.4 External Structure Factors (Dense HKL Grids)

Downstream projects that already construct a dense HKL grid (for example via
cctbx/MTZ) can provide it directly to `ExperimentModel` instead of letting the
internal `Crystal` instance load HKL files:

- Constructor hook:

  ```python
  experiment = ExperimentModel(
      crystal_config=crystal_cfg,
      detector_config=detector_cfg,
      beam_config=beam_cfg,
      device=device,
      dtype=torch.float32,
      param_init="stage_a",
      hkl_data=F_grid,        # torch.Tensor
      hkl_metadata=metadata,  # dict: h_min/h_max/k_min/k_max/l_min/l_max
  )
  ```

- Or setter hook before the first forward:

  ```python
  experiment = ExperimentModel(
      crystal_config=crystal_cfg,
      detector_config=detector_cfg,
      beam_config=beam_cfg,
      device=device,
      dtype=torch.float32,
      param_init="stage_a",
  )

  experiment.set_structure_factors(F_grid, metadata)
  image = experiment()
  ```

Behavior:

- The HKL tensor is moved to the experiment’s `device`/`dtype` before being
  attached to the internal `Crystal` instance.
- The `hkl_metadata` dictionary is passed through to `Crystal.hkl_metadata`
  unchanged; callers are responsible for providing compatible bounds
  (`h_min`, `h_max`, etc.).
- Interpolation behavior (`Crystal.interpolate`) and default_F handling are
  unchanged; the external grid is treated identically to data loaded via
  `Crystal.load_hkl()`.

This public hook avoids reaching into `Crystal.hkl_data`/`hkl_metadata`
directly and provides a stable surface for projects like dbex that already have
their own structure‑factor loading pipeline.

### 3.3 Optimizer Usage

A minimal Stage‑A optimization loop:

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
    pred = experiment()          # float image
    loss = torch.mean((pred - target_image) ** 2)
    loss.backward()
    optimizer.step()
```

This composition keeps all detector geometry, misset rotation, and sampling
rules in the existing `Crystal`, `Detector`, and `Simulator` implementations,
avoiding duplicate physics while exposing the key Stage‑A degrees of freedom as
standard PyTorch parameters.
