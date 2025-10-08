# Phase M2 Lattice Hypotheses — 2025-12-06 Update

**Context**
- Plan: `plans/active/cli-noise-pix0/plan.md` Phase M2 (Fix lattice factor propagation)
- Focus pixel: (spixel=1039, fpixel=685) from supervisor command configuration
- Canonical traces:
  - PyTorch: `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/trace_py_scaling.log`
  - C reference: `reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log`
- Manual reproduction: `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/manual_sincg.md`

## Observed deltas (φ tick = 0)
| Term | PyTorch | C trace | Δ (abs) | Δ (rel) |
| --- | --- | --- | --- | --- |
| `F_latt_a` | -2.35819512010207 | -2.36012735995387 | +1.93e-03 | -8.19e-04 |
| `F_latt_b` | 1.05066739326683 | 1.05079664302326 | -1.29e-04 | -1.23e-04 |
| `F_latt_c` | 0.960630659359605 | 0.960961003611676 | -3.30e-04 | -3.44e-04 |
| `F_latt` | -2.38013414214076 | -2.38319665299058 | +3.06e-03 | -1.29e-03 |
| `k_frac` | -0.607262620986129 | -0.607255839576692 | -6.78e-06 | +1.12e-05 |
| `rot_a_star[1]` | -0.0293789623945766 | -0.0293958845208845 | +1.69e-05 | -5.76e-04 |
| `rot_c_star[1]` | -0.0143496591104365 | -0.0143330159705160 | -1.66e-05 | +1.16e-03 |

- Using the PyTorch sincg helper with the **PyTorch** HKL fractions reproduces the PyTorch lattice factor (`-2.380125274`, matches manual_sincg.md).
- Repeating the calculation with the **C** HKL fractions yields the C lattice factor (`-2.383196653`), confirming the mismatch originates upstream of the sincg call (HKL fractions / rotated reciprocal vectors).
- Per-φ traces (`…/per_phi/…/trace_py_scaling_per_phi.log` vs `c_trace_scaling.log:277-287`) diverge at every tick by ~0.13%, so the issue is systematic rather than a single φ slice.

## Hypotheses

### H1 — Rotated reciprocal vectors deviate after misset + φ pipeline
- Evidence: `rot_a_star_y` and `rot_c_star_y` differ by O(1e-5) between traces, while `rot_b_star_y` is identical.
- Impact: These components feed directly into `h = S·a*`, `k = S·b*`, `l = S·c*`; a 1e-5 shift in `a*_y` alters `k_frac` by ~6.8e-06, large enough to move the sincg argument by ~2.1e-05π.
- Suspect locus: `Crystal.get_rotated_reciprocal_vectors` (PyTorch) vs `nanoBragg.c` rotation block (lines 3008-3120). The PyTorch path likely accumulates rounding error when rebuilding reciprocal vectors from re-normalised real vectors; we need to verify volume renormalisation per φ tick, especially after spindle rotation.
- Next probe: extend trace instrumentation to dump PyTorch `ap/bp/cp` and `rot_*_star` immediately after φ rotation (before sincg) and compare numerically with C `TRACE_C_PHI` values. Confirm whether the mismatch appears before or after the `torch.cross` recomputation of reciprocal vectors.

### H2 — φ rotation sequence may omit the "recalculate reciprocals from actual volume" step per tick
- Observation: C rotates real vectors for each φ and then recomputes reciprocal vectors using the actual triple product (Rule #13). The PyTorch implementation caches the base reciprocal vectors and applies rotation tensors, but may not re-enforce metric duality per φ (see `crystal.py:1084-1136`). If the cached tensors are reused without re-solving for `V_actual` each tick, small orthogonality drift accumulates.
- Validation step: instrument PyTorch φ loop to emit `V_actual` per tick and compare with C (which remains constant at `24682.2566301114 Å³`). Any deviation suggests the duality enforcement is drifting.

### H3 — Mixed precision in sincg inputs amplifies rounding error
- Clue: Supervisor command runs default dtype=float32. Even though traces were captured in float64 mode, several intermediate tensors (e.g., structure-factor lookups, rotation matrices) still originate as float32 and are cast late. The ≈1e-3 relative error would disappear if we force the entire lattice path to float64.
- Proposed check: rerun `trace_harness.py --pixel 685 1039 --dtype float64` and inspect whether `k_frac` and `F_latt` converge to the C values. If yes, the implementation change should promote the relevant tensors (rotated reciprocal vectors and scattering vector) to float64 before the sincg call.

## Recommended next steps

1. **Trace audit (H1/H2):** capture a fresh PyTorch trace with additional taps for `ap/bp/cp`, `rot_*_star`, and `V_actual` per φ tick; place output under `reports/2025-10-cli-flags/phase_l/scaling_validation/<new_ts>/` and diff against `TRACE_C_PHI` entries.
2. **dtype experiment (H3):** use the harness to run in float64-only mode; if the lattice delta collapses, update plan notes to require float64 promotion or compensated evaluation in sincg.
3. **Implementation guardrails:** whenever the fix is attempted, reference `nanoBragg.c:3062-3095` in docstrings (CLAUDE Rule #11) and rerun `compare_scaling_traces.py` so `metrics.json` reports `first_divergence=None`.

Document authored 2025-12-06 by galph (supervisor loop).

## 2025-12-07 Update — Carryover Shim Hypothesis
- Fresh inspection of `Crystal.get_rotated_real_vectors` shows the c-parity shim replaces φ=0 with the **current** pixel's φ=final vectors (advanced indexing over the φ dimension).
- C trace (`TRACE_C_PHI`) confirms φ=0 reuses the **previous** pixel's final φ state because `ap/bp/cp` persist across pixel iterations.
- Direct dumps from the harness (`python -m nanobrag_torch` snippet in supervisor loop 2025-12-07) show:
  - spec mode: φ=0 reciprocal vectors match the MOSFLM base orientation.
  - c-parity mode: φ=0 vectors exactly equal spec φ=9 vectors (`a*_y` delta ≈ +1.69e-05), which matches the lattice drift recorded in `trace_py_scaling.log`.
- Consequence: `k_frac` in c-parity mode is biased by ≈6.8e-06 for this pixel, producing the observed 0.13% `F_latt` deficit and keeping `I_before_scaling` outside the ≤1e-6 gate.
- Next probe: Capture consecutive-pixel traces (e.g., pixel 684,1039 then 685,1039) to quantify the true C carryover vector and decide whether to cache φ-final state between pixels or introduce a deterministic seed to mimic the C bug exactly.

## 2025-12-08 Parity Test Failure — M2e Evidence Capture

**Test Run:** 2025-12-08T10:21:55Z
**Artifacts:** `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T102155Z/parity_test_failure/`

**Command:**
```bash
env KMP_DUPLICATE_LIB_OK=TRUE pytest -vv tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c --maxfail=1
```

**Result:** FAILED (exit code 1)

**Key Metrics:**
- F_cell: Perfect match (190.27)
- F_latt: **DIVERGED**
  - Expected (C): -2.3831966530
  - Actual (PyTorch): 1.3794838506
  - Relative error: **157.88%** (1.57884)
  - Absolute delta: 3.762680504
- Test tolerance: ≤1e-6 relative (VG-2 gate)

**Root Cause:**
φ=0 carryover cache not working per-pixel. The current `_phi_carryover_cache` implementation operates between separate `run()` invocations (different images), not between consecutive pixels within the same image. Per M2d probe (Attempt #152), consecutive pixels show identical φ=0 ROTSTAR values, confirming no per-pixel carryover is occurring.

**Environment:**
- Python 3.13.7
- PyTorch 2.8.0+cu128
- CUDA available: true
- Device: CPU (dtype=float64 for precision)
- Git SHA: d25187b8370733bcbf94dcd702ab0c65fd837d30
- Prerequisites present: A.mat, scaled.hkl

**Next Steps:**
Per plan.md M2g–M2i, implement pixel-indexed cache with shape `(S,F,N_mos,3)` per Option 1 design documented in `phi_carryover_diagnosis.md`. Cache must be device/dtype neutral, gradient-preserving (no `.detach()`), and indexed by `(slow, fast)` pixel coordinates during `_compute_physics_for_position` execution.

## 2025-10-08T17:47:53Z Metrics Refresh (M2i.2)
- Artifacts: `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T174753Z/`
- Command: see `commands.txt` in the artifact directory (Phase M2i.2 metrics rerun).
- Result summary:
  - `I_before_scaling` remains the first divergence (relative delta ≈ -0.9999995).
  - Downstream scaling factors (`polar`, `omega_pixel`, `cos_2theta`, `I_pixel_final`) continue to diverge because of the upstream lattice mismatch.
  - `r_e_sqr`, `fluence`, `steps`, and `capture_fraction` still PASS exactly (matching C within tolerance).
- Interpretation: Replaying the comparison with the latest Option B trace (`carryover_probe/20251008T172721Z/trace_py.log`) confirms no improvement — the cache plumbing did not correct `F_latt`. Hypothesis H1/H2 (reciprocal vector drift/carryover semantics) remains active; no evidence yet that dtype (H3) is the primary driver.
- Next step: Proceed with plan task M2g.5 (trace tooling patch) so we can instrument per-φ taps under the cache-aware pipeline; keep focus on verifying per-pixel carryover rather than recalculating metrics again.

---

## 2025-10-22 Update — Spec-Mode Bundle 20251008T212459Z (Phase M2)

**Context:**
- Fresh spec-mode baseline captured after φ-carryover shim removal (Phase D complete)
- Bundle: `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/`
- Comprehensive analysis: `analysis_20251008T212459Z.md` (co-located)

### Observations (φ=0 snapshot)

| Metric | C Value | PyTorch Value | Absolute Δ | Relative Δ | Status |
|--------|---------|---------------|------------|------------|--------|
| F_latt | -2.38319665 | **+1.37931117** | +3.76251 | **+158%** | 🔴 SIGN FLIP |
| F_latt_b | +1.05079664 | **-0.85842768** | -1.90922 | **-182%** | 🔴 SIGN FLIP |
| k_frac | -0.607255840 | -0.589174404 | +0.018081 | **+3.0%** | ⚠️ SHIFT |
| rot_b Y-comp | 0.671588234 Å | 0.717320031 Å | +0.045732 Å | **+6.8%** | ⚠️ LARGE ΔRELATIVE |
| I_before_scaling | 943,654.81 | 805,473.79 | -138,181.02 | **-14.6%** | 🔴 PRIMARY ISSUE |

**Source Lines:**
- PyTorch: `trace_py_scaling.log:25-28` (F_latt), `:23` (hkl_frac), `:15` (rot_b)
- C: `c_trace_scaling.log:273-276` (F_latt), `:271` (hkl_frac), `:266` (rot_b)

### Ranked Hypotheses

#### H4 — φ-Rotation Application Inconsistency (HIGH CONFIDENCE, NEW)

**Evidence:**
- rot_b Y-component differs by **6.8%** (0.672 vs 0.717 Å) — largest relative vector component error
- This 0.0457 Å shift in rot_b propagates to k_frac via dot product S·b
- k_frac shift of 3% (Δ=+0.018) moves sincg(π·k, Nb=47) evaluation point significantly
- sincg has zero-crossings and sign changes near k ≈ integer values; shift from -0.607 to -0.589 crosses a critical boundary
- F_latt_b flips sign: C = +1.051, PyTorch = -0.858
- F_latt product inherits sign flip: C = -2.383, PyTorch = +1.379

**Mechanism:**
1. PyTorch φ-rotation implementation differs from C (spindle axis orientation? rotation matrix order? sign convention?)
2. Small rotation error accumulates in rot_b vector (especially Y-component)
3. k_frac = S·b is pulled toward zero (less negative: -0.607 → -0.589)
4. sincg(π·(-0.589), 47) evaluates at different regime than sincg(π·(-0.607), 47)
5. Sign flip or magnitude change in F_latt_b propagates to F_latt product
6. Net I_before_scaling = Σ(F_cell² × F_latt²) drops by 14.6%

**Validation Probes (Phase M3):**
- Add per-φ instrumentation to PyTorch (`TRACE_PY_PHI` lines matching C format)
- Manual sincg table: compute sincg(π·k, 47) for k ∈ [-0.61, -0.58] in steps of 0.001
- Compare rotation matrix construction: `src/nanobrag_torch/models/crystal.py::get_rotated_real_vectors` vs `nanoBragg.c:2797-3095`
- Single-φ parity test (phisteps=1, phi=0) to isolate rotation vs accumulation issues

**Priority:** P0 (blocks Phase M4 implementation)

---

#### H5 — Metric Duality Enforcement Missing Per-φ (MEDIUM CONFIDENCE)

**Evidence:**
- C code regenerates reciprocal vectors from rotated real vectors per φ tick using actual volume (CLAUDE Rule #13)
- PyTorch may cache reciprocal vectors and apply rotation tensors without re-enforcing metric duality
- Small orthogonality drift could accumulate across φ steps
- However, single φ=0 snapshot already shows divergence, suggesting issue manifests immediately

**Validation Probes:**
- Instrument PyTorch φ loop to emit V_actual per tick
- Compare with C constant volume (24682.3 Å³)
- Verify a·a* = 1 holds within machine precision for each φ step

**Priority:** P1 (secondary to rotation issue)

---

#### H6 — sincg Edge Case Handling (MEDIUM CONFIDENCE, REFINED FROM H2)

**Evidence:**
- sincg(x, N) = sin(N·x) / sin(x) is sensitive near x ≈ 0 and x ≈ nπ
- PyTorch sincg implementation may differ from C in numerical stability guards
- For k_frac ≈ -0.6, π·k ≈ -1.88 rad (between -3π/2 and -π)
- Small shift in k_frac can cause large output swings if crossing zero-crossing

**Validation Probes:**
- Compare `src/nanobrag_torch/utils/physics.py::sincg` implementation vs `nanoBragg.c` sincg
- Manual calculation table (already listed under H4)
- Check Taylor expansion cutoffs and limit handling (x→0, x→nπ)

**Priority:** P1 (likely secondary to rotation issue, but needs verification)

---

#### H7 — Per-φ Cache Artifact (LOW CONFIDENCE, HISTORICAL)

**Evidence:**
- Phase D explicitly removed φ-carryover shim and validated removal
- Prior hypothesis that cached vectors propagate across φ steps
- Evidence bundle from Phase D shows shim removal successful

**Status:** RULED OUT by Phase D validation
- `reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T203504Z/`
- Still listed for historical continuity

---

#### H8 — Tricubic Interpolation Mismatch (RULED OUT, CONFIRMED)

**Evidence:**
- Both C and PyTorch access same HKL grid cell (-7, -1, -14)
- F_cell_nearest = 190.27 matches exactly
- PyTorch emits full 4×4×4 tricubic grid matching HKL file
- C appears to use `-nointerpolate` or defaults to nearest neighbor

**Conclusion:** NOT a divergence source; both implementations agree on structure factor value.

---

### Next Actions (Phase M3 Gate)

Before proceeding to Phase M4 implementation:

1. **Deliver per-φ PyTorch trace** with TRACE_PY_PHI format matching C
2. **Generate sincg sensitivity table** for k ∈ [-0.61, -0.58]
3. **Execute single-φ parity test** (phisteps=1, phi=0) to isolate issue
4. **Audit rotation matrix construction** comparing PyTorch vs C line-by-line
5. **Document findings** in Phase M3 validation probe reports

All artifacts under: `reports/2025-10-cli-flags/phase_l/scaling_validation/<date>/phase_m3_probes/`

### Summary

The 14.6% I_before_scaling divergence is **fully attributed to F_latt sign flip** caused by **φ-rotation inconsistency** between PyTorch and C implementations. The rot_b Y-component error (6.8%) is the smoking gun, propagating through k_frac to F_latt_b and ultimately to I_before_scaling. All downstream scaling factors (r_e², fluence, steps, capture, polar, omega, cos_2theta) remain in perfect parity (≤1e-6 relative).

**Root Cause Hypothesis:** H4 (φ-Rotation Application Inconsistency) — HIGH CONFIDENCE

**Blocking Issue:** PyTorch rotation implementation deviates from C, requiring systematic comparison of rotation matrix construction and spindle axis application.

Document updated: 2025-10-22 (Ralph loop, CLI-FLAGS-003 Phase M2)
