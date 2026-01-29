Plan: docs/plans/2026-01-29-m2-amortized-evidence.md
References:
- docs/strategy/mainstrategy.md §7 — defines STRAT-M2-001 success metrics (150-iter Duck demo, per-image σ divergence, gradient scaling expectations)
- docs/development/testing_strategy.md §6.2 — canonical pytest/CLI selectors plus artifact + gradient validation workflow for the amortized Duck path
- docs/specs/duck_multi_image_dataset.md — dataset schema and observation scaling guarantees consumed by the demo/encoder
- docs/fix_plan.md — authoritative ledger for marking STRAT-M2-001 exit criteria + supervisor state updates after evidence lands
Summary:
Execute the new STRAT-M2-001 evidence plan: (1) run the canonical amortized Duck demo for 150 iterations with `--log-gradients`, stage artifacts under `plans/active/strat-m2-001/reports/2026-01-29T234500Z/amortized_demo/` and mirror them into `demo_outputs/duck_amortized/`, (2) fold the recorded σ trajectory + gradient norms into `docs/strategy/mainstrategy.md §7` so the milestone reflects actual results, (3) refresh `docs/development/testing_strategy.md §6.2` with the final canonical command/selector list and artifact expectations, and (4) close the STRAT-M2-001 entry in `docs/fix_plan.md` with references to the evidence bundle and next-step guidance for M3.
Summary: Capture the amortized Duck evidence bundle and update strategy/testing docs plus the fix-plan with the new artifacts.
Focus: STRAT-M2-001 — Duck multi-image demo
Branch: feature/spec-based-2
Mapped tests: pytest tests/test_vi_mosaic.py::test_demo_recover_duck_cli_amortized -v; pytest tests/test_vi_mosaic.py::test_multi_image_trainer_amortized_mode -v; pytest tests/test_vi_mosaic.py::test_duck_mosaic_encoder_outputs_mu_rho -v
Artifacts: plans/active/strat-m2-001/reports/2026-01-29T234500Z/
Next Up: 1) If time remains, add dataset-size gradient scaling notes to Strategy §7; 2) Prepare outline for STRAT-M2-001 Task M3 (joint global-local refinement).
