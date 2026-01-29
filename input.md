Plan: docs/plans/2026-01-29-m3-joint-global-local.md
References:
- docs/strategy/mainstrategy.md §7 — defines M3 acceptance criteria and expected CLI workflows
- docs/specs/duck_multi_image_dataset.md — dataset schema that must be extended with structure-factor payloads
- specs/spec-a-core.md §Structure Factors & Fdump — normative unit/shape rules for HKL tensors injected into Crystal
- docs/development/testing_strategy.md §6 — authoritative Duck demo testing workflow + CLI guidance
- docs/fix_plan.md — current initiative states + dependencies
Summary: Extend the Duck dataset + tooling so joint global/local refinement is possible: emit a reproducible structure-factor tensor in the generator/spec, add a differentiable `StructureFactorLatent` that can override Crystal HKL data per specs/spec-a-core.md §Structure Factors & Fdump, teach `MultiImageTrainer` a `joint_mode` that optimizes that latent plus per-image sigma/scale parameters, and expose the path via `scripts/demo_recover_duck.py --mode joint` with updated docs + evidence under STRAT-M3-001.
Summary (Goal): Deliver a joint-mode Duck benchmark where shared structure factors and per-image mosaics co-train with passing pytest + refreshed CLI docs.
Focus: STRAT-M3-001 — Duck joint global-local refinement
Branch: feature/spec-based-2
Mapped tests:
- pytest tests/test_duck_dataset.py::test_duck_dataset_includes_structure_factors -v
- pytest tests/test_vi_mosaic.py::TestStructureFactorLatent::test_latent_applies_tensor_and_tracks_grads -v
- pytest tests/test_vi_mosaic.py::test_multi_image_trainer_joint_mode_wires_latents -v
- pytest tests/test_vi_mosaic.py::test_demo_recover_duck_cli_joint -v
Artifacts: plans/active/strat-m3-001/reports/2026-01-29T142358Z/
Next Up:
1. Once joint CLI artifacts exist, rerun the 150-iteration benchmark with 20-image Duck dataset and archive screenshots/logs.
2. Add GPU smoke coverage for joint mode to ensure StructureFactorLatent stays device-neutral.
