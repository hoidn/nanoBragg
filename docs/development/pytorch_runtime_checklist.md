# PyTorch Runtime Checklist

Use this quick checklist before and after every PyTorch simulator edit. It distills the authoritative guidance from
`docs/architecture/pytorch_design.md`, `CLAUDE.md`, and the testing strategy.

1. **Vectorization**
   - Do not reintroduce Python loops that duplicate work already handled by batched tensor code.
   - When adding a new flow (sources, phi, mosaic, oversample), extend the existing broadcast shapes instead of looping.
   - Verify `_compute_physics_for_position` receives tensors with the expected batch dimensions.
   - **Tricubic & Absorption Evidence:** Phases C-F validated batched gather/polynomial interpolation and detector absorption with 0% performance regression on CPU (`reports/2025-10-vectorization/phase_e/`, `phase_f/`). Regression commands: `pytest tests/test_tricubic_vectorized.py -v` (19 tests) and `pytest tests/test_at_abs_001.py -v -k cpu` (8 tests). CUDA reruns resume after device-placement fix (PERF-PYTORCH-004).

2. **Device & Dtype Neutrality**
   - **Default dtype is float32** for performance and memory efficiency. Precision-critical operations (gradient checks, metric duality) explicitly override to float64 where required.
   - Materialize configuration tensors (beam, detector, crystal) on the execution device before the main loop.
   - Avoid per-iteration `.to()`, `.cpu()`, `.cuda()`, or tensor factories (`torch.tensor(...)`) inside compiled regions; cache constants once.
   - Run CPU **and** CUDA smoke commands (`pytest -v -m gpu_smoke`) when a GPU is available.

3. **torch.compile Hygiene**
   - Watch the console for Dynamo “graph break” warnings; treat them as blockers.
   - Benchmarks should reuse compiled functions; avoid changing shapes every call unless batching logic handles it.

4. **Documentation & Tests**
   - Update relevant docs/tests when you change vectorization or device handling.
   - Capture timings/metrics (CPU vs CUDA) and link them in `docs/fix_plan.md`.

Keep this checklist open while working; cite it in fix-plan entries so the vectorization/device guardrails stay visible.
