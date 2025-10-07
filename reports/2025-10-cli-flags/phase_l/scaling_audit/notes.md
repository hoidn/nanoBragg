# Phase L2b PyTorch Trace Capture — Workflow Log

**Date:** 2025-10-17
**Engineer:** Ralph (Loop i=62, evidence-only mode)
**Plan Reference:** `plans/active/cli-noise-pix0/plan.md` Phase L2b
**Task:** Generate PyTorch scaling trace for pixel (685, 1039) to mirror C trace

---

## Workflow Steps

### Step 0: Verify Editable Install
**Command:**
```bash
pip install -e .
```

**Output:**
```
Requirement already satisfied (editable install verified)
Location: /home/ollie/miniconda3/envs/myenv/lib/python3.13/site-packages
Editable project location: /home/ollie/Documents/tmp/nanoBragg
```

**Status:** ✅ Editable install active

---

### Step 1: Review Instrumentation Guidance
**File:** `reports/2025-10-cli-flags/phase_l/scaling_audit/instrumentation_notes.md`

**Expected TRACE keys (from lines 1-48):**
- `I_before_scaling` — Raw accumulated intensity before normalization
- `r_e_sqr` — Thomson cross section (7.94079248018965e-30 m²)
- `fluence_photons_per_m2` — Total X-ray fluence (1e24)
- `steps` — Normalization divisor (sources × mosaic × phi × oversample² = 10)
- `oversample_thick` — Thickness oversample flag (0 = use last-value)
- `oversample_polar` — Polarization oversample flag (0 = use last-value)
- `oversample_omega` — Solid angle oversample flag (0 = use last-value)
- `capture_fraction` — Detector absorption (1.0 for no thickness)
- `polar` — Kahn polarization factor (0.91463969894451)
- `omega_pixel` — Solid angle (4.20412684465831e-07 sr)
- `I_pixel_final` — Final scaled intensity (2.88139542684698e-07)

**Status:** ✅ Fields documented in harness

---

### Step 2: Prepare Harness Skeleton
**File:** `reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py`

**CLI flags added:**
- `--pixel SLOW FAST` — Target pixel coordinates
- `--out FILENAME` — Output trace filename
- `--config {supervisor}` — Config preset selector
- `--device {cpu,cuda}` — PyTorch device
- `--dtype {float32,float64}` — Tensor precision (default float32)

**Status:** ✅ Harness skeleton created with argparse

---

### Step 3: Load Supervisor Parameters
**Source:** `reports/2025-10-cli-flags/phase_i/supervisor_command/README.md:33-75`

**Parameters loaded into `config_snapshot.json`:**
```json
{
  "crystal": {
    "N_cells": [36, 47, 29],
    "phi_start_deg": 0.0,
    "osc_range_deg": 0.1,
    "phi_steps": 10,
    "mosaic_spread_deg": 0.0,
    "mosaic_domains": 1,
    "spindle_axis": [-1.0, 0.0, 0.0]
  },
  "detector": {
    "distance_mm": 231.27466,
    "pixel_size_mm": 0.172,
    "spixels": 2527,
    "fpixels": 2463,
    "beam_center_s": 213.90708,
    "beam_center_f": 217.742295,
    "convention": "CUSTOM",
    "pivot": "SAMPLE",
    "oversample": 1
  },
  "beam": {
    "wavelength_A": 0.9768,
    "polarization_factor": 0.0,
    "flux": 1e18,
    "exposure_s": 1.0,
    "beam_size_mm": 1.0
  }
}
```

**Status:** ✅ Config snapshot will be generated on execution

---

## Execution Log

### Run Timestamp: [TO BE FILLED]

**Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --out trace_py_scaling.log --config supervisor
```

**Expected artifacts:**
1. `trace_py_scaling.log` — TRACE_PY output
2. `trace_py_env.json` — Environment snapshot
3. `config_snapshot.json` — CLI arg/param dump
4. `trace_py_stdout.txt` — Stdout capture
5. `trace_py_stderr.txt` — Stderr capture

**Execution status:** [TO BE FILLED AFTER RUN]

---

## Notes

- Default dtype: float32 (per arch.md §14)
- Device: CPU (CUDA available for optional smoke if needed)
- Harness honours `-nonoise` implicitly (no noise generation step)
- Config uses MOSFLM A.mat + scaled.hkl from current directory
- Pixel (685, 1039) matches C trace target per instrumentation_notes.md line 52

---

## Observed Issues

[TO BE FILLED IF HARNESS RAISES OR PRODUCES UNEXPECTED OUTPUT]

---

## Verification

### Selector Check (Step 12 per input.md)
**Command:**
```bash
pytest --collect-only -q tests/test_cli_scaling.py::test_f_latt_square_matches_c
```

**Expected:** Test collection succeeds without import errors

**Status:** [TO BE FILLED]

---

### Manual Trace Review (Step 13 per input.md)
**Sanity checks against C trace (`c_trace_scaling.log`):**
- `steps == 10` ✓/✗
- `fluence ≈ 1e24` ✓/✗
- `omega_pixel ≈ 4.2e-7` ✓/✗
- `polar ≈ 0.9146` ✓/✗

**Deviations > 5%:** [TO BE FILLED]

---

### Git Status Check (Step 14 per input.md)
**Command:**
```bash
git status --short
```

**Expected files:**
```
?? reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py
?? reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log
?? reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_env.json
?? reports/2025-10-cli-flags/phase_l/scaling_audit/config_snapshot.json
?? reports/2025-10-cli-flags/phase_l/scaling_audit/notes.md
```

**Status:** [TO BE FILLED]

---

## Next Actions

- Execute harness command (input.md "Do Now")
- Capture stdout/stderr to dedicated files
- Update this notes.md with timestamps and outcomes
- Append Phase L2b summary to docs/fix_plan.md Attempt history

---

---

## Execution Log — Final Attempt (2025-10-17)

### Run Timestamp: 2025-10-17

**Command:**
```bash
export PYTHONPATH=src && export KMP_DUPLICATE_LIB_OK=TRUE && python -m nanobrag_torch \
  -mat A.mat -hkl scaled.hkl -lambda 0.9768 -distance 231.27466 -pixel 0.172 \
  -detpixels_s 2527 -detpixels_f 2463 -Xclose 211.818 -Yclose 217.322 \
  -phi 0.0 -osc 0.1 -phisteps 10 -Na 36 -Nb 47 -Nc 29 \
  -mosaic 0.0 -mosaic_dom 1 -flux 1e18 -exposure 1.0 -beamsize 1.0 \
  -spindle_axis -1 0 0 -trace_pixel 685 1039
```

**Execution status:** ✅ SUCCESS

**Artifacts created:**
1. `trace_py_scaling.log` — 40 lines of TRACE_PY output ✅
2. `trace_py_env.json` — Environment snapshot ✅
3. `config_snapshot_final.json` — CLI parameters ✅
4. `trace_py_cli_full.log` — Complete stdout/stderr capture ✅

### Key Findings

**Convention Detection:**
- PyTorch auto-selected CUSTOM convention with basis vectors:
  - fdet: [0, 0, 1]
  - sdet: [0, -1, 0]
  - pix0: [0.231275, 0.217322, -0.211818] meters

**Oversample Auto-Selection:**
- System auto-selected 4-fold oversampling
- Steps = 160 (10 φ steps × 1 mosaic × 4² oversample)

**Scaling Chain Values:**
- `r_e_sqr` = 7.9407927259064e-30 m²
- `fluence_photons_per_m2` = 1.25932017574725e+29
- `steps` = 160
- `capture_fraction` = 1.0
- `polar` = 1.0 (nopolar not set, but K=0?)
- `omega_pixel` = 4.18050007056081e-07 sr

**Divergence from C Trace:**
- PyTorch `steps` = 160 vs C `steps` = 10 (4× factor from auto-oversample)
- PyTorch `fluence` = 1.259e+29 vs C fluence = 1e+24 (beam_size difference?)
- Beam vector: PyTorch uses [0, 0, 1] vs C expects convention-dependent beam

### Issues Noted

1. **Zero Intensity:** F_cell = 0, indicating the HKL lookup failed or reflection is missing
2. **Fluence Mismatch:** 5 orders of magnitude difference suggests beam_size or flux calculation divergence
3. **Steps Mismatch:** Auto-oversample adds factor of 16 (4²) not present in C trace
4. **Polarization:** polar=1.0 suggests nopolar behavior despite K=0 in beam config

### Verification Status

**Selector Check:**
```bash
pytest --collect-only -q tests/test_trace_pixel.py::TestScalingTrace::test_scaling_trace_matches_physics
```
Status: [TO BE RUN]

**Sanity checks against C trace:**
- `steps == 10` ✗ (PyTorch: 160, C: 10) — auto-oversample divergence
- `fluence ≈ 1e24` ✗ (PyTorch: 1.26e+29, C: 1e+24) — 5 OOM difference
- `omega_pixel ≈ 4.2e-7` ✓ (PyTorch: 4.18e-7, C: 4.20e-7) — within 0.5%
- `polar ≈ 0.9146` ✗ (PyTorch: 1.0, C: 0.9146) — wrong polarization

**Major Deviations:**
1. Fluence: ~100,000× too high
2. Steps: 16× too high (auto-oversample)
3. Polarization: 9.3% error

---

## Next Actions (for fix_plan.md Attempt)

1. Compare trace_py_scaling.log with c_trace_scaling.log line-by-line
2. Identify first divergent factor (likely fluence or beam_size)
3. Update docs/fix_plan.md CLI-FLAGS-003 Attempt history with:
   - Metrics: steps=160 vs 10, fluence=1.26e+29 vs 1e+24, polar=1.0 vs 0.9146
   - Artifacts: reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log
   - Observations: Auto-oversample adds 4² factor; fluence calc diverges; polarization wrong
   - Next Actions: Phase L2c comparison script, then L3 normalization fix


---

## Execution Log — Phase L2b0 Rerun (2025-10-07, commit a36b0be)

### Run Timestamp: 2025-10-07T03:39:26.126195Z

**Command:**
```bash
export PYTHONPATH=src && export KMP_DUPLICATE_LIB_OK=TRUE && \
python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py \
  --config supervisor --pixel 685 1039 --out trace_py_scaling.log \
  --device cpu --dtype float32
```

**Execution status:** ✅ SUCCESS (trace generated with harness fix)

**Artifacts created:**
1. `trace_py_scaling.log` — 11 lines of TRACE_PY output ✅
2. `trace_py_env.json` — Environment snapshot ✅
3. `config_snapshot.json` — Harness parameters ✅
4. `harness_run.log` — Execution log ✅

### Key Findings

**Trace Harness Fix Applied:**
- Fixed Simulator initialization to pass Crystal and Detector *objects* instead of Config objects
- Removed duplicate detector instantiation

**Scaling Chain Values (from trace_py_scaling.log):**
- `I_before_scaling` = NOT_EXTRACTED (placeholder — requires instrumentation update per Phase L2b)
- `r_e_sqr` = 7.94079248018965e-30 m² ✓ (matches C exactly)
- `fluence_photons_per_m2` = 1.00000001384843e+24 ✓ (matches C 1e+24)
- `steps` = 10 ✓ (matches C exactly)
- `oversample_thick` = 0 ✓
- `oversample_polar` = 0 ✓
- `oversample_omega` = 0 ✓
- `capture_fraction` = 1.0 ✓
- `polar` = 0.0 (C expects 0.91463969894451 from line 297) ✗
- `omega_pixel` = 4.20412684465831e-07 sr (placeholder — not extracted from simulator)
- `I_pixel_final` = 0 ✗ (C expects 2.88139542684698e-07)

**Divergence from C Trace (c_trace_scaling.log):**
- ✓ PyTorch `steps` = 10 (matches C exactly)
- ✓ PyTorch `fluence` = 1.00000001384843e+24 (matches C 1e+24 within float32 precision)
- ✓ PyTorch `r_e_sqr` matches C exactly
- ✗ PyTorch `polar` = 0.0 vs C polar = 0.91463969894451 (100% error — placeholder not real value)
- ✗ PyTorch `I_pixel_final` = 0 vs C I_pixel_final = 2.88139542684698e-07 (zero intensity)
- ? PyTorch `omega_pixel` placeholder value (not extracted from actual simulator computation)

### Confirmed Per input.md Instructions

**Beam Vector Presence:**
- Harness `get_supervisor_params` includes `custom_beam_vector: (0.00051387949, 0.0, -0.99999986)` ✓
- C trace shows `INCIDENT_BEAM_DIRECTION= 0.000513879 0 -1` ✓

**Oversample Setting:**
- Harness sets `oversample: 1` ✓
- C trace confirms `1x1 pixel oversample steps` (line 154) ✓

**Flux/Beamsize Settings:**
- Harness sets `flux: 1e18`, `exposure: 1.0`, `beamsize_mm: 1.0` ✓
- C trace confirms `incident fluence: 1e+24 photons/m^2` (derived from flux/beamsize) ✓

**Zero Intensity Root Cause:**
- Pixel (685, 1039) final intensity = 0 suggests either:
  - F_cell lookup failed (HKL grid missing reflection)
  - F_latt calculation diverged to produce zero
  - Geometric mismatch left pixel outside Bragg condition

### Observations

1. **Fluence/Steps Parity Achieved:** With full supervisor flags present, PyTorch now matches C for `fluence` and `steps`.
2. **Placeholder Polarization:** The trace harness emits `polar = beam_config.polarization_factor` (default 0.0) instead of extracting the computed Kahn factor from the simulator. This must be fixed per Phase L2b instrumentation requirements.
3. **Placeholder omega_pixel:** The harness emits a hardcoded value instead of extracting the actual solid angle computed in the simulator.
4. **I_before_scaling Not Extracted:** The harness cannot access internal simulator state without instrumentation changes.
5. **Zero Final Intensity:** The simulation completed but pixel (685, 1039) has zero intensity. This either indicates a geometry/lattice divergence (see Phase K3e evidence showing k_frac mismatch) or an HKL lookup failure.

### Verification Status

**Sanity checks against C trace:**
- `steps == 10` ✓ (PyTorch: 10, C: 10)
- `fluence ≈ 1e24` ✓ (PyTorch: 1.00000001384843e+24, C: 1e+24)
- `omega_pixel ≈ 4.2e-7` ? (PyTorch: placeholder 4.20412684465831e-07, C: 4.20412684465831e-07 — exact match suggests copy-paste)
- `polar ≈ 0.9146` ✗ (PyTorch: 0.0, C: 0.91463969894451 — placeholder not real)

**Major Remaining Gaps:**
1. **Polarization:** Placeholder `0.0` instead of computed Kahn factor (~0.9146)
2. **Omega Pixel:** Hardcoded placeholder instead of extracted solid angle
3. **I_before_scaling:** Not accessible without simulator instrumentation changes
4. **Zero Intensity:** Final intensity is zero, indicating upstream physics divergence (likely k_frac mismatch per Phase K3e)

### Git Commit

**SHA:** a36b0be1cd60f17fbadc288fabbbce5d96ac57c6

---

## Next Actions (for docs/fix_plan.md Attempt Update)

1. ✅ **Phase L2b0 Complete** — Rerun with full supervisor flags confirms steps/fluence parity
2. **Phase L2b (blocked)** — Instrumentation required to extract real `polar`, `omega_pixel`, `I_before_scaling` from Simulator.run()
   - Must patch `src/nanobrag_torch/simulator.py` to surface actual values instead of placeholders
   - Gate behind `trace_pixel` debug flag to avoid runtime overhead
   - Update trace harness to pull from instrumented paths
3. **Phase L2c (pending L2b)** — Diff TRACE_C vs TRACE_PY once real scaling factors are available
4. **Phase L3 (pending L2c)** — Root cause zero intensity and fix normalization chain

