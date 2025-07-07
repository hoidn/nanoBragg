# Agent Implementation Checklist: `simple_cubic` Image Reproduction (v3, Final)

**Overall Goal:** To reproduce the entire `simple_cubic` golden test case image with the new PyTorch code, demonstrating correctness, performance potential, and differentiability.

**Instructions:**
1. This checklist is the sole focus for the first week. All other plans are deferred.
2. Follow the 5-day micro-plan. Update the `State` for each item as you progress.

| ID | Task Description | State | How/Why & API Guidance |
| :--- | :--- | :--- | :--- |
| **Day 0: Scaffolding & Planning** |
| 0.A | **Execute Phase 0 Setup** | `[✓]` | **Why:** To create the project structure, dev environment, and generate the Golden Suite. <br> **Action:** <br> 1. Create `requirements.txt` with `torch>=2.3`, `fabio`, `numpy`, `pytest`, `matplotlib`. <br> 2. Create `.gitignore` and `pyproject.toml` (with `black` and `ruff` configs). <br> 3. Create the full directory structure from the previous plan. <br> 4. Run `pip install -r requirements.txt`. <br> 5. Run `make -C golden_suite_generator/ all` to generate the Golden Suite. <br> 6. **Verify:** `ruff check .` and `black . --check` should show no diffs. |
| 0.B | **Create a Detailed Plan** | `[✓]` | **Why:** To formalize this checklist as the plan of record. <br> **Action:** Create `PLAN_first_win.md` containing this checklist. |
| **Day 1: Geometry Utilities** |
| 1.A | **Implement Core Geometry Functions** | `[ ]` | **Why:** These are the foundational building blocks for all geometric calculations. <br> **How:** In `src/nanobrag_torch/utils/geometry.py`, implement `dot_product`, `cross_product`, `unitize`, and `rotate_axis`. <br> **API Notes:** <br> - All ops must be vectorized and broadcastable over leading dimensions. <br> - `rotate_axis` must internally `unitize` the axis vector to ensure stability. <br> - Use `torch.float64` for all calculations. |
| 1.B | **Write Unit Tests** | `[ ]` | **Why:** To verify each function against known values. <br> **How:** In `tests/test_suite.py`: <br> 1. Create a helper `assert_tensor_close(a, b)` that wraps `torch.allclose` and also asserts `a.dtype == b.dtype`. <br> 2. Add tests for each geometry function using this helper. |
| **Day 2: Minimal Detector & Crystal Models** |
| 2.A | **Implement Minimal `Detector` Class** | `[ ]` | **Why:** To generate the full 2D grid of pixel coordinates. <br> **How:** In `src/nanobrag_torch/models/detector.py`, implement `__init__` and `get_pixel_coords()`. <br> **API Notes:** <br> - Hard-code the `simple_cubic` geometry. <br> - Return pixel coordinates in **millimeters (mm)** as a tensor of shape `(spixels, fpixels, 3)`. |
| 2.B | **Implement Minimal `Crystal` Class** | `[ ]` | **Why:** To provide the reciprocal lattice and structure factors. <br> **How:** In `src/nanobrag_torch/models/crystal.py`: <br> 1. Implement `__init__` to calculate reciprocal vectors from the `simple_cubic` cell. <br> 2. Implement a minimal `load_hkl` that reads `simple_cubic.hkl` into a **tensor** of shape `(N_reflections, 4)` for `h,k,l,F`. |
| **Day 3: Simulator v0.1** |
| 3.A | **Implement `sincg`** | `[ ]` | **Why:** To unblock the main simulator implementation. <br> **How:** In `src/nanobrag_torch/utils/physics.py`, implement `sincg(x, N)`. <br> **API:** `torch.where(x == 0, N, torch.sin(pi * N * x) / torch.sin(pi * x))` |
| 3.B | **Implement Minimal `Simulator.run()`** | `[ ]` | **Why:** To create the core forward model. <br> **How:** In `src/nanobrag_torch/simulator.py`: <br> 1. Propagate `device` and `dtype` to all created tensors. <br> 2. Wrap the main calculation with `with torch.no_grad():` for initial timing runs. <br> 3. Broadcast `pixel_coords` and `incident_vector` to calculate the `scattering_vector` tensor. <br> 4. Calculate `h,k,l` via dot products. <br> 5. Look up `F_cell` from the HKL tensor. <br> 6. Calculate `F_latt` using `sincg`. <br> 7. Compute `Intensity = (F_cell * F_latt)**2`. <br> 8. Sum over the (size-1) source dimension. Return the final 2D image tensor. |
| **Day 4: Validation Harness** |
| 4.A | **Write Integration Test** | `[ ]` | **Why:** To programmatically verify correctness against the golden image. <br> **How:** In `tests/test_suite.py`, create `test_simple_cubic_reproduction()`: <br> 1. Set `torch.manual_seed(0)` for reproducibility. <br> 2. Load `tests/golden_data/simple_cubic.img` using `fabio`. <br> 3. Run the PyTorch `Simulator` for the `simple_cubic` case. <br> 4. Assert `torch.allclose(pytorch_image, golden_image, rtol=1e-5, atol=1e-6)`. <br> 5. Assert `pytorch_image.dtype == torch.float64`. |
| **Day 5: Demo Artifacts & Presentation** |
| 5.A | **Create Demo Script/Notebook** | `[ ]` | **Why:** To generate all the visual assets for the PI demo. <br> **Path:** `reports/first_win_demo.py` or `.ipynb`. <br> **How:** The script must: <br> 1. Set `torch.manual_seed(0)`. <br> 2. Run sim on CPU. For GPU, use `torch.cuda.synchronize()` before and after the run for accurate timing. Print timings. <br> 3. Save the PyTorch image using `plt.imshow(image.cpu().numpy(), cmap='inferno')`. <br> 4. Compute a diff heatmap using `np.log1p(np.abs(golden - pytorch))` to make discrepancies visible. Save the plot. <br> 5. Run `torch.autograd.gradcheck` on a **3x3 cropped version** of the simulation with respect to `cell_a` to keep memory usage low. Print the result. |
| 5.B | **Prepare Summary Document** | `[ ]` | **Why:** To create the final presentation asset. <br> **Path:** `reports/first_win_summary.md`. <br> **How:** Create a short Markdown file containing: <br> - The side-by-side images and the diff heatmap. <br> - The timing comparison table (CPU vs. GPU). <br> - The `gradcheck` output confirming success. <br> - The "talking point" bullets from the external review. |

## Progress Notes
- **Day 0 Complete**: ✅ Project scaffolding, requirements, configs, and Golden Suite generation completed
- **Next**: Day 1 - Implement core geometry functions and unit tests