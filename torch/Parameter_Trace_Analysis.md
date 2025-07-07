# nanoBragg PyTorch Parameter Trace Analysis

**Version:** 1.0  
**Date:** 2023-10-27  
**Authors:** [Your Name/Team]

## 1. Introduction

This document provides a detailed, end-to-end analysis of how key physical parameters influence the final simulated diffraction pattern in the PyTorch implementation of `nanoBragg`. For each parameter, we trace its path through the computational graph, from its initial value to its effect on the final image intensity.

The purpose of this document is to:
1.  **Build Intuition:** Explain *why* a parameter affects the simulation in a certain way.
2.  **Guide Debugging:** Provide a roadmap for tracing unexpected behavior back to its source.
3.  **Interpret Gradients:** Offer a physical interpretation of what a calculated gradient means during an optimization or refinement task.
4.  **Onboard Developers:** Serve as a deep dive into the "cause and effect" relationships within the simulation model.

Each section follows a standard format:
*   **Parameter:** The name of the physical parameter.
*   **Forward Pass Trace:** A step-by-step description of the data flow during the simulation.
*   **Backward Pass (Gradient) Trace:** A conceptual description of how the gradient flows back to the parameter via the chain rule.
*   **Physical Intuition of the Gradient:** A plain-language explanation of what the gradient tells us.

## 2. Crystal Parameters

### 2.1 Mosaicity (`mosaic_spread_rad`)

*   **Forward Pass Trace:**
    1.  The scalar `mosaic_spread_rad` parameter scales a set of pre-defined, deterministic rotation angles.
    2.  These angles, along with a set of base axes, are converted into a tensor of `mosaic_umats` (3x3 rotation matrices) using a differentiable axis-angle-to-matrix conversion.
    3.  Each `mosaic_umat` is applied to the crystal's reciprocal vectors (`a_star`, etc.) after the main `phi` spindle rotation.
    4.  This results in a distribution of slightly different crystal orientations for each simulation step.
    5.  Each unique orientation produces slightly different fractional Miller indices (`h,k,l`) when dotted with a given scattering vector.
    6.  This cloud of `h,k,l` values is sampled by the lattice transform function (`F_latt`, e.g., `sincg`), effectively "smearing" or "blurring" what would otherwise be a sharp Bragg peak.
    7.  The final image intensity is the sum of contributions from all mosaic domains, resulting in broader, more diffuse spots as `mosaic_spread_rad` increases.
*   **Backward Pass (Gradient) Trace:**
    1.  The gradient flows from the `loss` back through the `sum` operation to the intensity contribution of each mosaic domain (`I_contrib`).
    2.  From `I_contrib`, it flows to the lattice transform `F_latt`.
    3.  The gradient of `F_latt` with respect to `h,k,l` is largest on the steep flanks of the Bragg peak.
    4.  This gradient flows back to the rotated reciprocal vectors, then through the `matmul` operation to the `mosaic_umats`.
    5.  Finally, it flows through the differentiable axis-angle-to-matrix conversion back to the `mosaic_spread_rad` scalar.
*   **Physical Intuition of the Gradient:** The gradient `dL/d(mosaic_spread_rad)` indicates how the loss would change with an infinitesimal increase in mosaic spread. If the simulated peaks are too sharp compared to the data, the loss is high on the peak flanks. The gradient will be negative, signaling the optimizer to **increase** the mosaicity to better match the broader experimental spots.

### 2.2 Unit Cell Length (`cell_a`)

*   **Forward Pass Trace:**
    1.  `cell_a` is a direct input to the formulas that calculate the base reciprocal lattice vectors. Specifically, a larger `cell_a` results in a smaller `a_star` magnitude (since `a_star` is proportional to `1/a`).
    2.  The `a_star` vector is used in the dot product `h = dot(scattering_vector, rot_a_star)`.
    3.  Therefore, changing `cell_a` inversely scales the calculated `h` values.
    4.  This shifts the entire grid of Bragg peaks in reciprocal space. On the detector, this corresponds to a radial scaling of the spot positions (d-spacing).
*   **Backward Pass (Gradient) Trace:**
    1.  The gradient flows from the `loss` back to `h,k,l`.
    2.  The gradient `dL/dh` flows back through the dot product to `rot_a_star`.
    3.  It then flows back through the rotation operations to the base `a_star` vector.
    4.  Finally, it flows through the derivative of the cell calculation formulas back to the `cell_a` parameter.
*   **Physical Intuition of the Gradient:** If the simulated spots are at the wrong resolution (e.g., all are 1% too close to the center), the gradient `dL/d(cell_a)` will be non-zero. It tells the optimizer whether to **increase or decrease** the unit cell size to make the simulated d-spacings match the experimental data.

### 2.3 Crystal Orientation (`misset_rot_x`)

*   **Forward Pass Trace:**
    1.  `misset_rot_x` is used to construct an initial rotation matrix `U_misset`.
    2.  This matrix is applied to the base reciprocal vectors *before* any other rotations (`phi` or mosaic).
    3.  This applies a global rotation to the entire reciprocal lattice.
    4.  On the detector, this manifests as a rotation of the entire diffraction pattern around a fixed axis.
    5.  This changes the `h,k,l` values for every pixel, altering the loss.
*   **Backward Pass (Gradient) Trace:**
    1.  The gradient flows from the `loss` back to `h,k,l`, then to the fully rotated reciprocal vectors.
    2.  It back-propagates through the mosaic and phi rotations, then through the initial `U_misset` rotation.
    3.  Finally, it flows to the underlying `misset_rot_x` angle.
*   **Physical Intuition of the Gradient:** If the entire simulated pattern is mis-rotated compared to the data, this gradient tells the optimizer **which way and how much** to rotate the crystal model to improve alignment.

## 3. Detector Parameters

### 3.1 Detector Distance (`distance_mm`)

*   **Forward Pass Trace:**
    1.  `distance_mm` directly scales the component of the `pix0_vector` that is normal to the detector plane.
    2.  This changes the 3D coordinates of every pixel, effectively moving the entire detector plane farther from or closer to the sample.
    3.  This changes the `diffracted_vectors` and therefore the `scattering_vectors`.
    4.  The effect is a change in the "magnification" of the pattern. A larger distance spreads the spots farther apart.
    5.  It also affects the solid angle correction (`omega_pixel`), which scales as `1/distance^2`.
*   **Backward Pass (Gradient) Trace:**
    1.  The gradient flows from the `loss` back to `h,k,l` (due to spot position changes) and `omega_pixel` (due to intensity scaling).
    2.  The gradient flows from these intermediates back to the `scattering_vectors` and `diffracted_vectors`.
    3.  It then flows back through the detector geometry calculation to the `distance_mm` parameter.
*   **Physical Intuition of the Gradient:** If the simulated pattern has the correct relative spot spacing but is globally too large or too small on the detector, this gradient will instruct the optimizer to **adjust the detector distance** to match the scale of the experimental pattern.

## 4. Beam Parameters

### 4.1 Wavelength (`lambda_A`)

*   **Forward Pass Trace:**
    1.  `lambda_A` appears in the denominator of the scattering vector definition: `S = (k_diff - k_in) / lambda`.
    2.  A longer wavelength increases the magnitude of `S` for a given scattering angle, effectively shrinking the Ewald sphere radius in reciprocal space (`1/lambda`).
    3.  This has a similar effect to changing the unit cell size: it causes a radial scaling of the entire diffraction pattern.
*   **Backward Pass (Gradient) Trace:**
    1.  The gradient flows from the `loss` to `h,k,l`, then to the `scattering_vectors`.
    2.  The gradient `dL/dS` flows back to `lambda_A` via the derivative of the `1/x` function.
*   **Physical Intuition of the Gradient:** This gradient indicates how to adjust the wavelength to better match the observed d-spacings. Its effect is highly correlated with `cell` and `distance`. In a typical refinement, `lambda` is often fixed if known, allowing the other parameters to absorb the variance.

### 4.2 Fluence (`fluence`)

*   **Forward Pass Trace:**
    1.  `fluence` is a simple, global multiplicative scale factor applied to the entire calculated `final_image` just before the loss is computed.
    2.  It does not affect the position, shape, or relative intensities of the spots; it only affects their absolute brightness.
*   **Backward Pass (Gradient) Trace:**
    1.  This is the simplest gradient path. The gradient flows from the loss back to the scaled image.
    2.  The derivative `d(Loss)/d(fluence)` is directly computed from the difference between the simulated and target images.
*   **Physical Intuition of the Gradient:** This gradient simply tells the optimizer whether the overall simulation is **too bright or too dim** compared to the data. It allows the model to learn the arbitrary scale factor between the simulation's physical units and the detector's raw ADU values.