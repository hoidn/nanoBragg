# Implementation Checklist - Detector Geometry Fixes

**CRITICAL**: Execute phases in order. Validate each phase before proceeding.

---

## 🔴 PHASE 1: COORDINATE SYSTEM FIX (CRITICAL - 192.67mm error)

### Step 1: Backup Current Implementation
```bash
cp src/nanobrag_torch/models/detector.py src/nanobrag_torch/models/detector.py.backup
```

### Step 2: Fix Basis Vectors
**File**: `src/nanobrag_torch/models/detector.py`  
**Method**: `_initialize_detector_frame()` or constructor

- [ ] **FIND** these lines:
```python
self.fdet_vec = torch.tensor([0, 1, 0])  # WRONG
self.sdet_vec = torch.tensor([0, 0, 1])  # WRONG
```

- [ ] **REPLACE** with:
```python
# CORRECTED: Match C implementation coordinate system
self.fdet_vec = torch.tensor([0, -1, 0], dtype=torch.float64)  # Fast along negative Y
self.sdet_vec = torch.tensor([0, 0, -1], dtype=torch.float64)  # Slow along negative Z
self.odet_vec = torch.tensor([1, 0, 0], dtype=torch.float64)   # Origin along positive X (beam)
```

### Step 3: Validate Phase 1
```bash
# Test identity configuration - MUST show <0.1mm error
python scripts/verify_detector_geometry.py \
    --rotx 0 --roty 0 --rotz 0 --twotheta 0 \
    --output phase1_validation.json

# Check output for:
# - pix0_vector error < 0.001 meters
# - Correlation > 0.99
```

**STOP HERE IF VALIDATION FAILS**

---

## 🟠 PHASE 2: TWOTHETA AXIS FIX (HIGH - 66.18mm error)

### Step 1: Fix Twotheta Rotation Axis
**File**: `src/nanobrag_torch/models/detector.py`  
**Method**: Look for twotheta rotation calculation

- [ ] **FIND** this line:
```python
twotheta_axis = torch.tensor([0.0, 1.0, 0.0])  # WRONG - Y axis
```

- [ ] **REPLACE** with:
```python
# CORRECTED: Match C implementation (negative Z-axis for MOSFLM)
if self.convention == "MOSFLM":
    twotheta_axis = torch.tensor([0.0, 0.0, -1.0], dtype=torch.float64)  # Negative Z
else:
    twotheta_axis = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)  # X for XDS
```

### Step 2: Validate Phase 2
```bash
# Test twotheta rotation only
python scripts/verify_detector_geometry.py \
    --rotx 0 --roty 0 --rotz 0 --twotheta 15 \
    --output phase2_validation.json

# Test combined rotations
python scripts/verify_detector_geometry.py \
    --rotx 5 --roty 3 --rotz 2 --twotheta 15 \
    --output phase2_combined.json

# Check for significant correlation improvement (>0.5)
```

---

## 🟡 PHASE 3: MOSFLM BEAM CENTER FIX (MEDIUM - 23.33mm error)

### Step 1: Add MOSFLM Convention Handler
**File**: `src/nanobrag_torch/models/detector.py`  
**Method**: `_calculate_pix0_vector()` or similar

- [ ] **ADD** this method:
```python
def _apply_mosflm_beam_convention(self):
    """Apply MOSFLM beam center convention with axis swap and pixel offset"""
    if self.convention == "MOSFLM":
        # MOSFLM swaps F and S axes AND adds 0.5 pixel
        adjusted_f = (self.beam_center_s_mm + 0.5) * self.pixel_size_mm / 1000.0  # S→F
        adjusted_s = (self.beam_center_f_mm + 0.5) * self.pixel_size_mm / 1000.0  # F→S
    else:
        # Standard convention
        adjusted_f = self.beam_center_f_mm * self.pixel_size_mm / 1000.0
        adjusted_s = self.beam_center_s_mm * self.pixel_size_mm / 1000.0
    
    return adjusted_f, adjusted_s
```

- [ ] **UPDATE** pix0_vector calculation to use the convention:
```python
def _calculate_pix0_vector(self):
    # Apply MOSFLM convention if needed
    beam_f_m, beam_s_m = self._apply_mosflm_beam_convention()
    
    # Calculate pix0 with corrected beam center
    pix0 = (self.distance_m * self.odet_vec_rotated +
            beam_s_m * self.sdet_vec_rotated +
            beam_f_m * self.fdet_vec_rotated)
    
    return pix0
```

### Step 2: Update Default Beam Center
- [ ] **FIND** default beam center initialization
- [ ] **CHANGE** from `51.2` to `51.25` for MOSFLM compatibility

### Step 3: Validate Phase 3
```bash
# Test with corrected beam center
python scripts/verify_detector_geometry.py \
    --beam 51.25 51.25 \
    --rotx 5 --roty 3 --rotz 2 --twotheta 15 \
    --output phase3_validation.json

# Test beam center scaling
for beam in 0 25.6 51.2 76.8; do
    python scripts/verify_detector_geometry.py \
        --beam $beam $beam \
        --rotx 5 --roty 3 --rotz 2 --twotheta 15 \
        --output phase3_beam_${beam}.json
done
```

---

## 🟢 PHASE 4: DISTANCE CORRECTION FIX (MEDIUM - 6.4mm error)

### Step 1: Add Distance Correction Method
**File**: `src/nanobrag_torch/models/detector.py`

- [ ] **ADD** this method:
```python
def get_effective_distance(self):
    """
    Apply geometric distance correction for tilted detector.
    When detector is tilted, effective distance = nominal_distance / cos(tilt_angle)
    """
    # Get the rotated detector normal vector (after all rotations)
    detector_normal = self.odet_vec_rotated  # Should already be normalized
    
    # Beam travels along positive X axis
    beam_direction = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64, device=self.device)
    
    # Calculate cosine of angle between beam and detector normal
    cos_angle = torch.dot(beam_direction, detector_normal)
    
    # Prevent division by zero for perpendicular detector
    cos_angle = torch.clamp(cos_angle, min=0.001)
    
    # Apply the distance correction
    effective_distance = self.distance_m / cos_angle
    
    return effective_distance
```

- [ ] **UPDATE** distance usage in calculations:
```python
# Replace self.distance_m with self.get_effective_distance() where needed
effective_dist = self.get_effective_distance()
```

### Step 2: Validate Phase 4
```bash
# Test distance scaling with correction
for dist in 50 100 200 400; do
    python scripts/verify_detector_geometry.py \
        --distance $dist \
        --rotx 5 --roty 3 --rotz 2 --twotheta 15 \
        --output phase4_dist_${dist}.json
done

# Verify error doesn't scale linearly with distance anymore
```

---

## ✅ PHASE 5: FINAL INTEGRATION VALIDATION

### Step 1: Run Complete Test Suite
```bash
# Create test result directory
mkdir -p final_validation_results

# Test 1: Simple cubic (baseline)
python scripts/verify_detector_geometry.py \
    --rotx 0 --roty 0 --rotz 0 --twotheta 0 \
    --output final_validation_results/simple_cubic.json

# Test 2: Original problematic tilted configuration
python scripts/verify_detector_geometry.py \
    --rotx 5 --roty 3 --rotz 2 --twotheta 15 \
    --beam 51.25 51.25 \
    --output final_validation_results/tilted_fixed.json

# Test 3: Various rotation combinations
for rotx in 0 5 10; do
    for roty in 0 3 6; do
        python scripts/verify_detector_geometry.py \
            --rotx $rotx --roty $roty --rotz 2 --twotheta 10 \
            --output final_validation_results/rot_${rotx}_${roty}.json
    done
done
```

### Step 2: Verify Success Criteria
- [ ] **Simple cubic correlation** > 0.999
- [ ] **Tilted detector correlation** > 0.999 (was 0.040)
- [ ] **All test correlations** > 0.99
- [ ] **Maximum pix0 error** < 1mm
- [ ] **Identity configuration error** < 0.1mm

### Step 3: Run Gradient Check
```bash
# Ensure differentiability maintained
python -c "
import torch
from src.nanobrag_torch.models.detector import Detector

# Create detector with requires_grad
config = {'detector_distance_mm': 100.0, 'requires_grad': True}
detector = Detector(config)

# Test gradient flow
loss = detector.get_pixel_positions().sum()
loss.backward()
print('Gradient check passed!' if detector.distance_m.grad is not None else 'GRADIENT BROKEN!')
"
```

### Step 4: Document Changes
- [ ] Update `docs/architecture/detector.md` with new conventions
- [ ] Add comments explaining each fix in the code
- [ ] Update `CLAUDE.md` with lessons learned
- [ ] Create PR with clear description of all changes

---

## 🚨 VALIDATION COMMANDS SUMMARY

```bash
# Quick validation after ALL phases complete
python scripts/verify_detector_geometry.py \
    --rotx 5 --roty 3 --rotz 2 --twotheta 15 \
    --beam 51.25 51.25 --distance 100 \
    --output FINAL_VALIDATION.json

# Expected output:
# - Correlation: >0.999 (was 0.040)
# - pix0_vector error: <0.001m (was 0.066m)
# - Error breakdown: X<0.5mm, Y<0.5mm, Z<0.5mm
```

---

## 🔄 ROLLBACK PROCEDURES

### If Phase 1 Fails:
```bash
cp src/nanobrag_torch/models/detector.py.backup src/nanobrag_torch/models/detector.py
# Debug: Check sign conventions, verify C code basis vectors
```

### If Phase 2 Fails:
```bash
# Revert twotheta_axis to [0, 1, 0]
# Debug: Check rotation direction, verify right-hand rule
```

### If Phase 3 Fails:
```bash
# Remove MOSFLM convention handler
# Debug: Verify axis swap logic, check pixel offset calculation
```

### If Phase 4 Fails:
```bash
# Remove distance correction method
# Debug: Check cos_angle calculation, verify normal vector
```

---

## 📊 EXPECTED OUTCOMES

| Metric | Before Fix | After Fix | Improvement |
|--------|------------|-----------|-------------|
| Tilted Correlation | 0.040 | >0.999 | 25x |
| Identity Error | 192.67mm | <0.1mm | 1900x |
| Twotheta Error | 66.18mm | <1mm | 66x |
| Beam Center Error | 23.33mm | <1mm | 23x |
| Total pix0 Error | 66mm | <1mm | 66x |

---

## ⏱️ TIME ESTIMATES

- Phase 1: 20 minutes (coordinate system)
- Phase 2: 10 minutes (twotheta axis)
- Phase 3: 15 minutes (MOSFLM convention)
- Phase 4: 10 minutes (distance correction)
- Phase 5: 15 minutes (validation)
- **Total: 70 minutes**

---

## 📝 NOTES

1. **CRITICAL**: Do phases in order - each builds on the previous
2. **Test after EVERY change** - don't batch fixes
3. **Keep backups** until all validation passes
4. **Document any deviations** from this plan
5. **If stuck**, check the detailed plan: `DETAILED_FIX_IMPLEMENTATION_PLAN.md`

---

**SUCCESS INDICATOR**: When `verify_detector_geometry.py` shows correlation >0.999 for the tilted configuration, the fix is complete!