# CLI-FLAGS-003 Watch Scaffolding

**Initiative**: CLI-FLAGS-003 — `-nonoise` and `-pix0_vector_mm` parity
**Status**: Closed with documented C-PARITY-001 tolerance (Option 1)
**Last Updated**: 2025-10-08

## Purpose

This document establishes lightweight watch tasks to catch scaling/parity regressions early without requiring full test-suite overhead. Use these quarterly/biannual commands to verify the spec-mode implementation remains aligned with expected behavior.

## Quarterly Trace Harness Cadence

**When**: Every 3 months (starting 2026-01-08)
**Command**: Spec-mode trace comparison at a representative on-peak pixel

```bash
# Reproduce the canonical spec-trace command from Phase D closure
export STAMP=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p reports/quarterly_traces/$STAMP

KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python scripts/validation/trace_harness.py \
  --config supervisor \
  --pixel 685 1039 \
  --device cpu \
  --dtype float64 \
  --out reports/quarterly_traces/$STAMP/trace_py.log \
  2>&1 | tee reports/quarterly_traces/$STAMP/stdout.txt

# Compare against latest baseline
diff reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T203504Z/trace_py_spec.log \
  reports/quarterly_traces/$STAMP/trace_py.log \
  > reports/quarterly_traces/$STAMP/trace_diff.txt

# Expected result: zero diff (or only timestamp/metadata changes)
```

**Reference Baseline**: `reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T203504Z/trace_py_spec.log`

**Success Criteria**:
- Trace diff limited to metadata lines (timestamps, env variables)
- Physics variables (`I_before_scaling`, `F_cell`, `F_latt`, downstream scaling factors) unchanged
- Any divergence → reopen CLI-FLAGS-003 with new Attempt

## Biannual nb-compare Smoke Test

**When**: Every 6 months (starting 2026-04-08)
**Command**: Full ROI comparison using canonical supervisor parameters

```bash
# Reproduce the authoritative nb-compare from Phase N closure
export STAMP=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p reports/biannual_smoke/$STAMP

nb-compare \
  --roi 100 156 100 156 \
  --resample \
  --outdir reports/biannual_smoke/$STAMP \
  --threshold 0.98 \
  -- \
  -mat A.mat \
  -hkl scaled.hkl \
  -nonoise \
  -nointerpolate \
  -oversample 1 \
  -exposure 1 \
  -flux 1e18 \
  -beamsize 1.0 \
  -spindle_axis -1 0 0 \
  -Xbeam 217.742295 \
  -Ybeam 213.907080 \
  -distance 231.274660 \
  -lambda 0.976800 \
  -pixel 0.172 \
  -detpixels_x 2463 \
  -detpixels_y 2527 \
  -odet_vector -0.000088 0.004914 -0.999988 \
  -sdet_vector -0.005998 -0.999970 -0.004913 \
  -fdet_vector 0.999982 -0.005998 -0.000118 \
  -pix0_vector_mm -216.336293 215.205512 -230.200866 \
  -beam_vector 0.00051387949 0.0 -0.99999986 \
  -Na 36 \
  -Nb 47 \
  -Nc 29 \
  -osc 0.1 \
  -phi 0 \
  -phisteps 10 \
  -detector_rotx 0 \
  -detector_roty 0 \
  -detector_rotz 0 \
  -twotheta 0
```

**Reference Baseline**: `reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/summary.json`

**Expected Metrics** (from Option 1 validation):
- **Correlation**: ≥ 0.98 (baseline: 0.9852)
- **Sum Ratio**: 1.1e5 – 1.3e5 (baseline: 1.159e5)
  - *Note*: Sum ratio divergence attributed to C-PARITY-001 (φ=0 carryover bug in nanoBragg.c); documented in `docs/bugs/verified_c_bugs.md:166-204`
- **Peak Alignment**: Mean/max distance ~ 0.0 pixels

**Success Criteria**:
- Correlation remains ≥ 0.98
- Sum ratio stays within documented C-PARITY-001 tolerance band (110K–130K)
- Peak positions stable (mean_peak_distance < 1 pixel)
- Any metric violation → reopen CLI-FLAGS-003 with new Attempt

## Environment Requirements

Both commands require:
- `KMP_DUPLICATE_LIB_OK=TRUE` (MKL conflict suppression)
- `NB_C_BIN=./golden_suite_generator/nanoBragg` (or `./nanoBragg` fallback)
- Editable install: `pip install -e .` from repo root
- Test data files present: `A.mat`, `scaled.hkl` (from supervisor command context)

## Artifact Management

- **Quarterly traces**: Retain only latest 4 runs (12 months); archive older bundles to `reports/archive/quarterly_traces/`
- **Biannual smoke**: Retain only latest 2 runs (12 months); archive older bundles to `reports/archive/biannual_smoke/`
- Always capture:
  - `commands.txt` (exact invocation)
  - `env.json` (environment snapshot)
  - `sha256.txt` (file checksums)
  - Comparison outputs (diff.txt / summary.json)

## Deviation Response

If either watch task fails:
1. Capture full diagnostic bundle under `reports/2025-XX-cli-flags-regression/<timestamp>/`
2. Add new Attempt to `docs/fix_plan.md` [CLI-FLAGS-003] with metrics + artifacts
3. Run targeted pytest: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py`
4. Compare against archived Phase D/N baselines to identify regression source
5. Reference this watch.md in the Attempt as the triggering harness

## Cross-References

- **Closure Evidence**: `reports/archive/cli-flags-003/supervisor_command/20251009T024433Z/summary.md`
- **Spec-Mode Decision**: `reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/20251009T013046Z/`
- **C-PARITY-001 Documentation**: `docs/bugs/verified_c_bugs.md:166-204`
- **Initiative Plan**: `plans/active/cli-noise-pix0/plan.md` (Phase P)
- **Phi Carryover Removal**: `plans/active/phi-carryover-removal/plan.md` (Phase E)

## Maintenance

- Review/update this document when:
  - nanoBragg.c reference binary changes (update `NB_C_BIN` path)
  - Spec evolves to tighten/loosen tolerances (update thresholds)
  - Test data files relocated (update `A.mat`/`scaled.hkl` paths)
- Keep commands self-contained (avoid external dependencies beyond documented env setup)
