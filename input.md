Summary: Build the loop-inventory tooling so we know exactly which Python surfaces still need vectorization work.
Mode: Perf
Focus: [VECTOR-GAPS-002] Vectorization gap audit
Branch: feature/spec-based-2
Mapped tests: none — planning
Artifacts: reports/2026-01-vectorization-gap/phase_a/<STAMP>/loop_inventory.json; reports/2026-01-vectorization-gap/phase_a/<STAMP>/summary.md
Do Now: [VECTOR-GAPS-002] Vectorization gap audit — Phase A1/A2. Implement `scripts/analysis/vectorization_inventory.py`, then run `python scripts/analysis/vectorization_inventory.py --package src/nanobrag_torch --outdir reports/2026-01-vectorization-gap/phase_a/<STAMP>/` followed by `pytest --collect-only -q` (log both outputs under the new phase_a folder).
If Blocked: Capture a manual loop list with `rg -n "^\s*for " src/nanobrag_torch` saved to `reports/2026-01-vectorization-gap/phase_a/<STAMP>/manual_scan.txt`, note blockers in docs/fix_plan.md Attempt, and pause before code edits.
Priorities & Rationale:
- plans/active/vectorization-gap-audit.md:6 — Phase A requires an AST-based inventory before we can rank candidates.
- docs/fix_plan.md:3735 — New [VECTOR-GAPS-002] entry depends on Phase A1 artifacts before delegating fixes.
- docs/architecture/pytorch_design.md:1 — Vectorization section defines required batch flows we must preserve when closing future gaps.
- docs/development/testing_strategy.md:1 — Mandates authoritative command capture; profiler + collect-only proof must accompany new tooling.
- reports/2025-10-vectorization/gaps/20251009T061928Z/analysis.md — Prior divergence loop evidence shows the value of structured gap reports.
How-To Map:
- Create `scripts/analysis/vectorization_inventory.py` that parses Python AST (use `ast` module) to list `For`/`While` nodes under `src/nanobrag_torch/`; include CLI args `--package` and `--outdir`, output both JSON (machine-readable) and Markdown excerpt totalling loop metadata (module, line, node text, heuristic iteration drivers).
- Ensure script inherits repo logging standards: place outputs in the provided outdir, reuse `pathlib`, enforce ASCII only, exit non-zero on errors; document usage at top of script.
- After implementation, run the command from Do Now with a fresh `<STAMP>` (UTC `date -u +%Y%m%dT%H%M%SZ`); store `loop_inventory.json`, `loop_inventory.md`, and the console transcript as `commands.txt`.
- Run `pytest --collect-only -q` immediately afterward; save the log as `pytest_collect.log` in the same directory to prove test discovery unaffected.
- Update docs/fix_plan.md Attempt for [VECTOR-GAPS-002] with artifact paths, summary bullets (counts of loops by module, highlight suspected hotspots), and note follow-up for Phase A3.
Pitfalls To Avoid:
- Do not scan outside `src/nanobrag_torch`; avoid third-party directories to keep output actionable.
- Keep the analysis script device/dtype agnostic (no hard-coded `.cuda()`); it should only inspect source text.
- Respect Protected Assets (leave docs/index.md, loop.sh untouched).
- Capture outputs under `reports/2026-01-vectorization-gap/...` only; no dumping to repo root or /tmp.
- Stay within ASCII for all new files; no emoji or smart quotes in reports.
- Document heuristics clearly so later runs remain comparable; include version info in env.json.
- Do not delete existing gap reports; reference them in summary instead.
- Record all commands invoked (inventory, pytest) in `commands.txt` for reproducibility.
Pointers:
- plans/active/vectorization-gap-audit.md:15 — Phase A checklist and artifact expectations.
- docs/fix_plan.md:3735 — Next Actions to satisfy when logging Attempt.
- docs/development/pytorch_runtime_checklist.md:5 — Vectorization guardrails to cite in summary.
- docs/development/testing_strategy.md:33 — Command sourcing rules for perf evidence.
- reports/2025-10-vectorization/gaps/20251009T061928Z/analysis.md — Reference style for summarising loop findings.
Next Up: Phase A3 annotation pass (summarise inventory findings) or Phase B1 profiler capture once the script output looks good.
