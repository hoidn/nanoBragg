# STRAT-PROB-002 Artifacts

Focus: Benchmark + evidence outputs for the probabilistic simulator per `docs/strategy/mainstrategy.md` §4 and `docs/plans/2026-01-29-probabilistic-simulator-implementation.md` Task 3.

Store benchmark logs, PNG/JSON copies, and CLI command transcripts here.

## Scenario Presets

| Preset | Cell (Å) | λ (Å) | Distance (mm) | Pixel (mm) | Detector |
| --- | --- | --- | --- | --- | --- |
| default | 100 | 1.0 | 100 | 0.1 | 64×64 |
| hi_res_a | 40 | 0.65 | 80 | 0.075 | 96×96 |
| hi_res_b | 30 | 0.5 | 60 | 0.05 | 128×128 |

## Reports

| Timestamp | Scenario | Key Finding |
| --- | --- | --- |
| 2026-01-29T061003Z | default | Speedup 1.9×, zero gradients for probabilistic |
| 2026-01-29T062136Z | hi_res_b | Speedup 2.1×, zero gradients confirmed (FND-PROB-2026-01) |
