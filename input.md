Summary: Fix simulator device placement so CUDA vectorization tests run clean and unblock Phase H closure.
Mode: Parity
Focus: [PERF-PYTORCH-004] Fuse physics kernels
Branch: feature/spec-based-2
Mapped tests: pytest tests/test_tricubic_vectorized.py -v -k cuda | pytest tests/test_at_abs_001.py -v -k cuda
Artifacts: reports/2025-10-vectorization/phase_h/<STAMP>/{commands.txt,env.json,pytest_logs/,benchmarks/}
Do Now: [PERF-PYTORCH-004] Fuse physics kernels — after device-placement fix run KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py -v -k cuda
If Blocked: Capture the failing CUDA traceback plus `torch.cuda.is_available()` status under reports/2025-10-vectorization/phase_h/<STAMP>/attempts/ with commands.txt and env.json, then note the blocker in docs/fix_plan.md Attempts before pausing.
Priorities & Rationale:
- plans/active/vectorization.md:91 – Phase H requires clearing the device-placement blocker before CUDA reruns.
- docs/fix_plan.md:3405 – Next Actions tie CUDA evidence to PERF-PYTORCH-004 Attempt #14 device fix.
- docs/development/pytorch_runtime_checklist.md:12 – Enforces device/dtype neutrality when touching simulator init paths.
- src/nanobrag_torch/simulator.py:505 – Current `torch.tensor(...)` path pins `incident_beam_direction` on CPU, breaking CUDA tests.
- reports/2025-10-vectorization/phase_f/summary.md:84 – Documents the existing CUDA failures and expected rerun commands post-fix.
How-To Map:
- Implementation: Ensure `Simulator.__init__` materialises `incident_beam_direction`, `beam_vector`, and related constants on `self.device` (reuse detector/crystal tensor devices). Replace raw `torch.tensor(...)` with `torch.as_tensor(..., device=device, dtype=dtype)` or existing cached tensors; update any caches touched by `_compute_physics_for_position` so they stay device-neutral.
- Smoke check: `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` before running CUDA selectors to confirm import health.
- CUDA tests: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py -v -k cuda` then `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_abs_001.py -v -k cuda`; store logs under phase_h/<STAMP>/pytest_logs/.
- Benchmarks: After tests pass, capture `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/tricubic_baseline.py --sizes 256 512 --repeats 200 --device cuda` and `python scripts/benchmarks/absorption_baseline.py --sizes 256 512 --thicksteps 5 --repeats 200 --device cuda`; save outputs to phase_h/<STAMP>/benchmarks/ with env snapshot.
- Documentation: Update docs/fix_plan.md [VECTOR-TRICUBIC-001] Attempt #18 with CUDA metrics and note the device-placement resolution; refresh the plan status snapshot if all Phase H tasks complete.
Pitfalls To Avoid:
- Do not introduce `.cpu()`/`.cuda()` calls inside hot loops; move tensors to the correct device once at construction.
- Avoid reintroducing Python loops or breaking existing vectorized broadcasts.
- Preserve gradient flow (no `.item()` / `.detach()` on tensors propagated to physics kernels).
- Keep CUDA skips conditional (use pytest skipif) rather than hard-failing when GPUs absent.
- Ensure cached tensors respect dtype overrides (float64 grad checks still need to work).
- Leave trace/instrumentation hooks intact; adjust only the data placement.
- Capture collect-only proof before targeted CUDA runs to document selector validity.
- Respect Protected Assets (docs/index.md) when editing documentation.
Pointers:
- plans/active/vectorization.md:91
- docs/fix_plan.md:3405
- docs/development/pytorch_runtime_checklist.md:12
- reports/2025-10-vectorization/phase_f/summary.md:84
- src/nanobrag_torch/simulator.py:505
Next Up: 1) Re-run vectorization CPU benchmarks for regression after CUDA fix; 2) Kick `plans/active/vectorization-gap-audit.md` Phase B2 once parity ≥0.99 on GPU.
