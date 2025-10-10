Summary: Build Tap 5 comparison pack so we can explain the 4× intensity mismatch before touching physics.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_e0/<STAMP>/comparison/intensity_pre_norm.md; reports/2026-01-vectorization-parity/phase_e0/<STAMP>/comparison/tap5_hypotheses.md; reports/2026-01-vectorization-parity/phase_e0/<STAMP>/comparison/commands.txt
Do Now: [VECTOR-PARITY-001] Generate the Tap 5 comparison + hypothesis bundle (analysis only, no pytest this loop).
If Blocked: Note the obstacle in attempts history, stash partial notes under the new <STAMP>/comparison/ folder, and stop; do not alter instrumentation or rerun nb-compare until we review.
Priorities & Rationale:
- docs/fix_plan.md:67-69 — Next Actions call for the Tap 5 comparison memo and hypothesis ranking.
- plans/active/vectorization-parity-regression.md:74-89 — Phase E table records Attempt #30 results and assigns E10/E11 to produce these artifacts.
- reports/2026-01-vectorization-parity/phase_e0/20251010T110735Z/py_taps/pixel_0_0_intensity_pre_norm.json — PyTorch Tap 5 data to reuse.
- reports/2026-01-vectorization-parity/phase_e0/20251010T112334Z/c_taps/pixel_0_0_tap5.log — C Tap 5 metrics showing the ~4× I_before_scaling gap.
- specs/spec-a-core.md:232-259 — Normative intensity accumulation formula to cite in the analysis.
How-To Map:
- Set `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and `OUTDIR=reports/2026-01-vectorization-parity/phase_e0/$STAMP/comparison`; create the directory and an empty `commands.txt`.
- Copy the exact commands you run (python snippets, jq, etc.) into `commands.txt` as you go.
- Use a short Python script that reads the two Tap 5 artifacts (`py_taps/*intensity_pre_norm.json` and `c_taps/pixel_*_tap5.log`) to extract `I_before_scaling`, `steps`, `omega`, `capture_fraction`, `polar`, and `I_pixel_final`; emit a CSV/JSON in `$OUTDIR` or embed the table directly in the markdown.
- Author `intensity_pre_norm.md` summarising the side-by-side metrics, explicit ratios (C/PyTorch), and which factors cancel; include references to specs/spec-a-core.md §§246–259 and attach delta percentages.
- Draft `tap5_hypotheses.md` ranking at least three candidate causes (e.g., per-subpixel accumulation order, lattice amplitude scaling, latent background terms). For each, note required follow-up evidence (Tap 6 water background vs Tap 5.1 per-subpixel audit) and the recommended next step.
- Update `plans/active/vectorization-parity-regression.md` Phase E rows E10/E11 only after the docs are written, then log a new Attempt in docs/fix_plan.md with artifact paths.
Pitfalls To Avoid:
- Do not modify production code, instrumentation, or regenerate traces this loop.
- Keep new artifacts under the fresh `$STAMP`; never overwrite the 20251010 bundles.
- Avoid introducing new tests or running nb-compare/full pytest; evidence-only loop.
- Maintain device/dtype neutrality in any exploratory scripts (stick to analysis of existing outputs).
- Respect Protected Assets (docs/index.md references) and do not move/delete listed files.
- Ensure `commands.txt` stays synced with actual commands executed.
- When quoting log snippets, keep them minimal—link to the artifact instead of pasting large blocks.
- Use float formatting with explicit exponents so ratios are easy to audit later.
Pointers:
- docs/fix_plan.md:60-76 — Current state + refreshed Next Actions.
- plans/active/vectorization-parity-regression.md:69-100 — Phase E roadmap and new E10/E11 tasks.
- reports/2026-01-vectorization-parity/phase_e0/20251010T110735Z/py_taps/intensity_pre_norm_summary.md — PyTorch Tap 5 summary to mine.
- reports/2026-01-vectorization-parity/phase_e0/20251010T112334Z/comparison/intensity_pre_norm_c_notes.md — C-side notes for context.
- specs/spec-a-core.md:232-259 — Acceptance formula for intensity accumulation.
Next Up: If the analysis lands quickly, tee up Tap 6 decision notes (water background vs deeper Tap 5) in the same bundle.
