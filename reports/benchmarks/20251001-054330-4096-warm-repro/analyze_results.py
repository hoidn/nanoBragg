#!/usr/bin/env python3
"""Analyze B6 reproducibility results."""
import json
import sys
from pathlib import Path
from statistics import mean, stdev

def main():
    outdir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Collect all run JSON files
    results = []
    for i in range(1, 11):
        json_file = outdir / f"run{i}_results.json"
        if json_file.exists():
            with open(json_file) as f:
                data = json.load(f)
                results.append(data)

    if not results:
        print("ERROR: No results found")
        return 1

    print(f"Loaded {len(results)} runs\n")

    # Extract key metrics
    speedups = []
    py_times = []
    c_times = []
    compile_modes = []
    cache_hits = []

    for run_data in results:
        # Each run_data is a list of size results
        for size_result in run_data:
            if size_result.get('size') == 4096:
                speedup = size_result.get('speedup_warm', 0)
                py_time = size_result.get('py_time_warm', 0)
                c_time = size_result.get('c_time', 0)
                compile_mode = size_result.get('compile_mode_warm', 'unknown')
                cache_hit = size_result.get('cache_hit_warm', False)

                if speedup > 0:
                    speedups.append(speedup)
                    py_times.append(py_time)
                    c_times.append(c_time)
                    compile_modes.append(compile_mode)
                    cache_hits.append(cache_hit)

    if not speedups:
        print("ERROR: No 4096x4096 speedup data found")
        return 1

    # Calculate statistics
    mean_speedup = mean(speedups)
    std_speedup = stdev(speedups) if len(speedups) > 1 else 0
    cv = (std_speedup / mean_speedup) * 100 if mean_speedup > 0 else 0

    mean_py = mean(py_times)
    mean_c = mean(c_times)
    std_py = stdev(py_times) if len(py_times) > 1 else 0
    std_c = stdev(c_times) if len(c_times) > 1 else 0

    # Report
    print("=" * 60)
    print("B6 Reproducibility Study Results")
    print("=" * 60)
    print(f"\nSample size: {len(speedups)} runs")
    print(f"\nSpeedup (C warm / PyTorch warm):")
    print(f"  Mean:    {mean_speedup:.4f} (PyTorch {1/mean_speedup:.2f}× {'slower' if mean_speedup < 1 else 'faster'})")
    print(f"  Std Dev: {std_speedup:.4f}")
    print(f"  CV:      {cv:.1f}% (coefficient of variation)")
    print(f"  Range:   [{min(speedups):.4f}, {max(speedups):.4f}]")

    print(f"\nAbsolute times:")
    print(f"  PyTorch warm: {mean_py:.3f}s (±{std_py:.3f}s)")
    print(f"  C warm:       {mean_c:.3f}s (±{std_c:.3f}s)")

    print(f"\nMetadata:")
    print(f"  Compile modes: {set(compile_modes)}")
    print(f"  Cache hits: {sum(cache_hits)}/{len(cache_hits)} runs")

    # Compare to targets
    print(f"\n" + "=" * 60)
    print("Comparison to Targets")
    print("=" * 60)
    target_speedup = 0.83  # ≤1.2× slower = speedup ≥0.83
    if mean_speedup >= target_speedup:
        status = "✓ MEETS TARGET"
    else:
        status = f"✗ BELOW TARGET (need {target_speedup:.2f}, have {mean_speedup:.2f})"
    print(f"Target: PyTorch ≤1.2× slower than C (speedup ≥{target_speedup:.2f})")
    print(f"Status: {status}")

    # Historical comparison
    print(f"\n" + "=" * 60)
    print("Historical Comparison")
    print("=" * 60)
    print("Prior measurements:")
    print("  Phase A baseline (2025-10-01): speedup 0.28 (PyTorch 3.55× slower)")
    print("  Attempt #31 (2025-10-01):      speedup 0.83 (PyTorch 1.21× slower)")
    print("  Attempt #32 regression:        speedup 0.30 (PyTorch 3.33× slower)")
    print("  Attempt #33 (2025-10-01):      speedup 0.83±0.03 (PyTorch 1.21× slower)")
    print(f"\nCurrent (B6 with B7 fix):        speedup {mean_speedup:.2f} (PyTorch {1/mean_speedup:.2f}× slower)")

    # Save summary
    summary = {
        'timestamp': outdir.name.split('-')[0] + '-' + outdir.name.split('-')[1],
        'n_runs': len(speedups),
        'mean_speedup': mean_speedup,
        'std_speedup': std_speedup,
        'cv_percent': cv,
        'speedup_range': [min(speedups), max(speedups)],
        'mean_pytorch_warm_s': mean_py,
        'std_pytorch_warm_s': std_py,
        'mean_c_warm_s': mean_c,
        'std_c_warm_s': std_c,
        'slowdown_factor': 1/mean_speedup,
        'compile_modes': list(set(compile_modes)),
        'cache_hits': sum(cache_hits),
        'meets_target': mean_speedup >= target_speedup,
        'target_speedup': target_speedup
    }

    summary_file = outdir / 'B6_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    # Create markdown summary
    md_file = outdir / 'B6_summary.md'
    with open(md_file, 'w') as f:
        f.write(f"# PERF-PYTORCH-004 Phase B Task B6: Warm-Run Reproducibility\n\n")
        f.write(f"**Date:** {summary['timestamp']}\n")
        f.write(f"**Sample size:** {len(speedups)} cold-process runs\n")
        f.write(f"**Configuration:** 4096×4096 detector, CPU, float32, 5 iterations per run\n\n")

        f.write(f"## Results\n\n")
        f.write(f"### Performance Statistics\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| Mean speedup | {mean_speedup:.4f} |\n")
        f.write(f"| PyTorch slowdown | {1/mean_speedup:.2f}× |\n")
        f.write(f"| Std deviation | {std_speedup:.4f} |\n")
        f.write(f"| CV (reproducibility) | {cv:.1f}% |\n")
        f.write(f"| Speedup range | [{min(speedups):.4f}, {max(speedups):.4f}] |\n\n")

        f.write(f"### Absolute Times\n\n")
        f.write(f"| Implementation | Mean | Std Dev |\n")
        f.write(f"|---------------|------|----------|\n")
        f.write(f"| PyTorch warm | {mean_py:.3f}s | ±{std_py:.3f}s |\n")
        f.write(f"| C warm | {mean_c:.3f}s | ±{std_c:.3f}s |\n\n")

        f.write(f"### Metadata\n\n")
        f.write(f"- Compile modes: {', '.join(set(compile_modes))}\n")
        f.write(f"- Cache hits: {sum(cache_hits)}/{len(cache_hits)} runs\n\n")

        f.write(f"## Target Assessment\n\n")
        f.write(f"**Target:** PyTorch ≤1.2× slower than C (speedup ≥{target_speedup:.2f})\n\n")
        if mean_speedup >= target_speedup:
            f.write(f"✓ **MEETS TARGET** - Mean speedup {mean_speedup:.4f} exceeds target {target_speedup:.2f}\n\n")
        else:
            f.write(f"✗ **BELOW TARGET** - Mean speedup {mean_speedup:.4f} below target {target_speedup:.2f}\n")
            f.write(f"  Gap: {target_speedup - mean_speedup:.4f} ({(1 - mean_speedup/target_speedup)*100:.1f}% below)\n\n")

        f.write(f"## Historical Context\n\n")
        f.write(f"| Measurement | Speedup | PyTorch Slowdown | Notes |\n")
        f.write(f"|-------------|---------|------------------|-------|\n")
        f.write(f"| Phase A baseline | 0.28 | 3.55× | Initial measurement |\n")
        f.write(f"| Attempt #31 | 0.83 | 1.21× | Appeared to meet target |\n")
        f.write(f"| Attempt #32 | 0.30 | 3.33× | Regression detected |\n")
        f.write(f"| Attempt #33 | 0.83±0.03 | 1.21× | CV=3.9%, 10 runs |\n")
        f.write(f"| **B6 (current)** | **{mean_speedup:.2f}±{std_speedup:.2f}** | **{1/mean_speedup:.2f}×** | With B7 harness fix |\n\n")

        f.write(f"## Conclusion\n\n")
        if cv < 5.0:
            f.write(f"**Reproducibility:** Excellent (CV={cv:.1f}% < 5%)\n\n")
        elif cv < 10.0:
            f.write(f"**Reproducibility:** Good (CV={cv:.1f}% < 10%)\n\n")
        else:
            f.write(f"**Reproducibility:** Poor (CV={cv:.1f}% ≥ 10%)\n\n")

        if mean_speedup >= target_speedup:
            f.write(f"Phase B target achieved. Ready to proceed to Phase C diagnostics or close Phase B.\n")
        else:
            f.write(f"Phase B target not met. Proceed to Phase C diagnostics to identify bottlenecks.\n")

    print(f"\nSummary saved to:")
    print(f"  - {summary_file}")
    print(f"  - {md_file}")

    return 0

if __name__ == '__main__':
    sys.exit(main())
