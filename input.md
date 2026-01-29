Plan: docs/plans/2026-01-29-hybrid-benchmark-evidence.md
References:
- docs/plans/2026-01-29-vi-hybrid-mc-vi.md — implementation details for HybridMosaicTrainer, MC warm-start helper, and CLI wiring
- docs/strategy/mainstrategy.md §9 — strategic mandate for hybrid MC-VI escalation plus σ≥1.5° exit criterion
- docs/findings.md (FND-VI-2026-01f/g) — baseline evidence for collapse and flow failure you must cite when logging hybrid outcomes
- docs/fix_plan.md §[STRAT-VI-001] — Task 27 status, supervisor state line, and artifact paths that must be updated
- plans/active/strat-vi-001/reports/2026-01-29T235959Z/{flow_diagnostics,flow_benchmark}/ — most recent comparative evidence for referencing when contrasting hybrid behavior
- docs/development/testing_strategy.md §1.4 — runtime guardrails (device/dtype neutrality, `KMP_DUPLICATE_LIB_OK=TRUE` requirement)
Summary:
- Follow docs/plans/2026-01-29-hybrid-benchmark-evidence.md with superpowers:executing-plans to capture the pending hybrid diagnostics + canonical benchmark artifacts and archive them under a new timestamp (2026-01-29T235800Z) inside plans/active/strat-vi-001/reports/.
- Run `scripts/analysis/vi_hybrid_refinement.py` to produce the 25-iter warm-start diagnostics, then execute `scripts/benchmark_vi_mosaic.py --pipeline hybrid` for the 150-iter canonical benchmark, copying demo_outputs artifacts into the new report folders.
- Update docs/strategy/mainstrategy.md §9, docs/findings.md (FND-VI-2026-01), and docs/fix_plan.md Task 27 with the hybrid results (explicit σ trajectories, whether ≥1.5° was reached, links to artifact folders) and refresh plans/active/strat-vi-001/reports/2026-01-29T235800Z/summary.md with the turn log.
Summary (one sentence): Capture and document the hybrid MC warm-start + VI fine-tune evidence so we can close or escalate STRAT-VI-001 Task 27 with canonical σ metrics.
Focus: STRAT-VI-001 — Task 27 Hybrid MC-VI escalation plan
Branch: feature/spec-based-2
Mapped tests: pytest tests/test_vi_hybrid.py::TestMCWarmStart::test_run_mc_warm_start_records_history -v; pytest tests/test_vi_mosaic.py::TestCLIs::test_vi_hybrid_refinement_cli -v
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T235800Z/
Next Up:
1. If hybrid meets ≥1.5°: author a short QA note under docs/findings.md summarizing σ trajectories and decision to adopt hybrid pipeline.
2. If hybrid fails: begin drafting Gaussian-likelihood follow-up in docs/plans/ per strategy §9 (temperature/likelihood scaling fallback).
