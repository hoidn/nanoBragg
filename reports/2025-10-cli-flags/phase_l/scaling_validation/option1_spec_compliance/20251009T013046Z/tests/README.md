# Test Logs for Option 1 Spec-Compliance Bundle

**Bundle:** 20251009T013046Z
**Phase:** M5e/M5f

---

## Contents

### `pytest_cpu.log`

**Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py
```

**Result:** PASS (2/2)
- `test_rot_b_matches_c` — Validates b_star rotation vector Y-component parity
- `test_k_frac_phi0_matches_c` — Validates k_frac value at φ=0

**Expected:** All tests pass because they verify the spec-compliant recalculation behavior

---

### `pytest_cuda.log`

**Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v -m gpu_smoke tests/test_cli_scaling_phi0.py
```

**Result:** 2 deselected
**Reason:** test_cli_scaling_phi0.py tests are not marked with `gpu_smoke` marker; they run on CPU only

**Note:** CUDA availability confirmed (torch.cuda.is_available() == True), but this test suite doesn't include GPU-specific smoke tests

---

## Cross-Reference

- **Comparison output:** `../compare_scaling_traces.txt` shows I_before_scaling delta (14.6%)
- **Metrics:** `../metrics.json` contains structured per-factor deltas
- **Summary:** `../summary.md` explains Option 1 decision and expected divergence
