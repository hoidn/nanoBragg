=== Phase C2 Parity Run Summary ===

**Date:** 2025-10-06T00:25:09Z
**Command:** Full supervisor command from prompts/supervisor.md

## Artifacts Generated
- c_cli.log: C binary stdout/stderr (7.9K)
- c_img.bin: C float image output (24M)
- torch_stdout.log: PyTorch CLI stdout/stderr (445B)
- torch_img.bin: PyTorch float image output (24M)

## Key Observations
### C Binary Behavior
- custom convention selected.
- pivoting detector around sample
- DETECTOR_PIX0_VECTOR -0.216475836204836 0.216343050492215 -0.230192414300537

### PyTorch CLI Behavior
-   Convention: CUSTOM (using custom detector basis vectors)
-   Max intensity: 1.150e+05 at pixel (1145, 2220)
- Wrote float image to reports/2025-10-cli-flags/phase_c/parity/torch_img.bin

## Test Results
**Command:** `env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE pytest -q tests/test_cli_flags.py`
**Result:** 18 passed in 2.47s
