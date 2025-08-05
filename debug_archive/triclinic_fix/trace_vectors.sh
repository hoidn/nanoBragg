#!/bin/bash
# Trace vector transformations for triclinic test case

# Create a simple P1.hkl file with one reflection
cat > P1_trace.hkl << EOF
0 0 0 100
1 0 0 100
0 1 0 100
0 0 1 100
EOF

# Run with triclinic parameters and misset angles
# Only generate a tiny image to focus on vector transformations
./golden_suite_generator/nanoBragg \
  -cell 70 80 90 75.0391 85.0136 95.0081 \
  -misset -89.968546 -31.328953 177.753396 \
  -hkl P1_trace.hkl \
  -lambda 1.0 \
  -distance 100 \
  -detsize 1 \
  -pixel 1 \
  -N 1 \
  -oversample 1 \
  2>&1 | grep -E "TRACE:|^a\[|^b\[|^c\[|^a_star|^b_star|^c_star|misset|cross|Volume" > vector_trace.log

echo "Vector trace saved to vector_trace.log"