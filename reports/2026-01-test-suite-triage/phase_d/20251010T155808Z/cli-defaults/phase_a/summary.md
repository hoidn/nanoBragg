# Phase A Summary: CLI vs Direct API Baseline Reconciliation

**Date:** 2025-10-10
**Initiative:** [CLI-DEFAULTS-001]
**Artifact Root:** `reports/2026-01-test-suite-triage/phase_d/20251010T155808Z/cli-defaults/phase_a/`

## Executive Summary

Phase A evidence capture confirms a **critical divergence** between CLI and direct API execution paths:

- **CLI Path** (`python -m nanobrag_torch`): Produces all-zero float image despite correct configuration
- **Direct API Path** (`debug_default_f.py`): Produces expected non-zero output with identical parameters

**Confidence:** 95% — The bug is definitively in the CLI orchestration layer, not in the underlying simulator or structure factor logic.

## Task Completion Status

| Task | Status | Artifacts |
|------|--------|-----------|
| A1 - CLI reproduction baseline | ✅ Complete | `cli_pytest/pytest.log`, `cli_pytest/commands.txt` |
| A2 - CLI configuration dump | ✅ Complete | `cli_pytest/config_dump.txt`, `cli_pytest/float_stats.txt` |
| A3 - Direct API control | ✅ Complete | `api_control/run.log` |
| A4 - Reconciliation summary | ✅ Complete | This document |

## Detailed Findings

### CLI Path Results

**Test:** `tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F`
**Command:**
```bash
python -m nanobrag_torch \
  -cell 100 100 100 90 90 90 \
  -default_F 100 \
  -detpixels 32 \
  -pixel 0.1 \
  -distance 100 \
  -lambda 6.2 \
  -N 5 \
  -floatfile output.bin \
  -intfile output.img
```

**Configuration (verified via -show_config):**
- Crystal: 100×100×100 Å cubic, N=5×5×5, default_F=100.0
- Detector: 32×32 pixels, 0.1mm pixel size, 100mm distance
- Beam: λ=6.2Å, fluence=1.26e+29 photons/m²
- Sources: 1 source
- Device: CPU, dtype: float32
- Oversample: 1 (auto-selected)

**Output Statistics:**
```
Shape: (32, 32)
Min: 0.0
Max: 0.0
Mean: 0.0
Sum: 0.0
Non-zero count: 0
```

**Result:** ❌ **FAILED** — All pixels zero, test assertion fails at line 59

### Direct API Path Results

**Script:** `debug_default_f.py`
**Configuration:** Identical parameters programmatically instantiated

**Output Statistics:**
```
Shape: torch.Size([32, 32])
Min: 7.749086e-07
Max: 1.546525e+02
Mean: 2.024670e+01
Non-zero pixels: 1024
```

**Result:** ✅ **SUCCESS** — Non-zero output, all pixels have intensity

### Configuration Parity Analysis

**Verified Identical:**
- ✅ Crystal cell parameters (100,100,100,90,90,90)
- ✅ default_F = 100.0
- ✅ N_cells = (5,5,5)
- ✅ Detector geometry (32×32, 0.1mm, 100mm distance)
- ✅ Wavelength (6.2Å)
- ✅ Fluence (1.26e+29 photons/m²)
- ✅ Device/dtype (CPU, float32)
- ✅ Oversample (1)
- ✅ HKL data (None in both cases)
- ✅ Structure factor fallback (verified: `Crystal.get_structure_factor()` returns default_F=100 when hkl_data=None)

**No configuration discrepancies detected.**

## Critical Observations

### 1. Structure Factor Logic is Correct
The direct API test explicitly verifies that `Crystal.get_structure_factor(h,k,l)` returns `tensor([100., 100., 100.])` when `hkl_data=None`. This confirms the fallback mechanism works.

### 2. Simulator Core Works
The direct API path successfully produces realistic diffraction intensity (max~155, mean~20) with the same crystal/detector/beam configuration. The physics engine is functional.

### 3. CLI Orchestration Suspect
The CLI entry point (`src/nanobrag_torch/__main__.py`) must be:
- Silently failing to pass configuration to simulator
- Overwriting/resetting critical parameters after parsing
- Triggering an error path that produces zero output without failing
- Introducing device/dtype mismatch despite config dump showing correct values

### 4. Exit Code Paradox
The CLI exits with code 0 (success) despite producing all-zero output. This suggests either:
- No validation of output sanity after simulation
- Silent fallback to zero on internal error
- Uninitialized output buffer being written

## Hypotheses for Phase B Investigation

### H1: Configuration Lost in CLI→Simulator Handoff (70% confidence)
The CLI parser correctly builds config objects (evidenced by `-show_config` dump), but the handoff to `Simulator.run()` may not preserve all parameters. Specifically, `default_F` or HKL-related state might not transfer.

**Test:** Instrument `Simulator.run()` entry point to log received crystal.config.default_F and crystal.hkl_data values.

### H2: Device/Dtype Mismatch Post-Config (15% confidence)
Despite both showing "cpu/float32", there may be a subtle device mismatch after simulator instantiation (e.g., detector pixels created on wrong device, causing silent zero-fill).

**Test:** Add device/dtype assertions at simulator entry and compare CLI vs API paths.

### H3: Silent Exception Swallowing (10% confidence)
The CLI may have a try/except block that catches simulator failures and produces zero output instead of propagating errors.

**Test:** Review `__main__.py` for bare `except:` blocks or generic exception handlers.

### H4: Output Buffer Initialization Bug (5% confidence)
The float image buffer might be pre-allocated and never written to due to early-exit condition.

**Test:** Check if CLI path ever reaches `intensity.numpy()` conversion and file write.

## Next Actions (Phase B Entry Criteria Met)

All Phase A tasks complete. Ready to proceed to Phase B:

1. **Execute B1-B2:** Generate callchain traces for CLI path using `prompts/callchain.md` with:
   - Analysis question: "Why does CLI execution produce all-zero output while direct API succeeds?"
   - Initiative ID: `cli-defaults-b1`
   - Scope hints: `['__main__.py', 'Simulator.run', 'Crystal.get_structure_factor', 'output writing']`
   - ROI: pixel (16,16) center of detector

2. **Execute B3:** Mirror callchain for direct API path (debug_default_f.py)

3. **Execute B4:** Compare traces to identify first divergent variable and prepare Phase C remediation blueprint

## Artifacts Inventory

```
reports/2026-01-test-suite-triage/phase_d/20251010T155808Z/cli-defaults/phase_a/
├── cli_pytest/
│   ├── pytest.log           # Full test output (FAILED)
│   ├── commands.txt          # Reproduction command and observations
│   ├── config_dump.txt       # CLI -show_config output
│   └── float_stats.txt       # NumPy stats of CLI output.bin
├── api_control/
│   └── run.log              # debug_default_f.py stdout (SUCCESS)
└── summary.md               # This document

Total size: ~15KB
```

## References

- Test source: `tests/test_at_cli_002.py:28-59`
- Control script: `debug_default_f.py`
- CLI entry point: `src/nanobrag_torch/__main__.py`
- Simulator: `src/nanobrag_torch/simulator.py`
- Crystal fallback logic: `src/nanobrag_torch/models/crystal.py:get_structure_factor()`

---
**Phase A Status:** ✅ **COMPLETE**
**Confidence in Findings:** 95%
**Blocking Issues:** None
**Ready for Phase B:** Yes
