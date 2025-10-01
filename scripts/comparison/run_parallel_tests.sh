#!/bin/bash
# Script to run all AT-PARALLEL tests and generate comparison PNGs

# Set environment variables
export KMP_DUPLICATE_LIB_OK=TRUE
export NB_RUN_PARALLEL=1
export NB_C_BIN=./golden_suite_generator/nanoBragg

# Create output directory
OUTPUT_DIR="parallel_test_outputs"
mkdir -p "$OUTPUT_DIR"

# Function to run a single test and generate outputs
run_test() {
    local test_name=$1
    local test_file=$2

    echo "=========================================="
    echo "Running $test_name"
    echo "=========================================="

    # Create test-specific directory
    TEST_DIR="$OUTPUT_DIR/$test_name"
    mkdir -p "$TEST_DIR"

    # Run the test and capture output
    pytest "$test_file" -v --tb=short 2>&1 | tee "$TEST_DIR/test_output.log"

    # Check if comparison artifacts were created
    if [ -d "comparison_artifacts" ]; then
        echo "Moving comparison artifacts to $TEST_DIR"
        mv comparison_artifacts/* "$TEST_DIR/" 2>/dev/null || true

        # Generate PNGs if .bin files exist
        for bin_file in "$TEST_DIR"/*.bin; do
            if [ -f "$bin_file" ]; then
                base_name=$(basename "$bin_file" .bin)
                python -c "
import numpy as np
import matplotlib.pyplot as plt
data = np.fromfile('$bin_file', dtype=np.float32)
# Try to reshape to square image
size = int(np.sqrt(len(data)))
if size * size == len(data):
    data = data.reshape(size, size)
    plt.figure(figsize=(8, 8))
    plt.imshow(data, cmap='viridis', origin='lower')
    plt.colorbar()
    plt.title('$base_name')
    plt.savefig('$TEST_DIR/${base_name}.png', dpi=150)
    plt.close()
    print(f'Generated $TEST_DIR/${base_name}.png')
else:
    print(f'Could not reshape $bin_file to square image')
" 2>/dev/null || echo "Could not convert $bin_file to PNG"
            fi
        done
    fi

    # Use nb-compare if available for specific test cases
    if command -v nb-compare &> /dev/null; then
        case "$test_name" in
            "AT-PARALLEL-001")
                echo "Running nb-compare for beam center scaling test..."
                nb-compare --outdir "$TEST_DIR/compare_64x64" -- \
                    -default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 \
                    -detpixels 64 -distance 100 -N 3 -floatfile output.bin
                ;;
            "AT-PARALLEL-006")
                echo "Running nb-compare for single reflection test..."
                nb-compare --outdir "$TEST_DIR/compare_single" -- \
                    -default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 \
                    -detpixels 256 -distance 100 -N 5 -floatfile output.bin
                ;;
            "AT-PARALLEL-012")
                echo "Running nb-compare for reference pattern test..."
                nb-compare --outdir "$TEST_DIR/compare_simple_cubic" -- \
                    -default_F 100 -cell 100 100 100 90 90 90 -lambda 6.2 \
                    -detpixels 1024 -distance 100 -N 5 -floatfile output.bin
                ;;
            "AT-PARALLEL-026")
                echo "Running nb-compare for triclinic test..."
                nb-compare --outdir "$TEST_DIR/compare_triclinic" -- \
                    -default_F 100 -cell 70 80 90 85 95 105 -lambda 1.5 \
                    -detpixels 256 -distance 150 -N 1 -misset 5 3 2 -floatfile output.bin
                ;;
        esac
    fi

    echo "Completed $test_name"
    echo ""
}

# Run all AT-PARALLEL tests
for i in 001 002 003 004 005 006 007 008 009 010 011 012 013 014 015 016 017 018 020 021 022 023 024 025 026 027; do
    test_file="tests/test_at_parallel_${i}.py"
    if [ -f "$test_file" ]; then
        run_test "AT-PARALLEL-${i}" "$test_file"
    else
        echo "Warning: $test_file not found"
    fi
done

# Generate summary report
echo "=========================================="
echo "Generating summary report..."
echo "=========================================="

cat > "$OUTPUT_DIR/summary.md" << EOF
# AT-PARALLEL Test Results Summary

Generated on: $(date)

## Test Results

EOF

for i in 001 002 003 004 005 006 007 008 009 010 011 012 013 014 015 016 017 018 020 021 022 023 024 025 026 027; do

    TEST_DIR="$OUTPUT_DIR/AT-PARALLEL-${i}"
    if [ -d "$TEST_DIR" ]; then
        echo "### AT-PARALLEL-${i}" >> "$OUTPUT_DIR/summary.md"

        # Extract pass/fail from log
        if [ -f "$TEST_DIR/test_output.log" ]; then
            grep -E "passed|failed|skipped|error" "$TEST_DIR/test_output.log" | tail -1 >> "$OUTPUT_DIR/summary.md"
        fi

        # List generated files
        echo "Files generated:" >> "$OUTPUT_DIR/summary.md"
        ls -la "$TEST_DIR"/*.png 2>/dev/null | wc -l | xargs echo "- PNG files:" >> "$OUTPUT_DIR/summary.md"
        ls -la "$TEST_DIR"/*.bin 2>/dev/null | wc -l | xargs echo "- Binary files:" >> "$OUTPUT_DIR/summary.md"

        echo "" >> "$OUTPUT_DIR/summary.md"
    fi
done

echo "=========================================="
echo "All tests completed!"
echo "Results saved to: $OUTPUT_DIR"
echo "Summary available at: $OUTPUT_DIR/summary.md"
echo "=========================================="

# Final summary statistics
echo ""
echo "Quick Statistics:"
find "$OUTPUT_DIR" -name "*.png" | wc -l | xargs echo "Total PNG files generated:"
find "$OUTPUT_DIR" -name "*.bin" | wc -l | xargs echo "Total binary files:"
find "$OUTPUT_DIR" -name "test_output.log" | xargs grep -h "passed" | wc -l | xargs echo "Tests with passes:"
find "$OUTPUT_DIR" -name "test_output.log" | xargs grep -h "failed" | wc -l | xargs echo "Tests with failures:"
find "$OUTPUT_DIR" -name "test_output.log" | xargs grep -h "skipped" | wc -l | xargs echo "Tests with skips:"