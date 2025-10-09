Summary: Vectorize source-grid generation so divergence/dispersion sampling stops burning 120ms per call.
Mode: Perf
Focus: [PERF-PYTORCH-004] Fuse physics kernels
Branch: feature/spec-based-2
Mapped tests: env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_divergence_culling.py -v
Artifacts: reports/2025-10-vectorization/gaps/20251009T061928Z/analysis.md; reports/2025-10-vectorization/gaps/20251009T061928Z/generate_sources_timing.txt
Do Now: [PERF-PYTORCH-004] Fuse physics kernels — batch `generate_sources_from_divergence_dispersion`; then run env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_divergence_culling.py -v (record logs under reports/ with new timestamp).
If Blocked: Capture fresh timing log with the existing script and note counts/latency under Attempts History; stop before code edits if rotation math is unclear.
Priorities & Rationale:
- src/nanobrag_torch/utils/auto_selection.py:220 — triple nested loops for divergence × dispersion; profiling shows 0.12s per call (Goal 2 blocker).
- docs/architecture/pytorch_design.md:3 — vectorization mandate; new flow must extend broadcast shapes instead of loops.
- docs/development/pytorch_runtime_checklist.md:6 — first guardrail forbids reintroducing Python loops; cite evidence bundle after refactor.
- plans/active/perf-pytorch-compile-refactor/plan.md — Phase roadmap needs this win before moving deeper into kernel fusion.
- reports/2025-10-vectorization/gaps/20251009T061928Z/analysis.md — baseline measurement + remediation sketch to validate improvements.
How-To Map:
- Implement batched angle mesh using torch.linspace/broadcast; replace append/stack patterns inside `generate_sources_from_divergence_dispersion`.
- Preserve dtype/device neutrality by deriving tensors from `beam_direction`/`polarization_axis`; add optional inputs for caller-provided tensors.
- Recompute vertical_axis once; use rotate_axis or manual Rodrigues formula with tensors (no Python loops).
- Benchmark with `python reports/2025-10-vectorization/gaps/20251009T061928Z/generate_sources_timing.txt` command body (update path for new timestamp); target ≥10× speedup for 25×25×9 case.
- After edits, run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_divergence_culling.py -v`; store stdout + collect-only proof under a new `reports/2025-10-vectorization/gaps/<stamp>/`.
- Update docs/fix_plan.md Attempt for [PERF-PYTORCH-004] with metrics + artifact paths; reference plan section once new timings recorded.
Pitfalls To Avoid:
- Do not change sampling semantics (counts/range/round_div); parity with tests/spec must hold.
- Keep dtype/device neutral; no hard-coded `.cpu()` or float literals without casting.
- Avoid torch.linspace with tensor endpoints if gradients needed; prefer manual arange math.
- Maintain Protected Assets (leave docs/index.md references untouched).
- Don’t regress CLI order or auto-selection defaults; run pytest before committing.
- Capture commands and timings in reports; no ad-hoc scripts outside reports/ tree.
- Respect vectorization checklists: no per-source Python loops once refactor lands.
- Keep git history clean; document Attempt in fix_plan before closing the loop.
Pointers:
- src/nanobrag_torch/utils/auto_selection.py:220 — current loop implementation.
- docs/architecture/pytorch_design.md:3 — vectorization strategy overview.
- docs/development/pytorch_runtime_checklist.md:6 — enforcement checklist.
- plans/active/perf-pytorch-compile-refactor/plan.md — initiative context.
- tests/test_divergence_culling.py:18 — regression coverage for divergence grids.
- reports/2025-10-vectorization/gaps/20251009T061928Z/analysis.md — baseline evidence + goals.
Next Up: Prototype GPU benchmarking once CPU batch path lands; reuse timing harness with `--device cuda` after device-placement blocker clears.
