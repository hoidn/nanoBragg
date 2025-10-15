Summary: Draft the C18 tolerance analysis packet so we can renegotiate the slow-gradient threshold with evidence.
Mode: Perf
Focus: [TEST-SUITE-TRIAGE-001] Phase P3 C18 tolerance packet
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_p/$STAMP/{c18_timing.md,timing_table.csv,summary.md}
Do Now: [TEST-SUITE-TRIAGE-001] Phase P3 — create the C18 timing packet (no pytest).
If Blocked: Capture open questions plus any partial timing scrap in c18_timing.md, log the blocker in docs/fix_plan.md Attempts, and stop before altering thresholds/tests.
Priorities & Rationale:
- plans/active/test-suite-triage.md:346 — Phase P3 is the next gate after C19 resolution.
- docs/fix_plan.md:1-8 — Active Focus now demands the C18 tolerance packet.
- reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/chunks/chunk_03/summary.md — 845.68s runtime data to leverage.
- docs/development/testing_strategy.md:68-120 — Performance/tolerance adjustments must cite authoritative process.
- arch.md:150-214 — Runtime guardrails to respect when proposing tolerance shifts.
How-To Map:
- `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` once; keep it for all new files.
- `mkdir -p reports/2026-01-test-suite-triage/phase_p/$STAMP`.
- Copy the key metrics (total runtime, per-test durations, environment) from `phase_o/20251015T043128Z/chunks/chunk_03/` into `c18_timing.md`; include a short rationale for any proposed tolerance (e.g., 900s guard with 845.68s baseline).
- Build a compact CSV (`timing_table.csv`) enumerating the slowest tests (≥5s) with columns: test_node,runtime_s,status,source_selector.
- Summarise conclusions + recommended next action in `summary.md` (include tolerance proposal, validation commands to rerun chunk 03 or targeted selector once tolerance updates land).
- Update `docs/fix_plan.md` Attempts for [TEST-SUITE-TRIAGE-001] with STAMP + artifact pointers when done.
Pitfalls To Avoid:
- Do not rerun pytest; this loop is evidence-only.
- Keep analysis CPU-focused; note CUDA availability but don’t assume GPU timing.
- Preserve prior artifacts (no overwriting `phase_o/20251015T043128Z`).
- Reference authoritative timing data; avoid ad-hoc estimates.
- Align tolerance recommendation with testing_strategy guardrails (document rationale ≥2 sentences).
- Note any assumptions about hardware specs and flag if additional runs are needed.
- Leave code/tests untouched; this loop produces documentation only.
- Record environment metadata (Python/PyTorch version) if proposing tolerance changes.
Pointers:
- plans/active/test-suite-triage.md:346-356
- docs/fix_plan.md:1-8
- reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/chunks/chunk_03/summary.md
- docs/development/testing_strategy.md:68-120
- arch.md:150-214
Next Up: 1. Draft the follow-on chunk 03 rerun plan once the tolerance packet is ready.
