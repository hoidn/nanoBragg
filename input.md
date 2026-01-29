Plan: docs/plans/2026-01-29-vi-poisson-likelihood-rescaling.md (Tasks 5–6)
References:
  - docs/strategy/mainstrategy.md §9 (defines canonical VI benchmark + KL schedule expectations)
  - docs/findings.md (FND-VI-2026-01 Observation Scale Bug context + evidence format)
  - docs/fix_plan.md (STRAT-VI-001 ledger + state machine requirements)
  - docs/development/testing_strategy.md §1.4 (device/dtype + command guardrails)
  - scripts/benchmark_vi_mosaic.py (CLI producing canonical MC/VI/analytic comparison)
  - scripts/analysis/vi_poisson_diagnostics.py (metadata schema for observation stats)
Summary: Run the full 150-iteration VI benchmark with `--fluence 1e13` and archive the PNG/JSON/log outputs under the new artifact root so we can prove whether Poisson observations restore σ≈2° and unblock STRAT-VI-001 Task 12.
Summary (1-sentence): Capture the canonical Poisson-fluence benchmark artifacts and update findings/strategy/fix-plan with the observed σ trajectory.
Focus: STRAT-VI-001 — Variational mosaic simulator
Branch: feature/spec-based-2
Mapped tests:
  - tests/test_vi_mosaic.py::test_benchmark_script_smoke
  - tests/test_vi_mosaic.py::test_vi_diagnostics_snapshot
Mapped Tests Guardrail: Both selectors already collect >0 tests; add a minimal targeted test if future changes introduce new CLI knobs.
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T120000Z/{benchmark,docs}
Next Up:
  1. If σ<1.5°, run `scripts/analysis/vi_poisson_diagnostics.py` with the same fluence to capture per-iteration curvature evidence.
  2. Prototype per-pixel likelihood normalization or alternative priors if Poisson rescaling still under-delivers.
