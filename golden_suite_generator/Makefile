# Makefile for Golden Suite Generation
#
# This generates the reference test data from the original C code
# for validating the PyTorch implementation.

CC = gcc
CFLAGS = -O3 -lm
# Try to use OpenMP if available, otherwise fallback to no OpenMP
ifeq ($(shell gcc -fopenmp -E - < /dev/null > /dev/null 2>&1 && echo yes), yes)
    CFLAGS += -fopenmp
endif

# Instrumented nanoBragg executable
nanoBragg_golden: nanoBragg.c
	$(CC) $(CFLAGS) -DDEBUG_GOLDEN_SUITE -o nanoBragg_golden nanoBragg.c

# Trace version for debugging vector transformations
nanoBragg_trace: nanoBragg_trace.c
	$(CC) $(CFLAGS) -o nanoBragg_trace nanoBragg_trace.c

# Clean compiled binaries
clean:
	rm -f nanoBragg_golden nanoBragg_trace

# Generate golden test data
golden_data: nanoBragg_golden
	@echo "Generating golden test data..."
	@mkdir -p ../tests/golden_data
	
	# Simple cubic test case
	@echo "Generating simple_cubic test case..."
	./nanoBragg_golden \
		-cell 100 100 100 90 90 90 \
		-lambda 1.0 \
		-distance 100 \
		-detsize 50 \
		-pixel 0.1 \
		-N 5 \
		-default_F 100 \
		-fluence 1e20 \
		-intfile ../tests/golden_data/simple_cubic.img \
		-floatfile ../tests/golden_data/simple_cubic.bin \
		-nonoise \
		2>&1 | tee ../tests/golden_data/simple_cubic.log
	
	# Test case with mosaicity
	@echo "Generating with_mosaicity test case..."
	./nanoBragg_golden \
		-cell 100 100 100 90 90 90 \
		-lambda 1.0 \
		-distance 100 \
		-detsize 50 \
		-pixel 0.1 \
		-N 5 \
		-default_F 100 \
		-fluence 1e20 \
		-mosaic 0.5 \
		-mosaic_domains 5 \
		-intfile ../tests/golden_data/with_mosaicity.img \
		-floatfile ../tests/golden_data/with_mosaicity.bin \
		-nonoise \
		2>&1 | tee ../tests/golden_data/with_mosaicity.log
	
	# Test case with oscillation
	@echo "Generating with_oscillation test case..."
	./nanoBragg_golden \
		-cell 100 100 100 90 90 90 \
		-lambda 1.0 \
		-distance 100 \
		-detsize 50 \
		-pixel 0.1 \
		-N 5 \
		-default_F 100 \
		-fluence 1e20 \
		-osc 1.0 \
		-phisteps 5 \
		-intfile ../tests/golden_data/with_oscillation.img \
		-floatfile ../tests/golden_data/with_oscillation.bin \
		-nonoise \
		2>&1 | tee ../tests/golden_data/with_oscillation.log
	
	@echo "Golden test data generation complete!"

# Main target
all: golden_data

.PHONY: all clean golden_data