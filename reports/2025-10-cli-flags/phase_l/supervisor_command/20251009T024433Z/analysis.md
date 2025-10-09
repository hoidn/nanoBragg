# Supervisor Command Analysis — Phase O VG-5
## CLI-FLAGS-003 Closure Attempt

**Timestamp:** 20251009T024433Z
**Git SHA:** `7f74e3aa23041b45138834e57263a2845d27c04c`
**Status:** ⚠️ **BLOCKER — Normalization regression detected**

---

## Executive Summary

The Phase O supervisor rerun was executed per `plans/active/cli-noise-pix0/plan.md` task O1, but **revealed a critical regression**: the PyTorch implementation produces intensities **~126,000× higher** than the C reference, indicating the normalization bug discovered in Phase M3c is still present in the CLI path despite passing targeted tests.

### Key Metrics

| Metric | Value | Status | Expected |
|--------|-------|--------|----------|
| **Correlation** | 0.9966 | ✓ PASS | ≥0.98 |
| **Sum Ratio (Py/C)** | 126,451× | ⚠️ **CRITICAL** | ~1.16×10⁵ |
| **C Sum** | 6,490.82 | — | — |
| **Py Sum** | 820,774,912 | ⚠️ **CRITICAL** | ~750,000 |
| **RMSE** | 42,014.24 | — | — |
| **Max |Δ|** | 58,741,636 | ⚠️ **CRITICAL** | ~60,000 |
| **Mean Peak Dist** | 37.79 px | ⚠️ HIGH | ~0 px |
| **Max Peak Dist** | 377.92 px | ⚠️ **CRITICAL** | ~0 px |

### Divergence Analysis

**C Reference (`c_stdout.txt`):**
- Max intensity: **446.254**
- Mean: 0.00104287
- RMS: 0.334386
- Statistics are physically reasonable for the given fluence and cell size

**PyTorch Implementation (`py_stdout.txt`):**
- Max intensity: **5.874×10⁷**
- Mean: 1.319×10²
- RMS: 4.201×10⁴
- Values are **~131,551× too high** relative to C

**Ratio:** 5.874×10⁷ / 446.254 ≈ **131,551×**

This magnitude matches the Phase M3c discovery where PyTorch was found to be 126,000× higher due to missing `/steps` normalization in `simulator.py`.

---

## Contradiction with Previous Evidence

### Expected Behavior (Phase N2)

The Phase N2 nb-compare run (`reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/`) reported:
- Correlation: **0.9852** (≥0.98 threshold)
- Sum ratio: **1.159×10⁵** (attributed to C-PARITY-001)

This was accepted as spec-compliant behavior under Option 1.

### Current Evidence (Phase O)

This supervisor rerun shows:
- Correlation: **0.9966** (higher, surprisingly)
- Sum ratio: **126,451** (≈9% higher than N2)

The sum ratio increased from ~116,000× to ~126,000×, indicating additional divergence beyond the documented C-PARITY-001 bug.

### Test Suite Status

The targeted tests **pass cleanly**:
```bash
$ KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py
tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c PASSED
tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c PASSED
============================== 2 passed in 2.06s ===============================
```

This suggests a **discrepancy between the test harness and the actual CLI execution path**.

---

## Root Cause Hypothesis

### H1: CLI Path Bypasses Normalization Fix (HIGH confidence)

The normalization fix landed in Attempts #188-189 modified `src/nanobrag_torch/simulator.py` to ensure `/steps` division occurs exactly once. However, the tests use a **simplified configuration** that may not exercise the full CLI argument parsing and config construction pipeline.

**Evidence:**
1. Tests pass (suggesting correct logic in `simulator.py`)
2. CLI fails (suggesting config construction issue)
3. The sum ratio (~126,000×) precisely matches the Phase M3c pre-fix ratio

**Hypothesis:** The CLI argument parser or `parse_and_validate_args` may be constructing a `SimulatorConfig` that results in a second `/steps` division being skipped or an incorrect `steps` value being computed.

### H2: Regression Between Phase N2 and Phase O (MEDIUM confidence)

The Phase N2 bundle was generated **before** the current commit (`7f74e3aa`). A code change between N2 and now may have re-introduced the bug.

**Evidence:**
- N2 sum ratio: 115,922
- O sum ratio: 126,451
- Difference: ~9.1% increase

**Action Required:** Compare the git diff between Phase N2 timestamp (20251009T020401Z) and current commit.

### H3: Test Coverage Gap (HIGH confidence)

The `test_cli_scaling_phi0.py` tests validate specific physical properties (rot_b, k_frac) but do **not** validate absolute intensity magnitude or sum ratios against the C reference.

**Evidence:** Test assertions focus on rotation matrices and Miller indices, not on final pixel intensities.

**Action Required:** Add regression test that runs full CLI and compares sum ratio to C reference within tolerance.

---

## Next Actions (for galph/supervisor)

### Immediate (blocking Phase O closure)

1. **Trace the CLI Path:**
   Generate a detailed execution trace showing:
   - How `steps` is computed in `__main__.py:parse_and_validate_args`
   - What value of `steps` reaches `simulator.py`
   - Where the normalization division occurs (or doesn't occur)

2. **Compare Phase N2 vs Phase O Configs:**
   Extract the effective config from both runs and diff them to identify what changed.

3. **Add CLI Integration Test:**
   Create `tests/test_cli_normalization_parity.py` that:
   ```python
   def test_cli_sum_ratio_vs_c():
       """Verify CLI produces intensities within 2× of C reference."""
       # Run C
       c_result = run_c_binary(args)
       # Run PyTorch CLI
       py_result = subprocess.run(["nanoBragg", *args])
       # Load and compare
       c_img = load_float_bin(c_result.floatfile)
       py_img = load_float_bin(py_result.floatfile)
       sum_ratio = py_img.sum() / c_img.sum()
       # Accept C-PARITY-001 divergence within bounds
       assert 1.10e5 <= sum_ratio <= 1.20e5, f"Sum ratio {sum_ratio} outside bounds"
   ```

4. **Git Bisect (if needed):**
   If regression is confirmed, bisect between:
   - Good: commit at Phase N2 timestamp
   - Bad: current commit `7f74e3aa`

### Follow-up (post-fix)

5. **Re-run Phase O:**
   After fix, regenerate this bundle and verify sum_ratio lands in [1.10e5, 1.20e5] per Option 1 tolerance.

6. **Update Plan:**
   Mark O1 as `[P]` (partial) with blocker reference; defer O2/O3 until fix lands.

7. **Document in ledger:**
   Add Attempt entry to `docs/fix_plan.md` under CLI-FLAGS-003 with:
   - Metrics from this run
   - Blocker status
   - Next actions

---

## C-PARITY-001 Attribution

Per `docs/bugs/verified_c_bugs.md:166-189`, the documented C-only bug (φ=0 rotation carryover) accounts for a sum_ratio of **~1.16×10⁵**. The current run shows **1.26×10⁵**, which is **~9% higher** than the documented divergence.

**Implication:** There is an **additional** ~10,000× scaling error beyond C-PARITY-001, strongly suggesting the Phase M3c normalization bug persists.

---

## Artifacts Inventory

All files stored in:
`reports/2025-10-cli-flags/phase_l/supervisor_command/20251009T024433Z/`

- ✅ `commands.txt` — Full invocation with metrics summary
- ✅ `env.json` — System/git metadata
- ✅ `sha256.txt` — Hashes for all binary/PNG files
- ✅ `c_stdout.txt` — C execution log (max_I=446.254)
- ✅ `c_stderr.txt` — Empty (no errors)
- ✅ `py_stdout.txt` — PyTorch execution log (max_I=5.874e+07)
- ✅ `py_stderr.txt` — Empty (no errors)
- ✅ `summary.json` — Machine-readable metrics
- ✅ `c.png` — C reference visualization
- ✅ `py.png` — PyTorch output visualization
- ✅ `diff.png` — Difference heatmap (reveals massive intensity error)
- ✅ `c_float.bin` — C float image (24 MB)
- ✅ `py_float.bin` — PyTorch float image (24 MB)
- ✅ `diff.bin` — Difference image (24 MB)
- ✅ `analysis.md` — This document

---

## Conclusion

**Phase O cannot close until the normalization regression is resolved.** The supervisor command execution succeeded (correlation ≥0.98), but the sum ratio divergence (~126,000× vs expected ~116,000×) indicates a **critical bug** that blocks acceptance.

**Recommended Path:**
1. Escalate to galph for diagnostic tracing (CLI path audit)
2. Add integration test covering CLI sum ratio
3. Fix normalization regression
4. Re-run Phase O with clean bundle
5. Close with VG-5 Attempt in ledgers

**Current Status:** CLI-FLAGS-003 remains `in_progress` with blocker documented.
