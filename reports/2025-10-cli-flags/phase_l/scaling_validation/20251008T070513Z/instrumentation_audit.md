# Phase M0 Instrumentation Hygiene Audit

**Date:** 2025-10-08T07:05:13Z
**Engineer:** Ralph (loop i=144)
**Plan Reference:** plans/active/cli-noise-pix0/plan.md Phase M0a–M0c
**Git Commit:** (captured in commands.txt)

## Objective

Guard CLI-FLAGS-003 debug instrumentation (`_last_tricubic_neighborhood`) to prevent unconditional payload retention during production runs and ensure device/dtype neutrality per docs/development/testing_strategy.md §1.4.

## Checklist (Phase M0a–M0c)

### M0a: Audit tricubic neighborhood cache scope ✅

**Finding:** `_last_tricubic_neighborhood` was unconditionally populated on every `_tricubic_interpolation` call (crystal.py:432-440), regardless of whether trace mode was active.

**Fix Applied:**
1. Added `self._enable_trace = False` flag to `Crystal.__init__` (crystal.py:123-124)
2. Guarded neighborhood capture with `if self._enable_trace:` conditional (crystal.py:439-454)
3. Production mode now clears stale payload via `self._last_tricubic_neighborhood = None`
4. Simulator sets `self.crystal._enable_trace = True` when `trace_pixel` is configured (simulator.py:501-504)

**Result:** Debug payload only retained when Simulator.debug_config contains `trace_pixel`, preventing memory bloat during batch runs (B > 1).

### M0b: Keep debug tensors device/dtype neutral ✅

**Finding:** All tensors in `_last_tricubic_neighborhood` dictionary (`sub_Fhkl`, `h_indices`, `k_indices`, `l_indices`, `h_flat`, `k_flat`, `l_flat`) are produced by batched gather operations (crystal.py:380-417) that already inherit device/dtype from input query tensors `h`, `k`, `l`.

**Verification:**
- Crystal initialization uses `torch.as_tensor(..., device=self.device, dtype=self.dtype)` for cell params (crystal.py:68-85)
- Batched offset array uses `device=self.device` (crystal.py:380)
- HKL grid indexing preserves device/dtype via advanced indexing (crystal.py:408-412)
- Coordinate arrays use `.to(dtype=self.dtype)` conversion (crystal.py:415-417)

**Result:** No explicit device/dtype conversion needed in guarded block (crystal.py:440-442 comment). Tensors naturally match caller's device/dtype.

### M0c: Document instrumentation toggle ✅

**Toggle Mechanism:**
- **Enable:** Simulator instantiation with `debug_config={'trace_pixel': [slow, fast]}` sets `Crystal._enable_trace = True`
- **Disable:** Production runs omit `trace_pixel` from debug_config; Crystal defaults to `_enable_trace = False`
- **Clear:** Explicitly cleared to `None` in production mode guard (crystal.py:453-454)

**Reproduction Commands:**
```bash
# Trace mode (M0a guard active, neighborhood populated)
KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py \
  --config supervisor --phi-mode c-parity --pixel 685 1039 \
  --out reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T070513Z/trace_py_scaling.log \
  --device cpu --dtype float64

# Production mode (M0a guard prevents neighborhood population)
pytest -xvs tests/test_cli_scaling_phi0.py tests/test_phi_carryover_mode.py
```

## Test Results

### Targeted Test Execution (M0a validation)

**Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -xvs tests/test_cli_scaling_phi0.py tests/test_phi_carryover_mode.py
```

**Result:** 35/35 passed in 2.67s

**Coverage:**
- `test_cli_scaling_phi0.py::TestPhiZeroParity` (2 tests) — φ=0 rotation vector parity
- `test_phi_carryover_mode.py` (33 tests) — CLI parsing, config validation, device/dtype neutrality (CPU + CUDA, float32 + float64)

**Device/Dtype Smoke (M0b validation):**
- CPU float32: ✅ (tests::TestDeviceDtypeNeutrality::test_cpu_consistency[dtype0-*])
- CPU float64: ✅ (tests::TestDeviceDtypeNeutrality::test_cpu_consistency[dtype1-*])
- CUDA float32: ✅ (tests::TestDeviceDtypeNeutrality::test_cuda_consistency[dtype0-*])
- CUDA float64: ✅ (tests::TestDeviceDtypeNeutrality::test_cuda_consistency[dtype1-*])

### Regression Check

No import errors, no device mismatch warnings, no collection failures.

## Artifacts

- **commands.txt**: Git sha, environment exports, test invocations
- **instrumentation_audit.md**: This document
- **Modified Files:**
  - `src/nanobrag_torch/models/crystal.py`: Added `_enable_trace` flag + guarded neighborhood capture
  - `src/nanobrag_torch/simulator.py`: Set `_enable_trace = True` when `trace_pixel` configured

## Next Actions (per plan Phase M0 completion)

1. ✅ M0a–M0c complete; guard active and tested
2. Proceed to Phase M (Structure-Factor & Normalization Parity) with guarded trace harness
3. Update docs/fix_plan.md CLI-FLAGS-003 Attempts History with this audit summary and artifact path

## Exit Criteria

- [✅] Debug helpers guarded behind trace flag
- [✅] Tensors allocated on caller device/dtype
- [✅] Findings logged with artifact paths under `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T070513Z/`

---

**Status:** Phase M0 complete. Ready for Phase M (M1–M4) execution.
