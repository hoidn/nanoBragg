| Key | Purpose | Owning Function (`path:line`) | Expected Units |
| --- | --- | --- | --- |
| seed_cli | Record global noise seed chosen by CLI (incl. default `-time`) | `src/nanobrag_torch/__main__.py:714` | integer |
| mosaic_seed_config | Capture mosaic seed handed to CrystalConfig before simulation | `src/nanobrag_torch/__main__.py:848-877` | integer |
| simulator_seed_handoff | Verify Simulator re-applies `mosaic_seed` onto live crystal prior to run | `src/nanobrag_torch/simulator.py:466-469` | integer |
| misset_rng_lcg | Confirm `misset_seed` is forwarded into LCG-based random misset generation | `src/nanobrag_torch/models/crystal.py:725-734` | radians (angles before deg conversion) |
| mosaic_rng_axes | Inspect random unit vectors generated for mosaic domains (should derive from seeded RNG) | `src/nanobrag_torch/models/crystal.py:1327-1332` | unitless vector components |
| mosaic_rng_angles | Capture per-domain random angles to ensure seeded distribution | `src/nanobrag_torch/models/crystal.py:1333-1337` | radians |
| steps_normalization | Confirm normalization denominator uses deterministic counts once RNG is fixed | `src/nanobrag_torch/simulator.py:892-896` | dimensionless count |
| lcg_internal_state | (Optional) Tap `CLCG` state before/after `ran1()` to prove parity with C when reusing helper | `src/nanobrag_torch/utils/c_random.py:125-205` | integer state / float deviate |
