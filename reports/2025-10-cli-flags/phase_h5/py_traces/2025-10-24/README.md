# Phase H5c PyTorch Trace — 2025-10-24

**Date:** 2025-10-24
**Task:** CLI-FLAGS-003 Phase H5c — Post-Attempt #33 trace capture
**Purpose:** Verify whether Attempt #33's beam-center mm→m unit conversion affected pix0 calculation

## Trace Command

```bash
export NB_C_BIN=./golden_suite_generator/nanoBragg
export KMP_DUPLICATE_LIB_OK=TRUE
export PYTHONPATH=src
python reports/2025-10-cli-flags/phase_h/trace_harness.py \
  --out reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-24/trace_py.log
```

## Environment

- **Git Commit:** `git rev-parse HEAD` (captured below)
- **NB_C_BIN:** `./golden_suite_generator/nanoBragg`
- **Python Path:** `src` (editable install)
- **MKL Override:** `KMP_DUPLICATE_LIB_OK=TRUE`

## Git Context

```
$(git rev-parse HEAD)
$(git log -1 --oneline)
```

## Trace Parameters (Supervisor Command)

```
-cell 26.7514 31.31 33.6734 88.687 71.5295 68.1375 \
-hkl scaled.hkl \
-lambda 0.9768 \
-N 36 47 29 \
-distance 231.275 \
-detpixels_f 2463 \
-detpixels_s 2527 \
-pixel 0.172 \
-Xbeam 217.742 \
-Ybeam 213.907 \
-fdet_vector 0.999982004873912 -0.00599800002923425 -0.000118000000575132 \
-sdet_vector -0.0059979996566955 -0.999969942765222 -0.0049129997187971 \
-odet_vector -8.85282813644494e-05 0.00491361907271126 -0.999987924182263 \
-pix0_vector_mm -216.475836204836 216.343050492215 -230.192414300537 \
-oversample 1 \
-phi 0 \
-phisteps 10 \
-osc 0.1 \
-exposure 1e-15 \
-flux 1e27 \
-beamsize 0.001 \
-mat A.mat
```

**Pixel Traced:** (slow=1039, fast=685)

## Critical Findings

⚠️ **Attempt #33 Had NO Effect on Pix0:**
- Pix0 deltas **identical** to 2025-10-22 baseline
- ΔF = -1136.4 μm (still exceeds <50 μm threshold)
- ΔS = +139.3 μm (still exceeds threshold)
- ΔO = -5.6 μm (within threshold)

**Interpretation:** The beam-center mm→m conversion fix in Attempt #33 affected a **different code path** (BEAM pivot without custom vectors) and did NOT resolve the pix0 discrepancy in custom-vector scenarios.

## Artifacts

- **PyTorch Trace (stdout):** `trace_py.stdout`
- **C Baseline:** `../../c_traces/2025-10-22/with_override.log`
- **Parity Summary:** `../../parity_summary.md`
- **Delta Analysis:** See parity_summary.md Pix0 Vector Comparison table

## Next Steps

**Phase H6 Required** — Pix0 discrepancy must be resolved before Phase K normalization can proceed.

See `plans/active/cli-noise-pix0/plan.md` for Phase H6 tasks.
