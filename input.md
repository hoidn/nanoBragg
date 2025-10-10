Summary: Phase B static audit for dtype-neutral cache handling so determinism work can resume.
Mode: Docs
Focus: [DTYPE-NEUTRAL-001] dtype neutrality guardrail
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-test-suite-triage/phase_d/<STAMP>/dtype-neutral/phase_b/
Do Now: Run plans/active/dtype-neutral.md Phase B (B1–B5) static audit; capture analysis/tap list/summary under reports/2026-01-test-suite-triage/phase_d/<STAMP>/dtype-neutral/phase_b/ (no pytest).
If Blocked: Record the blocker in phase_b/summary.md, update docs/fix_plan.md attempt notes, and signal in Attempts History before exiting.
Priorities & Rationale:
- Highlight cache dtype gaps per plans/active/dtype-neutral.md:33-39 to unblock determinism triage.
- Keep docs/fix_plan.md:534-557 in sync with new evidence so the ledger reflects Phase B progress.
- Cross-check detector caching rules in docs/architecture/detector.md:73-88 to confirm expected device/dtype behaviour.
How-To Map:
- `STAMP=$(date -u +%Y%m%dT%H%M%SZ); ART_ROOT=reports/2026-01-test-suite-triage/phase_d/$STAMP/dtype-neutral/phase_b; mkdir -p "$ART_ROOT"` — log this in `$ART_ROOT/commands.txt`.
- Use `rg -n "_cached" src/nanobrag_torch/models/detector.py` and `rg -n "allclose" src/nanobrag_torch/models/detector.py` to enumerate cache comparisons; copy relevant line anchors into `$ART_ROOT/analysis.md`.
- Inventory other modules with cache+dtype coupling via `rg -n "_cached_" src/nanobrag_torch -g"*.py"` and `rg -n "torch.allclose" src/nanobrag_torch -g"*.py"`; note any hotspots in detector, simulator, crystal, or beam components.
- Compile a tap proposal in `$ART_ROOT/tap_points.md` (B4) listing where instrumentation might confirm dtype transitions post-fix.
- Summarise findings and recommended remediation scope in `$ART_ROOT/summary.md`, then append Attempt details to docs/fix_plan.md `[DTYPE-NEUTRAL-001]` per B5.
Pitfalls To Avoid:
- No edits to src/ or tests/ files; this loop is evidence-only.
- Do not run pytest beyond the commands listed (none required this turn).
- Keep all artifacts under the timestamped ART_ROOT; avoid scattering logs elsewhere.
- Preserve Protected Assets (see docs/index.md) — no renames/deletions.
- Maintain ASCII output in reports; avoid adding notebooks or binaries.
Pointers:
- plans/active/dtype-neutral.md:28
- docs/fix_plan.md:534
- docs/architecture/detector.md:73
- src/nanobrag_torch/models/detector.py:744
- tests/test_at_parallel_013.py:146
Next Up: Draft Phase C remediation plan once Phase B artifacts are reviewed.
