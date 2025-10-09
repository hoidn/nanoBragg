Summary: Document the weighted-source normalization math so we can unblock parity fixes.
Mode: Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: main
Mapped tests: pytest --collect-only -q
Artifacts: reports/2025-11-source-weights/phase_b/<STAMP>/normalization_flow.md
Artifacts: reports/2025-11-source-weights/phase_b/<STAMP>/strategy.md
Artifacts: reports/2025-11-source-weights/phase_b/<STAMP>/tests.md
Artifacts: reports/2025-11-source-weights/phase_b/<STAMP>/summary.md
Artifacts: reports/2025-11-source-weights/phase_b/<STAMP>/commands.txt
Artifacts: reports/2025-11-source-weights/phase_b/<STAMP>/env.json
Artifacts: reports/2025-11-source-weights/phase_b/<STAMP>/pytest_collect.log
Do Now: SOURCE-WEIGHT-001 Phase B1–B3 — run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q`, then capture normalization_flow.md, strategy.md, tests.md, summary.md plus commands/env under `reports/2025-11-source-weights/phase_b/<STAMP>/` while tracing the simulator scaling math (no code changes).
If Blocked: If the math trace cannot reconcile with C behavior, log the blocking question in summary.md, keep partial notes, and update docs/fix_plan.md Attempt history before stopping.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:2 — Phase Goal demands sum-of-weights parity before implementation begins.
- plans/active/source-weight-normalization.md:19 — Phase B tasks specify the artifacts we need this loop.
- docs/fix_plan.md:3953 — Weighted-source gap is the immediate blocker for PERF-PYTORCH-004 parity work.
- docs/fix_plan.md:3795 — Vectorization-gap profiling stays blocked until weighted-source correlation improves.
- specs/spec-a-core.md:142 — Normative sampling rules define how source weighting interacts with accumulation.
- docs/development/c_to_pytorch_config_map.md:5 — Config parity guardrails mean any normalization change must align with C semantics.
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ); base=reports/2025-11-source-weights/phase_b/$STAMP; mkdir -p "$base"
- printf "%s\n" "$(date -Is) begin_phase_b $base" >> "$base"/commands.txt
- KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q | tee "$base"/pytest_collect.log; printf "%s\n%s\n" "$(date -Is) pytest_collect" "KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q" >> "$base"/commands.txt
- KMP_DUPLICATE_LIB_OK=TRUE python - <<'PY'
import json, os, platform, torch, pathlib
base = pathlib.Path(os.environ["base"]) if "base" in os.environ else pathlib.Path("$base")
base.mkdir(parents=True, exist_ok=True)
(base/"env.json").write_text(json.dumps({
    "python": platform.python_version(),
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "git_head": os.popen('git rev-parse HEAD').read().strip(),
    "nb_c_bin": os.environ.get("NB_C_BIN", "./golden_suite_generator/nanoBragg")
}, indent=2))
PY
- python - <<'PY'
from pathlib import Path
base = Path("$base")
# normalization_flow.md: step-by-step trace of Simulator.run scaling path
flow = base/"normalization_flow.md"
flow.write_text("## Normalization Flow (Simulator.run)\n\n" \
    + "- Trace inputs: source weights, fluence, oversample, thicksteps\n" \
    + "- List each arithmetic step with src/nanobrag_torch/simulator.py line anchors\n" \
    + "- Note where n_sources currently enters the formula\n")
# strategy.md: decision on fix approach
strategy = base/"strategy.md"
strategy.write_text("## Proposed Normalization Strategy\n\n" \
    + "- Describe whether to divide by sum(weights) or pre-normalize\n" \
    + "- Capture rationale, edge cases, and polarization coupling\n")
# tests.md: future regression coverage
tests = base/"tests.md"
tests.write_text("## Regression Coverage Plan\n\n" \
    + "- Targeted pytest selectors (CPU, CUDA)\n" \
    + "- Expected tolerances / metrics to record\n")
PY
- Use editors/tools of choice to fill normalization_flow.md with detailed math: cite simulator.py lines, any helper functions, and C references.
- Summarize findings and open questions in "$base"/summary.md (include conclusion on normalization rule, outstanding unknowns, next verification steps).
- After documentation is complete, update plans/active/source-weight-normalization.md Phase B rows with state [D] (include timestamp and artifact path) and log docs/fix_plan.md Attempt #2 referencing these artifacts.
Pitfalls To Avoid:
- Do not edit src/ or tests/ files in this loop — documentation only.
- Keep commands.txt chronological; every command must include ISO timestamp + literal invocation.
- Don’t overwrite prior phase_b directories; always use the new timestamp.
- Make sure normalization_flow.md includes concrete file:line references (e.g., simulator.py:837) and identifies where n_sources enters.
- Record any uncertainty about C behavior rather than guessing; flag in summary.md.
- Preserve device/dtype considerations when outlining the strategy; note CUDA expectations explicitly.
- Avoid speculative fixes in plan updates; stay within Phase B scope.
- Ensure env.json is UTF-8 ASCII and only contains the captured metadata.
- When editing markdown, stay within 100-column width where practical.
- After updating fix_plan, double-check git diff for accidental whitespace or unrelated edits.
Pointers:
- plans/active/source-weight-normalization.md:6
- plans/active/source-weight-normalization.md:24
- docs/fix_plan.md:3956
- docs/fix_plan.md:3795
- specs/spec-a-core.md:142
- docs/development/c_to_pytorch_config_map.md:5
Next Up: Prepare Phase C implementation plan (update simulator normalization + regression tests) once design notes are signed off.
