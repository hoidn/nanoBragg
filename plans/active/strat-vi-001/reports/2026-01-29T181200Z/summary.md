### Turn Summary
Authored the VI observation-scale parity plan and refreshed fix_plan/input.md so execution can start immediately.
Confirmed the raw-intensity vs Poisson-count mismatch in the benchmark wiring and spelled out how to thread `observation_scale` through ELBO, diagnostics, and MC/analytic loops.
Next step: implement Task 17, run the canonical 150-iteration benchmark with the corrected scaling, and update docs/findings based on the new artifacts.
Artifacts: plans/active/strat-vi-001/reports/2026-01-29T181200Z/ (summary.md, scale_parity/)
