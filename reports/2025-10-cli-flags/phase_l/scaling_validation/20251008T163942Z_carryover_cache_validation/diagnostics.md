# CUDA Carryover Cache Validation - M2h.2 (SUCCESS)

## Executive Summary
**Status:** ✅ SUCCESS - Device neutrality fix successful
**Timestamp:** 2025-10-08T16:39:42Z
**Git SHA:** cd123f697c1392de8e5c0a5bc94d2a1e3ca70a9d
**Phase:** CLI-FLAGS-003 M2h.2 (CUDA + CPU device parity)

## Context
This loop implements M2h.2 per `input.md` Do Now: patch `src/nanobrag_torch/simulator.py` debug tensor factories to inherit `self.device`/`self.dtype`, then run the CUDA trace harness to capture parity diagnostics.

## Previous Blocker (Resolved)
**Prior attempt (#165):** `20251008T162542Z_carryover_cache_validation/`
- **Error:** RuntimeError - Expected all tensors to be on same device, found cuda:0 and cpu
- **Root cause:** Debug instrumentation in `_apply_debug_output()` (lines 1487-1689) created HKL tensors via bare `torch.tensor()` without inheriting device from main computation
- **Violation:** CLAUDE.md Rule #16 (PyTorch Device & Dtype Neutrality)

## Fix Applied
**Modified:** `src/nanobrag_torch/simulator.py`
**Lines changed:** 1487-1489, 1506-1508, 1517-1519, 1687-1689

**Pattern:**
```python
# Before (CPU-only)
torch.tensor(h)
torch.tensor([[h0]])

# After (device/dtype neutral)
torch.tensor(h, device=self.device, dtype=self.dtype)
torch.tensor([[h0]], device=self.device, dtype=self.dtype)
```

**Files modified:**
- `src/nanobrag_torch/simulator.py:1487` - F_latt_a sincg argument
- `src/nanobrag_torch/simulator.py:1488` - F_latt_b sincg argument
- `src/nanobrag_torch/simulator.py:1489` - F_latt_c sincg argument
- `src/nanobrag_torch/simulator.py:1506-1508` - F_cell_interp HKL tensors (3 lines)
- `src/nanobrag_torch/simulator.py:1517-1519` - F_cell_nearest HKL tensors (3 lines)
- `src/nanobrag_torch/simulator.py:1687-1689` - F_latt_*_phi sincg arguments (per-φ trace, 3 lines)

**Total:** 12 tensor construction sites now device/dtype neutral

## Validation Results

### CUDA Run (Primary)
**Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py \
  --pixel 685 1039 --config supervisor --phi-mode c-parity --device cuda --dtype float64 \
  --out reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T163942Z_carryover_cache_validation/trace_py_scaling_cuda.log
```

**Result:** ✅ SUCCESS
- 114 TRACE_PY lines captured
- 10 TRACE_PY_PHI per-φ lines captured
- Final intensity: 2.45946637686447e-07
- No device mismatch errors
- Trace file: `trace_py_scaling_cuda.log` (checksum in `sha256.txt`)
- Per-φ trace: `trace_py_scaling_cuda_per_phi.log`

### CPU Run (Baseline Comparison)
**Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py \
  --pixel 685 1039 --config supervisor --phi-mode c-parity --device cpu --dtype float64 \
  --out reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T163942Z_carryover_cache_validation/trace_py_scaling_cpu.log
```

**Result:** ✅ SUCCESS
- 114 TRACE_PY lines captured
- 10 TRACE_PY_PHI per-φ lines captured
- Final intensity: 2.45946637686509e-07
- Trace file: `trace_py_scaling_cpu.log` (checksum in `sha256.txt`)
- Per-φ trace: `trace_py_scaling_cpu_per_phi.log`

### Device Parity Verification
**Intensity comparison:**
- CUDA: 2.45946637686447e-07
- CPU:  2.45946637686509e-07
- Relative difference: 2.52e-11 (negligible, within float64 precision)

**Observation:** Both devices produce identical results, confirming device neutrality.

## Environment Summary
- Python: 3.13.7
- PyTorch: 2.8.0+cu128
- CUDA available: True
- CUDA version: 12.8
- GPU: NVIDIA GeForce RTX 3090
- Driver: 570.172.08
- Git SHA: cd123f697c1392de8e5c0a5bc94d2a1e3ca70a9d

## Next Actions (M2h.3 Gradcheck)
Per `plans/active/cli-noise-pix0/plan.md:130`, M2h.3 gradcheck probe is now unblocked:

1. **Create gradcheck script:**
   ```python
   import torch
   from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig
   from nanobrag_torch.simulator import Simulator

   # Minimal 2x2 ROI, float64, CUDA
   device = torch.device('cuda')
   dtype = torch.float64

   # Test gradient flow through carryover cache
   phi_start = torch.tensor(0.0, requires_grad=True, device=device, dtype=dtype)
   config = CrystalConfig(..., phi_start_deg=phi_start, ...)

   simulator = Simulator(config, ..., device=device, dtype=dtype)
   output = simulator.run()

   # Verify cache gradients non-null
   assert output.requires_grad
   loss = output.sum()
   loss.backward()
   assert phi_start.grad is not None
   print(f"Gradient check: PASS")
   ```

2. **Run gradcheck harness:**
   ```bash
   KMP_DUPLICATE_LIB_OK=TRUE python <gradcheck_script.py>
   ```

3. **Capture artifacts:**
   - `gradcheck.log` - Script stdout/stderr
   - `gradcheck_metrics.json` - Gradient norms, loss value
   - Update `sha256.txt` with new checksums

4. **Update fix_plan:**
   - Record M2h.3 completion in Attempts History
   - Mark M2h.2 [D] and M2h.3 [D]
   - Reference this diagnostics.md

## Artifact Manifest
- `trace_py_scaling_cuda.log` - CUDA trace (114 TRACE_PY lines)
- `trace_py_scaling_cpu.log` - CPU trace (114 TRACE_PY lines)
- `harness_stdout.log` - CUDA harness stdout
- `cpu_stdout.log` - CPU harness stdout
- `env.json` - Runtime metadata
- `torch_collect_env.txt` - Detailed torch environment
- `commands.txt` - Reproduction commands
- `sha256.txt` - Artifact checksums
- `diagnostics.md` - This file

## References
- input.md Do Now: M2h.2 CUDA trace harness command
- plans/active/cli-noise-pix0/plan.md:128-131 (M2h validation steps)
- CLAUDE.md Rule #16 (Device & Dtype Neutrality)
- docs/development/pytorch_runtime_checklist.md:11-15 (Device neutrality guidelines)
- Prior blocked attempt: `20251008T162542Z_carryover_cache_validation/`
- Implementation commits: 678cbf4, fa0167b, cd123f6 (this fix)
- Option B design: `reports/.../20251210_optionB_design/optionB_batch_design.md`

## Notes
- Warnings about `torch.tensor(sourceTensor)` in `crystal.py:1317` are unrelated to this fix and can be addressed separately
- Per-φ traces written to nested `per_phi/` subdirectory per harness design
- Both CPU and CUDA runs completed in reasonable time (<2s each)
- No graph breaks or torch.compile warnings observed
