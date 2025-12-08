# nanoBragg PyTorch API Overview

This document is a navigation hub for the public `nanobrag_torch` API, tying
the core architecture and Stage‑A parameterization together for downstream
projects (e.g. dbex).

It does **not** duplicate the detailed specs; instead it points to the canonical
documents and modules that define the supported surface.

---

## 1. Core Modules & Entry Points

- Package: `nanobrag_torch`
  - `nanobrag_torch.__main__` → CLI entry point (`nanoBragg` command)
  - `nanobrag_torch.simulator.Simulator` → core simulation engine
  - `nanobrag_torch.models.Crystal` → crystal geometry + structure factors
  - `nanobrag_torch.models.Detector` → detector geometry
  - `nanobrag_torch.config` → `CrystalConfig`, `DetectorConfig`, `BeamConfig`

**Docs:**

- High‑level user guide: `README_PYTORCH.md`
- Architecture design (vectorization, shapes, devices):  
  `docs/architecture/pytorch_design.md`
- Detector spec and conventions:  
  `docs/architecture/detector.md`
- C parameter mapping:  
  `docs/architecture/c_parameter_dictionary.md`

---

## 2. Stage‑A Parameterization & ExperimentModel

**Implementation:** `src/nanobrag_torch/models/experiment.py`  
**Spec:** `docs/architecture/parameterized_experiment.md`

Key classes:

- `ExperimentModel`
  - High‑level `nn.Module` that owns Stage‑A parameters and delegates physics
    to `Simulator`.
  - Constructor:

    ```python
    from nanobrag_torch.models import ExperimentModel

    experiment = ExperimentModel(
        crystal_config=crystal_cfg,
        detector_config=detector_cfg,
        beam_config=beam_cfg,
        device="cuda",
        dtype=torch.float32,
        param_init="frozen",  # or "stage_a"
        hkl_data=None,
        hkl_metadata=None,
    )
    ```

  - `param_init="frozen"` → no learnable params, parity with config‑driven path.  
    `param_init="stage_a"` → Stage‑A DOFs exposed as `nn.Parameter`s.
  - `forward()` runs the simulation and returns a float image tensor
    `(spixels, fpixels)`.

- Stage‑A parameter blocks (internal to `ExperimentModel`):
  - `CrystalStageAParams`:
    - Log‑length deltas, bounded angle deltas, misset deltas.
    - Produces a `CrystalConfig` used by `Crystal`.
  - `DetectorStageAParams`:
    - Log‑distance delta, small‑angle tilts, beam‑center pixel shifts.
    - Produces a `DetectorConfig` used by `Detector`.
  - `BeamStageAParams`:
    - Log‑fluence delta.
    - Produces a `BeamConfig` used by `Simulator`.

**External HKL grid support:**

- Constructor hook:

  ```python
  experiment = ExperimentModel(
      crystal_config=crystal_cfg,
      detector_config=detector_cfg,
      beam_config=beam_cfg,
      device=device,
      dtype=torch.float32,
      param_init="stage_a",
      hkl_data=F_grid,
      hkl_metadata=metadata,
  )
  ```

- Setter hook:

  ```python
  experiment.set_structure_factors(F_grid, metadata)
  ```

where `F_grid` is a dense HKL tensor and `metadata` provides
`h_min/h_max/k_min/k_max/l_min/l_max`. The grid is moved to the experiment’s
device/dtype and attached to the internal `Crystal` instance; interpolation and
default_F behavior follow `Crystal.get_structure_factor`.

For full details, see `docs/architecture/parameterized_experiment.md`.

---

## 3. Multi‑Panel Usage Guidance

`nanobrag_torch` models a single detector panel per `DetectorConfig` /
`Detector` / `Simulator` / `ExperimentModel` instance.

**Canonical pattern for multi‑panel detectors (e.g. DIALS/dxtbx):**

- Build one `DetectorConfig` per panel.
- Instantiate one `ExperimentModel` per panel (or one `Simulator` per panel for
  non‑Stage‑A uses).
- Run each and stitch the results into a `[panel, slow, fast]` tensor on the
  caller side.

This is the supported pattern for downstream projects; a future
`MultiPanelExperimentModel` may encapsulate this, but the current API assumes
per‑panel models.

---

## 4. Testing & Stability

Relevant tests that exercise this API:

- Stage‑A nucleus:
  - `tests/test_at_stagea_param_001.py`
- CUDA graphs / torch.compile:
  - `tests/test_perf_pytorch_005_cudagraphs.py`
- General simulator/physics tests:
  - `tests/test_suite.py` and the `test_at_*` family

Downstream integrations should treat:

- `ExperimentModel` constructor, `forward()`, and
  `set_structure_factors(...)` as stable public API.
- The Stage‑A parameter blocks and `_build_simulator()` helper as internal
  (no stability guarantees).

