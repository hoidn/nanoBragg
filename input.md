Summary: Consolidate Tap 4 evidence and audit the default_F fallback so we know which parity tap to pursue next.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_e0/<STAMP>/comparison/
Do Now: [VECTOR-PARITY-001] Next Actions #1-2 — draft `f_cell_comparison.md` plus `default_f_audit.md` from Attempts #26/27 before choosing Tap 5 vs Tap 6
If Blocked: Capture a narrative summary in `reports/2026-01-vectorization-parity/phase_e0/<STAMP>/comparison/notes.md` explaining what data was missing and why the audit could not proceed.
Priorities & Rationale:
- docs/fix_plan.md:60-66 — Next Actions call for the Tap 4 comparison and default_F audit before selecting the next hypothesis.
- plans/active/vectorization-parity-regression.md:70-92 — Phase E table now marks E6 done and keeps E7 open pending this comparison/audit.
- reports/2026-01-vectorization-parity/phase_e0/20251010T102752Z/f_cell_summary.md — PyTorch Tap 4 findings to reference.
- reports/2026-01-vectorization-parity/phase_e0/20251010T103811Z/c_taps/PHASE_E6_SUMMARY.md — C Tap 4 evidence showing the centre-pixel 0.0 F_cell.
- specs/spec-a-core.md — Verify expected default_F behaviour when no HKL file is supplied.
How-To Map:
- `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `export BASE=reports/2026-01-vectorization-parity/phase_e0`; `export OUTDIR="$BASE/${STAMP}/comparison"`; `mkdir -p "$OUTDIR"`.
- Append each command you execute to `$OUTDIR/commands.txt` (e.g., `printf "%s\n" "<cmd>" >> "$OUTDIR/commands.txt"`).
- Generate the comparison doc:
  `python - <<'PY'`
  ```
  import json, os, pathlib, textwrap
  base = pathlib.Path(os.environ["BASE"]) 
  outdir = pathlib.Path(os.environ["OUTDIR"]) 
  outdir.mkdir(parents=True, exist_ok=True)
  py_files = {
      "edge": base / "20251010T102752Z/py_taps/pixel_0_0_f_cell_stats.json",
      "centre": base / "20251010T102752Z/py_taps/pixel_2048_2048_f_cell_stats.json",
  }
  c_metrics = json.load((base / "20251010T103811Z/c_taps/tap4_metrics.json").open())
  lines = ["# Tap 4 F_cell Comparison", "", "| Pixel | Impl | total_lookups | out_of_bounds | zero_f | default_f | mean_f_cell | h_range | k_range | l_range |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
  for label, py_path in py_files.items():
      py_stats = json.load(py_path.open())["values"]
      c_key = f"pixel_{0 if label == 'edge' else 2048}_{0 if label == 'edge' else 2048}"
      c_stats = c_metrics[c_key]
      bounds = py_stats["hkl_bounds"]
      lines.append(f"| {label} | PyTorch | {py_stats['total_lookups']} | {py_stats['out_of_bounds_count']} | {py_stats['zero_f_count']} | N/A | {py_stats['mean_f_cell']:.6f} | [{bounds['h_min']}, {bounds['h_max']}] | [{bounds['k_min']}, {bounds['k_max']}] | [{bounds['l_min']}, {bounds['l_max']}] |")
      lines.append(f"| {label} | C | {c_stats['total_lookups']} | {c_stats['out_of_bounds_count']} | {c_stats['zero_f_count']} | {c_stats['default_f_count']} | {c_stats['mean_f_cell']:.6f} | [{c_stats['hkl_min'][0]}, {c_stats['hkl_max'][0]}] | [{c_stats['hkl_min'][1]}, {c_stats['hkl_max'][1]}] | [{c_stats['hkl_min'][2]}, {c_stats['hkl_max'][2]}] |")
  lines.extend(["", "## Notes", "- PyTorch metrics from Attempt #26 (`20251010T102752Z/py_taps`).", "- C metrics from Attempt #27 (`20251010T103811Z/c_taps`).", "- Highlight the centre-pixel discrepancy (PyTorch `default_F=100` vs C `F_cell=0`).", "- Add any observations about intensity ratios or follow-up hypotheses before committing."])
  (outdir / "f_cell_comparison.md").write_text("\n".join(lines))
  PY
- Audit fallback logic:
  * `rg -n "default_F" src/nanobrag_torch -g"*.py" > "$OUTDIR/default_f_refs.txt"`
  * Inspect `src/nanobrag_torch/models/crystal.py` default-F handling (note key functions and conditions) via `sed -n '1,220p'` into `$OUTDIR/models_crystal_snippet.txt`.
  * Review `scripts/debug_pixel_trace.py` taps around `collect_f_cell_tap` to ensure instrumentation mirrors production (capture snippet to `$OUTDIR/trace_helper_snippet.txt`).
  * Summarise findings + spec citations in `$OUTDIR/default_f_audit.md` (include whether the fallback should apply to in-bounds HKL lookups when the array contains zeros).
- Close the loop by drafting Attempt notes for `[VECTOR-PARITY-001]` (reference the new artifacts) but do not mark E7 done until the audit conclusion is ready to select Tap 5 vs Tap 6.
Pitfalls To Avoid:
- No production code edits; analysis only.
- Do not re-instrument the C binary this loop.
- Keep all artifacts under `reports/` and out of git.
- Preserve Protected Assets (`docs/index.md`, `loop.sh`, `supervisor.sh`).
- Avoid assuming default_F semantics without citing spec (§4 of `specs/spec-a-core.md`).
- Maintain device/dtype neutrality in any snippets; no `.cpu()` hacks.
- Watch for stale STAMP reuse—each new bundle gets its own directory.
- Keep notes ASCII-only per editing constraints.
- Document commands/env in `$OUTDIR/commands.txt` for reproducibility.
- Do not run full pytest; evidence gathering only.
Pointers:
- docs/fix_plan.md:60-66
- plans/active/vectorization-parity-regression.md:70-92
- reports/2026-01-vectorization-parity/phase_e0/20251010T102752Z/f_cell_summary.md
- reports/2026-01-vectorization-parity/phase_e0/20251010T103811Z/c_taps/PHASE_E6_SUMMARY.md
- specs/spec-a-core.md
Next Up: 1) Once audit lands, decide between Tap 5 (pre-normalisation intensity) and Tap 6 (water background).
