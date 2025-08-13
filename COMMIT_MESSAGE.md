fix(detector): Correct MOSFLM F/S mapping and unify pixel convention

This commit fixes a critical geometric bug in tilted detector configurations 
with BEAM pivot mode that was causing large positional offsets.

## Primary Fix: MOSFLM F/S Axis Mapping
- **Root Cause**: Incorrect mapping of slow/fast beam center coordinates in MOSFLM convention
- **Previous (wrong)**: `beam_center_f → Xbeam, beam_center_s → Ybeam` 
- **Fixed (correct)**: `beam_center_s → Xbeam, beam_center_f → Ybeam`
- **Impact**: Resolves ~100-pixel geometric offset in tilted detector test case

## Secondary Fixes:
- **Pixel Convention**: Unified all detector geometry to use pixel centers (index + 0.5) 
  instead of inconsistent edge/center handling
- **Unit Documentation**: Clarified that detector returns coordinates in meters, 
  with explicit conversion to Angstroms in simulator
- **Test Expectations**: Fixed detector config tests to reflect meters-based internal units

## Verification:
- Added comprehensive regression tests (`test_detector_geometry.py`) to prevent 
  reintroduction of this bug
- Detector basis vectors now match C-code reference within 1e-8 tolerance
- Visual verification shows correct 100-pixel spot shift for 10mm beam offset
- All detector configuration tests pass

## Files Modified:
- `src/nanobrag_torch/models/detector.py`: Core F/S mapping fix + pixel convention
- `src/nanobrag_torch/simulator.py`: Explicit unit conversion documentation
- `tests/test_detector_geometry.py`: New regression tests with C-code validation
- `tests/test_detector_config.py`: Updated unit expectations for meters
- `docs/architecture/detector.md`: Updated with corrected mapping documentation

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>