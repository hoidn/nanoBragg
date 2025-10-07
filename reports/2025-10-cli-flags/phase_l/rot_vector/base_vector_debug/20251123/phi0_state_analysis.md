# φ=0 State Analysis — Phase L3k.3c.2 Evidence

**Date**: 2025-10-07
**Loop**: ralph i=107
**Mode**: Parity / Evidence Collection
**Status**: BLOCKED (awaiting C trace generation per Phase L3k.3b)

## Observed PyTorch Values

From `rot_vector_state_probe.log`:

```
b_base_y 0.7173197865486145
rot_b_phi0_y 0.7173197865486145
rot_b_phi1_y 0.7122385501861572
k_frac_placeholder 980.31396484375
```

### Interpretation

- **b_base_y**: Base `b` vector Y-component before rotation (Å units)
- **rot_b_phi0_y**: Rotated `b` vector Y-component at φ=0 (first φ step)
- **rot_b_phi1_y**: Rotated `b` vector Y-component at φ=0.01° (second φ step)
- **k_frac_placeholder**: Dot product `rot_b[0,0] · rot_b[0,0]` = |rot_b|² at φ=0

### Key Observation

**φ=0 matches base**: `rot_b_phi0_y == b_base_y` (0.7173197865486145 Å)

This indicates that at φ=0, the current PyTorch implementation correctly returns the unrotated base vector. The rotation begins at φ₁ (0.01°), where `rot_b_phi1_y = 0.7122385501861572` shows the expected small deviation.

## C Reference

**Status**: **MISSING** — C trace file does not exist

**Expected location**: `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/202510070839/c_trace_phi_202510070839.log`

**Required action**: Execute Phase L3k.3b to instrument `golden_suite_generator/nanoBragg.c` with `TRACE_C_PHI` output for the supervisor pixel, rebuild, and regenerate C traces for all φ steps (0–9).

**Reference from input.md**:
- Line 103: Points to `c_trace_phi_202510070839.log` as the C reference
- Line 104: Points to `trace_py_rot_vector_202510070839.log` as PyTorch reference (also missing)

## Delta Summary

**Unable to compute deltas** — C reference data unavailable.

Per input.md "If Blocked" guidance (lines 8-9):
> If A.mat or scaled.hkl are unavailable, switch to the existing C/Py traces under reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/202510070839/, document the gap in diagnosis.md, capture a stub entry in commands.txt explaining the missing assets, update sha256.txt accordingly, emit a placeholder delta_metrics.json noting the missing data, and log a new Attempt referencing the dependency issue before proceeding.

**Stub recorded**: `delta_metrics.json` contains status="BLOCKED" with captured PyTorch values.

## Vectorization Risk

The current implementation (after Attempt #97 φ rotation fix per CLAUDE Rule #13) rotates only real vectors and recomputes reciprocal vectors via cross products. This preserves the C semantics identified in `golden_suite_generator/nanoBragg.c:3056-3058`:

```c
/* rotate "a" using phi for this chunk */
rotate(&a[1],&a[2],&a[3],phi_tic,0.0,spindle_axis);
rotate(&b[1],&b[2],&b[3],phi_tic,0.0,spindle_axis);
rotate(&c[1],&c[2],&c[3],phi_tic,0.0,spindle_axis);
```

The C code rotates **only real vectors** at φ steps. Reciprocal vectors are not explicitly rotated in the φ loop; they are implicitly used via the Miller index calculation (`h = S·a`, etc.).

The PyTorch implementation now matches this (see `src/nanobrag_torch/models/crystal.py:1008-1035`):
1. Rotate real vectors (`a`, `b`, `c`) by φ
2. Recompute reciprocal vectors from rotated real vectors using cross products and V_actual

**Risk**: None identified at φ=0 based on current evidence. The φ=0 case correctly returns the base vector without applying rotation (identity operation).

## Next Diagnostic Step

**Phase L3k.3b** (from plan.md:278-280):
1. Instrument `golden_suite_generator/nanoBragg.c` to emit `TRACE_C_PHI phi_tic=X ap_Y=... bp_Y=... cp_Y=...` for each φ step
2. Rebuild: `make -C golden_suite_generator`
3. Run with supervisor command to generate C trace
4. Compare against this PyTorch probe to compute actual deltas

**Expected outcome** (per input.md lines 71-72):
- Extract C `phi_tic=0` and `phi_tic=9` values
- Compute Δb_y (predicted ≈ +4.57e-2 Å based on prior Phase L2c findings)
- Compute Δk_frac (predicted ≈ +2.28 based on prior findings)

## Provenance

- Commands: `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/commands.txt`
- Probe log: `rot_vector_state_probe.log` (SHA256: ef946e94957e9c953fc7fb214a1490509c5b8a00f73f4cdf3a9e5db7da07d1e5)
- Delta metrics: `delta_metrics.json` (status: BLOCKED)
- Hashes: `sha256.txt`

## Conclusion

**Evidence captured successfully** for Phase L3k.3c.2. PyTorch φ=0 behavior is consistent with expectations (returns base vector unchanged). **Next blocking step**: Generate C trace via Phase L3k.3b to enable delta computation and complete the carryover story.

**Recommendation**: Proceed to Phase L3k.3b instrumentation as the immediate next action. Do not attempt to update `diagnosis.md` with remediation proposals until the C reference data validates the hypothesis.
