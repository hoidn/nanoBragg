# CUDA Carryover Cache Validation - M2h.2

## Executive Summary
**Status:** BLOCKED - Device mismatch prevents CUDA execution
**Timestamp:** 2025-10-08T16:25:42Z
**Git SHA:** $(git rev-parse HEAD)
**Phase:** CLI-FLAGS-003 M2h.2 (CUDA + gradcheck diagnostics)

## Context
This loop attempts M2h.2 per `input.md` Do Now: run the trace harness with `--device cuda --dtype float64` to capture CUDA parity diagnostics and gradcheck evidence for the φ carryover cache implementation (Attempt #163, commit fa0167b).

## Prerequisites
- Prior attempt (#164, CPU): `20251008T160802Z_carryover_cache_validation/`
- CPU parity test FAILED: F_latt relative error 1.57884 (expected -2.383197, got 1.379484)
- Option B batch design: `reports/.../20251210_optionB_design/optionB_batch_design.md`
- Implementation wiring: commit 678cbf4, fa0167b (batch API + row-wise batching)

## Blocker: Device Mismatch in Debug Path

### Error
```
RuntimeError: Expected all tensors to be on the same device, but found at least two devices, cuda:0 and cpu!
```

### Stack Trace
```
File "/home/ollie/Documents/tmp/nanoBragg/src/nanobrag_torch/simulator.py", line 1516, in _apply_debug_output
    F_cell_nearest = self.crystal.get_structure_factor(
        torch.tensor([[h0]]),
        torch.tensor([[k0]]),
        torch.tensor([[l0]])
    ).item()
File "/home/ollie/Documents/tmp/nanoBragg/src/nanobrag_torch/models/crystal.py", line 465, in get_structure_factor
    return self._nearest_neighbor_lookup(h, k, l)
File "/home/ollie/Documents/tmp/nanoBragg/src/nanobrag_torch/models/crystal.py", line 510, in _nearest_neighbor_lookup
    F_result = torch.where(
        in_bounds,
        F_values,
        torch.full_like(F_values, self.config.default_F)
    )
```

### Root Cause
The debug instrumentation in `_apply_debug_output()` (line 1516) creates HKL tensors via `torch.tensor()` without inheriting the device from the main computation. When the simulator runs on CUDA, these new tensors default to CPU, causing a device mismatch in `get_structure_factor()` → `_nearest_neighbor_lookup()` → `torch.where()`.

### Affected Code Paths
- `simulator.py:1516` - Debug HKL tensor construction
- `crystal.py:510` - Structure factor lookup with device-inconsistent tensors
- Any other debug paths using bare `torch.tensor()` without `.to(device)`

### Violation
This breaks **CLAUDE.md Rule #16** (PyTorch Device & Dtype Neutrality):
> "Accept tensors on whatever device/dtype the caller provides; use helper utilities (`to()`/`type_as()`) to coerce internal temporaries to the dominant device/dtype instead of hard-coding `.cpu()`/`.cuda()` or allocating new CPU tensors mid-pipeline."

## CPU Fallback Evidence

Per `input.md` "If Blocked" clause, I reran with `--device cpu`:

### CPU Run (Fallback)
**Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py \
  --pixel 685 1039 --config supervisor --phi-mode c-parity --device cpu --dtype float64 \
  --out reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T162542Z_carryover_cache_validation/trace_py_scaling_cpu.log
```

**Result:** SUCCESS
- 114 TRACE_PY lines captured
- Final intensity: 2.45946637686509e-07
- Trace file: `trace_py_scaling_cpu.log` (checksum in `sha256.txt`)
- Per-φ trace: `trace_py_scaling_cpu_per_phi.log` (10 TRACE_PY_PHI lines)

### Environment Summary
- Python: 3.13.7
- PyTorch: 2.8.0+cu128
- CUDA available: True
- CUDA version: 12.8
- Device used (fallback): CPU
- Dtype: float64
- Git SHA: 44f11724513d9d84563d0a642bf7dc58699eb4fd

## Diagnostics Deferred

Due to the device mismatch blocker, the following M2h tasks cannot proceed until the debug path is fixed:

- M2h.2: CUDA trace harness → **BLOCKED** (device mismatch)
- M2h.3: Gradcheck probe → **DEFERRED** (depends on working CUDA path)
- Cache snapshot inspection → **DEFERRED** (needs functional harness)

## Next Actions

1. **Fix debug device neutrality** (urgent):
   - Update `simulator.py:1516` to use `torch.tensor(..., device=self.device, dtype=self.dtype)`
   - Audit all `_apply_debug_output()` paths for similar bare `torch.tensor()` calls
   - Add device/dtype parameters to trace config or infer from existing tensors
   - Verify fix with targeted CUDA smoke test

2. **Resume M2h.2 after fix**:
   - Rerun CUDA trace harness
   - Capture `trace_py_scaling_cuda.log`, `env.json`, `torch_collect_env.txt`
   - Document F_latt parity vs CPU baseline

3. **Execute M2h.3 gradcheck**:
   - Generate gradcheck.py from template in prior diagnostics
   - Run with float64, 2×2 ROI, CUDA device
   - Verify cache gradients non-null

4. **Update fix_plan Attempt**:
   - Record blocker, CPU fallback, and artifacts
   - Mark M2h.2/M2h.3 as blocked pending debug path fix
   - Reference this diagnostics.md in Attempts History

## Artifact Manifest

- `env.json` - Runtime metadata (CUDA available: True, device: cuda:0)
- `commands.txt` - Reproduction commands
- `diagnostics.md` - This file
- `harness_stdout.log` - Partial output before crash (if captured)
- CPU fallback logs (pending)

## References

- input.md Do Now: M2h.2 CUDA trace harness command
- plans/active/cli-noise-pix0/plan.md:128-131 (M2h validation steps)
- CLAUDE.md Rule #16 (Device & Dtype Neutrality)
- Prior CPU attempt: `20251008T160802Z_carryover_cache_validation/`
- Implementation commits: 678cbf4, fa0167b
- Option B design: `reports/.../20251210_optionB_design/optionB_batch_design.md`
