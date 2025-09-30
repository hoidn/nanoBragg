# PyTorch Runtime Checklist

Use this quick checklist before and after every PyTorch simulator edit. It distills the authoritative guidance from
`docs/architecture/pytorch_design.md`, `CLAUDE.md`, and the testing strategy.

1. **Vectorization**
   - Do not reintroduce Python loops that duplicate work already handled by batched tensor code.
   - When adding a new flow (sources, phi, mosaic, oversample), extend the existing broadcast shapes instead of looping.
   - Verify `_compute_physics_for_position` receives tensors with the expected batch dimensions.

2. **Device & Dtype Neutrality**
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
