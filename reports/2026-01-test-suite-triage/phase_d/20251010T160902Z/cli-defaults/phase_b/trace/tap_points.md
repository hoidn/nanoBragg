# Numeric Tap Points for CLI vs API Divergence Analysis

**Initiative:** CLI-DEFAULTS-001 Phase B
**Purpose:** Identify first divergent variable between CLI and API execution paths
**Timestamp:** 2025-10-10T16:09:02Z

## Recommended Tap Sequence

These taps should be instrumented in both CLI and API paths to identify the first point of divergence.

### Tap 1: Config Dictionary (Post-Parsing)
- **Key:** `config_default_F`
- **Purpose:** Verify CLI flag parsing captured default_F correctly
- **Owning Function:** `parse_and_validate_args()`
- **File:Line:** `src/nanobrag_torch/__main__.py:444`
- **Expected Value:** `100.0`
- **Units:** electrons (structure factor magnitude)
- **Instrumentation:**
  ```python
  print(f"TAP1: config['default_F'] = {config.get('default_F')}")
  ```

### Tap 2: CrystalConfig Construction
- **Key:** `crystal_config_default_F`
- **Purpose:** Verify default_F passed to CrystalConfig constructor
- **Owning Function:** `main()`
- **File:Line:** `src/nanobrag_torch/__main__.py:864`
- **Expected Value:** `100.0`
- **Units:** electrons
- **Instrumentation:**
  ```python
  print(f"TAP2: CrystalConfig default_F = {crystal_config.default_F}")
  ```

### Tap 3: Crystal Instance Initialization
- **Key:** `crystal_instance_default_F`
- **Purpose:** Verify Crystal object receives and stores default_F
- **Owning Function:** `Crystal.__init__()`
- **File:Line:** `src/nanobrag_torch/models/crystal.py:61` (approx)
- **Expected Value:** `100.0`
- **Units:** electrons
- **Instrumentation:**
  ```python
  print(f"TAP3: Crystal.config.default_F = {self.config.default_F}, hkl_data is None = {self.hkl_data is None}")
  ```

### Tap 4: HKL Data Assignment
- **Key:** `hkl_data_post_assignment`
- **Purpose:** Check if HKL data assignment affects default_F or Crystal state
- **Owning Function:** `main()`
- **File:Line:** `src/nanobrag_torch/__main__.py:1095`
- **Expected Value:** `hkl_data=None`, `default_F=100.0` still preserved
- **Units:** N/A (state check)
- **Instrumentation:**
  ```python
  print(f"TAP4: After HKL assignment - crystal.hkl_data is None = {crystal.hkl_data is None}, crystal.config.default_F = {crystal.config.default_F}")
  ```

### Tap 5: Structure Factor Lookup (First Call)
- **Key:** `structure_factor_return`
- **Purpose:** Verify get_structure_factor() returns default_F when hkl_data is None
- **Owning Function:** `Crystal.get_structure_factor()`
- **File:Line:** `src/nanobrag_torch/models/crystal.py:227`
- **Expected Value:** Tensor filled with `100.0`
- **Units:** electrons
- **Instrumentation:**
  ```python
  if self.hkl_data is None:
      result = torch.full_like(h, float(self.config.default_F), device=self.device, dtype=self.dtype)
      print(f"TAP5: get_structure_factor returning default_F={self.config.default_F}, result shape={result.shape}, device={result.device}, dtype={result.dtype}")
      return result
  ```

### Tap 6: Simulator Intensity Accumulation
- **Key:** `intensity_accumulator`
- **Purpose:** Check if computed intensities are being accumulated
- **Owning Function:** `Simulator.run()` or `compute_physics_for_position()`
- **File:Line:** `src/nanobrag_torch/simulator.py:688` (approx, where physics is called)
- **Expected Value:** Non-zero tensor
- **Units:** photons (or dimensionless before scaling)
- **Instrumentation:**
  ```python
  print(f"TAP6: intensity stats - min={intensity.min().item():.3e}, max={intensity.max().item():.3e}, sum={intensity.sum().item():.3e}")
  ```

### Tap 7: Final Output (Pre-Write)
- **Key:** `final_intensity_pre_write`
- **Purpose:** Verify intensity tensor before writing to floatfile
- **Owning Function:** `main()`
- **File:Line:** `src/nanobrag_torch/__main__.py:1149`
- **Expected Value:** Non-zero tensor matching Tap 6
- **Units:** photons
- **Instrumentation:**
  ```python
  print(f"TAP7: Pre-write intensity - shape={intensity.shape}, min={intensity.min().item():.3e}, max={intensity.max().item():.3e}")
  ```

## Tap Execution Strategy

1. **Add all 7 taps to both CLI and API paths**
2. **Run minimal test case:** 32×32 detector, default_F=100, no HKL file
3. **Compare tap outputs side-by-side:**
   - CLI: `python -m nanobrag_torch -cell 100 100 100 90 90 90 -default_F 100 -detpixels 32 -pixel 0.1 -distance 100 -lambda 6.2 -N 5 -floatfile /tmp/cli_tap.bin 2>&1 | grep "^TAP"`
   - API: `python debug_default_f.py 2>&1 | grep "^TAP"`
4. **Identify first divergent tap** where values differ
5. **Focus instrumentation** on the code between the last matching tap and the first divergent tap

## Expected Divergence Hypotheses

Based on static analysis, the most likely divergence points are:

1. **Tap 4 divergence** (HIGH): HKL assignment may corrupt Crystal state in CLI path
2. **Tap 5 divergence** (MEDIUM): Structure factor lookup may fail to return default_F in CLI
3. **Tap 6 divergence** (LOW): Physics computation may be correct but accumulation broken

If all taps match up to Tap 7, the bug is in the file writing logic (very unlikely given Phase A evidence).

## Artifact Storage

After running tap comparison:
- CLI tap output: `reports/2026-01-test-suite-triage/phase_d/20251010T160902Z/cli-defaults/phase_b/trace/cli_taps.log`
- API tap output: `reports/2026-01-test-suite-triage/phase_d/20251010T160902Z/cli-defaults/phase_b/trace/api_taps.log`
- Side-by-side diff: `reports/2026-01-test-suite-triage/phase_d/20251010T160902Z/cli-defaults/phase_b/trace/tap_diff.txt`
