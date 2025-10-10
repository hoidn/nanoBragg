# CLI-DEFAULTS-001 Attempt #1 — Failure Reproduction

## Summary
- **Date**: 2025-10-10T15:31:38Z
- **Command**: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F`
- **Exit Code**: 1 (test failure)
- **Runtime**: 11.01s

## Failure Mode

The CLI runner **succeeds** (returncode=0) and creates both output files, but the **float image contains all zeros**.

### Stack Trace Summary
```
tests/test_at_cli_002.py:59: AssertionError
assert np.any(float_data > 0), "Float image should have non-zero values"
```

### Test Command That Executed Successfully (but produced zero output)
```bash
python3.13 -m nanobrag_torch \
  -cell 100 100 100 90 90 90 \
  -default_F 100 \
  -detpixels 32 \
  -pixel 0.1 \
  -distance 100 \
  -lambda 6.2 \
  -N 5 \
  -floatfile /tmp/.../output.bin \
  -intfile /tmp/.../output.img
```

## Immediate Suspicions

### Primary Hypothesis (H1): Missing HKL fallback logic
- **Probability**: 80%
- **Evidence**: The command provides `-default_F 100` but no `-hkl` file
- **Expected behavior per spec**: When no HKL file is provided and `default_F > 0`, the simulator should use `default_F` as the structure factor for all reflections
- **Observed behavior**: Image is all zeros, suggesting structure factors are not being populated from `default_F`
- **Next action**: Inspect `src/nanobrag_torch/models/crystal.py` method `get_structure_factor()` to verify fallback logic

### Secondary Hypothesis (H2): Zero fluence calculation
- **Probability**: 15%
- **Evidence**: No explicit `-fluence` or `-flux`/`-exposure`/`-beamsize` provided
- **Expected behavior**: Simulator should use spec-defined defaults
- **Observed behavior**: Zero output could result from zero fluence
- **Next action**: Check `src/nanobrag_torch/config.py` BeamConfig defaults

### Tertiary Hypothesis (H3): Output scaling issue
- **Probability**: 5%
- **Evidence**: Files are created (no I/O error), but contain zeros
- **Possible cause**: Final intensity scaling step drops all values
- **Next action**: Add trace logging for intensity accumulation

## Artifacts
- `pytest.log`: Full pytest output with stack trace
- `commands.txt`: Exact command executed
- This file: `attempt_notes.md`

## Next Steps
1. Examine `Crystal.get_structure_factor()` implementation
2. Verify `default_F` parameter is correctly passed through config chain
3. Add minimal debug logging to confirm structure factor lookups
4. Draft targeted fix with regression test
5. Update `docs/fix_plan.md` with findings and remediation plan

## References
- Spec: `specs/spec-a-cli.md` §AT-CLI-002
- Test: `tests/test_at_cli_002.py:28-59`
- Config map: `docs/development/c_to_pytorch_config_map.md` (line 26: `-default_F` mapping)
