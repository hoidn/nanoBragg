## SOURCE-WEIGHT-001 — Correct weighted source normalization (Archive)

**Initiative ID:** SOURCE-WEIGHT-001
**Status:** Complete
**Dates:** 2025-11-17 through 2025-10-10
**Owner:** galph/ralph
**Normative References:**
- `specs/spec-a-core.md` §4 (Sources, Divergence & Dispersion), lines 146-160
- `docs/architecture/pytorch_design.md` §1.1.5 (Source Weighting & Steps Normalization)
- `docs/development/pytorch_runtime_checklist.md` item #4
- `golden_suite_generator/nanoBragg.c` lines 2570-2720 (source ingestion loop)

### Context

This initiative addressed a perceived C↔PyTorch divergence in source weighting behavior. Initial investigations (Phases A–E) revealed a sum_ratio≈328 bias, leading to the hypothesis that the C code weighted sources while PyTorch treated them equally. Phase H parity reassessment and C-code inspection conclusively demonstrated that **both implementations ignore source weights per spec**, and near-perfect parity (correlation ≥0.999, |sum_ratio−1| ≤5e-3) was achieved once fixture artifacts (comment parsing bugs) were eliminated.

### Initiative Phases — Summary

#### Phase A — Bias Capture
**Artifacts:** `reports/2025-11-source-weights/phase_a/20251009T071821Z/`
**Outcome:** Baseline sum_ratio≈3.28e2 documented; established reproduction commands and traced bias to test/fixture configuration mismatch.

#### Phase B — Spec Confirmation & Callchain
**Artifacts:** `reports/2025-11-source-weights/phase_b/20251009T083515Z/`
**Outcome:** Parallel trace analysis confirmed spec compliance (`specs/spec-a-core.md:151-153`). Both implementations use equal weighting; weight column ignored by design.

#### Phase C — Implementation Guards
**Commits:** 321c91e, dffea55
**Code:** `src/nanobrag_torch/simulator.py:399-423`
**Outcome:** Explicit guards and warnings added to enforce spec-mandated equal weighting; test coverage in `tests/test_cli_scaling.py` expanded.

#### Phase D — Divergence Design & Harness
**Artifacts:** `reports/2025-11-source-weights/phase_d/{20251009T102319Z,20251009T104310Z}/`
**Outcome:** CLI harness drafted; options analysis documented; test selector inventory completed.

#### Phase E — Ledger Propagation
**Artifacts:** `reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md` (superseded)
**Outcome:** Initial memo classified C-PARITY-001 as a divergence. Later superseded by Phase H reassessment.

#### Phase F — Test Realignment
**Artifacts:** `reports/2025-11-source-weights/phase_f/20251009T203823Z/test_plan.md`
**Outcome:** Spec-first pytest suite (`TestSourceWeights*`) landed; acceptance criteria defined.

#### Phase G — Parity Evidence Recovery
**Artifacts:** `reports/2025-11-source-weights/phase_g/{20251009T230946Z,20251009T232321Z,20251009T235016Z,20251010T000742Z}/`
**Key Deliverable:** Sanitized fixture (`fixtures/two_sources_nocomments.txt`, SHA256: f23e1b1e60412c5378ee197542e0aca1ffc658198edd4e9584a3dffb57330c44) eliminating C comment parsing bug
**Metrics:** correlation=0.9999886, sum_ratio=1.0038 (both within spec thresholds)
**Outcome:** Clean parity bundle proving C and PyTorch both use equal weighting. Segfault guardrails documented (`-interpolate 0` required when no HKL fixture provided).

#### Phase H — Parity Reassessment & Test Updates
**Artifacts:** `reports/2025-11-source-weights/phase_h/20251010T002324Z/parity_reassessment.md` (authoritative memo)
**Key Findings:**
- C source ingestion loop (`nanoBragg.c:2570-2720`) confirmed to ignore weight column
- Legacy C-PARITY-001 classification corrected; now scoped to φ-carryover only
- Test expectations updated: `tests/test_cli_scaling.py:585-692` now expects PASS with correlation ≥0.999, |sum_ratio−1| ≤5e-3
**Outcome:** Parity memo supersedes Phase E decision; bug ledger and dependent plans updated.

#### Phase I — Documentation & Downstream Unblocks
**Phase I1 (Complete):** `reports/2025-11-source-weights/phase_i/20251010T005717Z/`
- Updated `docs/architecture/pytorch_design.md` §1.1.5 (Source Weighting & Steps Normalization)
- Updated `docs/development/pytorch_runtime_checklist.md` item #4 (Equal weighting mandate)
- Updated `specs/spec-a-core.md:151-155` (parenthetical parity citation)

**Phase I2 (Complete):** `reports/2025-11-source-weights/phase_i/20251010T011249Z/`
- Updated dependent plans: `plans/active/vectorization.md` Phase A2, `plans/active/vectorization-gap-audit.md` Phase B1
- Updated ledger entries: `[VECTOR-TRICUBIC-002]`, `[VECTOR-GAPS-002]`, `[PERF-PYTORCH-004]` now cite parity memo and runtime checklist

**Phase I3 (This Archive):**
- Initiative archival complete
- Residual risks documented below

### Final Parity Metrics (Normative)

**Test:** `tests/test_cli_scaling.py::TestSourceWeightsDivergence::test_c_divergence_reference`
**Canonical Commands:**
- C: `"$NB_C_BIN" -mat A.mat -floatfile c_weight.bin -sourcefile reports/2025-11-source-weights/fixtures/two_sources_nocomments.txt -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -nonoise -nointerpolate`
- PyTorch: `KMP_DUPLICATE_LIB_OK=TRUE nanoBragg -mat A.mat -floatfile py_weight.bin -sourcefile reports/2025-11-source-weights/fixtures/two_sources_nocomments.txt -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -nonoise -nointerpolate`

**Metrics (Phase G Attempt #35, 20251010T000742Z):**
- Correlation: 0.9999886 (threshold: ≥0.999)
- Sum Ratio: 1.0038 (threshold: |ratio−1| ≤5e-3)
- C Sum: 125522.62
- PyTorch Sum: 126004.64

### Residual Risks & Known Issues

1. **[C-SOURCEFILE-001] C comment parsing bug:** C code generates ghost sources when sourcefile contains comment lines. Workaround: use comment-free fixtures (e.g., `two_sources_nocomments.txt`). Tracked in separate ledger entry.

2. **Tricubic interpolation segfault:** C code segfaults on negative Fhkl indices when interpolation auto-enables without HKL data. Guardrail: always pass `-nointerpolate` or provide a valid HKL fixture when using sourcefiles.

3. **Dependent initiatives:** Vectorization (VECTOR-TRICUBIC-002, VECTOR-GAPS-002) and performance profiling (PERF-PYTORCH-004) were temporarily blocked pending this closure. All unblocked as of Phase I2 completion.

### Cross-References

- **Spec:** `specs/spec-a-core.md` lines 146-160 (normative source weighting statement)
- **Architecture:** `docs/architecture/pytorch_design.md` §1.1.5
- **Runtime Checklist:** `docs/development/pytorch_runtime_checklist.md` item #4
- **Parity Memo:** `reports/2025-11-source-weights/phase_h/20251010T002324Z/parity_reassessment.md`
- **Bug Ledger:** `docs/bugs/verified_c_bugs.md` (C-PARITY-001 scoped to φ-carryover)
- **Active Plans:** `plans/active/vectorization.md`, `plans/active/vectorization-gap-audit.md`
- **Ledger Entry:** `docs/fix_plan.md` `[SOURCE-WEIGHT-001]` (now marked `done`)

### Lessons Learned

1. **Fixture hygiene matters:** Comment parsing bugs in the C code introduced false parity divergences. Always use sanitized, minimal test fixtures.

2. **Parity reassessment over assumption:** Early classification (Phase E) incorrectly assumed C code weighted sources. Direct C-code inspection (Phase H) proved both implementations follow the spec.

3. **Trace-driven debugging is essential:** Parallel traces (Phase B) and targeted pytest selectors (Phase G) enabled rapid root cause isolation.

4. **Documentation as contract:** Explicit references to spec sections, C-code line ranges, and parity thresholds in permanent docs (Phase I1) ensure future work stays aligned.

### Exit Criteria Met

- ✅ Parity thresholds achieved (correlation ≥0.999, |sum_ratio−1| ≤5e-3)
- ✅ Permanent docs updated with normative citations
- ✅ Dependent plans unblocked
- ✅ Residual risks documented and cross-linked
- ✅ Archive summary complete
- ✅ Ledger entry marked `done`

**Archive Date:** 2025-10-10
**Archived By:** ralph loop #270
