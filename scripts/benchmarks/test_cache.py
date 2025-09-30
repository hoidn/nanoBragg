#!/usr/bin/env python3
"""
Quick test of PERF-PYTORCH-005 simulator cache implementation.
Tests with a single small size (256x256) to verify caching works.
"""

import os
import sys
import tempfile
from pathlib import Path

# Ensure environment is set per project standards
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Import after environment setup
import torch

# Import benchmark module
sys.path.insert(0, str(Path(__file__).parent))
from benchmark_detailed import run_pytorch_timed, _simulator_cache

def main():
    print("Testing PERF-PYTORCH-005 simulator cache")
    print("=" * 60)

    size = 256
    args = f"-default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 -N 5 -distance 100 -detpixels {size}"
    device = 'cpu'

    with tempfile.TemporaryDirectory() as tmpdir:
        output1 = Path(tmpdir) / "output1.bin"
        output2 = Path(tmpdir) / "output2.bin"

        print(f"\nTest size: {size}x{size}")
        print(f"Device: {device}")

        # Run 1: Cold (no cache)
        print("\n[1] Running COLD (first time, should create simulator)...")
        cache_size_before = len(_simulator_cache)
        timings1 = run_pytorch_timed(args, output1, device=device, use_cache=True)
        cache_size_after = len(_simulator_cache)

        print(f"  Setup time: {timings1['setup']:.3f}s")
        print(f"  Simulation time: {timings1['simulation']:.3f}s")
        print(f"  Cache hit: {timings1['cache_hit']}")
        print(f"  Cache size before: {cache_size_before}, after: {cache_size_after}")

        # Run 2: Warm (use cache)
        print("\n[2] Running WARM (should reuse cached simulator)...")
        cache_size_before = len(_simulator_cache)
        timings2 = run_pytorch_timed(args, output2, device=device, use_cache=True)
        cache_size_after = len(_simulator_cache)

        print(f"  Setup time: {timings2['setup']:.3f}s")
        print(f"  Simulation time: {timings2['simulation']:.3f}s")
        print(f"  Cache hit: {timings2['cache_hit']}")
        print(f"  Cache size before: {cache_size_before}, after: {cache_size_after}")

        # Analysis
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)

        assert not timings1['cache_hit'], "First run should be a cache miss"
        assert timings2['cache_hit'], "Second run should be a cache hit"

        speedup = timings1['setup'] / timings2['setup']
        print(f"\n✓ Cache miss on first run: {timings1['cache_hit']}")
        print(f"✓ Cache hit on second run: {timings2['cache_hit']}")
        print(f"✓ Setup speedup: {speedup:.1f}x")
        print(f"✓ COLD setup: {timings1['setup']*1000:.1f}ms")
        print(f"✓ WARM setup: {timings2['setup']*1000:.1f}ms")

        # Check exit criteria
        if timings2['setup'] < 0.050:
            print(f"\n✓✓ PERF-PYTORCH-005 EXIT CRITERIA MET")
            print(f"   Warm setup {timings2['setup']*1000:.1f}ms < 50ms target")
        else:
            print(f"\n⚠ PERF-PYTORCH-005: Warm setup {timings2['setup']*1000:.1f}ms > 50ms target")

        print("\n✓ Test PASSED - cache mechanism works correctly")

if __name__ == "__main__":
    main()