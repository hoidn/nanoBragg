#!/usr/bin/env python3
"""
Option B Batch Cache Prototype — 4×4 ROI Proof-of-Concept

**Purpose:** Validate batch-indexed φ carryover cache design before production implementation.
**Scope:** CPU float32, minimal 4×4 detector, gradcheck on mock lattice function.
**Exit Criteria:** Gradcheck passes, cache indexing correct, no device leaks.

**DO NOT USE IN PRODUCTION** — This is a disposable design validation script.
"""

import os
import torch
import json
from datetime import datetime

# Required env var for MKL compatibility
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Force CPU for reproducibility
device = torch.device("cpu")
dtype = torch.float32

print("="*80)
print("Option B Batch Cache Prototype — 4×4 ROI")
print("="*80)
print(f"Device: {device}")
print(f"Dtype: {dtype}")
print(f"PyTorch version: {torch.__version__}")
print()

# ============================================================================
# Mock Rotation Function (simplified φ rotation)
# ============================================================================

def compute_phi_rotation_batch(
    base_vec: torch.Tensor,  # Shape: (3,)
    phi_angles: torch.Tensor,  # Shape: (N_phi,)
    spindle_axis: torch.Tensor,  # Shape: (3,)
    batch_size: int  # Number of pixels in batch
) -> torch.Tensor:
    """
    Compute φ rotations for a batch of pixels.

    Returns:
        rotated_vecs: Shape (batch_size, N_phi, 3)
    """
    # Simple rotation (mock — real implementation uses Rodrigues formula)
    # For prototype: just scale by cos(phi) to demonstrate differentiability
    cos_phi = torch.cos(phi_angles)  # (N_phi,)
    sin_phi = torch.sin(phi_angles)  # (N_phi,)

    # Broadcast to batch: (batch_size, N_phi, 3)
    # Real rotation would use cross products; here we mock with simple trig
    rotated_vecs = base_vec.unsqueeze(0).unsqueeze(0) * cos_phi.unsqueeze(0).unsqueeze(-1)
    rotated_vecs = rotated_vecs.expand(batch_size, -1, -1)  # (batch_size, N_phi, 3)

    return rotated_vecs

# ============================================================================
# Mock Cache Class (simplified Crystal.phi_cache)
# ============================================================================

class PhiCarryoverCache:
    """
    Simplified cache for φ=final vectors, indexed by (slow, fast).

    Mirrors proposed Crystal._phi_cache_a/b/c design.
    """
    def __init__(self, spixels: int, fpixels: int, device, dtype):
        self.spixels = spixels
        self.fpixels = fpixels

        # Allocate cache tensor: (S, F, 3)
        # In production: (S, F, N_mos, 3), but prototype uses N_mos=1
        self.cache_a = torch.zeros(
            (spixels, fpixels, 3),
            device=device, dtype=dtype
        )
        print(f"Allocated cache: shape={self.cache_a.shape}, "
              f"memory={self.cache_a.numel()*4/1024:.1f} KB")

    def apply_phi_carryover(
        self,
        slow_indices: torch.Tensor,
        fast_indices: torch.Tensor,
        rotated_vecs: torch.Tensor,  # (batch_size, N_phi, 3)
    ) -> torch.Tensor:
        """
        Substitute cached φ=final from prior pixels into φ=0 slot.

        Args:
            slow_indices: (batch_size,) slow coordinates
            fast_indices: (batch_size,) fast coordinates
            rotated_vecs: (batch_size, N_phi, 3) fresh rotations

        Returns:
            modified_vecs: (batch_size, N_phi, 3) with φ=0 replaced by cache
        """
        batch_size = len(slow_indices)

        # Advanced indexing to retrieve cached vectors
        cached_phi_final = self.cache_a[slow_indices, fast_indices]  # (batch_size, 3)

        # Clone rotated_vecs to avoid in-place modification issues
        # (Production must avoid .clone() if possible — see design note)
        modified_vecs = rotated_vecs.clone()

        # Substitute φ=0 slice
        modified_vecs[:, 0, :] = cached_phi_final

        print(f"  Applied carryover: slow={slow_indices.tolist()}, "
              f"fast={fast_indices.tolist()}, "
              f"cached_mean={cached_phi_final.mean().item():.6f}")

        return modified_vecs

    def store_phi_final(
        self,
        slow_indices: torch.Tensor,
        fast_indices: torch.Tensor,
        phi_final_vecs: torch.Tensor,  # (batch_size, 3)
    ):
        """
        Store φ=final vectors for next pixel's φ=0 carryover.

        Args:
            slow_indices: (batch_size,) slow coordinates
            fast_indices: (batch_size,) fast coordinates
            phi_final_vecs: (batch_size, 3) φ=final vectors to cache
        """
        # In-place update (preserves gradient graph)
        self.cache_a[slow_indices, fast_indices] = phi_final_vecs

        print(f"  Stored φ=final: slow={slow_indices.tolist()}, "
              f"fast={fast_indices.tolist()}, "
              f"stored_mean={phi_final_vecs.mean().item():.6f}")

# ============================================================================
# Mock Simulator Function (simplified batch physics)
# ============================================================================

def simulate_batch_with_carryover(
    base_vec: torch.Tensor,  # (3,) — lattice vector (differentiable input)
    phi_start: float,
    phi_step: float,
    n_phi: int,
    spixels: int,
    fpixels: int,
    cache: PhiCarryoverCache,
    spindle_axis: torch.Tensor,
) -> torch.Tensor:
    """
    Simulate row-wise batched processing with φ carryover cache.

    Returns:
        image: (spixels, fpixels) simulated intensities
    """
    image = torch.zeros((spixels, fpixels), device=base_vec.device, dtype=base_vec.dtype)

    # φ angle schedule
    phi_angles = phi_start + phi_step * torch.arange(n_phi, device=base_vec.device, dtype=base_vec.dtype)

    # Row-wise batch loop
    for slow in range(spixels):
        print(f"\n--- Processing row {slow} ---")

        # Batch indices for this row
        fast_indices = torch.arange(fpixels, device=base_vec.device, dtype=torch.long)
        slow_indices = torch.full_like(fast_indices, slow)

        # Compute fresh rotations for this batch
        rotated_vecs = compute_phi_rotation_batch(
            base_vec, phi_angles, spindle_axis, batch_size=fpixels
        )
        print(f"  Fresh rotations: shape={rotated_vecs.shape}")

        # Apply φ carryover (substitute φ=0 with cached φ=final from prior pixel)
        rotated_vecs = cache.apply_phi_carryover(slow_indices, fast_indices, rotated_vecs)

        # Store φ=final for next pixel's φ=0
        phi_final_vecs = rotated_vecs[:, -1, :]  # (batch_size, 3)
        cache.store_phi_final(slow_indices, fast_indices, phi_final_vecs)

        # Mock physics: sum over φ steps (real sim would compute scattering)
        row_intensities = rotated_vecs.sum(dim=(1, 2))  # (fpixels,)
        image[slow, :] = row_intensities

    return image

# ============================================================================
# Gradient Check Function
# ============================================================================

def gradcheck_lattice_parameter():
    """
    Validate gradient flow through cache operations using torch.autograd.gradcheck.

    Returns:
        success (bool), grad_magnitude (float)
    """
    print("\n" + "="*80)
    print("Gradient Check: Lattice Parameter (cell_a)")
    print("="*80)

    # Differentiable lattice vector (mock a-axis magnitude)
    cell_a = torch.tensor(100.0, requires_grad=True, dtype=torch.float64, device=device)

    # Mock base vector: [cell_a, 0, 0] (simplified)
    def compute_image(a_mag):
        base_vec = torch.stack([a_mag, torch.zeros_like(a_mag), torch.zeros_like(a_mag)])
        spindle_axis = torch.tensor([0.0, 0.0, 1.0], dtype=a_mag.dtype, device=a_mag.device)

        # Initialize cache
        cache = PhiCarryoverCache(spixels=4, fpixels=4, device=a_mag.device, dtype=a_mag.dtype)

        # Simulate
        image = simulate_batch_with_carryover(
            base_vec=base_vec,
            phi_start=0.0,
            phi_step=0.1,
            n_phi=3,  # φ=0, 0.1, 0.2 radians
            spixels=4,
            fpixels=4,
            cache=cache,
            spindle_axis=spindle_axis,
        )

        # Return scalar loss for gradcheck
        return image.sum()

    # Compute gradient via backprop
    loss = compute_image(cell_a)
    loss.backward()

    grad_magnitude = cell_a.grad.item()
    print(f"\nBackprop gradient: dL/d(cell_a) = {grad_magnitude:.6e}")
    print(f"Gradient is finite: {torch.isfinite(cell_a.grad).item()}")

    # Numerical gradient check (float64 for precision)
    print("\nRunning torch.autograd.gradcheck (may take 10-20 sec)...")
    try:
        gradcheck_passed = torch.autograd.gradcheck(
            compute_image,
            cell_a,
            eps=1e-6,
            atol=1e-4,
            raise_exception=False
        )
        print(f"Gradcheck result: {'PASS' if gradcheck_passed else 'FAIL'}")
    except RuntimeError as e:
        print(f"Gradcheck raised exception: {e}")
        gradcheck_passed = False

    return gradcheck_passed, grad_magnitude

# ============================================================================
# Main Execution
# ============================================================================

def main():
    print("\n" + "="*80)
    print("1. Cache Allocation & Indexing Test")
    print("="*80)

    # Mock 4×4 detector
    spixels, fpixels = 4, 4
    cache = PhiCarryoverCache(spixels=spixels, fpixels=fpixels, device=device, dtype=dtype)

    print(f"\nCache shape: {cache.cache_a.shape}")
    print(f"Expected: ({spixels}, {fpixels}, 3)")
    assert cache.cache_a.shape == (spixels, fpixels, 3), "Cache shape mismatch!"

    print("\n" + "="*80)
    print("2. Batch Indexing Test")
    print("="*80)

    # Test batch retrieval for row 0
    slow_indices = torch.tensor([0, 0, 0, 0], dtype=torch.long, device=device)
    fast_indices = torch.tensor([0, 1, 2, 3], dtype=torch.long, device=device)

    # Store mock values
    mock_phi_final = torch.randn((4, 3), device=device, dtype=dtype)
    cache.store_phi_final(slow_indices, fast_indices, mock_phi_final)

    # Retrieve via advanced indexing
    retrieved = cache.cache_a[slow_indices, fast_indices]
    print(f"\nStored values:\n{mock_phi_final}")
    print(f"Retrieved values:\n{retrieved}")
    print(f"Match: {torch.allclose(mock_phi_final, retrieved)}")

    assert torch.allclose(mock_phi_final, retrieved), "Cache retrieval failed!"

    print("\n" + "="*80)
    print("3. Full Simulation with Carryover")
    print("="*80)

    # Reset cache for fresh simulation
    cache = PhiCarryoverCache(spixels=spixels, fpixels=fpixels, device=device, dtype=dtype)

    base_vec = torch.tensor([100.0, 0.0, 0.0], device=device, dtype=dtype)
    spindle_axis = torch.tensor([0.0, 0.0, 1.0], device=device, dtype=dtype)

    image = simulate_batch_with_carryover(
        base_vec=base_vec,
        phi_start=0.0,
        phi_step=0.1,
        n_phi=5,  # φ=0, 0.1, 0.2, 0.3, 0.4 radians
        spixels=spixels,
        fpixels=fpixels,
        cache=cache,
        spindle_axis=spindle_axis,
    )

    print(f"\nSimulated image shape: {image.shape}")
    print(f"Image mean intensity: {image.mean().item():.6f}")
    print(f"Image (4×4 intensities):\n{image}")

    # 4. Gradient Check
    gradcheck_passed, grad_mag = gradcheck_lattice_parameter()

    # 5. Summary Metrics
    metrics = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "device": str(device),
        "dtype": str(dtype),
        "pytorch_version": torch.__version__,
        "cache_shape": list(cache.cache_a.shape),
        "cache_memory_kb": cache.cache_a.numel() * 4 / 1024,
        "image_shape": list(image.shape),
        "image_mean_intensity": image.mean().item(),
        "gradcheck_passed": gradcheck_passed,
        "gradient_magnitude": grad_mag,
    }

    print("\n" + "="*80)
    print("Summary Metrics")
    print("="*80)
    print(json.dumps(metrics, indent=2))

    # Save metrics
    with open("metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print("\nMetrics saved to metrics.json")

    # Exit code
    if gradcheck_passed:
        print("\n✅ PROTOTYPE VALIDATION SUCCESSFUL")
        return 0
    else:
        print("\n❌ PROTOTYPE VALIDATION FAILED (gradcheck)")
        return 1

if __name__ == "__main__":
    exit(main())
