Summary: Capture omega asymmetry taps to confirm the oversample hypothesis before touching production code.
Mode: Parity
Focus: docs/fix_plan.md#[VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_e0/<STAMP>/py_taps/omega_analysis.md; reports/2026-01-vectorization-parity/phase_e0/<STAMP>/c_taps/omega_c_trace.txt; reports/2026-01-vectorization-parity/phase_e0/<STAMP>/omega_comparison.md
Do Now: Execute docs/fix_plan.md item [VECTOR-PARITY-001] Next Action #1 with `KMP_DUPLICATE_LIB_OK=TRUE NB_TRACE_EDGE_PIXEL="0,0" python scripts/debug_pixel_trace.py --pixel 0 0 --oversample 2 --out-dir reports/2026-01-vectorization-parity/phase_e0/$STAMP/py_taps/`
If Blocked: If the trace script errors or missing flags, capture the stderr/log under `reports/2026-01-vectorization-parity/phase_e0/$STAMP/attempt_fail.log` and note the failure in docs/fix_plan.md Attempts before stopping.
Priorities & Rationale:
- Validate omega-last-value hypothesis: plans/active/vectorization-parity-regression.md Phase E table demands numeric taps before remediation.
- Keep parity guardrails aligned: docs/fix_plan.md#[VECTOR-PARITY-001] requires evidence before code edits.
- Follow callchain SOP: reports/2026-01-vectorization-parity/phase_e0/20251010T092845Z/summary.md enumerates Tap 2/3 as the next gate.
- Maintain spec parity: specs/spec-a-core.md§4 insists oversample scaling mirrors C semantics; we need facts before spec updates.
How-To Map:
- Export `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` to namespace artifacts.
- Run `KMP_DUPLICATE_LIB_OK=TRUE NB_TRACE_EDGE_PIXEL="0,0" python scripts/debug_pixel_trace.py --pixel 0 0 --oversample 2 --out-dir reports/2026-01-vectorization-parity/phase_e0/$STAMP/py_taps/`.
- After run, compute center-pixel baseline with `KMP_DUPLICATE_LIB_OK=TRUE NB_TRACE_EDGE_PIXEL="2048,2048" python scripts/debug_pixel_trace.py --pixel 2048 2048 --oversample 2 --out-dir reports/2026-01-vectorization-parity/phase_e0/$STAMP/py_taps_center/` (reuse to compare).
- Summarize omega statistics into `reports/2026-01-vectorization-parity/phase_e0/$STAMP/py_taps/omega_analysis.md` (include mean vs last-value and relative asymmetry figures).
- Update docs/fix_plan.md Attempts once artifacts exist; leave remediation for the next loop after C taps land.
Pitfalls To Avoid:
- Do not modify production code or trace script defaults—evidence pass only.
- Keep tensors device-neutral; avoid forcing CPU even if debug script offers shortcuts.
- Preserve Protected Assets (docs/index.md) when adding directories; nest under reports/ only.
- No nb-compare or full pytest runs this loop—stay focused on targeted taps.
- Be explicit with env vars (`KMP_DUPLICATE_LIB_OK`, `NB_TRACE_EDGE_PIXEL`) or the script may skip data.
- Record the exact commands and STAMP path in docs/fix_plan.md Attempt summary.
- Do not delete prior artifacts; append new folder under a fresh STAMP.
Pointers:
- docs/fix_plan.md#[VECTOR-PARITY-001]
- plans/active/vectorization-parity-regression.md (Phase E table)
- reports/2026-01-vectorization-parity/phase_e0/20251010T092845Z/summary.md
- scripts/debug_pixel_trace.py
Next Up: (1) Capture C omega taps (Next Action #2) once PyTorch asymmetry metrics are archived.
