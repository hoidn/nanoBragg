Summary: Capture per-source parity evidence before touching simulator normalization.
Mode: Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: main
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeightsDivergence
- KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_sourcefile_only_parity
- KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_sourcefile_divergence_warning
- KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_at_src_003.py
- KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_at_src_003.py::TestStepsNormalizationParity::test_steps_count_includes_zero_weight_sources
Artifacts:
- reports/2025-11-source-weights/phase_e/<STAMP>/trace_source2/commands.txt
- reports/2025-11-source-weights/phase_e/<STAMP>/trace_source2/env.json
- reports/2025-11-source-weights/phase_e/<STAMP>/trace_source2/py_trace_source2.txt
- reports/2025-11-source-weights/phase_e/<STAMP>/trace_source2/c_trace_source2.txt
- reports/2025-11-source-weights/phase_e/<STAMP>/trace_source2/diff.txt
- reports/2025-11-source-weights/phase_e/<STAMP>/trace_source2/trace_notes.md
- reports/2025-11-source-weights/phase_e/<STAMP>/design_steps.md
- reports/2025-11-source-weights/phase_e/<STAMP>/metrics_preliminary.json (optional quick ratios)
Do Now: [SOURCE-WEIGHT-001] Correct weighted source normalization — capture TC-D1 source-index trace bundle; validate tooling with `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeightsDivergence` before running the trace commands below.
If Blocked: Record obstacles in trace_source2/attempts.md, archive partial logs in the same <STAMP>, rerun all mapped `pytest --collect-only` selectors to confirm environment, then document the failure signature (command, stderr snippet) in docs/fix_plan.md Attempts.
Priorities & Rationale:
- plans/active/source-weight-normalization.md — Phase E2a complete; Phase E now targets scaling diagnosis + parity metrics.
- docs/fix_plan.md:4043 — Next Actions refreshed to demand placeholder design and source-index tracing prior to code edits.
- specs/spec-a-core.md:145-164 — Normative statement that weight/wavelength columns are ignored; evidence must prove PyTorch honours this once steps parity is resolved.
- golden_suite_generator/nanoBragg.c:2570-2720 — Authoritative source ingestion + steps formula; design memo must map C semantics to PyTorch entry points.
- src/nanobrag_torch/simulator.py:847-874 — Current steps calculation uses `n_sources`; highlight implications in design note without modifying code yet.
- docs/architecture/pytorch_design.md §1.1 — Vectorization rules we must preserve after normalization changes.
- reports/2025-11-source-weights/phase_e/20251009T192746Z/trace/trace_notes.md — Baseline trace showing steps=2 vs 4 and 1.5e8 vs 1.0e5 pre-polar intensity gap; use as comparison reference.
- arch.md §15 — Differentiability guardrails; ensure any proposed placeholder injection keeps tensors differentiable.
How-To Map:
- `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeightsDivergence`
- `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_sourcefile_only_parity`
- `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_sourcefile_divergence_warning`
- `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_at_src_003.py`
- `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_at_src_003.py::TestStepsNormalizationParity::test_steps_count_includes_zero_weight_sources`
- Create design memo scaffold:
-   `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`
-   `mkdir -p reports/2025-11-source-weights/phase_e/$STAMP/trace_source2`
-   `cat <<'DOC' > reports/2025-11-source-weights/phase_e/$STAMP/design_steps.md`
-   `# Placeholder / steps parity
-    ## Goals
-    - Match nanoBragg.c source counting even with sourcefile inputs.
-    - Preserve vectorization + differentiability guardrails.
-    ## C references
-    - golden_suite_generator/nanoBragg.c:2570-2720 (source ingestion)
-    - ...
-    DOC`
- Instrument C trace:
-   Add `if(source==2 && fpixel==trace_fpixel && spixel==trace_spixel){ ... }` block near existing TRACE_C logging to emit `TRACE_C_SOURCE2:` lines for F_cell, F_latt, I_before_scaling, polar, cos2theta, steps.
-   Guard instrumentation with `#ifdef TRACE_PIXEL` if preferred to avoid extraneous logs.
- `make -C golden_suite_generator`
- `export NB_C_BIN=./golden_suite_generator/nanoBragg`
- `export KMP_DUPLICATE_LIB_OK=TRUE`
- Run PyTorch trace:
-   `python -m nanobrag_torch -mat A.mat -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -default_F 100 -hdivsteps 0 -vdivsteps 0 -dispsteps 1 -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -trace_pixel 158 147 -floatfile reports/2025-11-source-weights/phase_e/$STAMP/trace_source2/py_tc_d1.bin > reports/2025-11-source-weights/phase_e/$STAMP/trace_source2/py_trace_source2.txt 2>&1`
- Run C trace:
-   `NB_RUN_PARALLEL=1 "$NB_C_BIN" -mat A.mat -sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt -default_F 100 -hdivsteps 0 -vdivsteps 0 -dispsteps 1 -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -trace_pixel 158 147 -floatfile reports/2025-11-source-weights/phase_e/$STAMP/trace_source2/c_tc_d1.bin > reports/2025-11-source-weights/phase_e/$STAMP/trace_source2/c_trace_source2.txt 2>&1`
- Generate diff:
-   `python scripts/compare_c_python_traces.py --py reports/2025-11-source-weights/phase_e/$STAMP/trace_source2/py_trace_source2.txt --c reports/2025-11-source-weights/phase_e/$STAMP/trace_source2/c_trace_source2.txt > reports/2025-11-source-weights/phase_e/$STAMP/trace_source2/diff.txt`
- Update trace notes:
-   Include per-source steps, polarization, I_before_scaling values, their ratios, and initial hypotheses (e.g., polarization mismatch, structure-factor sampling differences).
- Optional quick metrics:
-   `python scripts/create_diagnosis_summary.py --py reports/2025-11-source-weights/phase_e/$STAMP/trace_source2/py_trace_source2.txt --c reports/2025-11-source-weights/phase_e/$STAMP/trace_source2/c_trace_source2.txt --out reports/2025-11-source-weights/phase_e/$STAMP/trace_source2/metrics_preliminary.json`
- Update docs/fix_plan.md Attempts with <STAMP>, commands, headline findings.
- Restore nanoBragg.c instrumentation to minimal form (leave comments) once logs captured.
- Keep git staging limited to intended files (`golden_suite_generator/nanoBragg.c`, design_steps.md, trace_notes, docs updates).
Pitfalls To Avoid:
- Do not remove existing trace instrumentation; append additional prefixes instead.
- Keep device/dtype neutrality in any temporary PyTorch logging (no unconditional `.cpu()` / `.cuda()` inside compiled paths).
- Preserve Protected Assets listed in docs/index.md when staging artifacts or editing scripts.
- Resist editing simulator normalization logic until trace_summary narrative is complete and reviewed.
- Always rebuild `golden_suite_generator/nanoBragg` after modifying C instrumentation.
- Capture env.json, commands.txt, and metrics files for every new <STAMP> to keep parity runs reproducible.
- Do not commit binary outputs; reference paths only in docs/fix_plan attempts.
- Respect vectorization guardrails—no Python loops added when logging per-source data.
- Keep TRACES scoped to the single pixel; revert instrumentation before committing upstream changes.
- Ensure warnings from the CLI remain intact; do not silence the existing Option B guard.
- Verify each mapped `pytest --collect-only` selector succeeds before and after instrumentation changes.
- Watch for torch.compile cache warnings; if encountered, set `TORCH_LOGS=+dynamo` temporarily and include note in trace_notes.
- Avoid changing fixture files in `reports/2025-11-source-weights/phase_a/`; treat them as read-only inputs.
- When writing design_steps.md, cite exact file:line anchors (nanoBragg.c 2570-2720, simulator.py 847-874) to align with Rule 11.
Pointers:
- plans/active/source-weight-normalization.md
- docs/fix_plan.md:4043
- specs/spec-a-core.md:145-164
- golden_suite_generator/nanoBragg.c:2570-2720
- src/nanobrag_torch/simulator.py:847-874
- docs/architecture/pytorch_design.md §1.1
- arch.md §15
- reports/2025-11-source-weights/phase_e/20251009T192746Z/trace/trace_notes.md
- reports/2025-11-source-weights/phase_d/20251009T104310Z/summary.md (acceptance harness context)
- docs/development/testing_strategy.md §1.4 (device/dtype expectations)
Next Up:
1. Synthesize hypotheses and update trace_notes summary once source-index evidence is captured (prep for simulator normalization/design changes).
2. Review design_steps.md with galph before implementing placeholder injection or polarization fixes.
3. Queue parity rerun (TC-D1/TC-D3) only after hypotheses narrow the 1.5e8 vs 1.0e5 gap.
4. Draft implementation checklist for simulator adjustments based on the agreed design (include tests, trace reruns, docs updates).
5. Once parity succeeds, propagate metrics to `[VECTOR-GAPS-002]` and `[VECTOR-TRICUBIC-002]` to unblock profiling backlog.
6. Schedule follow-up collect-only proof once instrumentation is removed to ensure no stray trace statements remain.
