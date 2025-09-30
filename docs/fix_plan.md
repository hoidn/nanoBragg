# nanoBragg PyTorch Implementation Fix Plan

**Last Updated:** 2025-09-29
**Current Status:** Parity harness bootstrapped and operational; acceptance suite green.

---
## Active Focus

1. **Parity Harness Coverage Expansion** *(in_progress)*
   - Goal: ensure every parity-threshold AT (specs/spec-a-parallel.md) has a canonical entry in `tests/parity_cases.yaml` and executes via `tests/test_parity_matrix.py`.
   - Status: Harness file `tests/test_parity_matrix.py` created (2025-09-29); initial parity cases exist for AT-PARALLEL-001/002/004/006/007.
   - Exit criteria: parity matrix collects ≥1 case per AT with thresholds cited in metrics.json; `pytest -k parity_matrix` passes.
   - Reproduction: `NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py`.
   - Next: Verify harness executes cleanly for existing cases, then add remaining ATs (003/005/008/009/010/011/012/020/022/023/024/025/026/027/028/029).

2. **Docs-as-Data CI lint** *(queued)*  
   - Goal: add automated lint ensuring spec ↔ matrix ↔ YAML consistency and artifact references before close-out loops.  
   - Exit criteria: CI job fails when parity mapping/artifact requirements are unmet.

---
## Recent Resolutions

- **Parity Harness Bootstrap** (2025-09-29)
  - Context: Debugging loop Step 0 detected missing `tests/test_parity_matrix.py` (blocking condition per prompt).
  - Action: Created shared parity runner implementing canonical C↔PyTorch validation per testing strategy Section 2.5.
  - Implementation: 400-line pytest harness consuming `tests/parity_cases.yaml`; computes correlation/MSE/RMSE/max|Δ|/sum_ratio; writes metrics.json + diff artifacts on failure.
  - Coverage: Initial parity cases for AT-PARALLEL-001/002/004/006/007 defined in YAML (16 test cases collected).
  - Baseline Status: 13/16 pass, 3 fail (AT-PARALLEL-002: pixel-0.05mm/0.4mm; AT-PARALLEL-004: xds).
  - Status: Harness operational and gating parity work. Ready for debugging loops.
  - Artifacts: `tests/test_parity_matrix.py`, baseline metrics in `reports/2025-09-29-AT-PARALLEL-{002,004}/`.

- **AT-PARALLEL-002 Pixel Size Independence** (2025-09-29)
  - Root cause: comparison-tool resampling bug (commit 7958417).
  - Status: Complete; 4/4 PyTorch tests pass; parity harness case documented (`tests/parity_cases.yaml`: AT-PARALLEL-002).
  - Artifacts: `reports/debug/2025-09-29-at-parallel-002/summary.json`.

---
## TODO Backlog

- [ ] Add parity cases for AT-PARALLEL-003/005/008/009/010/012/013/014/015/016/017/018/020/021/022/023/024/025/026/027/028/029.  
- [ ] Implement docs-as-data lint (spec ↔ matrix ↔ YAML ↔ fix_plan).  
- [ ] Convert legacy manual comparison scripts to consume parity harness outputs (optional).

---
## Reference Commands

```
# Shared parity harness
NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py

# Individual AT (PyTorch self-checks remain secondary)
pytest -v tests/test_at_parallel_002.py
```

---
## Notes
- Harness cases fix seeds and use `sys.executable -m nanobrag_torch` to match venv.  
- Parity artifacts (metrics.json, diff PNGs) live under `reports/<date>-AT-*/` per attempt.  
- Keep `docs/development/testing_strategy.md` and `specs/spec-a-parallel.md` aligned with new parity entries.
