#!/bin/bash
# PERF-PYTORCH-004 Plan Phase B Task B6: Warm-run reproducibility study
# Rerun after B7 harness fixes with compile mode metadata
#
# Usage: bash scripts/benchmarks/run_b6_reproducibility.sh
#
# Expected output: reports/benchmarks/<timestamp>-4096-warm-repro/
#   containing run1.log...run10.log plus JSON files and summary

set -e

# Ensure environment per project standards
export KMP_DUPLICATE_LIB_OK=TRUE

# Create timestamped output directory
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
OUTDIR="reports/benchmarks/${TIMESTAMP}-4096-warm-repro"
mkdir -p "$OUTDIR"

echo "=========================================="
echo "PERF-PYTORCH-004 Phase B Task B6"
echo "Reproducibility study (10 cold processes)"
echo "=========================================="
echo ""
echo "Output directory: $OUTDIR"
echo "Timestamp: $TIMESTAMP"
echo ""

# Benchmark command
BENCH_CMD="env KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --iterations 5"

# Run 10 independent processes
for i in {1..10}; do
    echo "----------------------------------------"
    echo "Run $i/10 - $(date +"%H:%M:%S")"
    echo "----------------------------------------"

    # Each run in a fresh Python process (no cache reuse across runs)
    # Capture both stdout and results JSON
    LOG_FILE="$OUTDIR/run${i}.log"
    JSON_FILE="$OUTDIR/run${i}_results.json"

    $BENCH_CMD > "$LOG_FILE" 2>&1

    # Extract the benchmark_results.json from the temporary directory
    # The script writes to a timestamped directory, find it and copy
    BENCH_DIR=$(grep -o "reports/benchmarks/[0-9]\{8\}-[0-9]\{6\}" "$LOG_FILE" | head -1 || echo "")
    if [ -n "$BENCH_DIR" ] && [ -f "$BENCH_DIR/benchmark_results.json" ]; then
        cp "$BENCH_DIR/benchmark_results.json" "$JSON_FILE"
        echo "  Copied results to: $JSON_FILE"
    else
        echo "  Warning: Could not find benchmark_results.json for run $i"
    fi

    echo "  Log saved to: $LOG_FILE"
    echo ""
done

echo "=========================================="
echo "All runs complete"
echo "=========================================="
echo ""
echo "Analyzing results..."
echo ""

# Create analysis script inline
cat > "$OUTDIR/analyze_results.py" << 'EOF'
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

    for data in results:
        # Look for 4096x4096 results
        for size_key, size_data in data.items():
            if '4096' in size_key:
                speedup = size_data.get('speedup_warm', 0)
                py_time = size_data.get('pytorch_warm', 0)
                c_time = size_data.get('c_warm', 0)
                compile_mode = size_data.get('compile_mode_warm', 'unknown')
                cache_hit = size_data.get('cache_hit_warm', False)

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

    # Report
    print("=" * 60)
    print("B6 Reproducibility Study Results")
    print("=" * 60)
    print(f"\nSample size: {len(speedups)} runs")
    print(f"\nSpeedup (PyTorch warm / C warm):")
    print(f"  Mean:    {mean_speedup:.4f} (PyTorch {1/mean_speedup:.2f}× {'slower' if mean_speedup < 1 else 'faster'})")
    print(f"  Std Dev: {std_speedup:.4f}")
    print(f"  CV:      {cv:.1f}% (coefficient of variation)")
    print(f"  Range:   [{min(speedups):.4f}, {max(speedups):.4f}]")

    print(f"\nAbsolute times:")
    print(f"  PyTorch warm: {mean_py:.3f}s (±{stdev(py_times):.3f}s)")
    print(f"  C warm:       {mean_c:.3f}s (±{stdev(c_times):.3f}s)")

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

    # Save summary
    summary = {
        'n_runs': len(speedups),
        'mean_speedup': mean_speedup,
        'std_speedup': std_speedup,
        'cv_percent': cv,
        'speedup_range': [min(speedups), max(speedups)],
        'mean_pytorch_warm_s': mean_py,
        'mean_c_warm_s': mean_c,
        'compile_modes': list(set(compile_modes)),
        'cache_hits': sum(cache_hits),
        'meets_target': mean_speedup >= target_speedup,
        'target_speedup': target_speedup
    }

    summary_file = outdir / 'B6_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary saved to: {summary_file}")

    return 0

if __name__ == '__main__':
    sys.exit(main())
EOF

chmod +x "$OUTDIR/analyze_results.py"
python3 "$OUTDIR/analyze_results.py" "$OUTDIR"

echo ""
echo "=========================================="
echo "B6 reproducibility study complete"
echo "Results in: $OUTDIR"
echo "=========================================="
