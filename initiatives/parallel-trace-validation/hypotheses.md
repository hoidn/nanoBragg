# Hypotheses for the 28mm Systematic Offset

**Date**: January 9, 2025  
**Context**: After fixing pivot mode mismatch, we observe a consistent ~28mm error that redistributes between axes  
**Key Observation**: Error magnitude is preserved (~28mm) but changes direction based on pivot mode  

## The Phenomenon

When using different pivot modes, the same ~28mm error appears in different axes:

**SAMPLE Pivot**:
- X: +0.2mm ✓
- Y: -27.9mm ✗ (error concentrated here)
- Z: +0.1mm ✓
- Total error magnitude: ~28mm

**BEAM Pivot**:
- X: -14.3mm ✗
- Y: -0.7mm ✓
- Z: -14.9mm ✗
- Total error magnitude: √(14.3² + 14.9²) ≈ 20.6mm (similar magnitude)

**Critical Insight**: The error doesn't disappear, it **rotates** based on pivot mode!

## Hypothesis 1: Different Rotation Centers (60% probability)

### The Theory
C and PyTorch might be rotating around different points in space:
- **PyTorch**: Rotates around exact sample position (0,0,0)
- **C**: Might rotate around a slightly offset position

### Why This Fits
- A 28mm offset in rotation center would create exactly this kind of systematic error
- The error would redistribute based on rotation angles
- Different pivot modes would manifest the error in different axes

### Test Strategy
1. Check if C applies any offset to the rotation center
2. Look for terms like `distance * 0.28` or similar in C code
3. Test with different distances to see if error scales

### Expected Evidence
- Error should scale with distance (if percentage-based)
- Or remain constant (if absolute offset)

## Hypothesis 2: Beam Position Interpretation (40% probability)

### The Theory
The "beam position" on the detector might be interpreted differently:
- **PyTorch**: Beam hits at calculated position
- **C**: Beam hits at position + some offset (like the +0.5 pixel for MOSFLM)

### Why This Fits
- 28mm ≈ 280 pixels × 0.1mm/pixel
- Could be related to detector center vs corner reference
- Would explain why error moves with pivot change

### Test Strategy
1. Check if there's a systematic 280-pixel offset somewhere
2. Look for beam position adjustments in C
3. Test with different beam centers

### Expected Evidence
- Error might be exactly 280 pixels (or close)
- Should change if beam center changes

## Hypothesis 3: Distance Definition Mismatch (30% probability)

### The Theory
"Distance" might mean different things:
- **PyTorch**: Distance from sample to detector surface
- **C**: Distance from sample to detector center? Or to pixel (0,0)?

### Why This Fits
- 28mm could be the difference between two distance interpretations
- Would create systematic offset
- Would rotate based on detector orientation

### Test Strategy
1. Check exact definition of "distance" in C code
2. Look for distance adjustments or offsets
3. Test with different distances

### Expected Evidence
- Error might scale with distance
- Or might be related to detector thickness

## Hypothesis 4: Missing Coordinate Transformation (25% probability)

### The Theory
There might be an additional coordinate transformation in C that we're not applying:
- A translation before or after rotations
- A change of origin for certain calculations
- A detector-frame to lab-frame conversion we're missing

### Why This Fits
- Would create consistent offset
- Would change based on rotations (pivot mode)
- Magnitude would be preserved

### Test Strategy
1. Look for additional transformations in C
2. Check for coordinate system conversions
3. Trace coordinates through entire pipeline

### Expected Evidence
- Find unexpected transformation in C code
- Coordinates would diverge at transformation point

## Hypothesis 5: Detector Thickness/Parallax (20% probability)

### The Theory
C might account for detector thickness or parallax correction:
- Detector might have non-zero thickness
- X-rays might penetrate to different depths
- Could create apparent position offset

### Why This Fits
- Would create systematic offset
- Might be angle-dependent
- Could be ~28mm for typical detector

### Test Strategy
1. Check for detector thickness parameters
2. Look for parallax corrections
3. Test with different angles

### Expected Evidence
- Find thickness-related code in C
- Error might vary with incident angle

## Hypothesis 6: Integer Pixel vs Fractional Pixel (15% probability)

### The Theory
The 28mm (280 pixels) might be related to rounding or truncation:
- C might use integer pixel positions
- PyTorch uses fractional
- Difference accumulates to ~280 pixels

### Why This Fits
- 280 is suspiciously close to a round number
- Could be related to detector size (1024 pixels)
- Would create systematic offset

### Test Strategy
1. Check for integer truncation in C
2. Look for pixel rounding logic
3. Test with different detector sizes

### Expected Evidence
- Error might be exactly 280 pixels
- Would change with detector size

## Testing Priority

1. **First**: Check rotation centers (Hypothesis 1)
   - Most likely given error behavior
   - Easy to test

2. **Second**: Check beam position (Hypothesis 2)
   - The 280-pixel connection is suspicious
   - Related to previous +0.5 pixel issues

3. **Third**: Check distance definition (Hypothesis 3)
   - Common source of confusion
   - Would explain systematic nature

## Key Measurements to Make

1. **Exact error magnitude**: Is it exactly 28mm or 280 pixels?
2. **Scaling behavior**: Does error scale with distance?
3. **Angle dependence**: Does error change with rotation angles?
4. **Beam center dependence**: Does moving beam center affect error?

## Success Criteria

The correct hypothesis should explain:
- [ ] Why error is ~28mm
- [ ] Why it redistributes between axes
- [ ] Why it changes with pivot mode
- [ ] Why magnitude is preserved
- [ ] How to fix it

## Next Steps

1. Measure exact error magnitude in pixels
2. Test if error scales with distance
3. Check C code for rotation center offsets
4. Look for the number 28, 280, or 0.028 in C code
5. Test with simplified configurations

---

**Note**: The fact that the error **rotates** rather than disappears is a huge clue. This almost certainly means we're rotating around different points or have different coordinate origins.