Summary: Land Phase C3 by hardening tricubic gather assertions and cache device handling so Phase D polynomial work starts on a clean base.
Mode: Perf
Focus: VECTOR-TRICUBIC-001 Vectorize tricubic interpolation and detector absorption — Phase C3
Branch: feature/spec-based-2
Mapped tests: tests/test_tricubic_vectorized.py -k "gather"; tests/test_at_str_002.py::test_tricubic_interpolation_enabled
Artifacts: reports/2025-10-vectorization/phase_c/test_tricubic_vectorized.log
Artifacts: reports/2025-10-vectorization/phase_c/test_at_str_002_phi.log
Artifacts: reports/2025-10-vectorization/phase_c/implementation_notes.md
Artifacts: plans/active/vectorization.md
Artifacts: docs/fix_plan.md
Do Now: VECTOR-TRICUBIC-001 Phase C3 — add the gather shape assertions + device-aware cache adjustments in Crystal._tricubic_interpolation, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py -k "gather" -v` to confirm the path stays green and capture the log under reports/2025-10-vectorization/phase_c/.
If Blocked: If assertions or cache updates trip device/dtype mismatches, drop into `python -m pdb src/nanobrag_torch/models/crystal.py` with a minimal batched call (see tests/test_tricubic_vectorized.py::TestTricubicGather::test_vectorized_matches_scalar) and log the failing tensor shapes/devices in reports/2025-10-vectorization/phase_c/debug_notes.md before undoing the partial change.
Priorities & Rationale:
- plans/active/vectorization.md:5-18 — snapshot now singles out C3 as the remaining Phase C blocker before polynomial vectorization.
- plans/active/vectorization.md:37-52 — C3 row + checklist define concrete evidence (assertions, cache audit, pytest logs) required before Phase D starts.
- docs/fix_plan.md:1989-2005 — Next Actions demand C3 completion plus recorded pytest output ahead of the Attempt update.
- reports/2025-10-vectorization/phase_c/implementation_notes.md:15-120 — current notes cover C1; extend with the C3 audit so plan/fix_plan can cite the line numbers.
- specs/spec-a-core.md:230-312 — interpolation contract insists on metric duality; shape assertions prevent silent regressions when batching polynomials later.
How-To Map:
- `pytest --collect-only tests/test_tricubic_vectorized.py -q | tee reports/2025-10-vectorization/phase_c/collect_gather.log`
- `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py -k "gather" -v | tee reports/2025-10-vectorization/phase_c/test_tricubic_vectorized.log`
- `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_str_002.py::test_tricubic_interpolation_enabled -v | tee reports/2025-10-vectorization/phase_c/test_at_str_002_phi.log`
- Update `reports/2025-10-vectorization/phase_c/implementation_notes.md` with a “Phase C3 updates” section summarising assertion lines, cache audit, and device checks.
- Flip checklist items C3.1–C3.3 to ✅ in plans/active/vectorization.md and log the Attempt in docs/fix_plan.md with command outputs + SHA256 hashes of the two pytest logs.
Pitfalls To Avoid:
- Do not reintroduce `.cpu()` or `.numpy()` when touching cache tensors; always use `.type_as(sample)` per CLAUDE Rule #16.
- Keep assertions lightweight (boolean checks) so they do not execute data-dependent Python loops over batch elements.
- Maintain differentiability—no `.item()` on tensors involved in interpolation; rely on `.shape` and `.ndim` properties instead.
- Preserve device neutrality in tests by guarding CUDA cases with `torch.cuda.is_available()`.
- Respect Protected Assets: stay within reports/2025-10-vectorization/phase_c/ for new evidence, and leave docs/index.md untouched.
- Run only the targeted selectors above; defer full pytest to the end of the coding loop if additional files change.
- Avoid editing polynomial helpers yet; Phase D will handle `polint`/`polin2`/`polin3` after C3 is closed.
- Keep log filenames consistent with prior attempts so history tools stay diffable.
- Ensure new assertions are gated behind feature flags if they would fire during unit tests without interpolation enabled.
- No ad-hoc scripts in repo root—reuse existing tests for reproduction.
Pointers:
- plans/active/vectorization.md:33-64 (Phase C table and C3 checklist)
- docs/fix_plan.md:1989-2005 (VECTOR-TRICUBIC-001 next actions)
- reports/2025-10-vectorization/phase_c/implementation_notes.md:15-120 (current gather notes to extend)
- tests/test_tricubic_vectorized.py:180-314 (existing gather tests used for evidence)
- src/nanobrag_torch/models/crystal.py:355-460 (tricubic gather implementation and cache handling)
Next Up: Phase D1 — vectorize `polint` once C3 artifacts and Attempt entry are committed.
