# nanobrag_torch Gradient Correctness Issues — DBEX Integration Report

Prepared by: DBEX maintainers (Galph/Ralph agent loop)  
Date: 2025‑12‑08  
Context: DBEX + `nanobrag_torch` integration, DB‑AT‑010 “Gradient Correctness Guard”

This report documents two gradient‑flow problems in `nanobrag_torch` that block the DBEX gradient acceptance test DB‑AT‑010. All findings below are grounded in the in‑repo tests and architecture; Environment Freeze policy prevents us from patching or rebuilding `nanobrag_torch` locally, so we are handing these over for upstream investigation.

We avoid referring to runtime logs here; everything is anchored in the checked‑in tests and docs.

---

## 1. Test Harness and Call Path

- Acceptance test: `tests/dbex/test_gradients.py:1` (`TestDB_AT_010_Gradcheck`)
- Purpose: enforce gradient correctness using `torch.autograd.gradcheck` with tight tolerances.
- Coverage (per header docstring at `tests/dbex/test_gradients.py:1`):
  - Crystal parameters: `cell_a`, `cell_gamma`
  - Detector parameter: `distance_mm`
  - Beam parameter: `wavelength_A`
  - Model parameter: `spot_scale` (via SCALE‑002; not directly implicated in the external blockers)
- Runtime guards:
  - `NANOBRAGG_DISABLE_COMPILE=1` and `KMP_DUPLICATE_LIB_OK=TRUE` are set before importing torch (`tests/dbex/test_gradients.py:27`).
  - Tests run on CPU with `dtype=torch.float64` and `eps=1e-6, atol=1e-5, rtol=0.05`.
- Ingestion and inputs:
  - Uses canonical `refGeom` assets (`refGeom.expt`, `refGeom.refl`, `scaled.mtz`, `747_mask.pkl`) via `DataLoad` (`tests/dbex/test_gradients.py:47`–`83`).
  - `prepare_refinement_inputs` (`dbex.refinement.inputs.prepare_refinement_inputs`) constructs the masked loss target and sigma tensors (fixture `refinement_inputs`).
- Forward + loss:
  - Forward: `dbex.physics.forward.simulate_forward_torch` (owner for nanobrag_torch invocation).
  - Loss: `dbex.physics.loss.compute_masked_mse_loss` (variance‑weighted χ², Spec‑DB compliant).

### Gradcheck selectors

Each parameter‑specific test wraps `simulate_forward_torch` in a local `loss_fn` and passes a single differentiable scalar tensor into overrides:

- Crystal cell parameters:
  - `test_db_at_010_gradcheck_crystal_cell_a` (`tests/dbex/test_gradients.py:72`–`140`)
  - `test_db_at_010_gradcheck_crystal_cell_gamma` (`tests/dbex/test_gradients.py:141`–`219`)
  - Both use `crystal_overrides={'cell_a': cell_a_tensor}` / `{'cell_gamma': cell_gamma_tensor}`.
- Detector distance:
  - `test_db_at_010_gradcheck_detector_distance` (`tests/dbex/test_gradients.py:220`–`314`)
  - Uses `detector_overrides={'distance_mm': distance_tensor}`.
- Beam wavelength:
  - `test_db_at_010_gradcheck_beam_wavelength` (`tests/dbex/test_gradients.py:315`–`409`)
  - Uses `beam_overrides={'wavelength_A': wavelength_tensor}`.

All four feed through the same call:

```python
from dbex.physics.forward import simulate_forward_torch

bragg_torch = simulate_forward_torch(
    inputs=refinement_inputs,
    detector=geometry_objects["detector"],
    beam=geometry_objects["beam"],
    crystal=base_crystal,
    experiment=experiment,
    hkl_indices=hkl_data["indices"],
    hkl_amplitudes=hkl_data["amplitudes"],
    spot_scale_override=1.0,
    device=device,
    dtype=dtype,
    crystal_overrides=...,
    detector_overrides=...,
    beam_overrides=...,
)
```

The wrapper test `test_db_at_010_gradcheck` (`tests/dbex/test_gradients.py:410`–`640`) simply runs all four parameter tests and aggregates metrics.

---

## 2. DBEX Side: Override Wiring into nanobrag_torch

All DBEX‑side override plumbing has been audited and refactored to avoid `.item()` or other scalar extractions inside the gradient path.

### 2.1 Crystal overrides (working correctly)

`simulate_forward_torch` signature includes `crystal_overrides` and applies them after config creation (comments and behavior at `dbex/physics/forward.py` after commit `ee27cb3f`):

```python
def simulate_forward_torch(...,
                           crystal_overrides=None,
                           detector_overrides=None,
                           beam_overrides=None,
                           ...):
    """
    ...
    crystal_overrides: Optional dict of tensor-valued crystal parameter overrides
                       for gradcheck. Supports keys: 'cell_a', 'cell_b', 'cell_c',
                       'cell_alpha', 'cell_beta', 'cell_gamma'. Applied AFTER config
                       creation to preserve gradient graph (GRADIENT-001). Tensors
                       must have requires_grad=True.
    detector_overrides: ...
    beam_overrides: ...
    """
```

Internally, `crystal_overrides` is applied directly to the crystal config object returned by the factory (no scalar extraction). Crystal gradchecks were previously passing and are not the current focus of this report; they serve as a control that the overall DBEX→nanobrag_torch chain can support correct gradients.

### 2.2 Detector distance overrides (post‑creation, tensor‑safe)

Before the gradient‑flow initiative, detector distance overrides were threaded as a parameter into `create_detector_config`. That pattern was removed and replaced with a post‑creation assignment in `ee27cb3f`:

```python
beam_config = create_beam_config(beam)
...
for panel_id in range(n_panels):
    panel = detector[panel_id]
    detector_config = create_detector_config(
        panel=panel,
        beam=beam,
        trusted_mask=inputs.trusted_mask[panel_id],
    )

    # Apply detector overrides (post-creation pattern matching crystal_overrides)
    if detector_overrides is not None and 'distance_mm' in detector_overrides:
        detector_config.distance_mm = detector_overrides['distance_mm']
```

Key points:

- `create_detector_config` no longer accepts `distance_mm_override` and always reads distance from the dxtbx `panel`:

```python
def create_detector_config(panel, beam, trusted_mask=None, roi_bbox=None, oversample=-1) -> DetectorConfig:
    ...
    distance_mm = panel.get_directed_distance()
    ...
    return DetectorConfig(..., distance_mm=distance_mm, ...)
```

- The tensor override from `test_db_at_010_gradcheck_detector_distance` is assigned **directly** to the `DetectorConfig.distance_mm` field after construction, preserving the autograd graph (no `.item()`/`.detach()`).

This mirrors the crystal override pattern and removes the earlier potential gradient break in DBEX itself.

### 2.3 Beam wavelength overrides (post‑creation, tensor‑safe)

Similarly, beam overrides were moved from a `wavelength_override` argument into a post‑creation assignment:

```python
beam_config = create_beam_config(beam)

if beam_overrides is not None and 'wavelength_A' in beam_overrides:
    beam_config.wavelength_A = beam_overrides['wavelength_A']
```

`create_beam_config` now always calls `beam.get_wavelength()` and returns a `BeamConfig` with that scalar; DBEX then overwrites `wavelength_A` with the differentiable tensor passed from the test.

As with detector distance, DBEX no longer extracts scalars from the torch parameter; it simply hands a tensor into the nanobrag_torch‑ facing config.

---

## 3. External Issues in nanobrag_torch

With the DBEX‑side override plumbing corrected, two gradient problems remain that appear to originate inside `nanobrag_torch` itself, not in DBEX.

These are summarized in `docs/fix_plan.md:22` under the Tier‑0 initiative `[ARCH-GRADIENT-FLOW-001] Gradient Flow Restoration (DB-AT-010 Unblock)` and were the basis for halting further local edits.

### 3.1 Beam wavelength gradients: tensor detachment

Symptom:

- The DB‑AT‑010 beam‑wavelength gradcheck (`test_db_at_010_gradcheck_beam_wavelength` in `tests/dbex/test_gradients.py:315`–`409`) fails with a **disconnected autograd graph** despite:
  - Passing a `torch.float64` scalar tensor with `requires_grad=True` as `beam_overrides['wavelength_A']`.
  - Avoiding `.item()` or other scalar conversions in DBEX.
  - Running with `NANOBRAGG_DISABLE_COMPILE=1` (no TorchDynamo interference).

DBEX investigation traced this to `nanobrag_torch.simulator.py` (line number from `docs/fix_plan.md`, not logs), where a call of the form:

```python
torch.tensor(some_scalar, ...)
```

is used for wavelength. If `some_scalar` is itself a tensor, this pattern detaches it from the gradient graph. In other words, even if DBEX passes a differentiable `wavelength_A` into the BeamConfig, the simulator recreates it as a new tensor instead of reusing the original, breaking gradient flow at the entry boundary.

Request:

- Replace `torch.tensor(...)` with a form that **preserves** the incoming tensor’s graph, e.g.:
  - If the input is already a tensor, use it directly (or `tensor.to(device=device, dtype=dtype)`).
  - Only call `torch.tensor` on Python scalars or numpy values, not on torch tensors.
- If you prefer a uniform code path, a guarded helper like:

```python
def as_tensor_preserving_grad(x, device, dtype):
    if isinstance(x, torch.Tensor):
        return x.to(device=device, dtype=dtype)
    return torch.tensor(x, device=device, dtype=dtype)
```

applied at the simulator boundary would solve this class of issues.

Once this is fixed, we expect `test_db_at_010_gradcheck_beam_wavelength` to pass without any further DBEX changes.

### 3.2 Detector distance Jacobian: magnitude mismatch (~2.4e12 vs 1.1e8)

Symptom:

- The DB‑AT‑010 detector‑distance gradcheck (`test_db_at_010_gradcheck_detector_distance` in `tests/dbex/test_gradients.py:220`–`314`) fails with a **large Jacobian mismatch**:
  - Numerical Jacobian: ~2.39e12
  - Analytical gradient: ~1.11e8
  - Ratio: ~21,556×
- This mismatch persists across both override strategies tried in DBEX:
  - Pre‑creation overrides (now removed).
  - Post‑creation assignment to `DetectorConfig.distance_mm` (current code in `dbex/physics/forward.py`).

The fact that the **ratio and absolute magnitudes are essentially unchanged** after the DBEX refactor strongly suggests that:

- The gradient error is not coming from how DBEX passes the distance tensor into the simulator; and
- The problem lies in how nanobrag_torch interprets or propagates `DetectorConfig.distance_mm` (e.g., sign conventions, units, or missing scaling factors in the derivative chain).

DBEX’s own `create_detector_config` computes `distance_mm` from `panel.get_directed_distance()` and adjusts coordinates consistent with `docs/config_crosswalk.md` and `docs/architecture.md`. The override then simply replaces that scalar with a tensor of the same base value, so there is no additional scaling on the DBEX side.

Request:

- Audit the nanobrag_torch code that:
  - Consumes `DetectorConfig.distance_mm` to build the geometry used for forward simulation.
  - Computes gradients w.r.t. that field (e.g., via autodiff on origin/normal, or explicit derivatives).
- In particular, please:
  - Check for mismatched units (mm vs m), missing `1e3` or similar factors.
  - Verify any sign conventions (e.g., panel origin along −z vs +z) are handled consistently in both the forward map and the gradient.
  - Ensure there is no hidden `torch.tensor(...)` detachment as with wavelength.

We do not have a minimal reproduction entirely within nanobrag_torch because DBEX orchestrates the data, but the tests above should be a good starting harness once you wire them up in your own environment.

---

## 4. How to Reproduce from This Repo

Assuming you have the same external environment and canonical assets present (`refGeom.expt`, `refGeom.refl`, `scaled.mtz`, `747_mask.pkl` in the repo root), the DBEX team’s harness uses the following patterns:

1. Run the full DB‑AT‑010 gradient suite:

```bash
NANOBRAGG_DISABLE_COMPILE=1 \
KMP_DUPLICATE_LIB_OK=TRUE \
pytest -v tests/dbex/test_gradients.py::TestDB_AT_010_Gradcheck::test_db_at_010_gradcheck
```

2. To focus only on the detector distance parameter:

```bash
NANOBRAGG_DISABLE_COMPILE=1 \
KMP_DUPLICATE_LIB_OK=TRUE \
pytest -v tests/dbex/test_gradients.py::TestDB_AT_010_Gradcheck::test_db_at_010_gradcheck_detector_distance
```

3. To focus only on the beam wavelength parameter:

```bash
NANOBRAGG_DISABLE_COMPILE=1 \
KMP_DUPLICATE_LIB_OK=TRUE \
pytest -v tests/dbex/test_gradients.py::TestDB_AT_010_Gradcheck::test_db_at_010_gradcheck_beam_wavelength
```

Each test writes JSON metric artifacts under `plans/active/DB-AT-010/reports/...` (see the `artifact_dir` fixture in `tests/dbex/test_gradients.py:37`–`59`), but those artifacts are not required to see the failures; gradcheck will raise directly.

---

## 5. Summary of Requests to nanobrag_torch Maintainers

1. **Beam wavelength gradient detachment**
   - Replace `torch.tensor(...)` on tensor inputs (wavelength) with a grad‑preserving path.
   - Verify that a differentiable `wavelength_A` tensor propagated via your configs reaches the simulator unaltered (no `.item()`, `.detach()`, or implicit tensor recreation).

2. **Detector distance gradient magnitude**
   - Investigate and fix the ~2.4e12 vs 1.1e8 Jacobian mismatch for `DetectorConfig.distance_mm` as exercised by DBEX’s gradcheck harness.
   - Confirm that the analytical and numerical gradients agree within typical gradcheck tolerances for a small distance perturbation at the canonical `refGeom` configuration.

3. **Optional**: once fixes are available or patches are proposed, we are happy to:
   - Re‑run DB‑AT‑010 against your changes using the existing DBEX tests; and
   - Update our architecture docs and fix‑plan ledger to mark ARCH‑GRADIENT‑FLOW‑001 as unblocked.

Thank you for looking into this — it is currently the only Tier‑0 external dependency blocking the DBEX gradient‑safety conformance profile.

