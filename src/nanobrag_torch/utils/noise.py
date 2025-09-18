"""
Noise generation utilities for nanoBragg PyTorch implementation.

This module implements Poisson noise generation following the spec requirements:
- Exact Poisson for means < 12
- Rejection sampling for means between 12 and 1e6
- Gaussian approximation for means > 1e6
"""

import torch
from typing import Optional, Union


def generate_poisson_noise(
    mean: torch.Tensor,
    seed: Optional[int] = None,
    adc_offset: float = 40.0,
    readout_noise: float = 3.0,
    overload_value: float = 65535.0
) -> tuple[torch.Tensor, int]:
    """
    Generate Poisson noise following nanoBragg.c's three-regime approach.

    Per spec AT-NOISE-001:
    - For mean < 12: Use exact Poisson algorithm
    - For 12 <= mean <= 1e6: Use rejection sampling
    - For mean > 1e6: Use Gaussian approximation N(mean, variance=mean)

    C-Code Implementation Reference (from nanoBragg.c, lines 43726-43852):
    ```c
    // Three regimes for Poisson noise generation
    if(intfile_scale*floatimage[j] < 12) {
        // Exact Poisson for small means
        L = exp(-(intfile_scale*floatimage[j]));
        k=0; p=1.0;
        do {
            k++;
            p *= ((double) nrand(seed)/(double) RAND_MAX);
        } while (p > L);
        intimage[j] = k-1;
    } else if(intfile_scale*floatimage[j] < 1e6) {
        // Rejection sampling for medium means
        c = 0.767 - 3.36/(intfile_scale*floatimage[j]);
        // ... rejection algorithm ...
    } else {
        // Gaussian approximation for large means
        intimage[j] = poidev((intfile_scale*floatimage[j]),&seed);
    }
    ```

    Args:
        mean: Input intensities (photon counts) as float tensor
        seed: Random seed for reproducibility (None = use PyTorch default)
        adc_offset: ADC offset to add to all pixels
        readout_noise: Gaussian readout noise sigma
        overload_value: Maximum value before saturation

    Returns:
        Tuple of (noisy image, overload count)
        - noisy image: Integer tensor with Poisson noise, ADC offset, and clipping
        - overload_count: Number of pixels that exceeded overload_value
    """
    # Set up random generator with seed if provided
    if seed is not None:
        generator = torch.Generator(device=mean.device)
        generator.manual_seed(seed)
    else:
        generator = None

    # Create output tensor with same shape
    noisy = torch.zeros_like(mean)

    # Separate pixels into three regimes
    small_mask = mean < 12
    medium_mask = (mean >= 12) & (mean <= 1e6)
    large_mask = mean > 1e6

    # Regime 1: Exact Poisson for small means (<12)
    if small_mask.any():
        small_means = mean[small_mask]
        # For small counts, use torch.poisson which is exact for small lambda
        small_noise = torch.poisson(small_means, generator=generator)
        noisy[small_mask] = small_noise

    # Regime 2: Rejection sampling for medium means (12 to 1e6)
    if medium_mask.any():
        medium_means = mean[medium_mask]
        # PyTorch's poisson uses rejection sampling internally for this range
        # We use it directly rather than reimplementing the rejection algorithm
        medium_noise = torch.poisson(medium_means, generator=generator)
        noisy[medium_mask] = medium_noise

    # Regime 3: Gaussian approximation for large means (>1e6)
    if large_mask.any():
        large_means = mean[large_mask]
        # For very large means, Poisson approaches N(mean, variance=mean)
        std = torch.sqrt(large_means)
        gaussian_noise = torch.normal(mean=large_means, std=std, generator=generator)
        # Round to nearest integer since we need photon counts
        noisy[large_mask] = torch.round(gaussian_noise)

    # Add readout noise (Gaussian)
    if readout_noise > 0:
        readout = torch.normal(
            mean=torch.zeros_like(noisy),
            std=readout_noise,
            generator=generator
        )
        noisy = noisy + readout

    # Add ADC offset
    noisy = noisy + adc_offset

    # Ensure non-negative (clip at 0)
    noisy = torch.clamp(noisy, min=0)

    # Count overloads before clipping
    overload_count = (noisy > overload_value).sum().item()

    # Clip at overload value
    noisy = torch.clamp(noisy, max=overload_value)

    # Convert to integer
    noisy = torch.round(noisy).to(torch.int32)

    return noisy, overload_count


def lcg_random(seed: int, n: int = 1) -> torch.Tensor:
    """
    Linear Congruential Generator (LCG) for C-compatible random numbers.

    Implements the same LCG as used in nanoBragg.c for exact reproducibility.

    C-Code Implementation Reference (from nanoBragg.c):
    ```c
    #define RAND_MAX 2147483647
    #define RAND_MULT 1103515245
    #define RAND_ADD 12345
    #define RAND_SEED (seed)

    static long int idum;
    double nrand(long *idum) {
        *idum = (RAND_MULT*(*idum)+RAND_ADD) & RAND_MAX;
        return (double) (*idum)/(double) RAND_MAX;
    }
    ```

    Args:
        seed: Initial seed value
        n: Number of random values to generate

    Returns:
        Tensor of n random values in [0, 1)
    """
    # LCG parameters from nanoBragg.c
    RAND_MAX = 2147483647
    RAND_MULT = 1103515245
    RAND_ADD = 12345

    values = torch.zeros(n, dtype=torch.float64)
    current = seed

    for i in range(n):
        current = (RAND_MULT * current + RAND_ADD) & RAND_MAX
        values[i] = float(current) / float(RAND_MAX)

    return values