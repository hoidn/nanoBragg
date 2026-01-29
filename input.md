Plan: docs/plans/2026-01-29-m3-joint-global-local.md
References:
- docs/strategy/mainstrategy.md §7 — canonical acceptance criteria for the Duck multi-image milestones; now needs CUDA evidence noted explicitly
- docs/development/testing_strategy.md §6.3 — normative mapping of commands / validation rules for Duck joint mode, update this section with the GPU smoke workflow
- docs/fix_plan.md — STRAT-M3-001 status + exit criteria (Task 5 CUDA smoke) that must be satisfied before closure
Summary: Execute Task 5 of the joint-mode plan by running a short CUDA smoke of `scripts/demo_recover_duck.py --mode joint`, archiving artifacts + torch environment under the new report directory, mirroring PNG/JSON to `demo_outputs/duck_joint_gpu`, and updating docs/strategy and testing_strategy so GPU coverage is documented per the plan and fix-plan exit criteria.
Summary (Goal): Validate the joint global-local pipeline on CUDA and document the workflow plus artifacts.
Focus: STRAT-M3-001 — Duck joint global-local refinement (Task 5 CUDA smoke)
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_demo_recover_duck_cli_joint -v
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::test_multi_image_trainer_joint_mode_wires_latents -v
Artifacts: plans/active/strat-m3-001/reports/2026-01-29T210000Z/joint_gpu_smoke/ (mirror PNG/JSON to demo_outputs/duck_joint_gpu/)
Next Up:
1. If CUDA smoke passes quickly, extend the run to 25 iterations and log sigma/scale trajectories for gradient-trend diagnostics.
2. Start drafting the multi-image GPU benchmarking plan (e.g., amortized + joint comparison) if time remains.
