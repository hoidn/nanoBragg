# CLI-FLAGS-003 Phase L3k.3b Diagnosis — φ Rotation Drift Investigation

**Date:** 2025-10-07
**Session:** Evidence-only loop (no production code changes)
**Command:** `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --config supervisor --pixel 685 1039 --out trace_py_rot_vector_20251122.log --device cpu --dtype float64`

## Summary

Generated fresh per-φ traces using the `trace_harness.py` with supervisor configuration. The comparison script revealed that **NO C-code per-φ traces exist** in `c_trace_mosflm.log`, making direct PyTorch vs C comparison impossible at this stage.

## Artifacts Generated

All artifacts stored in `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122/`:

1. **trace_py_rot_vector_20251122.log** (2.1K) — Main trace with 43 TRACE_PY lines
2. **trace_py_rot_vector_20251122_per_phi.log** (1.3K) — Per-φ trace with 10 TRACE_PY_PHI entries
3. **trace_py_rot_vector_20251122_per_phi.json** (1.9K) — Machine-readable per-φ data
4. **comparison_stdout.txt** — Comparison script output showing zero C traces found
5. **pytest_collect.log** — Test collection results (653 tests collected successfully)

## Key Findings

### 1. PyTorch Trace Content

The PyTorch trace contains **10 per-φ entries** spanning φ = 0° → 0.1° (supervisor command uses `osc=0.1, phisteps=10`):

| φ_tic | φ (deg) | k_frac | F_latt_b | F_latt |
|-------|---------|--------|----------|--------|
| 0 | 0.0 | -0.589139 | -0.861431 | 1.351787 |
| 1 | 0.0111 | -0.591149 | -0.654273 | 1.078936 |
| 2 | 0.0222 | -0.593159 | -0.389060 | 0.672165 |
| ... | ... | ... | ... | ... |
| 9 | 0.1 | -0.607227 | 1.051326 | -2.351899 |

**Observable Drift:**
- **k_frac span:** Δk = 0.018088 (from -0.589139 to -0.607227)
- **F_latt_b variation:** -0.861431 → +1.051326 (total swing ~1.91)
- This drift suggests φ rotation is being applied and affecting Miller indices

### 2. C Trace Format Mismatch

The existing `c_trace_mosflm.log` contains:
- **Detector geometry traces** (`TRACE_C:detector_convention`, `TRACE_C:pix0_vector`, etc.)
- **NO per-φ iteration traces** (`TRACE_C_PHI` lines missing)

This means the C binary was run without per-φ trace instrumentation, or the instrumentation doesn't emit `TRACE_C_PHI` lines.

### 3. Comparison Script Adjustment

Fixed `scripts/compare_per_phi_traces.py` to handle both `'traces'` and `'per_phi_entries'` JSON keys (the harness uses `'per_phi_entries'`).

## Hypotheses

### H1: C Binary Lacks Per-φ Instrumentation

**Evidence:**
- `c_trace_mosflm.log` contains only static geometry traces, no loop iterations
- Comparison script found zero `TRACE_C_PHI` lines

**Implication:** Cannot perform C vs PyTorch per-φ diff until C binary is instrumented to emit per-φ traces for pixel (685, 1039) across the φ grid.

### H2: φ Rotation Implementation Divergence (Existing Hypothesis from L3k)

**Evidence from PyTorch traces:**
- k_frac drifts linearly by ~0.002 per φ step
- F_latt values oscillate (sign changes at φ_tic ≥ 4)
- Consistent with real-space vector rotation affecting Miller index calculation

**Status:** Cannot confirm or rule out without C reference traces. Hypothesis H2 from Phase L3k (φ rotation applies to both real and reciprocal independently) remains the leading candidate, but **requires C traces to isolate the divergence point.**

### H3: Supervisor Spindle Axis Configuration

**Context:** Plan L3k.3a states tests were updated to `spindle_axis=[-1,0,0]` to match supervisor command.

**Question:** Does the trace harness use the same spindle axis as the supervisor command?

**Check required:** Verify `trace_harness.py --config supervisor` applies `spindle_axis=[-1,0,0]`.

## Next Actions (from Plan L3k.3b)

Per `plans/active/cli-noise-pix0/plan.md:292`:

1. **[BLOCKED] Generate C per-φ traces:** Instrument `golden_suite_generator/nanoBragg.c` to emit `TRACE_C_PHI` lines for pixel (685, 1039) across φ = 0° → 0.1° (10 steps). Run supervisor command with instrumented binary and capture output to `c_trace_phi_instrumented.log`.

2. **Rerun comparison:** Once C traces exist, execute:
   ```bash
   python scripts/compare_per_phi_traces.py \
     reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122/trace_py_rot_vector_20251122_per_phi.json \
     <new_c_trace_phi_instrumented.log> \
     > reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122/comparison_with_c_phi.txt
   ```

3. **Identify first divergence:** Use comparison output to find the φ_tic where Δk exceeds tolerance (5e-4) and document the divergent tensor in this diagnosis.md.

4. **Update fix_checklist.md:** Record findings in VG-1.4 notes (`reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md`).

## Command Reproduction

For reproducibility:

```bash
# Create evidence directory
mkdir -p reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122

# Generate PyTorch per-φ traces
export PYTHONPATH=src
export KMP_DUPLICATE_LIB_OK=TRUE
python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py \
  --config supervisor \
  --pixel 685 1039 \
  --out trace_py_rot_vector_20251122.log \
  --device cpu \
  --dtype float64

# Move artifacts
mv trace_py_rot_vector_20251122.log reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122/
mv reports/2025-10-cli-flags/phase_l/per_phi/trace_py_rot_vector_20251122_per_phi.* \
   reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122/

# Run comparison (will show zero C traces until C binary instrumented)
python scripts/compare_per_phi_traces.py \
  reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122/trace_py_rot_vector_20251122_per_phi.json \
  reports/2025-10-cli-flags/phase_l/rot_vector/c_trace_mosflm.log \
  > reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122/comparison_stdout.txt

# Run pytest collection
pytest --collect-only -q | tee reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122/pytest_collect.log
```

## Observations

- **Test suite health:** 653 tests collected successfully (no import/collection errors)
- **Harness execution:** Completed cleanly, generated all expected artifacts
- **Pixel intensity:** Final intensity for (685, 1039) = 2.38e-7 (non-zero, on-peak region as expected)
- **Deprecation warnings:** `datetime.utcnow()` warnings present but non-blocking

## Plan Sync

This diagnosis satisfies Phase L3k.3b requirements from `plans/active/cli-noise-pix0/plan.md:292`:
- ✅ Regenerated per-φ traces
- ✅ Captured to `base_vector_debug/20251122/`
- ✅ Attempted comparison (blocked by missing C traces)
- ⚠️ **Cannot isolate first divergent tensor until C per-φ instrumentation complete**

Next loop should either:
1. Instrument C binary for per-φ traces (requires production C modification), OR
2. Proceed directly to L3k.3c with targeted φ rotation fix based on existing H2 hypothesis, deferring C comparison until post-fix validation

**Status:** Evidence collection complete; C instrumentation blocking further progress on L3k.3b diagnosis.
