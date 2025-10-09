Summary: Capture the lambda semantics decision so VECTOR-TRICUBIC-002 Phase A can unblock SOURCE-WEIGHT parity.
Mode: Docs
Focus: [VECTOR-TRICUBIC-002] Vectorization relaunch backlog
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2025-11-source-weights/phase_e/<STAMP>/lambda_semantics.md
Do Now: [VECTOR-TRICUBIC-002] Phase A0 — run `pytest --collect-only -q`; draft `reports/2025-11-source-weights/phase_e/<STAMP>/lambda_semantics.md` detailing the CLI `-lambda` override + steps reconciliation plan (reference the 20251009T130433Z lambda sweep).
If Blocked: capture TC-D1 PyTorch diagnostics (commands, simulator `n_sources`/`steps`/`fluence`) under `reports/2025-11-source-weights/phase_e/<STAMP>/py_diagnostics/` and note blockers in docs/fix_plan Attempts.
Priorities & Rationale:
- plans/active/vectorization.md:23 — Phase A0 now requires documenting how we force CLI `-lambda` and fix steps before parity reruns.
- docs/fix_plan.md:3775 — VECTOR-TRICUBIC-002 next actions hinge on confirming the lambda/steps approach.
- docs/fix_plan.md:4046 — SOURCE-WEIGHT-001 mandate to author the lambda semantics plan before fresh evidence runs.
- plans/active/source-weight-normalization.md:65 — Phase E2 done; Phase E3 stays blocked until the lambda/steps fix path is agreed.
- docs/development/testing_strategy.md:28 — collect-only proof required for doc-only loops.
How-To Map:
- Create a fresh timestamped folder under `reports/2025-11-source-weights/phase_e/` (e.g., `$(date -u +%Y%m%dT%H%M%SZ)`); store `lambda_semantics.md`, `commands.txt`, and any quick helper scripts there.
- Summarise the CLI `-lambda` override plan: entry points to touch (`src/nanobrag_torch/__main__.py`, `src/nanobrag_torch/config.py`, `src/nanobrag_torch/models/crystal.py`), how to ignore sourcefile wavelengths, and how to enforce consistent `steps` counting.
- Reference existing evidence (`reports/2025-11-source-weights/phase_e/20251009T130433Z/lambda_sweep/`) and cite spec lines (`specs/spec-a-core.md` on sources) plus C reference log anchors.
- Run `pytest --collect-only -q` from repo root after drafting the doc; capture output into the same report folder (`collect.log`).
- Update docs/fix_plan.md `[SOURCE-WEIGHT-001]` Attempts with the new artifact path and summary once the note is ready; include next steps for implementation.
Pitfalls To Avoid:
- Do not modify production code in this loop.
- Keep the new plan note ASCII and reference exact file paths / command lines.
- Do not claim parity metrics until the CLI `-lambda` fix is implemented and rerun.
- Avoid overwriting existing report folders; always use a new timestamp.
- Remember Protected Assets (no edits to docs/index.md referenced items).
- Maintain device/dtype neutrality in the plan (call out CPU+CUDA expectations).
- Do not delete or rename existing lambda sweep artifacts.
- Keep commands ready to replay (no hard-coded local paths outside repo).
Pointers:
- plans/active/vectorization.md:23
- docs/fix_plan.md:3775
- docs/fix_plan.md:4046
- plans/active/source-weight-normalization.md:65
- docs/development/testing_strategy.md:28
Next Up (optional): Implement the CLI `-lambda` override in source parsing and regenerate TC-D1/TC-D3 parity evidence once the design note is approved.
