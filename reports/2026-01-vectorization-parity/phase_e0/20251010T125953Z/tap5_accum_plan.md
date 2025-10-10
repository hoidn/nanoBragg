# Tap 5.3 Oversample Accumulation Instrumentation Plan

**Initiative:** VECTOR-PARITY-001 — Restore 4096² benchmark parity
**Phase:** E15 (Tap 5.3 instrumentation brief)
**Author:** Ralph (galph steering)
**Date:** 2025-10-10
**Artifact Bundle:** `reports/2026-01-vectorization-parity/phase_e0/20251010T125953Z/`

---

## 1. Scope & Motivation

**Problem:**
Tap 5 (Attempt #30, #31) isolated a ~4× intensity discrepancy at edge pixel (0,0) between C (`I_before_scaling=1.415e5`) and PyTorch (`I_before_scaling=3.54e4`), while centre pixel (2048,2048) values agree (both zero). ω, capture, polar, and step counts match, indicating the divergence lies within the **oversample accumulation loop** — specifically how `F_cell²·F_latt²` terms are summed across subpixels.

**Hypothesis H2 (PRIMARY, 80% confidence):**
PyTorch and C handle per-subpixel intensity contributions differently during oversample accumulation. Potential mechanisms:
- Order-of-operations difference in multiplicative factor application
- Early vs late application of ω/capture/polar weights
- Numerical precision issue in floating-point accumulation (unlikely but possible with 4× delta)

**Goal:**
Before writing any remediation code, capture per-subpixel accumulation logs from **both implementations** to:
- Identify whether the 4× gap accumulates gradually (different weights per subpixel) or appears suddenly (single-term miscalculation)
- Verify loop ordering and factor application semantics match `specs/spec-a-core.md:241-259`
- Provide evidence-backed fix input for Phase F remediation

---

## 2. Logging Schema (Normative)

### 2.1 Required Variables (Per Subpixel)

For **each of 4 subpixels** (oversample=2) at target pixels, log:

| Variable | Units | Description | Reference |
|----------|-------|-------------|-----------|
| `subpixel_idx` | — | Linear index (0–3) in row-major order (s_sub × oversample + f_sub) | — |
| `s_sub`, `f_sub` | — | Slow/fast subpixel grid coordinates (0–1 for oversample=2) | — |
| `h_frac`, `k_frac`, `l_frac` | — | Fractional Miller indices (a·q, b·q, c·q) | spec-a-core.md:219 |
| `h0`, `k0`, `l0` | — | Rounded nearest-integer indices (ceil(x−0.5)) | spec-a-core.md:220 |
| `F_cell` | electrons | Structure factor amplitude (from HKL or default_F) | spec-a-core.md:232-240 |
| `F_latt` | — | Lattice shape factor (sincg for SQUARE model) | spec-a-core.md:221-231 |
| `I_term` | — | Intensity contribution = `F_cell²·F_latt²` | spec-a-core.md:241-244 |
| `I_accum` | — | Running accumulator **after** adding `I_term` | spec-a-core.md:241-244 |
| `omega` | sr | Solid angle for this subpixel | spec-a-core.md:197-199 |
| `capture_fraction` | — | Detector absorption weight (layer 0 only; thickness disabled in test) | spec-a-core.md:200-203 |
| `polar` | — | Polarization factor (Kahn model) | spec-a-core.md:208-213 |

### 2.2 Additional Context (Per Pixel, Once)

| Variable | Units | Description |
|----------|-------|-------------|
| `pixel_s`, `pixel_f` | — | Target pixel coordinates (slow, fast) |
| `steps_total` | — | Normalization denominator = sources × mosaic_domains × phisteps × oversample² |
| `I_before_scaling` | — | Final accumulator after all subpixels (before r_e²·fluence/steps scaling) |
| `omega_last`, `capture_last`, `polar_last` | — | Last-computed values (if oversample_* toggles are off) |

### 2.3 Acceptance Criteria (Per-Subpixel Parity)

- **F_cell/F_latt parity:** Relative error ≤1e-6 for each subpixel
- **I_term parity:** Relative error ≤1e-6 for `F_cell²·F_latt²`
- **I_accum progression:** Running sum must match between C and PyTorch at each subpixel boundary
- **Factors:** ω, capture, polar must match within ≤1e-9 absolute (already validated in Tap 5 E8/E9)

---

## 3. Target Pixels & ROI

**Rationale:**
Edge pixel (0,0) exhibits the 4× discrepancy; centre pixel (2048,2048) serves as control (both implementations yield zero intensity).

| Pixel (s, f) | Purpose | Expected Behavior |
|--------------|---------|-------------------|
| (0, 0) | **Primary diagnostic** — edge pixel with steep viewing angle; 4× I_before_scaling gap identified in Tap 5 | Non-zero intensity; high ω asymmetry candidate; default_F usage confirmed (Tap 4) |
| (2048, 2048) | **Control** — centre pixel, direct beam, symmetric subpixel geometry | Zero intensity (F_cell=default_F, background-only); all subpixels should report identical Miller indices (0,0,0) |

**Detector parameters** (from `input.md` commands):
- Detector: 4096×4096 pixels, pixel=0.05 mm, distance=500 mm
- Wavelength: λ=0.5 Å
- Crystal: cubic 100×100×100 Å, N=5, default_F=100
- ROI: Full-frame (no ROI restriction for trace runs)
- Oversample: 2 (yields 4 subpixels per pixel)

---

## 4. Guard Names & Environment Triggers

### 4.1 PyTorch Trace (`scripts/debug_pixel_trace.py`)

- **Guard:** `--taps accum` (or `intensity_accum` if `--taps` accepts comma-separated list)
- **Implementation:** Extend `scripts/debug_pixel_trace.py` with `collect_accum_tap()` helper (mirroring `collect_f_cell_tap` / `collect_hkl_subpixel_tap` pattern)
- **Output format:** JSON per pixel: `pixel_{s}_{f}_accum.json` containing:
  ```json
  {
    "pixel_s": 0, "pixel_f": 0,
    "oversample": 2,
    "steps_total": 4,
    "subpixels": [
      {
        "subpixel_idx": 0, "s_sub": 0, "f_sub": 0,
        "h_frac": -7.898, "k_frac": 39.352, "l_frac": -39.352,
        "h0": -8, "k0": 39, "l0": -39,
        "F_cell": 100.0, "F_latt": 12.456,
        "I_term": 155175.936, "I_accum": 155175.936,
        "omega": 8.8611e-09, "capture_fraction": 1.0, "polar": 0.961277
      },
      { /* subpixel 1 */ },
      { /* subpixel 2 */ },
      { /* subpixel 3 */ }
    ],
    "I_before_scaling": 35430.12,
    "omega_last": 8.8615e-09, "capture_last": 1.0, "polar_last": 0.961280
  }
  ```
- **Stdout summary:** Brief table of subpixel I_term deltas + final accumulator

### 4.2 C Binary (`golden_suite_generator/nanoBragg.c`)

- **Guard:** `TRACE_C_TAP5_ACCUM` environment variable (non-empty = enabled)
- **Instrumentation location:** Inside oversample loop (likely near existing `TRACE_C_TAP5` guards added in Attempt #30, around line 3400-3450)
- **Output format:** Line-per-subpixel to stdout/stderr:
  ```
  TRACE_C_TAP5_ACCUM: pix=(0,0) sub_idx=0 s_sub=0 f_sub=0 h_frac=-7.898 k_frac=39.352 l_frac=-39.352 h0=-8 k0=39 l0=-39 F_cell=100.0 F_latt=12.456 I_term=1.55176e+05 I_accum=1.55176e+05 omega=8.8611e-09 capture=1.0 polar=0.961277
  TRACE_C_TAP5_ACCUM: pix=(0,0) sub_idx=1 s_sub=0 f_sub=1 h_frac=... I_accum=3.10352e+05 ...
  TRACE_C_TAP5_ACCUM: pix=(0,0) sub_idx=2 ...
  TRACE_C_TAP5_ACCUM: pix=(0,0) sub_idx=3 ... I_accum=6.20704e+05
  TRACE_C_TAP5_ACCUM: pix=(0,0) FINAL I_before_scaling=1.4152e+05 omega_last=8.8615e-09 capture_last=1.0 polar_last=0.961280
  ```
- **Post-processing:** Parse lines into JSON for parity comparison (manual or scripted)

---

## 5. Execution Commands (Template)

### 5.1 PyTorch Tap 5.3 (Phase E16)

```bash
# From repo root
STAMP=20251010T125953Z  # (or successor timestamp)

# Edge pixel (0,0)
KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py \
  --pixel 0 0 --oversample 2 --taps accum \
  --out-dir reports/2026-01-vectorization-parity/phase_e0/$STAMP/py_taps \
  --tag "edge_accum" \
  -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 \
     -distance 500 -detpixels 4096 -pixel 0.05

# Centre pixel (2048,2048)
KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py \
  --pixel 2048 2048 --oversample 2 --taps accum \
  --out-dir reports/2026-01-vectorization-parity/phase_e0/$STAMP/py_taps \
  --tag "centre_accum" \
  -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 \
     -distance 500 -detpixels 4096 -pixel 0.05

# Archive commands
echo "# PyTorch Tap 5.3 commands (E16)" >> reports/2026-01-vectorization-parity/phase_e0/$STAMP/commands.txt
echo "<full commands above>" >> reports/2026-01-vectorization-parity/phase_e0/$STAMP/commands.txt
```

**Expected artifacts:**
- `py_taps/pixel_0_0_accum.json`
- `py_taps/pixel_2048_2048_accum.json`
- `py_taps/accum_summary.md` (manual or auto-generated summary of subpixel progression)

### 5.2 C Tap 5.3 (Phase E17)

```bash
# Ensure C binary is instrumented and rebuilt
cd golden_suite_generator
make clean && make nanoBragg
cd ..

STAMP=20251010T125953Z
export TRACE_C_TAP5_ACCUM=1
export NB_C_BIN=./golden_suite_generator/nanoBragg

# Edge pixel (0,0) — redirect stderr to capture TRACE lines
TRACE_C_TAP5_ACCUM=1 "$NB_C_BIN" \
  -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 \
  -distance 500 -detpixels 4096 -pixel 0.05 \
  -floatfile /dev/null 2>&1 | grep "TRACE_C_TAP5_ACCUM.*pix=(0,0)" \
  > reports/2026-01-vectorization-parity/phase_e0/$STAMP/c_taps/pixel_0_0_accum.log

# Centre pixel (2048,2048)
TRACE_C_TAP5_ACCUM=1 "$NB_C_BIN" \
  -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 \
  -distance 500 -detpixels 4096 -pixel 0.05 \
  -floatfile /dev/null 2>&1 | grep "TRACE_C_TAP5_ACCUM.*pix=(2048,2048)" \
  > reports/2026-01-vectorization-parity/phase_e0/$STAMP/c_taps/pixel_2048_2048_accum.log

# Archive commands
echo "# C Tap 5.3 commands (E17)" >> reports/2026-01-vectorization-parity/phase_e0/$STAMP/commands.txt
echo "<full commands above>" >> reports/2026-01-vectorization-parity/phase_e0/$STAMP/commands.txt

# Clean up environment
unset TRACE_C_TAP5_ACCUM
```

**Expected artifacts:**
- `c_taps/pixel_0_0_accum.log`
- `c_taps/pixel_2048_2048_accum.log`
- `c_taps/accum_metrics.json` (parsed from logs via helper script if needed)

---

## 6. Spec References (Normative)

All instrumentation MUST align with the authoritative accumulation semantics:

### 6.1 Intensity Accumulation (`specs/spec-a-core.md:241-244`)

> **Intensity accumulation (additive term):**
> - I_term = (F_cell^2)·(F_latt^2).
> - Accumulator I (per pixel) starts at I_bg (background, see below) and adds I_term for every inner-loop combination.

**Interpretation:**
- Accumulator starts at `I_bg` (zero when -water 0 is set, as in our test)
- Each subpixel contributes `I_term = F_cell² × F_latt²`
- Running sum: `I_accum[n] = I_accum[n-1] + I_term[n]`

### 6.2 Oversample Last-Value Semantics (`specs/spec-a-core.md:245-259`)

> **Normalization caveat:**
> - If -oversample_thick is set, after each addition the entire current accumulator I is multiplied by the layer's capture fraction (rather than multiplying I_term).
> Similarly for -oversample_polar (multiply by polarization factor) and -oversample_omega (multiply by ω). This means the multiplicative factors apply to the running sum, not per-term, and thus depend on loop order and number of additions.
>
> **Final per-pixel scaling:**
> - Define steps = (number of sources) · (number of mosaic domains) · (phisteps) · (oversample^2).
> - After all loops (including all thickness layers and subpixels), compute:
>   - S = r_e^2 · fluence · I / steps.
>   - If -oversample_thick is NOT set, multiply S by the last computed capture fraction (from the last subpixel and last layer). If -oversample_polar is NOT set, multiply S by the last computed polarization factor. If -oversample_omega is NOT set, multiply S by the last computed ω. These "last value" applications are not averages; they depend on the final loop state for that pixel.

**Interpretation:**
- **Default behavior (oversample_omega=False):** Accumulate `I_term` values **without** multiplying by ω during the loop; apply ω **once** at the end using the last subpixel's value
- **Per-subpixel behavior (oversample_omega=True):** Multiply the **running accumulator** by ω after each I_term addition (not tested in this tap; our test uses default)

### 6.3 Miller Index Calculation (`specs/spec-a-core.md:219-220`)

> - Fractional Miller indices: h = a·q, k = b·q, l = c·q (dimensionless).
> - Nearest integer triplet: (h0, k0, l0) = round to nearest via ceil(x − 0.5).

**Verification:**
Both implementations should show identical (h0, k0, l0) for each subpixel at a given pixel (already validated in Tap 5.1 E12/E13).

---

## 7. Next-Step Checklist (Blocking Gate for E16/E17)

Before implementing Tap 5.3 instrumentation in either codebase:

- [x] Spec references §241-259 cited and quoted above
- [x] Logging schema defined (12 variables per subpixel + 4 summary variables)
- [x] Guard names chosen (`--taps accum` for PyTorch, `TRACE_C_TAP5_ACCUM` for C)
- [x] Target pixels confirmed (0,0 edge; 2048,2048 centre)
- [x] Acceptance thresholds documented (≤1e-6 relative for F_cell²·F_latt², running sum parity)
- [x] Command templates drafted (including env setup, output redirection, artifact paths)
- [x] Artifact naming convention established (`pixel_{s}_{f}_accum.{json|log}`)
- [x] Plan rows E15-E18 updated in `plans/active/vectorization-parity-regression.md` ✅

**Exit Criteria for This Planning Loop (E15):**
- [x] `tap5_accum_plan.md` committed with all sections complete
- [x] `commands.txt` placeholder exists in stamped report directory
- [x] `pytest --collect-only -q` executed and logged (no code changes, so no test regressions expected)
- [x] `docs/fix_plan.md` Attempt log updated referencing this artifact bundle

---

## 8. Risk Mitigation

**Risk 1:** Oversample loop instrumentation in C binary adds significant overhead (full 4096² run may timeout).
**Mitigation:** Instrument only for trace pixels (guard `if (spixel == target_s && fpixel == target_f)` before logging). Accept ~5s runtime penalty per pixel.

**Risk 2:** PyTorch trace helper does not currently support `--oversample` + `--taps accum` simultaneously (needs implementation).
**Mitigation:** Extend `scripts/debug_pixel_trace.py` in E16 task; use Attempt #25 (`collect_f_cell_tap`) as template; maintain backward compatibility with existing taps.

**Risk 3:** C binary may not expose subpixel-level loop state (if oversample loop is deeply nested without intermediate variables).
**Mitigation:** Review `nanoBragg.c` oversample loop structure (likely around lines 3000-3500 based on prior Tap 5 guards) before instrumenting; if unavailable, add temporary local variables for F_cell_sq/F_latt_sq/I_term within the loop.

**Risk 4:** Numerical precision difference (float32 vs float64) may introduce spurious ≤1e-6 deltas that obscure the 4× gap.
**Mitigation:** Use float64 for trace runs (already default in debug scripts); compare `I_accum` progression rather than individual `I_term` values to amplify systematic errors.

---

## 9. References

- **Spec:** `specs/spec-a-core.md:241-259` (accumulation + last-value semantics)
- **Plan:** `plans/active/vectorization-parity-regression.md:97-100` (Phase E table)
- **Hypothesis Doc:** `reports/2026-01-vectorization-parity/phase_e0/20251010T113608Z/comparison/tap5_hypotheses.md` (H2 PRIMARY)
- **Previous Taps:**
  - E8/E9 (Tap 5 intensity pre-norm): `reports/2026-01-vectorization-parity/phase_e0/20251010T110735Z/` (PyTorch), `20251010T112334Z/` (C)
  - E12/E13 (Tap 5.1 HKL audit): `20251010T115342Z/` (PyTorch), `20251010T121436Z/` (C)
  - E14 (Tap 5.2 HKL bounds): `20251010T123132Z/`

---

## 10. Appendix: Subpixel Indexing Convention

For **oversample=2**, the 4 subpixels are indexed in **row-major (slow-major) order**:

| subpixel_idx | s_sub | f_sub | Offset from pixel corner (slow, fast) |
|--------------|-------|-------|---------------------------------------|
| 0            | 0     | 0     | (0.25, 0.25) pixel widths             |
| 1            | 0     | 1     | (0.25, 0.75)                          |
| 2            | 1     | 0     | (0.75, 0.25)                          |
| 3            | 1     | 1     | (0.75, 0.75)                          |

**Rationale:**
Subpixel centers are at `(s + (s_sub + 0.5)/oversample, f + (f_sub + 0.5)/oversample)` in pixel coordinates. For pixel (0,0):
- subpixel 0: (0.25, 0.25)
- subpixel 1: (0.25, 0.75)
- subpixel 2: (0.75, 0.25)
- subpixel 3: (0.75, 0.75)

This convention matches `torch.meshgrid(..., indexing="ij")` output order and C nested loops `for (s_sub) for (f_sub)`.

---

**End of Tap 5.3 Instrumentation Plan**
**Next:** Execute Phase E16 (PyTorch capture) and E17 (C mirror) per template commands above.
