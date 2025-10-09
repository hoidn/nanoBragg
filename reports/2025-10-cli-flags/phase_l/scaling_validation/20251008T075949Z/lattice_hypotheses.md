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
# H4 Closure Addendum — 2025-10-08 Phase M4d

**Context:**
- Plan Phase M4d: Evidence capture after normalization fix (Attempts #188-#189, commit fe3a328)
- Previous status: H4 hypothesis elevated to HIGH CONFIDENCE (φ-rotation application inconsistency)
- Artifact bundle: `reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/`

## Status: PARTIALLY RESOLVED (Normalization Fix Applied, Upstream Issue Remains)

### Findings

**Normalization Fix Verification:**
- Code inspection confirmed single `/steps` division at `simulator.py:1127`
- Comments at lines 956 and 1041 explicitly state "Do NOT divide by steps here"
- Implementation correctly matches spec (specs/spec-a-core.md:247-250)

**Trace Comparison Results (2025-10-08):**
- PyTorch trace generated: 114 TRACE_PY lines captured successfully
- Comparison script executed against Phase M1 baseline (20251008T212459Z)
- **first_divergence:** I_before_scaling (STILL PRESENT)
- **Relative delta:** -14.6% (unchanged from Phase M2 analysis)

| Factor | Status | Notes |
|--------|--------|-------|
| I_before_scaling | 🔴 DIVERGENT | C: 943,654.81 vs PyTorch: 805,473.79 (-14.6%) |
| r_e_sqr | ✅ PASS | Exact match |
| fluence | ✅ PASS | Exact match |
| steps | ✅ PASS | Both = 10 |
| capture_fraction | ✅ PASS | Both = 1.0 |
| polar | ✅ PASS | δ_rel = -4.0e-08 |
| omega_pixel | ✅ PASS | δ_rel = -4.8e-07 |
| cos_2theta | ✅ PASS | δ_rel = -5.2e-08 |
| I_pixel_final | 🔴 DIVERGENT | Inherits I_before_scaling deficit (-14.6%) |

### Analysis

The normalization fix addressed the `/steps` division issue but did **NOT** eliminate the I_before_scaling divergence. This confirms:

1. **H4 remains the root cause:** The φ-rotation inconsistency affecting rot_b Y-component (+6.8%) propagates through k_frac (+3.0%) to F_latt (sign flip), ultimately causing the I_before_scaling deficit.

2. **Normalization was a red herring:** The -14.6% delta originated entirely from upstream physics (F_latt calculation), not from missing normalization steps. The fix was correct but addressed a different concern.

3. **All downstream factors pristine:** The perfect parity (≤1e-6) for all scaling factors confirms the issue is isolated to I_before_scaling accumulation, not final scaling.

### Revised Hypothesis Status

**H4 — φ-Rotation Application Inconsistency**
- **Status:** HIGH CONFIDENCE → **CONFIRMED PRIMARY CAUSE**
- **Evidence:** Normalization fix did not change divergence magnitude
- **Mechanism:** rot_b error → k_frac shift → F_latt sign flip → I_before_scaling deficit
- **Required Fix:** Address rotation matrix construction in `Crystal.get_rotated_real_vectors`

### Recommended Next Steps

The Phase M3 validation probes documented in the 2025-10-22 update remain the correct path forward:

1. **Per-φ instrumentation** (M3a complete, implementation deferred)
2. **Sincg sensitivity table** (M3b complete: zero-crossing at k≈-0.5955)
3. **Single-φ parity test** (M3c complete: identified 126,000× normalization error, now fixed)
4. **Rotation matrix audit** (M3d complete: confirmed rot_b +6.8% Y-component error)

**Actionable Item:** Investigate root cause of rot_b rotation error per M3d findings:
- Compare `src/nanobrag_torch/models/crystal.py::get_rotated_real_vectors` (lines 1084-1136) with `nanoBragg.c:2797-3095`
- Verify spindle axis orientation, rotation matrix order, and sign conventions
- Check per-φ metric duality enforcement (recalculate reciprocal vectors from actual volume)

### Documentation Updates

This finding should trigger:
1. Update `docs/fix_plan.md` Attempt #190 to note Phase M4d evidence complete, divergence persists
2. Keep CLI-FLAGS-003 status as BLOCKED pending rotation fix
3. Mark Phase M4d as [P] (partially complete - evidence captured, parity not achieved)
4. Phase M5 (CUDA validation) and M6 (ledger sync) remain deferred

### Artifacts Generated

- `trace_py_scaling.log` — Post-fix PyTorch trace (114 lines)
- `compare_scaling_traces.txt` — Detailed factor comparison
- `metrics.json` — Machine-readable results showing persistent divergence
- `run_metadata.json` — Execution metadata
- `blockers.md` — Detailed blocker documentation for supervisor escalation
- `diff_trace.md` — Comprehensive analysis summary
- `commands.txt` — Reproduction commands
- `sha256.txt` — Artifact manifest
- `lattice_hypotheses_h4_closure.md` — This document

### Supervisor Escalation

**Question for supervisor:**
Given that the normalization fix is correct but I_before_scaling divergence persists, should:
1. A fresh C baseline trace be generated with verified parameters?
2. Phase M4 be considered blocked pending rotation matrix fix?
3. The rotation fix be prioritized before continuing M4d closure?

The evidence bundle is complete for documentation purposes, but the parity gate (first_divergence = None) remains unmet.

---
Document appended: 2025-10-08 (Ralph loop i=190, CLI-FLAGS-003 Phase M4d)

---

# H4/H5 CLOSURE — Option 1 Decision (2025-12-20)

## Executive Summary
Hypotheses H4 (φ-Rotation Application Inconsistency) and H5 (Metric Duality Enforcement Missing Per-φ) are now **CLOSED** with the following resolution:

**PyTorch implements spec-compliant behavior** per `specs/spec-a-core.md:204-214`. The observed 14.6% I_before_scaling divergence is caused by **C-PARITY-001**, a documented bug in the C code where φ=0 reuses stale vectors from the previous pixel.

## Decision: Option 1 (Accept Spec-Compliant Divergence)

### Rationale
1. **Spec Compliance (Normative):**
   - Spec requires: "Fresh rotation of real-space vectors from newly rotated reciprocal vectors at each φ step"
   - PyTorch implements this correctly: `src/nanobrag_torch/models/crystal.py:1194-1292`
   - C code violates spec: carries over φ-final state from previous pixel at φ=0

2. **C Bug Documentation:**
   - C-PARITY-001 fully documented: `docs/bugs/verified_c_bugs.md:166-204`
   - Root cause: `ap/bp/cp` persist across pixel iterations in C code
   - Impact: 6.8% rot_b error → 3.0% k_frac shift → F_latt sign flip → 14.6% intensity deficit

3. **Test Coverage:**
   - Spec-compliant tests pass: `tests/test_cli_scaling_phi0.py` (2/2 PASSED)
   - Tests validate PyTorch matches spec, NOT buggy C behavior

### Impact on Hypotheses

**H4 (φ-Rotation Application Inconsistency):**
- **Status:** RESOLVED (No inconsistency—PyTorch is correct)
- **Finding:** PyTorch rotation implementation is spec-compliant
- **C Divergence:** Expected and documented (C-PARITY-001 bug)
- **Evidence:** rot_b Y = 0.717320 Å (PyTorch) matches C base b = 0.71732 Å
- **C trace:** rot_b Y = 0.671588 Å (from previous pixel carryover)

**H5 (Metric Duality Enforcement Missing Per-φ):**
- **Status:** RESOLVED (Duality correctly enforced)
- **Finding:** PyTorch implements CLAUDE Rules #12/#13 correctly
- **Implementation:** Conditional reciprocal recomputation matches spec intent
- **Evidence:** `src/nanobrag_torch/models/crystal.py:1194-1292` (docstring references `c_phi_rotation_reference.md`)

### Closure Metrics

| Aspect | Status | Evidence |
|--------|--------|----------|
| Spec Compliance | ✅ ACHIEVED | `specs/spec-a-core.md:204-214` |
| Implementation | ✅ CORRECT | `src/nanobrag_torch/models/crystal.py:1194-1292` |
| Test Coverage | ✅ PASSING | `tests/test_cli_scaling_phi0.py` (2/2) |
| C Bug Documented | ✅ COMPLETE | `docs/bugs/verified_c_bugs.md:166-204` |
| Optional C-Parity Mode | ⏸️ DEFERRED | Phase M6 (available if needed) |

## Artifacts

**Option 1 Bundle:**
- Location: `reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/20251009T011729Z/`
- Contents:
  - `blocker_analysis.md` (with Option 1 addendum)
  - `summary.md` (decision rationale)
  - `commands.txt` (reproduction steps)
  - `env.json` (environment metadata)
  - `sha256.txt` (artifact manifest)

**Implementation Evidence:**
- Fix landed: commit e2bc0ed
- C reference documented: `reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251009T005448Z/c_phi_rotation_reference.md`
- Test validation: `tests/test_cli_scaling_phi0.py` (2/2 PASSED)

## Future Work

**Phase M6 (Optional):** C-Parity Emulation Mode
- Add `--c-parity-mode` flag to reproduce C-PARITY-001 for legacy validation
- Default behavior remains spec-compliant
- Deferred unless validation against legacy C traces becomes critical

**Maintenance:**
- Keep C-PARITY-001 documented in `docs/bugs/verified_c_bugs.md`
- Reference this closure when explaining C trace divergence
- Update validation scripts to flag expected φ=0 discrepancy (Phase M5e)

## References
- **Normative Spec:** `specs/spec-a-core.md:204-214` (φ rotation pipeline)
- **C Bug Dossier:** `docs/bugs/verified_c_bugs.md:166-204` (C-PARITY-001)
- **Implementation:** `src/nanobrag_torch/models/crystal.py:1194-1292`
- **Architecture:** `arch.md` ADR-02, Core Rules #12/#13
- **Plan:** `plans/active/cli-noise-pix0/plan.md` Phase M5
- **Fix Plan:** `docs/fix_plan.md` CLI-FLAGS-003

---

**Document Updated:** 2025-12-20 (Ralph loop i=196, CLI-FLAGS-003 Phase M5d)
**Status:** H4/H5 CLOSED (Spec-compliant implementation confirmed)
