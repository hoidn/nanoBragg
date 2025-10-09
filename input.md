Summary: Capture and document the divergence auto-selection mismatch so we can pick the correct fix path before touching simulator code.
Mode: Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2025-11-source-weights/phase_d/<STAMP>/{divergence_analysis.md,commands.txt,pytest_collect.log}
Do Now: [SOURCE-WEIGHT-001] Phase D1 divergence analysis — create a new UTC-stamped folder under reports/2025-11-source-weights/phase_d/, write divergence_analysis.md summarising C vs PyTorch source counts (with spec + nanoBragg.c anchors), and finish by running `pytest --collect-only -q` (log to the same folder).
If Blocked: If you cannot reconcile C vs PyTorch behaviour, capture the unresolved questions in divergence_analysis.md plus the snippets you inspected, then ping me with the open items noted in Attempts History.
Priorities & Rationale:
- specs/spec-a-core.md:142 — normative statement that weights are ignored; confirm whether it forbids divergence grids when a sourcefile is present.
- reports/2025-11-source-weights/phase_d/20251009T101247Z/summary.md — existing evidence showing steps=4 vs 2; reuse data instead of rerunning heavy CLI commands.
- nanoBragg.c:2570 — ground-truth loop creating sources; quote exact lines to justify whatever fix direction we adopt.
- plans/active/source-weight-normalization.md — Phase D now requires documented evidence before implementation; keep entries aligned.
- docs/fix_plan.md:4129 — Next Actions expect divergence_analysis.md + design notes before handing off to code changes.
How-To Map:
- Export a UTC stamp (`export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`) and mkdir `reports/2025-11-source-weights/phase_d/$STAMP` before you start writing.
- Append every shell command you run (rg, sed, python snippets) to `commands.txt` in that folder so the evidence trail is reproducible.
- Use `rg -n "sourcefile" specs/spec-a-core.md` and `sed -n '2550,2750p' nanoBragg.c` to pull exact wording for the analysis doc.
- Summarise the old CLI metrics (steps, correlation, totals) in divergence_analysis.md; reference existing JSON/summary files rather than recomputing numbers.
- After drafting the doc, run `pytest --collect-only -q | tee reports/2025-11-source-weights/phase_d/$STAMP/pytest_collect.log` to verify the harness still imports cleanly.
Pitfalls To Avoid:
- Do not modify simulator or config code yet; this loop is documentation-only.
- Keep the analysis doc ASCII and quote spec/C code verbatim with line anchors per Rule #11 expectations.
- Avoid re-running the heavy CLI parity commands unless explicitly approved; reuse 20251009 artifacts.
- Maintain device/dtype neutrality in any reasoning; call out assumptions if evidence only covers CPU.
- Respect Protected Assets (docs/index.md references); do not move or delete existing artifacts.
- No ad-hoc scripts outside reports/…; use built-in tools like rg/sed for evidence gathering.
- Keep the stamped folder self-contained (divergence_analysis.md, commands.txt, pytest_collect.log).
Pointers:
- specs/spec-a-core.md:142
- docs/fix_plan.md:4129
- plans/active/source-weight-normalization.md
- reports/2025-11-source-weights/phase_d/20251009T101247Z/summary.md
- nanoBragg.c:2570
Next Up: Phase D2 design_notes.md outlining whether we mirror C’s divergence grid or seek a spec amendment.
