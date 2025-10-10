Summary: Publish the Phase H parity memo and flip the source-weight divergence test to expect PASS.
Mode: Docs
Focus: SOURCE-WEIGHT-001 Phase H (parity memo + test update)
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py::TestSourceWeights; tests/test_cli_scaling.py::TestSourceWeightsDivergence
Artifacts: reports/2025-11-source-weights/phase_h/<STAMP>/{commands.txt,parity_reassessment.md,pytest.log,metrics.json}
Do Now: [SOURCE-WEIGHT-001] Phase H1-H2 — NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence
If Blocked: Capture failing pytest output under phase_h/<STAMP>/pytest.log, leave the test marked xfail again, and document the failure plus hypotheses in parity_reassessment.md before stopping.
Priorities & Rationale:
- plans/active/source-weight-normalization.md (Phase H table) — H1–H2 are the gate before any downstream plans can unblock.
- docs/fix_plan.md:4065-4155 — Next Actions now demand the Phase H memo and test flip prior to Phase I propagation.
- specs/spec-a-core.md:151-153 — Normative statement that both implementations ignore source weights; memo must cite it.
- reports/2025-11-source-weights/phase_g/20251010T000742Z/notes.md — Authoritative parity metrics (corr=0.9999886, |sum_ratio−1|=0.0038) to restate in the memo/test.
- tests/test_cli_scaling.py:600-672 — Existing divergence test structure you will update to expect PASS.
How-To Map:
- Set env (repo root): `export KMP_DUPLICATE_LIB_OK=TRUE`; `export NB_RUN_PARALLEL=1`; `export NB_C_BIN=./golden_suite_generator/nanoBragg`.
- Create bundle dir: `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `OUT=reports/2025-11-source-weights/phase_h/$STAMP`; `mkdir -p "$OUT"` (do not commit `reports/`).
- Draft memo skeleton at `$OUT/parity_reassessment.md` summarising (a) spec citation, (b) Phase G metrics, (c) sanitized fixture hash (f23e1b1e6041…), (d) quote of `golden_suite_generator/nanoBragg.c:2570-2720` showing equal-weight accumulation, and (e) explicit statement that `phase_e/.../spec_vs_c_decision.md` is now historical.
- Record commands: append each step to `$OUT/commands.txt` (pytest run, any helper scripts).
- Update `tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_c_divergence_reference` by removing `@pytest.mark.xfail`, asserting `results.correlation >= 0.999` and `abs(results.sum_ratio - 1) <= 3e-3`, and adding a memo link comment referencing `$OUT/parity_reassessment.md`.
- Re-run the mapped tests (`NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence | tee "$OUT/pytest.log"`).
- After tests pass, capture metrics from the pytest fixture (most helper returns already include correlation/ratio) and store a small `$OUT/metrics.json` with the observed values.
- Update docs/fix_plan.md `[SOURCE-WEIGHT-001]` Attempts with the new `<STAMP>` bundle and mark Phase H1/H2 items as complete; note the memo path and pytest results.
- Leave Phase H3/H4 for the next loop but add a short "Next Steps" paragraph in parity_reassessment.md summarising remaining tasks.
Pitfalls To Avoid:
- Do not edit production simulator code; this loop is documentation + test expectation only.
- Keep all new evidence in `reports/…/phase_h/<STAMP>/`; never commit those artifacts.
- Ensure the memo includes the literal C-code quote (Rule 11) and references the sanitized fixture checksum.
- Preserve device neutrality when running pytest—no hard-coded `.cpu()` conversions when editing tests.
- Maintain `NB_RUN_PARALLEL=1`; otherwise the divergence test will skip the C runner.
- When modifying tests, avoid loosening tolerances beyond the documented thresholds (0.999 / 3e-3).
- Keep the xfail removal focused on this single test; do not touch other XPASS markers.
- Run `pytest --collect-only -q tests/test_cli_scaling.py` if import errors appear before editing expectations.
Pointers:
- specs/spec-a-core.md:151-153
- plans/active/source-weight-normalization.md (Phase H table)
- docs/fix_plan.md:4065-4155
- reports/2025-11-source-weights/phase_g/20251010T000742Z/notes.md
- tests/test_cli_scaling.py:600-672
Next Up: Tackle Phase H3 ledger/bug cleanup once the memo and test updates land.
