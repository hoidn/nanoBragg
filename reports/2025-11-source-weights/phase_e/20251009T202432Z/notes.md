# Phase E1 Execution Notes

## Loop Summary
- **Loop ID:** ralph loop #254
- **Mode:** Docs (documentation-only, no code changes)
- **Task:** Draft spec_vs_c_decision.md per input.md Do Now steps 1-10
- **Result:** SUCCESS

## Execution Timeline

### Step 1: Timestamp & Directory Creation
- Generated timestamp: `20251009T202432Z`
- Created: `reports/2025-11-source-weights/phase_e/20251009T202432Z/`

### Step 2: Environment Capture
- Python: 3.13.5
- PyTorch: 2.7.1+cu126
- Git commit: 54a28e2fefab3b13be19920fd3a35fa2972651fb
- Git branch: feature/spec-based-2
- Working tree: Clean (only new report directory untracked)

### Step 3: Pytest Selector Validation
- Command: `pytest --collect-only -q tests/test_cli_scaling.py::TestSourceWeights tests/test_cli_scaling.py::TestSourceWeightsDivergence`
- Exit code: 0
- Tests collected: 2 (TestSourceWeights::test_weighted_source_matches_c, TestSourceWeightsDivergence::test_sourcefile_only_parity)
- Validation: PASSED

### Step 4: Decision Memo Draft
- File: `spec_vs_c_decision.md`
- Sections: 22 (Executive Summary through Appendix B)
- Length: 500+ lines
- Content:
  - Spec citations (specs/spec-a-core.md:151-153)
  - Trace evidence (20251009T195032Z bundle)
  - C-PARITY-001 classification
  - Test redesign guidance (Phase F)
  - Downstream impacts (vectorization unblocks)
  - Decision statement (copy/paste ready)
  - Risk mitigation (migration guide, CLI warnings)
  - Next steps (Phases F-H roadmap)
  - References (all evidence bundles)
  - Numeric comparison table
  - Authoritative commands

### Step 5: Commands Log
- File: `commands.txt`
- Contents:
  - Environment setup
  - Directory creation
  - Pytest validation
  - Python metadata capture script
  - Git status
  - Spec/evidence references
  - Decision memo checksum (SHA1: e8bcac0220bd9ae4335641021e40b6a8eb70d37a)
  - Directory listing

### Step 6: Integrity Verification
- All artifacts stored under `reports/2025-11-source-weights/phase_e/20251009T202432Z/`
- Files created:
  - spec_vs_c_decision.md (FINAL)
  - commands.txt
  - collect.log
  - env.json
  - git_status.txt
  - notes.md (this file)

## Key Findings from Decision Memo

### Spec Authority
- **Primary:** `specs/spec-a-core.md:151` — "Both the weight column and the wavelength column are read but ignored"
- **Supporting:** `docs/development/c_to_pytorch_config_map.md:35` — Lambda override precedence

### C-PARITY-001 Bug Definition
- **Symptom:** C creates 4 sources (2 zero-weight placeholders + 2 from file) with steps=4
- **Impact:** Under-scales intensity by 2×, then applies weighted accumulation (violates spec)
- **Evidence:** Trace bundle 20251009T195032Z

### PyTorch Correctness
- **Implementation:** Steps=2 (counts only actual sources), ignores weights, uses CLI lambda
- **Status:** Spec-compliant per §4 requirements

### Test Redesign Requirements
- **Current:** TestSourceWeights::test_weighted_source_matches_c (enforces C parity, correlation > 0.95)
- **Proposed:** test_source_weights_ignored_per_spec (PyTorch self-consistency, rtol=1e-3)
- **Additional:** test_cli_lambda_overrides_sourcefile, @pytest.mark.xfail C-comparison test

### Downstream Unblocks
- **VECTOR-TRICUBIC-002:** Can proceed with PyTorch-only smoke tests once Phase F-G tests enforce spec
- **VECTOR-GAPS-002:** Phase B1 profiling unblocked by spec-compliance gate
- **Gate Update:** `pytest -v tests/test_cli_scaling.py::test_source_weights_ignored_per_spec` (≥0.999)

## Next Phase Responsibilities

### Phase E2 (galph — supervisor)
- Update `docs/fix_plan.md` [SOURCE-WEIGHT-001] Attempts History with Attempt #25
- Update `galph_memory.md` with decision summary
- Cite C-PARITY-001 as expected divergence
- Mark Phase E1 complete, E2 in-progress

### Phase E3 (galph — supervisor)
- Refresh `plans/active/vectorization.md` (VECTOR-TRICUBIC-002 gates)
- Refresh `plans/active/vectorization-gap-audit.md` (VECTOR-GAPS-002 Phase B1)
- Update dependent plan references from C-parity to spec-compliance

### Phase F1-F3 (galph — supervisor)
- Draft `phase_f/<STAMP>/test_plan.md`
- Inventory affected tests (TestSourceWeights*, AT-PARALLEL-*, golden_data cases)
- Define spec-aligned acceptance criteria
- Validate pytest selectors
- Document CLI artifact expectations

### Phase G1-G3 (ralph — engineer)
- Rewrite tests per test_plan.md
- Run targeted pytest + CLI bundle
- Capture evidence under `phase_g/<STAMP>/`
- Log new Attempt noting expected C divergence (correlation < 0.8)

### Phase H1-H3 (ralph — engineer)
- Update `docs/architecture/pytorch_design.md` (Sources section)
- Update `docs/development/pytorch_runtime_checklist.md` (warning items)
- Propagate decision to dependent plans
- Add C-PARITY-001 to `docs/user/migration_guide.md`
- Prepare archival summary

## Observations

### Decision Finality
- Memo marked as **FINAL**
- Spec-first stance locked
- C behavior classified as bug (C-PARITY-001)
- Test redesign approach documented
- Downstream impacts assessed

### Evidence Quality
- Trace bundle 20251009T195032Z provides comprehensive C vs PyTorch comparison
- Geometry match confirmed (cos2theta, pix0_vector, R_distance exact)
- First divergence identified (steps normalization)
- Spec citations authoritative (§4 normative statement)

### Risk Mitigation
- Migration guide update required
- CLI warning for varying weights
- Golden data audit for sourcefile-dependent tests
- Conversion script for spec-compliant sourcefiles

### Reproducibility
- All commands logged in commands.txt
- Environment snapshot in env.json
- Decision memo checksum recorded
- Git status captured

## Exit Criteria Verification

- [x] Phase E1 complete (decision memo drafted and locked)
- [x] Pytest selectors validated (2 tests collected successfully)
- [x] Environment metadata captured (env.json, git_status.txt)
- [x] Decision memo comprehensive (22 sections, all required content)
- [x] Commands reproducible (commands.txt with timestamps)
- [x] Integrity verifiable (SHA1 checksum recorded)
- [ ] Phase E2 pending (fix_plan.md update — supervisor task)
- [ ] Phase E3 pending (dependent plan updates — supervisor task)

## Handoff to Supervisor (galph)

This memo is ready for Phase E2 integration. The supervisor should:
1. Read spec_vs_c_decision.md in full
2. Update docs/fix_plan.md with Attempt #25 entry
3. Update galph_memory.md with decision summary
4. Proceed to Phase E3 (dependent plan updates)
5. Prepare Phase F design packet (test_plan.md)

---

**Memo Status:** FINAL
**Phase E1 Status:** COMPLETE
**Next Phase:** E2 (supervisor handoff)
