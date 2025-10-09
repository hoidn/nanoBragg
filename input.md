Summary: Capture weighted-source parity metrics (TC-D1/TC-D3) now that Option B is live.
Mode: Parity
Focus: SOURCE-WEIGHT-001 / Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_src_003.py -v
Artifacts: reports/2025-11-source-weights/phase_e/<STAMP>/{commands.txt,collect.log,pytest.log,py_tc_d1.bin,py_tc_d3.bin,c_tc_d1.bin,c_tc_d3.bin,correlation.txt,sum_ratio.txt,metrics.txt,simulator_diagnostics.txt,env.json}
Do Now: [SOURCE-WEIGHT-001] Run KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_src_003.py -v; STAMP=$(date -u +%Y%m%dT%H%M%SZ) FIXTURE=reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt && KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -mat reports/2025-11-source-weights/fixtures/A.mat -sourcefile $FIXTURE -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -floatfile reports/2025-11-source-weights/phase_e/$STAMP/py_tc_d1.bin && NB_RUN_PARALLEL=1 "$NB_C_BIN" -mat reports/2025-11-source-weights/fixtures/A.mat -sourcefile $FIXTURE -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -floatfile reports/2025-11-source-weights/phase_e/$STAMP/c_tc_d1.bin
If Blocked: Capture partial outputs under reports/2025-11-source-weights/phase_e/<STAMP>/attempts/ and log the blocker in docs/fix_plan.md attempts before exiting.
Priorities & Rationale:
- docs/fix_plan.md:4046 aligns Next Actions with TC-D1/TC-D3 parity evidence before downstream plans can move.
- plans/active/source-weight-normalization.md:57 keeps Phase E focused on correlation ≥0.999 and |sum_ratio−1| ≤1e-3 after the Option B fix.
- plans/active/vectorization.md:24 shows VECTOR-TRICUBIC-002 Phase A stays blocked until this parity bundle lands.
- docs/development/testing_strategy.md:28 mandates precise pytest selectors in Do Now and reuse of documented validation scripts.
How-To Map:
- export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md; export KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1.
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p reports/2025-11-source-weights/phase_e/$STAMP.
- KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_src_003.py -v | tee reports/2025-11-source-weights/phase_e/$STAMP/pytest.log; pytest --collect-only -q | tee reports/2025-11-source-weights/phase_e/$STAMP/collect.log.
- Record every shell step in reports/2025-11-source-weights/phase_e/$STAMP/commands.txt (append mode via tee -a).
- For TC-D1 and TC-D3 run both surfaces:
  KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -mat reports/2025-11-source-weights/fixtures/A.mat -sourcefile $FIXTURE -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -floatfile reports/2025-11-source-weights/phase_e/$STAMP/py_tc_d{1,3}.bin | tee reports/2025-11-source-weights/phase_e/$STAMP/py_stdout_tc_d{1,3}.log
  "$NB_C_BIN" -mat reports/2025-11-source-weights/fixtures/A.mat -sourcefile $FIXTURE -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -floatfile reports/2025-11-source-weights/phase_e/$STAMP/c_tc_d{1,3}.bin | tee reports/2025-11-source-weights/phase_e/$STAMP/c_stdout_tc_d{1,3}.log
- Capture simulator diagnostics once via the existing Python snippet (see Phase E2 commands) and save to simulator_diagnostics.txt in the new folder.
- Compute metrics with python - <<'PY' (using numpy to load py/c floatfiles, emit correlation and sum ratio) and tee output to metrics.txt; also write individual values to correlation.txt and sum_ratio.txt.
- Dump `env | sort` to env.json (or python -m json tool) so reruns know versions/path; ensure NB_C_BIN path recorded.
Pitfalls To Avoid:
- Do not change fixtures or geometry parameters; reuse the Phase A TC-D1/TC-D3 inputs verbatim.
- Ensure `$NB_C_BIN` resolves to ./golden_suite_generator/nanoBragg; abort if binary missing instead of switching to fallback silently.
- Use a single STAMP for all artifacts so parity bundles stay coherent.
- Keep UserWarning emission intact—do not filter or silence warnings.warn stacklevel=2.
- Avoid deleting or editing existing reports directories; place new evidence in a fresh timestamped folder.
- Stay device/dtype neutral (CPU only for this loop); no `.cuda()` or dtype casts inside parity commands.
- Update docs/fix_plan attempts only after metrics satisfy thresholds; otherwise log blockers instead of claiming success.
Pointers:
- docs/fix_plan.md:4046
- plans/active/source-weight-normalization.md:57
- plans/active/vectorization.md:23
- docs/development/testing_strategy.md:28
Next Up:
- 1. Update docs/architecture/pytorch_design.md sources section (Phase E4) once parity metrics pass.
- 2. Propagate the unblock to VECTOR-GAPS-002 Phase B and resume profiler capture.
