# Oversample Unification Refactor Plan
Goal
Unify the oversample==1 and oversample>1 code paths in simulator.py to enable whole-function torch.compile optimization and reduce code duplication.
Success Criteria

 All existing tests pass bit-for-bit
 <5% performance regression for oversample==1 case
 Compilation time reduced or neutral
 ~100 lines of duplicate code removed
 Single code path handles all oversample values


Phase 1: Infrastructure (1-2 days)
1.1 Add Unified Offset Generation
File: simulator.py
Location: New helper method in Simulator class
pythondef _generate_subpixel_offsets(
    self, 
    oversample: int,
    pixel_size_m: torch.Tensor
) -> torch.Tensor:
    """
    Generate subpixel offset grid for any oversample value.
    
    Returns:
        offsets: Shape (oversample^2, 3) or (1, 3) for oversample==1
        
    For oversample==1, returns zeros to avoid special-casing.
    """
    if oversample == 1:
        return torch.zeros(1, 3, device=self.device, dtype=self.dtype)
    
    # Existing subpixel offset logic from lines 700-710
    subpixel_step = 1.0 / oversample
    offset_start = -0.5 + subpixel_step / 2.0
    
    subpixel_offsets = offset_start + torch.arange(
        oversample, device=self.device, dtype=self.dtype
    ) * subpixel_step
    
    sub_s, sub_f = torch.meshgrid(subpixel_offsets, subpixel_offsets, indexing='ij')
    sub_s_flat = sub_s.flatten()
    sub_f_flat = sub_f.flatten()
    
    f_axis = self.detector.fdet_vec
    s_axis = self.detector.sdet_vec
    pixel_size_m_tensor = torch.as_tensor(
        pixel_size_m, device=self.device, dtype=self.dtype
    )
    
    delta_s = sub_s_flat * pixel_size_m_tensor
    delta_f = sub_f_flat * pixel_size_m_tensor
    
    return delta_s.unsqueeze(-1) * s_axis + delta_f.unsqueeze(-1) * f_axis
Test: Unit test that _generate_subpixel_offsets(1, ...) returns zeros
1.2 Extract Omega Calculation
File: simulator.py
Location: New helper method
pythondef _compute_omega(
    self,
    pixel_coords_m: torch.Tensor,
    pixel_size_m: torch.Tensor,
    close_distance_m: torch.Tensor
) -> torch.Tensor:
    """
    Compute solid angle for pixel/subpixel coordinates.
    
    Args:
        pixel_coords_m: Shape (..., 3) in meters
    
    Returns:
        omega: Shape (...) solid angle values
    """
    pixel_squared = torch.sum(pixel_coords_m * pixel_coords_m, dim=-1)
    pixel_squared = pixel_squared.clamp_min(1e-20)
    airpath_m = torch.sqrt(pixel_squared)
    
    if self.detector.config.point_pixel:
        return 1.0 / (airpath_m * airpath_m)
    else:
        return (
            (pixel_size_m * pixel_size_m)
            / (airpath_m * airpath_m)
            * close_distance_m
            / airpath_m
        )
Test: Verify outputs match existing calculations

Phase 2: Create Unified Implementation (2-3 days)
2.1 New Unified Code Path
File: simulator.py
Location: Replace lines 650-850 in run() method
pythondef run(self, ...):
    # ... existing setup code ...
    
    # UNIFIED IMPLEMENTATION
    # Generate subpixel offsets (returns zeros for oversample==1)
    n_subpixels = oversample * oversample
    subpixel_offsets = self._generate_subpixel_offsets(
        oversample, 
        pixel_size_m=self.detector.pixel_size
    )  # Shape: (n_subpixels, 3)
    
    # Expand pixel coordinates for all subpixels
    # pixel_coords_meters: (S, F, 3)
    S, F = pixel_coords_meters.shape[:2]
    
    # Add subpixel dimension: (S, F, 3) -> (S, F, n_subpixels, 3)
    coords_with_subpixels = (
        pixel_coords_meters.unsqueeze(2) + 
        subpixel_offsets.unsqueeze(0).unsqueeze(0)
    )
    
    # Convert to Angstroms and reshape for batched physics
    coords_angstroms = coords_with_subpixels * 1e10
    coords_flat = coords_angstroms.reshape(-1, 3).contiguous()
    
    # Compute physics for all subpixels
    if n_sources > 1:
        incident_dirs = -source_directions
        wavelengths = source_wavelengths_A
        intensity_flat = self._compute_physics_for_position(
            coords_flat, rot_a, rot_b, rot_c, 
            rot_a_star, rot_b_star, rot_c_star,
            incident_beam_direction=incident_dirs,
            wavelength=wavelengths,
            source_weights=source_weights
        )
    else:
        intensity_flat = self._compute_physics_for_position(
            coords_flat, rot_a, rot_b, rot_c,
            rot_a_star, rot_b_star, rot_c_star
        )
    
    # Reshape back: (S*F*n_subpixels,) -> (S, F, n_subpixels)
    intensity_grid = intensity_flat.reshape(S, F, n_subpixels)
    
    # Normalize by steps
    intensity_grid = intensity_grid / steps
    
    # Compute omega for all subpixels
    coords_meters_grid = coords_with_subpixels  # (S, F, n_subpixels, 3)
    omega_grid = self._compute_omega(
        coords_meters_grid,
        pixel_size_m=torch.as_tensor(
            self.detector.pixel_size, 
            device=self.device, dtype=self.dtype
        ),
        close_distance_m=torch.as_tensor(
            self.detector.close_distance,
            device=self.device, dtype=self.dtype
        )
    )  # Shape: (S, F, n_subpixels)
    
    # Apply omega based on oversample flags
    if oversample_omega or oversample == 1:
        # Per-subpixel omega (or single pixel case)
        intensity_with_omega = intensity_grid * omega_grid
    else:
        # Last-value semantics for subpixels
        intensity_with_omega = intensity_grid * omega_grid[..., -1:]
    
    # Sum over subpixels: (S, F, n_subpixels) -> (S, F)
    normalized_intensity = intensity_with_omega.sum(dim=-1)
    
    # Apply detector absorption if configured
    if self._should_apply_absorption():
        normalized_intensity = self._apply_detector_absorption(
            normalized_intensity,
            pixel_coords_meters,
            oversample_thick
        )
    
    # Final scaling
    physical_intensity = (
        normalized_intensity * 
        self.r_e_sqr * 
        self.fluence
    )
    
    # ... rest of existing code (water background, ROI, etc.) ...
2.2 Add Safety Helper
pythondef _should_apply_absorption(self) -> bool:
    """Check if absorption calculation is needed."""
    return (
        self.detector.config.detector_thick_um is not None and
        self.detector.config.detector_thick_um > 0 and
        self.detector.config.detector_abs_um is not None and
        self.detector.config.detector_abs_um > 0
    )
Validation:

Add @unittest.skip("Unified path not enabled") to all tests
Run tests to confirm they still pass with old code


Phase 3: Feature Flag Switchover (1 day)
3.1 Add Feature Flag
File: simulator.py
pythonclass Simulator:
    def __init__(self, ...):
        # ... existing init ...
        
        # Feature flag for unified path
        self._use_unified_oversample = os.environ.get(
            'NANOBRAGG_UNIFIED_OVERSAMPLE', '0'
        ) == '1'
3.2 Conditional Execution
pythondef run(self, ...):
    # ... setup ...
    
    if self._use_unified_oversample:
        return self._run_unified(...)
    else:
        return self._run_legacy(...)

def _run_unified(self, ...):
    # New implementation from Phase 2
    ...

def _run_legacy(self, ...):
    # Move existing if/else into here
    ...
Validation:

Run all tests with NANOBRAGG_UNIFIED_OVERSAMPLE=0 (should pass)
Run all tests with NANOBRAGG_UNIFIED_OVERSAMPLE=1 (find failures)


Phase 4: Debug & Validate (2-3 days)
4.1 Numerical Validation
For each failing test:

Add trace output to both paths
Compare intermediate values:

Subpixel coordinates
Physics intensity before omega
Omega values
Final intensity


Identify divergence point
Fix unified path

Expected issues:

Shape mismatches in edge cases
Off-by-one in subpixel indexing
Omega application order differences
ROI/mask interaction bugs

4.2 Performance Validation
Benchmark script:
pythonimport time
import torch
from nanobrag_torch import Simulator, Crystal, Detector

# Test oversample==1 (most common case)
for unified in [False, True]:
    os.environ['NANOBRAGG_UNIFIED_OVERSAMPLE'] = '1' if unified else '0'
    
    sim = Simulator(crystal, detector)
    
    # Warmup
    for _ in range(3):
        sim.run()
    
    # Benchmark
    torch.cuda.synchronize()
    start = time.time()
    for _ in range(10):
        sim.run()
    torch.cuda.synchronize()
    elapsed = time.time() - start
    
    print(f"Unified={unified}: {elapsed/10:.3f}s per run")
Acceptance: <5% regression
4.3 Memory Profiling
pythonimport torch.cuda

torch.cuda.reset_peak_memory_stats()
sim.run()
peak_mb = torch.cuda.max_memory_allocated() / 1e6
print(f"Peak memory: {peak_mb:.1f} MB")
Acceptance: <10% increase

Phase 5: Compilation Testing (1 day)
5.1 Verify torch.compile Works
python@torch.compile(mode="reduce-overhead")
def run(self, ...):
    # Unified implementation
    ...
Test:

Does it compile without errors?
Does compiled version match eager?
Is it faster than current separate compilation?

5.2 Remove Clone Workaround
If whole-function compilation works, try removing:
python# From _compute_physics_for_position
incident_beam_direction = incident_beam_direction.clone()  # Remove?
Test if CUDA graphs aliasing errors are gone.

Phase 6: Cleanup & Enable (1 day)
6.1 Remove Feature Flag

Delete _use_unified_oversample flag
Delete _run_legacy() method
Remove ~100 lines of duplicate code

6.2 Update Comments

Remove PERF-PYTORCH-004 clone workaround comments
Add docstring explaining unified approach
Update architecture docs

6.3 Final Validation

All tests pass
Performance benchmarks acceptable
Memory usage acceptable
Code review


Rollback Plan
If Phase 4 finds unfixable issues:

Keep feature flag, default to 0
Document known issues
Leave unified path as experimental
Return to it later with more time


Risk Mitigation
High-Risk Areas

ROI/mask interaction - subpixel coordinates may handle masks differently
Multi-source accumulation - shape broadcasting with extra dimension
Absorption calculation - currently only for oversample>1 path
Debug output - _apply_debug_output() assumes certain shapes

Mitigation Strategies

Phase 1 & 2: No test changes, just new code
Phase 3: Feature flag allows A/B comparison
Phase 4: Extensive validation before enabling
Phase 6: Final cleanup only after confirmed working

