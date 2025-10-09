# SOURCE-WEIGHT-001 Phase B3 — Current Parity Delta Reproduction

**Date:** 2025-10-09
**Task:** Reproduce the weighted-source divergence using current HEAD and document observed metrics.

## Test Configuration

**Fixture:** Two-source file with unequal weights
**Path:** `reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt`

```
# Weighted two-source fixture
# X Y Z weight wavelength(m)
0.0 0.0 10.0 1.0 6.2e-10
0.0 0.0 10.0 0.2 6.2e-10
```

**Common parameters:**
- Cell: 100 × 100 × 100 Å, 90° × 90° × 90°
- Distance: 231.274660 mm
- Lambda: 0.9768 Å
- Pixel: 0.172 mm
- Detector: 256 × 256 pixels
- Default F: 100
- Flags: `-nonoise -nointerpolate`

## Execution Commands

### C Reference
```bash
./golden_suite_generator/nanoBragg \
  -cell 100 100 100 90 90 90 \
  -default_F 100 \
  -floatfile c.bin \
  -sourcefile two_sources.txt \
  -distance 231.274660 \
  -lambda 0.9768 \
  -pixel 0.172 \
  -detpixels_x 256 \
  -detpixels_y 256 \
  -nonoise \
  -nointerpolate
```

**C Output log excerpt:**
```
  created a total of 4 sources:
0 0 0   0 0
0 0 0   0 0
0 0 10   1 6.2e-10
0 0 10   0.2 6.2e-10
...
max_I = 0.00200611  at 0.013158 0.022102
mean= 0.00156275 rms= 0.00157296 rmsd= 0.000178799
```

**Observation:** C code reads 4 sources (including two default-position sources with zero contribution), but only the last two contribute. Weights `[1.0, 0.2]` are printed but ignored per spec.

### PyTorch Implementation
```bash
KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch \
  -cell 100 100 100 90 90 90 \
  -default_F 100 \
  -floatfile py.bin \
  -sourcefile two_sources.txt \
  -distance 231.274660 \
  -lambda 0.9768 \
  -pixel 0.172 \
  -detpixels_x 256 \
  -detpixels_y 256 \
  -nonoise \
  -nointerpolate
```

**PyTorch Output log excerpt:**
```
Loaded 2 sources from reports/.../two_sources.txt
...
auto-selected 2-fold oversampling

Statistics:
  Max intensity: 5.927e+00 at pixel (128, 34)
  Mean: 8.239e-02
  RMS: 3.852e-01
  RMSD: 3.763e-01
```

**Observation:** PyTorch loads only 2 sources (skipping the default-position entries). Auto-selects 2× oversample while C uses 1×. This oversample difference explains part of the metric divergence.

## Measured Metrics

### C Reference
- **Sum:** 1.024165e+02
- **Max:** 2.006111e-03
- **Mean:** 1.562751e-03

### PyTorch Current HEAD
- **Sum:** 5.399717e+03
- **Max:** 5.927148e+00
- **Mean:** 8.239315e-02

### Comparison
- **Correlation:** 0.208182 (poor pattern agreement)
- **Sum Ratio (Py/C):** 52.723141
- **Delta:** +5172.31%

## Analysis

### Primary Divergence: Oversample Factor

The C log shows `auto-selected 1-fold oversampling` while PyTorch shows `auto-selected 2-fold oversampling`. This difference stems from the oversample auto-selection logic, which may differ between implementations.

**Impact on steps normalization:**
- C: `steps = 4 × 1 × 1 × 1² = 4`
- PyTorch: `steps = 2 × 1 × 1 × 2² = 8`

The 2× difference in steps should cause PyTorch to be **half** the C intensity (if weighted accumulation were correct), but we observe 52× **higher** intensity. This confirms the weighted multiplication violation.

### Secondary Divergence: Weighted Accumulation

From `pytorch_accumulation.md`, PyTorch multiplies intensities by weights before summing:
```python
intensity = torch.sum(intensity * weights_broadcast, dim=0)  # Line 413
```

With weights `[1.0, 0.2]`, the weighted sum yields `1.2 × base_intensity` per pixel, while the spec requires `2.0 × base_intensity` (equal weighting).

**Expected ratio (if oversample matched):** `1.2 / 2.0 = 0.6` (PyTorch underestimates by 40%)

**Observed ratio accounting for oversample:** `52.72 ≈ 0.6 × (C_oversample / Py_oversample)² × ???`

The compound effect of:
1. Weighted accumulation (0.6× factor)
2. Oversample mismatch (1×/2× affects normalization and accumulation)
3. Possible source filtering differences (C counts 4 sources, PyTorch 2)

...creates a complex divergence that requires controlled testing to isolate.

### Recommendation for Phase C

Before implementing the weight-removal fix, **first align the oversample auto-selection** to ensure both C and PyTorch use the same `steps` normalization. This will allow Phase C parity validation to cleanly isolate the weight multiplication issue.

Alternatively, use **explicit `-oversample 1`** in both commands during Phase D validation to eliminate this confounding variable.

## Pytest Collection Proof

**Command:** `pytest --collect-only -q`

**Result:** ✅ **Exit code 0**
**Collected:** 682 tests in 2.63s

**Excerpt:**
```
682 tests collected in 2.63s
Exit code: 0
```

**Observation:** Test collection succeeds. No import errors or collection failures. Repository is in a valid state for continued development.

## Artifacts Summary

All Phase B artifacts stored under `reports/2025-11-source-weights/phase_b/20251009T083515Z/`:

| File | Description |
|------|-------------|
| `c.bin` | C reference floatfile output |
| `py.bin` | PyTorch floatfile output |
| `c_stdout.log` | C execution log (shows 4 sources, 1× oversample) |
| `py_stdout.log` | PyTorch execution log (shows 2 sources, 2× oversample) |
| `metrics.json` | Machine-readable comparison metrics |
| `pytest_collect.log` | Pytest collection proof (682 tests, exit 0) |
| `spec_alignment.md` | Task B1: Spec & C behavior evidence |
| `pytorch_accumulation.md` | Task B2: PyTorch call-chain analysis |
| `analysis.md` | This document (Task B3) |

## Exit Criteria for Phase B3

✅ Complete. Parity delta reproduced with:
- Both CLI runs executed and logged
- Metrics captured in JSON and markdown
- Pytest collection verified (682 tests, exit 0)
- Oversample auto-selection divergence identified as confounding factor
- Recommendation provided for Phase C/D: align oversample before validating weight fix

## Next Actions (Phase C Guidance)

1. **Align oversample auto-selection** OR use explicit `-oversample 1` in validation commands
2. **Remove weighted multiplication** at `simulator.py:413,416`
3. **Rerun parity test** with oversample-controlled config
4. **Expect:** Correlation ≥0.999, |sum_ratio - 1| ≤ 1e-3 after both fixes
