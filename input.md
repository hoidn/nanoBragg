Summary: Capture the spec-first decision and draft the SOURCE-WEIGHT Phase F test redesign packet.
Mode: Docs
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence
Artifacts: reports/2025-11-source-weights/phase_f/<STAMP>/{test_plan.md,commands.txt,collect.log}
Do Now: Execute [SOURCE-WEIGHT-001] Phase F1–F3; run pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence and capture the selectors into the new phase_f/<STAMP>/ bundle before drafting test_plan.md.
If Blocked: Record blockers plus the partial artifacts in phase_f/<STAMP>/notes.md, update Attempts History, and ping supervisor for clarification before attempting code edits.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:35-45 — Phase F gates define the required design packet before any test rewrites.
- docs/fix_plan.md:4035-4059 — Ledger now references the spec decision and expects Phase F deliverables next.
- reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md — Source of spec-first conclusions you must cite in test_plan.md.
- docs/development/testing_strategy.md:1-120 — Authoritative commands/tolerances to reuse when scoping new selectors.
How-To Map:
- export KMP_DUPLICATE_LIB_OK=TRUE
- mkdir -p reports/2025-11-source-weights/phase_f/<STAMP>
- pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee reports/2025-11-source-weights/phase_f/<STAMP>/collect.log
- Document commands/env in reports/2025-11-source-weights/phase_f/<STAMP>/commands.txt
- Draft reports/2025-11-source-weights/phase_f/<STAMP>/test_plan.md summarising current vs proposed assertions, acceptance metrics, CLI bundle, and references to the spec decision memo
Pitfalls To Avoid:
- Do not modify src/ production code during this documentation loop.
- Keep artifacts under reports/…/phase_f/ but do not commit the generated binaries/logs.
- Maintain device/dtype neutrality in any proposed harness (reference CUDA coverage explicitly).
- Follow Rule 11: quote exact C references in design sections rather than paraphrasing.
- Preserve the parallel trace workflow; no new physics hypotheses without evidence links.
- Avoid guessing pytest selectors—validate with --collect-only before recording them.
- Note expected C divergence as "expected per C-PARITY-001" to prevent future confusion.
Pointers:
- plans/active/source-weight-normalization.md:35-44
- docs/fix_plan.md:4035-4051
- plans/active/vectorization.md:21-26
- plans/active/vectorization-gap-audit.md:32-36
- specs/spec-a-core.md:4-160
Next Up: 1) Once the design packet is merged, move to Phase G1 (rewrite TestSourceWeights suite). 2) After tests pass, prepare Phase G evidence bundle with targeted pytest + CLI runs.
