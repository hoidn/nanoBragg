#!/bin/bash
# Check where trace statements are located in C code

echo "=== Searching for TRACE_C statements ==="
grep -n "printf.*TRACE_C" /Users/ollie/Documents/nanoBragg/golden_suite_generator/nanoBragg.c | head -30

echo -e "\n=== Searching for where detector_twotheta is used ==="
grep -n "detector_twotheta" /Users/ollie/Documents/nanoBragg/golden_suite_generator/nanoBragg.c | grep -E "1[67][0-9]{2}|printf.*TRACE" | head -20