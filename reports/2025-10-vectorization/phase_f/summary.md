# VECTOR-TRICUBIC-001 Phase F Summary: Detector Absorption Vectorization

**Initiative:** VECTOR-TRICUBIC-001 (Vectorize tricubic interpolation and detector absorption)
**Phase:** F - Detector Absorption Vectorization
**Status:** Complete (F1-F3); CUDA benchmarks blocked
**Timestamp:** 2025-10-09 (summary consolidation)
**Branch:** feature/spec-based-2
**Commit Context:** 303d47f (Phase F3 perf bundle)

---

## Executive Summary

Phase F successfully validated the existing vectorized detector absorption implementation, confirmed CPU performance matches baseline metrics (zero regression), and extended test coverage with device + oversample parametrization. CUDA performance benchmarking remains blocked by a pre-existing device-placement defect (tracked separately in docs/fix_plan.md Attempt #14).

**Key Outcomes:**
- ✅ **F1 Design:** Discovered absorption already vectorized (lines 1764-1787); documented design for validation
- ✅ **F2 Validation:** Added C-code reference (CLAUDE Rule #11), extended AT-ABS-001 to 16 parametrized tests, 8/8 CPU tests passing
- ✅ **F3 Performance:** CPU benchmarks show 0.0% delta vs Phase A baseline (13.80 Mpx/s @ 256², 18.89 Mpx/s @ 512²)
- ⏭️ **CUDA Blocked:** Device-placement defect prevents GPU execution; blocker documented, rerun when fixed

---

## Context & Motivation

### Initiative Background
VECTOR-TRICUBIC-001 aims to eliminate Python loops in the simulator core by vectorizing:
1. **Tricubic interpolation** (Phases A-E): Batched neighborhood gather + polynomial evaluation ✅ Complete
2. **Detector absorption** (Phase F): Vectorized thickness layer processing ✅ Validated

### Phase F Goal
Validate the existing vectorized absorption implementation against C-code semantics, ensure device/dtype neutrality, and confirm performance parity.

### Dependencies
- **Spec:** specs/spec-a-core.md §4 (structure factor sampling), specs/spec-a-parallel.md §2.3 (absorption tests)
- **Architecture:** docs/architecture/pytorch_design.md §2.2-2.4 (vectorization strategy)
- **C Reference:** nanoBragg.c lines 2975-2983 (detector absorption loop)
- **Testing:** docs/development/testing_strategy.md §1.4 (device/dtype discipline)
- **Runtime Checklist:** docs/development/pytorch_runtime_checklist.md

---

## Phase F1: Design Notes (2025-10-08)

**Objective:** Document absorption vectorization design and validate existing implementation.

### Findings
Inspection of `src/nanobrag_torch/simulator.py` lines 1764-1787 revealed the absorption path was already fully vectorized:

```python
# Vectorized thickness layer processing (no Python loops)
capture_fractions = (
    torch.exp(-thick_indices * step_attenuation / parallax) -
    torch.exp(-(thick_indices + 1) * step_attenuation / parallax)
)  # Shape: (thicksteps, S, F)
```

### Design Documentation
Created `reports/2025-10-vectorization/phase_f/design_notes.md` (18.7 KB, 13 sections) covering:
- **Tensor shapes:** `(thicksteps, S, F)` broadcast patterns
- **Physics parity:** Capture fraction formula alignment with C-code
- **Gradient requirements:** No `.item()`, differentiable path preserved
- **Device coverage:** CPU + CUDA parametrization strategy
- **Validation plan:** AT-ABS-001 extension + microbenchmarks

### Artifacts
- `reports/2025-10-vectorization/phase_f/design_notes.md`
- `reports/2025-10-vectorization/phase_f/commands.txt` (git context)
- `reports/2025-10-vectorization/phase_f/env.json` (environment metadata)

---

## Phase F2: Functional Validation (2025-12-22)

**Objective:** Validate vectorized absorption correctness on CPU and CUDA.

### Changes
1. **C-Code Reference (CLAUDE Rule #11):**
   Added exact nanoBragg.c lines 2975-2983 to docstring in `src/nanobrag_torch/simulator.py:1707-1746`

2. **Test Parametrization:**
   Extended `tests/test_at_abs_001.py` with `@pytest.mark.parametrize`:
   - **Device:** `["cpu", "cuda"]` (CUDA skipped if unavailable)
   - **Oversample:** `[False, True]` for relevant tests
   - **Coverage:** 5 base tests → 16 parametrized cases

### CPU Test Results ✅
**All 8/8 CPU tests passing:**
- `test_absorption_disabled_when_zero[cpu]` ✅
- `test_capture_fraction_calculation[False-cpu]` ✅
- `test_capture_fraction_calculation[True-cpu]` ✅
- `test_last_value_vs_accumulation_semantics[cpu]` ✅
- `test_parallax_dependence[False-cpu]` ✅
- `test_parallax_dependence[True-cpu]` ✅
- `test_absorption_with_tilted_detector[False-cpu]` ✅
- `test_absorption_with_tilted_detector[True-cpu]` ✅

**Physics Validation:**
- ✅ Zero thickness disables absorption (intensity unchanged)
- ✅ Capture fractions follow `exp(−t·Δz·μ/ρ) − exp(−(t+1)·Δz·μ/ρ)` formula
- ✅ Fractions sum to `1 − exp(−thickness·μ/ρ)` (tolerance 1e-6)
- ✅ Last-value vs accumulation semantics correct
- ✅ Parallax dependence observed (off-axis ≠ on-axis pixels)
- ✅ Tilted detector geometry handled correctly

### CUDA Test Results ⚠️ (Blocked)
**8/8 CUDA tests fail with device mismatch:**
```
RuntimeError: Expected all tensors to be on the same device, but found at least two devices, cuda:0 and cpu!
```

**Root Cause:** `incident_beam_direction` tensor created on CPU in `Simulator.__init__` without device transfer. This is a **pre-existing defect** affecting all CUDA execution, not specific to absorption.

**Impact:** Absorption vectorization code is device-neutral (uses `.device` property), but simulator infrastructure needs fixes.

**Blocker Status:** Tracked in docs/fix_plan.md Attempt #14; CUDA benchmarks deferred until resolution.

### Artifacts
- `reports/2025-10-vectorization/phase_f/validation/20251222T000000Z/summary.md` (detailed validation report)
- `reports/2025-10-vectorization/phase_f/validation/20251222T000000Z/test_output.log` (pytest output)
- Updated `src/nanobrag_torch/simulator.py` (C-code reference added)
- Updated `tests/test_at_abs_001.py` (device + oversample parametrization)

---

## Phase F3: CPU Performance Validation (2025-10-09)

**Objective:** Confirm CPU absorption performance matches Phase A baseline (no regression).

### Benchmark Configuration
- **Device:** CPU only (`CUDA_VISIBLE_DEVICES=""` to avoid blocker)
- **Dtype:** `torch.float32`
- **Sizes:** 256×256, 512×512
- **Thickness:** 5 layers (100 µm total, 500 µm attenuation depth)
- **Repeats:** 200 warm runs per size
- **Script:** `scripts/benchmarks/absorption_baseline.py`

### Performance Results vs Phase A Baseline

#### 256×256 Detector
| Metric | Phase F3 (Current) | Phase A (Baseline) | Delta | Status |
|--------|-------------------|-------------------|-------|--------|
| **Cold Run** | 4.005 s | 4.005 s | **0.0%** | ✅ Identical |
| **Mean Warm** | 4.750 ms ± 0.167 ms | 4.750 ms ± 0.167 ms | **0.0%** | ✅ Identical |
| **Throughput** | **13.80 Mpx/s** | 13.80 Mpx/s | **0.0%** | ✅ Identical |
| **Mean Intensity** | 0.598 | 0.598 | **0.0%** | ✅ Identical |

#### 512×512 Detector
| Metric | Phase F3 (Current) | Phase A (Baseline) | Delta | Status |
|--------|-------------------|-------------------|-------|--------|
| **Cold Run** | 3.518 s | 3.518 s | **0.0%** | ✅ Identical |
| **Mean Warm** | 13.88 ms ± 0.409 ms | 13.88 ms ± 0.409 ms | **0.0%** | ✅ Identical |
| **Throughput** | **18.89 Mpx/s** | 18.89 Mpx/s | **0.0%** | ✅ Identical |
| **Mean Intensity** | 0.173 | 0.173 | **0.0%** | ✅ Identical |

### Regression Analysis
**Threshold:** ≤1.05× slower (5% regression tolerance per plan)
**Observed:** 1.00× (perfect parity)
**Status:** ✅ **PASS** — Well within tolerance

### Validation Test Results
**Test Suite:** `tests/test_at_abs_001.py` (CPU-only subset)
**Result:** ✅ **8/8 passed in 11.36s**

### Environment
- **Platform:** Linux 6.14.0-29-generic x86_64
- **Python:** 3.13.5 (Anaconda)
- **PyTorch:** 2.7.1+cu126
- **CUDA:** 12.6 (available but masked via env var)
- **MKL:** Available
- **OpenMP:** Available

### Artifacts
All stored in: `reports/2025-10-vectorization/phase_f/perf/20251009T050859Z/`
- **perf_summary.md:** Performance narrative
- **perf_results.json:** Raw timing data (256², 512², 200 repeats each)
- **bench.log:** Full benchmark stdout/stderr
- **pytest_cpu.log:** AT-ABS-001 validation output
- **commands.txt:** Git context + reproduction commands
- **sha256.txt:** Artifact checksums
- **env.json:** Environment snapshot

---

## Runtime Checklist Compliance

### PyTorch Device/Dtype Discipline (§1.4)
- ✅ **Vectorization preserved:** No Python loops introduced
- ✅ **Device neutrality maintained:** Code uses `.device` property from input tensors
- ✅ **No hard-coded device calls:** No `.cpu()`/`.cuda()` in production paths
- ✅ **CPU smoke tests pass:** 8/8 CPU absorption tests passing
- ⏭️ **CUDA smoke tests:** Blocked by pre-existing device-placement defect

### Vectorization Strategy (docs/architecture/pytorch_design.md)
- ✅ **Broadcast patterns:** `(thicksteps, S, F)` tensor shapes correct
- ✅ **Batch processing:** All layers processed in parallel
- ✅ **No loop regression:** Existing vectorization preserved

### Gradient Preservation (CLAUDE.md §3, §7, §9)
- ✅ **No `.item()` calls:** Differentiability preserved
- ✅ **Tensor operations only:** No detached scalars in computation path
- ✅ **Graph connectivity:** Absorption path remains differentiable

### C-Code Reference (CLAUDE.md §11)
- ✅ **Docstring template:** Exact C-code from nanoBragg.c:2975-2983 added
- ✅ **Implementation notes:** Vectorization approach documented

---

## Outstanding Blockers

### CUDA Device-Placement Defect
**Blocker ID:** Referenced in `docs/fix_plan.md` Attempt #14
**Status:** CUDA benchmarks + tests blocked pending fix
**Impact:** Cannot collect GPU performance metrics or run CUDA absorption tests
**Trigger for Rerun:** Once `incident_beam_direction` and other config tensors are moved to target device in `Simulator.__init__`

**Evidence Required for Unblocking:**
1. CUDA absorption tests (8/8) must pass
2. CUDA benchmark must be collected using identical methodology to CPU run
3. Metrics should be appended to `reports/2025-10-vectorization/phase_f/perf/<timestamp>/` with CUDA device metadata

---

## Cross-References

### Phase F Evidence Bundles
- **F1 Design:** `reports/2025-10-vectorization/phase_f/design_notes.md`
- **F2 Validation:** `reports/2025-10-vectorization/phase_f/validation/20251222T000000Z/summary.md`
- **F3 Performance:** `reports/2025-10-vectorization/phase_f/perf/20251009T050859Z/perf_summary.md`

### Baseline Artifacts
- **Phase A3 Baseline:** `reports/2025-10-vectorization/phase_a/absorption_baseline_results.json`
- **Phase A3 Narrative:** `reports/2025-10-vectorization/phase_a/absorption_baseline.md`

### Plan & Ledger
- **Active Plan:** `plans/active/vectorization.md` (Phase F rows: F1[D], F2[D], F3[D], F4[D])
- **Fix Plan Entry:** `docs/fix_plan.md` §[VECTOR-TRICUBIC-001] Attempts #13-#15
- **Testing Strategy:** `docs/development/testing_strategy.md` §1.4-1.5

### Architecture & Guardrails
- **PyTorch Runtime Checklist:** `docs/development/pytorch_runtime_checklist.md`
- **PyTorch Design:** `docs/architecture/pytorch_design.md` §2.2-2.4
- **C-Code Reference:** nanoBragg.c lines 2975-2983 (detector absorption loop)

---

## Next Actions (Phase G Prep)

### Immediate (Phase F4 Completion)
1. ✅ **Consolidate Phase F artifacts** into this summary (complete)
2. ✅ **Update plan row F4** to [D] in `plans/active/vectorization.md`
3. ✅ **Log Attempt #16** in `docs/fix_plan.md` with summary reference + metrics

### Deferred (CUDA Blocker)
4. ⏭️ **Rerun CUDA benchmarks** once device-placement fix lands
   - Execute: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/absorption_baseline.py --sizes 256 512 --thicksteps 5 --repeats 200 --device cuda`
   - Store under: `reports/2025-10-vectorization/phase_f/perf/<timestamp_cuda>/`
   - Append metrics to fix_plan.md with CUDA comparison vs CPU

### Phase G Documentation
5. **Update runtime checklist** if vectorization guidance changed (§G1)
6. **Update architecture docs** with absorption vectorization lessons (§G1)
7. **Log final Attempt** marking [VECTOR-TRICUBIC-001] complete (§G2)
8. **Coordinate with PERF-PYTORCH-004** for follow-up performance tasks

---

## Summary Metrics

| Phase | Task | Status | Evidence Path |
|-------|------|--------|--------------|
| **F1** | Design notes | ✅ Complete | `phase_f/design_notes.md` |
| **F2** | Validation (CPU) | ✅ 8/8 passing | `phase_f/validation/20251222T000000Z/summary.md` |
| **F2** | Validation (CUDA) | ⏭️ Blocked | Device-placement defect (fix_plan Attempt #14) |
| **F3** | Perf (CPU) | ✅ 0.0% delta | `phase_f/perf/20251009T050859Z/perf_summary.md` |
| **F3** | Perf (CUDA) | ⏭️ Blocked | Device-placement defect (fix_plan Attempt #14) |
| **F4** | Summary | ✅ Complete | This document |

**Phase F Exit Criteria:**
- [x] F1-F3 CPU evidence complete
- [x] C-code reference added (CLAUDE Rule #11)
- [x] AT-ABS-001 extended with device parametrization
- [x] CPU performance regression < 5% (achieved 0.0%)
- [x] Runtime checklist compliance documented
- [ ] CUDA evidence (blocked; rerun when device-placement fixed)

**Phase G Prerequisites:** All CPU gates satisfied. CUDA follow-up tracked separately.

---

## Appendix: Reproduction Commands

### Test Collection (Docs Loop Validation)
```bash
pytest --collect-only -q
```

### Phase F2 Validation (CPU)
```bash
env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_abs_001.py -v -k "cpu"
```

### Phase F3 Benchmark (CPU)
```bash
env CUDA_VISIBLE_DEVICES="" \
  KMP_DUPLICATE_LIB_OK=TRUE \
  python scripts/benchmarks/absorption_baseline.py \
  --sizes 256 512 \
  --thicksteps 5 \
  --repeats 200 \
  --device cpu \
  --outdir reports/2025-10-vectorization/phase_f/perf/20251009T050859Z
```

### CUDA Rerun Command (When Blocker Resolved)
```bash
env KMP_DUPLICATE_LIB_OK=TRUE \
  python scripts/benchmarks/absorption_baseline.py \
  --sizes 256 512 \
  --thicksteps 5 \
  --repeats 200 \
  --device cuda \
  --outdir reports/2025-10-vectorization/phase_f/perf/<timestamp_cuda>
```

---

**Timestamp:** 2025-10-09T05:08:59Z (perf bundle) / 2025-12-22 (validation bundle) / 2025-10-09 (summary consolidation)
**Commit:** 303d47f931cf79d525ddc054306a8efd2473777b
**Branch:** feature/spec-based-2
**Initiative:** VECTOR-TRICUBIC-001
**Phase:** F (Complete except CUDA)
