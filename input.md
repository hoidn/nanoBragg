Summary: Implement batched polint/polin2/polin3 so tricubic interpolation stops falling back to nearest-neighbour.
Mode: Perf
Focus: VECTOR-TRICUBIC-001 — Phase D2 polynomial vectorization
Branch: feature/spec-based-2
Mapped tests: tests/test_tricubic_vectorized.py::TestTricubicPoly; tests/test_at_str_002.py::TestStructureFactorInterpolation::test_tricubic_interpolation_enabled
Artifacts: reports/2025-10-vectorization/phase_d/collect.log; reports/2025-10-vectorization/phase_d/pytest_cpu_pass.log; reports/2025-10-vectorization/phase_d/pytest_cuda_pass.log; reports/2025-10-vectorization/phase_d/summary.md; reports/2025-10-vectorization/phase_d/implementation_notes.md
Do Now: VECTOR-TRICUBIC-001 Phase D2 – land vectorized polint/polin2/polin3 and rewire Crystal._tricubic_interpolation; then run KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::TestTricubicPoly -v
If Blocked: Capture the precise failure output + command into reports/2025-10-vectorization/phase_d/attempts.md and log a “blocked” Attempt for VECTOR-TRICUBIC-001 in docs/fix_plan.md before stopping.
Priorities & Rationale:
- reports/2025-10-vectorization/phase_d/polynomial_validation.md §2–§4 define tensor shapes, batching, and gradcheck tolerances for Phase D2.
- plans/active/vectorization.md:56-92 keeps Phase D tasks sequenced (D1 done, D2 now active, D3 already xfail tests, D4 validation next).
- docs/development/pytorch_runtime_checklist.md:1-29 enforces vectorization and device/dtype neutrality guardrails you must honour.
- specs/spec-a-core.md:205-230 mandates true tricubic interpolation (no nearest-neighbour fallback) for structure-factor sampling.
- docs/development/testing_strategy.md:1-120 requires targeted pytest selectors and dual CPU/CUDA smoke evidence for math-path edits.
- src/nanobrag_torch/models/crystal.py:360-470 currently warns and falls back when B>1; D2 must replace that branch with the vectorized path.
How-To Map:
- Add `polint_vectorized`, `polin2_vectorized`, `polin3_vectorized` to src/nanobrag_torch/utils/physics.py adjacent to scalar helpers, each with CLAUDE Rule #11 C-code docstrings quoting the nanoBragg.c snippets (lines 4150-4187).
- Use broadcasted tensor algebra (no Python loops): operate on `(B,4)` coordinate tensors and `(B,4,4,4)` neighborhoods; rely on worksheet Table 2.1 for shape math and reuse `torch.linalg` primitives to keep grad paths intact.
- Preserve scalar helpers for single-point callers but have new vectorized versions invoked from Crystal._tricubic_interpolation; ensure they accept float32/float64, CPU/CUDA tensors without implicit transfers.
- Update Crystal._tricubic_interpolation to call the vectorized helpers when `B > 1`, remove the temporary nearest-neighbour fallback/warning, and reshape `(B,)` output back to the original detector grid shape.
- Refresh reports/2025-10-vectorization/phase_d/implementation_notes.md with sections covering: shape handling, masking/denominator safety, gradcheck strategy, device/dtype validation.
- Re-run collect evidence: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::TestTricubicPoly --collect-only -q > reports/2025-10-vectorization/phase_d/collect.log` before executing the suite.
- After implementation run targeted CPU command (`KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::TestTricubicPoly -v | tee reports/2025-10-vectorization/phase_d/pytest_cpu_pass.log`) and, if CUDA available, `CUDA_VISIBLE_DEVICES=0 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py::TestTricubicPoly -v -k cuda | tee reports/2025-10-vectorization/phase_d/pytest_cuda_pass.log`.
- Follow up with the AT acceptance selector (`KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_str_002.py::TestStructureFactorInterpolation::test_tricubic_interpolation_enabled -v`) and append its log excerpt plus timing deltas to reports/2025-10-vectorization/phase_d/summary.md.
- Document gradients by running `python - <<'PY'` snippets or rely on the gradcheck tests (now expected to pass); mention success in implementation_notes.md and record epsilon/atol used.
- Update docs/fix_plan.md (VECTOR-TRICUBIC-001) with a new Attempt capturing SHA, commands, metrics (runtime deltas, correlation), and link to the report directory; mark plan row D2 as [D].
Pitfalls To Avoid:
- Do not use explicit Python for-loops over batch elements; rely on broadcasting and tensor contractions.
- Avoid `.item()`, `.detach()`, or `.cpu()` on tensors flowing through gradients.
- Keep tensors on caller device/dtype—no hidden `.to(self.device)` inside helpers beyond aligning constant tensors.
- Ensure denominator guards mirror the scalar implementation’s numerical stability; use `torch.where` instead of manual eps injections that break graph gradients.
- Maintain torch.compile compatibility (no data-dependent control flow that triggers graph breaks).
- Preserve existing scalar API signatures so other call sites remain untouched.
- Keep warnings suppressed once vector path is active; remove the temporary nearest-neighbour warning block.
- Respect Protected Assets; do not relocate files referenced in docs/index.md.
- Re-run `pytest --collect-only` before targeted runs to confirm selector stability.
- Capture environment metadata (Python, torch, CUDA) into reports/2025-10-vectorization/phase_d/env.json if versions changed.
Pointers:
- src/nanobrag_torch/utils/physics.py:315-443 — Current scalar polynomial helpers needing vectorized counterparts.
- src/nanobrag_torch/models/crystal.py:356-470 — Batched gather output and fallback branch to replace.
- tests/test_tricubic_vectorized.py:332-735 — xfail suite that will start passing once vector helpers land.
- reports/2025-10-vectorization/phase_d/polynomial_validation.md:1-220 — Shape design, gradcheck requirements, and tap-point notes.
- plans/active/vectorization.md:57-110 — Phase D checklist ensuring D2 feeds into D4 validation.
Next Up: After D2 passes, move to Phase D4 (rerun targeted pytest on CPU/CUDA, capture timings) or kick off Phase E1 acceptance + nb-compare perf sweep once evidence is archived.
