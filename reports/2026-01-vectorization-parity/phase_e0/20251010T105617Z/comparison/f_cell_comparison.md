# Tap 4 F_cell Comparison

| Pixel | Impl | total_lookups | out_of_bounds | zero_f | default_f | mean_f_cell | h_range | k_range | l_range |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| edge | PyTorch | 4 | 0 | 0 | N/A | 100.000000 | [-8, -8] | [39, 39] | [-39, -39] |
| edge | C | 4 | 4 | 0 | 4 | 100.000000 | [-7.900663, -7.897033] | [39.347118, 39.356724] | [-39.356724, -39.347118] |
| centre | PyTorch | 4 | 0 | 0 | N/A | 100.000000 | [0, 0] | [0, 0] | [0, 0] |
| centre | C | 4 | 0 | 4 | 0 | 0.000000 | [-1e-06, -0.0] | [0.005, 0.015] | [-0.015, -0.005] |

## Notes
- PyTorch metrics from Attempt #26 (`20251010T102752Z/py_taps`).
- C metrics from Attempt #27 (`20251010T103811Z/c_taps`).
- **CRITICAL DISCREPANCY**: Centre pixel (2048,2048) shows PyTorch mean_f_cell=100.0 (default_F) vs C mean_f_cell=0.0 (zero array value).
- Edge pixel (0,0) correctly uses default_F=100 in both implementations (out-of-bounds HKL).
- Centre pixel Miller indices are all zero (h=0, k=0, l=0) - direct beam position, in-bounds lookup.
- This suggests PyTorch applies default_F fallback for in-bounds lookups when HKL array contains zeros, while C returns the array value (0.0).
- Need to audit: Should default_F apply to in-bounds zero values, or only to out-of-bounds lookups?