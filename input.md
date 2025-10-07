Summary: Vectorize tricubic neighborhood gather per Phase C1 so batched queries stop falling back to nearest-neighbor.
Mode: Perf
Focus: VECTOR-TRICUBIC-001 Vectorize tricubic interpolation and detector absorption
Branch: feature/spec-based-2
Mapped tests:
- env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_matches_scalar -v
- env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_str_002.py::TestTricubicInterpolation::test_tricubic_interpolation_enabled -v
Artifacts:
- reports/2025-10-vectorization/phase_c/implementation_notes.md
- reports/2025-10-vectorization/phase_c/tricubic_gather_diff.json
Do Now: VECTOR-TRICUBIC-001 Phase C1 — implement batched `(B,4,4,4)` tricubic gather in `Crystal._tricubic_interpolation` using the Phase B design memo, then run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_matches_scalar -v` (author the test before running it).
If Blocked: Capture the scalar vs batched output comparison for a 4×4 ROI under `reports/2025-10-vectorization/phase_c/debug/` and note the failure in docs/fix_plan.md Attempt history.
Priorities & Rationale:
- plans/active/vectorization.md:30 — Phase C requires implementing batched gather before polynomial work can begin.
- docs/fix_plan.md:1683 — Next actions demand C1–C3 execution using the new design memo.
- reports/2025-10-vectorization/phase_b/design_notes.md:21 — Two-stage vectorization plan outlines gather expectations and memory envelope.
- docs/development/pytorch_runtime_checklist.md:6 — Guardrails for vectorization and device/dtype neutrality must stay satisfied.
How-To Map:
- Implement gather in `src/nanobrag_torch/models/crystal.py` using advanced indexing per design_notes §2; keep existing nearest-neighbor fallback for empty mask paths.
- Create `tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_matches_scalar` comparing batched vs scalar outputs on a seeded HKL grid; run with `env KMP_DUPLICATE_LIB_OK=TRUE pytest ... -v`.
- Re-run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_str_002.py::TestTricubicInterpolation::test_tricubic_interpolation_enabled -v` to ensure legacy behavior holds.
- Document implementation choices, shapes, and warnings under `reports/2025-10-vectorization/phase_c/implementation_notes.md`; record any numerical deltas in `tricubic_gather_diff.json`.
Pitfalls To Avoid:
- Do not leave `.item()` or `.cpu()` calls inside the batched gather path.
- Keep HKL tensors on the caller’s device; no implicit `.to('cpu')` shortcuts.
- Preserve single-warning behavior when fallbacks trigger.
- Avoid adding ad-hoc scripts outside `scripts/`—reuse existing benchmarks if needed.
- Maintain differentiability; no detached tensors in the gather pipeline.
- Respect Protected Assets; do not move files listed in docs/index.md.
- Run only the mapped selective pytest commands during the loop.
- Ensure torch.compile graph breaks are not introduced; watch console output.
- Keep new tensors contiguous and reuse cached ones where possible.
Pointers:
- plans/active/vectorization.md:30 — Phase C task definitions and exit criteria.
- docs/fix_plan.md:1683 — Current status and next actions for VECTOR-TRICUBIC-001.
- reports/2025-10-vectorization/phase_b/design_notes.md:21 — Gather design and memory guidance.
- docs/development/pytorch_runtime_checklist.md:6 — Vectorization/device checklist referenced by the plan.
Next Up (if time permits): Phase C2 fallback regression + targeted OOB pytest, or resume CLI-FLAGS-003 L3d regression authoring once gather lands.
