Summary: Drive Phase C2 of tricubic vectorization by locking regression coverage for the OOB fallback before moving on to shape assertions.
Mode: Docs
Focus: VECTOR-TRICUBIC-001 Vectorize tricubic interpolation and detector absorption
Branch: feature/spec-based-2
Mapped tests: tests/test_tricubic_vectorized.py::test_oob_warning_single_fire; tests/test_at_str_002.py::test_tricubic_interpolation_enabled
Artifacts: reports/2025-10-vectorization/phase_c/test_tricubic_vectorized.log; reports/2025-10-vectorization/phase_c/implementation_notes.md; reports/2025-10-vectorization/phase_c/status_snapshot.txt; plans/active/vectorization.md; docs/fix_plan.md
Do Now: VECTOR-TRICUBIC-001 Phase C2 — author `tests/test_tricubic_vectorized.py::test_oob_warning_single_fire` to pin the single-warning behavior, then run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::test_oob_warning_single_fire -v`
If Blocked: Run `env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests/test_tricubic_vectorized.py -q`, log the failure plus traceback in `reports/2025-10-vectorization/phase_c/attempt_notes.md`, and note the blocker under docs/fix_plan.md Attempts.

Priorities & Rationale:
- plans/active/vectorization.md:5 — Latest snapshot shows Phase C1 is complete and Phase C2 is the first remaining blocker; executing it keeps the plan on script.
- docs/fix_plan.md:1889 — Next Actions enumerate C2/C3; closing C2 supplies the evidence needed before reshaping caches.
- reports/2025-10-vectorization/phase_b/design_notes.md:52 — Section 2 spells out the `(B,4,4,4)` gather contract that the new test must respect.
- reports/2025-10-vectorization/phase_c/gather_notes.md:63 — Documents current fallback path and warning; leverage those details when codifying the regression.
- docs/development/testing_strategy.md:105 — Reinforces that targeted pytest selectors and logged outputs are mandatory for Tier 1 parity work.
- docs/development/pytorch_runtime_checklist.md:1 — Keep device/dtype neutrality explicit while authoring the test and any helper shims.

How-To Map:
- Inspect `src/nanobrag_torch/models/crystal.py` around the interpolation warning to capture the exact message and flag state (`_interpolation_warning_shown`).
- Draft `tests/test_tricubic_vectorized.py` (new file if absent) with fixtures that trigger one batched interpolation plus a repeat call to assert the warning fires exactly once and interpolation disables thereafter.
- Capture collection evidence first: `env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only tests/test_tricubic_vectorized.py -q` → save to `reports/2025-10-vectorization/phase_c/test_tricubic_vectorized.collect.log`.
- After implementing the test, run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::test_oob_warning_single_fire -v` and store the verbose log at `reports/2025-10-vectorization/phase_c/test_tricubic_vectorized.log`.
- Update `reports/2025-10-vectorization/phase_c/status_snapshot.txt` with a short summary (date, git SHA, warning toggle behavior) and extend `implementation_notes.md` with any helper edits needed for deterministic warning capture.
- When satisfied, append Attempt entry under docs/fix_plan.md referencing the new artifacts and mark Phase C2 as complete in plans/active/vectorization.md.

Pitfalls To Avoid:
- Do not delete or rename any file referenced in docs/index.md (Protected Assets rule).
- No `.item()` or dtype/device hardcoding inside tests or helpers—respect gradient flow even in assertions.
- Avoid adding ad-hoc scripts; reuse `reports/2025-10-vectorization/phase_c/` for logs instead of new directories.
- Keep warning capture deterministic; don’t rely on global stdout without asserting the exact message string.
- Ensure the test leaves global plan state untouched (`Crystal._interpolation_warning_shown` should reset via fixture teardown).
- No broad `pytest -k` sweeps beyond the specified selector without prior supervisor approval.
- Preserve existing Phase C1 artifacts; do not overwrite `gather_notes.md` except to append references if necessary.
- Maintain vectorization — no reintroducing pixel-level Python loops just to exercise the test case.
- Watch for torch.compile graph breaks; report them instead of disabling compile silently.
- Respect repo cleanliness: stage only intentional changes and capture new logs before exiting the loop.

Pointers:
- plans/active/vectorization.md:30 — Phase C task table and artifact expectations.
- docs/fix_plan.md:1889 — Official Next Actions checklist for VECTOR-TRICUBIC-001.
- reports/2025-10-vectorization/phase_b/design_notes.md:122 — Out-of-bounds handling and warning semantics from Phase B design.
- reports/2025-10-vectorization/phase_c/gather_notes.md:92 — Current fallback description plus scalar vs batched behavior notes.
- docs/development/testing_strategy.md:150 — Targeted pytest and artifact logging conventions.
- docs/development/pytorch_runtime_checklist.md:5 — Device/dtype guardrails to cite in implementation notes.

Next Up:
1. Phase C3 — Add shape assertions and device-aware caching once the warning regression is locked.
2. Phase D1 — Begin vectorizing `polint` after C2/C3 evidence is merged and documented.
