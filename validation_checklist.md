# nanoBragg Pre-Simulation Validation Checklist

**🚨 MANDATORY: Complete this checklist BEFORE running any nanoBragg simulation**

This checklist prevents the most common bugs that cause poor correlation with C reference code. **Print this checklist and physically check each box.**

---

## 📋 Critical Convention Verification

### □ 1. Convention Consistency Check
**MOST IMPORTANT**: Verify your parameters don't trigger silent convention switching.

**Run the startup warning system:**
```bash
python startup_warnings.py your_script.sh
```
**OR for direct command:**
```bash
python startup_warnings.py -- [your nanoBragg parameters]
```

- [ ] **No CRITICAL warnings displayed**
- [ ] **Reviewed any WARNING messages** 
- [ ] **Understand which convention will be active** (MOSFLM/XDS/CUSTOM)

**❌ STOP HERE if you have CRITICAL warnings - fix them before proceeding**

---

## 🔧 Parameter Verification

### □ 2. Axis Parameter Safety
**Check if you're using axis specification parameters:**

- [ ] **If using `-twotheta_axis`**: You understand this triggers CUSTOM convention
- [ ] **If using `-spindle_axis`**: You understand this triggers CUSTOM convention  
- [ ] **If using `-vert_axis`**: You understand this triggers CUSTOM convention
- [ ] **If using ANY axis parameter**: Added `-convention CUSTOM` explicitly

**Rule**: Either remove ALL axis parameters OR add `-convention CUSTOM`

### □ 3. Rotation Parameter Consistency
**For detector rotations, verify coordinate system alignment:**

- [ ] **Using MOSFLM convention**: detector_rotx/roty/rotz follow MOSFLM coordinate system
- [ ] **Using XDS convention**: detector_rotx/roty/rotz follow XDS coordinate system
- [ ] **Using CUSTOM convention**: All axes explicitly defined and verified

### □ 4. Beam Center Specification
**For non-centered beam configurations:**

- [ ] **Detector distance specified**: Also specified `-Xbeam` and `-Ybeam`
- [ ] **Beam center values**: Appropriate for your detector size and geometry
- [ ] **MOSFLM convention**: Remember +0.5 pixel offset is automatic
- [ ] **Tilted detector**: Beam center accounts for detector orientation

---

## 📊 Golden Reference Verification

### □ 5. Test Case Preparation
**Before production runs, validate with known test cases:**

- [ ] **Run simple cubic test**: Achieves >0.999 correlation
- [ ] **Use identical parameters**: Match golden reference exactly
- [ ] **Check units**: Distance in mm, wavelength in Angstroms, angles in degrees
- [ ] **Verify output format**: Correct image dimensions and file type

**Golden reference command for validation:**
```bash
./nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
    -distance 100 -detpixels 1024 -floatfile test_output.bin
```

### □ 6. Correlation Verification
**After running test case:**

- [ ] **Correlation coefficient**: >0.999 for simple cubic case
- [ ] **Image dimensions**: Match expected detector size
- [ ] **Intensity scale**: Reasonable values (not all zeros or overflow)
- [ ] **Visual inspection**: Bragg peaks in expected locations

---

## 🔍 Advanced Configuration Checks

### □ 7. Complex Geometry Verification
**For tilted detectors or complex rotations:**

- [ ] **Rotation order**: detector_rotx → detector_roty → detector_rotz → detector_twotheta
- [ ] **Pivot mode**: SAMPLE or BEAM pivot appropriate for your setup
- [ ] **Convention documentation**: Consulted appropriate convention reference
- [ ] **Test progression**: Start simple, add complexity incrementally

### □ 8. Matrix and Structure Factors
**For custom crystal orientations:**

- [ ] **Matrix file format**: MOSFLM-style orientation matrix
- [ ] **Structure factor file**: Correct h k l F format
- [ ] **File paths**: Absolute paths or correct relative paths
- [ ] **File validation**: Files exist and are readable

---

## ✅ Pre-Flight Checklist

### □ 9. Environment Verification
**Runtime environment preparation:**

- [ ] **Compiled nanoBragg**: Latest version with your modifications
- [ ] **File permissions**: All input files readable, output directory writable  
- [ ] **Disk space**: Sufficient for output images (can be several GB)
- [ ] **Validation tools**: Have correlation checking scripts ready

### □ 10. Documentation References Ready
**Have these references accessible during simulation:**

- [ ] **C Parameter Dictionary**: `docs/architecture/c_parameter_dictionary.md`
- [ ] **Detector Geometry Guide**: `docs/architecture/detector.md` 
- [ ] **Convention Mapping**: `docs/development/c_to_pytorch_config_map.md`
- [ ] **Debugging Checklist**: `docs/debugging/detector_geometry_checklist.md`

---

## 🎯 Execution Readiness

### □ 11. Final Safety Check
**Before hitting enter:**

- [ ] **Command double-checked**: All parameters spelled correctly
- [ ] **Output file naming**: Won't overwrite important data
- [ ] **Estimated runtime**: Reasonable for your system (N^3 scaling)
- [ ] **Validation plan**: Know how you'll verify results

### □ 12. Results Validation Plan
**After simulation completes:**

- [ ] **Correlation check**: Script ready to compare with reference
- [ ] **Visual inspection**: Tool ready to view diffraction images  
- [ ] **Log analysis**: Plan to check for warnings/errors in output
- [ ] **Documentation**: Will record parameters and results for reproducibility

---

## 🚨 Emergency Stops

**STOP and get help if:**
- [ ] Correlation drops below 0.95 for simple cubic test
- [ ] Images are all zeros or have obvious artifacts
- [ ] nanoBragg crashes or produces error messages
- [ ] Results don't match physical expectations
- [ ] You're unsure about any convention or parameter

**Get help from:**
- `docs/debugging/detector_geometry_checklist.md`
- Example scripts in `examples/` directory
- Issues in project repository

---

## 📝 Sign-Off

**I have completed all checklist items and understand the consequences of convention switching bugs.**

**Simulation planned for:** _______________________ (date/time)

**Key parameters:**
- Convention: _______________
- Lambda: _______________
- Distance: _______________  
- Detector rotations: _______________

**Signature:** _________________________________ **Date:** __________

---

## 🔗 Quick Reference Links

**Essential Files:**
- `startup_warnings.py` - Run this first!
- `examples/safe_mosflm_rotation.sh` - Safe MOSFLM example
- `examples/custom_convention_explicit.sh` - Safe CUSTOM example  
- `examples/DANGER_mixed_conventions.sh` - What NOT to do
- `preflight_check.py` - Automated validation script

**Documentation:**
- `docs/debugging/detector_geometry_checklist.md` - Debug workflow
- `docs/development/c_to_pytorch_config_map.md` - Parameter mapping
- `docs/architecture/c_parameter_dictionary.md` - All parameters
- `tests/golden_data/README.md` - Reference test cases