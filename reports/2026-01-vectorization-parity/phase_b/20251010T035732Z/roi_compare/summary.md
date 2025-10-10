=== ROI PARITY METRICS ===

**Command:** nb-compare --resample --roi 1792 2304 1792 2304 -- -lambda 0.5 -cell 100 100 100 90 90 90 -N 5 -default_F 100 -distance 500 -detpixels 4096 -pixel 0.05

**Results:**
- Correlation: 1.000000
- RMSE: 0.000033
- Sum ratio (Py/C): 0.999987
- Mean peak distance: 0.78 pixels
- Max peak distance: 1.41 pixels

**Status:** ✅ PASS (correlation=1.000000 ≥ 0.95)
