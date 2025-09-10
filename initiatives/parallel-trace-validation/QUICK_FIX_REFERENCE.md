# 🚀 QUICK FIX REFERENCE - Detector Geometry Corrections

**⚡ All fixes needed to achieve >0.999 correlation**

---

## 🔴 FIX #1: COORDINATE BASIS VECTORS (192.67mm error)

```python
# WRONG (current):
self.fdet_vec = torch.tensor([0, 1, 0])
self.sdet_vec = torch.tensor([0, 0, 1])

# CORRECT (fixed):
self.fdet_vec = torch.tensor([0, -1, 0], dtype=torch.float64)  # negative Y
self.sdet_vec = torch.tensor([0, 0, -1], dtype=torch.float64)  # negative Z
self.odet_vec = torch.tensor([1, 0, 0], dtype=torch.float64)   # positive X
```

**Validate**: `python scripts/verify_detector_geometry.py --rotx 0 --roty 0 --rotz 0 --twotheta 0`

---

## 🟠 FIX #2: TWOTHETA AXIS (66.18mm error)

```python
# WRONG (current):
twotheta_axis = torch.tensor([0.0, 1.0, 0.0])  # Y-axis

# CORRECT (fixed):
twotheta_axis = torch.tensor([0.0, 0.0, -1.0], dtype=torch.float64)  # negative Z-axis
```

**Validate**: `python scripts/verify_detector_geometry.py --rotx 0 --roty 0 --rotz 0 --twotheta 15`

---

## 🟡 FIX #3: MOSFLM BEAM CENTER (23.33mm error)

```python
def _apply_mosflm_beam_convention(self):
    if self.convention == "MOSFLM":
        # MOSFLM: Swap axes + add 0.5 pixel
        adjusted_f = (self.beam_center_s_mm + 0.5) * self.pixel_size_mm / 1000.0  # S→F
        adjusted_s = (self.beam_center_f_mm + 0.5) * self.pixel_size_mm / 1000.0  # F→S
    else:
        adjusted_f = self.beam_center_f_mm * self.pixel_size_mm / 1000.0
        adjusted_s = self.beam_center_s_mm * self.pixel_size_mm / 1000.0
    return adjusted_f, adjusted_s
```

**Also**: Change default beam center from `51.2` to `51.25` mm

**Validate**: `python scripts/verify_detector_geometry.py --beam 51.25 51.25 --rotx 5 --roty 3 --rotz 2 --twotheta 15`

---

## 🟢 FIX #4: DISTANCE CORRECTION (6.4mm error)

```python
def get_effective_distance(self):
    detector_normal = self.odet_vec_rotated
    beam_direction = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
    cos_angle = torch.dot(beam_direction, detector_normal)
    cos_angle = torch.clamp(cos_angle, min=0.001)  # prevent div by zero
    return self.distance_m / cos_angle
```

**Use**: Replace `self.distance_m` with `self.get_effective_distance()` in calculations

---

## ✅ FINAL VALIDATION COMMAND

```bash
python scripts/verify_detector_geometry.py \
    --rotx 5 --roty 3 --rotz 2 --twotheta 15 \
    --beam 51.25 51.25 \
    --output FINAL_CHECK.json

# SUCCESS = Correlation > 0.999 (was 0.040)
```

---

## 📊 IMPACT SUMMARY

| Fix | Error Resolved | Impact |
|-----|---------------|---------|
| Coordinate Basis | 192.67mm | Critical - fixes identity config |
| Twotheta Axis | 66.18mm | High - fixes rotation errors |
| MOSFLM Beam | 23.33mm | Medium - fixes beam scaling |
| Distance Correction | 6.4mm | Medium - fixes tilt errors |
| **TOTAL** | **~288mm → <1mm** | **Correlation: 0.040 → >0.999** |

---

## ⚠️ COMMON PITFALLS

1. **Don't forget dtype**: Always use `dtype=torch.float64` for precision
2. **Check convention**: MOSFLM vs XDS have different axes
3. **Preserve gradients**: Don't use `.item()` or `.detach()`
4. **Test incrementally**: Validate after EACH fix
5. **Use correct beam center**: 51.25mm not 51.2mm for MOSFLM

---

## 🔄 QUICK ROLLBACK

```bash
# If anything breaks:
cp src/nanobrag_torch/models/detector.py.backup src/nanobrag_torch/models/detector.py
```

---

**🎯 TARGET**: Correlation >0.999 | Error <1mm | All tests pass