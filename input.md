Summary: Add per-source TC-D1 trace instrumentation so we can identify the exact physics factors causing the weighted-source parity gap before changing the simulator.
Mode: Parity
Focus: [SOURCE-WEIGHT-001] Phase E — parity instrumentation
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_at_src_003.py
Artifacts: reports/2025-11-source-weights/phase_e/<STAMP>/trace_per_source/
Do Now: [SOURCE-WEIGHT-001] Phase E3 — KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -mat A.mat -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -default_F 100 -hdivsteps 0 -vdivsteps 0 -dispsteps 1 -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -trace_pixel 158 147 -printout -floatfile /tmp/trace_stub.bin > reports/2025-11-source-weights/phase_e/<STAMP>/trace_per_source/py_trace.txt
If Blocked: Capture the failing command, stderr, and any stack trace into reports/2025-11-source-weights/phase_e/<STAMP>/trace_per_source/blocked.log and add a short Attempts History note in docs/fix_plan.md for [SOURCE-WEIGHT-001] before pivoting.
Priorities & Rationale:
- docs/fix_plan.md:4035 keeps Phase E in-progress until TC-D1/TC-D3 parity metrics are trustworthy; without per-source taps we cannot prove where the 47–120× inflation originates.


- plans/active/source-weight-normalization.md:57 explicitly calls for refreshed trace evidence ahead of implementation work, so instrumentation is the immediate gate.


- reports/2025-11-source-weights/phase_e/20251009T195032Z/trace_source2/trace_notes.md already shows polar≈0.9997 vs C=0.5, yet only aggregate values are logged; per-source output is needed to isolate the culprit term.


- specs/spec-a-core.md:150 states that source weights are read but ignored; once normalization matches C, any remaining discrepancy must come from physics factors we are about to log.


- golden_suite_generator/nanoBragg.c:3337 (TRACE_C_SOURCE2) already emits per-source C metrics, so matching PyTorch taps are required for line-by-line comparison.


- src/nanobrag_torch/simulator.py:1240 is the consolidated trace hook; extending it keeps instrumentation aligned with the existing debugging SOP and avoids diverging helper scripts.


- docs/debugging/debugging.md:17 mandates parallel traces before changing physics; landing this evidence is prerequisite to every other SOURCE-WEIGHT-001 Phase E task.


- plans/active/vectorization.md:32 remains blocked on this parity evidence, so closing the instrumentation gap unblocks higher-priority profiling/Perf work once metrics pass.


How-To Map:
- Update src/nanobrag_torch/simulator.py:1240 (`_apply_debug_output`) to detect `self._source_directions` when trace_pixel is active and emit one `TRACE_PY_SOURCE {idx}` block per source containing: source index, source direction, wavelength (Å), F_cell, F_latt_a/b/c, F_latt, polarization factor, I_before_polar, I_after_polar, and contribution before the final steps normalization.


- Preserve existing TRACE_PY lines; append the per-source blocks after the current interpolation section so legacy tooling (diff scripts, reports) still parses earlier entries unchanged.


- When the per-source trace uses tensors, pull scalar values with `.item()` only on debug copies derived from already detached intermediates; never mutate tensors that participate in the compiled graph.


- Touch src/nanobrag_torch/models/crystal.py only if additional per-source metadata is needed; otherwise keep the change scoped to the simulator trace hook.


- Prepare a timestamp for artifacts via `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and create the folder with `mkdir -p reports/2025-11-source-weights/phase_e/$STAMP/trace_per_source` before executing any commands.


- Run `pytest --collect-only -q tests/test_at_src_003.py | tee reports/2025-11-source-weights/phase_e/$STAMP/trace_per_source/pytest_collect.log` to document selector validity without executing the tests.


- Execute the PyTorch trace command from Do Now, redirect stdout to `py_trace.txt`, and capture stderr separately using `2>&1 | tee` if you need both streams for later diffing; record the exact command in `commands.txt` and capture the environment with `python -m json.tool <<<'{}'` style script if helpful.


- Rerun the instrumented C binary: `NB_RUN_PARALLEL=1 "$NB_C_BIN" -mat A.mat -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -default_F 100 -hdivsteps 0 -vdivsteps 0 -dispsteps 1 -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -trace_pixel 158 147 > reports/2025-11-source-weights/phase_e/$STAMP/trace_per_source/c_trace.txt 2> reports/2025-11-source-weights/phase_e/$STAMP/trace_per_source/c_trace.stderr` so the TRACE_C output is preserved verbatim.


- Use the existing diff helper or a simple `python - <<'PY'` script to align per-source blocks: load both traces, find the first mismatching metric, and emit the summary into `diff.txt` plus a narrative in `trace_notes.md` (emphasise step count, polarization, and lattice factor comparisons).


- Update docs/fix_plan.md `[SOURCE-WEIGHT-001]` Attempts with the new STAMP, metrics, and the per-source observation so the ledger shows progress toward Phase E3.


- Leave simulator physics untouched this loop; once evidence exists, the follow-on edit (zero-weight placeholders, polarization fixes) will be trivial to target in the next Do Now.


Pitfalls To Avoid:
- Do not remove or rename any TRACE_PY labels referenced by existing reports; append new ones with a distinct `TRACE_PY_SOURCE` prefix.


- Avoid allocating new tensors inside the compiled region; perform any reshaping or indexing on tensors returned to `_apply_debug_output` to keep torch.compile caches valid.


- Keep all added instrumentation device/dtype neutral—no `.cpu()`, `.cuda()`, or implicit float64 constants.


- Remember to set `KMP_DUPLICATE_LIB_OK=TRUE` for every Python command that imports torch, including trace scripts.


- Do not commit the generated reports directory; reference paths in docs/fix_plan.md instead.


- Prevent `trace_per_source` logs from truncating by redirecting both stdout and stderr explicitly; large traces can exceed buffer limits if piped incorrectly.


- Leave the existing TRACE_C instrumentation intact; if you need additional C fields, add them in a separate loop with supervisor approval.


- Resist the temptation to tweak simulator normalization or polarization while instrumentation is in flight; evidence first, fix second.


- Verify that new logging respects Protected Assets (docs/index.md list) and does not write to any protected file.


- Run only the mapped collect-only pytest command this loop; defer full suite execution until code changes land.


Pointers:
- docs/fix_plan.md:4035


- plans/active/source-weight-normalization.md:57


- reports/2025-11-source-weights/phase_e/20251009T195032Z/trace_source2/trace_notes.md


- src/nanobrag_torch/simulator.py:1240


- golden_suite_generator/nanoBragg.c:3337


- docs/debugging/debugging.md:17


- docs/development/testing_strategy.md:369


Verification Checklist:
- Confirm TRACE_PY_SOURCE blocks exist for every source index and include F_cell, F_latt, and polarization fields.

- Validate the new per-source output keeps the aggregate TRACE_PY values unchanged by running a quick diff on pre-change vs post-change logs.

- Ensure reports/2025-11-source-weights/phase_e/$STAMP/trace_per_source/trace_notes.md summarises the first mismatching variable relative to TRACE_C_SOURCE.

- Re-run the TC-D1 command with NB_RUN_PARALLEL=0 to double-check the PyTorch-only warning path still fires once for wavelength mismatches.


Next Up: Implement zero-weight placeholder counting in simulator steps and re-run TC-D1/TC-D3 parity once the per-source trace confirms the polarization/lattice contributions.
