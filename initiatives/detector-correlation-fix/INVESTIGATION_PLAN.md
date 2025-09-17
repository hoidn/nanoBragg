# Detector Correlation Investigation Plan
## Tilted Configuration Correlation Failure (0.040)

**Created**: 2025-01-09  
**Goal**: Identify and fix root cause of catastrophic correlation failure in tilted detector configurations  
**Current State**: Baseline works (0.993), tilted fails (0.040), ~208 pixel displacement  

---

## Priority 1: Immediate Diagnostics (Day 1)

### 1.1 Parameter Verification [2 hours]
**Hypothesis**: C code may not be receiving correct parameters, especially `twotheta_axis`

**Test Steps**:
```bash
# Step 1: Add debug output to C code
cd golden_suite_generator
# Add printf statements in nanoBragg.c after parameter parsing:
# printf("DEBUG: twotheta_axis = [%f, %f, %f]\n", twotheta_axis[0], twotheta_axis[1], twotheta_axis[2]);

# Step 2: Run with explicit parameters
./nanoBragg -lambda 6.2 -N 5 -cell 100 100 100 90 90 90 -default_F 100 \
  -distance 100 -detpixels 1024 -detsize 102.4 -pixel 0.1 \
  -beam 51.2 51.2 -detector_rotx 5 -detector_roty 3 -detector_rotz 2 \
  -twotheta 20 -twotheta_axis 0 0 -1 -pivot SAMPLE \
  -floatfile tilted_debug.bin 2>&1 | tee c_debug.log

# Step 3: Verify parameter reception
grep "DEBUG:" c_debug.log
```

**Success Criteria**: 
- Confirm C receives `twotheta_axis = [0.0, 0.0, -1.0]`
- All rotation parameters match PyTorch config exactly

### 1.2 Single Pixel Trace Comparison [3 hours]
**Hypothesis**: Rotation matrices or application order differs between implementations

**Test Steps**:
```bash
# Step 1: Generate C trace for pixel (377, 644)
cd archive/parallel_trace_debugger
./generate_c_trace.sh 377 644 > c_pixel_377_644.trace

# Step 2: Generate Python trace for same pixel
python debug_beam_pivot_trace.py --pixel 377 644 > py_pixel_377_644.trace

# Step 3: Compare traces
python compare_traces.py c_pixel_377_644.trace py_pixel_377_644.trace
```

**Key Checkpoints**:
- [ ] Initial basis vectors match
- [ ] Individual rotation matrices (Rx, Ry, Rz) match
- [ ] Twotheta rotation matrix matches
- [ ] Composite rotation matrix matches
- [ ] pix0_vector calculation matches
- [ ] Final pixel coordinates match

---

## Priority 2: Rotation Convention Deep Dive (Day 1-2)

### 2.1 Rotation Matrix Element Comparison [2 hours]
**Hypothesis**: Rotation matrix construction differs (Euler angle conventions)

**Test Script**: `scripts/test_rotation_matrices.py`
```python
#!/usr/bin/env python3
"""Compare rotation matrices between C and PyTorch implementations."""

import numpy as np
import torch
from nanobrag_torch.utils.geometry import angles_to_rotation_matrix

def test_rotation_matrices():
    """Test individual and composite rotation matrices."""
    
    # Test angles (in radians)
    rotx = np.deg2rad(5.0)
    roty = np.deg2rad(3.0)
    rotz = np.deg2rad(2.0)
    
    # PyTorch rotation matrix
    R_pytorch = angles_to_rotation_matrix(
        torch.tensor(rotx), 
        torch.tensor(roty), 
        torch.tensor(rotz)
    )
    
    # C-style rotation matrix (manually computed)
    # Rx rotation around X axis
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(rotx), -np.sin(rotx)],
        [0, np.sin(rotx), np.cos(rotx)]
    ])
    
    # Ry rotation around Y axis  
    Ry = np.array([
        [np.cos(roty), 0, np.sin(roty)],
        [0, 1, 0],
        [-np.sin(roty), 0, np.cos(roty)]
    ])
    
    # Rz rotation around Z axis
    Rz = np.array([
        [np.cos(rotz), -np.sin(rotz), 0],
        [np.sin(rotz), np.cos(rotz), 0],
        [0, 0, 1]
    ])
    
    # Test different composition orders
    R_xyz = Rz @ Ry @ Rx  # Standard XYZ Euler
    R_zyx = Rx @ Ry @ Rz  # Reverse order
    
    print("PyTorch rotation matrix:")
    print(R_pytorch.numpy())
    print("\nC-style XYZ composition (Rz·Ry·Rx):")
    print(R_xyz)
    print("\nDifference:")
    print(R_pytorch.numpy() - R_xyz)
    
    # Check if matches reverse order
    print("\nC-style ZYX composition (Rx·Ry·Rz):")
    print(R_zyx)
    print("\nDifference from PyTorch:")
    print(R_pytorch.numpy() - R_zyx)

if __name__ == "__main__":
    test_rotation_matrices()
```

### 2.2 Twotheta Rotation Verification [2 hours]
**Hypothesis**: Twotheta rotation axis or application differs

**Test Script**: `scripts/test_twotheta_rotation.py`
```python
#!/usr/bin/env python3
"""Test twotheta rotation application."""

import numpy as np
import torch
from nanobrag_torch.utils.geometry import rotate_around_axis

def test_twotheta():
    """Compare twotheta rotation implementations."""
    
    # Test vector
    test_vec = np.array([1.0, 0.0, 0.0])
    
    # MOSFLM twotheta axis
    axis_mosflm = np.array([0.0, 0.0, -1.0])
    
    # Alternative axes to test
    axis_xds = np.array([0.0, 1.0, 0.0])
    axis_alt = np.array([0.0, 0.0, 1.0])
    
    # Rotation angle
    twotheta = np.deg2rad(20.0)
    
    # Apply rotations
    rotated_mosflm = rotate_around_axis(
        torch.tensor(test_vec),
        torch.tensor(axis_mosflm),
        torch.tensor(twotheta)
    )
    
    print(f"Original vector: {test_vec}")
    print(f"MOSFLM axis [0,0,-1] rotation: {rotated_mosflm.numpy()}")
    
    # Manual Rodrigues formula for verification
    k = axis_mosflm / np.linalg.norm(axis_mosflm)
    v_rot = (test_vec * np.cos(twotheta) + 
             np.cross(k, test_vec) * np.sin(twotheta) + 
             k * np.dot(k, test_vec) * (1 - np.cos(twotheta)))
    
    print(f"Manual Rodrigues result: {v_rot}")
    print(f"Difference: {rotated_mosflm.numpy() - v_rot}")

if __name__ == "__main__":
    test_twotheta()
```

---

## Priority 3: Coordinate System Verification (Day 2)

### 3.1 Basis Vector Convention Test [3 hours]
**Hypothesis**: Initial basis vector definitions differ between implementations

**Test Steps**:
1. Extract basis vectors from both implementations at initialization
2. Compare MOSFLM vs XDS conventions
3. Verify handedness of coordinate system

**Verification Script**: `scripts/verify_basis_vectors.py`
```python
#!/usr/bin/env python3
"""Verify basis vector conventions."""

import torch
from nanobrag_torch.config import DetectorConfig, DetectorConvention
from nanobrag_torch.models.detector import Detector

def verify_basis_vectors():
    """Compare basis vectors for different conventions."""
    
    # MOSFLM convention
    config_mosflm = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        distance_mm=100.0,
        detector_rotx_deg=0.0,
        detector_roty_deg=0.0,
        detector_rotz_deg=0.0,
    )
    
    det_mosflm = Detector(config_mosflm)
    
    print("MOSFLM Convention:")
    print(f"  fdet (fast): {det_mosflm.fdet_vec}")
    print(f"  sdet (slow): {det_mosflm.sdet_vec}")
    print(f"  odet (beam): {det_mosflm.odet_vec if hasattr(det_mosflm, 'odet_vec') else 'N/A'}")
    
    # Check orthogonality
    dot_fs = torch.dot(det_mosflm.fdet_vec, det_mosflm.sdet_vec)
    print(f"  fdet·sdet = {dot_fs.item():.6f} (should be 0)")
    
    # Check handedness
    cross = torch.cross(det_mosflm.fdet_vec, det_mosflm.sdet_vec)
    print(f"  fdet × sdet = {cross} (should align with beam)")

if __name__ == "__main__":
    verify_basis_vectors()
```

### 3.2 Pixel Coordinate Mapping Test [2 hours]
**Hypothesis**: Pixel-to-lab coordinate transformation differs

**Test**: Compare pixel (0,0), (512,512), (1023,1023) mappings between C and PyTorch

---

## Priority 4: Integration Testing (Day 2-3)

### 4.1 Progressive Rotation Test [4 hours]
**Hypothesis**: Error accumulates with rotation magnitude

**Test Matrix**:
| Test | rotx | roty | rotz | twotheta | Expected |
|------|------|------|------|----------|----------|
| 1    | 0    | 0    | 0    | 0        | >0.99    |
| 2    | 5    | 0    | 0    | 0        | >0.95    |
| 3    | 0    | 3    | 0    | 0        | >0.95    |
| 4    | 0    | 0    | 2    | 0        | >0.95    |
| 5    | 5    | 3    | 2    | 0        | >0.90    |
| 6    | 0    | 0    | 0    | 20       | Check    |
| 7    | 5    | 3    | 2    | 20       | 0.040    |

### 4.2 BEAM vs SAMPLE Pivot Comparison [3 hours]
**Test**: Run same configuration with both pivot modes
```bash
# BEAM pivot
python scripts/verify_detector_geometry.py --pivot BEAM

# SAMPLE pivot  
python scripts/verify_detector_geometry.py --pivot SAMPLE
```

---

## Priority 5: Fix Implementation (Day 3-4)

### 5.1 Implement Identified Fix
Based on findings from Priority 1-4, implement the fix:
- [ ] Update rotation matrix construction if needed
- [ ] Fix rotation application order if needed
- [ ] Correct basis vector conventions if needed
- [ ] Update pix0_vector calculation if needed

### 5.2 Validation Suite
- [ ] Run full correlation test suite
- [ ] Verify no regression in baseline case
- [ ] Confirm tilted correlation >0.99
- [ ] Check gradient flow still works

---

## Success Metrics

### Minimum Acceptable
- Tilted detector correlation > 0.95
- Baseline correlation maintained > 0.99
- All existing tests pass

### Target Goals  
- Tilted detector correlation > 0.999
- Pixel-perfect alignment (<1 pixel displacement)
- Full understanding of convention differences documented

---

## Escalation Path

If correlation remains poor after Priority 1-3:
1. **Deep C-code instrumentation**: Add trace output for every matrix operation
2. **Subpixel analysis**: Check if issue is in pixel center vs edge conventions  
3. **External validation**: Compare against third-party diffraction software
4. **Mathematical proof**: Derive expected transformation analytically

---

## Timeline

- **Day 1**: Priority 1-2 (Parameter verification, traces, rotation matrices)
- **Day 2**: Priority 3-4 (Coordinate systems, integration tests)
- **Day 3**: Priority 5 (Fix implementation)
- **Day 4**: Validation and documentation

---

## Notes

- Keep all test outputs in `reports/detector_verification/investigation/`
- Document each finding immediately in this file
- Create minimal reproducible examples for any bugs found
- Consider creating a Jupyter notebook for interactive debugging