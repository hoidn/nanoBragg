Summary: Capture CPU/GPU parity evidence for the vectorized tricubic path to unlock Phase E.
Mode: Perf
Focus: VECTOR-TRICUBIC-001 — Phase E1 parity/perf validation kickoff
Branch: feature/spec-based-2
Mapped tests: tests/test_tricubic_vectorized.py; tests/test_at_str_002.py
Artifacts: reports/2025-10-vectorization/phase_e/collect.log; reports/2025-10-vectorization/phase_e/pytest_cpu.log; reports/2025-10-vectorization/phase_e/pytest_cuda.log; reports/2025-10-vectorization/phase_e/env.json
Do Now: VECTOR-TRICUBIC-001 Phase E1 — KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py tests/test_at_str_002.py -v
If Blocked: Run KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests/test_tricubic_vectorized.py tests/test_at_str_002.py -q | tee reports/2025-10-vectorization/phase_e/collect.log, log the failure + hypothesis in docs/fix_plan.md Attempt history, and stop.
Priorities & Rationale:
- docs/fix_plan.md:2369 flags Phase E as the current gate after Phase D completion; logs now need to move under phase_e/.
  Revisit this paragraph when logging the Attempt so the status snapshot remains accurate.
- plans/active/vectorization.md:1 updates the status snapshot to “Phases A–D complete; Phase E pending”, so E1 must land before microbenchmarks can proceed.
  Without these artifacts the plan cannot progress to E2/E3 tasks.
- docs/development/testing_strategy.md:17 mandates device/dtype neutrality checks on CPU and CUDA before claiming success.
  Use parameterised test outputs to show both devices are executing without unexpected skips.
- docs/development/pytorch_runtime_checklist.md:8 requires capturing GPU smoke evidence whenever tensor math paths change.
  Cite the checklist explicitly in the Attempt to demonstrate compliance with runtime guardrails.
- specs/spec-a-parallel.md:220 enforces tricubic acceptance tolerances (corr ≥ 0.9995) that the Phase E summary must cite.
  Keep these thresholds handy when interpreting parity metrics later in Phase E3.
- reports/2025-10-vectorization/phase_d/polynomial_validation.md:1 already tracks Phase D metrics; Phase E evidence must append to that log for audit continuity.
  Add a new subsection referencing `phase_e/pytest_cpu.log` and `phase_e/pytest_cuda.log` once the runs complete.
- arch.md:94 keeps vectorization an explicit ADR; running the acceptance tests now verifies the ADR remains true after the new batched helpers landed.
  Mention ADR-11 in the Attempt summary to connect architecture intent with observed behaviour.
- specs/spec-a-core.md:205 spells out the φ loop ordering that the tricubic path uses; confirming unchanged behaviour ensures we stay within spec after vectorization.
  If failures appear, reread this spec section to confirm the rotation pipeline is still compliant.
- reports/2025-10-vectorization/phase_d/env.json preserves the baseline environment snapshot from Phase D.
  Mirroring its format in Phase E ensures reviewers can diff environments quickly.
How-To Map:
- mkdir -p reports/2025-10-vectorization/phase_e and clear stale logs before starting.
  Remove any prior scratch logs so the new evidence set is unambiguous.
- Run the Do Now command first, piping output to tee to populate reports/2025-10-vectorization/phase_e/pytest_cpu.log.
  Keep the raw terminal output as well in case additional parsing is needed later.
- Re-run with CUDA by prefixing `CUDA_VISIBLE_DEVICES=0 PYTORCH_TEST_DEVICE=cuda` (or the project’s preferred override) and tee to reports/2025-10-vectorization/phase_e/pytest_cuda.log; note skipped tests if GPU unavailable.
  Annotate the top of the log with a short comment explaining why skips occurred, if any.
- Capture collection metadata via `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests/test_tricubic_vectorized.py tests/test_at_str_002.py -q > reports/2025-10-vectorization/phase_e/collect.log`.
  This establishes the selector list for the Attempt record without executing the tests again.
- Record environment details by reusing the Phase D inline snippet (`python - <<'PY' ... PY`) and redirecting it to reports/2025-10-vectorization/phase_e/env.json so the format stays consistent.
  Ensure the snippet prints Python, PyTorch, CUDA availability, and commit SHA if convenient.
- After runs, annotate timings/tensors in reports/2025-10-vectorization/phase_d/polynomial_validation.md for continuity, noting new Phase E evidence paths.
  Append references near the top of the Phase E section so reviewers see them immediately.
- Append brief command provenance into reports/2025-10-vectorization/phase_e/README.md (create if absent) so later reviewers can replay E1 without hunting through logs.
  Include both CPU and CUDA command variants verbatim in that README.
- Diff the new `pytest_cpu.log` against Phase D equivalents to highlight any warning text changes before filing the Attempt entry.
  Capture the diff output (or note "no diff") in the Attempt narrative to document diligence.
- If CUDA skips occur, capture `nvidia-smi` output into reports/2025-10-vectorization/phase_e/nvidia_smi.txt to document availability status.
  Mention this file in the Attempt entry when explaining any skipped tests.
- Once logs exist, sha256sum all artifacts in phase_e/ and stash the hash listing alongside the env file for reproducibility.
  Follow the Phase D naming convention (`sha256.txt`) so tooling recognises it automatically.
- After recording hashes, update docs/fix_plan.md Attempt draft with placeholder bullet points so nothing is forgotten when the Run completes.
  This keeps the log while context is still fresh.
Pitfalls To Avoid:
- Do not regress vectorization by toggling nearest-neighbour fallbacks; keep batched helpers active.
  Any reinstated fallback will reintroduce the warnings that Phase D removed.
- No `.to()`/`.cpu()` calls inside hot loops—maintain device/dtype neutrality per runtime checklist.
  Introduce conversions outside the compiled region if temporary coercion is needed.
- Avoid overwriting Phase D artifacts; store new logs exclusively under phase_e/.
  If reruns are required, version the filenames with timestamps instead of clobbering evidence.
- Keep CUDA run even if tests skip; document skips explicitly in the log and fix_plan Attempt notes.
  Skipping documentation is treated as lack of evidence, so capture the reason in writing.
- Ensure KMP_DUPLICATE_LIB_OK remains set for every pytest/benchmark invocation.
  Missing the variable can crash mid-run, wasting time and producing partial logs.
- Don’t loosen tricubic tolerances; if assertions fail, investigate rather than patching tests.
  Loosened tolerances hide regressions and contradict the spec baseline set in Phase D.
- Maintain clean working tree; no ad-hoc script copies outside scripts/ or reports/.
  Temporary scripts should live inside reports/phase_e if they must exist at all.
- Follow CLAUDE Rule #11 if additional instrumentation is required—quote nanoBragg.c before coding.
  This protects future parity debugging from drifting away from the C reference.
- Refrain from running full pytest suite; stay targeted per testing_strategy.md.
  Save time and keep logs focused on the selectors tied to this plan item.
- Do not modify `tests/test_tricubic_vectorized.py` expectations; the goal is evidence gathering, not behaviour change this loop.
  Any behavioural edits would need separate supervisor approval and likely delay Phase E progress.
- Resist the urge to start Phase E2 benchmarks before attaching E1 logs, otherwise the performance data lacks a validated baseline.
  The plan makes Phase E2 contingent on E1 artifacts—respect that gating.
- Capture gradcheck failures verbatim if they surface; rerunning without fixing root causes hides real regressions.
  Include failing stack traces in reports/phase_e/debug.log if encountered.
Pointers:
- docs/fix_plan.md:2369 — VECTOR-TRICUBIC-001 entry with refreshed Next Actions.
  Reference this section when logging progress so the plan ledger stays synchronised.
- plans/active/vectorization.md:48 — Phase E task table detailing E1–E3 deliverables.
  Double-check the exit criteria there before marking any row as done.
- reports/2025-10-vectorization/phase_d/polynomial_validation.md:1 — Prior evidence context; append Phase E notes here after runs.
  Add a "Phase E1" subsection with bullet links to each new artifact.
- docs/development/pytorch_runtime_checklist.md:1 — Device/dtype guardrails to cite in Attempt summary.
  Mention the checklist item numbers to prove compliance.
- specs/spec-a-core.md:200 — Normative tricubic/phi loop context underpinning the acceptance thresholds.
  Useful if parity metrics look off; reconfirm the rotation pipeline from the spec.
- docs/architecture/pytorch_design.md:70 — Broadcast strategy reminders when interpreting parity logs.
  The tensor-shape diagrams help decode per-batch logging output.
- reports/2025-10-vectorization/phase_d/pytest_d4_cpu.log:1 — Reference log for expected pass output format.
  Use it as a baseline to spot warning text regressions.
- docs/development/testing_strategy.md:32 — Guidance on logging targeted pytest selectors in Attempt entries.
  Align the Attempt narrative with these requirements for future audits.
- reports/2025-10-vectorization/phase_e — Directory that will host the new CPU/GPU logs and metadata.
  Keep the structure consistent (logs, env, hashes, README) to simplify later reviews.
Next Up:
- Phase E2 microbenchmark sweep with scripts/benchmarks/tricubic_baseline.py once E1 logs are committed.
  Capture both CPU and CUDA runs, then compare against Phase A metrics before logging Attempt.
- Phase E3 parity/perf summary consolidation (nb-compare optional) before moving into Phase F planning.
  Draft summary.md alongside fix_plan updates so the documentation trail stays tight.
- Phase F1 design prep once Phase E closes, focusing on detector absorption batching strategy and doc references.
  Start sketching tensor layouts so the follow-on loop can move immediately into implementation.
