Summary: Capture Tap 5.1 PyTorch HKL audit so we can prove the centre-pixel default_F fallback before touching physics.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_e0/<STAMP>/py_taps/hkl_subpixel_*.json; reports/2026-01-vectorization-parity/phase_e0/<STAMP>/comparison/tap5_hkl_audit.md
Do Now: [VECTOR-PARITY-001] Run Tap 5.1 PyTorch per-subpixel HKL audit (`KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel 2048 2048 --oversample 2 --taps hkl_subpixel --json --out-dir $OUTDIR --tag centre`).
If Blocked: Record the obstacle in attempts history, stash partial outputs under $OUTDIR, and stop—do not modify C instrumentation or rerun nb-compare until we review.
Priorities & Rationale:
- docs/fix_plan.md:68-76 — Next Actions #1–#3 direct us to run Tap 5.1 PyTorch first, then mirror on C.
- plans/active/vectorization-parity-regression.md:84-101 — Phase E row E12 defines the new tap schema and storage requirements.
- reports/2026-01-vectorization-parity/phase_e0/20251010T113608Z/comparison/tap5_hypotheses.md — Recommends Tap 5.1/5.2 to confirm the HKL indexing bug (H1 at 95% confidence).
- specs/spec-a-core.md:232-240 — Normative nearest-neighbour fallback contract we must cite when we report `out_of_bounds` behaviour.
How-To Map:
- Export `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and `OUTDIR=reports/2026-01-vectorization-parity/phase_e0/${STAMP}`; create `$OUTDIR/py_taps` and `$OUTDIR/comparison`, plus `$OUTDIR/commands.txt`.
- Extend `scripts/debug_pixel_trace.py` with a new `collect_hkl_subpixel_tap` (mirror `collect_f_cell_tap`) that emits per-subpixel fractional HKL, rounded `(h0,k0,l0)`, `F_cell`, and `out_of_bounds`. Keep output JSON-serialisable (`subpixels` list) and respect device/dtype neutrality.
- Run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel 2048 2048 --oversample 2 --taps hkl_subpixel --json --out-dir $OUTDIR/py_taps --tag centre`.
- Optionally capture the edge pixel `(0,0)` in the same schema (`--tag edge`) to aid later comparisons; record both commands in `$OUTDIR/commands.txt`.
- Summarise findings in `$OUTDIR/comparison/tap5_hkl_audit.md` (centre vs optional edge), quoting the spec section above and noting whether `out_of_bounds` stayed `True`. Highlight the exact `(h0,k0,l0)` integers we recorded.
- Update `docs/fix_plan.md` attempts history with the new bundle path and log the command hash; do not touch plan rows yet (we still owe Tap 5.1 on C).
Pitfalls To Avoid:
- No production code beyond the new tap helper; do not edit simulator/crystal logic.
- Do not add/remove trace guards in the C binary this loop.
- Keep all artifacts under the fresh `$STAMP`; never overwrite 20251010 evidence packs.
- Maintain double precision (`--dtype float64`) unless a guardrail forces float32.
- Ensure environment variable `KMP_DUPLICATE_LIB_OK=TRUE` is set for every Python run.
- Do not run pytest/nb-compare; this is an evidence-only turn.
- Record every command in `$OUTDIR/commands.txt` as executed, no retroactive edits.
- Validate JSON dumps before exiting (use `jq .` or `python -m json.tool`).
- Respect Protected Assets referenced in docs/index.md (no deletes/moves).
Pointers:
- docs/fix_plan.md:60-83 — Fresh Next Actions and Tap 5.1/5.2 expectations.
- plans/active/vectorization-parity-regression.md:69-114 — Phase E task table with E12–E14 sequencing.
- reports/2026-01-vectorization-parity/phase_e0/20251010T113608Z/comparison/intensity_pre_norm.md — Baseline ratios motivating Tap 5.1.
- reports/2026-01-vectorization-parity/phase_e0/20251010T110735Z/py_taps/pixel_2048_2048_intensity_pre_norm.json — Existing PyTorch tap output to match schema.
- scripts/debug_pixel_trace.py:1-180 — Current tap infrastructure to extend.
Next Up: If time remains, prepare notes for the C-side instrumentation (tap schema + guard placement) but wait for supervisor approval before editing C.
