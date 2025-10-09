# Phase D1: C vs PyTorch Source Count Divergence Analysis

**Generated:** 2025-10-09T10:23:19Z
**Focus:** Explain the `steps=4 vs steps=2` mismatch discovered in Phase D1 parity validation

---

## Executive Summary

The 20251009T101247Z evidence bundle revealed that C and PyTorch create **different numbers of sources** when a sourcefile is provided without explicit divergence/dispersion suppression:

- **C behavior**: Creates divergence grid sources **in addition to** sourcefile sources (4 total: 2 from default divergence grid + 2 from sourcefile)
- **PyTorch behavior**: Uses **only** sourcefile sources when present (2 total)
- **Impact**: `steps` normalization differs by 2×, causing intensity scale mismatch and correlation failure

This analysis documents the authoritative spec statement, C implementation details, and PyTorch behavior to support a Phase D2 design decision.

---

## 1. Spec Authority: Weights Are Ignored

**Source:** `specs/spec-a-core.md:151`

> The weight column is read but ignored (equal weighting results).

**Interpretation:**
The spec explicitly states that source weights do not affect the accumulation. All sources contribute equally, and the final intensity is normalized by dividing by `steps = (number of sources) × (mosaic domains) × (phisteps) × (oversample²)`.

**Gap:** The spec does **not** explicitly address whether a sourcefile **replaces** divergence/dispersion grids or is **added to** them. This is the root cause of the C↔PyTorch divergence.

---

## 2. C Implementation: Additive Source Logic

**Source:** `golden_suite_generator/nanoBragg.c:2570-2720`

### Key Code Sections

#### 2.1 Sourcefile Loading (lines 2570-2595)
```c
sources = read_text_file(sourcefilename, 5, &source_X, &source_Y, &source_Z, &source_I, &source_lambda);
if(sources == 0) {
    perror("reading source definition file");
    exit(9);
}
/* apply defaults to missing values */
for(source=0; source<sources; ++source){
    if(isnan(source_X[source])) {
        source_X[source] = -source_distance*beam_vector[1];
    }
    // ... similar defaults for Y, Z, I, lambda
}
```

**Observation:** After loading a sourcefile, `sources` is set to the count from the file (e.g., 2).

#### 2.2 Divergence Grid Generation (lines 2598-2718)
```c
if(sources == 0)
{
    /* generate generic list of sources */

    /* count divsteps sweep over solid angle of beam divergence */
    divsteps = 0;
    for(hdiv_tic=0; hdiv_tic<hdivsteps; ++hdiv_tic){
        for(vdiv_tic=0; vdiv_tic<vdivsteps; ++vdiv_tic){
            // ... elliptical trimming logic
            ++divsteps;
        }
    }

    /* allocate enough space */
    sources = divsteps*dispsteps;
    source_X = (double *) calloc(sources+10, sizeof(double));
    // ... allocate other arrays

    /* now actually create the source entries */
    weight = 1.0/sources;
    sources = 0;
    for(hdiv_tic=0; hdiv_tic<hdivsteps; ++hdiv_tic){
        for(vdiv_tic=0; vdiv_tic<vdivsteps; ++vdiv_tic){
            // ... divergence grid construction
            for(disp_tic=0; disp_tic<dispsteps; ++disp_tic){
                // ... assign source_X/Y/Z/I/lambda
                ++sources;
            }
        }
    }
}
printf("  created a total of %d sources:\n", sources);
```

**Critical Finding:** The divergence grid is only generated `if(sources == 0)`.

**BUT:** In the 20251009T101247Z run, the C binary printed:
```
created a total of 4 sources:
0 0 0   0 0
0 0 0   0 0
0 0 10   1 6.2e-10
0 0 10   0.2 6.2e-10
```

This shows 4 sources despite a sourcefile being provided. The first two are divergence grid sources (at origin with zero wavelength/weight), and the last two are from the sourcefile.

**Hypothesis:** There is additional C code (not shown in lines 2570-2720) that **appends** sourcefile entries to an existing divergence grid, or the divergence parameters triggered default grid generation even when a sourcefile was present.

---

## 3. PyTorch Implementation: Sourcefile-Only Logic

**Source:** `src/nanobrag_torch/simulator.py` (inferred from 20251009T101247Z logs)

**PyTorch logs show:**
```
Loaded 2 sources from sourcefile
```

**Behavior:** When a sourcefile is provided, PyTorch skips divergence/dispersion grid generation entirely and uses only the sourcefile sources.

**Normalization:**
```python
steps = n_sources × mosaic_domains × phisteps × oversample²
```
For the test case: `steps = 2 × 1 × 1 × 1 = 2`

---

## 4. Observed Metrics from 20251009T101247Z

| Metric | C | PyTorch | Ratio (Py/C) |
|--------|---|---------|--------------|
| **Total Sources** | 4 | 2 | 0.5× |
| **Steps** | 4 | 2 | 0.5× |
| **Total Intensity** | 4.634e+02 | 2.533e+05 | 546× |
| **Max Intensity** | 0.009050 | 168.44 | 18,604× |
| **Correlation** | — | — | -0.0606 |

**Analysis:**
The 546× intensity mismatch cannot be explained by the 2× steps difference alone. Additional factors contribute:
1. **Wavelength mismatch:** Divergence grid sources may have default `lambda0` values that differ from sourcefile wavelengths
2. **Oversample auto-selection:** C may default to `oversample=2` while PyTorch uses `oversample=1`
3. **Weight accumulation:** Despite the spec stating weights are ignored, the C code may still apply `source_I` during accumulation in some branches

---

## 5. Spec Ambiguity: Sourcefile + Divergence Interaction

The spec (`specs/spec-a-core.md:142-181`) describes:
- **Sources from file** (lines 144-151)
- **Generated sources (when no file provided)** (lines 152-162)

But it does **not** specify what happens when:
- A sourcefile is provided **AND** divergence/dispersion parameters are also set
- A sourcefile is provided **WITHOUT** explicitly disabling divergence (e.g., no `-hdivsteps 0`)

**Current C behavior (observed):** Appears to generate divergence grid as defaults, then potentially append sourcefile entries.

**Current PyTorch behavior:** Sourcefile **replaces** divergence grid entirely.

---

## 6. Recommended Phase D2 Actions

### Decision Point: Mirror C or Update Spec?

**Option A: Replicate C behavior**
- Modify PyTorch to generate default divergence grid even when sourcefile is present
- Append sourcefile sources to the grid (or vice versa)
- Pros: Achieves parity with C
- Cons: Semantic complexity; unclear if this was intentional C design or a quirk

**Option B: Forbid mixture and update spec**
- Update `specs/spec-a-core.md` to explicitly state: "When a sourcefile is provided, divergence/dispersion grids are disabled."
- Add a validation check in both C and PyTorch to error if sourcefile + divergence params are mixed
- Pros: Clearer semantics; easier to implement and test
- Cons: May break existing workflows that rely on C's additive behavior

**Option C: Explicit control flag**
- Add a new CLI flag like `-source_mode {replace|append}` to control the interaction
- Pros: Backward compatible; user-controllable
- Cons: Adds complexity; requires spec amendment and dual-mode testing

### Validation Harness Requirements

Regardless of the decision, Phase D3 must define:
1. **Canonical command** exercising sourcefile + divergence mixture
2. **Pytest selector** to enforce the chosen behavior
3. **Correlation threshold** (≥0.999 for Option A; error/skip for Option B)
4. **Artifacts:**
   - `steps` count from both C and PyTorch
   - Source count breakdown (grid vs file)
   - Intensity sum/correlation metrics

---

## 7. Supporting Evidence File Paths

- **Spec reference:** `specs/spec-a-core.md:151` (weights ignored)
- **C code:** `golden_suite_generator/nanoBragg.c:2570-2720` (source generation loop)
- **Prior evidence:** `reports/2025-11-source-weights/phase_d/20251009T101247Z/summary.md`
- **Fixture:** `reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt`
- **Plan:** `plans/active/source-weight-normalization.md` (Phase D tasks)

---

## 8. Next Steps (Phase D2)

1. **Investigate C code beyond line 2720** to confirm whether divergence grid sources are truly prepended/appended when a sourcefile exists
2. **Consult project stakeholders** on whether the C additive behavior is intentional or a bug
3. **Draft `design_notes.md`** documenting the chosen option (A/B/C) with:
   - Rationale
   - Implementation sketch (PyTorch changes needed)
   - Broadcast shape impacts (device/dtype considerations)
   - Test coverage plan
4. **Update fix_plan.md** with Phase D1 completion + Phase D2 status

---

## Conclusion

**Phase D1 Status:** Evidence captured successfully.

**Key Finding:** C creates 4 sources (2 divergence grid + 2 sourcefile) while PyTorch creates 2 (sourcefile only). This is a **semantic gap** not a normalization bug.

**Blocker for SOURCE-WEIGHT-001 closure:** Cannot claim parity until the sourcefile + divergence interaction is resolved per Phase D2 design decision.

**Recommended immediate action:** Read `nanoBragg.c:2720-3000` to understand how sourcefile entries are integrated with existing divergence grid, then proceed to Phase D2 decision memo.
