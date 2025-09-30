#!/usr/bin/env python3
"""
Test script for PERF-PYTORCH-004 Phase 2: Compiled Kernel Cache.

This script creates multiple independent Simulator instances with identical
parameters and measures whether the compiled kernel cache provides speedup.

Exit Criteria (from plan):
- Second→tenth simulator instantiations skip compile (<50 ms setup)
- Cache hits logged via NB_SIM_CACHE_DEBUG

Follows nanoBragg tooling standards (testing_strategy.md §6):
- Located in scripts/benchmarks/
- Honors KMP_DUPLICATE_LIB_OK env var
- Saves outputs to reports/benchmarks/<timestamp>/
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Ensure environment is set per project standards
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Import after environment setup
import torch


def test_kernel_cache(n_constructions=10, device='cpu', dtype=torch.float64, size=1024):
    """
    Test compiled kernel cache by creating multiple Simulator instances.

    Args:
        n_constructions: Number of independent Simulator constructions
        device: Device to test ('cpu' or 'cuda')
        dtype: Data type (torch.float32 or torch.float64)
        size: Detector size (pixels)

    Returns:
        dict: Timing results and cache statistics
    """
    from nanobrag_torch.config import (
        CrystalConfig, DetectorConfig, BeamConfig,
        CrystalShape, DetectorConvention
    )
    from nanobrag_torch.models.crystal import Crystal
    from nanobrag_torch.models.detector import Detector
    from nanobrag_torch.simulator import Simulator
    from nanobrag_torch.utils.runtime_cache import get_global_kernel_cache, clear_global_cache

    # Clear cache at start for clean test
    clear_global_cache()

    # Setup configs (scalars only - device applied at model creation)
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=[5, 5, 5],
        default_F=100.0,
        shape=CrystalShape.SQUARE
    )

    detector_config = DetectorConfig(
        spixels=size,
        fpixels=size,
        pixel_size_mm=0.1,
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
        oversample=1
    )

    beam_config = BeamConfig(wavelength_A=6.2)

    # Convert device string to torch.device
    device_obj = torch.device(device)

    # Timing results
    construction_times = []
    cache_stats_history = []

    cache = get_global_kernel_cache()

    print(f"\n{'='*80}")
    print(f"Testing Compiled Kernel Cache ({n_constructions} constructions)")
    print(f"Device: {device_obj}, Dtype: {dtype}, Size: {size}x{size}")
    print(f"{'='*80}\n")

    for i in range(n_constructions):
        # Create NEW instances each time (not reusing)
        start = time.time()

        crystal = Crystal(crystal_config, device=device_obj, dtype=dtype)
        detector = Detector(detector_config, device=device_obj, dtype=dtype)
        simulator = Simulator(crystal, detector, crystal_config, beam_config, device=device_obj, dtype=dtype)

        if device_obj.type == 'cuda':
            torch.cuda.synchronize()

        construction_time = time.time() - start
        construction_times.append(construction_time)

        # Get cache stats
        stats = cache.stats()
        cache_stats_history.append(stats.copy())

        # Print progress
        if i == 0:
            print(f"  Construction {i+1:2d}: {construction_time*1000:6.1f} ms (COLD - expected cache MISS)")
        elif i == 1:
            speedup = construction_times[0] / construction_time
            print(f"  Construction {i+1:2d}: {construction_time*1000:6.1f} ms (WARM - expected cache HIT, {speedup:.1f}x faster)")
        else:
            speedup = construction_times[0] / construction_time
            print(f"  Construction {i+1:2d}: {construction_time*1000:6.1f} ms ({speedup:.1f}x faster)")

        # Clean up to avoid memory issues
        del simulator, detector, crystal

    print(f"\n{'='*80}")
    print("Results Summary")
    print(f"{'='*80}\n")

    cold_time = construction_times[0]
    warm_times = construction_times[1:]
    avg_warm_time = sum(warm_times) / len(warm_times)
    speedup = cold_time / avg_warm_time

    print(f"  Cold (1st) construction: {cold_time*1000:.1f} ms")
    print(f"  Warm (2nd-{n_constructions}th) avg: {avg_warm_time*1000:.1f} ms")
    print(f"  Average speedup: {speedup:.1f}x")
    print(f"  Max warm time: {max(warm_times)*1000:.1f} ms")
    print(f"  Min warm time: {min(warm_times)*1000:.1f} ms")

    # Final cache stats
    final_stats = cache.stats()
    print(f"\nCache Statistics:")
    print(f"  Hits: {final_stats['hits']}")
    print(f"  Misses: {final_stats['misses']}")
    print(f"  Hit rate: {final_stats['hit_rate']*100:.1f}%")
    print(f"  Cache size: {final_stats['size']} entries")

    # Check exit criteria
    print(f"\n{'='*80}")
    print("PERF-PYTORCH-004 Phase 2 Exit Criteria")
    print(f"{'='*80}\n")

    target_ms = 50.0
    all_warm_fast = all(t*1000 < target_ms for t in warm_times)

    if all_warm_fast:
        print(f"  ✓ All warm constructions < {target_ms} ms")
        print(f"  ✓ EXIT CRITERIA MET")
    else:
        slow_constructions = sum(1 for t in warm_times if t*1000 >= target_ms)
        print(f"  ✗ {slow_constructions}/{len(warm_times)} warm constructions >= {target_ms} ms")
        print(f"  ✗ EXIT CRITERIA NOT MET")

    return {
        'construction_times': construction_times,
        'cache_stats': final_stats,
        'speedup': speedup,
        'exit_criteria_met': all_warm_fast
    }


def main():
    # Create timestamped output directory
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    output_dir = Path('reports/benchmarks') / f'{timestamp}-kernel-cache'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("PERF-PYTORCH-004 Phase 2: Compiled Kernel Cache Test")
    print("=" * 80)
    print(f"\nOutputs will be saved to: {output_dir}")

    # Test configurations
    configs = [
        {'device': 'cpu', 'dtype': torch.float64, 'size': 512},
    ]

    if torch.cuda.is_available():
        configs.append({'device': 'cuda', 'dtype': torch.float32, 'size': 1024})

    results_all = []

    for config in configs:
        result = test_kernel_cache(n_constructions=10, **config)
        results_all.append({**config, **result})

        # Save individual result
        import json
        dtype_str = str(config['dtype']).split('.')[-1]
        result_file = output_dir / f"result_{config['device']}_{dtype_str}_{config['size']}.json"

        # Convert non-serializable types
        serializable_result = {
            'device': config['device'],
            'dtype': dtype_str,
            'size': config['size'],
            'construction_times_ms': [t*1000 for t in result['construction_times']],
            'cache_stats': result['cache_stats'],
            'speedup': result['speedup'],
            'exit_criteria_met': result['exit_criteria_met']
        }

        with open(result_file, 'w') as f:
            json.dump(serializable_result, f, indent=2)

        print(f"\nResults saved to: {result_file}")

    # Summary
    print(f"\n{'='*80}")
    print("OVERALL SUMMARY")
    print(f"{'='*80}\n")

    all_passed = all(r['exit_criteria_met'] for r in results_all)

    if all_passed:
        print("  ✓ ALL TESTS PASSED")
        print("  ✓ PERF-PYTORCH-004 Phase 2 COMPLETE")
    else:
        failed_configs = [r for r in results_all if not r['exit_criteria_met']]
        print(f"  ✗ {len(failed_configs)}/{len(results_all)} configurations failed")
        for r in failed_configs:
            print(f"    - {r['device']} {r['dtype']} {r['size']}x{r['size']}")

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
