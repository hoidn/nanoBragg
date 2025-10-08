Summary: Capture Phase D4 CPU/CUDA pytest evidence for the vectorized tricubic interpolation path and log timings.
Mode: Perf
Focus: VECTOR-TRICUBIC-001 — Phase D4 targeted pytest sweep
Branch: feature/spec-based-2
Mapped tests: tests/test_tricubic_vectorized.py::TestTricubicPoly; tests/test_at_str_002.py::TestStructureFactorInterpolation::test_tricubic_interpolation_enabled
Artifacts: reports/2025-10-vectorization/phase_d/collect.log; reports/2025-10-vectorization/phase_d/pytest_cpu.log; reports/2025-10-vectorization/phase_d/pytest_cuda.log; reports/2025-10-vectorization/phase_d/polynomial_validation.md
Do Now: VECTOR-TRICUBIC-001 Phase D4 – run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::TestTricubicPoly -v` (CPU) and, if available, `CUDA_VISIBLE_DEVICES=0 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::TestTricubicPoly -v` (CUDA); tee outputs to `reports/2025-10-vectorization/phase_d/pytest_{cpu,cuda}.log`, then rerun `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_str_002.py::TestStructureFactorInterpolation::test_tricubic_interpolation_enabled -v` and append timings to `polynomial_validation.md`.
If Blocked: Capture failing command + stderr into `reports/2025-10-vectorization/phase_d/attempt_fail.log`, note device/dtype, and log a blocked Attempt under VECTOR-TRICUBIC-001 in docs/fix_plan.md before pausing.
Priorities & Rationale:
- plans/active/vectorization.md:48-59 promotes Phase D4 as the active gate now that D2 succeeded; evidence must show CPU and CUDA sweeps with timings.
- docs/fix_plan.md:2303-2477 records Attempt #10 and asks for D4 logs plus timing deltas in polynomial_validation.md before moving to Phase E.
- reports/2025-10-vectorization/phase_d/polynomial_validation.md:1-220 outlines the measurement schema (wall-clock, device info, gradcheck notes) that needs updating after each sweep.
- docs/development/testing_strategy.md:66-120 mandates targeted selectors first, dual-device coverage, and logging commands in reports/ for reproducibility.
- docs/development/pytorch_runtime_checklist.md:1-35 reiterates the vectorization + device/dtype neutrality guardrails you must re-confirm while gathering evidence.
How-To Map:
- Refresh selector inventory: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::TestTricubicPoly --collect-only -q > reports/2025-10-vectorization/phase_d/collect.log` (append date stamp inside the file).
- CPU run: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::TestTricubicPoly -v | tee reports/2025-10-vectorization/phase_d/pytest_cpu.log` (include start/end timestamps and elapsed time in the log header).
- CUDA run (if torch.cuda.is_available()): `CUDA_VISIBLE_DEVICES=0 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::TestTricubicPoly -v | tee reports/2025-10-vectorization/phase_d/pytest_cuda.log`.
- Acceptance check: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_str_002.py::TestStructureFactorInterpolation::test_tricubic_interpolation_enabled -v >> reports/2025-10-vectorization/phase_d/pytest_cpu.log`; replicate on CUDA if feasible or note unavailability in polynomial_validation.md.
- Update reports/2025-10-vectorization/phase_d/polynomial_validation.md with a new “Phase D4 execution” subsection summarising command strings, wall-clock timings, device/dtype, and any CUDA availability notes.
- If CUDA unavailable, state that explicitly in polynomial_validation.md and leave placeholder for future run per plan guidance.
- After logs are captured, append a short bullet list in implementation_notes.md highlighting that D4 evidence is complete and referencing the new log filenames.
- Record a new Attempt in docs/fix_plan.md (VECTOR-TRICUBIC-001) with command hashes, obs/metrics (elapsed, pass counts), and confirm plan row D4 now [D].
Pitfalls To Avoid:
- Do not skip the collect-only sanity pass; selector drift must be caught before executing tests.
- Keep environment variables identical across runs (`KMP_DUPLICATE_LIB_OK=TRUE`) to avoid MKL crashes.
- Maintain CPU/CUDA parity where available; note explicitly when CUDA is skipped rather than silently omitting it.
- Avoid overwriting prior logs—use tee with explicit filenames and include timestamps for traceability.
- Do not edit production code or tests this loop; evidence only.
- Ensure pytest exits cleanly (no `nb-compare` or extra suites) to keep logs focused on Phase D4 scope.
- Preserve vectorization assumptions in narrative—no claims about performance until benchmarks (Phase E) run.
- Follow Protected Assets rule; do not relocate or delete files listed in docs/index.md.
- Capture command exit codes if a failure occurs so the blocked Attempt has concrete diagnostics.
Pointers:
- plans/active/vectorization.md:53-58 — Phase D task table with D4 requirements.
- docs/fix_plan.md:2470-2505 — Latest VECTOR-TRICUBIC-001 attempts and expectation to log D4 evidence.
- reports/2025-10-vectorization/phase_d/polynomial_validation.md:1-220 — Measurement template to extend with new timings.
- reports/2025-10-vectorization/phase_d/implementation_notes.md:1-200 — Phase D scratchpad to update after this sweep.
- docs/development/testing_strategy.md:66-120 — Targeted pytest cadence and CPU/CUDA smoke policy.
Next Up: (1) Stage Phase E1 acceptance + regression reruns once D4 logs are in place; (2) Alternatively, prep Phase E benchmarking harness (`scripts/benchmarks/tricubic_baseline.py`) while logs are fresh.
