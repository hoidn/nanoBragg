## Analysis Question
Why do the Sprint 1 determinism tests (AT-PARALLEL-013/024) still fail after dtype blockers were cleared? Map how RNG seeds flow from the CLI through `Crystal`/`Simulator` so we can identify where the PyTorch implementation diverges from the spec’s seeded LCG behavior.

## Candidate Entry Points
| Candidate | Relevance | Confidence | Expected Code Region |
| --- | --- | --- | --- |
| CLI parser & config builder | Seeds originate from CLI (`-seed`, `-mosaic_seed`, `-misset_seed`) per spec; must confirm storage | High | `src/nanobrag_torch/__main__.py` (arch.md:18-55) |
| Crystal configuration & rotation helpers | Crystal owns misset/mosaic RNG domains; spec mandates LCG parity | High | `src/nanobrag_torch/config.py`, `models/crystal.py` (arch.md:49-55; specs/spec-a-core.md:515-522) |
| Simulator orchestrator | Copies crystal config into runtime and drives per-pixel loops | Medium | `src/nanobrag_torch/simulator.py` (arch.md:49-56) |
| C-compatible RNG utilities | Spec calls for LCG equivalence; confirms available helpers | Medium | `src/nanobrag_torch/utils/c_random.py` (docs/architecture/c_function_reference.md:143) |

## Selected Entrypoint(s)
Primary: CLI parser → CrystalConfig (`src/nanobrag_torch/__main__.py`) and Crystal mosaic pipeline (`src/nanobrag_torch/models/crystal.py`). These stages determine whether seeds reach the RNG. Fallback: Simulator seed handoff (`src/nanobrag_torch/simulator.py`) to confirm propagation into runtime objects.

## Config Flow
- CLI defines seed flags and defaulting logic (`src/nanobrag_torch/__main__.py:280`, `604-614`, `714`).
- CrystalConfig construction copies CLI seeds (`src/nanobrag_torch/__main__.py:848-877`).
- Simulator injects `mosaic_seed` back onto the live crystal before running (`src/nanobrag_torch/simulator.py:451-469`).

## Core Pipeline Stages
- Crystal.get_rotated_real_vectors applies random misset via the C-compatible LCG helper when `misset_random` is set (`src/nanobrag_torch/models/crystal.py:720-737`).
- Crystal._generate_mosaic_rotations generates per-domain orientations using `torch.randn` without seeding (`src/nanobrag_torch/models/crystal.py:1327-1355`).
- Simulator.run consumes those rotated vectors inside `_compute_physics_for_position`, averaging over mosaic/phi/oversample loops (`src/nanobrag_torch/simulator.py:746-907`).

## Normalization / Scaling Chain
- Determinism relies on the same step counts used for averaging: Simulator computes `steps = sources * phi_steps * mosaic_domains * oversample^2` before dividing intensities (`src/nanobrag_torch/simulator.py:883-896`). The random mosaic orientations feed into this accumulation prior to normalization.

## Sinks / Outputs
- Final intensities written through CLI outputs inherit the averaged values; determinism tests read them directly (`tests/test_at_parallel_013.py`, AT spec `specs/spec-a-parallel.md:95-169`).

## Callgraph Edge List
- `parse_and_validate_args` → `CrystalConfig(...)` (seed fields) (`src/nanobrag_torch/__main__.py:844-877`).
- `CrystalConfig` → `Simulator.__init__` seed reassignment (`src/nanobrag_torch/simulator.py:451-469`).
- `Simulator._compute_physics_for_position` → `Crystal.get_rotated_real_vectors` (per-pixel lattice generation) (`src/nanobrag_torch/simulator.py:746-755` → `src/nanobrag_torch/models/crystal.py:1108-1231`).
- `Crystal.get_rotated_real_vectors` → `_generate_mosaic_rotations` (random domain orientations) (`src/nanobrag_torch/models/crystal.py:1149-1355`).
- `_generate_mosaic_rotations` (PyTorch RNG) → per-domain rotation matrices passed back to simulator (`src/nanobrag_torch/models/crystal.py:1327-1355`).

## Data / Units & Constants
- Spec mandates deterministic seeds with C LCG (`specs/spec-a-core.md:515-522`, ADR-05 `arch.md:85-87`).
- Mosaic spread handled in degrees but converted to radians before random sampling (`src/nanobrag_torch/models/crystal.py:1320-1337`).

## Device / dtype Handling
- Crystal mosaic RNG currently uses `torch.randn` on `self.device` and `self.dtype` (`src/nanobrag_torch/models/crystal.py:1327-1336`), inheriting whatever device/dtype simulator selected. No explicit generator is provided; global RNG state is used.

## Gaps / Unknowns + Confirmation Plan
- `mosaic_seed` never influences `_generate_mosaic_rotations`; randomness depends on global torch RNG, breaking deterministic expectations. Next step: design taps to capture RNG state before/after `_generate_mosaic_rotations`, and prototype replacing `torch.randn` with the spec LCG or a seeded `torch.Generator` seeded from `CrystalConfig.mosaic_seed`.
- Determinism tests still blocked by TorchDynamo CUDA probing (see reports/2026-01-test-suite-triage/phase_d/20251011T045211Z/determinism/phase_a/summary.md); plan to disable Dynamo during evidence capture to allow callchain taps once RNG fix is scoped.
