# nanoBragg C Architecture Overview

## 1. Introduction

This document provides a high-level architectural overview of the `nanoBragg.c` codebase. It is intended for developers tasked with understanding, maintaining, or translating the logic to a new framework (e.g., PyTorch). It aims to explain the program's structure, data flow, and core computational model without delving into line-by-line implementation details.

The entire application is contained within a single monolithic C file, `nanoBragg.c`. It is a procedural program where the `main` function orchestrates all operations from start to finish.

## 2. Core Philosophy

The design of `nanoBragg` is guided by principles common in high-performance scientific C code:

*   **Forward Model:** The code directly simulates the physics of diffraction. It starts with a source (beam), interacts with a sample (crystal), and calculates the result at a sensor (detector).
*   **Procedural Execution:** Logic flows sequentially from top to bottom within the `main` function. There is no object-oriented abstraction; state is managed through a large number of local variables in `main`.
*   **In-Place Modification:** Functions frequently use pointers to modify data in-place rather than returning new structures. This is a memory-efficient C idiom. For example, vector math functions take an output pointer (`newv`) as an argument.
*   **Explicit Integration:** The simulation calculates a final intensity by explicitly looping over every contributing physical factor (e.g., every source point, every mosaic domain, every sub-pixel) and summing the results. This "brute-force" integration is the primary target for vectorization in a framework like PyTorch.

## 3. Execution Flow

The program executes in three distinct phases, all orchestrated within the `main` function.

```mermaid
graph TD
    A[Start] --> B{Phase 1: Config & Setup};
    B --> C{Phase 2: Main Simulation Loop};
    C --> D{Phase 3: Post-Processing & Output};
    D --> E[End];

    subgraph Phase 1: Config & Setup
        B1[Parse Command-Line Arguments] --> B2;
        B2[Read Input Files: .mat, .hkl, .img] --> B3;
        B3[Initialize Parameters: Beam, Detector, Crystal] --> B4;
        B4[Calculate Derived Geometry: Detector & Crystal Vectors];
    end

    subgraph Phase 2: Main Simulation Loop
        C1[Loop over Detector Pixels (spixel, fpixel)] --> C2;
        C2[Loop over Sub-Pixels (oversample)] --> C3;
        C3[Loop over Detector Thickness Layers] --> C4;
        C4[Loop over Sources (divergence, dispersion)] --> C5;
        C5[Loop over Phi Steps (oscillation)] --> C6;
        C6[Loop over Mosaic Domains] --> C7{Calculate Intensity Contribution};
        C7 --> C8[Accumulate Intensity into `floatimage` buffer];
        C6 -.-> C8
    end

    subgraph Phase 3: Post-Processing & Output
        D1[Apply Final Scaling to `floatimage`] --> D2;
        D2{Add Poisson Noise (optional)} --> D3;
        D3[Write Output Files: .bin, .img, .pgm];
    end
```

## 4. Key Data Structures

State is managed by a large set of variables within `main`. The most critical ones are:

| Variable Name | C Type | Role & Description |
| :--- | :--- | :--- |
| `floatimage` | `float*` | **The Main Output Buffer.** A 1D array of size `fpixels * spixels` that accumulates the calculated photon intensity for each pixel before any noise or scaling is applied. |
| `Fhkl` | `double***` | **Structure Factor Lookup Table.** A 3D array implemented with nested pointers (`h -> k -> l`) that stores the structure factor `F` for each Miller index. It is indexed relative to `h_min`, `k_min`, `l_min`. |
| `a`, `b`, `c` | `double[4]` | **Real-Space Crystal Vectors.** Store the crystal's unit cell vectors in the lab coordinate system (in meters). The `[0]` element stores the vector's magnitude. |
| `a_star`, `b_star`, `c_star` | `double[4]` | **Reciprocal-Space Crystal Vectors.** Store the reciprocal lattice vectors (in Å⁻¹). The `[0]` element stores the magnitude. These are the primary vectors used for calculating Miller indices. |
| `fdet_vector`, `sdet_vector`, `odet_vector` | `double[4]` | **Detector Basis Vectors.** A set of three orthogonal unit vectors defining the detector's coordinate system: fast axis, slow axis, and the direction normal to the detector plane (outward). |
| `pix0_vector` | `double[4]` | **Detector Origin Vector.** The 3D vector from the crystal's origin to the center of the first pixel (pixel 0,0) on the detector. This, along with the basis vectors, defines the detector's position and orientation in space. |
| `incident`, `diffracted`, `scattering` | `double[4]` | **Per-Step Ray Vectors.** These vectors are calculated inside the innermost loops. `incident` is the incoming beam vector, `diffracted` points from the crystal to the current detector pixel, and `scattering` is their difference, scaled by wavelength. |

## 5. Parallelization Model (OpenMP)

To accelerate the computationally expensive main loop, the code uses the OpenMP library.

*   **Directive:** The parallelization is implemented with a single `#pragma omp parallel for` directive.
*   **Target Loop:** The pragma is applied to the outermost loop over the detector's slow axis (`for(spixel=...;)`). This is a classic domain decomposition strategy where each available CPU core is assigned a block of detector rows to compute independently.
*   **Data Sharing Clauses:**
    *   `private(...)`: Loop counters and per-step calculation variables (`fpixel`, `h`, `k`, `l`, `scattering`, `incident`, etc.) are declared `private`. This ensures each thread gets its own independent copy, preventing race conditions.
    *   `shared(...)`: Read-only configuration data (`Na`, `Nb`, `Nc`, `Fhkl`, detector vectors) and the main output buffer (`floatimage`) are `shared`. Sharing `floatimage` is safe because each thread writes to a unique, non-overlapping section of the array (`spixel*fpixels+fpixel`).
    *   `reduction(+:...)`: Global statistics variables (`sum`, `sumsqr`, `sumn`) are handled with a `reduction` clause. Each thread computes a local sum, and OpenMP safely combines (reduces) these local sums into the global variable after the parallel section is complete.

## 6. External Dependencies

The codebase is self-contained but relies on standard system libraries that must be linked during compilation.

*   **C Standard Library:** `stdio.h`, `stdlib.h`, `string.h`, `math.h`, etc.
*   **Math Library (`libm`):** Required for functions like `sin`, `cos`, `sqrt`, `exp`, `log`. Linked with the `-lm` flag.
*   **OpenMP Library:** Required for the parallel processing directives. Enabled and linked with the `-fopenmp` compiler flag.

## 7. Key Physics & Non-Standard Conventions

**For implementation guidance on these conventions, see [CLAUDE.md](../../CLAUDE.md) and the [Architecture Hub](./README.md).**

### ⚠️ 7.1 CRITICAL: Non-Standard Miller Index Calculation

The `nanoBragg.c` code uses a **non-standard convention** for calculating Miller indices that MUST be replicated exactly:

```c
// nanoBragg.c lines 3547-3549
h = dot_product(scattering,a);
k = dot_product(scattering,b);
l = dot_product(scattering,c);
```

**Non-Standard:** The scattering vector `S = (s_out - s_in) / λ` is dotted with the **real-space lattice vectors (`a,b,c`)**, NOT the reciprocal-space vectors (`a*,b*,c*`) as is standard in crystallography textbooks.

**Why This Matters:** This convention affects all downstream calculations and is the reason CLAUDE.md Rule #2 exists.

### ⚠️ 7.2 CRITICAL: F_latt Calculation Using Fractional Indices

The lattice shape transform (`sincg` function) is applied to the **fractional part of the Miller index**, not the full index:

```c
// nanoBragg.c lines 3555-3557
h0 = ceil(h-0.5);
k0 = ceil(k-0.5);
l0 = ceil(l-0.5);

// Then later (lines 3575-3577):
F_latt = Na*sincg(M_PI*Na*(h-h0), &stol_of_h);
F_latt*= Nb*sincg(M_PI*Nb*(k-k0), &stol_of_k);
F_latt*= Nc*sincg(M_PI*Nc*(l-l0), &stol_of_l);
```

**Critical Detail:** The shape transform uses `(h-h0)`, `(k-k0)`, `(l-l0)` which are the fractional parts (always between -0.5 and 0.5).

**Common Mistake:** Using the full Miller indices `h`, `k`, `l` in the sincg calculation will produce incorrect results.

### 7.3 Structure Factor Lookup Convention

The structure factor is looked up using the **nearest integer** Miller indices:

```c
// nanoBragg.c line 3600
F_cell = Fhkl[h0-h_min][k0-k_min][l0-l_min];
```

Where `h0`, `k0`, `l0` are the nearest integers calculated using `ceil(h-0.5)`.

## 8. Key Conventions and Coordinate Systems

### 8.1 Canonical Lattice Orientation

The C code establishes a canonical orientation for the base reciprocal lattice vectors before any missetting or dynamic rotation is applied. This convention MUST be replicated to match the golden data.

The geometric rules are:
- `a*` is aligned with the laboratory X-axis.
- `b*` lies in the laboratory XY-plane.
- `c*` is placed accordingly to form a right-handed system.

This is implemented in `nanoBragg.c` (lines 1862-1871) with the following logic:

```c
/* construct default orientation */
a_star[1] = a_star[0];
b_star[1] = b_star[0]*cos_gamma_star;
c_star[1] = c_star[0]*cos_beta_star;
a_star[2] = 0.0;
b_star[2] = b_star[0]*sin_gamma_star;
c_star[2] = c_star[0]*(cos_alpha_star-cos_beta_star*cos_gamma_star)/sin_gamma_star;
a_star[3] = 0.0;
b_star[3] = 0.0;
c_star[3] = c_star[0]*V_cell/(a[0]*b[0]*c[0]*sin_gamma_star);
```