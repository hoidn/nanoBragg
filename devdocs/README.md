```
python reports/milestone1_demo.py --cuda
=== nanoBragg PyTorch Milestone 1 Demo ===
✓ Set random seed for reproducibility
✓ Project root: /Users/ollie/Documents/nanoBragg
✓ Golden data: /Users/ollie/Documents/nanoBragg/tests/golden_data
✓ HKL file: /Users/ollie/Documents/nanoBragg/simple_cubic.hkl
✓ Output directory: /Users/ollie/Documents/nanoBragg/reports

--- Loading Golden Reference ---
✓ Loaded golden image: (1024, 1024)
✓ Golden stats: max=1.55e+02, mean=8.81e-01

--- Setting up PyTorch Simulation ---
✓ Loaded HKL data: 27 reflections

--- Running CPU Simulation ---
✓ CPU simulation completed in 0.044 seconds
✓ PyTorch CPU stats: max=1.55e+02, mean=9.43e-01

--- Running C Code Simulation ---
✓ C code simulation completed in 0.081 seconds
✓ PyTorch vs C speedup: 1.83x

--- GPU Not Available ---
ℹ GPU simulation skipped

--- Creating Visualizations ---
✓ Saved: side_by_side_comparison.png
✓ Saved: difference_heatmap.png
✓ Saved: timing_comparison.png

--- Testing Differentiability ---
✓ Gradient check passed: True

--- Summary Statistics ---
Max absolute difference: 1.20e+01
Mean absolute difference: 6.21e-02
Relative error: 7.05e-02
PyTorch CPU time: 0.044s
C code time: 0.081s
PyTorch vs C speedup: 1.83x
Differentiable: ✓

=== Demo Complete ===
Generated files in: /Users/ollie/Documents/nanoBragg/reports
- side_by_side_comparison.png
- difference_heatmap.png
- timing_comparison.png
```
