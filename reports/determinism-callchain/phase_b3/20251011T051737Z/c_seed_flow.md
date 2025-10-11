# nanoBragg C-Code Seed Propagation Callchain

**Phase:** B3 (Evidence — C seed contract capture)
**Date:** 2025-10-11T05:17:37Z
**Purpose:** Document the C-side RNG seed initialization, propagation, and invocation flow to complete Phase B3 of `plans/active/determinism.md` and unblock PyTorch parity debugging.

---

## Executive Summary

The nanoBragg C implementation uses a **Minimal Standard Linear Congruential Generator (LCG)** with a **Bays-Durham shuffle** (`ran1`) as the single source of all pseudorandom values. Three distinct seed variables control deterministic behavior across three RNG domains:

1. **`misset_seed`** — Controls crystal misset (static orientation) rotations
2. **`mosaic_seed`** — Controls mosaic domain rotations (crystal imperfections)
3. **`seed`** (noise_seed) — Controls Poisson noise generation

All three seeds are propagated via **pointer side effects** (`long *idum`) through `ran1`, mutating the seed state in-place on every call. This side-effect contract is **critical** for determinism: each invocation advances the PRNG state predictably, and multiple domains must use independent seed variables to avoid cross-contamination.

---

## 1. Entry Point: CLI Argument Parsing

**Source:** `golden_suite_generator/nanoBragg.c` lines 375, 374, 1123-1129

### 1.1 Seed Variable Initialization

```c
// Line 374: mosaic_seed default (note: help text says "1234567" but code is -12345678)
long mosaic_seed = -12345678;

// Line 375: misset_seed default (inherits from noise seed)
long misset_seed = seed;
```

**Critical Observations:**
- `misset_seed` defaults to the value of `seed` (noise seed), which is computed from wall-clock time if not provided
- `mosaic_seed` has a fixed default of `-12345678` (hardcoded, independent of wall-clock time)
- **Spec Reference:** `specs/spec-a-core.md` §5.3 defines canonical defaults:
  - `noise_seed` default: negative wall-clock time
  - `mosaic_seed` default: `-12345678`
  - `misset_seed` default: inherits `noise_seed` unless explicitly set

### 1.2 CLI Flag Processing

```c
// Lines 1123-1125: -mosaic_seed override
if(strstr(argv[i], "-mosaic_seed") && (argc > (i+1)))
{
    mosaic_seed = -atoi(argv[i+1]);
}

// Lines 1127-1129: -misset_seed override
if(strstr(argv[i], "-misset_seed") && (argc > (i+1)))
{
    misset_seed = -atoi(argv[i+1]);
}
```

**Note:** Both seeds are negated (`-atoi`) per Numerical Recipes convention: `ran1` requires `idum <= 0` for initialization.

---

## 2. RNG Core: `ran1` (Minimal Standard LCG + Bays-Durham Shuffle)

**Source:** `golden_suite_generator/nanoBragg.c` lines 4143-4185
**Algorithm:** Minimal Standard LCG (Park & Miller 1988) with Bays-Durham shuffle table

### 2.1 Constants

```c
#define IA 16807          // Multiplier (7^5)
#define IM 2147483647     // Modulus (2^31 - 1, Mersenne prime)
#define AM (1.0/IM)       // Reciprocal for scaling to [0,1]
#define IQ 127773         // Schrage decomposition quotient
#define IR 2836           // Schrage decomposition remainder
#define NTAB 32           // Shuffle table size
#define NDIV (1+(IM-1)/NTAB)
#define EPS 1.2e-7
#define RNMX (1.0-EPS)    // Maximum return value (prevents exact 1.0)
```

### 2.2 State Variables (Static, Per-Process)

```c
static long iy=0;         // Current shuffle output
static long iv[NTAB];     // Shuffle table (32 precomputed values)
```

**CRITICAL:** These are **global static** variables shared across all `ran1` calls. The shuffle table is initialized once per seed and then reused. Multiple independent RNG domains (misset, mosaic, noise) **MUST** use separate seed pointers to maintain independent state chains.

### 2.3 Initialization Logic (First Call)

```c
if (*idum <= 0 || !iy) {
    /* first time around.  don't want idum=0 */
    if(-(*idum) < 1) *idum=1;
    else *idum = -(*idum);

    /* load the shuffle table */
    for(j=NTAB+7;j>=0;j--) {
        k=(*idum)/IQ;
        *idum=IA*(*idum-k*IQ)-IR*k;
        if(*idum < 0) *idum += IM;
        if(j < NTAB) iv[j] = *idum;
    }
    iy=iv[0];
}
```

**Key Points:**
- Trigger: `*idum <= 0` (negative seed) or `!iy` (uninitialized shuffle table)
- Seed normalization: Negates input and clamps to range [1, IM-1]
- Warm-up: Advances LCG 40 times (`NTAB+7 = 39`) to fill shuffle table and discard transients

### 2.4 Main Loop (Every Call)

```c
/* always start here after initializing */
k=(*idum)/IQ;
*idum=IA*(*idum-k*IQ)-IR*k;  // Schrage's method for safe modular arithmetic
if (*idum < 0) *idum += IM;
j=iy/NDIV;                    // Select shuffle slot
iy=iv[j];                     // Output previous value at that slot
iv[j] = *idum;                // Store new LCG output in slot
if((temp=AM*iy) > RNMX) return RNMX;
else return temp;
```

**Output Range:** `[EPS, RNMX]` ≈ `[1.2e-7, 1.0-1.2e-7]` (excludes exact 0.0 and 1.0)

**Side Effect:** Every call mutates `*idum` in-place, advancing the LCG state. This is **not thread-safe** and requires careful seed isolation.

---

## 3. Misset Rotation Seeding

**Source:** `golden_suite_generator/nanoBragg.c` line 2083
**Context:** Static crystal misorientation application (executed once per simulation)

### 3.1 Invocation Site

```c
// Line 2083: Called when -misset random is specified
mosaic_rotation_umat(90.0, umat, &misset_seed);
```

**Arguments:**
- `mosaicity = 90.0` degrees (large rotation, full randomization)
- `umat` — output 3×3 rotation matrix (stored in reciprocal space)
- `&misset_seed` — **pointer** to seed variable (mutated by `ran1` calls)

### 3.2 `mosaic_rotation_umat` Implementation

**Source:** Lines 3820-3868

```c
double *mosaic_rotation_umat(float mosaicity, double umat[9], long *seed)
{
    float ran1(long *idum);
    double r1,r2,r3,xyrad,rot;
    // ...

    /* make three random uniform deviates on [-1:1] */
    r1= (double) 2.0*ran1(seed)-1.0;  // Call 1: axis component X
    r2= (double) 2.0*ran1(seed)-1.0;  // Call 2: axis component Y
    r3= (double) 2.0*ran1(seed)-1.0;  // Call 3: angle scaling

    xyrad = sqrt(1.0-r2*r2);
    rot = mosaicity*powf((1.0-r3*r3),(1.0/3.0));

    v1 = xyrad*sin(M_PI*r1);
    v2 = xyrad*cos(M_PI*r1);
    v3 = r2;

    /* [quaternion calculation and umat population omitted for brevity] */
    return umat;
}
```

**RNG Consumption:** **3 calls** to `ran1(seed)` per invocation
- `r1` — uniform on [0,1], scaled to [-1,1], used to sample rotation axis direction
- `r2` — uniform on [0,1], scaled to [-1,1], affects axis Z-component
- `r3` — uniform on [0,1], scaled to [-1,1], determines rotation angle magnitude

**Seed Mutation:** `*seed` is advanced 3 times (via `ran1` side effects)

---

## 4. Mosaic Domain Seeding

**Source:** `golden_suite_generator/nanoBragg.c` line 2689
**Context:** Mosaic crystal modeling (loop over `mosaic_domains`, typically 10-100 iterations)

### 4.1 Invocation Site

```c
// Line 2689: Inside mosaic domain loop
for(mos_tic=0; mos_tic < mosaic_domains; ++mos_tic) {
    mosaic_rotation_umat(mosaic_spread, mosaic_umats+9*mos_tic, &mosaic_seed);
    // ...
}
```

**Arguments:**
- `mosaic_spread` — typically 0.1–2.0 degrees (small rotations)
- `mosaic_umats+9*mos_tic` — array of 3×3 matrices (one per domain)
- `&mosaic_seed` — **pointer** to seed variable (shared across loop, mutated each iteration)

### 4.2 Seed Propagation Across Domains

**CRITICAL:** The mosaic loop calls `mosaic_rotation_umat` repeatedly with the **same seed pointer**. Each call:
1. Consumes 3 random values from `ran1(&mosaic_seed)`
2. Mutates `mosaic_seed` in-place (advances LCG state 3 steps)
3. Produces a deterministic but unique rotation matrix for each domain

**Example Seed State Progression** (10 domains):
- Domain 0: `mosaic_seed` initial state → calls 1-3 → `mosaic_seed` state after 3 steps
- Domain 1: `mosaic_seed` state after 3 steps → calls 4-6 → state after 6 steps
- Domain 9: `mosaic_seed` state after 27 steps → calls 28-30 → final state after 30 steps

**Total RNG Consumption:** `3 * mosaic_domains` calls to `ran1`

---

## 5. Seed Independence Guarantee

**Spec Requirement:** `specs/spec-a-core.md` §5.3 mandates independent RNG domains to avoid unintended correlation between crystal orientation, mosaic structure, and noise patterns.

**C Implementation Strategy:**
- Use **separate seed variables** (`misset_seed`, `mosaic_seed`, `seed`)
- Pass seeds via **pointer references** (`&misset_seed`, `&mosaic_seed`)
- Allow `ran1` to mutate each seed independently via side effects

**Violation Risk:** If the same seed variable were passed to both `mosaic_rotation_umat` (misset) and the mosaic loop, the LCG chains would interleave, breaking determinism and creating unintended correlations.

**PyTorch Parity Implication:**
The PyTorch implementation **MUST** replicate this pointer-based side-effect contract. Options:
1. **Stateful seed wrapper:** Encapsulate seed state in a class with `next()` method
2. **Explicit state passing:** Thread seed value through function returns
3. **Separate Generator objects:** Use `torch.Generator` instances with distinct seeds (IF bitstream parity is verified)

---

## 6. Open Questions for Phase C Instrumentation

1. **Noise seed usage:** Where is `seed` (noise_seed) consumed? Likely in `poidev` (Poisson noise) calls. Requires further tracing.
2. **Seed initialization timing:** When exactly is `misset_seed` initialized to `seed`? Need to verify sequencing relative to wall-clock time capture.
3. **Thread safety:** Does the C code use OpenMP parallelism? If so, how are seeds protected (thread-local copies vs. critical sections)?
4. **PyTorch LCG bitstream parity:** Does `src/nanobrag_torch/utils/c_random.py` produce **identical** output sequences to `ran1` for the same seed? This must be verified via side-by-side trace.

---

## 7. Artifacts and Next Steps

### 7.1 Artifacts Produced (Phase B3)

All files stored in: `reports/determinism-callchain/phase_b3/20251011T051737Z/`

- `grep_misset_seed.txt` — 7 matches (lines 375, 570, 579, 1127, 1129, 1368, 2083)
- `grep_mosaic_seed.txt` — 4 matches (lines 374, 1123, 1125, 1367, 2689)
- `c_rng_excerpt.c` — 105 lines (ran1 full implementation + mosaic_rotation_umat)
- `c_seed_flow.md` — This document (callchain summary)

### 7.2 Phase B3 Exit Criteria

✅ **COMPLETE:**
- [x] Documented RNG algorithm (Minimal Standard LCG + Bays-Durham shuffle)
- [x] Identified seed entry points (CLI flags → `misset_seed`, `mosaic_seed`)
- [x] Traced seed propagation (pointer side effects via `&seed` arguments)
- [x] Documented RNG invocation sites (misset: line 2083, mosaic: line 2689)
- [x] Captured excerpts (ran1 + mosaic_rotation_umat source code)

### 7.3 Next Steps (Phase C — Dynamic Taps)

**Blocked by:** TorchDynamo device query crash (AT-PARALLEL-013 test suite aborts before reaching seed-dependent code)

**Mitigation Options:**
1. Disable TorchDynamo for determinism tests (`TORCHDYNAMO_DISABLE=1`)
2. Force CPU-only execution (`CUDA_VISIBLE_DEVICES=''`)
3. Patch `torch/_dynamo/device_interface.py` to handle `device_count==0` gracefully

**Post-Mitigation Actions:**
1. Instrument `Simulator.run()` to log mosaic seed state before/after `_generate_mosaic_rotations`
2. Add tap points in `mosaic_rotation_umat` (PyTorch side) to log `r1, r2, r3` values
3. Generate parallel C trace with identical parameters and compare random values
4. Verify PyTorch LCG (`c_random.py`) produces bitwise-identical output to C `ran1`

---

## 8. References

- **Spec:** `specs/spec-a-core.md` §5.3 (RNG determinism requirements)
- **Plan:** `plans/active/determinism.md` (Phase B3 tasks)
- **C Source:** `golden_suite_generator/nanoBragg.c` (lines cited throughout)
- **PyTorch RNG:** `src/nanobrag_torch/utils/c_random.py` (LCG implementation)
- **Architecture:** `arch.md` ADR-05 (Deterministic Sampling & Seeds)
- **Prior Work:** `reports/determinism-callchain/callchain/static.md` (PyTorch-side static callchain from Attempt #4)

---

**Authored by:** ralph (evidence-only loop)
**Timestamp:** 2025-10-11T05:17:37Z
**Commit:** Pending (Phase B3 complete, ready for ledger update)
