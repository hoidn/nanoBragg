# Lambda Override Semantics & Steps Reconciliation Plan
## SOURCE-WEIGHT-001 Phase A0/E3 — Configuration Parity Design

**Date:** 2025-10-09T13:17:09Z
**Initiative:** [VECTOR-TRICUBIC-002] Phase A0 dependency gate
**Plan Reference:** `plans/active/vectorization.md`, `plans/active/source-weight-normalization.md`
**Evidence Base:** `reports/2025-11-source-weights/phase_e/20251009T130433Z/lambda_sweep/`

---

## Problem Statement

### Lambda Mismatch (Primary Blocker)

The lambda sweep experiment (20251009T130433Z) definitively proves PyTorch honours sourcefile wavelength values while the C reference uses CLI `-lambda`:

- **TC-D1 Fixture:** Sourcefile specifies `λ = 6.2 Å`, CLI provides `-lambda 0.9768`
- **PyTorch Behaviour:** Uses sourcefile `6.2 Å` → total sum 2.53e5
- **C Behaviour:** Uses CLI `0.9768 Å` → total sum ~1e3
- **Parity Delta:** 140–300× intensity inflation, correlation ≈−0.3 to +0.07

Per `specs/spec-a-core.md:150-190` (Sources section), the **weight** column is explicitly stated as "read but ignored." The spec is silent on wavelength column semantics, but the C code (`nanoBragg.c:2574-2576`) treats both weight AND wavelength as metadata-only, populating all source entries with the single CLI `-lambda` value.

### Steps Normalization Mismatch (Secondary)

Even after the wavelength fix, a residual steps difference remains:

- **PyTorch:** `steps = n_sources × mosaic × phi × oversample²`; when divergence is auto-selected, PyTorch counts only positive-weight sources → `steps = 2`
- **C:** Always includes zero-weight divergence placeholders → `steps = 4` for the same fixture

This delta affects final intensity scaling but is masked by the ~300× wavelength error until the primary issue is resolved.

---

## Spec Interpretation & Design Decision

### Option A (Rejected): Honour Sourcefile Wavelengths
**Rationale:** Would break parity with the C reference, invalidate all existing golden data, and contradict the C implementation's design choice to treat sourcefiles as divergence/dispersion grids anchored to a single CLI wavelength.

### Option B (Selected): Ignore Sourcefile Wavelengths, Enforce CLI Override
**Rationale:**
- Matches C semantics exactly
- Maintains spec's stated design principle that sourcefiles define sampling grids but do not override beam parameters
- Preserves golden data compatibility
- Aligns with implicit contract discovered through empirical testing

**Implementation Path:**
1. Modify sourcefile parsing in `src/nanobrag_torch/io/source.py` to:
   - Read wavelength column for metadata/validation
   - Override all `source_wavelengths` entries with CLI `-lambda` value
   - Emit `warnings.warn` when sourcefile wavelengths differ from CLI (stacklevel=2)
2. Update steps calculation logic in `src/nanobrag_torch/simulator.py` (or CLI entrypoint) to:
   - Count **all** sources (including zero-weight divergence entries) when computing `steps` denominator
   - Match C convention: `steps = sources_total × mosaic_domains × phi_steps × oversample²`
3. Add regression test `tests/test_at_src_003.py::TestSourcefileLambdaOverride` covering:
   - TC-E1: Sourcefile with divergent wavelengths → CLI wins
   - TC-E2: Warning emission when λ_file ≠ λ_CLI
   - TC-E3: Steps normalization parity (C ↔ PyTorch with multi-source fixture)

---

## File Touchpoints

### Primary Changes
1. **`src/nanobrag_torch/io/source.py`** (~lines 40-90)
   - Function: `parse_source_file`
   - Add CLI wavelength override after parsing
   - Insert warning emission when λ mismatch detected

2. **`src/nanobrag_torch/__main__.py`** (~lines 180-220)
   - CLI argument resolution: ensure `-lambda` is applied to all source entries
   - Pass `cli_lambda_A` into source parser or override post-parse

3. **`src/nanobrag_torch/config.py`** (optional, clarity)
   - Add docstring note to `BeamConfig.wavelength_A` clarifying precedence over sourcefile values

### Steps Reconciliation Changes
4. **`src/nanobrag_torch/simulator.py`** (~lines 250-280, initialization)
   - Update `steps` calculation to count all sources (including zero-weight) per C convention
   - Add comment referencing `nanoBragg.c:2700-2720` for traceability

### Testing
5. **`tests/test_at_src_003.py`** (new file)
   - Implement TC-E1, TC-E2, TC-E3 as parameterised pytest cases
   - Use CPU fixture (CUDA optional)
   - Acceptance: corr ≥0.999, |sum_ratio−1| ≤1e-3, warning capture via `pytest.warns`

### Documentation
6. **`specs/spec-a-core.md`** (~lines 150-190, Sources section)
   - Clarify: "Both weight and wavelength columns in sourcefiles are read but ignored. The CLI `-lambda` parameter is the sole authoritative wavelength source."
7. **`docs/development/c_to_pytorch_config_map.md`** (Beam parameters table)
   - Add precedence note: `-lambda` overrides sourcefile wavelength column
8. **`docs/architecture/pytorch_design.md`** (Sources subsection, if present)
   - Document CLI override behaviour

---

## C Reference Anchors

Per `golden_suite_generator/nanoBragg.c`:

**Wavelength Handling (lines 2574-2576):**
```c
// Read sourcefile wavelength column but override with CLI lambda:
source[source_I].lambda = lambda0;  // Always uses CLI parameter
```

**Steps Counting (lines 2700-2720):**
```c
// Always count total sources, including zero-weight entries:
steps = sources * mosaic_domains * phisteps * oversample * oversample;
```

---

## Acceptance Thresholds (Phase E3)

Once implementation lands, TC-D1/TC-D3 parity reruns MUST satisfy:

- **Correlation:** ≥0.999 (Pearson r between C and PyTorch float images)
- **Sum Ratio:** |sum_C / sum_Py − 1| ≤ 1e-3 (0.1% tolerance)
- **Warning Emission:** `pytest.warns(UserWarning, match="sourcefile wavelength")` for TC-E2
- **Steps Parity:** PyTorch `steps` matches C `steps` exactly when same fixture used

---

## Implementation Sequence (for Ralph)

1. **Read Evidence:** Review `reports/2025-11-source-weights/phase_e/20251009T130433Z/lambda_sweep/summary.md`
2. **Implement Lambda Override:**
   - Edit `src/nanobrag_torch/io/source.py` (parse function)
   - Edit `src/nanobrag_torch/__main__.py` (CLI resolution)
   - Add warning logic (stacklevel=2)
3. **Fix Steps Calculation:**
   - Edit `src/nanobrag_torch/simulator.py` (initialization)
   - Count all sources per C convention
4. **Add Regression Tests:**
   - Create `tests/test_at_src_003.py` with TC-E1/E2/E3
   - Run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_src_003.py -v`
5. **Rerun Parity:**
   - Execute TC-D1/TC-D3 via:
     ```bash
     NB_RUN_PARALLEL=1 KMP_DUPLICATE_LIB_OK=TRUE \
       python scripts/cli/run_weighted_source_parity.py \
       --oversample 1 \
       --outdir reports/2025-11-source-weights/phase_e/<NEW_STAMP>/
     ```
   - Capture correlation.txt, sum_ratio.txt, commands.txt, simulator diagnostics, env.json
6. **Update Documentation:**
   - Edit spec (`specs/spec-a-core.md`)
   - Update config map (`docs/development/c_to_pytorch_config_map.md`)
7. **Log Attempt:**
   - Append to `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` Attempts History with metrics and artifact paths

---

## Blocking Dependencies

**Before implementation:**
- None; evidence complete, design agreed (Option B)

**Before claiming Phase E3 closure:**
- TC-E1/E2/E3 regression tests passing
- TC-D1/TC-D3 parity metrics meet thresholds (corr ≥0.999, |sum_ratio−1| ≤1e-3)
- Docs updated per touchpoints above

**Downstream unblocks:**
- `[VECTOR-GAPS-002]` Phase B1 profiler capture can proceed once correlation ≥0.99
- `[VECTOR-TRICUBIC-002]` Phase A1 can advance to A2/A3

---

## Risk Mitigation

- **Protected Assets:** No files in `docs/index.md` are modified beyond documented touchpoints
- **Device/Dtype Neutrality:** Changes are CPU-focused (source parsing); no new tensor ops introduced
- **Differentiability:** No gradient-critical paths touched (source metadata only)
- **Vectorization:** No loops introduced; source override is O(n_sources) scalar list operation
- **Regression Coverage:** New tests prevent future drift from C semantics

---

## Artifact Storage Convention

- **This Design Note:** `reports/2025-11-source-weights/phase_e/20251009T131709Z/lambda_semantics.md`
- **Commands:** `reports/2025-11-source-weights/phase_e/20251009T131709Z/commands.txt` (to be created by implementation loop)
- **Test Collection:** `reports/2025-11-source-weights/phase_e/20251009T131709Z/collect.log` (archived)
- **Post-Fix Parity:** `reports/2025-11-source-weights/phase_e/<NEW_STAMP>/` (after implementation)

---

## References

- **Lambda Sweep Evidence:** `reports/2025-11-source-weights/phase_e/20251009T130433Z/lambda_sweep/`
- **Spec Source:** `specs/spec-a-core.md:150-190`
- **C Reference:** `golden_suite_generator/nanoBragg.c:2574-2576, 2700-2720`
- **Config Map:** `docs/development/c_to_pytorch_config_map.md`
- **Testing Strategy:** `docs/development/testing_strategy.md` §2.5
- **Plan Context:** `plans/active/source-weight-normalization.md` Phase E, `plans/active/vectorization.md` Phase A
