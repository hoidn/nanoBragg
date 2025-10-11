Summary: Guard the debug trace pre-polar accumulator so Cluster C4 stops throwing UnboundLocalError during Phase M1 quick fixes.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Phase M1 — Sprint 0 Quick Fixes (Cluster C4)
Branch: feature/spec-based-2
Mapped tests: tests/test_debug_trace.py::TestDebugTraceFeatures::test_printout_flag; tests/test_debug_trace.py::TestDebugTraceFeatures
Artifacts: reports/2026-01-test-suite-triage/phase_m1/$STAMP/debug_trace/
Do Now: Execute [TEST-SUITE-TRIAGE-001] Phase M1c and run env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_debug_trace.py::TestDebugTraceFeatures::test_printout_flag
If Blocked: Capture the failing log with the selector above into reports/2026-01-test-suite-triage/phase_m1/$STAMP/debug_trace/baseline.log, note the traceback in notes.md, and halt for guidance.
Priorities & Rationale:
- plans/active/test-suite-triage.md:202-214 keeps Phase M1 on track; M1c is the next open Sprint 0 task after C1/C3 landed.
- reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md:126-153 documents Cluster C4’s root cause and selectors.
- docs/fix_plan.md:40-51 binds current Sprint 0 work to clusters C4/C5/C7 now that C1/C3 are closed.
- src/nanobrag_torch/simulator.py:1000-1275 contains the debug trace path that dereferences I_before_normalization_pre_polar.
- docs/development/testing_strategy.md:31-48 reminds us to stay on targeted selectors and log artifacts under stamped directories.
How-To Map:
- export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md; export STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2026-01-test-suite-triage/phase_m1/$STAMP/debug_trace/
- env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_debug_trace.py::TestDebugTraceFeatures::test_printout_flag 2>&1 | tee reports/2026-01-test-suite-triage/phase_m1/$STAMP/debug_trace/baseline.log
- In src/nanobrag_torch/simulator.py ensure I_before_normalization_pre_polar is initialised before conditional branches (vectorised + oversample paths) and guard _apply_debug_output so it only prints when the value is not None; keep vectorisation and dtype/device neutrality intact.
- Re-run env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_debug_trace.py::TestDebugTraceFeatures::test_printout_flag --maxfail=1 2>&1 | tee reports/2026-01-test-suite-triage/phase_m1/$STAMP/debug_trace/fix.log
- Run env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_debug_trace.py::TestDebugTraceFeatures 2>&1 | tee reports/2026-01-test-suite-triage/phase_m1/$STAMP/debug_trace/regression.log to confirm the other three tests cleared.
- Summarise the before/after behaviour and any code touchpoints in reports/2026-01-test-suite-triage/phase_m1/$STAMP/debug_trace/notes.md, then log Attempt #23 in docs/fix_plan.md and mark plan row M1c as done before requesting review.
Pitfalls To Avoid:
- Do not run the full pytest suite or unrelated selectors—stay on the mapped debug-trace tests.
- Preserve vectorisation: no per-pixel Python loops or scalar tensor conversions when initialising the debug variable.
- Avoid `.item()` or `.cpu()` on tensors inside the simulator; keep device/dtype neutrality per arch.md §15.
- Keep `_apply_debug_output` signature compatible with existing call sites (no parameter order changes).
- Do not remove or rename debug-tap variables referenced by other instrumentation (specifically CLI-FLAGS-003 comments).
- Leave other Sprint 0 clusters (C5/C7) untouched in this loop; they will follow once C4 lands.
- Maintain Protected Assets from docs/index.md (loop.sh, input.md, etc.).
- Capture logs under the stamped directory before editing code so Attempt history has baseline evidence.
Pointers:
- plans/active/test-suite-triage.md:202-214
- reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md:126-153
- docs/fix_plan.md:40-51
- src/nanobrag_torch/simulator.py:1000-1275
- docs/development/testing_strategy.md:31-48
Next Up: Cluster C5 (Simulator API kwargs) once debug trace scope is resolved and logged.
