# nanoBragg C Function Reference

## 1. Introduction

This document provides a detailed reference for every function defined in `nanoBragg.c`. Its purpose is to serve as a quick lookup guide for developers translating or maintaining the code.

Each function entry includes:
*   **Signature:** The C function declaration.
*   **Description:** A plain-language summary of what the function does.
*   **Purity Analysis:** Whether the function is pure or has side effects.
*   **Arguments:** A detailed breakdown of each input and output parameter.
*   **Return Value:** The meaning of the value returned by the function.
*   **Dependencies:** A list of other custom functions it calls.

**A Note on C Idioms:** This codebase frequently uses pointers as "output parameters." This means instead of returning a value, a function will write its result into a memory location provided by the caller. This is documented explicitly for each function.

## 2. Function Reference by Category

### 2.1 Main Application Logic

#### `main`
*   **Signature:** `int main(int argc, char** argv)`
*   **Description:** The main entry point and orchestrator of the entire program. It is not a reusable function. Its logic is divided into three phases:
    1.  **Configuration & Setup:** Parses command-line arguments, reads input files, and initializes all simulation parameters and geometry.
    2.  **Main Simulation Loop:** Executes the nested loops over pixels, sources, mosaic domains, etc., to calculate the diffraction pattern. This section is parallelized with OpenMP.
    3.  **Post-Processing & Output:** Takes the raw `floatimage` buffer, adds noise (optional), scales the data, and writes the final images to disk.
*   **Purity Analysis:** Has Side Effects.
*   **Arguments:** Standard command-line arguments.
*   **Return Value:** `int`: `0` on successful completion, non-zero on error.

### 2.2 File I/O and Parsing

#### `read_text_file`
*   **Signature:** `size_t read_text_file(char *filename, size_t nargs, ... )`
*   **Description:** A generic utility to read a multi-column text file into a series of dynamically allocated double arrays.
*   **Purity Analysis:** Has Side Effects.
*   **Arguments:**
    *   `char *filename`: **Input.** Path to the text file to read.
    *   `size_t nargs`: **Input.** The number of columns to read (and the number of subsequent pointer arguments).
    *   `...`: **Output.** A variadic list of `double**` arguments. The function allocates memory for each array and modifies the pointers to point to the new data.
*   **Return Value:** `size_t`: The number of lines read from the file.

#### `GetFrame`
*   **Signature:** `SMVinfo GetFrame(char *filename)`
*   **Description:** Reads an SMV-formatted image file, parsing its header and making its pixel data available.
*   **Purity Analysis:** Has Side Effects.
*   **Arguments:**
    *   `char *filename`: **Input.** Path to the SMV file.
*   **Return Value:** `SMVinfo`: A struct containing the parsed header info, file handle, and a pointer to the memory-mapped image data.

#### `ValueOf`
*   **Signature:** `double ValueOf(const char *keyword, SMVinfo smvfile)`
*   **Description:** Parses an SMV header string to find the floating-point value associated with a given keyword.
*   **Purity Analysis:** Pure Function.
*   **Arguments:**
    *   `const char *keyword`: **Input.** The header keyword to search for (e.g., `"DISTANCE"`).
    *   `SMVinfo smvfile`: **Input.** The SMV info struct containing the header text.
*   **Return Value:** `double`: The parsed value, or `NAN` if not found.

### 2.3 Vector & Geometry Math

**Convention:** All vector arguments are pointers to a `double[4]` array where `[1]`, `[2]`, `[3]` are the x,y,z components. The `[0]` element is often used to store the vector's magnitude as a side effect.

#### `rotate`
*   **Signature:** `double *rotate(double *v, double *newv, double phix, double phiy, double phiz)`
*   **Description:** Rotates vector `v` by applying successive rotations around the X, Y, and Z axes.
*   **Purity Analysis:** Has Side Effects.
*   **Arguments:**
    *   `double *v`: **Input.** The source vector to rotate.
    *   `double *newv`: **Output.** The destination vector where the result is stored.
    *   `double phix, phiy, phiz`: **Input.** Rotation angles in radians.
*   **Return Value:** `double*`: The pointer `newv`.

#### `rotate_axis`
*   **Signature:** `double *rotate_axis(double *v, double *newv, double *axis, double phi)`
*   **Description:** Rotates vector `v` around an arbitrary `axis` vector by angle `phi` using Rodrigues' rotation formula.
*   **Purity Analysis:** Has Side Effects.
*   **Arguments:**
    *   `double *v`: **Input.** The source vector.
    *   `double *newv`: **Output.** The destination vector.
    *   `double *axis`: **Input.** The unit vector defining the axis of rotation.
    *   `double phi`: **Input.** The rotation angle in radians.
*   **Return Value:** `double*`: The pointer `newv`.

#### `cross_product`
*   **Signature:** `double *cross_product(double *x, double *y, double *z)`
*   **Description:** Calculates the cross product of vectors `x` and `y`.
*   **Purity Analysis:** Has Side Effects.
*   **Arguments:**
    *   `double *x`, `*y`: **Input.** The two source vectors.
    *   `double *z`: **Output.** The destination vector for the result.
*   **Return Value:** `double*`: The pointer `z`.

#### `dot_product`
*   **Signature:** `double dot_product(double *x, double *y)`
*   **Description:** Calculates the dot product of vectors `x` and `y`.
*   **Purity Analysis:** Pure Function.
*   **Arguments:** `double *x`, `*y`: **Input.** The two source vectors.
*   **Return Value:** `double`: The scalar result of the dot product.

#### `magnitude`
*   **Signature:** `double magnitude(double *vector)`
*   **Description:** Calculates the magnitude of a vector.
*   **Purity Analysis:** Has Side Effects.
*   **Arguments:**
    *   `double *vector`: **Input/Output.** The source vector. The function writes the calculated magnitude into `vector[0]`.
*   **Return Value:** `double`: The calculated magnitude.

#### `unitize`
*   **Signature:** `double unitize(double *vector, double *new_unit_vector)`
*   **Description:** Normalizes `vector` to a unit vector.
*   **Purity Analysis:** Has Side Effects.
*   **Arguments:**
    *   `double *vector`: **Input.** The source vector.
    *   `double *new_unit_vector`: **Output.** The destination for the resulting unit vector.
*   **Return Value:** `double`: The original magnitude of the vector before normalization.
*   **Dependencies:** `magnitude()`

### 2.4 Physics & Shape Models

#### `sincg`
*   **Signature:** `double sincg(double x, double N)`
*   **Description:** Calculates the Fourier transform of a 1D grating of `N` elements. Used for the parallelepiped crystal shape model.
*   **Purity Analysis:** Pure Function.

#### `sinc3`
*   **Signature:** `double sinc3(double x)`
*   **Description:** Calculates the 3D Fourier transform of a sphere. Used for the spherical crystal shape model.
*   **Purity Analysis:** Pure Function.

#### `polarization_factor`
*   **Signature:** `double polarization_factor(double kahn_factor, double *incident, double *diffracted, double *axis)`
*   **Description:** Calculates the polarization correction factor for a given scattering geometry.
*   **Purity Analysis:** Has Side Effects.
*   **Arguments:**
    *   `double kahn_factor`: **Input.** The polarization factor (0 to 1).
    *   `double *incident`, `*diffracted`, `*axis`: **Input/Output.** These vectors are normalized in-place by the `unitize` helper function.
*   **Return Value:** `double`: The polarization correction factor (typically between 0.5 and 1.0).
*   **Dependencies:** `unitize()`, `dot_product()`, `cross_product()`.

### 2.5 Random Number Generation

**Convention:** All random number generators take a pointer to a seed, `long *idum`, and modify its value as a side effect to maintain the state of the generator.

#### 2.5.1 RNG Algorithm Overview

The nanoBragg C implementation uses a **Minimal Standard Linear Congruential Generator (LCG)** enhanced with a **Bays-Durham shuffle** for improved randomness properties. This combination provides a deterministic, reproducible pseudo-random number stream suitable for scientific simulations.

**Algorithm Details:**
- **Core LCG:** Park & Miller (1988) "Minimal Standard" generator
  - Multiplier: `IA = 16807`
  - Modulus: `IM = 2147483647` (2³¹ − 1, a Mersenne prime)
  - Period: ~2.1 billion values
- **Enhancement:** 32-element Bays-Durham shuffle table (`NTAB = 32`)
- **Implementation:** `ran1()` function (lines 4143-4185 in `nanoBragg.c`)
- **Output Range:** `[1.2e-7, 1.0-1.2e-7]` — excludes exact 0.0 and 1.0 to prevent singularities in downstream calculations

#### 2.5.2 Seed Domains and Defaults

The C implementation maintains three independent seed domains to ensure statistical independence between noise generation, crystal mosaicity, and static misorientation:

| Seed Variable | Default Value | CLI Override | Purpose |
|---------------|---------------|--------------|---------|
| `seed` (noise_seed) | `-time(NULL)` (negative wall-clock) | `-seed <val>` | Poisson noise generation for detector readout |
| `mosaic_seed` | `-12345678` | `-mosaic_seed <val>` | Mosaic domain rotation generation (per-domain variability) |
| `misset_seed` | `seed` (inherits noise_seed) | `-misset_seed <val>` | Static crystal misorientation (single application) |

**Spec Reference:** `specs/spec-a-core.md` §5.3 (RNG determinism requirements)

#### 2.5.3 Pointer Side-Effect Contract (CRITICAL)

> **⚠️ CRITICAL: Pointer-Based Seed Mutation**
>
> The C implementation uses **pointer side effects** to advance seed state. This is a non-obvious but essential aspect of the RNG contract:
>
> ```c
> double ran1(long *idum)  // ← Pointer allows in-place mutation
> {
>     // ... LCG computation ...
>     *idum = new_state;  // ← Mutates caller's seed variable
>     return random_value;
> }
> ```
>
> Each call to `ran1(&seed)` mutates `seed` in-place, advancing the LCG chain by one step. Functions that consume multiple random values (e.g., `mosaic_rotation_umat`) advance the seed multiple times per invocation.
>
> **Example:** `mosaic_rotation_umat(umat, &mosaic_seed)` consumes **3 random values** internally:
> 1. Axis direction angle
> 2. Axis Z-component
> 3. Rotation magnitude scaling
>
> This means `mosaic_seed` advances **3 steps** per call.
>
> **PyTorch Parity Requirement:**
> The PyTorch implementation MUST replicate this deterministic state progression. The `LCGRandom` class in `src/nanobrag_torch/utils/c_random.py` wraps seed state and exposes a `.uniform()` method to advance state identically to C's `ran1(&seed)`.

#### 2.5.4 Invocation Sites

The following table documents where RNG functions are called in the C code and their seed consumption patterns:

| Function | Invocation Site | Seed Parameter | RNG Calls per Invocation | Purpose |
|----------|----------------|----------------|--------------------------|---------|
| `mosaic_rotation_umat` | Line 2083 (misset) | `&misset_seed` | 3 | Static crystal misorientation (applied once per simulation) |
| `mosaic_rotation_umat` | Line 2689 (mosaic loop) | `&mosaic_seed` | 3 × `mosaic_domains` | Mosaic domain rotations (loop over domains) |
| `poidev` | Multiple sites | `&seed` | Variable | Poisson noise generation for detector output |

**Total RNG Consumption Example:**
- Configuration: 10 mosaic domains
- Mosaic RNG calls: 3 calls/domain × 10 domains = 30 calls to `ran1(&mosaic_seed)`
- Final seed state: Initial `mosaic_seed` advanced 30 steps

#### `ran1`, `poidev`, `gaussdev`, `lorentzdev`, `triangledev`, `expdev`
*   **Description:** These functions return random deviates from uniform, Poisson, Gaussian, Lorentzian, triangular, and exponential distributions, respectively. All are stateful and not pure.

#### `mosaic_rotation_umat`
*   **Signature:** `double *mosaic_rotation_umat(float mosaicity, double umat[9], long *idum)`
*   **Description:** Generates a random 3x3 unitary rotation matrix representing a single mosaic domain. Consumes **3 random values** from the RNG per invocation (see §2.5.3 for details).
*   **Purity Analysis:** Has Side Effects (mutates `*idum` seed state via 3 calls to `ran1`).

### 2.6 Interpolation

#### `polint`, `polin2`, `polin3`
*   **Signatures:** `void func_name(..., double *y)`
*   **Description:** Perform 1D, 2D, and 3D polynomial (cubic) interpolation.
*   **Purity Analysis:** Has Side Effects (writes result to output pointer `*y`).

---

## Appendix: Triage of C Helper Functions for PyTorch Port

The following table provides a comprehensive triage of all helper functions found in the original C codebase. This serves as the definitive guide for the porting effort.

| Function Name | Status | Rationale / PyTorch Equivalent |
| :--- | :--- | :--- |
| **Vector & Geometry Math** | | |
| `rotate`, `rotate_axis`, `rotate_umat` | **PORT** | Core geometry logic. To be vectorized in `utils/geometry.py`. |
| `cross_product`, `dot_product` | **PORT** | Core geometry logic. To be vectorized in `utils/geometry.py`. |
| `magnitude`, `unitize`, `vector_scale` | **PORT** | Core geometry logic. To be vectorized in `utils/geometry.py`. |
| `vector_rescale`, `vector_diff` | **PORT** | Core geometry logic. To be vectorized in `utils/geometry.py`. |
| `umat2misset` | **PORT** | Useful debugging and geometry utility. |
| **Physics & Shape Models** | | |
| `sincg`, `sinc3`, `sinc_conv_sinc3` | **PORT** | Core physics models for crystal shape factors. To be implemented in `utils/physics.py`. |
| `polarization_factor` | **PORT** | Core physics model. To be vectorized in `utils/physics.py`. |
| `ngauss2D`, `ngauss2D_pixel` | **PORT** | Core PSF logic. To be implemented in a `psf.py` module. |
| `apply_psf` | **REFACTOR & PORT** | The core convolution logic will be ported, but memory management will be redesigned. |
| **Random Number Generation** | | |
| `ran1`, `gammln` | **REPLACE** | Internal components of the C RNGs. Not needed. |
| `poidev`, `gaussdev`, `lorentzdev` | **REPLACE** | Use `torch.poisson`, `torch.randn`, and `torch.distributions.Cauchy`. |
| `mosaic_rotation_umat` | **PORT** | Core logic for mosaic simulation. To be implemented in `utils/physics.py`. |
| **File I/O and Parsing** | | |
| `read_text_file` | **REPLACE** | Use `numpy.loadtxt` or `pandas.read_csv`. |
| `GetFrame`, `ValueOf` | **REPLACE** | Use the `fabio` library (`fabio.open()`). |
| **Interpolation & Statistics** | | |
| `polint`, `polin2`, `polin3` | **REPLACE** | Use `torch.nn.functional.grid_sample`. |
| `fmedian`, `fmean_with_rejection` | **REPLACE** | Use `torch.median` and boolean mask indexing. |