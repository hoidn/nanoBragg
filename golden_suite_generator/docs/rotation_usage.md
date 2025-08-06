# nanoBragg.c Rotation Function Analysis

## Key Findings

### 1. The `rotate` Function Definition (lines 3295-3344)

```c
double *rotate(double *v, double *newv, double phix, double phiy, double phiz)
```

**Parameters:**
- `v`: Input vector (1-indexed array, so v[1], v[2], v[3] are x, y, z)
- `newv`: Output vector (can be the same as input for in-place rotation)
- `phix`, `phiy`, `phiz`: Rotation angles in RADIANS around x, y, z axes respectively

### 2. Rotation Convention

The function implements **active rotations** (rotating the vector, not the coordinate system) with the following order:

1. **First**: Rotation around X-axis by `phix`
2. **Then**: Rotation around Y-axis by `phiy`  
3. **Finally**: Rotation around Z-axis by `phiz`

This is an **X-Y-Z Euler angle convention** (intrinsic rotations).

### 3. Rotation Matrices Used

For rotation around X-axis:
```
Rx = | 1     0          0      |
     | 0   cos(phix) -sin(phix)|
     | 0   sin(phix)  cos(phix)|
```

For rotation around Y-axis:
```
Ry = | cos(phiy)  0   sin(phiy)|
     |    0       1      0     |
     |-sin(phiy)  0   cos(phiy)|
```

For rotation around Z-axis:
```
Rz = | cos(phiz) -sin(phiz)  0|
     | sin(phiz)  cos(phiz)  0|
     |    0          0       1|
```

### 4. Misset Angle Usage (lines 1913-1915)

The misset angles are applied to the reciprocal lattice vectors:

```c
rotate(a_star,a_star,misset[1],misset[2],misset[3]);
rotate(b_star,b_star,misset[1],misset[2],misset[3]);
rotate(c_star,c_star,misset[1],misset[2],misset[3]);
```

Where:
- `misset[1]` = rotation around X in radians
- `misset[2]` = rotation around Y in radians  
- `misset[3]` = rotation around Z in radians

### 5. Command Line Input

The misset angles are provided in DEGREES on the command line and converted to radians:

```c
misset[1] = atof(argv[i+1])/RTD;  // RTD = 180/π ≈ 57.2958
misset[2] = atof(argv[i+2])/RTD;
misset[3] = atof(argv[i+3])/RTD;
```

### 6. Important Implementation Details

1. The function uses 1-indexed arrays (C convention in this codebase)
2. Rotations are applied sequentially, not as a single combined rotation matrix
3. Each rotation updates the vector components before the next rotation
4. The function can do in-place rotation when `v == newv`

### 7. Rotation Order Summary

For a vector **v**, applying rotations with angles (phix, phiy, phiz):

**v' = Rz(phiz) · Ry(phiy) · Rx(phix) · v**

This means:
1. First rotate around X by phix
2. Then rotate the result around Y by phiy
3. Finally rotate that result around Z by phiz

This is consistent with **intrinsic X-Y-Z Euler angles** where each rotation is about the transformed axes.