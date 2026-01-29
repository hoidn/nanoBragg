Plan: docs/plans/2026-01-29-vi-hybrid-mc-vi.md
References:
- docs/strategy/mainstrategy.md §9 — documents exhausted VI mitigations and hybrid MC-VI requirements
- docs/findings.md (FND-VI-2026-01f/g) — authoritative evidence for prior failures to reference when logging new artifacts
- docs/fix_plan.md §[STRAT-VI-001] — task 27 scope + exit criteria you must update as progress lands
- plans/active/strat-vi-001/reports/2026-01-29T235959Z/flow_diagnostics/ & flow_benchmark/ — last turn’s evidence bundle to cite when contrasting hybrid behavior
- docs/development/testing_strategy.md §1.4 — runtime discipline (device/dtype neutrality, `KMP_DUPLICATE_LIB_OK=TRUE`)
Summary:
- Execute Task 27 by implementing the hybrid MC warm-start + VI fine-tune pipeline per plan tasks 1–5, using superpowers:executing-plans to drive the workflow.
- Land `run_mc_warm_start()` + dataclasses/tests, add `MosaicPosterior.prime_from_sigma()`, build `HybridMosaicTrainer`, ship the diagnostics CLI, then integrate the hybrid path into `scripts/benchmark_vi_mosaic.py`.
- Archive 25-iter diagnostics and the canonical 150-iter benchmark under `plans/active/strat-vi-001/reports/2026-01-29T235200Z/hybrid_{diagnostics,benchmark}/`, update docs/findings/fix_plan with outcomes, and state clearly whether σ≥1.5°.
Summary (one sentence): Build and evidence the hybrid MC-VI mitigation so we either recover σ≥1.5° or document the failure with canonical logs.
Focus: STRAT-VI-001 — Task 27 Hybrid MC-VI escalation plan
Branch: feature/spec-based-2
Mapped tests: pytest tests/test_vi_hybrid.py::TestMCWarmStart::test_run_mc_warm_start_records_history -k warm_start; pytest tests/test_vi_mosaic.py::TestCLIs::test_vi_hybrid_refinement_cli
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T235200Z/
Next Up:
1. If hybrid succeeds, draft follow-on QA doc entry summarizing σ trajectories for docs/findings.
2. If hybrid fails, start outlining Gaussian likelihood mitigation notes under docs/plans/ (per strategy §9).
