# SOURCE-WEIGHT-001 Phase B1 — Spec & C Behavior Analysis

**Date:** 2025-10-09
**Task:** Document authoritative spec evidence and C reference implementation showing that source weights are read but ignored.

## Spec Evidence

### Primary Normative Statement

From `specs/spec-a-core.md` lines 150-151:

> **Sources from file:**
>    - Each line: X, Y, Z (position vector in meters), weight (dimensionless), λ (meters). Missing
> fields default to:
>        - Position along −source_distance·b (source_distance default 10 m).
>        - Weight = 1.0.
>        - λ = λ0.
>    - Positions are normalized to unit direction vectors (X,Y,Z overwrites become unit direction).
> **The weight column is read but ignored (equal weighting results).**

**Normative interpretation:** This single statement is authoritative. The spec explicitly mandates that:
1. The weight column SHALL be read from source files (parsed and stored)
2. The weight column SHALL be ignored during intensity accumulation
3. Equal weighting SHALL result regardless of user-provided weight values

### Supporting Context: Sampling & Accumulation

From `specs/spec-a-core.md` lines 99-100 (Final per-pixel scaling):

> Define steps = (number of sources) · (number of mosaic domains) · (phisteps) · (oversample^2).

**Key observation:** The `steps` normalization divides by the **count** of sources, not the sum of weights. This ensures equal weighting semantically.

From lines 88-91 (Intensity accumulation additive term):

> I_term = (F_cell^2)·(F_latt^2).
> Accumulator I (per pixel) starts at I_bg (background, see below) and adds I_term for every inner-loop combination.

**Key observation:** No mention of multiplying `I_term` by source weights during accumulation. All sources contribute equally.

## C Reference Implementation Evidence

### Source Weight Reading (`nanoBragg.c:2570-2593`)

```c
sources = read_text_file(sourcefilename,5,&source_X,&source_Y,&source_Z,&source_I,&source_lambda);
if(sources == 0) {
    perror("reading source definition file");
    exit(9);
}
/* apply defaults to missing values */
for(source=0;source<sources;++source){
    if(isnan(source_X[source])) {
        source_X[source] = -source_distance*beam_vector[1];
    }
    if(isnan(source_Y[source])) {
        source_Y[source] = -source_distance*beam_vector[2];
    }
    if(isnan(source_Z[source])) {
        source_Z[source] = -source_distance*beam_vector[3];
    }
    if(isnan(source_I[source])) {
        source_I[source] = 1.0;    // ← Default weight = 1.0
    }
    if(isnan(source_lambda[source])) {
        source_lambda[source] = lambda0;
    }
}
```

**Observation:** The C code reads the weight column into `source_I` array and applies a default of `1.0` when missing. This demonstrates the "read" part of the spec requirement.

### Weight Usage in Accumulation (`nanoBragg.c:2666-2682`)

```c
printf("  created a total of %d sources:\n",sources);
for(source=0;source<sources;++source){
    /* retrieve stuff from cache */
    X = vector[1] = source_X[source];
    Y = vector[2] = source_Y[source];
    Z = vector[3] = source_Z[source];
    I = source_I[source];              // ← Weight retrieved
    lambda = source_lambda[source];

    /* make sure these are unit vectors */
    unitize(vector,vector);
    source_X[source] = vector[1];
    source_Y[source] = vector[2];
    source_Z[source] = vector[3];

    printf("%g %g %g   %g %g\n",X,Y,Z,I,lambda);  // ← Logged for diagnostics
}
```

**Observation:** The weight `I` is retrieved from cache and printed for user visibility, but never used in subsequent calculations.

### Steps Normalization (`nanoBragg.c:2710`)

```c
steps = sources*mosaic_domains*phisteps*oversample*oversample;
```

**Critical observation:** The `steps` calculation multiplies by `sources` (the count), NOT by any weight sum. This is the concrete implementation of the spec's "equal weighting" requirement.

### Search for Weight Usage

A comprehensive search through the C accumulation loop (lines 2710–3278, the main rendering loop) reveals:
- `source_I` array is never dereferenced during intensity accumulation
- No multiplication by weight factors in the inner physics loop
- All sources contribute identically, normalized only by `steps` division

## Conclusion

**Primary finding:** Both the normative spec and the C reference implementation agree perfectly:
1. Source weights ARE read from files (or defaulted to 1.0)
2. Source weights are NOT used during intensity calculations
3. Final normalization divides by source **count**, ensuring equal weighting

**Implication for PyTorch implementation:** The current PyTorch code that multiplies intensity contributions by `source_weights` (`simulator.py:400-420`) violates this spec requirement and creates a C↔Py divergence.

**Exit criterion for Phase B1:** ✅ Complete. Spec citation and C code evidence documented with line anchors.
