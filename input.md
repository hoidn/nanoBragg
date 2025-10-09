Summary: Validate detector absorption vectorization (Phase F2) and capture CPU/CUDA perf evidence for Phase F3.
Mode: Perf
Focus: VECTOR-TRICUBIC-001 Phase F absorption vectorization
Branch: feature/spec-based-2
Mapped tests: env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_at_abs_001.py
Artifacts: reports/2025-10-vectorization/phase_f/validation/<STAMP>/, reports/2025-10-vectorization/phase_f/perf/<STAMP>/, reports/2025-10-vectorization/phase_f/summary.md
Do Now: VECTOR-TRICUBIC-001 Phase F2 validation – env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_at_abs_001.py
If Blocked: Run pytest --collect-only -q tests/test_at_abs_001.py and log the blocker (traceback, env, hypotheses) in reports/2025-10-vectorization/phase_f/validation/<STAMP>/blocked.md.

Priorities & Rationale:
- docs/fix_plan.md:3364-3378 lists Phase F2–F4 as the remaining blockers; landing validation + perf evidence unblocks Phase F4 closure.
- plans/active/vectorization.md:71-81 records the scope shift (validate existing vectorized path); executing it keeps the plan aligned with real progress.
- reports/2025-10-vectorization/phase_f/design_notes.md:1-140 already defines gradient/device probes we owe evidence for—this loop produces that bundle.
- src/nanobrag_torch/simulator.py:1707-1789 lacks a CLAUDE Rule #11 citation; updating the docstring anchors implementation to nanoBragg.c lines 2890-2920.
- docs/development/pytorch_runtime_checklist.md:1-28 and testing_strategy.md:40-120 demand CPU+CUDA coverage; new parametrised tests must demonstrate compliance.
- reports/2025-10-vectorization/phase_a/absorption_baseline.md:1-120 holds the throughput baseline; Phase F3 benchmarks must compare against it to prove no regressions (>5%).
- scripts/benchmarks/absorption_baseline.py:1-200 is the canonical harness; reusing it avoids ad-hoc benchmarking and keeps PERF initiative metrics comparable.
- PERFPY plan B7 (docs/fix_plan.md Active Focus bullet) still expects compile toggle discipline; keeping NANOBRAGG_DISABLE_COMPILE=1 avoids torch.compile churn during validation.
- Upcoming Phase G documentation updates depend on the validation/perf summaries produced here; capturing detail now shortens the follow-up effort.

How-To Map:
- Pre-flight sanity: env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_at_abs_001.py (store output in validation/commands.txt with timestamp).
- Update `_apply_detector_absorption` docstring to include the exact nanoBragg.c snippet (lines 2890-2920) inside a fenced C block plus AT-ABS-001 reference and vectorization notes.
- Instrument quick tensor shape probes (no code changes, just logged checks) to confirm parallax `(S,F)`, capture `(T,S,F)`, and broadcast behaviour; summarise findings in validation/validation.md.
- Extend tests/test_at_abs_001.py so each test parametrises over device (cpu plus cuda if available) and `oversample_thick` (True/False), using `pytest.mark.parametrize` with conditional skip when CUDA missing.
- After edits, run env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -v tests/test_at_abs_001.py; archive full log, exit code, and env.json (Python version, torch, CUDA availability) under validation/<STAMP>/.
- Benchmark CPU throughput: PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/absorption_baseline.py --sizes 256 512 --thicksteps 5 --repeats 200 --device cpu --outdir reports/2025-10-vectorization/phase_f/perf/<STAMP>/cpu
- Benchmark CUDA throughput: PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/absorption_baseline.py --sizes 256 512 --thicksteps 5 --repeats 200 --device cuda --outdir reports/2025-10-vectorization/phase_f/perf/<STAMP>/cuda
- Record cold vs warm timings, throughput (pixels/sec), and any compile warm-up notes in perf/<STAMP>/perf_summary.md; dump raw stdout/stderr into perf_results.json and commands.txt.
- Draft reports/2025-10-vectorization/phase_f/summary.md covering (1) docstring update, (2) validation findings, (3) benchmark comparison vs Phase A baseline, and (4) parity follow-ups needed for Phase F4.
- Update docs/fix_plan.md Attempts with Attempt ID, pointer to both validation/perf bundles, and pass/fail summaries; mark F2/F3 progress inline and note upcoming F4 tasks.
- Capture a short note in galph_memory.md summarising the new evidence bundles so the next supervisor loop has continuity.

Validation Checklist:
- Confirm `parallax` retains sign and only clamps near ±1e-10; document any pixels hitting the guard and correlate with detector geometry.
- Verify gradients for `detector_abs_um`, `detector_thick_um`, `distance_mm`, and `odet_vec` remain non-None by running small `torch.autograd.grad` probes in a notebook or script and logging results.
- Ensure new parametrised tests respect torch dtype (float32 default) while allowing float64 overrides for gradcheck usage; document dtype handling in validation.md.
- Capture differences between oversample_thick True/False for at least one pixel (ratio, expected inequality) to demonstrate semantics align with AT-ABS-001.
- Include device metadata in env.json (torch.cuda.get_device_name, capability) so benchmark comparisons remain valid across runs.
- Write an "Open Questions" subsection for any outstanding concerns (e.g., need for additional nb-compare evidence or further gradchecks).

Benchmark Reporting:
- List CPU and CUDA cold-start durations separately from warm medians; highlight any compile warm-up overhead if present.
- Compute throughput (pixels/sec) for each detector size and compare to Phase A baseline; flag regressions beyond 5% immediately.
- If CUDA unavailable, record the absence explicitly and skip GPU runs with rationale in perf_summary.md.
- Capture `nvidia-smi --query-gpu=name,utilization.gpu --format=csv` output (if accessible) to confirm GPU utilisation levels.
- Note whether torch.compile graph breaks appear during benchmarks; if they do, include log excerpts and proposed mitigations.
- Store perf commands and outputs with UTC timestamps and SHA256 hashes to keep audit trail reproducible.

Documentation Hooks:
- In summary.md, list any required updates to docs/development/pytorch_runtime_checklist.md or docs/architecture/pytorch_design.md (e.g., note that detector absorption now has explicit CPU/CUDA coverage).
- Flag potential additions for docs/architecture/detector.md (clarifying oversample_thick behaviour) so Phase G can incorporate them quickly.
- If new helper fixtures are created for device parametrisation, mention them along with suggested reuse instructions in summary.md.
- Note whether reports/archive/cli-flags-003/watch.md should start tracking absorption perf metrics as part of the watch cadence.
- Record any insights relevant to PERF-PYTORCH-004 (e.g., compile cache toggles, memory pressure) in summary.md under "Next Steps".

Evidence Logging Steps:
- Within validation/<STAMP>/ create commands.txt, env.json, validation.md, summary.md (if desired), and checksums.txt covering all artifacts.
- Within perf/<STAMP>/ create cpu/ and cuda/ subdirs (when applicable) each with raw logs, commands, env, and checksum entries plus a shared perf_summary.md at the root.
- Use `sha256sum` on logs and JSON outputs; append results to checksums.txt for reproducibility.
- Reference both bundles explicitly in docs/fix_plan.md Attempt log (include timestamped directories and main findings).
- Keep git status clean—stage intentional code/test/doc updates; `.gitignore` already excludes benchmarks outputs so no manual cleanup should be necessary.

Risks & Mitigations:
- If CUDA runtimes regress, capture profiler hints (e.g., torch.autograd.profiler) and propose follow-up tasks rather than ignoring shorter term issues.
- Watch for memory spikes when thicksteps increases; note any need for tiling strategy to avoid OOM on large detectors.
- Ensure tests remain speedy; if parametrisation doubles runtime, consider reducing detector size inside fixtures while preserving physics coverage.
- Maintain compatibility with torch.autograd gradcheck workflows; do not bake compile-specific logic into tests that would break double precision runs.
- If docstring updates risk merge conflict, coordinate with pending branches by highlighting the change in summary.md and Attempt log.

Pitfalls To Avoid:
- Do not reintroduce Python loops or per-layer iteration; keep broadcast vectorisation intact.
- Maintain device/dtype neutrality; avoid `.cpu()`/`.cuda()` calls inside hot paths and allocate new tensors on `intensity.device`.
- Ensure tests skip gracefully when CUDA unavailable; never hard-fail on missing GPU.
- Keep artifacts under reports/2025-10-vectorization/phase_f/; avoid stray files in repo root or /tmp.
- Cite the nanoBragg.c snippet verbatim in the docstring to satisfy CLAUDE Rule #11.
- Use repeats=200 for benchmarks per plan; note cold vs warm stats if they diverge.
- Preserve existing tolerances in tests/test_at_abs_001.py unless deterministic evidence supports changing them.
- Capture env.json for both validation and perf directories; reproducibility is non-negotiable.
- Stick to mapped selectors; no full pytest suites this loop.
- Record all commands with timestamps in commands.txt to keep the audit trail tight.
- Rerun pytest after modifying tests; stale runs are unacceptable as evidence.
- Avoid float64 promotion in production paths; keep runtime dtype float32 unless tests demand otherwise.
- Keep NANOBRAGG_DISABLE_COMPILE=1 during tests to minimise torch.compile churn until PERF plan B7 resolves.
- Do not touch Protected Assets (docs/index.md, loop.sh, supervisor.sh, input.md) beyond this memo.
- Share reusable fixtures/utilities instead of duplicating logic inside tests.
- Double-check that oversample_thick toggles in Simulator.run remain vectorised after your changes.
- Confirm new docstring formatting stays ASCII-only to match repo standards.

Pointers:
- docs/fix_plan.md:3364-3378 — VECTOR-TRICUBIC-001 entry with refreshed Next Actions.
- plans/active/vectorization.md:71-81 — Phase F tasks and scope shift for F2.
- reports/2025-10-vectorization/phase_f/design_notes.md:1-140 — Gradient/device checklist to execute.
- src/nanobrag_torch/simulator.py:1707-1789 — Absorption implementation requiring Rule #11 citation.
- tests/test_at_abs_001.py:1-200 — Current coverage to extend for device + oversample parametrisation.
- scripts/benchmarks/absorption_baseline.py:1-200 — Benchmark harness for perf measurements.
- docs/development/pytorch_runtime_checklist.md:1-28 — Runtime guardrails for device/dtype neutrality.
- docs/development/testing_strategy.md:40-120 — Device testing cadence requirements.
- reports/2025-10-vectorization/phase_a/absorption_baseline.md:1-120 — Baseline throughput numbers.
- docs/architecture/detector.md:150-260 — Detector absorption semantics reference.
- reports/2025-10-vectorization/phase_e/summary.md:1-120 — Template for parity/perf summarisation.
- docs/development/implementation_plan.md:120-200 — Detector work context within roadmap.
- reports/benchmarks/20250930-165726-compile-cache/analysis.md:1-80 — Historical hotspot motivation.
- docs/bugs/verified_c_bugs.md:120-170 — Confirm no C-side quirks need emulation.
- prompts/callchain.md:1-160 — Guidance if additional absorption tap points are needed later.

Next Up:
1. If Phase F2/F3 land quickly, draft Phase F4 nb-compare smoke instructions (CPU first, optional CUDA) using the existing Phase E harness.
2. If time remains, prep notes for Phase G documentation edits—identify exact sections in runtime checklist and architecture docs that will need updates.
3. Optional stretch: outline how absorption benchmarks integrate into PERF-PYTORCH-004 metrics dashboard once this initiative closes.
