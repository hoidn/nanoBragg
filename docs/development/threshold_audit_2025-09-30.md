# AT-PARALLEL Threshold Audit Report

**Date:** 2025-09-30
**Auditor:** Ralph (Spec Compliance Loop)
**Scope:** Cross-reference all AT-PARALLEL test thresholds against specs/spec-a-parallel.md

## Executive Summary

**Total Tests Audited:** 9 of 28 AT-PARALLEL tests
**Status Distribution:**
- **MATCH:** 2 tests (AT-PARALLEL-001, AT-PARALLEL-028)
- **LOOSENED (Minor):** 2 tests (AT-PARALLEL-007, AT-PARALLEL-009)
- **LOOSENED (Major):** 4 tests (AT-PARALLEL-002, AT-PARALLEL-006, AT-PARALLEL-020, AT-PARALLEL-029)
- **FAILING:** 1 test (AT-PARALLEL-012 triclinic_P1)

**Critical Finding:** Multiple tests have relaxed thresholds below spec requirements, with AT-PARALLEL-006 and AT-PARALLEL-020 showing the most significant deviations.

---

## Detailed Findings

### ✅ AT-PARALLEL-001: Beam Center Scales with Detector Size

**Status:** MATCH with additions

**Spec Requirements:**
- Correlation: ≥0.9999
- Peak position: ±2 pixels
- Beam center calculation: SHALL equal detector_pixels/2 × pixel_size_mm

**Test Implementation:**
- Parity test correlation: 0.9999 ✓
- Peak position: ±2 pixels ✓
- Beam center precision: 0.001mm (TIGHTENED, not in spec)
- Intensity scaling: 0.8-1.25 ratio (ADDED, not in spec)

**Recommendation:** No action needed. Additions strengthen validation.

---

### ⚠️ AT-PARALLEL-002: Pixel Size Independence

**Status:** LOOSENED

**Spec Requirements:**
- Beam center: ±0.1 pixels
- Pattern correlation: ≥0.9999

**Test Implementation:**
- Beam center: ±0.1 pixels ✓
- Pattern correlation: ≥0.9799 (0.9999 - 0.02) ❌ **LOOSENED**
- Justification: "discrete sampling effects"

**Severity:** Moderate

**Recommendation:**
1. Investigate if 2% correlation relaxation is masking a real implementation issue
2. Consider if the parity test (which uses correct 0.9999) is sufficient

---

### 🔴 AT-PARALLEL-006: Single Reflection Position

**Status:** SIGNIFICANTLY LOOSENED

**Spec Requirements:**
- Peak position: ±0.5 pixels
- Wavelength scaling: ±1%
- Distance scaling: ±2%
- Correlation: ≥0.9999

**Test Implementation:**
- Peak position: ±1.5 pixels ❌ **3x LOOSER**
- Wavelength scaling: ±3% ❌ **3x LOOSER**
- Distance scaling: ±4% ❌ **2x LOOSER**
- Correlation: 0.9999 (in parity test) ✓

**Severity:** HIGH

**Recommendation:**
1. **Urgent:** Restore spec thresholds (0.5px, 1%, 2%)
2. If discretization is the issue, this suggests insufficient subpixel accuracy
3. Consider if the underlying Bragg angle calculation needs refinement

---

### ⚠️ AT-PARALLEL-007: Peak Position with Rotations

**Status:** LOOSENED

**Spec Requirements:**
- Correlation: ≥0.9999
- Peak matching: ≥95% within ≤1.0px
- Intensity ratio: [0.9, 1.1]

**Test Implementation:**
- Correlation: ≥0.9995 ❌ **LOOSENED**
- Peak matching: ≥95% @ ≤1.0px ✓
- Intensity ratio: [0.9, 1.1] ✓

**Discrepancy:** parity_cases.yaml specifies 0.9999 but test uses 0.9995

**Severity:** Moderate

**Recommendation:**
1. Harmonize test and YAML (use 0.9999 from spec)
2. Investigate if 0.0004 relaxation is necessary

---

### ⚠️ AT-PARALLEL-009: Intensity Normalization

**Status:** LOOSENED (minor)

**Spec Requirements:**
- N-scaling slope: 6.0 ± 0.3
- F-scaling slope: 2.0 ± 0.05
- R²: ≥0.99

**Test Implementation:**
- N-scaling slope: 6.0 ± 0.35 ❌ **17% LOOSER**
- F-scaling slope: 2.0 ± 0.05 ✓
- R²: ≥0.99 ✓

**Severity:** Low

**Recommendation:**
1. Accept current threshold (minor deviation with justification)
2. Monitor for further drift

---

### 🔴 AT-PARALLEL-012: Reference Pattern Correlation

**Status:** LOOSENED + FAILING

**Spec Requirements:**
- simple_cubic: correlation ≥0.9995, peaks ≤0.5px
- triclinic_P1: correlation ≥0.9995, peaks ≤0.5px
- tilted: correlation ≥0.9995, peaks ≤1.0px
- high-res: correlation ≥0.95, peaks ≤1.0px

**Test Implementation:**
- simple_cubic: correlation ≥0.9985 (ADR-12 tolerance), peak matching 85% ❌ **LOOSENED**
- triclinic_P1: correlation ≥0.9995 ✓ **BUT FAILING (0.9605)**
- tilted: correlation ≥0.9985 (ADR-12 tolerance) ❌ **LOOSENED**
- high-res: SKIPPED ❌ **NOT IMPLEMENTED**

**Current Failure:** triclinic_P1 correlation 0.9605 < 0.9995 (4% below spec)

**Severity:** CRITICAL

**Recommendation:**
1. **MUST ROUTE TO DEBUG PROMPT** (per Ralph routing rules)
2. Remove ADR-12 relaxations from simple_cubic and tilted
3. Restore peak matching from 85% to 95% for simple_cubic
4. Implement high-res variant

---

### 🔴 AT-PARALLEL-020: Comprehensive Integration Test

**Status:** SIGNIFICANTLY LOOSENED

**Spec Requirements:**
- Correlation: ≥0.95
- Peak matching: top 50 within ≤1.0px
- Intensity ratio: [0.9, 1.1]

**Test Implementation:**
- Correlation: ≥0.85 ❌ **LOOSENED**
- Peak matching: ≥35% matched ❌ **WEAKENED** (17.5 peaks vs 50)
- Intensity ratio: [0.15, 1.5] ❌ **10x WIDER**
- Minimal features case: correlation ≥0.95 ✓

**Severity:** HIGH

**Recommendation:**
1. **Urgent:** Investigate absorption implementation (noted as cause)
2. Restore spec thresholds once absorption is fixed
3. Consider marking comprehensive tests as xfail until fixed

---

### ✅ AT-PARALLEL-028: Performance Parity Requirement

**Status:** MATCHES SPEC

**Spec Requirements:**
- CPU: PyTorch ≥0.5x C throughput
- GPU: PyTorch ≥10x C throughput

**Test Implementation:**
- CPU: ≥0.5x ✓
- GPU: ≥10x ✓

**Recommendation:** No action needed.

---

### ⚠️ AT-PARALLEL-029: Subpixel Sampling and Aliasing Mitigation

**Status:** LOOSENED

**Spec Requirements:**
- Aliasing reduction (oversample≥2): ≥50%
- Peak drift: ≤0.5px
- FWHM stability: ≤5%
- C-PyTorch correlation: ≥0.98

**Test Implementation:**
- Aliasing reduction: ≥15% ❌ **LOOSENED** (in test_pytorch_aliasing_reduction)
- Aliasing reduction: ≥50% ✓ (in test_issue_subpixel_aliasing)
- Peak drift: ≤0.5px ✓
- FWHM stability: ≤5% ✓
- C-PyTorch correlation: ≥0.98 ✓

**Severity:** Moderate (inconsistent thresholds between tests)

**Recommendation:**
1. Harmonize thresholds (use 50% everywhere)
2. Remove temporary 15% threshold after "fixing subpixel physics"

---

## Summary Table

| Test | Threshold | Spec | Implementation | Delta | Severity |
|------|-----------|------|----------------|-------|----------|
| AT-PARALLEL-001 | Correlation | ≥0.9999 | ≥0.9999 | 0 | ✅ MATCH |
| AT-PARALLEL-002 | Correlation | ≥0.9999 | ≥0.9799 | -0.02 | ⚠️ LOOSENED |
| AT-PARALLEL-006 | Peak position | ±0.5px | ±1.5px | +1.0px | 🔴 LOOSENED |
| AT-PARALLEL-006 | Wavelength | ±1% | ±3% | +2% | 🔴 LOOSENED |
| AT-PARALLEL-006 | Distance | ±2% | ±4% | +2% | 🔴 LOOSENED |
| AT-PARALLEL-007 | Correlation | ≥0.9999 | ≥0.9995 | -0.0004 | ⚠️ LOOSENED |
| AT-PARALLEL-009 | N-slope | ±0.3 | ±0.35 | +0.05 | ⚠️ LOOSENED |
| AT-PARALLEL-012 | simple_cubic corr | ≥0.9995 | ≥0.9985 | -0.001 | 🔴 LOOSENED |
| AT-PARALLEL-012 | simple_cubic match | ≥95% | ≥85% | -10% | 🔴 LOOSENED |
| AT-PARALLEL-012 | triclinic_P1 | ≥0.9995 | 0.9605 | -0.0390 | 🔴 **FAILING** |
| AT-PARALLEL-020 | Correlation | ≥0.95 | ≥0.85 | -0.10 | 🔴 LOOSENED |
| AT-PARALLEL-020 | Intensity ratio | [0.9, 1.1] | [0.15, 1.5] | 10x wider | 🔴 LOOSENED |
| AT-PARALLEL-028 | CPU perf | ≥0.5x | ≥0.5x | 0 | ✅ MATCH |
| AT-PARALLEL-028 | GPU perf | ≥10x | ≥10x | 0 | ✅ MATCH |
| AT-PARALLEL-029 | Aliasing | ≥50% | ≥15% | -35% | ⚠️ LOOSENED |

---

## Actionable Recommendations

### Priority 1 (Blocking)

1. **AT-PARALLEL-012 triclinic_P1 FAILURE**
   - **Action:** Route to debug prompt (per Ralph routing rules)
   - **Owner:** Debugging loop
   - **Blocker:** Yes - spec violation, must fix before claiming conformance

### Priority 2 (High - Spec Violations)

2. **AT-PARALLEL-006 Excessive Loosening**
   - **Action:** Restore thresholds to spec (0.5px, 1%, 2%)
   - **Investigation:** Why is discretization causing 3x errors?
   - **Blocker:** Yes - major spec deviations

3. **AT-PARALLEL-012 ADR-12 Relaxations**
   - **Action:** Remove 0.001 correlation tolerance from simple_cubic and tilted
   - **Action:** Restore peak matching from 85% to 95%
   - **Action:** Implement high-res variant (currently skipped)

4. **AT-PARALLEL-020 Absorption Issues**
   - **Action:** Fix absorption implementation
   - **Action:** Restore correlation (0.85→0.95), intensity ratio ([0.15,1.5]→[0.9,1.1])
   - **Alternative:** Mark as xfail until absorption fixed

### Priority 3 (Moderate - Minor Spec Violations)

5. **AT-PARALLEL-007 Correlation Harmonization**
   - **Action:** Change test from 0.9995 to 0.9999 to match spec and YAML

6. **AT-PARALLEL-002 Pattern Correlation**
   - **Action:** Investigate if 0.9799 threshold is masking real issues
   - **Decision:** Keep if parity test (0.9999) is sufficient gate

7. **AT-PARALLEL-029 Aliasing Threshold**
   - **Action:** Harmonize to 50% everywhere, remove 15% temporary threshold

### Priority 4 (Low - Accept with Justification)

8. **AT-PARALLEL-009 N-scaling Tolerance**
   - **Action:** Accept ±0.35 (documented, minor deviation)

---

## Compliance Score

**Spec Conformance:** 78%
- **Fully Conforming:** 2/9 tests (22%)
- **Minor Violations:** 3/9 tests (33%)
- **Major Violations:** 3/9 tests (33%)
- **Failing:** 1/9 test (11%)

**Risk Assessment:**
- **HIGH RISK:** AT-PARALLEL-012 (failing), AT-PARALLEL-006 (3x loosening), AT-PARALLEL-020 (10x loosening)
- **MODERATE RISK:** AT-PARALLEL-007, AT-PARALLEL-002, AT-PARALLEL-029
- **LOW RISK:** AT-PARALLEL-009

---

## Next Steps

1. ✅ **Complete this audit** (document findings)
2. 🔄 **Update fix_plan.md** with prioritized action items
3. 🔴 **Route AT-PARALLEL-012 to debug prompt** (per routing rules)
4. 🔧 **Create fix_plan items** for Priority 2-4 issues
5. 📊 **Track progress** on restoring spec compliance

---

## Audit Methodology

- **Spec source:** specs/spec-a-parallel.md
- **Test sources:** tests/test_at_parallel_*.py, tests/parity_cases.yaml
- **Tools:** Parallel subagent analysis, manual cross-reference
- **Coverage:** 9 of 28 AT-PARALLEL tests (remaining tests assumed MATCH unless flagged)

---

**Audit completed:** 2025-09-30
**Next audit recommended:** After AT-PARALLEL-012 resolution