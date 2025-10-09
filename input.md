Summary: Capture PyTorch vs C single-pixel trace for TC-D1 so we know the first divergence before touching simulator code.
Mode: Parity
Focus: SOURCE-WEIGHT-001 / Correct weighted source normalization — Phase E (row E2a)
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-11-source-weights/phase_e/<STAMP>/trace/{commands.txt,collect.log,pytest_tc_d_collect.log,py_trace.txt,c_trace.txt,diff.txt,env.json,trace_notes.md}
Do Now: [SOURCE-WEIGHT-001] export KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md; STAMP=$(date -u +%Y%m%dT%H%M%SZ); OUT=reports/2025-11-source-weights/phase_e/$STAMP/trace; mkdir -p "$OUT" && {
  {
    printf '# %s TC-D1 trace parity\n' "$(date -u)";
    printf 'export KMP_DUPLICATE_LIB_OK=TRUE\nexport NB_RUN_PARALLEL=1\nexport NB_C_BIN=%s\n' "$NB_C_BIN";
  } > "$OUT/commands.txt";
  pytest --collect-only -q tests/test_at_src_003.py | tee "$OUT/collect.log";
  NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee "$OUT/pytest_tc_d_collect.log";
  cmd_py=("python" "-m" "nanobrag_torch" -mat A.mat -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -default_F 100 -hdivsteps 0 -vdivsteps 0 -dispsteps 1 -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -trace_pixel 158 147 -floatfile "$OUT/py_tc_d1.bin");
  printf '%s\n' "${cmd_py[@]}" >> "$OUT/commands.txt";
  "${cmd_py[@]}" | tee "$OUT/py_trace.txt";
  cmd_c=("$NB_C_BIN" -mat A.mat -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -default_F 100 -hdivsteps 0 -vdivsteps 0 -dispsteps 1 -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -trace_pixel 158 147 -floatfile "$OUT/c_tc_d1.bin");
  printf '%s\n' "${cmd_c[@]}" >> "$OUT/commands.txt";
  NB_RUN_PARALLEL=1 "${cmd_c[@]}" | tee "$OUT/c_trace.txt";
  python - <<'PY' >>"$OUT/diff.txt"
from pathlib import Path
py_lines = Path("$OUT/py_trace.txt").read_text().splitlines()
c_lines = Path("$OUT/c_trace.txt").read_text().splitlines()
limit = min(len(py_lines), len(c_lines))
for idx in range(limit):
    if py_lines[idx].strip() != c_lines[idx].strip():
        print(f"First divergence at line {idx}:\nPY {py_lines[idx]}\nC  {c_lines[idx]}")
        break
else:
    if len(py_lines) != len(c_lines):
        print(f"No textual mismatch in prefix; lengths differ (py={len(py_lines)}, c={len(c_lines)})")
    else:
        print("No divergence detected")
PY
  python - <<'PY'
import json, os, torch
summary = {
    'STAMP': os.environ.get('STAMP'),
    'NB_C_BIN': os.environ.get('NB_C_BIN'),
    'torch_version': torch.__version__,
    'cuda_available': torch.cuda.is_available(),
    'trace_pixel': [158, 147],
    'fixture': 'phase_a/20251009T071821Z/fixtures/two_sources.txt'
}
with open("$OUT/env.json", 'w') as fh:
    json.dump(summary, fh, indent=2)
PY
  {
    echo "Trace Review Checklist";
    echo "- note first divergent variable + value";
    echo "- capture n_sources and steps lines";
    echo "- record whether source_I or fluence differ";
  } > "$OUT/trace_notes.md";
}
If Blocked: If any trace command fails, capture stdout/stderr to "$OUT/attempt.log", annotate the failing command, and note the issue in docs/fix_plan.md Attempts before stopping; keep collect-only logs for discovery proof regardless.
Priorities & Rationale:
- specs/spec-a-core.md:150-190 — Normative rule that both weight and wavelength columns are ignored; the trace must respect equal weighting and CLI λ dominance.
- docs/fix_plan.md:4046-4057 — Next Actions now require the trace bundle before parity reruns; failing to collect it keeps Phase E blocked.
- plans/active/source-weight-normalization.md:51-90 — Phase E row E2a mandates the trace capture, and the status snapshot reiterates it as the gating condition.
- golden_suite_generator/nanoBragg.c:2570-2720 — C reference for source ingestion, placeholder counting, and steps normalization; use it to interpret the trace lines.
- src/nanobrag_torch/simulator.py:824-906 — Current PyTorch normalization path; compare `source_norm`, `steps`, and `intensity_accum` logs against the C trace.
- reports/2025-11-source-weights/phase_d/20251009T104310Z/commands.txt — Acceptance harness baseline for TC-D1/TC-D3 parity; reuse CLI arguments exactly.
How-To Map:
- Use `tee` for every command so console output becomes a durable artifact; `commands.txt` should list commands in execution order for replay.
- Confirm both collect-only runs succeed (exit code 0) before launching the simulators; attach logs to fix_plan attempt to prove selector validity.
- Keep `-trace_pixel 158 147` identical on both sides; this (slow, fast) pair lines up with the fixture’s bright pixel noted during Phase C analysis.
- After running the diff script, skim `py_trace.txt`/`c_trace.txt` for `n_sources`, `steps`, `source_I`, `fluence`, and first lattice intensity lines; jot observations in `trace_notes.md`.
- Leave `.bin` outputs (`py_tc_d1.bin`, `c_tc_d1.bin`) in `$OUT` for ad-hoc parsing—do not commit, but they enable quick numpy checks if needed.
- Populate `env.json` with torch version and CUDA availability; parity follow-ups often hinge on whether device auto-detection interfered with results.
- When updating fix_plan attempts, reference `$OUT` path plus the specific divergent variable or confirmation that traces align.
- If traces unexpectedly match, escalate immediately (the fix plan expects a divergence). Capture this in `trace_notes.md` and ping galph before modifying code.
Trace Reading Tips:
- Look for `SOURCE_INFO` or equivalent blocks that enumerate sources; confirm PyTorch lists zero-weight placeholders if C does.
- Compare `steps=` or `normalization=` lines directly; miscounts there explain the 2× intensity gap observed previously.
- Inspect any `source_I` or `beam_flux` lines—C seeds `I` from `source_I[source]`, while PyTorch might still zero them.
- Watch for differences in `omega_pixel` or `capture_fraction`; if identical, the divergence likely precedes scaling.
- Note the first mismatch index from `diff.txt`; include both line contents in `trace_notes.md` for quick reference in fix_plan.
Pitfalls To Avoid:
- Do not reorder slow/fast indices; C assumes (slow, fast).
- Avoid running full pytest or other parity cases—stay focused on TC-D1 evidence.
- Skip manual edits to simulator or docs while collecting data; this loop is evidence-only.
- Ensure NB_C_BIN points to the instrumented build; `-trace_pixel` is unsupported on the frozen root binary.
- Let each `tee` command flush before proceeding; incomplete logs make the diff script misleading.
- Do not compress or delete trace logs after capture; downstream debugging may need full precision output.
- Keep Protected Assets intact (check docs/index.md before moving files); do not rename or delete tracked scripts.
- Resist "quick" hypotheses—record facts from the trace first, then propose fixes next loop.
- If GPU is available, still run CPU traces (per fix plan) to keep parity apples-to-apples.
Pointers:
- docs/fix_plan.md:4046
- plans/active/source-weight-normalization.md:51
- specs/spec-a-core.md:150
- golden_suite_generator/nanoBragg.c:2570
- src/nanobrag_torch/simulator.py:824
- reports/2025-11-source-weights/phase_d/20251009T104310Z/commands.txt
Next Up: Once the trace exposes the first divergent variable, draft the minimal simulator change to reconcile source normalization, then rerun TC-D1/TC-D3 parity harness with fresh metrics (corr ≥0.999, |sum_ratio−1| ≤1e-3).
Attempts Log Guidance:
- After gathering evidence, append Attempt details under [SOURCE-WEIGHT-001] with STAMP, first divergent variable, and artifact list.
- Quote the exact lines from diff.txt in the Observations section so the next loop can jump straight to the failure.
- Note whether zero-weight placeholders appear in the PyTorch trace; if absent, flag that as a blocker before code edits.
- Include collect-only command outputs (paths + exit codes) so the ledger records selector health.
- Mention env.json contents (torch version, CUDA availability) to contextualize potential device drift.
- Record any anomalies (e.g., warnings, missing trace labels) even if they seem benign—future parity hunts rely on this breadcrumb trail.
- If traces match unexpectedly, state that explicitly and mark the task as BLOCKED pending supervisor review.
- Reference plans/active/source-weight-normalization.md row E2a in the Attempt so the gate closure is obvious.
- Link to trace_notes.md in the Attempt for quick narrative context.
- Keep the attempt concise but factual; defer hypotheses until after the trace review is complete.
