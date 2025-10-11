# Determinism Seed Callchain — Findings

## What We Traced
- CLI correctly captures `-seed`, `-mosaic_seed`, and `-misset_seed`, defaulting the global noise seed to `-time.time()` when unspecified (`src/nanobrag_torch/__main__.py:604-714`).
- `CrystalConfig` receives those seed values and the Simulator pushes `mosaic_seed` back onto the live crystal object before pixel processing (`src/nanobrag_torch/__main__.py:848-877`; `src/nanobrag_torch/simulator.py:451-469`).
- `Crystal.get_rotated_real_vectors` calls the C-compatible LCG helper for random misset, honouring `misset_seed` exactly (`src/nanobrag_torch/models/crystal.py:720-737`).
- Mosaic randomness bypasses the seed: `_generate_mosaic_rotations` samples axes and angles via `torch.randn` on the default global generator, ignoring `CrystalConfig.mosaic_seed` (`src/nanobrag_torch/models/crystal.py:1327-1336`).
- Intensities are averaged over the mosaic domain dimension (`src/nanobrag_torch/simulator.py:883-896`), so any non-determinism in mosaic orientations propagates directly into test outputs.

## Key Insight
`mosaic_seed` is never consulted after the Simulator copies it to the crystal. As a result, mosaic orientations depend on the global torch RNG state, violating ADR‑05 / spec requirements and explaining the residual failures in AT-PARALLEL-013/024 once dtype blockers were removed.

## Next Step to Confirm
Instrument the taps listed in `trace/tap_points.md` to capture RNG state before `_generate_mosaic_rotations` and after its `torch.randn` calls, ideally while running AT-PARALLEL-024 with TorchDynamo disabled (current logs show Dynamo crashes when CUDA metadata is probed with zero visible devices). The evidence will prove that swapping in the C-compatible LCG (or a locally seeded `torch.Generator`) restores determinism before any implementation change is delegated.

## Deferred Dynamic Trace
Attempting to run AT-PARALLEL-013 under tracing still trips the known TorchDynamo CUDA query bug (`torch/_dynamo/device_interface.py:218`). Once Dynamo is temporarily disabled for determinism selectors, rerun a minimal ROI capture to populate `callgraph/dynamic.txt` alongside the planned taps.
