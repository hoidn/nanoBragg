Summary: Apply the detector cache dtype fix and prove AT-013/024 progress without dtype crashes.
Mode: Parity
Focus: [DTYPE-NEUTRAL-001] dtype neutrality guardrail
Branch: feature/spec-based-2
Mapped tests: tests/test_at_parallel_013.py; tests/test_at_parallel_024.py; tests/test_detector_geometry.py
Artifacts: reports/2026-01-test-suite-triage/phase_d/<STAMP>/dtype-neutral/phase_d/
Do Now: [DTYPE-NEUTRAL-001] Phase D1–D4 — implement the 4-line `Detector` cache dtype fix, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py --maxfail=0 --durations=10 --tb=short`
If Blocked: If the fix location is unclear, rerun the baseline failure (`pytest -v tests/test_at_parallel_013.py --maxfail=1 --tb=short`) and save the log to phase_d/baseline/ for inspection before editing.
Priorities & Rationale:
- plans/active/dtype-neutral.md:40 — Phase D1–D4 require the dtype-coerced cache before determinism work can resume.
- docs/fix_plan.md:520 — Active Next Actions elevate this fix as the gate to unblock `[DETERMINISM-001]`.
- reports/2026-01-test-suite-triage/phase_d/20251010T173558Z/dtype-neutral/phase_b/summary.md — Confirms the 4-line `.to(..., dtype=self.dtype)` change scope.
- reports/2026-01-test-suite-triage/phase_d/20251010T174636Z/dtype-neutral/phase_c/tests.md — Authoritative validation commands and artifact policy.
- docs/development/testing_strategy.md#14-pytorch-device--dtype-discipline — Guardrail demanding CPU/GPU dtype neutrality.
How-To Map:
- Edit `src/nanobrag_torch/models/detector.py` so every cache `.to(self.device)` call (lines ~762-777) specifies `dtype=self.dtype`; invalidate caches if dtype changes.
- After edits, run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py --maxfail=0 --durations=10 --tb=short | tee phase_d_primary_validation.log` and archive under `primary/`.
- Run regression guard: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_detector_geometry.py --durations=10 --tb=short | tee phase_d_regression_check.log` (store under `secondary/`).
- If CUDA available, run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v -m gpu_smoke --tb=short | tee phase_d_gpu_smoke.log` (store under `tertiary/`).
- Summarize results in `reports/.../<STAMP>/dtype-neutral/phase_d/summary.md`, then prepare doc updates listed in `docs_updates.md` for the follow-up phase.
Pitfalls To Avoid:
- Do not leave tensors created with default dtype on CPU while mixing with GPU inputs; keep device-neutral allocations.
- Avoid introducing `.item()` or `.detach()` anywhere in the detector cache code path.
- Preserve cache invalidation semantics; ensure geometry version increments when dtype/device shifts.
- Respect Protected Assets — no edits to files listed in docs/index.md (e.g., loop.sh, input.md).
- Keep artifacts under the specified reports directory; no stray logs in repo root.
- Run only the mapped tests before implementation is complete; defer full suite until cleanup.
Pointers:
- plans/active/dtype-neutral.md:40
- docs/fix_plan.md:520
- reports/2026-01-test-suite-triage/phase_d/20251010T173558Z/dtype-neutral/phase_b/summary.md
- reports/2026-01-test-suite-triage/phase_d/20251010T174636Z/dtype-neutral/phase_c/tests.md
- src/nanobrag_torch/models/detector.py:762
Next Up: Phase G addendum for `[TEST-SUITE-TRIAGE-001]` once dtype fix artifacts land.
