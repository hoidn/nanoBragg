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
   - **Cache dtype neutrality:** When retrieving cached tensors for comparison, use `.to(device=..., dtype=...)` to match both device AND dtype of live tensors. Example from `Detector.get_pixel_coords()`:
     ```python
     # Retrieve cached basis vector with dtype coercion
     cached_f = self._cached_basis_vectors[0].to(device=self.device, dtype=self.dtype)
     # Now safe to compare with live geometry tensor
     torch.allclose(self.fdet_vec, cached_f, atol=1e-15)  # ✅ Both same dtype
     ```
     Omitting `dtype=` causes `RuntimeError` when dtype switches occur (e.g., `detector.to(dtype=torch.float64)`).

3. **torch.compile Hygiene**
   - Watch the console for Dynamo “graph break” warnings; treat them as blockers.
   - Benchmarks should reuse compiled functions; avoid changing shapes every call unless batching logic handles it.

4. **Source Handling & Equal Weighting (C-Parity)**
   - **Do not apply source weights as multiplicative factors.** The weight column in sourcefiles is parsed but ignored per `specs/spec-a-core.md:151-153`.
   - Steps normalization divides by source count, not weight sum: `steps = sources * mosaic_domains * phisteps * oversample^2`.
   - CLI `-lambda` is authoritative for all sources; sourcefile wavelength column is also ignored.
   - **Parity Memo:** `reports/2025-11-source-weights/phase_h/20251010T002324Z/parity_reassessment.md` confirms C reference (nanoBragg.c:2570-2720) implements equal weighting; correlation ≥0.999, |sum_ratio−1| ≤5e-3 are the validated thresholds.
   - **Tests:** `pytest tests/test_cli_scaling.py::TestSourceWeights* -v` (expect 7/7 passing)

5. **Documentation & Tests**
   - Update relevant docs/tests when you change vectorization or device handling.
   - Capture timings/metrics (CPU vs CUDA) and link them in `docs/fix_plan.md`.

Keep this checklist open while working; cite it in fix-plan entries so the vectorization/device guardrails stay visible.
