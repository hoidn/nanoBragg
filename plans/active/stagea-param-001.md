## Implementation Plan — Generalized Learnable Parameterization

## Initiative
- ID: STAGEA-PARAM-001
- Title: Generalized Learnable Geometry & Beam Parameterization
- Owner: <TBD>
- Spec Owner: specs/spec-a-core.md
- Status: pending

## Goals
- Provide a first-class, optimizer-friendly parameterization for Crystal, Detector, and Beam geometry/intensity degrees of freedom used in Stage-A (and later) optimization.
- Preserve the existing config-driven API and C-parity guarantees, with old call sites seeing no behavior changes by default.

## Phases Overview
- Phase A — Design & Spec: Define parameterization, contracts, and API surfaces.
- Phase B — Crystal Path: Implement parameterized Crystal geometry and tests.
- Phase C — Detector/Beam & Composition: Extend to Detector and Beam and add a composed experiment model.

## Exit Criteria
1. A documented parameterization for Crystal, Detector, and Beam (raw tensors to physical geometry) is published and implemented.
2. Existing CLI/config workflows and nb-compare tests pass unchanged when parameterization is disabled (default mode).
3. New parameterized entry points for Stage-A expose optimizer-friendly tensors and reproduce legacy outputs to within numerical tolerance for at least the golden simple_cubic and a representative tilted/triclinic case.
4. Test registry synchronized: `docs/TESTING_GUIDE.md` §2 and `docs/development/TEST_SUITE_INDEX.md` reflect any new/changed tests; `pytest --collect-only` logs for documented selectors are saved under `plans/active/STAGEA-PARAM-001/reports/<timestamp>/`. Do not close the initiative if any selector marked "Active" collects 0 tests.

## Compliance Matrix (Mandatory)
- [ ] Spec Constraint: `specs/spec-a-core.md` — Units, crystal/reciprocal lattice, misset pipeline, and detector geometry clauses.
- [ ] Spec Constraint: `docs/architecture/pytorch_design.md` — Vectorization strategy and device/dtype neutrality.
- [ ] Spec Constraint: `docs/architecture/detector.md` — Detector geometry conventions and pivot/convention rules.
- [ ] Fix-Plan Link: `docs/fix_plan.md` — Row `[STAGEA-PARAM-001]` (this plan).
- [ ] Finding/Policy ID: PyTorch runtime guardrails (no `.item()` on grad tensors, device neutrality, no `torch.linspace` for grad-critical ranges).
- [ ] Finding/Policy ID: Detector geometry debugging checklist and C-CLI to PyTorch configuration map.

## Spec Alignment
- Normative Spec: `specs/spec-a-core.md`
- Key Clauses:
  - Crystal and reciprocal lattice definitions and misset rotation pipeline.
  - Detector coordinate systems, pivot modes, and convention-dependent beam center mapping.
  - Stage-A degrees of freedom (cell, orientation, coarse detector distance/tilt, beam fluence) as implied by existing configs and DBEX integration.
  - PyTorch differentiability and vectorization requirements from `docs/architecture/pytorch_design.md`.

## Context Priming (read before edits)
- Primary docs/specs to re-read:
  - `docs/architecture/pytorch_design.md`
  - `docs/architecture/detector.md`
  - `docs/development/c_to_pytorch_config_map.md`
  - `docs/development/testing_strategy.md`
  - `docs/user/known_limitations.md`
- Required findings/case law:
  - `docs/findings.md` entries for detector beam center offsets, PIX0 vector root cause, and triclinic misset behavior.
  - Geometry-related findings referenced in `PHASE_5_FINAL_VALIDATION_REPORT.md` and `PHASE_6_FINAL_REPORT.md`.
- Related telemetry/attempts:
  - `PARALLEL_VALIDATION_ACCEPTANCE_TESTS.md` and recent `parallel_test_summary.md`.
  - Any DBEX→nanoBragg integration notes under `initiatives/` or `reports/`.

## Phase A — Design & Spec for Learnable Parameterization

### Checklist
- [ ] A0: Nucleus / Test-first gate: add a minimal test that instantiates Crystal and Detector from config and verifies that adding noop parameter ownership (frozen parameters equal to config values) does not change Simulator output for a small ROI.
- [ ] A1: Author `docs/architecture/parameterized_experiment.md` describing:
  - Raw parameterization for Crystal (log-length deltas, bounded angle deltas, orientation vector to quaternion to rotation matrix).
  - Raw parameterization for Detector (distance/tilt deltas, beam-center deltas in an appropriate basis).
  - Raw parameterization for Beam (fluence and, if in scope, simple spectral/direction parameters).
  - Mapping from raw tensors to physical values and to existing config/geometry fields.
- [ ] A2: Decide ownership model:
  - Option 1: promote `Crystal` and `Detector` to `nn.Module` and let them own `nn.Parameter` objects for learnable degrees of freedom.
  - Option 2: introduce thin `CrystalParam` and `DetectorParam` modules that encapsulate parameters and expose `build_*_state()` helpers while keeping existing classes config-driven.
  - Document pros/cons and choose one, including implications for `torch.compile`.
- [ ] A3: Define external API surface:
  - `Crystal.from_config(..., param_init="stage_a" | "frozen")` (and detector/beam equivalents) or a top-level `ExperimentModel.from_configs(...)`.
  - Specify how callers obtain `parameters()` and how they opt into parameterization without affecting existing CLI usage.

### Dependency Analysis (Required for Refactors)
- Touched Modules:
  - `src/nanobrag_torch/models/crystal.py`
  - `src/nanobrag_torch/models/detector.py`
  - `src/nanobrag_torch/config.py`
  - `src/nanobrag_torch/simulator.py`
  - `src/nanobrag_torch/__main__.py` (CLI wiring as needed)
- Circular Import Risks:
  - Avoid introducing a new experiment module that creates a cycle between `simulator` and `models`.
  - Keep any `ExperimentModel` composition in a module that `simulator` does not import.
- State Migration:
  - Existing state: configs are passed into Crystal/Detector, which materialize tensors and caches.
  - New state: learnable raw parameters live as `nn.Parameter`s; per-step physical tensors are derived from them.
  - Plan: configs remain the source of truth for defaults and non-learnable fields; parameters encode deltas or reparameterizations relative to base values.

### Notes & Risks
- Risk: nb-compare parity regressions if the parameterized path alters geometry ordering or unit conversions.
- Risk: degraded `torch.compile` behavior if parameterization introduces shape-changing code paths across runs.
- Risk: API confusion if opting into parameterization is not clearly separated from simple config-driven usage.

## Phase B — Parameterized Crystal Path

### Checklist
- [ ] B1: Implement a parameterized Crystal path according to Phase A:
  - Either convert `Crystal` into an `nn.Module` or add a `CrystalModule` that owns raw `nn.Parameter` tensors for Stage-A degrees of freedom.
  - Derive physical cell lengths, angles, orientation, and misset pipeline from raw parameters using the existing math pipeline.
  - Expose the same effective tensors currently used by `Simulator` without changing simulator physics.
- [ ] B2: Wire Stage-A style usage:
  - Add an explicit entry point (for example, `Crystal.from_config(..., param_init="stage_a")`) that initializes parameters from `CrystalConfig` so that the initial forward model matches the config geometry.
  - Ensure `crystal.parameters()` returns exactly the intended Stage-A geometry parameters.
- [ ] B3: Tests—parity and gradients:
  - Add tests that, for a fixed `CrystalConfig`, compare legacy Crystal+Simulator output vs parameterized Crystal+Simulator for:
    - `simple_cubic` golden case.
    - At least one triclinic+misset case used in existing parity tests.
  - Add `torch.autograd.gradcheck` tests for Crystal Stage-A parameters with a small ROI and scalar loss.
- [ ] B4: Documentation:
  - Update `docs/architecture/pytorch_design.md` to describe the Crystal parameterization path and its intended Stage-A usage.

### Notes & Risks
- Crystal parameterization must preserve the misset rotation pipeline and reciprocal/real vector recalculation order; shortcuts likely break metric duality and triclinic edge cases.
- Gradcheck may require careful numerical tolerances and double precision.

## Phase C — Parameterized Detector/Beam and Experiment Composition

### Checklist
- [ ] C1: Detector parameterization:
  - Identify Stage-A-relevant detector DOFs (e.g., distance, twotheta, small rotations, beam-center deltas).
  - Implement raw parameters and mappings that respect detector conventions, pivot modes, and MOSFLM beam-center rules by reusing existing helper routines.
  - Add a `Detector.from_config(..., param_init="stage_a")` (or analogous) API that initializes parameters to match config geometry.
- [ ] C2: Beam parameterization:
  - Add raw parameters for beam fluence and, if in scope, simple divergence/spectrum parameters.
  - Integrate cleanly with existing beam config and simulator physics, preserving device/dtype neutrality and differentiability.
- [ ] C3: Experiment composition model:
  - Introduce a thin `ExperimentModel` (or equivalent) that:
    - Owns parameterized Crystal, Detector, and Beam.
    - Exposes `forward()` that calls into `Simulator` with derived geometry and beam state.
    - Exposes `parameters()` that returns a curated parameter set or groups for Stage-A optimization.
  - Keep `Simulator` unchanged as much as possible; composition should live at this higher level.
- [ ] C4: End-to-end tests and example:
  - Add an integration test that:
    - Builds an experiment from configs.
    - Runs a few optimizer steps on a toy loss (e.g., MSE against a synthetic target image).
    - Confirms gradients flow through Crystal, Detector, and Beam parameters without errors.
  - Provide a minimal Stage-A optimization example (docs or `examples/`) showing:
    - Building an experiment from configs.
    - Passing `experiment.parameters()` to Adam/LBFGS`.
    - Reusing detector/simulator across steps.
- [ ] C5: Documentation and registry updates:
  - Update `README_PYTORCH.md` and any relevant user docs to reference parameterized geometry.
  - Update `docs/development/testing_strategy.md` and test suite index with new selectors for parameterization and gradient tests.

### Notes & Risks
- Detector parameterization is fragile due to pivot and convention subtleties; rely on detector geometry checklist and C-trace comparison.
- Experiment composition must stay thin to avoid hiding unit and convention invariants and to remain compatible with `torch.compile`.

## Artifacts Index
- Reports root: `plans/active/STAGEA-PARAM-001/reports/`
- Latest run: `<YYYY-MM-DDTHHMMSSZ>/`

