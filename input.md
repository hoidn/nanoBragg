Plan: docs/plans/2026-01-29-vi-gaussian-likelihood.md
References:
- docs/strategy/mainstrategy.md §9.2 — normative escalation + ≥1.5° benchmark gate
- docs/architecture/vi_gaussian_likelihood.md §Model/Contracts — Gaussian log-likelihood equation + required observation metadata
- docs/development/testing_strategy.md §1.4 + §3.2 — runtime guardrails + benchmark evidence workflow
- docs/findings.md (FND-VI-2026-02) — update with Gaussian outcome + artifact links
- docs/plans/2026-01-29-vi-mosaic-design.md — posterior contracts that diagnostics/benchmark must respect
Summary:
- Use superpowers:executing-plans to execute Task 6 of docs/plans/2026-01-29-vi-gaussian-likelihood.md without deviating from the spec math (reference docs/architecture/vi_gaussian_likelihood.md §Model instead of paraphrasing it).
- Capture fresh Gaussian diagnostics and the canonical 150-iteration benchmark with `--likelihood gaussian --observation-mean 25 --observation-std 5`, logging JSON + stdout under plans/active/strat-vi-002/reports/2026-01-29T213000Z/{gaussian_diagnostics,gaussian_benchmark}/ and copying `vi_vs_mc_*` into demo_outputs/ after each run.
- Record σ trajectories vs the ≥1.5° success criterion in per-folder summary.md files plus the top-level report summary; update docs/findings.md (FND-VI-2026-02), docs/strategy/mainstrategy.md §9.2, and docs/development/testing_strategy.md with whichever outcome occurs, citing the artifact paths.
- Ensure ObservationBundle metadata and diagnostics JSON include `likelihood_model`, `observation_std`, and `scale` so Poisson/Gaussian parity is auditable; mention the new workflow in README_PYTORCH only if user-facing guidance changes.
- After evidence lands, rerun Gaussian-focused pytest selectors to prove the helpers/ELBO/CLI wiring still pass, then `git status` to show only intentional files changed.
Summary (one sentence): Run and document the Gaussian diagnostics + canonical benchmark so we can log σ vs ≥1.5° and update the findings/strategy/testing docs accordingly.
Focus: STRAT-VI-002 — Gaussian likelihood VI path
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py -k gaussian -v; KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_vi_mosaic.py::TestBenchmarkCLI::test_benchmark_cli_gaussian -v
Artifacts: plans/active/strat-vi-002/reports/2026-01-29T213000Z/
Next Up:
1. If Gaussian meets ≥1.5°, close STRAT-VI-002 and outline amortized multi-image plan per docs/strategy/mainstrategy.md §8.
2. If Gaussian fails, draft mitigation brief for multi-image amortized inference.
