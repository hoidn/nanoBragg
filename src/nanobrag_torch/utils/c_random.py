"""C-compatible Random Number Generator (Minimal Standard LCG + Bays-Durham Shuffle)

This module implements the Minimal Standard Linear Congruential Generator
(Park & Miller 1988) with Bays-Durham shuffle, providing bitwise-exact
compatibility with nanoBragg.c's `ran1()` function.

Algorithm Overview:
-------------------
- Core: LCG with multiplier IA=16807, modulus IM=2147483647 (2^31 - 1)
- Enhancement: 32-element Bays-Durham shuffle table for improved randomness
- Period: ~2.1 billion (IM - 1), sufficient for most simulations
- Output: Uniform random values in [1.2e-7, 1.0-1.2e-7] (excludes exact 0.0/1.0)

Seed Contract (C Pointer Side-Effect Semantics):
------------------------------------------------
The C implementation uses **pointer side effects** to advance seed state:
    double ran1(long *idum) { ... *idum = new_state; ... }

Each call mutates the seed variable in-place. The PyTorch implementation
replicates this via the LCGRandom class (CLCG):
    rng = CLCG(seed=12345)
    val1 = rng.ran1()  # Advances internal state
    val2 = rng.ran1()  # Advances again (deterministic sequence)

Key Functions:
--------------
- mosaic_rotation_umat(): Generates random rotation matrix for mosaic/misset
  Consumes **3 RNG values** per call (axis direction + angle scaling)
- CLCG.ran1(): Generates single uniform random value in [0, 1)
  Advances internal state by 1 step (equivalent to C's `ran1(&seed)`)

Determinism Requirements:
--------------------------
1. Same seed → identical random sequence (bitwise reproducible)
2. Independent seeds for noise/mosaic/misset domains (avoid correlation)
3. CPU/GPU neutrality: Results independent of device (CPU vs CUDA)

Validation:
-----------
Bitstream parity verified by test_lcg_compatibility (AT-PARALLEL-024).
Determinism validated by AT-PARALLEL-013 (same-seed runs, correlation ≥0.9999999).

References:
-----------
- C Source: nanoBragg.c lines 4143-4185 (ran1), 3820-3868 (mosaic_rotation_umat)
- Spec: specs/spec-a-core.md §5.3 (RNG determinism)
- Architecture: arch.md ADR-05 (Deterministic Sampling & Seeds)
- Phase B3 Analysis: reports/determinism-callchain/phase_b3/20251011T051737Z/c_seed_flow.md
"""

import math
import torch
from typing import Optional, Tuple
import numpy as np


class CLCG:
    """C-compatible Linear Congruential Generator (LCG).

    This class implements the ran1() function from nanoBragg.c, which is based on
    the Park and Miller "Minimal Standard" generator with Bays-Durham shuffle.

    C-Code Implementation Reference (from nanoBragg.c, lines ~49100-49150):
    ```c
    #define IA 16807
    #define IM 2147483647
    #define AM (1.0/IM)
    #define IQ 127773
    #define IR 2836
    #define NTAB 32
    #define NDIV (1+(IM-1)/NTAB)
    #define EPS 1.2e-7
    #define RNMX (1.0-EPS)

    float ran1(long *idum)
    {
        int j;
        long k;
        static long iy=0;
        static long iv[NTAB];
        float temp;

        if (*idum <= 0 || !iy) {
            // first time around.  don't want idum=0
            if(-(*idum) < 1) *idum=1;
            else *idum = -(*idum);
            // load the shuffle table
            for(j=NTAB+7;j>=0;j--) {
                k=(*idum)/IQ;
                *idum=IA*(*idum-k*IQ)-IR*k;
                if(*idum < 0) *idum += IM;
                if(j < NTAB) iv[j] = *idum;
            }
            iy=iv[0];
        }
        // always start here after initializing
        k=(*idum)/IQ;
        *idum=IA*(*idum-k*IQ)-IR*k;
        if (*idum < 0) *idum += IM;
        j=iy/NDIV;
        iy=iv[j];
        iv[j] = *idum;
        if((temp=AM*iy) > RNMX) return RNMX;
        else return temp;
    }
    ```
    """

    # Constants from C implementation
    IA = 16807
    IM = 2147483647
    AM = 1.0 / IM
    IQ = 127773
    IR = 2836
    NTAB = 32
    NDIV = 1 + (IM - 1) // NTAB
    EPS = 1.2e-7
    RNMX = 1.0 - EPS

    def __init__(self, seed: Optional[int] = None):
        """Initialize the LCG with a seed.

        Args:
            seed: Random seed. If None, uses 42 as default.
        """
        self.seed = seed if seed is not None else 42
        self.idum = abs(self.seed) if self.seed != 0 else 1
        self.iy = 0
        self.iv = [0] * self.NTAB
        self._initialized = False

    def ran1(self) -> float:
        """Generate a uniform random deviate between 0 and 1.

        Returns:
            A float between 0 and RNMX (approximately 1.0).
        """
        if not self._initialized or self.idum <= 0:
            # Initialize the generator
            if self.idum < 1:
                self.idum = 1

            # Load the shuffle table
            for j in range(self.NTAB + 7, -1, -1):
                k = self.idum // self.IQ
                self.idum = self.IA * (self.idum - k * self.IQ) - self.IR * k
                if self.idum < 0:
                    self.idum += self.IM
                if j < self.NTAB:
                    self.iv[j] = self.idum

            self.iy = self.iv[0]
            self._initialized = True

        # Normal operation
        k = self.idum // self.IQ
        self.idum = self.IA * (self.idum - k * self.IQ) - self.IR * k
        if self.idum < 0:
            self.idum += self.IM

        j = self.iy // self.NDIV
        self.iy = self.iv[j]
        self.iv[j] = self.idum

        temp = self.AM * self.iy
        return min(temp, self.RNMX)


def mosaic_rotation_umat(
    mosaicity: float,
    seed: Optional[int] = None,
    dtype: Optional[torch.dtype] = None,
    device: torch.device = torch.device('cpu')
) -> torch.Tensor:
    """Generate a random unitary rotation matrix within a spherical cap.

    This function ports the mosaic_rotation_umat() function from nanoBragg.c,
    which generates a random rotation matrix with maximum rotation angle
    limited by the mosaicity parameter.

    C-Code Implementation Reference (from nanoBragg.c, lines ~48855-48905):
    ```c
    double *mosaic_rotation_umat(float mosaicity, double umat[9], long *seed)
    {
        float ran1(long *idum);
        double r1,r2,r3,xyrad,rot;
        double v1,v2,v3;
        double t1,t2,t3,t6,t7,t8,t9,t11,t12,t15,t19,t20,t24;

        // make three random uniform deviates on [-1:1]
        r1= (double) 2.0*ran1(seed)-1.0;
        r2= (double) 2.0*ran1(seed)-1.0;
        r3= (double) 2.0*ran1(seed)-1.0;

        xyrad = sqrt(1.0-r2*r2);
        rot = mosaicity*powf((1.0-r3*r3),(1.0/3.0));

        v1 = xyrad*sin(M_PI*r1);
        v2 = xyrad*cos(M_PI*r1);
        v3 = r2;

        // quaternion calculation
        t1 =  cos(rot);
        t2 =  1.0 - t1;
        t3 =  v1*v1;
        t6 =  t2*v1;
        t7 =  t6*v2;
        t8 =  sin(rot);
        t9 =  t8*v3;
        t11 = t6*v3;
        t12 = t8*v2;
        t15 = v2*v2;
        t19 = t2*v2*v3;
        t20 = t8*v1;
        t24 = v3*v3;

        // populate the unitary rotation matrix
        umat[0] = uxx = t1 + t2*t3;
        umat[1] = uxy = t7 - t9;
        umat[2] = uxz = t11 + t12;
        umat[3] = uyx = t7 + t9;
        umat[4] = uyy = t1 + t2*t15;
        umat[5] = uyz = t19 - t20;
        umat[6] = uzx = t11 - t12;
        umat[7] = uzy = t19 + t20;
        umat[8] = uzz = t1 + t2*t24;
    }
    ```

    Args:
        mosaicity: Maximum rotation angle in radians.
        seed: Random seed for reproducibility.
        dtype: Data type for output tensor (default: torch.get_default_dtype())
        device: Device for output tensor (default: CPU)

    Returns:
        A 3x3 unitary rotation matrix as a torch.Tensor.

    RNG Consumption:
    ----------------
    This function consumes **3 random values** per call:
    1. r1: Axis direction angle (uniform on [-1, 1])
    2. r2: Axis Z-component (uniform on [-1, 1])
    3. r3: Rotation magnitude scaling (uniform on [-1, 1])

    C Equivalent:
    -------------
    Replicates nanoBragg.c lines 3820-3868 (mosaic_rotation_umat).
    C version uses pointer side effects: `ran1(&seed)` mutates seed in-place.
    PyTorch version uses stateful CLCG class for memory safety.

    Seed State Progression Example:
    --------------------------------
    rng = CLCG(seed=-12345678)
    umat1 = mosaic_rotation_umat(1.0, seed=-12345678)  # Consumes 3 values
    # For next call, seed has advanced 3 steps internally

    For 10 mosaic domains: Total 30 RNG calls → seed advances 30 steps.
    """
    # Use default dtype if not specified
    if dtype is None:
        dtype = torch.get_default_dtype()

    rng = CLCG(seed)

    # Make three random uniform deviates on [-1:1]
    r1 = 2.0 * rng.ran1() - 1.0
    r2 = 2.0 * rng.ran1() - 1.0
    r3 = 2.0 * rng.ran1() - 1.0

    xyrad = math.sqrt(1.0 - r2 * r2)
    rot = mosaicity * math.pow(1.0 - r3 * r3, 1.0/3.0)

    v1 = xyrad * math.sin(math.pi * r1)
    v2 = xyrad * math.cos(math.pi * r1)
    v3 = r2

    # Quaternion calculation
    t1 = math.cos(rot)
    t2 = 1.0 - t1
    t3 = v1 * v1
    t6 = t2 * v1
    t7 = t6 * v2
    t8 = math.sin(rot)
    t9 = t8 * v3
    t11 = t6 * v3
    t12 = t8 * v2
    t15 = v2 * v2
    t19 = t2 * v2 * v3
    t20 = t8 * v1
    t24 = v3 * v3

    # Populate the unitary rotation matrix
    umat = torch.zeros(3, 3, dtype=dtype, device=device)
    umat[0, 0] = t1 + t2 * t3      # uxx
    umat[0, 1] = t7 - t9            # uxy
    umat[0, 2] = t11 + t12          # uxz
    umat[1, 0] = t7 + t9            # uyx
    umat[1, 1] = t1 + t2 * t15      # uyy
    umat[1, 2] = t19 - t20          # uyz
    umat[2, 0] = t11 - t12          # uzx
    umat[2, 1] = t19 + t20          # uzy
    umat[2, 2] = t1 + t2 * t24      # uzz

    return umat


def umat2misset(umat: torch.Tensor) -> Tuple[float, float, float]:
    """Convert a unitary rotation matrix into misset angles.

    This function ports the umat2misset() function from nanoBragg.c,
    which decomposes a rotation matrix into XYZ Euler angles.

    C-Code Implementation Reference (from nanoBragg.c, lines ~48910-48995):
    ```c
    double *umat2misset(double umat[9],double *missets)
    {
        // Extract and normalize matrix elements
        uxx=umat[0];uxy=umat[1];uxz=umat[2];
        uyx=umat[3];uyy=umat[4];uyz=umat[5];
        uzx=umat[6];uzy=umat[7];uzz=umat[8];

        // ... normalization code ...

        // Decompose into Euler angles
        if(uzx*uzx < 1.0)
        {
            rotx = atan2(uzy,uzz);
            roty = atan2(-uzx,sqrt(uzy*uzy+uzz*uzz));
            rotz = atan2(uyx,uxx);
        }
        else
        {
            rotx = atan2(1,1)*4;  // pi
            roty = atan2(1,1)*2;  // pi/2
            rotz = atan2(uxy,-uyy);
        }

        missets[1] = rotx;
        missets[2] = roty;
        missets[3] = rotz;
    }
    ```

    Args:
        umat: A 3x3 unitary rotation matrix.

    Returns:
        A tuple of (rotx, roty, rotz) in radians.
    """
    # Extract matrix elements
    if isinstance(umat, torch.Tensor):
        u = umat.cpu().numpy()
    else:
        u = np.array(umat)

    uxx, uxy, uxz = u[0, 0], u[0, 1], u[0, 2]
    uyx, uyy, uyz = u[1, 0], u[1, 1], u[1, 2]
    uzx, uzy, uzz = u[2, 0], u[2, 1], u[2, 2]

    # Normalize rows
    mx = math.sqrt(uxx*uxx + uxy*uxy + uxz*uxz)
    my = math.sqrt(uyx*uyx + uyy*uyy + uyz*uyz)
    mz = math.sqrt(uzx*uzx + uzy*uzy + uzz*uzz)

    if mx > 0:
        uxx /= mx; uxy /= mx; uxz /= mx
    if my > 0:
        uyx /= my; uyy /= my; uyz /= my
    if mz > 0:
        uzx /= mz; uzy /= mz; uzz /= mz

    # Decompose into Euler angles
    if uzx * uzx < 1.0:
        rotx = math.atan2(uzy, uzz)
        roty = math.atan2(-uzx, math.sqrt(uzy*uzy + uzz*uzz))
        rotz = math.atan2(uyx, uxx)
    else:
        # Gimbal lock case
        rotx = math.pi
        roty = math.pi / 2
        rotz = math.atan2(uxy, -uyy)

    return (rotx, roty, rotz)