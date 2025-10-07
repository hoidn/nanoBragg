Summary: Capture Phase B design memo for tricubic vectorization so implementation work can proceed with clear tensor/broadcast guidance.
Mode: Docs
Focus: VECTOR-TRICUBIC-001 — Vectorize tricubic interpolation and detector absorption
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-vectorization/phase_b/design_notes.md (new), docs/fix_plan.md attempt log update
Do Now: VECTOR-TRICUBIC-001 — Draft `reports/2025-10-vectorization/phase_b/design_notes.md` covering Phase B tasks B1–B3 in `plans/active/vectorization.md`
If Blocked: Summarise the blocker in `reports/2025-10-vectorization/phase_b/blockers.md` and ping the supervisor before leaving the loop.

Priorities & Rationale:
- `plans/active/vectorization.md:19` still lists B1–B3 as open; the design memo is the gating artifact before code edits.
- `docs/fix_plan.md:1683` documents the status as Phase A complete with Phase B outstanding, demanding written guidance before implementation.
- `reports/2025-10-vectorization/phase_a/tricubic_baseline.md` already holds baseline timing; the design memo must reference it to justify vectorization targets.
- `docs/development/pytorch_runtime_checklist.md:1` requires explicit device/dtype planning ahead of PyTorch edits; capture these decisions in the memo.
- `specs/spec-a-parallel.md:1` ties interpolation behavior to acceptance tests; the design must note how vectorization will preserve those guarantees.
- `docs/architecture/pytorch_design.md:1` stresses vectorization without breaking differentiability; align memo guidance accordingly.
- `nanoBragg.c:2604` (polin3/polin2/polint) is the authoritative behavior; map each helper into batched tensor algebra in the memo.
- `reports/2025-10-vectorization/phase_a/absorption_baseline.md` provides absorption timings that should inform subsequent performance goals documented in the memo.
- `reports/2025-10-vectorization/phase_a/env.json` shows the CUDA-capable environment; memo should explicitly plan CPU+CUDA validation to match available hardware.
- `docs/development/testing_strategy.md:2` enumerates Tier 1 acceptance tests that the vectorized path must continue to satisfy; cite relevant nodes when planning regression coverage.
- `docs/architecture/c_code_overview.md:1` collects background on interpolation helpers; link to specific subsections where polin2/polin3 are analysed.
- `docs/architecture/undocumented_conventions.md:1` highlights subtle C behaviors; incorporate any interpolation-specific quirks into risk assessment.
- `reports/benchmarks/20250930-165726-compile-cache/analysis.md` catalogs hotspots attributed to scalar tricubic loops; align performance goals against these measurements.
- `docs/index.md:1` flags the PyTorch runtime checklist as mandatory; citing index ensures Protected Asset policy compliance.

How-To Map:
- Ensure directory exists: `mkdir -p reports/2025-10-vectorization/phase_b`.
- Skim C reference: `rg -n "polin" nanoBragg.c | sed -n '2600,2750p'` for polynomial flow details.
- Review PyTorch current implementation: `sed -n '350,520p' src/nanobrag_torch/models/crystal.py` to capture existing scalar loops.
- Load baseline timings for citation: `less reports/2025-10-vectorization/phase_a/tricubic_baseline.md`.
- Capture absorption context: `less reports/2025-10-vectorization/phase_a/absorption_baseline.md`.
- Reference runtime checklist: `less docs/development/pytorch_runtime_checklist.md` and note device/dtype rules in memo.
- Outline memo scaffold (Context → Shape Plan → Polynomial Vectorization → Gradient/Device checklist → Pending validation strategy).
- When describing shapes, include diagrams or tables referencing `(slow, fast)` broadcast conventions from the plan.
- Document how oversample, phi, mosaic, and source dimensions expand through the gather and polynomial evaluation.
- Summarise gradient expectations, citing where `.item()`/`torch.linspace` cannot appear and which new tests are required.
- Include explicit pointers to future regression commands (e.g., reuse `pytest tests/test_at_str_002.py` and upcoming vectorized unit tests) with CPU/CUDA variants.
- Note performance measurement plan: reuse `scripts/benchmarks/tricubic_baseline.py --mode vectorized` once implemented; mention expected output paths.
- Keep memo ASCII and ensure headings use markdown `##`/`###` for clarity.
- After drafting, re-read to confirm it answers Phase B exit criteria (shapes, equations, gradient/device checklist, validation strategy).
- Update `docs/fix_plan.md` Attempt history with memo path, key findings, and planned validation once draft is saved.
- Leave TODO markers only inside memo if follow-up data is required; highlight them in fix_plan entry.
- No simulator code edits this loop—focus solely on documentation.
- Capture memo revision metadata (date, git SHA) at the top for traceability per plan guidance.
- Cross-check notation with existing acceptance tests to ensure h/k/l indexing matches spec wording.
- Reference how caching strategy will evolve post-vectorization (e.g., reuse vs recalculation) to pre-empt Phase C decisions.
- Draft preliminary risk table (numerical precision, memory usage, compile compatibility) so future loops can prioritise mitigation.
- Consider including short pseudocode snippets or tensor expressions to clarify the intended broadcast order.
- Mention dependency on `torch.vectorize` vs manual broadcasting if relevant; note reasoning for chosen approach.
- Indicate where additional unit tests will live (e.g., `tests/test_tricubic_vectorized.py`) and what they will assert.
- Call out any data collection needed before Phase C (e.g., verifying mismatched warning counts) so it can be scheduled.
- Save intermediate notes if memo drafting spans multiple loops; reference them in plan attempts.
- Plan to attach appendix tables for Na/Nb/Nc sampling so future engineers can extend checks easily.
- Note any dependencies on torch.compile behavior (graph breaks, caching) gleaned from prior reports.
- Encourage capturing symbolic expressions for Vandermonde weights to ensure reproducibility.
- Include a short glossary for symbols (S, F, Na, etc.) to keep memo self-contained.

Pitfalls To Avoid:
- Do not change implementation files; documentation-only per supervisor brief.
- Avoid inventing new flags or renaming plan tasks; stay aligned with existing plan structure.
- Keep device discussion detached from current CLI issues to prevent conflation with CLI-FLAGS work.
- Do not duplicate plan content verbatim; synthesise actionable steps in your own words.
- Ensure memo references existing artifacts (baseline logs) rather than restating numbers without citation.
- No direct copy of C code beyond short citations; summarise behavior instead.
- Maintain `(slow, fast)` ordering clarity; note `meshgrid(indexing="ij")` expectations in memo.
- Don’t promise performance numbers without linking to baseline data; set goals relative to recorded timings.
- Avoid editing archived reports; create new Phase B files only.
- Keep the memo versioned; include date and SHA at top for traceability.
- Avoid reintroducing the deprecated scalar fallback as a "temporary" solution—memo should plan to retire it once vectorized path lands.
- Do not schedule code changes before documenting validation approach; Phase B exit criteria forbid this.
- Resist adding new plan phases; stick to the agreed structure and update only within current phase boundaries.
- Avoid conflating vectorized tricubic work with detector absorption; memo should separate prerequisites clearly.
- Ensure new diagrams or tables remain textual ASCII; no pasted images.
- Do not forget to mention gradient check prerequisites; missing them creates rework later.
- Avoid referencing private experiments; cite only artifacts checked into repo.
- Keep memo free of speculative benchmarks; mark estimates distinctly if needed.
- Do not leave memo in draft without logging status in fix_plan; incomplete communication slows follow-up loops.
- Avoid forgetting to mention ROI/shape expectations; these drive regression harness updates.
- Do not alter plan checklists directly from memo—use supervisor plan updates if structure must change.
- Avoid mixing scalar fallback cleanup steps into design memo; they belong to implementation phases.

Pointers:
- `plans/active/vectorization.md:1` — Phase roadmap with B1–B3 definitions.
- `docs/fix_plan.md:1683` — Status ledger and Next Actions.
- `reports/2025-10-vectorization/phase_a/tricubic_baseline.md:1` — Current tricubic timing baseline.
- `reports/2025-10-vectorization/phase_a/absorption_baseline.md:1` — Detector absorption baseline metrics.
- `docs/development/pytorch_runtime_checklist.md:1` — Device/dtype runtime guardrails.
- `specs/spec-a-core.md:1` — Core interpolation requirements (see linked shard for structure factors).
- `specs/spec-a-parallel.md:1` — Acceptance tests impacted by interpolation changes.
- `docs/architecture/pytorch_design.md:1` — Vectorization and differentiability expectations.
- `nanoBragg.c:2604` — Reference polin3/polin2 implementation lines.
- `scripts/benchmarks/tricubic_baseline.py:1` — Baseline harness to reference in memo.
- `reports/2025-10-vectorization/phase_a/env.json:1` — Captured environment metadata for reproducibility notes.
- `docs/architecture/c_code_overview.md:1` — Background analysis of interpolation routines to cite.
- `docs/architecture/undocumented_conventions.md:1` — Implicit behaviors to watch during vectorization.
- `docs/development/testing_strategy.md:40` — Tiered validation expectations for parity and gradients.
- `reports/benchmarks/20250930-165726-compile-cache/analysis.md:1` — Existing performance hotspot evidence.
- `plans/archive/general-detector-geometry/implementation.md:1` — Example phased plan tone/style referenced in instructions.

Next Up: Once Phase B memo lands and is logged, proceed to Phase C implementation planning (vectorized neighborhood gather) per `plans/active/vectorization.md`.
