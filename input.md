Summary: Capture PyTorch Tap 5.1 per-subpixel HKL evidence so we can prove the centre pixel is wrongly defaulting to F_cell=default_F.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_e0/<STAMP>/py_taps/hkl_subpixel_*.json; reports/2026-01-vectorization-parity/phase_e0/<STAMP>/comparison/tap5_hkl_audit.md
Do Now: [VECTOR-PARITY-001] Add the PyTorch `hkl_subpixel` tap and run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel 2048 2048 --oversample 2 --taps hkl_subpixel --json --out-dir $OUTDIR/py_taps --tag centre`.
If Blocked: Log the obstacle in docs/fix_plan.md attempts, stash whatever JSON/logs you did capture under $OUTDIR, and stop—do not touch the C binary or run nb-compare until we regroup.
Priorities & Rationale:
- docs/fix_plan.md:68-76 — Next Actions #1-3 require the PyTorch HKL audit before instrumenting C.
- plans/active/vectorization-parity-regression.md:70-93 — Phase E row E12 defines the tap schema and storage targets we must hit.
- reports/2026-01-vectorization-parity/phase_e0/20251010T113608Z/comparison/intensity_pre_norm.md:10 — Shows the centre pixel default_F fallback we are validating.
- specs/spec-a-core.md:232-240 — Normative contract for nearest-neighbour HKL lookup that our tap output must cite.
- scripts/debug_pixel_trace.py:1-200 — Existing tap infrastructure to extend; mirror collect_f_cell_tap patterns.
How-To Map:
- Export `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and `OUTDIR=reports/2026-01-vectorization-parity/phase_e0/${STAMP}`; create `$OUTDIR/py_taps`, `$OUTDIR/comparison`, and `$OUTDIR/commands.txt`.
- Add a `collect_hkl_subpixel_tap` helper (parallel to `collect_f_cell_tap`) that logs per-subpixel fractional HKL, rounded `(h0,k0,l0)`, retrieved `F_cell`, and `out_of_bounds` booleans; keep tensors on the caller’s device/dtype.
- Update tap routing so `--taps hkl_subpixel` calls the new helper and writes JSON files when `--json` is set; follow the existing schema conventions (tap_id, pixel coords, subpixels list).
- Run the centre-pixel command listed above; append the exact command and env vars to `$OUTDIR/commands.txt`. If time allows, capture the edge pixel `(0,0)` with `--tag edge` for later comparisons.
- Validate JSON structure via `python -m json.tool $OUTDIR/py_taps/*json` (or `jq`) before writing the comparison memo.
- Summarise findings in `$OUTDIR/comparison/tap5_hkl_audit.md` (centre vs optional edge), quoting the spec clause and calling out whether `out_of_bounds` stayed `True` on PyTorch.
- Record Attempt details in docs/fix_plan.md under `[VECTOR-PARITY-001]`, referencing the new bundle path and command snippets; leave plan rows E12-E14 untouched until C taps land.
Pitfalls To Avoid:
- Do not modify production HKL lookup logic; restrict changes to tap plumbing.
- Leave the C binary alone this loop—no new TRACE_C guards or rebuilds.
- Keep dtype/device neutrality when building tap payloads; no forced `.cpu()` or float64-only tensors.
- Avoid rerunning older stamps; every artifact must live under the fresh `$STAMP` directory.
- Don’t run pytest or nb-compare—this is an evidence-only turn.
- Ensure `KMP_DUPLICATE_LIB_OK=TRUE` prefixes every Python invocation.
- Keep commands history exact; no rewriting `commands.txt` after execution.
- Respect Protected Assets from docs/index.md; no file moves or deletes.
- Validate JSON before exiting so the next loop isn’t blocked on format errors.
Pointers:
- docs/fix_plan.md:68-76
- plans/active/vectorization-parity-regression.md:70-93
- reports/2026-01-vectorization-parity/phase_e0/20251010T113608Z/comparison/intensity_pre_norm.md:10
- specs/spec-a-core.md:232-240
- scripts/debug_pixel_trace.py:1-200
Next Up: Instrument the C-side `TRACE_C_TAP5_HKL` mirror (Phase E13) once the PyTorch tap output is archived.
