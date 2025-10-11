# Source Weighting Implementation Plan ([SOURCE-WEIGHT-002])

**Initiative:** [TEST-SUITE-TRIAGE-001] Sprint 1.2
**Owner:** ralph
**Status:** Phase A — Baseline Capture
**Priority:** High (Critical Path — Spec Compliance)
**Created:** 2025-01-17

---

## Context

**Problem Statement:**
Six tests in cluster C3 (Source Weighting) are failing due to incomplete sourcefile parsing and missing source weight application in simulator normalization. This violates spec-a-core.md §§3.4–3.5 (Sources, Divergence & Dispersion) and AT-SRC-001 requirements.

**Spec References:**
- `specs/spec-a-core.md` §142–166 (Sources, Divergence & Dispersion)
- `specs/spec-a-core.md` Lines 635–637 (AT-SRC-001 Sourcefile and weighting)
- `arch.md` §8 (Physics Model & Scaling)

**Key Requirements from Spec:**
1. **Sourcefile format** (spec lines 144–149):
   - Each line: `X Y Z weight λ` (position in meters, weight dimensionless, λ in meters)
   - Missing fields default to: position along `-source_distance·b`, weight=1.0, λ=λ0
   - Positions normalized to unit direction vectors

2. **AT-SRC-001 Expectation** (spec lines 636–637):
   - Setup: `-sourcefile` with two sources having distinct weights and λ; disable other sampling
   - Expectation: `steps = 2`; intensity contributions SHALL sum with per-source λ and weight, then divide by steps

3. **Current Implementation Gap:**
   - `io/source.py`: `read_sourcefile()` parses weight column but may not handle all column configurations
   - `simulator.py`: Source weights not integrated into intensity normalization (steps calculation ignores weights)

**Test Suite:**
- `tests/test_at_src_001.py` — AT-SRC-001 I/O and integration tests (6 tests)
- `tests/test_at_src_001_simple.py` — Simplified weighting regression test (1 test)

**Current Failure Count:** 6 (from Phase I classification)

**Reproduction Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py
```

---

## Phase A: Baseline Capture (Evidence-Only)

**Goal:** Document current test failures, capture environment snapshot, and identify exact failure modes before implementation begins.

### Tasks

**A1. Create artifact directory**
- Create timestamped directory: `reports/2026-01-test-suite-triage/phase_j/<STAMP>/source_weighting/`
- Subdirectories: `logs/`, `artifacts/`, `env/`

**A2. Execute baseline test run**
- Run: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py`
- Capture: stdout → `logs/pytest.log`, stderr if applicable
- Save `pytest --junit-xml` output → `artifacts/pytest.xml`
- Record exit code, runtime, environment variables

**A3. Environment snapshot**
- Capture Python version, PyTorch version, CUDA availability
- Record git status (branch, commit SHA, modified files)
- Save as `env/env.json` with structured fields
- Record package versions: `pip list --format=json` → `env/packages.json`

**A4. Failure analysis**
- Parse pytest output for failure types:
  - Missing implementation (e.g., AttributeError, NotImplementedError)
  - Incorrect behavior (e.g., AssertionError on weights/wavelengths)
  - Integration failures (simulation runs but wrong normalization)
- Extract failure stack traces → `artifacts/failures_raw.txt`
- Categorize failures by type → `summary.md`

### Deliverables
- [ ] `reports/2026-01-test-suite-triage/phase_j/<STAMP>/source_weighting/commands.txt` — exact commands executed
- [ ] `reports/2026-01-test-suite-triage/phase_j/<STAMP>/source_weighting/logs/pytest.log` — full pytest output
- [ ] `reports/2026-01-test-suite-triage/phase_j/<STAMP>/source_weighting/env/env.json` — environment snapshot
- [ ] `reports/2026-01-test-suite-triage/phase_j/<STAMP>/source_weighting/summary.md` — failure counts + categorization

### Exit Criteria
- All 4 tasks (A1-A4) complete
- Baseline artifacts archived with timestamp
- Failure modes documented and categorized
- Ready for Phase B implementation planning

---

## Phase B: Implementation (PENDING — Not Authorized Yet)

**DO NOT BEGIN PHASE B UNTIL PHASE A IS COMPLETE AND APPROVED**

Phase B will include:
1. Sourcefile parsing implementation for all column configurations
2. Source weight integration into simulator normalization
3. Flux calculation validation against spec formulas
4. Weighted multi-source regression tests

(Detailed Phase B tasks to be added after Phase A completion)

---

## References

- **Remediation sequence:** `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_sequence.md` §Sprint 1.2
- **Remediation tracker:** `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md` (Cluster C3)
- **Fix plan entry:** `docs/fix_plan.md` §[SOURCE-WEIGHT-002]
- **Spec (core):** `specs/spec-a-core.md` §§3.4–3.5, AT-SRC-001
- **Config map:** `docs/development/c_to_pytorch_config_map.md` (Beam Parameters section)

---

**Plan Status:** Phase A READY — awaiting execution of baseline capture tasks
