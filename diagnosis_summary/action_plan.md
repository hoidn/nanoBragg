
# 🎯 ACTION PLAN: Fix 28mm Systematic Offset

## PHASE 1: Identity Configuration Fix (CRITICAL - 192.67mm error)
**Target:** < 0.1mm error in identity configuration

### Root Cause
Current identity pix0: [0.100000, 0.051250, -0.051250] m
Expected identity pix0: [-0.005170, -0.005170, 0.100000] m
❌ Wrong coordinate axes, wrong signs, wrong MOSFLM implementation

### Action Items
- [ ] Fix coordinate system: X=beam direction, Y=vertical, Z=horizontal  
- [ ] Correct pix0 formula: pix0 = [-Fbeam, -Sbeam, +distance]
- [ ] Implement proper MOSFLM +0.5 pixel offset
- [ ] Test until identity error < 0.1mm

## PHASE 2: Beam Center Implementation (HIGH - 0.01-23.33mm scaling)
**Target:** Consistent error across beam center positions

### Root Cause  
Error scales linearly with beam center magnitude (slope ≈ 0.227)
❌ Incorrect beam center offset calculation and application

### Action Items
- [ ] Fix MOSFLM beam center formula
- [ ] Verify coordinate system for beam center application
- [ ] Test beam center variations until std dev < 0.5mm

## PHASE 3: Rotation Logic (MEDIUM - up to 13.38mm per rotation)
**Target:** Combined rotation error < 1mm

### Root Cause
Twotheta rotation contributes 13.38mm error (dominant)
❌ Incorrect twotheta axis implementation and rotation order

### Action Items
- [ ] Compare rotation matrices with C implementation
- [ ] Fix twotheta axis definition and application  
- [ ] Verify rotation order: rotx → roty → rotz → twotheta
- [ ] Test until individual rotation errors < 2mm

## SUCCESS METRICS
- [x] Distance scaling test: PASSED (H1 ruled out)
- [x] Beam center analysis: CONFIRMED (H2 identified) 
- [x] Identity configuration analysis: CRITICAL ISSUE FOUND
- [ ] Identity fix: error < 0.1mm
- [ ] Beam center fix: consistent across positions
- [ ] Rotation fix: tilted correlation > 0.99
- [ ] Final verification: C vs PyTorch correlation > 0.999

## ESTIMATED TIMELINE
- Phase 1 (Identity): 1-2 days
- Phase 2 (Beam Center): 1 day  
- Phase 3 (Rotations): 2-3 days
- **Total: 4-6 days**

The systematic approach has successfully identified all root causes.
Focus on identity configuration first - it's the foundation for everything else.
