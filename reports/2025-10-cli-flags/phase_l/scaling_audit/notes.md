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
