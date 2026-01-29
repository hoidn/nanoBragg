Plan: docs/plans/2026-01-29-vi-hybrid-mc-vi.md (TO BE DRAFTED)
References:
- docs/strategy/mainstrategy.md §9 — flow posterior FAILED, all 8 mitigations exhausted
- docs/findings.md FND-VI-2026-01g — flow posterior blow-up / NaN evidence
- plans/active/strat-vi-001/reports/2026-01-29T235959Z/ — flow diagnostics + benchmark artifacts
Summary:
- Task 26 (flow posterior evaluation) is COMPLETE with FAILURE outcome. Flow posterior diverges to NaN on canonical benchmark.
- All 8 VI mitigations tested: (1) KL annealing, (2) temperature scaling, (3) IWAE, (4) non-centered parameterization, (5) observation-scale parity, (6) informative priors, (7) multi-scale geometry, (8) normalizing flows. None achieve σ≥1.5°.
- NEXT: Draft hybrid MC-VI mitigation plan (`docs/plans/2026-01-29-vi-hybrid-mc-vi.md`). The hybrid approach uses MC warm-start to initialize σ near the true value, then fine-tunes via a constrained variational posterior.
Summary (one sentence): All VI mitigations exhausted — escalate to hybrid MC-VI plan.
Focus: STRAT-VI-001 — Hybrid MC-VI escalation
Branch: feature/spec-based-2
Mapped tests: (none — planning phase)
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T235959Z/
Next Up:
1. Draft `docs/plans/2026-01-29-vi-hybrid-mc-vi.md` with implementation tasks.
2. Register hybrid plan entry in `docs/fix_plan.md`.
3. If hybrid approach is rejected, consider alternative strategies (Gaussian likelihood, amortized inference).
