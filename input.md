Plan: docs/plans/2026-01-29-vi-gaussian-likelihood.md
References:
- docs/strategy/mainstrategy.md §9 — normative mandate for Gaussian likelihood escalation and σ≥1.5° benchmark criteria
- docs/architecture/README.md + docs/index.md — check architecture hub + index before touching simulator interfaces (Protected Assets rule)
- docs/findings.md (FND-VI-2026-01 / -01h) — baseline evidence you must cite when logging Gaussian results
- docs/development/testing_strategy.md §1.4 — runtime guardrails (device/dtype neutrality, KMP_DUPLICATE_LIB_OK)
- docs/plans/2026-01-29-vi-mosaic-design.md — posterior contracts that Gaussian path must preserve
Summary:
- Use superpowers:executing-plans to follow docs/plans/2026-01-29-vi-gaussian-likelihood.md step-by-step: author the Gaussian-likelihood spec, extend observation helpers, add the Gaussian ELBO, wire diagnostics + benchmark CLIs with a `--likelihood` switch, and capture artifacts + doc updates under plans/active/strat-vi-002/reports/2026-01-29T130500Z/ so we can decide if Gaussian loss recovers σ≥1.5°.
- Ensure new math references cite docs/strategy/mainstrategy.md §9 (do not restate equations from specs); keep ObservationBundle metadata consistent with existing Poisson helpers.
Summary (one sentence): Deliver the Gaussian likelihood fallback (spec, helpers, ELBO, CLI, artifacts) per the plan so we can judge whether it fixes the σ collapse.
Focus: STRAT-VI-002 — Gaussian likelihood VI path
Branch: feature/spec-based-2
Mapped tests: pytest tests/test_vi_mosaic.py::test_gaussian_observation_helper_hits_target_mean -v; pytest tests/test_vi_mosaic.py::TestGaussianELBO::test_gaussian_elbo_returns_diagnostics -v; pytest tests/test_vi_mosaic.py::TestDiagnosticsCLI::test_diagnostics_cli_gaussian -v; pytest tests/test_vi_mosaic.py::TestBenchmarkCLI::test_benchmark_cli_gaussian -v
Artifacts: plans/active/strat-vi-002/reports/2026-01-29T130500Z/
Next Up:
1. If Gaussian succeeds, draft docs/findings entry FND-VI-2026-02 and prep STRAT-VI-002 exit.
2. If Gaussian fails, outline amortized multi-image inference plan per strategy §8.
