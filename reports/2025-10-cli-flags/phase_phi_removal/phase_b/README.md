# Phase B — Implementation De-scoping

**Status:** Not Started  
**Prerequisites:** Phase A complete (baseline inventory captured)  
**Goal:** Remove φ carryover shim entry points while preserving spec-mode behavior

## Design Review Checklist

Before executing Phase B tasks (B1-B3), review the following:

### B1: CLI Flag Deprecation
- [ ] Locate `--phi-carryover-mode` argparse definition in `src/nanobrag_torch/__main__.py`
- [ ] Verify no documentation outside CLAUDE.md references the flag
- [ ] Plan help text update to remove mention of c-parity mode
- [ ] Ensure error messaging no longer suggests the flag as an option

### B2: Config/Model Plumbing Removal
- [ ] Confirm `CrystalConfig.phi_carryover_mode` field can be safely deleted
- [ ] Identify all call sites of `apply_phi_carryover` method
- [ ] Verify `_phi_cache_initialized` is only used by carryover path
- [ ] Review `crystal.py:1482-1484` conditional for clean extraction
- [ ] Ensure spec-mode rotation pipeline remains vectorized (no scalar loops)
- [ ] Update docstrings to cite `specs/spec-a-core.md:204-240`

### B3: Debug Harness Retirement
- [ ] Audit `scripts/trace_harness.py` (if exists) for `--phi-mode` options
- [ ] Check `reports/.../trace_harness.py` variants for similar cleanup
- [ ] Plan replacement guidance for spec-only tooling
- [ ] Document deprecation in script help text or README

## Targeted Test Plan

After B1-B3 implementation:

1. Run spec-mode baseline: `pytest -v tests/test_cli_scaling_phi0.py`
2. Verify no import errors: `pytest --collect-only -q`
3. Confirm device neutrality: Run once on CPU, once on CUDA (if available)
4. Capture metrics/logs under `reports/.../phase_b/<timestamp>/`

## Exit Criteria

- [ ] All B1-B3 tasks complete
- [ ] Spec-mode tests pass without degradation
- [ ] No references to `phi_carryover_mode` in production code
- [ ] Artifacts captured with commands/env/checksums
- [ ] Ready for Phase C test realignment

## Handoff Notes

Ralph will execute this phase once supervisor approves Phase A artifacts and provides updated `input.md` with specific Do Now instructions for B1-B3.
