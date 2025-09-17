# C vs Python Trace Analysis Report

## Execution Summary
**Date**: September 10, 2025  
**Task**: Compare C and Python implementations for pixel (512, 512) with tilted detector configuration  
**Configuration**: rotx=5°, roty=3°, rotz=2°, twotheta=20°, SAMPLE pivot  

## Key Findings

### 🚨 CRITICAL DIVERGENCE IDENTIFIED

The C and Python implementations produce **fundamentally different pixel positions** for the same pixel coordinates.

#### Pixel Position Calculation

**C Implementation** (`nanoBragg.c`):
```
TRACE_C: pixel_pos_meters 0.1 0 0
```

**Python Implementation** (`trace_pixel_512_512.py`):
```
TRACE_PY:pixel_pos_meters=0.0949897892755101 -0.0308070973357056 -0.00527898542738564
```

This represents a **major geometry calculation error** where:
- C calculates pixel position as `(0.1, 0, 0)` meters
- Python calculates pixel position as `(0.095, -0.031, -0.005)` meters
- The Y and Z coordinates differ by several centimeters!

#### Scattering Vector Impact

**C Implementation**:
```
TRACE_C:scattering_final=0 0 0
```

**Python Implementation**:
```
TRACE_PY:k_scattered=0.962642417900668 -0.312204278943387 -0.0534981215838013
```

The incorrect pixel position in C leads to a zero scattering vector, which explains why the correlation is so poor (0.040).

## Detector Geometry Analysis

### Detector Basis Vectors (Match ✅)
Both implementations agree on the rotated detector basis vectors:

**C Implementation**:
```
TRACE_C:fdet_after_twotheta=0.0551467333542405 -0.0852831016700733 0.994829447880333
TRACE_C:sdet_after_twotheta=0.0302080931112661 -0.99574703303416 -0.0870362988312832
TRACE_C:odet_after_twotheta=0.998021196624068 0.0348516681551873 -0.0523359562429438
```

**Python Implementation**:
```
TRACE_PY:fdet_rotated=0.0551467333542405 -0.0852831016700733 0.994829447880333
TRACE_PY:sdet_rotated=0.0302080931112661 -0.99574703303416 -0.0870362988312832
TRACE_PY:odet_rotated=0.998021196624068 0.0348516681551873 -0.0523359562429438
```

### Pix0 Vector (Diverges ❌)
The detector origin vector differs significantly:

**C Implementation**:
```
TRACE_C:pix0_vector=0.0956255651436428 0.055402794403592 -0.0465243988887638
```

**Python Implementation**:
```
TRACE_PY:pix0_vector=0.109813559827604 0.0226983931746408 -0.0517579947957671
```

## Root Cause Analysis

The divergence appears to stem from **different pivot mode implementations**:

1. **Configuration**: Both use `twotheta=20°` which should trigger SAMPLE pivot mode
2. **C Trace Shows**: "pivoting detector around direct beam spot" (BEAM pivot)
3. **Python Trace Shows**: `detector_pivot=sample` (SAMPLE pivot)

### Hypothesis
The C code may not be correctly applying the SAMPLE pivot mode when `twotheta != 0`. Instead, it appears to be using BEAM pivot mode, which calculates pix0_vector differently.

## Next Steps

1. **Verify Pivot Mode Logic**: Check C code logic for `-twotheta` parameter and SAMPLE pivot activation
2. **Fix Pivot Implementation**: Ensure C code correctly implements SAMPLE pivot when twotheta is specified  
3. **Validate Fix**: Re-run trace comparison after fixing pivot mode
4. **Full Correlation Test**: Run complete correlation verification

## Files Generated
- `c_trace.log`: 33 lines of C trace data
- `py_trace.log`: 93 lines of Python trace data  
- `c_trace_full.log`: Complete C execution log
- `c_trace_output.bin`: C simulation output

## Enhanced C Code
Successfully added comprehensive tracing to `nanoBragg.c` including:
- Detector geometry calculations
- Pixel position computation  
- Scattering vector calculation
- Miller index computation

The enhanced tracing successfully identified the exact point of divergence between implementations.