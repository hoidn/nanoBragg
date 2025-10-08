# Phase M2g.5 - Trace Tooling Verification Report

## Context
Task: Verify trace harness (`trace_harness.py`) handles Option B batch-indexed cache without IndexError.
Date: 2025-10-08
Engineer: ralph (loop i=169)
Plan Reference: `plans/active/cli-noise-pix0/plan.md` Phase M2g.5

## Objective
Verify that the trace harness works correctly with the recent Option B batch cache implementation (Attempt #163) and device/dtype neutrality fixes (Attempt #166).

## Test Configuration
- Pixel: (slow=685, fast=1039) — supervisor command ROI pixel
- Config preset: supervisor (CLI-FLAGS-003 authoritative command)
- Phi carryover mode: c-parity (emulate C-PARITY-001 bug)
- Devices tested: CPU (float64), CUDA (float64)
- Emit rot-stars: enabled (TRACE_PY_ROTSTAR output)

## Results

### CPU Execution
**Status**: ✅ SUCCESS

- Command: `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --phi-mode c-parity --pixel 685 1039 --device cpu --dtype float64 --emit-rot-stars --out reports/2025-10-cli-flags/phase_l/trace_tooling_patch/20251008T175913Z/trace_cpu.log`
- Trace lines captured: 124 TRACE_PY lines
- Per-φ traces: 10 TRACE_PY_PHI lines
- Final intensity: 2.45946637686509e-07
- Output: `trace_cpu.log` (124 lines)

### CUDA Execution
**Status**: ✅ SUCCESS

- Command: Same as CPU with `--device cuda`
- Trace lines captured: 124 TRACE_PY lines
- Per-φ traces: 10 TRACE_PY_PHI lines
- Final intensity: 2.45946637686447e-07
- Output: `trace_cuda.log` (124 lines)
- **CPU/CUDA parity**: Δ = 6.2e-13 relative (2.52e-11 absolute) — PASS

## Key Findings

1. **No IndexError encountered**: The trace harness successfully indexed omega_pixel and F_latt tensors for both CPU and CUDA runs.

2. **Device/dtype neutrality confirmed**: Attempt #166 fix (tensor factory device alignment) enabled CUDA traces without modification.

3. **Cache-aware taps working**: The harness captured all trace fields including:
   - omega_pixel_sr (solid angle)
   - F_latt_a, F_latt_b, F_latt_c, F_latt (lattice factors)
   - I_before_scaling_pre_polar, I_before_scaling_post_polar
   - rot_a/b/c_angstroms (real-space rotated vectors)
   - rot_a/b/c_star_A_inv (reciprocal-space rotated vectors)

4. **Per-φ traces functional**: TRACE_PY_PHI output captured for all 10 φ steps with per-step lattice factors.

5. **Gradient-preserving**: No `.item()` calls on gradient-critical tensors; all indexing uses tensor-native operations.

## Observations

- **Attempt #166 effect**: The device-neutral tensor factory fix (`_apply_debug_output` line 1445-1446) eliminated the CUDA blocker from Attempt #164.
- **Attempt #163 batch cache compatibility**: Row-wise batching through `Crystal.get_rotated_real_vectors_for_batch()` does not interfere with trace indexing.
- **No code changes required**: M2g.5 tooling patch was already complete from prior attempts; this run provides evidence of success.

## Artifacts
- `commands.txt` — Reproduction commands with exit status
- `trace_cpu.log` — CPU trace (124 lines, float64)
- `trace_cuda.log` — CUDA trace (124 lines, float64)
- `run_metadata.json` — Environment snapshot (Python 3.13.7, PyTorch 2.8.0+cu128, CUDA 12.8)
- `sha256.txt` — Artifact checksums

## Next Actions (per input.md)

1. ✅ **M2g.5 COMPLETE** — Trace tooling verified cache-aware without IndexError
2. **M2g.6** — Document Option B architecture decision in `phi_carryover_diagnosis.md`
3. **M2h** — Execute validation bundle (CPU pytest, CUDA probe, gradcheck)
4. **M2i** — Regenerate cross-pixel traces expecting φ=0 carryover to work

## Exit Criteria Met
- [x] Trace harness executes without IndexError on CPU
- [x] Trace harness executes without IndexError on CUDA
- [x] Omega and F_latt values captured in trace output
- [x] Per-φ rotation traces (TRACE_PY_PHI) functional
- [x] CPU/CUDA parity within tolerance (≤1e-10 relative)

## Git State
- SHA: e2c75edecfc179a3cccf3c1524df51e359f54bff
- Branch: feature/spec-based-2
