# AT-PARALLEL-002 Debug Attempt #2 Update

## Progress
- ✅ Generated parallel traces for pixel (64,79) in 0.4mm case
- ✅ Fixed trace code bug (was using reciprocal vectors instead of real vectors for Miller index calc)
- ✅ Validated single-pixel physics calculations match C code perfectly
- ✅ Identified systematic spatial error pattern

## Key Findings

### Spatial Error Pattern (CRITICAL)
The error is NOT uniform - it scales with distance from beam center:
- Beam center (64,64): ratio = 1.000000 (PERFECT)
- Distance 10px: ratio = 1.000799
- Distance 20px: ratio = 1.003190  
- Distance 30px: ratio = 1.007149

**Fit: error ≈ 7.97e-6 * distance²**

This quadratic scaling strongly suggests a bug in:
1. Airpath (R) calculation
2. Omega (solid angle) = (pixel_size² · close_distance) / R³
3. Some geometric factor that appears squared in the formula

### Single-Pixel Agreement
Pixel (64,79) shows:
- Miller indices: PERFECT match
- F_latt components: PERFECT match  
- I_before_scaling: PERFECT match (within 7e-8%)
- **BUT final intensity: 0.179% error (2121.36 vs 2117.56)**

This 0.179% single-pixel error, when accumulated across image with spatial structure, contributes to the 10% global error.

### Pixel-Size Dependence
- 0.05mm: +3.74% (6.2x baseline)
- 0.1mm: +0.60% (baseline)
- 0.2mm: +0.57% (0.95x baseline)
- 0.4mm: +10.00% (16.7x baseline)

Pattern suggests error scales roughly as `pixel_size²` but not perfectly.

## Next Action (Mandatory)
Generate omega/airpath values for multiple pixels (center, 10px, 20px, 30px offsets) from BOTH C and PyTorch.
Compare to find which component diverges.

Command for PyTorch omega trace:
```bash
python -m nanobrag_torch -default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -distance 100 -seed 1 -detpixels 256 -pixel 0.4 -Xbeam 25.6 -Ybeam 25.6 -mosflm -trace_pixel 64 64 -floatfile /tmp/test.bin 2>&1 | grep "TRACE: Omega"
python -m nanobrag_torch ... -trace_pixel 64 74 ... | grep "TRACE: Omega"
python -m nanobrag_torch ... -trace_pixel 64 84 ... | grep "TRACE: Omega"
```

Then instrument C code to print omega for same pixels and compare.

## Hypothesis
Bug is in omega calculation where a geometric factor (likely involving R or close_distance) is computed incorrectly for off-center pixels, causing quadratic error growth with distance.

